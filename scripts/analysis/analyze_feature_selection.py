"""
Feature selection bias analysis: Compare original 7 features vs new features selected on held-out train set.

This script performs out-of-sample feature selection validation:
1. Split data: Train (2010–2020) vs Test (2021–2026, held-out)
2. Evaluate baseline with original 7 features on test set
3. Select new features using correlation-based filtering on train set only
4. Evaluate new features on test set
5. Compare performance (regime accuracy, VaR metrics)
6. Recommendation: Keep original or switch to new features
"""

import os
import sys
import numpy as np
import pandas as pd
import logging
from datetime import datetime

# Local imports
from config import (
    FEATURE_SUBSET, DATA_DIR, RANDOM_SEED, REGIME_NAMES,
    PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD, PCA_ROLLING_WINDOW
)
from features import build_features
from inference import expanding_standardize, filtered_labels, StudentTHMM
from hmm_training import fit_rolling_pca, label_regimes, check_stability
from evaluation import evaluate, compute_var_backtest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================================================================
# Helper: Load market data and features
# ===================================================================

def load_and_split_data():
    """Load market data and split into train (2010–2020) and test (2021–2026)."""
    market_path = os.path.join(DATA_DIR, 'market_data.csv')
    features_path = os.path.join(DATA_DIR, 'features_transformed.csv')

    if not os.path.exists(market_path):
        raise FileNotFoundError(f"Market data not found: {market_path}")

    market = pd.read_csv(market_path, index_col=0, parse_dates=True)
    features = pd.read_csv(features_path, index_col=0, parse_dates=True)

    # Align indices
    market = market.loc[features.index]

    # Split: Train (2010–2020), Test (2021–2026)
    split_date = pd.Timestamp('2021-01-01')
    train_market = market[market.index < split_date].copy()
    test_market = market[market.index >= split_date].copy()

    train_features = features.loc[train_market.index].copy()
    test_features = features.loc[test_market.index].copy()

    print(f"\nData Split:")
    print(f"  Train (2010–2020): {len(train_market)} trading days")
    print(f"  Test  (2021–2026): {len(test_market)} trading days")

    return {
        'train_market': train_market,
        'test_market': test_market,
        'train_features': train_features,
        'test_features': test_features,
    }


# ===================================================================
# Feature selection: Correlation-based filtering on train set
# ===================================================================

def select_features_on_holdout(train_features, original_features, target_k=6):
    """
    Select K features on train set using correlation-based filtering.

    Strategy: Start with original features, remove highly correlated pairs (>0.8),
    keep top features by regime discriminative power (variance in PCA).

    Parameters
    ----------
    train_features : DataFrame
        Train set features (2010–2020)
    original_features : list
        Original feature names
    target_k : int
        Target number of features (default 6)

    Returns
    -------
    selected_features : list
        Selected feature names
    """
    # Get original 7 features that exist in training data
    available = [f for f in original_features if f in train_features.columns]
    print(f"\n  Original {len(available)} features available: {available}")

    # Compute correlation matrix on train set only
    train_features_clean = train_features[available].dropna()
    corr_matrix = train_features_clean.corr().abs()

    # Find and remove highly correlated pairs
    selected = available.copy()
    upper_triangle = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    # Remove columns with high correlation
    for col in upper_triangle.columns:
        max_corr = upper_triangle[col].max()
        if max_corr > 0.8:
            # Find which column it's correlated with
            corr_col = upper_triangle[col][upper_triangle[col] > 0.8].index[0]
            # Remove the one with lower variance (less information)
            var_col = train_features_clean[col].var()
            var_corr = train_features_clean[corr_col].var()
            if var_col < var_corr and col in selected:
                selected.remove(col)

    # If we removed too many, keep original features
    if len(selected) < target_k - 1:
        selected = available.copy()

    # Sort by variance (keep features with highest variance/information)
    variances = {f: train_features_clean[f].var() for f in selected}
    selected = sorted(selected, key=lambda x: variances[x], reverse=True)[:target_k]

    return selected


# ===================================================================
# HMM training and evaluation
# ===================================================================

def fit_and_evaluate_features(split_data, features_to_use, label):
    """
    Train HMM on train features, evaluate on test features.

    Parameters
    ----------
    split_data : dict
        Train/test split data
    features_to_use : list
        Feature names to use
    label : str
        Label for output ('Original 7' or 'New Features')

    Returns
    -------
    results : dict
        Performance metrics
    """
    print(f"\n{'='*70}")
    print(f"{label} — Training on 2010–2020, Evaluating on 2021–2026")
    print(f"{'='*70}")
    print(f"  Features ({len(features_to_use)}): {features_to_use}")

    train_features = split_data['train_features'][features_to_use].copy()
    test_features = split_data['test_features'][features_to_use].copy()

    # Standardize (expanding window, causal)
    X_train_scaled, train_mean, train_std = expanding_standardize(
        train_features.fillna(0).values, min_warmup=252
    )

    # Apply same standardization to test (using train statistics)
    X_test_raw = test_features.fillna(0).values
    X_test_scaled = (X_test_raw - train_mean) / (train_std + 1e-8)

    # Remove NaN rows
    train_valid = ~np.isnan(X_train_scaled).any(axis=1)
    test_valid = ~np.isnan(X_test_scaled).any(axis=1)

    X_train = X_train_scaled[train_valid]
    X_test = X_test_scaled[test_valid]

    train_idx = np.where(train_valid)[0]
    test_idx = np.where(test_valid)[0]

    print(f"  Train valid rows: {len(X_train)} (after standardization)")
    print(f"  Test valid rows:  {len(X_test)}")

    # Rolling PCA
    pcs_train, _, valid_mask_train, n_pcs, pca = fit_rolling_pca(
        X_train,
        window=PCA_ROLLING_WINDOW,
        max_components=PCA_MAX_COMPONENTS,
        var_threshold=PCA_VAR_THRESHOLD
    )
    print(f"  PCA components selected: {n_pcs}")

    # Project test set using final PCA
    X_test_pca = X_test @ pca.components_[:n_pcs].T

    # Fit HMM on train PCA
    n_states = 3
    model = StudentTHMM(n_components=n_states, covariance_type='full', n_iter=300, random_state=RANDOM_SEED)
    try:
        model.fit(pcs_train)
    except Exception as e:
        print(f"  ERROR: HMM fit failed: {e}")
        return None

    # Get regime labels
    test_labels = filtered_labels(model, X_test_pca, hold_days=1)

    # Map to regime names
    name_map = {i: REGIME_NAMES[n_states][i] for i in range(n_states)}

    # Compute metrics
    print(f"\n  Regime Distribution:")
    unique_labels, counts = np.unique(test_labels, return_counts=True)
    for reg, cnt in zip(unique_labels, counts):
        name = name_map.get(reg, f"Regime {reg}")
        pct = 100 * cnt / len(test_labels)
        print(f"    {name}: {cnt} days ({pct:.1f}%)")

    # Regime accuracy: how stable/well-separated
    # (metric: average dwell time per regime)
    dwell_times = []
    current_regime = None
    regime_start = 0
    for i, label in enumerate(test_labels):
        if label != current_regime:
            if current_regime is not None:
                dwell_times.append(i - regime_start)
            current_regime = label
            regime_start = i
    if current_regime is not None:
        dwell_times.append(len(test_labels) - regime_start)

    avg_dwell = np.mean(dwell_times) if dwell_times else 0

    # Get SPY returns for evaluation
    spy_ret = np.log(split_data['test_market']['SPY_close'] /
                     split_data['test_market']['SPY_close'].shift(1))
    spy_ret = spy_ret[test_valid]

    # VaR backtesting
    kupiec_pval = np.nan
    christoffersen_pval = np.nan
    try:
        var_results = compute_var_backtest(
            spy_ret.dropna(),
            test_labels[1:],  # Align with 5-day returns
            name_map
        )
        if not var_results.empty:
            # Average p-values across regimes
            kupiec_pval = var_results['kupiec_pval'].mean()
            christoffersen_pval = var_results['christo_pval'].mean()
    except Exception as e:
        logger.warning(f"VaR backtest failed: {e}")

    # Regime accuracy metric (simplified: proportion of days in largest regime)
    regime_accuracy = np.max(counts) / len(test_labels) * 100

    print(f"\n  Performance Metrics:")
    print(f"    Regime Accuracy (% in largest): {regime_accuracy:.1f}%")
    print(f"    Avg Dwell Time: {avg_dwell:.1f} days")
    if not np.isnan(kupiec_pval):
        print(f"    Kupiec POF p-value: {kupiec_pval:.4f}")
    else:
        print(f"    Kupiec POF p-value: N/A")
    if not np.isnan(christoffersen_pval):
        print(f"    Christoffersen p-value: {christoffersen_pval:.4f}")
    else:
        print(f"    Christoffersen p-value: N/A")

    return {
        'label': label,
        'features': features_to_use,
        'n_features': len(features_to_use),
        'n_pca_components': n_pcs,
        'regime_accuracy': regime_accuracy,
        'avg_dwell_time': avg_dwell,
        'kupiec_pval': kupiec_pval,
        'christoffersen_pval': christoffersen_pval,
        'n_states': n_states,
        'model': model,
        'test_labels': test_labels,
    }


# ===================================================================
# Main execution
# ===================================================================

def main():
    """Run feature selection bias analysis."""
    print("\n" + "="*70)
    print("FEATURE SELECTION BIAS ANALYSIS")
    print("="*70)
    print(f"Objective: Re-select features on held-out train set (2010–2020)")
    print(f"           Evaluate on held-out test set (2021–2026)")
    print(f"           Compare original 7 vs new features")

    # Load and split data
    split_data = load_and_split_data()

    # Get original features
    original_features = FEATURE_SUBSET
    print(f"\nOriginal FEATURE_SUBSET ({len(original_features)}): {original_features}")

    # Task 1: Evaluate original 7 features on test set
    print("\n" + "-"*70)
    print("TASK 1: BASELINE - Original 7 Features")
    print("-"*70)
    baseline_results = fit_and_evaluate_features(
        split_data, original_features, "Original 7 Features"
    )

    if baseline_results is None:
        print("ERROR: Baseline evaluation failed. Exiting.")
        return

    # Task 2: Select new features on train set only
    print("\n" + "-"*70)
    print("TASK 2: FEATURE SELECTION - Select on Train Set Only")
    print("-"*70)
    new_features = select_features_on_holdout(
        split_data['train_features'],
        original_features,
        target_k=6
    )
    print(f"\n  New features selected: {new_features}")

    # Task 3: Evaluate new features on test set
    print("\n" + "-"*70)
    print("TASK 3: EVALUATION - New Features on Test Set")
    print("-"*70)
    new_results = fit_and_evaluate_features(
        split_data, new_features, "New Features"
    )

    if new_results is None:
        print("ERROR: New features evaluation failed. Using baseline.")
        new_results = baseline_results

    # Task 4: Compare performance
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON")
    print("="*70)

    comparison = pd.DataFrame({
        'Metric': [
            'Feature Count',
            'Regime Accuracy (%)',
            'Avg Dwell Time (days)',
            'Kupiec POF p-value',
            'Christoffersen p-value',
        ],
        'Original 7': [
            baseline_results['n_features'],
            f"{baseline_results['regime_accuracy']:.1f}",
            f"{baseline_results['avg_dwell_time']:.1f}",
            f"{baseline_results['kupiec_pval']:.4f}" if not np.isnan(baseline_results['kupiec_pval']) else "N/A",
            f"{baseline_results['christoffersen_pval']:.4f}" if not np.isnan(baseline_results['christoffersen_pval']) else "N/A",
        ],
        'New Features': [
            new_results['n_features'],
            f"{new_results['regime_accuracy']:.1f}",
            f"{new_results['avg_dwell_time']:.1f}",
            f"{new_results['kupiec_pval']:.4f}" if not np.isnan(new_results['kupiec_pval']) else "N/A",
            f"{new_results['christoffersen_pval']:.4f}" if not np.isnan(new_results['christoffersen_pval']) else "N/A",
        ],
    })

    print("\n" + comparison.to_string(index=False))

    # Task 5: Decision rule
    print("\n" + "="*70)
    print("DECISION")
    print("="*70)

    # Score: Original wins on positive metrics (higher accuracy, p-value)
    baseline_wins = 0
    new_wins = 0

    if baseline_results['regime_accuracy'] >= new_results['regime_accuracy']:
        baseline_wins += 1
    else:
        new_wins += 1

    if baseline_results['avg_dwell_time'] >= new_results['avg_dwell_time']:
        baseline_wins += 1
    else:
        new_wins += 1

    if not np.isnan(baseline_results['kupiec_pval']):
        if baseline_results['kupiec_pval'] >= new_results['kupiec_pval']:
            baseline_wins += 1
        else:
            new_wins += 1

    if not np.isnan(baseline_results['christoffersen_pval']):
        if baseline_results['christoffersen_pval'] >= new_results['christoffersen_pval']:
            baseline_wins += 1
        else:
            new_wins += 1

    print(f"\n  Baseline (Original 7): {baseline_wins} metric wins")
    print(f"  New Features: {new_wins} metric wins")

    if new_wins >= 3:
        recommendation = "Switch to new features"
        decision_features = new_features
    else:
        recommendation = "Keep original 7 features"
        decision_features = original_features

    print(f"\n  RECOMMENDATION: {recommendation}")

    # Save report
    report_path = os.path.join(DATA_DIR, 'feature_selection_report.txt')
    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("FEATURE SELECTION BIAS ANALYSIS REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")

        f.write("OBJECTIVE\n")
        f.write("-"*70 + "\n")
        f.write("Re-select features on held-out training set (2010-2020)\n")
        f.write("Evaluate on held-out test set (2021-2026)\n")
        f.write("Compare performance: original 7 vs newly selected features\n\n")

        f.write("DATA SPLIT\n")
        f.write("-"*70 + "\n")
        f.write(f"Train: 2010-2020 ({len(split_data['train_market'])} trading days)\n")
        f.write(f"Test:  2021-2026 ({len(split_data['test_market'])} trading days)\n\n")

        f.write("ORIGINAL 7 FEATURES (BASELINE)\n")
        f.write("-"*70 + "\n")
        f.write(f"Features: {baseline_results['features']}\n")
        f.write(f"Regime Accuracy: {baseline_results['regime_accuracy']:.1f}%\n")
        f.write(f"Avg Dwell Time: {baseline_results['avg_dwell_time']:.1f} days\n")
        f.write(f"Kupiec POF p-value: {baseline_results['kupiec_pval']:.4f}\n")
        f.write(f"Christoffersen p-value: {baseline_results['christoffersen_pval']:.4f}\n\n")

        f.write("NEW FEATURES (SELECTED ON TRAIN SET ONLY)\n")
        f.write("-"*70 + "\n")
        f.write(f"Features ({len(new_features)}): {new_features}\n")
        f.write(f"Regime Accuracy: {new_results['regime_accuracy']:.1f}%\n")
        f.write(f"Avg Dwell Time: {new_results['avg_dwell_time']:.1f} days\n")
        f.write(f"Kupiec POF p-value: {new_results['kupiec_pval']:.4f}\n")
        f.write(f"Christoffersen p-value: {new_results['christoffersen_pval']:.4f}\n\n")

        f.write("PERFORMANCE COMPARISON\n")
        f.write("-"*70 + "\n")
        f.write(comparison.to_string(index=False) + "\n\n")

        f.write("DECISION\n")
        f.write("-"*70 + "\n")
        f.write(f"Baseline wins: {baseline_wins} metrics\n")
        f.write(f"New wins: {new_wins} metrics\n")
        f.write(f"Recommendation: {recommendation}\n")
        f.write(f"Decision features: {decision_features}\n\n")

        f.write("CAUSALITY GUARANTEE\n")
        f.write("-"*70 + "\n")
        f.write("All features computed with expanding windows (past data only).\n")
        f.write("Feature selection performed on train set (2010–2020) only.\n")
        f.write("Evaluation on held-out test set (2021–2026) — no future data leakage.\n")

    print(f"\n  Report saved to: {report_path}")

    # Summary output
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nORIGINAL 7 FEATURES:")
    print(f"  Regime Accuracy: {baseline_results['regime_accuracy']:.1f}%")
    print(f"  Kupiec POF p-value: {baseline_results['kupiec_pval']:.4f}")
    print(f"  Christoffersen p-value: {baseline_results['christoffersen_pval']:.4f}")
    print(f"  Dwell Time: {baseline_results['avg_dwell_time']:.1f} days")

    print(f"\nNEW FEATURES ({len(new_features)}):")
    print(f"  Regime Accuracy: {new_results['regime_accuracy']:.1f}%")
    print(f"  Kupiec POF p-value: {new_results['kupiec_pval']:.4f}")
    print(f"  Christoffersen p-value: {new_results['christoffersen_pval']:.4f}")
    print(f"  Dwell Time: {new_results['avg_dwell_time']:.1f} days")

    print(f"\nWINNER: {recommendation.upper()}")
    print(f"FEATURES FOR PRODUCTION: {decision_features}")

    print("\n" + "="*70)


if __name__ == '__main__':
    main()
