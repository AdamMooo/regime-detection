"""Phase 1 (PRODUCT-PLAN): residual (idiosyncratic) momentum on industries — the crash fix at the root.

Rank industries on 12-1 momentum of the RESIDUALS from a rolling 36m FF3 regression (vol-standardized),
not raw returns. Stripping the market/size/value betas removes the time-varying-beta dynamics that
drive momentum crashes (Blitz-Huij-Martens 2011; Daniel-Moskowitz 2016 on the beta mechanism). Compare
RAW vs RESIDUAL momentum, especially on the 2000-09 crash decade + max drawdown.

GATE: residual momentum reduces the crash-decade loss and/or max DD vs raw, without killing the edge.
A-priori params (36m window, 12-1 skip-month, top/bottom-3, 20bps). No optimization. No look spent.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_config import maxdd

ANN = 12
COST_BPS = 20.0
K = 3
WIN = 36               # FF3 regression window (months)


def perf(ret, rf, name):
    ret = np.asarray(ret)
    eq = np.cumprod(1 + ret)
    ann = eq[-1] ** (ANN / len(ret)) - 1
    vol = ret.std() * np.sqrt(ANN)
    shp = (ret - rf).mean() / ret.std() * np.sqrt(ANN) if ret.std() > 0 else 0.0
    return dict(strategy=name, ann_ret=round(ann, 4), ann_vol=round(vol, 4),
                sharpe=round(shp, 3), max_dd=round(maxdd(ret), 4))


def rolling_ff3_residuals(exret, F):
    """For each asset (col of exret, T x N excess returns), rolling WIN-month FF3 regression;
    return the standardized residual return at each month t (residual_t / trailing residual vol).
    Causal: month t uses the regression fit on [t-WIN, t-1]."""
    T, N = exret.shape
    Xall = np.column_stack([np.ones(T), F])            # const + mkt,smb,hml
    resid = np.full((T, N), np.nan)
    for t in range(WIN, T):
        Xtr = Xall[t - WIN:t]
        for j in range(N):
            y = exret[t - WIN:t, j]
            b, *_ = np.linalg.lstsq(Xtr, y, rcond=None)
            fitted = Xall[t] @ b
            resid[t, j] = exret[t, j] - fitted         # this month's residual vs prior-window betas
    rdf = pd.DataFrame(resid)
    rstd = rdf.rolling(WIN, min_periods=12).std()
    return (rdf / rstd)                                # standardized residual returns


def momentum_returns(score, R, rf, label):
    """Long-only momentum tilt + WML from a monthly `score` (T x N, higher = winner). Causal:
    score at t-1 trades at t. 20bps turnover cost. Returns (perf_lo, perf_wml, monthly_series)."""
    inds = R.columns
    lo_ret, wml_ret = [], []
    wl_p = ws_p = wlo_p = None
    idx = []
    sig = score.shift(1)
    for i, t in enumerate(R.index):
        s = sig.iloc[i]
        if s.isna().any():
            continue
        order = s.rank()
        longs = order[order > len(inds) - K].index
        shorts = order[order <= K].index
        wl = pd.Series(0.0, index=inds); wl[longs] = 1.0 / K
        ws = pd.Series(0.0, index=inds); ws[shorts] = 1.0 / K
        wlo = pd.Series(1.0 / len(inds), index=inds)
        wlo[longs] += 0.5 / K; wlo[shorts] -= 0.5 / K
        wlo = wlo.clip(lower=0); wlo /= wlo.sum()
        r_t = R.iloc[i]
        c = lambda w, wp: 0.0 if wp is None else np.abs(w - wp).sum() * COST_BPS * 1e-4
        wml_ret.append((wl * r_t).sum() - (ws * r_t).sum() - c(wl, wl_p) - c(ws, ws_p))
        lo_ret.append((wlo * r_t).sum() - c(wlo, wlo_p))
        wl_p, ws_p, wlo_p = wl, ws, wlo
        idx.append(t)
    return (pd.Series(lo_ret, index=idx), pd.Series(wml_ret, index=idx))


def main():
    d = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    inds = [c for c in d.columns if c.startswith("ind_")]
    m = (1 + d[inds + ["mkt_ret", "rf", "smb", "hml"]]).resample("ME").prod() - 1
    R = m[inds]
    rf = m["rf"]
    F = m[["mkt_ret", "smb", "hml"]].to_numpy()        # mkt is excess-ish; fine for residualization
    exret = R.sub(rf, axis=0).to_numpy()

    # RAW 12-1 momentum score
    cum12 = (1 + R).rolling(12).apply(np.prod, raw=True) - 1
    raw_score = ((1 + cum12) / (1 + R) - 1)            # skip most recent month

    # RESIDUAL momentum score: cumulate standardized residuals over t-12..t-2
    res = rolling_ff3_residuals(exret, F)
    res.index = R.index; res.columns = inds
    res_score = res.rolling(11).sum().shift(1)          # 11 months (t-12..t-2), then shift handled in mom fn
    res_score.index = R.index

    lo_raw, wml_raw = momentum_returns(raw_score, R, rf, "raw")
    lo_res, wml_res = momentum_returns(res_score, R, rf, "residual")

    common = lo_raw.index.intersection(lo_res.index)
    rf_c = rf.loc[common].to_numpy()
    rows = [perf(lo_raw.loc[common], rf_c, "raw_mom_long_only"),
            perf(lo_res.loc[common], rf_c, "residual_mom_long_only"),
            perf(wml_raw.loc[common], np.zeros(len(common)), "raw_WML"),
            perf(wml_res.loc[common], np.zeros(len(common)), "residual_WML")]
    print(f"RESIDUAL vs RAW MOMENTUM ({common[0].date()}..{common[-1].date()}, {len(common)} months, "
          f"{len(inds)} industries, {WIN}m FF3, {COST_BPS:.0f}bps)")
    print(f"{'strategy':26}{'ann ret':>9}{'ann vol':>9}{'Sharpe':>8}{'max DD':>9}")
    for r in rows:
        print(f"{r['strategy']:26}{r['ann_ret']:9.2%}{r['ann_vol']:9.2%}{r['sharpe']:8.2f}{r['max_dd']:9.1%}")

    print("\nCRASH-DECADE CHECK — WML Sharpe by era (does residual tame 2000-09?):")
    print(f"{'era':16}{'raw_WML':>10}{'resid_WML':>12}")
    for lab, a, b in [("pre-1970", "1927", "1969"), ("1970-1999", "1970", "1999"),
                      ("2000-2009", "2000", "2009"), ("2010-now", "2010", "2026")]:
        sr = perf(wml_raw.loc[a:b], np.zeros(len(wml_raw.loc[a:b])), "")["sharpe"] if len(wml_raw.loc[a:b]) else float("nan")
        se = perf(wml_res.loc[a:b], np.zeros(len(wml_res.loc[a:b])), "")["sharpe"] if len(wml_res.loc[a:b]) else float("nan")
        print(f"{lab:16}{sr:10.2f}{se:12.2f}")
    pd.DataFrame(rows).to_csv(ROOT / "results/residual_momentum.csv", index=False)


if __name__ == "__main__":
    main()
