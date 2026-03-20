"""Shared fixtures for regime-detection tests."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def rng():
    """Deterministic random state."""
    return np.random.RandomState(42)


@pytest.fixture
def synthetic_array(rng):
    """500x3 array with known statistical properties."""
    return rng.randn(500, 3) * np.array([1, 2, 3]) + np.array([10, 20, 30])


@pytest.fixture
def synthetic_features(rng):
    """DataFrame mimicking features_transformed.csv (500 rows, 5 cols)."""
    dates = pd.bdate_range('2020-01-01', periods=500)
    data = rng.randn(500, 5) * np.array([1, 2, 0.5, 3, 1.5])
    cols = ['VIX', 'VRP', 'rv_ratio_10_63', 'SPY_ret', 'credit_stress']
    return pd.DataFrame(data, index=dates, columns=cols)
