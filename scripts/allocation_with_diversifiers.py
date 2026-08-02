"""Characterization (no look, a-priori params, no tuning): does adding a GOLD + TREND leg to the
existing momentum-sleeve product improve holdability? PRODUCT-PLAN's own next-undone step
("diversify allocation w/ trend+gold, the honest 2022 stock-bond-together fix, as a diversifier
not a timer").

Reuses the exact existing construction (`validate_product.py` / `compare_vs_jm.py`): 48-industry
buffered momentum sleeve (`momentum_breadth.buffered_momentum`) + 10y bond, vol-targeted to 10%
ann (6m trailing vol, monthly, one-period lag). Adds the already-GATED trend proxy
(`trend_proxy_daily.csv`, corr 0.69 vs DBMF, UNCHANGED) and a standalone long-only GLD leg,
at round a-priori sizes from institutional practice (gold 5-15%, trend 5-15% of the book) —
NOT fit to this data. Reports a couple of alternate sizings for sensitivity, not an optimum search.

Matched-window comparison: BEFORE and AFTER are both restricted to the window where gold+trend
data exist (2005-02+, since GLD lists Nov-2004 and the trend proxy starts Feb-2005) so the
DD/Sharpe comparison isn't confounded by different history lengths.

Writes results/allocation_with_diversifiers.csv.
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
VT_TARGET = 0.10     # matches compare_vs_jm.py / validate_product.py
VOL_WIN = 6


def perf(r, rf):
    r = r.dropna()
    rfa = rf.reindex(r.index).fillna(0.0).to_numpy()
    eq = np.cumprod(1 + r.to_numpy())
    return dict(n=len(r),
                ann_ret=round(eq[-1] ** (ANN / len(r)) - 1, 4),
                sharpe=round((r.to_numpy() - rfa).mean() / r.std() * np.sqrt(ANN), 3),
                max_dd=round(maxdd(r.to_numpy()), 4))


def window_ret(r, start, end):
    seg = r.loc[start:end].dropna()
    return round(float((1 + seg).prod() - 1), 4) if len(seg) else np.nan


def vol_target(base, rf, target=VT_TARGET):
    vol = (base.rolling(VOL_WIN).std() * np.sqrt(ANN)).shift(1)
    w = (target / vol).clip(0, 1).fillna(0)
    return w * base + (1 - w) * rf.reindex(base.index).fillna(0)


def load_gold_monthly():
    px = pd.read_csv(ROOT / "data/raw/trend_universe_prices.csv", index_col=0, parse_dates=True)
    r = px["GLD"].pct_change()
    return (1 + r).resample("ME").prod() - 1


def load_trend_monthly():
    r = pd.read_csv(ROOT / "data/processed/trend_proxy_daily.csv", index_col=0, parse_dates=True)["trend_ret"]
    return (1 + r).resample("ME").prod() - 1


def main():
    a = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    rf = (1 + a["rf"]).resample("ME").prod() - 1
    bond = (1 + a["bond10_ret"]).resample("ME").prod() - 1

    R48 = load_industry(48)
    m48 = (1 + R48).resample("ME").prod() - 1
    sleeve, turn = buffered_momentum(m48, rf.reindex(m48.index).fillna(0.0))

    gold = load_gold_monthly()
    trend = load_trend_monthly()

    idx = sleeve.index.intersection(bond.dropna().index).intersection(gold.dropna().index) \
        .intersection(trend.dropna().index).intersection(rf.dropna().index)
    sleeve, bond_i, gold_i, trend_i, rf_i = (s.loc[idx] for s in (sleeve, bond, gold, trend, rf))
    print(f"matched window: {idx[0].date()}..{idx[-1].date()}  ({len(idx)} months)")

    rows = []
    sizings = {"before (0% div)": 0.0, "5%/5%": 0.05, "10%/10% (a-priori default)": 0.10, "15%/15%": 0.15}
    prods = {}
    for label, d in sizings.items():
        w_sleeve, w_bond, w_div = 0.6 * (1 - 2 * d), 0.4 * (1 - 2 * d), d
        base = w_sleeve * sleeve + w_bond * bond_i + w_div * gold_i + w_div * trend_i
        prod = vol_target(base, rf_i)
        prods[label] = prod
        p = perf(prod, rf_i)
        rows.append(dict(sizing=label, w_sleeve=round(w_sleeve, 2), w_bond=round(w_bond, 2),
                          w_gold=round(d, 2), w_trend=round(d, 2),
                          ann_ret=p["ann_ret"], sharpe=p["sharpe"], max_dd=p["max_dd"],
                          ret_2008=window_ret(prod, "2008-01", "2008-12"),
                          ret_2022=window_ret(prod, "2022-01", "2022-12")))

    print(f"\n{'sizing':28}{'ann ret':>9}{'Sharpe':>8}{'max DD':>9}{'2008':>9}{'2022':>9}")
    for r in rows:
        print(f"{r['sizing']:28}{r['ann_ret']:9.2%}{r['sharpe']:8.2f}{r['max_dd']:9.1%}"
              f"{r['ret_2008']:9.1%}{r['ret_2022']:9.1%}")

    # diversification check: correlation of the ADDED legs' blended return (the "residual" piece
    # beyond the pre-existing sleeve+bond core) against the pre-existing allocation.
    before = prods["before (0% div)"]
    d = 0.10
    added_legs = d * gold_i + d * trend_i          # what's newly introduced, unscaled by overlay
    corr = float(pd.concat([added_legs, before], axis=1).dropna().corr().iloc[0, 1])
    print(f"\ncorr(added gold+trend legs, pre-existing sleeve+bond-VT allocation) = {corr:+.3f}"
          f"  (matched window)")

    pd.DataFrame(rows).to_csv(ROOT / "results/allocation_with_diversifiers.csv", index=False)
    print("wrote results/allocation_with_diversifiers.csv")


if __name__ == "__main__":
    main()
