"""Episode anatomy — phase structure inside stress episodes from REAL-TIME observables
(descriptive, frozen OOS labels; instrument work, no prereg needed, no look spent;
firewalled from the chapter-3 draft prereg — informs future preregs only).

The question (Adam, 2026-07-23): the state may be correct, but the state is not the
phase. Can shock -> persistent stress -> trough -> recovery be distinguished using
variables observable at time t?

Causal coordinates at t: episode age tau; EWMA-20 vol sig (backtest spec) and its 5d
trend dsig / acceleration d2sig; drawdown DD vs running peak and its 5d velocity dDD;
trailing 21d jump count J21 (|r| > 2.5 x lagged daily EWMA vol). Described objects:
forward 5d/21d returns, forward 21d realized vol, day-level exit hazard within 21d
(right-censored final episode excluded, discrete-time survival convention).

Overlapping forward windows => serially correlated rows; this is DESCRIPTION, no SEs,
no economic claims. Any pattern found is a hypothesis for out-of-hypothesis-sample
confirmation (international panels), per the 2026-07-23 discipline.

Writes results/episode_anatomy.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from atlas import episodes_of

ANN = 252
AGE_BINS = [(1, 5), (6, 10), (11, 21), (22, 42), (43, 63), (64, 126), (127, 10_000)]


def shift(x, k):
    out = np.full_like(x, np.nan, dtype=float)
    if k > 0:
        out[k:] = x[:-k]
    return out


def main():
    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True)
    labels = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"])
    df = panel.loc[panel.index.isin(labels["date"])]
    s = labels.set_index("date").loc[df.index, "state"].to_numpy()
    r = df["mkt_ret"].to_numpy()
    dates = df.index
    T = len(r)
    rows = []

    # --- causal coordinates ---
    sig_d = pd.Series(r).ewm(halflife=20).std().to_numpy()
    sig = sig_d * np.sqrt(ANN)
    dsig = np.log(sig / shift(sig, 5))
    d2sig = dsig - shift(dsig, 5)
    px = np.cumprod(1.0 + r)
    dd = px / np.maximum.accumulate(px) - 1.0
    ddd = dd - shift(dd, 5)
    jump = (np.abs(r) > 2.5 * shift(sig_d, 1)).astype(float)
    j21 = pd.Series(jump).rolling(21).sum().to_numpy()

    # --- forward (described) objects ---
    rs = pd.Series(r)
    fwd5 = rs.rolling(5).mean().shift(-5).to_numpy() * ANN
    fwd21 = rs.rolling(21).mean().shift(-21).to_numpy() * ANN
    fvol21 = rs.rolling(21).std().shift(-21).to_numpy() * np.sqrt(ANN)

    # --- episode geometry ---
    eps = episodes_of(s)
    age = np.zeros(T, dtype=int)
    to_exit = np.full(T, np.nan)
    exit21 = np.full(T, np.nan)
    ep_id = np.full(T, -1, dtype=int)
    for e, (a, b) in enumerate(eps):
        idx = np.arange(a, b + 1)
        age[idx] = idx - a + 1
        ep_id[idx] = e
        if b < T - 1:  # uncensored
            to_exit[idx] = b - idx
            exit21[idx] = (b - idx < 21).astype(float)
    stress = s == 1
    print(f"{len(eps)} stress episodes, {int(stress.sum())} stress days, "
          f"{dates[0].date()}..{dates[-1].date()}"
          + (" (final episode censored)" if eps and eps[-1][1] == T - 1 else ""))

    print("\n=== 1. AGE PROFILE: conditional on stress and tau = days since onset ===")
    print(f"  {'tau':>9} {'n':>5} {'eps':>4} {'hz21':>5} {'fwd5':>7} {'fwd21':>7} "
          f"{'fvol21':>6} {'sig':>6} {'dsig>0':>6} {'DD':>7} {'dDD>0':>6} {'J21':>5}")
    for lo, hi in AGE_BINS:
        m = stress & (age >= lo) & (age <= hi)
        if m.sum() < 10:
            continue
        hz = np.nanmean(exit21[m])
        row = dict(section="age_profile", key=f"{lo}-{hi if hi < 10_000 else '+'}",
                   n=int(m.sum()), n_eps=int(len(np.unique(ep_id[m]))),
                   hazard21=round(float(hz), 3),
                   fwd5_ann=round(float(np.nanmean(fwd5[m])), 3),
                   fwd21_ann=round(float(np.nanmean(fwd21[m])), 3),
                   fvol21=round(float(np.nanmean(fvol21[m])), 3),
                   sig=round(float(np.nanmean(sig[m])), 3),
                   frac_dsig_pos=round(float(np.nanmean(dsig[m] > 0)), 3),
                   frac_d2sig_pos=round(float(np.nanmean(d2sig[m] > 0)), 3),
                   dd=round(float(np.nanmean(dd[m])), 3),
                   frac_ddd_pos=round(float(np.nanmean(ddd[m] > 0)), 3),
                   j21=round(float(np.nanmean(j21[m])), 2))
        rows.append(row)
        print(f"  {row['key']:>9} {row['n']:>5} {row['n_eps']:>4} {row['hazard21']:>5.0%} "
              f"{row['fwd5_ann']:>+7.1%} {row['fwd21_ann']:>+7.1%} {row['fvol21']:>6.1%} "
              f"{row['sig']:>6.1%} {row['frac_dsig_pos']:>6.0%} {row['dd']:>7.1%} "
              f"{row['frac_ddd_pos']:>6.0%} {row['j21']:>5.1f}")

    print("\n=== 2. VOL TRAJECTORY: sig level x dsig direction, within stress ===")
    med_sig = float(np.median(sig[stress]))
    for lv, lname in ((sig >= med_sig, "hi-vol"), (sig < med_sig, "lo-vol")):
        for dv, dname in ((dsig > 0, "rising"), (dsig <= 0, "falling")):
            m = stress & lv & dv
            if m.sum() < 10:
                continue
            row = dict(section="vol_trajectory", key=f"{lname}/{dname}", n=int(m.sum()),
                       hazard21=round(float(np.nanmean(exit21[m])), 3),
                       fwd5_ann=round(float(np.nanmean(fwd5[m])), 3),
                       fwd21_ann=round(float(np.nanmean(fwd21[m])), 3),
                       fvol21=round(float(np.nanmean(fvol21[m])), 3))
            rows.append(row)
            print(f"  {row['key']:>16}: n={row['n']:5} hz21 {row['hazard21']:>4.0%} "
                  f"fwd5 {row['fwd5_ann']:>+7.1%} fwd21 {row['fwd21_ann']:>+7.1%} "
                  f"fvol21 {row['fvol21']:>6.1%}")

    print("\n=== 3. PHASE SIGNATURE: dsig x dDD quadrants, within stress ===")
    print("  (shock = rising vol + deepening DD; recovery = falling vol + healing DD)")
    for dv, vn in ((dsig > 0, "vol-rising"), (dsig <= 0, "vol-falling")):
        for dq, qn in ((ddd < 0, "DD-deepening"), (ddd >= 0, "DD-healing")):
            m = stress & dv & dq
            if m.sum() < 10:
                continue
            row = dict(section="phase_quadrant", key=f"{vn}/{qn}", n=int(m.sum()),
                       n_eps=int(len(np.unique(ep_id[m]))),
                       hazard21=round(float(np.nanmean(exit21[m])), 3),
                       fwd5_ann=round(float(np.nanmean(fwd5[m])), 3),
                       fwd21_ann=round(float(np.nanmean(fwd21[m])), 3),
                       fvol21=round(float(np.nanmean(fvol21[m])), 3),
                       med_age=int(np.median(age[m])), j21=round(float(np.nanmean(j21[m])), 2))
            rows.append(row)
            print(f"  {row['key']:>25}: n={row['n']:5} ({row['n_eps']:2} eps, med age "
                  f"{row['med_age']:3}) hz21 {row['hazard21']:>4.0%} fwd5 {row['fwd5_ann']:>+7.1%} "
                  f"fwd21 {row['fwd21_ann']:>+7.1%} fvol21 {row['fvol21']:>6.1%} J21 {row['j21']:.1f}")

    print("\n=== 4. POSITION IN EPISODE (first10 causal; last10 EX-POST — not tradeable) ===")
    groups = (("first10 (tau<=10)", stress & (age <= 10)),
              ("middle", stress & (age > 10) & (to_exit >= 10)),
              ("last10 (EX-POST)", stress & (to_exit < 10) & (age > 10)))
    for name, m in groups:
        if m.sum() < 10:
            continue
        row = dict(section="position", key=name, n=int(m.sum()),
                   ret_ann=round(float(np.nanmean(r[m]) * ANN), 3),
                   sig=round(float(np.nanmean(sig[m])), 3),
                   frac_dsig_pos=round(float(np.nanmean(dsig[m] > 0)), 3),
                   frac_ddd_pos=round(float(np.nanmean(ddd[m] > 0)), 3),
                   j21=round(float(np.nanmean(j21[m])), 2))
        rows.append(row)
        print(f"  {name:>18}: n={row['n']:5} ret {row['ret_ann']:>+7.1%} sig {row['sig']:>6.1%} "
              f"dsig>0 {row['frac_dsig_pos']:>4.0%} dDD>0 {row['frac_ddd_pos']:>4.0%} "
              f"J21 {row['j21']:.1f}")

    print("\n=== 5. TRAJECTORY SHAPE per episode (EX-POST alignment) ===")
    ep_rows = []
    for e, (a, b) in enumerate(eps):
        if b - a + 1 < 5:
            continue
        path = np.cumprod(1.0 + r[a:b + 1])
        t_trough = int(np.argmin(path)) + 1
        t_sigpk = int(np.argmax(sig[a:b + 1])) + 1
        ep_rows.append(dict(section="episode_shape", key=str(dates[a].date()),
                            days=b - a + 1, t_trough=t_trough, t_sigpeak=t_sigpk,
                            sigpk_minus_trough=t_sigpk - t_trough,
                            early_j21=round(float(np.nanmean(j21[a:min(a + 10, b + 1)])), 2),
                            early_dsig=round(float(np.nanmean(dsig[a:min(a + 10, b + 1)])), 4)))
    ep = pd.DataFrame(ep_rows)
    rows.extend(ep_rows)
    frac_after = float((ep["sigpk_minus_trough"] > 0).mean())
    print(f"  vol peak vs price trough: sig peaks AFTER the trough in {frac_after:.0%} of "
          f"{len(ep)} episodes (median offset {ep['sigpk_minus_trough'].median():+.0f}d) — "
          f"if vol peaked reliably before the trough, falling vol would flag the rebound")

    print("\n=== 6. EPISODE SPECIES: do early observables foretell duration? (EX-POST split) ===")
    ep["long"] = ep["days"] > 42
    for grp, gdf in ep.groupby("long"):
        name = "long (>42d)" if grp else "short (<=42d)"
        row = dict(section="species", key=name, n=len(gdf),
                   med_days=int(gdf["days"].median()),
                   med_early_j21=float(gdf["early_j21"].median()),
                   med_early_dsig=float(gdf["early_dsig"].median()))
        rows.append(row)
        print(f"  {name:>13}: {row['n']:2} episodes, median {row['med_days']:3}d, "
              f"early J21 {row['med_early_j21']:.1f}, early dsig {row['med_early_dsig']:+.3f}")

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results" / "episode_anatomy.csv", index=False)
    print(f"\nwrote results/episode_anatomy.csv ({len(out)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
