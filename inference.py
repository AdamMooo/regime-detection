"""Core regime inference logic.

Regime probability filtering (forward-pass only, no lookahead), label assignment
with hysteresis, and HMM model fitting.

This module implements causal regime detection: filtered probabilities use only
past/present data, never future data. Regime labels stick for a minimum hold
period to suppress noise.

Functions
---------
expanding_standardize(X_raw, min_warmup=252)
    Expanding-window z-score (past data only, no lookahead)

filtered_probs(model, X)
    Forward-pass regime probabilities (filtered, not smoothed)

filtered_labels(model, X, hold_days=REGIME_HOLD_DAYS)
    Regime labels with hysteresis

Classes
-------
StudentTHMM
    Student-t HMM implementation (fat tails)
"""

import logging
import numpy as np
from hmmlearn import hmm
from scipy.stats import multivariate_t as _mvt

from config import T_DF, HMM_ITER, REGIME_HOLD_DAYS

logger = logging.getLogger(__name__)


# ===================================================================
# Expanding-window standardization (causal, no lookahead)
# ===================================================================

def expanding_standardize(X_raw, min_warmup=252):
    """Expanding-window z-score: row t uses mean/std from [0..t] only.

    This is a causal transformation: standardization at time t uses only data
    from time 0 to t, not future data. This is essential for live trading.

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


# ===================================================================
# Student-t HMM (fat-tail emission distributions)
# ===================================================================

class StudentTHMM(hmm.GaussianHMM):
    """GaussianHMM with Student-t emission log-likelihoods.

    Extends hmmlearn.GaussianHMM with multivariate Student-t emissions,
    capturing fat tails in regime-dependent returns.

    Attributes
    ----------
    n_components : int
        Number of regimes/states
    means_ : ndarray
        State emission means
    covars_ : ndarray
        State emission covariances
    transmat_ : ndarray
        State transition matrix
    startprob_ : ndarray
        Initial state probabilities
    """

    def _compute_log_likelihood(self, X):
        """Compute Student-t log-likelihoods for each state.

        Parameters
        ----------
        X : ndarray (T, D)
            Observations

        Returns
        -------
        ll : ndarray (T, n_components)
            Log-likelihood for each state at each time
        """
        ll = np.empty((len(X), self.n_components))
        for k in range(self.n_components):
            ll[:, k] = _mvt.logpdf(
                X, loc=self.means_[k], shape=self.covars_[k], df=T_DF,
            )
        return ll


def _fit_hmm(X, n_states, cov_type, seed):
    """Fit a Student-t HMM to feature data.

    Parameters
    ----------
    X : ndarray (T, n_features)
        Standardized feature matrix
    n_states : int
        Number of regimes
    cov_type : str
        Covariance type ('full', 'tied', 'diag', 'spherical')
    seed : int
        Random seed for reproducibility

    Returns
    -------
    model : StudentTHMM
        Fitted HMM instance
    """
    m = StudentTHMM(
        n_components=n_states, covariance_type=cov_type,
        n_iter=HMM_ITER, random_state=seed, verbose=False,
    )
    m.fit(X)
    return m


# ===================================================================
# Forward-pass regime probabilities (causal, no future lookahead)
# ===================================================================

def filtered_probs(model, X):
    """Forward-only (filtered) regime probabilities — NO future lookahead.

    Unlike predict_proba() which uses forward-backward (smoothed),
    this only uses information up to time t for P(state_t | x_1..x_t).
    This is the correct real-time / online regime estimate and is essential
    for causal live trading.

    Parameters
    ----------
    model : StudentTHMM
        Fitted HMM
    X : ndarray (T, n_features)
        Observations

    Returns
    -------
    probs : ndarray (T, n_states)
        Forward-filtered regime probabilities (rows sum to 1)
    """
    log_ll = model._compute_log_likelihood(X)
    n_states = model.n_components
    T = len(X)

    # Forward pass only (no backward pass)
    alpha = np.zeros((T, n_states))
    log_startprob = np.log(model.startprob_ + 1e-300)
    log_transmat = np.log(model.transmat_ + 1e-300)

    # t = 0: initial state probabilities
    alpha[0] = log_startprob + log_ll[0]
    alpha[0] -= np.logaddexp.reduce(alpha[0])

    # t = 1..T-1: forward recursion
    for t in range(1, T):
        for j in range(n_states):
            alpha[t, j] = np.logaddexp.reduce(
                alpha[t - 1] + log_transmat[:, j]
            ) + log_ll[t, j]
        alpha[t] -= np.logaddexp.reduce(alpha[t])

    # Convert log-probs to probs
    probs = np.exp(alpha)
    probs /= probs.sum(axis=1, keepdims=True)
    return probs


# ===================================================================
# Regime labeling with hysteresis (noise suppression)
# ===================================================================

def filtered_labels(model, X, hold_days=REGIME_HOLD_DAYS):
    """Argmax of filtered probabilities with hysteresis to prevent flicker.

    A regime switch only takes effect after the new regime has been the
    argmax for hold_days consecutive days. This eliminates 1-2 day
    noise-driven flips while keeping genuine transitions fast.

    Parameters
    ----------
    model : StudentTHMM
        Fitted HMM
    X : ndarray (T, n_features)
        Observations
    hold_days : int
        Minimum consecutive days before regime change takes effect

    Returns
    -------
    labels : ndarray (T,)
        Regime labels with hysteresis
    """
    probs = filtered_probs(model, X)
    raw = probs.argmax(axis=1)

    if hold_days <= 1:
        return raw

    out = np.empty_like(raw)
    out[0] = raw[0]
    pending = raw[0]
    streak = 0

    for t in range(1, len(raw)):
        if raw[t] == out[t - 1]:
            # Same as current regime — reset any pending switch
            out[t] = out[t - 1]
            pending = out[t]
            streak = 0
        elif raw[t] == pending:
            # Continuing a pending switch
            streak += 1
            if streak >= hold_days:
                out[t] = pending
                streak = 0
            else:
                out[t] = out[t - 1]
        else:
            # New candidate — start fresh
            pending = raw[t]
            streak = 1
            if hold_days <= 1:
                out[t] = pending
            else:
                out[t] = out[t - 1]

    return out


__all__ = [
    'expanding_standardize',
    'StudentTHMM',
    '_fit_hmm',
    'filtered_probs',
    'filtered_labels',
]
