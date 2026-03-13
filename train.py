"""
PCA -> HMM -> Regime-Dependent SV Pipeline
==========================================
1. Rolling 63-day PCA    -> principal components + market-mode ratio
2. BIC state selection   -> optimal K
3. Student-t HMM         -> regime labels + probabilities
4. Forward-only filter   -> real-time regime detection (no lookahead)
5. Multi-seed stability  -> robustness check
6. Regime-dependent SV   -> AR(1) log-vol per regime (Kalman filter)
7. Regime-dependent GARCH -> comparison benchmark
8. Walk-forward OOS      -> out-of-sample validation
9. Evaluation & plotting
"""

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
from scipy.stats import multivariate_t as _mvt, norm as _norm
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.mlemodel import MLEModel

from config import (
    RANDOM_SEED, N_STATES, N_STATES_RANGE, COV_TYPE, T_DF,
    N_SEEDS, HMM_ITER, PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD,
    PCA_ROLLING_WINDOW, VIX_BYPASS,
    GARCH_P, GARCH_Q, GARCH_DIST, MIN_REGIME_OBS, REGIME_HOLD_DAYS,
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS, VAR_ALPHA,
    REGIME_NAMES, DATA_DIR, MODEL_DIR, FIGURE_DIR, TICKERS,
)
from features import build_features, standardize

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
                X, loc=self.means_[k], shape=self.covars_[k], df=T_DF,
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

    for t in range(window - 1, T):
        chunk = X_scaled[t - window + 1: t + 1]
        pca = PCA(n_components=n_comp, random_state=RANDOM_SEED)
        scores = pca.fit_transform(chunk)

        # Sign-flip alignment with previous window
        if prev_loadings is not None:
            for j in range(n_comp):
                if np.dot(pca.components_[j], prev_loadings[j]) < 0:
                    pca.components_[j] *= -1
                    scores[:, j] *= -1

        prev_loadings = pca.components_.copy()
        all_scores[t] = scores[-1]          # current day's projection
        mode_ratio[t] = pca.explained_variance_ratio_[0]

    # Number of components: use last window's variance structure
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
    sorted_by_vix = sorted(regime_vix, key=regime_vix.get)
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

    def update(self, params, **kwargs):
        params = super().update(params, **kwargs)
        mu, phi, sigma_eta = params
        self['state_intercept'] = np.array([[mu * (1 - phi)]])
        self['transition'] = np.array([[phi]])
        self['state_cov'] = np.array([[sigma_eta ** 2]])


def fit_regime_sv(spy_returns, labels, name_map):
    """
    Fit linearized SV model per regime.

    Returns dict  {regime_id: {params, smoothed_h, annualized_vol}, 'full': ...}
    """
    y_all = spy_returns.dropna()

    # Transform: z_t = log(r_t^2), add epsilon to avoid log(0)
    z_all = np.log(y_all.values ** 2 + 1e-20)

    print("\nRegime-Dependent Stochastic Volatility (AR(1) log-vol):")

    # Full-sample SV
    results = {}
    try:
        sv_full = LinearizedSV(z_all)
        res_full = sv_full.fit(disp=False, maxiter=300)
        mu_f, phi_f, se_f = res_full.params
        h_smooth_full = res_full.smoothed_state[0]
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

        z = np.log(y.values ** 2 + 1e-20)

        try:
            sv_model = LinearizedSV(z)
            res = sv_model.fit(disp=False, maxiter=300)
            mu, phi, sigma_eta = res.params
            h_smooth = res.smoothed_state[0]
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
        vol_in_regime = cond_vol_all.reindex(y.index).dropna()

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

def walk_forward(market, features, n_states, n_pca, cov_type=COV_TYPE):
    """
    Expanding-window walk-forward.

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

        raw_preds = best_m.predict(pc_test)

        # Remap labels by VIX rank (consistent across windows)
        train_labels = best_m.predict(pc_train)
        vix_vals = market['VIX'].reindex(train_feats.index).values
        regime_vix = {}
        for r in range(n_states):
            mask = (train_labels == r)
            regime_vix[r] = vix_vals[mask].mean() if mask.any() else 0
        sorted_by_vix = sorted(regime_vix, key=regime_vix.get)
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
# 9. Plotting
# ===================================================================

_REGIME_COLORS = {
    'Low-Vol': 'green',   'Moderate': 'dodgerblue',
    'Elevated': 'gold',   'Crisis': 'red',
    'Medium-Vol': 'gold', 'High-Vol': 'red',
    'Very-Low': 'darkgreen',
}


def _get_blocks(mask):
    """Return (start, end) index pairs for contiguous True blocks."""
    blocks, in_block = [], False
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
                color=_REGIME_COLORS.get(name, 'gray'),
            )


def plot_regime_history(market, labels, name_map, title_suffix=''):
    """Multi-panel: SPY, VIX, HY spread, yield slope with regime shading."""
    panels = [('SPY', market.get('SPY_close'), 'k')]
    panels.append(('VIX', market.get('VIX'), 'b'))
    if 'hy_spread' in market.columns:
        panels.append(('HY Spread (%)', market['hy_spread'], 'r'))
    if 'yield_slope' in market.columns:
        panels.append(('Yield Slope', market['yield_slope'], 'teal'))

    fig, axes = plt.subplots(len(panels), 1,
                             figsize=(16, 4 * len(panels)), sharex=True)
    if len(panels) == 1:
        axes = [axes]

    label_series = pd.Series(labels, index=market.index[:len(labels)])

    for ax, (ylabel, data, color) in zip(axes, panels):
        _shade_regimes(ax, label_series, name_map, market.index)
        if data is not None:
            ax.plot(data.index, data, '-', color=color, lw=0.7)
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)

    axes[0].set_title(f'Market Regimes {title_suffix}',
                      fontsize=13, fontweight='bold')
    axes[0].legend(
        handles=[Patch(facecolor=_REGIME_COLORS.get(n, 'gray'), alpha=0.3, label=n)
                 for n in name_map.values()],
        loc='upper left',
    )
    if len(axes) > 1:
        axes[1].axhline(20, color='orange', ls='--', alpha=0.5)
        axes[1].axhline(30, color='red', ls='--', alpha=0.5)
    if 'yield_slope' in market.columns:
        axes[-1].axhline(0, color='red', ls='--', alpha=0.5)

    plt.tight_layout()
    return fig


def plot_regime_probabilities(market, model, pcs, name_map):
    """Stacked area chart of filtered (forward-only) regime probabilities."""
    probs = filtered_probs(model, pcs)
    ordered = sorted(name_map.keys())
    idx = market.index[:len(probs)]
    fig, ax = plt.subplots(figsize=(16, 5))
    bottom = np.zeros(len(probs))
    for r in ordered:
        name = name_map[r]
        ax.fill_between(idx, bottom, bottom + probs[:, r],
                        alpha=0.6,
                        color=_REGIME_COLORS.get(name, 'gray'), label=name)
        bottom += probs[:, r]
    ax.set_ylabel('Probability'); ax.set_xlabel('Date')
    ax.set_title('Regime Probabilities', fontsize=13, fontweight='bold')
    ax.legend(loc='upper left'); ax.grid(alpha=0.3)
    plt.tight_layout()
    return fig


def plot_current_state(market, model, pcs, name_map):
    """Current regime bar + last 90d pie (filtered/online)."""
    probs  = filtered_probs(model, pcs)
    labels = filtered_labels(model, pcs)
    current_probs = probs[-1]
    current_date  = market.index[-1].date()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ordered    = sorted(name_map.keys())
    bar_names  = [name_map[r] for r in ordered]
    bar_vals   = [current_probs[r] for r in ordered]
    bar_colors = [_REGIME_COLORS.get(n, 'gray') for n in bar_names]

    ax1.bar(bar_names, bar_vals, color=bar_colors, alpha=0.7)
    ax1.set_ylabel('Probability')
    ax1.set_title(f'Current Regime ({current_date})', fontweight='bold')
    ax1.set_ylim(0, 1); ax1.grid(axis='y', alpha=0.3)
    for i, v in enumerate(bar_vals):
        ax1.text(i, v + 0.02, f'{v:.0%}', ha='center', fontsize=11)

    recent = labels[-90:]
    name_series = pd.Series([name_map[l] for l in recent])
    counts = name_series.value_counts()
    ax2.pie(counts, labels=counts.index, autopct='%1.0f%%',
            colors=[_REGIME_COLORS.get(n, 'gray') for n in counts.index],
            startangle=90)
    ax2.set_title('Last 90 Days', fontweight='bold')
    plt.tight_layout()
    return fig


def plot_model_diagnostics(pca_model, bic_df, garch_results, name_map):
    """3-panel figure: PCA scree, BIC selection, GARCH parameters."""
    regimes = [r for r in sorted(name_map.keys()) if r in garch_results]
    has_garch = len(regimes) > 0

    fig, axes = plt.subplots(1, 3 if has_garch else 2,
                             figsize=(18 if has_garch else 12, 5))

    # Panel 1: PCA scree
    ax = axes[0]
    var = pca_model.explained_variance_ratio_
    cum = np.cumsum(var)
    x = range(1, len(var) + 1)
    ax.bar(x, var, alpha=0.6, label='Individual')
    ax.plot(x, cum, 'ro-', label='Cumulative')
    ax.axhline(PCA_VAR_THRESHOLD, color='gray', ls='--', alpha=0.5,
               label=f'{PCA_VAR_THRESHOLD:.0%} threshold')
    ax.set_xlabel('Principal Component')
    ax.set_ylabel('Explained Variance Ratio')
    ax.set_title('PCA Scree Plot')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # Panel 2: BIC selection
    ax = axes[1]
    best_idx = bic_df['BIC'].idxmin()
    colors = ['crimson' if i == best_idx else 'steelblue'
              for i in range(len(bic_df))]
    ax.bar(bic_df['K'], bic_df['BIC'], color=colors, alpha=0.7)
    ax.set_xlabel('Number of States (K)')
    ax.set_ylabel('BIC')
    ax.set_title(f"BIC — Best K={int(bic_df.loc[best_idx, 'K'])}")
    ax.grid(alpha=0.3)

    # Panel 3: GARCH parameters
    if has_garch:
        ax = axes[2]
        names   = [name_map[r] for r in regimes]
        omegas  = [garch_results[r].params.get('omega', 0) for r in regimes]
        alphas  = [garch_results[r].params.get('alpha[1]', 0) for r in regimes]
        betas   = [garch_results[r].params.get('beta[1]', 0) for r in regimes]
        xr = np.arange(len(regimes))
        w = 0.25
        ax.bar(xr - w, omegas, w, label='omega', alpha=0.7)
        ax.bar(xr,     alphas, w, label='alpha', alpha=0.7)
        ax.bar(xr + w, betas,  w, label='beta',  alpha=0.7)
        ax.set_xticks(xr); ax.set_xticklabels(names)
        ax.set_ylabel('Parameter Value')
        ax.set_title('GARCH(1,1) by Regime')
        ax.legend(fontsize=8); ax.grid(alpha=0.3)

    fig.suptitle('Model Diagnostics', fontsize=14, fontweight='bold')
    plt.tight_layout()
    return fig


def plot_market_mode(dates, mode_ratio, labels, name_map):
    """Plot the market-mode ratio over time with regime shading."""
    fig, ax = plt.subplots(figsize=(16, 5))
    label_series = pd.Series(labels, index=dates[:len(labels)])
    _shade_regimes(ax, label_series, name_map, dates)
    ax.plot(dates, mode_ratio, '-', color='navy', lw=0.8)
    ax.set_ylabel('$\\lambda_1 / \\Sigma\\lambda$')
    ax.set_title('Market-Mode Ratio (Rolling PCA)', fontsize=13, fontweight='bold')
    ax.legend(
        handles=[Patch(facecolor=_REGIME_COLORS.get(n, 'gray'), alpha=0.3, label=n)
                 for n in name_map.values()],
        loc='upper right', fontsize=8,
    )
    ax.grid(alpha=0.3)
    plt.tight_layout()
    return fig


def plot_sv_volatility(dates, sv_results, labels, name_map, vix_series=None):
    """Plot SV-implied annualized volatility vs VIX with regime shading."""
    fig, axes = plt.subplots(2, 1, figsize=(16, 9), sharex=False)

    # Panel 1: VIX vs SV latent vol (full sample)
    ax1 = axes[0]
    label_series = pd.Series(labels, index=dates[:len(labels)])
    _shade_regimes(ax1, label_series, name_map, dates)

    if vix_series is not None:
        ax1.plot(vix_series.index, vix_series.values, '-', color='blue',
                 lw=0.6, alpha=0.6, label='VIX')

    full_sv = sv_results.get('full', {})
    ann_vol = full_sv.get('annualized_vol')
    if ann_vol is not None:
        ax1.plot(dates[:len(ann_vol)], ann_vol, '-', color='darkred',
                 lw=0.8, label='SV Latent Vol (%)')

    ax1.set_ylabel('Volatility (%)')
    ax1.set_title('Stochastic Volatility: Latent Vol vs VIX',
                  fontsize=13, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(alpha=0.3)

    # Panel 2: SV parameters comparison across regimes
    ax2 = axes[1]
    regime_keys = [r for r in sorted(name_map.keys())
                   if r in sv_results and 'params' in sv_results.get(r, {})]
    if regime_keys:
        names = [name_map[r] for r in regime_keys]
        phis = [sv_results[r]['params']['phi'] for r in regime_keys]
        sigmas = [sv_results[r]['params']['sigma_eta'] for r in regime_keys]
        mean_vols = [sv_results[r]['annualized_vol'].mean()
                     for r in regime_keys]

        x = np.arange(len(regime_keys))
        w = 0.25
        ax2.bar(x - w, phis, w, label='phi (persistence)',
                alpha=0.7, color='steelblue')
        ax2.bar(x, [s * 5 for s in sigmas], w,
                label='sigma_eta x5 (vol-of-vol)', alpha=0.7, color='coral')
        ax2.bar(x + w, [v / 100 for v in mean_vols], w,
                label='mean vol / 100', alpha=0.7, color='seagreen')
        ax2.set_xticks(x); ax2.set_xticklabels(names)
        ax2.set_ylabel('Parameter Value')
        ax2.set_title('SV Parameters by Regime')
        ax2.legend(loc='upper left')
        ax2.grid(alpha=0.3)

    plt.tight_layout()
    return fig


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

    # ── 1. Rolling PCA ─────────────────────────────────────────────
    pcs, mode_ratio, valid_mask, n_pca, last_pca = fit_rolling_pca(X_scaled)

    # Trim everything to valid dates (after PCA warm-up)
    valid_dates    = feat_scaled.index[valid_mask]
    market_v       = market.loc[valid_dates]
    spy_ret_5d_v   = spy_ret_5d.loc[valid_dates]
    spy_daily_ret_v = spy_daily_ret.loc[valid_dates]

    # ── VIX bypass: append scaled VIX directly to PCs ─────────────
    if VIX_BYPASS:
        vix_valid = market_v['VIX'].values
        vix_mean, vix_std = vix_valid.mean(), vix_valid.std()
        vix_scaled = ((vix_valid - vix_mean) / vix_std).reshape(-1, 1)
        pcs = np.hstack([pcs, vix_scaled])
        print(f"  VIX bypass: appended scaled VIX as dim {pcs.shape[1]}")

    # ── 2. BIC state selection ─────────────────────────────────────
    best_k, bic_model, bic_df = select_states_bic(pcs)
    n_states = best_k

    # ── 3. Stability check ─────────────────────────────────────────
    model, agreement = check_stability(pcs, n_states)

    # ── 4. Label regimes ───────────────────────────────────────────
    labels, name_map = label_regimes(model, pcs, market_v)
    evaluate(market_v, pd.Series(labels, index=valid_dates),
             name_map, spy_ret_5d_v, 'In-Sample')

    # ── 5. Walk-forward OOS ────────────────────────────────────────
    print("\nWalk-Forward Validation:")
    oos_labels, oos_name_map = walk_forward(
        market, feat_raw, n_states, n_pca,
    )
    evaluate(market, oos_labels, oos_name_map, spy_ret_5d, 'Out-of-Sample')

    # ── 6. Transition matrix ──────────────────────────────────────
    print("\nTransition Matrix:")
    trans = pd.DataFrame(
        model.transmat_,
        columns=[name_map[i] for i in range(n_states)],
        index=[name_map[i] for i in range(n_states)],
    )
    print(trans.round(3))
    for r, name in name_map.items():
        p   = model.transmat_[r, r]
        dur = 1 / (1 - p) if p < 1 else np.inf
        print(f"  {name}: persistence={p:.1%}, avg duration={dur:.0f} days")

    # ── 7. Regime-dependent SV ─────────────────────────────────────
    spy_dr_v = spy_daily_ret_v.dropna()
    common_v = valid_dates.intersection(spy_dr_v.index)
    sv_results = fit_regime_sv(
        spy_dr_v.loc[common_v],
        pd.Series(labels, index=valid_dates).loc[common_v].values,
        name_map,
    )

    # ── 8. Regime-dependent GARCH ──────────────────────────────────
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

    # ── 9. Save results ───────────────────────────────────────────
    results = market_v.copy()
    results['regime'] = labels
    results['regime_name'] = [name_map[l] for l in labels]
    probs = filtered_probs(model, pcs)
    for r, name in name_map.items():
        results[f'prob_{name}'] = probs[:, r]
    results['market_mode_ratio'] = mode_ratio
    results.to_csv(os.path.join(DATA_DIR, 'regime_results.csv'))

    joblib.dump(model,    os.path.join(MODEL_DIR, 'hmm_model.pkl'))
    joblib.dump(last_pca, os.path.join(MODEL_DIR, 'pca_model.pkl'))

    # ── 10. Plots ─────────────────────────────────────────────────
    fig = plot_model_diagnostics(last_pca, bic_df, garch_results, name_map)
    fig.savefig(os.path.join(FIGURE_DIR, 'model_diagnostics.png'), dpi=150)

    fig = plot_regime_history(market_v, labels, name_map, '(In-Sample)')
    fig.savefig(os.path.join(FIGURE_DIR, 'regime_history.png'), dpi=150)

    fig = plot_regime_probabilities(market_v, model, pcs, name_map)
    fig.savefig(os.path.join(FIGURE_DIR, 'regime_probabilities.png'), dpi=150)

    fig = plot_current_state(market_v, model, pcs, name_map)
    fig.savefig(os.path.join(FIGURE_DIR, 'current_regime.png'), dpi=150)

    fig = plot_market_mode(valid_dates, mode_ratio, labels, name_map)
    fig.savefig(os.path.join(FIGURE_DIR, 'market_mode_ratio.png'), dpi=150)

    fig = plot_sv_volatility(
        valid_dates, sv_results, labels, name_map,
        vix_series=market_v['VIX'],
    )
    fig.savefig(os.path.join(FIGURE_DIR, 'sv_volatility.png'), dpi=150)

    if len(oos_labels) > 0:
        fig = plot_regime_history(
            market.loc[oos_labels.index],
            oos_labels.values,
            oos_name_map,
            '(Out-of-Sample)',
        )
        fig.savefig(os.path.join(FIGURE_DIR, 'regime_history_oos.png'), dpi=150)

    plt.close('all')

    # ── 11. Summary ───────────────────────────────────────────────
    current = results.iloc[-1]
    print(f"\n{'=' * 60}")
    print(f"Current State ({valid_dates[-1].date()}):")
    print(f"  Regime          : {current['regime_name']}")
    print(f"  VIX             : {current['VIX']:.1f}")
    if 'hy_spread' in current:
        print(f"  HY Spread       : {current['hy_spread']:.2f}%")
    if 'yield_slope' in current:
        print(f"  Yield Slope     : {current['yield_slope']:.2f}")
    print(f"  Market-Mode     : {current['market_mode_ratio']:.1%}")
    print(f"  PCA dims        : {n_pca}")
    print(f"  HMM states      : {n_states} (by BIC)")
    print(f"  Stability       : {agreement:.1%}")
    print(f"{'=' * 60}")

    return model, results
