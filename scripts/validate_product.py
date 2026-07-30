"""Phase A4 (PRODUCT-PLAN): OOS/robustness validation of the momentum sleeve + static allocation,
plus international (Japan/Europe) confirmation. QA/characterization — a-priori params, NO optimization,
NO parameter search. The momentum construction has no fitted parameters (deterministic 12-1 buffered
rule), so "walk-forward" here = out-of-sample in TIME (decade-by-decade, and the recent/most-crowded
decade specifically — McLean-Pontiff post-publication decay) and out-of-sample in GEOGRAPHY (French
international 25 size/BE-ME panels the US signal never saw).

Everything reuses the already-frozen construction (`buffered_momentum` from momentum_breadth) and the
already-used allocation params (60/40 base, 6m trailing vol, 10% target — from compare_vs_jm). Nothing
is tuned here. Writes results/validate_product_*.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from momentum_breadth import buffered_momentum, load_industry
from run_config import maxdd

ANN = 12


def perf(r, rf):
    r = r.dropna()
    if len(r) < 24:
        return dict(n=len(r), ann_ret=np.nan, sharpe=np.nan, max_dd=np.nan)
    rfa = rf.reindex(r.index).fillna(0.0).to_numpy()
    eq = np.cumprod(1 + r.to_numpy())
    return dict(n=len(r),
                ann_ret=round(eq[-1] ** (ANN / len(r)) - 1, 4),
                sharpe=round((r.to_numpy() - rfa).mean() / r.std() * np.sqrt(ANN), 3),
                max_dd=round(maxdd(r.to_numpy()), 4))


def ew_bench(R, rf):
    """Equal-weight, monthly-rebalanced benchmark of the same universe (near-zero turnover)."""
    return R.mean(axis=1)


def decade_table(sleeve, bench, rf, label):
    rows = []
    segs = [("full", None)] + [(f"{d}s", str(d)[:3]) for d in range(1930, 2030, 10)]
    for name, dec in segs:
        s = sleeve if dec is None else sleeve.loc[f"{dec}0":f"{dec}9"]
        b = bench if dec is None else bench.loc[f"{dec}0":f"{dec}9"]
        if len(s.dropna()) < 24:
            continue
        ps, pb = perf(s, rf), perf(b, rf)
        rows.append(dict(universe=label, period=name, n=ps["n"],
                         sleeve_ret=ps["ann_ret"], sleeve_sharpe=ps["sharpe"], sleeve_dd=ps["max_dd"],
                         bench_ret=pb["ann_ret"], bench_sharpe=pb["sharpe"], bench_dd=pb["max_dd"],
                         sharpe_edge=round(ps["sharpe"] - pb["sharpe"], 3)))
    return pd.DataFrame(rows)


def run_universe(R, rf, label):
    """R: monthly returns DataFrame (names in columns). Returns (sleeve monthly, EW bench, decade df)."""
    sleeve, turn = buffered_momentum(R, rf.reindex(R.index).fillna(0.0))
    bench = ew_bench(R, rf).reindex(sleeve.index)
    df = decade_table(sleeve, bench, rf, label)
    return sleeve, bench, df, turn


def print_table(df, title):
    print(f"\n{title}")
    print(f"{'period':8}{'n':>5}{'sleeve_ret':>12}{'sl_Sharpe':>11}{'sl_DD':>9}"
          f"{'bench_Sh':>10}{'edge':>8}")
    for _, r in df.iterrows():
        print(f"{r['period']:8}{int(r['n']):5d}{r['sleeve_ret']:12.2%}{r['sleeve_sharpe']:11.2f}"
              f"{r['sleeve_dd']:9.1%}{r['bench_sharpe']:10.2f}{r['sharpe_edge']:+8.2f}")


def main():
    a = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    rf_us = ((1 + a["rf"]).resample("ME").prod() - 1)
    bond_us = ((1 + a["bond10_ret"]).resample("ME").prod() - 1)

    # ---- US SLEEVE (48-industry buffered momentum) — OOS-in-time robustness ----
    R48 = load_industry(48)
    m48 = (1 + R48).resample("ME").prod() - 1
    sleeve, bench, us_df, turn = run_universe(m48, rf_us, "US_48ind")
    print("=" * 70)
    print("PART 1 — US 48-industry momentum SLEEVE (a-priori buffered, no tuning)")
    print(f"annualized turnover {turn:.1f}x")
    print_table(us_df, "sleeve vs equal-weight 48-industry benchmark, by decade (OOS in time):")

    # ---- FULL PRODUCT: sleeve (60%) + 10y bond (40%), vol-targeted to 10% (compare_vs_jm params) ----
    idx = sleeve.index.intersection(bond_us.dropna().index)
    base = 0.6 * sleeve.loc[idx] + 0.4 * bond_us.loc[idx]
    volsig = (base.rolling(6).std() * np.sqrt(ANN)).shift(1)
    w = (0.10 / volsig).clip(0, 1).fillna(0)
    prod = w * base + (1 - w) * rf_us.reindex(idx).fillna(0)
    static = base                                      # non-vol-targeted 60/40 base = product benchmark
    prod_df = decade_table(prod, static, rf_us, "US_product")
    print("\n" + "=" * 70)
    print("PART 2 — FULL PRODUCT (sleeve 60% + bond 40%, vol-targeted 10%) vs static 60/40 base")
    print_table(prod_df, "product vs static-blend benchmark, by decade:")

    # ---- INTERNATIONAL confirmation (Japan, Europe) — genuinely OOS geographies ----
    intl_frames = []
    print("\n" + "=" * 70)
    print("PART 3 — INTERNATIONAL confirmation (identical construction, 25 size/BE-ME ports)")
    print("  NOTE: intl panels carry no rf; Sharpe uses rf=0 (raw). sleeve-vs-EW edge is rf-free & fair.")
    for region in ("japan", "europe"):
        p = pd.read_csv(ROOT / f"data/processed/{region}_assets_daily.csv", index_col=0, parse_dates=True)
        mp = (1 + p).resample("ME").prod() - 1
        zero_rf = pd.Series(0.0, index=mp.index)
        s, b, df, t = run_universe(mp, zero_rf, region)
        df["ann_turnover"] = round(t, 2)
        print_table(df, f"{region.upper()}: sleeve vs equal-weight 25-portfolio benchmark:")
        intl_frames.append(df)

    us_df.to_csv(ROOT / "results/validate_product_us_sleeve.csv", index=False)
    prod_df.to_csv(ROOT / "results/validate_product_us_full.csv", index=False)
    pd.concat(intl_frames).to_csv(ROOT / "results/validate_product_intl.csv", index=False)
    print("\nwrote results/validate_product_{us_sleeve,us_full,intl}.csv")


if __name__ == "__main__":
    main()
