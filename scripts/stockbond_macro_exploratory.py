#!/usr/bin/env python3
"""EXPLORATORY (go/no-go screen, NOT a validation test).

Hypothesis: after controlling for the volatility/stress axis, the macro/rates axis
(yield_slope) organizes the stock-bond correlation -- a dependence property VIX (a vol
LEVEL) is structurally sign-blind to. This is the one principled orthogonal-to-vol
target (rates/inflation regime governs stock-bond corr SIGN; Campbell-Sunderam-Viceira).

CAVEAT baked in: 2016-2026 contains ~ONE stock-bond correlation sign transition (2022).
Treat every number here as exploratory evidence for whether to invest in a backward data
extension (realized-vol stress axis -> ~1976, multiple inflation/rates cycles), NOT as
validation. In-sample descriptive + a low-power OOS split, reported side by side.

Reads : data/processed/features.csv (standardized vol/macro coords),
        data/processed/cross_asset.csv (adj prices)
Writes: results/stockbond_macro_exploratory.csv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import DATA_DIR, TRAIN_END

PROC = os.path.join(DATA_DIR, "processed")
H = 63


def fwd_corr(a, b, h):
    out = np.full(len(a), np.nan)
    for t in range(len(a) - h):
        out[t] = np.corrcoef(a[t + 1:t + 1 + h], b[t + 1:t + 1 + h])[0, 1]
    return out


def r2(y, pred):
    return 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)


def fit_r2(X, y, disc, val):
    m = LinearRegression().fit(X[disc], y[disc])
    return r2(y[val], m.predict(X[val]))


def main():
    feat = pd.read_csv(os.path.join(PROC, "features.csv"), parse_dates=["Date"]).set_index("Date")
    px = pd.read_csv(os.path.join(PROC, "cross_asset.csv"), parse_dates=["Date"]).set_index("Date")
    rets = px[["SPY", "IEF", "TLT"]].pct_change()
    df = feat.join(rets, how="inner").dropna()
    dates = df.index
    vix, slope, nfci = df["vol_index"].values, df["yield_slope"].values, df["nfci"].values
    spy, ief, tlt = df["SPY"].values, df["IEF"].values, df["TLT"].values
    N = len(df)
    ntr = int((dates <= pd.Timestamp(TRAIN_END)).sum())
    print(f"Aligned N={N} ({dates[0].date()}..{dates[-1].date()}); discovery n={ntr}; validation n={N-ntr}\n")

    for name, bond in (("SPY-IEF", ief), ("SPY-TLT", tlt)):
        Y = fwd_corr(spy, bond, H)
        ok = ~np.isnan(Y)
        print("=" * 74)
        print(f"{name}  |  target = forward {H}d realized correlation")
        print("=" * 74)

        # context: correlation regime over time (the single-episode caveat, made visible)
        yrs = np.array([d.year for d in dates])
        print("  mean forward corr by year (shows the 2022 sign flip = the one transition):")
        for y in sorted(set(yrs)):
            m = ok & (yrs == y)
            if m.sum() > 20:
                print(f"    {y}: {np.nanmean(Y[m]):+.2f}  (n={int(m.sum())})")

        # 2x2 descriptive: does the macro axis move corr WITHIN vol buckets?
        vhi = vix >= np.median(vix)
        shi = slope >= np.median(slope)  # high slope = steep curve
        print("\n  2x2 mean forward corr [vol bucket x curve]  (orthogonality = macro moves it within a vol row):")
        print(f"    {'':<10}{'inverted(loSlope)':>20}{'steep(hiSlope)':>18}{'steep-inv':>12}")
        for vname, vm in (("loVIX", ~vhi & ok), ("hiVIX", vhi & ok)):
            inv = Y[vm & ~shi].mean()
            stp = Y[vm & shi].mean()
            print(f"    {vname:<10}{inv:>20.2f}{stp:>18.2f}{stp - inv:>12.2f}")

        # regression: macro axis beyond vol controls
        C = np.column_stack([vix, vix ** 2])
        CM = np.column_stack([vix, vix ** 2, slope, nfci])
        idx = np.where(ok)[0]
        disc = idx[idx < ntr - H]
        val = idx[idx >= ntr]
        yv = Y
        # in-sample descriptive
        r2c_is = r2(yv[idx], LinearRegression().fit(C[idx], yv[idx]).predict(C[idx]))
        r2cm_is = r2(yv[idx], LinearRegression().fit(CM[idx], yv[idx]).predict(CM[idx]))
        # low-power OOS
        r2c_oos = fit_r2(C, yv, disc, val)
        r2cm_oos = fit_r2(CM, yv, disc, val)
        print(f"\n  in-sample:  R2(vol controls)={r2c_is:+.3f}  R2(+macro axis)={r2cm_is:+.3f}  "
              f"dR2_macro={r2cm_is - r2c_is:+.3f}")
        print(f"  OOS(2024+): R2(vol controls)={r2c_oos:+.3f}  R2(+macro axis)={r2cm_oos:+.3f}  "
              f"dR2_macro={r2cm_oos - r2c_oos:+.3f}   [LOW POWER: ~1 sign regime]\n")

    print("Reminder: exploratory only. A steep-minus-inverted gap that survives WITHIN vol buckets,\n"
          "and an in-sample dR2_macro > 0, is a GO signal to extend data to ~1976 for real validation.")


if __name__ == "__main__":
    main()
