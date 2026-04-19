---
phase: 5
slug: feature-engineering-overhaul
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
updated: 2026-04-18
---

> **Nyquist compliance semantics (clarified in revision iter1):**
> The phase-level `nyquist_compliant: false` and `wave_0_complete: false` in
> the frontmatter reflect EXECUTION STATE - as of plan creation, Wave 0 has
> not yet run, so the test stubs do not yet exist on disk. Each plan's
> frontmatter carries `nyquist_compliant: true` which reflects PLANNING
> INTENT - the plans commit to creating the Wave 0 stubs (Plan 01) and turning
> them green (Plans 03, 04). No conflict. These fields flip to `true` in
> this file after Plan 01 executes (per the phase sign-off checklist below).


# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (160+ existing tests) |
| **Config file** | pytest.ini or pyproject.toml (existing) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | FEAT-01 | — | FRED_API_KEY from env var, not hardcoded | unit | `pytest tests/test_section_signals.py::test_build_section_signals_returns_4_columns -x` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | FEAT-01 | — | New FRED features present in expanded feature matrix | unit | `pytest tests/test_features.py::test_fred_features -x` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | FEAT-02 | — | Section PCA not fitted on test-fold data | unit | `pytest tests/test_walk_forward.py::test_no_lookahead -x` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | FEAT-02 | — | MI computed on train fold only | unit | `pytest tests/test_walk_forward.py::test_mi_train_only -x` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 3 | FEAT-03 | — | Selection frequency table present in report | integration | `pytest tests/test_walk_forward.py::test_report_written -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_section_signals.py` — stubs for FEAT-01 (build_section_signals columns, sign anchoring)
- [ ] `tests/test_walk_forward.py` — stubs for FEAT-02 (causal guarantee, MI train-only) and FEAT-03 (report written)
- [ ] `tests/test_features.py::test_fred_features` — stub for FEAT-01 FRED feature presence

*Existing infrastructure (pytest + conftest.py) covers framework setup — no new installs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| FRED API key set in environment | FEAT-01 | Requires user to obtain free key at fred.stlouisfed.org | Run `python -c "from fredapi import Fred; Fred().get_series('T10Y2Y', observation_start='2024-01-01')"` and verify non-empty result |
| feature_importance_report.md economic rationale is correct | FEAT-03 | Prose content requires human judgment | Read data/feature_importance_report.md and verify each selected section has 1+ sentence of rationale |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
