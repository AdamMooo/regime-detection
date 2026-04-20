---
phase: 05-feature-engineering-overhaul
plan: 05
status: complete
completed: 2026-04-19
---

# Plan 05 Summary — Apply Feature Selection + Human Checkpoint

## Final FEATURE_SUBSET (15 features, 3 sections)

All 3 sections selected at 100% fold stability across 155 folds (3-year rolling window, 21-day step, 2010–2026).

```python
FEATURE_SUBSET = [
    # s_mac (2): yield_curve_slope, GLD_trend
    'yield_curve_slope', 'GLD_trend',
    # s_fin (5): credit_stress, SPY_TLT_corr63, NFCI, eigen_conc, SPY_dd63
    'credit_stress', 'SPY_TLT_corr63', 'NFCI', 'eigen_conc', 'SPY_dd63',
    # s_vol (8): VIX, VRP, rv_ratio_10_63, vix_ts_slope, SPY_volvol20, SPY_rv10_lag5, SPY_rv10_lag10, SPY_skew20
    'VIX', 'VRP', 'rv_ratio_10_63', 'vix_ts_slope', 'SPY_volvol20',
    'SPY_rv10_lag5', 'SPY_rv10_lag10', 'SPY_skew20',
]
```

Previous (Phase 2.5): 6 features. Phase 5: 15 features. Old block preserved as `# Phase 5 replaced:` comment in config.py.

## Report Highlights

- **n_folds:** 155
- **Selected sections:** s_mac (100%), s_fin (100%), s_vol (100%)
- **Stability threshold:** 60% — all sections cleared comfortably
- **Report:** `data/feature_importance_report.md`
- **Machine-readable result:** `data/walk_forward_selection_result.json`

## Key Operational Note: HY_OAS Removed

ICE Data Services restricted `BAMLH0A0HYM2` on FRED to post-April-2023 data. Including HY_OAS truncated the feature matrix from ~4000 rows to 749 via `build_features` dropna, making the 756-row minimum for a 3-year fold unreachable (0 folds).

**Resolution:** HY_OAS removed from:
- `SECTION_MAP['s_fin']` (5 features remain)
- `build_features` output (no longer written to feature matrix)
- `SECTION_ANCHORS['s_fin']` → changed to `NFCI`
- Tests updated: `test_features.py`, `test_section_signals.py`

This is a permanent data constraint. Re-enable when a full-history HY OAS source is available.

## Test Suite Status

- **171 passing** (core suite, excluding known-failing zombie files)
- **Known-failing (pre-existing, not introduced here):**
  - `test_model_card_validation.py` — Windows subprocess path issue
  - `test_regime_count_selection.py` — requires live data + K=4 logic (K=3 now)
  - `test_dashboard_hardening.py`, `test_dashboard_refactor.py` — zombie tests for deleted dashboard.py

## Public API

Unchanged: `detect()`, `fit()`, K=3 regime labels. Downstream consumers (Algo-Trading-Bot, Portfolio-Manager) are unaffected — Phase 5 only changes INPUT features, not the regime output schema.

## Handoff to Phase 6

Phase 6 (Model Architecture Experiments) now has a clean, walk-forward-validated 15-feature set to test K-selection and USE_HDP against. The sectioned funnel architecture (s_vol/s_fin/s_mac → section signals → HMM) is the new standard input path.
