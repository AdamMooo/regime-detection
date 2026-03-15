"""
Feature engineering for PCA -> HMM -> SV pipeline.

Computes:
  - Daily log returns  (SPY, QQQ, IWM, EEM, TLT, HYG, GLD)
  - Realized-volatility proxies  (rolling std, Parkinson, Garman-Klass, 63d)
  - Implied volatility  (VIX)
  - Volatility risk premium  (VIX - realized vol)
  - Vol-of-vol  (VVIX, rolling std of VIX changes)
  - VIX term structure  (VIX/VIX3M contango-backwardation ratio)
  - SPY momentum  (63d) and max drawdown  (63d)
  - Cross-asset: credit stress, SPY-TLT correlation, small-cap relative,
    gold flow, EM-DM spread, dispersion, eigenvalue concentration
  - Yield curve / macro: yield_slope, yield_slope change, hy_spread level
  - Return dynamics: rolling skewness, autocorrelation
  - Liquidity: relative volume, TED spread, volume-adjusted returns
  - SV-specific: lagged realized vol, vol-of-vol, leverage effect proxy
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
             VIX3M, VVIX, yield_slope, yield_2y, yield_10y, hy_spread,
             ted_spread, SPY_volume

    Returns
    -------
    features : DataFrame (T x n_features), warm-up NaN rows dropped
    """
    f = pd.DataFrame(index=market.index)

    # ── 1. Daily log returns for each ticker ───────────────────────
    for ticker in TICKERS:
        col = f'{ticker}_close'
        if col in market.columns:
            f[f'{ticker}_ret'] = np.log(market[col] / market[col].shift(1))

    spy_ret = f.get('SPY_ret')
    tlt_ret = f.get('TLT_ret')
    hyg_ret = f.get('HYG_ret')
    gld_ret = f.get('GLD_ret')

    # ── 2. Realized volatility proxies (SPY) ──────────────────────
    if spy_ret is not None:
        f['SPY_rv10'] = _realized_vol(spy_ret, SHORT_WINDOW)
        f['SPY_rv20'] = _realized_vol(spy_ret, MED_WINDOW)
        f['SPY_rv63'] = _realized_vol(spy_ret, LONG_WINDOW)

    # 3. Realized vol ratio (short/long — mean-reversion signal)
    if 'SPY_rv10' in f.columns and 'SPY_rv63' in f.columns:
        f['rv_ratio_10_63'] = f['SPY_rv10'] / f['SPY_rv63'].clip(lower=1e-6)

    # 4. Parkinson vol (SPY, 10d)
    if 'SPY_high' in market.columns and 'SPY_low' in market.columns:
        f['SPY_parkinson10'] = _parkinson_vol(
            market['SPY_high'], market['SPY_low'], SHORT_WINDOW,
        )

    # 5. Garman-Klass vol (SPY, 10d)
    if all(c in market.columns for c in ['SPY_open', 'SPY_high', 'SPY_low', 'SPY_close']):
        f['SPY_gk10'] = _garman_klass_vol(
            market['SPY_open'], market['SPY_high'],
            market['SPY_low'],  market['SPY_close'],
            SHORT_WINDOW,
        )

    # ── 6. Implied volatility (VIX level) ─────────────────────────
    if 'VIX' in market.columns:
        f['VIX'] = market['VIX']

    # 7. Volatility risk premium (VIX - realized, in vol points)
    if 'VIX' in market.columns and 'SPY_rv10' in f.columns:
        f['VRP'] = market['VIX'] - f['SPY_rv10'] * 100

    # ── 8. Vol-of-vol / VVIX ──────────────────────────────────────
    if 'VVIX' in market.columns:
        f['VVIX'] = market['VVIX']
        if 'VIX' in market.columns:
            f['VVIX_VIX_ratio'] = market['VVIX'] / market['VIX'].clip(lower=1)
    elif 'VIX' in market.columns:
        # Fallback: rolling std of VIX daily changes
        vix_ret = market['VIX'].diff()
        f['vix_vol10'] = vix_ret.rolling(SHORT_WINDOW).std()

    # ── 9. VIX term structure (contango vs backwardation) ─────────
    if 'VIX' in market.columns and 'VIX3M' in market.columns:
        # > 0 = backwardation (stress), < 0 = contango (normal carry)
        f['vix_ts_slope'] = market['VIX'] / market['VIX3M'].clip(lower=1) - 1

    # ── 10. Momentum (63d cumulative return of SPY) ────────────────
    if 'SPY_close' in market.columns:
        f['SPY_mom63'] = market['SPY_close'].pct_change(LONG_WINDOW)

    # 11. Max drawdown (63d rolling) of SPY
    if 'SPY_close' in market.columns:
        rolling_max = market['SPY_close'].rolling(LONG_WINDOW).max()
        f['SPY_dd63'] = market['SPY_close'] / rolling_max - 1

    # ── 12. Yield curve / macro ────────────────────────────────────
    if 'yield_slope' in market.columns:
        f['yield_slope'] = market['yield_slope']
        f['yield_slope_d'] = market['yield_slope'].diff()

    if 'hy_spread' in market.columns:
        f['hy_spread'] = market['hy_spread']

    # ── 13. Funding / liquidity stress ─────────────────────────────
    if 'ted_spread' in market.columns:
        f['ted_spread'] = market['ted_spread']

    # ── Cross-asset features ───────────────────────────────────────

    # 14. Credit stress: HYG return minus TLT return (20d rolling mean)
    if hyg_ret is not None and tlt_ret is not None:
        f['credit_stress'] = (hyg_ret - tlt_ret).rolling(MED_WINDOW).mean()

    # 15. SPY-TLT rolling correlation (63d)
    #     Sign flip from negative to positive = crisis correlation regime
    if spy_ret is not None and tlt_ret is not None:
        f['SPY_TLT_corr63'] = spy_ret.rolling(LONG_WINDOW).corr(tlt_ret)

    # 16. Small-cap vs large-cap relative strength (IWM/SPY, 20d)
    if 'IWM_close' in market.columns and 'SPY_close' in market.columns:
        iwm_spy = market['IWM_close'] / market['SPY_close']
        f['IWM_SPY_rel'] = iwm_spy.pct_change(MED_WINDOW)

    # 17. Gold flight-to-safety (GLD return vs SPY return, 20d)
    if gld_ret is not None and spy_ret is not None:
        f['gold_flow'] = (gld_ret - spy_ret).rolling(MED_WINDOW).mean()

    # 18. EM-DM spread (EEM vs SPY, 20d rolling mean)
    eem_ret = f.get('EEM_ret')
    if eem_ret is not None and spy_ret is not None:
        f['EM_DM_spread'] = (eem_ret - spy_ret).rolling(MED_WINDOW).mean()

    # 19. Cross-asset dispersion (rolling std of returns across all tickers, 10d)
    ret_cols = [c for c in f.columns if c.endswith('_ret')]
    if len(ret_cols) >= 3:
        f['xasset_disp'] = f[ret_cols].std(axis=1).rolling(SHORT_WINDOW).mean()

    # 20. Eigenvalue concentration (rolling covariance regime signal)
    #     High concentration = one dominant factor = trending/crisis regime
    if len(ret_cols) >= 3:
        ret_matrix = f[ret_cols].values
        n = len(ret_matrix)
        eigen_vals = np.full(n, np.nan)
        for i in range(LONG_WINDOW - 1, n):
            window = ret_matrix[i - LONG_WINDOW + 1: i + 1]
            if np.isnan(window).any():
                continue
            cov = np.cov(window, rowvar=False)
            eigs = np.linalg.eigvalsh(cov)
            eigs = np.maximum(eigs, 0)
            total = eigs.sum()
            if total > 1e-12:
                eigen_vals[i] = eigs[-1] / total
        f['eigen_conc'] = eigen_vals

    # ── Return dynamics ────────────────────────────────────────────

    # 21. Rolling skewness of SPY returns (20d)
    if spy_ret is not None:
        f['SPY_skew20'] = spy_ret.rolling(MED_WINDOW).skew()

    # 22. Rolling first-order autocorrelation (20d, efficient proxy)
    #     ρ̂₁ ≈ Σ(r_t · r_{t-1}) / Σ(r_t²)
    if spy_ret is not None:
        ret_lag = spy_ret.shift(1)
        f['SPY_ac1_20'] = (
            (spy_ret * ret_lag).rolling(MED_WINDOW).sum()
            / (spy_ret ** 2).rolling(MED_WINDOW).sum().clip(lower=1e-12)
        )

    # ── Liquidity ──────────────────────────────────────────────────

    # 23. Relative volume (SPY volume vs 20d mean)
    if 'SPY_volume' in market.columns:
        vol_ma = market['SPY_volume'].rolling(MED_WINDOW).mean()
        f['SPY_rel_volume'] = market['SPY_volume'] / vol_ma.clip(lower=1)

    # 24. Volume-normalized absolute return (fragility proxy)
    if 'SPY_volume' in market.columns and spy_ret is not None:
        norm_vol = market['SPY_volume'] / market['SPY_volume'].rolling(LONG_WINDOW).mean()
        f['SPY_vol_adj_ret'] = spy_ret.abs() / norm_vol.clip(lower=0.1)

    # ── SV-specific features (critical for ρ, ϕ identification) ───

    # 25. Lagged realized vol (SV persistence ϕ support)
    if 'SPY_rv10' in f.columns:
        f['SPY_rv10_lag5'] = f['SPY_rv10'].shift(5)
        f['SPY_rv10_lag10'] = f['SPY_rv10'].shift(10)

    # 26. Vol-of-vol estimate (discrete-time ξ analog)
    if 'SPY_rv10' in f.columns:
        f['SPY_volvol20'] = f['SPY_rv10'].rolling(MED_WINDOW).std()

    # 27. Leverage effect proxy (rolling corr between return and next-day vol change)
    #     Empirically measures ρ < 0 in Heston / SV models
    if spy_ret is not None and 'SPY_rv10' in f.columns:
        vol_chg = f['SPY_rv10'].diff()
        f['lev_effect20'] = spy_ret.rolling(MED_WINDOW).corr(vol_chg)

    # ── Drop warm-up NaN rows (with diagnostics) ──────────────────
    na_counts = f.isna().sum()
    binding = na_counts[na_counts > 0].sort_values(ascending=False)
    if not binding.empty:
        print(f"  Feature NaN counts (top 5 binding constraints):")
        for feat, cnt in binding.head(5).items():
            print(f"    {feat}: {cnt} NaN rows")

    f = f.dropna()

    return f


# ── Skewness correction ────────────────────────────────────────────

# Features that are non-negative and right-skewed → log(1+x) compresses
# the right tail so PCA doesn't over-weight crisis outliers and the
# symmetric Student-t emissions fit each regime more cleanly.
_LOG_TRANSFORM_COLS = {
    'SPY_rv10', 'SPY_rv20', 'SPY_rv63', 'SPY_parkinson10', 'SPY_gk10',
    'VIX', 'VVIX', 'VVIX_VIX_ratio', 'rv_ratio_10_63',
    'hy_spread', 'ted_spread',
    'xasset_disp', 'SPY_rel_volume', 'SPY_vol_adj_ret',
    'SPY_volvol20', 'SPY_rv10_lag5', 'SPY_rv10_lag10',
}


def _fix_skew(features: pd.DataFrame) -> pd.DataFrame:
    """Apply log1p to right-skewed non-negative features in-place."""
    for col in _LOG_TRANSFORM_COLS:
        if col in features.columns:
            features[col] = np.log1p(features[col])
    return features


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
    features = _fix_skew(features)
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
