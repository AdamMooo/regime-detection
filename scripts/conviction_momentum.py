"""Phase A2+ (PRODUCT-PLAN): conviction weighting + confidence modeling (Adam 2026-07-30).

Question: concentrate bets when confidence is high — and does it help or just add drawdown? Grinold-Kahn:
active weight proportional to signal / risk. But concentration FIGHTS the breadth that just tamed the
crash, so this is a TRADEOFF to measure, not a free win.

Three long-only 48-industry sleeves, monthly, 20bps, causal:
  diversified   top-third by momentum, inverse-vol weighted (the breadth baseline)
  conviction    weight ∝ max(momentum z-score, 0) / vol  — concentrate on strong signals (Grinold-Kahn)
  convict+conf  conviction ADDITIONALLY scaled by CONFIDENCE = consistency ("frog-in-the-pan",
                Da-Gurun-Warachka 2014: continuous trends more reliable than jumpy ones). ID =
                sign(PRET)·(%down − %up) days; confidence = −ID (high = smooth/continuous).

Reports Sharpe / max DD / effective-N (concentration) / turnover. Honest tradeoff, a-priori, no opt.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_config import maxdd

ANN, COST = 12, 20.0


def perf(ret, rf, name, effn, turn):
    ret = np.asarray(ret); eq = np.cumprod(1 + ret)
    return dict(sleeve=name, ann_ret=round(eq[-1] ** (ANN / len(ret)) - 1, 4),
                sharpe=round((ret - rf).mean() / ret.std() * np.sqrt(ANN), 3),
                max_dd=round(maxdd(ret), 4), eff_N=round(effn, 1), turnover=round(turn, 2))


def run(R, rf, daily, mode):
    """mode in {diversified, conviction, convict_conf}. R monthly, daily = daily returns (for FIP)."""
    inds = R.columns
    cum12 = (1 + R).rolling(12).apply(np.prod, raw=True) - 1
    score = ((1 + cum12) / (1 + R) - 1).shift(1)
    z = score.sub(score.mean(axis=1), axis=0).div(score.std(axis=1), axis=0)
    vol = R.rolling(12).std().shift(1)
    # confidence: frog-in-the-pan info discreteness on daily returns over ~12m, sampled at month-ends
    pos = (daily > 0).rolling(252).mean()
    cr = (1 + daily).rolling(252).apply(np.prod, raw=True) - 1
    ID = np.sign(cr) * ((1 - pos) - pos)                     # in [-1,1]; low/neg = continuous
    conf = (-ID).reindex(R.index, method="ffill").clip(lower=0) + 0.1   # >0, high = smooth

    ret, effn, turn, idx = [], [], [], []
    wp = pd.Series(0.0, index=inds)
    for i, t in enumerate(R.index):
        s, zz, vv = score.iloc[i], z.iloc[i], vol.iloc[i]
        if s.isna().any() or vv.isna().any():
            continue
        if mode == "diversified":
            top = s.rank(pct=True) >= 0.667
            raw = (1.0 / vv) * top.astype(float)
        else:
            raw = np.maximum(zz, 0) / vv                     # conviction: signal/risk, long-only
            if mode == "convict_conf":
                raw = raw * conf.iloc[i]
        w = raw / raw.sum() if raw.sum() > 0 else pd.Series(1.0 / len(inds), index=inds)
        turn.append(np.abs(w - wp).sum())
        ret.append((w * R.iloc[i]).sum() - turn[-1] * COST * 1e-4)
        effn.append(1.0 / (w ** 2).sum()); wp = w; idx.append(t)
    r = pd.Series(ret, index=idx)
    return r, np.mean(effn), np.mean(turn) * 12


def main():
    R48 = pd.read_csv(ROOT / "data/processed/industry48_daily.csv", index_col=0, parse_dates=True)
    rf = ((1 + pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)["rf"])
          .resample("ME").prod() - 1)
    m = (1 + R48).resample("ME").prod() - 1

    print(f"48-industry sleeves ({m.index[0].date()}..{m.index[-1].date()})")
    print(f"{'sleeve':16}{'ann ret':>9}{'Sharpe':>8}{'max DD':>9}{'eff_N':>8}{'turnover':>10}")
    rows = []
    for mode, name in [("diversified", "diversified"), ("conviction", "conviction"),
                       ("convict_conf", "convict+conf")]:
        r, effn, turn = run(m, rf, R48, mode)
        common = r.index.intersection(rf.dropna().index)
        p = perf(r.loc[common], rf.loc[common].to_numpy(), name, effn, turn)
        rows.append(p)
        print(f"{p['sleeve']:16}{p['ann_ret']:9.2%}{p['sharpe']:8.2f}{p['max_dd']:9.1%}"
              f"{p['eff_N']:8.1f}{p['turnover']:10.1f}x")
        # crash decade
        seg = r.loc["2000":"2009"]
        print(f"{'':16}   2000-09 Sharpe {seg.mean()/seg.std()*np.sqrt(ANN):+.2f}  DD {maxdd(seg):.1%}")
    pd.DataFrame(rows).to_csv(ROOT / "results/conviction_momentum.csv", index=False)


if __name__ == "__main__":
    main()
