"""Tests for FEAT-01: sectioned feature signal construction (build_section_signals)."""

import numpy as np
import pandas as pd
import pytest

try:
    from src.features.features import build_section_signals, SECTION_MAP, SECTION_ANCHORS
    _IMPORT_ERROR = None
except ImportError as e:
    build_section_signals = None
    SECTION_MAP = None
    SECTION_ANCHORS = None
    _IMPORT_ERROR = e


def _require_import():
    """Raise ImportError if build_section_signals is not yet implemented."""
    if _IMPORT_ERROR is not None:
        raise _IMPORT_ERROR


def _synthetic_feature_frame():
    """Build a deterministic DataFrame with 500 rows covering all section features."""
    rng = np.random.default_rng(42)
    n = 500
    idx = pd.date_range('2018-01-01', periods=n, freq='B')
    cols = [
        # s_vol
        'VIX', 'VRP', 'rv_ratio_10_63', 'vix_ts_slope', 'SPY_volvol20',
        'SPY_rv10_lag5', 'SPY_rv10_lag10', 'SPY_skew20',
        # s_fin
        'credit_stress', 'SPY_TLT_corr63', 'HY_OAS', 'NFCI', 'eigen_conc', 'SPY_dd63',
        # s_mac
        'yield_curve_slope', 'GLD_trend',
        # s_str
        'lev_effect20', 'SPY_ac1_20', 'SPY_vol_adj_ret', 'SPY_rel_volume',
        'amihud_illiq20', 'roll_spread20',
    ]
    data = rng.standard_normal((n, len(cols)))
    # Make VIX always positive (realistic)
    vix_idx = cols.index('VIX')
    data[:, vix_idx] = np.abs(data[:, vix_idx]) + 10.0
    # Make amihud_illiq20 always positive (it's |r|/volume by construction)
    ami_idx = cols.index('amihud_illiq20')
    data[:, ami_idx] = np.abs(data[:, ami_idx]) + 0.01
    return pd.DataFrame(data, index=idx, columns=cols)


def test_build_section_signals_returns_3_columns():
    """FEAT-01: build_section_signals must return DataFrame with exactly 3 section columns.
    s_str removed — microstructure requires tick data (walk-forward MI freq=0.26, below threshold).
    """
    _require_import()
    features = _synthetic_feature_frame()
    result = build_section_signals(features)
    assert set(result.columns) == {'s_vol', 's_fin', 's_mac'}, (
        f"Expected exactly {{'s_vol', 's_fin', 's_mac'}}, got {set(result.columns)}"
    )


def test_build_section_signals_sign_anchored_to_vix():
    """FEAT-01: s_vol signal must be positively correlated with VIX (sign anchor enforced)."""
    _require_import()
    features = _synthetic_feature_frame()
    result = build_section_signals(features)
    corr = result['s_vol'].corr(features['VIX'])
    assert corr > 0, (
        f"s_vol signal must be positively correlated with VIX; got corr={corr:.4f}"
    )


def test_build_section_signals_causal_pca_window():
    """FEAT-01: build_section_signals must not reference data beyond the last input row (no lookahead)."""
    _require_import()
    rng = np.random.default_rng(99)
    n = 500
    idx = pd.date_range('2018-01-01', periods=n, freq='B')
    cols = [
        'VIX', 'VRP', 'rv_ratio_10_63', 'vix_ts_slope', 'SPY_volvol20',
        'SPY_rv10_lag5', 'SPY_rv10_lag10', 'SPY_skew20',
        'credit_stress', 'SPY_TLT_corr63', 'HY_OAS', 'NFCI', 'eigen_conc', 'SPY_dd63',
        'yield_curve_slope', 'GLD_trend',
        'lev_effect20', 'SPY_ac1_20', 'SPY_vol_adj_ret', 'SPY_rel_volume',
        'amihud_illiq20', 'roll_spread20',
    ]
    data = rng.standard_normal((n, len(cols)))
    data[:, cols.index('VIX')] = np.abs(data[:, cols.index('VIX')]) + 10.0
    data[:, cols.index('amihud_illiq20')] = np.abs(data[:, cols.index('amihud_illiq20')]) + 0.01

    f1 = pd.DataFrame(data.copy(), index=idx, columns=cols)
    f2 = pd.DataFrame(data.copy(), index=idx, columns=cols)
    # Mutate only the last row in f2 — prior rows [0:499] remain identical
    f2.iloc[499] = f2.iloc[499] * 100.0 + 50.0

    result1 = build_section_signals(f1, pca_window=252)
    result2 = build_section_signals(f2, pca_window=252)

    # All rows before the trailing row must be identical across both runs
    assert np.allclose(
        result1.iloc[:499].values,
        result2.iloc[:499].values,
        equal_nan=True,
    ), "build_section_signals leaked future data: prior rows differ when trailing row changed"


def test_build_section_signals_single_feature_section_passthrough():
    """FEAT-01: if a section has only one available feature, signal must equal that feature (no PCA)."""
    _require_import()
    rng = np.random.default_rng(7)
    n = 300
    idx = pd.date_range('2020-01-01', periods=n, freq='B')

    # For each active section, keep only the anchor column — exercises single-feature passthrough
    # s_vol: VIX, s_fin: HY_OAS, s_mac: yield_curve_slope
    single_cols = {
        'VIX': 's_vol',
        'HY_OAS': 's_fin',
        'yield_curve_slope': 's_mac',
    }
    data = rng.standard_normal((n, len(single_cols)))
    col_names = list(single_cols.keys())
    data[:, col_names.index('VIX')] = np.abs(data[:, col_names.index('VIX')]) + 10.0
    features = pd.DataFrame(data, index=idx, columns=col_names)

    result = build_section_signals(features, pca_window=252)

    for feat_col, signal_col in single_cols.items():
        feat_series = features[feat_col]
        sig_series = result[signal_col]
        # With a single feature, signal should be linearly proportional to the feature
        pd.testing.assert_series_equal(
            sig_series.reset_index(drop=True),
            feat_series.reset_index(drop=True),
            check_names=False,
            rtol=1e-6,
            check_exact=False,
        )


# NYQUIST: These tests are expected to fail (ImportError) until Plan 03 lands build_section_signals.
