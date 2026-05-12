import yfinance as yf
import pandas as pd
from fredapi import Fred
import os
from datetime import datetime

# API key for FRED - set in environment or here
FRED_API_KEY = os.getenv('FRED_API_KEY', 'your_fred_api_key_here')  # Replace with actual key

fred = Fred(api_key=FRED_API_KEY)

def download_data():
    # Download XEG.TO data
    xeg = yf.download('XEG.TO', start='2015-01-01', end='2026-12-31')
    xeg = xeg[['Close', 'Volume']].rename(columns={'Close': 'xeg_close', 'Volume': 'xeg_volume'})

    # Calculate WTI shocks (daily % change in WTI price)
    wti = yf.download('CL=F', start='2015-01-01', end='2026-12-31')[['Close']].rename(columns={'Close': 'wti_close'})
    wti['wti_shock'] = wti['wti_close'].pct_change()

    # TSX vol - use VIX as proxy or find TSX vol index, for now use VIX
    tsx_vol = fred.get_series('VIXCLS', start='2015-01-01', end='2026-12-31').rename('tsx_vol')

    # BOC spread - Bank of Canada overnight rate vs 10-year yield
    boc_overnight = fred.get_series('IRSTCB01CAM156N', start='2015-01-01', end='2026-12-31').rename('boc_overnight')
    boc_10y = fred.get_series('IRLTLT01CAM156N', start='2015-01-01', end='2026-12-31').rename('boc_10y')
    boc_spread = boc_10y - boc_overnight

    # Combine all
    df = pd.concat([xeg, wti[['wti_shock']], tsx_vol, boc_spread], axis=1).dropna()

    # Save to CSV
    os.makedirs('data/processed', exist_ok=True)
    df.to_csv('data/processed/xeg_macros.csv')

    print(f"Data downloaded and saved. Shape: {df.shape}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

if __name__ == '__main__':
    download_data()