---
phase: 07-daily-pipeline-clean-outputs
plan: "01"
subsystem: pipeline
tags: [pipeline, stages, runner, refactor, tdd, wave-0-tests]
dependency_graph:
  requires: []
  provides:
    - src/pipeline: Pipeline class + STAGES registry (9 stages)
    - scripts/run.py: argparse entry point with --validate flag
  affects:
    - scripts/pipelines/train.py: duplicate walk_forward removed
    - scripts/run.py: rewired to use Pipeline class
tech_stack:
  added: []
  patterns:
    - Stateless disk-to-disk stage functions with GSD_FORCE_STAGE_FAIL test hook
    - Per-stage wall-clock timing in Pipeline.run_all()
    - Hard exit-code contract: every stage exception triggers sys.exit(1)
    - walk_forward gated behind --validate flag (T-07-01 mitigation)
key_files:
  created:
    - src/pipeline/__init__.py
    - src/pipeline/stages.py
    - src/pipeline/runner.py
    - tests/test_pipeline_stages.py
    - tests/test_pipeline_timing.py
    - tests/test_pipeline_idempotent.py
    - tests/test_output_count.py
    - tests/test_exit_codes.py
    - tests/test_regime_results_schema.py
    - tests/test_regime_results_freshness.py
  modified:
    - scripts/run.py
    - scripts/pipelines/train.py
decisions:
  - "stage_pca is a no-op in run_all() because PCA is embedded in train(); kept in STAGES registry to satisfy 8-stage design contract"
  - "stage_train_hmm delegates entirely to train() monolith; full decomposition is out of scope for this plan"
  - "stage_signals adds PIPE-03 placeholder columns (all-NaN) to satisfy schema contract; Plan 07-03 wires real data"
metrics:
  duration: "425 seconds (~7 minutes)"
  completed: "2026-04-25"
  tasks_completed: 4
  files_created: 10
  files_modified: 2
  tests_added: 7
---

# Phase 07 Plan 01: Pipeline Modularization Summary

**One-liner:** src/pipeline package with 9 stateless stages, Pipeline runner (timing + sys.exit(1) contract + --validate gate), 7 Wave-0 test stubs, and duplicate walk_forward removed from train.py.

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Wave-0 test stubs (RED) | 7efa87c | 7 test files under tests/ |
| 2 | src/pipeline/ package (stages + runner) | 7693978 | src/pipeline/__init__.py, stages.py, runner.py |
| 3 | scripts/run.py rewired to Pipeline | 9ab377a | scripts/run.py |
| 4 | Remove duplicate walk_forward from train.py | 741916c | scripts/pipelines/train.py |

## What Was Built

### src/pipeline/ Package

- **`__init__.py`**: Exports `Pipeline` class
- **`stages.py`**: 9 stateless stage functions in LOCKED order:
  1. `stage_collect` — delegates to `src.features.collect.collect()`
  2. `stage_features` — delegates to `src.features.features.prepare_features()`
  3. `stage_feature_analysis` — delegates to `scripts.pipelines.analyze.analyze()`
  4. `stage_pca` — no-op (PCA is embedded in train()); keeps 8-stage design contract
  5. `stage_train_hmm` — delegates to `scripts.pipelines.train.train()`; returns results_df + market_v
  6. `stage_garch` — calls `fit_regime_garch()`; writes `data/garch_params.json`
  7. `stage_signals` — enriches regime_results.csv with PIPE-03 placeholder columns
  8. `stage_dashboard` — delegates to `scripts.pipelines.train.rebuild_dashboard()`
  9. `stage_walk_forward` — imports from `src.core.orchestrator` (not train.py); writes `data/oos_regime_labels.csv`
  - Every stage has `GSD_FORCE_STAGE_FAIL` testability hook

- **`runner.py`**: `Pipeline` class with:
  - `run_all(validate=False)` — executes 8 daily stages; appends walk_forward iff validate=True; per-stage wall-clock timing; any exception → sys.exit(1)
  - `run_stage(name)` — single stage by name
  - `run_from(name, validate)` — run from a named stage forward
  - 3 `sys.exit(1)` call sites (one per method)

### scripts/run.py Rewire

- Replaced ad-hoc if/elif with `argparse` + `Pipeline.run_all/run_stage`
- `--validate` flag gates walk_forward (T-07-01 threat mitigation)
- Silent-swallow exception handlers removed (was: `except Exception: return` in collect/features/analyze)
- Back-compat aliases: `analyze` → `feature_analysis`, `train` → `train_hmm`
- Non-pipeline commands `regime` and `trust` preserved

### scripts/pipelines/train.py Refactor

- Deleted lines 90–218: local `walk_forward()` function (Phase-6 leftover duplicate)
- The `from src.core.orchestrator import walk_forward` import (line 55) now resolves the remaining internal call
- Added module-level docstring marking train.py as a legacy helper module
- `build_interactive_dashboard()`, `train()`, `rebuild_dashboard()` all preserved

### Test Files (Wave 0 — 7 stubs)

| File | Marker | Purpose |
|------|--------|---------|
| test_pipeline_stages.py | none | Package import + STAGES registry + callable check |
| test_pipeline_timing.py | slow | Pipeline completes in <600s |
| test_pipeline_idempotent.py | slow | Two runs produce identical regime/regime_name columns |
| test_output_count.py | slow | Exactly 2 HTML files in figures/ after 2 runs |
| test_exit_codes.py | slow | GSD_FORCE_STAGE_FAIL=features → exit code 1 |
| test_regime_results_schema.py | none | PIPE-03 schema contract (canonical column names) |
| test_regime_results_freshness.py | slow | Last row within 5 calendar days of today |

## Verification Results

```
tests/test_pipeline_stages.py  3 passed
tests/test_regime_results_schema.py  3 skipped (regime_results.csv not present — expected)
```

```
python -c "from src.pipeline import Pipeline" → OK
python scripts/run.py --help → shows --validate flag
grep -c "^def walk_forward" scripts/pipelines/train.py → 0
```

## Deviations from Plan

### Auto-added: PIPE-03 placeholder columns in stage_signals

**Rule:** Rule 2 (missing critical functionality for schema contract)
**Found during:** Task 2 implementation
**Issue:** test_regime_results_schema.py requires `days_in_regime`, `regime_entropy`, `garch_vol_forecast`, `blended_vol_forecast`, `transition_score`, `structural_anomaly` columns in regime_results.csv. train() does not write these.
**Fix:** `stage_signals` enriches regime_results.csv with all 6 columns as all-NaN placeholders after each run. Plan 07-03 wires real values for days_in_regime, regime_entropy, garch_vol_forecast.
**Files modified:** src/pipeline/stages.py

### Design note: stage_pca is a no-op

**Found during:** Task 2
**Issue:** The plan specifies `stage_pca` writes `data/principal_components.csv`, but PCA is tightly coupled inside `train()` (which writes `data/pca_components.csv` directly). Extracting PCA from train() would require a full decomposition of the 2,400-line `train()` monolith — out of scope per Task 4's instructions ("minimal, surgical refactor").
**Resolution:** `stage_pca` is a documented no-op that preserves the 8-stage design contract. `train()` (called by `stage_train_hmm`) still writes `pca_components.csv` as before. The stage registry slot is held for Plan 08+ when PCA is extracted.

### runner.py created in Task 2 (not Task 3)

**Found during:** Task 2
**Issue:** `src/pipeline/__init__.py` imports from `src.pipeline.runner`. Creating `__init__.py` without `runner.py` caused ImportError, preventing Task 2's verification from passing.
**Resolution:** runner.py was created alongside stages.py in Task 2. Task 3 updated scripts/run.py as planned. No behavioral difference — the full runner content from the Task 3 spec was implemented.

## Known Stubs

| Stub | File | Purpose |
|------|------|---------|
| `blended_vol_forecast = NaN` | src/pipeline/stages.py (stage_signals) | Future phase (vol forecast ensemble) |
| `transition_score = NaN` | src/pipeline/stages.py (stage_signals) | Future phase (transition predictor) |
| `structural_anomaly = NaN` | src/pipeline/stages.py (stage_signals) | Future phase (anomaly detection) |
| `days_in_regime = NaN` | src/pipeline/stages.py (stage_signals) | Plan 07-03 wires real values |
| `regime_entropy = NaN` | src/pipeline/stages.py (stage_signals) | Plan 07-03 wires real values |
| `garch_vol_forecast = NaN` | src/pipeline/stages.py (stage_signals) | Plan 07-03 wires real values |

The first 3 are intentional permanent stubs for future phases per the PIPE-03 spec. The last 3 are temporary stubs that Plan 07-03 resolves.

## Threat Flags

None. All new surface (GSD_FORCE_STAGE_FAIL env hook, --validate CLI flag) is within the plan's documented threat model (T-07-01, T-07-02).

## Self-Check: PASSED

Files created:
- src/pipeline/__init__.py ✓
- src/pipeline/stages.py ✓
- src/pipeline/runner.py ✓
- tests/test_pipeline_stages.py ✓
- tests/test_pipeline_timing.py ✓
- tests/test_pipeline_idempotent.py ✓
- tests/test_output_count.py ✓
- tests/test_exit_codes.py ✓
- tests/test_regime_results_schema.py ✓
- tests/test_regime_results_freshness.py ✓

Commits verified:
- 7efa87c ✓ (test stubs)
- 7693978 ✓ (pipeline package)
- 9ab377a ✓ (run.py update)
- 741916c ✓ (train.py refactor)
