"""The risk engine (Goal A — the money): a vol-targeted, diversified allocation.

This is NOT a new alpha claim and spends NO look — it IMPLEMENTS the approach that already won every
horse race in this project (vol-targeting + diversification beat timing/overlays: Ch1/Ch2/Path-B) and
that the literature endorses (Asness: risk management is the edge, not prediction). The point for an
advisor product is the DRAWDOWN reduction that makes a portfolio holdable, plus improved risk-adjusted
return — and (via Goal B) the behavior-gap return from clients actually staying invested.

Universe: equity (French total market) + 10y Treasury (diversifier), 1962+ (bond history). A static
60/40 is the diversified base; the engine vol-targets it (EWMA vol, 10% ann target, no leverage: scale
DOWN in turbulence only). Target is a round a-priori 10% — NOT grid-optimized (overfitting refused).

Compares B&H equity / static 60-40 / vol-targeted 60-40 on the metrics an advisor client feels:
annualized return, vol, Sharpe, MAX DRAWDOWN, worst rolling 12m. Writes results/risk_engine.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from backtest import strategy_returns, vol_target_weights
from run_config import maxdd


def metrics(ret, rf):
    ret = np.asarray(ret, dtype=float)
    eq = np.cumprod(1.0 + ret)
    ann_ret = eq[-1] ** (252 / len(ret)) - 1.0
    ann_vol = ret.std() * np.sqrt(252)
    ex = ret - np.asarray(rf, dtype=float)
    sharpe = ex.mean() / ret.std() * np.sqrt(252)
    roll1y = pd.Series(ret).rolling(252).apply(lambda x: np.prod(1 + x) - 1.0, raw=True)
    return dict(ann_ret=ann_ret, ann_vol=ann_vol, sharpe=sharpe,
                max_drawdown=maxdd(ret), worst_12m=float(roll1y.min()))


def main():
    d = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    d = d[["mkt_ret", "bond10_ret", "rf"]].dropna()
    eq, bd, rf = d["mkt_ret"].to_numpy(), d["bond10_ret"].to_numpy(), d["rf"].to_numpy()

    port = 0.6 * eq + 0.4 * bd                          # static diversified base, daily rebalanced
    w_vt = vol_target_weights(port, target_ann=0.10, halflife=20, cap=1.0)
    vt = strategy_returns(w_vt, port, rf, cost_bps=10.0, delay=2)

    arms = {"BH_equity": eq, "static_60_40": port, "voltarget_60_40": vt}
    rows = []
    print("=" * 84)
    print(f"RISK ENGINE — diversified vol-targeted allocation ({d.index[0].date()}..{d.index[-1].date()})")
    print("=" * 84)
    print(f"{'arm':18}{'ann ret':>9}{'ann vol':>9}{'Sharpe':>8}{'max DD':>9}{'worst 12m':>11}")
    for name, r in arms.items():
        m = metrics(r, rf)
        rows.append(dict(arm=name, **{k: round(v, 4) for k, v in m.items()}))
        print(f"{name:18}{m['ann_ret']:9.2%}{m['ann_vol']:9.2%}{m['sharpe']:8.2f}"
              f"{m['max_drawdown']:9.1%}{m['worst_12m']:11.1%}")

    avg_w = float(pd.Series(w_vt).mean())
    print(f"\nvol-target avg exposure {avg_w:.0%} (scales DOWN in turbulence; capped at 100%, no leverage)")
    pd.DataFrame(rows).to_csv(ROOT / "results/risk_engine.csv", index=False)
    print("wrote results/risk_engine.csv")


if __name__ == "__main__":
    main()
