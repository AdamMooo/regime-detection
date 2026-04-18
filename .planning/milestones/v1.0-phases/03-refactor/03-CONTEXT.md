---
phase_number: 3
phase_name: Code Refactoring + Polish
phase_type: backlog
status: planning
created: "2026-04-13"
---

# Phase 3 Context — Code Refactoring + Polish

## Phase Goal
Improve code maintainability, robustness, and documentation. This is **post-deadline backlog work** that does not block production deployment (2026-04-30).

---

## Dependencies
- **Blocks:** None (post-deadline)
- **Depends on:** Phase 1 + Phase 2 complete

---

## User Requirements (from ROADMAP.md)

### 3.1 — Refactor train.py Monolith
**Why:** train.py is 1452 lines; hard to test and modify.

**Requirements:**
- Split train.py into focused modules:
  - `hmmlearn.py` — Core HMM training logic
  - `inference.py` — Prediction and regime assignment
  - `evaluation.py` — Metrics and diagnostics
  - `orchestrator.py` — Training workflow coordination
- All tests still pass (no regressions)
- No API changes to `signals.py` (backward compatible)
- Commits should be atomic per module split

**Success Criteria:**
- [ ] train.py split into 4+ modules
- [ ] All 33+ tests passing (no regressions)
- [ ] Code coverage stable or improved
- [ ] CLAUDE.md updated with new module structure
- [ ] Each module documented with docstrings

---

### 3.2 — Dashboard Hardening
**Why:** Dashboard has had crashes (fixed in 95ea51b); prevent regressions.

**Requirements:**
- Add hex color parser tests
- Add large date range stress tests
- Add performance profiling for slow renders
- Add error boundary for missing data
- Prevent future dashboard crashes

**Success Criteria:**
- [ ] 8+ new dashboard-specific tests added
- [ ] Stress test with 20+ years of data (handles date range extremes)
- [ ] Hex color parsing validated (malformed colors handled gracefully)
- [ ] Performance benchmarks documented (P50/P95 render times)
- [ ] Error boundary catches and logs missing data without crashing

---

### 3.3 — Documentation + Examples
**Why:** Handoff to future maintainers needs clear guides.

**Requirements:**
- Architecture guide (HMM rationale, regime meaning, pipeline flow)
- Integration guide (how Algo-Trading-Bot uses signals, schema format)
- Troubleshooting guide (common failures, how to debug)
- Example notebooks (regime analysis, backtesting workflows)

**Success Criteria:**
- [ ] Architecture guide (2–3 pages) in `docs/ARCHITECTURE.md`
- [ ] Integration guide (1–2 pages) in `docs/INTEGRATION.md`
- [ ] Troubleshooting guide (1–2 pages) in `docs/TROUBLESHOOTING.md`
- [ ] 2+ example notebooks in `examples/` (Jupyter format)
- [ ] All guides linked from README.md

---

### 3.4 — Multi-Signal Combination (Fundamental Law of Active Management)
**Why:** Current system combines 13 features into single HMM via PCA (naive). Institutional research (Fundamental Law: IR = IC × √N) shows combining independent signals beats single models.

**Approach:**
- 11-step alpha combination engine (weighted edge combination)
- Cross-sectional demeaning (remove shared variance across features)
- Orthogonal regression (identify unique contribution per signal)
- Optimal weighting based on independent IC, not signal strength

**Requirements:**
- Implement 11-step signal combination engine
- Replace naive PCA weighting with independent edge estimation
- Calculate effective signal independence (Effective N vs. raw count)
- Cross-validate combined regime probabilities vs. single-HMM baseline
- Document how signal independence improves regime accuracy

**Success Criteria:**
- [ ] Signal combination engine in new `signal_combination.py` module
- [ ] Independent IC calculation for each feature (Step 9: orthogonal regression)
- [ ] Effective N calculation (√13 ≈ 3.6x diversification benefit target)
- [ ] Cross-validation results vs. baseline (accuracy, stability)
- [ ] Documentation: IC improvement 0.05–0.15 → 0.10–0.25 (expected)
- [ ] Option to use multi-signal ensemble alongside single-HMM

---

## Architecture Context

### Current State
- **Core pipeline:** collect.py → features.py → train.py → signals.py
- **Feature engineering:** 13 features → rolling PCA reduction → HDP-HMM
- **Regime output:** 3 regimes (Low-Vol, Medium-Vol, High-Vol) with probabilities
- **Test coverage:** 33 tests (28 existing + 5 bot integration)
- **Known issue:** train.py is monolithic (1452 lines), difficult to modify

### Code Organization (Current)
```
Regime-Detection/
├── collect.py               (data collection)
├── features.py              (13-feature engineering + PCA)
├── train.py                 (1452 lines — HMM training + inference)
├── hdp_hmm.py               (core HMM implementation)
├── signals.py               (regime signal generation)
├── config.py                (model params, label mapping)
├── dashboard.py             (Streamlit visualization)
├── run.py                   (orchestration)
├── analyze.py               (post-hoc analysis)
├── trust.py                 (regime confidence scoring)
├── requirements.txt         (pinned JAX 0.9.1, NumPyro 0.20.0)
├── tests/                   (33 tests)
└── .planning/               (GSD artifacts)
```

### Code Organization (Target — Phase 3.1)
```
Regime-Detection/
├── collect.py               (unchanged)
├── features.py              (unchanged)
├── hmmlearn.py              (extracted from train.py — training logic)
├── inference.py             (extracted from train.py — prediction logic)
├── evaluation.py            (extracted from train.py — metrics)
├── orchestrator.py          (extracted from train.py — workflow coordination)
├── train.py                 (refactored — delegates to above modules)
├── hdp_hmm.py               (unchanged)
├── signals.py               (unchanged — backward compatible)
├── signal_combination.py    (new — Phase 3.4)
├── config.py                (unchanged)
├── dashboard.py             (hardened — Phase 3.2)
├── run.py                   (unchanged)
├── analyze.py               (unchanged)
├── trust.py                 (unchanged)
├── requirements.txt         (unchanged)
├── tests/                   (33+ tests, 8+ new for dashboard)
├── docs/                    (new — Phase 3.3)
│   ├── ARCHITECTURE.md
│   ├── INTEGRATION.md
│   └── TROUBLESHOOTING.md
├── examples/                (new — Phase 3.3)
│   ├── regime_analysis.ipynb
│   └── backtesting.ipynb
└── .planning/               (GSD artifacts)
```

---

## Constraints & Assumptions

### Hard Constraints (from CLAUDE.md)
- ✅ Use NumPyro for HMM (not hmmlearn, pomegranate)
- ✅ 13 features → rolling PCA → HDP-HMM (do not skip PCA)
- ✅ No K-means or hard clustering (probabilistic only)
- ✅ 3 regime target with fixed labels
- ✅ JAX 0.9.1 and NumPyro 0.20.0 pinned exactly
- ✅ Causality guarantees (no lookahead in features, standardization, PCA, inference)

### Refactoring Constraints
- **No API changes** to `signals.py` (downstream dependency: Algo-Trading-Bot)
- **Backward compatibility** required — any train.py function called by run.py must work as before
- **All 33+ tests must pass** (no regressions)
- **Docstrings mandatory** for new modules
- **No new external dependencies** (stick to current requirements.txt)

### Dashboard Hardening Constraints
- **Streamlit-based only** (no rewrite to React, Vue, etc.)
- **No data schema changes** (input format unchanged)
- **Performance target:** P95 render time <5 sec on 20 years of data

---

## Work Breakdown

### Phase 3.1 — Refactor train.py
- Identify functional boundaries in train.py (training, inference, evaluation, orchestration)
- Extract `hmmlearn.py` (HMM training, parameter initialization)
- Extract `inference.py` (regime assignment, probability filtering, hysteresis)
- Extract `evaluation.py` (diagnostics, metrics, cross-validation)
- Extract `orchestrator.py` (training workflow, parameter sweep, model selection)
- Refactor train.py to use new modules (thin wrapper)
- Update imports across codebase (run.py, etc.)
- Run full test suite after each extraction
- Commit each module atomically
- Update CLAUDE.md with new structure

**Estimated effort:** 8–12 hours  
**Estimated calendar time:** 2–3 days

### Phase 3.2 — Dashboard Hardening
- Review dashboard.py crash history (commit 95ea51b)
- Add hex color parsing tests (malformed input handling)
- Add large date range tests (20+ years, edge cases)
- Add performance profiling (render times)
- Add error boundary (graceful handling of missing data)
- Run full test suite after each addition
- Document performance benchmarks
- Commit tests atomically

**Estimated effort:** 6–8 hours  
**Estimated calendar time:** 1–2 days

### Phase 3.3 — Documentation + Examples
- Write architecture guide (HMM theory, regime meaning, feature pipeline)
- Write integration guide (signal schema, label mapping, downstream usage)
- Write troubleshooting guide (common issues, debug workflow)
- Create `regime_analysis.ipynb` (explore regimes, backtest analysis)
- Create `backtesting.ipynb` (regime-aware strategy workflow)
- Link all docs from README.md
- Commit docs atomically

**Estimated effort:** 8–10 hours  
**Estimated calendar time:** 2–3 days

### Phase 3.4 — Multi-Signal Combination (Fundamental Law)
- Research 11-step alpha combination framework
- Implement signal weighting engine (Steps 1–11)
- Implement orthogonal regression (Step 9) for independent IC
- Calculate effective signal independence (Effective N)
- Cross-validate multi-signal vs. baseline HMM
- Document IC improvement projections
- Add optional ensemble mode to config.py
- Commit signal_combination.py atomically
- Create performance report

**Estimated effort:** 12–16 hours  
**Estimated calendar time:** 3–4 days

---

## Testing Strategy

### Phase 3.1 Testing
- Run full test suite after each module extraction (baseline: 33 tests)
- No new tests required (refactoring only)
- If any test fails, investigate before proceeding
- Verify train.py API unchanged (run.py calls work as before)

### Phase 3.2 Testing
- 8+ new dashboard-specific tests
- Stress test data: 20+ years (performance benchmark)
- Edge cases: missing data, malformed colors, date range extremes
- Performance profiling: P50/P95 render times

### Phase 3.3 Testing
- Documentation review (clarity, completeness, accuracy)
- Notebook execution (Jupyter cells run without error)
- Link verification (all docs referenced from README)

### Phase 3.4 Testing
- Cross-validation: multi-signal vs. single-HMM
- IC calculations: baseline vs. with independent weighting
- Ensemble mode: backward compatible, no breaking changes
- Performance: training time, inference time

---

## Success Criteria (Phase 3 Complete)

✅ Phase 3.1: train.py split into 4+ focused modules, all tests passing  
✅ Phase 3.2: Dashboard hardened with 8+ new tests, stress tested  
✅ Phase 3.3: 3 documentation guides + 2 example notebooks created, linked  
✅ Phase 3.4: Multi-signal combination engine working, IC improvement measured  
✅ Code coverage stable or improved (≥33 tests passing)  
✅ All external dependencies unchanged (no new packages)  
✅ CLAUDE.md updated with refactoring summary  

---

## Known Risks

1. **Backward Compatibility:** Splitting train.py could break run.py or other callers
   - *Mitigation:* Comprehensive API testing, atomic commits per module
   
2. **Dashboard Regression:** Hardening could introduce new bugs
   - *Mitigation:* Run full test suite after each change, performance profiling
   
3. **Documentation Staleness:** Docs could drift from code
   - *Mitigation:* Docs linked from README, CI/CD can validate doc freshness
   
4. **Signal Combination Complexity:** 11-step framework is complex to implement
   - *Mitigation:* Research phase before coding, step-by-step implementation, cross-validation

---

## Deliverables

### Phase 3.1
- [ ] `hmmlearn.py` (extracted training logic)
- [ ] `inference.py` (extracted prediction logic)
- [ ] `evaluation.py` (extracted metrics)
- [ ] `orchestrator.py` (extracted workflow)
- [ ] Refactored `train.py` (thin wrapper)
- [ ] Updated CLAUDE.md (module structure)
- [ ] Atomic commits (one per module)

### Phase 3.2
- [ ] 8+ dashboard-specific tests
- [ ] Performance benchmarks (P50/P95 times)
- [ ] Hex color parser tests
- [ ] Large date range stress tests
- [ ] Error boundary for missing data
- [ ] Updated dashboard.py with error handling

### Phase 3.3
- [ ] `docs/ARCHITECTURE.md` (HMM theory, pipeline)
- [ ] `docs/INTEGRATION.md` (signal schema, downstream usage)
- [ ] `docs/TROUBLESHOOTING.md` (common issues, debug)
- [ ] `examples/regime_analysis.ipynb` (exploration, backtest)
- [ ] `examples/backtesting.ipynb` (strategy workflow)
- [ ] Updated README.md (links to docs)

### Phase 3.4
- [ ] `signal_combination.py` (11-step combination engine)
- [ ] Orthogonal regression implementation
- [ ] Effective N calculation
- [ ] Cross-validation vs. baseline
- [ ] Performance report (IC improvement)
- [ ] Optional ensemble mode in config.py

---

## Timeline & Milestones

**Phase 3 is post-deadline backlog.** Production deployment (2026-04-30) does not depend on Phase 3.

If Phase 3 is executed:
- **Phase 3.1 (Refactor):** 2–3 days after Phase 2 complete
- **Phase 3.2 (Hardening):** Parallel with 3.1
- **Phase 3.3 (Docs):** Parallel with 3.1–3.2
- **Phase 3.4 (Signal Combination):** 3–4 days after 3.1–3.3 complete

**Total Phase 3 effort:** 34–46 hours (backlog, not blocking)

---

## Decision Log

### Decision: Post-Deadline Backlog Status
**Context:** Phase 1 and 2 are critical for production (2026-04-30). Phase 3 is backlog.  
**Decision:** Phase 3 is optional, post-deadline work.  
**Rationale:** Refactoring and signal combination are nice-to-haves; production deployment does not depend on them.  
**Trade-off:** If Phase 3 skipped, codebase remains monolithic but functional.  
**Status:** ✅ Locked in ROADMAP.md

---

## Notes for Planner

- Phase 3 is post-deadline backlog — treat as exploratory/nice-to-have
- User has 2 separate projects (Algo-Trading-Bot, Portfolio-Manager) consuming regime signals
- Refactoring must preserve backward compatibility with downstream consumers
- Signal combination is a research-heavy task; cross-validation is critical
- Dashboard hardening is defensive (prevent regression, not add features)

