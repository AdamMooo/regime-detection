"""
Cross-validation test comparing multi-signal combination vs. single-HMM baseline.

This test runs 5-fold cross-validation on historical regime labels,
comparing the IC (information coefficient) of the combined signal against
a baseline single principal component.
"""

import os
import numpy as np
import pandas as pd
import pytest
from scripts.analysis.signal_combination import compare_signals_cv


def test_signal_combination_cv_performance():
    """
    Cross-validate multi-signal combination vs. baseline (single HMM).

    Creates synthetic regime labels and features for testing.
    In production, would load from regime_results.csv.
    """
    # Generate test data
    np.random.seed(42)
    n_samples = 500
    n_features = 13

    # Create features with varying correlation structure
    base_signal = np.random.randn(n_samples)
    features = pd.DataFrame({
        f'feature_{i}': base_signal * (0.5 ** (i % 3)) + np.random.randn(n_samples)
        for i in range(n_features)
    })

    # Create regime labels with some signal
    labels = np.random.randint(0, 3, n_samples)
    # Add some correlation: features predict labels
    signal_component = (features.iloc[:, 0] + features.iloc[:, 1]) / 2
    labels = np.where(signal_component > 0.5, 2, np.where(signal_component < -0.5, 0, 1))

    # Run cross-validation
    cv_results = compare_signals_cv(features, labels, n_splits=5)

    # Log performance
    combined_ic = cv_results['combined_ic_oos_mean']
    baseline_ic = cv_results['baseline_ic_oos_mean']
    improvement = cv_results['improvement_mean']

    print("\n" + "=" * 60)
    print("Signal Combination Cross-Validation Performance Report")
    print("=" * 60)
    print(f"Baseline (Single-HMM / PCA):  IC = {baseline_ic:.4f}")
    print(f"Combined (11-step):           IC = {combined_ic:.4f}")
    print(f"Improvement (absolute):       {improvement:+.4f}")
    if baseline_ic != 0:
        pct_improvement = 100 * improvement / abs(baseline_ic)
        print(f"Improvement (relative):       {pct_improvement:+.1f}%")
    print(f"\nEffective N target:           ~3.6 (sqrt(13) diversification)")
    print("=" * 60)

    # Verify results are valid
    assert np.isfinite(combined_ic), "Combined IC should be finite"
    assert np.isfinite(baseline_ic), "Baseline IC should be finite"
    assert len(cv_results['combined_ic_oos']) == 5, "Should have 5 CV folds"
    assert len(cv_results['baseline_ic_oos']) == 5, "Should have 5 CV folds"

    # Verify cross-validation structure
    assert 'combined_ic_oos_mean' in cv_results
    assert 'baseline_ic_oos_mean' in cv_results
    assert 'improvement_mean' in cv_results


def test_cv_with_real_regime_structure():
    """
    Test with features that have realistic regime structure.

    Creates features that behave differently in different regimes.
    """
    np.random.seed(123)
    n_samples = 500

    # Create regime-dependent features
    base_regimes = np.random.choice([0, 1, 2], size=n_samples, p=[0.33, 0.33, 0.34])

    features_list = []
    for i in range(13):
        # Different mean/std per regime
        feature_data = np.zeros(n_samples)
        for regime in [0, 1, 2]:
            mask = base_regimes == regime
            if regime == 0:
                feature_data[mask] = np.random.normal(-1, 0.5, mask.sum())
            elif regime == 1:
                feature_data[mask] = np.random.normal(0, 1.0, mask.sum())
            else:  # regime 2
                feature_data[mask] = np.random.normal(1.5, 1.5, mask.sum())
        features_list.append(feature_data)

    features = pd.DataFrame(np.column_stack(features_list),
                           columns=[f'feature_{i}' for i in range(13)])

    # Use base_regimes as labels (they have predictive power)
    labels = base_regimes

    # Run cross-validation
    cv_results = compare_signals_cv(features, labels, n_splits=5)

    combined_ic = cv_results['combined_ic_oos_mean']
    baseline_ic = cv_results['baseline_ic_oos_mean']

    print("\n" + "=" * 60)
    print("Regime-Structured Cross-Validation")
    print("=" * 60)
    print(f"Features with regime structure (different mean/std per regime)")
    print(f"Baseline IC: {baseline_ic:.4f}")
    print(f"Combined IC: {combined_ic:.4f}")
    print("=" * 60)

    # With regime structure, both should detect signal
    assert np.isfinite(combined_ic)
    assert np.isfinite(baseline_ic)


def test_cv_n_splits_validation():
    """Test cross-validation with different numbers of splits."""
    np.random.seed(42)
    n_samples = 300
    features = pd.DataFrame(np.random.randn(n_samples, 13),
                           columns=[f'feature_{i}' for i in range(13)])
    labels = np.random.randint(0, 3, n_samples)

    for n_splits in [3, 5, 10]:
        cv_results = compare_signals_cv(features, labels, n_splits=n_splits)

        assert len(cv_results['combined_ic_oos']) == n_splits
        assert len(cv_results['baseline_ic_oos']) == n_splits
        assert len(cv_results['improvement']) == n_splits

        combined_mean = cv_results['combined_ic_oos_mean']
        baseline_mean = cv_results['baseline_ic_oos_mean']

        assert np.isfinite(combined_mean)
        assert np.isfinite(baseline_mean)


if __name__ == '__main__':
    pytest.main([__file__, '-xvs', '-s'])
