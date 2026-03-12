"""
Shared configuration for regime detection pipeline.
Edit parameters here, not in individual scripts.
"""

# --- Data ---
START_DATE = '2000-01-01'
FRED_API_KEY = '9284d1ec1af2e1c12114b61681304e81'

FEATURES = ['vix', 'hy_spread', 'garch_vol', 'yield_spread']

# --- Feature transforms ---
LOG_FEATURES = ['vix', 'hy_spread']                 # direct log; garch_vol becomes VRP separately
YIELD_SPREAD_SHIFT = 4.0                             # shift T10Y2Y before log (handles negatives)

# --- Model ---
N_STATES = 4
COV_TYPE = 'full'
T_DF     = 4            # Student-t degrees of freedom for emissions
N_SEEDS  = 20           # initialization runs for stability check
HMM_ITER = 300

# --- Validation ---
WALK_FORWARD_TRAIN_YEARS = 10   # minimum training window
WALK_FORWARD_STEP_DAYS = 63     # re-fit quarterly
SLOPE_WINDOW = 20               # trading days (~1 month) for slope/curvature geometry

# --- Regime naming (sorted by ascending VIX mean) ---
REGIME_NAMES = {
    2: ['Low-Risk', 'Crisis'],
    3: ['Low-Risk', 'Elevated-Risk', 'Crisis'],
    4: ['Low-Risk', 'Moderate', 'Elevated-Risk', 'Crisis'],
}

# --- Paths ---
DATA_DIR = 'data'
MODEL_DIR = 'models'
FIGURE_DIR = 'figures'
