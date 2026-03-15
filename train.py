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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from arch import arch_model
from hmmlearn import hmm
from itertools import permutations
from scipy.linalg import orthogonal_procrustes
from scipy.stats import multivariate_t as _mvt, norm as _norm, gaussian_kde
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.mlemodel import MLEModel

from config import (
    RANDOM_SEED, N_STATES, N_STATES_RANGE, COV_TYPE, T_DF,
    N_SEEDS, HMM_ITER, PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD,
    PCA_ROLLING_WINDOW, VIX_BYPASS, USE_HDP, HDP_INFERENCE, HDP_MAX_REGIMES,
    GARCH_P, GARCH_Q, GARCH_DIST, MIN_REGIME_OBS, REGIME_HOLD_DAYS,
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS,
    WALK_FORWARD_MODE, VAR_ALPHA,
    REGIME_NAMES, DATA_DIR, MODEL_DIR, FIGURE_DIR, TICKERS,
)
from features import build_features, standardize
from signals import compute_signals

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
    min_train = WALK_FORWARD_TRAIN_YEARS * 252
    step      = WALK_FORWARD_STEP_DAYS

    oos_labels = pd.Series(index=features.index, dtype=float)
    oos_labels[:] = np.nan

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

        # Standardize (fit on train)
        scaler_wf = StandardScaler()
        X_train = scaler_wf.fit_transform(train_feats.values)
        X_test  = scaler_wf.transform(test_feats.values)

        # PCA: fit on last ROLLING_WINDOW days of train, project all
        pca_window = min(PCA_ROLLING_WINDOW, len(X_train))
        n_comp = min(n_pca, X_train.shape[1])
        pca_wf = PCA(n_components=n_comp, random_state=RANDOM_SEED)
        pca_wf.fit(X_train[-pca_window:])
        pc_train = pca_wf.transform(X_train)
        pc_test  = pca_wf.transform(X_test)

        # VIX bypass: append scaled VIX directly to PCs
        if VIX_BYPASS:
            vix_train = market['VIX'].reindex(train_feats.index).values
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
        raw_preds = best_m.predict(pc_test)

        # Remap labels by VIX rank (consistent across windows)
        train_labels = best_m.predict(pc_train)
        vix_vals = market['VIX'].reindex(train_feats.index).values
        regime_vix = {}
        for r in range(n_states):
            mask = (train_labels == r)
            regime_vix[r] = vix_vals[mask].mean() if mask.any() else 0
        sorted_by_vix = sorted(regime_vix, key=lambda k: regime_vix[k])
        remap = {orig: rank for rank, orig in enumerate(sorted_by_vix)}
        remapped = np.array([remap[r] for r in raw_preds])

        oos_labels.iloc[t:end] = remapped

        step_num += 1
        if step_num % 10 == 0:
            print(f"    step {step_num}")
        t = end

    valid = oos_labels.dropna().astype(int)
    names = REGIME_NAMES.get(n_states, [f'Regime-{i}' for i in range(n_states)])
    name_map = {i: names[i] for i in range(n_states)}
    return valid, name_map


# ===================================================================
# 8. Evaluation
# ===================================================================

def evaluate(market, labels, name_map, spy_ret, label_source='In-Sample'):
    """Print regime characteristics using 5-day SPY returns (independent)."""
    print(f"\nRegime Characteristics ({label_source}):")
    hdr = (f"  {'Regime':<14s} {'Days':>6s} {'Pct':>6s} {'VIX':>7s} "
           f"{'HYSprd':>7s} {'YldSlp':>7s} {'SPY5d':>7s}")
    print(hdr)
    print(f"  {'-' * 58}")

    for r in sorted(name_map.keys()):
        name = name_map[r]
        if hasattr(labels, 'index'):
            idx = labels.index[labels == r]
        else:
            idx = market.index[labels == r]
        n   = len(idx)
        pct = n / len(labels) * 100

        vix_m = market.loc[idx, 'VIX'].mean()           if 'VIX'         in market else np.nan
        hy_m  = market.loc[idx, 'hy_spread'].mean()     if 'hy_spread'   in market else np.nan
        yl_m  = market.loc[idx, 'yield_slope'].mean()   if 'yield_slope' in market else np.nan
        sp_m  = spy_ret.reindex(idx).mean() * 100

        print(f"  {name:<14s} {n:>6d} {pct:>5.1f}% {vix_m:>7.1f} "
              f"{hy_m:>6.2f}% {yl_m:>+7.2f} {sp_m:>+6.2f}%")


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
        print(f"  Overall      : exc={total_exc}/{total_n} "
              f"({total_exc / total_n:.1%})")


# ===================================================================
# 9. Plotting  (publication-quality matplotlib + interactive Plotly)
# ===================================================================

# Modern color palette — every regime gets a distinct, attractive color
_REGIME_COLORS = {
    'Very-Low':   '#2ecc71',   # emerald green
    'Low-Vol':    '#27ae60',   # nephritis green
    'Moderate':   '#3498db',   # peter river blue
    'Medium-Vol': '#f39c12',   # orange
    'Elevated':   '#f1c40f',   # sunflower yellow
    'Stressed':   '#e67e22',   # carrot orange
    'High-Vol':   '#e74c3c',   # alizarin red
    'Crisis':     '#c0392b',   # pomegranate red
}

# Plotly-compatible hex colors — same mapping
_REGIME_COLORS_HEX = _REGIME_COLORS.copy()

# Matplotlib global styling for all static figures
_MPL_STYLE = {
    'figure.facecolor':  '#0d1117',
    'axes.facecolor':    '#161b22',
    'axes.edgecolor':    '#30363d',
    'axes.labelcolor':   '#c9d1d9',
    'text.color':        '#c9d1d9',
    'xtick.color':       '#8b949e',
    'ytick.color':       '#8b949e',
    'grid.color':        '#21262d',
    'grid.alpha':        0.6,
    'legend.facecolor':  '#161b22',
    'legend.edgecolor':  '#30363d',
    'figure.dpi':        150,
    'savefig.dpi':       300,
    'font.size':         11,
    'axes.titlesize':    13,
    'axes.labelsize':    11,
}


def _apply_style():
    """Apply the dark theme to matplotlib."""
    plt.rcParams.update(_MPL_STYLE)


def _get_blocks(mask):
    """Return (start, end) index pairs for contiguous True blocks."""
    blocks, in_block = [], False
    start = 0
    for i, val in enumerate(mask):
        if val and not in_block:
            start = i; in_block = True
        elif not val and in_block:
            blocks.append((start, i - 1)); in_block = False
    if in_block:
        blocks.append((start, len(mask) - 1))
    return blocks


def _shade_regimes(ax, label_series, name_map, index):
    for r, name in name_map.items():
        mask = label_series == r
        for s, e in _get_blocks(mask):
            ax.axvspan(
                index[s], index[e],
                alpha=0.25 if 'Crisis' in name or 'High' in name else 0.15,
                color=_REGIME_COLORS.get(name, '#888'),
            )


def _regime_legend(name_map):
    return [Patch(facecolor=_REGIME_COLORS.get(n, '#888'), alpha=0.5, label=n)
            for n in name_map.values()]


def plot_regime_history(market, labels, name_map, title_suffix=''):
    """Multi-panel: SPY, VIX, HY spread, yield slope with regime shading."""
    _apply_style()
    panels = [('SPY', market.get('SPY_close'), '#58a6ff')]
    panels.append(('VIX', market.get('VIX'), '#bc8cff'))
    if 'hy_spread' in market.columns:
        panels.append(('HY Spread (%)', market['hy_spread'], '#ff7b72'))
    if 'yield_slope' in market.columns:
        panels.append(('Yield Slope', market['yield_slope'], '#7ee787'))

    fig, axes = plt.subplots(len(panels), 1,
                             figsize=(18, 3.5 * len(panels)), sharex=True)
    if len(panels) == 1:
        axes = [axes]

    label_series = pd.Series(labels, index=market.index[:len(labels)])

    for ax, (ylabel, data, color) in zip(axes, panels):
        _shade_regimes(ax, label_series, name_map, market.index)
        if data is not None:
            ax.plot(data.index, data, '-', color=color, lw=0.8, alpha=0.9)
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.grid(True)

    axes[0].set_title(f'Market Regimes {title_suffix}',
                      fontsize=15, fontweight='bold')
    axes[0].legend(handles=_regime_legend(name_map), loc='upper left',
                   fontsize=9, ncol=min(len(name_map), 3))
    if len(axes) > 1:
        axes[1].axhline(20, color='#f0883e', ls='--', alpha=0.5, lw=0.7)
        axes[1].axhline(30, color='#ff7b72', ls='--', alpha=0.5, lw=0.7)
    if 'yield_slope' in market.columns:
        axes[-1].axhline(0, color='#ff7b72', ls='--', alpha=0.5, lw=0.7)

    fig.tight_layout(h_pad=0.3)
    return fig


def plot_regime_probabilities(market, model, pcs, name_map):
    """Stacked area chart of filtered (forward-only) regime probabilities."""
    _apply_style()
    probs = filtered_probs(model, pcs)
    ordered = sorted(name_map.keys())
    idx = market.index[:len(probs)]
    fig, ax = plt.subplots(figsize=(18, 5))
    bottom = np.zeros(len(probs))
    for r in ordered:
        name = name_map[r]
        ax.fill_between(idx, bottom, bottom + probs[:, r],
                        alpha=0.7,
                        color=_REGIME_COLORS.get(name, '#888'), label=name)
        bottom += probs[:, r]
    ax.set_ylabel('Probability', fontweight='bold')
    ax.set_title('Regime Probabilities', fontsize=15, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9, ncol=min(len(name_map), 3))
    ax.set_ylim(0, 1)
    ax.grid(True)
    fig.tight_layout()
    return fig


def plot_current_state(market, model, pcs, name_map):
    """Current regime bar + last 90d donut."""
    _apply_style()
    probs  = filtered_probs(model, pcs)
    labels = filtered_labels(model, pcs)
    current_probs = probs[-1]
    current_date  = market.index[-1].date()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ordered    = sorted(name_map.keys())
    bar_names  = [name_map[r] for r in ordered]
    bar_vals   = [current_probs[r] for r in ordered]
    bar_colors = [_REGIME_COLORS.get(n, '#888') for n in bar_names]

    bars = ax1.barh(bar_names, bar_vals, color=bar_colors, alpha=0.85,
                    edgecolor='#30363d', linewidth=0.5)
    ax1.set_xlabel('Probability', fontweight='bold')
    ax1.set_title(f'Current Regime  ({current_date})',
                  fontsize=13, fontweight='bold')
    ax1.set_xlim(0, 1)
    ax1.grid(axis='x')
    for bar, v in zip(bars, bar_vals):
        if v > 0.03:
            ax1.text(v + 0.02, bar.get_y() + bar.get_height() / 2,
                     f'{v:.0%}', va='center', fontsize=11, color='#c9d1d9')

    recent = labels[-90:]
    name_series = pd.Series([name_map[l] for l in recent])
    counts = name_series.value_counts()
    wedge_colors = [_REGIME_COLORS.get(n, '#888') for n in counts.index]
    wedges, texts, autotexts = ax2.pie(
        counts, labels=counts.index, autopct='%1.0f%%',
        colors=wedge_colors, startangle=90,
        pctdistance=0.8, wedgeprops=dict(width=0.45, edgecolor='#0d1117'),
        textprops=dict(color='#c9d1d9'),
    )
    for t in autotexts:
        t.set_color('#c9d1d9')
        t.set_fontsize(10)
    ax2.set_title('Last 90 Days', fontsize=13, fontweight='bold')
    fig.tight_layout()
    return fig


def plot_model_diagnostics(pca_model, bic_df, garch_results, name_map):
    """PCA scree + GARCH parameters (skip BIC panel for HDP mode)."""
    _apply_style()
    regimes = [r for r in sorted(name_map.keys()) if r in garch_results]
    has_garch = len(regimes) > 0
    has_bic = bic_df is not None
    n_panels = 1 + int(has_bic) + int(has_garch)

    fig, axes = plt.subplots(1, n_panels, figsize=(6 * n_panels, 5))
    if n_panels == 1:
        axes = [axes]
    pi = 0

    # PCA scree
    ax = axes[pi]; pi += 1
    var = pca_model.explained_variance_ratio_
    cum = np.cumsum(var)
    x = range(1, len(var) + 1)
    ax.bar(x, var, alpha=0.7, color='#58a6ff', label='Individual')
    ax.plot(x, cum, 'o-', color='#f0883e', lw=1.5, label='Cumulative')
    ax.axhline(PCA_VAR_THRESHOLD, color='#8b949e', ls='--', alpha=0.5,
               label=f'{PCA_VAR_THRESHOLD:.0%} threshold')
    ax.set_xlabel('Principal Component')
    ax.set_ylabel('Explained Variance')
    ax.set_title('PCA Scree')
    ax.legend(fontsize=8); ax.grid(True)

    # BIC (only in classic mode)
    if has_bic:
        ax = axes[pi]; pi += 1
        best_idx = bic_df['BIC'].idxmin()
        colors = ['#f0883e' if i == best_idx else '#58a6ff'
                  for i in range(len(bic_df))]
        ax.bar(bic_df['K'], bic_df['BIC'], color=colors, alpha=0.7)
        ax.set_xlabel('States (K)')
        ax.set_ylabel('BIC')
        ax.set_title(f"BIC  (best K={int(bic_df.loc[best_idx, 'K'])})")
        ax.grid(True)

    # GARCH
    if has_garch:
        ax = axes[pi]
        names_g = [name_map[r] for r in regimes]
        omegas = [garch_results[r].params.get('omega', 0) for r in regimes]
        alphas = [garch_results[r].params.get('alpha[1]', 0) for r in regimes]
        betas  = [garch_results[r].params.get('beta[1]', 0) for r in regimes]
        xr = np.arange(len(regimes))
        w = 0.22
        ax.bar(xr - w, omegas, w, label='omega', alpha=0.8, color='#58a6ff')
        ax.bar(xr,     alphas, w, label='alpha', alpha=0.8, color='#f0883e')
        ax.bar(xr + w, betas,  w, label='beta',  alpha=0.8, color='#7ee787')
        ax.set_xticks(xr); ax.set_xticklabels(names_g, fontsize=9)
        ax.set_ylabel('Parameter')
        ax.set_title('GARCH(1,1) by Regime')
        ax.legend(fontsize=8); ax.grid(True)

    fig.suptitle('Model Diagnostics', fontsize=15, fontweight='bold')
    fig.tight_layout()
    return fig


def plot_market_mode(dates, mode_ratio, labels, name_map):
    """Market-mode ratio with regime shading."""
    _apply_style()
    fig, ax = plt.subplots(figsize=(18, 5))
    label_series = pd.Series(labels, index=dates[:len(labels)])
    _shade_regimes(ax, label_series, name_map, dates)
    ax.plot(dates, mode_ratio, '-', color='#bc8cff', lw=0.9)
    ax.set_ylabel('$\\lambda_1 / \\Sigma\\lambda$', fontweight='bold')
    ax.set_title('Market-Mode Ratio (Rolling PCA)',
                 fontsize=15, fontweight='bold')
    ax.legend(handles=_regime_legend(name_map), loc='upper right',
              fontsize=8, ncol=2)
    ax.grid(True)
    fig.tight_layout()
    return fig


def plot_sv_volatility(dates, sv_results, labels, name_map, vix_series=None):
    """SV latent vol vs VIX + SV params by regime."""
    _apply_style()
    fig, axes = plt.subplots(2, 1, figsize=(18, 9), sharex=False)

    ax1 = axes[0]
    label_series = pd.Series(labels, index=dates[:len(labels)])
    _shade_regimes(ax1, label_series, name_map, dates)

    if vix_series is not None:
        ax1.plot(vix_series.index, vix_series.values, '-', color='#bc8cff',
                 lw=0.6, alpha=0.7, label='VIX')

    full_sv = sv_results.get('full', {})
    ann_vol = full_sv.get('annualized_vol')
    if ann_vol is not None:
        ax1.plot(dates[:len(ann_vol)], ann_vol, '-', color='#f0883e',
                 lw=0.8, label='SV Latent Vol (%)')

    ax1.set_ylabel('Volatility (%)', fontweight='bold')
    ax1.set_title('Stochastic Volatility: Latent Vol vs VIX',
                  fontsize=15, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True)

    ax2 = axes[1]
    regime_keys = [r for r in sorted(name_map.keys())
                   if r in sv_results and 'params' in sv_results.get(r, {})]
    if regime_keys:
        names_r = [name_map[r] for r in regime_keys]
        phis = [sv_results[r]['params']['phi'] for r in regime_keys]
        sigmas = [sv_results[r]['params']['sigma_eta'] for r in regime_keys]
        mean_vols = [sv_results[r]['annualized_vol'].mean()
                     for r in regime_keys]

        x = np.arange(len(regime_keys))
        w = 0.22
        ax2.bar(x - w, phis, w, label='phi (persistence)',
                alpha=0.8, color='#58a6ff')
        ax2.bar(x, [s * 5 for s in sigmas], w,
                label='sigma_eta x5', alpha=0.8, color='#f0883e')
        ax2.bar(x + w, [v / 100 for v in mean_vols], w,
                label='mean_vol / 100', alpha=0.8, color='#7ee787')
        ax2.set_xticks(x); ax2.set_xticklabels(names_r, fontsize=9)
        ax2.set_ylabel('Parameter', fontweight='bold')
        ax2.set_title('SV Parameters by Regime')
        ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True)

    fig.tight_layout()
    return fig


# ===================================================================
# Interactive Plotly Dashboard  (single HTML file)
# ===================================================================

def build_interactive_dashboard(dates, pcs, probs, labels, name_map,
                                market, sv_results, model, garch_results,
                                mode_ratio, oos_labels=None, oos_name_map=None,
                                oos_market=None, pca_model=None, bic_df=None,
                                feature_names=None, features_df=None):
    """
    Single interactive HTML dashboard:
      1. Timeline  (IS SPY+VIX + OOS SPY+VIX + Market Mode — one scroll)
      2. SV Volatility
      3. KDE Density Surfaces  (per-regime panels + combined 3D)
      4. Transitions  (Sankey + full matrix + per-state stats)
      5. Current State  (detailed market context + probabilistic outlook)
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    ordered = sorted(name_map.keys())
    regime_names = [name_map[r] for r in ordered]
    colors = [_REGIME_COLORS_HEX.get(n, '#888') for n in regime_names]
    T_len = len(dates)
    date_strs = [d.strftime('%Y-%m-%d') for d in dates[:T_len]]
    label_arr = np.asarray(labels[:T_len])

    # helper: add regime shading via filled scatter shapes
    def _add_shading(fig, lab_arr, d_strs, cols, ords, row=None, col=None):
        for r_idx, r in enumerate(ords):
            c_hex = cols[r_idx].lstrip('#')
            rv, gv, bv = int(c_hex[:2], 16), int(c_hex[2:4], 16), int(c_hex[4:6], 16)
            rgba = f'rgba({rv},{gv},{bv},0.18)'
            mask = lab_arr == r
            for s, e in _get_blocks(mask):
                kw = dict(
                    x0=d_strs[s], x1=d_strs[min(e, len(d_strs) - 1)],
                    fillcolor=rgba, opacity=1.0, line_width=0,
                    layer='below',
                )
                if row is not None:
                    kw['row'] = row; kw['col'] = col  # type: ignore[assignment]
                fig.add_vrect(**kw)  # type: ignore[arg-type]

    # ── Tab 1: Combined Timeline ───────────────────────────────────
    has_oos = (oos_labels is not None and len(oos_labels) > 0
               and oos_market is not None)
    n_rows = 3 + (2 if has_oos else 0)
    row_heights = [0.25, 0.15] + ([0.20, 0.12] if has_oos else []) + [0.15]
    total_h = sum(row_heights)
    row_heights = [h / total_h for h in row_heights]

    subtitles = ['SPY + Regime Shading (In-Sample)', 'VIX (In-Sample)']
    if has_oos:
        subtitles += ['SPY (Out-of-Sample)', 'VIX (Out-of-Sample)']
    subtitles += ['Market-Mode Ratio (Rolling PCA)']

    fig_tl = make_subplots(
        rows=n_rows, cols=1, shared_xaxes=False,
        row_heights=row_heights, vertical_spacing=0.04,
        subplot_titles=subtitles,
    )

    for row_i in [1, 2]:
        _add_shading(fig_tl, label_arr, date_strs, colors, ordered,
                     row=row_i, col=1)

    spy_data = market.get('SPY_close')
    if spy_data is not None:
        fig_tl.add_trace(go.Scatter(
            x=spy_data.index, y=spy_data.values, mode='lines',
            line=dict(color='#58a6ff', width=1.2), name='SPY',
            hovertemplate='%{x}<br>$%{y:.2f}<extra></extra>',
        ), row=1, col=1)

    vix_data = market.get('VIX')
    if vix_data is not None:
        fig_tl.add_trace(go.Scatter(
            x=vix_data.index, y=vix_data.values, mode='lines',
            line=dict(color='#bc8cff', width=1), name='VIX',
            hovertemplate='%{x}<br>VIX: %{y:.1f}<extra></extra>',
        ), row=2, col=1)
        fig_tl.add_hline(y=20, line_dash='dash', line_color='#f0883e',
                         opacity=0.4, row=2, col=1)  # type: ignore[arg-type]
        fig_tl.add_hline(y=30, line_dash='dash', line_color='#ff7b72',
                         opacity=0.4, row=2, col=1)  # type: ignore[arg-type]

    oos_row_start = 3
    if has_oos:
        assert oos_name_map is not None and oos_labels is not None and oos_market is not None
        oos_ord = sorted(oos_name_map.keys())
        oos_nm = [oos_name_map[r] for r in oos_ord]
        oos_cols = [_REGIME_COLORS_HEX.get(n, '#888') for n in oos_nm]
        oos_ds = [d.strftime('%Y-%m-%d') for d in oos_labels.index]
        oos_la = oos_labels.values
        for row_i in [3, 4]:
            _add_shading(fig_tl, oos_la, oos_ds, oos_cols, oos_ord,
                         row=row_i, col=1)
        spy_oos = oos_market.get('SPY_close')
        if spy_oos is not None:
            fig_tl.add_trace(go.Scatter(
                x=spy_oos.index, y=spy_oos.values, mode='lines',
                line=dict(color='#58a6ff', width=1.2), name='SPY OOS',
                showlegend=False,
            ), row=3, col=1)
        vix_oos = oos_market.get('VIX')
        if vix_oos is not None:
            fig_tl.add_trace(go.Scatter(
                x=vix_oos.index, y=vix_oos.values, mode='lines',
                line=dict(color='#bc8cff', width=1), name='VIX OOS',
                showlegend=False,
            ), row=4, col=1)
        oos_row_start = 5

    mode_row = oos_row_start
    _add_shading(fig_tl, label_arr, date_strs, colors, ordered,
                 row=mode_row, col=1)
    fig_tl.add_trace(go.Scatter(
        x=dates, y=mode_ratio, mode='lines',
        line=dict(color='#bc8cff', width=1.2), name='Mode Ratio',
        hovertemplate='%{x}<br>%{y:.4f}<extra></extra>',
    ), row=mode_row, col=1)
    fig_tl.update_yaxes(title_text='λ₁/Σλ', row=mode_row, col=1)

    fig_tl.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        height=250 * n_rows, margin=dict(l=60, r=30, t=50, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.01, font_size=11),
    )

    # ── Tab 2: SV Volatility ──────────────────────────────────────
    fig_sv = _build_sv_volatility(dates, sv_results, labels, name_map,
                                  market, colors, ordered, regime_names)

    # ── Tab 3: KDE Density Surfaces ────────────────────────────────
    fig_kde = _build_kde_surface(pcs, labels, name_map, colors, ordered,
                                 regime_names, pca_model=pca_model,
                                 feature_names=feature_names)

    # ── Tab 4: Transitions ─────────────────────────────────────────
    fig_trans = _build_transitions(model, labels, name_map, colors,
                                   ordered, regime_names)

    # ── Tab 5: Current State ───────────────────────────────────────
    fig_current = _build_current_state(probs, labels, name_map, dates,
                                       market, colors, ordered, regime_names,
                                       model=model, sv_results=sv_results)

    # ── Tab 6: Regime Awareness ──────────────────────────────────
    results_df = market.copy()
    results_df['regime'] = labels
    results_df['regime_name'] = [name_map[l] for l in labels]
    for r_key in ordered:
        results_df[f'prob_{name_map[r_key]}'] = probs[:, r_key]
    fig_signals = _build_signals_tab(results_df, model, name_map,
                                     colors, ordered, regime_names)

    # ── Tab 7: Feature Health ──────────────────────────────────────
    fig_health = None
    if features_df is not None:
        fig_health = _build_feature_health_tab(features_df, pcs, pca_model)

    tabs = [
        ('Timeline', fig_tl),
        ('SV Volatility', fig_sv),
        ('KDE Surfaces', fig_kde),
        ('Transitions', fig_trans),
        ('Current State', fig_current),
        ('Regime Awareness', fig_signals),
    ]
    if fig_health is not None:
        tabs.append(('Feature Health', fig_health))

    _write_dashboard_html(tabs)


def _build_kde_surface(pcs, labels, name_map, colors, ordered, regime_names,
                       pca_model=None, feature_names=None):
    """
    KDE density surfaces — combined 3D view + per-regime detail panels
    + PCA loading breakdown showing what PC1/PC2 represent.
    Returns a list of figures rendered as stacked HTML.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    if pcs.shape[1] < 2:
        return go.Figure()

    pc1_all, pc2_all = pcs[:, 0], pcs[:, 1]
    margin = 0.8
    x_min, x_max = pc1_all.min() - margin, pc1_all.max() + margin
    y_min, y_max = pc2_all.min() - margin, pc2_all.max() + margin
    grid_x, grid_y = np.mgrid[x_min:x_max:80j, y_min:y_max:80j]
    grid_positions = np.vstack([grid_x.ravel(), grid_y.ravel()])

    def _hex_to_rgba(h, a=0.85):
        c = h.lstrip('#')
        return f'rgba({int(c[:2],16)},{int(c[2:4],16)},{int(c[4:6],16)},{a})'

    def _make_colorscale(hex_c):
        return [[0, _hex_to_rgba(hex_c, 0)], [1, _hex_to_rgba(hex_c, 0.85)]]

    # ── Figure 1: PCA Loading Breakdown ────────────────────────────
    figs = []
    if pca_model is not None and feature_names is not None:
        loadings = pca_model.components_  # (n_components, n_features)
        n_show = min(2, loadings.shape[0])
        var_ratio = pca_model.explained_variance_ratio_

        fig_load = make_subplots(
            rows=1, cols=n_show,
            subplot_titles=[
                f'PC{i+1} ({var_ratio[i]:.1%} variance explained)'
                for i in range(n_show)
            ],
            horizontal_spacing=0.15,
        )

        for pc_idx in range(n_show):
            weights = loadings[pc_idx]
            sort_idx = np.argsort(np.abs(weights))[::-1]
            n_feat = min(len(feature_names), 12)
            top_idx = sort_idx[:n_feat]

            feat_names_sorted = [feature_names[i] for i in top_idx]
            feat_weights = [weights[i] for i in top_idx]
            bar_colors = ['#58a6ff' if w >= 0 else '#f0883e' for w in feat_weights]

            fig_load.add_trace(go.Bar(
                y=feat_names_sorted[::-1],
                x=feat_weights[::-1],
                orientation='h',
                marker=dict(color=bar_colors[::-1],
                            line=dict(color='#30363d', width=0.5)),
                hovertemplate='%{y}: %{x:.3f}<extra></extra>',
                showlegend=False,
            ), row=1, col=pc_idx+1)

        fig_load.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
            title=dict(
                text='What Do PC1 & PC2 Represent? — PCA Eigenvector Loadings',
                font_size=18,
            ),
            height=max(350, 28 * n_feat),  # type: ignore[possibly-undefined]
            margin=dict(l=120, r=30, t=80, b=30),
        )
        for i in range(n_show):
            fig_load.update_xaxes(
                title_text='Loading Weight', row=1, col=i+1,
                zeroline=True, zerolinecolor='#484f58',
            )
        figs.append(fig_load)

    # ── Figure 2: Combined 3D Density Surfaces ────────────────────
    fig_3d = go.Figure()
    pc_label = lambda i: (
        f'PC{i+1} ({pca_model.explained_variance_ratio_[i]:.0%})'
        if pca_model is not None else f'PC{i+1}'
    )

    for r_idx, r in enumerate(ordered):
        name = regime_names[r_idx]
        mask = (labels == r)
        if mask.sum() < 15:
            continue
        pc1_r, pc2_r = pc1_all[mask], pc2_all[mask]
        try:
            kde = gaussian_kde(np.vstack([pc1_r, pc2_r]), bw_method=0.25)
            density = kde(grid_positions).reshape(grid_x.shape)
        except np.linalg.LinAlgError:
            continue

        fig_3d.add_trace(go.Surface(
            x=grid_x[:, 0], y=grid_y[0, :], z=density.T,
            colorscale=_make_colorscale(colors[r_idx]),
            opacity=0.75, showscale=False,
            name=name, showlegend=True,
            hovertemplate=(
                f'{name}<br>{pc_label(0)}: %{{x:.2f}}<br>'
                f'{pc_label(1)}: %{{y:.2f}}<br>Density: %{{z:.4f}}<extra></extra>'
            ),
            contours=dict(
                z=dict(show=True, usecolormap=True, highlightcolor='white',
                       project_z=True),
            ),
            lighting=dict(ambient=0.5, diffuse=0.6, specular=0.3,
                          roughness=0.8, fresnel=0.2),
        ))

    fig_3d.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117',
        title=dict(text='Combined Regime Density Landscapes', font_size=18),
        scene=dict(
            xaxis=dict(title=pc_label(0), backgroundcolor='#161b22',
                       gridcolor='#21262d', showbackground=True),
            yaxis=dict(title=pc_label(1), backgroundcolor='#161b22',
                       gridcolor='#21262d', showbackground=True),
            zaxis=dict(title='Density', backgroundcolor='#161b22',
                       gridcolor='#21262d', showbackground=True),
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.8)),
            aspectratio=dict(x=1.2, y=1.2, z=0.7),
        ),
        height=700, margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(font_size=12, bgcolor='rgba(22,27,34,0.8)',
                    orientation='h', yanchor='bottom', y=1.01),
    )
    figs.append(fig_3d)

    # ── Figure 3: Per-Regime Detail Panels (2D contour + scatter) ──
    active_regimes = [(r_idx, r) for r_idx, r in enumerate(ordered)
                      if (labels == r).sum() >= 15]
    n_panels = len(active_regimes)
    if n_panels > 0:
        ncols = min(3, n_panels)
        nrows = (n_panels + ncols - 1) // ncols

        fig_panels = make_subplots(
            rows=nrows, cols=ncols,
            subplot_titles=[
                f'{regime_names[r_idx]} ({(labels==r).sum()} days)'
                for r_idx, r in active_regimes
            ],
            horizontal_spacing=0.08,
            vertical_spacing=0.12,
        )

        for panel_i, (r_idx, r) in enumerate(active_regimes):
            row = panel_i // ncols + 1
            col = panel_i % ncols + 1
            mask = labels == r
            pc1_r, pc2_r = pc1_all[mask], pc2_all[mask]

            try:
                kde = gaussian_kde(np.vstack([pc1_r, pc2_r]), bw_method=0.25)
                density = kde(grid_positions).reshape(grid_x.shape)
            except np.linalg.LinAlgError:
                continue

            fig_panels.add_trace(go.Contour(
                x=grid_x[:, 0], y=grid_y[0, :], z=density.T,
                colorscale=_make_colorscale(colors[r_idx]),
                showscale=False,
                contours=dict(coloring='heatmap', showlines=True,
                              showlabels=False),
                line=dict(width=0.5, color='rgba(255,255,255,0.3)'),
                hovertemplate=(
                    f'{regime_names[r_idx]}<br>{pc_label(0)}: %{{x:.2f}}<br>'
                    f'{pc_label(1)}: %{{y:.2f}}<br>Density: %{{z:.4f}}<extra></extra>'
                ),
                showlegend=False,
            ), row=row, col=col)

            # Scatter overlay (sample of points)
            n_pts = min(200, mask.sum())
            sample = np.random.choice(mask.sum(), n_pts, replace=False)
            fig_panels.add_trace(go.Scatter(
                x=pc1_r[sample], y=pc2_r[sample], mode='markers',
                marker=dict(size=2.5, color=colors[r_idx], opacity=0.5),
                showlegend=False,
                hoverinfo='skip',
            ), row=row, col=col)

            fig_panels.update_xaxes(title_text=pc_label(0), row=row, col=col)
            fig_panels.update_yaxes(title_text=pc_label(1), row=row, col=col)

        fig_panels.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
            title=dict(
                text='Per-Regime Density Detail — Contour + Data Points',
                font_size=18,
            ),
            height=380 * nrows,
            margin=dict(l=60, r=30, t=80, b=40),
        )
        figs.append(fig_panels)

    return figs


def _build_transitions(model, labels, name_map, colors, ordered, regime_names):
    """Sankey diagram + full transition matrix table + per-state stats."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    trans = model.transmat_
    K = len(ordered)

    # ── Sankey (top) ───────────────────────────────────────────────
    sources, targets, values, link_colors = [], [], [], []
    for i in range(K):
        for j in range(K):
            if i == j:
                continue
            p = trans[i, j]
            if p > 0.005:
                sources.append(i)
                targets.append(j + K)
                values.append(round(p * 100, 1))
                c = colors[i].lstrip('#')
                rv, gv, bv = int(c[:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                link_colors.append(f'rgba({rv},{gv},{bv},0.3)')

    fig_sankey = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            pad=20, thickness=25, line=dict(color='#30363d', width=1),
            label=regime_names + regime_names,
            color=colors + colors,
        ),
        link=dict(source=sources, target=targets, value=values,
                  color=link_colors),
    ))

    # Self-loop annotations
    annotations = []
    for i in range(K):
        p = trans[i, i]
        annotations.append(dict(
            text=f'{regime_names[i]}: {p:.1%} stay',
            x=0, y=1 - i / max(K - 1, 1),
            xref='paper', yref='paper',
            showarrow=False, font=dict(size=10, color=colors[i]),
            xanchor='left',
        ))

    fig_sankey.update_layout(
        template='plotly_dark', paper_bgcolor='#0d1117',
        title=dict(text='Regime Transition Flows', font_size=18),
        height=450, margin=dict(l=140, r=30, t=60, b=10),
        annotations=annotations,
    )

    # ── Transition matrix heatmap ──────────────────────────────────
    fig_matrix = go.Figure(go.Heatmap(
        z=[[trans[i, j] for j in range(K)] for i in range(K)],
        x=regime_names, y=regime_names,
        text=[[f'{trans[i, j]:.1%}' for j in range(K)] for i in range(K)],
        texttemplate='%{text}', textfont=dict(size=12),
        colorscale=[[0, '#161b22'], [0.5, '#1f6feb'], [1, '#f0883e']],
        zmin=0, zmax=1, showscale=False,
        hovertemplate='From %{y} → %{x}<br>P = %{z:.2%}<extra></extra>',
    ))
    fig_matrix.update_layout(
        template='plotly_dark', paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        title=dict(text='Transition Probability Matrix (row = from, col = to)',
                   font_size=15),
        xaxis=dict(title='To', side='top'),
        yaxis=dict(title='From', autorange='reversed'),
        height=380, margin=dict(l=80, r=30, t=80, b=30),
    )

    # ── Per-state stats table ──────────────────────────────────────
    label_arr = np.asarray(labels)
    total_days = len(label_arr)

    header_vals = ['Regime', 'Days', '%', 'Avg Duration', 'Persistence',
                   'Top Exit →', 'Exit %']
    cell_vals = [[] for _ in range(7)]

    for i, r in enumerate(ordered):
        name = regime_names[i]
        mask = label_arr == r
        n_days = mask.sum()
        pct = n_days / total_days

        # average duration via blocks
        blocks = _get_blocks(mask)
        avg_dur = np.mean([e - s + 1 for s, e in blocks]) if blocks else 0

        persist = trans[i, i]

        # top exit destination (excluding self)
        exit_probs = [(trans[i, j], regime_names[oi])
                      for oi, j in enumerate(range(K)) if j != i]
        exit_probs.sort(reverse=True)
        top_exit_name = exit_probs[0][1] if exit_probs else '-'
        top_exit_pct = exit_probs[0][0] if exit_probs else 0

        cell_vals[0].append(name)
        cell_vals[1].append(f'{n_days}')
        cell_vals[2].append(f'{pct:.1%}')
        cell_vals[3].append(f'{avg_dur:.1f}d')
        cell_vals[4].append(f'{persist:.1%}')
        cell_vals[5].append(top_exit_name)
        cell_vals[6].append(f'{top_exit_pct:.1%}')

    fig_table = go.Figure(go.Table(
        header=dict(
            values=[f'<b>{v}</b>' for v in header_vals],
            fill_color='#161b22', line_color='#30363d',
            font=dict(color='#c9d1d9', size=12), align='center',
        ),
        cells=dict(
            values=cell_vals,
            fill_color=[
                [_REGIME_COLORS_HEX.get(n, '#888') + '33' if False
                 else '#0d1117' for n in cell_vals[0]]
            ] * 7,
            line_color='#30363d',
            font=dict(
                color=[colors] + [['#c9d1d9'] * K] * 6,
                size=12,
            ),
            align='center',
        ),
    ))
    fig_table.update_layout(
        template='plotly_dark', paper_bgcolor='#0d1117',
        title=dict(text='Per-State Statistics', font_size=15),
        height=280, margin=dict(l=10, r=10, t=50, b=10),
    )

    # Combine as stacked HTML (write_dashboard_html handles this via
    # a single "figure" that is actually raw HTML of three figures)
    # We wrap all three into one container
    return _stack_figures([fig_sankey, fig_matrix, fig_table])


def _stack_figures(figs):
    """Return a list-of-figures marker that _write_dashboard_html can handle."""
    # We use a special wrapper — just return the list;
    # _write_dashboard_html detects list vs single figure.
    return figs



def _build_current_state(probs, labels, name_map, dates, market,
                         colors, ordered, regime_names,
                         model=None, sv_results=None):
    """
    Detailed current-state panel with market context, probabilistic
    duration estimates, and regime interpretation.
    Returns a list of stacked figures.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    current_probs = probs[-1]
    current_date = dates[-1].strftime('%Y-%m-%d')
    current_label = labels[-1]
    current_name = name_map.get(current_label, '?')
    current_color = _REGIME_COLORS_HEX.get(current_name, '#888')
    K = len(ordered)

    # ── Compute statistics ─────────────────────────────────────────
    label_arr = np.asarray(labels)
    total_days = len(label_arr)

    # Current streak
    streak = 1
    for t in range(len(label_arr) - 2, -1, -1):
        if label_arr[t] == current_label:
            streak += 1
        else:
            break

    # Expected total duration from transition matrix: E[dur] = 1/(1-p_ii)
    trans = model.transmat_ if model is not None else None
    cur_idx = list(ordered).index(current_label)
    if trans is not None:
        persist = trans[cur_idx, cur_idx]
        expected_dur = 1.0 / max(1.0 - persist, 1e-6)
        expected_remaining = max(0, expected_dur - streak)
        # Geometric distribution: P(T > t) = p_ii^t
        p_survive_7d = persist ** 7 if persist < 1 else 1.0
        p_survive_30d = persist ** 30 if persist < 1 else 1.0
    else:
        persist = expected_dur = expected_remaining = 0
        p_survive_7d = p_survive_30d = 0

    # Historical block durations for current regime
    blocks = _get_blocks(label_arr == current_label)
    durations = [e - s + 1 for s, e in blocks]
    median_dur = float(np.median(durations)) if durations else 0
    max_dur = max(durations) if durations else 0
    pct_time = (label_arr == current_label).sum() / total_days

    # Market context
    vix_val = market['VIX'].iloc[-1] if 'VIX' in market.columns else None
    spy_close = market['SPY_close'].iloc[-1] if 'SPY_close' in market.columns else None
    spy_20d_ret = None
    if 'SPY_close' in market.columns and len(market) >= 20:
        spy_20d_ret = (market['SPY_close'].iloc[-1] /
                       market['SPY_close'].iloc[-20] - 1) * 100
    hy_spread = market['hy_spread'].iloc[-1] if 'hy_spread' in market.columns else None
    yield_slope = market['yield_slope'].iloc[-1] if 'yield_slope' in market.columns else None

    # VIX interpretation
    if vix_val is not None:
        if vix_val < 15:
            vix_interp = 'Very Low — complacency / low hedging demand'
        elif vix_val < 20:
            vix_interp = 'Normal — typical market conditions'
        elif vix_val < 25:
            vix_interp = 'Elevated — growing uncertainty'
        elif vix_val < 30:
            vix_interp = 'High — significant fear, hedging active'
        else:
            vix_interp = 'Extreme — panic / crisis-level volatility'
    else:
        vix_interp = 'N/A'

    # Top exit destinations
    exit_info = []
    if trans is not None:
        for j in range(K):
            if j != cur_idx:
                exit_info.append((trans[cur_idx, j], regime_names[j]))
        exit_info.sort(reverse=True)

    # SV vol info
    sv_vol = None
    full_sv = sv_results.get('full', {}) if sv_results else {}
    ann_vol = full_sv.get('annualized_vol')
    if ann_vol is not None and len(ann_vol) > 0:
        sv_vol = ann_vol[-1]

    figs = []

    # ── Figure 1: Regime Status Card ───────────────────────────────
    fig_status = go.Figure()

    # Current regime probabilities bar
    bar_colors_list = []
    for r_idx, r in enumerate(ordered):
        if r == current_label:
            bar_colors_list.append(colors[r_idx])
        else:
            c = colors[r_idx].lstrip('#')
            rv, gv, bv = int(c[:2], 16), int(c[2:4], 16), int(c[4:6], 16)
            bar_colors_list.append(f'rgba({rv},{gv},{bv},0.4)')

    fig_status.add_trace(go.Bar(
        x=[current_probs[r] for r in ordered],
        y=regime_names, orientation='h',
        marker=dict(color=bar_colors_list,
                    line=dict(color='#30363d', width=1)),
        text=[f'{current_probs[r]:.0%}' for r in ordered],
        textposition='outside', textfont=dict(color='#c9d1d9', size=13),
        hovertemplate='%{y}: %{x:.1%}<extra></extra>',
        showlegend=False,
    ))

    # Title annotation with regime name
    fig_status.add_annotation(
        text=(f'<b style="color:{current_color};font-size:32px">'
              f'{current_name}</b>'
              f'<br><span style="color:#8b949e;font-size:14px">'
              f'as of {current_date}</span>'),
        xref='paper', yref='paper', x=0.5, y=1.18,
        showarrow=False, align='center',
    )

    fig_status.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        title=dict(text='Current Regime Probabilities', font_size=16,
                   y=0.88),
        height=320, margin=dict(l=100, r=40, t=100, b=20),
        xaxis=dict(range=[0, 1.05], tickformat='.0%'),
    )
    figs.append(fig_status)

    # ── Figure 2: Market Context Table ─────────────────────────────
    header_vals = ['Metric', 'Value', 'Interpretation']
    metrics, values, interps = [], [], []

    if vix_val is not None:
        metrics.append('VIX')
        values.append(f'{vix_val:.1f}')
        interps.append(vix_interp)
    if spy_close is not None:
        metrics.append('SPY Close')
        values.append(f'${spy_close:.2f}')
        interps.append('')
    if spy_20d_ret is not None:
        metrics.append('SPY 20d Return')
        values.append(f'{spy_20d_ret:+.1f}%')
        trend = 'Bullish trend' if spy_20d_ret > 2 else ('Bearish trend' if spy_20d_ret < -2 else 'Sideways')
        interps.append(trend)
    if sv_vol is not None:
        metrics.append('SV Latent Vol')
        values.append(f'{sv_vol:.1f}%')
        interps.append('Annualized, Kalman-smoothed')
    if hy_spread is not None:
        metrics.append('HY Spread (OAS)')
        values.append(f'{hy_spread:.2f}%')
        hy_interp = 'Tight — risk-on' if hy_spread < 4 else ('Wide — stress' if hy_spread > 6 else 'Normal range')
        interps.append(hy_interp)
    if yield_slope is not None:
        metrics.append('Yield Curve (10Y-2Y)')
        values.append(f'{yield_slope:+.2f}%')
        yc_interp = 'Inverted — recession signal' if yield_slope < 0 else 'Normal — expansion'
        interps.append(yc_interp)

    fig_market = go.Figure(go.Table(
        header=dict(
            values=[f'<b>{v}</b>' for v in header_vals],
            fill_color='#161b22', line_color='#30363d',
            font=dict(color='#c9d1d9', size=13), align='left',
            height=35,
        ),
        cells=dict(
            values=[metrics, values, interps],
            fill_color='#0d1117', line_color='#30363d',
            font=dict(color=['#58a6ff', '#c9d1d9', '#8b949e'], size=12),
            align='left', height=30,
        ),
    ))
    fig_market.update_layout(
        template='plotly_dark', paper_bgcolor='#0d1117',
        title=dict(text='Market Context', font_size=16),
        height=35 + 35 * max(len(metrics), 1) + 80,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    figs.append(fig_market)

    # ── Figure 3: Duration & Outlook ───────────────────────────────
    fig_outlook = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'table'}, {'type': 'pie'}]],
        column_widths=[0.55, 0.45],
        subplot_titles=['Probabilistic Regime Outlook',
                        'Last 90 Days Distribution'],
    )

    # Duration stats table
    outlook_metrics = [
        'Current Streak',
        'Expected Duration (geometric)',
        'Expected Remaining',
        'Median Historical Duration',
        'Longest Historical Episode',
        f'P(still {current_name} in 7d)',
        f'P(still {current_name} in 30d)',
        'Persistence (self-transition)',
        f'Historical Time in {current_name}',
    ]
    outlook_values = [
        f'{streak} days',
        f'{expected_dur:.0f} days',
        f'{expected_remaining:.0f} days',
        f'{median_dur:.0f} days',
        f'{max_dur} days',
        f'{p_survive_7d:.0%}',
        f'{p_survive_30d:.0%}',
        f'{persist:.1%}',
        f'{pct_time:.1%}',
    ]

    fig_outlook.add_trace(go.Table(
        header=dict(
            values=['<b>Metric</b>', '<b>Value</b>'],
            fill_color='#161b22', line_color='#30363d',
            font=dict(color='#c9d1d9', size=12), align='left',
            height=30,
        ),
        cells=dict(
            values=[outlook_metrics, outlook_values],
            fill_color='#0d1117', line_color='#30363d',
            font=dict(color=['#8b949e', '#c9d1d9'], size=12),
            align='left', height=28,
        ),
    ), row=1, col=1)

    # Donut for last 90 days
    recent = labels[-90:]
    name_series = pd.Series([name_map[l] for l in recent])
    counts = name_series.value_counts()
    pie_colors = [_REGIME_COLORS_HEX.get(n, '#888') for n in counts.index]
    fig_outlook.add_trace(go.Pie(
        labels=counts.index, values=counts.values,
        hole=0.5, marker=dict(colors=pie_colors,
                               line=dict(color='#0d1117', width=2)),
        textinfo='label+percent', textfont=dict(size=11),
        hovertemplate='%{label}: %{value} days (%{percent})<extra></extra>',
    ), row=1, col=2)

    fig_outlook.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        height=400, margin=dict(l=10, r=10, t=60, b=20),
    )
    figs.append(fig_outlook)

    # ── Figure 4: Transition Risk (where could we go next?) ────────
    if exit_info:
        exit_names = [e[1] for e in exit_info[:5]]
        exit_probs_vals = [e[0] for e in exit_info[:5]]
        exit_colors = [_REGIME_COLORS_HEX.get(n, '#888') for n in exit_names]

        fig_exit = go.Figure(go.Bar(
            x=exit_probs_vals, y=exit_names, orientation='h',
            marker=dict(color=exit_colors,
                        line=dict(color='#30363d', width=1)),
            text=[f'{p:.1%}' for p in exit_probs_vals],
            textposition='outside', textfont=dict(color='#c9d1d9', size=13),
            hovertemplate='%{y}: %{x:.1%}<extra></extra>',
        ))
        fig_exit.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
            title=dict(
                text=f'If {current_name} Ends — Most Likely Next Regime',
                font_size=16,
            ),
            height=250, margin=dict(l=100, r=60, t=50, b=20),
            xaxis=dict(range=[0, max(exit_probs_vals) * 1.3],
                       tickformat='.0%'),
            showlegend=False,
        )
        figs.append(fig_exit)

    return figs


def _build_sv_volatility(dates, sv_results, labels, name_map,
                         market, colors, ordered, regime_names):
    """SV latent vol vs VIX + regime params — Plotly version."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    T_len = len(dates)
    label_arr = np.asarray(labels[:T_len])
    date_strs = [d.strftime('%Y-%m-%d') for d in dates[:T_len]]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=False, row_heights=[0.6, 0.4],
        vertical_spacing=0.1,
        subplot_titles=['SV Latent Vol vs VIX', 'SV Parameters by Regime'],
    )

    # Regime shading on top panel
    for r_idx, r in enumerate(ordered):
        c_hex = colors[r_idx].lstrip('#')
        rv, gv, bv = int(c_hex[:2], 16), int(c_hex[2:4], 16), int(c_hex[4:6], 16)
        rgba = f'rgba({rv},{gv},{bv},0.18)'
        mask = label_arr == r
        for s, e in _get_blocks(mask):
            fig.add_vrect(
                x0=date_strs[s], x1=date_strs[min(e, T_len - 1)],
                fillcolor=rgba, opacity=1.0, line_width=0,
                layer='below', row=1, col=1,  # type: ignore[arg-type]
            )

    # VIX line
    vix_data = market.get('VIX')
    if vix_data is not None:
        fig.add_trace(go.Scatter(
            x=vix_data.index, y=vix_data.values, mode='lines',
            line=dict(color='#bc8cff', width=0.8),
            name='VIX', hovertemplate='%{x}<br>VIX: %{y:.1f}<extra></extra>',
        ), row=1, col=1)

    # SV latent vol
    full_sv = sv_results.get('full', {})
    ann_vol = full_sv.get('annualized_vol')
    if ann_vol is not None:
        fig.add_trace(go.Scatter(
            x=dates[:len(ann_vol)], y=ann_vol, mode='lines',
            line=dict(color='#f0883e', width=1),
            name='SV Latent Vol', hovertemplate='%{x}<br>SV Vol: %{y:.1f}%<extra></extra>',
        ), row=1, col=1)

    # Regime SV params bar chart
    regime_keys = [r for r in sorted(name_map.keys())
                   if r in sv_results and 'params' in sv_results.get(r, {})]
    if regime_keys:
        names_r = [name_map[r] for r in regime_keys]
        phis = [sv_results[r]['params']['phi'] for r in regime_keys]
        sigmas = [sv_results[r]['params']['sigma_eta'] * 5 for r in regime_keys]
        mean_vols = [sv_results[r]['annualized_vol'].mean() / 100 for r in regime_keys]

        fig.add_trace(go.Bar(x=names_r, y=phis, name='phi', marker_color='#58a6ff',
                             hovertemplate='%{x}<br>phi: %{y:.3f}<extra></extra>'),
                      row=2, col=1)
        fig.add_trace(go.Bar(x=names_r, y=sigmas, name='σ_η ×5', marker_color='#f0883e',
                             hovertemplate='%{x}<br>σ_η×5: %{y:.3f}<extra></extra>'),
                      row=2, col=1)
        fig.add_trace(go.Bar(x=names_r, y=mean_vols, name='mean_vol/100', marker_color='#7ee787',
                             hovertemplate='%{x}<br>vol/100: %{y:.3f}<extra></extra>'),
                      row=2, col=1)

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        barmode='group',
        height=700, margin=dict(l=60, r=30, t=60, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, font_size=11),
    )
    return fig


def _build_signals_tab(results, model, name_map, colors, ordered, regime_names):
    """Regime Awareness tab: distributions, validation, vol context."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    sigs = compute_signals(results, model, name_map)
    aw = sigs['awareness']
    dists = sigs['distributions']
    trans = sigs['transitions']
    vol_ctx = sigs['vol_context']
    val = sigs['validation']
    current = aw['current_regime']
    date_str = sigs['date']

    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{'type': 'table', 'colspan': 2}, None],
            [{'type': 'table'}, {'type': 'table'}],
            [{'type': 'table', 'colspan': 2}, None],
            [{'type': 'table', 'colspan': 2}, None],
        ],
        row_heights=[0.18, 0.32, 0.25, 0.25],
        vertical_spacing=0.04,
        subplot_titles=[
            f'Regime Awareness — {current} ({date_str})',
            'Distribution Profile per Regime (SPY daily)',
            'Vol Context',
            'Transition Probabilities',
            'Model Validation — Is This Real?',
        ],
    )

    # ── Row 1: Regime awareness summary ───────────────────────────
    conf_pct = f"{aw['confidence']:.0%}"
    summary_labels = [
        'Current Regime', 'Confidence', 'Days in Regime',
        'Median Duration (this regime)', 'VIX', 'VRP',
    ]
    summary_values = [
        current,
        conf_pct,
        str(aw['days_in_regime']),
        f"{aw['median_duration']:.0f} days",
        f"{vol_ctx['vix']:.1f}" if vol_ctx['vix'] else 'N/A',
        f"{vol_ctx['vrp']:+.1f}" if vol_ctx['vrp'] else 'N/A',
    ]

    # Color-code confidence
    conf = aw['confidence']
    conf_color = '#7ee787' if conf > 0.7 else '#f0883e' if conf > 0.4 else '#f85149'

    val_colors = ['#0d1117'] * len(summary_labels)
    val_colors[1] = conf_color  # confidence cell

    fig.add_trace(go.Table(
        header=dict(
            values=['Metric', 'Value'],
            fill_color='#21262d', font=dict(color='#c9d1d9', size=12),
            align='left',
        ),
        cells=dict(
            values=[summary_labels, summary_values],
            fill_color=[['#0d1117'] * len(summary_labels), val_colors],
            font=dict(color='#c9d1d9', size=11),
            align='left', height=25,
        ),
    ), row=1, col=1)

    # ── Row 2 Left: Distribution table ────────────────────────────
    regimes_list = list(dists.index)
    dist_regime = regimes_list
    dist_vol = [f"{dists.loc[r, 'ann_vol']*100:.1f}%"
                if not np.isnan(dists.loc[r, 'ann_vol']) else '—' for r in regimes_list]
    dist_skew = [f"{dists.loc[r, 'skew']:.2f}"
                 if not np.isnan(dists.loc[r, 'skew']) else '—' for r in regimes_list]
    dist_kurt = [f"{dists.loc[r, 'kurtosis']:.1f}"
                 if not np.isnan(dists.loc[r, 'kurtosis']) else '—' for r in regimes_list]
    dist_var5 = [f"{dists.loc[r, 'var_5']*100:.2f}%"
                 if not np.isnan(dists.loc[r, 'var_5']) else '—' for r in regimes_list]
    dist_cvar5 = [f"{dists.loc[r, 'cvar_5']*100:.2f}%"
                  if not np.isnan(dists.loc[r, 'cvar_5']) else '—' for r in regimes_list]
    dist_dd = [f"{dists.loc[r, 'max_dd']*100:.1f}%"
               if not np.isnan(dists.loc[r, 'max_dd']) else '—' for r in regimes_list]
    dist_days = [f"{int(dists.loc[r, 'n_days'])}" for r in regimes_list]
    dist_normal = []
    for r in regimes_list:
        val_n = dists.loc[r, 'is_normal']
        if val_n is True:
            dist_normal.append('Yes')
        elif val_n is False:
            dist_normal.append('No')
        else:
            dist_normal.append('—')

    # Highlight current regime row
    n_cols = 9
    cell_colors_dist = []
    for _ in range(n_cols):
        col_c = []
        for r in regimes_list:
            col_c.append('#1f3a5f' if r == current else '#0d1117')
        cell_colors_dist.append(col_c)

    fig.add_trace(go.Table(
        header=dict(
            values=['Regime', 'Ann Vol', 'Skew', 'Kurtosis',
                    'VaR 5%', 'CVaR 5%', 'Max DD', 'Days', 'Normal?'],
            fill_color='#21262d', font=dict(color='#c9d1d9', size=10),
            align='left',
        ),
        cells=dict(
            values=[dist_regime, dist_vol, dist_skew, dist_kurt,
                    dist_var5, dist_cvar5, dist_dd, dist_days, dist_normal],
            fill_color=cell_colors_dist,
            font=dict(color='#c9d1d9', size=10),
            align='left',
        ),
    ), row=2, col=1)

    # ── Row 2 Right: Vol context ──────────────────────────────────
    vol_labels = ['VIX', 'VRP', 'Term Structure', 'VRP Meaning']
    vol_values = [
        f"{vol_ctx['vix']:.1f}" if vol_ctx['vix'] else 'N/A',
        f"{vol_ctx['vrp']:+.1f}" if vol_ctx['vrp'] else 'N/A',
        vol_ctx['term_structure_label'],
        vol_ctx['vrp_label'],
    ]
    fig.add_trace(go.Table(
        header=dict(
            values=['Metric', 'Value'],
            fill_color='#21262d', font=dict(color='#c9d1d9', size=10),
            align='left',
        ),
        cells=dict(
            values=[vol_labels, vol_values],
            fill_color='#0d1117',
            font=dict(color='#c9d1d9', size=10),
            align='left', height=30,
        ),
    ), row=2, col=2)

    # ── Row 3: Transition context ─────────────────────────────────
    if trans:
        t_regimes = [t['regime'] for t in trans]
        t_probs = [f"{t['probability']:.1%}" for t in trans]
        t_dir = [t['direction'] for t in trans]
        t_jump = [str(t['severity_jump']) for t in trans]

        # Color: higher-vol transitions in orange/red
        t_colors = []
        for t in trans:
            if t['direction'] == 'higher vol' and t['severity_jump'] >= 2:
                t_colors.append('#3d1f00')
            elif t['direction'] == 'higher vol':
                t_colors.append('#2a1a00')
            elif t['direction'] == 'lower vol':
                t_colors.append('#0a3d0a')
            else:
                t_colors.append('#0d1117')

        fig.add_trace(go.Table(
            header=dict(
                values=['Nearby Regime', 'Probability', 'Direction', 'Severity Jump'],
                fill_color='#21262d', font=dict(color='#c9d1d9', size=10),
                align='left',
            ),
            cells=dict(
                values=[t_regimes, t_probs, t_dir, t_jump],
                fill_color=[t_colors] * 4,
                font=dict(color='#c9d1d9', size=10),
                align='left',
            ),
        ), row=3, col=1)
    else:
        fig.add_trace(go.Table(
            header=dict(values=['Transitions'], fill_color='#21262d',
                        font=dict(color='#c9d1d9')),
            cells=dict(values=[['No significant transition probabilities']],
                       fill_color='#0d1117', font=dict(color='#c9d1d9')),
        ), row=3, col=1)

    # ── Row 4: Validation metrics ─────────────────────────────────
    val_labels = []
    val_values = []
    val_row_colors = []

    # Regime separation
    sep_p = val.get('separation_pvalue', np.nan)
    sep_ok = val.get('separation_significant', False)
    val_labels.append('Regime Separation (Kruskal-Wallis)')
    val_values.append(
        f"p={sep_p:.2e} — {'PASS: regimes are distinct' if sep_ok else 'FAIL: regimes may be noise'}"
    )
    val_row_colors.append('#0a3d0a' if sep_ok else '#3d0a0a')

    # Vol ordering
    vol_ord = val.get('vol_ordering_match', False)
    val_labels.append('Vol Ordering (severity ↔ realized vol)')
    regime_vols = val.get('regime_vols', {})
    vol_str = ', '.join(f"{r}: {v*100:.1f}%" for r, v in
                        sorted(regime_vols.items(),
                               key=lambda x: x[1]))
    val_values.append(
        f"{'PASS' if vol_ord else 'PARTIAL'}: {vol_str}"
    )
    val_row_colors.append('#0a3d0a' if vol_ord else '#3d1f00')

    # Persistence
    persist = val.get('persistent', False)
    val_labels.append('Regime Persistence')
    val_values.append(val.get('persistence_interpretation', '—'))
    val_row_colors.append('#0a3d0a' if persist else '#3d1f00')

    # VaR backtest summary
    var_bt = val.get('var_backtest', {})
    for r, vr in var_bt.items():
        val_labels.append(f'VaR 5% Backtest — {r}')
        val_values.append(
            f"Actual breach: {vr['breach_pct']:.1f}% "
            f"({vr['n_breaches']}/{vr['n_total']}) — "
            f"{'PASS' if vr['ok'] else 'FAIL'}"
        )
        val_row_colors.append('#0a3d0a' if vr['ok'] else '#3d0a0a')

    fig.add_trace(go.Table(
        header=dict(
            values=['Validation Check', 'Result'],
            fill_color='#21262d', font=dict(color='#c9d1d9', size=10),
            align='left',
        ),
        cells=dict(
            values=[val_labels, val_values],
            fill_color=[['#0d1117'] * len(val_labels), val_row_colors],
            font=dict(color='#c9d1d9', size=10),
            align='left',
        ),
    ), row=4, col=1)

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        height=1400, margin=dict(l=30, r=30, t=50, b=30),
        showlegend=False,
    )
    return fig


    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        height=1400, margin=dict(l=30, r=30, t=50, b=30),
        showlegend=False,
    )
    return fig


# ===================================================================
# Tab 7: Feature Health
# ===================================================================

def _build_feature_health_tab(features_df, pcs, pca_model):
    """
    Feature Health diagnostics: correlation matrix, VIF, skew/kurtosis,
    PCA loadings. Validates that the feature set is clean.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    cols = list(features_df.columns)
    n_feat = len(cols)

    # ── Correlation matrix ─────────────────────────────────────────
    corr = features_df.corr()
    max_offdiag = 0.0
    for i in range(n_feat):
        for j in range(i + 1, n_feat):
            max_offdiag = max(max_offdiag, abs(corr.iloc[i, j]))

    fig = make_subplots(
        rows=3, cols=2,
        specs=[
            [{'type': 'heatmap', 'colspan': 2}, None],
            [{'type': 'table'}, {'type': 'table'}],
            [{'type': 'table', 'colspan': 2}, None],
        ],
        row_heights=[0.50, 0.25, 0.25],
        vertical_spacing=0.06,
        subplot_titles=[
            f'Feature Correlation Matrix (max |r| = {max_offdiag:.2f})',
            'Feature Quality (Skew / Kurtosis / VIF)',
            'PCA Loadings (top 3 components)',
            'Feature Health Summary',
        ],
    )

    # Heatmap
    fig.add_trace(go.Heatmap(
        z=corr.values, x=cols, y=cols,
        colorscale='RdBu_r', zmid=0, zmin=-1, zmax=1,
        text=np.round(corr.values, 2),
        texttemplate='%{text}',
        textfont=dict(size=8),
        hovertemplate='%{x} vs %{y}: %{z:.3f}<extra></extra>',
        showscale=True,
    ), row=1, col=1)

    # ── VIF + Skew/Kurtosis table ──────────────────────────────────
    from sklearn.linear_model import LinearRegression

    skews = features_df.skew()
    kurts = features_df.kurtosis()

    # VIF: for each feature, R² from regressing it on all others
    X = features_df.values
    vifs = []
    for i in range(n_feat):
        others = np.delete(X, i, axis=1)
        y = X[:, i]
        mask = ~(np.isnan(others).any(axis=1) | np.isnan(y))
        if mask.sum() < 10:
            vifs.append(float('inf'))
            continue
        reg = LinearRegression().fit(others[mask], y[mask])
        r2 = reg.score(others[mask], y[mask])
        vifs.append(1 / (1 - r2) if r2 < 1 else float('inf'))

    # Status columns
    skew_status = ['PASS' if abs(s) < 2.0 else 'WARN' if abs(s) < 3.0 else 'FAIL' for s in skews]
    kurt_status = ['PASS' if abs(k) < 7.0 else 'WARN' if abs(k) < 10.0 else 'FAIL' for k in kurts]
    vif_status = ['PASS' if v < 5.0 else 'WARN' if v < 10.0 else 'FAIL' for v in vifs]

    # Color cells
    def _status_color(statuses):
        return ['#1a4d1a' if s == 'PASS' else '#4d3d1a' if s == 'WARN' else '#4d1a1a' for s in statuses]

    fig.add_trace(go.Table(
        header=dict(
            values=['Feature', 'Skew', '', 'Kurtosis', '', 'VIF', ''],
            fill_color='#21262d', font=dict(color='#c9d1d9', size=10),
            align='left',
        ),
        cells=dict(
            values=[
                cols,
                [f'{s:.2f}' for s in skews], skew_status,
                [f'{k:.1f}' for k in kurts], kurt_status,
                [f'{v:.1f}' for v in vifs], vif_status,
            ],
            fill_color=[
                ['#0d1117'] * n_feat,
                ['#0d1117'] * n_feat, _status_color(skew_status),
                ['#0d1117'] * n_feat, _status_color(kurt_status),
                ['#0d1117'] * n_feat, _status_color(vif_status),
            ],
            font=dict(color='#c9d1d9', size=9),
            align='left',
        ),
    ), row=2, col=1)

    # ── PCA loadings table ─────────────────────────────────────────
    if pca_model is not None and hasattr(pca_model, 'components_'):
        n_show = min(3, pca_model.components_.shape[0])
        var_ratios = pca_model.explained_variance_ratio_[:n_show]
        # Loadings: components_ has shape (n_components, n_features)
        # We need to map to our feature names
        n_pca_feats = pca_model.components_.shape[1]
        if n_pca_feats == n_feat:
            loadings = pca_model.components_[:n_show]
            header_vals = ['Feature'] + [
                f'PC{i+1} ({var_ratios[i]:.1%})' for i in range(n_show)
            ]
            cell_vals = [cols] + [
                [f'{loadings[i, j]:.3f}' for j in range(n_feat)]
                for i in range(n_show)
            ]
        else:
            header_vals = ['Info']
            cell_vals = [[f'PCA has {n_pca_feats} inputs vs {n_feat} features — mismatch']]
    else:
        header_vals = ['Info']
        cell_vals = [['PCA model not available']]

    fig.add_trace(go.Table(
        header=dict(
            values=header_vals,
            fill_color='#21262d', font=dict(color='#c9d1d9', size=10),
            align='left',
        ),
        cells=dict(
            values=cell_vals,
            fill_color='#0d1117', font=dict(color='#c9d1d9', size=9),
            align='left',
        ),
    ), row=2, col=2)

    # ── Summary table ──────────────────────────────────────────────
    n_corr_high = sum(
        1 for i in range(n_feat) for j in range(i+1, n_feat)
        if abs(corr.iloc[i, j]) > 0.85
    )
    n_vif_high = sum(1 for v in vifs if v >= 5.0)
    n_skew_bad = sum(1 for s in skews if abs(s) >= 2.0)
    n_kurt_bad = sum(1 for k in kurts if abs(k) >= 7.0)

    checks = [
        ('Feature count', str(n_feat), 'PASS' if 10 <= n_feat <= 20 else 'WARN'),
        ('Observations', str(len(features_df)), 'PASS' if len(features_df) > 2000 else 'WARN'),
        ('Correlated pairs (|r| > 0.85)', str(n_corr_high), 'PASS' if n_corr_high == 0 else 'FAIL'),
        ('Max |correlation|', f'{max_offdiag:.2f}', 'PASS' if max_offdiag < 0.85 else 'FAIL'),
        ('High VIF features (≥ 5)', str(n_vif_high), 'PASS' if n_vif_high == 0 else 'WARN'),
        ('High skew features (|s| ≥ 2)', str(n_skew_bad), 'PASS' if n_skew_bad == 0 else 'WARN'),
        ('High kurtosis features (|k| ≥ 7)', str(n_kurt_bad), 'PASS' if n_kurt_bad == 0 else 'WARN'),
    ]

    fig.add_trace(go.Table(
        header=dict(
            values=['Check', 'Value', 'Status'],
            fill_color='#21262d', font=dict(color='#c9d1d9', size=11),
            align='left',
        ),
        cells=dict(
            values=[
                [c[0] for c in checks],
                [c[1] for c in checks],
                [c[2] for c in checks],
            ],
            fill_color=[
                ['#0d1117'] * len(checks),
                ['#0d1117'] * len(checks),
                _status_color([c[2] for c in checks]),
            ],
            font=dict(color='#c9d1d9', size=10),
            align='left',
        ),
    ), row=3, col=1)

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        height=max(900, 20 * n_feat + 700),
        margin=dict(l=30, r=30, t=50, b=30),
        showlegend=False,
    )
    return fig


def _write_dashboard_html(tabs):
    """Write all figures into a single tabbed HTML dashboard."""
    import plotly.io as pio

    plotly_included = False
    tab_buttons = ''
    tab_contents = ''
    for i, (label, fig_or_figs) in enumerate(tabs):
        active = ' active' if i == 0 else ''
        display = 'block' if i == 0 else 'none'

        # Handle stacked figures (list) vs single figure
        if isinstance(fig_or_figs, list):
            parts = []
            for sub_fig in fig_or_figs:
                parts.append(pio.to_html(
                    sub_fig, include_plotlyjs=(not plotly_included),
                    full_html=False, config={
                        'displayModeBar': True, 'scrollZoom': True,
                        'modeBarButtonsToAdd': ['toggleSpikelines'],
                    }))
                plotly_included = True
            div_html = '\n'.join(parts)
        else:
            div_html = pio.to_html(
                fig_or_figs, include_plotlyjs=(not plotly_included),
                full_html=False, config={
                    'displayModeBar': True, 'scrollZoom': True,
                    'modeBarButtonsToAdd': ['toggleSpikelines'],
                })
            plotly_included = True

        tab_buttons += (
            f'<button class="tab-btn{active}" '
            f'onclick="switchTab({i})">{label}</button>\n'
        )
        tab_contents += (
            f'<div class="tab-content" id="tab-{i}" '
            f'style="display:{display}">{div_html}</div>\n'
        )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Regime Detection Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0d1117; color: #c9d1d9;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  }}
  .header {{
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    padding: 16px 24px; border-bottom: 1px solid #21262d;
    display: flex; align-items: center; gap: 16px;
    flex-wrap: wrap;
  }}
  .header h1 {{
    font-size: 22px; font-weight: 600;
    background: linear-gradient(90deg, #58a6ff, #bc8cff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .header .badge {{
    background: #21262d; border: 1px solid #30363d; border-radius: 20px;
    padding: 4px 14px; font-size: 12px; color: #8b949e;
  }}
  .tab-bar {{
    display: flex; gap: 0; background: #161b22;
    border-bottom: 2px solid #21262d; padding: 0 20px;
  }}
  .tab-btn {{
    background: none; border: none; color: #8b949e; padding: 12px 20px;
    font-size: 14px; cursor: pointer; border-bottom: 2px solid transparent;
    transition: all 0.2s; font-weight: 500;
  }}
  .tab-btn:hover {{ color: #c9d1d9; }}
  .tab-btn.active {{
    color: #58a6ff; border-bottom-color: #58a6ff;
  }}
  .tab-content {{ padding: 8px; max-width: 100%; overflow-x: auto; }}
  .tab-content .plotly-graph-div {{ width: 100% !important; }}
  @media (max-width: 768px) {{
    .header {{ padding: 12px 16px; }}
    .header h1 {{ font-size: 18px; }}
    .tab-bar {{ padding: 0 8px; overflow-x: auto; white-space: nowrap; }}
    .tab-btn {{ padding: 10px 14px; font-size: 13px; }}
    .tab-content {{ padding: 4px; }}
  }}
</style>
</head>
<body>
<div class="header">
  <h1>Regime Detection Dashboard</h1>
  <span class="badge">HDP-HMM &middot; Bayesian</span>
</div>
<div class="tab-bar">
{tab_buttons}
</div>
{tab_contents}
<script>
function switchTab(idx) {{
  document.querySelectorAll('.tab-content').forEach((el, i) => {{
    el.style.display = i === idx ? 'block' : 'none';
  }});
  document.querySelectorAll('.tab-btn').forEach((el, i) => {{
    el.classList.toggle('active', i === idx);
  }});
  // Force Plotly resize for the visible tab
  setTimeout(() => window.dispatchEvent(new Event('resize')), 50);
}}
</script>
</body>
</html>'''

    path = os.path.join(FIGURE_DIR, 'dashboard.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Interactive dashboard saved: {path}")


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
    feat_raw = pd.read_csv(
        os.path.join(DATA_DIR, 'features_raw.csv'),
        index_col=0, parse_dates=True,
    )
    feat_scaled = pd.read_csv(
        os.path.join(DATA_DIR, 'features_scaled.csv'),
        index_col=0, parse_dates=True,
    )

    # Align market to feature dates
    market = market.loc[feat_scaled.index]
    X_scaled = feat_scaled.values

    # SPY returns (independent evaluation -- not in HMM features)
    spy_close     = market['SPY_close']
    spy_ret_5d    = spy_close.pct_change(5)
    spy_daily_ret = pd.Series(np.log(spy_close / spy_close.shift(1)),
                              index=market.index)

    # ── 1. Rolling PCA (Procrustes-aligned) ────────────────────────
    pcs, mode_ratio, valid_mask, n_pca, last_pca = fit_rolling_pca(X_scaled)

    # Trim everything to valid dates (after PCA warm-up)
    valid_dates    = feat_scaled.index[valid_mask]
    market_v       = market.loc[valid_dates]
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
            HDPModelAdapter, get_transition_matrix,
            merge_similar_states,
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
            labels, active_states, market_v['VIX'].values,
        )
        print(f"  Final regimes: {list(name_map.values())}")

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

    # VaR back-test
    compute_var_backtest(
        spy_dr_v.loc[common_v],
        pd.Series(labels, index=valid_dates).loc[common_v],
        name_map,
    )

    # ── Save results ──────────────────────────────────────────────
    results = market_v.copy()
    results['regime'] = labels
    results['regime_name'] = [name_map[l] for l in labels]
    for r, name in name_map.items():
        results[f'prob_{name}'] = probs[:, r]
    results['market_mode_ratio'] = mode_ratio
    results.to_csv(os.path.join(DATA_DIR, 'regime_results.csv'))

    joblib.dump(model,    os.path.join(MODEL_DIR, 'hmm_model.pkl'))
    joblib.dump(last_pca, os.path.join(MODEL_DIR, 'pca_model.pkl'))

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
    if 'hy_spread' in current:
        print(f"  HY Spread       : {current['hy_spread']:.2f}%")
    if 'yield_slope' in current:
        print(f"  Yield Slope     : {current['yield_slope']:.2f}")
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
