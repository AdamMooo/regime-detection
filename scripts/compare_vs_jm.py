"""Head-to-head: does the momentum approach beat the JUMP-MODEL strategy? (QA, no look — same window.)

Compares, over the JM label's window (1990+), monthly, cost-aware:
  BH_equity       buy & hold the market
  JM_overlay      the Chapter-1 jump-model strategy: hold equity when calm (state 0), cash when stressed
  voltarget       market scaled by trailing vol to a target (the reactive baseline that beat JM in Ch1)
  momentum_tilt   long-only 12-1 industry cross-sectional momentum (the alpha sleeve)
  mom_in_6040VT   momentum sleeve (60%) + bonds (40%), vol-targeted = the assembled product sketch
Metrics an advisor feels: ann ret, vol, Sharpe, max drawdown. Honest, same period for all.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_config import maxdd

ANN, COST, K = 12, 20.0, 3


def perf(ret, rf, name):
    ret = np.asarray(ret); eq = np.cumprod(1 + ret)
    return dict(strategy=name, ann_ret=round(eq[-1] ** (ANN / len(ret)) - 1, 4),
                ann_vol=round(ret.std() * np.sqrt(ANN), 4),
                sharpe=round((ret - rf).mean() / ret.std() * np.sqrt(ANN), 3) if ret.std() > 0 else 0.0,
                max_dd=round(maxdd(ret), 4))


def mom_tilt(R):
    inds = R.columns
    cum12 = (1 + R).rolling(12).apply(np.prod, raw=True) - 1
    score = ((1 + cum12) / (1 + R) - 1).shift(1)
    out, wp, idx = [], None, []
    for i, t in enumerate(R.index):
        s = score.iloc[i]
        if s.isna().any():
            continue
        order = s.rank(); longs, shorts = order[order > len(inds) - K].index, order[order <= K].index
        w = pd.Series(1.0 / len(inds), index=inds); w[longs] += 0.5 / K; w[shorts] -= 0.5 / K
        w = w.clip(lower=0); w /= w.sum()
        c = 0.0 if wp is None else np.abs(w - wp).sum() * COST * 1e-4
        out.append((w * R.iloc[i]).sum() - c); wp = w; idx.append(t)
    return pd.Series(out, index=idx)


def main():
    d = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    inds = [c for c in d.columns if c.startswith("ind_")]
    m = (1 + d[inds + ["mkt_ret", "bond10_ret", "rf"]]).resample("ME").prod() - 1
    reg = pd.read_csv(ROOT / "data/processed/regime_monthly.csv", index_col=0, parse_dates=True)
    state = reg["state_eom"].reindex(m.index)          # JM monthly state (1990+)

    mom = mom_tilt(m[inds])
    idx = mom.index.intersection(state.dropna().index)  # common window (JM exists + momentum formed)
    mkt, bond, rf = m["mkt_ret"].loc[idx], m["bond10_ret"].loc[idx], m["rf"].loc[idx]
    st = state.loc[idx].shift(1).fillna(0)              # trade next month on last month's state (causal)
    mom = mom.loc[idx]

    # JM overlay: equity when calm else cash, cost on switches
    jm_w = (st == 0).astype(float)
    jm_ret = jm_w * mkt + (1 - jm_w) * rf - jm_w.diff().abs().fillna(0) * COST * 1e-4
    # vol-target market
    vs = (mkt.rolling(6).std() * np.sqrt(ANN)).shift(1)
    vw = (0.15 / vs).clip(0, 1).fillna(0)
    vt_ret = vw * mkt + (1 - vw) * rf
    # momentum sleeve inside a vol-targeted 60/40 (the assembled product sketch)
    base = 0.6 * mom + 0.4 * bond
    bs = (base.rolling(6).std() * np.sqrt(ANN)).shift(1)
    bw = (0.10 / bs).clip(0, 1).fillna(0)
    prod_ret = bw * base + (1 - bw) * rf

    rfn = rf.to_numpy()
    rows = [perf(mkt, rfn, "BH_equity"), perf(jm_ret, rfn, "JM_overlay"),
            perf(vt_ret, rfn, "voltarget_equity"), perf(mom, rfn, "momentum_tilt"),
            perf(prod_ret, rfn, "mom_in_6040VT (product)")]
    print(f"HEAD-TO-HEAD ({idx[0].date()}..{idx[-1].date()}, {len(idx)} months)")
    print(f"{'strategy':26}{'ann ret':>9}{'ann vol':>9}{'Sharpe':>8}{'max DD':>9}")
    for r in rows:
        print(f"{r['strategy']:26}{r['ann_ret']:9.2%}{r['ann_vol']:9.2%}{r['sharpe']:8.2f}{r['max_dd']:9.1%}")
    pd.DataFrame(rows).to_csv(ROOT / "results/compare_vs_jm.csv", index=False)


if __name__ == "__main__":
    main()
