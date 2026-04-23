# Regime-Detection — Session Resume

## Status
Phase: v1.1 — Phase 6 complete (2026-04-21)
Milestone: Model Quality & Regime Reliability (Phases 4–7)
Branch: main

## Last Session Work
Phase 6 fully executed (2026-04-21) — both plans complete.

**Plan 06-01: HDP-HMM vs StudentTHMM Comparison (MODEL-02)**
- Ran formal OOS comparison: 133 walk-forward folds, all SVI-converged
- Results: HDP +1.7pp accuracy (36.6% vs 34.9%), +19% dwell time
- Machine verdict: studenthmm_wins (0.3pp short of +2pp threshold)
- **Human override: HDP-HMM enabled as default** — better long-term headroom, fewer whipsaw transitions
- USE_HDP = True in config.py; StudentTHMM branch removed from train.py
- hdp_hmm.py retained; MODEL_CARD.md updated with decision record
- tests/_hdp_verdict.txt = "enabled"; all 4 test_hdp_decision tests green

**Plan 06-02: src/core/ Module Refactor (MODEL-03)**
- evaluation.py: 821 → 186 lines (evaluate + bootstrap helpers only)
- hmm_training.py: 606 → 458 lines (BIC/stability/labeling/SV/GARCH only)
- 3 new focused modules: pca_utils.py (181), var_backtesting.py (403), forward_returns.py (275)
- 10+ import sites updated to direct module paths — zero re-export indirection
- test_module_size gate live (excludes hdp_hmm.py as documented exception)
- Full test suite green (test_dashboard_refactor failure is pre-existing, unrelated)

**Phase 8 added to roadmap:** HDP-HMM Inference Optimization — parallelize fold loop (joblib), JAX XLA CPU flag, ELBO early stopping, optional NUTS path. Goal: cut ~4hr run to <90min.

## Next Action
**NEXT SESSION: Phase 7 — Daily Pipeline & Clean Outputs**

Goal: Single command runs full daily pipeline end-to-end in under 10 minutes, exactly 2 HTML outputs, cron-ready.  
**Critical addition:** Phase 7 must be designed with research extension points — see `.planning/COMPLETION-PLAN.md`

Run: `/gsd-plan-phase 7`

Key Phase 7 design constraint: train.py splits into pipeline stages (Plan 07-01), regime_results.csv schema extended with placeholder columns for Phases 9–12 (Plan 07-03), garch_params.json and oos_regime_labels.csv written as extension artifacts.

Research sequence after Phase 7:
- Phase 8: HDP inference optimization (4hr → <90min)
- Phase 9: Regime-weighted GARCH vol forecast (Research Path 1)
- Phase 10: Strategy backtester + tactical allocation (Research Path 2, CRITICAL gate)
- Phase 11: Transition early-warning model (conditional on Phase 10 result)

Full research rationale: `.planning/RESEARCH-STRATEGY.md`
Full completion plan: `.planning/COMPLETION-PLAN.md`

## Known Issues (pre-existing, not blocking)
- test_dashboard_refactor.py::test_dashboard_loads_regime_results — ModuleNotFoundError: No module named 'dashboard' (zombie test for deleted dashboard.py)
- test_model_card_validation: Windows subprocess path issue
- Unicode render error on Windows terminal (cp1252)

## Architecture Constraints
- HDP-HMM via NumPyro (SVI) — USE_HDP=True, StudentTHMM removed from train.py
- inference.py still contains StudentTHMM (full removal deferred to Plan 06-02 scope — do in Phase 8 or standalone cleanup)
- Rolling PCA with Procrustes alignment for label consistency
- Student-t emissions for fat-tailed returns
- K=3 regimes confirmed (locked)
- Downstream consumers: Algo-Trading-Bot, Portfolio-Manager

## Key Files
- `src/config.py` — USE_HDP=True, FEATURE_SUBSET, VIX_BYPASS=True
- `src/core/hdp_hmm.py` — primary model (844 lines, retained)
- `src/core/evaluation.py` — regime evaluate + bootstrap helpers only (186 lines)
- `src/core/var_backtesting.py` — VaR/GARCH backtest functions (403 lines, new)
- `src/core/forward_returns.py` — forward return analysis (275 lines, new)
- `src/core/pca_utils.py` — fit_rolling_pca + LinearizedSV (181 lines, new)
- `docs/MODEL_CARD.md` — includes Model Architecture Decision (Phase 6) section
- `data/hdp_comparison_results.json` — Phase 6 comparison numbers
- `tests/_hdp_verdict.txt` — "enabled"
