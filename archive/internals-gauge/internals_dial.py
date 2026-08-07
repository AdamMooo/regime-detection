"""H3 — dial sanity check (prereg S4/S5, SECONDARY, non-gating). Turns g(t) into an
exposure dial and checks it does not significantly worsen drawdown geometry vs
reactive vol-targeting, at matched average exposure. Cash (rf), not bonds, is the
de-risk leg (S4 already frozen this way — no change made here).

A flat/marginal H3 is acceptable per prereg; only a significant *worsening* (bootstrap
CI entirely on the wrong side) counts as evidence against the gauge (F5).

Usage: python internals_dial.py --panel {us,japan,europe}
"""

import argparse

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from backtest import strategy_returns, vol_target_weights, stationary_bootstrap_ci
from internals_gauge import build_internals, z_expand
from internals_h1 import load_panel
from run_config import maxdd, DELAY, COST


def dial_weights(g, k, cap=1.0):
    gz = z_expand(g)
    return np.clip(1.0 - k * gz.fillna(0.0), 0.0, cap)


def solve_k(g, w_vt, cap=1.0):
    """1-D root solve: k such that mean(dial weight) == mean(w_vt). Uses ONLY the
    two exposure paths (never return/DD outcomes), per S4."""
    target = np.nanmean(w_vt)

    def diff(k):
        return np.nanmean(dial_weights(g, k, cap)) - target

    lo, hi = -50.0, 50.0
    if diff(lo) * diff(hi) > 0:
        # target unreachable in range; return the closer bound
        return lo if abs(diff(lo)) < abs(diff(hi)) else hi
    return brentq(diff, lo, hi)


def run(panel):
    ind, mkt = load_panel(panel)
    internals = build_internals(ind)
    r = mkt.reindex(internals.index).fillna(0.0)
    rf = pd.Series(0.0, index=r.index)  # OOS panels have no rf column; US uses 0 here too for parity

    w_vt = vol_target_weights(r)
    k = solve_k(internals["g"], w_vt)
    w_dial = dial_weights(internals["g"], k).to_numpy()

    exposure_match_pct = abs(np.nanmean(w_dial) - np.nanmean(w_vt)) / np.nanmean(w_vt)

    ret_dial = strategy_returns(w_dial, r.to_numpy(), rf.to_numpy(), cost_bps=COST, delay=DELAY)
    ret_vt = strategy_returns(w_vt, r.to_numpy(), rf.to_numpy(), cost_bps=COST, delay=DELAY)

    dd_dial = maxdd(ret_dial)
    dd_vt = maxdd(ret_vt)

    ci = stationary_bootstrap_ci(ret_dial, ret_vt, lambda a, b: maxdd(a) - maxdd(b))

    return dict(k=k, exposure_match_pct=exposure_match_pct, maxdd_dial=dd_dial,
                maxdd_vt=dd_vt, ci_diff=ci)


def report(panel, out):
    print(f"\n=== H3 dial sanity (secondary, non-gating) — panel: {panel} ===")
    print(f"k={out['k']:.3f}  exposure-match error={out['exposure_match_pct']:.2%} "
          f"(must be <1% before this is read, S7)")
    print(f"maxDD dial={out['maxdd_dial']:.2%}  maxDD vol-target={out['maxdd_vt']:.2%}")
    lo, hi = out["ci_diff"]
    print(f"90% CI on (dial - vt) maxDD: [{lo:.4f}, {hi:.4f}]")
    if lo > 0:
        print("F5: CI entirely on the wrong side -> significant WORSENING, evidence against gauge.")
    else:
        print("No significant worsening (flat/marginal is acceptable per S5).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", choices=["us", "japan", "europe"], required=True)
    args = ap.parse_args()
    res = run(args.panel)
    report(args.panel, res)
