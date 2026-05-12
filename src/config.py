"""Thesis Configuration: Sticky HDP-HMM vs Threshold Rules on SPX

Data: S&P 500 (^GSPC) + VIX + WTI shocks, 2015-2026
Models: Threshold rules, Parametric HMM (statsmodels), Sticky HDP-HMM (NumPyro)
Metrics: Log-likelihood, 2020 COVID F1, regime stability, Sharpe ratio
"""

import os

# --- Reproducibility ---
RANDOM_SEED = 42

# --- Data ---
START_DATE = '2015-01-01'
END_DATE   = '2026-12-31'
TRAIN_END  = '2023-12-31'

# Tickers - Real market indices
SPX_TICKER = '^GSPC'  # S&P 500
VOL_TICKER = '^VIX'   # Market volatility index
WTI_TICKER = 'CL=F'   # WTI crude oil futures (macro feature)

# --- Features for HDP-HMM ---
FEATURES = ['vol_index', 'wti_shock']  # VIX level, WTI % change

# --- Threshold Rules ---
THRESH_VOL_LOW = 15
THRESH_VOL_HIGH = 25
THRESH_WTI_POS = 0
THRESH_WTI_NEG = -0.05

# --- Parametric HMM ---
PARAMETRIC_K_REGIMES = 3

# --- Sticky HDP-HMM ---
HDP_TRUNCATION = 8
HDP_ALPHA = 1.0
HDP_KAPPA = 10.0  # stickiness
HDP_INFERENCE = 'svi'
SVI_NUM_STEPS = 4000
SVI_LEARNING_RATE = 0.005
SVI_NUM_SAMPLES = 500

# --- Metrics ---
COVID_START = '2020-03-09'
COVID_END = '2020-03-23'
COVID_DRAWDOWN_THRESH = 0.15

# --- Output ---
FIGURES_DIR = 'figures'
RESULTS_DIR = 'results'

# --- Incremental Data Collection ---
CACHE_WINDOW     = 252
INCREMENTAL_MODE = 'auto'
