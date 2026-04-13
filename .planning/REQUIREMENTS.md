# REQUIREMENTS — Regime-Detection

## Functional Requirements (Tier 1: MVP)

### R1: Regime Classification Pipeline
**User Story:** As an algorithmic trader, I need regime labels (Low-Vol / Moderate-Vol / High-Vol) for portfolio decision-making, so that I can adjust position sizing and risk exposure dynamically.

**Acceptance Criteria:**
- [ ] HDP-HMM produces 3 regime classes from 13 features
- [ ] Rolling PCA reduces dimensionality before HMM (no bypassing)
- [ ] Regime assignments are probabilistic (not hard-clustered)
- [ ] Model trains in <20 min on full history (2008–2026)
- [ ] Incremental update mode available (new data only, <5 min)
- [ ] Regime probabilities sum to 1.0 per timestamp

---

### R2: Bot Label Mapping
**User Story:** As the Portfolio-Manager, I need regime signals that match my expected volatility regimes (LOW_VOL, MED_VOL, HIGH_VOL), so integration is seamless.

**Acceptance Criteria:**
- [ ] Regime 0 maps to LOW_VOL (low volatility expansion)
- [ ] Regime 1 maps to MED_VOL (moderate volatility neutral)
- [ ] Regime 2 maps to HIGH_VOL (high volatility contraction)
- [ ] Mapping is validated in integration test (signals.py output → Algo-Trading-Bot input)
- [ ] Label names are consistent across all output formats (CSV, signals dict, dashboard)
- [ ] Documentation clarifies regime economic meaning

---

### R3: Causal Pipeline (No Lookahead)
**User Story:** As a researcher, I need guarantees that the pipeline doesn't leak future information (no lookahead), so that backtests and live trading are on equal footing.

**Acceptance Criteria:**
- [ ] Features computed without future data (rolling windows only, no fill-forward)
- [ ] Standardization uses expanding windows (not future data)
- [ ] PCA fitted incrementally (not on future data)
- [ ] HMM inference uses past regimes only (filtering, not smoothing in production)
- [ ] All checks automated in test suite (causality_test.py or similar)
- [ ] CI/CD fails if lookahead violations detected

---

### R4: Reproducibility
**User Story:** As an engineer, I need exact reproducible runs (same seed → same results), so I can debug and audit regime signals confidently.

**Acceptance Criteria:**
- [ ] JAX and NumPyro versions pinned exactly (e.g., `jax==0.4.35`, not `>=0.4.30`)
- [ ] Random seeds logged in all outputs
- [ ] Model checkpoints saved (model.pkl or NumPyro state dict)
- [ ] Reloading checkpoint produces identical inference on same data
- [ ] CI/CD pins dependency versions strictly

---

### R5: Integration with Algo-Trading-Bot
**User Story:** As the bot's signal handler, I need regime predictions with timestamps and confidence, so I can make trading decisions.

**Acceptance Criteria:**
- [ ] Integration test exists: run pipeline → extract signals → feed to bot → verify bot accepts output
- [ ] Signal format matches bot's expected schema (timestamp, regime_label, regime_probs)
- [ ] No breaking changes to signals.py API (backward compatible)
- [ ] Bot can consume live signals (not just backtested data)
- [ ] Error handling: bot gracefully handles missing or late signals

---

## Non-Functional Requirements (Tier 2: Quality)

### R6: Test Coverage
**User Story:** As a maintainer, I need automated tests that catch regressions, so I can refactor safely.

**Acceptance Criteria:**
- [ ] Minimum 28 tests passing (current baseline maintained)
- [ ] Feature engineering tests present (input → output validation)
- [ ] HMM training tests present (convergence, regime stability)
- [ ] Integration test present (bot round-trip)
- [ ] Causality test present (no lookahead)
- [ ] All tests run in <2 min (CI/CD friendly)

---

### R7: Code Organization
**User Story:** As a developer, I need clear file structure and separation of concerns, so onboarding is fast and changes are safe.

**Acceptance Criteria:**
- [ ] Each file has 1 responsibility (collect, features, train, inference, signals, trust, dashboard)
- [ ] No circular dependencies (checked by import analysis)
- [ ] All functions have docstrings (type hints optional but good)
- [ ] Config.py is source of truth for all parameters
- [ ] No "magic numbers" in code (all parametrized)

---

### R8: Dashboard Robustness
**User Story:** As an analyst, I need a stable Streamlit dashboard that visualizes regime history and confidence, so I can understand model behavior.

**Acceptance Criteria:**
- [ ] Dashboard renders without crashes (test against real data)
- [ ] Hex color parsing handles edge cases (fixed in commit 95ea51b)
- [ ] Large date ranges don't cause performance issues
- [ ] Regime probability heatmaps are readable
- [ ] Trust scorecard visible and interpretable

---

## Documentation Requirements (Tier 3: Handoff)

### R9: User Guide
- [ ] README explains regime economic meaning
- [ ] Sample usage: how to get latest regime labels
- [ ] Integration instructions for Algo-Trading-Bot

### R10: Architect Guide
- [ ] Data pipeline causality guarantees documented
- [ ] HMM algorithm choice justified (why NumPyro, why 3 regimes)
- [ ] Feature engineering derivation explained
- [ ] Trust scorecard criteria listed

---

## Definition of Done (Phase 1)
1. All Tier 1 (Functional) requirements ✅
2. All Tier 2 (Non-Functional) requirements ✅
3. Zero blocking issues in integration test
4. 100% of hard constraints satisfied
5. Code reviewed and approved
6. Commit message references this REQUIREMENTS.md

---

## Not in Scope (Phase 1)
- train.py monolithic refactor (Phase 3 backlog)
- New HMM algorithm research (HDP-HMM is final)
- Real-time signal streaming (Algo-Trading-Bot handles that)
- New regime count or labels (3 regimes, fixed)
- GPU acceleration (NumPyro CPU performance is sufficient)
