# Codebase Structure

**Analysis Date:** 2026-03-22 (updated)

## Directory Layout

```
Regime-Detection/
├── run.py              # CLI entry point — orchestrates all pipeline stages
├── config.py           # All tunable parameters and paths (single source of truth)
├── collect.py          # Stage 1: Download market data via yfinance (93 lines)
├── features.py         # Stage 2: Feature engineering (17 indicators, 435 lines)
├── analyze.py          # Stage 3: Interactive EDA report (optional, 235 lines)
├── train.py            # Stage 4: Rolling PCA → HMM → SV/GARCH (1452 lines)
├── dashboard.py        # Interactive 7-tab Plotly dashboard builder (1549 lines)
├── hdp_hmm.py          # Bayesian HDP-HMM model — NumPyro + JAX (729 lines)
├── signals.py          # Regime awareness engine — translates model output (367 lines)
├── trust.py            # Trust scorecard — aggregates 8 validation checks into PASS/WARN/FAIL
├── requirements.txt    # Python dependencies (semver ranges, not pinned)
├── README.md           # Project documentation
├── data/               # Pipeline data artifacts (CSV)
│   ├── market_data.csv         # Raw aligned OHLCV + VIX family
│   ├── features_transformed.csv# 17 engineered features (log1p + causal winsorized)
│   ├── features_scaled.csv     # Expanding-window standardized (saved by train.py for rebuild_dashboard)
│   └── regime_results.csv      # Final regime labels + probabilities + OOS labels
├── models/             # Serialized model artifacts (joblib PKL + JSON)
│   ├── pca_model.pkl           # Last-window PCA object
│   ├── hmm_model.pkl           # HMM model (classic or HDPModelAdapter)
│   ├── hdp_params.pkl          # HDP posterior mean parameters
│   ├── hdp_samples.pkl         # HDP posterior samples (SVI_NUM_SAMPLES)
│   └── hdp_metadata.json       # Human-readable HDP diagnostics
├── tests/             # pytest test suite (28 tests)
│   ├── conftest.py            # Shared fixtures (rng, synthetic_array, synthetic_features)
│   ├── test_causality.py      # 10 tests — forward-only guarantees
│   ├── test_oos_validation.py # 5 tests — OOS agreement, separation
│   ├── test_calibration.py    # 5 tests — ECE computation
│   ├── test_trust_scorecard.py# 5 tests — trust scorecard aggregation
│   └── test_validation.py     # 3 tests — VaR backtest
├── figures/            # Generated HTML visualizations
│   ├── dashboard.html          # 7-tab interactive Plotly dashboard
│   └── feature_analysis.html   # Feature EDA report
└── .venv/              # Python virtual environment (not committed)
```

## Directory Purposes

**Root (Python source):**
- Purpose: All source code lives flat at project root — no `src/` subdirectory
- Key files: `run.py` (entry), `config.py` (settings), `collect.py`, `features.py`, `analyze.py`, `train.py`, `hdp_hmm.py`, `signals.py`, `trust.py`

**`data/`:**
- Purpose: Pipeline CSV outputs; read/written by pipeline stages
- Contains: Raw and engineered time-series data, regime labels, standardized features
- Key files: `market_data.csv` (Stage 1), `features_transformed.csv` (Stage 2), `features_scaled.csv` (Stage 4), `regime_results.csv` (Stage 4)
- Generated: Yes — created by pipeline stages
- Note: Legacy files `features_raw.csv` and `scaler.pkl` may exist from old runs but are no longer produced or consumed

**`models/`:**
- Purpose: Serialized model artifacts persisted between pipeline runs
- Contains: `*.pkl` files (via `joblib`), `hdp_metadata.json`
- Key files: `hmm_model.pkl`, `pca_model.pkl`, `hdp_params.pkl`, `hdp_samples.pkl`
- Generated: Yes — created by `train.py`
- Note: Legacy `scaler.pkl` may exist from old runs but is no longer produced or consumed

**`figures/`:**
- Purpose: Generated HTML report outputs
- Contains: Self-contained Plotly HTML files (include embedded JavaScript)
- Key files: `dashboard.html` (~large), `feature_analysis.html`
- Generated: Yes

## Key File Locations

**Entry Points:**
- `run.py`: CLI orchestrator; `python run.py [step]`
- `run.py::main()` line 106: Step dispatch logic

**Configuration:**
- `config.py`: ALL tunable parameters — tickers, date range, feature windows, PCA settings, HMM/HDP settings, GARCH settings, validation settings, output paths

**Core Logic:**
- `train.py::train()`: Full in-sample training pipeline (line 2541)
- `train.py::expanding_standardize()`: Causal z-score shared by train + walk_forward (line 62)
- `train.py::fit_rolling_pca()`: Rolling PCA with Procrustes alignment (line 198)
- `train.py::filtered_probs()` / `filtered_labels()`: Causal forward-only regime assignment (lines 115, 150)
- `train.py::walk_forward()`: OOS validation with aligned pipeline (line 556)
- `train.py::build_interactive_dashboard()`: 7-tab Plotly dashboard builder (line 1040)
- `hdp_hmm.py::fit_hdp_hmm()`: NumPyro SVI/NUTS inference entry point (line 172)
- `hdp_hmm.py::hdp_hmm_model()`: NumPyro probabilistic model definition (line 95)
- `features.py::build_features()`: 17-feature engineering (line 86)
- `features.py::_winsorize()`: Causal expanding-window winsorization (line 254)
- `features.py::_validate_features()`: ADF + VIF + PCA + JB diagnostics (line 276)
- `signals.py::compute_signals()`: Regime awareness computation (line 338)

**Testing:**
- `tests/` directory with 28 tests across 5 files + `conftest.py` shared fixtures
- `trust.py::compute_trust_scorecard()`: Aggregates 8 validation checks (line-level entry point)

## Naming Conventions

**Files:**
- `snake_case.py` — all Python source files (e.g., `hdp_hmm.py`, `collect.py`)
- `snake_case.csv`, `snake_case.pkl` — all data/model artifacts

**Directories:**
- `lowercase/` with no hyphens (e.g., `data/`, `models/`, `figures/`)

**Functions:**
- `snake_case` for public functions: `fit_rolling_pca`, `compute_signals`, `build_features`
- `_leading_underscore` for private/internal helpers: `_fix_skew`, `_winsorize`, `_build_kde_surface`

**Classes:**
- `PascalCase`: `StudentTHMM`, `LinearizedSV`, `HDPModelAdapter`

**Constants (in `config.py`):**
- `UPPER_SNAKE_CASE`: `RANDOM_SEED`, `HDP_TRUNCATION`, `FEATURE_SUBSET`

**Private module-level items:**
- `_LEADING_UNDERSCORE_UPPER` for module-level private constants: `_REGIME_COLORS`, `_LOG_CHI2_MEAN`, `_LOG_TRANSFORM_COLS`

## Where to Add New Code

**New feature indicator:**
- Add computation to `features.py::build_features()` (follow existing pattern with `None`-guarded sections)
- Add name to `CURATED_FEATURES` list in `features.py`
- If including in PCA: add to `FEATURE_SUBSET` list in `config.py`
- If right-skewed: add to `_LOG_TRANSFORM_COLS` in `features.py`

**New regime visualization / dashboard tab:**
- Add a `_build_<tab_name>_tab()` function in `train.py` (follow existing pattern returning `go.Figure`)
- Append `(label, fig)` tuple to the `tabs` list inside `build_interactive_dashboard()` (`train.py` ~line 1040)

**New model variant:**
- Add training logic in `train.py::train()` behind a new config flag in `config.py`
- Save artifacts to `models/` using `joblib.dump()`

**New data source:**
- Add download logic to `collect.py::collect()`
- Add config (series name, column name) to `config.py`

**New CLI command:**
- Add `elif step == 'my_command':` branch in `run.py::main()`
- Add command name to the `known` set in `run.py`

**New regime awareness metric:**
- Add computation to `signals.py` (private helper function `_my_metric()`)
- Call from `compute_signals()` and include in returned dict

## Special Directories

**`.venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (via `python -m venv .venv`)
- Committed: No

**`.gsd/`:**
- Purpose: GSD codebase mapping analysis documents and execution plan
- Generated: By AI tooling
- Committed: Optional

---

*Structure analysis: 2026-03-22 (updated)*
