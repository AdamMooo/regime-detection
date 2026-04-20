# Regime-Detection — Session Resume

## Status
Phase: v1.1 — Phase 4 complete (2026-04-18)
Milestone: Model Quality & Regime Reliability (Phases 4–7)
Branch: main

## Last Session Work
Phase 5 Plan 05 complete (2026-04-19)

- Phase 4 code review fixes: all 5 warnings resolved (458a47a docstring fix)
- Phase 5 test suite audit: 59 failures → 190 passing, 36 remaining
  - Fixed: stale module paths (train→src.core.inference, signal_combination→scripts.analysis, etc.)
  - Fixed: walk_forward n_jobs=-1 → n_jobs=1 (Windows joblib _posixsubprocess)
  - Skipped: test_dashboard_hardening.py (functions removed in Phase 3, needs rewrite)
  - Remaining 36: test_model_card_validation (Windows subprocess path issue) + test_regime_count_selection (live data dependency)
- Phase 5 plan state: Plans 01–04 DONE, Plan 05 NOT YET EXECUTED

## Next Action
**NEXT SESSION:** Begin Phase 6 — Model Architecture Experiments
- MODEL-01: K regime count validation (K=3 confirmed, test formally)
- MODEL-02: HDP-HMM vs StudentTHMM evaluation (USE_HDP decision)
- MODEL-03: Refactor train.py (1452 lines → modular)
- Start with `/gsd-plan-phase` for Phase 6

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
