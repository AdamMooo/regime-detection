"""health_check.py — verify regime_results.csv freshness; prints PASS/FAIL.

Exit 0 on PASS, 1 on FAIL. Suitable for a cron post-check or monitoring poll.
"""
import os
import sys
from datetime import date, timedelta

import pandas as pd

from src.config import DATA_DIR

MAX_STALENESS_DAYS = 5  # ~3 trading days + weekend tolerance


def main() -> int:
    path = os.path.join(DATA_DIR, 'regime_results.csv')
    if not os.path.exists(path):
        print('FAIL: regime_results.csv not found at', path)
        return 1
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
    except Exception as e:
        print(f'FAIL: could not read regime_results.csv ({e})')
        return 1
    if len(df) == 0:
        print('FAIL: regime_results.csv is empty')
        return 1
    last_ts = df.index[-1]
    last_date = last_ts.date() if hasattr(last_ts, 'date') else last_ts
    today = date.today()
    staleness = (today - last_date).days
    if staleness > MAX_STALENESS_DAYS:
        print(f'FAIL: regime_results.csv last updated {last_date} ({staleness} days ago)')
        return 1
    print(f'PASS: regime_results.csv current as of {last_date}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
