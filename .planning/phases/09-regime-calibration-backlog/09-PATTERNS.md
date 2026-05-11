# Phase 9: Regime Calibration — Pattern Map

**Mapped:** 2026-05-09
**Files analyzed:** 6 (4 modified, 1 new diagnostic script, 3 new regression test files)
**Analogs found:** 6 / 6

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/core/var_backtesting.py` | utility (bug fix) | transform | `src/core/hmm_training.py::fit_regime_garch()` | exact — same GARCH scale pattern |
| `src/core/orchestrator.py` | utility (bug fix) | transform | `src/core/hmm_training.py::_best_perm_agreement()` | role-match — label alignment logic |
| `scripts/pipelines/train.py::rebuild_dashboard()` | pipeline stage (bug fix) | batch | `scripts/pipelines/train.py` line 2331 | exact — same file, same pattern one block up |
| `src/config.py` | config | — | `src/config.py` (self-referential) | exact |
| `scripts/analysis/analyze_vol_distribution.py` (new) | utility/diagnostic | batch | `scripts/analysis/analyze_regime_characterization.py` | exact — standalone load → analyze → print |
| `tests/test_phase9_*.py` (3 new test files) | test | — | `tests/test_var_backtesting.py`, `tests/test_oos_validation.py` | exact — same pytest class structure |

---

## Pattern Assignments

### `src/core/var_backtesting.py` — GARCH unit fix (Plan 1)

**Analog:** `src/core/hmm_training.py::fit_regime_garch()` and `compute_var_backtest_garch()`

**The bug — current code (line 247):**
```python
y = spy_returns.dropna() * 10000  # scale to 1-1000 range for GARCH optimizer
```
`compute_var_backtest_garch()` scales by `× 10000`, but `fit_regime_garch()` (line 437) scales by `× 100000`. These differ by 10×, causing parameter estimates that are internally consistent but produce wildly wrong annualized vol when back-converted.

**The canonical scale pattern** (`hmm_training.py` lines 397–413):
```python
# _fit_one_regime — the production GARCH path
y = (spy_returns[mask].dropna()) * 100000   # scale: 1e5
am = arch_model(y, vol='GARCH', p=GARCH_P, q=GARCH_Q, mean='Zero', dist=GARCH_DIST)
res = am.fit(disp='off')
# Annualized vol back-conversion (line 407):
mean_vol_ann = vol_in_regime.mean() / 100000 * np.sqrt(252) * 100
```
The pattern is: `input × 1e5` → fit → `output ÷ 1e5 × √252 × 100` → annualized %.

**Fix pattern for `compute_var_backtest_garch()` (lines 247–254):**
```python
# BEFORE (wrong scale — produces mean_vol=700%+):
y = spy_returns.dropna() * 10000
am = arch_model(y, vol='GARCH', p=1, q=1, mean='Zero', dist='normal')
res = am.fit(disp='off')
cond_vol_scaled = res.conditional_volatility.values
cond_vol = cond_vol_scaled / 10000  # back to decimal for output

# AFTER (match hmm_training.py canonical scale):
y = spy_returns.dropna() * 100000
am = arch_model(y, vol='GARCH', p=1, q=1, mean='Zero', dist='normal')
res = am.fit(disp='off')
cond_vol_scaled = res.conditional_volatility.values
cond_vol = cond_vol_scaled / 100000  # back to decimal for output
```

Also fix `compare_var_methods()` lines 319 and 327 — same `× 10000` / `÷ 10000` pattern must become `× 100000` / `÷ 100000`.

**Regression assertion to add (D-05):** immediately after `res = am.fit(disp='off')`:
```python
mean_vol_ann = res.conditional_volatility.values.mean() / 100000 * np.sqrt(252) * 100
assert mean_vol_ann < 100.0, (
    f"GARCH mean_vol={mean_vol_ann:.1f}% — likely unit error (should be <100%)"
)
```
Pattern: silent assertion, not try/except — matches existing `assert best_m is not None` in `orchestrator.py` line 115.

**try/except preservation pattern** (`hmm_training.py` lines 402–413):
```python
try:
    res = am.fit(disp='off')
    ...
except Exception:
    return r, None, f"  {name_map[r]:12s}: GARCH fit failed (n={len(y)})"
```
The GARCH fit is always wrapped in `try/except Exception` for graceful skip. Do not change this structure when fixing units.

---

### `src/core/orchestrator.py::walk_forward()` — Hungarian label alignment (Plan 2)

**Analog:** `src/core/hmm_training.py::_best_perm_agreement()` (lines 186–211) — the existing permutation-search approach that Hungarian replaces.

**Current broken pattern (lines 119–133):**
```python
# Assign names using VIX-rank order — same logic as label_regimes() in hmm_training.
# BUG: VIX-rank fold-by-fold does not guarantee consistent mapping across folds
# when fold HMMs discover different state orderings. Result: 8 distinct regime_name_oos.
train_labels = filtered_labels(best_m, pc_train, hold_days=REGIME_HOLD_DAYS)
vix_train = market['VIX'].reindex(train_feats_valid.index).values
tl = train_labels[:len(vix_train)]
regime_vix = {}
for r in range(n_states):
    mask = (tl == r)
    regime_vix[r] = float(np.nanmean(vix_train[mask])) if mask.sum() > 0 else 0.0
sorted_by_vix = sorted(regime_vix, key=lambda k: regime_vix[k])
names = REGIME_NAMES.get(n_states, [f'Regime-{i}' for i in range(n_states)])
fold_name_map = {sorted_by_vix[i]: names[i] for i in range(n_states)}
```

**Hungarian replacement pattern (D-06):**

Import to add at top of `orchestrator.py`:
```python
from scipy.optimize import linear_sum_assignment
```

Replacement block: after `raw_preds = filtered_labels(...)` and `train_labels = filtered_labels(...)`, compute VIX-rank as IS reference (once, from the first fold or from the IS model), then align each fold's states to IS states via Hungarian:
```python
# Build IS reference: VIX-rank name map for this fold's training labels
train_labels = filtered_labels(best_m, pc_train, hold_days=REGIME_HOLD_DAYS)
vix_train = market['VIX'].reindex(train_feats_valid.index).values
tl = train_labels[:len(vix_train)]

# VIX-rank reference (Low=low VIX, High=high VIX)
regime_vix = {}
for r in range(n_states):
    mask = (tl == r)
    regime_vix[r] = float(np.nanmean(vix_train[mask])) if mask.sum() > 0 else 0.0
is_sorted = sorted(regime_vix, key=lambda k: regime_vix[k])  # IS state indices, VIX-ascending
names = REGIME_NAMES.get(n_states, [f'Regime-{i}' for i in range(n_states)])
is_name_map = {is_sorted[i]: names[i] for i in range(n_states)}  # IS reference map

# Hungarian alignment: cost matrix = overlap between fold raw_preds and IS train_labels
# cost[i, j] = -count(raw_preds==i AND train_labels==j) — maximize overlap
raw_preds_arr = np.array(raw_preds)
overlap = np.zeros((n_states, n_states), dtype=int)
# align raw_preds (test) to train_labels (IS) on the training slice
tl_arr = tl[:len(raw_preds_arr)] if len(tl) >= len(raw_preds_arr) else np.pad(tl, (0, len(raw_preds_arr)-len(tl)))
for i in range(n_states):
    for j in range(n_states):
        overlap[i, j] = int(((raw_preds_arr == i) & (tl_arr == j)).sum())
row_ind, col_ind = linear_sum_assignment(-overlap)  # maximize overlap
# col_ind[i] = which IS state fold-state i corresponds to
fold_name_map = {row_ind[k]: is_name_map[col_ind[k]] for k in range(n_states)}
```

**Regression assertion to add (D-07):** after the while loop, before `return valid, name_map`:
```python
# D-07: OOS label count must be <= K (regression guard for fold alignment)
n_distinct = oos_name_labels.dropna().nunique()
assert n_distinct <= n_states, (
    f"walk_forward: {n_distinct} distinct OOS regime names (expected <= {n_states}). "
    "Fold alignment failure — check Hungarian matching."
)
```

**Import pattern** (`orchestrator.py` lines 14–19 — add scipy import):
```python
from src.config import (
    RANDOM_SEED, PCA_ROLLING_WINDOW, REGIME_HOLD_DAYS, VIX_BYPASS,
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS, WALK_FORWARD_MODE,
    COV_TYPE, REGIME_NAMES,
)
from src.core.inference import expanding_standardize, _fit_hmm, filtered_labels
from scipy.optimize import linear_sum_assignment  # add this line
```

---

### `scripts/pipelines/train.py::rebuild_dashboard()` — NaN guard before PCA (Plan 1)

**Analog:** The same function, three lines above the crash site (line 2331):
```python
feat_scaled = feat_scaled.dropna()  # warm-up NaN rows crash sklearn PCA
```

This pattern is already established in `rebuild_dashboard()` at line 2331. The crash occurs because `features_df` (passed as the last arg to `build_interactive_dashboard()` at line 2392) still contains NaN rows — it is `feat_scaled` after the dropna at line 2331, but the alignment at line 2340 re-introduces NaN via `market.loc[feat_scaled.index]`.

**NaN crash site:** `build_interactive_dashboard()` calls `_build_feature_health_tab(features_df, ...)` at line 597. Inside `_build_feature_health_tab()` (line 1658):
```python
X = features_df.values  # passed directly to LinearRegression and corr() — crashes if NaN
```

**Fix pattern (D-03):** add a `dropna()` guard on `features_df` before it enters `_build_feature_health_tab()`. Two equivalent insertion points:

Option A — inside `build_interactive_dashboard()` before line 597:
```python
if features_df is not None:
    features_df = features_df.dropna()          # guard: NaN rows crash PCA in health tab
    fig_health = _build_feature_health_tab(features_df, pcs, pca_model)
```

Option B — first line of `_build_feature_health_tab()` (line 1613):
```python
features_df = features_df.dropna()             # D-03: guard warm-up NaN rows
cols = list(features_df.columns)
```

Option B is preferred: it is self-contained (the guard lives where the crash occurs), matches the `rebuild_dashboard()` pattern of dropping NaN at the point of use, and requires no caller changes.

**Established dropna pattern** (lines 2331–2337 — the exact template to copy):
```python
feat_scaled = feat_scaled.dropna()  # warm-up NaN rows crash sklearn PCA

# Align to valid dates and ensure absolutely no NaN before PCA (defensive)
if valid_dates[0] in feat_scaled.index:
    feat_for_pca = feat_scaled.loc[valid_dates].dropna()
else:
    feat_for_pca = feat_scaled.dropna()
```
The comment style (`# guard: NaN rows crash sklearn PCA`) should match this.

---

### `src/config.py` — VOL_BRACKETS calibration (Plan 3)

**Current values (lines 166–171):**
```python
VOL_BRACKETS = [
    (0,   10,  'Low-Vol'),
    (10,  18,  'Moderate-Vol'),
    (18,  28,  'Elevated-Vol'),
    (28, 999,  'Crisis-Vol'),
]
```

**Change pattern (D-09):** modify thresholds only — do not change the structure, tuple format, or label names. The diagnostic (Plan 3 diagnostic script) determines which thresholds to shift. Example of a valid edit to reduce High-Vol dominance:
```python
VOL_BRACKETS = [
    (0,   12,  'Low-Vol'),       # widened from 10
    (12,  22,  'Moderate-Vol'),  # shifted up
    (22,  32,  'Elevated-Vol'),  # shifted up
    (32, 999,  'Crisis-Vol'),
]
```
These are placeholders — actual values come from the diagnostic run.

**Downstream impact:** `VOL_BRACKETS` is consumed by two callers:
- `src/core/hdp_hmm.py` imports `VOL_BRACKETS` at line 43 (used in `label_regimes_hdp()`)
- `src/core/orchestrator.py` imports from `src.config` (but does not directly reference `VOL_BRACKETS` in the current code — the VIX-rank path in walk_forward uses `REGIME_NAMES`, not `VOL_BRACKETS`)

Config change pattern: add a comment above the modified block referencing Phase 9:
```python
# Phase 9 (Plan 3): thresholds tuned to bring High-Vol frequency into 15-25% target
# Diagnostic run: scripts/analysis/analyze_vol_distribution.py
VOL_BRACKETS = [...]
```

---

### `scripts/analysis/analyze_vol_distribution.py` (new diagnostic, Plan 3)

**Analog:** `scripts/analysis/analyze_regime_characterization.py` — identical structure: standalone script, loads CSVs, prints analysis, optionally saves figures.

**Template structure** (lines 1–80 of `analyze_regime_characterization.py`):
```python
"""
Analyze [topic]: [description].

This script runs standalone (not imported by the pipeline).
It loads regime results and price data to generate [analysis].

Run: python scripts/analysis/analyze_vol_distribution.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.config import DATA_DIR, FIGURE_DIR, VOL_BRACKETS

REPORTS_DIR = 'reports'


def load_regime_results():
    """Load regime results from CSV."""
    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if os.path.exists(results_path):
        return pd.read_csv(results_path, index_col=0, parse_dates=True)
    return None


def load_market_data():
    """Load market data."""
    market_path = os.path.join(DATA_DIR, 'market_data.csv')
    if os.path.exists(market_path):
        return pd.read_csv(market_path, index_col=0, parse_dates=True)
    return None
```

**Additional pattern for vol distribution analysis** (`analyze_regime_characterization.py` lines 54–82):
```python
def analyze_regime_statistics(results, market):
    results_aligned = results.loc[results.index.intersection(market.index)]
    market_aligned = market.loc[results_aligned.index]
    regime_col = 'regime_name' if 'regime_name' in results_aligned.columns else results_aligned.columns[0]
    regimes = results_aligned[regime_col]
    spy_close = market_aligned.get('SPY_close')
    if spy_close is not None:
        returns = np.log(spy_close / spy_close.shift(1)).dropna()
        for regime in sorted(regimes.dropna().unique()):
            mask = regimes == regime
            ...
```

**Diagnostic-specific additions** (not in template, must be written):
```python
def analyze_high_vol_frequency(results):
    """Check what fraction of days fall in each VOL_BRACKET name."""
    regime_col = 'regime_name' if 'regime_name' in results.columns else 'regime_name_hdp'
    counts = results[regime_col].value_counts(normalize=True) * 100
    print("\nRegime frequency (% of all days):")
    for name, pct in counts.items():
        flag = " <-- HIGH-VOL TARGET: 15-25%" if "High" in name or "Crisis" in name or "Elevated" in name else ""
        print(f"  {name:<20s}: {pct:.1f}%{flag}")
    return counts
```

**`if __name__ == '__main__':` pattern:**
```python
if __name__ == '__main__':
    results = load_regime_results()
    market = load_market_data()
    if results is None or market is None:
        print("ERROR: data files not found. Run the pipeline first.")
    else:
        analyze_high_vol_frequency(results)
        analyze_regime_statistics(results, market)
```

---

## Shared Patterns

### Error handling — try/except for GARCH fits
**Source:** `src/core/hmm_training.py` lines 398–413
**Apply to:** Any new GARCH fitting code in `var_backtesting.py`
```python
try:
    res = am.fit(disp='off')
    # ... extract params
except Exception:
    return r, None, f"  {name_map[r]:12s}: GARCH fit failed (n={len(y)})"
```
Never use bare `except:` (matches existing linting conventions in the file).

### Regression assertion style
**Source:** `src/core/orchestrator.py` line 115
**Apply to:** All three new regression assertions (D-05, D-07)
```python
assert best_m is not None
```
Use bare `assert` (not `if ... raise`). Place immediately after the operation being guarded. Include a descriptive failure message string.

### Test file structure — pytest class + fixtures
**Source:** `tests/test_var_backtesting.py` lines 26–55
**Apply to:** All three new regression test files
```python
@pytest.fixture
def spy_returns_sample():
    """Generate realistic SPY returns for testing."""
    np.random.seed(42)
    ...
    return pd.Series(returns, index=date_index), regime_labels


class TestGarchVarFix:
    """Verify GARCH unit fix produces sane volatility estimates."""

    def test_mean_vol_below_100_pct(self, spy_returns_sample):
        """After unit fix, mean annualized vol must be < 100%."""
        ...
        assert mean_vol < 1.0, f"mean_vol={mean_vol:.1%} — GARCH unit bug not fixed"
```
Test files: one class per fix, fixtures at module level, docstrings on every test method.

### Import style
**Source:** `src/core/var_backtesting.py` lines 23–31 and `src/core/orchestrator.py` lines 14–20
```python
import logging
import numpy as np
import pandas as pd
from scipy.stats import binom, chi2

from src.config import VAR_ALPHA
```
Standard-library first, then third-party (alphabetical), then blank line, then `src.*` imports.

### Config-only magic numbers
**Source:** `src/config.py` (all constants)
**Apply to:** Plan 3 threshold changes
All numerical thresholds go in `src/config.py` only — the diagnostic script reads `VOL_BRACKETS` from config, never hardcodes bracket values inline.

---

## No Analog Found

None — all files have close analogs in the codebase.

---

## Metadata

**Analog search scope:** `src/`, `scripts/`, `tests/`
**Files read:** `src/core/var_backtesting.py`, `src/core/orchestrator.py`, `src/core/hmm_training.py`, `src/core/hdp_hmm.py`, `src/pipeline/stages.py`, `src/config.py`, `scripts/pipelines/train.py` (targeted sections), `scripts/analysis/analyze_regime_characterization.py`, `tests/test_var_backtesting.py`, `tests/test_walk_forward.py`, `tests/test_calibration.py`, `tests/test_pipeline_stages.py`, `tests/test_oos_validation.py`
**Pattern extraction date:** 2026-05-09
