"""Rolling PCA utilities extracted from hmm_training.py (Phase 6, MODEL-03).

This module handles rolling-window PCA with Procrustes alignment and the
linearized stochastic volatility state-space model. Both were extracted from
hmm_training.py to keep that module under the 500-line concern boundary.

Functions
---------
fit_rolling_pca(X_scaled, window, max_components, var_threshold)
    Rolling-window PCA with Procrustes alignment for regime stability

Classes
-------
LinearizedSV
    Linearized stochastic volatility model estimated via Kalman filter
    (statsmodels MLEModel). Co-located here to avoid a single-class file.
"""

import logging
import numpy as np
from scipy.linalg import orthogonal_procrustes
from sklearn.decomposition import PCA
from statsmodels.tsa.statespace.mlemodel import MLEModel

from src.config import (
    RANDOM_SEED, PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD, PCA_ROLLING_WINDOW,
)

logger = logging.getLogger(__name__)

# Constants for linearized SV model
_LOG_CHI2_MEAN = -1.2704
_LOG_CHI2_VAR = np.pi ** 2 / 2


# ===================================================================
# Rolling PCA (Procrustes-aligned)
# ===================================================================

def fit_rolling_pca(X_scaled, window=PCA_ROLLING_WINDOW,
                    max_components=PCA_MAX_COMPONENTS,
                    var_threshold=PCA_VAR_THRESHOLD):
    """Rolling-window PCA with Procrustes alignment.

    For each day t (t >= window-1), fits PCA on X_scaled[t-window+1 : t+1].
    Returns the last row's projection as that day's PC scores. Procrustes
    alignment ensures that consecutive PCA components are smoothly rotated,
    preventing sign flips and alignment artifacts.

    Parameters
    ----------
    X_scaled : ndarray (T, D)
        Standardized feature matrix
    window : int
        Rolling window size (default 252 trading days ≈ 1 year)
    max_components : int
        Maximum PCA components to compute
    var_threshold : float
        Variance threshold for selecting number of components (e.g., 0.95 = 95%)

    Returns
    -------
    pcs : ndarray (T_valid, n_selected)
        Principal component scores (rows correspond to valid trading days)
    mode_ratio : ndarray (T_valid,)
        Market-mode ratio (λ₁ / Σλ) — ratio of first eigenvalue to trace
    valid_mask : ndarray (T,)
        Boolean mask indicating days with valid PCA projections
    n_selected : int
        Number of selected principal components
    pca : PCA
        Final PCA model (fitted on last window)
    """
    T, D = X_scaled.shape
    n_comp = min(max_components, D)

    all_scores = np.full((T, n_comp), np.nan)
    mode_ratio = np.full(T, np.nan)
    prev_loadings = None
    pca = None

    for t in range(window - 1, T):
        chunk = X_scaled[t - window + 1: t + 1]
        pca = PCA(n_components=n_comp, random_state=RANDOM_SEED)
        scores = pca.fit_transform(chunk)

        # Procrustes alignment: jointly align all components with previous window
        if prev_loadings is not None:
            # Find orthogonal rotation R that minimizes ||A @ R - B||_F
            # where A = current components, B = previous components
            R, _ = orthogonal_procrustes(pca.components_.T, prev_loadings.T)
            aligned = R.T @ pca.components_
            pca.components_ = aligned
            scores = chunk @ aligned.T  # re-project with aligned loadings
            # Center scores to match PCA convention
            scores = scores - scores.mean(axis=0)

        prev_loadings = pca.components_.copy()
        all_scores[t] = scores[-1]          # current day's projection
        mode_ratio[t] = pca.explained_variance_ratio_[0]

    # Number of components: use last window's variance structure
    assert pca is not None, "PCA was never fitted (no valid windows)"
    cum_var = np.cumsum(pca.explained_variance_ratio_)
    n_selected = int(np.searchsorted(cum_var, var_threshold) + 1)
    n_selected = max(2, min(n_selected, n_comp))

    valid_mask = ~np.isnan(all_scores[:, 0])
    pcs = all_scores[valid_mask, :n_selected]
    mr = mode_ratio[valid_mask]

    print(f"\nRolling PCA (window={window}):")
    print(f"  {n_comp} components computed, {n_selected} selected "
          f"({cum_var[n_selected - 1]:.1%} variance, last window)")
    for i in range(n_comp):
        tag = ' <-' if i < n_selected else ''
        print(f"  PC{i + 1}: {pca.explained_variance_ratio_[i]:.1%}  "
              f"(cum {cum_var[i]:.1%}){tag}")
    print(f"  Market-mode ratio: mean={mr.mean():.1%}, "
          f"min={mr.min():.1%}, max={mr.max():.1%}")
    print(f"  Valid days: {valid_mask.sum()} / {T}")

    return pcs, mr, valid_mask, n_selected, pca


# ===================================================================
# Linearized Stochastic Volatility Model
# ===================================================================

class LinearizedSV(MLEModel):
    """Linearized stochastic volatility model estimated via Kalman filter.

    Observation : z_t = c + h_t + xi_t,   xi_t ~ N(0, π²/2)
    State       : h_t = μ(1-φ) + φ*h_{t-1} + σ_η*η_t

    where z_t = log(r_t²), c = E[log(ε²)] = -1.2704 (log-chi-squared(1) mean),
    and h_t is the latent log-volatility.

    Parameters: μ (long-run log-vol), φ (persistence), σ_η (vol-of-vol)
    """

    def __init__(self, endog, **kwargs):
        super().__init__(endog, k_states=1, k_posdef=1, **kwargs)

        self['design'] = np.array([[1.0]])
        self['obs_intercept'] = np.array([[_LOG_CHI2_MEAN]])
        self['obs_cov'] = np.array([[_LOG_CHI2_VAR]])
        self['selection'] = np.eye(1)

        self.initialize_approximate_diffuse()

    @property
    def param_names(self):
        return ['mu', 'phi', 'sigma_eta']

    @property
    def start_params(self):
        mu0 = np.nanmean(self.endog) - _LOG_CHI2_MEAN
        return np.array([mu0, 0.95, 0.2])

    def transform_params(self, unconstrained):
        c = unconstrained.copy()
        c[1] = np.tanh(c[1])           # phi in (-1, 1)
        c[2] = np.exp(c[2])            # sigma_eta > 0
        return c

    def untransform_params(self, constrained):
        u = constrained.copy()
        u[1] = np.arctanh(np.clip(constrained[1], -0.999, 0.999))
        u[2] = np.log(max(constrained[2], 1e-10))
        return u

    def update(self, params, **kwargs):  # type: ignore[override]
        params = super().update(params, **kwargs)  # type: ignore[assignment]
        mu, phi, sigma_eta = params  # type: ignore[misc]
        self['state_intercept'] = np.array([[mu * (1 - phi)]])
        self['transition'] = np.array([[phi]])
        self['state_cov'] = np.array([[sigma_eta ** 2]])


__all__ = ['fit_rolling_pca', 'LinearizedSV']
