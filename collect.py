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
    TICKERS, VIX_TICKER, VIX3M_TICKER, VVIX_TICKER,
    FRED_SERIES, DATA_DIR,
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
        assert df is not None, f"yf.download returned None for {ticker}"
        # Ensure columns are plain strings (not MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        ohlcv[ticker] = df
        print(f"  {ticker}: {len(df)} rows")

    # --- VIX / VIX3M / VVIX ---
    print("Downloading VIX family...")
    vol_tickers = {
        'VIX':   VIX_TICKER,
        'VIX3M': VIX3M_TICKER,
        'VVIX':  VVIX_TICKER,
    }
    vol_series: dict[str, pd.Series] = {}
    for label, sym in vol_tickers.items():
        raw = yf.download(sym, start=START_DATE, end=END_DATE, progress=False)
        if raw is None or raw.empty:
            print(f"  {label} ({sym}): not available, skipping")
            continue
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.droplevel(1)
        vol_series[label] = pd.Series(raw['Close'].squeeze())
        print(f"  {label}: {len(raw)} rows")

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
            spy_vol = pd.Series(df['Volume'].squeeze())
            market['SPY_volume'] = spy_vol.reindex(ref_index, method='ffill')

    # VIX family (VIX, VIX3M, VVIX)
    for label, s in vol_series.items():
        market[label] = pd.Series(s).reindex(ref_index, method='ffill')

    # FRED (forward-fill to trading days)
    for col_name, series in fred_data.items():
        market[col_name] = series.reindex(ref_index, method='ffill')

    market = market.dropna()

    assert len(market) >= 252, (
        f"Insufficient data after alignment: {len(market)} trading days "
        f"(need >= 252). Check date range or data sources."
    )

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
