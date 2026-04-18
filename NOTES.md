# Regime-Detection — Session Resume

## Status
Phase: v1.1 — Phase 4 complete (2026-04-18)
Milestone: Model Quality & Regime Reliability (Phases 4–7)
Branch: main

## Last Session Work
Phase 4: Empirical Diagnostics — COMPLETE (4/4 must-haves verified)

- Extended `scripts/analysis/analyze_regime_characterization.py`:
  - DIAG-01: vol boxplot, dwell histogram, transition heatmap saved to `figures/`
  - DIAG-02: `compute_persistence_baseline()` — OOS accuracy vs persist-yesterday (2021–2026 split)
  - DIAG-03: `analyze_failure_modes()` — short spells, flip-flop patterns, crisis alignment
  - `write_diagnostics_report()` → `reports/diagnostics_report.md` (run with live data)
- Extended `src/core/evaluation.py`:
  - DIAG-04: `compute_forward_return_analysis()` — Kruskal-Wallis p-values for SPY/EEM/TLT/HYG at 1d/5d/21d
- Added `tests/test_regime_economic_validity.py` — 24 tests, all passing

## Code Review Findings (5 warnings, 0 critical — 04-REVIEW.md)
- WR-01: `compute_persistence_baseline` — model_preds duplicates baseline_preds (dead var bug)
- WR-03: `compare_var_methods` — Christoffersen p-value hardcoded to 0.547 (stale)
- WR-02, WR-04, WR-05: minor correctness issues in evaluation.py

## Next Action
Option A (recommended): `/gsd-code-review-fix 4` — fix 5 warnings first
Option B: `/gsd-discuss-phase 5` — start Phase 5: Feature Engineering Overhaul

## Phase Backlog (v1.1)
- Phase 5: Feature Engineering Overhaul (FEAT-01, FEAT-02, FEAT-03)
- Phase 6: Model Architecture Experiments (MODEL-01, MODEL-02, MODEL-03)
- Phase 7: Daily Pipeline & Clean Outputs (PIPE-01, PIPE-02, PIPE-03)

## Architecture Constraints
- HDP-HMM via NumPyro (variational inference + NUTS)
- 13 curated market features from Yahoo Finance + FRED
- Rolling PCA with Procrustes alignment for label consistency
- Student-t emissions for fat-tailed returns
- K=4 regimes (locked after Phase 2.5 BIC experiment)
- Downstream consumers: Algo-Trading-Bot, Portfolio-Manager
- Do NOT change public API (detect(), fit(), regime labels) without coordinating

## Key Files
- `scripts/analysis/analyze_regime_characterization.py` — Phase 4 diagnostics
- `src/core/evaluation.py` — forward return analysis + VaR backtesting
- `tests/test_regime_economic_validity.py` — DIAG-04 tests (24)
- `.planning/phases/04-empirical-diagnostics/04-REVIEW.md` — code review findings
- `src/`: Main pipeline source (collect, features, train, evaluate)
- `scripts/`: CLI entry points
