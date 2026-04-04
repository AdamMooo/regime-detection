# Coding Conventions

**Analysis Date:** 2026-03-22 (updated)

## Naming Patterns

**Files:**
- `snake_case.py` — all Python source files (e.g. `collect.py`, `hdp_hmm.py`)
- `snake_case.csv`, `snake_case.pkl` — all data and model artifacts

**Functions:**
- `snake_case` for public functions: `fit_rolling_pca`, `compute_signals`, `build_features`, `prepare_features`, `expanding_standardize`
- `_leading_underscore_snake_case` for private helpers: `_fix_skew`, `_winsorize`, `_validate_features`, `_build_kde_surface`, `_diag_mvt_logpdf_batch`

**Classes:**
- `PascalCase`: `StudentTHMM`, `LinearizedSV`, `HDPModelAdapter`

**Constants:**
- `UPPER_SNAKE_CASE` for public config constants in `config.py`: `RANDOM_SEED`, `HDP_TRUNCATION`, `FEATURE_SUBSET`, `REGIME_NAMES`
- `_UPPER_SNAKE_CASE` for private module-level constants: `_REGIME_COLORS`, `_LOG_CHI2_MEAN`, `_LOG_TRANSFORM_COLS`, `_REGIME_SEVERITY`

**Variables:**
- `snake_case` throughout; no abbreviations except established domain shorthand (`pcs`, `sv`, `var`, `bic`, `rv`)

## Code Style

**Formatting:**
- No formatter config present (no `.prettierrc`, `pyproject.toml [tool.black]`, or `ruff.toml`)
- Style is consistent with PEP 8: 4-space indentation, single blank line between local blocks, two blank lines between top-level definitions
- Line length is not strictly enforced; long Plotly chain calls span multiple lines with parentheses

**Linting:**
- No linter config present; code is convention-driven

**Type Hints:**
- Used on all public function signatures; `pd.DataFrame`, `pd.Series`, `np.ndarray`, `dict`, `list`, `int | None` union syntax (Python 3.10+)
- Not used on private helpers consistently

## Import Organization

**Order:**
1. Standard library (`os`, `sys`, `warnings`, `json`, `logging`)
2. Third-party numerical (`numpy`, `scipy`, `pandas`, `sklearn`, `statsmodels`, `arch`, `jax`, `numpyro`)
3. Third-party data/viz (`yfinance`, `plotly`, `joblib`)
4. Local modules (`from config import ...`)

**Path Aliases:**
- `import numpy as np`
- `import pandas as pd`
- `import plotly.graph_objects as go`
- `import numpyro.distributions as dist`
- `import jax.numpy as jnp`
- No other aliases used

## Error Handling

**Patterns:**
- `assert len(df) >= 252` — data sufficiency guards in `collect.py`, `features.py`, `train.py`; fail-fast on bad data
- `try/except Exception as e:` around individual model fits (`LinearizedSV.fit()`, `arch_model.fit()`, per-regime SV/GARCH) — prints `[WARN]`, stores `None`, continues pipeline
- `run.py` catches stage-level errors with `except Exception as e:`, prints `[ERROR]`, exits on single-step runs
- `run.py` validates unknown commands against a `known` set
- No custom exception classes; all errors are bare `Exception`

**Example pattern:**
```python
try:
    res = model.fit(disp=False)
    sv_results[name] = res
except Exception as e:
    print(f"[WARN] SV fit failed for {name}: {e}")
    sv_results[name] = None
```

## Data Handling Conventions

**Index alignment:**
- All DataFrames use `pd.DatetimeIndex`; VIX family series reindexed to SPY trading-day index via `.reindex(ref_index).ffill()` in `collect.py`
- Explicit `pd.Series(..., index=...)` construction when creating new series inside functions

**None-guarded feature sections:**
- Each feature block in `features.py::build_features()` is wrapped: compute into local var, then `if local_var is not None: df[col] = local_var`; NaN columns dropped with `df.dropna()`

**DataFrames vs arrays:**
- Feature DataFrames kept as `pd.DataFrame` through `build_features()` / `prepare_features()`
- Converted to `np.ndarray` (`.values`) only at the point of model input (standardization, PCA fit, HMM fit)
- PCA scores returned as `np.ndarray`; labeled results assembled back into `pd.DataFrame` with date index

## Standardization Convention

**Feature pipeline (`features.py`) does NOT standardize.** It applies:
1. `_fix_skew()` — log1p on right-skewed features
2. `_winsorize()` — causal expanding-window percentile clipping
3. `_validate_features()` — diagnostics (ADF, VIF, PCA, JB)
4. Saves `features_transformed.csv`

**Standardization happens in `train.py`** via `expanding_standardize()`:
- Causal: row t uses mean/std from rows [0..t] only
- First 252 rows set to NaN (warm-up period)
- Used identically by both `train()` and `walk_forward()`

## Persistence Conventions

**Serialization:**
- `joblib.dump(obj, path)` / `joblib.load(path)` for all `.pkl` artifacts
- JSON (`json.dump`) for human-readable metadata (`models/hdp_metadata.json`)
- CSV via `pd.DataFrame.to_csv()` for all data artifacts
- Paths constructed from `config.MODEL_DIR`, `config.DATA_DIR`, `config.FIGURE_DIR` constants; never hardcoded strings

## Configuration Convention

**Single source of truth:**
- All tunable parameters live exclusively in `config.py`; no magic numbers in other files
- When adding a new parameter: add it to `config.py` first, then import it where needed
- `from config import PARAM_NAME` — specific named imports used throughout, not `import config as cfg`

## JAX / NumPy Conventions

**JAX:**
- CPU forced at startup: `jax.config.update("jax_platform_name", "cpu")`
- 64-bit precision enabled: `jax.config.update("jax_enable_x64", True)`
- Set at import time in `hdp_hmm.py`; must occur before any JAX computation
- JAX arrays (`jnp.ndarray`) used only inside `hdp_hmm.py`; converted via `.tolist()` / `np.array()` before leaving that module

**NumPy:**
- `np.random.seed(RANDOM_SEED)` called at pipeline start in `train.py::train()`

## Visualization Conventions

**Plotly:**
- All charts use `go.Figure()` / `make_subplots()` — no Plotly Express
- `_REGIME_COLORS` dict in `train.py` maps regime names to hex colors (consistent palette across all tabs)
- Dashboard HTML built by `_write_dashboard_html(tabs)` which injects CSS/JS inline; `include_plotlyjs='cdn'` for the first tab figure, `False` for subsequent tabs to reduce file size
- Figures returned from `_build_*_tab()` private functions; added to `tabs: list[tuple[str, go.Figure]]`

---

*Convention analysis: 2026-03-22 (updated)*
