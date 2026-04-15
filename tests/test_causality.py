"""Tests for the three causality guarantees.

If any of these fail, every regime label in the pipeline is contaminated
with future data and cannot be trusted for real-time decisions.
"""

import numpy as np
import pandas as pd
import pytest
from hmmlearn import hmm

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from train import expanding_standardize, filtered_probs, filtered_labels, StudentTHMM
from src.features.features import _winsorize


# ═══════════════════════════════════════════════════════════════════
# expanding_standardize — causal z-score
# ═══════════════════════════════════════════════════════════════════

class TestExpandingStandardize:

    def test_uses_only_past_data(self, rng):
        """Modifying future rows must NOT change z-score at row t."""
        X = rng.randn(500, 3)

        # Full run
        result_full, _, _ = expanding_standardize(X, min_warmup=50)

        # Truncated: only first 300 rows
        result_trunc, _, _ = expanding_standardize(X[:300], min_warmup=50)

        # Row 250 should be identical in both runs
        np.testing.assert_allclose(
            result_full[250], result_trunc[250], rtol=1e-12,
            err_msg="expanding_standardize leaked future data into row 250"
        )

    def test_warmup_is_nan(self, rng):
        """First min_warmup rows must be NaN; row min_warmup must not."""
        X = rng.randn(500, 3)
        result, _, _ = expanding_standardize(X, min_warmup=100)

        assert np.isnan(result[:100]).all(), "Warm-up rows should all be NaN"
        assert not np.isnan(result[100]).any(), "Row min_warmup should not be NaN"

    def test_manual_computation(self):
        """Hand-verify z-scores on a tiny array."""
        X = np.array([[10.0], [20.0], [30.0], [40.0], [50.0]])
        result, _, _ = expanding_standardize(X, min_warmup=2)

        # Rows 0, 1 should be NaN (warm-up)
        assert np.isnan(result[0, 0])
        assert np.isnan(result[1, 0])

        # Row 2: mean([10,20,30])=20, std=sqrt(200/3)~8.165
        vals = X[:3, 0]
        m = vals.mean()
        s = np.sqrt(np.mean((vals - m) ** 2))  # population std (ddof=0)
        expected = (X[2, 0] - m) / s
        np.testing.assert_allclose(result[2, 0], expected, rtol=1e-10)

        # Row 4: mean([10,20,30,40,50])=30, std=sqrt(200)~14.14
        vals = X[:5, 0]
        m = vals.mean()
        s = np.sqrt(np.mean((vals - m) ** 2))
        expected = (X[4, 0] - m) / s
        np.testing.assert_allclose(result[4, 0], expected, rtol=1e-10)


# ═══════════════════════════════════════════════════════════════════
# filtered_probs — forward-only regime probabilities
# ═══════════════════════════════════════════════════════════════════

def _fit_simple_hmm(rng, n_states=3, n_dim=2, n_samples=300):
    """Helper: fit a StudentTHMM on synthetic data for testing."""
    X = rng.randn(n_samples, n_dim)
    model = StudentTHMM(
        n_components=n_states, covariance_type='full',
        n_iter=50, random_state=42, verbose=False,
    )
    model.fit(X)
    return model, X


class TestFilteredProbs:

    def test_uses_only_past_data(self, rng):
        """Replacing future observations must NOT change probs at row t."""
        model, X = _fit_simple_hmm(rng)

        # Full run
        probs_full = filtered_probs(model, X)

        # Replace rows 151..end with extreme garbage
        X_modified = X.copy()
        X_modified[151:] = 9999.0
        probs_modified = filtered_probs(model, X_modified)

        # Row 150 should be identical
        np.testing.assert_allclose(
            probs_full[150], probs_modified[150], rtol=1e-12,
            err_msg="filtered_probs leaked future data into row 150"
        )

    def test_differs_from_smoother(self, rng):
        """filtered_probs must differ from predict_proba (forward-backward)."""
        model, X = _fit_simple_hmm(rng)

        filtered = filtered_probs(model, X)
        smoothed = model.predict_proba(X)

        # They should NOT be identical (smoother uses future info)
        assert not np.allclose(filtered, smoothed, atol=1e-6), (
            "filtered_probs matches predict_proba — "
            "may be accidentally using backward pass"
        )

    def test_probabilities_sum_to_one(self, rng):
        """Each row of filtered_probs must sum to 1."""
        model, X = _fit_simple_hmm(rng)
        probs = filtered_probs(model, X)

        np.testing.assert_allclose(
            probs.sum(axis=1), np.ones(len(X)), atol=1e-10,
            err_msg="Filtered probabilities don't sum to 1"
        )


# ═══════════════════════════════════════════════════════════════════
# filtered_labels — hysteresis
# ═══════════════════════════════════════════════════════════════════

class TestFilteredLabels:

    def test_hysteresis_suppresses_brief_blip(self, rng):
        """A 1-day regime blip should NOT flip label with hold_days=3."""
        model, X = _fit_simple_hmm(rng)

        labels_hold1 = filtered_labels(model, X, hold_days=1)
        labels_hold3 = filtered_labels(model, X, hold_days=3)

        # hold_days=3 should produce fewer or equal transitions
        transitions_1 = np.sum(labels_hold1[1:] != labels_hold1[:-1])
        transitions_3 = np.sum(labels_hold3[1:] != labels_hold3[:-1])
        assert transitions_3 <= transitions_1, (
            f"Hysteresis (hold=3) produced MORE transitions ({transitions_3}) "
            f"than hold=1 ({transitions_1})"
        )

    def test_hold_days_1_equals_raw_argmax(self, rng):
        """With hold_days=1, labels should equal raw argmax of filtered probs."""
        model, X = _fit_simple_hmm(rng)

        labels = filtered_labels(model, X, hold_days=1)
        probs = filtered_probs(model, X)
        raw_argmax = probs.argmax(axis=1)

        np.testing.assert_array_equal(
            labels, raw_argmax,
            err_msg="hold_days=1 should produce raw argmax labels"
        )


# ═══════════════════════════════════════════════════════════════════
# _winsorize — causal expanding-window clipping
# ═══════════════════════════════════════════════════════════════════

class TestWinsorize:

    def test_uses_only_past_data(self):
        """Late extreme outliers must NOT affect early winsorized values."""
        np.random.seed(42)
        base_data = np.random.randn(300)

        # Same first 300 rows, but spike version has 50 extreme rows appended
        calm = pd.DataFrame({'A': base_data.copy()})
        with_spike = pd.DataFrame({
            'A': np.concatenate([base_data.copy(), [10000.0] * 50])
        })

        result_calm = _winsorize(calm, min_warmup=50)
        result_spike = _winsorize(with_spike, min_warmup=50)

        # Row 200 should be identical regardless of spike at rows 300+
        np.testing.assert_allclose(
            result_calm.iloc[200, 0], result_spike.iloc[200, 0], rtol=1e-12,
            err_msg="_winsorize leaked future outliers into row 200"
        )

    def test_warmup_period_unchanged(self):
        """Rows before min_warmup should not be clipped."""
        np.random.seed(42)
        data = pd.DataFrame({'A': np.random.randn(500)})
        result = _winsorize(data, min_warmup=252)

        # First 251 rows (indices 0..250) should be unchanged
        # (expanding quantile has NaN before min_periods is reached)
        pd.testing.assert_series_equal(
            data['A'].iloc[:251], result['A'].iloc[:251],
            check_names=False,
            obj="Warmup rows should pass through unchanged",
        )
