"""Core causal inference utilities.

Functions
---------
expanding_standardize(X_raw, min_warmup=252)
    Expanding-window z-score (past data only, no lookahead)
expanding_regime_vol(returns, labels, n_regimes, min_periods, fallback)
    Causal, point-in-time annualized vol per regime (past data only)
"""

import numpy as np


def expanding_standardize(X_raw, min_warmup=252):
    """Expanding-window z-score: row t uses mean/std from [0..t] only.

    Causal transformation — standardization at time t uses only data
    from time 0 to t. Essential for live trading (no lookahead).

    Parameters
    ----------
    X_raw : ndarray (T, D)
        Raw feature matrix
    min_warmup : int
        First N rows are set to NaN (statistics too unstable)

    Returns
    -------
    X_scaled : ndarray (T, D)
        Standardized features (NaN for first min_warmup rows)
    cum_mean_final : ndarray (D,)
        Cumulative mean at last row (for live prediction)
    cum_std_final : ndarray (D,)
        Cumulative std at last row (for live prediction)
    """
    X = X_raw.astype(np.float64)
    T, D = X.shape
    cumsum = np.cumsum(X, axis=0)
    cumsq = np.cumsum(X ** 2, axis=0)
    counts = np.arange(1, T + 1, dtype=np.float64).reshape(-1, 1)
    cum_mean = cumsum / counts
    cum_var = cumsq / counts - cum_mean ** 2
    cum_std = np.sqrt(np.maximum(cum_var, 0))
    cum_std[cum_std < 1e-8] = 1.0
    X_scaled = (X - cum_mean) / cum_std
    X_scaled[:min_warmup] = np.nan
    return X_scaled, cum_mean[-1], cum_std[-1]


def expanding_regime_vol(returns, labels, n_regimes, min_periods=20, fallback=15.0):
    """Causal, point-in-time annualized vol (%) estimate, grouped by regime.

    Row t uses only returns[s] for s < t where labels[s] == labels[t] --
    same "no future data" discipline as expanding_standardize(), but
    grouped by regime instead of global, AND lagged one extra step:
    returns[t] is the outcome being traded on day t, so it must not be
    folded into regime k's running stats until AFTER vol_series[t] is
    computed (the same reason the RV30 baseline uses `.shift(1)`).

    Parameters
    ----------
    returns : ndarray (T,)
        Daily returns.
    labels : ndarray (T,) int
        Regime label per row, values in [0, n_regimes).
    n_regimes : int
    min_periods : int
        Minimum past observations of a regime before trusting its estimate.
    fallback : float
        Annualized vol (%) to use before min_periods is reached.

    Returns
    -------
    vol_series : ndarray (T,)
        Annualized vol (%) known at the START of day t (uses no data
        from day t onward).
    """
    returns = np.asarray(returns, dtype=np.float64)
    labels = np.asarray(labels)
    T = len(returns)
    vol_series = np.empty(T)

    sums = np.zeros(n_regimes)
    sqsums = np.zeros(n_regimes)
    counts = np.zeros(n_regimes, dtype=np.int64)

    for t in range(T):
        k = labels[t]
        if counts[k] >= min_periods:
            mean_k = sums[k] / counts[k]
            var_k = sqsums[k] / counts[k] - mean_k ** 2
            vol_series[t] = np.sqrt(max(var_k, 0.0)) * np.sqrt(252) * 100
        else:
            vol_series[t] = fallback

        sums[k] += returns[t]
        sqsums[k] += returns[t] ** 2
        counts[k] += 1

    return vol_series


__all__ = ['expanding_standardize', 'expanding_regime_vol']
