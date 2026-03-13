"""
Feature engineering for PCA -> HMM -> SV pipeline.

Computes:
  - Daily log returns  (SPY, QQQ, IWM, EEM, TLT, HYG, GLD)
  - Realized-volatility proxies  (rolling std, Parkinson, Garman-Klass)
  - Implied volatility  (VIX)
  - Volatility risk premium  (VIX - realized vol)
  - SPY momentum  (63d) and max drawdown  (63d)
  - Cross-asset: credit stress, small-cap relative strength, gold flow, dispersion
  - Standardization via StandardScaler
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import os

from config import (
    TICKERS, SHORT_WINDOW, MED_WINDOW, LONG_WINDOW,
    DATA_DIR, MODEL_DIR,
)


# ── Volatility estimators ──────────────────────────────────────────

def _realized_vol(returns: pd.Series, window: int) -> pd.Series:
    """Annualized rolling standard deviation of returns."""
    return returns.rolling(window).std() * np.sqrt(252)


def _parkinson_vol(high: pd.Series, low: pd.Series, window: int) -> pd.Series:
    """Parkinson (1980) high-low volatility estimator, rolling."""
    hl2 = (np.log(high / low)) ** 2 / (4 * np.log(2))
    return np.sqrt(hl2.rolling(window).mean() * 252)


def _garman_klass_vol(
    open_: pd.Series, high: pd.Series,
    low: pd.Series, close: pd.Series,
    window: int,
) -> pd.Series:
    """Garman-Klass (1980) OHLC volatility estimator, rolling."""
    hl2 = 0.5 * (np.log(high / low)) ** 2
    co2 = (2 * np.log(2) - 1) * (np.log(close / open_)) ** 2
    gk  = hl2 - co2
    return np.sqrt(gk.rolling(window).mean().clip(lower=0) * 252)


# ── Feature builder ────────────────────────────────────────────────

def build_features(market: pd.DataFrame) -> pd.DataFrame:
    """
    Build feature matrix from raw market data.

    Parameters
    ----------
    market : DataFrame with columns like SPY_close, SPY_high, ..., VIX,
             yield_slope, hy_spread

    Returns
    -------
    features : DataFrame (T x n_features), warm-up NaN rows dropped
    """
    f = pd.DataFrame(index=market.index)

    # 1. Daily log returns for each ticker
    for ticker in TICKERS:
        col = f'{ticker}_close'
        if col in market.columns:
            f[f'{ticker}_ret'] = np.log(market[col] / market[col].shift(1))

    # 2. Realized volatility proxies (SPY)
    spy_ret = f.get('SPY_ret')
    if spy_ret is not None:
        f['SPY_rv10'] = _realized_vol(spy_ret, SHORT_WINDOW)
        f['SPY_rv20'] = _realized_vol(spy_ret, MED_WINDOW)

    # 3. Parkinson vol (SPY, 10d)
    if 'SPY_high' in market.columns and 'SPY_low' in market.columns:
        f['SPY_parkinson10'] = _parkinson_vol(
            market['SPY_high'], market['SPY_low'], SHORT_WINDOW,
        )

    # 4. Garman-Klass vol (SPY, 10d)
    if all(c in market.columns for c in ['SPY_open', 'SPY_high', 'SPY_low', 'SPY_close']):
        f['SPY_gk10'] = _garman_klass_vol(
            market['SPY_open'], market['SPY_high'],
            market['SPY_low'],  market['SPY_close'],
            SHORT_WINDOW,
        )

    # 5. Implied volatility (VIX level)
    if 'VIX' in market.columns:
        f['VIX'] = market['VIX']

    # 6. Volatility risk premium (VIX - realized, in vol points)
    if 'VIX' in market.columns and 'SPY_rv10' in f.columns:
        # VIX is in annualized % terms; rv10 is annualized fraction
        f['VRP'] = market['VIX'] - f['SPY_rv10'] * 100

    # 7. Momentum (63d cumulative return of SPY)
    if 'SPY_close' in market.columns:
        f['SPY_mom63'] = market['SPY_close'].pct_change(LONG_WINDOW)

    # 8. Max drawdown (63d rolling) of SPY
    if 'SPY_close' in market.columns:
        rolling_max = market['SPY_close'].rolling(LONG_WINDOW).max()
        f['SPY_dd63'] = market['SPY_close'] / rolling_max - 1

    # ── Cross-asset features ───────────────────────────────────────

    # 9. Credit stress: HYG return minus TLT return (20d rolling mean)
    #    Negative = credit widening / flight-to-quality
    spy_ret = f.get('SPY_ret')
    tlt_ret = f.get('TLT_ret')
    hyg_ret = f.get('HYG_ret')
    if hyg_ret is not None and tlt_ret is not None:
        f['credit_stress'] = (hyg_ret - tlt_ret).rolling(MED_WINDOW).mean()

    # 11. Small-cap vs large-cap relative strength (IWM/SPY, 20d)
    #     Falls when risk appetite drops (small caps sell first)
    if 'IWM_close' in market.columns and 'SPY_close' in market.columns:
        iwm_spy = market['IWM_close'] / market['SPY_close']
        f['IWM_SPY_rel'] = iwm_spy.pct_change(MED_WINDOW)

    # 12. Gold flight-to-safety (GLD return vs SPY return, 20d)
    #     Positive = gold outperforming = risk-off
    gld_ret = f.get('GLD_ret')
    if gld_ret is not None and spy_ret is not None:
        f['gold_flow'] = (gld_ret - spy_ret).rolling(MED_WINDOW).mean()

    # 13. Cross-asset dispersion (rolling std of returns across all tickers, 10d)
    #     High dispersion = regime transition / disagreement across markets
    ret_cols = [c for c in f.columns if c.endswith('_ret')]
    if len(ret_cols) >= 3:
        f['xasset_disp'] = f[ret_cols].std(axis=1).rolling(SHORT_WINDOW).mean()

    # Drop warm-up NaN rows
    f = f.dropna()

    return f


# ── Standardization ────────────────────────────────────────────────

def standardize(features: pd.DataFrame, scaler=None, fit=True):
    """
    Z-score standardize features.

    Returns
    -------
    X_scaled : ndarray (T x n_features)
    scaler   : fitted StandardScaler
    """
    if scaler is None:
        scaler = StandardScaler()
    if fit:
        X = scaler.fit_transform(features.values)
    else:
        X = scaler.transform(features.values)
    return X, scaler


# ── Convenience: build + scale + save ──────────────────────────────

def prepare_features(market=None):
    """
    Full feature pipeline:  build -> standardize -> save.
    If *market* is None, loads from DATA_DIR/market_data.csv.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    if market is None:
        market = pd.read_csv(
            os.path.join(DATA_DIR, 'market_data.csv'),
            index_col=0, parse_dates=True,
        )

    features = build_features(market)
    X_scaled, scaler = standardize(features)

    # Save raw features, scaled features, scaler
    features.to_csv(os.path.join(DATA_DIR, 'features_raw.csv'))
    pd.DataFrame(
        X_scaled, columns=features.columns, index=features.index,
    ).to_csv(os.path.join(DATA_DIR, 'features_scaled.csv'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler.pkl'))

    print(f"Features: {features.shape[1]} indicators x {features.shape[0]} days")
    print(f"  Columns: {list(features.columns)}")

    return features, X_scaled, scaler


if __name__ == '__main__':
    prepare_features()
