"""Tests for causality guarantees.

If any of these fail, regime labels are contaminated with future data
and cannot be trusted for real-time trading decisions.
"""

import numpy as np
import pandas as pd
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.inference import expanding_standardize
from src.features.features import _winsorize


# ═══════════════════════════════════════════════════════════════════
# expanding_standardize — causal z-score
# ═══════════════════════════════════════════════════════════════════

class TestExpandingStandardize:

    def test_uses_only_past_data(self, rng):
        """Modifying future rows must NOT change z-score at row t."""
        X = rng.randn(500, 3)

        result_full, _, _ = expanding_standardize(X, min_warmup=50)
        result_trunc, _, _ = expanding_standardize(X[:300], min_warmup=50)

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

        assert np.isnan(result[0, 0])
        assert np.isnan(result[1, 0])

        vals = X[:3, 0]
        m = vals.mean()
        s = np.sqrt(np.mean((vals - m) ** 2))
        np.testing.assert_allclose(result[2, 0], (X[2, 0] - m) / s, rtol=1e-10)

        vals = X[:5, 0]
        m = vals.mean()
        s = np.sqrt(np.mean((vals - m) ** 2))
        np.testing.assert_allclose(result[4, 0], (X[4, 0] - m) / s, rtol=1e-10)


# ═══════════════════════════════════════════════════════════════════
# _winsorize — causal expanding-window clipping
# ═══════════════════════════════════════════════════════════════════

class TestWinsorize:

    def test_uses_only_past_data(self):
        """Late extreme outliers must NOT affect early winsorized values."""
        np.random.seed(42)
        base_data = np.random.randn(300)

        calm = pd.DataFrame({'A': base_data.copy()})
        with_spike = pd.DataFrame({
            'A': np.concatenate([base_data.copy(), [10000.0] * 50])
        })

        result_calm = _winsorize(calm, min_warmup=50)
        result_spike = _winsorize(with_spike, min_warmup=50)

        np.testing.assert_allclose(
            result_calm.iloc[200, 0], result_spike.iloc[200, 0], rtol=1e-12,
            err_msg="_winsorize leaked future outliers into row 200"
        )

    def test_warmup_period_unchanged(self):
        """Rows before min_warmup should not be clipped."""
        np.random.seed(42)
        data = pd.DataFrame({'A': np.random.randn(500)})
        result = _winsorize(data, min_warmup=252)

        pd.testing.assert_series_equal(
            data['A'].iloc[:251], result['A'].iloc[:251],
            check_names=False,
            obj="Warmup rows should pass through unchanged",
        )
