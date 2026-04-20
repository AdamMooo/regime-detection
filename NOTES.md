# Regime-Detection — Session Resume

## Status
Phase: v1.1 — Phase 5 complete (2026-04-19)
Milestone: Model Quality & Regime Reliability (Phases 4–7)
Branch: main

## Last Session Work
Phase 5 Plan 05 + pipeline retrain + dashboard fix (2026-04-19)

- Phase 5 complete: walk-forward selection → 15-feature FEATURE_SUBSET (all 3 sections at 100%)
- HY_OAS removed (ICE FRED restricted to post-2023 only)
- Pipeline retrained with all 15 features
- Dashboard shading fixed: Plotly 6 broke add_vrect before traces — moved all 4 shading calls after traces
- Data stale: market_data.csv last date 2026-04-13, cache returned 0 new rows (cache/file sync issue)

## Critical Model Quality Issues (Phase 6 priority)

**THE MODEL IS ECONOMICALLY BROKEN after Phase 5 feature expansion:**

1. **VIX 25+ labeled "Low-Vol"** — Apr 7 2026 (VIX=25.78) → Low-Vol at 97% confidence. Catastrophic mislabeling during the tariff volatility spike.

2. **In-sample VIX spread is collapsed** — Low-Vol=17.3, Med-Vol=17.8, High-Vol=21.0. Only 4 VIX points across 3 regimes. The HMM is not separating on vol level at all.

3. **OOS Med-Vol dominates** — makes no economic sense. OOS proliferates into 9 regime variants (Crisis-Vol-B, Elevated-Vol-B etc.) — naming logic fragmented.

4. **Max drawdown per regime is wildly off** — because labels don't correspond to vol states, per-regime risk profiles are meaningless.

5. **Root cause hypothesis:** 15-feature PCA now captures macro cycle signals (s_mac, s_fin) that override the vol signal. The model is technically fitting a latent space but economically mislabeling vol regimes. Phase 5 feature expansion likely made this worse.

## Next Action
**NEXT SESSION: Phase 6 — Fix model quality BEFORE architecture experiments**

Priority order:
1. **Collect fresh data first** — `python scripts/run.py collect` then `python scripts/run.py features` (cache returned 0 rows, may need full refresh)
2. **Diagnose PCA loading** — check what PC1/PC2 actually capture with 15-feature set. If PC1 is macro not vol, that's the bug.
3. **Consider vol-anchoring** — force VIX/vol features to dominate PCA or use VIX as direct HMM emission component
4. **Re-examine FEATURE_SUBSET** — Phase 5 walk-forward selected all 3 sections but the macro/financial features may be diluting the vol signal. Consider vol-only or vol+credit only.
5. **Fix OOS regime proliferation** — naming logic in walk-forward OOS produces too many variants
6. **GARCH scale warnings** — returns need ×10 rescaling (arch DataScaleWarning on every regime)
7. Plan Phase 6 with `/gsd-plan-phase` after diagnosis

## Known Issues (pre-existing, not blocking)
- test_model_card_validation: Windows subprocess path issue
- test_regime_count_selection: requires live data + K=4 logic
- test_dashboard_hardening, test_dashboard_refactor: zombie tests for deleted dashboard.py
- Feature work backlog: more feature engineering needed (Phase 6+)

## Architecture Constraints
- HDP-HMM via NumPyro (variational inference + NUTS)
- 15 curated features post-Phase-5 (s_vol + s_fin + s_mac, HY_OAS excluded)
- Rolling PCA with Procrustes alignment for label consistency
- Student-t emissions for fat-tailed returns
- K=3 regimes confirmed
- Downstream consumers: Algo-Trading-Bot, Portfolio-Manager
- Do NOT change public API (detect(), fit(), regime labels) without coordinating

## Key Files
- `scripts/analysis/walk_forward_feature_selection.py` — Phase 5 FEAT-02/03
- `scripts/analysis/apply_feature_selection.py` — Phase 5 config update script
- `src/core/evaluation.py` — forward return analysis + VaR backtesting
- `tests/test_regime_economic_validity.py` — DIAG-04 tests (24)
- `src/`: Main pipeline source (collect, features, train, evaluate)
- `scripts/`: CLI entry points
