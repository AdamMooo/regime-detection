# Roadmap: Regime-Detection

## Milestones

- ✅ **v1.0 Production Ready** — Phases 1–3 (shipped 2026-04-16)
- 🚧 **v1.1 Model Validation & Trust** — Phases 4+ (in progress)

## Phases

<details>
<summary>✅ v1.0 Production Ready (Phases 1–3) — SHIPPED 2026-04-16</summary>

- [x] Phase 1: Fix Critical Blockers (4/4 plans) — JAX pinning, bot mapping, causality tests, integration test
- [x] Phase 2: Incremental Data Updates (1/1 plan) — delta-only fetch, <5 min on new data
- [x] Phase 2.5: Model Diagnostics & Robustness (5/5 plans) — OOS fragmentation, feature bias, K=4, GARCH VaR, model card
- [x] Phase 3: Code Refactoring + Polish (4/4 plans) — train.py split, dashboard hardening, docs, signal combination framework

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Model Validation & Trust (Planned)

> Goal: Build confidence in the model before live trading — rigorous out-of-sample validation,
> regime quality assessment, and a clear "trust threshold" that must be met before going live.

*Phases to be defined via `/gsd-new-milestone`*

## Progress

| Phase | Milestone | Plans Complete | Status   | Completed  |
|-------|-----------|---------------|----------|------------|
| 1. Fix Critical Blockers | v1.0 | 4/4 | Complete | 2026-04-13 |
| 2. Incremental Data Updates | v1.0 | 1/1 | Complete | 2026-04-13 |
| 2.5 Model Diagnostics & Robustness | v1.0 | 5/5 | Complete | 2026-04-14 |
| 3. Code Refactoring + Polish | v1.0 | 4/4 | Complete | 2026-04-15 |
