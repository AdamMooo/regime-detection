"""Tests for confidence calibration."""

import numpy as np
import pandas as pd
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.signals.signals import _confidence_calibration


def _make_calibration_df(n=1000, perfect=False, seed=42):
    """Create synthetic regime_results with filtered and smoothed probs."""
    rng = np.random.RandomState(seed)
    dates = pd.bdate_range('2020-01-01', periods=n)

    # 3-state filtered probs (random but normalized)
    raw = rng.dirichlet([2, 1, 0.5], size=n)
    names = ['Low-Vol', 'Medium-Vol', 'High-Vol']

    if perfect:
        # Smoothed = filtered (perfect calibration)
        smooth = raw.copy()
    else:
        # Smoothed differs randomly
        smooth = rng.dirichlet([2, 1, 0.5], size=n)

    df = pd.DataFrame(index=dates)
    for i, name in enumerate(names):
        df[f'prob_{name}'] = raw[:, i]
        df[f'smooth_prob_{name}'] = smooth[:, i]

    return df


class TestConfidenceCalibration:

    def test_ece_zero_when_perfectly_calibrated(self):
        """When confidence exactly matches accuracy, ECE should be ~0."""
        # Construct a scenario: 200 samples all with confidence=0.9
        # where exactly 90% have matching argmax (= calibrated)
        n = 200
        dates = pd.bdate_range('2020-01-01', periods=n)
        df = pd.DataFrame(index=dates)

        # 180 samples: filtered and smoothed agree (argmax both state 0)
        # 20 samples:  filtered says state 0, smoothed says state 1
        filt = np.zeros((n, 2))
        smooth = np.zeros((n, 2))

        filt[:, 0] = 0.9   # high confidence on state 0
        filt[:, 1] = 0.1

        smooth[:180, 0] = 0.9  # agree
        smooth[:180, 1] = 0.1
        smooth[180:, 0] = 0.1  # disagree
        smooth[180:, 1] = 0.9

        df['prob_A'] = filt[:, 0]
        df['prob_B'] = filt[:, 1]
        df['smooth_prob_A'] = smooth[:, 0]
        df['smooth_prob_B'] = smooth[:, 1]

        result = _confidence_calibration(df, n_bins=10)
        assert result['available'] is True
        # All 200 samples fall in the 0.85-0.95 bin, accuracy=0.9, confidence=0.9
        # ECE = |0.9 - 0.9| = 0.0
        assert result['ece'] < 0.05

    def test_random_calibration(self):
        """Random smoothed probs should give higher ECE."""
        df = _make_calibration_df(n=2000, perfect=False)
        result = _confidence_calibration(df)

        assert result['available'] is True
        assert isinstance(result['ece'], float)
        assert 0.0 <= result['ece'] <= 1.0

    def test_missing_columns(self):
        """Should return unavailable if no smooth_prob columns."""
        dates = pd.bdate_range('2020-01-01', periods=100)
        df = pd.DataFrame({
            'prob_Low-Vol': np.random.rand(100),
            'prob_High-Vol': 1 - np.random.rand(100),
        }, index=dates)

        result = _confidence_calibration(df)
        assert result['available'] is False

    def test_bins_structure(self):
        """Should return proper bin structure."""
        df = _make_calibration_df(n=500)
        result = _confidence_calibration(df, n_bins=5)

        assert result['available'] is True
        assert len(result['bin_centers']) == 5
        assert len(result['bin_accuracies']) == 5
        assert len(result['bin_counts']) == 5
        assert sum(result['bin_counts']) == result['n_samples']

    def test_interpretation_string(self):
        """Interpretation should contain ECE percentage."""
        df = _make_calibration_df(n=500)
        result = _confidence_calibration(df)

        assert result['available'] is True
        assert 'ECE' in result['interpretation']
