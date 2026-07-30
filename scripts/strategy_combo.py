"""Vol-targeted trend-following vs vol-targeting alone (Adam's 'vol model + momentum model' idea).

The honest test: the oracle showed the reliable structure is risk-scaling (vol) + a trend tilt
(momentum). Combining them = managed-futures-lite. Does adding TREND to VOL-TARGETING actually beat
vol-targeting ALONE, net of costs, on a diversified panel? Comparative, cost-aware, causal (delay=2),
NO weight-optimization (overfitting refused). If trend adds nothing beyond risk-scaling, that's the
project's recurring finding one more time; if it adds, it's a real managed-futures effect.

Construction (long-flat, advisor-appropriate — go to cash when the trend is down, never short):
  per asset i: vol scale v_i = clip(target_vol / EWM-vol_i, 0, 1); trend t_i = 1[trailing 12m ret > 0].
  vol-target-only weight = v_i ;  vol+trend weight = v_i * t_i ;  cash residual earns rf.
Assets: equity + 10y Treasury (+ gold when available). Costs on turnover; delay=2.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_config import maxdd

ANN = 252
TARGET = 0.07          # per-asset vol target (a priori, not optimized)
COST_BPS = 10.0
DELAY = 2


def ewm_vol(r):
    return pd.Series(r).ewm(halflife=20).std() * np.sqrt(ANN)


def portfolio(weights, rets, rf):
    """weights (T x k), rets (T x k), rf (T,). Lag weights DELAY days; cash residual earns rf;
    charge COST_BPS on per-asset turnover. Returns net daily return array."""
    W = np.vstack([np.zeros((DELAY, weights.shape[1])), weights[:-DELAY]])   # causal lag
    gross = (W * rets).sum(axis=1)
    cash = (1.0 - W.sum(axis=1)) * rf
    turn = np.abs(np.diff(W, axis=0, prepend=0.0)).sum(axis=1)
    return gross + cash - turn * COST_BPS * 1e-4


def metrics(ret, rf, name):
    ret = np.asarray(ret)
    eq = np.cumprod(1 + ret)
    ann = eq[-1] ** (ANN / len(ret)) - 1
    vol = ret.std() * np.sqrt(ANN)
    shp = (ret - rf).mean() / ret.std() * np.sqrt(ANN)
    return dict(strategy=name, ann_ret=round(ann, 4), ann_vol=round(vol, 4),
                sharpe=round(shp, 3), max_dd=round(maxdd(ret), 4))


def main():
    d = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    d = d[["mkt_ret", "bond10_ret", "gold_ret", "rf"]].copy()

    for start, cols, tag in [("1962-01-01", ["mkt_ret", "bond10_ret"], "equity+bond 1962+"),
                             ("2000-09-01", ["mkt_ret", "bond10_ret", "gold_ret"], "eq+bond+gold 2000+")]:
        sub = d.loc[start:].dropna(subset=cols + ["rf"])
        R = sub[cols].to_numpy()
        rf = sub["rf"].to_numpy()
        T, k = R.shape

        vscale = np.column_stack([np.clip(TARGET / ewm_vol(R[:, i]), 0, 1.0).fillna(0.0)
                                  for i in range(k)])
        # trend = trailing 12m (252d) cumulative return > 0, long-flat
        cum = pd.DataFrame(R, columns=cols).add(1).rolling(252).apply(np.prod, raw=True) - 1
        trend = (cum > 0).to_numpy().astype(float)
        trend[np.isnan(cum.to_numpy())] = 1.0

        w_vt = vscale / k                              # vol-target only (equal split), cash residual
        w_vtt = vscale * trend / k                     # vol-target + trend
        w_bh = np.full((T, k), 1.0 / k)                # static equal-weight buy&hold

        rows = [metrics(portfolio(w_bh, R, rf), rf, "static_equalwt"),
                metrics(portfolio(w_vt, R, rf), rf, "voltarget_only"),
                metrics(portfolio(w_vtt, R, rf), rf, "voltarget_PLUS_trend")]
        print(f"\n=== {tag} ({sub.index[0].date()}..{sub.index[-1].date()}) ===")
        print(f"{'strategy':24}{'ann ret':>9}{'ann vol':>9}{'Sharpe':>8}{'max DD':>9}")
        for m in rows:
            print(f"{m['strategy']:24}{m['ann_ret']:9.2%}{m['ann_vol']:9.2%}{m['sharpe']:8.2f}{m['max_dd']:9.1%}")
        pd.DataFrame(rows).assign(universe=tag).to_csv(
            ROOT / f"results/strategy_combo_{tag.split()[0].replace('+','_')}.csv", index=False)


if __name__ == "__main__":
    main()
