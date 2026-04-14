# ROADMAP — Regime-Detection

## Milestone 1: Production-Ready Regime Detection
**Goal:** Close 4 critical blockers, validate integration with Algo-Trading-Bot, deploy to production.  
**Timeline:** 2 weeks (by 2026-04-30)  
**Success Criteria:** All Phase 1 requirements met, integration test passing, zero blockers.

---

## Phase 1: Fix Critical Blockers
**Goal:** Address the 4 production blockers identified in codebase analysis.  
**Effort:** 3–5 days  
**Owner:** Adam Morris

### 1.1 — Tighten JAX/NumPyro Version Pinning
**Why:** Current constraints (`jax>=0.4.30`) allow breaking changes; reproducibility at risk.

**UAT:**
- [ ] `requirements.txt` or `pyproject.toml` pins exact versions (e.g., `jax==0.4.35`)
- [ ] `pip freeze` matches pinned versions
- [ ] CI/CD rejects PRs that loosen constraints
- [ ] README documents reproduction setup

**Deliverables:**
- Updated `requirements.txt` with exact versions
- CI/CD pin-check step
- Note in CLAUDE.md about JAX stability

---

### 1.2 — Implement Bot Label Mapping + Validation
**Why:** Regime names (Low-Vol, etc.) not validated against Algo-Trading-Bot's convention; integration breaks.

**UAT:**
- [ ] `config.py` has regime label mapping (Regime 0 → LOW_VOL, etc.)
- [ ] Integration test validates mapping (signals → bot schema → bot accepts)
- [ ] `signals.py` uses mapped labels (backward compatible)
- [ ] Dashboard shows both internal labels and bot labels
- [ ] CLAUDE.md documents label convention

**Deliverables:**
- Label mapping in `config.py`
- Integration test (test_bot_integration.py)
- Updated `signals.py` output format
- Documentation update

---

### 1.3 — Add Causal Pipeline Tests + Documentation
**Why:** No automated verification that pipeline has no lookahead; risk of silent data leaks.

**UAT:**
- [ ] `test_causality.py` verifies no future data in features
- [ ] `test_causality.py` verifies no future data in standardization
- [ ] `test_causality.py` verifies PCA fitted on past only
- [ ] All tests pass in CI/CD
- [ ] CLAUDE.md documents causality guarantees

**Deliverables:**
- `tests/test_causality.py` with 6+ test cases
- Causality test in CI/CD pipeline
- Updated `CLAUDE.md` hard constraints section

---

### 1.4 — Create Integration Test with Algo-Trading-Bot
**Why:** No end-to-end verification that signals work with trading bot; integration failures in production.

**UAT:**
- [ ] Integration test exists (test_bot_integration.py or similar)
- [ ] Test runs regime pipeline on sample data
- [ ] Test extracts signals in bot-expected format
- [ ] Test validates bot can consume signals (schema check or mock bot import)
- [ ] Test runs in <5 min, green in CI/CD

**Deliverables:**
- `tests/test_bot_integration.py`
- Mock or stub of Algo-Trading-Bot signal handler
- Integration test in CI/CD
- README integration instructions

---

## Phase 2: Incremental Data Updates
**Goal:** Optimize pipeline to avoid re-downloading 16 years of data; reduce training time from 20 min to <5 min on new data.  
**Effort:** 1–2 weeks  
**Depends on:** Phase 1 complete

### 2.1 — Implement Incremental Data Collection
**Why:** Every run re-downloads full history (10–20 min waste); blocks live updates.

**UAT:**
- [ ] `collect.py` detects latest data in local cache
- [ ] New data only (delta) is fetched from FRED and yfinance
- [ ] Full backtest mode still available (force re-download)
- [ ] Incremental mode runs in <5 min on 1–30 days of new data
- [ ] No data consistency issues (no gaps, duplicates, or misalignment)

**Deliverables:**
- Cache mechanism in `collect.py` (SQLite or Parquet)
- `--mode incremental` vs `--mode full` flags in run.py
- Updated config.py with cache path
- Tests for cache coherence

---

### 2.2 — Optimize Feature Computation for Live Data
**Why:** Rolling PCA and standardization are slow on full history; live updates need to be fast.

**UAT:**
- [ ] PCA incrementally updated (new features fitted, past retained)
- [ ] Standardization uses expanding windows (no expensive recomputation)
- [ ] Live prediction on 1 new row < 1 sec
- [ ] Backtesting still available (full recompute if needed)

**Deliverables:**
- Incremental PCA in `features.py`
- Live prediction mode in `train.py`
- Performance benchmarks (before/after)
- Updated config.py with cache strategy

---

## Phase 2.5: Model Diagnostics & Robustness Fixes
**Goal:** Fix critical model validation issues (OOS regime fragmentation, feature selection bias, VaR backtesting) before production deployment.  
**Effort:** 3–5 days  
**Depends on:** Phase 2.1 complete  
**Blocker:** Yes — must pass before go-live

### 2.5.1 — Diagnose Out-of-Sample Regime Fragmentation
**Why:** In-sample model has 4 regimes, but OOS walk-forward produces 10 fragmented regimes. This breaks signal stability and trading.

**UAT:**
- [ ] Root cause identified: rolling PCA drift vs non-stationary features
- [ ] Test with FIXED PCA (fitted on train set) vs rolling PCA on OOS data
- [ ] If fixed PCA reduces OOS regimes from 10→~4, rolling PCA is culprit
- [ ] Decision made: Use fixed PCA for production or longer rolling window
- [ ] OOS regime count documented in model card

**Deliverables:**
- `analyze_oos_fragmentation.py` — Compare fixed vs rolling PCA on OOS data
- Model card with findings (cause, impact, mitigation)
- Updated `hmm_training.py` or `orchestrator.py` to use fixed PCA (if decided)

---

### 2.5.2 — Fix Feature Selection Bias
**Why:** 7 features were selected on full dataset (2010–2026), creating implicit overfitting. Features should be selected on train set only.

**UAT:**
- [ ] Feature selection re-done: train set (2010–2020), held-out test (2021–2026)
- [ ] Re-selected features compared to original 7
- [ ] Model retrained with new features; OOS performance compared
- [ ] Test set performance reported (regime accuracy, VaR metrics)
- [ ] Decision: Use new features if OOS improves, else keep original

**Deliverables:**
- `analyze_feature_selection.py` — Train/test feature selection
- Updated `features.py` if new features selected
- Performance comparison report

---

### 2.5.3 — Resolve K=3 vs K=4 Regime Count
**Why:** BIC selected K=4 (crisis regime) with marginal improvement over K=3. May be overfitting.

**UAT:**
- [ ] Walk-forward validate both K=3 and K=4 on OOS data
- [ ] Compare: in-sample likelihood, OOS likelihood, regime stability
- [ ] Parsimony test: If BIC improvement < 2%, default to K=3
- [ ] Decision rule documented in code
- [ ] Bot integration requirement confirmed (3 regimes: Low/Med/High)

**Deliverables:**
- `select_k_via_crossval.py` — WF cross-validate K=3 vs K=4
- Comparison report with recommendation
- Updated code to enforce K=3 (if decided)

---

### 2.5.4 — Fix VaR Backtesting (Christoffersen Rejection)
**Why:** In-sample VaR fails Christoffersen test (p=0.0039), meaning exceedances cluster. GARCH-conditional VaR passes (p=0.5465). Static VaR underestimates tail clustering.

**UAT:**
- [ ] Document why static regime-dependent VaR clusters (volatility persistence)
- [ ] Validate GARCH-conditional VaR passes both Kupiec & Christoffersen tests
- [ ] Risk model card created: use GARCH-conditional VaR only for risk limits
- [ ] Dashboard updated to show GARCH VaR, deprecate static VaR
- [ ] Signals.py augmented with GARCH-conditional VaR warnings

**Deliverables:**
- Risk model card (static vs GARCH VaR comparison)
- Dashboard update to use GARCH VaR
- Code comments documenting why Christoffersen matters for trading

---

### 2.5.5 — Create Model Validation Scorecard
**Why:** Document all validation results before production. Future phases can reference this.

**UAT:**
- [ ] Model card created: architecture, data, assumptions, limitations
- [ ] Causality guarantees re-verified (no lookahead)
- [ ] Reproducibility checklist: JAX/NumPyro pinned, seed reproducible
- [ ] Known issues and workarounds documented
- [ ] Production checklist: All green before go-live

**Deliverables:**
- `MODEL_CARD.md` in root (accessible from README)
- Reproducibility guide
- Known issues & mitigations

---

## Phase 3: Code Refactoring + Polish (BACKLOG — Post-Deadline)
**Goal:** Improve maintainability and robustness; no blockers to deployment.  
**Effort:** 2–3 weeks  
**Depends on:** Phase 1–2 complete, post-deadline work

### 3.1 — Refactor train.py Monolith
**Why:** train.py is 1452 lines; hard to test and modify.

**Deliverables:**
- Split train.py into: hmmlearn.py (training), inference.py (prediction), evaluation.py (metrics)
- Move HMM orchestration to orchestrator.py
- All tests still pass, no API changes

---

### 3.2 — Dashboard Hardening
**Why:** Dashboard has had crashes (fixed in 95ea51b); prevent regressions.

**Deliverables:**
- Hex color parser tests
- Large date range stress tests
- Performance profiling for slow renders
- Error boundary for missing data

---

### 3.3 — Documentation + Examples
**Why:** Handoff to future maintainers needs clear guides.

**Deliverables:**
- Architecture guide (HMM rationale, regime meaning)
- Integration guide (how Algo-Trading-Bot uses signals)
- Troubleshooting guide (common failures, how to debug)
- Example notebooks (regime analysis, backtesting)

---

### 3.4 — Multi-Signal Combination (Fundamental Law of Active Management)
**Why:** Current system combines features into single HMM regime. Institutional research (Fundamental Law: IR = IC × √N) shows combining independent signals beats single models. Apply 11-step alpha combination procedure to weight 13 features independently, not just via PCA.

**Deliverables:**
- Implement 11-step signal combination engine (Steps 1–11 from institutional framework)
- Replace naive PCA weighting with independent edge estimation (Step 9: orthogonal regression)
- Calculate effective signal independence (Effective N vs. raw count of 13 features)
- Cross-validate combined regime probabilities vs. single-HMM baseline
- Documentation: How signal independence improves regime accuracy

**Impact:** 
- Expected IC improvement: 0.05–0.15 → 0.10–0.25 (from √13 ≈ 3.6x diversification benefit)
- Regime probability estimates more robust (noise-penalized, correlation-adjusted)
- Foundation for multi-model ensemble (HMM + Bayesian + tree-based regime classifiers)

---

## Dependency Graph
```
Phase 1.1 (JAX pinning)
  ↓
Phase 1.2 (Bot mapping)
  ↓
Phase 1.3 (Causality tests) + Phase 1.4 (Integration test) — PARALLEL
  ↓
Phase 2.1 (Incremental collection)
  ↓
Phase 2.2 (Live prediction optimization)
  ↓
[Production Go-Live: 2026-04-30]
  ↓
Phase 3.x (Backlog refactoring, post-deadline)
```

---

## Rollout Plan
1. **Phase 1 complete** → Code review + commit
2. **Phase 1 + Phase 2 complete** → Integration test with live Algo-Trading-Bot staging environment
3. **All systems green** → Merge to main, tag v1.0
4. **Deployment** → Move to production, monitor signal quality for 1 week
5. **Feedback loop** → Post-mortem, Phase 3 planning (backlog)

---

## Success Metrics (Milestone 1)
✅ All Phase 1 critical blockers closed  
✅ Phase 2 incremental updates working  
✅ Integration test with Algo-Trading-Bot passing  
✅ All 28+ tests passing (no regressions)  
✅ Code review approved by domain expert  
✅ Documentation complete (README, architecture guide, integration guide)  
✅ Zero known blockers in production  

---

## Resource Estimates
| Phase | Effort | Calendar Time | Owner |
|-------|--------|---------------|-------|
| 1.1 | 4 hrs | 1 day | Adam |
| 1.2 | 8 hrs | 1–2 days | Adam |
| 1.3 | 6 hrs | 1 day | Adam |
| 1.4 | 8 hrs | 1–2 days | Adam |
| **Phase 1 Total** | **26 hrs** | **3–5 days** | |
| 2.1 | 12 hrs | 2–3 days | Adam |
| 2.2 | 10 hrs | 1–2 days | Adam |
| **Phase 2 Total** | **22 hrs** | **3–5 days** | |
| **Milestone 1 Total** | **48 hrs** | **6–10 days** | Adam |

---

## Notes
- Backlog Phase 3 work does **not** block production; start after v1.0 deployment
- Each phase has atomic commits with clear messages referencing requirements
- CI/CD must run after each phase (all tests + linting)
- Code review required before merge (domain expert sign-off on causality)
