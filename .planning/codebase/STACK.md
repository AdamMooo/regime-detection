# Technology Stack

**Analysis Date:** 2026-04-18

## Languages

**Primary:**
- Python 3.10 — all pipeline code, training, evaluation, signals

## Runtime

**Environment:**
- CPython 3.10 (pinned via CI matrix: `python-version: '3.10'`)
- CPU-only JAX backend (explicitly forced: `jax.config.update("jax_platform_name", "cpu")`)
- 64-bit precision enabled globally: `jax.config.update("jax_enable_x64", True)`

**Package Manager:**
- pip
- Lockfile: `requirements.txt` with exact `==` pins (hard requirement — see version pinning section)

## Frameworks

**Core Bayesian Inference:**
- NumPyro 0.20.0 — probabilistic programming, SVI and NUTS inference for HDP-HMM
- JAX 0.9.1 — array computation backend for NumPyro (JIT compilation, vmap, lax.scan)
- JAXlib 0.9.1 — JAX C++ backend

**Classic HMM (active backend, `USE_HDP=False`):**
- hmmlearn 0.3.3 — GaussianHMM base class extended by `StudentTHMM` in `src/core/inference.py`

**Dimensionality Reduction:**
- scikit-learn 1.8.0 — PCA with Procrustes alignment (`src/core/hmm_training.py`)

**Volatility Modeling:**
- arch 8.0.0 — GARCH(1,1) per-regime models (`src/core/hmm_training.py::fit_regime_garch()`)
- statsmodels 0.14.6 — linearized Stochastic Volatility (Kalman filter via MLEModel, `src/core/hmm_training.py::LinearizedSV`)

**Data / Science:**
- pandas 3.0.1 — DataFrames throughout pipeline
- numpy 2.4.3 — numerical operations
- scipy 1.17.1 — multivariate_t, orthogonal_procrustes, stats tests

**Visualization:**
- plotly 6.6.0 — interactive dashboards (`figures/dashboard.html`, `figures/feature_analysis.html`)
- matplotlib 3.9.2 — static plots

**Data Collection:**
- yfinance 1.2.0 — OHLCV data (SPY, QQQ, IWM, EEM, TLT, HYG, GLD) + VIX family from Yahoo Finance

**Persistence:**
- joblib 1.5.3 — model serialization (`models/hmm_model.pkl`, `models/pca_model.pkl`, `models/regime_model.pkl`)

**Testing:**
- pytest 9.0.2 — test runner (`tests/`)

## Version Pinning (Critical Constraint)

All packages use exact `==` pins. JAX/NumPyro are pinned with special enforcement:

- CI job `check-version-pins` in `.github/workflows/tests.yml` rejects any PR that uses `>=` for JAX or NumPyro
- Rationale documented in `requirements.txt`: "Breaking changes in JAX/NumPyro silently corrupt regime assignments"
- Never loosen these pins without full regime label regression testing

## Configuration

**Central config file:** `src/config.py` — all hyperparameters, paths, feature lists

**Key config values:**
- `USE_HDP = False` — classic Student-t HMM active (Bayesian HDP-HMM available but disabled)
- `N_STATES = 3`, `N_STATES_RANGE = [3]` — K locked at 3 post Phase 2.5.3 BIC experiment
- `RANDOM_SEED = 42` — deterministic throughout
- `FEATURE_SUBSET` — 6 features selected on held-out 2010-2020 train set
- `WALK_FORWARD_MODE = 'rolling'`, `WALK_FORWARD_TRAIN_YEARS = 5`
- `DATA_DIR = 'data'`, `MODEL_DIR = 'models'`, `FIGURE_DIR = 'figures'`, `CACHE_PATH = 'data/cache'`

**Environment:** No `.env` files used. All configuration is in `src/config.py` directly.

## Platform Requirements

**Development:**
- Python 3.10 (exact version per CI)
- CPU-only (no GPU required; JAX forced to CPU in `src/core/hdp_hmm.py`)
- Windows 11 (current dev environment) or Ubuntu 20.04+ (CI)

**Production:**
- No server deployment — pipeline runs as a local script
- Outputs CSV files consumed by Algo-Trading-Bot and Portfolio-Manager
- GitHub Actions CI on push to `main` / `develop`

---

*Stack analysis: 2026-04-18*
