---
phase: 6
slug: model-architecture-experiments
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-20
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini / pyproject.toml |
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
| 06-01-01 | 01 | 1 | MODEL-02 | — | N/A | unit | `pytest tests/ -k "hdp" -q` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | MODEL-02 | — | N/A | unit | `pytest tests/ -k "hdp" -q` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | MODEL-03 | — | N/A | unit | `pytest tests/ -k "refactor" -q` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | MODEL-03 | — | N/A | unit | `pytest tests/ -k "refactor" -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_hdp_decision.py` — stubs for MODEL-02 (HDP comparison + deprecation)
- [ ] `tests/test_train_refactor.py` — stubs for MODEL-03 (module line count checks)
- [ ] Existing pytest infrastructure — already installed

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| USE_HDP documentation reviewed | MODEL-02 | Requires human judgment on decision quality | Review ADR file for completeness and clarity |
| OOS regime accuracy comparison | MODEL-02 | Statistical validity requires visual inspection | Run comparison script, review metrics table |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
