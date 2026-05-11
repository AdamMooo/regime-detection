"""Core causal inference utilities.

Functions
---------
expanding_standardize(X_raw, min_warmup=252)
    Expanding-window z-score (past data only, no lookahead)
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


__all__ = ['expanding_standardize']
