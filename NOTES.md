# Regime-Detection — Session Resume

## Status
Phase: v1.1 — Phase 6 diagnosis complete (2026-04-19)
Milestone: Model Quality & Regime Reliability (Phases 4–7)
Branch: main

## Last Session Work
Phase 6 model quality fix (2026-04-19)

**Root cause diagnosed and fixed:**

1. **GLD_trend** was the #1 PC1 loading (0.661) but PC1 barely separated regimes (F=29). GLD can rise as safe-haven while VIX spikes (tariff shock), causing VIX=25+ to map to wrong regime cluster. → **Removed from FEATURE_SUBSET**.

2. **VIX_BYPASS = True** — appends scaled VIX directly to PCA dims as 6th HMM feature (now PC5). This is now the dominant separator (F=2858 vs next-best F=222). Forces HMM to cluster on implied vol level.

**Before/After validation:**
- VIX spread (max−min regime mean): 4 pts → **16 pts**
- Apr 7 2026 (VIX=25.78): Low-Vol → **High-Vol** ✓
- High-Vol VIX mean: 19.8 → **30.1**
- Low-Vol VIX mean: 17.0 → **14.3**
- Ann. vol spread: 13.6/17.7/21.7% → **9.0/14.7/27.6%**
- GARCH-VaR Christoffersen: REJECT → **PASS**

## Next Action
**NEXT SESSION: Plan and execute Phase 6 formally**

Phase 6 work done so far (unplanned diagnostic fix):
- Config changes: GLD_trend removed, VIX_BYPASS=True
- Retrained pipeline, validated regime separation
- Committed as Phase 6 diagnostic fix

Remaining Phase 6 work to plan:
1. Fix OOS regime proliferation (9+ name variants in walk-forward OOS)
2. Fix GARCH DataScaleWarning (returns need ×10 rescaling)
3. Run full economic validity test suite and check pass/fail
4. Consider whether yield_curve_slope should also be dropped (0.015 PC1 loading, near-zero signal)
5. Update downstream consumers if regime label schema changed (it hasn't — still 3 regimes)
6. Plan Phase 7 (dashboard refresh / consumer sync)

Run: `/gsd-plan-phase` to plan Phase 6 formally before continuing

## Known Issues (pre-existing, not blocking)
- test_model_card_validation: Windows subprocess path issue
- test_regime_count_selection: requires live data + K=4 logic
- test_dashboard_hardening, test_dashboard_refactor: zombie tests for deleted dashboard.py
- Unicode render error on Windows terminal for regime awareness printout (cp1252)

## Architecture Constraints
- HDP-HMM via NumPyro (variational inference + NUTS) — currently using classic StudentT HMM
- 14 curated features post-Phase-6 (GLD_trend removed)
- VIX_BYPASS = True (raw VIX appended as 6th HMM dim)
- Rolling PCA with Procrustes alignment for label consistency
- Student-t emissions for fat-tailed returns
- K=3 regimes confirmed
- Downstream consumers: Algo-Trading-Bot, Portfolio-Manager

## Key Files
- `src/config.py` — FEATURE_SUBSET (14 features), VIX_BYPASS=True
- `scripts/analysis/walk_forward_feature_selection.py` — Phase 5 FEAT-02/03
- `src/core/evaluation.py` — forward return analysis + VaR backtesting
- `tests/test_regime_economic_validity.py` — DIAG-04 tests (24)
- `src/`: Main pipeline source (collect, features, train, evaluate)
- `scripts/`: CLI entry points
