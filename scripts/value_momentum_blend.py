"""Phase 2 (PRODUCT-PLAN): value + momentum blend — the structural crash fix (Asness-Moskowitz-Pedersen).

Value and momentum are negatively correlated; value wins exactly when momentum crashes (the bear-market
rebound is a value/junk rally), so a value sleeve offsets the momentum crash STRUCTURALLY (not fitted).
The research bottom-line: the holdable product is the COMBINATION, not standalone momentum.

Value signal (industry-level, breadth-independent): long-term REVERSAL (DeBondt-Thaler) as the value
proxy — past 60-to-13-month return; CHEAP = low past long-term return. Momentum = 12-1 raw (residual
didn't transfer on 10 industries, Phase 1). Blend = 50/50 of the two long-only tilts (AMP combination).
A-priori params, no optimization, no look. GATE: the blend's 2000-09 decade + max DD become holdable.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_config import maxdd

ANN, COST_BPS, K = 12, 20.0, 3


def perf(ret, rf, name):
    ret = np.asarray(ret)
    eq = np.cumprod(1 + ret)
    return dict(strategy=name, ann_ret=round(eq[-1] ** (ANN / len(ret)) - 1, 4),
                ann_vol=round(ret.std() * np.sqrt(ANN), 4),
                sharpe=round((ret - rf).mean() / ret.std() * np.sqrt(ANN), 3) if ret.std() > 0 else 0.0,
                max_dd=round(maxdd(ret), 4))


def long_only(score, R):
    """Long-only tilt from a monthly score (higher=preferred), causal (t-1 trades t), 20bps turnover."""
    inds = R.columns
    out, wp, idx = [], None, []
    sig = score.shift(1)
    for i, t in enumerate(R.index):
        s = sig.iloc[i]
        if s.isna().any():
            continue
        order = s.rank()
        longs, shorts = order[order > len(inds) - K].index, order[order <= K].index
        w = pd.Series(1.0 / len(inds), index=inds)
        w[longs] += 0.5 / K; w[shorts] -= 0.5 / K
        w = w.clip(lower=0); w /= w.sum()
        cost = 0.0 if wp is None else np.abs(w - wp).sum() * COST_BPS * 1e-4
        out.append((w * R.iloc[i]).sum() - cost); wp = w; idx.append(t)
    return pd.Series(out, index=idx)


def main():
    d = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    inds = [c for c in d.columns if c.startswith("ind_")]
    m = (1 + d[inds + ["rf"]]).resample("ME").prod() - 1
    R, rf = m[inds], m["rf"]

    cum12 = (1 + R).rolling(12).apply(np.prod, raw=True) - 1
    mom_score = (1 + cum12) / (1 + R) - 1                       # 12-1 momentum
    cum60 = (1 + R).rolling(60).apply(np.prod, raw=True) - 1
    cum13 = (1 + R).rolling(13).apply(np.prod, raw=True) - 1
    val_score = -((1 + cum60) / (1 + cum13) - 1)               # value = low past 60-13m return (LT reversal)

    mom = long_only(mom_score, R)
    val = long_only(val_score, R)
    ew = R.mean(axis=1)
    common = mom.index.intersection(val.index)
    blend = 0.5 * mom.loc[common] + 0.5 * val.loc[common]
    rf_c = rf.loc[common].to_numpy()

    rows = [perf(ew.loc[common], rf_c, "EW_market"),
            perf(mom.loc[common], rf_c, "momentum_only"),
            perf(val.loc[common], rf_c, "value_only"),
            perf(blend, rf_c, "value+mom_blend")]
    print(f"VALUE + MOMENTUM BLEND ({common[0].date()}..{common[-1].date()}, {len(common)} months, "
          f"{len(inds)} industries)")
    print(f"{'strategy':22}{'ann ret':>9}{'ann vol':>9}{'Sharpe':>8}{'max DD':>9}")
    for r in rows:
        print(f"{r['strategy']:22}{r['ann_ret']:9.2%}{r['ann_vol']:9.2%}{r['sharpe']:8.2f}{r['max_dd']:9.1%}")
    print(f"\ncorr(momentum, value) monthly: {mom.loc[common].corr(val.loc[common]):+.2f}  "
          f"(negative => structural crash offset)")

    print("\nCRASH-DECADE CHECK — Sharpe by era:")
    print(f"{'era':16}{'mom':>8}{'value':>8}{'blend':>8}")
    for lab, a, b in [("pre-1970", "1927", "1969"), ("1970-1999", "1970", "1999"),
                      ("2000-2009", "2000", "2009"), ("2010-now", "2010", "2026")]:
        seg_m, seg_v, seg_b = mom.loc[a:b], val.loc[a:b], blend.loc[a:b]
        f = lambda s: perf(s, np.zeros(len(s)), "")["sharpe"] if len(s) else float("nan")
        print(f"{lab:16}{f(seg_m):8.2f}{f(seg_v):8.2f}{f(seg_b):8.2f}")
    pd.DataFrame(rows).to_csv(ROOT / "results/value_momentum_blend.csv", index=False)


if __name__ == "__main__":
    main()
