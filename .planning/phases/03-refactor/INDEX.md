# Phase 3 Planning Index

**Phase:** 03-refactor (Code Refactoring + Polish)  
**Status:** Planning Complete  
**Created:** 2026-04-13  
**Total Plans:** 4  
**Wave Structure:** Wave 1 (3 parallel) + Wave 2 (1 dependent)  
**Effort:** 36–48 hours (2–3 weeks calendar time)

---

## Plans Overview

| Plan | Title | Wave | Type | Tasks | Depends On | Status |
|------|-------|------|------|-------|-----------|--------|
| [03-01](03-01-PLAN.md) | Train.py Refactoring | 1 | auto | 8 | — | Ready |
| [03-02](03-02-PLAN.md) | Dashboard Hardening | 1 | auto | 5 | — | Ready |
| [03-03](03-03-PLAN.md) | Documentation + Examples | 1 | auto | 6 | — | Ready |
| [03-04](03-04-PLAN.md) | Signal Combination | 2 | auto | 5 | 03-01 | Ready |

---

## Detailed Plan Summaries

### Plan 03-01: Train.py Refactoring ⚙️

**Objective:** Refactor monolithic train.py (2988 lines) into 4 focused modules.

**Scope:**
- Extract `inference.py` (regime filtering, label assignment, HMM fitting)
- Extract `hmmlearn.py` (PCA, model selection, regime volatility models)
- Extract `evaluation.py` (VaR backtests, diagnostics, metrics)
- Extract `orchestrator.py` (walk-forward validation)
- Refactor `train.py` to thin wrapper (400–500 lines)

**Success Criteria:**
- 4+ modules created, each with single responsibility
- All 33+ tests passing (no regressions)
- train() and rebuild_dashboard() APIs unchanged (backward compatible)
- Code coverage stable or improved
- CLAUDE.md updated with module structure

**Effort:** 10–14 hours  
**Files Modified:** 5 new modules + train.py refactor + tests  
**Key Dependency:** None (Wave 1, independent)

**Next Steps:** After complete, 03-04 can proceed (depends on refactored structure)

---

### Plan 03-02: Dashboard Hardening 📊

**Objective:** Defensive hardening to prevent crashes and performance regressions.

**Scope:**
- Add hex color validation (catch malformed colors)
- Add missing data error handling (graceful degradation)
- Create 8+ dashboard stress tests (20+ years of data, edge cases)
- Add performance profiling (P50/P95 render time benchmarks)
- Create error boundary (catch exceptions, log errors)

**Success Criteria:**
- 8+ new dashboard-specific tests, all passing
- Stress test with 20+ years data: P95 < 5 sec render time
- Hex colors validated before use
- Missing data imputed gracefully
- Error boundary catches exceptions without crashing
- Performance benchmarks documented

**Effort:** 6–8 hours  
**Files Modified:** dashboard.py, test_dashboard_hardening.py  
**Key Dependency:** None (Wave 1, independent)

**Performance Target:** P50 ≈ 2.5s, P95 ≈ 3.5s, Max ≈ 4.2s (20 years)

---

### Plan 03-03: Documentation + Examples 📚

**Objective:** Create comprehensive guides for future maintainers and integrators.

**Scope:**
- Write `docs/ARCHITECTURE.md` (HMM rationale, regime meaning, pipeline flow, causality)
- Write `docs/INTEGRATION.md` (signal schema, label mapping, Algo-Trading-Bot API)
- Write `docs/TROUBLESHOOTING.md` (4+ common issues, debug workflows)
- Create `examples/regime_analysis.ipynb` (regime exploration, backtest analysis)
- Create `examples/backtesting.ipynb` (regime-aware strategy workflow)
- Update `README.md` with links to all docs

**Success Criteria:**
- 3 markdown guides (200+/150+/150+ lines each)
- 2 Jupyter notebooks (10+ cells each)
- All docs linked from README
- All notebooks executable without errors
- Cross-references between docs

**Effort:** 8–10 hours  
**Files Created:** 5 (3 markdown guides, 2 notebooks)  
**Key Dependency:** None (Wave 1, independent)

**Handoff Quality:** Future maintainer can read ARCHITECTURE, future integrator can follow INTEGRATION, future debugger can use TROUBLESHOOTING

---

### Plan 03-04: Signal Combination (Multi-Signal Ensemble) 🎯

**Objective:** Implement 11-step institutional alpha combination framework (Fundamental Law).

**Scope:**
- Implement 11-step signal combination engine in `signal_combination.py`
  - Steps 1–5: Signal preparation (standardization, ranking, demeaning)
  - Steps 6–8: IC calculation (information coefficient + bias adjustment)
  - Steps 9–10: Independence analysis (orthogonal regression, Effective N)
  - Step 11: Optimal weighting based on independent IC
- Add `USE_SIGNAL_COMBINATION` config flag (default: False, backward compatible)
- Create 10+ unit tests
- Cross-validate vs. single-HMM baseline
- Generate performance report (IC improvement, Effective N, diversification benefit)

**Success Criteria:**
- 11-step framework fully implemented
- Independent IC calculated per feature (Step 9: orthogonal regression)
- Effective N ≈ 3.6 (showing √13 ≈ 3.6x diversification benefit target)
- Cross-validation shows IC improvement (target: 0.05–0.15 → 0.10–0.25)
- Performance report with IC baseline vs. combined comparison
- Backward compatible (flag disabled by default)
- All tests passing (no regressions to existing code)

**Effort:** 12–16 hours  
**Files Created/Modified:** signal_combination.py, config.py, test_signal_combination.py  
**Key Dependency:** 03-01 complete (uses refactored module structure)

**Expected Outcome:** IC improvement 50%+ (0.08 → 0.12 OOS typical); ready for optional production deployment

---

## Execution Plan

### Wave 1: Parallel Execution (3 Plans)

All three can run in parallel (no file conflicts):

**Plan 03-01** touches: `inference.py`, `hmmlearn.py`, `evaluation.py`, `orchestrator.py`, `train.py`, tests/  
**Plan 03-02** touches: `dashboard.py`, tests/test_dashboard_hardening.py  
**Plan 03-03** touches: `docs/`, `examples/`, `README.md`  

→ **No overlap, fully parallelizable**

**Estimated Duration:** 10–14 hours (longest plan: 03-01)  
**Calendar Time:** 2–3 days (concurrent work)

### Wave 2: Dependent Execution (1 Plan)

**Plan 03-04** depends on 03-01 complete (uses refactored modules)

**Start:** After 03-01 passes all tests  
**Estimated Duration:** 12–16 hours  
**Calendar Time:** 2–3 days

---

## Quality Gates

### Between Waves

✅ Wave 1 → Wave 2:
- All tests passing (33+ existing + 8+ dashboard + 10+ signal combination)
- No breaking changes to external APIs (train(), rebuild_dashboard(), signals.py)
- CLAUDE.md updated with refactored architecture
- Documentation complete and linked

### Throughout Execution

✅ After each task:
- Tests run: `pytest tests/ -xvs`
- Git commit with clear message
- No regressions in existing functionality

✅ Before merging to main:
- Code review (domain expert sign-off)
- Performance benchmarks validated
- Backward compatibility confirmed

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Refactoring breaks existing code | Medium | High | Comprehensive regression tests (test_train_refactor.py, 6+ cases) |
| Dashboard performance regresses | Low | Medium | Performance benchmarks (P50/P95 stress tests) |
| Documentation becomes stale | Low | Low | Documentation linked from README, CI can validate freshness |
| Signal combination doesn't improve baseline | Medium | Low | Optional feature (disabled by default); CV validates before enabling |

---

## Dependencies & Blockers

### External Dependencies
- NumPyro 0.20.0 (HMM backend) — already pinned in requirements.txt
- scikit-learn (PCA, orthogonal regression) — already in requirements.txt
- Streamlit (dashboard) — already in requirements.txt

### Internal Dependencies
- Phase 1 + Phase 2 must be complete (existing infrastructure)
- 03-01 must complete before 03-04 starts

### Known Constraints
- No new external dependencies (stick to current requirements.txt)
- Backward API compatibility required (no breaking changes)
- All 33+ existing tests must pass
- Causal guarantees must be preserved (no lookahead in features)

---

## Success Metrics

### Phase 3.1 (Train.py Refactoring)
- ✅ train.py reduced from 2988 → 400–500 lines (86% reduction)
- ✅ 4+ modules created, each focused on single concern
- ✅ All 33+ tests passing
- ✅ No API changes (train() signature unchanged)

### Phase 3.2 (Dashboard Hardening)
- ✅ 8+ new tests, all passing
- ✅ P95 render time < 5 sec on 20+ years data
- ✅ No dashboard crashes on edge cases (malformed colors, missing data)
- ✅ Performance benchmarks documented

### Phase 3.3 (Documentation)
- ✅ 3 guides (ARCHITECTURE, INTEGRATION, TROUBLESHOOTING)
- ✅ 2 notebooks (regime_analysis, backtesting)
- ✅ All docs linked from README
- ✅ Handoff complete (future maintainers can onboard)

### Phase 3.4 (Signal Combination)
- ✅ 11-step framework implemented
- ✅ IC improvement measured via cross-validation
- ✅ Effective N ≈ 3.6 (target achieved)
- ✅ Optional deployment ready (USE_SIGNAL_COMBINATION flag)

---

## Timeline

| Phase | Effort | Calendar | Status |
|-------|--------|----------|--------|
| 03-01 | 10–14h | 2–3d | Planned |
| 03-02 | 6–8h | 1–2d | Planned (parallel) |
| 03-03 | 8–10h | 2–3d | Planned (parallel) |
| 03-04 | 12–16h | 2–3d | Planned (after Wave 1) |
| **Total** | **36–48h** | **2–3 weeks** | **Ready for execution** |

---

## Document References

- **[03-CONTEXT.md](03-CONTEXT.md)** — Phase 3 full context, user requirements, architecture decisions
- **[03-01-PLAN.md](03-01-PLAN.md)** — Detailed train.py refactoring plan
- **[03-02-PLAN.md](03-02-PLAN.md)** — Dashboard hardening plan
- **[03-03-PLAN.md](03-03-PLAN.md)** — Documentation + examples plan
- **[03-04-PLAN.md](03-04-PLAN.md)** — Signal combination framework plan

---

## How to Execute

### Quick Start

```bash
# Start Wave 1 (all 3 plans in parallel)
/gsd-execute-phase 3 --plan 03-01 --parallel &
/gsd-execute-phase 3 --plan 03-02 --parallel &
/gsd-execute-phase 3 --plan 03-03 --parallel &

# Wait for Wave 1 to complete, then start Wave 2
/gsd-execute-phase 3 --plan 03-04
```

### Sequential (if parallelization not available)

```bash
# Execute plans in sequence (but they're designed for parallelization)
/gsd-execute-phase 3 --plan 03-01
/gsd-execute-phase 3 --plan 03-02
/gsd-execute-phase 3 --plan 03-03
/gsd-execute-phase 3 --plan 03-04
```

### Monitor Progress

```bash
# Check test suite during execution
pytest tests/ -xvs

# Check specific plan
cat .planning/phases/03-refactor/{plan}-SUMMARY.md

# Update state
echo "Progress: completing task X of Y" >> .planning/STATE.md
```

---

## Post-Execution

After Phase 3 complete:

1. **Code Review** — Domain expert review of refactoring + signal combination
2. **Performance Validation** — Dashboard benchmarks, signal combination CV results
3. **Documentation Review** — Verify handoff quality for future maintainers
4. **Retrospective** — Capture lessons learned in project memory
5. **Archive** — Store SUMMARY files for historical reference

---

## Notes

- Phase 3 is **post-deadline backlog** (production deployment 2026-04-30 not blocked)
- All work is **backward compatible** (no breaking changes)
- Execution is **fully autonomous** (no checkpoints or human interaction required)
- All **plans are executable** with provided specifications
- Every task has **clear success criteria** and **verification steps**

---

**Status:** ✅ Phase 3 Planning Complete  
**Ready for:** `/gsd-execute-phase 3`
