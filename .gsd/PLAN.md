# Regime-Detection — Forward Plan

**Created:** 2026-03-22
**Status:** Active
**Previous audit:** 7 data-leakage issues identified 2026-03-16, all RESOLVED as of 2026-03-20.

---

## Current State

The pipeline is **feature-complete**: collect → features → PCA → HDP-HMM → SV/GARCH → walk-forward → trust scorecard → dashboard. 28 tests pass. All causality guarantees in place.

**What needs work:** Tech debt and structural maintainability.

---

## Phase 1: Quick Cleanup (Low Risk, Low Effort)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 1.1 | Remove unused deps (`fredapi`, `matplotlib`) | `requirements.txt` | **DONE** |
| 1.2 | Fix stale feature count comment (19→17, 15→13) | `features.py` L55-56 | **DONE** |
| 1.3 | Remove vestigial FRED refs (`hy_spread`, `yield_slope`) | `train.py` (4 locations) | **DONE** |
| 1.4 | Delete legacy files no longer produced/consumed | `data/features_raw.csv`, `data/features_scaled.csv`, `models/scaler.pkl` | **DONE** |
| 1.5 | Pin dependency versions | `requirements.txt` | **DONE** |

---

## Phase 2: Structural Refactor — `train.py` Decomposition (Medium Risk, High Effort)

`train.py` is 3002 lines containing PCA, HMM fitting, SV/GARCH, walk-forward, VaR backtests, 7 dashboard tabs, and HTML generation. Split into focused modules:

| # | Task | New File | What Moves |
|---|------|----------|------------|
| 2.1 | Extract dashboard builders | `dashboard.py` | 7 `_build_*_tab()` functions + `_write_dashboard_html()` + `build_interactive_dashboard()` — **DONE** (1526 lines moved) |
| 2.2 | Extract validation logic | `validation.py` | `walk_forward()`, VaR backtest, OOS metrics — **DEFERRED** (circular import with core functions) |
| 2.3 | Extract PCA module | `pca.py` | `fit_rolling_pca()`, Procrustes alignment — **DEFERRED** (only 72 lines, low impact) |
| 2.4 | Slim `train.py` to orchestrator | `train.py` | Now 1452 lines (down from 3002). Further splits require `core.py` to avoid circular imports — revisit when needed |

**Constraint:** All 28 tests must pass after each extraction. `python run.py train` must produce identical output.

**Note:** Tasks 2.2-2.4 deferred because remaining functions (`walk_forward`, `expanding_standardize`, `filtered_labels`, `_fit_hmm`, PCA, HMM selection, SV/GARCH fitting) are tightly coupled. Extracting them requires a `core.py` intermediary to avoid circular imports. The dashboard extraction (2.1) delivered the biggest win — 1526 lines out. The remaining 1452-line `train.py` is manageable as-is.

---

## Phase 3: CLI Improvement (Low Risk, Low Effort)

| # | Task | File(s) |
|---|------|---------|
| 3.1 | Replace if/elif dispatch with `argparse` | `run.py` |
| 3.2 | Add `--help` and proper error messages | `run.py` |

---

## Phase 4: Future Enhancements (Not Started)

Potential next directions (not yet scoped):
- Multi-asset regime detection (beyond SPY-centric)
- Incremental update path (avoid full refit every run)
- GPU acceleration for HDP-HMM SVI
- Additional test coverage (features.py indicators, hdp_hmm.py internals)

---

## Execution Priority

1. **Phase 1** — Do first, minimal risk, cleans noise
2. **Phase 2** — High-value refactor, do when ready for focused work
3. **Phase 3** — Small polish, can do anytime
4. **Phase 4** — Future roadmap, scope when needed

---

*Plan updated: 2026-03-22*
