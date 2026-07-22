#!/usr/bin/env python3
"""Stage 2 (first cut): does a SIMPLE CAUSAL CONTINUOUS stress/macro environment
coordinate condition cross-asset behavior -- incrementally over the raw features?

Per the established verdict, the environment is represented continuously (not by the
rejected HMM estimator): EWMA(span 10, causal) of the standardized macro features ->
  stress axis = smoothed (VIX + NFCI)   [risk/vol/financial-stress level]
  macro  axis = smoothed yield_slope    [rate / curve / cycle regime]

Discipline (the whole point): a smoothed 'environment' is a function of the feature
history, so it must EARN its keep by conditioning cross-asset behavior BEYOND the raw
contemporaneous features. For each asset property we compare, OOS (fit 2016-2023, score
2024-2026):
  R2_raw   = property ~ raw contemporaneous features {VIX, slope, NFCI, spy_ret}
  R2_both  = property ~ raw + env coordinate
  incremental = R2_both - R2_raw   (> 0 => the persistent env representation adds value)

Pre-specified (NOT fished): forward 21d return and forward 21d vol for a basket spanning
the two axes -- equity SPY, duration IEF/TLT, credit HYG/LQD, haven GLD, style IWF/IWD --
plus the growth-value spread and the SPY-bond correlation (the rate-regime hypothesis).

Reads  : data/processed/features.csv  (+ yfinance for the cross-asset basket, cached)
Writes : data/processed/cross_asset.csv, results/stage2_conditioning.csv
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

from src.config import FEATURES, TRAIN_END, DATA_DIR, RESULTS_DIR

TICKERS = ["SPY", "IEF", "TLT", "HYG", "LQD", "GLD", "IWF", "IWD"]
H = 21
CACHE = os.path.join(DATA_DIR, "processed", "cross_asset.csv")


def load_cross_asset(index):
    if os.path.exists(CACHE):
        px = pd.read_csv(CACHE, parse_dates=["Date"]).set_index("Date")
        print(f"Loaded cached cross-asset prices {CACHE}")
    else:
        import yfinance as yf
        print(f"Fetching {TICKERS} via yfinance ...")
        raw = yf.download(TICKERS, start="2015-06-01", end="2026-07-22",
                          auto_adjust=True, progress=False)["Close"]
        px = raw.dropna(how="all")
        px.index.name = "Date"
        px.to_csv(CACHE)
        print(f"Cached -> {CACHE}")
    ret = np.log(px).diff().reindex(index)
    return ret[TICKERS]


def fwd_ret(r, h):
    return pd.Series(r).rolling(h).sum().shift(-h).values


def fwd_vol(r, h):
    return (pd.Series(r).rolling(h).std().shift(-h) * np.sqrt(252) * 100).values


def oos_r2(target, Xtr_cols, tr, te):
    """OOS R2 for target ~ columns, fit on tr, scored on te. NaN-safe."""
    y = target
    X = np.column_stack(Xtr_cols)
    m = np.isfinite(y) & np.isfinite(X).all(1)
    tr_, te_ = tr & m, te & m
    if tr_.sum() < 50 or te_.sum() < 30:
        return np.nan
    lr = LinearRegression().fit(X[tr_], y[tr_])
    return lr.score(X[te_], y[te_])


def main():
    feat = pd.read_csv(os.path.join(DATA_DIR, "processed", "features.csv"),
                       parse_dates=["Date"]).set_index("Date")
    idx = feat.index
    F = {c: feat[c].values for c in FEATURES}

    # ---- simple causal continuous environment coordinate ----
    sm = feat[FEATURES].ewm(span=10).mean()
    stress = 0.5 * (sm["vol_index"] + sm["nfci"]).values
    macro = sm["yield_slope"].values
    print(f"Env coordinate built (EWMA span 10). stress & macro; "
          f"corr(stress,macro)={np.corrcoef(stress,macro)[0,1]:+.2f}\n")

    ret = load_cross_asset(idx)
    tr = np.asarray(idx <= pd.Timestamp(TRAIN_END))
    te = np.asarray(idx > pd.Timestamp(TRAIN_END))

    raw_cols = [F[c] for c in FEATURES]
    env_cols = [stress, macro]

    # derived series
    gmv = (ret["IWF"] - ret["IWD"]).values          # growth minus value
    assets = {t: ret[t].values for t in TICKERS}
    assets["GmV(growth-value)"] = gmv

    # ---- incremental value test, OOS ----
    print("Incremental OOS value of the env coordinate over raw features")
    print(f"{'asset':<18}{'property':<10}{'R2_raw':>9}{'R2_both':>9}{'ΔR2_env':>9}")
    print("-" * 55)
    rows = []
    for name, r in assets.items():
        for prop, fn in (("fwd_ret", fwd_ret), ("fwd_vol", fwd_vol)):
            y = fn(r, H)
            r2raw = oos_r2(y, raw_cols, tr, te)
            r2both = oos_r2(y, raw_cols + env_cols, tr, te)
            inc = r2both - r2raw if np.isfinite(r2raw) and np.isfinite(r2both) else np.nan
            print(f"{name:<18}{prop:<10}{r2raw:>9.3f}{r2both:>9.3f}{inc:>+9.3f}")
            rows.append({"asset": name, "property": prop, "r2_raw": r2raw,
                         "r2_both": r2both, "dr2_env": inc})

    # ---- descriptive env-map: forward 21d return by stress / macro tertile (full sample) ----
    def tercile(z):
        q = np.nanquantile(z, [1/3, 2/3])
        return np.digitize(z, q)
    st, mt = tercile(stress), tercile(macro)
    print("\nMean forward-21d return (%), by STRESS tertile  [risk-axis hypothesis]")
    print(f"{'asset':<18}{'low':>8}{'mid':>8}{'high':>8}")
    for name, r in assets.items():
        y = fwd_ret(r, H) * 100
        print(f"{name:<18}" + "".join(f"{np.nanmean(y[st==b]):>8.2f}" for b in range(3)))
    print("\nMean forward-21d return (%), by MACRO tertile  [rate/curve-axis hypothesis]")
    print(f"{'asset':<18}{'low(inv)':>9}{'mid':>8}{'high(steep)':>12}")
    for name, r in assets.items():
        y = fwd_ret(r, H) * 100
        print(f"{name:<18}" + "".join(f"{np.nanmean(y[mt==b]):>{9 if b==0 else (8 if b==1 else 12)}.2f}"
                                       for b in range(3)))

    # ---- rate-regime hypothesis: SPY-bond correlation vs macro axis ----
    win = 63
    sb = pd.Series(ret["SPY"].values).rolling(win).corr(pd.Series(ret["IEF"].values)).values
    ok = np.isfinite(sb) & np.isfinite(macro)
    print(f"\nStock-bond (SPY~IEF, {win}d) correlation vs macro axis:")
    print(f"  corr(rolling SPY-IEF corr, macro) = {np.corrcoef(sb[ok], macro[ok])[0,1]:+.3f}")
    print(f"  mean SPY-IEF corr by macro tertile: " +
          "  ".join(f"{lbl}={np.nanmean(sb[mt==b]):+.2f}"
                    for b, lbl in zip(range(3), ("inv", "mid", "steep"))))

    pd.DataFrame(rows).to_csv(os.path.join(RESULTS_DIR, "stage2_conditioning.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'stage2_conditioning.csv')}")


if __name__ == "__main__":
    main()
