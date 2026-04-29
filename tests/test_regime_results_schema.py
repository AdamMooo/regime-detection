"""PIPE-03: regime_results.csv schema contract (actual column names, not placeholders)."""
import os
import pytest
import pandas as pd
from src.config import DATA_DIR

REQUIRED = [
    'regime', 'regime_name', 'VIX', 'SPY_close', 'garch_var_95',
    'days_in_regime', 'regime_entropy', 'garch_vol_forecast',
    'blended_vol_forecast', 'transition_score', 'structural_anomaly',
]


def _load():
    path = os.path.join(DATA_DIR, 'regime_results.csv')
    if not os.path.exists(path):
        pytest.skip("regime_results.csv not present — run pipeline first")
    return pd.read_csv(path, index_col=0, parse_dates=True)


def test_required_columns_exist():
    df = _load()
    missing = [c for c in REQUIRED if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


def test_prob_columns_named_by_regime():
    df = _load()
    prob_cols = [c for c in df.columns if c.startswith('prob_') and not c.startswith('prob_Low-Vol_smooth')]
    assert 'prob_Low-Vol' in prob_cols
    assert 'prob_Medium-Vol' in prob_cols
    assert 'prob_High-Vol' in prob_cols


def test_placeholder_columns_are_all_nan():
    df = _load()
    for col in ['blended_vol_forecast', 'transition_score', 'structural_anomaly']:
        assert df[col].isna().all(), f"{col} must be all-NaN in Phase 7"
