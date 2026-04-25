---
phase: 07-daily-pipeline-clean-outputs
plan: "03"
subsystem: signals
tags: [signals, schema, enrichment, garch, entropy, pipeline, wave-2]
dependency_graph:
  requires:
    - 07-01: Pipeline package structure (stages.py, runner.py)
    - 07-02: Cron infrastructure (runner.py logging, HTML cleanup)
  provides:
    - src/signals/signals.py: enrich_results() + compute_days_in_regime() public API
    - scripts/pipelines/train.py: single enrichment call-site before regime_results.csv write
  affects:
    - data/regime_results.csv: gains 6 new columns on every pipeline run
    - src/pipeline/stages.py: stage_signals now preserves computed values (changed=False)
tech_stack:
  added: []
  patterns:
    - enrich_results() is a pure DataFrame transformation — no side effects, no disk I/O
    - garch_vol_forecast from .conditional_volatility (fitted once, deterministic — not per-row refit)
    - compute_days_in_regime uses sequential scan O(n) — no pandas rolling gotchas
    - prob_cols filtered by startswith('prob_') and 'smooth' not in c — safe across K=3/4 schemas
    - Placeholder NaN columns documented in enrich_results docstring with phase assignments
key_files:
  created: []
  modified:
    - src/signals/signals.py
    - scripts/pipelines/train.py
decisions:
  - "enrich_results call-site is in train.py (line 2228) not stage_signals — enrichment happens at the single canonical write point"
  - "stage_signals in stages.py correctly preserves computed values post-Plan-07-03 (changed=False when all 6 cols present)"
  - "garch_vol_forecast key normalization handles both string regime name keys and integer keys (converts integer to regime name by position)"
  - "stages.py left unchanged — no code changes needed; enrichment flows through existing train() delegation"
metrics:
  duration: "5 minutes"
  completed: "2026-04-24"
  tasks_completed: 3
  files_created: 0
  files_modified: 2
  tests_added: 0
---

# Phase 07 Plan 03: regime_results.csv Schema Hardening Summary

**One-liner:** enrich_results() in signals.py adds 6 Phase-7 columns (days_in_regime, regime_entropy, garch_vol_forecast + 3 NaN placeholders) via single call-site in train.py line 2228, immediately before the regime_results.csv write.

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Add enrich_results() and compute_days_in_regime() to signals.py | 8b223d4 | src/signals/signals.py |
| 2 | Wire enrich_results() into train.py before CSV write | 459c121 | scripts/pipelines/train.py |
| 3 | Verify stages.py unchanged; document deferred items | f9eff8e | .planning/phases/07-daily-pipeline-clean-outputs/deferred-items.md |

## What Was Built

### src/signals/signals.py — Two New Functions

**`compute_days_in_regime(regime_names: pd.Series) -> pd.Series`**
- Cumulative run-length counter that resets to 1 on each regime change
- Sequential scan — O(n), no pandas groupby complexity
- Unit test verified: `['A','A','A','B','B','A'] -> [1,2,3,1,2,1]`

**`enrich_results(results: pd.DataFrame, garch_results: dict | None) -> pd.DataFrame`**
- Pure transformation — returns a copy, does not mutate input
- 3 computed columns:
  - `days_in_regime`: delegates to `compute_days_in_regime(out['regime_name'])`
  - `regime_entropy`: `-Σ p_k log(p_k)` over `prob_*` columns (excluding `smooth_*`), clipped to `[1e-12, 1]`
  - `garch_vol_forecast`: `.conditional_volatility / 100` per regime (decimal daily vol), masked by `regime_name`, reindexed to results.index
- 3 placeholder NaN columns: `blended_vol_forecast` (Phase 9), `transition_score` (Phase 11), `structural_anomaly` (Phase 12)
- All existing canonical columns PRESERVED (no renames, no deletions)
- `garch_results=None` → `garch_vol_forecast` all-NaN (safe for tests without GARCH)

**Enrichment call-site — train.py line 2228:**
```python
results = enrich_results(results, garch_results)   # line 2228
results.to_csv(os.path.join(DATA_DIR, 'regime_results.csv'))  # line 2229
```

### GARCH Determinism (Pitfall 5 mitigation)

`garch_vol_forecast` uses `.conditional_volatility` from the already-fitted `arch` ModelResult object — the GARCH is fitted once per regime across the full history (`fit_regime_garch` at lines 2166-2170 of train.py), not per-row. This guarantees:
- Idempotency: two runs produce identical `garch_vol_forecast` values
- Speed: avoids N row-level GARCH fits (was O(N) fits → O(1) attribute read)

**Key normalization for garch_results dict keys:** The dict may be keyed by string regime names OR integer indices. `enrich_results` normalizes: if the key is a digit string (`"0"`, `"1"`, `"2"`), it maps to `regime_names_in_data[int(key)]`. Otherwise, uses the key directly as regime name.

### stages.py — Unchanged (No Modifications)

`stage_signals` reads `regime_results.csv` after `train()` and only adds columns if missing. After Plan 07-03 wires real enrichment into `train()`, all 6 columns are already present in the CSV (`changed = False`) — the all-NaN placeholder fallback is never triggered in normal flow. No code change needed.

## Column Schema After Enrichment

| Column | Type | Computed? | Notes |
|--------|------|-----------|-------|
| `days_in_regime` | int | Yes | Cumulative run-length, resets on regime_name change |
| `regime_entropy` | float | Yes | Shannon entropy over prob_* cols; always finite if prob_cols exist |
| `garch_vol_forecast` | float | Yes | NaN if garch_results=None or regime not in dict |
| `blended_vol_forecast` | float (NaN) | No | Phase 9 placeholder |
| `transition_score` | float (NaN) | No | Phase 11 placeholder |
| `structural_anomaly` | float (NaN) | No | Phase 12 placeholder |

## Verification Results

### Task 1 inline test (synthetic data):
```
compute_days_in_regime(['A','A','A','B','B','A']) == [1,2,3,1,2,1]  PASS
enrich_results with garch_results=None → all 6 columns present      PASS
regime_entropy notna().all()                                         PASS
garch_vol_forecast isna().all() (no garch_results)                  PASS
3 placeholder columns isna().all()                                   PASS
```

### Task 2 import checks:
```
from scripts.pipelines.train import train                            PASS
from scripts.pipelines.train import train, build_interactive_dashboard, rebuild_dashboard  PASS
grep "enrich_results(" scripts/pipelines/train.py (non-def) → 1 match  PASS
enrich_results call at line 2228, to_csv at line 2229                PASS
```

### Task 3 schema test behavior:
```
pytest tests/test_regime_results_schema.py (no data dir) → 3 skipped  PASS
pytest tests/test_pipeline_stages.py → 3 passed                      PASS
```

### Enrichment on actual regime_results.csv (integration check):
```
Shape: (3723, 45) → (3723, 51) — 6 new columns added
days_in_regime: all non-null, starts [1,2,3,4,5,6,...]
regime_entropy: all non-null, values in [0.0002, 2.19]
garch_vol_forecast: all-NaN (garch_results=None in test)
3 placeholder cols: all-NaN
```

## Deviations from Plan

None — plan executed exactly as written. stages.py was inspected as specified; no code changes were needed (stage_signals correctly defers to train()'s enrichment).

## Known Stubs

| Stub | File | Reason |
|------|------|--------|
| `blended_vol_forecast = NaN` | src/signals/signals.py (enrich_results) | Phase 9 fills — vol forecast ensemble |
| `transition_score = NaN` | src/signals/signals.py (enrich_results) | Phase 11 fills — transition predictor |
| `structural_anomaly = NaN` | src/signals/signals.py (enrich_results) | Phase 12 fills — anomaly detection |

These are intentional permanent stubs per the PIPE-03 spec. Downstream consumers (Algo-Trading-Bot, Portfolio-Manager) must `.fillna()` or `.isna()`-guard these columns per T-07-09 mitigation.

## Pre-existing Issues (Not Introduced by This Plan)

1. **test_dashboard_refactor.py::test_dashboard_loads_regime_results** — `ModuleNotFoundError: No module named 'dashboard'`. Pre-existing on base commit cd07baa.

2. **test_regime_results_schema.py — prob_Moderate-Vol vs prob_Medium-Vol mismatch** — Test expects `prob_Moderate-Vol` but actual model (K=3) produces `prob_Medium-Vol`. The plan spec used "Moderate-Vol" but `src/config.py` REGIME_NAMES for K=3 is `['Low-Vol', 'Medium-Vol', 'High-Vol']`. This naming drift predates Plan 07-03. The schema test `test_prob_columns_named_by_regime` will fail after a real pipeline run. Fix: update test to check `prob_Medium-Vol`, or align config naming — either change is outside Plan 07-03 scope.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries beyond what the plan's threat model covers. T-07-09 (placeholder columns consumed before Phase 9/11/12) is mitigated via docstring documentation in `enrich_results`.

## Self-Check: PASSED

Files modified:
- src/signals/signals.py: contains `def enrich_results` (1 match) and `def compute_days_in_regime` (1 match)
- scripts/pipelines/train.py: `enrich_results` in import at line 49; call at line 2228 (before to_csv at line 2229)

Commits verified:
- 8b223d4: feat(07-03): add enrich_results() and compute_days_in_regime() to signals.py
- 459c121: feat(07-03): wire enrich_results() into train.py before regime_results.csv write
- f9eff8e: chore(07-03): document deferred items from Task 3 verification
