"""
Diagnostic script to identify root cause of OOS regime fragmentation.

Problem: In-sample HMM finds 4 regimes, but OOS walk-forward produces 10+ regimes.
Hypothesis: Rolling PCA drift or non-stationary features cause fragmentation.

Solution: Compare three PCA strategies:
  A. FIXED PCA: Fit on train set (2010-2020), apply to OOS (2021-2026) with no refitting
  B. ROLLING PCA: Current approach, refit on expanding/rolling windows
  C. EXTENDED WINDOW: Rolling PCA with larger window (504 days vs 252)

Output:
  - Regime count for each experiment (A, B, C)
  - PCA drift magnitude (Procrustes angle between components)
  - Regime stability metrics (transitions, dwell time, label consistency)
  - Recommendation: Use fixed PCA, extend rolling window, or cluster regimes
  - Findings saved to fragmentation_report.txt
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from scipy.linalg import orthogonal_procrustes
from sklearn.decomposition import PCA

from src.features.collect import collect
from src.features.features import build_features
from src.config import (
    RANDOM_SEED, N_STATES, COV_TYPE, PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD,
    REGIME_NAMES, DATA_DIR, FEATURE_SUBSET, WALK_FORWARD_TRAIN_YEARS,
)
from src.core.inference import expanding_standardize, _fit_hmm, filtered_labels

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def compute_pca_drift(pca_a, pca_b):
    """
    Compute drift between two PCA models via component angle.

    Parameters
    ----------
    pca_a : PCA
        First PCA model (e.g., from window A)
    pca_b : PCA
        Second PCA model (e.g., from window B)

    Returns
    -------
    angle_deg : float
        Mean angle (degrees) between corresponding principal components.
        Small angle (<15°) = stable components, large angle (>30°) = drift.
    """
    # Get components (shape: n_components x n_features)
    comp_a = pca_a.components_  # (n_components, n_features)
    comp_b = pca_b.components_

    # Compute angles between corresponding components
    n_comp = min(comp_a.shape[0], comp_b.shape[0])
    angles = []

    for i in range(n_comp):
        # Normalize components
        a = comp_a[i] / (np.linalg.norm(comp_a[i]) + 1e-10)
        b = comp_b[i] / (np.linalg.norm(comp_b[i]) + 1e-10)

        # Cosine similarity
        cos_sim = np.dot(a, b)
        cos_sim = np.clip(cos_sim, -1, 1)
        angle_rad = np.arccos(np.abs(cos_sim))  # Use absolute value to handle sign flips
        angles.append(np.degrees(angle_rad))

    return np.mean(angles)


def count_regime_transitions(labels):
    """Count number of regime transitions (changes) in label sequence."""
    return np.sum(np.diff(labels) != 0)


def compute_regime_dwell_time(labels):
    """Compute mean dwell time (consecutive days in same regime)."""
    transitions = count_regime_transitions(labels)
    # Total regimes visited = transitions + 1
    n_regimes_visited = transitions + 1
    mean_dwell = len(labels) / n_regimes_visited if n_regimes_visited > 0 else len(labels)
    return mean_dwell


def regime_label_entropy(labels):
    """Compute Shannon entropy of regime distribution."""
    unique, counts = np.unique(labels, return_counts=True)
    probs = counts / counts.sum()
    entropy = -np.sum(probs * np.log2(probs + 1e-10))
    return entropy


def experiment_fixed_pca(market, features_df, train_end_date):
    """
    Experiment A: Fixed PCA fitted on train set, applied to OOS.

    Parameters
    ----------
    market : DataFrame
        Market data with dates
    features_df : DataFrame
        Feature matrix with dates
    train_end_date : str or int
        Training end date or number of rows for training window

    Returns
    -------
    dict with keys: n_regimes, regime_counts, labels, pca, dwell_time, transitions
    """
    logger.info("\n" + "="*70)
    logger.info("EXPERIMENT A: FIXED PCA (fitted on train, applied to OOS)")
    logger.info("="*70)

    # Split train/test at train_end_date
    if isinstance(train_end_date, int):
        train_mask = np.arange(len(features_df)) < train_end_date
    else:
        train_mask = features_df.index <= train_end_date

    train_feats = features_df[train_mask]
    test_feats = features_df[~train_mask]

    logger.info(f"Train set: {len(train_feats)} rows ({train_feats.index[0]} to {train_feats.index[-1]})")
    logger.info(f"Test set:  {len(test_feats)} rows ({test_feats.index[0]} to {test_feats.index[-1]})")

    # Standardize on combined data (expanding window for causality)
    X_combined = np.vstack([train_feats.values, test_feats.values])
    X_scaled, _, _ = expanding_standardize(X_combined, min_warmup=252)
    X_train = X_scaled[:len(train_feats)]
    X_test = X_scaled[len(train_feats):]

    # Drop NaN rows from train
    valid_train = ~np.isnan(X_train[:, 0])
    X_train = X_train[valid_train]
    train_feats_valid = train_feats[valid_train]

    # Fit PCA on train set only (FROZEN)
    n_comp = min(PCA_MAX_COMPONENTS, X_train.shape[1])
    pca_fixed = PCA(n_components=n_comp, random_state=RANDOM_SEED)
    pca_fixed.fit(X_train)

    logger.info(f"Fitted PCA on {len(X_train)} training samples")
    logger.info(f"Explained variance: {pca_fixed.explained_variance_ratio_[:3]}")

    # Transform train and test using FIXED PCA
    pc_train = pca_fixed.transform(X_train)
    pc_test = pca_fixed.transform(X_test)

    # Train HMM on PCA-reduced train data
    hmm_model = _fit_hmm(pc_train, N_STATES, COV_TYPE, seed=RANDOM_SEED)
    logger.info(f"Trained HMM with {N_STATES} states on {len(pc_train)} train samples")

    # Predict regimes on test data
    test_labels = filtered_labels(hmm_model, pc_test)

    # Count unique regimes in OOS data
    unique_regimes = len(np.unique(test_labels[~np.isnan(test_labels)]))
    regime_counts = np.bincount(test_labels[~np.isnan(test_labels)].astype(int))
    transitions = count_regime_transitions(test_labels[~np.isnan(test_labels)])
    dwell_time = compute_regime_dwell_time(test_labels[~np.isnan(test_labels)])

    logger.info(f"\nResults:")
    logger.info(f"  OOS unique regimes: {unique_regimes}")
    logger.info(f"  Regime distribution: {regime_counts}")
    logger.info(f"  Regime transitions: {transitions}")
    logger.info(f"  Mean dwell time: {dwell_time:.1f} days")
    logger.info(f"  Label entropy: {regime_label_entropy(test_labels[~np.isnan(test_labels)]):.3f}")

    return {
        "name": "FIXED_PCA",
        "n_regimes": unique_regimes,
        "regime_counts": regime_counts,
        "labels": test_labels,
        "pca": pca_fixed,
        "dwell_time": dwell_time,
        "transitions": transitions,
        "hmm_model": hmm_model,
        "test_dates": test_feats.index,
    }


def experiment_rolling_pca(market, features_df, train_end_date, window_days=252):
    """
    Experiment B: Rolling PCA (current approach).

    Parameters
    ----------
    market : DataFrame
        Market data with dates
    features_df : DataFrame
        Feature matrix with dates
    train_end_date : int or str
        Training end date
    window_days : int
        Rolling window size (default 252 = 1 year)

    Returns
    -------
    dict with keys: n_regimes, regime_counts, labels, pca, dwell_time, transitions
    """
    logger.info("\n" + "="*70)
    logger.info(f"EXPERIMENT B: ROLLING PCA (window={window_days} days)")
    logger.info("="*70)

    # Split train/test
    if isinstance(train_end_date, int):
        train_mask = np.arange(len(features_df)) < train_end_date
    else:
        train_mask = features_df.index <= train_end_date

    train_feats = features_df[train_mask]
    test_feats = features_df[~train_mask]

    logger.info(f"Train set: {len(train_feats)} rows")
    logger.info(f"Test set:  {len(test_feats)} rows")

    # Combine and standardize
    X_combined = np.vstack([train_feats.values, test_feats.values])
    X_scaled, _, _ = expanding_standardize(X_combined, min_warmup=252)
    X_train = X_scaled[:len(train_feats)]
    X_test = X_scaled[len(train_feats):]

    # Drop NaN from train
    valid_train = ~np.isnan(X_train[:, 0])
    X_train = X_train[valid_train]

    # Fit rolling PCA on train (last window only, like orchestrator.py)
    pca_window = min(window_days, len(X_train))
    n_comp = min(PCA_MAX_COMPONENTS, X_train.shape[1])
    pca_rolling = PCA(n_components=n_comp, random_state=RANDOM_SEED)
    pca_rolling.fit(X_train[-pca_window:])

    logger.info(f"Fitted rolling PCA on last {pca_window} training samples")
    logger.info(f"Explained variance: {pca_rolling.explained_variance_ratio_[:3]}")

    # Transform train and test
    pc_train = pca_rolling.transform(X_train)
    pc_test = pca_rolling.transform(X_test)

    # Train HMM
    hmm_model = _fit_hmm(pc_train, N_STATES, COV_TYPE, seed=RANDOM_SEED)
    logger.info(f"Trained HMM with {N_STATES} states on {len(pc_train)} train samples")

    # Predict regimes
    test_labels = filtered_labels(hmm_model, pc_test)

    # Count unique regimes
    unique_regimes = len(np.unique(test_labels[~np.isnan(test_labels)]))
    regime_counts = np.bincount(test_labels[~np.isnan(test_labels)].astype(int))
    transitions = count_regime_transitions(test_labels[~np.isnan(test_labels)])
    dwell_time = compute_regime_dwell_time(test_labels[~np.isnan(test_labels)])

    logger.info(f"\nResults:")
    logger.info(f"  OOS unique regimes: {unique_regimes}")
    logger.info(f"  Regime distribution: {regime_counts}")
    logger.info(f"  Regime transitions: {transitions}")
    logger.info(f"  Mean dwell time: {dwell_time:.1f} days")
    logger.info(f"  Label entropy: {regime_label_entropy(test_labels[~np.isnan(test_labels)]):.3f}")

    return {
        "name": f"ROLLING_PCA_{window_days}d",
        "n_regimes": unique_regimes,
        "regime_counts": regime_counts,
        "labels": test_labels,
        "pca": pca_rolling,
        "dwell_time": dwell_time,
        "transitions": transitions,
        "hmm_model": hmm_model,
        "test_dates": test_feats.index,
    }


def detect_pca_drift_across_windows(features_df, train_end_date, window_size=252, n_windows=5):
    """
    Measure PCA component drift across multiple rolling windows.

    Fit PCA at multiple time points and measure Procrustes angle between
    corresponding components. Large drift (>30°) suggests rolling PCA instability.
    """
    logger.info("\n" + "="*70)
    logger.info("PCA DRIFT ANALYSIS: Detect component misalignment over time")
    logger.info("="*70)

    if isinstance(train_end_date, int):
        train_mask = np.arange(len(features_df)) < train_end_date
    else:
        train_mask = features_df.index <= train_end_date

    train_feats = features_df[train_mask]
    test_feats = features_df[~train_mask]

    # Combine and standardize
    X_combined = np.vstack([train_feats.values, test_feats.values])
    X_scaled, _, _ = expanding_standardize(X_combined, min_warmup=252)
    X_train = X_scaled[:len(train_feats)]
    X_test = X_scaled[len(train_feats):]

    # Drop NaN from train
    valid_train = ~np.isnan(X_train[:, 0])
    X_train = X_train[valid_train]

    # Fit PCA at multiple windows
    pcas = []
    dates = []

    # Window 1: end of training
    pca_train = PCA(n_components=PCA_MAX_COMPONENTS, random_state=RANDOM_SEED)
    pca_train.fit(X_train[-window_size:])
    pcas.append(pca_train)
    dates.append(f"Train end (idx={len(train_feats)-1})")

    # Windows 2-5: equally spaced through test set
    n_test = len(X_test)
    for i in range(1, n_windows):
        idx = int(i * n_test / n_windows)
        if idx < len(X_test) - window_size:
            X_window = np.vstack([X_train, X_test[:idx+1]])
            X_window = X_window[-(window_size):]
            pca = PCA(n_components=PCA_MAX_COMPONENTS, random_state=RANDOM_SEED)
            pca.fit(X_window)
            pcas.append(pca)
            dates.append(f"Test idx={idx}")

    # Compute drifts between consecutive windows
    logger.info(f"\nPCA component drift (consecutive windows):")
    drifts = []
    for i in range(len(pcas) - 1):
        angle = compute_pca_drift(pcas[i], pcas[i+1])
        drifts.append(angle)
        logger.info(f"  {dates[i]} → {dates[i+1]}: {angle:.2f}°")

    mean_drift = np.mean(drifts)
    max_drift = np.max(drifts)
    logger.info(f"\nDrift statistics:")
    logger.info(f"  Mean drift: {mean_drift:.2f}°")
    logger.info(f"  Max drift:  {max_drift:.2f}°")
    logger.info(f"  Interpretation: {'LARGE drift (>30°) → Rolling PCA unstable' if max_drift > 30 else 'Small drift (<30°) → Rolling PCA stable'}")

    return {
        "mean_drift": mean_drift,
        "max_drift": max_drift,
        "drifts": drifts,
        "interpretation": "rolling_pca_drift" if max_drift > 30 else "rolling_pca_stable",
    }


def analyze_feature_stationarity(features_df, train_end_date, window_size=252):
    """
    Analyze feature stationarity by comparing statistics in train vs test sets.

    Large differences in mean/std suggest non-stationary features.
    """
    logger.info("\n" + "="*70)
    logger.info("FEATURE STATIONARITY ANALYSIS")
    logger.info("="*70)

    if isinstance(train_end_date, int):
        train_mask = np.arange(len(features_df)) < train_end_date
    else:
        train_mask = features_df.index <= train_end_date

    train_feats = features_df[train_mask]
    test_feats = features_df[~train_mask]

    logger.info(f"\nFeature mean shift (train vs test):")
    logger.info(f"  {'Feature':<20s} {'Train':>10s} {'Test':>10s} {'Shift %':>10s}")
    logger.info(f"  {'-'*52}")

    max_shift = 0
    for col in train_feats.columns[:5]:  # Show top 5 features
        train_mean = train_feats[col].mean()
        test_mean = test_feats[col].mean()
        shift_pct = 100 * (test_mean - train_mean) / (abs(train_mean) + 1e-10)
        logger.info(f"  {col:<20s} {train_mean:>10.3f} {test_mean:>10.3f} {shift_pct:>9.1f}%")
        max_shift = max(max_shift, abs(shift_pct))

    logger.info(f"\nStationarity verdict: {'Non-stationary features detected' if max_shift > 20 else 'Features relatively stable'}")

    return {
        "max_shift_pct": max_shift,
        "interpretation": "non_stationary" if max_shift > 20 else "stationary",
    }


def main():
    """Run all three experiments and generate diagnostics."""
    logger.info("\n" + "#"*70)
    logger.info("# OOS REGIME FRAGMENTATION DIAGNOSTIC")
    logger.info("# Purpose: Identify root cause of 4→10 regime explosion")
    logger.info("#"*70)

    # Load data
    logger.info("\nLoading market data and features...")
    mode_used, delta_rows, tickers_refreshed, market = collect()
    features_df = build_features(market)

    # Define train/test split: 2010-2020 train, 2021-2026 test
    train_end_idx = int(WALK_FORWARD_TRAIN_YEARS * 252)  # ~5 years
    logger.info(f"Train/test split: first {train_end_idx} rows = train, remaining = test")

    # Run three experiments
    results_a = experiment_fixed_pca(market, features_df, train_end_idx)
    results_b = experiment_rolling_pca(market, features_df, train_end_idx, window_days=252)
    results_c = experiment_rolling_pca(market, features_df, train_end_idx, window_days=504)

    # Analyze PCA drift and feature stationarity
    drift_analysis = detect_pca_drift_across_windows(features_df, train_end_idx)
    stationarity = analyze_feature_stationarity(features_df, train_end_idx)

    # Comparison table
    logger.info("\n" + "="*70)
    logger.info("COMPARISON TABLE")
    logger.info("="*70)
    logger.info(f"\n{'Experiment':<25s} {'OOS Regimes':>15s} {'Dwell Time':>15s} {'Transitions':>15s}")
    logger.info(f"{'-'*70}")
    logger.info(f"{'A: FIXED_PCA':<25s} {results_a['n_regimes']:>15d} {results_a['dwell_time']:>15.1f} {results_a['transitions']:>15d}")
    logger.info(f"{'B: ROLLING_PCA_252d':<25s} {results_b['n_regimes']:>15d} {results_b['dwell_time']:>15.1f} {results_b['transitions']:>15d}")
    logger.info(f"{'C: ROLLING_PCA_504d':<25s} {results_c['n_regimes']:>15d} {results_c['dwell_time']:>15.1f} {results_c['transitions']:>15d}")

    # Decision logic
    logger.info("\n" + "="*70)
    logger.info("ROOT CAUSE ANALYSIS & RECOMMENDATION")
    logger.info("="*70)

    improvement_a = results_b['n_regimes'] - results_a['n_regimes']
    improvement_c = results_b['n_regimes'] - results_c['n_regimes']

    logger.info(f"\nKey findings:")
    logger.info(f"  1. Fixed PCA reduces fragmentation by {improvement_a} regimes ({improvement_a/results_b['n_regimes']*100:.1f}%)")
    logger.info(f"  2. Extended window (504d) reduces fragmentation by {improvement_c} regimes ({improvement_c/results_b['n_regimes']*100:.1f}%)")
    logger.info(f"  3. PCA drift analysis: max {drift_analysis['max_drift']:.2f}° ({drift_analysis['interpretation']})")
    logger.info(f"  4. Feature stationarity: {stationarity['interpretation']} (max shift {stationarity['max_shift_pct']:.1f}%)")

    # Decision rule
    recommendation = None
    if improvement_a > results_b['n_regimes'] * 0.5:  # If fixed PCA reduces by >50%
        recommendation = "USE_FIXED_PCA"
        logger.info(f"\n✓ RECOMMENDATION: Use fixed PCA for production")
        logger.info(f"  Reason: Fixed PCA reduces OOS regimes from {results_b['n_regimes']} to {results_a['n_regimes']} (>50% reduction)")
        logger.info(f"  Action: Modify hmm_training.py to support fixed PCA mode")
    elif improvement_c > results_b['n_regimes'] * 0.5:  # If extended window reduces by >50%
        recommendation = "EXTEND_WINDOW"
        logger.info(f"\n✓ RECOMMENDATION: Extend rolling window to 504 days")
        logger.info(f"  Reason: Extended window reduces OOS regimes from {results_b['n_regimes']} to {results_c['n_regimes']} (>50% reduction)")
        logger.info(f"  Action: Update PCA_ROLLING_WINDOW in config.py from 252 to 504")
    else:
        recommendation = "CLUSTER_FRAGMENTED"
        logger.info(f"\n✓ RECOMMENDATION: Cluster fragmented regimes (fallback)")
        logger.info(f"  Reason: Neither fixed nor extended window reduces fragmentation significantly")
        logger.info(f"  Action: Implement regime clustering in hmm_training.py")

    # Write report to file
    report_path = Path("fragmentation_report.txt")
    with open(report_path, "w") as f:
        f.write("OOS REGIME FRAGMENTATION DIAGNOSTIC REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"Date: {datetime.now().isoformat()}\n\n")

        f.write("EXPERIMENT RESULTS\n")
        f.write("-"*70 + "\n")
        f.write(f"FIXED_PCA experiment: K = {results_a['n_regimes']} regimes (vs in-sample K={N_STATES})\n")
        f.write(f"ROLLING_PCA_252d experiment: K = {results_b['n_regimes']} regimes (OOS fragmentation)\n")
        f.write(f"ROLLING_PCA_504d experiment: K = {results_c['n_regimes']} regimes (extended window)\n\n")

        f.write("ROOT CAUSE ANALYSIS\n")
        f.write("-"*70 + "\n")
        f.write(f"PCA drift detected: {drift_analysis['interpretation']}\n")
        f.write(f"  - Max drift angle: {drift_analysis['max_drift']:.2f}°\n")
        f.write(f"  - Mean drift angle: {drift_analysis['mean_drift']:.2f}°\n\n")
        f.write(f"Non-stationary features: {stationarity['interpretation']}\n")
        f.write(f"  - Max feature shift: {stationarity['max_shift_pct']:.1f}%\n\n")

        f.write("RECOMMENDATION\n")
        f.write("-"*70 + "\n")
        f.write(f"{recommendation}\n")
        if recommendation == "USE_FIXED_PCA":
            f.write(f"  Fixed PCA reduces OOS fragmentation from {results_b['n_regimes']} to {results_a['n_regimes']} regimes.\n")
            f.write(f"  Action: Implement fixed PCA mode in hmm_training.py + config.py\n")
        elif recommendation == "EXTEND_WINDOW":
            f.write(f"  Extended rolling window (504 days) reduces OOS fragmentation from {results_b['n_regimes']} to {results_c['n_regimes']} regimes.\n")
            f.write(f"  Action: Update PCA_ROLLING_WINDOW in config.py from 252 to 504\n")
        else:
            f.write(f"  Neither fixed nor extended window resolves fragmentation.\n")
            f.write(f"  Action: Implement regime clustering as fallback\n")

    logger.info(f"\n✓ Report saved to {report_path}")
    logger.info("\n" + "#"*70 + "\n")


if __name__ == "__main__":
    main()
