"""
Shared configuration for PCA -> HMM -> Regime-Dependent SV pipeline.
Edit parameters here, not in individual scripts.
"""

import os
from pathlib import Path

# --- Reproducibility ---
RANDOM_SEED = 42

# --- Data ---
START_DATE   = '2010-01-01'
END_DATE     = None             # None = today

# Load FRED API key from .env file or environment variable
_env_path = Path(__file__).resolve().parent / '.env'
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip())

FRED_API_KEY = os.environ.get('FRED_API_KEY', '')

# Universe (OHLCV from yfinance)
TICKERS    = ['SPY', 'QQQ', 'IWM', 'EEM', 'TLT', 'HYG', 'GLD']
VIX_TICKER  = '^VIX'
VIX3M_TICKER = '^VIX3M'      # 3-month VIX (term structure)
VVIX_TICKER  = '^VVIX'       # vol-of-VIX

# FRED series:  {series_id: column_name}
FRED_SERIES = {
    'T10Y2Y':       'yield_slope',      # 10Y-2Y Treasury spread
    'BAMLH0A0HYM2': 'hy_spread',        # ICE BofA US High Yield spread
    'DGS10':        'yield_10y',         # 10Y Treasury yield
    'DGS2':         'yield_2y',          # 2Y Treasury yield
    'TEDRATE':      'ted_spread',        # TED spread (funding stress)
}

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
    # Vol: one per horizon, plus the high-low estimator
    'SPY_rv10', 'SPY_rv63', 'SPY_parkinson10',
    # Implied vol & risk premium
    'VIX', 'VRP',
    # Vol-of-vol & term structure
    'SPY_volvol20', 'vix_ts_slope',
    # Returns: SPY + key cross-asset
    'SPY_ret', 'TLT_ret', 'EEM_ret',
    # Cross-asset signals
    'credit_stress', 'SPY_TLT_corr63', 'xasset_disp', 'eigen_conc',
    # Macro & credit
    'yield_slope', 'hy_spread', 'ted_spread',
    # Return dynamics
    'SPY_skew20', 'SPY_ac1_20',
    # Momentum & drawdown
    'SPY_mom63', 'SPY_dd63',
    # Leverage effect
    'lev_effect20',
]

# --- HMM (classic) ---
N_STATES_RANGE = [2, 3, 4]       # BIC search grid
N_STATES       = 4               # default if BIC is skipped
COV_TYPE       = 'full'
T_DF           = 4               # Student-t degrees of freedom
N_SEEDS        = 20              # multi-seed stability check
HMM_ITER       = 300

# --- Bayesian HDP-HMM (NumPyro) ---
USE_HDP            = True        # True = Bayesian HDP-HMM; False = classic StudentTHMM
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
REGIME_HOLD_DAYS = 2             # hysteresis: require N days before switching regime

# --- Validation ---
WALK_FORWARD_TRAIN_YEARS = 5
WALK_FORWARD_STEP_DAYS   = 21   # ~monthly re-fit
WALK_FORWARD_MODE        = 'rolling'  # 'expanding' or 'rolling'
VAR_ALPHA                = 0.05 # 95% VaR

# --- Regime naming (sorted by ascending VIX mean) ---
# For fixed-K HMM. HDP-HMM generates names dynamically for any K.
REGIME_NAMES = {
    2: ['Low-Vol', 'High-Vol'],
    3: ['Low-Vol', 'Medium-Vol', 'High-Vol'],
    4: ['Low-Vol', 'Moderate', 'Elevated', 'Crisis'],
    5: ['Low-Vol', 'Moderate', 'Elevated', 'High-Vol', 'Crisis'],
    6: ['Very-Low', 'Low-Vol', 'Moderate', 'Elevated', 'High-Vol', 'Crisis'],
}

# --- Paths ---
DATA_DIR   = 'data'
MODEL_DIR  = 'models'
FIGURE_DIR = 'figures'
