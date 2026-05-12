# Technology Stack

**Analysis Date:** 2026-05-11

## Languages

**Primary:**
- Python 3.12 - All application code, experiments, data processing, and model training

## Runtime

**Environment:**
- CPython 3.12.3 on Linux (WSL2)

**Package Manager:**
- pip with virtualenv (`.venv/`)
- Lockfile: absent — `requirements.txt` uses exact pins `==` (JAX/NumPyro must be pinned exactly for reproducibility)

## Frameworks

**Core ML:**
- NumPyro 0.20.0 - Bayesian inference for HDP-HMM with SVI optimization
- JAX 0.9.1 - Probabilistic computing backend
- statsmodels 0.14.6 - Parametric HMM baseline (ParametricHMM)

**Data:**
- pandas 3.0.1 - Tabular data manipulation, CSV I/O
- numpy 2.4.3 - Numerical computation

**Visualization:**
- matplotlib 3.9.2 - Line plots, diagnostics
- plotly 6.6.0 - Interactive dashboards (legacy, not used in thesis experiments)

**Model Selection:**
- scikit-learn 1.8.0 - Clustering utilities (KMeans for baseline if needed)
- hmmlearn 0.3.3 - Standard HMM baseline

**Testing:**
- pytest 9.0.2 - Test runner

## Key Dependencies

**Critical (thesis):**
- yfinance 1.2.0 - S&P 500, VIX, WTI data fetching
- numpyro 0.20.0 - Sticky HDP-HMM inference via SVI
- jax 0.9.1 - JAX arrays and autodiff (MUST be 0.9.1, pinned for regime reproducibility)

**Supporting:**
- arch 8.0.0 - GARCH models (unused in current thesis)
- fredapi 0.5.2 - FRED data (unused, removed from SPX pivot)
- scipy 1.17.1 - Scientific computing (optimization, statistics)
- joblib 1.5.3 - Parallel compute (unused)
- pandas_datareader 0.10 - Data fetch utilities (unused)
- python-dotenv 1.0+ - `.env` file loading

## Configuration

**Environment:**
- No `.env` required for thesis experiments (yfinance requires no API key)
- Config loaded via `src/config.py` (Python module, not YAML)

**Build:**
- No build system; scripts run directly: `python -m src.experiments.thesis_experiments`
- No `pyproject.toml`, `setup.py`, or `Makefile`

## Platform Requirements

**Development:**
- Python 3.12+
- `.venv/` virtual environment
- Internet access for yfinance (S&P 500, VIX, WTI data)

**Production:**
- CPU recommended (JAX CPU backend used; GPU optional)
- ~2GB RAM for SVI training (4000 steps on 2261 train samples)

---

*Stack analysis: 2026-05-11*

---
LINKS:AUTO
