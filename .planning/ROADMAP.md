# Roadmap: Regime-Detection

## Milestones

- ✅ **v1.0 Production Ready** — Phases 1–3 (shipped 2026-04-16)
- 🚧 **v1.1 Model Quality & Regime Reliability** — Phases 4–7 (active)

## Phases

<details>
<summary>✅ v1.0 Production Ready (Phases 1–3) — SHIPPED 2026-04-16</summary>

- [x] Phase 1: Fix Critical Blockers (4/4 plans) — JAX pinning, bot mapping, causality tests, integration test
- [x] Phase 2: Incremental Data Updates (1/1 plan) — delta-only fetch, <5 min on new data
- [x] Phase 2.5: Model Diagnostics & Robustness (5/5 plans) — OOS fragmentation, feature bias, K=4, GARCH VaR, model card
- [x] Phase 3: Code Refactoring + Polish (4/4 plans) — train.py split, dashboard hardening, docs, signal combination framework

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Model Quality & Regime Reliability (Active)

> Goal: Diagnose regime detection failures, overhaul feature engineering, experiment with model
> architecture, and wire up a clean daily pipeline. Model quality is the only priority —
> no UI work until regimes are economically valid.

- [ ] **Phase 4: Empirical Diagnostics** - Measure regime quality before any changes
- [ ] **Phase 5: Feature Engineering Overhaul** - Expand and properly validate feature set
- [ ] **Phase 6: Model Architecture Experiments** - K selection, HDP-HMM decision, train.py refactor
- [x] **Phase 7: Daily Pipeline & Clean Outputs** - Single entry point, 2 HTML outputs, cron-ready

## Phase Details

### Phase 4: Empirical Diagnostics
**Goal**: Regime quality is measured, failure modes are documented, and economic validity is established — so all subsequent work is grounded in evidence
**Depends on**: Nothing (first phase of v1.1; v1.0 shipped)
**Requirements**: DIAG-01, DIAG-02, DIAG-03, DIAG-04
**Success Criteria** (what must be TRUE):
  1. A diagnostics report shows vol ordering across regimes, dwell time distributions, and a transition matrix heatmap — failure modes visible at a glance
  2. OOS regime accuracy is compared to a naive persistence baseline — it is clear whether the model adds signal
  3. A documented failure mode analysis identifies which regimes are most often misclassified and under which market conditions
  4. Regime-conditional forward return analysis (1d/5d/21d) for SPY/EEM/TLT/HYG runs in evaluation.py and a Kruskal-Wallis test confirms or denies statistical separation across regimes
**Plans**: 2 plans
Plans:
- [x] 04-01-PLAN.md — Diagnostic figures, persistence baseline, failure mode analysis, diagnostics_report.md (DIAG-01, DIAG-02, DIAG-03)
- [x] 04-02-PLAN.md — compute_regime_forward_returns() in evaluation.py + test_regime_economic_validity.py (DIAG-04)

### Phase 5: Feature Engineering Overhaul
**Goal**: Sectioned funnel feature architecture — expanded 21-feature candidate set grouped into 4 thematic sections (Vol / FinConditions / Macro / Market Structure), reduced to per-section PC1 signals, selected via walk-forward MI with >=60% fold stability; importance documented in data/feature_importance_report.md
**Depends on**: Phase 4
**Requirements**: FEAT-01, FEAT-02, FEAT-03
**Success Criteria** (what must be TRUE):
  1. Feature candidate set contains 12+ candidates, each with a written economic rationale (21 features including 3 FRED series + GLD_trend)
  2. Feature selection runs walk-forward: each fold selects features on training data only and tests OOS — no held-out split contamination
  3. A feature importance document (OOS-measured) shows which sections drive regime separation
**Plans**: 5 plans
Plans:
- [x] 05-01-PLAN.md — Wave 0 test stubs (test_section_signals, test_walk_forward, test_features::test_fred_features) (FEAT-01, FEAT-02, FEAT-03)
- [x] 05-02-PLAN.md — FRED_API_KEY config + src/data/collect_macro.py with fredapi / pandas_datareader fallback (FEAT-01)
- [ ] 05-03-PLAN.md — Extend build_features with FRED + GLD_trend; add build_section_signals + SECTION_MAP + SECTION_ANCHORS (FEAT-01)
- [x] 05-04-PLAN.md — scripts/analysis/walk_forward_feature_selection.py: causal MI walk-forward + FEAT-03 report writer (FEAT-02, FEAT-03)
- [ ] 05-05-PLAN.md — apply_feature_selection.py idempotent config update + human verification checkpoint (FEAT-02, FEAT-03)

### Phase 6: Model Architecture Experiments
**Goal**: The USE_HDP decision is locked with documentation, and train.py is refactored so no module exceeds 500 lines
**Depends on**: Phase 5
**Requirements**: MODEL-02, MODEL-03
**Success Criteria** (what must be TRUE):
  1. K=3 is locked (confirmed 2026-04-18 — academically correct, empirically K=4 regimes 0&1 overlapped). K-selection experiment dropped.
  2. A documented decision on USE_HDP exists: either NumPyro HDP-HMM is re-enabled with evidence it outperforms StudentTHMM, or the dead code is formally deprecated and removed
  3. No single module in the training pipeline exceeds 500 lines; training, evaluation, and dashboard building are separate files
**Plans**: 2 plans
Plans:
- [x] 06-01-PLAN.md — HDP-HMM vs StudentTHMM comparison, MODEL_CARD decision section, verdict applied (MODEL-02)
- [x] 06-02-PLAN.md — Split evaluation.py/hmm_training.py by concern (pca_utils, var_backtesting, forward_returns), update all imports, test_module_size gate (MODEL-03)

### Phase 7: Daily Pipeline & Clean Outputs
**Goal**: A single command runs the full daily pipeline end-to-end in under 10 minutes, exactly 2 HTML outputs exist, and regime results are written in a format suitable for nightly cron
**Depends on**: Phase 6
**Requirements**: PIPE-01, PIPE-02, PIPE-03
**Success Criteria** (what must be TRUE):
  1. `python scripts/run.py` executes collect → features → train → signals in under 10 minutes on new data
  2. Exactly 2 HTML files exist after a run: figures/dashboard.html and figures/feature_analysis.html — no others are created or left over
  3. regime_results.csv is written on every run containing today's regime, probabilities, and GARCH VaR — verified by running the script twice and checking the file updates
**Plans:** 3 plans
Plans:
- [x] 07-01-PLAN.md — Pipeline Modularization + Timing Gate (src/pipeline/ package, 8 stages, Wave 0 test stubs, walk_forward gate) (PIPE-01)
- [x] 07-02-PLAN.md — Clean Output Enforcement + Cron Readiness (figures/ cleanup, rotating log, cron_run.sh, health_check.py) (PIPE-02)
- [x] 07-03-PLAN.md — regime_results.csv Schema Hardening (enrich_results in signals.py, 3 computed + 3 placeholder columns) (PIPE-03)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Fix Critical Blockers | v1.0 | 4/4 | Complete | 2026-04-13 |
| 2. Incremental Data Updates | v1.0 | 1/1 | Complete | 2026-04-13 |
| 2.5 Model Diagnostics & Robustness | v1.0 | 5/5 | Complete | 2026-04-14 |
| 3. Code Refactoring + Polish | v1.0 | 4/4 | Complete | 2026-04-15 |
| 4. Empirical Diagnostics | v1.1 | 2/2 | Complete | 2026-04-20 |
| 5. Feature Engineering Overhaul | v1.1 | 5/5 | Complete | 2026-04-19 |
| 6. Model Architecture Experiments | v1.1 | 2/2 | Complete | 2026-04-21 |
| 7. Daily Pipeline & Clean Outputs | v1.1 | 3/3 | Complete | 2026-04-27 |

### Phase 9: Regime Calibration (BACKLOG)
**Goal:** Fix the three model quality failures observed in the first live pipeline run (2026-04-27): High-Vol dominates at 61% of days (regime boundaries are not well-calibrated), OOS walk-forward produces 8 label variants instead of 3 stable regimes (fold-level label instability), and GARCH conditional VaR outputs nonsensical values (mean_vol=700%+, VaR=-546%).
**Depends on:** Phase 7
**Requirements:** TBD
**Deferred at:** 2026-04-27 — observed during Phase 7 UAT full pipeline run
**Problems to solve:**
  1. High-Vol at 61% — threshold/prior calibration causing one regime to absorb too much of the distribution
  2. OOS label proliferation — walk-forward fold labels not aligned to in-sample regime names; need Procrustes or Hungarian matching across folds
  3. GARCH VaR scaling bug — mean_vol=700% suggests returns are in basis points not decimals somewhere in the GARCH path
**Plans:** 0 plans (run /gsd-plan-phase 9 to break down)

Plans:
- [ ] TBD (run /gsd-plan-phase 9 to break down)

### Phase 8: HDP-HMM Inference Optimization — Parallelize the 133-fold walk-forward loop (joblib multiprocessing), add JAX XLA CPU flag for all-core utilization, implement ELBO early stopping when plateau detected, and optionally expose a NUTS path for overnight-viable full posterior sampling. Goal: cut overnight run from ~4 hours to under 90 minutes on a 6-core machine.

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 7
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 8 to break down)
