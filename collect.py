"""
Data collection: OHLCV from yfinance, macro series from FRED.
Aligns everything to SPY's trading-day index and saves raw data.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from fredapi import Fred
import os

from config import (
    START_DATE, END_DATE, FRED_API_KEY,
    TICKERS, VIX_TICKER, FRED_SERIES, DATA_DIR,
)


def collect():
    os.makedirs(DATA_DIR, exist_ok=True)

    # --- Download OHLCV per ticker ---
    print("Downloading OHLCV data...")
    ohlcv = {}
    for ticker in TICKERS:
        df = yf.download(
            ticker, start=START_DATE, end=END_DATE,
            auto_adjust=True, progress=False,
        )
        # Ensure columns are plain strings (not MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        ohlcv[ticker] = df
        print(f"  {ticker}: {len(df)} rows")

    # --- VIX ---
    print("Downloading VIX...")
    vix_df = yf.download(VIX_TICKER, start=START_DATE, end=END_DATE, progress=False)
    if isinstance(vix_df.columns, pd.MultiIndex):
        vix_df.columns = vix_df.columns.droplevel(1)
    vix_close = vix_df['Close'].squeeze()

    # --- FRED ---
    print("Downloading FRED data...")
    fred = Fred(api_key=FRED_API_KEY)
    fred_data = {}
    for series_id, col_name in FRED_SERIES.items():
        fred_data[col_name] = fred.get_series(series_id, observation_start=START_DATE)

    # --- Build aligned DataFrame on SPY trading days ---
    ref_index = ohlcv['SPY'].index
    if not isinstance(ref_index, pd.DatetimeIndex):
        ref_index = pd.to_datetime(ref_index)

    market = pd.DataFrame(index=ref_index)

    for ticker in TICKERS:
        df = ohlcv[ticker]
        for field in ['Close', 'High', 'Low', 'Open']:
            series = df[field].squeeze()
            market[f'{ticker}_{field.lower()}'] = series.reindex(ref_index, method='ffill')
        if ticker == 'SPY':
            vol_series = df['Volume'].squeeze()
            market['SPY_volume'] = vol_series.reindex(ref_index, method='ffill')

    # VIX close
    market['VIX'] = vix_close.reindex(ref_index, method='ffill')

    # FRED (forward-fill to trading days)
    for col_name, series in fred_data.items():
        market[col_name] = series.reindex(ref_index, method='ffill')

    market = market.dropna()

    # --- Save ---
    market.to_csv(os.path.join(DATA_DIR, 'market_data.csv'))

    print(f"\nCollected {len(market)} trading days  "
          f"{market.index[0].date()} -> {market.index[-1].date()}")
    print(f"  Tickers : {TICKERS}")
    print(f"  VIX     : {market['VIX'].min():.1f} - {market['VIX'].max():.1f}")
    for col in FRED_SERIES.values():
        if col in market.columns:
            print(f"  {col:10s}: {market[col].min():.2f} - {market[col].max():.2f}")

    return market


if __name__ == '__main__':
    collect()
