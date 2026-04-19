---
phase: 05-feature-engineering-overhaul
plan: 01
subsystem: tests
tags: [tdd, wave-0, nyquist, feat-01, feat-02, feat-03, section-signals, walk-forward]
completed: "2026-04-19"
duration_minutes: 25

dependency_graph:
  requires: []
  provides:
    - "tests/test_section_signals.py — FEAT-01 section signal construction contract (4 RED stubs)"
    - "tests/test_walk_forward.py — FEAT-02 causal guarantee + FEAT-03 report contract (4 RED stubs)"
    - "tests/test_features.py — FEAT-01 FRED feature presence contract (2 RED stubs)"
    - "scripts/analysis/__init__.py — explicit Python package marker enabling module-level imports"
  affects:
    - "Plan 03 (build_section_signals implementation turns test_section_signals.py GREEN)"
    - "Plan 04 (walk_forward_feature_selection implementation turns test_walk_forward.py GREEN)"

tech_stack:
  added: []
  patterns:
    - "try/except import guard at module level — allows pytest --collect-only to list tests before target module exists"
    - "NYQUIST marker comment — documents expected RED state and which plan resolves it"
    - "tmp_path + monkeypatch DATA_DIR — prevents report tests from writing to repo data/ (T-05-01-01)"

key_files:
  created:
    - scripts/analysis/__init__.py
    - tests/test_section_signals.py
    - tests/test_walk_forward.py
    - tests/test_features.py
  modified: []

decisions:
  - "Used try/except import guard (not bare module-level import) so all 4 test functions collect under pytest --collect-only even before target implementations exist"
  - "test_no_lookahead patches src.features.features.build_section_signals_for_fold (not the walk-forward module directly) to record every fold call's slice length and last index — enforces FEAT-02 at the PCA refit point per RESEARCH.md Pitfall 4"
  - "test_report_written monkeypatches wffs.DATA_DIR to tmp_path — mitigates T-05-01-01 threat (no writes to repo data/ dir during tests)"
  - "K=3 in synthetic fixture regime_labels (values in {0,1,2}) — matches config.py N_STATES=3 per CLAUDE.md lock"

metrics:
  tasks_completed: 4
  tasks_total: 4
  files_created: 4
  files_modified: 0
  test_stubs_created: 10
  commits: 4
---

# Phase 05 Plan 01: Wave 0 Test Stubs Summary

**One-liner:** Wave 0 Nyquist test stubs anchoring FEAT-01/02/03 contracts via try/except import guards, enabling pytest collection before implementations exist.

## What Was Built

Four artifacts were created to satisfy the Wave 0 Requirements in 05-VALIDATION.md:

| Artifact | Purpose | Status |
|----------|---------|--------|
| `scripts/analysis/__init__.py` | Explicit Python package marker | Created — import succeeds |
| `tests/test_section_signals.py` | FEAT-01 section construction contract | 4 RED stubs |
| `tests/test_walk_forward.py` | FEAT-02 causal + FEAT-03 report contracts | 4 RED stubs |
| `tests/test_features.py` | FEAT-01 FRED feature presence contract | 2 RED stubs |

## Test Function Inventory (8 stubs + 2 in test_features.py = 10 total)

### tests/test_section_signals.py (4 stubs)

| Function | Contract | Fails Until |
|----------|----------|------------|
| `test_build_section_signals_returns_4_columns` | output columns == {s_vol, s_fin, s_mac, s_str} | Plan 03 |
| `test_build_section_signals_sign_anchored_to_vix` | corr(s_vol, VIX) > 0 | Plan 03 |
| `test_build_section_signals_causal_pca_window` | prior rows unchanged when trailing row mutated | Plan 03 |
| `test_build_section_signals_single_feature_section_passthrough` | single-feature section returns feature directly | Plan 03 |

### tests/test_walk_forward.py (4 stubs)

| Function | Contract | Fails Until |
|----------|----------|------------|
| `test_no_lookahead` | build_section_signals_for_fold called with len <= 3*252 rows per fold | Plan 03 + 04 |
| `test_mi_train_only` | mutual_info_classif receives only train-fold rows | Plan 04 |
| `test_report_written` | data/feature_importance_report.md written with required heading + table | Plan 04 |
| `test_stability_threshold_applied` | only s_vol selected when only s_vol passes 60% fold threshold | Plan 04 |

### tests/test_features.py (2 stubs)

| Function | Contract | Fails Until |
|----------|----------|------------|
| `test_curated_features_includes_fred_additions` | CURATED_FEATURES contains HY_OAS, NFCI, yield_curve_slope, GLD_trend | Plan 03 |
| `test_fred_features` | build_features() output contains the 4 FRED-derived columns | Plan 03 |

## Confirmation: Stubs Are RED (Expected)

All stubs fail at this wave — this is the Nyquist contract:

- `test_section_signals.py`: `ImportError: cannot import name 'build_section_signals'` — correct
- `test_walk_forward.py`: `ImportError: cannot import name 'walk_forward_feature_selection' from 'scripts.analysis'` — correct (scripts.analysis package now resolves; missing module is the expected error)
- `test_features.py::test_fred_features`: `AssertionError: build_features missing FRED features: {'yield_curve_slope', 'NFCI', 'HY_OAS', 'GLD_trend'}` — correct
- `test_features.py::test_curated_features_includes_fred_additions`: `AssertionError` — correct

## Nyquist Contract Link

These stubs satisfy the Wave 0 Requirements checklist in `05-VALIDATION.md §Per-Task Verification Map`. The "turn green" sequence is:

1. Plan 03 (build_section_signals + FRED features) → test_section_signals.py + test_features.py GREEN
2. Plan 03 (build_section_signals_for_fold) + Plan 04 (walk_forward_feature_selection) → test_walk_forward.py GREEN

## Deviations from Plan

**1. [Rule 2 - Missing Critical Functionality] try/except import guard instead of bare top-level import**

- **Found during:** Task 1 verification
- **Issue:** Plan specified `from src.features.features import build_section_signals, SECTION_MAP, SECTION_ANCHORS` as a bare module-level import. This caused `pytest --collect-only` to collect 0 tests (collection failed at import time), violating the acceptance criterion "collection succeeds even if runtime fails."
- **Fix:** Wrapped the import in `try/except ImportError` with a `_require_import()` helper called at the top of each test. Tests now collect (4 visible) AND fail at runtime with the correct ImportError.
- **Applied to:** test_section_signals.py and test_walk_forward.py
- **Commit:** 2d06af4, b743939

## Commits

| Hash | Message |
|------|---------|
| ccd4e04 | feat(05-01): add scripts/analysis/__init__.py package marker |
| 2d06af4 | test(05-01): add failing test stubs for FEAT-01 section signal construction |
| b743939 | test(05-01): add failing test stubs for FEAT-02/FEAT-03 walk-forward selection |
| 7439adb | test(05-01): add failing test stubs for FEAT-01 FRED feature presence |

## Threat Flags

No new threat surface introduced. All threats from plan's threat model were mitigated:
- T-05-01-01: test_report_written uses `tmp_path` + `monkeypatch` for DATA_DIR — no writes to repo `data/` dir
- T-05-01-02: All test data via `np.random.default_rng(42)` — no PII or credentials
- T-05-01-03: Synthetic fixtures capped at 2000 rows maximum

## Self-Check

- [x] scripts/analysis/__init__.py exists — FOUND
- [x] tests/test_section_signals.py exists with 4 test functions — FOUND
- [x] tests/test_walk_forward.py exists with 4 test functions — FOUND
- [x] tests/test_features.py exists with 2 target test functions — FOUND
- [x] All commits exist — ccd4e04, 2d06af4, b743939, 7439adb — FOUND

## Self-Check: PASSED
