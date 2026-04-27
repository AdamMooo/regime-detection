---
status: complete
phase: 07-daily-pipeline-clean-outputs
source: [07-01-SUMMARY.md, 07-02-SUMMARY.md, 07-03-SUMMARY.md]
started: 2026-04-25T19:35:00Z
updated: 2026-04-27T01:50:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Pipeline Package Import
expected: |
  Run: python -c "from src.pipeline import Pipeline; print('OK')"
  Expected output: OK (no errors or import failures).
  Then run: python scripts/run.py --help
  Expected: help text shows a --validate flag.
result: pass

### 2. STAGES Registry Order
expected: |
  Run: python -c "from src.pipeline.stages import STAGES; print([s[0] for s in STAGES])"
  Expected output: a list of 9 stage names in this order:
  ['collect', 'features', 'feature_analysis', 'pca', 'train_hmm', 'garch', 'signals', 'dashboard', 'walk_forward']
result: pass

### 3. Exit Code on Forced Stage Failure
expected: |
  Run: GSD_FORCE_STAGE_FAIL=features python scripts/run.py features
  Expected: process exits with code 1 (check with: echo $?)
  The pipeline should not silently swallow the failure.
result: pass

### 4. Cron Script Syntax Check
expected: |
  Run: bash -n scripts/cron_run.sh && echo "syntax OK"
  Expected output: syntax OK (no bash syntax errors).
  Also verify the file exists: ls -la scripts/cron_run.sh
  Expected: file is present and executable.
result: pass

### 5. health_check.py Exists and Imports
expected: |
  Run: python -c "import ast; ast.parse(open('scripts/health_check.py').read()); print('parse OK')"
  Expected output: parse OK
  Also verify it references DATA_DIR: grep "DATA_DIR" scripts/health_check.py
  Expected: at least 1 match.
result: pass

### 6. Full Pipeline Run — Exactly 2 HTML Outputs
expected: |
  (SLOW — ~10 min) Run: python scripts/run.py
  After completion, run: ls figures/*.html
  Expected: exactly 2 files — figures/dashboard.html and figures/feature_analysis.html.
  No other .html files. Exit code should be 0.
result: issue
reported: "Pipeline produced both HTML files, but pipeline.log shows dashboard stage crashes with NaN/PCA error on every run (2026-04-25, 2026-04-26 manual run, 2026-04-26 cron run). HTML is written before the crash so output looks correct, but exit code is 1. Error: 'Input X contains NaN' in stage_dashboard PCA call."
severity: blocker

### 7. regime_results.csv — 6 New Columns Present
expected: |
  (SLOW — requires pipeline run from test 6)
  Run: python -c "import pandas as pd; df=pd.read_csv('data/regime_results.csv',index_col=0); print([c for c in ['days_in_regime','regime_entropy','garch_vol_forecast','blended_vol_forecast','transition_score','structural_anomaly'] if c in df.columns])"
  Expected: all 6 column names printed.
result: pass

### 8. Pipeline Log Created
expected: |
  (SLOW — requires pipeline run from test 6)
  Run: ls -lh logs/pipeline.log
  Expected: file exists with non-zero size and a recent timestamp.
  Run: tail -5 logs/pipeline.log
  Expected: timestamped log lines with stage names and timing info.
result: pass

### 9. Cron Wrapper Logs Exit Code
expected: |
  (SLOW — requires pipeline run from test 6)
  Run: bash scripts/cron_run.sh
  After completion, run: tail -5 logs/cron_run.log
  Expected: log contains a line showing the exit code (e.g. "EXIT_CODE=0").
result: issue
reported: "Cron exit code logging mechanism works correctly (logged '[2026-04-26T21:42:40Z] cron_run exit code: 1'). However exit code is 1 — same dashboard NaN/PCA crash as test 6. The cron infrastructure is correct; the underlying pipeline failure is the same blocker."
severity: blocker

## Summary

total: 9
passed: 7
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "python scripts/run.py exits with code 0 on a successful full pipeline run"
  status: failed
  reason: "User reported: dashboard stage crashes with 'Input X contains NaN' in PCA call on every run. HTML output is written before crash so figures look correct, but exit code is 1. Confirmed across 3 consecutive runs (Apr 25, Apr 26 manual, Apr 26 cron)."
  severity: blocker
  test: 6
  artifacts:
    - path: "src/pipeline/stages.py"
      issue: "stage_dashboard calls PCA on data that contains NaN — crash happens after dashboard.html is already saved"
    - path: "logs/pipeline.log"
      issue: "Three consecutive [FAIL] dashboard entries with identical NaN/PCA traceback"
  missing:
    - "Find the PCA call inside stage_dashboard and identify which DataFrame has NaN rows"
    - "Either drop NaN rows before PCA, impute, or guard with a try/except that logs and continues (dashboard failure should not kill the pipeline)"
