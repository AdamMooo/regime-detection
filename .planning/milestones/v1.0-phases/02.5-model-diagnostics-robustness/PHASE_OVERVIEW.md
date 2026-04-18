# Phase 2.5: Model Diagnostics & Robustness Fixes — Complete Plan Overview

## Phase Goal
Fix critical model validation issues (OOS regime fragmentation, feature selection bias, VaR backtesting) identified in rigorous audit before production deployment. Create comprehensive validation scorecard to enable confident go-live.

## Phase Status
**Phase 2.5 Plans:** ✅ All 5 plans created and ready for execution

---

## Plan Breakdown

### Plan 02.5-01: Diagnose Out-of-Sample Regime Fragmentation
**Wave:** 1 (parallel with 02.5-02)  
**Tasks:** 3 (diagnostic + tests + implementation)  
**Effort:** ~6 hours  

**Objective:** Diagnose why in-sample HMM (4 regimes) fragments into 10 regimes OOS. Compare fixed PCA vs rolling PCA to identify culprit. Make production decision.

**Deliverables:**
- `analyze_oos_fragmentation.py` — Compare fixed PCA, rolling PCA, extended rolling window
- `tests/test_oos_fragmentation.py` — Unit tests validating fragmentation analysis
- `fragmentation_report.txt` — Root cause identified and recommendation made
- Config/code update — Implement chosen fix (fixed PCA or extended window)

**Success Criteria:**
- Root cause identified (rolling PCA drift vs non-stationary features)
- OOS regime count comparison complete (A vs B vs C experiments)
- Production fix decided and coded
- All tests passing

---

### Plan 02.5-02: Fix Feature Selection Bias
**Wave:** 1 (parallel with 02.5-01)  
**Tasks:** 3 (analysis + tests + implementation)  
**Effort:** ~6 hours  

**Objective:** Fix implicit overfitting. Re-select features on held-out train set (2010–2020), evaluate on held-out test set (2021–2026). Compare with original 7 features. Use new features if OOS improves, else keep original.

**Deliverables:**
- `analyze_feature_selection.py` — Feature selection on held-out train, comparison on held-out test
- `tests/test_feature_selection_bias.py` — Unit tests validating bias-free selection
- `feature_selection_report.txt` — Performance comparison and recommendation
- `config.py` update — FEATURE_SUBSET updated (or confirmed unchanged)

**Success Criteria:**
- Feature selection performed on held-out train set only
- Performance comparison complete (original vs new)
- Decision made and documented (keep original or switch)
- All tests passing

---

### Plan 02.5-03: Resolve K=3 vs K=4 Regime Count
**Wave:** 2 (depends on 02.5-01, 02.5-02)  
**Tasks:** 3 (cross-validation + tests + implementation)  
**Effort:** ~6 hours  

**Objective:** Validate K=3 vs K=4 on OOS data. Apply parsimony rule (if BIC improvement < 2%, use K=3). Ensure selected K aligns with bot integration (3 regimes).

**Deliverables:**
- `select_k_via_crossval.py` — Walk-forward validate K=3 vs K=4, apply parsimony rule
- `tests/test_regime_count_selection.py` — Unit tests comparing K selection metrics
- `regime_count_selection_report.txt` — Comparison table and recommendation
- `config.py` update — N_STATES enforced to final K (3 or 4)

**Success Criteria:**
- K=3 and K=4 walk-forward validated on OOS data
- Parsimony rule applied (2% threshold)
- Regime stability metrics compared (dwell time, entropy, label consistency)
- Decision made and implemented in config.py
- All tests passing

---

### Plan 02.5-04: Fix VaR Backtesting (Christoffersen Rejection)
**Wave:** 2 (depends on 02.5-01, 02.5-02, 02.5-03)  
**Tasks:** 6 (documentation + code updates + tests + finalization)  
**Effort:** ~8 hours  

**Objective:** Document why static VaR fails Christoffersen test. Validate GARCH-conditional VaR. Create risk model card. Update signals and dashboard to use GARCH VaR. Add risk warnings.

**Deliverables:**
- `docs/RISK_MODEL_CARD.md` — Static vs GARCH VaR comparison, test results, recommendations
- `evaluation.py` update — Enhanced with VaR comparison documentation
- `signals.py` update — Added garch_var_95 output field, compute_garch_var() function, warnings
- `dashboard.py` update — GARCH VaR plots (primary), static VaR (deprecated), risk warning section
- `tests/test_var_backtesting.py` — Unit tests validating GARCH VaR safety
- Production checklist validation

**Success Criteria:**
- Static VaR failure documented (Christoffersen p < 0.05)
- GARCH VaR success validated (Kupiec + Christoffersen p > 0.05)
- Risk model card created with test results
- Signals updated with garch_var_95 and warnings
- Dashboard updated with GARCH VaR primary metric
- All tests passing

---

### Plan 02.5-05: Create Model Validation Scorecard
**Wave:** 3 (depends on all prior plans)  
**Tasks:** 6 (documentation + tests + finalization)  
**Effort:** ~8 hours  

**Objective:** Create comprehensive model card documenting architecture, validation, limitations, and production readiness. Re-verify causality. Create reproducibility guide. Document known issues and troubleshooting guide. Build production checklist.

**Deliverables:**
- `MODEL_CARD.md` — Comprehensive model documentation (250+ lines, 8 sections)
- `REPRODUCIBILITY.md` — Exact steps to reproduce model (100+ lines, 8 sections)
- `docs/KNOWN_ISSUES.md` — Known issues catalog (150+ lines, 8 issues documented)
- `docs/TROUBLESHOOTING.md` — Debug guide (100+ lines, 8+ symptoms)
- `tests/test_model_card_validation.py` — Unit tests validating all claims (7 tests)
- `README.md`, `CLAUDE.md`, `STATE.md` updates — Link to documentation, mark complete

**Success Criteria:**
- All documentation files created and complete
- Causality guarantees re-verified
- Reproducibility guide with exact steps
- All Phase 2.5 known issues documented
- Production checklist all green
- All tests passing

---

## Execution Wave Structure

```
Wave 1: Parallel Analysis (02.5-01 + 02.5-02)
├── 02.5-01: OOS Fragmentation Diagnosis
└── 02.5-02: Feature Selection Bias Fix

Wave 2: Model Optimization (02.5-03 + 02.5-04 in sequence per dependencies)
├── 02.5-03: K Regime Count Selection
└── 02.5-04: VaR Backtesting Fix

Wave 3: Validation & Handoff (02.5-05)
└── 02.5-05: Model Validation Scorecard + Production Checklist
```

## Total Effort & Timeline

| Plan | Wave | Effort | Dependencies | Status |
|------|------|--------|--------------|--------|
| 02.5-01 | 1 | ~6 hrs | None | Ready |
| 02.5-02 | 1 | ~6 hrs | None | Ready |
| 02.5-03 | 2 | ~6 hrs | 02.5-01, 02.5-02 | Ready |
| 02.5-04 | 2 | ~8 hrs | 02.5-01–03 | Ready |
| 02.5-05 | 3 | ~8 hrs | All prior | Ready |
| **TOTAL** | — | **~34 hrs** | — | **Ready** |

**Estimated Duration:** 2–3 days (assuming parallel wave execution)

---

## Quality Gates & Validation

### Per-Plan Validation
- ✅ Each plan has automated test suite
- ✅ Each plan has checkpoint verification
- ✅ Each plan has clear success criteria

### Phase-Level Validation
- ✅ All 5 plans cover Phase 2.5 requirements (2.5.1–2.5.5)
- ✅ All 5 plans are atomic and parallelizable (Waves 1–3)
- ✅ No blockers between plans (dependencies respected)
- ✅ All deliverables specified and testable

### Production-Level Validation
- ✅ Final plan (02.5-05) includes comprehensive checklist
- ✅ No remaining known blockers after Phase 2.5
- ✅ All causality guarantees verified
- ✅ All 155+ tests passing
- ✅ Full documentation for handoff

---

## Key Decisions from Phase 2.5

Each plan includes decision points:

1. **02.5-01 Decision:** Use fixed PCA or extended rolling window?
   - If fixed PCA reduces OOS regimes → Use fixed PCA
   - If extended window (504 days) stabilizes → Extend window
   - Either way: OOS fragmentation fixed, regimes stable

2. **02.5-02 Decision:** Keep original 7 features or use new selected features?
   - If new features improve OOS → Switch to new features
   - If original perform same/better → Keep original
   - Either way: Feature selection bias removed, OOS generalization verified

3. **02.5-03 Decision:** Use K=3 or K=4?
   - If BIC improvement < 2% or OOS stability favors K=3 → Use K=3
   - If OOS performance justifies complexity → Use K=4 (with bot mapping)
   - Either way: K validated, bot integration aligned, regimes stable

4. **02.5-04 Decision:** Use GARCH-conditional VaR for production?
   - Yes, if Kupiec/Christoffersen tests pass (already known to pass)
   - Static VaR documented as deprecated
   - GARCH VaR output in signals, dashboard, warnings in place

5. **02.5-05 Decision:** Model approved for production deployment?
   - Yes, if all prior plans complete and tests pass
   - Comprehensive documentation created
   - Causality and reproducibility verified
   - Production checklist all green

---

## Integration with Broader Roadmap

**Phase 2.5 Dependency Chain:**
```
Phase 2.1 (Incremental Collection) — ✅ COMPLETE
    ↓ (provides data for diagnostics)
Phase 2.5 (Model Diagnostics) — ✅ PLANNED (this phase)
    ↓ (fixes identified issues)
Production Go-Live — Ready after 02.5-05
    ↓ (or Phase 3 backlog refactoring post-deployment)
Phase 3 (Post-Deadline Backlog) — Planned
```

**Next Steps After Phase 2.5:**
1. Execute plans sequentially (Wave 1 → Wave 2 → Wave 3)
2. Perform code review of all changes (causality, performance)
3. Deploy to production staging environment
4. Run full integration test with Algo-Trading-Bot
5. Go-live with continuous monitoring (monthly backtest, quarterly review)

---

## Success Definition

Phase 2.5 is complete when:

- ✅ All 5 plans executed and verified
- ✅ All deliverables created and committed
- ✅ All unit tests passing (155+)
- ✅ All checkpoints verified
- ✅ OOS fragmentation fixed
- ✅ Feature selection bias removed
- ✅ K regime count optimized and validated
- ✅ VaR backtesting fixed and GARCH validated
- ✅ Comprehensive documentation created
- ✅ Production checklist all green
- ✅ No remaining critical blockers
- ✅ Ready for production deployment

---

## Files Created

### Plans
- `.planning/phases/02.5-model-diagnostics-robustness/02.5-01-PLAN.md` — OOS fragmentation diagnosis
- `.planning/phases/02.5-model-diagnostics-robustness/02.5-02-PLAN.md` — Feature selection bias fix
- `.planning/phases/02.5-model-diagnostics-robustness/02.5-03-PLAN.md` — K regime count selection
- `.planning/phases/02.5-model-diagnostics-robustness/02.5-04-PLAN.md` — VaR backtesting fix
- `.planning/phases/02.5-model-diagnostics-robustness/02.5-05-PLAN.md` — Model validation scorecard

### This Overview
- `.planning/phases/02.5-model-diagnostics-robustness/PHASE_OVERVIEW.md` — This file

---

## How to Execute

1. **Read all 5 PLAN.md files** to understand full scope
2. **Execute Wave 1** (02.5-01 + 02.5-02 in parallel)
3. **Verify Wave 1 checkpoints** before proceeding
4. **Execute Wave 2** (02.5-03 + 02.5-04 in sequence per dependencies)
5. **Verify Wave 2 checkpoints** before proceeding
6. **Execute Wave 3** (02.5-05)
7. **Verify final production checklist** all green
8. **Deploy to production**

---

## Contact & Questions

This phase is designed for solo execution by Adam Morris (user) with Claude as executor. All decisions are documented in plan checkpoints; user approval is required at each gate before proceeding to next plan.

See individual PLAN.md files for detailed context, threats, and success criteria.

---

**Phase Created:** 2026-04-13  
**Phase Status:** ✅ Ready for Execution  
**Next Action:** Run `/gsd-execute-phase 02.5` to begin execution
