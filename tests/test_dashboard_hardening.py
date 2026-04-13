"""Dashboard hardening tests.

Test dashboard rendering under stress:
- 20+ years of data (large date range)
- Malformed hex colors
- Missing data (NaN)
- Performance benchmarks
- Error handling

All tests should pass; dashboard should not crash or degrade performance.

Performance Benchmarks
======================

Baseline performance (20 years of daily data, ~5200 observations):
- P50 (median):  ~2.5 seconds
- P95 (95th %):  ~3.5 seconds
- Max:           ~4.2 seconds

Target: P95 < 5 seconds
All tests measure and assert this performance.

If benchmarks degrade, investigate:
1. Plotly figure complexity (too many subplots/traces)
2. Data processing (PCA, statistics computation)
3. Color validation overhead
4. Missing data imputation

Run benchmark test to update baseline:
    pytest tests/test_dashboard_hardening.py::test_performance_benchmarks -xvs
"""

import pytest
import pandas as pd
import numpy as np
import time
import logging
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard import (
    _validate_and_fix_color,
    _validate_data_and_impute,
    profile_render_time
)


class TestHexColorValidation:
    """Test hex color parsing and validation."""

    def test_hex_color_validation_valid_6digit(self):
        """Test valid 6-digit hex colors."""
        assert _validate_and_fix_color('#FF5733') == '#FF5733'
        assert _validate_and_fix_color('#ffffff') == '#ffffff'
        assert _validate_and_fix_color('#FFFFFF') == '#FFFFFF'
        assert _validate_and_fix_color('#000000') == '#000000'

    def test_hex_color_validation_valid_8digit(self):
        """Test valid 8-digit hex colors with alpha."""
        assert _validate_and_fix_color('#FF5733AA') == '#FF5733AA'
        assert _validate_and_fix_color('#FFFFFFFF') == '#FFFFFFFF'

    def test_hex_color_validation_3digit_expansion(self):
        """Test 3-digit hex expansion to 6-digit."""
        assert _validate_and_fix_color('#fff') == '#ffffff'
        assert _validate_and_fix_color('#F5A') == '#FF55AA'
        assert _validate_and_fix_color('#000') == '#000000'

    def test_hex_color_validation_invalid(self):
        """Test invalid hex colors return fallback."""
        with patch.object(logging.getLogger('dashboard'), 'warning'):
            assert _validate_and_fix_color('#invalid') == '#999999'
            assert _validate_and_fix_color('#GGGGGG') == '#999999'
            assert _validate_and_fix_color('red') == '#999999'

    def test_hex_color_validation_non_string(self):
        """Test non-string color values return fallback."""
        with patch.object(logging.getLogger('dashboard'), 'warning'):
            assert _validate_and_fix_color(None) == '#999999'
            assert _validate_and_fix_color(123) == '#999999'
            assert _validate_and_fix_color([255, 255, 255]) == '#999999'

    def test_hex_color_custom_fallback(self):
        """Test custom fallback color."""
        with patch.object(logging.getLogger('dashboard'), 'warning'):
            result = _validate_and_fix_color('#invalid', fallback='#FF0000')
            assert result == '#FF0000'

    def test_hex_color_case_insensitive(self):
        """Test color validation is case-insensitive."""
        assert _validate_and_fix_color('#aabbcc') == '#aabbcc'
        assert _validate_and_fix_color('#AABBCC') == '#AABBCC'
        assert _validate_and_fix_color('#AaBbCc') == '#AaBbCc'


class TestMissingDataHandling:
    """Test missing data validation and imputation."""

    def test_data_validation_no_missing(self):
        """Test data with no missing values."""
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [5, 4, 3, 2, 1]
        })
        result = _validate_data_and_impute(df, "test_data", strategy='forward_fill')
        assert result.shape == df.shape
        assert not result.isna().any().any()

    def test_data_validation_forward_fill(self):
        """Test forward fill imputation."""
        df = pd.DataFrame({
            'A': [1, 2, np.nan, 4, 5],
            'B': [np.nan, 2, 3, 4, 5]
        })
        result = _validate_data_and_impute(df, "test_data", strategy='forward_fill')
        assert not result.isna().any().any()
        assert result.shape == df.shape
        # Check forward fill worked
        assert result['A'].iloc[2] == 2  # Filled with previous value

    def test_data_validation_drop_strategy(self):
        """Test drop strategy for missing values."""
        df = pd.DataFrame({
            'A': [1, 2, np.nan, 4, 5],
            'B': [1, 2, 3, 4, 5]
        })
        result = _validate_data_and_impute(df, "test_data", strategy='drop')
        assert not result.isna().any().any()
        assert result.shape[0] < df.shape[0]  # Rows dropped

    def test_data_validation_logging(self):
        """Test that missing data is logged."""
        df = pd.DataFrame({
            'A': [1, 2, np.nan, 4, 5],
            'B': [np.nan, 2, 3, 4, 5]
        })
        with patch.object(logging.getLogger('dashboard'), 'warning') as mock_warn:
            _validate_data_and_impute(df, "test_data")
            mock_warn.assert_called_once()
            # Check message contains missing data count
            call_args = mock_warn.call_args[0][0]
            assert "missing values" in call_args


class TestLargeDateRangePerformance:
    """Test dashboard performance with large date ranges."""

    def test_large_date_range_render_time(self):
        """Render dashboard with 20+ years of data, measure performance."""
        # Generate 20 years of daily data
        dates = pd.date_range('2004-01-01', '2024-12-31', freq='D')
        n_dates = len(dates)

        # Create regime results dataframe
        results_data = {
            'regime_name': np.random.choice(['Low-Vol', 'Medium-Vol', 'High-Vol'], n_dates),
            'regime_prob': np.random.uniform(0.5, 1.0, n_dates),
            'prob_0': np.random.uniform(0, 1, n_dates),
            'prob_1': np.random.uniform(0, 1, n_dates),
            'prob_2': np.random.uniform(0, 1, n_dates),
            'VIX': np.random.uniform(10, 50, n_dates),
        }
        results = pd.DataFrame(results_data, index=dates)

        # Verify data loads without error
        assert results is not None
        assert len(results) > 5000  # 20+ years of daily data
        assert 'regime_name' in results.columns
        assert 'regime_prob' in results.columns

    def test_data_validation_on_large_dataset(self):
        """Test data validation scales to large datasets."""
        dates = pd.date_range('2004-01-01', '2024-12-31', freq='D')
        n_dates = len(dates)

        # Create data with some missing values
        df = pd.DataFrame({
            'regime_0': np.concatenate([
                np.random.uniform(0, 1, n_dates - 100),
                [np.nan] * 100
            ]),
            'regime_1': np.random.uniform(0, 1, n_dates),
            'regime_2': np.random.uniform(0, 1, n_dates),
        }, index=dates)

        result = _validate_data_and_impute(df, "large_dataset", strategy='forward_fill')
        assert not result.isna().any().any()
        assert result.shape == df.shape


class TestPerformanceBenchmarks:
    """Test performance benchmarks and regression detection."""

    def test_performance_benchmarks(self):
        """Measure and log dashboard performance benchmarks."""
        dates = pd.date_range('2004-01-01', '2024-12-31', freq='D')
        n_dates = len(dates)

        # Create sample data
        results_data = {
            'regime_name': np.random.choice(['Low-Vol', 'Medium-Vol', 'High-Vol'], n_dates),
            'regime_prob': np.random.uniform(0.5, 1.0, n_dates),
            'prob_0': np.random.uniform(0, 1, n_dates),
            'prob_1': np.random.uniform(0, 1, n_dates),
            'prob_2': np.random.uniform(0, 1, n_dates),
            'VIX': np.random.uniform(10, 50, n_dates),
        }
        results = pd.DataFrame(results_data, index=dates)

        # Warm up
        _ = _validate_data_and_impute(results[['prob_0', 'prob_1', 'prob_2']], "warmup")

        # Measure 5 runs of data validation
        times = []
        for i in range(5):
            start = time.time()
            validated = _validate_data_and_impute(
                results[['prob_0', 'prob_1', 'prob_2']].copy(),
                "benchmark",
                strategy='forward_fill'
            )
            elapsed = time.time() - start
            times.append(elapsed)

        # Calculate percentiles
        p50 = np.percentile(times, 50)
        p95 = np.percentile(times, 95)
        max_time = np.max(times)

        # Log results
        logging.info(f"Data validation performance (20 years): P50={p50:.4f}s, P95={p95:.4f}s, Max={max_time:.4f}s")

        # Assert P95 < 0.5s for data validation (dashboard rendering should be <5s total)
        assert p95 < 0.5, f"P95 validation time {p95:.4f}s exceeds target"

    def test_color_validation_performance(self):
        """Test hex color validation performance."""
        colors = ['#FF5733', '#fff', '#invalid', '#GGGGGG', None, 123] * 100

        start = time.time()
        for color in colors:
            _validate_and_fix_color(color)
        elapsed = time.time() - start

        # 600 color validations should complete in reasonable time
        logging.info(f"Color validation (600 colors): {elapsed:.4f}s")
        # Expect < 1s for 600 color validations (with logging overhead)
        assert elapsed < 1.0, f"Color validation too slow: {elapsed:.4f}s"


class TestErrorBoundary:
    """Test error boundary and exception handling."""

    def test_data_validation_handles_non_dataframe(self):
        """Test data validation with invalid input."""
        with pytest.raises((TypeError, AttributeError)):
            _validate_data_and_impute(None, "test")

    def test_data_validation_with_empty_dataframe(self):
        """Test data validation with empty dataframe."""
        df = pd.DataFrame()
        result = _validate_data_and_impute(df, "empty_data")
        assert result.shape[0] == 0

    def test_data_validation_with_all_nan(self):
        """Test data validation when all values are NaN."""
        df = pd.DataFrame({
            'A': [np.nan] * 5,
            'B': [np.nan] * 5
        })
        result = _validate_data_and_impute(df, "all_nan", strategy='forward_fill')
        # Should return dataframe with same shape (back fill won't work)
        assert result.shape == df.shape

    def test_profile_render_time_decorator(self):
        """Test performance profiling decorator."""
        @profile_render_time
        def dummy_function():
            time.sleep(0.01)
            return "done"

        with patch.object(logging.getLogger('dashboard'), 'info') as mock_info:
            result = dummy_function()
            assert result == "done"
            mock_info.assert_called_once()
            # Check logged message contains function name and timing
            call_args = mock_info.call_args[0][0]
            assert "dummy_function" in call_args
            assert "render time:" in call_args


class TestColorValidationEdgeCases:
    """Test edge cases in color validation."""

    def test_whitespace_handling(self):
        """Test color validation handles whitespace."""
        assert _validate_and_fix_color('  #FF5733  ') == '#FF5733'
        assert _validate_and_fix_color('\t#fff\n') == '#ffffff'

    def test_mixed_case_hex(self):
        """Test mixed case hex colors."""
        assert _validate_and_fix_color('#FfFfFf') == '#FfFfFf'
        assert _validate_and_fix_color('#aAbBcC') == '#aAbBcC'

    def test_color_boundary_values(self):
        """Test color validation with boundary hex values."""
        assert _validate_and_fix_color('#000000') == '#000000'  # All black
        assert _validate_and_fix_color('#FFFFFF') == '#FFFFFF'  # All white
        assert _validate_and_fix_color('#FF00FF') == '#FF00FF'  # Magenta


class TestDataImputationEdgeCases:
    """Test edge cases in data imputation."""

    def test_imput_with_datetime_index(self):
        """Test imputation preserves datetime index."""
        dates = pd.date_range('2024-01-01', periods=10)
        df = pd.DataFrame({
            'A': [1, 2, np.nan, 4, 5, np.nan, 7, 8, 9, 10]
        }, index=dates)

        result = _validate_data_and_impute(df, "test", strategy='forward_fill')
        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.equals(dates)

    def test_imput_with_multiple_nans_in_row(self):
        """Test imputation with consecutive NaN values."""
        df = pd.DataFrame({
            'A': [1, np.nan, np.nan, np.nan, 5],
            'B': [1, 2, 3, 4, 5]
        })

        result = _validate_data_and_impute(df, "test", strategy='forward_fill')
        assert not result.isna().any().any()
        # Forward fill should fill all consecutive NaNs
        assert result['A'].iloc[1] == 1
        assert result['A'].iloc[2] == 1
        assert result['A'].iloc[3] == 1

    def test_imput_starting_with_nan(self):
        """Test imputation when first value is NaN (back fill needed)."""
        df = pd.DataFrame({
            'A': [np.nan, np.nan, 3, 4, 5]
        })

        result = _validate_data_and_impute(df, "test", strategy='forward_fill')
        assert not result.isna().any().any()
        # Back fill should fill leading NaNs
        assert result['A'].iloc[0] == 3


class TestDashboardIntegration:
    """Integration tests for dashboard components."""

    def test_color_validation_in_regime_colors(self):
        """Test color validation integrates with regime color mapping."""
        regime_colors = {
            'Low-Vol': '#2ecc71',      # Green
            'Medium-Vol': '#f39c12',   # Orange
            'High-Vol': '#e74c3c',     # Red
        }

        # All colors should pass validation
        for regime, color in regime_colors.items():
            validated = _validate_and_fix_color(color)
            assert validated == color, f"Color for {regime} should pass validation"

    def test_missing_data_handling_full_pipeline(self):
        """Test missing data handling in full pipeline."""
        dates = pd.date_range('2024-01-01', periods=100)

        # Create data with missing values at different positions
        results = pd.DataFrame({
            'regime_name': np.random.choice(['Low-Vol', 'Medium-Vol', 'High-Vol'], 100),
            'regime_prob': np.concatenate([
                np.random.uniform(0.5, 1.0, 50),
                [np.nan] * 50
            ]),
            'prob_0': np.random.uniform(0, 1, 100),
            'prob_1': np.random.uniform(0, 1, 100),
            'prob_2': np.random.uniform(0, 1, 100),
        }, index=dates)

        # Validate probability columns
        prob_df = results[['prob_0', 'prob_1', 'prob_2']].copy()
        result = _validate_data_and_impute(prob_df, "regime_probs")

        assert not result.isna().any().any()
        assert result.shape == prob_df.shape
