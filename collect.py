"""
Collects VIX (Yahoo), HY Spread + T10Y2Y (FRED), GARCH vol (SPY via arch),
aligns to trading days, saves raw and scaled versions.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from fredapi import Fred
from arch import arch_model
from sklearn.preprocessing import StandardScaler
import joblib
import os

from config import (
    START_DATE, FRED_API_KEY, FEATURES,
    LOG_FEATURES, YIELD_SPREAD_SHIFT, DATA_DIR, MODEL_DIR
)


def collect():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    # --- VIX ---
    vix = yf.download('^VIX', start=START_DATE, progress=False)['Close'].squeeze()
    vix.name = 'vix'

    # --- SPY (for GARCH vol) ---
    spy = yf.download('SPY', start=START_DATE, progress=False)['Close'].squeeze()
    spy_ret = np.log(spy).diff().dropna() * 100   # pct log-returns
    am = arch_model(spy_ret, p=1, q=1, mean='Zero', vol='GARCH', dist='t')
    res = am.fit(disp='off')
    garch_vol = res.conditional_volatility
    garch_vol.name = 'garch_vol'

    # --- FRED -
    fred = Fred(api_key=FRED_API_KEY)
    hy_spread    = fred.get_series('BAMLH0A0HYM2', observation_start=START_DATE)
    yield_spread = fred.get_series('T10Y2Y',       observation_start=START_DATE)
    hy_spread.name    = 'hy_spread'
    yield_spread.name = 'yield_spread'

    # --- Align to VIX trading-day index ---
    market = pd.DataFrame({'vix': vix})
    market['hy_spread']    = hy_spread.reindex(market.index,    method='ffill')
    market['garch_vol']    = garch_vol.reindex(market.index,    method='ffill')
    market['yield_spread'] = yield_spread.reindex(market.index, method='ffill')
    market = market[FEATURES].dropna()

    # --- Log-transform features ---
    log_features = pd.DataFrame(index=market.index)
    for feat in LOG_FEATURES:
        log_features[f'log_{feat}'] = np.log(market[feat])
    log_features['log_yield_spread'] = np.log(market['yield_spread'] + YIELD_SPREAD_SHIFT)

    # --- Scale ---
    scaler = StandardScaler()
    X = pd.DataFrame(
        scaler.fit_transform(log_features),
        columns=log_features.columns,
        index=log_features.index
    )

    market.to_csv(f'{DATA_DIR}/market_data.csv')
    X.to_csv(f'{DATA_DIR}/features_scaled.csv')
    joblib.dump(scaler, f'{MODEL_DIR}/scaler.pkl')

    print(f"Collected {len(market)} days | {market.index[0].date()} to {market.index[-1].date()}")
    print(f"VIX: {market['vix'].min():.1f} - {market['vix'].max():.1f}")
    print(f"HY Spread: {market['hy_spread'].min():.2f} - {market['hy_spread'].max():.2f}")
    print(f"GARCH vol: {market['garch_vol'].min():.2f} - {market['garch_vol'].max():.2f}")
    print(f"Yield spread (T10Y2Y): {market['yield_spread'].min():.2f} - {market['yield_spread'].max():.2f}")

    return market, X


if __name__ == '__main__':
    collect()
