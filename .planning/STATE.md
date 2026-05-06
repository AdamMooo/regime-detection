---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Model Quality & Regime Reliability
status: completed
last_updated: "2026-05-06T02:05:10.340Z"
last_activity: 2026-05-04
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 12
  completed_plans: 12
  percent: 100
---

# STATE — Regime-Detection Project Memory

## Latest Status

**As of:** 2026-05-04
**Phase:** 9 (Regime Calibration — fixing 3 critical UAT failures from Phase 7)
**Plan:** In progress
**Status:** v1.1 milestone phases complete; Phase 9 calibration work active
**Last activity:** 2026-05-04

---

## v1.1 Phase Structure

| Phase | Goal | Requirements | Status |
|-------|------|--------------|--------|
| 4. Empirical Diagnostics | Measure regime quality before any changes | DIAG-01, DIAG-02, DIAG-03, DIAG-04 | ✅ Complete 2026-04-20 |
| 5. Feature Engineering Overhaul | Expand and walk-forward validate features | FEAT-01, FEAT-02, FEAT-03 | ✅ Complete 2026-04-19 (5/5 plans) |
| 6. Model Architecture Experiments | K selection, HDP-HMM decision, refactor | MODEL-01, MODEL-02, MODEL-03 | ✅ Complete 2026-04-21 |
| 7. Daily Pipeline & Clean Outputs | Single entry point, 2 HTML outputs, cron-ready | PIPE-01, PIPE-02, PIPE-03 | ✅ Complete 2026-04-27 |
| 9. Regime Calibration | Fix 3 critical UAT failures from Phase 7 | TBD | 🔄 In Progress |

---

## Critical Blockers (Identified & Scheduled)

1. **JAX Version Pinning** — `jax>=0.4.30` allows breaking changes; reproducibility risk
   - **Fix in:** Phase 1.1
   - **Effort:** 4 hrs
   - **Status:** v1.0 milestone complete

2. **Bot Label Mapping** — Regime names not validated for Algo-Trading-Bot integration
   - **Fix in:** Phase 1.2
   - **Effort:** 8 hrs
   - **Status:** Scheduled

3. **Incremental Data Update** — Every run re-downloads 16 years (10–20 min overhead)
   - **Fix in:** Phase 2.1
   - **Effort:** 12 hrs
   - **Status:** Scheduled

4. **Integration Test Gap** — No end-to-end bot validation
   - **Fix in:** Phase 1.4
   - **Effort:** 8 hrs
   - **Status:** Scheduled

---

## Architecture Decision Log

### Decision 1: Keep NumPyro, Don't Switch HMM Libraries

**Context:** Previous sessions tried multiple approaches; K-means caused instability  
**Decision:** NumPyro is final choice (Bayesian HDP-HMM with probabilistic regimes)  
**Rationale:** Causal guarantees, no lookahead, stable regime assignments  
**Trade-offs:** Slower than K-means, but mathematically sound  
**Status:** Locked in hard constraints (CLAUDE.md)  

---

### Decision 2: 3 Regime Fixed Count

**Context:** Model produces 3 latent regimes; labels map to market volatility regimes  
**Decision:** Fix at K=3 regimes (Low-Vol, Moderate, High-Vol)  
**Rationale:** K=3 is academically correct. Phase 2.5 BIC justified K=4 statistically but empirically regimes 0&1 overlapped (15.3 vs 17.4 VIX avg — barely different). K=4 was a statistical artefact. config.py already has N_STATES=3.  
**Trade-offs:** Downstream consumers (Algo-Trading-Bot, Portfolio-Manager) expect 4-label schema — both must be updated  
**Status:** Locked — K=3 confirmed 2026-04-18, overrides Phase 2.5-03 BIC result

---

### Decision 3: Monolithic train.py Stays in Phase 1

**Context:** train.py is 1452 lines; hard to modify, but functional  
**Decision:** Refactoring deferred to Phase 3 (post-deadline, non-blocking)  
**Rationale:** Phase 1 focus is unblocking integration, not refactoring  
**Trade-offs:** Code remains monolithic, but no risk to deadline  
**Status:** Tracked in ROADMAP.md Phase 3 (v1.0 complete)

---

### Decision 4: Incremental Updates in Phase 2 (Not Phase 1)

**Context:** Every training run takes 10–20 min (16 years of data re-download)  
**Decision:** Phase 1 fixes blockers, Phase 2 optimizes incremental updates  
**Rationale:** Blockers are integration-critical; optimization is performance-critical but not blocking production  
**Trade-offs:** First production deployment still uses full re-download; Phase 2 is fast-follow  
**Status:** Phased in ROADMAP.md (v1.0 complete)

---

### Decision 5: Forward Returns Are Validation Only (v1.1)

**Context:** DIAG-04 implements regime-conditional return analysis for economic validity checking  
**Decision:** Forward returns (1d/5d/21d SPY/EEM/TLT/HYG) live in evaluation.py as diagnostics only — never added as model features or used in training  
**Rationale:** Adding forward returns as features would introduce lookahead bias and invalidate causality guarantees  
**Trade-offs:** Cannot use return predictability to improve model directly, but preserves integrity  
**Status:** Locked — enforced by out-of-scope constraint in REQUIREMENTS.md

---

### Decision 6: HDP-HMM Enabled as Primary Model (Phase 6 complete)

**Context:** Phase 6 OOS comparison: HDP +1.7pp accuracy (36.6% vs 34.9%), +19% dwell time. Machine verdict was studenthmm_wins (0.3pp short of +2pp D-03 threshold).  
**Decision:** Human override — HDP-HMM enabled as default (USE_HDP=True). StudentTHMM branch removed from train.py.  
**Rationale:** HDP's nonparametric architecture has better long-term headroom as data grows; +19% dwell improvement reduces whipsaw transitions in trading bot. Full StudentTHMM removal from inference.py/orchestrator.py deferred to Plan 02 refactor.  
**Trade-offs:** Adds NumPyro/SVI dependency; overnight runs ~4 hours (Phase 8 optimizes this)  
**Status:** Locked — USE_HDP=True in config.py; hdp_hmm.py retained; tests/_hdp_verdict.txt = "enabled"

---

## Accumulated Context

### Roadmap Evolution

- Phase 8 added (2026-04-21): HDP-HMM Inference Optimization — parallelize fold loop (joblib), JAX XLA CPU flag, ELBO early stopping, optional NUTS path. Goal: cut ~4hr overnight run to <90min on 6-core machine.

---

## Code Quality Baseline (v1.0 shipped)

- **Test count:** 160+ tests passing
- **Hard constraint compliance:** All 4 met (NumPyro, 13→PCA→HMM, no K-means, K=3 regimes)
- **Causal guarantees:** Verified (no lookahead in features, standardization, PCA)
- **VaR:** GARCH-conditional (Kupiec p=0.952, Christoffersen p=0.547)
- **Known concern:** Model not empirically validated for economic meaningfulness — v1.1 addresses this

---

## Known Gotchas (Learned from History)

1. **K-Means Instability** — Hard clustering produces different labels with different random seeds
   - **Prevention:** Use only NumPyro (probabilistic); verified in tests
   
2. **Skipping PCA** — 13 raw features cause slow, unstable HMM training
   - **Prevention:** PCA reduction is mandatory in config; failing without it triggers error
   
3. **Lookahead in Features** — Rolling windows computed on future data leak information
   - **Prevention:** Causality tests verify no future data in features, standardization, PCA

4. **Forward Returns as Features** — DIAG-04 forward return analysis must never be fed back into training
   - **Prevention:** Enforced by out-of-scope constraint; evaluation.py is read-only diagnostic output

5. **HTML Output Proliferation** — Previous runs left stale HTML files beyond the 2 required outputs
   - **Prevention:** PIPE-02 enforces exactly 2 outputs; cleanup logic required in run.py

---

## Integration Dependencies

**Depends on:**

- Algo-Trading-Bot: signal schema, regime label convention, trading decision logic
- Portfolio-Manager: regime probability outputs, dashboard visibility

**Blocks:**

- Any live trading deployment (bot depends on regime signals)
- Portfolio risk adjustments (manager depends on regime confidence)

---

## Resources & References

- **Repository:** https://github.com/AdamMooo/Regime-Detection
- **Codebase analysis:** `.planning/CODEBASE-STATE.md` (465 lines, detailed audit)
- **Hard constraints:** `.planning/CLAUDE.md` and local `CLAUDE.md`
- **Test suite:** `tests/` directory (160+ tests minimum)
- **Training data:** FRED (macro indicators) + yfinance (market prices)
- **v1.0 archive:** `.planning/milestones/v1.0-ROADMAP.md`

---

## Phase 2.5 Execution Summary (Session #11 — 2026-04-14)

**All 5 Plans Executed & Verified via Wave-Based Parallelization:**

### Wave 1 (Parallel): Diagnostics

- **02.5-01:** OOS Fragmentation Diagnosis
  - Finding: K=3 stable, rolling PCA superior to fixed PCA
  - Decision: Continue rolling PCA (current approach confirmed)
  - Tests: 4/4 passing

- **02.5-02:** Feature Selection Bias Fix
  - Finding: 6 new features outperform original 7 on held-out test set
  - New Features: VRP, VIX, SPY_skew20, SPY_TLT_corr63, lev_effect20, rv_ratio_10_63
  - Improvement: +3.5% regime accuracy, +3.2x dwell time stability
  - Tests: 21/21 passing

### Wave 2 (Dependent): Model Optimization

- **02.5-03:** K Regime Count Selection
  - Finding: K=4 justified (4.9% BIC improvement >> 2% threshold)
  - Decision: Enforce K=4 in production (config.py N_STATES=4)
  - Tests: 21/21 passing

- **02.5-04:** VaR Backtesting Fix
  - Finding: Static VaR fails Christoffersen (p=0.0039), GARCH passes both tests
  - GARCH VaR: Kupiec p=0.952, Christoffersen p=0.547
  - Tests: 16/16 passing

### Wave 3 (Final): Validation & Documentation

- **02.5-05:** Model Validation Scorecard & Production Checklist
  - Deliverables: MODEL_CARD.md, REPRODUCIBILITY.md, KNOWN_ISSUES.md, TROUBLESHOOTING.md
  - Tests: 30+ validation tests, all passing

**Total Duration:** ~9 hours (3 waves, parallelized)  
**Test Status:** 160+ tests passing  
**Production Readiness:** ALL GREEN

---

## Session Notes

- User requested "full reset on planning and GSD structure" (tons of things happened, wasn't well organized)
- Model accuracy/stability issues + code organization issues identified
- Goal: Clean code + good model + live integration by 2026-04-30
- Architecture is fundamentally sound (NumPyro, 160+ tests, causal guarantees)
- Reset is unblocking + optimization, not rewrite
