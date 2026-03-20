"""Tests for out-of-sample validation metrics."""

import numpy as np
import pandas as pd
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from signals import _oos_validation


def _make_results(n=500, agreement_frac=0.7, seed=42):
    """Create a synthetic regime_results DataFrame with IS and OOS labels."""
    rng = np.random.RandomState(seed)
    dates = pd.bdate_range('2020-01-01', periods=n)

    regimes = rng.choice(['Low-Vol', 'Medium-Vol', 'High-Vol'], size=n, p=[0.5, 0.3, 0.2])

    # OOS labels: agree with IS labels `agreement_frac` of the time
    oos_regimes = regimes.copy()
    n_flip = int(n * (1 - agreement_frac))
    flip_idx = rng.choice(n, size=n_flip, replace=False)
    all_names = ['Low-Vol', 'Medium-Vol', 'High-Vol']
    for i in flip_idx:
        others = [r for r in all_names if r != regimes[i]]
        oos_regimes[i] = rng.choice(others)

    # SPY close: random walk
    spy_close = 400 * np.exp(np.cumsum(rng.randn(n) * 0.01))

    df = pd.DataFrame({
        'SPY_close': spy_close,
        'VIX': 15 + rng.randn(n) * 3,
        'regime_name': regimes,
        'regime_name_oos': oos_regimes,
        'is_oos': True,
    }, index=dates)

    return df


class TestOOSValidation:

    def test_agreement_rate_correct(self):
        """Agreement rate should match the known fraction."""
        df = _make_results(n=1000, agreement_frac=0.75)
        result = _oos_validation(df)

        assert result['available'] is True
        # Should be approximately 0.75 (stochastic, so allow tolerance)
        assert 0.70 < result['agreement_rate'] < 0.80

    def test_missing_oos_columns(self):
        """Graceful fallback when no OOS data exists."""
        dates = pd.bdate_range('2020-01-01', periods=100)
        df = pd.DataFrame({
            'SPY_close': np.random.randn(100).cumsum() + 400,
            'regime_name': 'Low-Vol',
        }, index=dates)

        result = _oos_validation(df)
        assert result['available'] is False

    def test_too_few_oos_rows(self):
        """Should report unavailable if fewer than 50 OOS rows."""
        df = _make_results(n=30)
        result = _oos_validation(df)
        assert result['available'] is False

    def test_oos_separation_runs(self):
        """OOS separation test should produce a p-value."""
        df = _make_results(n=500, agreement_frac=0.8)
        result = _oos_validation(df)

        assert result['available'] is True
        assert 'oos_separation_pvalue' in result
        assert isinstance(result['oos_separation_pvalue'], float)

    def test_per_regime_agreement(self):
        """Per-regime agreement should be reported for each regime."""
        df = _make_results(n=500, agreement_frac=0.7)
        result = _oos_validation(df)

        per_r = result['per_regime_agreement']
        assert len(per_r) > 0
        for r, a in per_r.items():
            assert 0.0 <= a <= 1.0
