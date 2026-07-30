"""Phase A2/A3 (PRODUCT-PLAN): does BREADTH (48 vs 10 industries) + BUFFERED construction improve the
momentum sleeve? (QA, no look.)

Adam: use finer sector data. French offers 48-industry daily (same clean pipeline, free, no survivorship
bias) vs our 10. Test whether more breadth (a) lifts Sharpe and (b) diversifies away the -72%
concentration crash. Construction is the research's holdable recipe: 12-1 momentum + skip-month, hold a
diversified top third, INVERSE-VOL weighted, with ASYMMETRIC BUFFERING (enter top-1/3, hold until it
drops below median) to control turnover (AQR). Reports Sharpe / max DD / annual turnover / 2000-09.
A-priori params, no optimization. Caches the 48-industry panel to data/processed/.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_assets import _ff_daily_table
from run_config import maxdd

ANN, COST = 12, 20.0


def load_industry(n):
    cache = ROOT / "data" / "processed" / f"industry{n}_daily.csv"
    if cache.exists():
        return pd.read_csv(cache, index_col=0, parse_dates=True)
    df = _ff_daily_table(f"{n}_Industry_Portfolios_daily_CSV.zip")
    df.to_csv(cache)
    return df


def buffered_momentum(R, rf, enter=0.667, exit_=0.5):
    """Long-only momentum sleeve with asymmetric buffering + inverse-vol weighting. Monthly.
    A name ENTERS the held set when its 12-1 momentum percentile >= enter, and is HELD until the
    percentile falls below exit_. Held names weighted by inverse trailing vol. 20bps on turnover."""
    inds = R.columns
    cum12 = (1 + R).rolling(12).apply(np.prod, raw=True) - 1
    score = ((1 + cum12) / (1 + R) - 1).shift(1)                 # 12-1, skip month, causal
    vol = R.rolling(12).std().shift(1)
    held = set()
    ret, turn, idx = [], [], []
    wp = pd.Series(0.0, index=inds)
    for i, t in enumerate(R.index):
        s = score.iloc[i]
        if s.isna().any() or vol.iloc[i].isna().any():
            continue
        pct = s.rank(pct=True)
        held = {n for n in held if pct[n] >= exit_} | {n for n in inds if pct[n] >= enter}
        iv = (1.0 / vol.iloc[i])[list(held)]
        w = pd.Series(0.0, index=inds)
        if len(held):
            w[list(held)] = (iv / iv.sum()).values
        turn.append(np.abs(w - wp).sum())
        ret.append((w * R.iloc[i]).sum() - turn[-1] * COST * 1e-4 + (1 - w.sum()) * rf.iloc[i])
        wp = w; idx.append(t)
    r = pd.Series(ret, index=idx)
    return r, float(np.mean(turn) * 12)                          # annualized turnover


def perf(ret, rf, name, turn):
    ret = np.asarray(ret); eq = np.cumprod(1 + ret)
    return dict(sleeve=name, ann_ret=round(eq[-1] ** (ANN / len(ret)) - 1, 4),
                sharpe=round((ret - rf).mean() / ret.std() * np.sqrt(ANN), 3),
                max_dd=round(maxdd(ret), 4), ann_turnover=round(turn, 2))


def main():
    rf = ((1 + pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)["rf"])
          .resample("ME").prod() - 1)
    print(f"{'sleeve':22}{'ann ret':>9}{'Sharpe':>8}{'max DD':>9}{'turnover':>10}")
    era_rows = {}
    for n in (10, 48):
        R = load_industry(n)
        m = (1 + R).resample("ME").prod() - 1
        rfc = rf.reindex(m.index)
        r, turn = buffered_momentum(m, rfc)
        common = r.index.intersection(rfc.dropna().index)
        p = perf(r.loc[common], rfc.loc[common].to_numpy(), f"{n}-industry momentum", turn)
        print(f"{p['sleeve']:22}{p['ann_ret']:9.2%}{p['sharpe']:8.2f}{p['max_dd']:9.1%}{p['ann_turnover']:10.1f}x")
        era_rows[n] = r
        pd.DataFrame([p]).to_csv(ROOT / f"results/momentum_breadth_{n}.csv", index=False)

    print("\n2000-09 crash-decade Sharpe (does breadth diversify the crash?):")
    for n, r in era_rows.items():
        seg = r.loc["2000":"2009"]
        print(f"  {n}-industry: {(seg.mean()/seg.std()*np.sqrt(ANN)):.2f}   max DD {maxdd(seg):.1%}")


if __name__ == "__main__":
    main()
