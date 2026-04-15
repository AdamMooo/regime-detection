"""HMM model training, feature engineering (PCA), and regime volatility modeling.

This module handles:
1. Rolling-window PCA with Procrustes alignment for regime stability
2. BIC-based model selection (number of states)
3. Regime naming based on volatility clustering
4. Regime-dependent stochastic volatility (SV) and GARCH models

Functions
---------
fit_rolling_pca(X_scaled, window=252, max_components=10, var_threshold=0.95)
    Rolling PCA with Procrustes alignment
select_states_bic(pcs, n_range=[2,3,4,5], cov_type='full')
    Model selection via BIC
check_stability(pcs, n_states, cov_type='full')
    Regime label stability across random seeds
label_regimes(model, pcs, market)
    Assign volatility-based names to learned regimes
fit_regime_sv(spy_returns, labels, name_map)
    Fit linearized stochastic volatility model per regime
fit_regime_garch(spy_returns, labels, name_map)
    Fit GARCH(1,1) per regime (comparison benchmark)
"""

import logging
import numpy as np
import pandas as pd
from itertools import permutations
from scipy.linalg import orthogonal_procrustes
from sklearn.decomposition import PCA
from arch import arch_model
from statsmodels.tsa.statespace.mlemodel import MLEModel

from src.config import (
    RANDOM_SEED, N_STATES_RANGE, COV_TYPE, N_SEEDS, PCA_MAX_COMPONENTS,
    PCA_VAR_THRESHOLD, PCA_ROLLING_WINDOW, GARCH_P, GARCH_Q, GARCH_DIST,
    MIN_REGIME_OBS, REGIME_NAMES, VOL_BRACKETS, DATA_DIR,
)
from src.core.inference import _fit_hmm, filtered_labels, StudentTHMM

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
# BIC State Selection
# ===================================================================

def _hmm_n_params(n_states, n_features, cov_type):
    """Count free parameters for BIC calculation.

    BIC = -2 * LL + k * log(n) where k is the number of free parameters.

    Parameters
    ----------
    n_states : int
        Number of hidden states
    n_features : int
        Number of features
    cov_type : str
        Covariance type ('full', 'tied', 'diag', 'spherical')

    Returns
    -------
    k : int
        Number of free parameters
    """
    k = n_states * (n_states - 1)  # transition matrix (row-stochastic)
    k += n_states - 1              # initial state probs (sum to 1)
    k += n_states * n_features     # emission means
    if cov_type == 'full':
        k += n_states * n_features * (n_features + 1) // 2
    elif cov_type == 'diag':
        k += n_states * n_features
    else:
        k += n_states * n_features * (n_features + 1) // 2
    return k


def _hmm_bic(model, X, n_states, n_features, cov_type):
    """Compute BIC for HMM model.

    Parameters
    ----------
    model : HMM
        Fitted HMM
    X : ndarray (T, D)
        Training data
    n_states : int
        Number of states
    n_features : int
        Number of features
    cov_type : str
        Covariance type

    Returns
    -------
    bic : float
        BIC score (lower is better)
    ll : float
        Log-likelihood (higher is better)
    """
    ll = model.score(X)
    k = _hmm_n_params(n_states, n_features, cov_type)
    bic = -2 * ll + k * np.log(len(X))
    return bic, ll


def select_states_bic(pcs, n_range=N_STATES_RANGE, cov_type=COV_TYPE):
    """Fit HMM for each K in n_range; return best K by BIC.

    If n_range contains a single value, skip BIC selection and use that value directly.
    Otherwise, performs model selection over a range of state counts. For each K,
    tries multiple random seeds and selects the best (highest likelihood)
    model. BIC score (accounting for model complexity) determines final choice.

    Parameters
    ----------
    pcs : ndarray (T, D)
        Principal component scores
    n_range : list
        Range of state counts to evaluate (e.g., [2, 3, 4, 5])
        If single value (e.g., [4]), uses that K directly (per Phase 2.5.3 decision)
    cov_type : str
        HMM covariance type ('full', 'diag', etc.)

    Returns
    -------
    best_k : int
        Optimal number of states (by BIC)
    best_model : HMM
        Best-fitted model for the chosen K
    bic_df : DataFrame
        BIC scores for all candidates
    """
    # If n_range is a single value, enforce that K (Phase 2.5.3 decision)
    if len(n_range) == 1:
        K = n_range[0]
        print(f"\nK={K} enforced (Phase 2.5.3 walk-forward validation)")
        best_bic, best_ll, best_m = np.inf, -np.inf, None
        for seed in range(min(5, N_SEEDS)):
            m = _fit_hmm(pcs, K, cov_type, seed)
            bic, ll = _hmm_bic(m, pcs, K, pcs.shape[1], cov_type)
            if bic < best_bic:
                best_bic, best_ll, best_m = bic, ll, m
        print(f"  Best model (K={K}): BIC={best_bic:,.0f}, LL={best_ll:,.0f}")

        # Create single-row DataFrame for consistency
        bic_df = pd.DataFrame([
            {'K': K, 'BIC': best_bic, 'LL': best_ll}
        ])
        import os
        bic_df.to_csv(os.path.join(DATA_DIR, 'bic_selection.csv'), index=False)
        return K, best_m, bic_df

    # Standard BIC model selection for multiple K values
    results = []
    print("\nBIC state selection:")
    for K in n_range:
        best_bic, best_ll, best_m = np.inf, -np.inf, None
        for seed in range(min(5, N_SEEDS)):
            m = _fit_hmm(pcs, K, cov_type, seed)
            bic, ll = _hmm_bic(m, pcs, K, pcs.shape[1], cov_type)
            if bic < best_bic:
                best_bic, best_ll, best_m = bic, ll, m
        results.append({'K': K, 'BIC': best_bic, 'LL': best_ll, 'model': best_m})
        print(f"  K={K}:  BIC={best_bic:,.0f}   LL={best_ll:,.0f}")

    bic_df = pd.DataFrame([
        {'K': r['K'], 'BIC': r['BIC'], 'LL': r['LL']} for r in results
    ])
    import os
    bic_df.to_csv(os.path.join(DATA_DIR, 'bic_selection.csv'), index=False)

    best = min(results, key=lambda r: r['BIC'])
    print(f"  -> Best: K={best['K']}  (BIC={best['BIC']:,.0f})")
    return best['K'], best['model'], bic_df


# ===================================================================
# Stability Check
# ===================================================================

def _best_perm_agreement(a, b, n_states):
    """Find best permutation agreement between two label sequences.

    Tries all n_states! permutations and finds the one with highest
    agreement (fraction of matching labels).

    Parameters
    ----------
    a : ndarray (T,)
        First label sequence
    b : ndarray (T,)
        Second label sequence
    n_states : int
        Number of states

    Returns
    -------
    best : float
        Maximum agreement (fraction in [0, 1])
    """
    best = 0
    for perm in permutations(range(n_states)):
        mapped = np.array([perm[x] for x in b])
        best = max(best, np.mean(a == mapped))
    return best


def check_stability(pcs, n_states, cov_type=COV_TYPE):
    """Fit across multiple seeds; return best-LL model and agreement score.

    Checks if regime labels are stable across different random initializations.
    High stability (>90% agreement) indicates robust regime structure.

    Parameters
    ----------
    pcs : ndarray (T, D)
        Principal component scores
    n_states : int
        Number of states
    cov_type : str
        HMM covariance type

    Returns
    -------
    best_model : HMM
        Best model (highest likelihood across all seeds)
    mean_agreement : float
        Mean pairwise agreement across top 5 models (fraction in [0, 1])
    """
    runs = []
    for seed in range(N_SEEDS):
        m = _fit_hmm(pcs, n_states, cov_type, seed)
        runs.append((seed, m.score(pcs), m))
    runs.sort(key=lambda x: -x[1])
    top = runs[:5]

    top_labels = [m.predict(pcs) for _, _, m in top]
    agreements = []
    for i in range(len(top_labels)):
        for j in range(i + 1, len(top_labels)):
            agreements.append(
                _best_perm_agreement(top_labels[i], top_labels[j], n_states),
            )

    mean_agr = np.mean(agreements)
    print(f"\nStability ({N_SEEDS} seeds, top 5):")
    print(f"  Agreement : {mean_agr:.1%} +/- {np.std(agreements):.1%}")
    print(f"  Best seed : {top[0][0]}  (LL={top[0][1]:.2f})")
    return top[0][2], mean_agr


# ===================================================================
# Regime Labeling (Volatility-Based)
# ===================================================================

def label_regimes(model, pcs, market):
    """Assign interpretable names by sorting regimes on VIX mean.

    Uses filtered (forward-only) labels to assign names based on the
    VIX level in each regime. Low-VIX regimes are named "Low-Vol",
    medium-VIX regimes are "Med-Vol", high-VIX regimes are "High-Vol".

    Parameters
    ----------
    model : HMM
        Fitted HMM
    pcs : ndarray (T, D)
        Principal component scores
    market : DataFrame
        Market data including 'VIX' column

    Returns
    -------
    labels : ndarray (T,)
        Regime labels with hysteresis
    name_map : dict
        Mapping from regime index to name (e.g., {0: 'Low-Vol', 1: 'Med-Vol'})
    """
    labels = filtered_labels(model, pcs)
    n = model.n_components
    regime_vix = {
        r: market['VIX'].values[labels == r].mean() for r in range(n)
    }
    sorted_by_vix = sorted(regime_vix, key=lambda k: regime_vix[k])
    names = REGIME_NAMES.get(n, [f'Regime-{i}' for i in range(n)])
    name_map = {sorted_by_vix[i]: names[i] for i in range(n)}
    return labels, name_map


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


def fit_regime_sv(spy_returns, labels, name_map):
    """Fit linearized SV model per regime.

    Fits a linearized stochastic volatility model to each regime's
    returns. SV models capture time-varying volatility with persistence.

    Parameters
    ----------
    spy_returns : Series
        SPY daily log-returns
    labels : ndarray (T,)
        Regime labels
    name_map : dict
        Mapping from regime index to name

    Returns
    -------
    results : dict
        Dictionary with keys: regime indices + 'full'
        Each value is a dict with:
        - 'result': fitted model result
        - 'params': dict of {mu, phi, sigma_eta}
        - 'smoothed_h': smoothed log-volatility
        - 'annualized_vol': annualized volatility %
    """
    y_all = spy_returns.dropna()

    # Transform: z_t = log(r_t^2), floor to avoid log(0) bias
    z_all = np.log(np.maximum(y_all.values ** 2, 1e-10))

    print("\nRegime-Dependent Stochastic Volatility (AR(1) log-vol):")

    # Full-sample SV
    results = {}
    try:
        sv_full = LinearizedSV(z_all)
        res_full = sv_full.fit(disp=False, maxiter=300)
        mu_f, phi_f, se_f = res_full.params  # type: ignore[attr-defined]
        h_smooth_full = res_full.smoothed_state[0]  # type: ignore[attr-defined]
        ann_vol_full = np.exp(h_smooth_full / 2) * np.sqrt(252) * 100
        half_life_f = -np.log(2) / np.log(abs(phi_f)) if abs(phi_f) < 1 else np.inf
        print(f"  Full-sample:  mu={mu_f:.3f}  phi={phi_f:.4f}  "
              f"sigma_eta={se_f:.4f}  half-life={half_life_f:.0f}d  "
              f"mean_vol={ann_vol_full.mean():.1f}%")
        results['full'] = {
            'result': res_full,
            'params': {'mu': mu_f, 'phi': phi_f, 'sigma_eta': se_f},
            'smoothed_h': h_smooth_full,
            'annualized_vol': ann_vol_full,
        }
    except Exception as e:
        print(f"  Full-sample SV fit failed: {e}")
        results['full'] = {'result': None, 'smoothed_h': None,
                           'annualized_vol': None}

    label_series = pd.Series(labels, index=spy_returns.index[:len(labels)])

    for r in sorted(name_map.keys()):
        mask = (label_series == r)
        y = spy_returns[mask].dropna()

        if len(y) < MIN_REGIME_OBS:
            print(f"  {name_map[r]:12s}: skipped ({len(y)} obs < {MIN_REGIME_OBS})")
            continue

        z = np.log(np.maximum(y.values ** 2, 1e-10))

        try:
            sv_model = LinearizedSV(z)
            res = sv_model.fit(disp=False, maxiter=300)
            mu, phi, sigma_eta = res.params  # type: ignore[attr-defined]
            h_smooth = res.smoothed_state[0]  # type: ignore[attr-defined]
            ann_vol = np.exp(h_smooth / 2) * np.sqrt(252) * 100

            results[r] = {
                'result': res,
                'params': {'mu': mu, 'phi': phi, 'sigma_eta': sigma_eta},
                'smoothed_h': h_smooth,
                'annualized_vol': ann_vol,
            }

            half_life = -np.log(2) / np.log(abs(phi)) if abs(phi) < 1 else np.inf
            print(f"  {name_map[r]:12s}: mu={mu:.3f}  phi={phi:.4f}  "
                  f"sigma_eta={sigma_eta:.4f}  half-life={half_life:.0f}d  "
                  f"mean_vol={ann_vol.mean():.1f}%  (n={len(y)})")
        except Exception:
            print(f"  {name_map[r]:12s}: SV fit failed (n={len(y)})")

    return results


# ===================================================================
# Regime-Dependent GARCH (comparison benchmark)
# ===================================================================

def fit_regime_garch(spy_returns, labels, name_map):
    """Fit GARCH(1,1) per regime on SPY daily log-returns.

    Fits GARCH models to compare with stochastic volatility. GARCH is
    faster but less flexible than SV for time-varying volatility.

    Parameters
    ----------
    spy_returns : Series
        SPY daily log-returns
    labels : ndarray (T,)
        Regime labels
    name_map : dict
        Mapping from regime index to name

    Returns
    -------
    results : dict
        Dictionary with keys: regime indices + 'full'
        Each value is a fitted GARCH model result
    """
    y_all = spy_returns.dropna() * 100  # percent returns for arch

    am_all = arch_model(y_all, vol='GARCH', p=GARCH_P, q=GARCH_Q,
                        mean='Zero', dist=GARCH_DIST)
    res_all = am_all.fit(disp='off')
    cond_vol_all = res_all.conditional_volatility

    print("\nRegime-Dependent GARCH(1,1):")
    print(f"  Full-sample:  w={res_all.params.get('omega', np.nan):.4f}  "
          f"a={res_all.params.get('alpha[1]', np.nan):.4f}  "
          f"b={res_all.params.get('beta[1]', np.nan):.4f}")

    results = {'full': res_all}
    label_series = pd.Series(labels, index=spy_returns.index[:len(labels)])

    for r in sorted(name_map.keys()):
        mask = (label_series == r)
        y = (spy_returns[mask].dropna()) * 100
        vol_in_regime = cond_vol_all.reindex(y.index).dropna()  # type: ignore[union-attr]

        if len(y) < MIN_REGIME_OBS:
            print(f"  {name_map[r]:12s}: skipped ({len(y)} obs < {MIN_REGIME_OBS})")
            continue

        am = arch_model(y, vol='GARCH', p=GARCH_P, q=GARCH_Q,
                        mean='Zero', dist=GARCH_DIST)
        try:
            res = am.fit(disp='off')
            omega = res.params.get('omega', np.nan)
            alpha = res.params.get('alpha[1]', np.nan)
            beta = res.params.get('beta[1]', np.nan)
            results[r] = res
            persist = alpha + beta
            print(f"  {name_map[r]:12s}: w={omega:.4f}  a={alpha:.4f}  "
                  f"b={beta:.4f}  persist={persist:.4f}  "
                  f"mean_vol={vol_in_regime.mean():.2f}  (n={len(y)})")
        except Exception:
            print(f"  {name_map[r]:12s}: GARCH fit failed (n={len(y)})")

    return results


__all__ = [
    'fit_rolling_pca',
    'select_states_bic',
    'check_stability',
    'label_regimes',
    'fit_regime_sv',
    'fit_regime_garch',
]
