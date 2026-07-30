"""Oracle / in-sample-optimal exposure diagnostic (Adam 2026-07-30).

DELIBERATELY OVERFIT, ON PURPOSE. Compute the best-possible equity exposure conditional on each
regime cell (perfect knowledge of that cell's in-sample return distribution), to see whether the
optimal policy has LEARNABLE STRUCTURE. This is a hypothesis generator + an upper bound, NOT a
strategy: any structure found must be confirmed by a CAUSAL out-of-sample test before it is believed
or deployed. No look is "spent" in the prereg sense because we make no OOS claim here.

The mean-variance optimal exposure per cell is w* = mu / (gamma * sigma^2). It decomposes into:
  - the SIGMA^2 part  -> scale down in volatile regimes = vol-targeting = reliable, already captured;
  - the MU part       -> a return/drift tilt per regime = the timing signal this project keeps killing.
So this diagnostic answers: is the best move just inverse-vol in disguise, or is there real drift
structure beyond risk-scaling?

CELLS = TREND (SMA200 up/down) x TURBULENCE SEVERITY (downside-vol percentile terciles). The JUMP
MODEL IS DELIBERATELY REMOVED from the analytical side (2026-07-30, Adam): it is a mediocre detector
(a dumb vol threshold beats it) so it has no business defining the exposure cells — its only honest
role is the stable CLIENT-COMMUNICATION label, not the strategy signal. Turbulence here = the good
vol measure (downside semivariance percentile), trend = the one orthogonal directional axis.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from regime_read import build

ANN = 252


def main():
    df = build().copy()
    # daily excess equity return and its FORWARD 21d realized path (the thing exposure is chosen for)
    d = pd.read_csv(ROOT / "data/processed/market_daily.csv", index_col=0, parse_dates=True)
    df["ex"] = (d["mkt_ret"] - d["rf"]).reindex(df.index)
    df = df.dropna(subset=["ex", "turb_pct", "trend_down"])

    df["trend"] = np.where(df["trend_down"] > 0.5, "down", "up")
    df["sev"] = pd.cut(df["turb_pct"], [0, .6, .8, 1.01], labels=["low", "high", "extreme"])

    print("=" * 100)
    print("ORACLE EXPOSURE — turbulence x trend (NO jump model) — decompose risk (sigma) vs drift (mu)")
    print("=" * 100)
    print(f"{'cell (trend / turbulence)':40}{'days':>6}{'ann mu':>9}{'ann vol':>9}{'Sharpe':>8}{'w*(mu/sig2)':>13}{'invvol':>9}")

    base_var = df["ex"].var()
    rows = []
    for trend in ["up", "down"]:
        for sev in ["low", "high", "extreme"]:
            sel = (df["trend"] == trend) & (df["sev"] == sev)
            n = int(sel.sum())
            if n < 40:
                continue
            ex = df["ex"][sel]
            mu, var = ex.mean(), ex.var()
            ann_mu, ann_vol = mu * ANN, np.sqrt(var * ANN)
            sharpe = mu / np.sqrt(var) * np.sqrt(ANN)
            wstar = mu / var                              # gamma=1 mean-variance optimal (relative)
            invvol = np.sqrt(base_var) / np.sqrt(var)     # inverse-vol exposure (risk-only, normalized)
            label = f"{trend:>4} / {sev}"
            print(f"{label:40}{n:6d}{ann_mu:9.1%}{ann_vol:9.1%}{sharpe:8.2f}{wstar:13.2f}{invvol:9.2f}")
            rows.append(dict(trend=trend, sev=sev, n=n, ann_mu=round(ann_mu, 4),
                             ann_vol=round(ann_vol, 4), sharpe=round(sharpe, 3),
                             wstar=round(float(wstar), 3), invvol=round(float(invvol), 3)))

    out = pd.DataFrame(rows)
    # does optimal exposure track inverse-vol (risk) or does mu add structure beyond it?
    corr_riskonly = out["wstar"].corr(out["invvol"])
    print(f"\ncorr( w*  ,  inverse-vol )  = {corr_riskonly:+.2f}   "
          f"(high => 'best move' is just risk-scaling; low => drift/mu carries extra structure)")
    print("mu spread across cells (ann): "
          f"{out['ann_mu'].min():+.1%} .. {out['ann_mu'].max():+.1%}  "
          f"(if erratic / non-monotonic => the drift tilt is the overfit mirage)")
    out.to_csv(ROOT / "results/oracle_exposure.csv", index=False)
    print("wrote results/oracle_exposure.csv")


if __name__ == "__main__":
    main()
