"""Thesis Configuration: Sticky HDP-HMM vs Threshold Rules on SPX

Data: S&P 500 (^GSPC) + VIX + FRED macro series, 2015-2026
Models: Threshold rules, Parametric HMM (statsmodels), Sticky HDP-HMM (NumPyro)
Metrics: Log-likelihood, 2020 COVID F1, regime stability, within-regime Sharpe
"""

import os

# --- Reproducibility ---
RANDOM_SEED = 42

# --- Data ---
START_DATE = '2015-01-01'
END_DATE   = '2026-12-31'
TRAIN_END  = '2023-12-31'

# Tickers
SPX_TICKER = '^GSPC'   # S&P 500
VOL_TICKER = '^VIX'    # Implied volatility

# FRED series
FRED_YIELD_SERIES = 'T10Y2Y'   # 10y minus 2y Treasury spread (yield slope)
FRED_NFCI_SERIES  = 'NFCI'     # Chicago Fed National Financial Conditions Index

# --- Features (4 direct, no PCA -- reviewers can't argue with it) ---
FEATURES = ['spy_ret', 'vol_index', 'yield_slope', 'nfci']

# --- Threshold Baseline ---
THRESH_VOL_LOW  = 15    # VIX below -> Low-Vol
THRESH_VOL_HIGH = 25    # VIX above -> High-Vol

# --- Parametric HMM Baseline ---
PARAMETRIC_K_REGIMES = 3

# --- Sticky HDP-HMM ---
# alpha_trans and kappa are NOT set here -- they are fully Bayesian latents
# (Gamma priors) inferred inside hdp_hmm_model(). See paper.tex:289.
HDP_TRUNCATION    = 8
HDP_INFERENCE     = 'svi'
SVI_NUM_STEPS     = 4000
SVI_LEARNING_RATE = 0.005
SVI_NUM_SAMPLES   = 500

# --- MCMC settings (for paper-quality NUTS run, best overnight) ---
MCMC_NUM_WARMUP  = 500
MCMC_NUM_SAMPLES = 1000
MCMC_NUM_CHAINS  = 2

# --- Regime labeling: absolute realized-vol brackets (annualized %) ---
VOL_BRACKETS = [
    (0,   14, 'Low-Vol'),
    (14,  22, 'Moderate-Vol'),
    (22, 200, 'High-Vol'),
]

# --- Paper event windows ---
COVID_START           = '2020-03-09'
COVID_END             = '2020-03-23'
COVID_DRAWDOWN_THRESH = 0.15

# --- Output directories ---
DATA_DIR    = 'data'
MODEL_DIR   = 'models'
FIGURE_DIR  = 'figures'
RESULTS_DIR = 'results'
