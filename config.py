"""
Shared configuration for PCA -> HMM -> Regime-Dependent SV pipeline.
Edit parameters here, not in individual scripts.
"""

# --- Reproducibility ---
RANDOM_SEED = 42

# --- Data ---
START_DATE   = '2010-01-01'
END_DATE     = None             # None = today
FRED_API_KEY = '9284d1ec1af2e1c12114b61681304e81'

# Universe (OHLCV from yfinance)
TICKERS    = ['SPY', 'QQQ', 'IWM', 'EEM', 'TLT', 'HYG', 'GLD']
VIX_TICKER = '^VIX'

# FRED series:  {series_id: column_name}
FRED_SERIES = {
    'T10Y2Y':       'yield_slope',      # 10Y-2Y Treasury spread
    'BAMLH0A0HYM2': 'hy_spread',        # ICE BofA US High Yield spread
}

# --- Feature windows ---
SHORT_WINDOW = 10       # ~2 weeks
MED_WINDOW   = 20       # ~1 month
LONG_WINDOW  = 63       # ~1 quarter

# --- PCA ---
PCA_MAX_COMPONENTS = 5
PCA_VAR_THRESHOLD  = 0.85   # cumulative variance for auto-selection
PCA_ROLLING_WINDOW = 63     # rolling window for PCA (~3 months)
VIX_BYPASS         = True   # append scaled VIX directly to PCs (bypasses PCA dilution)

# --- HMM ---
N_STATES_RANGE = [2, 3, 4]       # BIC search grid
N_STATES       = 4               # default if BIC is skipped
COV_TYPE       = 'full'
T_DF           = 4               # Student-t degrees of freedom
N_SEEDS        = 20              # multi-seed stability check
HMM_ITER       = 300

# --- Regime-Dependent GARCH ---
GARCH_P        = 1
GARCH_Q        = 1
GARCH_DIST     = 'normal'
MIN_REGIME_OBS = 50              # minimum obs per regime for GARCH fit
REGIME_HOLD_DAYS = 3             # hysteresis: require N days before switching regime

# --- Validation ---
WALK_FORWARD_TRAIN_YEARS = 5
WALK_FORWARD_STEP_DAYS   = 21   # ~monthly re-fit
VAR_ALPHA                = 0.05 # 95% VaR

# --- Regime naming (sorted by ascending VIX mean) ---
REGIME_NAMES = {
    2: ['Low-Vol', 'High-Vol'],
    3: ['Low-Vol', 'Medium-Vol', 'High-Vol'],
    4: ['Low-Vol', 'Moderate', 'Elevated', 'Crisis'],
}

# --- Paths ---
DATA_DIR   = 'data'
MODEL_DIR  = 'models'
FIGURE_DIR = 'figures'
