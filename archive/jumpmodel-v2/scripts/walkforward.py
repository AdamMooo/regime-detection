"""V2 shared walk-forward pipeline — used by BOTH the synthetic validation battery and the
real-data stage-1 runner so the two paths cannot drift (v1 lesson: byte-identical architecture).

Protocol (frozen in .planning/V2-JUMPMODEL-PREREG.md §3):
expanding walk-forward; per refit, lambda chosen from a frozen grid by validation-window
strategy Sharpe (causal split of the training window); centers fit on the training window;
greedy online classification of the next block with frozen centers/lambda/z-params; state
chained across refit boundaries.
"""

import numpy as np

from jumpmodel import filter_states, fit_jump_model
from backtest import jm_weights, sharpe, strategy_returns


def _zapply(F, mean, std):
    return (F - mean) / std


def select_lambda(F_train, r_train, grid, val=1008, n_init=5, cost_bps=10.0, delay=1, k=2):
    sub, valF = F_train[:-val], F_train[-val:]
    r_val = r_train[-val:]
    mean, std = sub.mean(axis=0), sub.std(axis=0)
    Zs, Zv = _zapply(sub, mean, std), _zapply(valF, mean, std)
    best_lam, best_sharpe = grid[0], -np.inf
    for lam in grid:
        mu, _, _, w = fit_jump_model(Zs, k=k, lam=lam, n_init=n_init, seed=0)
        _, V_end = filter_states(Zs * np.sqrt(w), mu, lam)
        s_val, _ = filter_states(Zv * np.sqrt(w), mu, lam, V0=V_end)
        # validation weights: linear in state rank ((k-1-s)/(k-1)); identical to
        # jm_weights for k=2, the natural graded generalization otherwise
        w_val = jm_weights(s_val) if k == 2 else (k - 1 - s_val) / (k - 1)
        sr = sharpe(strategy_returns(w_val, r_val, 0.0, cost_bps=cost_bps, delay=delay))
        if sr >= best_sharpe:
            best_lam, best_sharpe = lam, sr
    return best_lam


def walk_forward(r, F, burn, train0, refit, grid, val=1008, n_init=5, cost_bps=10.0, delay=1,
                 k=2, return_margin=False):
    """Returns (states aligned to r with -1 outside OOS, lambda history).

    At each refit the filter's value state V is re-initialized by a causal forward
    pass over the training window with the NEW centers, so accumulated evidence is
    always expressed in current-center units (no cross-center chaining).

    return_margin=True (k=2 only) additionally returns the filter's normalized
    evidence gap m_t = (V_t[calm] - V_t[stressed]) / lam aligned to r (NaN outside
    OOS): m_t > 0 means the filter favors the stressed state, and the lam
    normalization expresses the gap as a fraction of the switch band so it is
    comparable across refits (chapter-3 calibration input, prereg §6)."""
    if return_margin and k != 2:
        raise ValueError("return_margin is defined for k=2 only")
    states = np.full(len(r), -1, dtype=int)
    margins = np.full(len(r), np.nan) if return_margin else None
    lam_hist = []
    t0 = burn + train0
    while t0 < len(r):
        F_train = F[burn:t0]
        lam = select_lambda(F_train, r[burn:t0], grid, val=val, n_init=n_init,
                            cost_bps=cost_bps, delay=delay, k=k)
        mean, std = F_train.mean(axis=0), F_train.std(axis=0)
        Z_train = _zapply(F_train, mean, std)
        mu, _, _, w = fit_jump_model(Z_train, k=k, lam=lam, n_init=n_init, seed=0)
        _, V_end = filter_states(Z_train * np.sqrt(w), mu, lam)
        block = slice(t0, min(t0 + refit, len(r)))
        Z_block = _zapply(F[block], mean, std) * np.sqrt(w)
        if return_margin:
            s_block, _, V_path = filter_states(Z_block, mu, lam, V0=V_end, return_path=True)
            margins[block] = (V_path[:, 0] - V_path[:, 1]) / lam
        else:
            s_block, _ = filter_states(Z_block, mu, lam, V0=V_end)
        states[block] = s_block
        lam_hist.append(lam)
        t0 += refit
    if return_margin:
        return states, lam_hist, margins
    return states, lam_hist
