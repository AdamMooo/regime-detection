"""Collect the 4 thesis features: SPY return, VIX, yield slope, NFCI.

Sources:
    spy_ret     -- S&P 500 daily log return (yfinance ^GSPC)
    vol_index   -- VIX level (yfinance ^VIX)
    yield_slope -- 10y minus 2y Treasury spread (FRED T10Y2Y, daily)
    nfci        -- Chicago Fed National Financial Conditions Index (FRED NFCI, weekly -> ffill)

Requires FRED_API_KEY in .env at the project root (free at fred.stlouisfed.org).
"""

import os
import numpy as np
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

from src.config import (
    START_DATE, END_DATE, TRAIN_END,
    SPX_TICKER, VOL_TICKER,
    FRED_YIELD_SERIES, FRED_NFCI_SERIES,
    DATA_DIR,
)

load_dotenv()


def _get_fred_api():
    key = os.getenv('FRED_API_KEY')
    if not key or key == 'your_fred_api_key_here':
        raise EnvironmentError(
            "FRED_API_KEY not set. Add it to .env (free at fred.stlouisfed.org)"
        )
    from fredapi import Fred
    return Fred(api_key=key)


def fetch_and_save_data() -> pd.DataFrame:
    """Fetch all 4 features, align to SPX trading days, save CSV.

    Returns the merged DataFrame.
    """
    fred = _get_fred_api()

    print("[1/4] Fetching SPX...")
    spx = yf.download(SPX_TICKER, start=START_DATE, end=END_DATE, progress=False)[['Close']]
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = [c[0] for c in spx.columns]
    spx = spx.rename(columns={'Close': 'spx_close'})
    spx['spy_ret'] = np.log(spx['spx_close']).diff()

    print("[2/4] Fetching VIX...")
    vix = yf.download(VOL_TICKER, start=START_DATE, end=END_DATE, progress=False)[['Close']]
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = [c[0] for c in vix.columns]
    vix = vix.rename(columns={'Close': 'vol_index'})

    print("[3/4] Fetching yield slope (T10Y2Y) from FRED...")
    raw_yield = fred.get_series(
        FRED_YIELD_SERIES, observation_start=START_DATE, observation_end=END_DATE
    )
    raw_yield.name = 'yield_slope'

    print("[4/4] Fetching NFCI from FRED...")
    raw_nfci = fred.get_series(
        FRED_NFCI_SERIES, observation_start=START_DATE, observation_end=END_DATE
    )
    raw_nfci.name = 'nfci'
    # fred.get_series() indexes NFCI by its reference week (a Friday), not
    # its release date. The Chicago Fed publishes each week's NFCI value
    # the following Friday (~7-day lag) -- shift the index forward by the
    # publication lag so ffill never assigns a value before it was public.
    raw_nfci.index = raw_nfci.index + pd.Timedelta(days=7)

    # Align everything to SPX trading-day index
    idx = spx.index
    yield_daily = raw_yield.reindex(idx, method='ffill')
    nfci_daily  = raw_nfci.reindex(idx, method='ffill')

    df = pd.concat(
        [spx[['spy_ret']], vix[['vol_index']], yield_daily, nfci_daily],
        axis=1,
    ).dropna()
    df.index.name = 'Date'

    print(f"\nFeature matrix: {df.shape}  ({df.index[0].date()} to {df.index[-1].date()})")
    print(df.describe().round(4))

    os.makedirs(os.path.join(DATA_DIR, 'processed'), exist_ok=True)
    full_path  = os.path.join(DATA_DIR, 'processed', 'spx_data.csv')
    train_path = os.path.join(DATA_DIR, 'processed', 'train.csv')
    test_path  = os.path.join(DATA_DIR, 'processed', 'test.csv')

    df.to_csv(full_path)
    df.loc[:TRAIN_END].to_csv(train_path)
    df.loc[TRAIN_END:].to_csv(test_path)

    print(f"\nSaved -> {full_path}  (train: {(df.index <= TRAIN_END).sum()}, "
          f"test: {(df.index > TRAIN_END).sum()})")
    return df


if __name__ == '__main__':
    fetch_and_save_data()
