# Technology Stack

**Analysis Date:** 2026-05-09

## Languages

**Primary:**
- Python 3.12.3 — all production code (`.venv/` created with `/usr/bin/python3.12`)

**CI Target:**
- Python 3.10 — GitHub Actions matrix in `.github/workflows/tests.yml`

## Runtime

**Environment:**
- CPython 3.12.3 (local dev venv), CPython 3.10 (CI)
- WSL2 (Linux 6.6.x, Microsoft kernel)
- CPU-only JAX backend — no GPU required; XLA thread counts auto-set in `scripts/run.py`

**Package Manager:**
- pip (no poetry/uv)
- Lockfile: `requirements.txt` — exact `==` pins for critical packages, `>=` only for non-critical data/dev tools

## Frameworks

**Bayesian Inference (CRITICAL — version-pinned, do not loosen):**
- NumPyro 0.20.0 — HDP-HMM probabilistic model; SVI and NUTS inference (`src/core/hdp_hmm.py`)
- JAX 0.9.1 — XLA-compiled tensor math; forward algorithm via `jax.lax.scan` (`src/core/hdp_hmm.py`)
- JAXlib 0.9.1 — JAX C++ backend (must exactly match JAX version)

**Classic ML / Statistics:**
- scikit-learn 1.8.0 — `sklearn.decomposition.PCA` in rolling PCA pipeline (`src/core/pca_utils.py`, `src/core/hmm_training.py`)
- hmmlearn 0.3.3 — `GaussianHMM` base class extended by `StudentTHMM` (used in `scripts/pipelines/train.py` fallback path)
- arch 8.0.0 — `arch_model` for GARCH(1,1) per-regime volatility models (`src/core/hmm_training.py`, `src/core/var_backtesting.py`)
- statsmodels 0.14.6 — `MLEModel` (linearized SV model), time-series utilities (`scripts/pipelines/train.py`)
- scipy 1.17.1 — `orthogonal_procrustes` (PCA alignment), `multivariate_t`, `gaussian_kde`, stats tests

**Data:**
- pandas 3.0.1 — DataFrames as the primary data structure throughout the entire pipeline
- numpy 2.4.3 — numerical arrays

**Visualization:**
- plotly 6.6.0 — interactive HTML dashboard (`figures/dashboard.html`); built by `scripts/pipelines/train.py::rebuild_dashboard()`
- matplotlib 3.9.2 — static diagnostic plots

**Data Collection:**
- yfinance 1.2.0 — Yahoo Finance OHLCV + VIX family (`src/features/collect.py`)
- fredapi >=0.5 — authenticated FRED API client (primary macro data path, `src/data/collect_macro.py`)
- pandas_datareader >=0.10 — unauthenticated FRED fallback, rate-limited (`src/data/collect_macro.py`)

**Dev / Infra:**
- python-dotenv >=1.0 — `.env` loading in `scripts/run.py`
- joblib 1.5.3 — model serialization to `.pkl` files in `models/`
- pytest 9.0.2 — test runner; 160+ tests in `tests/`

## Version Pinning (Hard Constraint)

Exact `==` pins are required for regime reproducibility. Breaking changes in JAX/NumPyro silently corrupt regime assignments.

- `jax==0.9.1` — **never loosen**
- `jaxlib==0.9.1` — **never loosen**
- `numpyro==0.20.0` — **never loosen**

CI job `check-version-pins` in `.github/workflows/tests.yml` rejects any PR that uses `>=` for JAX or NumPyro. See `requirements.txt` header comment.

## Configuration

**Central config:** `src/config.py` — single source of truth for all hyperparameters, file paths, feature lists, label mappings.

**Key config values:**
- `USE_HDP = True` — HDP-HMM (NumPyro) is the active backend (Phase 6 human override)
- `N_STATES = 3`, `N_STATES_RANGE = [3]` — K=3 locked after Phase 2.5.3 BIC + OOS validation
- `RANDOM_SEED = 42` — deterministic throughout
- `HDP_INFERENCE = 'svi'` — SVI inference (~5-10 min CPU); NUTS available for overnight runs
- `SVI_NUM_STEPS = 3000`, `SVI_LEARNING_RATE = 0.003`, `SVI_NUM_SAMPLES = 500`
- `FEATURE_SUBSET` — 14 features selected via walk-forward section selection (Phase 5/6)
- `VIX_BYPASS = True` — VIX appended directly to PCA dims (forces clustering on implied vol)
- `WALK_FORWARD_MODE = 'rolling'`, `WALK_FORWARD_TRAIN_YEARS = 5`
- `MAX_DATA_STALENESS_DAYS = 3` — staleness warning threshold
- `DATA_DIR = 'data'`, `MODEL_DIR = 'models'`, `FIGURE_DIR = 'figures'`, `CACHE_PATH = 'data/cache'`

**Environment:**
- `.env` file at project root — loaded by `scripts/run.py` via `python-dotenv`
- Key env var: `FRED_API_KEY` (optional; falls back to `pandas_datareader` if absent)
- Thread counts auto-set: `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `XLA_FLAGS`

## Serialized Artifacts

| File | Contents | Format |
|------|----------|--------|
| `models/hdp_params.pkl` | Trained HDP-HMM SVI parameters | joblib |
| `models/hdp_samples.pkl` | Posterior samples from trained guide | joblib |
| `models/hdp_metadata.json` | Run metadata (timestamp, config) | JSON |
| `models/pca_model.pkl` | Fitted rolling PCA | joblib |
| `models/regime_model.pkl` | Final assembled regime model | joblib |
| `data/regime_results.csv` | Primary output — regime labels + probabilities per trading day | CSV |
| `data/features_scaled.csv` | Expanding-window z-scored features | CSV |
| `data/features_transformed.csv` | log1p + winsorized features (pre-standardization) | CSV |
| `data/pca_components.csv` | PCA-projected feature matrix | CSV |
| `data/garch_params.json` | Per-regime GARCH(1,1) parameters | JSON |
| `data/macro_data.csv` | FRED macro indicators (yield curve, HY spread, NFCI) | CSV |
| `data/market_data.csv` | Raw aligned OHLCV + VIX series | CSV |

## Platform Requirements

**Development:**
- Python 3.12.3 in `.venv` (`source .venv/bin/activate`)
- `FRED_API_KEY` env var optional but recommended for reliable macro collection
- CPU multi-threading for JAX/XLA (auto-detected via `os.cpu_count()`)

**Production:**
- Linux (WSL2 confirmed; CI Ubuntu)
- No server deployment — pipeline runs as a local script
- GARCH VaR requires ≥50 obs per regime (`MIN_REGIME_OBS = 50`); falls back to static VaR if insufficient

## CI/CD

**Pipeline:** GitHub Actions (`.github/workflows/tests.yml`)
- Trigger: `workflow_dispatch` only (push/PR triggers commented out)
- Jobs run sequentially: `check-version-pins` → `test`
- Test suite includes: causality, bot integration, incremental collection, PCA caching, dashboard, full suite

---

*Stack analysis: 2026-05-09*
