"""
HDP-HMM vs StudentTHMM Comparison (Phase 6, MODEL-02)

Compares HDP-HMM (SVI) vs StudentTHMM on the same OOS split used in
Phase 4/5 diagnostics to lock the USE_HDP decision.

Procedure:
1. Load feature data and market data from DATA_DIR
2. Run StudentTHMM via walk_forward harness (OOS labels + dwell time)
3. Run HDP-HMM via manual fold loop on identical PCs (SVI inference only, D-02)
4. Compute OOS accuracy and mean dwell time for both models
5. Apply verdict logic (D-03): HDP wins only if +2pp accuracy AND meaningfully longer dwell
6. Print comparison table; write full results to data/hdp_comparison_results.json

Output:
- data/hdp_comparison_results.json: machine verdict + per-fold convergence + metrics
- stdout: formatted comparison table
"""

import os
import sys
import json
import logging
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

# Add repo root to path (matches select_k_via_crossval.py pattern)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import (
    HDP_TRUNCATION, N_STATES, DATA_DIR, MODEL_DIR,
    FEATURE_SUBSET, PCA_ROLLING_WINDOW, RANDOM_SEED,
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS, WALK_FORWARD_MODE,
    VIX_BYPASS, REGIME_HOLD_DAYS, COV_TYPE, VOL_BRACKETS, SVI_NUM_STEPS,
)
from src.core.orchestrator import walk_forward
from src.core.inference import expanding_standardize, _fit_hmm, filtered_labels
from src.core.hdp_hmm import (
    fit_hdp_hmm, posterior_mean_params,
    get_labels_and_probs, label_regimes_hdp, mcmc_diagnostics,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


# ===================================================================
# Data Loading
# ===================================================================

def load_data():
    """Load market data and features from DATA_DIR.

    Returns (market, features, spy_returns) where:
    - market: DataFrame with market data (VIX, SPY_close, etc.)
    - features: DataFrame filtered to available FEATURE_SUBSET columns
    - spy_returns: Series of SPY log returns
    """
    market = pd.read_csv(
        os.path.join(DATA_DIR, 'market_data.csv'),
        index_col=0, parse_dates=True,
    )
    feat_raw = pd.read_csv(
        os.path.join(DATA_DIR, 'features_transformed.csv'),
        index_col=0, parse_dates=True,
    )

    # Apply feature subset (filter to available columns only — handles missing FRED features)
    if FEATURE_SUBSET:
        available = [f for f in FEATURE_SUBSET if f in feat_raw.columns]
        if len(available) < len(FEATURE_SUBSET):
            missing = [f for f in FEATURE_SUBSET if f not in feat_raw.columns]
            logger.warning(f"Missing FEATURE_SUBSET columns (no macro data?): {missing}")
            logger.warning(f"Proceeding with {len(available)} of {len(FEATURE_SUBSET)} features")
        feat_raw = feat_raw[available]

    # SPY log returns for vol-bracket naming
    spy_col = 'SPY_close' if 'SPY_close' in market.columns else 'SPY_Close'
    spy_prices = market[spy_col].dropna()
    spy_returns = np.log(spy_prices / spy_prices.shift(1)).dropna()

    logger.info(f"Data loaded: {len(market)} market days, {len(feat_raw.columns)} features")
    logger.info(f"Feature columns: {list(feat_raw.columns)}")

    return market, feat_raw, spy_returns


# ===================================================================
# Metric Helpers
# ===================================================================

def mean_dwell_time(labels):
    """Compute mean dwell time (mean run length) from a label sequence.

    Exact run-length loop from src/signals/signals.py:_validation_metrics().
    Works on any label Series or array (named or integer).
    """
    if hasattr(labels, 'values'):
        labels = labels.values
    if len(labels) == 0:
        return 0.0
    run_lengths = []
    curr_len = 1
    for i in range(1, len(labels)):
        if labels[i] == labels[i - 1]:
            curr_len += 1
        else:
            run_lengths.append(curr_len)
            curr_len = 1
    run_lengths.append(curr_len)
    return float(np.mean(run_lengths))


def oos_accuracy(is_named_labels, oos_named_labels):
    """Compare IS and OOS named labels on overlapping dates.

    # Pitfall 2: compare on named labels, NOT integers
    Both args should be string-label Series with DatetimeIndex.

    Returns (accuracy, n_common).
    """
    common = is_named_labels.index.intersection(oos_named_labels.index)
    if len(common) == 0:
        return 0.0, 0
    # Pitfall 2: compare on named labels, NOT integers
    agree = (is_named_labels[common] == oos_named_labels[common])
    return float(agree.mean()), len(common)


# ===================================================================
# StudentTHMM OOS Path
# ===================================================================

def run_studenthmm_oos(market, features):
    """Run StudentTHMM walk-forward OOS validation.

    Uses walk_forward harness directly — USE_HDP=False is config default
    so the harness uses StudentTHMM.

    Returns dict with oos_named_labels, name_map, dwell, n_obs.
    """
    print("\n" + "=" * 70)
    print("STUDENTTHMM: Walk-Forward OOS Validation")
    print("=" * 70)

    n_pca = min(5, features.shape[1])
    oos_int_labels, name_map = walk_forward(
        market, features,
        n_states=N_STATES,
        n_pca=n_pca,
        cov_type=COV_TYPE,
        mode=WALK_FORWARD_MODE,
    )

    # Convert integer labels back to named labels using name_map
    # (walk_forward returns int-coded labels + name_map)
    oos_named = oos_int_labels.map(name_map)

    dwell = mean_dwell_time(oos_named.dropna())
    n_obs = oos_named.dropna().__len__()

    print(f"\nStudentTHMM OOS: n_obs={n_obs}, dwell={dwell:.1f} days")
    print(f"Name map: {name_map}")

    return {
        'oos_named_labels': oos_named,
        'name_map': name_map,
        'dwell': dwell,
        'n_obs': n_obs,
    }


def _run_studenthmm_full_sample(market, features):
    """Run StudentTHMM on full sample for IS labels (used in oos_accuracy)."""
    n_pca = min(5, features.shape[1])
    min_warmup = min(252, max(50, len(features) // 4))

    X_scaled, _, _ = expanding_standardize(features.values, min_warmup=min_warmup)
    valid_mask = ~np.isnan(X_scaled[:, 0])
    X_valid = X_scaled[valid_mask]
    features_valid = features[valid_mask]

    pca_window = min(PCA_ROLLING_WINDOW, len(X_valid))
    n_comp = min(n_pca, X_valid.shape[1])
    pca_full = PCA(n_components=n_comp, random_state=RANDOM_SEED)
    pca_full.fit(X_valid[-pca_window:])
    pcs = pca_full.transform(X_valid)

    if VIX_BYPASS:
        vix_vals = market['VIX'].reindex(features_valid.index).values
        v_mean, v_std = vix_vals.mean(), vix_vals.std()
        pcs = np.hstack([pcs, ((vix_vals - v_mean) / v_std).reshape(-1, 1)])

    best_m, best_ll = None, -np.inf
    for seed in range(5):
        m = _fit_hmm(pcs, N_STATES, COV_TYPE, seed)
        ll = m.score(pcs)
        if ll > best_ll:
            best_m, best_ll = m, ll

    raw_labels = filtered_labels(best_m, pcs, hold_days=REGIME_HOLD_DAYS)

    spy_col = 'SPY_close' if 'SPY_close' in market.columns else 'SPY_Close'
    spy_train = market[spy_col].reindex(features_valid.index)
    spy_ret = np.log(spy_train / spy_train.shift(1)).dropna().values
    tl_aligned = raw_labels[1:len(spy_ret) + 1]

    fold_vol = {}
    for r in range(N_STATES):
        mask = (tl_aligned == r)
        if mask.sum() > 5:
            fold_vol[r] = float(np.std(spy_ret[mask]) * np.sqrt(252) * 100)
        else:
            fold_vol[r] = 0.0

    name_map = {}
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
        name_map[r] = bracket_name

    named_labels = pd.Series(
        [name_map.get(r, f'Regime-{r}') for r in raw_labels],
        index=features_valid.index,
    )
    return named_labels


# ===================================================================
# HDP-HMM OOS Path
# ===================================================================

def run_hdp_oos(market, features, spy_returns):
    """Run HDP-HMM walk-forward OOS validation.

    Replicates the walk_forward fold loop so HDP sees the SAME pcs arrays
    on the SAME date ranges as StudentTHMM (Pitfall 1 alignment guard).

    # D-02: inference='svi' is literal — no NUTS path may be invoked here
    Returns dict with oos_named_labels, dwell, n_obs, convergence info.
    """
    print("\n" + "=" * 70)
    print("HDP-HMM (SVI): Walk-Forward OOS Validation")
    print("=" * 70)

    min_train = WALK_FORWARD_TRAIN_YEARS * 252
    step = WALK_FORWARD_STEP_DAYS
    n_pca = min(5, features.shape[1])

    all_oos_named = []
    fold_convergence = []
    n_folds_converged = 0
    n_folds_total = 0

    t = min_train
    step_num = 0

    while t < len(features):
        end = min(t + step, len(features))
        n_folds_total += 1

        if WALK_FORWARD_MODE == 'rolling':
            train_start = max(0, t - min_train)
            train_feats = features.iloc[train_start:t]
        else:
            train_feats = features.iloc[:t]
        test_feats = features.iloc[t:end]

        if len(test_feats) == 0:
            t = end
            continue

        # Expanding-window standardize (match walk_forward exactly — Pitfall 1)
        X_combined = np.vstack([train_feats.values, test_feats.values])
        wf_warmup = min(252, max(50, len(train_feats) // 4))
        X_all_scaled, _, _ = expanding_standardize(X_combined, min_warmup=wf_warmup)
        X_train = X_all_scaled[:len(train_feats)]
        X_test = X_all_scaled[len(train_feats):]

        valid_train = ~np.isnan(X_train[:, 0])
        X_train_v = X_train[valid_train]
        train_feats_v = train_feats[valid_train]

        # PCA: fit on last PCA_ROLLING_WINDOW rows of train (same as walk_forward)
        pca_window = min(PCA_ROLLING_WINDOW, len(X_train_v))
        n_comp = min(n_pca, X_train_v.shape[1])
        pca_wf = PCA(n_components=n_comp, random_state=RANDOM_SEED)
        pca_wf.fit(X_train_v[-pca_window:])
        pc_train = pca_wf.transform(X_train_v)
        pc_test = pca_wf.transform(X_test)

        if VIX_BYPASS:
            vix_train = market['VIX'].reindex(train_feats_v.index).values
            vix_test = market['VIX'].reindex(test_feats.index).values
            v_mean, v_std = vix_train.mean(), vix_train.std()
            pc_train = np.hstack([pc_train, ((vix_train - v_mean) / v_std).reshape(-1, 1)])
            pc_test = np.hstack([pc_test, ((vix_test - v_mean) / v_std).reshape(-1, 1)])

        # Fit HDP-HMM on training PCs
        # D-02: inference='svi' is literal — no NUTS path may be invoked here
        result, samples = fit_hdp_hmm(pc_train, K_max=HDP_TRUNCATION, inference='svi')

        diag = mcmc_diagnostics(result, samples)
        converged = diag.get('converged', False)

        # Pitfall 3: skip non-converged folds from metric aggregation
        if not converged:
            logger.warning(f"Fold {step_num}: SVI did not converge — skipping labels for this fold")
            fold_convergence.append({'fold': step_num, 'converged': False})
            t = end
            step_num += 1
            continue

        n_folds_converged += 1
        fold_convergence.append({'fold': step_num, 'converged': True})

        # Decode OOS labels from training posterior
        params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)

        # Get labels on full train set for vol-bracket naming
        labels_train, _, _, active_states = get_labels_and_probs(pc_train, params)

        # Name map from training window SPY returns
        spy_train_idx = market['VIX'].reindex(train_feats_v.index).index
        spy_col = 'SPY_close' if 'SPY_close' in market.columns else 'SPY_Close'
        spy_train_prices = market[spy_col].reindex(train_feats_v.index)
        spy_ret_train = np.log(spy_train_prices / spy_train_prices.shift(1)).dropna().values

        # Align labels with returns (drop first for diff)
        tl_aligned = labels_train[1:len(spy_ret_train) + 1]
        # Remap to active-state local indices for label_regimes_hdp
        # labels from get_labels_and_probs are already local (0..len(active)-1)
        # label_regimes_hdp expects local labels and active_states list
        name_map, state_vols = label_regimes_hdp(tl_aligned, active_states, spy_ret_train)
        print(f"  Per-state realized vols: {state_vols}")

        # Apply trained model to test PCs for OOS labels
        labels_test, _, _, _ = get_labels_and_probs(pc_test, params)

        # Pitfall 2: compare on named labels, NOT integers
        named_test = pd.Series(
            [name_map.get(r, f'Regime-{r}') for r in labels_test],
            index=test_feats.index,
        )
        all_oos_named.append(named_test)

        step_num += 1
        if step_num % 10 == 0:
            print(f"    HDP fold {step_num}")
        t = end

    if len(all_oos_named) == 0:
        logger.error("No converged HDP folds — returning empty results")
        return {
            'oos_named_labels': pd.Series(dtype=object),
            'dwell': 0.0,
            'n_obs': 0,
            'all_folds_converged': False,
            'n_folds_converged': 0,
            'n_folds_total': n_folds_total,
        }

    oos_named = pd.concat(all_oos_named)
    dwell = mean_dwell_time(oos_named)
    n_obs = len(oos_named)
    all_converged = (n_folds_converged == n_folds_total)

    print(f"\nHDP OOS: n_obs={n_obs}, dwell={dwell:.1f} days")
    print(f"Convergence: {n_folds_converged}/{n_folds_total} folds converged")

    return {
        'oos_named_labels': oos_named,
        'dwell': dwell,
        'n_obs': n_obs,
        'all_folds_converged': all_converged,
        'n_folds_converged': n_folds_converged,
        'n_folds_total': n_folds_total,
    }


def _run_hdp_full_sample(market, features, spy_returns):
    """Run HDP-HMM on full sample for IS labels (used in oos_accuracy).

    # D-02: inference='svi' is literal — no NUTS path may be invoked here
    """
    n_pca = min(5, features.shape[1])
    min_warmup = min(252, max(50, len(features) // 4))

    X_scaled, _, _ = expanding_standardize(features.values, min_warmup=min_warmup)
    valid_mask = ~np.isnan(X_scaled[:, 0])
    X_valid = X_scaled[valid_mask]
    features_valid = features[valid_mask]

    pca_window = min(PCA_ROLLING_WINDOW, len(X_valid))
    n_comp = min(n_pca, X_valid.shape[1])
    pca_full = PCA(n_components=n_comp, random_state=RANDOM_SEED)
    pca_full.fit(X_valid[-pca_window:])
    pcs = pca_full.transform(X_valid)

    if VIX_BYPASS:
        vix_vals = market['VIX'].reindex(features_valid.index).values
        v_mean, v_std = vix_vals.mean(), vix_vals.std()
        pcs = np.hstack([pcs, ((vix_vals - v_mean) / v_std).reshape(-1, 1)])

    # D-02: inference='svi' is literal — no NUTS path may be invoked here
    result, samples = fit_hdp_hmm(pcs, K_max=HDP_TRUNCATION, inference='svi')
    diag = mcmc_diagnostics(result, samples)

    if not diag.get('converged', False):
        logger.warning("Full-sample HDP fit did not converge")

    params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
    labels, _, _, active_states = get_labels_and_probs(pcs, params)

    spy_col = 'SPY_close' if 'SPY_close' in market.columns else 'SPY_Close'
    spy_prices = market[spy_col].reindex(features_valid.index)
    spy_ret = np.log(spy_prices / spy_prices.shift(1)).dropna().values
    tl_aligned = labels[1:len(spy_ret) + 1]

    name_map, state_vols = label_regimes_hdp(tl_aligned, active_states, spy_ret)
    print(f"  Per-state realized vols: {state_vols}")

    named_labels = pd.Series(
        [name_map.get(r, f'Regime-{r}') for r in labels],
        index=features_valid.index,
    )
    return named_labels


# ===================================================================
# Verdict Logic
# ===================================================================

def compare_and_verdict(student_metrics, hdp_metrics):
    """Apply D-03 verdict logic: HDP wins only if +2pp accuracy AND meaningfully longer dwell.

    Returns dict with all comparison numbers + verdict.
    """
    student_accuracy = student_metrics['accuracy']
    student_dwell = student_metrics['dwell']
    hdp_accuracy = hdp_metrics['accuracy']
    hdp_dwell = hdp_metrics['dwell']
    all_folds_converged = hdp_metrics['all_folds_converged']

    accuracy_delta = hdp_accuracy - student_accuracy
    dwell_delta = hdp_dwell - student_dwell

    # Determine verdict
    if not all_folds_converged:
        # Pitfall 3: non-converged folds mean inconclusive result
        verdict = 'inconclusive'
    elif (accuracy_delta >= 0.02
          and dwell_delta > 0
          and (student_dwell == 0 or dwell_delta / student_dwell >= 0.10)):
        # D-03: +2pp accuracy AND meaningfully longer dwell (>=10% improvement)
        verdict = 'hdp_wins'
    else:
        verdict = 'studenthmm_wins'

    print(f"\n{'=' * 70}")
    print("VERDICT LOGIC (D-03)")
    print(f"{'=' * 70}")
    print(f"  accuracy_delta = {accuracy_delta:+.4f}  (need >= +0.02 for HDP win)")
    print(f"  dwell_delta    = {dwell_delta:+.2f}  (need > 0 and >= 10% gain)")
    if student_dwell > 0:
        print(f"  dwell % gain   = {dwell_delta/student_dwell:+.1%}")
    print(f"  all_folds_converged = {all_folds_converged}")
    print(f"\n  VERDICT: {verdict.upper()}")

    return {
        'student_accuracy': student_accuracy,
        'student_dwell': student_dwell,
        'hdp_accuracy': hdp_accuracy,
        'hdp_dwell': hdp_dwell,
        'accuracy_delta': accuracy_delta,
        'dwell_delta': dwell_delta,
        'all_folds_converged': all_folds_converged,
        'n_folds_converged': hdp_metrics['n_folds_converged'],
        'n_folds_total': hdp_metrics['n_folds_total'],
        'verdict': verdict,
        'student_n_obs': student_metrics['n_obs'],
        'hdp_n_obs': hdp_metrics['n_obs'],
    }


# ===================================================================
# Main
# ===================================================================

def main():
    """Run HDP-HMM vs StudentTHMM comparison and write results."""

    print("\n" + "#" * 70)
    print("# HDP-HMM vs StudentTHMM OOS COMPARISON (Phase 6, MODEL-02)")
    print("#" * 70)
    print(f"Start time: {pd.Timestamp.now()}")
    print(f"SVI_NUM_STEPS={SVI_NUM_STEPS}, HDP_TRUNCATION={HDP_TRUNCATION}, N_STATES={N_STATES}")

    # Load data
    print("\nLoading data...")
    market, features, spy_returns = load_data()

    # ===================================================================
    # StudentTHMM path
    # ===================================================================
    student_oos = run_studenthmm_oos(market, features)

    # Full-sample IS labels for OOS accuracy computation
    print("\nFitting StudentTHMM full sample (for IS reference)...")
    student_is_labels = _run_studenthmm_full_sample(market, features)

    student_acc, student_n_common = oos_accuracy(student_is_labels, student_oos['oos_named_labels'])
    print(f"StudentTHMM OOS accuracy: {student_acc:.4f} ({student_n_common} common obs)")

    student_metrics = {
        'accuracy': student_acc,
        'dwell': student_oos['dwell'],
        'n_obs': student_oos['n_obs'],
        'n_common': student_n_common,
    }

    # ===================================================================
    # HDP-HMM path
    # ===================================================================
    hdp_oos = run_hdp_oos(market, features, spy_returns)

    if hdp_oos['n_obs'] > 0 and hdp_oos['all_folds_converged']:
        print("\nFitting HDP-HMM full sample (for IS reference)...")
        hdp_is_labels = _run_hdp_full_sample(market, features, spy_returns)
        hdp_acc, hdp_n_common = oos_accuracy(hdp_is_labels, hdp_oos['oos_named_labels'])
        print(f"HDP-HMM OOS accuracy: {hdp_acc:.4f} ({hdp_n_common} common obs)")
    else:
        logger.warning("HDP-HMM folds not all converged — skipping full-sample IS fit")
        hdp_acc = 0.0
        hdp_n_common = 0

    hdp_metrics = {
        'accuracy': hdp_acc,
        'dwell': hdp_oos['dwell'],
        'n_obs': hdp_oos['n_obs'],
        'n_common': hdp_n_common,
        'all_folds_converged': hdp_oos['all_folds_converged'],
        'n_folds_converged': hdp_oos['n_folds_converged'],
        'n_folds_total': hdp_oos['n_folds_total'],
    }

    # ===================================================================
    # Verdict
    # ===================================================================
    results = compare_and_verdict(student_metrics, hdp_metrics)

    # ===================================================================
    # Formatted comparison table
    # ===================================================================
    print(f"\n{'=' * 70}")
    print("COMPARISON TABLE")
    print(f"{'=' * 70}")
    print(f"{'Metric':<30} {'StudentTHMM':>15} {'HDP-HMM (SVI)':>15} {'Win threshold':>20} {'Winner':>10}")
    print("-" * 92)

    # OOS accuracy row
    student_acc_pct = f"{student_metrics['accuracy']:.1%}"
    hdp_acc_pct = f"{hdp_metrics['accuracy']:.1%}"
    acc_winner = 'HDP' if results['accuracy_delta'] >= 0.02 else 'StudentTHMM'
    print(f"{'OOS accuracy':<30} {student_acc_pct:>15} {hdp_acc_pct:>15} {'HDP needs +2pp':>20} {acc_winner:>10}")

    # Dwell time row
    student_dwell_str = f"{student_metrics['dwell']:.1f}"
    hdp_dwell_str = f"{hdp_metrics['dwell']:.1f}"
    dwell_winner_val = results['dwell_delta']
    dwell_pct = (dwell_winner_val / student_metrics['dwell'] * 100) if student_metrics['dwell'] > 0 else 0
    dwell_winner = 'HDP' if (results['dwell_delta'] > 0 and dwell_pct >= 10) else 'StudentTHMM'
    print(f"{'Mean dwell time (days)':<30} {student_dwell_str:>15} {hdp_dwell_str:>15} {'HDP needs >10% gain':>20} {dwell_winner:>10}")

    # SVI convergence row
    svi_str = 'Yes' if hdp_oos['all_folds_converged'] else f"No ({hdp_oos['n_folds_converged']}/{hdp_oos['n_folds_total']})"
    print(f"{'SVI converged':<30} {'—':>15} {svi_str:>15} {'—':>20} {'—':>10}")

    print(f"\nVerdict: {results['verdict'].upper()}")

    # ===================================================================
    # Write JSON results
    # ===================================================================
    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, 'hdp_comparison_results.json')

    json_results = {
        # Core verdict fields
        'student_accuracy': float(results['student_accuracy']),
        'student_dwell': float(results['student_dwell']),
        'hdp_accuracy': float(results['hdp_accuracy']),
        'hdp_dwell': float(results['hdp_dwell']),
        'accuracy_delta': float(results['accuracy_delta']),
        'dwell_delta': float(results['dwell_delta']),
        'verdict': results['verdict'],
        'all_folds_converged': bool(results['all_folds_converged']),
        'n_folds_converged': int(results['n_folds_converged']),
        'n_folds_total': int(results['n_folds_total']),
        # Additional metadata
        'comparison_date': datetime.now().strftime('%Y-%m-%d'),
        'svi_num_steps': int(SVI_NUM_STEPS),
        'hdp_truncation': int(HDP_TRUNCATION),
        'n_states': int(N_STATES),
        'n_features': int(len(features.columns)),
        'student_n_obs': int(results['student_n_obs']),
        'hdp_n_obs': int(results['hdp_n_obs']),
        'student_n_common': int(student_metrics['n_common']),
        'hdp_n_common': int(hdp_metrics['n_common']),
        'walk_forward_mode': str(WALK_FORWARD_MODE),
    }

    with open(out_path, 'w') as f:
        json.dump(json_results, f, indent=2)

    print(f"\nResults written to: {out_path}")
    print(f"\nDone: {pd.Timestamp.now()}")


if __name__ == '__main__':
    main()
