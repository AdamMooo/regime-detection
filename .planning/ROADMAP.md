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
- [ ] **Phase 7: Daily Pipeline & Clean Outputs** - Single entry point, 2 HTML outputs, cron-ready

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
**Goal**: Feature selection uses walk-forward cross-validation with an expanded candidate set, and importance is documented — no held-out split bias remains
**Depends on**: Phase 4
**Requirements**: FEAT-01, FEAT-02, FEAT-03
**Success Criteria** (what must be TRUE):
  1. Feature candidate set contains 12+ candidates, each with a written economic rationale
  2. Feature selection runs walk-forward: each fold selects features on training data only and tests OOS — no held-out split contamination
  3. A feature importance document (OOS-measured) shows which features drive regime separation
**Plans**: TBD

### Phase 6: Model Architecture Experiments
**Goal**: K regime count is selected on OOS evidence, the USE_HDP decision is locked with documentation, and train.py is refactored so no module exceeds 500 lines
**Depends on**: Phase 5
**Requirements**: MODEL-01, MODEL-02, MODEL-03
**Success Criteria** (what must be TRUE):
  1. K=3, K=4, and K=5 are compared on OOS stability and economic validity (DIAG-04 metrics) — a winner is selected and locked in config
  2. A documented decision on USE_HDP exists: either NumPyro HDP-HMM is re-enabled with evidence it outperforms StudentTHMM, or the dead code is formally deprecated and removed
  3. No single module in the training pipeline exceeds 500 lines; training, evaluation, and dashboard building are separate files
**Plans**: TBD

### Phase 7: Daily Pipeline & Clean Outputs
**Goal**: A single command runs the full daily pipeline end-to-end in under 10 minutes, exactly 2 HTML outputs exist, and regime results are written in a format suitable for nightly cron
**Depends on**: Phase 6
**Requirements**: PIPE-01, PIPE-02, PIPE-03
**Success Criteria** (what must be TRUE):
  1. `python scripts/run.py` executes collect → features → train → signals in under 10 minutes on new data
  2. Exactly 2 HTML files exist after a run: figures/dashboard.html and figures/feature_analysis.html — no others are created or left over
  3. regime_results.csv is written on every run containing today's regime, probabilities, and GARCH VaR — verified by running the script twice and checking the file updates
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Fix Critical Blockers | v1.0 | 4/4 | Complete | 2026-04-13 |
| 2. Incremental Data Updates | v1.0 | 1/1 | Complete | 2026-04-13 |
| 2.5 Model Diagnostics & Robustness | v1.0 | 5/5 | Complete | 2026-04-14 |
| 3. Code Refactoring + Polish | v1.0 | 4/4 | Complete | 2026-04-15 |
| 4. Empirical Diagnostics | v1.1 | 0/2 | Not started | - |
| 5. Feature Engineering Overhaul | v1.1 | 0/? | Not started | - |
| 6. Model Architecture Experiments | v1.1 | 0/? | Not started | - |
| 7. Daily Pipeline & Clean Outputs | v1.1 | 0/? | Not started | - |
