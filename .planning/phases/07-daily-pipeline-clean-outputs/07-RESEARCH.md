# Phase 7: Daily Pipeline & Clean Outputs — Research

**Researched:** 2026-04-21
**Domain:** Python pipeline architecture, subprocess/exit codes, logging, CSV schema, test patterns
**Confidence:** HIGH — all findings based on direct codebase inspection

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Plan 07-01: Pipeline Modularization + Timing Gate**
- Create `src/pipeline/` package: `__init__.py`, `stages.py`, `runner.py`
- Stages in order: collect → features → pca → train_hmm → garch → signals → dashboard
- Each stage reads its own inputs from disk, writes its own outputs to disk — stateless
- Walk-forward only via `--validate` flag, NEVER in daily pipeline
- `runner.py` records timing per stage; prints wall-clock summary
- Tests: `test_pipeline_stages.py`, `test_pipeline_timing.py`, `test_pipeline_idempotent.py`
- Refactor `scripts/pipelines/train.py` into discrete stage functions

**Plan 07-02: Clean Output Enforcement + Cron Readiness**
- `figures/` cleanup: delete stale HTML before each run, write exactly 2
- Exit code 0 on success, exit 1 on any stage failure
- `logs/pipeline.log`: rotating (10MB cap, 3 backups), timestamps per stage
- `scripts/cron_run.sh`: activate venv, run, log exit code
- `scripts/health_check.py`: reads regime_results.csv, checks freshness, prints PASS/FAIL
- Tests: `test_output_count.py`, `test_exit_codes.py`

**Plan 07-03: regime_results.csv Schema Hardening**
- Existing columns (unchanged): `date` (index), `regime_name`, `regime_id`, `prob_0`, `prob_1`, `prob_2`, `confidence`, `VIX`, `SPY_close`, `garch_var_5`, `garch_var_1`
- New columns: `days_in_regime`, `regime_entropy`, `garch_vol_forecast`, `blended_vol_forecast` (NaN), `transition_score` (NaN), `structural_anomaly` (NaN)
- Extension artifact: `data/garch_params.json`
- Extension artifact: `data/oos_regime_labels.csv`
- Tests: `test_regime_results_schema.py`, `test_regime_results_freshness.py`

### Claude's Discretion
- Exact internal structure of stage functions (function signatures, args/kwargs)
- Whether `stages.py` uses a registry dict or inheritance
- Exact log format within the rotating log file
- Whether health_check.py uses argparse or hardcoded paths
- Error handling verbosity inside each stage

### Deferred Ideas (OUT OF SCOPE)
- Automated cron scheduling (cron_run.sh provided but not registered)
- Docker container for pipeline
- Real-time streaming inference
- Dashboard live regime indicator panel
- StudentTHMM full removal from inference.py
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPE-01 | `python scripts/run.py` executes full daily pipeline in under 10 minutes | Stage timing budgets documented; walk-forward isolation is the key enabler |
| PIPE-02 | Exactly 2 HTML outputs exist — dashboard.html and feature_analysis.html | Both HTML writers identified; cleanup approach documented |
| PIPE-03 | regime_results.csv written every run with today's regime, probs, GARCH VaR — cron-safe | Current schema gaps documented; new columns specified; exit code/idempotency requirements documented |
</phase_requirements>

---

## Summary

Phase 7 is a structural refactoring phase, not a feature-addition phase. The codebase already produces the correct outputs — the problem is that they emerge from a 1,000+ line monolith (`train.py`) with no stage boundaries, silent swallowed failures, no enforced output count, and no rotating log. The work is decomposing existing logic into a proper pipeline class without breaking any behavior.

The two HTML outputs (`dashboard.html` from `build_interactive_dashboard()` in `train.py`, and `feature_analysis.html` from `scripts/pipelines/analyze.py`) are already being written by the correct code. The `figures/` directory currently contains exactly these two files. The enforcement problem is that there is no deletion step before a run, so stale files from experimental runs can accumulate. The fix is a single glob-and-delete at pipeline start.

The `regime_results.csv` schema currently does NOT match the CONTEXT.md specification in an important way: the column names use `garch_var_95` (computed per-row in a row loop inside `train()`), not `garch_var_5` and `garch_var_1`. The signals.py file does not write `regime_results.csv` at all — it only reads it. The new columns (`days_in_regime`, `regime_entropy`, `garch_vol_forecast`) need to be added to `signals.py` as a post-processing step that augments the DataFrame before the CSV write in `train.py`.

**Primary recommendation:** Implement the pipeline class by wrapping existing function calls as stage delegates, not by rewriting logic. The logic in `train.py` is sound — only the boundaries need to be drawn.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pipeline orchestration | Pipeline runner (`src/pipeline/runner.py`) | `scripts/run.py` (thin CLI) | runner owns stage sequencing, timing, error handling |
| Stage logic: collect, features, pca, garch | Individual stage functions in `stages.py` | Existing modules (collect.py, features.py, etc.) | stages.py wraps existing functions, adds disk I/O contract |
| Stage logic: train_hmm | Stage function wrapping hdp_hmm + inference modules | `scripts/pipelines/train.py` internals | train.py body becomes the `train_hmm` stage |
| Signal enrichment | `src/signals/signals.py` | None | adds days_in_regime, regime_entropy, garch_vol_forecast |
| Dashboard writing | `build_interactive_dashboard()` in train.py | `scripts/pipelines/analyze.py` | these become the dashboard stage and features stage respectively |
| Output enforcement | Pipeline runner pre-run cleanup | None | delete `figures/*.html` before stages execute |
| Exit code propagation | `scripts/run.py` main() | None | currently partially implemented — gaps identified below |
| Logging | `logs/pipeline.log` via Python logging.handlers | None | RotatingFileHandler, new in Phase 7 |
| Cron wrapper | `scripts/cron_run.sh` | None | thin shell, does not need to understand pipeline internals |

---

## Standard Stack

### Core (already in project, no installation needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `logging` | built-in | Per-stage timestamps, rotating log | No dependency; `RotatingFileHandler` is the standard approach |
| Python stdlib `logging.handlers.RotatingFileHandler` | built-in | 10MB cap, 3 backups | Exact match for CONTEXT.md spec |
| Python stdlib `subprocess` | built-in | Not needed — pipeline is in-process | All stages run in same process |
| Python stdlib `time` | built-in | Wall-clock stage timing | `time.perf_counter()` for sub-second precision |
| Python stdlib `glob` | built-in | `figures/*.html` enumeration for cleanup | Simple and idiomatic |
| `pandas` | already installed | regime_results.csv read/write, schema validation | Already the primary data layer |
| `numpy` | already installed | `regime_entropy` computation (-Σ p log p) | Already used throughout |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | already installed | All new tests | Consistent with existing 160+ test suite |
| `pytest-subprocess` or `subprocess.run` | stdlib | test_exit_codes.py — force a stage failure, capture exit code | Use `subprocess.run(['python', 'scripts/run.py', ...])` — no extra library needed |

**Version verification:** No new packages need to be installed. All functionality is implemented using stdlib and already-installed project dependencies. [VERIFIED: direct codebase inspection]

---

## Architecture Patterns

### System Architecture Diagram

```
scripts/run.py  (thin CLI, --validate flag parsed here)
      |
      v
src/pipeline/runner.py  Pipeline.run_all()
      |
      |-- pre-run: glob.glob('figures/*.html') -> delete all
      |-- pre-run: setup RotatingFileHandler -> logs/pipeline.log
      |
      +--> [collect]    reads config -> writes data/market_data.csv, data/macro_data.csv
      |       t_start ... t_end (5 min budget)
      |
      +--> [features]   reads market CSVs -> writes data/features_transformed.csv
      |       (30 sec budget)
      |
      +--> [pca]        reads features CSV -> writes data/principal_components.csv
      |       (30 sec budget)
      |
      +--> [train_hmm]  reads PCs + market -> fits HDP-HMM -> writes models/
      |       (2 min budget — no walk-forward)
      |
      +--> [garch]      reads regime labels + returns -> writes data/garch_params.json
      |       (30 sec budget)
      |
      +--> [signals]    reads regime state -> augments with new cols -> caller writes CSV
      |       (10 sec budget) — adds days_in_regime, regime_entropy, garch_vol_forecast
      |
      +--> [dashboard]  reads regime_results + signals -> writes figures/dashboard.html
              (30 sec budget)

      [feature_analysis.html is written by analyze stage, called from run.py 'analyze' step]
      NOTE: analyze() writes feature_analysis.html — this is currently NOT part of 'all' flow
      -> Phase 7 must decide: either wire analyze into the daily pipeline, or keep it separate

      --validate flag:
      +--> [walk_forward]   long-running, writes data/oos_regime_labels.csv
              (skip in daily run)

      Exit: sys.exit(0) on success, sys.exit(1) on any stage exception
```

### Recommended Project Structure
```
src/
├── pipeline/
│   ├── __init__.py          # exports Pipeline class
│   ├── stages.py            # stage functions + registry
│   └── runner.py            # Pipeline class: run_all(), run_from(), run_stage()
scripts/
├── run.py                   # updated: delegates to Pipeline.run_all()
├── health_check.py          # new: reads regime_results.csv, prints PASS/FAIL
├── cron_run.sh              # new: activates venv, runs run.py
├── pipelines/
│   ├── train.py             # refactored: logic split into stage functions
│   └── analyze.py           # unchanged
logs/
│   └── pipeline.log         # new: created on first run
data/
│   ├── regime_results.csv   # schema extended
│   ├── garch_params.json    # new: written by garch stage
│   └── oos_regime_labels.csv  # new: written by walk_forward stage
tests/
│   ├── test_pipeline_stages.py       # new
│   ├── test_pipeline_timing.py       # new
│   ├── test_pipeline_idempotent.py   # new
│   ├── test_output_count.py          # new
│   ├── test_exit_codes.py            # new
│   ├── test_regime_results_schema.py # new
│   └── test_regime_results_freshness.py  # new
```

### Pattern 1: Stage as Stateless Function
**What:** Each stage is a standalone function that reads its inputs from known disk paths and writes its outputs to known disk paths. No in-memory state passes between stages.
**When to use:** Every stage in the daily pipeline.
**Example:**
```python
# Source: CONTEXT.md design + codebase inspection
def stage_garch(config) -> dict:
    """Reads regime labels from disk, fits per-regime GARCH, writes garch_params.json."""
    import json
    from src.config import DATA_DIR
    results = pd.read_csv(os.path.join(DATA_DIR, 'regime_results.csv'), index_col=0, parse_dates=True)
    # ... fit_regime_garch logic extracted from train.py lines 2289-2294 ...
    params = {str(r): {'omega': float(res.params['omega']),
                        'alpha': float(res.params['alpha[1]']),
                        'beta': float(res.params['beta[1]'])}
              for r, res in garch_results.items() if hasattr(res, 'params')}
    with open(os.path.join(DATA_DIR, 'garch_params.json'), 'w') as f:
        json.dump(params, f, indent=2)
    return {'garch_results': garch_results}
```

### Pattern 2: Pipeline Runner with Per-Stage Timing
**What:** `runner.py` wraps each stage call in `time.perf_counter()`, logs start/end, catches exceptions to emit exit code 1.
**When to use:** `Pipeline.run_all()`.
**Example:**
```python
# Source: CONTEXT.md design
import time, logging, sys

class Pipeline:
    def run_all(self, validate: bool = False):
        logger = logging.getLogger('pipeline')
        stage_times = {}
        for name, fn in self._stages:
            if name == 'walk_forward' and not validate:
                continue
            t0 = time.perf_counter()
            logger.info(f'[START] {name}')
            try:
                fn(self.config)
            except Exception as e:
                logger.error(f'[FAIL] {name}: {e}')
                sys.exit(1)
            elapsed = time.perf_counter() - t0
            stage_times[name] = elapsed
            logger.info(f'[DONE] {name} — {elapsed:.1f}s')
        total = sum(stage_times.values())
        logger.info(f'[TOTAL] {total:.0f}s')
        print(f"\nPipeline complete in {total:.0f}s")
        for name, t in stage_times.items():
            print(f"  {name:12s} {t:6.1f}s")
```

### Pattern 3: Rotating Log Setup
**What:** `RotatingFileHandler` from `logging.handlers`, configured before first stage runs.
**When to use:** In `Pipeline.__init__()` or `run_all()` preamble.
**Example:**
```python
# Source: Python stdlib docs [ASSUMED — standard pattern, not Context7 verified]
import logging
from logging.handlers import RotatingFileHandler
import os

def _setup_logging(log_dir: str = 'logs') -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger('pipeline')
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(
        os.path.join(log_dir, 'pipeline.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=3,
    )
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    return logger
```

### Pattern 4: HTML Cleanup Before Run
**What:** Delete all `figures/*.html` before starting stages.
**When to use:** At the top of `Pipeline.run_all()`, before any stage executes.
**Example:**
```python
# Source: codebase inspection — figures/ dir currently has exactly 2 HTML files
import glob, os
for f in glob.glob(os.path.join('figures', '*.html')):
    os.remove(f)
```

### Pattern 5: regime_entropy Computation
**What:** Shannon entropy over the K regime probability columns.
**When to use:** In the `signals` stage, applied row-wise to the filtered probability columns.
**Example:**
```python
# Source: Information theory standard; confirmed compatible with existing prob_* columns
prob_cols = [c for c in results.columns if c.startswith('prob_')]
probs = results[prob_cols].values.clip(1e-12, 1)  # avoid log(0)
results['regime_entropy'] = -(probs * np.log(probs)).sum(axis=1)
```

### Pattern 6: days_in_regime Computation
**What:** Count consecutive days at the end of the series where `regime_name` equals the current regime for each day. This is a cumulative run-length that resets on regime change.
**When to use:** In the `signals` stage, applied to the `regime_name` column.
**Example:**
```python
# Source: CONTEXT.md design + existing _regime_awareness() in signals.py (lines 106-113)
# The existing _regime_awareness() already computes the current streak.
# For the CSV column, compute it for ALL rows, not just the last.
def compute_days_in_regime(regime_names: pd.Series) -> pd.Series:
    days = pd.Series(0, index=regime_names.index, dtype=int)
    count = 0
    prev = None
    for i, name in enumerate(regime_names):
        if name == prev:
            count += 1
        else:
            count = 1
        days.iloc[i] = count
        prev = name
    return days
```

### Anti-Patterns to Avoid
- **Calling walk_forward in daily run:** Already a known risk. The `--validate` flag gate in `runner.py` must be enforced as a hard conditional, not a soft default. [VERIFIED: CONTEXT.md]
- **Passing data between stages in memory:** If any stage stores a Python object and passes it to the next stage via function return, the stateless disk contract breaks. The planner must verify stage boundaries respect this.
- **Silent exception swallowing in run.py `all` mode:** Currently, `run.py` lines 180-185 catch `features` failure and `return` instead of `sys.exit(1)`. This is a confirmed bug to fix. [VERIFIED: scripts/run.py lines 178-186]
- **Writing new columns in train.py instead of signals.py:** New columns (`days_in_regime`, `regime_entropy`, `garch_vol_forecast`) must be computed in `signals.py` and applied before the CSV write, to keep signal logic in one place.
- **Modifying frozen files:** `src/core/hdp_hmm.py`, `src/core/inference.py`, `src/features/features.py` are frozen per CONTEXT.md. Do not add imports or function calls that require touching these.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rotating log file | Custom log rotation logic | `logging.handlers.RotatingFileHandler` | stdlib, battle-tested, exact fit for 10MB/3-backup spec |
| Timing each stage | Custom timing class | `time.perf_counter()` + dict | Zero dependencies, nanosecond precision |
| CSV schema validation in tests | Custom column checker | `assert set(EXPECTED_COLS).issubset(df.columns)` + `df.dtypes` | Simpler than any library, fast in CI |
| Exit code capture in tests | Mocking sys.exit | `subprocess.run(['python', 'scripts/run.py', ...], capture_output=True)` | Tests actual process exit code, not mocked behavior |

**Key insight:** Every utility needed for this phase (logging, timing, exit codes, file cleanup) is in Python's standard library. The only new file content is wiring logic, not new algorithms.

---

## Codebase Facts — Findings from Direct Inspection

### What scripts/run.py currently does
[VERIFIED: scripts/run.py, full read]

- **Partial exit code coverage:** `run.py` calls `sys.exit(1)` for `collect`, `features`, and `analyze` only when running those steps directly (not `all`). In `all` mode: `collect` failure returns silently (line 174-177), `features` failure returns silently (line 183-186), `analyze` failure returns silently (line 191-194), `train` failure calls `sys.exit(1)` (line 202). **Bug:** 3 of 4 steps swallow exceptions in `all` mode.
- **No `--validate` flag:** No argparse or flag parsing currently exists. The `all` mode always runs collect, features, analyze, train sequentially.
- **analyze is in the pipeline:** `analyze()` (which writes `feature_analysis.html`) IS called in the `all` mode today. It must remain in the pipeline to satisfy PIPE-02.
- **No Pipeline class:** No `src/pipeline/` directory exists. This is entirely new.
- **No timing:** No stage timing recorded anywhere in run.py.
- **No log file:** No rotating log file exists. `logs/` directory does not exist.

### What scripts/pipelines/train.py currently does (relevant to refactoring)
[VERIFIED: scripts/pipelines/train.py, partial reads covering key sections]

- **Line count:** The file is approximately 2,510 lines. Well above the 500-line threshold from MODEL-03. The monolith is confirmed.
- **Current stage boundaries (inferred from function calls):**
  - Lines 1–60: imports (heavy: arch, hmmlearn, scipy, sklearn, statsmodels, all src modules)
  - Lines 94–217: `walk_forward()` function — currently duplicated here AND in `src/core/orchestrator.py`. The CONTEXT.md freezes `src/core/orchestrator.py`.
  - Lines 220–550: helper visualization functions (`_print_bootstrap_cis`, `_get_blocks`, etc.)
  - Lines 554–2043: `build_interactive_dashboard()` — the dashboard stage function
  - Lines 2045–2405: `train()` — the monolithic training function containing pca + hmm + garch + results writing
  - Lines 2412–2509: `rebuild_dashboard()` — convenience function
- **GARCH stage extraction:** GARCH fitting is at lines 2289–2310. `fit_regime_garch()` is already in `src/core/hmm_training.py`. The garch stage just needs to call it and write `garch_params.json`.
- **regime_results.csv write location:** Line 2352. The `results` DataFrame is assembled in `train()` starting at line 2313 and written at 2352. The new columns must be added before line 2352 OR the signals stage can re-read, augment, and re-write.
- **Current regime_results.csv schema (from train.py lines 2313–2350):**
  - All columns from `market_v` (SPY_close, VIX, QQQ_close, etc.)
  - `regime` (integer)
  - `regime_name` (string)
  - `prob_{name}` for each regime name (NOT `prob_0`, `prob_1`, `prob_2`)
  - `smooth_prob_{name}` for each regime name
  - `market_mode_ratio`
  - `is_oos`, `regime_oos`, `regime_name_oos`
  - `garch_var_95` (not `garch_var_5` / `garch_var_1`)

  **SCHEMA MISMATCH WARNING:** The CONTEXT.md spec lists columns `prob_0`, `prob_1`, `prob_2`, `confidence`, `garch_var_5`, `garch_var_1`. The actual file uses `prob_{regime_name}` (e.g., `prob_Low-Vol`), no `confidence` column, and `garch_var_95`. The `regime_id` column is named `regime` in the actual output. **The planner must decide**: adopt the existing column names as the "locked" schema (not CONTEXT.md's abstract names), or rename them. Renaming would break existing test suite references. Recommendation: treat the actual column names as canonical; the CONTEXT.md used abstract placeholders.

- **walk_forward in train.py:** There is a `walk_forward()` function defined at lines 94–216 of train.py. This is separate from the `src/core/orchestrator.py` version imported at line 51. The local one appears to be a duplicate or pre-refactor version. This is a naming collision that must be resolved when creating the walk_forward stage — use `src/core/orchestrator.walk_forward`, not the local one.

### What scripts/pipelines/analyze.py currently does
[VERIFIED: grep results showing line 227 writes feature_analysis.html]

- Writes `figures/feature_analysis.html`. This is called in run.py `all` mode via `analyze()`.
- This IS part of the current daily pipeline, so `feature_analysis.html` IS being written today.

### What src/signals/signals.py currently does
[VERIFIED: full read]

- Does NOT write `regime_results.csv`. It only reads it (in `print_regime()` in run.py).
- Contains `compute_signals()` which computes `days_in_regime` streak (awareness dict key) but does NOT write it to the CSV.
- Contains `compute_garch_var()` which fits a rolling GARCH on recent returns. This is the basis for `garch_vol_forecast`.
- The new columns for Plan 07-03 need to be added as a post-processing enrichment, either in a new `enrich_results()` function in signals.py, or called inline inside the signals stage.

### figures/ directory state
[VERIFIED: ls output]

- Currently contains exactly: `dashboard.html`, `feature_analysis.html`
- **Exactly 2 files already.** The enforcement problem is preventing future accumulation.
- The `data/` directory is currently empty (no CSV files present — dev environment, not post-run state).

### Extension artifact files
[VERIFIED: ls data/ returned empty]

- `data/garch_params.json` — does NOT exist yet. Will be created by garch stage.
- `data/oos_regime_labels.csv` — does NOT exist yet. Will be created by walk_forward stage.

### Existing test patterns
[VERIFIED: ls tests/, conftest.py read, test_train_refactor.py read]

- All 160+ tests use `pytest` with fixtures in `conftest.py`.
- `conftest.py` provides: `rng` (np.random.RandomState(42)), `synthetic_array`, `synthetic_features`.
- Existing tests test imports, function signatures, and correctness with synthetic data.
- No existing test uses `subprocess.run` to test the full pipeline. The exit code and output count tests will be the first subprocess-based tests.
- `test_train_refactor.py` shows the pattern: test imports and function signatures to verify refactoring didn't break APIs.

---

## Common Pitfalls

### Pitfall 1: Schema Column Name Mismatch
**What goes wrong:** CONTEXT.md specifies `prob_0`, `prob_1`, `prob_2` but actual CSV has `prob_Low-Vol`, `prob_Moderate-Vol`, etc. If tests assert `'prob_0' in df.columns`, they fail.
**Why it happens:** CONTEXT.md used abstract placeholder names; actual code uses regime-name-based column names.
**How to avoid:** In test_regime_results_schema.py, assert that the schema contains `prob_`-prefixed columns matching the current K=3 regime names, not hardcoded `prob_0/1/2`. Use `[c for c in df.columns if c.startswith('prob_')]`.
**Warning signs:** Schema test failures on first run.

### Pitfall 2: walk_forward Naming Collision
**What goes wrong:** train.py defines a local `walk_forward()` at lines 94–216. `src/core/orchestrator.py` also exports `walk_forward`. When stages.py imports from orchestrator, and train.py also has its own, there is a naming collision.
**Why it happens:** The Phase 6 refactor moved walk_forward to orchestrator but left the original in train.py (possibly as a deprecated copy).
**How to avoid:** The walk_forward stage function should explicitly import from `src.core.orchestrator`, not from train.py.
**Warning signs:** `ImportError` or silent wrong-function-being-called when walk_forward stage runs.

### Pitfall 3: analyze() Not Wired into New Pipeline
**What goes wrong:** The new `Pipeline.run_all()` calls the 7 locked stages but omits `analyze()`. Feature_analysis.html is not written, PIPE-02 fails.
**Why it happens:** The 7-stage table in CONTEXT.md (collect, features, pca, train_hmm, garch, signals, dashboard) does not list `analyze` as a named stage. But `analyze()` writes `feature_analysis.html`, which is one of the exactly-2 required outputs.
**How to avoid:** Either (a) add `features_analysis` as an 8th stage in the pipeline, or (b) call `analyze()` as part of the `features` stage after writing features_transformed.csv. The safest choice is option (a) — add it as a named stage after `features`.
**Warning signs:** After pipeline refactor, `ls figures/` shows only `dashboard.html`.

### Pitfall 4: Silent Exit on `all` Mode
**What goes wrong:** Current `run.py` swallows exceptions for collect/features/analyze in `all` mode and returns without `sys.exit(1)`. After refactor, if this behavior is replicated in runner.py, stage failures are invisible to cron.
**Why it happens:** The original run.py had inconsistent exit code handling (confirmed at lines 174-186).
**How to avoid:** In `runner.py`, ALL stage exceptions must call `sys.exit(1)`. No stage has a "soft fail" mode in the daily pipeline.
**Warning signs:** `test_exit_codes.py` passes but cron misses real failures.

### Pitfall 5: Idempotency Broken by Row-Loop GARCH
**What goes wrong:** `train()` computes `garch_var_95` via a per-row loop that calls `compute_garch_var()` with `recent_returns` from the previous 20 rows (lines 2338–2350). This may produce slightly different float values on two runs if floating-point ordering differs.
**Why it happens:** `compute_garch_var()` fits a fresh GARCH model on each of the N rows — not deterministic if GARCH convergence varies.
**How to avoid:** For the `garch_vol_forecast` column (the renamed replacement), use the full `fit_regime_garch()` result to compute conditional volatility from the stored GARCH params, not re-fitting per-row. This is both faster and deterministic. The `garch_var_95` column can be computed once using the GARCH result's `.conditional_volatility`.
**Warning signs:** `test_pipeline_idempotent.py` fails with small float differences.

### Pitfall 6: Timing Test Flakiness on Dev Machine
**What goes wrong:** `test_pipeline_timing.py` runs the full pipeline in CI or a slow dev machine and exceeds 600 seconds, causing spurious test failures.
**Why it happens:** HDP-HMM SVI training time depends heavily on CPU speed and JAX compilation.
**How to avoid:** Mark `test_pipeline_timing.py` with `@pytest.mark.slow` and exclude it from the default `pytest` run (use `pytest -m "not slow"` for CI). Run it as an explicit gate check, not in every commit. Alternatively, test timing on a synthetic dataset with minimal SVI steps.
**Warning signs:** Flaky CI pipeline.

---

## Code Examples

### regime_entropy column
```python
# Source: direct codebase inspection of prob_* column structure in train.py
# Confirmed: prob_cols are named prob_{regime_name}, e.g. prob_Low-Vol
prob_cols = [c for c in results.columns if c.startswith('prob_')]
probs = results[prob_cols].values.clip(1e-12, 1)
results['regime_entropy'] = -(probs * np.log(probs)).sum(axis=1)
```

### garch_vol_forecast from existing GARCH result
```python
# Source: train.py lines 2289-2294; fit_regime_garch returns arch ModelResult objects
# Use .conditional_volatility (in % scale, /100 to get decimal daily vol)
garch_vol = pd.Series(np.nan, index=results.index)
spy_col = 'SPY_close'
spy_ret = np.log(results[spy_col] / results[spy_col].shift(1)) * 100
for regime_name, res in garch_results.items():
    if hasattr(res, 'conditional_volatility'):
        cond_vol = res.conditional_volatility.reindex(results.index) / 100
        mask = results['regime_name'] == regime_name
        garch_vol[mask] = cond_vol[mask]
results['garch_vol_forecast'] = garch_vol
```

### garch_params.json format
```python
# Source: CONTEXT.md specifics section
# {"0": {"omega": ..., "alpha": ..., "beta": ...}, "1": {...}, "2": {...}}
import json
params = {}
for regime_name, res in garch_results.items():
    if hasattr(res, 'params'):
        params[str(regime_name)] = {
            'omega': float(res.params.get('omega', 0.0)),
            'alpha': float(res.params.get('alpha[1]', 0.0)),
            'beta':  float(res.params.get('beta[1]', 0.0)),
        }
with open(os.path.join(DATA_DIR, 'garch_params.json'), 'w') as f:
    json.dump(params, f, indent=2)
```

### health_check.py logic
```python
# Source: CONTEXT.md Plan 07-02 spec
import pandas as pd
import sys
from datetime import date, timedelta
from src.config import DATA_DIR
import os

path = os.path.join(DATA_DIR, 'regime_results.csv')
if not os.path.exists(path):
    print('FAIL: regime_results.csv not found')
    sys.exit(1)
df = pd.read_csv(path, index_col=0, parse_dates=True)
last_date = df.index[-1].date()
today = date.today()
# Allow up to 3 trading-day lag (weekends, holidays)
staleness = (today - last_date).days
if staleness > 5:  # 5 calendar days ~ 3 trading days
    print(f'FAIL: regime_results.csv last updated {last_date} ({staleness} days ago)')
    sys.exit(1)
print(f'PASS: regime_results.csv current as of {last_date}')
sys.exit(0)
```

---

## Runtime State Inventory

Not applicable — this is not a rename/refactor/migration phase. It is a pipeline modularization phase with no stored string keys, service configs, or OS-registered state that needs renaming.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All stages | Yes (implied by existing tests passing) | 3.13 (cpython-313 in __pycache__) | — |
| `arch` library | GARCH stage | Yes | installed (imported in train.py line 25) | — |
| `joblib` | Model checkpointing | Yes | installed (imported in train.py line 22) | — |
| `plotly` | Dashboard stage | Yes | installed (imported in build_interactive_dashboard) | — |
| `hmmlearn` | HMM training | Yes | installed (imported in train.py line 28) | — |
| `NumPyro/JAX` | HDP-HMM fitting | Yes (implied by Phase 6 complete) | unknown version | — |
| `logs/` directory | RotatingFileHandler | No — must be created | — | `os.makedirs('logs', exist_ok=True)` in pipeline setup |
| `data/` directory | All stages | No files present in dev env | — | Stages create as needed |
| `figures/` directory | Dashboard stage | Yes — confirmed by ls (has 2 HTML files) | — | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** `logs/` directory — created by pipeline setup code on first run.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (version unverified, but 160+ tests already passing) |
| Config file | Not found — check for pytest.ini or pyproject.toml |
| Quick run command | `pytest tests/ -m "not slow" -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | Full pipeline completes in <600s | integration timing | `pytest tests/test_pipeline_timing.py -m slow` | No — Wave 0 |
| PIPE-01 | Each stage produces expected output file | integration | `pytest tests/test_pipeline_stages.py -x` | No — Wave 0 |
| PIPE-02 | Exactly 2 HTML files exist after run | integration | `pytest tests/test_output_count.py -x` | No — Wave 0 |
| PIPE-02 | Running twice still yields exactly 2 HTML files | integration | `pytest tests/test_output_count.py -x` | No — Wave 0 |
| PIPE-03 | regime_results.csv has all required columns + correct dtypes | unit | `pytest tests/test_regime_results_schema.py -x` | No — Wave 0 |
| PIPE-03 | Last row date equals today after run | integration | `pytest tests/test_regime_results_freshness.py -x` | No — Wave 0 |
| PIPE-03 | Two runs produce identical regime_results.csv | integration | `pytest tests/test_pipeline_idempotent.py -x` | No — Wave 0 |
| PIPE-01/03 | Stage failure → exit code 1 | integration | `pytest tests/test_exit_codes.py -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -m "not slow" -x --tb=short`
- **Per wave merge:** `pytest tests/ -x --tb=short`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_pipeline_stages.py` — covers PIPE-01 stage isolation
- [ ] `tests/test_pipeline_timing.py` — covers PIPE-01 timing gate (mark as slow)
- [ ] `tests/test_pipeline_idempotent.py` — covers PIPE-03 idempotency
- [ ] `tests/test_output_count.py` — covers PIPE-02 HTML count
- [ ] `tests/test_exit_codes.py` — covers PIPE-01/03 exit code contract
- [ ] `tests/test_regime_results_schema.py` — covers PIPE-03 schema
- [ ] `tests/test_regime_results_freshness.py` — covers PIPE-03 freshness
- [ ] `src/pipeline/__init__.py`, `stages.py`, `runner.py` — new package
- [ ] `scripts/health_check.py` — new script
- [ ] `scripts/cron_run.sh` — new shell wrapper
- [ ] `logs/` directory — created at runtime

---

## Validation Architecture — Detailed Test Approaches

### Test: Pipeline Timing Gate (<600 seconds)
```python
# tests/test_pipeline_timing.py
import subprocess, time, pytest

@pytest.mark.slow
def test_pipeline_under_600s():
    t0 = time.perf_counter()
    result = subprocess.run(
        ['python', 'scripts/run.py'],
        capture_output=True, cwd='/path/to/repo'
    )
    elapsed = time.perf_counter() - t0
    assert result.returncode == 0, f"Pipeline failed: {result.stderr.decode()}"
    assert elapsed < 600, f"Pipeline took {elapsed:.0f}s (budget: 600s)"
```
**Caveat:** This test requires live data and a full model run. Mark `@pytest.mark.slow` and exclude from CI default run. For unit-level timing confidence, test individual stages with synthetic data against their per-stage budgets.

### Test: Exactly-2-HTML Enforcement
```python
# tests/test_output_count.py
import subprocess, glob, os, pytest

def test_exactly_two_html_files(tmp_path, monkeypatch):
    # Run pipeline twice; count HTML files after second run
    for _ in range(2):
        subprocess.run(['python', 'scripts/run.py'], check=True)
    html_files = glob.glob('figures/*.html')
    assert len(html_files) == 2, f"Expected 2 HTML files, found: {html_files}"
    names = {os.path.basename(f) for f in html_files}
    assert names == {'dashboard.html', 'feature_analysis.html'}
```
**Note:** This is an integration test requiring a full run environment. For unit-level verification, test that `Pipeline.run_all()` calls the cleanup function and verify the cleanup function deletes all `figures/*.html`.

### Test: regime_results.csv Schema Correctness
```python
# tests/test_regime_results_schema.py
import pandas as pd
import pytest
from src.config import DATA_DIR
import os

REQUIRED_COLUMNS = [
    'regime', 'regime_name',
    'VIX', 'SPY_close',
    'garch_var_95',
    'days_in_regime', 'regime_entropy', 'garch_vol_forecast',
    'blended_vol_forecast', 'transition_score', 'structural_anomaly',
]

def test_schema_columns_exist():
    path = os.path.join(DATA_DIR, 'regime_results.csv')
    if not os.path.exists(path):
        pytest.skip("regime_results.csv not present — run pipeline first")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"

def test_prob_columns_exist():
    path = os.path.join(DATA_DIR, 'regime_results.csv')
    if not os.path.exists(path):
        pytest.skip("regime_results.csv not present")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    prob_cols = [c for c in df.columns if c.startswith('prob_')]
    assert len(prob_cols) == 3, f"Expected 3 prob_ columns (K=3), found: {prob_cols}"

def test_placeholder_columns_are_nan():
    path = os.path.join(DATA_DIR, 'regime_results.csv')
    if not os.path.exists(path):
        pytest.skip("regime_results.csv not present")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    for col in ['blended_vol_forecast', 'transition_score', 'structural_anomaly']:
        if col in df.columns:
            assert df[col].isna().all(), f"{col} should be all NaN in Phase 7"
```

### Test: Idempotency (same output on 2 runs)
```python
# tests/test_pipeline_idempotent.py
import subprocess, pandas as pd, pytest
from src.config import DATA_DIR
import os

@pytest.mark.slow
def test_idempotent_regime_results():
    path = os.path.join(DATA_DIR, 'regime_results.csv')
    # Run 1
    subprocess.run(['python', 'scripts/run.py'], check=True)
    df1 = pd.read_csv(path, index_col=0, parse_dates=True)

    # Run 2
    subprocess.run(['python', 'scripts/run.py'], check=True)
    df2 = pd.read_csv(path, index_col=0, parse_dates=True)

    # Compare key deterministic columns
    for col in ['regime_name', 'days_in_regime', 'regime_entropy']:
        pd.testing.assert_series_equal(
            df1[col], df2[col], check_names=True,
            err_msg=f"Column {col} differs between runs"
        )
    # Float columns — use approximate equality
    for col in ['garch_vol_forecast']:
        if col in df1.columns and col in df2.columns:
            pd.testing.assert_series_equal(
                df1[col], df2[col], check_exact=False, rtol=1e-4,
                err_msg=f"Column {col} differs between runs (rtol=1e-4)"
            )
```
**Note:** True idempotency requires that HDP-HMM SVI converges to the same solution with the same random seed. This is guaranteed by `np.random.seed(RANDOM_SEED)` at the top of `train()` (line 2053) AND by the JAX PRNG key being seeded with `RANDOM_SEED`. Verify that the HDP-HMM SVI inference in `src/core/hdp_hmm.py` uses the config's `RANDOM_SEED` — if it doesn't, results may not be idempotent.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic train() function | Stage-based Pipeline class | Phase 7 (this phase) | Enables per-stage timing, isolation, and extension points |
| Silent exception swallowing in `all` mode | Exit code 1 on any failure | Phase 7 | Cron deployability |
| No log file | RotatingFileHandler, 10MB/3 backups | Phase 7 | Debuggability of overnight runs |
| Walk-forward in daily run | Walk-forward isolated to `--validate` flag | Phase 7 | Core enabler of <10min daily run |

**Deprecated/outdated:**
- Local `walk_forward()` in train.py (lines 94–216): superseded by `src/core/orchestrator.walk_forward` from Phase 6 refactor. Should be removed when train.py is refactored into stages.
- Per-row GARCH loop for `garch_var_95` (lines 2338–2350): replaced by `garch_vol_forecast` column computed from the already-fitted `garch_results` object. More efficient and deterministic.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `test_pipeline_timing.py` should be marked `@pytest.mark.slow` to avoid CI timeouts | Validation Architecture | If not excluded, CI fails on every commit during HDP training |
| A2 | JAX/NumPyro SVI uses RANDOM_SEED for reproducibility | Pitfall 5, Idempotency test | If SVI is non-deterministic, idempotency test cannot pass; would need to mark that test as non-deterministic or test only the non-HMM columns |
| A3 | `analyze()` (which writes feature_analysis.html) should be added as an 8th stage in the pipeline, not remain a separate `run.py` command | Pitfall 3, Architecture | If analyze is not wired in, PIPE-02 fails |
| A4 | The `garch_results` object from `fit_regime_garch()` is indexed by regime name (string), not integer | Code Examples — garch_vol_forecast | If indexed by integer, the mask logic in garch_vol_forecast example needs adjustment |

---

## Open Questions (RESOLVED)

1. **CONTEXT.md schema names vs. actual column names**
   - RESOLVED: Treat actual column names as canonical. Do NOT rename existing columns. The CONTEXT.md names (`prob_0`, `prob_1`, `prob_2`, `regime_id`, `garch_var_5`, `garch_var_1`) were abstract placeholders. Actual CSV uses `prob_Low-Vol`, `prob_Moderate-Vol`, `prob_High-Vol`, `regime` (int), `garch_var_95`. Renaming would break existing 160+ tests and downstream consumers. Plans 07-01 and 07-03 use actual column names throughout. CONTEXT.md updated to match.

2. **analyze stage positioning**
   - RESOLVED: `feature_analysis` is added as an 8th pipeline stage inserted after `features` (since it reads `features_transformed.csv`). This satisfies PIPE-02 by guaranteeing `figures/feature_analysis.html` is written as part of every daily run. The 7-stage table in CONTEXT.md was missing this stage; all plans use the 8-stage structure.

---

## Sources

### Primary (HIGH confidence)
- `scripts/run.py` — direct read, all 221 lines
- `scripts/pipelines/train.py` — partial reads covering imports (1-60), walk_forward (94-216), train() body (2045-2405), rebuild_dashboard (2412-2509), dashboard builder (554-600)
- `src/signals/signals.py` — direct read, all 733 lines
- `src/config.py` — direct read, all 204 lines
- `.planning/phases/07-daily-pipeline-clean-outputs/07-CONTEXT.md` — direct read
- `.planning/COMPLETION-PLAN.md` — direct read
- `.planning/REQUIREMENTS.md` — direct read
- `.planning/STATE.md` — direct read
- `tests/conftest.py` — direct read
- `tests/test_train_refactor.py` — direct read (first 60 lines)
- Directory listings: `tests/`, `figures/`, `src/`, `scripts/`, `scripts/pipelines/`, `logs/`

### Secondary (MEDIUM confidence)
- Python stdlib documentation for `logging.handlers.RotatingFileHandler` — pattern is standard, not looked up in this session [ASSUMED standard]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, verified by import statements
- Architecture: HIGH — based on direct code inspection, not assumptions
- Pitfalls: HIGH — most pitfalls are confirmed code observations, not speculative
- Schema: MEDIUM — actual CSV not present in dev environment; schema inferred from train.py write logic

**Research date:** 2026-04-21
**Valid until:** 2026-05-21 (stable codebase, no fast-moving dependencies)
