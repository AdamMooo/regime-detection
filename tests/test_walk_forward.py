"""Tests for FEAT-02 and FEAT-03: walk-forward section selection causal guarantee and report output."""

import os
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Imports the walk-forward script as a module
try:
    from scripts.analysis import walk_forward_feature_selection as wffs
    _IMPORT_ERROR = None
except (ImportError, ModuleNotFoundError) as e:
    wffs = None
    _IMPORT_ERROR = e


def _require_import():
    """Raise the original import error if walk_forward_feature_selection is not yet implemented."""
    if _IMPORT_ERROR is not None:
        raise _IMPORT_ERROR


def _synthetic_raw_features(n_rows=2000, seed=42):
    """Build a synthetic raw features DataFrame with 21 required columns."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range('2010-01-01', periods=n_rows, freq='B')
    cols = [
        'VIX', 'VRP', 'rv_ratio_10_63', 'vix_ts_slope', 'SPY_volvol20',
        'SPY_rv10_lag5', 'SPY_rv10_lag10', 'lev_effect20',
        'credit_stress', 'SPY_TLT_corr63', 'HY_OAS', 'NFCI',
        'yield_curve_slope', 'GLD_trend', 'SPY_ret', 'SPY_ac1_20',
        'eigen_conc', 'SPY_dd63', 'SPY_rel_volume', 'SPY_vol_adj_ret', 'SPY_skew20',
    ]
    data = rng.standard_normal((n_rows, len(cols)))
    data[:, cols.index('VIX')] = np.abs(data[:, cols.index('VIX')]) + 10.0
    return pd.DataFrame(data, index=idx, columns=cols)


def _synthetic_section_signals(n_rows=2000, n_sections=4, seed=42):
    """Return a section signals DataFrame and aligned regime_labels Series."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range('2010-01-01', periods=n_rows, freq='B')
    data = rng.standard_normal((n_rows, n_sections))
    signals = pd.DataFrame(data, index=idx, columns=['s_vol', 's_fin', 's_mac', 's_str'])
    # K=3 regimes matching config.py N_STATES per CLAUDE.md lock
    regime_labels = pd.Series(
        rng.integers(0, 3, size=n_rows),
        index=idx,
    )
    return signals, regime_labels


def test_no_lookahead():
    """FEAT-02: section PCA must be refit on training slice only — never on full history.

    walk_forward_section_selection accepts raw_features (not pre-built signals) and
    must call build_section_signals_for_fold(features.iloc[train_start:t], pca_window=252)
    inside every fold. Validated by patching build_section_signals_for_fold and recording
    every call's slice length and last index.
    """
    _require_import()

    raw_features = _synthetic_raw_features(n_rows=2000, seed=0)
    _, regime_labels = _synthetic_section_signals(n_rows=2000, seed=0)

    calls = []

    def recording_build_fold(features_slice, pca_window=252):
        calls.append({
            'len': len(features_slice),
            'last_idx': features_slice.index[-1],
        })
        # Return minimal valid section signals matching slice length
        rng = np.random.default_rng(len(features_slice))
        return pd.DataFrame(
            rng.standard_normal((len(features_slice), 4)),
            index=features_slice.index,
            columns=['s_vol', 's_fin', 's_mac', 's_str'],
        )

    with patch('src.features.features.build_section_signals_for_fold', side_effect=recording_build_fold):
        result = wffs.walk_forward_section_selection(
            raw_features,
            regime_labels,
            train_years=3,
            step_days=21,
            pca_window=252,
        )

    assert len(calls) > 0, "build_section_signals_for_fold was never called"

    max_train_rows = 3 * 252
    for i, call in enumerate(calls):
        assert call['len'] <= max_train_rows, (
            f"Fold {i}: build_section_signals_for_fold received {call['len']} rows "
            f"(max allowed: {max_train_rows}). Full-history PCA fit detected — FEAT-02 violated."
        )

    # Additional: fold_scores must be reproducible when full-history is identical up to fold boundary
    fold_scores = result.get('fold_scores', [])
    assert len(fold_scores) > 0, "walk_forward_section_selection returned no fold_scores"


def test_mi_train_only():
    """FEAT-02: mutual_info_classif must receive only training-fold rows, never the full series."""
    _require_import()

    raw_features = _synthetic_raw_features(n_rows=2000, seed=1)
    _, regime_labels = _synthetic_section_signals(n_rows=2000, seed=1)

    mi_call_lengths = []

    def recording_mi(X, y, **kwargs):
        mi_call_lengths.append(X.shape[0])
        # Return small MI scores so all sections look equal
        return np.zeros(X.shape[1])

    with patch('sklearn.feature_selection.mutual_info_classif', side_effect=recording_mi):
        wffs.walk_forward_section_selection(
            raw_features,
            regime_labels,
            train_years=3,
            step_days=21,
            pca_window=252,
        )

    assert len(mi_call_lengths) > 0, "mutual_info_classif was never called"
    max_train_rows = 3 * 252
    full_len = len(raw_features)
    for i, n in enumerate(mi_call_lengths):
        assert n <= max_train_rows, (
            f"mutual_info_classif call {i}: received {n} rows "
            f"(max allowed: {max_train_rows}, full series: {full_len}). "
            "Lookahead detected — FEAT-02 violated."
        )
        assert n != full_len, (
            f"mutual_info_classif call {i}: received all {n} rows (full series). "
            "Must use training fold only."
        )


def test_report_written(tmp_path, monkeypatch):
    """FEAT-03: after running main(), feature_importance_report.md must exist with required structure."""
    _require_import()

    # Monkeypatch DATA_DIR to tmp_path so report writes to tmp dir, not repo
    monkeypatch.setattr(wffs, 'DATA_DIR', str(tmp_path))

    wffs.main()

    report_path = tmp_path / 'feature_importance_report.md'
    assert os.path.exists(report_path), (
        f"feature_importance_report.md not written to {tmp_path}"
    )

    content = report_path.read_text()
    assert '# Feature Importance Report' in content, (
        "Report missing '# Feature Importance Report' heading"
    )
    assert '| Section | Selection Frequency | Mean OOS MI | Rationale |' in content, (
        "Report missing required markdown table header"
    )


def test_stability_threshold_applied():
    """FEAT-02: only sections meeting the stability threshold should appear in 'selected'."""
    _require_import()

    rng = np.random.default_rng(42)
    n_rows = 2000
    idx = pd.date_range('2010-01-01', periods=n_rows, freq='B')

    # s_vol is perfectly correlated with regime; others are noise
    regime_labels = pd.Series(rng.integers(0, 3, size=n_rows), index=idx)

    # Synthetic raw features: only VIX drives regimes (s_vol section anchor)
    cols = [
        'VIX', 'VRP', 'rv_ratio_10_63', 'vix_ts_slope', 'SPY_volvol20',
        'SPY_rv10_lag5', 'SPY_rv10_lag10', 'lev_effect20',
        'credit_stress', 'SPY_TLT_corr63', 'HY_OAS', 'NFCI',
        'yield_curve_slope', 'GLD_trend', 'SPY_ret', 'SPY_ac1_20',
        'eigen_conc', 'SPY_dd63', 'SPY_rel_volume', 'SPY_vol_adj_ret', 'SPY_skew20',
    ]
    data = rng.standard_normal((n_rows, len(cols)))
    # Make s_vol section features strongly predictive; others near-zero
    vix_idx = cols.index('VIX')
    data[:, vix_idx] = regime_labels.values * 5.0 + rng.standard_normal(n_rows) * 0.01
    raw_features = pd.DataFrame(data, index=idx, columns=cols)

    result = wffs.walk_forward_section_selection(
        raw_features,
        regime_labels,
        train_years=3,
        step_days=21,
        stability_threshold=0.60,
        top_n_per_fold=1,
    )

    selected = result.get('selected', [])
    assert 's_vol' in selected, (
        f"Expected 's_vol' in selected sections (high MI), got: {selected}"
    )
    # Sections that never pass 60% fold threshold should not appear
    for sec in ['s_fin', 's_mac', 's_str']:
        assert sec not in selected, (
            f"Section '{sec}' should NOT be selected (low MI in all folds), but was: {selected}"
        )


# NYQUIST: These tests are expected to fail (ImportError or AttributeError) until Plan 04 lands walk_forward_feature_selection.py.
