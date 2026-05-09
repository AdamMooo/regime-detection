# Coding Conventions

**Analysis Date:** 2026-05-09

## Naming Patterns

**Files:**
- Module files: `snake_case.py` — `inference.py`, `hmm_training.py`, `pca_utils.py`
- Test files: `test_<subject>.py` — `test_causality.py`, `test_bot_integration.py`
- Analysis scripts: `analyze_<topic>.py` — `analyze_feature_selection.py`, `analyze_signal_quality.py`
- Private helpers: leading underscore prefix — `_winsorize`, `_fit_hmm`, `_fit_one_regime`

**Functions:**
- Public API: `snake_case` — `expanding_standardize`, `filtered_probs`, `filtered_labels`, `select_states_bic`
- Private helpers: `_snake_case` — `_hmm_n_params`, `_hmm_bic`, `_best_perm_agreement`, `_fit_one_regime`
- Test functions: `test_<what_it_checks>` — `test_uses_only_past_data`, `test_warmup_is_nan`

**Variables:**
- `snake_case` throughout — `spy_returns`, `name_map`, `prob_sum`, `n_states`
- DataFrame columns: hyphenated regime names in data (`Low-Vol`, `Medium-Vol`, `High-Vol`)
- Constants: `UPPER_SNAKE_CASE` in `src/config.py` — `RANDOM_SEED`, `N_STATES`, `LABEL_MAPPING`

**Classes:**
- `PascalCase` — `StudentTHMM`, `LinearizedSV`, `MockBotSignalHandler`, `Pipeline`
- Test classes grouped by subject: `TestExpandingStandardize`, `TestFilteredProbs`, `TestBotIntegration`

**Regime Labels (two canonical formats):**
- Internal names (human-readable): `Low-Vol`, `Medium-Vol`, `High-Vol` (hyphenated, title-case)
- Bot labels (downstream API): `LOW_VOL`, `MED_VOL`, `HIGH_VOL` (UPPER_SNAKE_CASE)
- Mapping source of truth: `src/config.py::LABEL_MAPPING` — never hardcode elsewhere

## Module Structure

**Module docstring pattern** (every `src/` module has this):
```python
"""One-line summary.

Paragraph describing what this module handles.

Functions
---------
function_name(params)
    One-line description

Classes
-------
ClassName
    One-line description
"""
```

**Section separators** — used to divide logical sections within files:
```python
# ===================================================================
# Section Name
# ===================================================================
```
or in test files:
```python
# ═══════════════════════════════════════════════════════════════════
# Section Name — description
# ═══════════════════════════════════════════════════════════════════
```

## Import Organization

**Order (observed in `src/core/` modules):**
1. Standard library — `import logging`, `import warnings`, `from itertools import permutations`
2. Third-party — `import numpy as np`, `import pandas as pd`, `from hmmlearn import hmm`
3. Internal — `from src.config import ...`, `from src.core.inference import ...`

**Path aliases:** None. Direct module paths used throughout (`from src.core.pca_utils import fit_rolling_pca`).

**Test file path injection** (legacy pattern in some tests — not preferred):
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
```
Newer tests import directly without `sys.path` manipulation (e.g., `test_pipeline_stages.py`, `test_train_refactor.py`).

## Docstrings

**NumPy-style docstrings** used on all public functions:
```python
def expanding_standardize(X_raw, min_warmup=252):
    """Expanding-window z-score: row t uses mean/std from [0..t] only.

    This is a causal transformation: standardization at time t uses only data
    from time 0 to t, not future data. This is essential for live trading.

    Parameters
    ----------
    X_raw : ndarray (T, D)
        Raw feature matrix
    min_warmup : int
        First N rows are set to NaN (statistics too unstable)

    Returns
    -------
    X_scaled : ndarray (T, D)
        Standardized features (NaN for first min_warmup rows)
    """
```

**Private helpers** get one-line docstrings only:
```python
def _fit_one_regime(r, spy_returns, labels, label_series, name_map, cond_vol_all):
    """Fit GARCH for a single regime — called in parallel by fit_regime_garch."""
```

## Error Handling

**Assertion style in tests:** Plain `assert` with descriptive message strings:
```python
assert bot_label in valid_labels, (
    f"Invalid bot_label: {bot_label}. Must be one of {valid_labels}"
)
```

**`np.testing` / `pd.testing` for numeric checks** — always preferred over manual comparison:
```python
np.testing.assert_allclose(result_full[250], result_trunc[250], rtol=1e-12,
    err_msg="expanding_standardize leaked future data into row 250")
pd.testing.assert_series_equal(data['A'].iloc[:251], result['A'].iloc[:251], ...)
```

**Logging:** `logging.getLogger(__name__)` at module level in every `src/` module. Logger named `logger`.

## Hard Constraints Enforced by Convention

These are non-negotiable rules enforced by tests and CI:

1. **No K-means** — probabilistic regime detection only. Use `StudentTHMM` / NumPyro.
2. **No lookahead** — all transformations use expanding windows (past data only). Never use smoothed probabilities in production; use `filtered_probs()`, not `model.predict_proba()`.
3. **K=3 regimes** — `N_STATES = 3` in `src/config.py`. Labels: `Low-Vol`, `Medium-Vol`, `High-Vol`.
4. **NumPyro/JAX exact pins** — `jax==0.9.1`, `numpyro==0.20.0` (== operator, never >=). CI rejects loosened pins.
5. **Module size gate** — `src/core/*.py` files must be ≤ 500 lines (except `hdp_hmm.py`, documented exception). Verified by `test_train_refactor.py::test_module_size`.
6. **No circular imports** — verified by `test_train_refactor.py::test_no_circular_imports`.
7. **Bot signal schema** — `compute_signals()` output must include `bot_label`, `awareness`, `date`. Verified by `tests/test_bot_integration.py`.
8. **GARCH VaR only** — static VaR is deprecated. Use `garch_var_95` from `signals.py` for all risk limits.

## Configuration Pattern

All tunable parameters live in `src/config.py`. Never hardcode values in implementation modules. Import from config:
```python
from src.config import T_DF, HMM_ITER, REGIME_HOLD_DAYS, RANDOM_SEED, N_STATES
```

Key config constants:
- `RANDOM_SEED = 42` — used everywhere for reproducibility
- `N_STATES = 3` — regime count (do not change without coordination)
- `LABEL_MAPPING` — internal name → bot label dict (source of truth)
- `REGIME_NAMES` — dict of `n_states → [name list]` for all supported K values
- `DATA_DIR` — path to `data/` directory for file I/O

## Commit Conventions

Conventional Commits format (enforced by `gsd-validate-commit.sh` hook):
```
<type>(<scope>): <description>
```

Types observed in git history:
- `feat` — new functionality
- `fix` — bug fix (e.g., `fix(dashboard): drop NaN rows before fit_rolling_pca`)
- `test` — test additions (e.g., `test(07): complete UAT`)
- `docs` — documentation (e.g., `docs(state): record phase 9 context session`)
- `chore` — maintenance (e.g., `chore: clean up stale Claude settings`)
- `refactor` — code restructure without behavior change

Breaking changes to the `MacroRegimeDetector` API must be coordinated with `algo-trading-bot` and `portfolio-manager` projects before committing.

## Dev Workflow (GSD)

1. Read `.planning/STATE.md` to determine current phase
2. Read current phase `PLAN.md` in `.planning/phases/<phase>/`
3. Activate venv: `source .venv/bin/activate`
4. Run tests before and after changes: `pytest tests/ -v --tb=short`
5. Run priority tests explicitly when modifying core modules: `pytest tests/test_causality.py tests/test_bot_integration.py -v`
6. Skip slow tests during development: `pytest tests/ -v -m "not slow"`
7. Update `NOTES.md` with progress + next action before session close
8. Commit with Conventional Commits format

---

*Convention analysis: 2026-05-09*
