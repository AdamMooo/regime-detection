# STATE — Regime-Detection Project Memory

## Latest Status
**As of:** 2026-04-12 (Session #3)  
**Phase:** Planning complete, ready for Phase 1 execution  
**Branch:** main  

---

## Critical Blockers (Identified & Scheduled)
1. **JAX Version Pinning** — `jax>=0.4.30` allows breaking changes; reproducibility risk
   - **Fix in:** Phase 1.1
   - **Effort:** 4 hrs
   - **Status:** Scheduled

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
**Status:** ✅ Locked in hard constraints (CLAUDE.md)  

---

### Decision 2: 3 Regime Fixed Count
**Context:** Model produces 3 latent regimes; labels map to market volatility regimes  
**Decision:** Fix at 3 regimes (Low-Vol, Moderate-Vol, High-Vol)  
**Rationale:** Matches economic intuition and Algo-Trading-Bot convention  
**Trade-offs:** Less flexibility, but simpler integration  
**Status:** ✅ Locked in hard constraints  

---

### Decision 3: Monolithic train.py Stays in Phase 1
**Context:** train.py is 1452 lines; hard to modify, but functional  
**Decision:** Refactoring deferred to Phase 3 (post-deadline, non-blocking)  
**Rationale:** Phase 1 focus is unblocking integration, not refactoring  
**Trade-offs:** Code remains monolithic, but no risk to deadline  
**Status:** ✅ Tracked in ROADMAP.md Phase 3  

---

### Decision 4: Incremental Updates in Phase 2 (Not Phase 1)
**Context:** Every training run takes 10–20 min (16 years of data re-download)  
**Decision:** Phase 1 fixes blockers, Phase 2 optimizes incremental updates  
**Rationale:** Blockers are integration-critical; optimization is performance-critical but not blocking production  
**Trade-offs:** First production deployment still uses full re-download; Phase 2 is fast-follow  
**Status:** ✅ Phased in ROADMAP.md  

---

## Code Quality Baseline
From codebase analysis (commit 95ea51b):
- **Test count:** 28 tests (causality, validation, calibration)
- **Hard constraint compliance:** ✅ All 4 met (NumPyro, 13→PCA→HMM, no K-means, 3 regimes)
- **Causal guarantees:** ✅ Verified (no lookahead in features, standardization, PCA)
- **Trust scorecard:** ✅ 8 validation checks implemented
- **Known issues:** ❌ 4 blockers (JAX pinning, bot mapping, incremental update, integration test)

---

## Phase 1 Execution Plan
**Timeline:** 3–5 days  
**Parallel structure:**
- 1.1 (JAX pinning) → 1.2 (bot mapping) → (1.3 + 1.4 in parallel) → Phase 2

**Deliverables:**
- [ ] Updated `requirements.txt` with exact pinned versions
- [ ] `config.py` regime label mapping (Regime 0 → LOW_VOL, etc.)
- [ ] `test_causality.py` with 6+ test cases
- [ ] `test_bot_integration.py` validating end-to-end signal flow
- [ ] Updated CLAUDE.md with label convention documentation
- [ ] All tests passing in CI/CD
- [ ] Code review approved

---

## Known Gotchas (Learned from History)
1. **K-Means Instability** — Hard clustering produces different labels with different random seeds
   - **Prevention:** Use only NumPyro (probabilistic); verified in tests
   
2. **Skipping PCA** — 13 raw features cause slow, unstable HMM training
   - **Prevention:** PCA reduction is mandatory in config; failing without it triggers error
   
3. **Lookahead in Features** — Rolling windows computed on future data leak information
   - **Prevention:** Causality tests verify no future data in features, standardization, PCA

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
- **Test suite:** `tests/` directory (28 tests minimum)
- **Training data:** FRED (macro indicators) + yfinance (market prices)

---

## Next Steps
1. **Immediate:** Run `/gsd-plan-phase 1` to generate detailed phase plan
2. **Then:** Execute Phase 1 with atomic commits and integration tests
3. **Success:** All blockers closed, integration test green, code review passed
4. **Then:** Phase 2 (incremental updates), Phase 3 (refactoring, backlog)

---

## Session Notes
- User requested "full reset on planning and GSD structure" (tons of things happened, wasn't well organized)
- Model accuracy/stability issues + code organization issues identified
- Goal: Clean code + good model + live integration by 2026-04-30
- Codebase analysis revealed 4 critical production blockers (not 10+)
- Architecture is **fundamentally sound** (NumPyro, 28 tests, causal guarantees)
- Reset is **unblocking + optimization**, not rewrite
