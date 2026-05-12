"""Collect SPX market data: prices, VIX, WTI shocks."""

import os
import pandas as pd
import yfinance as yf
from src.config import START_DATE, END_DATE, TRAIN_END, SPX_TICKER, WTI_TICKER, VOL_TICKER

def fetch_spx_data() -> pd.DataFrame:
    """Fetch S&P 500, VIX, WTI."""
    print("[1/3] Fetching SPX...")
    spx = yf.download(SPX_TICKER, start=START_DATE, end=END_DATE)[['Close']].rename(columns={'Close': 'spx_price'})
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = [col[0] for col in spx.columns]
    
    print("[2/3] Fetching VIX...")
    vix = yf.download(VOL_TICKER, start=START_DATE, end=END_DATE)[['Close']].rename(columns={'Close': 'vol_index'})
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = [col[0] for col in vix.columns]
    
    print("[3/3] Fetching WTI...")
    wti = yf.download(WTI_TICKER, start=START_DATE, end=END_DATE)[['Close']].rename(columns={'Close': 'wti_price'})
    if isinstance(wti.columns, pd.MultiIndex):
        wti.columns = [col[0] for col in wti.columns]
    wti['wti_shock'] = wti['wti_price'].pct_change()
    
    # Merge and clean
    df = pd.concat([spx, vix[['vol_index']], wti[['wti_shock']]], axis=1, join='outer', sort=True).dropna()
    df.index.name = 'Date'
    
    print(f"\nData shape: {df.shape}")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"\nFirst 5 rows:\n{df.head()}")
    print(f"\nLast 5 rows:\n{df.tail()}")
    print(f"\nSummary stats:\n{df.describe()}")
    
    return df

def save_train_test(df: pd.DataFrame):
    """Save full, train, test."""
    os.makedirs('data/processed', exist_ok=True)
    df.to_csv('data/processed/spx_data.csv')
    train = df.loc[:TRAIN_END]
    test = df.loc[TRAIN_END:]
    train.to_csv('data/processed/train.csv')
    test.to_csv('data/processed/test.csv')
    print(f"\nSaved: {len(df)} total, {len(train)} train, {len(test)} test")

if __name__ == '__main__':
    df = fetch_spx_data()
    save_train_test(df)
