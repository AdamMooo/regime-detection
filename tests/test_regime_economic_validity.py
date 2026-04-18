"""Tests for DIAG-04: regime-conditional forward return analysis.

Validates that analyze_forward_returns() in src.core.evaluation:
- Returns correctly structured output
- Contains Kruskal-Wallis statistics
- Does not modify regime assignments (no lookahead)
- Handles missing asset columns gracefully
- Computes per-regime median returns
"""

import numpy as np
import pandas as pd
import pytest

from src.core.evaluation import analyze_forward_returns


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_results(n=500, regimes=None):
    """Create synthetic regime results DataFrame."""
    if regimes is None:
        regimes = ['Low-Vol', 'Moderate-Vol', 'High-Vol', 'Crisis']
    dates = pd.date_range('2021-01-01', periods=n, freq='B')
    rng = np.random.default_rng(42)
    labels = rng.choice(regimes, size=n)
    return pd.DataFrame({'regime_name': labels}, index=dates)


def _make_market(n=500, assets=None):
    """Create synthetic market price DataFrame."""
    if assets is None:
        assets = ['SPY', 'EEM', 'TLT', 'HYG']
    dates = pd.date_range('2021-01-01', periods=n, freq='B')
    rng = np.random.default_rng(99)
    data = {}
    for asset in assets:
        # Geometric random walk
        ret = rng.normal(0.0003, 0.01, size=n)
        prices = 100 * np.exp(np.cumsum(ret))
        data[f'{asset}_close'] = prices
    return pd.DataFrame(data, index=dates)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_analyze_forward_returns_returns_dict():
    """Result is a dict with (asset, horizon) tuple keys."""
    results = _make_results()
    market = _make_market()
    out = analyze_forward_returns(results, market, horizons=[1, 5], assets=['SPY', 'TLT'])

    assert isinstance(out, dict), "Output must be a dict"
    assert len(out) > 0, "Output must be non-empty when data is valid"
    for key in out:
        assert isinstance(key, tuple) and len(key) == 2, "Keys must be (asset, horizon) tuples"
        asset, horizon = key
        assert isinstance(asset, str)
        assert isinstance(horizon, int)


def test_analyze_forward_returns_kw_stat_present():
    """Each result entry has kw_stat and kw_pvalue fields."""
    results = _make_results()
    market = _make_market()
    out = analyze_forward_returns(results, market, horizons=[1, 5, 21], assets=['SPY'])

    for key, val in out.items():
        assert 'kw_stat' in val, f"Missing kw_stat for {key}"
        assert 'kw_pvalue' in val, f"Missing kw_pvalue for {key}"
        assert isinstance(val['kw_stat'], float), "kw_stat must be float"
        assert isinstance(val['kw_pvalue'], float), "kw_pvalue must be float"
        assert 0.0 <= val['kw_pvalue'] <= 1.0, "kw_pvalue must be in [0, 1]"


def test_analyze_forward_returns_no_lookahead():
    """Function does not modify results DataFrame (no lookahead)."""
    results = _make_results()
    market = _make_market()
    original_regime_col = results['regime_name'].copy()
    original_index = results.index.copy()

    analyze_forward_returns(results, market, horizons=[1], assets=['SPY'])

    # Regime assignments must be unchanged
    pd.testing.assert_series_equal(
        results['regime_name'],
        original_regime_col,
        check_names=True,
    )
    pd.testing.assert_index_equal(results.index, original_index)
    # No new columns must have been added to results
    assert list(results.columns) == ['regime_name'], \
        "analyze_forward_returns must not add columns to results"


def test_analyze_forward_returns_handles_missing_assets():
    """Graceful handling when an asset column is missing from market data."""
    results = _make_results()
    # Market data only has SPY — EEM, TLT, HYG are absent
    market = _make_market(assets=['SPY'])

    # Should not raise; missing assets are silently skipped
    out = analyze_forward_returns(results, market, horizons=[1, 5], assets=['SPY', 'EEM', 'TLT'])

    present_assets = {k[0] for k in out}
    assert 'SPY' in present_assets, "SPY should be present"
    assert 'EEM' not in present_assets, "EEM column absent — should be skipped"
    assert 'TLT' not in present_assets, "TLT column absent — should be skipped"


def test_analyze_forward_returns_median_returns_per_regime():
    """median_returns dict has one key per unique regime in results."""
    regimes = ['Low-Vol', 'High-Vol', 'Crisis']
    results = _make_results(n=600, regimes=regimes)
    market = _make_market(n=600)

    out = analyze_forward_returns(results, market, horizons=[5], assets=['SPY'])

    key = ('SPY', 5)
    assert key in out, "Expected (SPY, 5) key in output"
    median_ret = out[key]['median_returns']

    # Every regime that appears in results should have a median return entry
    unique_regimes = set(results['regime_name'].unique())
    for reg in unique_regimes:
        assert reg in median_ret, f"Missing median return for regime '{reg}'"
        assert isinstance(median_ret[reg], float), "Median return must be float"


def test_analyze_forward_returns_none_inputs():
    """Returns empty dict when inputs are None."""
    out = analyze_forward_returns(None, None)
    assert out == {}, "Should return empty dict for None inputs"

    results = _make_results()
    out2 = analyze_forward_returns(results, None)
    assert out2 == {}, "Should return empty dict when market is None"


def test_analyze_forward_returns_n_regimes_field():
    """n_regimes field equals number of unique regimes tested."""
    regimes = ['A', 'B', 'C']
    results = _make_results(n=400, regimes=regimes)
    market = _make_market(n=400)

    out = analyze_forward_returns(results, market, horizons=[1], assets=['SPY'])

    key = ('SPY', 1)
    if key in out:
        assert out[key]['n_regimes'] == 3, "n_regimes should equal number of unique regimes"
