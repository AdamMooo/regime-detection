# Phase 6: Model Architecture Experiments - Research

**Researched:** 2026-04-20
**Domain:** HDP-HMM vs StudentTHMM comparison, Python module refactoring
**Confidence:** HIGH — this phase operates entirely on the local codebase; all findings are verified by reading source files

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**HDP-HMM Evaluation (MODEL-02)**
- D-01: Primary comparison metrics are OOS regime accuracy AND regime stability (dwell time). HDP-HMM must outperform StudentTHMM on BOTH dimensions.
- D-02: Inference mode for HDP-HMM: SVI only (`HDP_INFERENCE='svi'`). NUTS is off the table.
- D-03: Win threshold: +2 percentage points OOS accuracy AND meaningfully longer average dwell time. Below this bar, StudentTHMM stays.
- D-04: Use the same OOS test split used in Phase 4/5 diagnostics.
- D-05: In-sample looks good; OOS regime shading on HTML dashboard looks poor — skeptical prior going in.

**Dead Code Outcome**
- D-06: If HDP-HMM loses: delete `hdp_hmm.py` entirely and remove all references. No DEPRECATED comments — clean removal. Decision documented in MODEL_CARD.md.
- D-07: If HDP-HMM wins: set `USE_HDP=True` as default; keep StudentTHMM as fallback.

**Refactor Strategy (MODEL-03)**
- D-08: Split by concern, not by caller.
- D-09: `evaluation.py` → `evaluation.py` + `var_backtesting.py` + `forward_returns.py`
- D-10: `hmm_training.py` → extract `pca_utils.py` (PCA functions + LinearizedSV); `hmm_training.py` retains BIC/stability/labeling
- D-11: If HDP deleted, its 844 lines count toward MODEL-03 scope — remaining splits may be smaller.
- D-12: Update all imports cleanly in `orchestrator.py`, `signals.py`, and all scripts. No re-export indirection. Public API (`detect()`, `fit()` in `signals.py`) does not change.

**Decision Documentation (MODEL-02)**
- D-13: USE_HDP verdict goes in a new "Model Architecture Decision" section in `docs/MODEL_CARD.md` with comparison numbers and rationale.

### Claude's Discretion
- Exact split point within `evaluation.py` if concern-based split leaves a file slightly over 500 lines
- Whether `LinearizedSV` goes into `pca_utils.py` or its own `sv_model.py`
- Format of the MODEL_CARD.md comparison table (columns, ordering)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MODEL-02 | Decision on USE_HDP documented and locked — either re-enable HDP-HMM with evidence it outperforms StudentTHMM, or formally deprecate and remove the dead code | Comparison script runs both models on same OOS split via walk_forward harness; verdict appended to MODEL_CARD.md |
| MODEL-03 | train.py monolith refactored — no single module exceeds 500 lines; training, evaluation, and dashboard building are separate concerns | Three modules verified over-limit; split plan derived from concern mapping; import graph fully traced |
</phase_requirements>

---

## Summary

Phase 6 has two clean, independent tasks: (1) run a formal comparison of HDP-HMM against StudentTHMM and record the verdict, and (2) split three oversize modules by concern. Both are pure codebase operations — no new dependencies, no external services.

The comparison is expected to confirm StudentTHMM wins (per D-05, OOS dashboard shading was already poor), making deletion of `hdp_hmm.py` the likely outcome. If deletion happens first, MODEL-03 becomes simpler: `hdp_hmm.py`'s 844 lines are gone, and only `evaluation.py` (821 lines) and `hmm_training.py` (606 lines) need active splitting.

The refactor scope is fully traceable: every function in every oversize module has been read, all import sites in `scripts/`, `tests/`, and `src/` have been catalogued, and the concern-based splits map cleanly to the existing function groupings without restructuring any business logic.

**Primary recommendation:** Run the HDP comparison first. If StudentTHMM wins (likely), delete `hdp_hmm.py` immediately — this shrinks the refactor surface and removes the need to update any HDP-related imports in `train.py`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HDP-HMM vs StudentTHMM comparison | `scripts/analysis/` script | `src/core/orchestrator.py` (walk_forward harness) | Analysis scripts are the established pattern; orchestrator provides the shared eval harness |
| HDP decision documentation | `docs/MODEL_CARD.md` | `src/config.py` (USE_HDP flag) | MODEL_CARD.md is the canonical reference for downstream consumers |
| PCA utilities | `src/core/pca_utils.py` (new) | none | Extracted from `hmm_training.py` by concern |
| Stochastic volatility model | `src/core/pca_utils.py` or `sv_model.py` (new) | `src/core/hmm_training.py` (caller) | LinearizedSV used in `hmm_training.py` only; co-locate with PCA or isolate by complexity |
| VaR backtesting | `src/core/var_backtesting.py` (new) | `src/core/evaluation.py` | VaR functions are a distinct concern from regime evaluation |
| Forward return analysis | `src/core/forward_returns.py` (new) | `src/core/evaluation.py` | Phase 4 addition; distinct validation concern |
| Regime evaluation (core) | `src/core/evaluation.py` (trimmed) | none | Retain `evaluate()`, bootstrap CIs |
| BIC / stability / labeling | `src/core/hmm_training.py` (trimmed) | none | Keep in place per D-10 |
| Walk-forward harness | `src/core/orchestrator.py` | none | Already 167 lines — no change needed |
| Import updates | `scripts/pipelines/train.py`, `src/core/orchestrator.py`, `src/signals/signals.py`, all scripts | `tests/` (10+ test files) | Full import graph traced below |

---

## Standard Stack

### Core (already installed — no new dependencies needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| hmmlearn | installed | StudentTHMM base class (GaussianHMM) | Used in `inference.py:StudentTHMM` |
| numpyro | installed | HDP-HMM inference (SVI path) | Used in `hdp_hmm.py` |
| jax / jaxlib | installed (pinned) | HDP-HMM JAX backend | Pinned to exact versions per reproducibility guarantee |
| arch | installed | GARCH model in `hmm_training.py` and `evaluation.py` | VaR backtesting |
| statsmodels | installed | `LinearizedSV` (MLEModel base class) in `hmm_training.py` | Kalman filter SV |
| sklearn | installed | PCA in `hmm_training.py` and `orchestrator.py` | Rolling PCA |
| scipy | installed | Procrustes alignment, Student-t pdf | Used throughout |

No new packages required. [VERIFIED: reading requirements.txt and import statements across all source files]

**Installation:** No new `pip install` needed for this phase.

---

## Architecture Patterns

### System Architecture Diagram

```
Comparison Script (scripts/analysis/compare_hdp_vs_student.py)
        |
        v
[StudentTHMM path]                     [HDP-HMM path]
orchestrator.walk_forward()            fit_hdp_hmm(pcs, inference='svi')
        |                                      |
        v                                      v
evaluation.evaluate()              get_labels_and_probs()
        |                                      |
        +------------- compare ----------------+
                            |
                            v
                    Decision: win/lose vs D-03 threshold
                            |
                  +---------+----------+
                  |                    |
              HDP WINS              HDP LOSES
         USE_HDP=True default     delete hdp_hmm.py
         StudentTHMM fallback     remove all references
                  |                    |
                  v                    v
            MODEL_CARD.md "Model Architecture Decision" section
```

```
Refactor Dependency Graph (after splits):

evaluation.py (trimmed ~400 lines)
  imports: nothing from core siblings

var_backtesting.py (new ~250 lines)
  imports: from src.config import VAR_ALPHA
  contains: compute_var_backtest, compute_var_backtest_garch,
            compare_var_methods, kupiec_pof_test, christoffersen_test,
            warn_static_var_deprecated

forward_returns.py (new ~150 lines)
  imports: from scipy.stats import kruskal
  contains: compute_forward_return_analysis, analyze_forward_returns

pca_utils.py (new ~180 lines)
  imports: sklearn.decomposition.PCA, scipy.linalg.orthogonal_procrustes
  contains: fit_rolling_pca, [LinearizedSV or imported from sv_model.py]

hmm_training.py (trimmed ~250 lines)
  imports: from src.core.pca_utils import fit_rolling_pca
  contains: select_states_bic, check_stability, label_regimes,
            fit_regime_sv, fit_regime_garch
```

### Recommended Project Structure After Phase 6

```
src/core/
├── __init__.py          # empty (unchanged)
├── inference.py         # 268 lines (unchanged)
├── orchestrator.py      # 167 lines (unchanged)
├── hmm_training.py      # ~250 lines after extraction
├── evaluation.py        # ~400 lines after extraction
├── pca_utils.py         # NEW: fit_rolling_pca, [LinearizedSV]
├── var_backtesting.py   # NEW: VaR/GARCH backtest functions
├── forward_returns.py   # NEW: forward return analysis
└── hdp_hmm.py           # DELETED if HDP loses (likely)
```

### Pattern 1: Concern-Based Module Split

**What:** Move functions to new files based on what they operate on, not who calls them. Keep callers' imports updated.
**When to use:** When a module exceeds 500 lines and contains clearly distinct concerns (PCA is not VaR is not forward returns).
**Example:**

```python
# Before (in evaluation.py):
from src.core.evaluation import compute_var_backtest_garch, analyze_forward_returns

# After:
from src.core.var_backtesting import compute_var_backtest_garch
from src.core.forward_returns import analyze_forward_returns
```

### Pattern 2: HDP Comparison via Existing Harness

**What:** Run both models through the same `walk_forward()` harness on the same data split, compare `evaluate()` output for OOS accuracy and dwell time.
**When to use:** When comparing model variants under equal conditions.

```python
# Source: verified from src/core/orchestrator.py:walk_forward()
# and scripts/analysis/select_k_via_crossval.py (established pattern)

from src.core.orchestrator import walk_forward
from src.core.evaluation import evaluate

# StudentTHMM path (USE_HDP=False already default)
oos_labels_student, name_map = walk_forward(market, features, n_states=3, n_pca=n_pca)

# HDP-HMM path: run fit_hdp_hmm() on each fold manually,
# or set USE_HDP=True in config and run through train.py's existing HDP branch
# (train.py lines 2186-2245 already contain the full HDP path)
```

### Pattern 3: Computing Dwell Time for Comparison

**What:** Average dwell time = mean run length in the label sequence.
**When to use:** As the stability metric in the HDP comparison (D-01, D-03).

```python
# Pattern verified from src/signals/signals.py:_validation_metrics()
import numpy as np

def mean_dwell_time(labels):
    run_lengths = []
    curr_len = 1
    for i in range(1, len(labels)):
        if labels[i] == labels[i - 1]:
            curr_len += 1
        else:
            run_lengths.append(curr_len)
            curr_len = 1
    run_lengths.append(curr_len)
    return float(np.mean(run_lengths))
```

### Pattern 4: OOS Accuracy Measurement

**What:** Compare IS labels to OOS labels on the overlapping date range; fraction matching is the accuracy.
**When to use:** As the accuracy metric for the HDP comparison (D-01, D-03).

```python
# Pattern from src/signals/signals.py:_oos_validation()
agree = (oos_valid['regime_name'] == oos_valid['regime_name_oos'])
oos_accuracy = float(agree.mean())
```

### Anti-Patterns to Avoid

- **Re-export indirection:** Do not create a `from src.core.evaluation import compute_var_backtest_garch` re-export in `evaluation.py` after moving the function. D-12 requires clean removal — callers must update their imports.
- **Circular imports:** `pca_utils.py` must not import from `hmm_training.py`. Only `hmm_training.py` imports from `pca_utils.py`.
- **Running NUTS for the comparison:** D-02 locks inference to SVI only. The NUTS path in `hdp_hmm.py` must not be invoked.
- **Using smoothed probabilities for OOS accuracy:** OOS accuracy must use filtered (forward-only) labels, not smoothed. The `walk_forward()` harness already uses `filtered_labels()` — do not switch to `predict_proba()`.
- **Modifying `signals.py` public API:** `compute_signals()`, `detect()`, `fit()` must not change signatures.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Walk-forward OOS split | Custom train/test loop | `orchestrator.walk_forward()` | Already handles expanding/rolling mode, PCA refit per fold, VIX bypass |
| Regime dwell time | New run-length encoder | Pattern from `signals.py:_validation_metrics()` | 8 lines, already tested |
| OOS accuracy | Custom comparison logic | Pattern from `signals.py:_oos_validation()` | Already handles aligned index, per-regime breakdown |
| SVI convergence check | Custom ELBO monitor | Already in `hdp_hmm.py:_fit_svi()` lines 210-219 | Rel-change check with 200-step tail window |

---

## Full Import Graph (Critical for MODEL-03)

All files that import from the three refactor targets, verified by reading source:

### Importers of `evaluation.py`

| File | What it imports |
|------|----------------|
| `scripts/pipelines/train.py:48` | `evaluate, compute_var_backtest, compute_var_backtest_garch, kupiec_pof_test, christoffersen_test` |
| `scripts/analysis/analyze_feature_selection.py:28` | `evaluate, compute_var_backtest` |
| `scripts/analysis/analyze_regime_characterization.py:669` | `compute_forward_return_analysis` (lazy import) |
| `tests/test_feature_selection_bias.py:26` | `compute_var_backtest` |
| `tests/test_train_refactor.py:36` | `evaluate, compute_var_backtest, compute_var_backtest_garch, compare_var_methods, kupiec_pof_test, christoffersen_test, compute_forward_return_analysis` |
| `tests/test_regime_economic_validity.py:18` | `compute_forward_return_analysis` |
| `tests/test_regime_economic_validity.py:274` | `from src.core import evaluation` (module-level) |
| `tests/test_var_backtesting.py` | likely imports VaR functions — verify before splitting |

### Importers of `hmm_training.py`

| File | What it imports |
|------|----------------|
| `scripts/pipelines/train.py:47` | `fit_rolling_pca, select_states_bic, check_stability, label_regimes, fit_regime_sv, fit_regime_garch` |
| `scripts/analysis/analyze_feature_selection.py:27` | `fit_rolling_pca, label_regimes, check_stability` |
| `scripts/analysis/select_k_via_crossval.py:39` | `fit_rolling_pca, select_states_bic, check_stability, label_regimes` |
| `tests/test_feature_selection_bias.py:25` | `fit_rolling_pca` |
| `tests/test_regime_count_selection.py:24` | `select_states_bic, check_stability, label_regimes, fit_rolling_pca` |
| `tests/test_train_refactor.py:24` | `fit_rolling_pca, select_states_bic, check_stability, label_regimes, fit_regime_sv, fit_regime_garch` |

### Importers of `hdp_hmm.py`

| File | What it imports |
|------|----------------|
| `scripts/pipelines/train.py:2188` | `fit_hdp_hmm, effective_K, posterior_mean_params, get_labels_and_probs, label_regimes_hdp, mcmc_diagnostics, save_hdp_results, hdp_stability_check` (lazy import inside `if USE_HDP:` block at line 2186) |

No other files import from `hdp_hmm.py` directly. Deletion only requires removing the `if USE_HDP:` block in `train.py` and the `USE_HDP` config flag. [VERIFIED: grep across all .py files]

---

## Concern Mapping: What Goes Where

### `evaluation.py` splits (D-09)

**Stays in `evaluation.py` (~400 lines):**
- `evaluate()` — regime characteristic reporting
- `_print_bootstrap_cis()` — bootstrap CIs for evaluate()
- `_get_blocks()` — utility used by bootstrap
- `__all__` (trimmed to remaining symbols)

**Moves to `var_backtesting.py` (~250 lines):**
- `compute_var_backtest()` — deprecated static VaR
- `kupiec_pof_test()` — test statistic
- `christoffersen_test()` — test statistic
- `compute_var_backtest_garch()` — production VaR
- `compare_var_methods()` — comparison utility
- `warn_static_var_deprecated()` — logging helper

**Moves to `forward_returns.py` (~150 lines):**
- `compute_forward_return_analysis()` — DIAG-04 forward returns
- `analyze_forward_returns()` — more detailed version (Phase 4 addition)

**Estimated line counts after split:**
- `evaluation.py`: ~400 lines (well under 500)
- `var_backtesting.py`: ~250 lines
- `forward_returns.py`: ~150 lines

### `hmm_training.py` splits (D-10)

**Stays in `hmm_training.py` (~250 lines):**
- `_hmm_n_params()` — BIC helper
- `_hmm_bic()` — BIC helper
- `select_states_bic()` — model selection
- `_best_perm_agreement()` — stability helper
- `check_stability()` — stability check
- `label_regimes()` — regime naming
- `fit_regime_sv()` — SV model fit (calls LinearizedSV)
- `fit_regime_garch()` — GARCH fit
- `__all__`
- Import of `fit_rolling_pca` from new `pca_utils.py`

**Moves to `pca_utils.py` (~180 lines):**
- `fit_rolling_pca()` — rolling PCA with Procrustes alignment
- `LinearizedSV` class — SV model (OR moved to `sv_model.py` — Claude's discretion)

**Note on LinearizedSV placement:** `LinearizedSV` is only used by `fit_regime_sv()` in `hmm_training.py`. Its natural home is wherever the 500-line threshold is most comfortably met. If `hmm_training.py` stays under 500 lines after removing `fit_rolling_pca` alone (current: 606 lines, `fit_rolling_pca` is ~135 lines → ~471 remaining — just under), then `LinearizedSV` can stay in `hmm_training.py`. If `pca_utils.py` is the extraction target and `LinearizedSV` adds useful context, it moves there. [VERIFIED: line counts from wc -l]

---

## Common Pitfalls

### Pitfall 1: Breaking the Comparison's OOS Split Alignment
**What goes wrong:** HDP and StudentTHMM are evaluated on different date ranges because HDP requires a warm-up period or has different NaN handling.
**Why it happens:** The SVI path in `hdp_hmm.py` takes PCs as direct input — its warm-up is controlled externally. But `walk_forward()` handles standardization and PCA warm-up before calling the HMM. If the HDP comparison script uses a different data-preparation path, the OOS dates won't match.
**How to avoid:** Run both models on the same `pcs` array from the same `walk_forward()` fold. Use the same `valid_mask` from `fit_rolling_pca()` to align dates.
**Warning signs:** OOS date ranges differ between the two comparison rows in the results table.

### Pitfall 2: HDP Label Permutation Mismatch
**What goes wrong:** HDP and StudentTHMM discover the same 3 regimes but label them with different integers (e.g., HDP's regime 0 = StudentTHMM's regime 2). OOS accuracy comparison gives spuriously low numbers.
**Why it happens:** Both models independently assign integer labels — there's no shared ordering constraint.
**How to avoid:** Both pipelines already use vol-bracket naming (`label_regimes_hdp()` for HDP, `label_regimes()` for StudentTHMM) — compare on named labels ('Low-Vol', 'Medium-Vol', 'High-Vol'), not integers. The `walk_forward()` output already returns named labels.
**Warning signs:** OOS accuracy < 40% with either model (below random chance for K=3).

### Pitfall 3: SVI ELBO Non-Convergence Silently Produces Bad Labels
**What goes wrong:** SVI runs `SVI_NUM_STEPS=3000` steps but doesn't converge — the convergence warning is printed but the comparison proceeds anyway with garbage posterior samples.
**Why it happens:** The convergence check in `_fit_svi()` lines 210-219 only warns; it doesn't raise an error.
**How to avoid:** Check the ELBO convergence flag before recording HDP results. If not converged, report inconclusive rather than a false HDP loss/win.
**Warning signs:** `SVI may not have converged` warning in stdout.

### Pitfall 4: Import Renames Breaking Tests
**What goes wrong:** Tests import `from src.core.evaluation import compute_var_backtest_garch` — after moving to `var_backtesting.py`, those tests silently fail at import time or skip.
**Why it happens:** Python's import system resolves at test collection time; a missing symbol raises `ImportError`, which pytest treats as a collection error (not a skipped test).
**How to avoid:** Update ALL import sites simultaneously with the module split. Use the import graph table above as a checklist. Run `pytest` after each file's imports are updated.
**Warning signs:** `ImportError` or `ModuleNotFoundError` in pytest output; collection errors rather than test failures.

### Pitfall 5: `test_train_refactor.py` Imports All Symbols
**What goes wrong:** `test_train_refactor.py:36` imports `evaluate, compute_var_backtest, compute_var_backtest_garch, compare_var_methods, kupiec_pof_test, christoffersen_test, compute_forward_return_analysis` from `src.core.evaluation`. After splitting, 5 of these 7 symbols no longer exist there.
**Why it happens:** This test was written to verify the Phase 3.1 refactor — it imports from the post-refactor module locations and verifies they exist.
**How to avoid:** Update this test's imports as part of the refactor wave, not after.
**Warning signs:** `test_train_refactor.py` fails at collection with `ImportError`.

### Pitfall 6: `__all__` Lists Not Updated After Split
**What goes wrong:** `evaluation.py`'s `__all__` still lists symbols that moved to other files, causing `from src.core.evaluation import *` to fail silently or raise `AttributeError`.
**Why it happens:** `__all__` is not enforced at definition time — it's only validated when `import *` is used.
**How to avoid:** Update `__all__` in every split file. Add the symbol to the new file's `__all__` before removing from the old file's `__all__`.

---

## Code Examples

### Running HDP SVI on an existing PCs array

```python
# Source: verified from src/core/hdp_hmm.py:fit_hdp_hmm()
from src.core.hdp_hmm import (
    fit_hdp_hmm, effective_K, posterior_mean_params,
    get_labels_and_probs, label_regimes_hdp, mcmc_diagnostics,
    hdp_stability_check,
)
from src.config import HDP_TRUNCATION, HDP_INFERENCE

# pcs: ndarray (T, n_pca) — from fit_rolling_pca()
result, samples = fit_hdp_hmm(pcs, K_max=HDP_TRUNCATION, inference='svi')
diag = mcmc_diagnostics(result, samples)  # ELBO convergence check

params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
labels, filt_probs, smooth_probs, active_states = get_labels_and_probs(pcs, params)

name_map_hdp = label_regimes_hdp(labels, active_states, spy_returns)
stability = hdp_stability_check(samples, pcs, n_draws=10)
```

### Computing comparison metrics

```python
# Source: patterns from src/signals/signals.py
import numpy as np

def mean_dwell_time(labels):
    run_lengths, curr_len = [], 1
    for i in range(1, len(labels)):
        if labels[i] == labels[i - 1]:
            curr_len += 1
        else:
            run_lengths.append(curr_len)
            curr_len = 1
    run_lengths.append(curr_len)
    return float(np.mean(run_lengths))

def oos_accuracy(is_named_labels, oos_named_labels):
    """Both args are string label arrays (e.g., 'Low-Vol')."""
    common = is_named_labels.index.intersection(oos_named_labels.index)
    agree = (is_named_labels[common] == oos_named_labels[common])
    return float(agree.mean()), len(common)
```

### Clean module split pattern

```python
# var_backtesting.py — new file
"""VaR backtesting functions extracted from evaluation.py (Phase 6, MODEL-03).

Decision: GARCH-conditional VaR is production standard.
  Static VaR is kept for documentation/comparison only (deprecated).
See docs/MODEL_CARD.md 'Model Architecture Decision' for rationale.
"""
from src.config import VAR_ALPHA
# ... move functions here verbatim, no logic changes ...
```

### MODEL_CARD.md comparison table format (Claude's discretion)

```markdown
## Model Architecture Decision (Phase 6)

**Comparison date:** 2026-04-XX
**OOS split:** same as Phase 4/5 diagnostics (Phase 5 FEATURE_SUBSET)
**Inference mode:** SVI (HDP_INFERENCE='svi', SVI_NUM_STEPS=3000)

| Metric | StudentTHMM | HDP-HMM (SVI) | Win threshold (D-03) | Winner |
|--------|------------|---------------|----------------------|--------|
| OOS accuracy | XX.X% | XX.X% | HDP needs +2pp | X |
| Mean dwell time (days) | X.X | X.X | HDP needs meaningful gain | X |
| SVI converged | — | Yes/No | — | — |

**Verdict:** [StudentTHMM stays / HDP enabled]
**Rationale:** [...]
**Action taken:** [hdp_hmm.py deleted / USE_HDP=True set as default]
```

---

## Runtime State Inventory

This phase is a code/config-only refactor and model comparison. No rename or migration is involved.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — no stored regime labels reference model architecture | None |
| Live service config | None — no external services involved | None |
| OS-registered state | None | None |
| Secrets/env vars | None | None |
| Build artifacts | `src/core/__pycache__/` — stale `.pyc` for hdp_hmm.py if deleted | Python auto-removes on next import; no manual action |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| numpyro | HDP comparison | verified (in requirements.txt, pinned) | pinned | — |
| jax | HDP comparison (SVI) | verified (in requirements.txt, pinned) | pinned | — |
| hmmlearn | StudentTHMM | verified (in inference.py imports) | installed | — |
| arch | GARCH in evaluation.py, hmm_training.py | verified (in imports) | installed | — |
| statsmodels | LinearizedSV (MLEModel) | verified (in hmm_training.py imports) | installed | — |
| pytest | Test validation | verified (tests/ directory present, 160+ tests) | installed | — |

No missing dependencies.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none detected (standard pytest discovery) |
| Quick run command | `pytest tests/test_train_refactor.py tests/test_var_backtesting.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODEL-02 | USE_HDP verdict documented in MODEL_CARD.md | manual inspection | n/a | n/a |
| MODEL-02 | HDP comparison script runs and produces accuracy + dwell numbers | smoke | `python scripts/analysis/compare_hdp_vs_student.py` | ❌ Wave 0 |
| MODEL-03 | No module in `src/core/` exceeds 500 lines | unit | `pytest tests/test_train_refactor.py -k "module_size" -x` | ❌ Wave 0 |
| MODEL-03 | All existing public imports still resolve after split | regression | `pytest tests/test_train_refactor.py -x -q` | ✅ |
| MODEL-03 | VaR backtest functions work from new location | unit | `pytest tests/test_var_backtesting.py -x -q` | ✅ (needs import update) |
| MODEL-03 | Forward return analysis works from new location | unit | `pytest tests/test_regime_economic_validity.py -x -q` | ✅ (needs import update) |

### Sampling Rate

- Per task commit: `pytest tests/test_train_refactor.py -x -q`
- Per wave merge: `pytest tests/ -x -q`
- Phase gate: Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `scripts/analysis/compare_hdp_vs_student.py` — comparison script (MODEL-02 main deliverable)
- [ ] `tests/test_train_refactor.py::test_module_size` — verifies no module exceeds 500 lines (MODEL-03 gate)

*(Note: `test_var_backtesting.py` and `test_regime_economic_validity.py` exist but will need import path updates after the split — they are not Wave 0 gaps, they are Wave 1 tasks.)*

---

## Security Domain

This phase has no network access, authentication, user input, or cryptography. ASVS does not apply.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `hdp_hmm.py` is only imported by `train.py` (one import site) | Import Graph | If other scripts import it, deletion requires more cleanup. Risk: LOW — grep verified no other `.py` files import from `hdp_hmm` |
| A2 | `hmm_training.py` will land at ~250 lines after removing `fit_rolling_pca` (135 lines) and `LinearizedSV` (~55 lines) | Concern Mapping | If actual trimmed count is > 500, additional splitting is needed. Risk: LOW — line math checks out (606 - 135 - ~55 = ~416) |
| A3 | Evaluation.py after splitting will be ~400 lines (VaR = ~250 lines, forward returns = ~150 lines) | Concern Mapping | If remaining evaluation.py is still > 500, adjust split boundary. Risk: LOW — Claude's discretion per decision allows adjustment |

**All three assumed claims are based on verified line counts from `wc -l` on the actual files.** Risk is LOW in all cases. No user confirmation needed — these are arithmetic estimates, not policy decisions.

---

## Open Questions

1. **LinearizedSV placement (Claude's discretion)**
   - What we know: `LinearizedSV` is 55 lines; it is only used by `fit_regime_sv()` in `hmm_training.py`; it has no PCA relationship
   - What's unclear: Whether co-locating with PCA (`pca_utils.py`) is logical or whether it warrants its own `sv_model.py`
   - Recommendation: Put it in `pca_utils.py` if that keeps `hmm_training.py` well under 500 after `fit_rolling_pca` extraction alone. If `hmm_training.py` is already at ~416 lines without it, keep `LinearizedSV` in `hmm_training.py` and name the new file `pca_utils.py` cleanly.

2. **Comparison script structure (new script vs config toggle)**
   - What we know: Analysis scripts live in `scripts/analysis/` (established pattern per code context); a new `compare_hdp_vs_student.py` fits this pattern
   - What's unclear: Whether to toggle `USE_HDP` in a subprocess or import both models directly in the same script
   - Recommendation: Single script that imports both `fit_hdp_hmm` and the `walk_forward` harness directly, running both on identical feature data. Avoids subprocess complexity and keeps results in one place for the MODEL_CARD.md table.

---

## Sources

### Primary (HIGH confidence — all verified by reading local source files)
- `src/core/hdp_hmm.py` — full HDP-HMM implementation, 844 lines [VERIFIED]
- `src/core/hmm_training.py` — training functions, 606 lines [VERIFIED]
- `src/core/evaluation.py` — evaluation functions, 821 lines [VERIFIED]
- `src/core/orchestrator.py` — walk_forward harness, 167 lines [VERIFIED]
- `src/core/inference.py` — StudentTHMM, 268 lines [VERIFIED]
- `src/config.py` — USE_HDP, HDP_INFERENCE, all config values [VERIFIED]
- `scripts/pipelines/train.py` — 2520 lines; HDP conditional at line 2186; import sites at lines 46-49 [VERIFIED]
- `src/signals/signals.py` — public API, dwell time and OOS accuracy patterns [VERIFIED]
- Import graph — grep across all .py files in scripts/, tests/, src/ [VERIFIED]

### No secondary or tertiary sources needed
This phase is entirely local codebase work. No external documentation, ecosystem research, or web search required.

---

## Metadata

**Confidence breakdown:**
- Current module line counts: HIGH — verified with `wc -l`
- Import dependency graph: HIGH — verified with grep across all Python files
- Refactor split line estimates: MEDIUM — arithmetic from current counts; exact counts depend on final placement of LinearizedSV
- HDP comparison outcome: MEDIUM — expected StudentTHMM win per D-05 prior, but actual numbers not yet run
- Architecture patterns: HIGH — drawn directly from existing code in established scripts

**Research date:** 2026-04-20
**Valid until:** This research is tied to current file contents. Valid as long as no other phase modifies the source files listed above. If Phase 5 artifacts change any core file, re-verify line counts.
