# Retrospective — Regime-Detection

---

## Milestone: v1.0 — Production Ready

**Shipped:** 2026-04-16  
**Phases:** 4 | **Plans:** 14 | **Tasks:** 61  
**Timeline:** 2026-03-12 → 2026-04-15 (34 days)

### What Was Built

- Closed 4 critical production blockers (JAX pinning, bot mapping, causality tests, integration test)
- Incremental data pipeline: delta-only fetch, 20 min → <5 min
- Diagnosed OOS regime fragmentation (PCA drift 74.91°), fixed with Procrustes alignment
- Feature selection re-done on held-out set: 6 new features, +3.5% OOS accuracy
- K=4 regimes enforced via walk-forward BIC validation
- GARCH-conditional VaR replacing static VaR (Christoffersen p=0.547)
- Full production docs: MODEL_CARD.md, REPRODUCIBILITY.md, KNOWN_ISSUES.md
- train.py refactored from 1452-line monolith into 4 modules

### What Worked

- Wave-based parallelization in Phase 2.5 — 5 plans in ~9 hours by running diagnostics in parallel
- Starting each phase with a clear diagnostic question before jumping to fixes
- Keeping hard constraints in CLAUDE.md — prevented NumPyro/K-means regressions across sessions
- GSD phase structure gave clear stopping points and prevented scope creep

### What Was Inefficient

- Multiple codebase reorganizations (Streamlit removed, K=3→K=4 revert, src/ restructure) — scope wasn't locked early enough
- Phase 3 refactoring happened while model still not trusted — may need revisiting if architecture changes
- `audit-open` bug in gsd-tools.cjs blocked milestone close — wasted time debugging tooling

### Patterns Established

- Diagnostic phases (2.5.1, 2.5.2) before fix phases prevent solving the wrong problem
- Walk-forward validation is the right gate for model decisions, not in-sample BIC alone
- GARCH over static VaR is now a hard constraint for this project

### Key Lessons

- **Trust the stats, not intuition:** K=4 looked like overfitting but walk-forward confirmed it
- **OOS fragmentation is a real risk:** Rolling PCA drift isn't obvious until you plot it
- **Model is not trusted yet:** 160+ tests passing ≠ model is good for live trading — v1.1 exists for a reason
- **Tooling debt compounds:** stale hooks + audit-open bug both cost time during milestone close

### Cost Observations

- Sessions: ~11 sessions over 34 days
- Notable: Phase 2.5 was the highest-value phase — found real model issues that would have caused silent failures in prod

---

## Cross-Milestone Trends

| Metric | v1.0 |
|--------|------|
| Phases | 4 |
| Plans | 14 |
| Tests at close | 160+ |
| Days | 34 |
| Major rework | 2 (K revert, codebase reorg) |
