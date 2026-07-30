"""Dynamic (reactive-covariance) allocation across equity-sleeve / bonds / cash (Adam 2026-07-30).

Fixes the static 60/40's fatal assumption that bonds always diversify equities (false in 2022, and
pre-2000). Uses a TRAILING (reactive) covariance of [equity-momentum-sleeve, bond] to form a long-only
MINIMUM-VARIANCE mix, then VOL-TARGETS it with a cash residual. Mechanism:
  - the covariance CONTAINS the stock-bond correlation (no forecasting — that macro axis is killed,
    [[stockbond-macro-stage1]]; this only REACTS, which is what wins in this project);
  - when corr spikes positive and both are volatile (2022), the min-var portfolio's own vol jumps ->
    the vol-target scales exposure DOWN into cash. "No point holding both -> go to cash," automatically.

Compares vs the static 60/40 vol-target (prior product), full window AND the 2020-2026 window that
contains the 2022 stock-bond crash. Shows the trailing stock-bond correlation so we can see it work.
A-priori params (24m cov, 10% vol target). No optimization. No look.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_config import maxdd
from compare_vs_jm import mom_tilt

ANN, COV_WIN, TARGET = 12, 24, 0.10


def perf(ret, rf, name):
    ret = np.asarray(ret); eq = np.cumprod(1 + ret)
    return dict(strategy=name, ann_ret=round(eq[-1] ** (ANN / len(ret)) - 1, 4),
                ann_vol=round(ret.std() * np.sqrt(ANN), 4),
                sharpe=round((ret - rf).mean() / ret.std() * np.sqrt(ANN), 3) if ret.std() > 0 else 0.0,
                max_dd=round(maxdd(ret), 4))


def minvar_w(cov):
    try:
        inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        return np.array([0.5, 0.5])
    w = inv @ np.ones(2)
    w = np.clip(w / w.sum(), 0, 1)                    # long-only
    return w / w.sum() if w.sum() > 0 else np.array([0.5, 0.5])


def main():
    d = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    inds = [c for c in d.columns if c.startswith("ind_")]
    m = (1 + d[inds + ["bond10_ret", "rf"]]).resample("ME").prod() - 1
    eq = mom_tilt(m[inds])                             # equity momentum sleeve
    idx = eq.index.intersection(m.index)
    A = pd.DataFrame({"eq": eq.loc[idx], "bond": m["bond10_ret"].loc[idx]})
    rf = m["rf"].loc[idx]

    corr = A["eq"].rolling(COV_WIN).corr(A["bond"])
    dyn, w_hist = [], []
    for i, t in enumerate(A.index):
        if i < COV_WIN:
            dyn.append(np.nan); w_hist.append((np.nan, np.nan, np.nan)); continue
        win = A.iloc[i - COV_WIN:i]                   # strictly prior window (causal)
        w = minvar_w(win.cov().to_numpy())
        pv = np.sqrt(w @ win.cov().to_numpy() @ w) * np.sqrt(ANN)   # min-var portfolio vol
        scale = min(TARGET / pv, 1.0) if pv > 0 else 0.0            # vol-target -> cash residual
        r_t = A.iloc[i]
        dyn.append(scale * (w @ r_t.to_numpy()) + (1 - scale) * rf.iloc[i])
        w_hist.append((w[0] * scale, w[1] * scale, 1 - scale))      # eq, bond, cash exposures

    dyn = pd.Series(dyn, index=A.index)
    W = pd.DataFrame(w_hist, index=A.index, columns=["eq", "bond", "cash"])

    # TREND-GATED: hold each sleeve only while its trailing 12m return > 0 (else that sleeve -> cash),
    # inverse-vol weighted, then vol-targeted. A per-asset "is it working NOW" signal, faster than corr.
    tg, tgw = [], []
    for i, t in enumerate(A.index):
        if i < 12:
            tg.append(np.nan); tgw.append((np.nan, np.nan, np.nan)); continue
        look = A.iloc[i - 12:i]
        trend = ((1 + look).prod() - 1) > 0
        vol = look.std() * np.sqrt(ANN)
        raw = (1.0 / vol) * trend.astype(float)
        w = raw / raw.sum() if raw.sum() > 0 else pd.Series([0.0, 0.0], index=A.columns)
        pv = np.sqrt(w.to_numpy() @ look.cov().to_numpy() @ w.to_numpy()) * np.sqrt(ANN) if raw.sum() > 0 else 0.0
        scale = min(TARGET / pv, 1.0) if pv > 0 else 0.0
        r_t = A.iloc[i]
        tg.append(scale * (w @ r_t) + (1 - scale) * rf.iloc[i])
        tgw.append((w["eq"] * scale, w["bond"] * scale, 1 - scale))
    tg = pd.Series(tg, index=A.index)
    TGW = pd.DataFrame(tgw, index=A.index, columns=["eq", "bond", "cash"])

    # static 60/40 vol-target (prior product) for comparison
    base = 0.6 * A["eq"] + 0.4 * A["bond"]
    bvol = (base.rolling(6).std() * np.sqrt(ANN)).shift(1)
    bw = (TARGET / bvol).clip(0, 1).fillna(0)
    static = bw * base + (1 - bw) * rf

    for lab, a, b in [("FULL 1992+", "1900", "2100"), ("2020-2026 (incl 2022 crash)", "2020", "2026")]:
        seg = slice(a, b)
        common = dyn.loc[seg].dropna().index.intersection(static.loc[seg].dropna().index).intersection(tg.loc[seg].dropna().index)
        rfc = rf.loc[common].to_numpy()
        print(f"\n=== {lab} ({common[0].date()}..{common[-1].date()}, {len(common)}m) ===")
        print(f"{'strategy':26}{'ann ret':>9}{'ann vol':>9}{'Sharpe':>8}{'max DD':>9}")
        for r in [perf(static.loc[common], rfc, "static_6040_VT"),
                  perf(dyn.loc[common], rfc, "dynamic_minvar_VT"),
                  perf(tg.loc[common], rfc, "trend_gated_VT")]:
            print(f"{r['strategy']:26}{r['ann_ret']:9.2%}{r['ann_vol']:9.2%}{r['sharpe']:8.2f}{r['max_dd']:9.1%}")

    print(f"\nstock-bond corr: 2010s avg {corr.loc['2010':'2019'].mean():+.2f}  "
          f"2022 {corr.loc['2022'].mean():+.2f}  latest {corr.dropna().iloc[-1]:+.2f}")
    print(f"dynamic avg exposure — eq {W['eq'].mean():.0%}  bond {W['bond'].mean():.0%}  cash {W['cash'].mean():.0%}")
    print(f"minvar exposure in 2022 — eq {W.loc['2022','eq'].mean():.0%}  bond {W.loc['2022','bond'].mean():.0%}  cash {W.loc['2022','cash'].mean():.0%}")
    print(f"trend-gated exposure in 2022 — eq {TGW.loc['2022','eq'].mean():.0%}  bond {TGW.loc['2022','bond'].mean():.0%}  cash {TGW.loc['2022','cash'].mean():.0%}")
    dyn.to_frame("minvar_ret").join(tg.to_frame("trendgated_ret")).to_csv(ROOT / "results/dynamic_allocation.csv")


if __name__ == "__main__":
    main()
