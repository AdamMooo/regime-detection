# Regime-Detection — Session Resume

## Status
Phase: v1.1 — Phase 7 complete (2026-04-27), v1.1 milestone complete
Milestone: Model Quality & Regime Reliability (Phases 4–7) — ALL PHASES DONE
Branch: main

## v1.1 Summary (all phases complete)

| Phase | Status | Completed |
|-------|--------|-----------|
| 4. Empirical Diagnostics | ✅ Complete | 2026-04-20 |
| 5. Feature Engineering Overhaul | ✅ Complete | 2026-04-19 |
| 6. Model Architecture Experiments | ✅ Complete | 2026-04-21 |
| 7. Daily Pipeline & Clean Outputs | ✅ Complete | 2026-04-27 |

## Phase 7 UAT — Critical Failures Discovered (2026-04-27)

Three model quality failures found during first live pipeline run. Phase 9 (Regime Calibration) created to fix:

1. **High-Vol dominance** — 61% of days assigned High-Vol (should be ~15-25%). Threshold/prior miscalibration.
2. **Label variant explosion** — OOS walk-forward produces 8 label variants instead of 3. Procrustes/Hungarian matching broken across folds.
3. **GARCH VaR scaling bug** — mean_vol=700%+, VaR=-546%. Returns likely in wrong units (basis points vs decimal) somewhere in GARCH path.

## Next Action
**CURRENT: Phase 9 — Regime Calibration**

Fix the 3 critical UAT failures in order:
1. GARCH VaR scaling bug (isolated, fastest fix)
2. Label variant explosion (walk-forward fold alignment)
3. High-Vol dominance (prior/threshold calibration)

Files: `src/core/var_backtesting.py`, `signals.py`, `src/core/hmm_training.py`, `src/core/orchestrator.py`, `src/config.py`

## Key Feature State (Post Phase 5+6)

**14 active features** in `FEATURE_SUBSET` (config.py):
- s_vol (8): VIX, VRP, rv_ratio_10_63, vix_ts_slope, SPY_volvol20, SPY_rv10_lag5, SPY_rv10_lag10, SPY_skew20
- s_fin (5): credit_stress, SPY_TLT_corr63, NFCI, eigen_conc, SPY_dd63
- s_mac (1): yield_curve_slope (GLD_trend removed in Phase 6 — dominated PC1, caused mislabeling)

**VIX_BYPASS=True** (appends scaled VIX directly to PCA dims to force regime separation on implied vol level)

## Architecture Constraints
- HDP-HMM via NumPyro (SVI) — USE_HDP=True, StudentTHMM removed from train.py
- Rolling PCA with Procrustes alignment for label consistency (currently broken — Phase 9 to fix)
- Student-t emissions for fat-tailed returns
- K=3 regimes (locked)
- Downstream consumers: Algo-Trading-Bot, Portfolio-Manager

## Known Issues (pre-existing, not blocking)
- test_dashboard_refactor.py::test_dashboard_loads_regime_results — zombie test for deleted dashboard.py
- test_model_card_validation.py — Windows subprocess path issue
- test_regime_count_selection.py — requires live data + K=4 logic (K=3 now)

## Key Files
- `src/config.py` — USE_HDP=True, FEATURE_SUBSET (14 features), VIX_BYPASS=True
- `src/core/hdp_hmm.py` — primary model (844 lines)
- `src/core/var_backtesting.py` — VaR/GARCH backtest functions (bug here)
- `src/core/hmm_training.py` — label_regimes(), check_stability(), fit_rolling_pca()
- `src/core/orchestrator.py` — walk_forward() (label alignment bug here)
- `src/core/pca_utils.py` — fit_rolling_pca + LinearizedSV
- `data/feature_importance_report.md` — Phase 5 walk-forward selection report
