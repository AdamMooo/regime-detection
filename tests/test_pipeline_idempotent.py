"""PIPE-01/03: two runs produce identical regime_results.csv for deterministic cols."""
import subprocess
import sys
import pytest
import os
import pandas as pd
from src.config import DATA_DIR


@pytest.mark.slow
def test_idempotent_regime_results():
    path = os.path.join(DATA_DIR, 'regime_results.csv')
    subprocess.run([sys.executable, 'scripts/run.py'], check=True)
    df1 = pd.read_csv(path, index_col=0, parse_dates=True)
    subprocess.run([sys.executable, 'scripts/run.py'], check=True)
    df2 = pd.read_csv(path, index_col=0, parse_dates=True)
    for col in ['regime_name', 'regime']:
        pd.testing.assert_series_equal(df1[col], df2[col], check_names=True)
