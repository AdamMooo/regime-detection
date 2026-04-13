"""
Shared configuration for PCA -> HMM -> Regime-Dependent SV pipeline.
Edit parameters here, not in individual scripts.
"""

import os

# --- Reproducibility ---
RANDOM_SEED = 42

# --- Data ---
START_DATE   = '2010-01-01'
END_DATE     = None             # None = today

# Universe (OHLCV from yfinance)
TICKERS    = ['SPY', 'QQQ', 'IWM', 'EEM', 'TLT', 'HYG', 'GLD']
VIX_TICKER  = '^VIX'
VIX3M_TICKER = '^VIX3M'      # 3-month VIX (term structure)
VVIX_TICKER  = '^VVIX'       # vol-of-VIX

# --- Feature windows ---
SHORT_WINDOW = 10       # ~2 weeks
MED_WINDOW   = 20       # ~1 month
LONG_WINDOW  = 63       # ~1 quarter

# --- PCA ---
PCA_MAX_COMPONENTS = 5
PCA_VAR_THRESHOLD  = 0.90   # cumulative variance for auto-selection
PCA_ROLLING_WINDOW = 63     # rolling window for PCA (~3 months)
VIX_BYPASS         = False  # VIX is now a direct curated feature; no need to append separately

# Representative feature subset for PCA (reduces collinearity).
# Set to None to use all features. Using a curated subset prevents
# the vol cluster (~10 features) from dominating the first PCs.
FEATURE_SUBSET = [
    # Vol state
    'VIX', 'VRP',
    # Vol dynamics
    'rv_ratio_10_63',
    # Cross-asset
    'SPY_TLT_corr63',
    # Return dynamics
    'SPY_skew20',
    # Market structure
    'SPY_dd63',
    # Leverage / fragility
    'lev_effect20',
]

# --- HMM (classic) ---
N_STATES_RANGE = [2, 3, 4]       # BIC search grid
N_STATES       = 3               # 3-regime target for Algo-Trading-Bot integration (see CLAUDE.md)
                                # default if BIC is skipped; BIC search can explore 2, 3, 4
COV_TYPE       = 'full'
T_DF           = 4               # Student-t degrees of freedom
N_SEEDS        = 20              # multi-seed stability check
HMM_ITER       = 300

# --- Bayesian HDP-HMM (NumPyro) ---
USE_HDP            = False       # Simplified: Use classic StudentTHMM instead of full Bayesian HDP-HMM
HDP_TRUNCATION     = 20          # max states for stick-breaking (must exceed expected K)
HDP_ALPHA          = 1.0         # DP concentration (global)
HDP_KAPPA          = 10.0        # sticky self-transition weight
HDP_MAX_REGIMES    = 6           # merge down to at most this many regimes
HDP_INFERENCE      = 'svi'       # 'svi' (fast, ~5-10min CPU) or 'nuts' (slow, best overnight)

# SVI settings (only used if HDP_INFERENCE='svi')
SVI_NUM_STEPS      = 3000        # optimization steps
SVI_LEARNING_RATE  = 0.003       # Adam step size
SVI_NUM_SAMPLES    = 500         # posterior samples drawn from trained guide

# NUTS settings (only used if HDP_INFERENCE='nuts')
MCMC_NUM_WARMUP    = 300
MCMC_NUM_SAMPLES   = 1000
MCMC_NUM_CHAINS    = 1           # single chain for CPU

# --- Regime-Dependent GARCH ---
GARCH_P        = 1
GARCH_Q        = 1
GARCH_DIST     = 'normal'
MIN_REGIME_OBS = 50              # minimum obs per regime for GARCH fit
REGIME_HOLD_DAYS = 1             # Simplified: Reduced hysteresis filter

# --- Validation ---
WALK_FORWARD_TRAIN_YEARS = 5
WALK_FORWARD_STEP_DAYS   = 21   # ~monthly re-fit
WALK_FORWARD_MODE        = 'rolling'  # 'expanding' or 'rolling'
VAR_ALPHA                = 0.05 # 95% VaR

# --- Regime naming ---
# REGIME_NAMES: fallback for fixed-K classic HMM (sorted by ascending VIX mean).
REGIME_NAMES = {
    2: ['Low-Vol', 'High-Vol'],
    3: ['Low-Vol', 'Medium-Vol', 'High-Vol'],
    4: ['Low-Vol', 'Moderate', 'Elevated', 'Crisis'],
    5: ['Low-Vol', 'Moderate', 'Elevated', 'High-Vol', 'Crisis'],
    6: ['Very-Low', 'Low-Vol', 'Moderate', 'Elevated', 'High-Vol', 'Crisis'],
}

# --- Bot Label Mapping ---
# Maps internal regime names to Algo-Trading-Bot canonical labels.
# This is the source of truth for all downstream integrations.
# Covers all possible regime names from REGIME_NAMES and VOL_BRACKETS.
LABEL_MAPPING = {
    # Classic 2-state and 3-state regimes
    'Low-Vol': 'LOW_VOL',
    'Medium-Vol': 'MED_VOL',
    'High-Vol': 'HIGH_VOL',

    # 4-state regime names (from REGIME_NAMES[4])
    'Moderate': 'MED_VOL',
    'Elevated': 'HIGH_VOL',
    'Crisis': 'HIGH_VOL',

    # 5-state regime names (from REGIME_NAMES[5])
    # Low-Vol, Moderate, Elevated, High-Vol, Crisis already covered above

    # 6-state regime names (from REGIME_NAMES[6])
    'Very-Low': 'LOW_VOL',
    # Other names already covered above

    # VOL_BRACKETS regime names (absolute vol-based naming)
    'Moderate-Vol': 'MED_VOL',
    'Elevated-Vol': 'HIGH_VOL',
    'Crisis-Vol': 'HIGH_VOL',
}

# Absolute vol-bracket thresholds for HDP regime naming.
# Each state is named by its realized vol level, not its rank — so a state
# with 14% annualized vol is always "Moderate-Vol" whether the model finds
# 2 states or 5.  Thresholds are annualized SPY realized vol (%).
VOL_BRACKETS = [
    (0,   10,  'Low-Vol'),
    (10,  18,  'Moderate-Vol'),
    (18,  28,  'Elevated-Vol'),
    (28, 999,  'Crisis-Vol'),
]

# --- Data freshness ---
MAX_DATA_STALENESS_DAYS = 3  # warn if market_data.csv is this many trading days old

# --- Paths ---
DATA_DIR   = 'data'
MODEL_DIR  = 'models'
FIGURE_DIR = 'figures'
