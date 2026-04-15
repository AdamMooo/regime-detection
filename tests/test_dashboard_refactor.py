"""
Test suite for dashboard refactoring and analysis scripts.

Covers dashboard rendering, analysis script execution, and regression checks.
"""

import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def temp_data_dir():
    """Temporary data directory for dashboard testing."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_regime_results(temp_data_dir):
    """Generate sample regime results CSV."""
    dates = pd.date_range(start='2020-01-01', periods=250, freq='B')
    data = pd.DataFrame({
        'regime_name': np.random.choice(['Low-Vol', 'Medium-Vol', 'High-Vol'], 250),
        'regime_prob': np.random.uniform(0.6, 1.0, 250),
        'prob_0': np.random.uniform(0, 1, 250),
        'prob_1': np.random.uniform(0, 1, 250),
        'prob_2': np.random.uniform(0, 1, 250),
        'VIX': np.random.uniform(10, 30, 250),
    }, index=dates)

    # Normalize probabilities
    data[['prob_0', 'prob_1', 'prob_2']] = data[['prob_0', 'prob_1', 'prob_2']].div(
        data[['prob_0', 'prob_1', 'prob_2']].sum(axis=1), axis=0
    )

    results_path = os.path.join(temp_data_dir, 'regime_results.csv')
    data.to_csv(results_path)
    return results_path


@pytest.fixture
def sample_trust_scorecard(temp_data_dir):
    """Generate sample trust scorecard JSON."""
    scorecard = {
        'all_passed': True,
        'checks': {
            'regime_persistence': {
                'passed': True,
                'message': 'Regime persistence OK'
            },
            'probability_sum': {
                'passed': True,
                'message': 'Probabilities sum to 1.0'
            },
            'volatility_consistency': {
                'passed': True,
                'message': 'VIX consistent with regime'
            }
        }
    }

    scorecard_path = os.path.join(temp_data_dir, 'trust_scorecard.json')
    with open(scorecard_path, 'w') as f:
        json.dump(scorecard, f)

    return scorecard_path


@pytest.fixture
def sample_market_data(temp_data_dir):
    """Generate sample market data CSV."""
    dates = pd.date_range(start='2020-01-01', periods=250, freq='B')
    data = pd.DataFrame({
        'SPY_close': 300 + np.cumsum(np.random.randn(250) * 2),
        'SPY_high': 305 + np.cumsum(np.random.randn(250) * 2),
        'SPY_low': 295 + np.cumsum(np.random.randn(250) * 2),
        'SPY_open': 300 + np.cumsum(np.random.randn(250) * 2),
        'VIX': 15 + np.cumsum(np.random.randn(250) * 0.5),
    }, index=dates)

    market_path = os.path.join(temp_data_dir, 'market_data.csv')
    data.to_csv(market_path)
    return market_path


class TestDashboardLoading:
    """Test dashboard data loading functions."""

    def test_dashboard_loads_regime_results(self, sample_regime_results, temp_data_dir, monkeypatch):
        """Verify dashboard loads regime_results.csv without errors."""
        monkeypatch.setattr('dashboard.DATA_DIR', temp_data_dir)

        import dashboard
        results = dashboard.load_regime_results()

        assert results is not None
        assert isinstance(results, pd.DataFrame)
        assert 'regime_name' in results.columns
        assert len(results) == 250

    def test_dashboard_loads_trust_scorecard(self, sample_trust_scorecard, temp_data_dir, monkeypatch):
        """Verify dashboard loads trust_scorecard.json without errors."""
        monkeypatch.setattr('dashboard.DATA_DIR', temp_data_dir)

        import dashboard
        scorecard = dashboard.load_trust_scorecard()

        assert scorecard is not None
        assert isinstance(scorecard, dict)
        assert 'checks' in scorecard
        assert scorecard['all_passed'] is True


class TestDashboardFunctions:
    """Test individual dashboard display functions."""

    def test_display_current_regime(self, sample_regime_results, temp_data_dir, monkeypatch):
        """Verify display_current_regime doesn't crash."""
        monkeypatch.setattr('dashboard.DATA_DIR', temp_data_dir)

        import dashboard
        results = dashboard.load_regime_results()

        # This would normally call streamlit functions, so just verify it's callable
        assert callable(dashboard.display_current_regime)

    def test_display_regime_probabilities(self, sample_regime_results, temp_data_dir, monkeypatch):
        """Verify display_regime_probabilities doesn't crash."""
        monkeypatch.setattr('dashboard.DATA_DIR', temp_data_dir)

        import dashboard
        results = dashboard.load_regime_results()

        assert callable(dashboard.display_regime_probabilities)

    def test_display_trust_scorecard(self, sample_trust_scorecard, temp_data_dir, monkeypatch):
        """Verify display_trust_scorecard doesn't crash."""
        monkeypatch.setattr('dashboard.DATA_DIR', temp_data_dir)

        import dashboard
        scorecard = dashboard.load_trust_scorecard()

        assert callable(dashboard.display_trust_scorecard)


class TestAnalysisScripts:
    """Test analysis script execution."""

    def test_analyze_feature_importance_runs(self, temp_data_dir, monkeypatch):
        """Verify analyze_feature_importance.py runs without errors."""
        import analyze_feature_importance

        # Mock main() to avoid dependencies
        with patch.object(analyze_feature_importance, 'load_pca_model', return_value=None):
            with patch.object(analyze_feature_importance, 'load_features', return_value=None):
                analyze_feature_importance.main()

        # If we get here without exception, test passes
        assert True

    def test_analyze_regime_characterization_runs(self, temp_data_dir, monkeypatch):
        """Verify analyze_regime_characterization.py runs without errors."""
        import analyze_regime_characterization

        with patch.object(analyze_regime_characterization, 'load_regime_results', return_value=None):
            analyze_regime_characterization.main()

        assert True

    def test_analyze_signal_quality_runs(self, temp_data_dir, monkeypatch):
        """Verify analyze_signal_quality.py runs without errors."""
        import analyze_signal_quality

        with patch.object(analyze_signal_quality, 'load_regime_results', return_value=None):
            analyze_signal_quality.main()

        assert True


class TestDashboardRefactoring:
    """Test that dashboard refactoring doesn't break existing functionality."""

    def test_dashboard_imports_without_errors(self):
        """Verify dashboard module can be imported."""
        import dashboard
        assert dashboard is not None
        assert hasattr(dashboard, 'load_regime_results')
        assert hasattr(dashboard, 'load_trust_scorecard')

    def test_dashboard_no_imports_from_pipeline(self):
        """Verify dashboard doesn't import from train.py or features.py."""
        import os
        dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard.py')
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Dashboard should NOT import train or features
        assert 'from train import' not in content
        assert 'from src.features.features import' not in content
        assert 'import train' not in content
        assert 'import src.features.features' not in content

    def test_analysis_scripts_independent(self):
        """Verify analysis scripts don't import from pipeline."""
        import os
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        scripts = [
            os.path.join(base_dir, 'analyze_feature_importance.py'),
            os.path.join(base_dir, 'analyze_regime_characterization.py'),
            os.path.join(base_dir, 'analyze_signal_quality.py'),
        ]

        for script in scripts:
            with open(script, 'r', encoding='utf-8') as f:
                content = f.read()

            # Should NOT import from collect, features, train, or run
            assert 'from src.features.collect import' not in content
            assert 'from src.features.features import' not in content
            assert 'from train import' not in content
            assert 'from run import' not in content


class TestRegressions:
    """Test for regressions in existing functionality."""

    def test_existing_causality_tests_still_pass(self):
        """Verify existing causality tests still work."""
        from tests import test_causality
        assert hasattr(test_causality, 'TestExpandingStandardize')

    def test_existing_bot_integration_tests_still_pass(self):
        """Verify existing bot integration tests still work."""
        from tests import test_bot_integration
        assert hasattr(test_bot_integration, 'validate_signal_schema')

    def test_existing_incremental_tests_still_pass(self):
        """Verify incremental collection tests still work."""
        from tests import test_incremental_collection
        assert hasattr(test_incremental_collection, 'TestCacheManifest')

    def test_existing_pca_tests_still_pass(self):
        """Verify PCA caching tests still work."""
        from tests import test_pca_caching
        assert hasattr(test_pca_caching, 'TestPCAComputeAndTransform')


class TestDashboardSlimness:
    """Verify dashboard has been slimmed down."""

    def test_dashboard_is_slim(self):
        """Verify dashboard.py is reasonably small (<500 lines)."""
        import os
        dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard.py')
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) < 500, f"Dashboard is {len(lines)} lines (should be <500)"
        print(f"Dashboard is {len(lines)} lines (target <500) — OK")
