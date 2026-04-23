---
phase: 7
slug: daily-pipeline-clean-outputs
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-21
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (160+ tests already passing) |
| **Config file** | none detected — uses default pytest discovery |
| **Quick run command** | `pytest tests/ -m "not slow" -x --tb=short` |
| **Full suite command** | `pytest tests/ -x --tb=short` |
| **Slow suite command** | `pytest tests/ --tb=short` (includes timing + idempotency) |
| **Estimated runtime** | ~30 seconds (quick), ~10 min (full with slow tests) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -m "not slow" -x --tb=short`
- **After every plan wave:** Run `pytest tests/ -x --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green (including slow tests)
- **Max feedback latency:** 30 seconds (quick run)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline_stages.py -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline_stages.py -x` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline_stages.py -x` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 1 | PIPE-01 | integration slow | `pytest tests/test_pipeline_timing.py -m slow` | ❌ W0 | ⬜ pending |
| 07-01-05 | 01 | 1 | PIPE-01 | integration slow | `pytest tests/test_pipeline_idempotent.py -m slow` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | PIPE-01/02 | integration | `pytest tests/test_output_count.py -x` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 1 | PIPE-01 | integration | `pytest tests/test_exit_codes.py -x` | ❌ W0 | ⬜ pending |
| 07-02-03 | 02 | 1 | PIPE-01 | unit | `pytest tests/ -m "not slow" -k health_check -x` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 2 | PIPE-03 | unit | `pytest tests/test_regime_results_schema.py -x` | ❌ W0 | ⬜ pending |
| 07-03-02 | 03 | 2 | PIPE-03 | integration | `pytest tests/test_regime_results_freshness.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_pipeline_stages.py` — stubs for PIPE-01 stage isolation
- [ ] `tests/test_pipeline_timing.py` — stub for PIPE-01 timing gate (mark @pytest.mark.slow)
- [ ] `tests/test_pipeline_idempotent.py` — stub for PIPE-01/03 idempotency (mark @pytest.mark.slow)
- [ ] `tests/test_output_count.py` — stub for PIPE-02 exactly-2-HTML
- [ ] `tests/test_exit_codes.py` — stub for PIPE-01 exit code contract
- [ ] `tests/test_regime_results_schema.py` — stub for PIPE-03 schema columns
- [ ] `tests/test_regime_results_freshness.py` — stub for PIPE-03 freshness

*Wave 0 test stubs should import the target modules and fail with NotImplementedError or ImportError — RED phase. Implementation makes them GREEN.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `python scripts/run.py` completes in <10 min on live data | PIPE-01 | Requires live market data fetch; `@pytest.mark.slow` test covers it but needs live env | Run `time python scripts/run.py` on dev machine with live data |
| `python scripts/health_check.py` prints PASS after a run | PIPE-03 | Requires live pipeline run to produce fresh regime_results.csv | Run pipeline, then run health_check.py, verify PASS output |
| `scripts/cron_run.sh` executes without error on target machine | PIPE-01 | Shell script; requires venv path correct for target OS | Run `bash scripts/cron_run.sh` on target machine |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s (quick run)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
