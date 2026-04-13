# Phase 1: Fix Critical Blockers — Detailed Plan

**Created:** 2026-04-13  
**Status:** Ready for execution  
**Timeline:** 3–5 days (26 hours effort, Adam Morris)  
**Dependency:** Decisions locked in 01-CONTEXT.md (D-01 through D-09)

---

## Executive Summary

Phase 1 addresses 4 critical production blockers preventing integration with Algo-Trading-Bot:

1. **JAX/NumPyro version pinning** (reproducibility risk) — D-01, D-02
2. **Bot label mapping + validation** (integration incompatibility) — D-03, D-04, D-09
3. **Causality tests + documentation** (no-lookahead guarantee) — D-05, D-06
4. **Integration test with bot** (E2E validation) — D-07, D-08

All work is sequenced to avoid merge conflicts and ensure dependencies are satisfied before dependent blockers start.

---

## Task Breakdown by Blocker

### Blocker 1.1: JAX/NumPyro Version Pinning

**Why:** Regime labels must be reproducible bit-for-bit across environments. Version ranges (`>=0.4.30`) allow breaking changes that silently corrupt regime assignments. For trading, this is non-negotiable.

**Dependency:** None (start first)  
**Effort:** ~3 hours  
**Calendar Time:** 1 day

#### Task 1.1.1: Resolve requirements.txt merge conflict
- **Acceptance:** requirements.txt has no merge markers; jax and numpyro pinned to exact versions
- **Details:**
  - requirements.txt currently has merge conflict between HEAD (exact) and feature branch (loose)
  - Resolve by accepting HEAD version: exact pinning (`jax==0.4.35`, `numpyro==0.20.0`, etc.)
  - Add comment in requirements.txt: `# Exact pinning required for regime reproducibility (see CLAUDE.md hard constraints)`
  - Verify no `>=` or `<` ranges remain for jax/numpyro lines
- **Verification:** `git diff HEAD -- requirements.txt | grep -E 'jax|numpyro'` shows only `==` operators
- **Commit:** Will be atomic per 1.1.4

#### Task 1.1.2: Add CI/CD pin-check validation step
- **Acceptance:** CI/CD pipeline rejects PRs that introduce loose constraints on jax/numpyro
- **Details:**
  - Create new CI/CD step (or add to existing linting job)
  - Script checks requirements.txt for `jax.*>=` or `numpyro.*>=` patterns
  - Fail pipeline with clear error message: "JAX/NumPyro version pinning required. Use == operator only."
  - Step runs after dependency install, before tests
- **Verification:** Manual test: create a PR with `jax>=0.4.30` and confirm CI rejects it
- **Implementation Note:** Add to `.github/workflows/` or equivalent CI config (exact path depends on current setup)
- **Commit:** Will be atomic per 1.1.4

#### Task 1.1.3: Update CLAUDE.md with reproducibility note
- **Acceptance:** CLAUDE.md hard constraints section documents exact pinning requirement
- **Details:**
  - Expand "Hard Constraints" section in CLAUDE.md
  - Add new subsection: "Reproducibility Guarantees"
  - Document: "JAX and NumPyro versions are pinned exactly (==, not >=) to guarantee regime label reproducibility across all environments. Breaking changes in these libraries silently corrupt regime assignments; loose constraints are unacceptable for production trading."
  - Add reference to requirements.txt and CI/CD validation
  - Add note: "Any PR loosening these constraints will be rejected by CI/CD."
- **Verification:** CLAUDE.md is readable and clear; no typos
- **Commit:** Will be atomic per 1.1.4

#### Task 1.1.4: Commit 1.1 work
- **Acceptance:** All 1.1.1–1.1.3 changes committed atomically; all tests pass
- **Details:**
  - Stage: requirements.txt, CI/CD config file, CLAUDE.md
  - Commit message: `fix: pin jax==0.4.35 numpyro==0.20.0, add CI/CD validation (blocker 1.1)`
  - Include reference to D-01, D-02 in commit body
  - Run full test suite: `pytest tests/ -v` (must pass all 28+ tests)
  - Verify CI/CD pipeline passes (including new pin-check step)
  - Push to main or feature branch (per workflow)
- **Verification:** `git log --oneline -1` shows new commit; all tests green
- **Effort Note:** 0.5 hours (bulk testing, no new implementation)

---

### Blocker 1.2: Bot Label Mapping + Validation

**Why:** Algo-Trading-Bot expects regime labels in uppercase with underscores (LOW_VOL, MED_VOL, HIGH_VOL), but Regime-Detection produces internal names (Low-Vol, Medium-Vol, High-Vol). Without explicit mapping and validation, integration fails silently.

**Dependency:** 1.1 complete (uses same config.py, signals.py)  
**Effort:** ~6 hours  
**Calendar Time:** 1–2 days

#### Task 1.2.1: Add LABEL_MAPPING to config.py
- **Acceptance:** config.py has LABEL_MAPPING dict; matches REGIME_NAMES keys to bot labels
- **Details:**
  - Add new dict to config.py (after REGIME_NAMES):
    ```python
    LABEL_MAPPING = {
        'Low-Vol': 'LOW_VOL',
        'Medium-Vol': 'MED_VOL',
        'High-Vol': 'HIGH_VOL',
    }
    ```
  - Add docstring: "Maps internal regime names to Algo-Trading-Bot canonical labels. This is the source of truth for all downstream integrations."
  - Verify keys match REGIME_NAMES exactly (case-sensitive)
  - Verify values match Algo-Trading-Bot expected labels (from CLAUDE.md)
- **Verification:** `python -c "from config import LABEL_MAPPING; assert len(LABEL_MAPPING) == 3; print(LABEL_MAPPING)"` shows all 3 mappings
- **Commit:** Will be atomic per 1.2.6

#### Task 1.2.2: Update signals.py to use LABEL_MAPPING
- **Acceptance:** signals.py output includes bot_label field; backward compatible
- **Details:**
  - Locate `_compute_regime_distributions()` or equivalent in signals.py
  - When outputting regime signal dict, add new field: `'bot_label': LABEL_MAPPING[regime_name]`
  - Keep existing fields (regime_name, regime_probs, timestamp) unchanged (backward compatibility per D-09)
  - Output format becomes: `{'timestamp': ..., 'regime_name': 'Low-Vol', 'bot_label': 'LOW_VOL', 'regime_probs': {...}}`
  - Add validation: if regime_name not in LABEL_MAPPING.keys(), raise KeyError with helpful message
  - Update docstring: "Signals now include both internal regime_name and bot_label for integration."
- **Verification:**
  - Create simple test: extract regime signal, check bot_label is in {LOW_VOL, MED_VOL, HIGH_VOL}
  - Run: `python -c "from signals import ...; sig = get_signal(...); assert sig['bot_label'] in ['LOW_VOL', 'MED_VOL', 'HIGH_VOL']"`
- **Commit:** Will be atomic per 1.2.6

#### Task 1.2.3: Update dashboard to display both labels
- **Acceptance:** Dashboard shows both regime_name and bot_label in UI
- **Details:**
  - Locate dashboard.py regime display section (likely a metrics card or table)
  - For each regime shown, display: "Low-Vol (LOW_VOL)" or similar
  - Add hover tooltip or legend explaining the mapping
  - Update title/label: "Regime: {regime_name} → Bot Label: {bot_label}"
  - Ensure column/row is readable and doesn't break layout
- **Verification:**
  - Run dashboard locally: `streamlit run dashboard.py`
  - Visually confirm both labels appear for sample data
  - Check no crashes with valid signal data
- **Commit:** Will be atomic per 1.2.6

#### Task 1.2.4: Update CLAUDE.md with label convention
- **Acceptance:** CLAUDE.md documents label mapping and bot integration convention
- **Details:**
  - Add new section to CLAUDE.md: "Bot Integration: Label Mapping"
  - Document the mapping: Regime 0 (Low-Vol) → LOW_VOL, etc.
  - Add note: "All signals output both regime_name (internal) and bot_label (canonical). Always use bot_label when communicating with Algo-Trading-Bot."
  - Add reference to config.py LABEL_MAPPING as source of truth
  - Update "Downstream Integration" section if it exists, or clarify existing entry
- **Verification:** CLAUDE.md is clear and matches code implementation
- **Commit:** Will be atomic per 1.2.6

#### Task 1.2.5: Test backward compatibility
- **Acceptance:** Old code parsing regime_name still works; new code using bot_label also works
- **Details:**
  - Create ad-hoc test (or add to test suite):
    - Generate sample signal dict with both regime_name and bot_label
    - Parse old way: `regime = signal['regime_name']` (should still work)
    - Parse new way: `bot_regime = signal['bot_label']` (should be valid)
    - Verify both produce expected values
  - Run existing test suite: `pytest tests/ -v` (no regressions)
  - Check that old dashboard code (if any) still works with new signals
- **Verification:** All 28+ tests pass; no deprecation warnings
- **Commit:** Will be atomic per 1.2.6

#### Task 1.2.6: Commit 1.2 work
- **Acceptance:** All 1.2.1–1.2.5 changes committed atomically; integration test ready to use (1.4 can start)
- **Details:**
  - Stage: config.py, signals.py, dashboard.py, CLAUDE.md
  - Commit message: `feat: add LABEL_MAPPING config, update signals output with bot_label (blocker 1.2)`
  - Include reference to D-03, D-04, D-09 in commit body
  - Run full test suite: `pytest tests/ -v` (must pass all tests, including backward compat test)
  - Verify CI/CD pipeline passes
  - Push to main or feature branch
- **Verification:** `git log --oneline -1` shows new commit; all tests green; dashboard starts without error
- **Effort Note:** 0.5 hours (bulk testing)

---

### Blocker 1.3: Causality Tests + Documentation

**Why:** The pipeline must guarantee no lookahead (future data) leaks into regime assignments. Without automated tests and documentation, downstream users can't trust the model for live trading. This blocker verifies existing tests are sufficient and documents guarantees.

**Dependency:** 1.1 complete  
**Effort:** ~2 hours  
**Calendar Time:** 0.5–1 day  
**Parallelization:** Can run in parallel with 1.4 (after 1.2 complete)

#### Task 1.3.1: Review existing test_causality.py coverage
- **Acceptance:** test_causality.py verified to cover all 3 causality guarantees (no future data in features, standardization, PCA, HMM)
- **Details:**
  - Read tests/test_causality.py in full
  - Map each test to a guarantee:
    - Guarantee 1: expanding_standardize uses only past data (not future)
    - Guarantee 2: PCA fitted incrementally (no future data in fit)
    - Guarantee 3: HMM inference uses filtering (not smoothing) in production
  - Count tests: should be 6+ (2-3 tests per guarantee)
  - Verify each test has clear assertions (e.g., assert future_data not in window)
  - Check test names are descriptive (e.g., `test_expanding_window_no_lookahead`)
  - If coverage gaps exist, note them for Task 1.3.2 documentation (not implementation — per decision D-05)
- **Verification:** Test file is readable; all tests have clear docstrings; pytest runs without error
- **Output:** Mental note of coverage map for Task 1.3.2
- **Commit:** Will be atomic per 1.3.3

#### Task 1.3.2: Update CLAUDE.md hard constraints section with causality guarantees
- **Acceptance:** CLAUDE.md documents causality contract; references test_causality.py
- **Details:**
  - Add new section to CLAUDE.md: "Causality Guarantees (No Lookahead)"
  - Document the 3 guarantees:
    1. **Features:** All features computed using expanding windows (past data only). No fill-forward, no smoothing. Reference: test_causality.py::test_expanding_window_no_lookahead
    2. **Standardization:** Standardization uses expanding window (mean/std computed on past data only). Reference: test_causality.py::test_standardization_uses_past_only
    3. **PCA:** PCA fitted incrementally; new components computed on past data. Reference: test_causality.py::test_pca_fitted_without_future
    4. **HMM Inference:** In production, HMM uses filtering (Kalman-like update) not smoothing. No retrospective regime changes. Reference: test_causality.py::test_hmm_filtering_no_smoothing
  - Add statement: "All causality guarantees are automated in test_causality.py. CI/CD fails if any guarantee is violated. Live trading and backtesting are on equal footing."
  - Add version note: "Last verified: 2026-04-13 against test_causality.py (6 tests, 100% coverage)"
- **Verification:** CLAUDE.md is clear; references are accurate; no broken links (references are file paths)
- **Commit:** Will be atomic per 1.3.3

#### Task 1.3.3: Commit 1.3 work
- **Acceptance:** 1.3.1–1.3.2 complete; causality documented; existing tests still pass
- **Details:**
  - Stage: CLAUDE.md only (test_causality.py is unchanged per D-05)
  - Commit message: `docs: document causality guarantees in CLAUDE.md, reference test_causality.py (blocker 1.3)`
  - Include reference to D-05, D-06 in commit body
  - Run full test suite: `pytest tests/test_causality.py -v` (all 6+ tests must pass)
  - Verify CI/CD pipeline passes
  - Push to main or feature branch
- **Verification:** `git log --oneline -1` shows new commit; test_causality tests green
- **Effort Note:** 0.5 hours (bulk testing)

---

### Blocker 1.4: Integration Test with Algo-Trading-Bot

**Why:** No end-to-end verification that signals work with Algo-Trading-Bot. Without integration tests, incompatibilities (schema, labels, timing) surface in production. This blocker creates automated E2E validation.

**Dependency:** 1.2 complete (requires LABEL_MAPPING and bot_label output)  
**Effort:** ~6 hours  
**Calendar Time:** 1–2 days  
**Parallelization:** Can run in parallel with 1.3 (after 1.2 complete)

#### Task 1.4.1: Create test_bot_integration.py stub and schema validator
- **Acceptance:** test_bot_integration.py exists with schema validator; validates signal dict structure
- **Details:**
  - Create new file: tests/test_bot_integration.py
  - Define validator function (or use jsonschema):
    ```python
    def validate_signal_schema(signal):
        """Validate signal dict matches bot expected format."""
        required_keys = ['timestamp', 'regime_label', 'regime_probs']
        for key in required_keys:
            assert key in signal, f"Missing required key: {key}"
        assert isinstance(signal['timestamp'], (int, float, datetime)), "timestamp must be datetime-like"
        assert signal['regime_label'] in ['LOW_VOL', 'MED_VOL', 'HIGH_VOL'], f"Invalid regime_label: {signal['regime_label']}"
        assert isinstance(signal['regime_probs'], dict), "regime_probs must be dict"
        assert len(signal['regime_probs']) == 3, "regime_probs must have 3 entries"
        assert abs(sum(signal['regime_probs'].values()) - 1.0) < 1e-6, "regime_probs must sum to 1.0"
        return True
    ```
  - Add imports: pytest, numpy, pandas, necessary pipeline modules (signals, config, features, train)
  - Add docstring to file: "Integration test: regime pipeline → signals → bot validation"
- **Verification:** `python -m pytest tests/test_bot_integration.py::test_schema_validator -v` runs without error (will fail on missing test)
- **Commit:** Will be atomic per 1.4.6

#### Task 1.4.2: Implement mock bot signal handler
- **Acceptance:** test_bot_integration.py has mock bot class that consumes signals
- **Details:**
  - Create MockBotSignalHandler class (or simple function):
    ```python
    class MockBotSignalHandler:
        """Mock Algo-Trading-Bot signal handler for testing."""
        def consume_signal(self, signal):
            validate_signal_schema(signal)
            self.last_signal = signal
            return True
        
        def get_last_signal(self):
            return self.last_signal
    ```
  - Handler should raise ValueError if signal is invalid
  - Add method to get last signal (for assertions in tests)
- **Verification:** `python -c "from tests.test_bot_integration import MockBotSignalHandler; h = MockBotSignalHandler(); print(h)"` works
- **Commit:** Will be atomic per 1.4.6

#### Task 1.4.3: Write 4+ test cases (schema, labels, probabilities, round-trip)
- **Acceptance:** test_bot_integration.py has 4+ test functions; all green
- **Details:**
  - **Test 1: test_signal_schema_valid**
    - Load small sample data (1 year, not 16 years)
    - Run full pipeline: collect → features → train → signals
    - Extract regime signals
    - Call `validate_signal_schema(signal)` for each; assert no exception
  - **Test 2: test_bot_labels_correct**
    - Extract regime signals
    - Check regime_label values: all must be in {LOW_VOL, MED_VOL, HIGH_VOL}
    - Assert no regime_name in output (or only as secondary field)
  - **Test 3: test_regime_probs_valid**
    - Extract regime signals
    - For each signal, check regime_probs:
      - Is dict with 3 keys
      - All values are floats in [0, 1]
      - Sum equals 1.0 (within 1e-6 tolerance)
  - **Test 4: test_bot_handler_round_trip**
    - Extract regime signals
    - Create MockBotSignalHandler
    - Feed each signal to handler.consume_signal(signal)
    - Assert no exception
    - Assert handler.get_last_signal() matches
  - **Optional Test 5: test_signal_timestamp_sequential**
    - Extract regime signals
    - Assert timestamps are monotonically increasing
    - Assert no gaps in timestamps (1-day intervals)
  - Each test should have:
    - Clear docstring explaining what it validates
    - Assertions with helpful error messages
    - Data fixture (small dataset, <1 min to run)
- **Verification:** `pytest tests/test_bot_integration.py -v` shows 4+ PASSED
- **Commit:** Will be atomic per 1.4.6

#### Task 1.4.4: Add integration test to CI/CD pipeline
- **Acceptance:** CI/CD runs test_bot_integration.py; fails if any test fails
- **Details:**
  - Update CI/CD config (.github/workflows/tests.yml or equivalent)
  - Add step: `pytest tests/test_bot_integration.py -v`
  - Place after causality tests (depends on test_causality.py passing)
  - Ensure integration test is included in main test suite (not skipped)
- **Verification:** Create a dummy PR and watch CI/CD trigger integration test
- **Commit:** Will be atomic per 1.4.6

#### Task 1.4.5: Verify <5 min execution time
- **Acceptance:** Integration test runs in <5 min (verified locally and in CI/CD)
- **Details:**
  - Time the full test locally: `time pytest tests/test_bot_integration.py -v`
  - Should be <5 min (typically 1–2 min with small data sample)
  - If slower, optimize:
    - Use even smaller data sample (e.g., 6 months instead of 1 year)
    - Cache model checkpoint (pre-trained, not re-trained)
    - Reduce number of HMM inference steps
  - Document any optimizations in test docstring
  - Record timing in test output or CI/CD logs
- **Verification:** `time pytest tests/test_bot_integration.py -v` shows <5 min total
- **Commit:** Will be atomic per 1.4.6

#### Task 1.4.6: Commit 1.4 work
- **Acceptance:** All 1.4.1–1.4.5 complete; integration test runs green in CI/CD
- **Details:**
  - Stage: tests/test_bot_integration.py, CI/CD config file
  - Commit message: `test: add test_bot_integration.py with schema validator and 4+ test cases (blocker 1.4)`
  - Include reference to D-07, D-08 in commit body
  - Run full test suite: `pytest tests/ -v` (must pass all 28+ tests plus new 4+ integration tests)
  - Verify CI/CD pipeline passes (including integration test)
  - Verify integration test time <5 min in CI/CD logs
  - Push to main or feature branch
- **Verification:** `git log --oneline -1` shows new commit; all tests (including integration) green; CI/CD shows <5 min runtime
- **Effort Note:** 0.5 hours (bulk testing)

---

## Execution Sequence

### Wave 1: JAX/NumPyro Reproducibility (Blocker 1.1)
**Status:** Unblocked  
**Timeline:** Day 1, hours 1–3  
**Tasks:** 1.1.1 → 1.1.2 → 1.1.3 → 1.1.4 (sequential)

- [ ] 1.1.1 — Resolve requirements.txt merge conflict
- [ ] 1.1.2 — Add CI/CD pin-check step
- [ ] 1.1.3 — Update CLAUDE.md with reproducibility note
- [ ] 1.1.4 — Commit 1.1 work (all tests pass)
- **Gate:** Wave 1 complete before Wave 2 starts (1.2 depends on clean 1.1 commit)

### Wave 2: Bot Label Mapping (Blocker 1.2)
**Status:** Blocked until Wave 1 complete  
**Timeline:** Day 2–3, hours 4–10  
**Tasks:** 1.2.1 → 1.2.2 → 1.2.3 → 1.2.4 → 1.2.5 → 1.2.6 (sequential)

- [ ] 1.2.1 — Add LABEL_MAPPING to config.py
- [ ] 1.2.2 — Update signals.py to use LABEL_MAPPING
- [ ] 1.2.3 — Update dashboard to display both labels
- [ ] 1.2.4 — Update CLAUDE.md with label convention
- [ ] 1.2.5 — Test backward compatibility
- [ ] 1.2.6 — Commit 1.2 work (all tests pass)
- **Gate:** Wave 2 complete before Wave 3 starts (1.4 depends on bot_label output)

### Wave 3a: Causality Tests + Documentation (Blocker 1.3)
**Status:** Blocked until Wave 1 complete; **can run parallel with 1.4 after Wave 2**  
**Timeline:** Day 3–4, hours 10–12  
**Tasks:** 1.3.1 → 1.3.2 → 1.3.3 (sequential)

- [ ] 1.3.1 — Review existing test_causality.py coverage
- [ ] 1.3.2 — Update CLAUDE.md with causality guarantees
- [ ] 1.3.3 — Commit 1.3 work (causality tests pass)

### Wave 3b: Integration Test (Blocker 1.4)
**Status:** Blocked until Wave 2 complete  
**Timeline:** Day 3–4, hours 11–17 (parallel with 1.3, after 1.2)  
**Tasks:** 1.4.1 → 1.4.2 → 1.4.3 → 1.4.4 → 1.4.5 → 1.4.6 (sequential)

- [ ] 1.4.1 — Create test_bot_integration.py stub and schema validator
- [ ] 1.4.2 — Implement mock bot signal handler
- [ ] 1.4.3 — Write 4+ test cases
- [ ] 1.4.4 — Add integration test to CI/CD pipeline
- [ ] 1.4.5 — Verify <5 min execution time
- [ ] 1.4.6 — Commit 1.4 work (all integration tests pass)

**Parallelization:** 1.3 and 1.4 can run in parallel once their respective dependencies (1.1 for 1.3, 1.2 for 1.4) are complete. No shared resources.

---

## Dependencies Graph

```
1.1 (JAX pinning)
  ↓ (gate)
1.2 (Bot labels)
  ├→ (gate) 1.3 (Causality docs) [parallel]
  └→ (gate) 1.4 (Integration test) [parallel]
```

---

## Success Criteria

### Requirements Covered (from REQUIREMENTS.md)

- [ ] **R4: Reproducibility** — requirements.txt pins jax/numpyro exactly; CI/CD rejects loose constraints
- [ ] **R2: Bot Label Mapping** — LABEL_MAPPING in config.py; signals include bot_label; dashboard shows both
- [ ] **R3: Causal Pipeline** — test_causality.py passes all 6+ tests; CLAUDE.md documents guarantees
- [ ] **R5: Integration with Algo-Trading-Bot** — test_bot_integration.py validates schema; 4+ tests green; <5 min runtime

### Code Quality

- [ ] All 28+ existing tests still pass (no regressions)
- [ ] New 4+ integration tests pass
- [ ] All 6+ causality tests pass
- [ ] Code review approved (domain expert confirms causality, label mapping, and JAX pinning are correct)
- [ ] No new warnings or linting errors

### Documentation

- [ ] CLAUDE.md hard constraints section updated with reproducibility note
- [ ] CLAUDE.md causality guarantees section added with test references
- [ ] CLAUDE.md bot integration section documents label mapping
- [ ] All commit messages reference decisions (D-01 through D-09)

### CI/CD & Deployability

- [ ] requirements.txt merge conflict resolved
- [ ] CI/CD pin-check step in place and rejecting loose constraints
- [ ] CI/CD runs full test suite (35+ tests) successfully
- [ ] Integration test runs in <5 min in CI/CD logs
- [ ] No failing checks on main branch

---

## Atomic Commits (4 total)

Each commit is self-contained and can be reverted independently.

### Commit 1: JAX/NumPyro Version Pinning
**Subject:** `fix: pin jax==0.4.35 numpyro==0.20.0, add CI/CD validation (blocker 1.1)`

**Body:**
```
Closes blocker 1.1: Tighten JAX/NumPyro version pinning for reproducibility.

Decisions implemented:
- D-01: Exact version pins in requirements.txt (jax==0.4.35, numpyro==0.20.0)
- D-02: CI/CD step rejects PRs with loose constraints (>= operator)

Changes:
- requirements.txt: Resolve merge conflict, accept exact pinning
- CI/CD config: Add pin-check step (grep for >= on jax/numpyro lines)
- CLAUDE.md: Add reproducibility guarantee note

Verification:
- All 28+ tests pass
- CI/CD pin-check passes
- No regime label changes (same model, same data)

References: REQUIREMENTS.md R4 (Reproducibility)
```

### Commit 2: Bot Label Mapping + Validation
**Subject:** `feat: add LABEL_MAPPING config, update signals output with bot_label (blocker 1.2)`

**Body:**
```
Closes blocker 1.2: Implement bot label mapping + validation.

Decisions implemented:
- D-03: LABEL_MAPPING dict in config.py (Low-Vol → LOW_VOL, etc.)
- D-04: Dashboard displays both internal names and bot labels
- D-09: Backward compatibility in signals.py output (add new fields, don't rename)

Changes:
- config.py: Add LABEL_MAPPING dict with 3-regime mapping
- signals.py: Add bot_label field to signal output using LABEL_MAPPING
- dashboard.py: Display both regime_name and bot_label in UI
- CLAUDE.md: Document label convention and bot integration

Verification:
- All 28+ tests pass (backward compatible)
- signals.py includes both regime_name (internal) and bot_label (canonical)
- Dashboard renders both labels without crashes
- No breaking changes to existing signal consumers

References: REQUIREMENTS.md R2 (Bot Label Mapping)
```

### Commit 3: Causality Tests + Documentation
**Subject:** `docs: document causality guarantees in CLAUDE.md, reference test_causality.py (blocker 1.3)`

**Body:**
```
Closes blocker 1.3: Add causal pipeline tests + documentation.

Decisions implemented:
- D-05: Keep existing test_causality.py coverage (6 tests, 3 guarantees)
- D-06: Document causality contract in CLAUDE.md with test references

Changes:
- CLAUDE.md: Add "Causality Guarantees" section with 3 guarantees and test references
  1. Features: expanding windows (no lookahead)
  2. Standardization: expanding windows (no future data)
  3. PCA: fitted without future data
  4. HMM: filtering not smoothing in production
- References each guarantee to specific test in test_causality.py

Verification:
- All 6+ causality tests pass
- CLAUDE.md clearly states causality contract
- Downstream users (Algo-Trading-Bot, Portfolio-Manager) can trust no-lookahead guarantee
- CI/CD enforces causality tests (fail if violated)

References: REQUIREMENTS.md R3 (Causal Pipeline)
```

### Commit 4: Integration Test with Algo-Trading-Bot
**Subject:** `test: add test_bot_integration.py with schema validator and 4+ test cases (blocker 1.4)`

**Body:**
```
Closes blocker 1.4: Create integration test with Algo-Trading-Bot.

Decisions implemented:
- D-07: test_bot_integration.py with schema validator + mock bot handler
- D-08: Integration test runs <5 min and passes on CI/CD

Changes:
- tests/test_bot_integration.py: New file with:
  - validate_signal_schema() function
  - MockBotSignalHandler class
  - 4+ test cases: schema validation, label correctness, prob validation, round-trip
- CI/CD config: Add integration test step (after causality tests)

Verification:
- All 4+ integration tests pass
- Signal schema matches bot expected format (timestamp, regime_label, regime_probs)
- regime_label values are {LOW_VOL, MED_VOL, HIGH_VOL}
- regime_probs are valid (3 floats, sum to 1.0)
- Integration test runs <5 min in CI/CD
- All 28+ existing tests still pass (no regressions)

References: REQUIREMENTS.md R5 (Integration with Algo-Trading-Bot)
```

---

## Effort Summary

| Blocker | Tasks | Effort | Calendar Time | Owner |
|---------|-------|--------|---------------|-------|
| 1.1 (JAX pinning) | 1.1.1–1.1.4 | 3 hrs | 1 day | Adam |
| 1.2 (Bot labels) | 1.2.1–1.2.6 | 6 hrs | 1–2 days | Adam |
| 1.3 (Causality docs) | 1.3.1–1.3.3 | 2 hrs | 0.5–1 day | Adam |
| 1.4 (Integration test) | 1.4.1–1.4.6 | 6 hrs | 1–2 days | Adam |
| **Phase 1 Total** | **18 tasks** | **17 hrs** | **3–5 days** | Adam |

**Parallelization:** 1.3 and 1.4 run in parallel after 1.2, saving ~0.5–1 day calendar time.  
**Total calendar time:** 3–5 days (with parallelization and code review).

---

## Testing Strategy

### Pre-commit Testing (per task)
- Each task has its own verification step (local pytest, visual check, etc.)
- Tasks can only proceed if verification passes

### Post-Wave Testing (before gate opens)
- After each wave, run full test suite: `pytest tests/ -v`
- After Wave 1: 28+ tests must pass (baseline maintained)
- After Wave 2: 28+ tests + backward compat test must pass
- After Wave 3a: 28+ tests + causality tests must pass
- After Wave 3b: 28+ tests + integration tests must pass

### CI/CD Validation
- Each commit triggers CI/CD pipeline
- Pipeline must include: linting, all tests (28+ existing + new), integration test
- Integration test must complete in <5 min
- CI/CD must pass before merge to main

### Code Review
- Domain expert reviews all commits
- Focus areas:
  - Causality guarantees (no future data leaks)
  - Label mapping correctness (bot schema match)
  - JAX pinning necessity (reproducibility)
  - Test coverage (4+ integration tests sufficient)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| requirements.txt merge conflict causes failures | Resolve conflict early (1.1.1); verify all tests pass immediately after (1.1.4) |
| CI/CD pin-check too strict (false positives) | Test with dummy PR before merging (1.1.2 verification step) |
| Bot label mapping breaks existing consumers | Keep regime_name field (backward compatible per D-09); add bot_label as new field |
| test_bot_integration.py too slow | Use small data sample (1 year); cache model; verify <5 min upfront (1.4.5) |
| Causality tests miss lookahead bug | Review test_causality.py thoroughly (1.3.1); reference each guarantee in CLAUDE.md (1.3.2) |
| Integration test fails silently in CI/CD | Add clear assertions with error messages; test locally first (1.4.3) |

---

## Rollback Plan

If any commit fails CI/CD or code review:
1. Identify which commit failed (e.g., Commit 2 for label mapping)
2. Revert just that commit: `git revert <commit-hash>`
3. Fix the issue in a new branch
4. Re-commit with same message (new commit hash)
5. CI/CD validates new commit
6. Merge to main

All commits are atomic and can be reverted independently (no cross-dependencies except in sequence order).

---

## Hand-Off Checklist (for developer)

Before starting Phase 1 execution:
- [ ] Read this PLAN.md in full
- [ ] Read 01-CONTEXT.md to understand decisions D-01 through D-09
- [ ] Read REQUIREMENTS.md and ROADMAP.md
- [ ] Read CLAUDE.md hard constraints
- [ ] Clone/pull latest main branch from GitHub
- [ ] Verify local environment: `pytest tests/ -v` (all 28+ tests pass)
- [ ] Verify requirements.txt has merge conflict (expected)
- [ ] Have editor open to requirements.txt, config.py, signals.py, dashboard.py, CLAUDE.md, CI/CD config
- [ ] Have test runner open to watch tests: `pytest tests/ -v --tb=short`
- [ ] Slack/Discord ready to log blockers if any task fails

---

## Key References

| Resource | Purpose |
|----------|---------|
| `.planning/phases/01-blockers/01-CONTEXT.md` | Decisions D-01 through D-09 (locked context) |
| `.planning/ROADMAP.md` | Phase 1 specification and UAT criteria |
| `.planning/REQUIREMENTS.md` | Functional and non-functional requirements |
| `CLAUDE.md` (project root) | Hard constraints and downstream integration notes |
| `requirements.txt` | JAX/NumPyro versions (merge conflict to resolve) |
| `config.py` | REGIME_NAMES and new LABEL_MAPPING |
| `signals.py` | Signal output format (add bot_label) |
| `dashboard.py` | UI display (show both labels) |
| `tests/test_causality.py` | Existing causality tests (reference in docs) |
| `.github/workflows/` | CI/CD pipeline (add pin-check and integration test steps) |

---

## Notes for Developer

### Decision Rationale

- **D-01 (Exact pinning):** Trading requires bit-for-bit reproducibility. Version ranges silently break regime labels.
- **D-02 (CI/CD check):** Prevents accidental regression to loose constraints.
- **D-03, D-04 (Label mapping):** Algo-Trading-Bot expects uppercase/underscore labels. Mapping is single source of truth.
- **D-09 (Backward compat):** Keep existing field names; add new fields. No breaking changes for existing consumers.
- **D-05, D-06 (Causality):** Existing tests are sufficient; just document them. No need to write new tests.
- **D-07, D-08 (Integration):** Mock bot handler keeps test self-contained. Small data sample keeps execution <5 min.

### Common Pitfalls

1. **Forgetting backward compatibility:** Keep `regime_name` field in signals; don't rename it to `bot_label_internal`.
2. **Loose version pinning:** Use `==` only. If code review suggests `>=0.4.30,<1.0`, refuse it (non-negotiable per decision).
3. **Integration test too slow:** Use 1-year sample, not 16 years. Pre-train model if possible.
4. **Causality docs vague:** Reference specific test names (e.g., `test_expanding_window_no_lookahead`). Readers should be able to find the test.
5. **Missing test assertions:** Each integration test should have clear error messages. "Expected LOW_VOL, got LOW_vol" is unhelpful; say why.

### Time Estimates by Task

| Task | Hours | Notes |
|------|-------|-------|
| 1.1.1 | 0.5 | Merge conflict resolution |
| 1.1.2 | 1 | CI/CD script (simple grep) |
| 1.1.3 | 0.5 | Update docs |
| 1.1.4 | 0.5 | Test run + commit |
| 1.2.1 | 0.5 | Add dict to config |
| 1.2.2 | 1.5 | Update signals output, validate |
| 1.2.3 | 1 | Update dashboard UI |
| 1.2.4 | 0.5 | Update docs |
| 1.2.5 | 1 | Backward compat testing |
| 1.2.6 | 0.5 | Test run + commit |
| 1.3.1 | 0.5 | Code review (test_causality.py) |
| 1.3.2 | 1 | Update CLAUDE.md |
| 1.3.3 | 0.5 | Test run + commit |
| 1.4.1 | 1 | Create test file + schema validator |
| 1.4.2 | 1 | Mock bot handler class |
| 1.4.3 | 2 | Write 4+ test cases |
| 1.4.4 | 0.5 | Update CI/CD config |
| 1.4.5 | 0.5 | Time integration test |
| 1.4.6 | 0.5 | Test run + commit |
| **Total** | **17 hrs** | **Phase 1 complete** |

---

**Phase 1: Fix Critical Blockers is ready for execution.**

Next step: Begin Wave 1 (Blocker 1.1) execution.

