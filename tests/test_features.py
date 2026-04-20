"""Tests for FEAT-01: feature matrix expansion with FRED macro features."""

import numpy as np
import pandas as pd
import pytest

from src.features.features import build_features, CURATED_FEATURES


def test_curated_features_includes_fred_additions():
    """FEAT-01: CURATED_FEATURES list must include the 4 Phase 5 additions."""
    required_additions = {'HY_OAS', 'NFCI', 'yield_curve_slope', 'GLD_trend'}
    assert required_additions.issubset(set(CURATED_FEATURES)), (
        f"Missing Phase 5 features in CURATED_FEATURES: "
        f"{required_additions - set(CURATED_FEATURES)}"
    )


def test_fred_features():
    """FEAT-01: build_features() output must contain the 4 new FRED-derived columns."""
    rng = np.random.default_rng(42)
    n = 1000
    idx = pd.date_range('2010-01-01', periods=n, freq='B')
    # Market columns required by build_features + new FRED columns + GLD_close for GLD_trend
    market = pd.DataFrame({
        'SPY_close':  100 * np.exp(np.cumsum(rng.normal(0, 0.01, n))),
        'TLT_close':  100 * np.exp(np.cumsum(rng.normal(0, 0.008, n))),
        'HYG_close':  100 * np.exp(np.cumsum(rng.normal(0, 0.006, n))),
        'GLD_close':  100 * np.exp(np.cumsum(rng.normal(0, 0.009, n))),
        'QQQ_close':  100 * np.exp(np.cumsum(rng.normal(0, 0.012, n))),
        'IWM_close':  100 * np.exp(np.cumsum(rng.normal(0, 0.011, n))),
        'EEM_close':  100 * np.exp(np.cumsum(rng.normal(0, 0.013, n))),
        'SPY_high':   105 + rng.normal(0, 1, n),
        'SPY_low':     95 + rng.normal(0, 1, n),
        'SPY_open':   100 + rng.normal(0, 1, n),
        'SPY_volume': rng.uniform(1e7, 5e7, n),
        'VIX':        15 + rng.normal(0, 3, n).clip(-10, 20),
        'VIX3M':      16 + rng.normal(0, 2, n).clip(-8, 15),
        'HY_OAS':     4.0 + rng.normal(0, 0.5, n).clip(-2, 3),
        'NFCI':       rng.normal(0, 0.3, n),
        'yield_curve_slope': rng.normal(1.0, 0.5, n),
    }, index=idx)
    features = build_features(market)
    # HY_OAS removed from build_features output (ICE FRED data only goes back to 2023)
    required = {'NFCI', 'yield_curve_slope', 'GLD_trend'}
    missing = required - set(features.columns)
    assert not missing, f"build_features missing FRED features: {missing}"


# NYQUIST: test_fred_features expected to fail until Plan 03 extends build_features with FRED columns.
