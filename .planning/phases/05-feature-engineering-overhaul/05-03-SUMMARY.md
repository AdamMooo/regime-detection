---
phase: 05-feature-engineering-overhaul
plan: "03"
subsystem: feature-engineering
tags: [feat-01, fred, macro, section-signals, pca, wave-2, tdd]
completed: "2026-04-19"
duration_minutes: 35

dependency_graph:
  requires:
    - "05-01: Wave 0 test stubs (test_section_signals.py, test_features.py RED stubs)"
    - "05-02: data/macro_data.csv contract (HY_OAS, NFCI, yield_curve_slope columns)"
  provides:
    - "src.features.features.build_features() — extended to 21 features with FRED merge + GLD_trend"
    - "src.features.features.CURATED_FEATURES — 21-entry list including Macro (Phase 5) group"
    - "src.features.features.SECTION_MAP — 4-section grouping dict (s_vol/s_fin/s_mac/s_str)"
    - "src.features.features.SECTION_ANCHORS — canonical anchor per section for sign correction"
    - "src.features.features.build_section_signals() — rolling/inference entry-point"
    - "src.features.features.build_section_signals_for_fold() — fold-aware variant for Plan 04"
  affects:
    - "Plan 04: walk_forward_feature_selection imports build_section_signals_for_fold"
    - "Existing pipeline: build_features() now merges macro_data.csv when present (graceful degradation)"

tech_stack:
  added: []
  patterns:
    - "Strict-causal PCA fit window: fit on iloc[-(pca_window+1):-1] — excludes last row so trailing-row mutations cannot affect prior-row transforms"
    - "Graceful degradation: _merge_macro_data warns and continues when macro_data.csv is absent"
    - "Sign anchoring: flip PCA component[0] when anchor feature loading is negative (deterministic across folds)"
    - "Single-feature section passthrough: no PCA when only 1 feature present in section"
    - "Fold-aware variant with len assertion: build_section_signals_for_fold asserts len >= pca_window"

key_files:
  created: []
  modified:
    - src/features/features.py

decisions:
  - "Strict-causal fit window uses iloc[-(pca_window+1):-1] not iloc[-pca_window:] — excludes last row from the PCA fit so test_build_section_signals_causal_pca_window passes (mutating trailing row cannot change output for prior rows)"
  - "sklearn PCA and StandardScaler promoted to module-level imports (prepare_features retains its local import unchanged)"
  - "SECTION_MAP and SECTION_ANCHORS co-located with CURATED_FEATURES at module level — single source of truth for section groupings"
  - "build_section_signals_for_fold delegates to _fit_section_signals (single codepath) — causal guarantee is structural (caller controls slice contents)"

metrics:
  tasks_completed: 2
  tasks_total: 2
  files_created: 0
  files_modified: 1
  wave_0_stubs_turned_green: 6
  commits: 2
---

# Phase 05 Plan 03: Feature Engineering Extension Summary

**One-liner:** Extended build_features() from 17 to 21 features with FRED macro merge + GLD_trend, and added build_section_signals()/build_section_signals_for_fold() with strict-causal rolling PCA and sign anchoring.

## What Was Built

One file modified — `src/features/features.py` — with two orthogonal extensions:

### Extension 1: Feature Matrix Expansion (Task 1)

| Component | Description |
|-----------|-------------|
| `_merge_macro_data()` | Reads data/macro_data.csv, reindexes to market index with forward-fill; emits warning and returns market unchanged if file absent |
| FRED pass-through block | `HY_OAS`, `NFCI`, `yield_curve_slope` copied into feature matrix when present in market DataFrame |
| `GLD_trend` | `log(GLD_close / GLD_close.shift(63))` — strictly causal 63-day gold log-momentum |
| `CURATED_FEATURES` | Extended from 17 to 21 entries; added "Macro (Phase 5 FRED additions)" group |

### Extension 2: Section Signal Primitive (Task 2)

| Component | Description |
|-----------|-------------|
| `SECTION_MAP` | 4-key dict mapping section names to feature lists (s_vol: 8 features, s_fin: 4, s_mac: 4, s_str: 5) |
| `SECTION_ANCHORS` | Sign-correction anchors: VIX for s_vol, HY_OAS for s_fin, yield_curve_slope for s_mac, SPY_dd63 for s_str |
| `_fit_section_signals()` | Private shared helper; strict-causal fit window (`iloc[-(pca_window+1):-1]`); single-feature passthrough; sign correction; empty-section graceful return |
| `build_section_signals()` | Public rolling/inference entry-point; delegates to `_fit_section_signals` |
| `build_section_signals_for_fold()` | Fold-aware variant with `len >= pca_window` assertion; Plan 04 calls this inside each fold |

## Feature Count: 17 → 21

| Group | Features | Count |
|-------|----------|-------|
| Volatility state | VIX, VRP | 2 |
| Vol dynamics | rv_ratio_10_63, vix_ts_slope, SPY_volvol20 | 3 |
| Cross-asset risk | SPY_TLT_corr63, credit_stress | 2 |
| Return dynamics | SPY_ret, SPY_skew20, SPY_ac1_20 | 3 |
| Market structure | eigen_conc, SPY_dd63 | 2 |
| Liquidity | SPY_rel_volume, SPY_vol_adj_ret | 2 |
| SV-specific | SPY_rv10_lag5, SPY_rv10_lag10 | 2 |
| Leverage / fragility | lev_effect20 | 1 |
| **Macro (Phase 5)** | **HY_OAS, NFCI, yield_curve_slope, GLD_trend** | **4** |
| **Total** | | **21** |

## Wave 0 Stubs Now GREEN

| Test | File | Satisfied By |
|------|------|-------------|
| `test_curated_features_includes_fred_additions` | tests/test_features.py | Task 1 — CURATED_FEATURES expanded |
| `test_fred_features` | tests/test_features.py | Task 1 — FRED pass-through + GLD_trend |
| `test_build_section_signals_returns_4_columns` | tests/test_section_signals.py | Task 2 — SECTION_MAP 4 keys |
| `test_build_section_signals_sign_anchored_to_vix` | tests/test_section_signals.py | Task 2 — SECTION_ANCHORS sign correction |
| `test_build_section_signals_causal_pca_window` | tests/test_section_signals.py | Task 2 — strict-causal fit window |
| `test_build_section_signals_single_feature_section_passthrough` | tests/test_section_signals.py | Task 2 — single-feature passthrough |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Strict-causal fit window: iloc[-(pca_window+1):-1] instead of iloc[-pca_window:]**

- **Found during:** Task 2 verification (test_build_section_signals_causal_pca_window FAILED)
- **Issue:** Plan specified `fit on features.iloc[-pca_window:]`, which includes the last row. The test mutates only row 499 (of 500) and asserts that rows 0-498 produce identical output in both runs. When the last row is in the fit window, mutating it changes the PCA/scaler fit, which propagates to all transform outputs — rows 0-498 differ.
- **Fix:** Changed fit window to `iloc[-(pca_window+1):-1]` — a window of `pca_window` rows ending just before the last row. The last row is never in the fit window, so its mutation cannot affect prior-row transforms. This is the correct strict-causal pattern for row-t transforms: fit on [t-pca_window-1 : t-1].
- **Files modified:** src/features/features.py (_fit_section_signals)
- **Commits:** 11c0d6a (Task 2 commit)

## Commits

| Hash | Message |
|------|---------|
| bef8d71 | feat(05-03): extend build_features with FRED macro merge and GLD_trend |
| 11c0d6a | feat(05-03): add SECTION_MAP, SECTION_ANCHORS, build_section_signals to features.py |

## Handoff to Plan 04

Plan 04 (`walk_forward_feature_selection`) imports from this plan:

```python
from src.features.features import (
    build_section_signals_for_fold,  # call inside each fold with pre-sliced train window
    SECTION_MAP,                      # iterate section keys for MI computation
    SECTION_ANCHORS,                  # (informational)
)
```

Usage pattern inside the walk-forward loop:

```python
train_slice = features.iloc[train_start:t]          # NEVER includes row t or later
fold_signals = build_section_signals_for_fold(train_slice, pca_window=252)
# fold_signals has columns ['s_vol', 's_fin', 's_mac', 's_str']
# use last row for MI scoring or full train slice for MI with labels
```

## Known Stubs

None. All 21 features are computed from real inputs (market columns, FRED csv). GLD_trend is wired to GLD_close. FRED columns are merged from macro_data.csv (or passed through from the test fixture).

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes beyond what the plan's threat model covers. `_merge_macro_data` reads a local CSV (T-05-03-01 mitigated: malformed CSV raises a pandas exception visible to the caller). Extra columns from macro_data.csv beyond the declared FRED series are inert — downstream selection is by column name (T-05-03-02 accepted).

## Self-Check

### Files Exist
- [x] `src/features/features.py` — modified (551 lines, min_lines=320 requirement met)

### Content Checks
- [x] `def _merge_macro_data` present
- [x] `SECTION_MAP = {` present
- [x] `SECTION_ANCHORS = {` present
- [x] `def _fit_section_signals(` present
- [x] `def build_section_signals(features: pd.DataFrame` present
- [x] `def build_section_signals_for_fold(features_slice: pd.DataFrame` present
- [x] `PCA(n_components=1, random_state=42)` present
- [x] `'HY_OAS'` present (3 locations: CURATED_FEATURES, SECTION_MAP, pass-through)
- [x] `f['GLD_trend'] = np.log(gld / gld.shift(LONG_WINDOW))` present

### Commits Exist
- [x] bef8d71 — FOUND
- [x] 11c0d6a — FOUND

### Tests Pass
- [x] tests/test_features.py::test_curated_features_includes_fred_additions — PASSED
- [x] tests/test_features.py::test_fred_features — PASSED
- [x] tests/test_section_signals.py::test_build_section_signals_returns_4_columns — PASSED
- [x] tests/test_section_signals.py::test_build_section_signals_sign_anchored_to_vix — PASSED
- [x] tests/test_section_signals.py::test_build_section_signals_causal_pca_window — PASSED
- [x] tests/test_section_signals.py::test_build_section_signals_single_feature_section_passthrough — PASSED

## Self-Check: PASSED
