---
phase: 05-feature-engineering-overhaul
plan: "02"
subsystem: data-collection
tags: [fred, macro-data, config, data-pipeline, feat-01]
dependency_graph:
  requires: []
  provides: [src.data.collect_macro, FRED_API_KEY config constant, data/macro_data.csv contract]
  affects: [src/config.py, src/data/__init__.py, src/data/collect_macro.py]
tech_stack:
  added: [fredapi 0.5.2, pandas_datareader 0.10.0 (fallback)]
  patterns: [env-var config loading, business-day resample causal forward-fill, fredapi + pdr dual-path]
key_files:
  created:
    - src/data/__init__.py
    - src/data/collect_macro.py
  modified:
    - src/config.py
decisions:
  - "FRED_API_KEY loaded exclusively via os.getenv('FRED_API_KEY', '') — never hardcoded or logged (T-05-02-01 mitigation)"
  - "fredapi import inside _fetch_via_fredapi() not at module top — ensures fallback path works even if fredapi has issues"
  - "git add -f required for src/data/__init__.py and src/data/collect_macro.py — .gitignore has bare 'data/' glob that mistakenly matches src/data/ (intended for data artifacts only)"
metrics:
  duration: "5 minutes"
  completed: "2026-04-19"
  tasks_completed: 3
  tasks_total: 3
  files_created: 2
  files_modified: 1
---

# Phase 05 Plan 02: FRED Macro Data Collector Summary

**One-liner:** FRED macro collector with fredapi primary path and pandas_datareader fallback, writing T10Y2Y / BAMLH0A0HYM2 / NFCI to data/macro_data.csv with causal business-day forward-fill.

## What Was Built

Three files form the FRED data path required by Plan 03 (feature builder):

1. **`src/config.py`** — Added `FRED_API_KEY = os.getenv('FRED_API_KEY', '')` in a new `# --- External API keys ---` section, inserted after the `VVIX_TICKER` line. N_STATES=3 and FEATURE_SUBSET untouched.

2. **`src/data/__init__.py`** — New package marker with docstring explaining the FRED vs yfinance separation rationale. No imports or functions — pure package marker.

3. **`src/data/collect_macro.py`** — Full FRED collector (113 lines):
   - `FRED_SERIES` dict: `T10Y2Y → yield_curve_slope`, `BAMLH0A0HYM2 → HY_OAS`, `NFCI → NFCI`
   - `_fetch_via_fredapi()`: authenticated path via fredapi.Fred
   - `_fetch_via_pdr()`: fallback via pandas_datareader (rate-limited, no key needed)
   - `collect_macro_features()`: fetches, aligns via `.resample('B').last().ffill()`, validates >= 252 rows and expected columns
   - `collect()`: top-level entry, writes `data/macro_data.csv`
   - `__main__` guard for `python -m src.data.collect_macro` invocation

## FRED_SERIES Mapping Confirmed

| FRED Code | Canonical Column | Frequency | Source |
|-----------|-----------------|-----------|--------|
| T10Y2Y | yield_curve_slope | Daily | 10Y-2Y Treasury spread, from 1976 |
| BAMLH0A0HYM2 | HY_OAS | Daily | ICE BofA HY Option-Adjusted Spread, from 1996-12-31 |
| NFCI | NFCI | Weekly (Friday) | Chicago Fed NFCI, from 1971 |

## Fallback Behavior

When `FRED_API_KEY` is empty (default):
- `collect_macro_features()` logs `"[collect_macro] FRED_API_KEY empty -- falling back to pandas_datareader"`
- `_fetch_via_pdr()` uses `pandas_datareader.data.get_data_fred()` (public endpoint, rate-limited)
- Both paths produce identical output schema (same columns, same alignment)

NAPM excluded — removed from FRED in 2016 (05-RESEARCH.md Pitfall 5).

## Causal Guarantee

All series aligned with `.resample('B').last().ffill()`:
- Daily series (T10Y2Y, BAMLH0A0HYM2): gaps filled forward (no future leakage)
- Weekly NFCI: Friday reading propagates forward to next Thursday (causal, no backfill)

## Next-Plan Handoff

**Plan 03** (`build_features()` extension) reads `data/macro_data.csv` and merges the three FRED columns (`HY_OAS`, `NFCI`, `yield_curve_slope`) into the feature matrix. Contract:
- File path: `data/macro_data.csv`
- Index: `Date` (business-day DatetimeIndex)
- Columns: `['HY_OAS', 'NFCI', 'yield_curve_slope']` (forward-filled, no NaN in aligned rows)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] .gitignore `data/` glob blocked `src/data/` package**
- **Found during:** Task 2 commit
- **Issue:** `.gitignore` contains bare `data/` pattern which Git resolves to match `src/data/` as well as the root `data/` artifacts directory
- **Fix:** Used `git add -f` for both `src/data/__init__.py` and `src/data/collect_macro.py` to force-add source package files that should be tracked
- **Impact:** Minor — no code change needed, only commit procedure
- **Files modified:** none (commit procedure only)
- **Commit:** 5d70e0c, f842766

### Pre-existing Test Failures (Out of Scope)

The following test collection errors existed before this plan and are unrelated to our changes:
- `test_bot_integration.py`, `test_causality.py`, `test_train_refactor.py`: `ModuleNotFoundError: No module named 'train'` (old import path)
- `test_dashboard_hardening.py`, `test_signal_combination*.py`: similar module import issues
- 33 core tests pass; 5 skipped (missing data files in worktree)

## Threat Flags

No new network endpoints or auth paths introduced beyond what the plan's threat model already covers. FRED_API_KEY is loaded via `os.getenv` only — not logged, not hardcoded (T-05-02-01 mitigated).

## Self-Check

### Files Exist
- [x] `src/config.py` — modified (contains `FRED_API_KEY = os.getenv('FRED_API_KEY', '')`)
- [x] `src/data/__init__.py` — created
- [x] `src/data/collect_macro.py` — created (113 lines)

### Commits Exist
- [x] `973e952` — feat(05-02): add FRED_API_KEY env-var loader to src/config.py
- [x] `5d70e0c` — feat(05-02): create src/data/ package with docstring-only __init__.py
- [x] `f842766` — feat(05-02): implement src/data/collect_macro.py — FRED fetcher with fallback

## Self-Check: PASSED
