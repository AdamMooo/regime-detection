# Phase 6: Model Architecture Experiments - Pattern Map

**Mapped:** 2026-04-20
**Files analyzed:** 8 new/modified files
**Analogs found:** 8 / 8

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/analysis/compare_hdp_vs_student.py` | analysis script | batch, request-response | `scripts/analysis/select_k_via_crossval.py` | exact |
| `src/core/var_backtesting.py` | utility module | batch | `src/core/evaluation.py` (lines 202–546) | exact (extract) |
| `src/core/forward_returns.py` | utility module | batch | `src/core/evaluation.py` (lines 549–637) | exact (extract) |
| `src/core/pca_utils.py` | utility module | transform | `src/core/hmm_training.py` (lines 1–136) | exact (extract) |
| `src/core/hmm_training.py` (trimmed) | model-training | transform | `src/core/hmm_training.py` (current, lines 137–606) | self (trim) |
| `src/core/evaluation.py` (trimmed) | evaluation | batch | `src/core/evaluation.py` (current, lines 1–196) | self (trim) |
| `docs/MODEL_CARD.md` (append section) | documentation | n/a | `docs/MODEL_CARD.md` (existing sections) | exact |
| `scripts/pipelines/train.py` (import updates) | orchestrator | n/a | `src/core/orchestrator.py` import block | role-match |

---

## Pattern Assignments

### `scripts/analysis/compare_hdp_vs_student.py` (analysis script, batch)

**Analog:** `scripts/analysis/select_k_via_crossval.py`

**Imports pattern** (lines 20–46 of analog):
```python
import os
import sys
import logging
import warnings

import numpy as np
import pandas as pd

# Add repo to path
sys.path.insert(0, os.path.dirname(__file__))

from src.config import (
    DATA_DIR, MODEL_DIR, RANDOM_SEED, COV_TYPE,
    REGIME_HOLD_DAYS, PCA_ROLLING_WINDOW, N_SEEDS,
)
from src.core.inference import expanding_standardize, _fit_hmm, filtered_labels
from src.core.hmm_training import fit_rolling_pca, label_regimes
from src.core.orchestrator import walk_forward

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
```

**Script structure pattern** (select_k_via_crossval.py lines 55–122 — each concern is a named function, called from a `main()` or top-level block):
```python
def in_sample_model_selection(market, feat_scaled):
    """...docstring with procedure and output..."""
    print("\n" + "="*70)
    print("PHASE 1: ...")
    print("="*70)
    # ... work ...
    return results_dict

def walk_forward_validation_for_k(market, feat_scaled, k_value, name='K'):
    """..."""
    # ...
    return metrics_dict
```

**Walk-forward harness pattern** (src/core/orchestrator.py lines 23–164 — use as-is, do not reimplement):
```python
from src.core.orchestrator import walk_forward

# StudentTHMM path (USE_HDP=False — already the config default)
oos_labels, name_map = walk_forward(market, features, n_states=3, n_pca=n_pca)
```

**Dwell time metric pattern** (src/signals/signals.py lines 185–310, `_validation_metrics` — extract the run-length loop):
```python
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
```

**OOS accuracy pattern** (src/signals/signals.py lines 345–422, `_oos_validation`):
```python
# Both are string-label Series with DatetimeIndex
agree = (oos_valid['regime_name'] == oos_valid['regime_name_oos'])
oos_accuracy = float(agree.mean())
```
Note: compare on named labels ('Low-Vol', 'Medium-Vol', 'High-Vol'), NOT integers, to avoid label-permutation mismatch (Pitfall 2 in RESEARCH.md).

**HDP-HMM invocation pattern** (src/core/hdp_hmm.py, verified from RESEARCH.md code examples):
```python
from src.core.hdp_hmm import (
    fit_hdp_hmm, effective_K, posterior_mean_params,
    get_labels_and_probs, label_regimes_hdp, mcmc_diagnostics,
    hdp_stability_check,
)
from src.config import HDP_TRUNCATION, HDP_INFERENCE

result, samples = fit_hdp_hmm(pcs, K_max=HDP_TRUNCATION, inference='svi')
diag = mcmc_diagnostics(result, samples)   # check ELBO convergence flag before proceeding
params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
labels, filt_probs, smooth_probs, active_states = get_labels_and_probs(pcs, params)
name_map_hdp = label_regimes_hdp(labels, active_states, spy_returns)
```
Anti-pattern: Do NOT pass `inference='nuts'` — D-02 locks this to `'svi'` only.

**Section separator pattern** (used throughout all analysis scripts):
```python
# ===================================================================
# Walk-Forward OOS Validation
# ===================================================================
```

---

### `src/core/var_backtesting.py` (utility module, batch — extract from evaluation.py)

**Analog:** `src/core/evaluation.py` lines 202–546 (source of the extract)

**Module header pattern** (copy and adapt evaluation.py lines 1–48 module docstring style):
```python
"""VaR backtesting functions extracted from evaluation.py (Phase 6, MODEL-03).

Decision: GARCH-conditional VaR is production standard.
  Static VaR is kept for documentation/comparison only (deprecated).
See docs/MODEL_CARD.md 'Model Architecture Decision' for rationale.

Functions
---------
compute_var_backtest(spy_returns, labels, name_map, alpha)
    [DEPRECATED] Static VaR — Kupiec POF + Christoffersen tests
compute_var_backtest_garch(spy_returns, regime_probs, labels, name_map, alpha)
    [PRODUCTION] GARCH-based VaR backtest
compare_var_methods(spy_returns, regime_probs, labels, name_map, alpha)
    Compare static vs GARCH VaR
kupiec_pof_test(n_obs, n_exc, alpha)
    Kupiec POF test statistic
christoffersen_test(spy_returns, labels, name_map, alpha)
    Christoffersen independence test
warn_static_var_deprecated()
    Deprecation warning helper
"""

import logging
import numpy as np
import pandas as pd
from scipy.stats import binom, chi2
from scipy.special import erfinv

from src.config import VAR_ALPHA

logger = logging.getLogger(__name__)
```

**`__all__` pattern** (must match exactly the symbols being moved — adapt from evaluation.py lines 811–821):
```python
__all__ = [
    'compute_var_backtest',
    'compute_var_backtest_garch',
    'compare_var_methods',
    'kupiec_pof_test',
    'christoffersen_test',
    'warn_static_var_deprecated',
]
```

**Functions to move verbatim** (evaluation.py line ranges, no logic changes):
- `compute_var_backtest()` — lines 202–280
- `kupiec_pof_test()` — lines 283–320
- `christoffersen_test()` — lines 323–380 (verify exact end)
- `compute_var_backtest_garch()` — lines 383–480 (verify exact end)
- `compare_var_methods()` — lines 483–546
- `warn_static_var_deprecated()` — lines 640–648

**Critical:** After moving, remove these symbols from `evaluation.py`'s `__all__` (lines 811–821) and from evaluation.py's import block. Update `evaluation.py` docstring to remove VaR function entries.

---

### `src/core/forward_returns.py` (utility module, batch — extract from evaluation.py)

**Analog:** `src/core/evaluation.py` lines 549–637 (source of the extract)

**Module header pattern**:
```python
"""Forward return analysis extracted from evaluation.py (Phase 6, MODEL-03).

Functions
---------
compute_forward_return_analysis(results, market)
    Regime-conditional forward returns with Kruskal-Wallis tests (DIAG-04)
analyze_forward_returns(results, market, horizons, assets)
    Detailed forward return analysis (Phase 4 addition)
"""

import logging
import numpy as np
import pandas as pd
from scipy.stats import kruskal

logger = logging.getLogger(__name__)
```

**`__all__` pattern**:
```python
__all__ = [
    'compute_forward_return_analysis',
    'analyze_forward_returns',
]
```

**Functions to move verbatim**:
- `compute_forward_return_analysis()` — evaluation.py lines 549–637
- `analyze_forward_returns()` — evaluation.py lines 682–809 (verify exact end; includes the `_get_blocks()` helper — move it too or keep private in this file)

Note: `compute_forward_return_analysis()` uses a lazy `from scipy.stats import kruskal` at line 572. Move this to the module-level import block in the new file.

---

### `src/core/pca_utils.py` (utility module, transform — extract from hmm_training.py)

**Analog:** `src/core/hmm_training.py` lines 1–136 (source of the extract)

**Module header pattern** (adapt hmm_training.py lines 1–23 style):
```python
"""Rolling PCA utilities extracted from hmm_training.py (Phase 6, MODEL-03).

Functions
---------
fit_rolling_pca(X_scaled, window, max_components, var_threshold)
    Rolling-window PCA with Procrustes alignment for regime stability
"""

import logging
import numpy as np
from scipy.linalg import orthogonal_procrustes
from sklearn.decomposition import PCA

from src.config import (
    RANDOM_SEED, PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD, PCA_ROLLING_WINDOW,
)

logger = logging.getLogger(__name__)
```

**`__all__` pattern**:
```python
__all__ = ['fit_rolling_pca']
```
(Add `'LinearizedSV'` here only if LinearizedSV is moved to this file — see discretion note below.)

**Function to move verbatim**:
- `fit_rolling_pca()` — hmm_training.py lines 52–136 (including the two module-level constants used only by it, if any)

**LinearizedSV placement (Claude's discretion):**
Per RESEARCH.md open question: `hmm_training.py` currently is 606 lines. Removing `fit_rolling_pca` (~85 lines of function body, plus constants at lines 43–44 = ~87 lines) leaves ~519 lines — still over 500. `LinearizedSV` is ~55 lines; removing it too yields ~464 lines (under 500). Therefore `LinearizedSV` MUST move to `pca_utils.py` (or `sv_model.py`) to meet the MODEL-03 gate.

Decision: Move `LinearizedSV` to `pca_utils.py`. It has no PCA relationship but co-locating avoids creating a single-class file. Add it to `pca_utils.py`'s `__all__`.

**Circular import constraint:** `pca_utils.py` must NOT import from `hmm_training.py`. After the split, `hmm_training.py` imports `from src.core.pca_utils import fit_rolling_pca, LinearizedSV`.

---

### `src/core/hmm_training.py` (trimmed, model-training, transform)

**Analog:** `src/core/hmm_training.py` (current file — self-modification, retain lines 137–606 minus LinearizedSV)

**New imports block** (replace current lines 25–40 — remove PCA/Procrustes imports, add pca_utils import):
```python
import logging
import numpy as np
import pandas as pd
from itertools import permutations
from arch import arch_model

from src.config import (
    RANDOM_SEED, N_STATES_RANGE, COV_TYPE, N_SEEDS, GARCH_P, GARCH_Q, GARCH_DIST,
    MIN_REGIME_OBS, REGIME_NAMES, VOL_BRACKETS, DATA_DIR,
)
from src.core.inference import _fit_hmm, filtered_labels, StudentTHMM
from src.core.pca_utils import fit_rolling_pca, LinearizedSV  # extracted in Phase 6
```

**`__all__` after trim** (update lines 599–606 — remove `fit_rolling_pca` if no longer defined here; keep all other symbols):
```python
__all__ = [
    'select_states_bic',
    'check_stability',
    'label_regimes',
    'fit_regime_sv',
    'fit_regime_garch',
]
```
Note: `fit_rolling_pca` moves to `pca_utils.py`; callers that imported it from `hmm_training` must now import from `pca_utils` (see import graph in RESEARCH.md).

---

### `src/core/evaluation.py` (trimmed, evaluation, batch)

**Analog:** `src/core/evaluation.py` (current file — self-modification, retain lines 1–196 plus `_get_blocks` if not moved)

**New `__all__`** (replace lines 811–821 — remove all moved symbols):
```python
__all__ = [
    'evaluate',
]
```
(`_print_bootstrap_cis` and `_get_blocks` are private helpers — not in `__all__`.)

**New module docstring** (replace lines 1–38 — remove VaR and forward return entries from the Functions section):
Keep the `IMPORTANT: VaR Backtesting` warning block in the docstring, but update it to point to `src.core.var_backtesting` for the functions. This preserves the historical context without listing symbols that no longer live here.

**Imports to remove** from lines 40–48: remove `binom, chi2` (scipy.stats), `erfinv` (scipy.special) — only needed by VaR functions. Retain `kruskal` only if `_get_blocks` stays; if `_get_blocks` and `analyze_forward_returns` both move, remove `kruskal` too.

---

### `docs/MODEL_CARD.md` (documentation append)

**Analog:** `docs/MODEL_CARD.md` existing section headers (lines 1–40 read above)

**Append location:** After the last existing section. Do NOT modify existing content.

**Section format pattern** (matches existing MODEL_CARD.md header style):
```markdown
---

## Model Architecture Decision (Phase 6)

**Comparison date:** 2026-04-20
**OOS split:** Same as Phase 4/5 diagnostics (Phase 5 FEATURE_SUBSET, walk-forward expanding mode)
**Inference mode:** SVI (`HDP_INFERENCE='svi'`, `SVI_NUM_STEPS=3000`)
**Win threshold (D-03):** HDP-HMM must show +2 percentage points OOS accuracy AND meaningfully longer mean dwell time

| Metric | StudentTHMM | HDP-HMM (SVI) | Win threshold | Winner |
|--------|------------|---------------|---------------|--------|
| OOS accuracy | XX.X% | XX.X% | HDP needs +2pp | — |
| Mean dwell time (days) | X.X | X.X | HDP needs meaningful gain | — |
| SVI converged | — | Yes / No | — | — |

**Verdict:** [StudentTHMM stays / HDP-HMM enabled as default]
**Rationale:** [Fill in after running compare_hdp_vs_student.py]
**Action taken:** [hdp_hmm.py deleted and all references removed / USE_HDP=True set as default in config.py]
```

---

### Import update sites (train.py, orchestrator.py, signals.py, tests)

**Analog:** `src/core/orchestrator.py` import block (lines 12–21) for the clean, explicit import pattern. No re-export indirection.

**Pattern — before/after for each moved symbol:**
```python
# BEFORE (in train.py, orchestrator.py, test files):
from src.core.evaluation import compute_var_backtest_garch, compute_forward_return_analysis
from src.core.hmm_training import fit_rolling_pca

# AFTER (clean direct imports — D-12: no re-export indirection):
from src.core.var_backtesting import compute_var_backtest_garch
from src.core.forward_returns import compute_forward_return_analysis
from src.core.pca_utils import fit_rolling_pca
```

**Full import update checklist** (from RESEARCH.md import graph):

For `evaluation.py` splits:
- `scripts/pipelines/train.py:48` — update 5 symbols
- `scripts/analysis/analyze_feature_selection.py:28` — update 2 symbols
- `scripts/analysis/analyze_regime_characterization.py:669` — update lazy import of `compute_forward_return_analysis`
- `tests/test_feature_selection_bias.py:26` — update `compute_var_backtest`
- `tests/test_train_refactor.py:36` — update all 7 symbols (highest risk — see Pitfall 5 in RESEARCH.md)
- `tests/test_regime_economic_validity.py:18` and `:274` — update `compute_forward_return_analysis` + module-level import
- `tests/test_var_backtesting.py` — verify and update VaR imports

For `hmm_training.py` splits:
- `scripts/pipelines/train.py:47` — update `fit_rolling_pca`
- `scripts/analysis/analyze_feature_selection.py:27` — update `fit_rolling_pca`
- `scripts/analysis/select_k_via_crossval.py:39` — update `fit_rolling_pca`
- `tests/test_feature_selection_bias.py:25` — update `fit_rolling_pca`
- `tests/test_regime_count_selection.py:24` — update `fit_rolling_pca`
- `tests/test_train_refactor.py:24` — update `fit_rolling_pca`

---

## Shared Patterns

### Module docstring format
**Source:** `src/core/evaluation.py` lines 1–38, `src/core/hmm_training.py` lines 1–23
**Apply to:** All three new utility modules (`var_backtesting.py`, `forward_returns.py`, `pca_utils.py`)

Pattern: One-line summary, blank line, multi-line description of what the module handles, a `Functions\n---------` section listing each public function with its one-line description.

### Section separator comments
**Source:** `src/core/evaluation.py` line 51, `src/core/hmm_training.py` line 50
**Apply to:** All new modules and trimmed modules
```python
# ===================================================================
# <Section Name>
# ===================================================================
```

### `__all__` list
**Source:** `src/core/evaluation.py` lines 811–821, `src/core/hmm_training.py` lines 599–606
**Apply to:** Every new module and every trimmed module
- Define at the bottom of the file
- List only publicly intended symbols (no `_` prefixed helpers)
- Update the source module's `__all__` immediately when a symbol is removed

### Logger instantiation
**Source:** `src/core/evaluation.py` line 48, `src/core/hmm_training.py` line 41
**Apply to:** All new modules
```python
logger = logging.getLogger(__name__)
```

### Config imports
**Source:** `src/core/hmm_training.py` lines 34–38, `src/core/orchestrator.py` lines 15–19
**Apply to:** All new modules — import only the config symbols actually used in that file, no wildcard imports
```python
from src.config import VAR_ALPHA   # var_backtesting.py — only VAR_ALPHA needed
from src.config import RANDOM_SEED  # evaluation.py — RANDOM_SEED and VAR_ALPHA
```

### Analysis script top-level structure
**Source:** `scripts/analysis/select_k_via_crossval.py`
**Apply to:** `scripts/analysis/compare_hdp_vs_student.py`

Pattern:
1. Module docstring: purpose, procedure (numbered steps), output files
2. `sys.path.insert(0, ...)` for repo root
3. Imports: stdlib → numpy/pandas → project modules
4. `logging.basicConfig(level=logging.INFO)` + `warnings.filterwarnings`
5. Named functions per concern (one function per analysis step)
6. `if __name__ == '__main__':` guard calling a `main()` function or sequential function calls

---

## No Analog Found

All files have close analogs. No entries in this section.

---

## Metadata

**Analog search scope:** `src/core/`, `src/signals/`, `scripts/analysis/`, `docs/`, `tests/`
**Files read:** 10 source files
**Pattern extraction date:** 2026-04-20
