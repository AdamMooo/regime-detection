"""Tail-hazard MVE — mathematical core (frozen prereg §8.3, rung D).

ADAM WRITES THE TWO FUNCTIONS BELOW. This is the mathematical core of the
hypothesis — the excitation state H_t and the Bernoulli likelihood. All
surrounding infrastructure (data build, ladder, OOS harness) is scaffolded.
Tests: tests/test_tailhazard_core.py (skip until written; green when correct).

Conventions (fixed — tests and the stage harness assume them):
- events: array e in {0,1}, ordered in time, length n.
- H[t] includes e_t:  H_t = exp(-beta) * H_{t-1} + e_t,  with H before the
  first observation = 0. The stage harness pairs H[t] with target
  y[t] = e_{t+1} (predict tomorrow from information through today).
  alpha is fixed to 1 (absorbed into b), per the frozen ladder.
- bernoulli_nll: params = [a, b, g_1..g_k];
  logit u_t = a + b*H_t + X_t @ g;  p_t = sigmoid(u_t);
  returns the MEAN negative log-likelihood (a float). Must be numerically
  stable for |u| large — express -log p and -log(1-p) without ever forming
  p (np.logaddexp is the standard tool); see test_nll_stable_extreme.
"""

import numpy as np


def excitation_state(events: np.ndarray, beta: float) -> np.ndarray:
    """Discrete-time Hawkes excitation state, O(n).

    Equivalent closed form: H[t] = sum_{s<=t} exp(-beta*(t-s)) * events[s].
    Splitting the sum at t: every s<t term gains one factor exp(-beta) moving
    from t-1 to t, so H_t = exp(-beta)*H_{t-1} + e_t with H before the start = 0.
    Only indices <= t are ever read — H[t] is causal by construction.
    """
    decay = np.exp(-beta)
    H = np.empty(len(events), dtype=float)
    h = 0.0
    for t, e in enumerate(events):
        h = decay * h + e
        H[t] = h
    return H


def bernoulli_nll(params: np.ndarray, H: np.ndarray, X: np.ndarray, y: np.ndarray) -> float:
    """Mean Bernoulli negative log-likelihood of y under logit u = a + b*H + X@g.

    params = [a, b, *g]; X has shape (n, k), k >= 0; y in {0,1}.
    Logit-space form: -log p(u) = logaddexp(0,-u) and -log(1-p(u)) = logaddexp(0,u),
    and since logaddexp(0,-u) = logaddexp(0,u) - u, the per-observation loss
    collapses to logaddexp(0,u) - y*u. p is never formed — stable at extreme u.
    """
    u = params[0] + params[1] * H + X @ params[2:]
    return float(np.mean(np.logaddexp(0.0, u) - y * u))
