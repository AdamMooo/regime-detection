"""PIPE-03: after a run, last row date is today (or most recent business day)."""
import subprocess
import os
import pytest
from datetime import date, timedelta
import pandas as pd
from src.config import DATA_DIR


@pytest.mark.slow
def test_last_row_is_recent_business_day():
    subprocess.run(['python', 'scripts/run.py'], check=True)
    df = pd.read_csv(os.path.join(DATA_DIR, 'regime_results.csv'),
                     index_col=0, parse_dates=True)
    last = df.index[-1].date()
    # Allow up to 5 calendar days (weekend + holiday tolerance)
    assert (date.today() - last) <= timedelta(days=5), (
        f"Last row {last} is stale; today is {date.today()}"
    )
