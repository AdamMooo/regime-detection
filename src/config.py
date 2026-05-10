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

# --- External API keys ---
# FRED API key for macro data collection (T10Y2Y, BAMLH0A0HYM2, NFCI).
# Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html.
# If empty, collect_macro.py falls back to pandas_datareader (rate-limited, no key needed).
FRED_API_KEY = os.getenv('FRED_API_KEY', '')

# --- Feature windows ---
SHORT_WINDOW = 10       # ~2 weeks
MED_WINDOW   = 20       # ~1 month
LONG_WINDOW  = 63       # ~1 quarter

# --- PCA ---
PCA_MAX_COMPONENTS = 5
PCA_VAR_THRESHOLD  = 0.90   # cumulative variance for auto-selection
PCA_ROLLING_WINDOW = 63     # rolling window for PCA (~3 months)
VIX_BYPASS         = False  # Phase 9 (Plan 3): removed — VIX is already in FEATURE_SUBSET via PCA;
                            # bypass was double-counting it and forcing VIX-driven clustering that
                            # mismatched the realized-vol naming (e.g. 2021: VIX~18 but RV~13%).
                            # Phase 6 original reason: VIX_BYPASS=True added to force HMM to cluster
                            # on implied vol level directly (GLD_trend dominated PC1). GLD_trend was
                            # removed in Phase 5; bypass is no longer needed.

# Representative feature subset for PCA (reduces collinearity).
# Set to None to use all features. Using a curated subset prevents
# the vol cluster (~10 features) from dominating the first PCs.
# Updated per Phase 2.5.2: Feature selection on held-out train set (2010-2020)
# improved OOS regime accuracy from 72.7% to 76.2% and dwell time from 5.6 to 17.7 days.
# See data/feature_selection_report.txt for full analysis.
# Phase 5 replaced: FEATURE_SUBSET = [
#     # Vol state
#     'VRP', 'VIX',
#     # Return dynamics
#     'SPY_skew20',
#     # Cross-asset
#     'SPY_TLT_corr63',
#     # Leverage / fragility
#     'lev_effect20',
#     # Vol dynamics
#     'rv_ratio_10_63',
# ]
# Phase 6 fix (2026-04-19): removed GLD_trend — dominated PC1 (loading 0.661) but PC1 barely
# separated regimes (F=29 vs PC2/PC3 F=699/859). GLD trend is a macro/sentiment signal that
# can move opposite to VIX (safe-haven flows), causing VIX=25+ days to be labeled Low-Vol.
# VIX_BYPASS=True added to force HMM to cluster on implied vol level directly.
# Phase 5 selected on 2026-04-19: walk-forward section selection
# Source: data/walk_forward_selection_result.json
# Selected sections (>=60% fold stability): s_mac, s_fin, s_vol
FEATURE_SUBSET = [
    # 'lev_effect20' excluded: F=0.4, p=0.70 — statistically indistinguishable from noise
    # (Phase 9 diagnosis: zero discriminative power across all three regimes)
    'yield_curve_slope',
    'credit_stress',
    'SPY_TLT_corr63',
    'NFCI',
    'eigen_conc',
    'SPY_dd63',
    'VIX',
    'VRP',
    'rv_ratio_10_63',
    'vix_ts_slope',
    'SPY_volvol20',
    'SPY_rv10_lag5',
    'SPY_rv10_lag10',
    'SPY_skew20',
]

# --- HMM (classic) ---
N_STATES_RANGE = [3]             # Reverted to K=3 (Phase 2.5.3+ analysis showed K=4 regimes 0&1 overlap too much)
N_STATES       = 3               # K=3 confirmed cleaner: Low-Vol (15.3 VIX), Moderate (17.4), High-Vol (22.8)
                                # K=4 was statistically justified by BIC but empirically weak - 2 regimes barely different
                                # Phase 3.1 next: feature diversification (reduce correlated vol signals)
COV_TYPE       = 'full'
T_DF           = 4               # Student-t degrees of freedom
N_SEEDS        = 20              # multi-seed stability check
HMM_ITER       = 300

# --- Bayesian HDP-HMM (NumPyro) ---
USE_HDP = True                   # Phase 6 human override: HDP-HMM enabled as default
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

# --- Regime-Dependent GARCH (Phase 2.5.4) ---
# GARCH-conditional VaR for risk management (passes Kupiec POF and Christoffersen tests)
# Per-regime GARCH(1,1) models capture volatility persistence and remove exceedance clustering
# See docs/RISK_MODEL_CARD.md for detailed comparison vs static VaR
GARCH_P        = 1
GARCH_Q        = 1
GARCH_DIST     = 'normal'
MIN_REGIME_OBS = 50              # minimum obs per regime for GARCH fit
REGIME_HOLD_DAYS = 1             # Simplified: Reduced hysteresis filter

# --- Validation ---
WALK_FORWARD_TRAIN_YEARS = 5
WALK_FORWARD_STEP_DAYS   = 21   # ~monthly re-fit
WALK_FORWARD_MODE        = 'rolling'  # 'expanding' or 'rolling'
VAR_ALPHA                = 0.05 # 95% VaR confidence level for GARCH-conditional VaR

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
# Phase 9 (Plan 3): thresholds below are PROVISIONAL pending retrain.
# After retrain, Task 3 reviews discovered state realized vols and may adjust these.
# See scripts/analysis/regime_label_audit.py for per-day audit output.
VOL_BRACKETS = [
    (0,   10,  'Low-Vol'),
    (10,  18,  'Moderate-Vol'),
    (18,  28,  'Elevated-Vol'),
    (28, 999,  'Crisis-Vol'),
]

# --- Data freshness ---
MAX_DATA_STALENESS_DAYS = 3  # warn if market_data.csv is this many trading days old

# --- Paths ---
DATA_DIR       = 'data'
MODEL_DIR      = 'models'
FIGURE_DIR     = 'figures'
CACHE_PATH     = 'data/cache'     # Directory for incremental data cache (CSV + Feather indices)

# --- Incremental Data Collection ---
CACHE_WINDOW       = 252           # Trading days for rolling PCA refit (1 year window)
INCREMENTAL_MODE   = 'auto'        # 'auto' = auto-detect based on cache existence, 'full', or 'incremental'

# ===================================================================
# Phase 3.4: Multi-Signal Combination (Optional Ensemble Mode)
# ===================================================================

# Enable 11-step signal combination engine (Fundamental Law of Active Management)
# When True: regime probabilities from combined signal engine
# When False: regime probabilities from single-HMM baseline (current behavior)
# Default: False (backward compatible, single-HMM)
USE_SIGNAL_COMBINATION = False

# Signal combination configuration
SIGNAL_COMBINATION_CONFIG = {
    'hold_days': 1,              # Forward-looking window for IC calculation
    'min_warmup': 252,           # Minimum observations before calculating IC
    'n_cross_val_folds': 5,      # Number of CV folds for evaluation
    'bias_adjustment_factor': 0.1,  # Penalty factor for IC overfitting correction
    'winsorize_sigma': 3.0,      # Clipping threshold (n sigma)
}
