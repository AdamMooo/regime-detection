"""Regime-Detection configuration. Edit parameters here, not in individual scripts."""

import os

# --- Reproducibility ---
RANDOM_SEED = 42

# --- Data ---
START_DATE   = '2010-01-01'
END_DATE     = None             # None = today

TICKERS      = ['SPY', 'QQQ', 'IWM', 'EEM', 'TLT', 'HYG', 'GLD']
VIX_TICKER   = '^VIX'
VIX3M_TICKER = '^VIX3M'
VVIX_TICKER  = '^VVIX'

# FRED API key — get free key at https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.getenv('FRED_API_KEY', '')

# --- Feature windows ---
SHORT_WINDOW = 10
MED_WINDOW   = 20
LONG_WINDOW  = 63

# --- Feature selection ---
# 4 features fed directly into HDP-HMM (no PCA).
# All lagged 1 day in train.py for causality.
FEATURE_SUBSET = [
    'VIX',               # implied volatility level
    'yield_curve_slope', # 10y-2y — macro cycle
    'NFCI',              # financial stress
    'VRP',               # variance risk premium — implied vs realized vol gap
]

# --- Bayesian HDP-HMM (NumPyro) ---
HDP_TRUNCATION  = 6            # max states for stick-breaking
HDP_ALPHA       = 1.0          # DP concentration (global)
HDP_KAPPA       = 10.0         # sticky self-transition weight
HDP_MAX_REGIMES = 6            # merge down to at most this many regimes
HDP_INFERENCE   = 'svi'        # 'svi' (fast) or 'nuts' (gold-standard, overnight)

# SVI settings
SVI_NUM_STEPS     = 3000
SVI_LEARNING_RATE = 0.003
SVI_NUM_SAMPLES   = 500

# NUTS settings
MCMC_NUM_WARMUP  = 300
MCMC_NUM_SAMPLES = 1000
MCMC_NUM_CHAINS  = 1

REGIME_HOLD_DAYS = 1

# --- Walk-forward validation ---
WALK_FORWARD_TRAIN_YEARS = 5
WALK_FORWARD_STEP_DAYS   = 21
WALK_FORWARD_MODE        = 'rolling'

# --- Regime naming ---
# VOL_BRACKETS: map annualized realized vol (%) to regime name.
# Thresholds are absolute — a state with 13% vol is always "Moderate-Vol"
# regardless of how many other states exist.
VOL_BRACKETS = [
    (0,   10,  'Low-Vol'),
    (10,  18,  'Moderate-Vol'),
    (18,  28,  'Elevated-Vol'),
    (28, 999,  'Crisis-Vol'),
]

# --- Bot Label Mapping ---
# Source of truth for downstream consumers (algo-trading-bot, portfolio-manager).
LABEL_MAPPING = {
    'Low-Vol':      'LOW_VOL',
    'Moderate-Vol': 'MED_VOL',
    'Elevated-Vol': 'HIGH_VOL',
    'Crisis-Vol':   'HIGH_VOL',
}

# --- Data freshness ---
MAX_DATA_STALENESS_DAYS = 3

# --- Paths ---
DATA_DIR   = 'data'
MODEL_DIR  = 'models'
FIGURE_DIR = 'figures'
CACHE_PATH = 'data/cache'

# --- Incremental Data Collection ---
CACHE_WINDOW     = 252
INCREMENTAL_MODE = 'auto'
