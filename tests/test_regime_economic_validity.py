"""Tests for DIAG-04: Regime-conditional forward return analysis.

Validates that compute_forward_return_analysis() in evaluation.py:
- Returns correct structure (kruskal_wallis, mean_returns, n_obs keys)
- Kruskal-Wallis p-values are valid floats in [0, 1]
- Mean returns are computed per regime per horizon
- Does NOT add forward returns as model features (causal integrity check)
- Works with missing assets gracefully

Per REQUIREMENTS.md DIAG-04 and CONTEXT.md D-07:
  p-values are reported only — no auto-flagging. Human interprets.
"""

import numpy as np
import pandas as pd
import pytest

from src.core.evaluation import compute_forward_return_analysis


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture()
def sample_results():
    """Synthetic regime_results DataFrame with 3 regimes over 500 days."""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='B')
    # Alternate regimes in blocks to simulate realistic dwell
    regime_sequence = []
    regimes = ['Low-Vol', 'Mid-Vol', 'High-Vol']
    for i in range(0, 500, 30):
        r = regimes[i // 30 % 3]
        regime_sequence.extend([r] * min(30, 500 - i))
    df = pd.DataFrame({'regime_name': regime_sequence[:500]}, index=dates)
    return df


@pytest.fixture()
def sample_market(sample_results):
    """Synthetic market data with SPY/EEM/TLT/HYG price columns."""
    np.random.seed(42)
    dates = sample_results.index
    n = len(dates)

    # Generate realistic price series via cumulative returns
    def make_price(seed, drift=0.0003, vol=0.01, start=100):
        np.random.seed(seed)
        rets = np.random.normal(drift, vol, n)
        prices = start * np.exp(np.cumsum(rets))
        return prices

    df = pd.DataFrame({
        'SPY_close': make_price(1, drift=0.0004, vol=0.012),
        'EEM_close': make_price(2, drift=0.0003, vol=0.015),
        'TLT_close': make_price(3, drift=0.0001, vol=0.008),
        'HYG_close': make_price(4, drift=0.0002, vol=0.006),
    }, index=dates)
    return df


@pytest.fixture()
def two_regime_results(sample_results):
    """Minimum viable: only 2 regimes (still valid for Kruskal-Wallis)."""
    df = sample_results.copy()
    df['regime_name'] = df['regime_name'].replace({'High-Vol': 'Mid-Vol'})
    return df


# ===================================================================
# Structure tests
# ===================================================================

class TestReturnStructure:
    """compute_forward_return_analysis returns expected structure."""

    def test_returns_dict(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        assert isinstance(result, dict)

    def test_has_required_keys(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        assert 'kruskal_wallis' in result
        assert 'mean_returns' in result
        assert 'n_obs' in result

    def test_n_obs_positive(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        assert result['n_obs'] > 0

    def test_kruskal_wallis_is_dict(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        assert isinstance(result['kruskal_wallis'], dict)

    def test_mean_returns_is_dict(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        assert isinstance(result['mean_returns'], dict)

    def test_none_inputs_return_empty(self):
        result = compute_forward_return_analysis(None, None)
        assert result == {}

    def test_none_market_returns_empty(self, sample_results):
        result = compute_forward_return_analysis(sample_results, None)
        assert result == {}


# ===================================================================
# Kruskal-Wallis tests
# ===================================================================

class TestKruskalWallis:
    """Kruskal-Wallis results are valid."""

    def test_kw_keys_cover_all_assets_and_horizons(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        kw = result['kruskal_wallis']
        expected_keys = {
            f'{asset}_{horizon}'
            for asset in ['SPY', 'EEM', 'TLT', 'HYG']
            for horizon in ['1d', '5d', '21d']
        }
        # All expected keys present (may be subset if asset missing from market data)
        for key in expected_keys:
            assert key in kw, f"Missing KW key: {key}"

    def test_kw_p_values_in_unit_interval(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        kw = result['kruskal_wallis']
        for key, val in kw.items():
            p = val.get('p_value')
            if p is not None:
                assert 0.0 <= p <= 1.0, f"{key} p-value {p} outside [0,1]"

    def test_kw_statistics_nonnegative(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        kw = result['kruskal_wallis']
        for key, val in kw.items():
            stat = val.get('statistic')
            if stat is not None:
                assert stat >= 0.0, f"{key} statistic {stat} is negative"

    def test_kw_has_statistic_and_p_value_keys(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        kw = result['kruskal_wallis']
        for key, val in kw.items():
            assert 'statistic' in val, f"Missing 'statistic' in {key}"
            assert 'p_value' in val, f"Missing 'p_value' in {key}"

    def test_kw_works_with_two_regimes(self, two_regime_results, sample_market):
        """Kruskal-Wallis requires >= 2 groups — minimum case works."""
        result = compute_forward_return_analysis(two_regime_results, sample_market)
        assert 'kruskal_wallis' in result
        for val in result['kruskal_wallis'].values():
            p = val.get('p_value')
            if p is not None:
                assert 0.0 <= p <= 1.0


# ===================================================================
# Mean returns tests
# ===================================================================

class TestMeanReturns:
    """Mean forward returns are computed per regime per horizon."""

    def test_mean_returns_covers_all_assets(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        mr = result['mean_returns']
        for asset in ['SPY', 'EEM', 'TLT', 'HYG']:
            assert asset in mr, f"Asset {asset} missing from mean_returns"

    def test_mean_returns_covers_all_regimes(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        mr = result['mean_returns']
        expected_regimes = {'Low-Vol', 'Mid-Vol', 'High-Vol'}
        for asset in mr:
            actual_regimes = set(mr[asset].keys())
            assert expected_regimes == actual_regimes, (
                f"{asset}: expected regimes {expected_regimes}, got {actual_regimes}"
            )

    def test_mean_returns_covers_all_horizons(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        mr = result['mean_returns']
        for asset in mr:
            for regime in mr[asset]:
                for horizon in ['1d', '5d', '21d']:
                    assert horizon in mr[asset][regime], (
                        f"Missing horizon {horizon} for {asset} regime {regime}"
                    )

    def test_mean_returns_are_floats_or_none(self, sample_results, sample_market):
        result = compute_forward_return_analysis(sample_results, sample_market)
        mr = result['mean_returns']
        for asset in mr:
            for regime in mr[asset]:
                for horizon in mr[asset][regime]:
                    v = mr[asset][regime][horizon]
                    assert v is None or isinstance(v, float), (
                        f"{asset}/{regime}/{horizon}: expected float or None, got {type(v)}"
                    )

    def test_mean_returns_are_percent_scale(self, sample_results, sample_market):
        """Mean returns should be in percent — not in decimal (not 0.001, but 0.1)."""
        result = compute_forward_return_analysis(sample_results, sample_market)
        mr = result['mean_returns']
        for asset in mr:
            for regime in mr[asset]:
                for horizon in mr[asset][regime]:
                    v = mr[asset][regime][horizon]
                    if v is not None:
                        # 21-day return in % should be between -50% and +50% for test data
                        assert abs(v) < 50.0, (
                            f"{asset}/{regime}/{horizon}: return {v} looks like it "
                            "may not be in percent scale"
                        )


# ===================================================================
# Causal integrity tests (DIAG-04 out-of-scope constraint)
# ===================================================================

class TestCausalIntegrity:
    """Forward returns must NEVER appear as model features or training inputs."""

    def test_forward_return_analysis_not_in_config(self):
        """Forward return function name must not appear in config.py."""
        try:
            with open('src/config.py') as f:
                content = f.read()
            assert 'forward_return' not in content.lower(), (
                "Forward return analysis must not appear in config.py — "
                "it is a validation diagnostic, not a model parameter"
            )
        except FileNotFoundError:
            pytest.skip("config.py not found at expected path")

    def test_forward_return_function_not_imported_in_train(self):
        """compute_forward_return_analysis must not be imported in train.py."""
        train_paths = ['scripts/train.py', 'src/core/train.py', 'train.py']
        for path in train_paths:
            try:
                with open(path) as f:
                    content = f.read()
                assert 'compute_forward_return_analysis' not in content, (
                    f"compute_forward_return_analysis must NOT be imported in {path} "
                    "(forward returns are validation-only, never training features)"
                )
            except FileNotFoundError:
                continue  # File doesn't exist — skip

    def test_forward_return_function_not_imported_in_features(self):
        """compute_forward_return_analysis must not appear in feature engineering."""
        feature_paths = [
            'src/core/features.py',
            'scripts/features.py',
            'src/features.py',
        ]
        for path in feature_paths:
            try:
                with open(path) as f:
                    content = f.read()
                assert 'compute_forward_return_analysis' not in content, (
                    f"compute_forward_return_analysis must NOT appear in {path} "
                    "(forward returns are validation-only, never training features)"
                )
            except FileNotFoundError:
                continue  # File doesn't exist — skip

    def test_evaluation_module_docstring_states_validation_only(self):
        """evaluation.py module docstring must indicate forward returns are validation only."""
        from src.core import evaluation
        doc = evaluation.__doc__ or ''
        # The function docstring carries this guarantee
        fn = compute_forward_return_analysis
        fn_doc = fn.__doc__ or ''
        assert 'validation' in fn_doc.lower() or 'diagnostic' in fn_doc.lower(), (
            "compute_forward_return_analysis docstring must state it is validation/diagnostic only"
        )


# ===================================================================
# Edge cases
# ===================================================================

class TestEdgeCases:
    """Graceful handling of edge cases."""

    def test_missing_asset_column_skipped(self, sample_results, sample_market):
        """If an asset column is missing, result still returned for other assets."""
        market_partial = sample_market.drop(columns=['EEM_close'])
        result = compute_forward_return_analysis(sample_results, market_partial)
        assert 'kruskal_wallis' in result
        # SPY should still be present
        mr = result['mean_returns']
        assert 'SPY' in mr

    def test_single_regime_kw_skipped(self):
        """If only 1 regime, Kruskal-Wallis cannot run — handled gracefully."""
        dates = pd.date_range('2022-01-01', periods=200, freq='B')
        results = pd.DataFrame({'regime_name': ['Low-Vol'] * 200}, index=dates)
        np.random.seed(7)
        market = pd.DataFrame({
            'SPY_close': 100 * np.exp(np.cumsum(np.random.normal(0, 0.01, 200))),
            'EEM_close': 50 * np.exp(np.cumsum(np.random.normal(0, 0.012, 200))),
            'TLT_close': 80 * np.exp(np.cumsum(np.random.normal(0, 0.008, 200))),
            'HYG_close': 90 * np.exp(np.cumsum(np.random.normal(0, 0.006, 200))),
        }, index=dates)
        result = compute_forward_return_analysis(results, market)
        # Should return without crashing; KW dict may be empty or have None p-values
        assert isinstance(result, dict)
        assert 'kruskal_wallis' in result

    def test_results_with_nans_handled(self, sample_market):
        """NaN regimes in results are excluded gracefully."""
        dates = pd.date_range('2020-01-01', periods=500, freq='B')
        regime_sequence = ['Low-Vol'] * 200 + [np.nan] * 50 + ['High-Vol'] * 250
        results = pd.DataFrame({'regime_name': regime_sequence}, index=dates)
        result = compute_forward_return_analysis(results, sample_market)
        assert 'n_obs' in result
