---
phase: 01-blockers
reviewed: 2026-04-13T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - config.py
  - signals.py
  - tests/test_bot_integration.py
  - CLAUDE.md
  - requirements.txt
  - .github/workflows/tests.yml
  - dashboard.py
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase 01-blockers Code Review Report

**Reviewed:** 2026-04-13
**Depth:** standard
**Files Reviewed:** 7
**Status:** Issues Found

## Summary

Phase 1-blockers implementation adds bot label mapping, version pinning, causality guarantees, and integration tests. Core functionality is sound: all 33 tests pass, CI/CD workflow is properly configured, and reproducibility guarantees are enforced. However, there is **one critical design gap** in LABEL_MAPPING coverage that could cause runtime failures if regime configuration is changed, and one medium-severity configuration mismatch that violates the documented architecture.

All version pinning is correct and properly enforced. Causality documentation is accurate and well-tested. Integration tests are comprehensive and validate the actual signal schema. The code quality is high, with proper error handling and type validation.

## Critical Issues

### CR-01: Incomplete LABEL_MAPPING — Missing Regime Names

**File:** `config.py:102-106, signals.py:537-542`

**Issue:**

The `LABEL_MAPPING` dictionary only covers 3 regime labels:
```python
LABEL_MAPPING = {
    'Low-Vol': 'LOW_VOL',
    'Medium-Vol': 'MED_VOL',
    'High-Vol': 'HIGH_VOL',
}
```

However, the codebase can produce other regime names from `REGIME_NAMES` (line 91-96) and `VOL_BRACKETS` (line 112-117):
- `REGIME_NAMES[4]` = `['Low-Vol', 'Moderate', 'Elevated', 'Crisis']`
- `VOL_BRACKETS` produces names like `'Moderate-Vol'`, `'Elevated-Vol'`, `'Crisis-Vol'`
- The walk-forward training code (train.py:657) appends suffixes like `-B`, `-C` to disambiguate duplicate names

If the model produces any regime name NOT in LABEL_MAPPING (e.g., 'Moderate', 'Elevated', 'Crisis-Vol'), `compute_signals()` will raise:
```
KeyError: "Regime 'Moderate' not in LABEL_MAPPING. Valid regimes: ['Low-Vol', 'Medium-Vol', 'High-Vol']"
```

This causes production signal generation to crash at runtime, violating the guarantee that regime signal output is always valid.

**Root Cause:**

The LABEL_MAPPING was designed for the 3-regime case only (matching Algo-Trading-Bot expectations), but the code's configuration allows multiple regime states without updating the mapping.

**Fix:**

Add all possible regime names to LABEL_MAPPING. Since the architecture specifies "3 regime target" (CLAUDE.md line 33), either:

**Option A (Recommended):** Enforce 3-regime constraint at config load time
```python
# In config.py, after LABEL_MAPPING
assert N_STATES == 3, (
    "Only 3-regime models are supported for bot integration. "
    "N_STATES must be 3. See CLAUDE.md: '3 regime target'."
)
```

**Option B:** Expand LABEL_MAPPING to cover all possible regimes
```python
LABEL_MAPPING = {
    # Classic 2-state
    'Low-Vol': 'LOW_VOL',
    'High-Vol': 'HIGH_VOL',
    
    # HDP 3-state (primary)
    'Medium-Vol': 'MED_VOL',
    
    # HDP 4+ state
    'Moderate': 'MED_VOL',
    'Moderate-Vol': 'MED_VOL',
    'Elevated': 'HIGH_VOL',
    'Elevated-Vol': 'HIGH_VOL',
    'Crisis': 'HIGH_VOL',
    'Crisis-Vol': 'HIGH_VOL',
    'Very-Low': 'LOW_VOL',
}
```
(With variants for suffixes like `'Moderate-B'` → `'MED_VOL'`)

**Severity:** CRITICAL — Production signal generation will crash if regime configuration is changed.

---

## Warnings

### WR-01: Configuration Mismatch — N_STATES Default vs Architecture Specification

**File:** `config.py:52`

**Issue:**

```python
N_STATES = 4               # default if BIC is skipped
```

But CLAUDE.md (lines 7, 33) specifies:
```
HDP-HMM market regime detection from macro and price features. Produces regime labels
(3 regimes expected) consumed downstream by Algo-Trading-Bot and Portfolio-Manager.
...
- 3 regime target: match labels to Algo-Trading-Bot convention when integrating
```

This mismatch means:
1. If someone runs the code with default config, it will use 4 states instead of the documented 3
2. The 4-state regime names (`'Low-Vol'`, `'Moderate'`, `'Elevated'`, `'Crisis'`) won't map to LABEL_MAPPING (see CR-01 above)
3. New users reading the default config value will be confused about the actual architecture constraint

**Fix:**

Change N_STATES default to 3 to match the documented target:
```python
N_STATES = 3               # 3-regime target for Algo-Trading-Bot integration (see CLAUDE.md)
```

And add a comment explaining why:
```python
# CRITICAL: Must be 3 for Algo-Trading-Bot integration.
# LABEL_MAPPING only covers Low-Vol, Medium-Vol, High-Vol.
# BIC search range [2, 3, 4] can explore other sizes, but final model must use 3.
```

**Severity:** WARNING — Violates documented architecture; could cause CR-01 to manifest in production.

---

## Info

None.

---

## Detailed Findings

### ✓ Version Pinning (PASSED)

- `requirements.txt`: All dependencies use exact `==` pins ✓
- JAX==0.9.1, NumPyro==0.20.0, jaxlib==0.9.1 all correctly pinned
- CI/CD check-version-pins job correctly enforces `==` operator and rejects `>=` ✓
- Comment at top of requirements.txt explains reproducibility rationale ✓

**Status:** No issues found.

### ✓ Bot Label Mapping Structure (PASSED)

- `LABEL_MAPPING` defined in config.py as source of truth ✓
- `signals.py` correctly imports LABEL_MAPPING ✓
- `compute_signals()` validates regime_name before mapping (line 537) ✓
- Error message provides helpful context (lines 539-540) ✓
- Backward compatibility: `current_regime` field preserved; `bot_label` is additive ✓

**Status:** No issues found in structure; see CR-01 for incomplete coverage.

### ✓ Integration Tests (PASSED)

Test file: `tests/test_bot_integration.py` (362 lines)

- Schema validator handles actual signal structure ✓
- Tests cover all required validations:
  - bot_label in {LOW_VOL, MED_VOL, HIGH_VOL} (test_bot_labels_correct) ✓
  - regime_probs dict has 3 keys, sums to 1.0 (test_regime_probs_valid) ✓
  - Signal schema matches bot expectations (test_signal_schema_valid) ✓
  - Mock handler round-trip works (test_bot_handler_round_trip) ✓
  - Date field present and parseable (test_signal_date_field) ✓
- All 5 tests pass ✓
- Execution time: 3.27s (well under 5-min requirement) ✓
- Fixture correctly generates 3-regime data matching LABEL_MAPPING ✓

**Status:** No issues found; tests are well-written and comprehensive.

### ✓ CI/CD Workflow (PASSED)

File: `.github/workflows/tests.yml`

- check-version-pins job runs first and blocks if loose constraints found ✓
- Explicitly runs causality tests before integration tests ✓
- Error message references CLAUDE.md hard constraints ✓
- Python 3.10 specified ✓
- Dependency installation is clean ✓

**Status:** No issues found.

### ✓ Documentation (PASSED)

File: `CLAUDE.md`

- Hard Constraints section documents JAX/NumPyro pinning requirement ✓
- Bot Integration section documents label mapping convention ✓
- Causality Guarantees section documents 6 guarantees with test references ✓
- Specifies "3 regime target" (line 33) ✓
- References LABEL_MAPPING as source of truth (line 52) ✓

**Status:** No issues found in documentation.

### ✓ Error Handling (PASSED)

- `compute_signals()` raises KeyError with helpful message if regime not in LABEL_MAPPING (lines 537-541) ✓
- Mock bot handler catches AssertionError and re-raises as ValueError with context (test_bot_integration.py:142-145) ✓
- Schema validator uses assert with descriptive messages ✓
- No silent failures or swallowed exceptions ✓

**Status:** No issues found.

### ✓ Type Safety (PASSED)

- `compute_signals()` function signature uses type hints ✓
- MockBotSignalHandler methods have return type annotations ✓
- validate_signal_schema() has type hint on signal parameter ✓
- No bare `except:` clauses (test_bot_integration.py:142 catches AssertionError specifically) ✓

**Status:** No issues found.

---

## Test Execution Summary

```
All Tests: 33 passed in 9.58s ✓
  - Integration tests: 5 passed in 3.27s ✓
  - Causality tests: 10 passed in 8.98s ✓
  - Other validation tests: 18 passed ✓

No test failures.
```

---

## Security Assessment

### Threat Model Coverage

| Threat | Category | Mitigation | Status |
|--------|----------|-----------|--------|
| Version tampering | Tampering | Exact == pins in requirements.txt; CI/CD rejects loose constraints | ✓ |
| Regime label mismatch | Integrity | KeyError raised if mapping missing; schema validator tests bot_label format | ⚠️ (incomplete coverage) |
| Lookahead in features | Causality | Expanding windows, filtered inference, test_causality.py with 10 tests | ✓ |
| Bot signal format | Integration | Schema validator, 5 integration tests, mock handler | ✓ |

**Status:** Security posture is strong except for CR-01 (incomplete LABEL_MAPPING coverage).

### Secrets/Credentials

- No hardcoded API keys, passwords, or tokens found ✓
- No database connection strings ✓
- No AWS/GCP credentials ✓

**Status:** Clean.

---

## Code Quality Assessment

### Strengths

1. **Well-documented:** Docstrings explain purpose and return values clearly
2. **Type-annotated:** Modern Python type hints throughout
3. **Comprehensive testing:** Integration tests validate end-to-end flow
4. **Proper error handling:** Meaningful error messages aid debugging
5. **Backward compatible:** New bot_label field doesn't break existing code
6. **CI/CD enforcement:** Version pinning is automatically validated on every PR

### Weaknesses

1. **Incomplete mapping coverage (CR-01):** LABEL_MAPPING doesn't cover all possible regime names
2. **Configuration mismatch (WR-01):** N_STATES default doesn't match architecture spec
3. **No defensive validation:** Code doesn't verify regime names at load time

---

## Recommendations

**Immediate (Pre-Release):**

1. **Fix CR-01:** Choose either Option A (enforce 3-regime constraint) or Option B (expand LABEL_MAPPING)
2. **Fix WR-01:** Change N_STATES default to 3

**Short-term (Next Sprint):**

1. Add unit test case that exercises non-mapped regime names to catch this earlier
2. Add config validation at startup to ensure N_STATES == 3

**Long-term (Post-Release):**

1. Consider refactoring LABEL_MAPPING to be more flexible if multi-regime support is planned
2. Document the 3-regime constraint more prominently in README.md

---

## Verification Commands

All tests pass:
```bash
pytest tests/ -v --tb=short
# Output: 33 passed in 9.58s ✓

pytest tests/test_bot_integration.py -v
# Output: 5 passed in 3.27s ✓

grep "jax==" requirements.txt
# Output: jax==0.9.1 ✓
```

---

_Reviewed: 2026-04-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
