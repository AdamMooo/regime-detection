"""V2 shared walk-forward pipeline — used by BOTH the synthetic validation battery and the
real-data stage-1 runner so the two paths cannot drift (v1 lesson: byte-identical architecture).

Protocol (frozen in .planning/V2-JUMPMODEL-PREREG.md §3):
expanding walk-forward; per refit, lambda chosen from a frozen grid by validation-window
strategy Sharpe (causal split of the training window); centers fit on the training window;
greedy online classification of the next block with frozen centers/lambda/z-params; state
chained across refit boundaries.
"""

import numpy as np

from v2_core import filter_states, fit_jump_model
from v2_eval import jm_weights, sharpe, strategy_returns


def _zapply(F, mean, std):
    return (F - mean) / std


def select_lambda(F_train, r_train, grid, val=1008, n_init=5, cost_bps=10.0, delay=1):
    sub, valF = F_train[:-val], F_train[-val:]
    r_val = r_train[-val:]
    mean, std = sub.mean(axis=0), sub.std(axis=0)
    Zs, Zv = _zapply(sub, mean, std), _zapply(valF, mean, std)
    best_lam, best_sharpe = grid[0], -np.inf
    for lam in grid:
        mu, _, _, w = fit_jump_model(Zs, k=2, lam=lam, n_init=n_init, seed=0)
        _, V_end = filter_states(Zs * np.sqrt(w), mu, lam)
        s_val, _ = filter_states(Zv * np.sqrt(w), mu, lam, V0=V_end)
        sr = sharpe(strategy_returns(jm_weights(s_val), r_val, 0.0, cost_bps=cost_bps, delay=delay))
        if sr >= best_sharpe:
            best_lam, best_sharpe = lam, sr
    return best_lam


def walk_forward(r, F, burn, train0, refit, grid, val=1008, n_init=5, cost_bps=10.0, delay=1):
    """Returns (states aligned to r with -1 outside OOS, lambda history).

    At each refit the filter's value state V is re-initialized by a causal forward
    pass over the training window with the NEW centers, so accumulated evidence is
    always expressed in current-center units (no cross-center chaining)."""
    states = np.full(len(r), -1, dtype=int)
    lam_hist = []
    t0 = burn + train0
    while t0 < len(r):
        F_train = F[burn:t0]
        lam = select_lambda(F_train, r[burn:t0], grid, val=val, n_init=n_init,
                            cost_bps=cost_bps, delay=delay)
        mean, std = F_train.mean(axis=0), F_train.std(axis=0)
        Z_train = _zapply(F_train, mean, std)
        mu, _, _, w = fit_jump_model(Z_train, k=2, lam=lam, n_init=n_init, seed=0)
        _, V_end = filter_states(Z_train * np.sqrt(w), mu, lam)
        block = slice(t0, min(t0 + refit, len(r)))
        s_block, _ = filter_states(_zapply(F[block], mean, std) * np.sqrt(w), mu, lam, V0=V_end)
        states[block] = s_block
        lam_hist.append(lam)
        t0 += refit
    return states, lam_hist
