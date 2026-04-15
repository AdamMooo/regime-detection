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

from src.config import (
    RANDOM_SEED, N_STATES, N_STATES_RANGE, COV_TYPE, T_DF,
    N_SEEDS, HMM_ITER, PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD,
    PCA_ROLLING_WINDOW, VIX_BYPASS, USE_HDP, HDP_INFERENCE, HDP_MAX_REGIMES,
    GARCH_P, GARCH_Q, GARCH_DIST, MIN_REGIME_OBS, REGIME_HOLD_DAYS,
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS,
    WALK_FORWARD_MODE, VAR_ALPHA, FEATURE_SUBSET,
    REGIME_NAMES, VOL_BRACKETS, DATA_DIR, MODEL_DIR, FIGURE_DIR, TICKERS,
    MAX_DATA_STALENESS_DAYS,
)
from src.features.features import build_features
from src.signals.signals import compute_signals
from src.core.inference import expanding_standardize, StudentTHMM, _fit_hmm, filtered_probs, filtered_labels
from src.core.hmm_training import fit_rolling_pca, select_states_bic, check_stability, label_regimes, fit_regime_sv, fit_regime_garch
from src.core.evaluation import evaluate, compute_var_backtest, compute_var_backtest_garch, kupiec_pof_test, christoffersen_test
from src.core.orchestrator import walk_forward

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
# Color mapping for regime visualization
# ===================================================================
_REGIME_COLORS_HEX = {
    # Classic regimes
    'Low-Vol': '#2E7D32',           # Green
    'Medium-Vol': '#F57C00',        # Orange
    'High-Vol': '#C62828',          # Red
    'Moderate': '#F57C00',          # Orange
    'Elevated': '#FF9800',          # Light Orange
    'Crisis': '#C62828',            # Red
    'Very-Low': '#1B5E20',          # Dark Green
    'Moderate-Vol': '#F57C00',      # Orange
    'Elevated-Vol': '#FF9800',      # Light Orange
    'Crisis-Vol': '#C62828',        # Red
}

def _get_regime_color(regime_name):
    """Get color for regime, handling suffixes like -B, -C from walk-forward validation."""
    if regime_name in _REGIME_COLORS_HEX:
        return _REGIME_COLORS_HEX[regime_name]
    # Strip suffix (-B, -C, etc.) and try base name
    base_name = regime_name.rsplit('-', 1)[0] if '-' in regime_name else regime_name
    return _REGIME_COLORS_HEX.get(base_name, '#888888')


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
    colors = [_get_regime_color(n) for n in regime_names]
    T_len = len(dates)
    label_arr = np.asarray(labels[:T_len])

    # helper: add regime shading via filled scatter shapes
    def _add_shading(fig, lab_arr, dt_arr, cols, ords, row=None, col=None):
        for r_idx, r in enumerate(ords):
            c_hex = cols[r_idx].lstrip('#')
            rv, gv, bv = int(c_hex[:2], 16), int(c_hex[2:4], 16), int(c_hex[4:6], 16)
            rgba = f'rgba({rv},{gv},{bv},0.22)'
            mask = lab_arr == r
            for s, e in _get_blocks(mask):
                kw = dict(
                    x0=dt_arr[s], x1=dt_arr[min(e, len(dt_arr) - 1)],
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
        _add_shading(fig_tl, label_arr, dates, colors, ordered,
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
        oos_cols = [_get_regime_color(n) for n in oos_nm]
        oos_dt = list(oos_labels.index)
        oos_la = oos_labels.values
        for row_i in [3, 4]:
            _add_shading(fig_tl, oos_la, oos_dt, oos_cols, oos_ord,
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
    _add_shading(fig_tl, label_arr, dates, colors, ordered,
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
        legend=dict(orientation='h', yanchor='bottom', y=1.01, font_size=12),
    )

    # Regime legend — invisible scatter traces with colored markers
    for r_idx, r in enumerate(ordered):
        fig_tl.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=10, color=colors[r_idx], symbol='square'),
            name=regime_names[r_idx], showlegend=True,
        ))

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

    # ── Sankey (top) — conditional probs P(j | leave i) ──────────
    sources, targets, values, link_colors, link_labels = [], [], [], [], []
    for i in range(K):
        off_diag = 1.0 - trans[i, i]
        for j in range(K):
            if i == j:
                continue
            cond_p = trans[i, j] / off_diag if off_diag > 1e-9 else 0.0
            if cond_p > 0.01:
                sources.append(i)
                targets.append(j + K)
                values.append(round(cond_p * 100, 1))
                link_labels.append(f'{regime_names[i]} → {regime_names[j]}: {cond_p:.0%}')
                c = colors[i].lstrip('#')
                rv, gv, bv = int(c[:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                link_colors.append(f'rgba({rv},{gv},{bv},0.4)')

    fig_sankey = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            pad=20, thickness=25, line=dict(color='#30363d', width=1),
            label=regime_names + regime_names,
            color=colors + colors,
        ),
        link=dict(source=sources, target=targets, value=values,
                  color=link_colors, label=link_labels),
    ))

    # Self-loop annotations
    annotations = []
    for i in range(K):
        p = trans[i, i]
        annotations.append(dict(
            text=f'{regime_names[i]}: {p:.1%} persist',
            x=0, y=1 - i / max(K - 1, 1),
            xref='paper', yref='paper',
            showarrow=False, font=dict(size=11, color=colors[i]),
            xanchor='left',
        ))

    fig_sankey.update_layout(
        template='plotly_dark', paper_bgcolor='#0d1117',
        title=dict(text='Conditional Transition Flows  (P(j | leave i))',
                   font_size=18),
        height=450, margin=dict(l=140, r=30, t=60, b=10),
        annotations=annotations,
    )

    # ── Transition matrix heatmap ──────────────────────────────────
    fig_matrix = go.Figure(go.Heatmap(
        z=[[trans[i, j] for j in range(K)] for i in range(K)],
        x=regime_names, y=regime_names,
        text=[[f'{trans[i, j]:.1%}' for j in range(K)] for i in range(K)],
        texttemplate='%{text}', textfont=dict(size=13),
        colorscale=[
            [0, '#0d1117'], [0.02, '#161b22'],
            [0.1, '#1f6feb'], [0.5, '#f0883e'], [1, '#f85149'],
        ],
        zmin=0, zmax=1, showscale=True,
        colorbar=dict(title='P', tickformat='.0%', len=0.8),
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

    header_vals = ['Regime', 'Days', '%', 'Avg Duration', 'Median Duration',
                   'Persistence', 'Top Exit →', 'Cond Exit %']
    cell_vals = [[] for _ in range(8)]

    for i, r in enumerate(ordered):
        name = regime_names[i]
        mask = label_arr == r
        n_days = mask.sum()
        pct = n_days / total_days

        # average & median duration via blocks
        blocks = _get_blocks(mask)
        block_durs = [e - s + 1 for s, e in blocks]
        avg_dur = np.mean(block_durs) if block_durs else 0
        med_dur = float(np.median(block_durs)) if block_durs else 0

        persist = trans[i, i]

        # top exit destination — conditional P(j | leave i)
        off_diag = 1.0 - persist
        exit_probs = []
        for oi, j in enumerate(range(K)):
            if j != i:
                cond_p = trans[i, j] / off_diag if off_diag > 1e-9 else 0.0
                exit_probs.append((cond_p, regime_names[oi]))
        exit_probs.sort(reverse=True)
        top_exit_name = exit_probs[0][1] if exit_probs else '-'
        top_exit_pct = exit_probs[0][0] if exit_probs else 0

        cell_vals[0].append(name)
        cell_vals[1].append(f'{n_days}')
        cell_vals[2].append(f'{pct:.1%}')
        cell_vals[3].append(f'{avg_dur:.1f}d')
        cell_vals[4].append(f'{med_dur:.0f}d')
        cell_vals[5].append(f'{persist:.1%}')
        cell_vals[6].append(top_exit_name)
        cell_vals[7].append(f'{top_exit_pct:.0%}')

    # Row-level fill: light tint of regime color
    row_fills = []
    for n in cell_vals[0]:
        c_hex = _get_regime_color(n).lstrip('#')
        rv, gv, bv = int(c_hex[:2], 16), int(c_hex[2:4], 16), int(c_hex[4:6], 16)
        row_fills.append(f'rgba({rv},{gv},{bv},0.08)')

    fig_table = go.Figure(go.Table(
        header=dict(
            values=[f'<b>{v}</b>' for v in header_vals],
            fill_color='#161b22', line_color='#30363d',
            font=dict(color='#c9d1d9', size=12), align='center',
        ),
        cells=dict(
            values=cell_vals,
            fill_color=[row_fills] * 8,
            line_color='#30363d',
            font=dict(
                color=[colors] + [['#c9d1d9'] * K] * 7,
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
    # Live label = argmax of current filtered probabilities (no hysteresis)
    current_label = int(current_probs.argmax())
    # Held label = hysteresis-smoothed; may lag live signal by REGIME_HOLD_DAYS days
    held_label    = labels[-1]
    current_name  = name_map.get(current_label, '?')
    current_color = _get_regime_color(current_name)
    K = len(ordered)

    # ── Compute statistics ─────────────────────────────────────────
    label_arr = np.asarray(labels)
    total_days = len(label_arr)
    # Live argmax series — used for streak and block durations
    live_arr = probs.argmax(axis=1)

    # Current streak — consecutive days the live model calls this regime
    streak = 1
    for t in range(len(live_arr) - 2, -1, -1):
        if live_arr[t] == current_label:
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

    # Historical block durations for current regime (from live argmax series)
    blocks = _get_blocks(live_arr == current_label)
    durations = [e - s + 1 for s, e in blocks]
    median_dur = float(np.median(durations)) if durations else 0
    max_dur = max(durations) if durations else 0
    pct_time = (live_arr == current_label).sum() / total_days

    # Market context
    vix_val = market['VIX'].iloc[-1] if 'VIX' in market.columns else None
    spy_close = market['SPY_close'].iloc[-1] if 'SPY_close' in market.columns else None
    spy_20d_ret = None
    if 'SPY_close' in market.columns and len(market) >= 20:
        spy_20d_ret = (market['SPY_close'].iloc[-1] /
                       market['SPY_close'].iloc[-20] - 1) * 100
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

    # Top exit destinations — conditional on leaving (normalize off-diagonal)
    exit_info = []
    if trans is not None:
        off_diag_sum = 1.0 - trans[cur_idx, cur_idx]
        for j in range(K):
            if j != cur_idx:
                cond_prob = trans[cur_idx, j] / off_diag_sum if off_diag_sum > 1e-9 else 0.0
                exit_info.append((cond_prob, regime_names[j]))
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
    held_name = name_map.get(held_label, '?')
    held_note = (
        f'<br><span style="color:#f0883e;font-size:12px">'
        f'held label: {held_name} (pending {REGIME_HOLD_DAYS}-day confirmation)</span>'
        if held_label != current_label else ''
    )
    fig_status.add_annotation(
        text=(f'<b style="color:{current_color};font-size:32px">'
              f'{current_name}</b>'
              f'<br><span style="color:#8b949e;font-size:14px">'
              f'as of {current_date}</span>'
              f'{held_note}'),
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
        'Geometric Expected Duration',
        'Geometric Remaining',
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
    pie_colors = [_get_regime_color(n) for n in counts.index]
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
        exit_colors = [_get_regime_color(n) for n in exit_names]

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

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=False, row_heights=[0.6, 0.4],
        vertical_spacing=0.1,
        subplot_titles=['SV Latent Vol vs VIX', 'SV Parameters by Regime'],
    )

    # Regime shading on top panel
    for r_idx, r in enumerate(ordered):
        c_hex = colors[r_idx].lstrip('#')
        rv, gv, bv = int(c_hex[:2], 16), int(c_hex[2:4], 16), int(c_hex[4:6], 16)
        rgba = f'rgba({rv},{gv},{bv},0.22)'
        mask = label_arr == r
        for s, e in _get_blocks(mask):
            fig.add_vrect(
                x0=dates[s], x1=dates[min(e, T_len - 1)],
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
            fill_color='#21262d', font=dict(color='#c9d1d9', size=12),
            align='left',
        ),
        cells=dict(
            values=[dist_regime, dist_vol, dist_skew, dist_kurt,
                    dist_var5, dist_cvar5, dist_dd, dist_days, dist_normal],
            fill_color=cell_colors_dist,
            font=dict(color='#c9d1d9', size=12),
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
            fill_color='#21262d', font=dict(color='#c9d1d9', size=12),
            align='left',
        ),
        cells=dict(
            values=[vol_labels, vol_values],
            fill_color='#0d1117',
            font=dict(color='#c9d1d9', size=12),
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
                fill_color='#21262d', font=dict(color='#c9d1d9', size=12),
                align='left',
            ),
            cells=dict(
                values=[t_regimes, t_probs, t_dir, t_jump],
                fill_color=[t_colors] * 4,
                font=dict(color='#c9d1d9', size=12),
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
            f"({vr['n_breaches']}/{vr['n_evaluated']}) — "
            f"{'PASS' if vr['ok'] else 'FAIL'}"
        )
        val_row_colors.append('#0a3d0a' if vr['ok'] else '#3d0a0a')

    fig.add_trace(go.Table(
        header=dict(
            values=['Validation Check', 'Result'],
            fill_color='#21262d', font=dict(color='#c9d1d9', size=12),
            align='left',
        ),
        cells=dict(
            values=[val_labels, val_values],
            fill_color=[['#0d1117'] * len(val_labels), val_row_colors],
            font=dict(color='#c9d1d9', size=12),
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
            fill_color='#21262d', font=dict(color='#c9d1d9', size=12),
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
            fill_color='#21262d', font=dict(color='#c9d1d9', size=12),
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
            font=dict(color='#c9d1d9', size=12),
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
    from datetime import datetime as _dt

    timestamp = _dt.now().strftime('%Y-%m-%d %H:%M')

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
    font-size: 24px; font-weight: 600;
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
    background: none; border: none; color: #8b949e; padding: 12px 22px;
    font-size: 15px; cursor: pointer; border-bottom: 2px solid transparent;
    transition: all 0.2s; font-weight: 500;
  }}
  .tab-btn:hover {{ color: #c9d1d9; background: rgba(88, 166, 255, 0.06); }}
  .tab-btn.active {{
    color: #58a6ff; border-bottom-color: #58a6ff;
  }}
  .tab-content {{ padding: 12px 8px; max-width: 100%; overflow-x: auto; }}
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
  <span class="badge">Updated: {timestamp}</span>
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

def train(reload_pca_checkpoint_path=None):
    """
    Train HMM model with optional PCA checkpoint reload.

    Args:
        reload_pca_checkpoint_path: Path to joblib checkpoint containing cached PCA.
                                   If None, compute PCA from scratch.
    """
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

    # ── PCA Checkpoint Load (incremental mode) ─────────────────────
    # Per D-07: Load cached PCA from prior run if available
    reload_pca = None
    if reload_pca_checkpoint_path and os.path.exists(reload_pca_checkpoint_path):
        try:
            checkpoint = joblib.load(reload_pca_checkpoint_path)
            reload_pca = checkpoint.get('pca')
            print(f"  Loaded cached PCA from checkpoint: {reload_pca_checkpoint_path}")
        except Exception as e:
            print(f"  WARNING: Failed to load PCA checkpoint ({e}); recomputing from scratch")
            reload_pca = None

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
        from src.core.hdp_hmm import (
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

    # ── Compute GARCH-conditional VaR for each date ─────────────────
    from src.signals.signals import compute_garch_var
    garch_var_95 = []
    spy_ret = np.log(results['SPY_close'] / results['SPY_close'].shift(1)).dropna()
    for i, (date, row) in enumerate(results.iterrows()):
        regime_name = row['regime_name']
        # Use past 20 days of returns
        start_idx = max(0, i - 20)
        recent_rets = spy_ret.iloc[start_idx:i].values
        if len(recent_rets) >= 5:
            var_95 = compute_garch_var(regime_name, recent_rets, alpha=0.05)
        else:
            var_95 = np.nan
        garch_var_95.append(var_95)
    results['garch_var_95'] = garch_var_95

    results.to_csv(os.path.join(DATA_DIR, 'regime_results.csv'))

    # Save unified model checkpoint (includes PCA for incremental mode)
    model_checkpoint = {
        'model': model,
        'pca': last_pca,
        'regime_results': results,
    }
    checkpoint_path = os.path.join(MODEL_DIR, 'regime_model.pkl')
    joblib.dump(model_checkpoint, checkpoint_path)
    print(f"  Saved model checkpoint (with PCA): {checkpoint_path}")

    # Also save individual checkpoints for backward compatibility
    joblib.dump(model,    os.path.join(MODEL_DIR, 'hmm_model.pkl'))
    joblib.dump(last_pca, os.path.join(MODEL_DIR, 'pca_model.pkl'))
    feat_scaled.to_csv(os.path.join(DATA_DIR, 'features_scaled.csv'))

    # Save PCA components for dashboard
    pca_cols = [f'PC{i+1}' for i in range(pcs.shape[1])]
    pca_df = pd.DataFrame(pcs, index=valid_dates, columns=pca_cols)
    pca_df.to_csv(os.path.join(DATA_DIR, 'pca_components.csv'))
    print(f"  Saved PCA components ({pcs.shape[1]} dims, {len(pcs)} dates)")

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

    return model, last_pca, results


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
