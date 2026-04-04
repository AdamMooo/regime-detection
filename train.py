"""
PCA -> HMM -> Regime-Dependent SV Pipeline
==========================================
Supports two HMM backends:
  A) Classic Student-t HMM  (USE_HDP=False)  — fast EM-based via hmmlearn
  B) Bayesian HDP-HMM       (USE_HDP=True)   — auto-K via NumPyro MCMC

Pipeline:
1. Rolling PCA (Procrustes-aligned)  -> principal components + market-mode ratio
2. HMM regime detection              -> labels + probabilities
3. Forward-only filter               -> real-time regime detection (no lookahead)
4. Regime-dependent SV / GARCH       -> per-regime volatility models
5. Walk-forward OOS validation        -> expanding or rolling window
6. 3D regime visualizations           -> probability surfaces + KDE densities
"""

import json
import logging
import os
import warnings

import joblib

import numpy as np
import pandas as pd
from arch import arch_model
from hmmlearn import hmm
from itertools import permutations
from scipy.linalg import orthogonal_procrustes
from scipy.stats import multivariate_t as _mvt, norm as _norm, gaussian_kde
from sklearn.decomposition import PCA
from statsmodels.tsa.statespace.mlemodel import MLEModel

from config import (
    RANDOM_SEED, N_STATES, N_STATES_RANGE, COV_TYPE, T_DF,
    N_SEEDS, HMM_ITER, PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD,
    PCA_ROLLING_WINDOW, VIX_BYPASS, USE_HDP, HDP_INFERENCE, HDP_MAX_REGIMES,
    GARCH_P, GARCH_Q, GARCH_DIST, MIN_REGIME_OBS, REGIME_HOLD_DAYS,
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS,
    WALK_FORWARD_MODE, VAR_ALPHA, FEATURE_SUBSET,
    REGIME_NAMES, VOL_BRACKETS, DATA_DIR, MODEL_DIR, FIGURE_DIR, TICKERS,
    MAX_DATA_STALENESS_DAYS,
)
from features import build_features
from signals import compute_signals
from dashboard import build_interactive_dashboard, _get_blocks

# Suppress noisy warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='.*did not converge.*')
warnings.filterwarnings('ignore', message='.*KMeans.*')
warnings.filterwarnings('ignore', message='.*Optimization.*')
warnings.filterwarnings('ignore', message='.*overflow.*')
warnings.filterwarnings('ignore', message='.*divide by zero.*')
logging.getLogger('hmmlearn').setLevel(logging.ERROR)
logging.getLogger('statsmodels').setLevel(logging.ERROR)


# ===================================================================
# Expanding-window standardization (shared by train + walk_forward)
# ===================================================================

def expanding_standardize(X_raw, min_warmup=252):
    """Expanding-window z-score: row t uses mean/std from [0..t] only.

    Parameters
    ----------
    X_raw : ndarray (T, D)
    min_warmup : int — first N rows get NaN (unstable statistics)

    Returns
    -------
    X_scaled : ndarray (T, D)
    cum_mean_final : ndarray (D,) — cumulative mean at last row
    cum_std_final : ndarray (D,) — cumulative std at last row
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
# Student-t HMM
# ===================================================================

class StudentTHMM(hmm.GaussianHMM):
    """GaussianHMM with Student-t emission log-likelihoods."""

    def _compute_log_likelihood(self, X):
        ll = np.empty((len(X), self.n_components))
        for k in range(self.n_components):
            ll[:, k] = _mvt.logpdf(
                X, loc=self.means_[k], shape=self.covars_[k], df=T_DF,  # type: ignore[index]
            )
        return ll


def _fit_hmm(X, n_states, cov_type, seed):
    m = StudentTHMM(
        n_components=n_states, covariance_type=cov_type,
        n_iter=HMM_ITER, random_state=seed, verbose=False,
    )
    m.fit(X)
    return m


def filtered_probs(model, X):
    """
    Forward-only (filtered) regime probabilities — NO future lookahead.

    Unlike predict_proba() which uses forward-backward (smoothed),
    this only uses information up to time t for P(state_t | x_1..x_t).
    This is the correct real-time / online regime estimate.
    """
    log_ll = model._compute_log_likelihood(X)
    n_states = model.n_components
    T = len(X)

    # Forward pass only
    alpha = np.zeros((T, n_states))
    log_startprob = np.log(model.startprob_ + 1e-300)
    log_transmat = np.log(model.transmat_ + 1e-300)

    # t = 0
    alpha[0] = log_startprob + log_ll[0]
    alpha[0] -= np.logaddexp.reduce(alpha[0])

    # t = 1..T-1
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


def filtered_labels(model, X, hold_days=REGIME_HOLD_DAYS):
    """Argmax of filtered probabilities with hysteresis to prevent flicker.

    A regime switch only takes effect after the new regime has been the
    argmax for *hold_days* consecutive days.  This eliminates 1-2 day
    noise-driven flips while keeping genuine transitions fast.
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


# ===================================================================
# 1. Rolling PCA
# ===================================================================

def fit_rolling_pca(X_scaled, window=PCA_ROLLING_WINDOW,
                    max_components=PCA_MAX_COMPONENTS,
                    var_threshold=PCA_VAR_THRESHOLD):
    """
    Rolling-window PCA with sign alignment.

    For each day t (t >= window-1), fits PCA on X_scaled[t-window+1 : t+1].
    Returns the last row's projection as that day's PC scores.

    Returns
    -------
    pcs          : ndarray (T_valid x n_selected)
    mode_ratio   : ndarray (T_valid,) -- lambda_1 / sum(lambda)
    valid_mask   : bool array (T,)
    n_selected   : int
    last_pca     : PCA object from the final window
    """
    T, D = X_scaled.shape
    n_comp = min(max_components, D)

    all_scores = np.full((T, n_comp), np.nan)
    mode_ratio = np.full(T, np.nan)
    prev_loadings = None
    pca: PCA | None = None

    for t in range(window - 1, T):
        chunk = X_scaled[t - window + 1: t + 1]
        pca = PCA(n_components=n_comp, random_state=RANDOM_SEED)
        scores = pca.fit_transform(chunk)

        # Procrustes alignment: jointly align all components with previous window
        if prev_loadings is not None:
            # orthogonal_procrustes(A, B) finds R s.t. A @ R ≈ B
            # A = components_.T (D, K), B = prev_loadings.T (D, K) → R is (K, K)
            # Then components_.T @ R ≈ prev_loadings.T → R.T @ components_ ≈ prev_loadings
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
# 2. BIC State Selection
# ===================================================================

def _hmm_n_params(n_states, n_features, cov_type):
    """Count free parameters for BIC."""
    k = n_states * (n_states - 1)
    k += n_states - 1
    k += n_states * n_features
    if cov_type == 'full':
        k += n_states * n_features * (n_features + 1) // 2
    elif cov_type == 'diag':
        k += n_states * n_features
    else:
        k += n_states * n_features * (n_features + 1) // 2
    return k


def _hmm_bic(model, X, n_states, n_features, cov_type):
    ll = model.score(X)
    k  = _hmm_n_params(n_states, n_features, cov_type)
    bic = -2 * ll + k * np.log(len(X))
    return bic, ll


def select_states_bic(pcs, n_range=N_STATES_RANGE, cov_type=COV_TYPE):
    """Fit HMM for each K in *n_range*; return best K by BIC."""
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
    bic_df.to_csv(os.path.join(DATA_DIR, 'bic_selection.csv'), index=False)

    best = min(results, key=lambda r: r['BIC'])
    print(f"  -> Best: K={best['K']}  (BIC={best['BIC']:,.0f})")
    return best['K'], best['model'], bic_df


# ===================================================================
# 3. Stability Check
# ===================================================================

def _best_perm_agreement(a, b, n_states):
    best = 0
    for perm in permutations(range(n_states)):
        mapped = np.array([perm[x] for x in b])
        best = max(best, np.mean(a == mapped))
    return best


def check_stability(pcs, n_states, cov_type=COV_TYPE):
    """Fit across N_SEEDS seeds; return best-LL model and agreement."""
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
# 4. Regime Labeling
# ===================================================================

def label_regimes(model, pcs, market):
    """Assign interpretable names by sorting regimes on raw VIX mean.
    Uses filtered (forward-only) labels — no future lookahead."""
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
# 5. Linearized Stochastic Volatility Model
# ===================================================================

# Constants for the log-chi-squared(1) approximation
_LOG_CHI2_MEAN = -1.2704   # E[log(eps^2)] where eps ~ N(0,1)
_LOG_CHI2_VAR  = np.pi ** 2 / 2   # Var[log(eps^2)] ~ 4.935


class LinearizedSV(MLEModel):
    """
    Linearized stochastic volatility model estimated via Kalman filter.

    Observation : z_t = c + h_t + xi_t,   xi_t ~ N(0, pi^2/2)
    State       : h_t = mu(1-phi) + phi*h_{t-1} + sigma_eta*eta_t

    where z_t = log(r_t^2), c = E[log(eps^2)] = -1.2704,
    and h_t is the latent log-volatility.

    Parameters: mu (long-run log-vol), phi (persistence), sigma_eta (vol-of-vol)
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
    """
    Fit linearized SV model per regime.

    Returns dict  {regime_id: {params, smoothed_h, annualized_vol}, 'full': ...}
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
# 6. Regime-Dependent GARCH (comparison benchmark)
# ===================================================================

def fit_regime_garch(spy_returns, labels, name_map):
    """Fit GARCH(1,1) per regime on SPY daily log-returns."""
    y_all = spy_returns.dropna() * 100          # percent returns for arch

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
            beta  = res.params.get('beta[1]', np.nan)
            results[r] = res
            persist = alpha + beta
            print(f"  {name_map[r]:12s}: w={omega:.4f}  a={alpha:.4f}  "
                  f"b={beta:.4f}  persist={persist:.4f}  "
                  f"mean_vol={vol_in_regime.mean():.2f}  (n={len(y)})")
        except Exception:
            print(f"  {name_map[r]:12s}: GARCH fit failed (n={len(y)})")

    return results


# ===================================================================
# 7. Walk-Forward Validation
# ===================================================================

def walk_forward(market, features, n_states, n_pca, cov_type=COV_TYPE,
                 mode=WALK_FORWARD_MODE):
    """
    Walk-forward validation with expanding or rolling window.

    mode='expanding': training window grows over time (all past data).
    mode='rolling':   fixed-length training window (most recent N years).

    Each fold:  standardize on train -> PCA on last ROLLING_WINDOW days
    -> project full train -> HMM -> predict test
    """
    # Note: features are already subset-filtered by train() before this call

    min_train = WALK_FORWARD_TRAIN_YEARS * 252
    step      = WALK_FORWARD_STEP_DAYS

    oos_name_labels = pd.Series(index=features.index, dtype=object)
    oos_name_labels[:] = np.nan

    t = min_train
    step_num = 0
    while t < len(features):
        end = min(t + step, len(features))

        if mode == 'rolling':
            # Fixed-length rolling window
            train_start = max(0, t - min_train)
            train_feats = features.iloc[train_start:t]
        else:
            # Expanding window (all past data)
            train_feats = features.iloc[:t]
        test_feats  = features.iloc[t:end]

        if len(test_feats) == 0:
            t = end
            continue

        # Expanding-window standardize (match train() pipeline exactly)
        X_combined = np.vstack([train_feats.values, test_feats.values])
        wf_warmup = min(252, max(50, len(train_feats) // 4))
        X_all_scaled, _, _ = expanding_standardize(X_combined, min_warmup=wf_warmup)
        X_train = X_all_scaled[:len(train_feats)]
        X_test = X_all_scaled[len(train_feats):]

        # Drop warm-up NaN rows from training data
        valid_train = ~np.isnan(X_train[:, 0])
        X_train = X_train[valid_train]
        train_feats_valid = train_feats[valid_train]

        # PCA: fit on last ROLLING_WINDOW days of train, project all
        pca_window = min(PCA_ROLLING_WINDOW, len(X_train))
        n_comp = min(n_pca, X_train.shape[1])
        pca_wf = PCA(n_components=n_comp, random_state=RANDOM_SEED)
        pca_wf.fit(X_train[-pca_window:])
        pc_train = pca_wf.transform(X_train)
        pc_test  = pca_wf.transform(X_test)

        # VIX bypass: append scaled VIX directly to PCs
        if VIX_BYPASS:
            vix_train = market['VIX'].reindex(train_feats_valid.index).values
            vix_test  = market['VIX'].reindex(test_feats.index).values
            v_mean, v_std = vix_train.mean(), vix_train.std()
            pc_train = np.hstack([pc_train, ((vix_train - v_mean) / v_std).reshape(-1, 1)])
            pc_test  = np.hstack([pc_test,  ((vix_test  - v_mean) / v_std).reshape(-1, 1)])

        # HMM (fit on train PCs, pick best seed)
        best_m, best_ll = None, -np.inf
        for seed in range(5):
            m = _fit_hmm(pc_train, n_states, cov_type, seed)
            ll = m.score(pc_train)
            if ll > best_ll:
                best_m, best_ll = m, ll

        assert best_m is not None
        raw_preds = filtered_labels(best_m, pc_test, hold_days=REGIME_HOLD_DAYS)

        # Assign vol-bracket names using training-window SPY returns
        train_labels = filtered_labels(best_m, pc_train, hold_days=REGIME_HOLD_DAYS)
        spy_col = 'SPY_close' if 'SPY_close' in market.columns else 'SPY_Close'
        spy_train = market[spy_col].reindex(train_feats_valid.index)
        spy_ret_train = np.log(spy_train / spy_train.shift(1)).dropna().values

        # Build per-state vol-bracket name map for this fold
        # (align train_labels with available returns — drop first row for diff)
        tl_aligned = train_labels[1:len(spy_ret_train) + 1]
        fold_vol = {}
        for r in range(n_states):
            mask = (tl_aligned == r)
            if mask.sum() > 5:
                fold_vol[r] = float(np.std(spy_ret_train[mask]) * np.sqrt(252) * 100)
            else:
                fold_vol[r] = 0.0

        # Map each state to its vol-bracket name
        fold_name_map = {}
        name_counts = {}
        for r in sorted(fold_vol, key=lambda k: fold_vol[k]):
            vol = fold_vol[r]
            bracket_name = f'Regime-{r}'
            for lo, hi, bname in VOL_BRACKETS:
                if lo <= vol < hi:
                    bracket_name = bname
                    break
            name_counts[bracket_name] = name_counts.get(bracket_name, 0) + 1
            if name_counts[bracket_name] > 1:
                bracket_name = f"{bracket_name}-{chr(64 + name_counts[bracket_name])}"
            fold_name_map[r] = bracket_name

        # Store OOS labels as vol-bracket names for direct IS-OOS comparison
        oos_name_labels.iloc[t:end] = [fold_name_map.get(r, f'Regime-{r}') for r in raw_preds]

        step_num += 1
        if step_num % 10 == 0:
            print(f"    step {step_num}")
        t = end

    valid_names = oos_name_labels.dropna()
    # Convert string names to integer labels with a unified name_map
    unique_names = sorted(valid_names.unique())
    name_to_int = {name: i for i, name in enumerate(unique_names)}
    name_map = {i: name for i, name in enumerate(unique_names)}
    valid = valid_names.map(name_to_int).astype(int)
    return valid, name_map


# ===================================================================
# 8. Evaluation
# ===================================================================

def evaluate(market, labels, name_map, spy_ret, label_source='In-Sample'):
    """Print regime characteristics using 5-day SPY returns (independent)."""
    print(f"\nRegime Characteristics ({label_source}):")
    hdr = (f"  {'Regime':<14s} {'Days':>6s} {'Pct':>6s} {'VIX':>7s} "
           f"{'SPY5d':>7s}")
    print(hdr)
    print(f"  {'-' * 44}")

    for r in sorted(name_map.keys()):
        name = name_map[r]
        if hasattr(labels, 'index'):
            idx = labels.index[labels == r]
        else:
            idx = market.index[labels == r]
        n   = len(idx)
        pct = n / len(labels) * 100

        vix_m = market.loc[idx, 'VIX'].mean() if 'VIX' in market else np.nan
        sp_m  = spy_ret.reindex(idx).mean() * 100

        print(f"  {name:<14s} {n:>6d} {pct:>5.1f}% {vix_m:>7.1f} "
              f"{sp_m:>+6.2f}%")

    # Bootstrap confidence intervals for key statistics
    _print_bootstrap_cis(market, labels, name_map, spy_ret, label_source)


def _print_bootstrap_cis(market, labels, name_map, spy_ret, label_source,
                         n_boot=1000, block_size=21, ci=90):
    """Block bootstrap 90% confidence intervals for regime statistics."""
    label_arr = np.asarray(labels)
    T = len(label_arr)
    if T < block_size * 2:
        return

    n_blocks = (T + block_size - 1) // block_size
    rng = np.random.RandomState(RANDOM_SEED)

    # Pre-extract aligned data
    vix = market['VIX'].values if 'VIX' in market.columns else None
    spy = spy_ret.reindex(market.index).values if spy_ret is not None else None

    boot_stats = {r: {'vix': [], 'duration': [], 'persist': []}
                  for r in name_map}

    for _ in range(n_boot):
        # Draw block-bootstrap indices
        block_starts = rng.randint(0, T - block_size + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, min(s + block_size, T))
                              for s in block_starts])[:T]

        boot_labels = label_arr[idx]
        for r in name_map:
            mask = boot_labels == r
            if mask.sum() < 5:
                continue
            if vix is not None:
                boot_stats[r]['vix'].append(float(vix[idx][mask].mean()))
            # Block durations
            blocks = _get_blocks(mask)
            if blocks:
                boot_stats[r]['duration'].append(
                    float(np.mean([e - s + 1 for s, e in blocks])))
            # Self-transition rate
            transitions = np.sum(
                (boot_labels[:-1] == r) & (boot_labels[1:] == r))
            total = max(np.sum(boot_labels[:-1] == r), 1)
            boot_stats[r]['persist'].append(float(transitions / total))

    lo = (100 - ci) / 2
    hi = 100 - lo
    print(f"\n  Bootstrap {ci}% CIs ({label_source}, block={block_size}d, n={n_boot}):")
    print(f"  {'Regime':<14s} {'VIX':>18s} {'Avg Dur':>18s} {'Persist':>18s}")
    print(f"  {'-' * 70}")
    for r in sorted(name_map.keys()):
        name = name_map[r]
        parts = []
        for stat in ['vix', 'duration', 'persist']:
            vals = boot_stats[r][stat]
            if len(vals) >= 10:
                l, h = np.percentile(vals, [lo, hi])
                if stat == 'persist':
                    parts.append(f"[{l:.1%}, {h:.1%}]")
                elif stat == 'duration':
                    parts.append(f"[{l:.0f}d, {h:.0f}d]")
                else:
                    parts.append(f"[{l:.1f}, {h:.1f}]")
            else:
                parts.append(f"{'N/A':>18s}")
        print(f"  {name:<14s} {parts[0]:>18s} {parts[1]:>18s} {parts[2]:>18s}")


def compute_var_backtest(spy_returns, labels, name_map, alpha=VAR_ALPHA):
    """Simple VaR back-test: regime-conditional Gaussian VaR."""
    z = _norm.ppf(alpha)
    print(f"\nVaR Back-test ({1 - alpha:.0%} confidence):")

    total_exc, total_n = 0, 0
    for r in sorted(name_map.keys()):
        if hasattr(labels, 'index'):
            idx = labels.index[labels == r]
        else:
            idx = spy_returns.index[labels == r]
        y = spy_returns.reindex(idx).dropna()
        if len(y) < 30:
            continue
        mu, sigma = y.mean(), y.std()
        var_level = mu + z * sigma
        exc = (y < var_level).sum()
        rate = exc / len(y)
        total_exc += exc
        total_n += len(y)
        print(f"  {name_map[r]:12s}: VaR={var_level * 100:+.2f}%  "
              f"exc={exc}/{len(y)} ({rate:.1%})  expected~{alpha:.1%}")

    if total_n > 0:
        overall_rate = total_exc / total_n
        print(f"  Overall      : exc={total_exc}/{total_n} ({overall_rate:.1%})")

        # Kupiec Proportion of Failures (POF) test
        kupiec_p = kupiec_pof_test(total_n, total_exc, alpha)
        # Christoffersen Independence test
        chris_p = christoffersen_test(spy_returns, labels, name_map, alpha)
        print(f"  Kupiec POF p-value    : {kupiec_p:.4f}"
              f"  {'(OK)' if kupiec_p > 0.05 else '(REJECT — VaR miscalibrated)'}")
        print(f"  Christoffersen p-value: {chris_p:.4f}"
              f"  {'(OK)' if chris_p > 0.05 else '(REJECT — exceedances cluster)'}")


def kupiec_pof_test(n_obs, n_exc, alpha):
    """
    Kupiec (1995) Proportion of Failures test.
    H0: true exceedance rate = alpha.
    Returns p-value from likelihood ratio chi-squared test.
    """
    from scipy.stats import chi2
    p0 = alpha
    p_hat = n_exc / n_obs if n_obs > 0 else 0
    if p_hat == 0 or p_hat == 1:
        return 1.0  # degenerate case
    lr = -2 * (
        n_exc * np.log(p0) + (n_obs - n_exc) * np.log(1 - p0)
        - n_exc * np.log(p_hat) - (n_obs - n_exc) * np.log(1 - p_hat)
    )
    return float(chi2.sf(lr, df=1))


def christoffersen_test(spy_returns, labels, name_map, alpha):
    """
    Christoffersen (1998) Independence test for VaR exceedances.
    Tests that exceedances are not clustered (i.i.d. Bernoulli).
    Returns p-value from likelihood ratio chi-squared test.
    """
    from scipy.stats import chi2
    z = _norm.ppf(alpha)

    # Build full exceedance indicator series
    hits = pd.Series(0, index=spy_returns.index, dtype=int)
    for r in sorted(name_map.keys()):
        if hasattr(labels, 'index'):
            idx = labels.index[labels == r]
        else:
            idx = spy_returns.index[labels == r]
        y = spy_returns.reindex(idx).dropna()
        if len(y) < 30:
            continue
        mu, sigma = y.mean(), y.std()
        var_level = mu + z * sigma
        hits.loc[y.index] = (y < var_level).astype(int)

    hits = hits.dropna().values
    if len(hits) < 10:
        return 1.0

    # 2x2 transition counts: n_ij = count of (hit_{t-1}=i, hit_t=j)
    n00 = n01 = n10 = n11 = 0
    for t in range(1, len(hits)):
        i, j = hits[t - 1], hits[t]
        if i == 0 and j == 0: n00 += 1
        elif i == 0 and j == 1: n01 += 1
        elif i == 1 and j == 0: n10 += 1
        else: n11 += 1

    # Transition probabilities
    p01 = n01 / max(n00 + n01, 1)
    p11 = n11 / max(n10 + n11, 1)
    p_hat = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)

    if p_hat == 0 or p_hat == 1 or p01 == 0 or p11 == 0:
        return 1.0

    # LR statistic for independence
    def _safe_log(x):
        return np.log(max(x, 1e-300))

    lr = -2 * (
        n00 * _safe_log(1 - p_hat) + n01 * _safe_log(p_hat)
        + n10 * _safe_log(1 - p_hat) + n11 * _safe_log(p_hat)
        - n00 * _safe_log(1 - p01) - n01 * _safe_log(p01)
        - n10 * _safe_log(1 - p11) - n11 * _safe_log(p11)
    )
    return float(chi2.sf(max(lr, 0), df=1))


def compute_var_backtest_garch(spy_returns, regime_probs, labels, name_map,
                               garch_results, alpha=VAR_ALPHA):
    """
    GARCH-conditional, probability-weighted VaR back-test.

    For each regime k, runs the GARCH(1,1) recursion with that regime's
    (ω_k, α_k, β_k) over the full return series to get σ_{k,t}.
    Then blends: VaR(t) = Σ_k P(regime=k|t) × z × σ_{k,t}.

    This adapts VaR *within* a regime (via GARCH dynamics) and smooths
    across regimes during transitions (via probability weighting).
    """
    z = _norm.ppf(alpha)
    ordered = sorted(name_map.keys())

    # Full-sample GARCH conditional vol for index alignment
    cond_vol_full = garch_results['full'].conditional_volatility
    common_idx = spy_returns.index.intersection(cond_vol_full.index)

    if len(common_idx) < 30:
        print("\nGARCH-Conditional VaR: insufficient data, skipping.")
        return

    spy_ret = spy_returns.loc[common_idx]
    ret_pct = spy_ret.values * 100  # decimal → % (arch convention)
    T_len = len(common_idx)

    # --- Compute per-regime GARCH σ_t paths over full return series ---
    # GARCH(1,1): σ²_t = ω + α × ε²_{t-1} + β × σ²_{t-1}
    # Each regime's parameters produce a different vol path.
    regime_vol = {}  # r -> ndarray shape (T_len,) in % daily
    full_res = garch_results['full']
    full_omega = full_res.params.get('omega', 0.04)
    full_alpha = full_res.params.get('alpha[1]', 0.10)
    full_beta = full_res.params.get('beta[1]', 0.85)

    for r in ordered:
        if r in garch_results and hasattr(garch_results[r], 'params'):
            res_r = garch_results[r]
            omega = res_r.params.get('omega', full_omega)
            alpha_g = res_r.params.get('alpha[1]', full_alpha)
            beta_g = res_r.params.get('beta[1]', full_beta)
        else:
            omega, alpha_g, beta_g = full_omega, full_alpha, full_beta

        # Run GARCH recursion with regime-k params on full return series
        sig2 = np.empty(T_len)
        # Initialize with unconditional variance
        persist = alpha_g + beta_g
        if persist < 1:
            sig2[0] = omega / (1 - persist)
        else:
            sig2[0] = ret_pct[:20].var() if T_len >= 20 else 1.0
        for t in range(1, T_len):
            sig2[t] = omega + alpha_g * ret_pct[t - 1] ** 2 + beta_g * sig2[t - 1]
            sig2[t] = max(sig2[t], 1e-8)  # floor
        regime_vol[r] = np.sqrt(sig2) / 100  # % → decimal

    # Align filtered probs to common_idx
    if hasattr(regime_probs, 'loc'):
        prob_arr = regime_probs.loc[common_idx].values
    else:
        label_idx = labels.index if hasattr(labels, 'index') else spy_returns.index
        prob_df = pd.DataFrame(regime_probs, index=label_idx[:len(regime_probs)])
        prob_arr = prob_df.reindex(common_idx).values

    # Blend: VaR(t) = Σ_k P(k|t) × z × σ_{k,t}
    blended_var = np.zeros(T_len)
    for k_idx, r in enumerate(ordered):
        if k_idx >= prob_arr.shape[1]:
            continue
        var_k = z * regime_vol[r]  # negative (left tail)
        blended_var += prob_arr[:, k_idx] * var_k

    # Exceedances
    label_arr = labels.loc[common_idx].values if hasattr(labels, 'loc') else labels
    ret_arr = spy_ret.values
    hits = (ret_arr < blended_var).astype(int)
    total_exc = int(hits.sum())
    total_n = len(hits)

    print(f"\nGARCH-Conditional VaR Back-test ({1 - alpha:.0%} confidence):")

    for r in ordered:
        mask = (label_arr == r)
        n_r = int(mask.sum())
        if n_r < 30:
            continue
        exc_r = int(hits[mask].sum())
        mean_var_r = blended_var[mask].mean() * 100
        mean_vol_r = regime_vol[r][mask].mean() * 100
        print(f"  {name_map[r]:12s}: VaR={mean_var_r:+.2f}%  "
              f"exc={exc_r}/{n_r} ({exc_r/n_r:.1%})  "
              f"vol={mean_vol_r:.2f}%  expected~{alpha:.1%}")

    overall_rate = total_exc / total_n if total_n > 0 else 0
    print(f"  Overall      : exc={total_exc}/{total_n} ({overall_rate:.1%})")

    # Kupiec POF test
    kupiec_p = kupiec_pof_test(total_n, total_exc, alpha)
    print(f"  Kupiec POF p-value    : {kupiec_p:.4f}"
          f"  {'(OK)' if kupiec_p > 0.05 else '(REJECT — VaR miscalibrated)'}")

    # Christoffersen Independence test on the blended VaR
    n00 = n01 = n10 = n11 = 0
    for t in range(1, len(hits)):
        i, j = hits[t - 1], hits[t]
        if i == 0 and j == 0: n00 += 1
        elif i == 0 and j == 1: n01 += 1
        elif i == 1 and j == 0: n10 += 1
        else: n11 += 1

    p01 = n01 / max(n00 + n01, 1)
    p11 = n11 / max(n10 + n11, 1)
    p_hat = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)

    if p_hat == 0 or p_hat == 1 or p01 == 0 or p11 == 0:
        chris_p = 1.0
    else:
        from scipy.stats import chi2
        def _sl(x): return np.log(max(x, 1e-300))
        lr = -2 * (
            n00 * _sl(1 - p_hat) + n01 * _sl(p_hat)
            + n10 * _sl(1 - p_hat) + n11 * _sl(p_hat)
            - n00 * _sl(1 - p01) - n01 * _sl(p01)
            - n10 * _sl(1 - p11) - n11 * _sl(p11)
        )
        chris_p = float(chi2.sf(max(lr, 0), df=1))

    print(f"  Christoffersen p-value: {chris_p:.4f}"
          f"  {'(OK)' if chris_p > 0.05 else '(REJECT — exceedances cluster)'}")


# Dashboard functions moved to dashboard.py
# ===================================================================
# Main
# ===================================================================

def train():
    np.random.seed(RANDOM_SEED)
    os.makedirs(FIGURE_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ── Load data ──────────────────────────────────────────────────
    market = pd.read_csv(
        os.path.join(DATA_DIR, 'market_data.csv'),
        index_col=0, parse_dates=True,
    )

    # Data freshness check
    last_date = market.index[-1]
    today = pd.Timestamp.now().normalize()
    trading_days_stale = int(np.busday_count(
        last_date.date(), today.date()
    ))
    if trading_days_stale > MAX_DATA_STALENESS_DAYS:
        warnings.warn(
            f"market_data.csv is {trading_days_stale} trading days old "
            f"(last date: {last_date.date()}). Run 'python run.py collect' "
            f"to refresh.",
            UserWarning, stacklevel=2,
        )

    feat_raw = pd.read_csv(
        os.path.join(DATA_DIR, 'features_transformed.csv'),
        index_col=0, parse_dates=True,
    )

    assert len(feat_raw) >= 252, (
        f"Insufficient feature data: {len(feat_raw)} rows (need >= 252 = 1 year)."
    )
    nan_pct = feat_raw.isnull().mean()
    bad_cols = nan_pct[nan_pct > 0.1]
    if len(bad_cols) > 0:
        print(f"  WARNING: {len(bad_cols)} features have >10% NaN: "
              f"{list(bad_cols.index[:5])}")

    # Apply feature subset to reduce collinearity before PCA.
    if FEATURE_SUBSET is not None:
        available = [f for f in FEATURE_SUBSET if f in feat_raw.columns]
        dropped = [f for f in FEATURE_SUBSET if f not in feat_raw.columns]
        if dropped:
            print(f"  Feature subset: {len(dropped)} requested features not found: {dropped}")
        feat_raw = feat_raw[available]
        print(f"  Feature subset: {len(available)} of {len(FEATURE_SUBSET)} features selected")

    # ── Feature health diagnostics ─────────────────────────────────
    print("\nFeature health check (post-transform, pre-standardization):")
    _feat_stds = feat_raw.std()
    _dead = _feat_stds[_feat_stds < 1e-8]
    if len(_dead) > 0:
        print(f"  CRITICAL: {len(_dead)} features have near-zero variance: "
              f"{list(_dead.index)} — dropping them")
        feat_raw = feat_raw.drop(columns=_dead.index)
    _feat_skew = feat_raw.skew()
    _high_skew = _feat_skew[_feat_skew.abs() > 5]
    if len(_high_skew) > 0:
        print(f"  WARNING: {len(_high_skew)} features still heavily skewed "
              f"after transforms: {list(_high_skew.index)}")
    _corr = feat_raw.corr()
    _high_corr = []
    for _i in range(len(_corr)):
        for _j in range(_i + 1, len(_corr)):
            if abs(_corr.iloc[_i, _j]) > 0.95:
                _high_corr.append(
                    f"{_corr.index[_i]}<->{_corr.columns[_j]} "
                    f"({_corr.iloc[_i, _j]:.2f})")
    if _high_corr:
        print(f"  WARNING: highly correlated pairs: {_high_corr}")
    if len(_dead) == 0 and len(_high_skew) == 0 and not _high_corr:
        print("  All {0} features OK".format(len(feat_raw.columns)))

    # ── Expanding-window standardization (causal) ──────────────────
    # Each day t is z-scored using mean/std computed from days [0..t] only.
    # This prevents future statistics from leaking into early PCA windows.
    _MIN_WARMUP = 252
    X_scaled, _, _ = expanding_standardize(feat_raw.values, min_warmup=_MIN_WARMUP)
    print(f"  Expanding-window standardization: {_MIN_WARMUP}-day warm-up, "
          f"{len(feat_raw) - _MIN_WARMUP} valid days")

    feat_scaled = pd.DataFrame(
        X_scaled, columns=feat_raw.columns, index=feat_raw.index,
    )

    # Align market to feature dates
    market = market.loc[feat_scaled.index]

    # SPY returns (independent evaluation -- not in HMM features)
    spy_close     = market['SPY_close']
    spy_ret_5d    = spy_close.pct_change(5)
    spy_daily_ret = pd.Series(np.log(spy_close / spy_close.shift(1)),
                              index=market.index)

    # ── 1. Rolling PCA (Procrustes-aligned) ────────────────────────
    # Trim data to rows with valid expanding-window standardization
    _warmup_mask = ~np.isnan(X_scaled[:, 0])
    X_scaled_valid = X_scaled[_warmup_mask]
    _warmup_dates = feat_scaled.index[_warmup_mask]

    pcs, mode_ratio, valid_mask, n_pca, last_pca = fit_rolling_pca(X_scaled_valid)

    # Trim everything to valid dates (after expanding + PCA warm-up)
    valid_dates    = _warmup_dates[valid_mask]
    market_v       = market.reindex(valid_dates).dropna(how='all')
    spy_ret_5d_v   = spy_ret_5d.loc[valid_dates]
    spy_daily_ret_v = spy_daily_ret.loc[valid_dates]

    # ── VIX bypass: append scaled VIX directly to PCs ─────────────
    if VIX_BYPASS:
        vix_valid = np.asarray(market_v['VIX'].values, dtype=float)
        vix_mean, vix_std = float(vix_valid.mean()), float(vix_valid.std())
        vix_scaled = ((vix_valid - vix_mean) / vix_std).reshape(-1, 1)
        pcs = np.hstack([pcs, vix_scaled])
        print(f"  VIX bypass: appended scaled VIX as dim {pcs.shape[1]}")

    # ==============================================================
    # 2. Regime Detection  (HDP-HMM or Classic)
    # ==============================================================
    bic_df = None
    agreement = None

    if USE_HDP:
        # ── Bayesian HDP-HMM (auto-K, sticky transitions, Student-t) ──
        from hdp_hmm import (
            fit_hdp_hmm, effective_K, posterior_mean_params,
            get_labels_and_probs, label_regimes_hdp,
            mcmc_diagnostics, save_hdp_results,
            HDPModelAdapter, merge_similar_states,
            hdp_stability_check,
        )

        mcmc, samples = fit_hdp_hmm(pcs)
        diagnostics = mcmc_diagnostics(mcmc, samples)
        k_mean, k_std, k_mode = effective_K(samples)
        print(f"\n  Effective K: {k_mean:.1f} +/- {k_std:.1f} (mode={k_mode})")

        params = posterior_mean_params(samples)
        labels, filt_probs, smooth_probs, active_states = \
            get_labels_and_probs(pcs, params, hold_days=REGIME_HOLD_DAYS)

        # Merge excessive states down to interpretable count
        if len(active_states) > HDP_MAX_REGIMES:
            print(f"  Merging {len(active_states)} states -> {HDP_MAX_REGIMES}")
            labels, n_merged, active_states = merge_similar_states(
                labels, filt_probs, params, active_states,
            )
            # Rebuild probs for merged states
            filt_probs_new = np.zeros((len(labels), n_merged))
            for i in range(n_merged):
                filt_probs_new[:, i] = (labels == i).astype(float)
            # Smooth with small window
            from scipy.ndimage import uniform_filter1d
            filt_probs = uniform_filter1d(filt_probs_new.astype(float), size=5, axis=0)
            filt_probs /= filt_probs.sum(axis=1, keepdims=True)
            smooth_probs = filt_probs

        n_states = max(len(active_states), 2)

        name_map = label_regimes_hdp(
            labels, active_states, spy_daily_ret_v.values,
        )
        print(f"  Final regimes: {list(name_map.values())}")

        # Stability check: label agreement across posterior samples
        stability = hdp_stability_check(samples, pcs, n_draws=10)
        print(f"  HDP Stability: {stability['mean_agreement']:.1%} label agreement "
              f"across {stability['n_draws']} posterior draws "
              f"(mean K={stability['mean_effective_k']:.1f})")

        # Build adapter for compatibility with existing plotting/eval code
        model = HDPModelAdapter(params, active_states, labels, filt_probs)
        probs = filt_probs

        # Save HDP results with metadata
        data_info = {
            'date_start': str(valid_dates[0].date()),
            'date_end': str(valid_dates[-1].date()),
            'n_obs': len(pcs),
            'n_features': pcs.shape[1],
        }
        save_hdp_results(
            MODEL_DIR, mcmc, samples, params, diagnostics,
            (k_mean, k_std, k_mode), data_info,
        )

    else:
        # ── Classic Student-t HMM (BIC state selection, EM) ────────
        best_k, bic_model, bic_df = select_states_bic(pcs)
        n_states = best_k

        model, agreement = check_stability(pcs, n_states)
        labels, name_map = label_regimes(model, pcs, market_v)
        probs = filtered_probs(model, pcs)
        smooth_probs = model.predict_proba(pcs)

    # ── Evaluate in-sample ────────────────────────────────────────
    evaluate(market_v, pd.Series(labels, index=valid_dates),
             name_map, spy_ret_5d_v, 'In-Sample')

    # ── Walk-forward OOS ──────────────────────────────────────────
    print(f"\nWalk-Forward Validation (mode={WALK_FORWARD_MODE}):")
    try:
        oos_labels, oos_name_map = walk_forward(
            market, feat_raw, n_states, n_pca, mode=WALK_FORWARD_MODE,
        )
        evaluate(market, oos_labels, oos_name_map, spy_ret_5d, 'Out-of-Sample')
    except Exception as e:
        print(f"  Walk-forward failed ({type(e).__name__}: {e}) — skipping OOS evaluation")
        oos_labels = pd.Series(dtype=int)
        oos_name_map = {}

    # ── Transition matrix ─────────────────────────────────────────
    print("\nTransition Matrix:")
    trans = pd.DataFrame(
        model.transmat_,
        columns=[name_map[i] for i in sorted(name_map.keys())],
        index=[name_map[i] for i in sorted(name_map.keys())],
    )
    print(trans.round(3))
    for r, name in name_map.items():
        idx_r = sorted(name_map.keys()).index(r)
        p   = model.transmat_[idx_r, idx_r]
        dur = 1 / (1 - p) if p < 1 else np.inf
        print(f"  {name}: persistence={p:.1%}, avg duration={dur:.0f} days")

    # ── Regime-dependent SV ───────────────────────────────────────
    spy_dr_v = spy_daily_ret_v.dropna()
    common_v = valid_dates.intersection(spy_dr_v.index)
    sv_results = fit_regime_sv(
        spy_dr_v.loc[common_v],
        pd.Series(labels, index=valid_dates).loc[common_v].values,
        name_map,
    )

    # ── Regime-dependent GARCH ────────────────────────────────────
    garch_results = fit_regime_garch(
        spy_dr_v.loc[common_v],
        pd.Series(labels, index=valid_dates).loc[common_v].values,
        name_map,
    )

    # VaR back-test (static Gaussian)
    compute_var_backtest(
        spy_dr_v.loc[common_v],
        pd.Series(labels, index=valid_dates).loc[common_v],
        name_map,
    )

    # VaR back-test (GARCH-conditional, probability-weighted)
    compute_var_backtest_garch(
        spy_dr_v.loc[common_v],
        pd.DataFrame(probs, index=valid_dates).loc[common_v],
        pd.Series(labels, index=valid_dates).loc[common_v],
        name_map,
        garch_results,
    )

    # ── Save results (in-sample + OOS) ────────────────────────────
    results = market_v.copy()
    results['regime'] = labels
    results['regime_name'] = [name_map[l] for l in labels]
    for r, name in name_map.items():
        results[f'prob_{name}'] = probs[:, r]
    # Smoothed (full-sample) probs for confidence calibration
    if smooth_probs is not None and smooth_probs.shape[1] == len(name_map):
        for r, name in name_map.items():
            results[f'smooth_prob_{name}'] = smooth_probs[:, r]
    results['market_mode_ratio'] = mode_ratio

    # Stitch OOS labels into results for trust & transparency
    results['is_oos'] = False
    results['regime_oos'] = np.nan
    results['regime_name_oos'] = ''
    if oos_labels is not None and len(oos_labels) > 0:
        oos_idx = oos_labels.index.intersection(results.index)
        results.loc[oos_idx, 'is_oos'] = True
        results.loc[oos_idx, 'regime_oos'] = oos_labels.loc[oos_idx].values
        results.loc[oos_idx, 'regime_name_oos'] = [
            oos_name_map.get(int(l), '') for l in oos_labels.loc[oos_idx].values
        ]
    results.to_csv(os.path.join(DATA_DIR, 'regime_results.csv'))

    joblib.dump(model,    os.path.join(MODEL_DIR, 'hmm_model.pkl'))
    joblib.dump(last_pca, os.path.join(MODEL_DIR, 'pca_model.pkl'))
    feat_scaled.to_csv(os.path.join(DATA_DIR, 'features_scaled.csv'))

    # ── Dashboard (single interactive HTML) ───────────────────────
    oos_mkt = market.loc[oos_labels.index] if len(oos_labels) > 0 else None
    build_interactive_dashboard(
        dates=valid_dates, pcs=pcs, probs=probs, labels=labels,
        name_map=name_map, market=market_v, sv_results=sv_results,
        model=model, garch_results=garch_results,
        mode_ratio=mode_ratio,
        oos_labels=oos_labels if len(oos_labels) > 0 else None,
        oos_name_map=oos_name_map if len(oos_labels) > 0 else None,
        oos_market=oos_mkt,
        pca_model=last_pca, bic_df=bic_df,
        feature_names=list(feat_scaled.columns),
        features_df=feat_scaled,
    )

    # ── Summary ───────────────────────────────────────────────────
    current = results.iloc[-1]
    model_type = f'HDP-HMM (Bayesian, {HDP_INFERENCE.upper()})' if USE_HDP else 'Student-t HMM (BIC)'
    print(f"\n{'=' * 60}")
    print(f"Current State ({valid_dates[-1].date()}):")
    print(f"  Model           : {model_type}")
    print(f"  Regime          : {current['regime_name']}")
    print(f"  VIX             : {current['VIX']:.1f}")
    print(f"  Market-Mode     : {current['market_mode_ratio']:.1%}")
    print(f"  PCA dims        : {n_pca}")
    print(f"  HMM states      : {n_states}"
          f"{' (auto-discovered)' if USE_HDP else ' (by BIC)'}")
    if agreement is not None:
        print(f"  Stability       : {agreement:.1%}")
    print(f"{'=' * 60}")

    return model, results


# ===================================================================
# Rebuild dashboard from saved artifacts (no SVI re-training)
# ===================================================================

def rebuild_dashboard():
    """Reload saved model/results and rebuild only the dashboard HTML."""
    np.random.seed(RANDOM_SEED)
    os.makedirs(FIGURE_DIR, exist_ok=True)

    # ── Load saved data ───────────────────────────────────────────
    results = pd.read_csv(
        os.path.join(DATA_DIR, 'regime_results.csv'),
        index_col=0, parse_dates=True,
    )
    market = pd.read_csv(
        os.path.join(DATA_DIR, 'market_data.csv'),
        index_col=0, parse_dates=True,
    )
    feat_scaled = pd.read_csv(
        os.path.join(DATA_DIR, 'features_scaled.csv'),
        index_col=0, parse_dates=True,
    )
    model = joblib.load(os.path.join(MODEL_DIR, 'hmm_model.pkl'))
    last_pca = joblib.load(os.path.join(MODEL_DIR, 'pca_model.pkl'))

    # ── Derive labels, name_map, probs from saved results ─────────
    valid_dates = results.index
    market_v = market.loc[valid_dates]
    labels = results['regime'].values
    regime_names_in_results = results['regime_name'].values

    # Reconstruct name_map: {int_label -> str_name}
    name_map = {}
    for lbl, nm in zip(labels, regime_names_in_results):
        name_map[int(lbl)] = nm
    ordered = sorted(name_map.keys())

    # Reconstruct probs from saved prob_* columns (ordered by regime int key)
    probs = np.column_stack([
        results[f'prob_{name_map[r]}'].values for r in ordered
    ])

    # mode_ratio
    mode_ratio = results['market_mode_ratio'].values

    # ── Re-run rolling PCA (needed for KDE surface tab) ───────────
    X_scaled = feat_scaled.loc[valid_dates].values if valid_dates[0] in feat_scaled.index else feat_scaled.values
    market_aligned = market.loc[feat_scaled.index]
    pcs, mr, valid_mask, n_pca, last_pca = fit_rolling_pca(feat_scaled.values)

    # Trim to valid dates (same alignment as train)
    pca_valid_dates = feat_scaled.index[valid_mask]
    # PCs should align with results dates
    mask_in_results = pca_valid_dates.isin(valid_dates)
    pcs = pcs[mask_in_results]

    # VIX bypass
    if VIX_BYPASS:
        vix_valid = np.asarray(market_v['VIX'].values, dtype=float)
        vix_mean, vix_std = float(vix_valid.mean()), float(vix_valid.std())
        vix_scaled = ((vix_valid - vix_mean) / vix_std).reshape(-1, 1)
        pcs = np.hstack([pcs, vix_scaled])

    # ── SPY returns for SV / GARCH ────────────────────────────────
    spy_close = market_v['SPY_close']
    spy_daily_ret = pd.Series(
        np.log(spy_close / spy_close.shift(1)), index=valid_dates,
    )
    spy_dr_v = spy_daily_ret.dropna()
    common_v = valid_dates.intersection(spy_dr_v.index)

    print("Fitting regime-dependent SV...")
    sv_results = fit_regime_sv(
        spy_dr_v.loc[common_v],
        pd.Series(labels, index=valid_dates).loc[common_v].values,
        name_map,
    )

    print("Fitting regime-dependent GARCH...")
    garch_results = fit_regime_garch(
        spy_dr_v.loc[common_v],
        pd.Series(labels, index=valid_dates).loc[common_v].values,
        name_map,
    )

    # ── BIC df (not critical, pass None) ──────────────────────────
    bic_path = os.path.join(DATA_DIR, 'bic_selection.csv')
    bic_df = pd.read_csv(bic_path) if os.path.exists(bic_path) else None

    # ── Build dashboard ───────────────────────────────────────────
    print("\nRebuilding dashboard...")
    build_interactive_dashboard(
        dates=valid_dates, pcs=pcs, probs=probs, labels=labels,
        name_map=name_map, market=market_v, sv_results=sv_results,
        model=model, garch_results=garch_results,
        mode_ratio=mode_ratio,
        oos_labels=None, oos_name_map=None, oos_market=None,
        pca_model=last_pca, bic_df=bic_df,
        feature_names=list(feat_scaled.columns),
        features_df=feat_scaled,
    )
    print("Dashboard rebuilt → figures/dashboard.html")
