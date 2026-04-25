---
phase: 07-daily-pipeline-clean-outputs
plan: "02"
subsystem: pipeline
tags: [pipeline, cron, logging, cleanup, exit-codes, wave-2]
dependency_graph:
  requires:
    - 07-01: Pipeline runner (run_all, run_stage, run_from hook points)
  provides:
    - src/pipeline/runner.py: _cleanup_figures() + _setup_logging() module-level helpers
    - scripts/cron_run.sh: Cron shell wrapper with venv activation + exit-code logging
    - scripts/health_check.py: regime_results.csv freshness PASS/FAIL gate
  affects:
    - scripts/run.py: top-level try/except wraps main() dispatch for safe exit propagation
tech_stack:
  added:
    - logging.handlers.RotatingFileHandler (stdlib)
    - glob (stdlib, for figures cleanup)
  patterns:
    - Pre-run HTML cleanup via glob.glob('figures/*.html') before stage loop
    - RotatingFileHandler 10MB/3-backup log rotation capping total log at ~40MB
    - Duplicate-handler guard (isinstance check) for safe repeated invocation
    - try/except SystemExit + re-raise pattern for clean exit-code propagation
    - Cron venv detection: Windows .venv/Scripts/activate or Unix .venv/bin/activate
key_files:
  created:
    - scripts/cron_run.sh
    - scripts/health_check.py
  modified:
    - src/pipeline/runner.py
    - scripts/run.py
decisions:
  - "cleanup scoped to figures/*.html only (no recursion, no other extensions) — satisfies T-07-05 glob tampering threat"
  - "RotatingFileHandler maxBytes=10MB backupCount=3 caps total log disk at ~40MB — satisfies T-07-06 DoS threat"
  - "cron_run.sh logs exit code to cron_run.log separate from pipeline.log — satisfies T-07-07 repudiation threat"
  - "health_check.py MAX_STALENESS_DAYS=5 chosen as 3 trading days + weekend tolerance"
  - "SystemExit re-raise pattern preserves pipeline's sys.exit(1) without swallowing"
metrics:
  duration: "3 minutes"
  completed: "2026-04-25"
  tasks_completed: 3
  files_created: 2
  files_modified: 2
  tests_added: 0
---

# Phase 07 Plan 02: Cron-Readiness & Clean Outputs Summary

**One-liner:** Pre-run figures cleanup, 10MB rotating pipeline log, cron shell wrapper (Windows+Unix venv detection), and CSV freshness health check gate layered on top of the Plan 07-01 Pipeline runner.

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Add _cleanup_figures + _setup_logging to runner.py | cbad022 | src/pipeline/runner.py |
| 2 | Create cron_run.sh + health_check.py | 5257d06 | scripts/cron_run.sh, scripts/health_check.py |
| 3 | Harden exit-code propagation in run.py | 6246f7f | scripts/run.py |

## What Was Built

### src/pipeline/runner.py — Two new module-level helpers

**`_cleanup_figures(figures_dir='figures') -> int`**
- Called at the top of `run_all()` before the stage loop starts
- `glob.glob(os.path.join(figures_dir, '*.html'))` — scoped, non-recursive, HTML-only
- Each file removed with `os.remove()`; `OSError` is silenced (e.g., race condition with another process)
- Returns count of removed files; logged as `[CLEANUP] removed N stale HTML file(s)`
- Not called from `run_stage()` or `run_from()` — cleanup is a full-run concern only

**`_setup_logging(log_dir='logs') -> logging.Logger`**
- Called at the top of `run_all()`, `run_stage()`, and `run_from()`
- Creates `logs/` directory if absent (`os.makedirs(log_dir, exist_ok=True)`)
- Configures `RotatingFileHandler('logs/pipeline.log', maxBytes=10MB, backupCount=3)`
- Duplicate-handler guard: `if not any(isinstance(h, RotatingFileHandler) for h in lg.handlers)`
- Total log disk cap: ~40MB (4 files × 10MB)
- Log format: `%(asctime)s %(levelname)s %(name)s %(message)s`

### scripts/cron_run.sh — Cron shell wrapper

- `set -u` (fail on undefined vars); deliberately NOT `set -e` so exit code can be captured
- `PROJECT_ROOT` resolved via `$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)` — works from any cwd
- Venv detection (in order): `.venv/Scripts/activate` (Windows Git-Bash) → `.venv/bin/activate` (Unix)
- Writes timestamped start + exit-code lines to `logs/cron_run.log`
- Captures `python scripts/run.py` exit code as `RC=$?` and propagates via `exit $RC`
- Satisfies T-07-07 (cron failure invisibility) — all outcomes logged

### scripts/health_check.py — Freshness PASS/FAIL gate

- Reads `data/regime_results.csv` (via `DATA_DIR` from `src.config`)
- `MAX_STALENESS_DAYS = 5` (~3 trading days + weekend tolerance)
- FAIL cases: file missing, unreadable, empty, or `staleness > 5 days`
- PASS case: prints `PASS: regime_results.csv current as of YYYY-MM-DD`; exits 0
- Suitable for cron post-check, monitoring poll, or CI smoke test

### scripts/run.py — Hardened exit-code propagation

- `main()` dispatch now wrapped in `try / except SystemExit / except Exception`
- `except SystemExit: raise` — pipeline's `sys.exit(1)` propagates cleanly
- `except Exception: traceback.print_exc(); sys.exit(1)` — unexpected errors produce exit 1
- No `except: pass` blocks anywhere in the file

## Verification Results

```
Post-task 1: from src.pipeline.runner import _cleanup_figures, _setup_logging → OK
Post-task 2: bash -n scripts/cron_run.sh → OK; ast.parse(health_check.py) → OK
Post-task 3: GSD_FORCE_STAGE_FAIL=features python scripts/run.py features → exit 1 confirmed
tests/test_pipeline_stages.py → 3 passed
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None introduced by this plan.

## Threat Flags

None. All new surface (glob cleanup, log file, cron wrapper, CSV reader) is within the plan's documented threat model (T-07-05 through T-07-08). No new network endpoints or auth paths introduced.

## Self-Check: PASSED

Files created:
- scripts/cron_run.sh (exists, chmod +x) ✓
- scripts/health_check.py (exists, parses clean) ✓

Files modified:
- src/pipeline/runner.py (_cleanup_figures, _setup_logging, run_all/run_stage/run_from updated) ✓
- scripts/run.py (try/except SystemExit wrapper in main()) ✓

Commits verified:
- cbad022 ✓ (runner.py cleanup + logging)
- 5257d06 ✓ (cron_run.sh + health_check.py)
- 6246f7f ✓ (run.py exit-code hardening)
