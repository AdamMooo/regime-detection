"""V2 statistical jump model core (Bemporad et al. 2018; Nystrup et al. 2020).

Objective: min over (mu, s)  sum_t ||x_t - mu_{s_t}||^2 + lam * #{t: s_t != s_{t-1}}
Fitting alternates a k-means center update with an exact dynamic-programming
state-sequence assignment. lam=0 reduces to k-means; lam -> inf gives one state.

State identification convention: states sorted ascending by center coordinate 0
(feature 0 = downside deviation), so state 0 = calm/bull, state k-1 = stressed/bear.
"""

import numpy as np
import pandas as pd


def build_features(r):
    """Return-derived feature panel (Shu/Yu/Mulvey 2024): EWM downside deviation
    (halflife 10d) and EWM Sortino ratios (halflives 20d, 60d). Causal by
    construction (EWMs only look back)."""
    r = pd.Series(np.asarray(r, dtype=float))
    neg2 = np.minimum(r, 0.0) ** 2
    feats = {}
    dd10 = np.sqrt(neg2.ewm(halflife=10).mean())
    feats["dd10"] = dd10
    for hl in (20, 60):
        dd = np.sqrt(neg2.ewm(halflife=hl).mean())
        feats[f"sortino{hl}"] = r.ewm(halflife=hl).mean() / dd.replace(0.0, np.nan)
    return pd.DataFrame(feats)


def _dp_assign(C, lam):
    """Exact min-cost state sequence for per-day cost matrix C (T,k) with switch
    penalty lam. Returns (sequence, objective)."""
    T, k = C.shape
    if k == 2:
        return _dp_assign_k2(C, lam)
    switch = lam * (1.0 - np.eye(k))
    V = np.empty((T, k))
    B = np.zeros((T, k), dtype=int)
    V[0] = C[0]
    for t in range(1, T):
        tot = V[t - 1][:, None] + switch
        B[t] = tot.argmin(axis=0)
        V[t] = C[t] + tot.min(axis=0)
    s = np.empty(T, dtype=int)
    s[-1] = int(V[-1].argmin())
    for t in range(T - 1, 0, -1):
        s[t - 1] = B[t, s[t]]
    return s, float(V[-1].min())


def _dp_assign_k2(C, lam):
    """Scalar fast path for k=2 (avoids per-step numpy overhead in the T-loop)."""
    T = C.shape[0]
    c0, c1 = C[:, 0].tolist(), C[:, 1].tolist()
    v0, v1 = c0[0], c1[0]
    back = np.zeros((T, 2), dtype=np.uint8)
    for t in range(1, T):
        s0, s1 = v1 + lam, v0 + lam
        if s0 < v0:
            back[t, 0] = 1
            v0_new = c0[t] + s0
        else:
            v0_new = c0[t] + v0
        if s1 < v1:
            back[t, 1] = 0
            v1_new = c1[t] + s1
        else:
            back[t, 1] = 1
            v1_new = c1[t] + v1
        v0, v1 = v0_new, v1_new
    s = np.empty(T, dtype=int)
    s[-1] = 0 if v0 <= v1 else 1
    for t in range(T - 1, 0, -1):
        s[t - 1] = back[t, s[t]]
    return s, float(min(v0, v1))


def _cost(X, mu):
    return ((X[:, None, :] - mu[None, :, :]) ** 2).sum(axis=-1)


def _fit_once(X, k, lam, n_init, max_iter, rng):
    best = None
    inits = [X[rng.choice(len(X), size=k, replace=False)].copy() for _ in range(max(n_init - 1, 0))]
    # domain-informed init: centers at the feature-0 (downside-dev) extremes, which
    # biases one basin toward the vol-aligned split the balanced local optimum hides
    lo, hi = np.quantile(X[:, 0], [0.10, 0.90])
    q_init = np.vstack([X[np.abs(X[:, 0] - lo).argmin()], X[np.abs(X[:, 0] - hi).argmin()]])
    inits.append(q_init if k == 2 else X[rng.choice(len(X), size=k, replace=False)].copy())
    for mu in inits:
        mu = mu.copy()
        s_prev = None
        for _ in range(max_iter):
            s, obj = _dp_assign(_cost(X, mu), lam)
            if s_prev is not None and np.array_equal(s, s_prev):
                break
            s_prev = s
            for j in range(k):
                if np.any(s == j):
                    mu[j] = X[s == j].mean(axis=0)
        # re-sync (s, obj) with the final centers so the cross-init comparison
        # never uses a stale objective when max_iter is exhausted
        s, obj = _dp_assign(_cost(X, mu), lam)
        if best is None or obj < best[2]:
            best = (mu.copy(), s.copy(), obj)
    return best


def fit_jump_model(X, k=2, lam=10.0, n_init=10, max_iter=300, seed=0, weight_iters=3):
    """Weighted jump model fit (lightweight sparse-JM variant, Nystrup/Kolm/Lindstrom
    2021): after each fit, per-feature weights are set proportional to between-center
    separation, so uninformative features stop diluting the L2 distance. weight_iters=0
    recovers the plain jump model.

    Returns (centers_in_weighted_space, states, objective, weights); classify new data
    against these centers as X * sqrt(weights). Identification: state 0 = lower
    weighted-feature-0 center."""
    X = np.asarray(X, dtype=float)
    if not np.isfinite(X).all():
        raise ValueError("fit_jump_model requires a finite feature matrix (drop burn-in NaNs first)")
    rng = np.random.default_rng(seed)
    D = X.shape[1]
    w = np.ones(D)
    for it in range(weight_iters + 1):
        Xw = X * np.sqrt(w)
        mu_w, s, obj = _fit_once(Xw, k, lam, n_init, max_iter, rng)
        if it == weight_iters or len(np.unique(s)) < k:
            break
        sep = np.abs(mu_w[-1] - mu_w[0]) / np.sqrt(w)
        if sep.sum() <= 0:
            break
        w = np.maximum(sep / sep.sum() * D, 1e-3)
    order = np.argsort(mu_w[:, 0])
    remap = np.empty(k, dtype=int)
    remap[order] = np.arange(k)
    return mu_w[order], remap[s], obj, w


def filter_states(X, mu, lam, V0=None):
    """Causal filtered states: endpoint of the forward DP value recursion.
    V_t[k] = C_t[k] + min_j(V_{t-1}[j] + lam*1{j!=k}); s_t = argmin_k V_t[k].
    V_t depends only on the past, so s_t is filtered (the backtracked DP path is
    the smoothed object and is never used here). Unlike a greedy one-step rule,
    this accumulates evidence, so the same lam scale as the fit applies.
    Returns (states, V_end) — pass V_end back in as V0 to chain across blocks."""
    X = np.asarray(X, dtype=float)
    C = _cost(X, mu)
    k = len(mu)
    switch = lam * (1.0 - np.eye(k))
    V = np.zeros(k) if V0 is None else np.asarray(V0, dtype=float).copy()
    s = np.empty(len(X), dtype=int)
    for t in range(len(X)):
        V = C[t] + (V[:, None] + switch).min(axis=0)
        V -= V.min()
        s[t] = int(V.argmin())
    return s, V
