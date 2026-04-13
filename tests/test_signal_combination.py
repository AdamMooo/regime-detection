"""Unit tests for 11-step signal combination engine."""

import numpy as np
import pandas as pd
import pytest
from signal_combination import SignalCombination, compare_signals_cv


class TestSignalPreparation:
    """Tests for Steps 1–5 (signal preparation)."""

    def setup_method(self):
        """Create dummy features and labels."""
        np.random.seed(42)
        self.features = pd.DataFrame(
            np.random.randn(500, 13),
            columns=[f'feature_{i}' for i in range(13)]
        )
        self.labels = np.random.randint(0, 3, 500)

    def test_standardize_expanding_window(self):
        """Test expanding-window standardization."""
        combo = SignalCombination(self.features, self.labels)
        X_std = combo._standardize(self.features, min_warmup=50)

        # First 50 rows should be NaN
        assert X_std.iloc[:50].isna().all().all()
        # After warmup, should be finite
        assert not X_std.iloc[100:].isna().any().any()

    def test_rank_percentile(self):
        """Test percentile ranking."""
        combo = SignalCombination(self.features, self.labels)
        X_rank = combo._rank(self.features)

        # Ranked values should be between 0 and 1
        assert (X_rank >= 0).all().all() and (X_rank <= 1).all().all()

    def test_winsorize_clipping(self):
        """Test winsorization at 3-sigma."""
        combo = SignalCombination(self.features, self.labels)
        X_winsor = combo._winsorize(self.features, n_sigma=3.0)

        # No value should exceed 3-sigma
        assert (X_winsor >= -3.0).all().all() and (X_winsor <= 3.0).all().all()

    def test_cross_sectional_demean(self):
        """Test cross-sectional demeaning."""
        combo = SignalCombination(self.features, self.labels)
        X_demean = combo._cross_sectional_demean(self.features)

        # Each row mean should be close to 0
        row_means = X_demean.mean(axis=1)
        assert np.allclose(row_means, 0, atol=1e-10)

    def test_prepare_signals_full_pipeline(self):
        """Test full signal preparation (Steps 1-5)."""
        combo = SignalCombination(self.features, self.labels)
        X_prep = combo.prepare_signals()

        # Output should be DataFrame with same shape
        assert isinstance(X_prep, pd.DataFrame)
        assert X_prep.shape == self.features.shape


class TestICCalculation:
    """Tests for Steps 6–8 (IC calculation)."""

    def setup_method(self):
        """Create dummy features with known IC."""
        np.random.seed(42)
        self.n = 500

        # Create signal correlated with labels
        self.labels = np.random.randint(0, 3, self.n)
        self.signal_strong = 0.5 * self.labels + 0.3 * np.random.randn(self.n)
        self.signal_weak = 0.1 * self.labels + 0.9 * np.random.randn(self.n)

        self.features = pd.DataFrame({
            'feature_0': self.signal_strong,
            'feature_1': self.signal_weak,
            **{f'feature_{i}': np.random.randn(self.n) for i in range(2, 13)}
        })

    def test_ic_calculation_strong_signal(self):
        """Strong signal should have higher IC."""
        combo = SignalCombination(self.features, self.labels)
        ic_strong = combo._calculate_ic(self.signal_strong, np.roll(self.labels, -1))
        ic_weak = combo._calculate_ic(self.signal_weak, np.roll(self.labels, -1))

        assert ic_strong > ic_weak  # Strong signal IC > weak signal IC

    def test_ic_calculation_no_signal(self):
        """Uncorrelated signal should have IC near 0."""
        combo = SignalCombination(self.features, self.labels)
        noise = np.random.randn(self.n)
        ic_noise = combo._calculate_ic(noise, np.roll(self.labels, -1))

        assert abs(ic_noise) < 0.3  # Weak correlation expected

    def test_raw_ics_all_signals(self):
        """Calculate raw IC for all 13 features."""
        combo = SignalCombination(self.features, self.labels)
        ics = combo.calculate_raw_ics(self.features)

        assert len(ics) == 13
        assert all(isinstance(v, (int, float)) for v in ics.values())

    def test_bias_adjust_ics(self):
        """Bias adjustment should reduce high IC values."""
        combo = SignalCombination(self.features, self.labels)
        raw_ics = {'feature_0': 0.2, 'feature_1': 0.1}
        adjusted_ics = combo.bias_adjust_ics(raw_ics)

        # Adjusted IC should be less than raw IC
        assert adjusted_ics['feature_0'] < raw_ics['feature_0']
        assert adjusted_ics['feature_1'] < raw_ics['feature_1']

    def test_tstat_significance(self):
        """T-stat calculation should handle edge cases."""
        combo = SignalCombination(self.features, self.labels)
        ics = {'feature_0': 0.1, 'feature_1': 0.05}
        tstats = combo.tstat_significance(ics, 500)

        assert len(tstats) == 2
        for signal, (tstat, ic) in tstats.items():
            assert isinstance(tstat, (int, float, np.number))


class TestIndependenceAnalysis:
    """Tests for Steps 9–10 (orthogonal regression, Effective N)."""

    def setup_method(self):
        """Create dummy features."""
        np.random.seed(42)
        self.features = pd.DataFrame(
            np.random.randn(500, 13),
            columns=[f'feature_{i}' for i in range(13)]
        )
        self.labels = np.random.randint(0, 3, 500)

    def test_orthogonal_regression_residuals(self):
        """Test that residuals are calculated for all features."""
        combo = SignalCombination(self.features, self.labels)
        residuals = combo.orthogonal_regression(self.features)

        assert len(residuals) == 13
        # All residuals should be finite arrays
        assert all(isinstance(r, np.ndarray) for r in residuals.values())

    def test_independent_ics_calculation(self):
        """Test independent IC calculation."""
        combo = SignalCombination(self.features, self.labels)
        residuals = combo.orthogonal_regression(self.features)
        indep_ics = combo.independent_ics(residuals)

        assert len(indep_ics) == 13
        assert all(isinstance(v, (int, float)) for v in indep_ics.values())

    def test_effective_n_calculation(self):
        """Test Effective N is between 1 and N."""
        combo = SignalCombination(self.features, self.labels)
        eff_n, diversif_benefit = combo.effective_n(self.features)

        assert 1 <= eff_n <= 13
        assert 0 < diversif_benefit <= np.sqrt(13)

    def test_effective_n_target(self):
        """Effective N should be between 1 and N."""
        # Create moderately correlated features
        np.random.seed(42)
        n_samples = 500
        base = np.random.randn(n_samples)
        features = pd.DataFrame({
            f'feature_{i}': base * (0.3 ** i) + np.random.randn(n_samples) * (1 - 0.3**i)
            for i in range(13)
        })
        labels = np.random.randint(0, 3, n_samples)

        combo = SignalCombination(features, labels)
        eff_n, _ = combo.effective_n(features)

        # Effective N should be reasonable (between 1 and number of features)
        assert 1.0 <= eff_n <= 13.0, f"Expected Effective N between 1-13, got {eff_n}"


class TestOptimalWeighting:
    """Tests for Step 11 (optimal weighting)."""

    def setup_method(self):
        """Create dummy features."""
        np.random.seed(42)
        self.features = pd.DataFrame(
            np.random.randn(500, 13),
            columns=[f'feature_{i}' for i in range(13)]
        )
        self.labels = np.random.randint(0, 3, 500)

    def test_weights_sum_to_one(self):
        """Weights should sum to 1."""
        combo = SignalCombination(self.features, self.labels)
        independent_ics = {f'feature_{i}': 0.05 + 0.01*i for i in range(13)}
        weights = combo.optimal_weights(independent_ics)

        total_weight = sum(weights.values())
        assert np.isclose(total_weight, 1.0)

    def test_weights_proportional_to_ic(self):
        """Weights should be proportional to IC."""
        combo = SignalCombination(self.features, self.labels)
        independent_ics = {f'feature_{i}': 0.1 if i == 0 else 0.01 for i in range(13)}
        weights = combo.optimal_weights(independent_ics)

        # Feature 0 should have highest weight
        assert weights['feature_0'] > max(weights[f'feature_{i}'] for i in range(1, 13))

    def test_zero_ic_signals_equal_weight(self):
        """When all ICs are zero, signals should get equal weight (default)."""
        combo = SignalCombination(self.features, self.labels)
        independent_ics = {f'feature_{i}': 0.0 for i in range(13)}
        weights = combo.optimal_weights(independent_ics)

        # With no positive ICs, should default to equal weight
        assert np.allclose(list(weights.values()), 1.0/13)

    def test_combined_signal_generation(self):
        """Test combined signal generation from weights."""
        combo = SignalCombination(self.features, self.labels)
        weights = {f'feature_{i}': 1.0/13 for i in range(13)}
        combined = combo.combined_signal(self.features, weights)

        assert len(combined) == len(self.features)
        assert isinstance(combined, np.ndarray)


class TestFullPipeline:
    """Tests for full 11-step pipeline."""

    def setup_method(self):
        """Create dummy features."""
        np.random.seed(42)
        self.features = pd.DataFrame(
            np.random.randn(500, 13),
            columns=[f'feature_{i}' for i in range(13)]
        )
        self.labels = np.random.randint(0, 3, 500)

    def test_full_run_returns_all_results(self):
        """Full pipeline should return all intermediate and final results."""
        combo = SignalCombination(self.features, self.labels)
        results = combo.run()

        required_keys = [
            'raw_ics', 'adjusted_ics', 'tstats',
            'residuals', 'independent_ics',
            'effective_n', 'diversification_benefit',
            'weights', 'combined_signal'
        ]
        for key in required_keys:
            assert key in results

    def test_full_run_combined_signal_length(self):
        """Combined signal should match data length."""
        combo = SignalCombination(self.features, self.labels)
        results = combo.run()

        assert len(results['combined_signal']) == len(self.features)

    def test_full_run_weights_sum_to_one(self):
        """Weights from full pipeline should sum to 1."""
        combo = SignalCombination(self.features, self.labels)
        results = combo.run()

        total_weight = sum(results['weights'].values())
        assert np.isclose(total_weight, 1.0) or total_weight == 0.0


class TestCrossValidation:
    """Tests for cross-validation comparison."""

    def setup_method(self):
        """Create dummy features."""
        np.random.seed(42)
        self.features = pd.DataFrame(
            np.random.randn(500, 13),
            columns=[f'feature_{i}' for i in range(13)]
        )
        self.labels = np.random.randint(0, 3, 500)

    def test_cv_comparison_structure(self):
        """Cross-validation should return comparison dict."""
        results = compare_signals_cv(self.features, self.labels, n_splits=3)

        required_keys = [
            'combined_ic_oos', 'baseline_ic_oos',
            'combined_ic_oos_mean', 'baseline_ic_oos_mean',
            'improvement_mean'
        ]
        for key in required_keys:
            assert key in results

    def test_cv_folds_match_n_splits(self):
        """Number of OOS ICs should match n_splits."""
        results = compare_signals_cv(self.features, self.labels, n_splits=3)

        assert len(results['combined_ic_oos']) == 3
        assert len(results['baseline_ic_oos']) == 3
        assert len(results['improvement']) == 3

    def test_cv_comparison_valid_values(self):
        """IC values should be finite."""
        results = compare_signals_cv(self.features, self.labels, n_splits=3)

        combined_mean = results['combined_ic_oos_mean']
        baseline_mean = results['baseline_ic_oos_mean']

        assert np.isfinite(combined_mean)
        assert np.isfinite(baseline_mean)
