"""V2 evaluation machinery: strategy construction, baselines, FKO economic value.

Conventions (to be frozen in the prereg): 1-day execution delay on every signal,
10 bps one-way proportional costs on weight changes, long-only weights in [0, 1],
cash leg earns rf. FKO fee follows Fleming/Kirby/Ostdiek (JF 2001): quadratic
utility U(x) = (1+x) - [gamma/(2(1+gamma))] (1+x)^2; the fee is the constant
daily deduction Delta from strategy A that equates average realized utility with
strategy B; reported annualized in bps.
"""

import numpy as np
import pandas as pd


def strategy_returns(w, r, rf, cost_bps=10.0, delay=1):
    w = pd.Series(np.asarray(w, dtype=float)).shift(delay).fillna(0.0)
    r = pd.Series(np.asarray(r, dtype=float))
    rf = pd.Series(np.broadcast_to(np.asarray(rf, dtype=float), r.shape).copy())
    turnover = w.diff().abs().fillna(w.abs())
    return (w * r + (1.0 - w) * rf - turnover * cost_bps * 1e-4).to_numpy()


def jm_weights(states):
    return (np.asarray(states) == 0).astype(float)


def vol_target_weights(r, target_ann=0.10, halflife=20, cap=1.0):
    sig = pd.Series(np.asarray(r, dtype=float)).ewm(halflife=halflife).std() * np.sqrt(252)
    return np.clip(target_ann / sig.replace(0.0, np.nan), 0.0, cap).fillna(1.0).to_numpy()


def sma_weights(r, window=200):
    px = (1.0 + pd.Series(np.asarray(r, dtype=float))).cumprod()
    w = (px > px.rolling(window).mean()).astype(float)
    w.iloc[: window - 1] = 1.0
    return w.to_numpy()


def sharpe(ret, rf=0.0):
    ex = np.asarray(ret, dtype=float) - np.broadcast_to(np.asarray(rf, dtype=float), np.shape(ret))
    sd = ex.std()
    if sd < 1e-12:
        return 0.0
    return float(ex.mean() / sd * np.sqrt(252))


def fko_fee(r_a, r_b, gamma=10.0):
    """Annualized fee (bps) investor with quadratic utility would pay to hold A over B.
    Closed form: average utility is quadratic in the constant deduction Delta."""
    a = 1.0 + np.asarray(r_a, dtype=float)
    b = 1.0 + np.asarray(r_b, dtype=float)
    c = gamma / (2.0 * (1.0 + gamma))
    K = b.mean() - c * (b ** 2).mean()
    # mean U(a - Delta) = (m1 - Delta) - c (m2 - 2 m1 Delta + Delta^2) = K
    coeffs = [-c, 2.0 * c * a.mean() - 1.0, a.mean() - c * (a ** 2).mean() - K]
    roots = np.roots(coeffs)
    real = roots[np.abs(roots.imag) < 1e-12].real
    delta = real[np.argmin(np.abs(real))]
    return float(delta * 252 * 1e4)


def stationary_bootstrap_ci(r_a, r_b, stat, n_boot=500, mean_block=126, alpha=0.10, seed=0):
    """CI for stat(r_a, r_b) under paired stationary bootstrap (Politis-Romano 1994)."""
    r_a = np.asarray(r_a, dtype=float)
    r_b = np.asarray(r_b, dtype=float)
    T = len(r_a)
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for i in range(n_boot):
        idx = np.empty(T, dtype=int)
        t = 0
        while t < T:
            start = rng.integers(T)
            length = min(rng.geometric(1.0 / mean_block), T - t)
            idx[t:t + length] = (start + np.arange(length)) % T
            t += length
        vals[i] = stat(r_a[idx], r_b[idx])
    lo, hi = np.quantile(vals, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)
