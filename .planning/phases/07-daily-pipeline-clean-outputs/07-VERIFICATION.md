---
phase: 07-daily-pipeline-clean-outputs
verified: 2026-04-24T00:00:00Z
status: gaps_found
score: 11/13 must-haves verified
gaps:
  - truth: "test_prob_columns_named_by_regime asserts prob_Moderate-Vol — but config.py REGIME_NAMES[3] is 'Medium-Vol', so the assertion is permanently wrong"
    status: failed
    reason: "test_regime_results_schema.py line 31 asserts 'prob_Moderate-Vol' in prob_cols, but the model produces 'prob_Medium-Vol' (K=3 config uses Medium-Vol). The test was authored with the wrong name from the plan spec. The test will always fail against a real run."
    artifacts:
      - path: "tests/test_regime_results_schema.py"
        issue: "Line 31: assert 'prob_Moderate-Vol' in prob_cols — wrong column name for K=3; should be 'prob_Medium-Vol'"
    missing:
      - "Fix test_regime_results_schema.py line 31 to assert 'prob_Medium-Vol' instead of 'prob_Moderate-Vol' (matching config.py REGIME_NAMES[3])"
  - truth: "regime_results.csv contains all 3 new computed columns (days_in_regime, regime_entropy, garch_vol_forecast) and 3 placeholder NaN columns after a run"
    status: partial
    reason: "enrich_results() is correctly implemented and wired into train.py immediately before the to_csv write (line 2228/2229). However, the on-disk regime_results.csv is stale — it predates the enrichment wiring and lacks all 6 new columns. The code path is correct; the stale file makes test_required_columns_exist and test_placeholder_columns_are_all_nan fail. Per instructions, this is expected until next pipeline run, but the schema test currently fails."
    artifacts:
      - path: "data/regime_results.csv"
        issue: "Stale — written before enrich_results() was wired in. Missing: days_in_regime, regime_entropy, garch_vol_forecast, blended_vol_forecast, transition_score, structural_anomaly"
    missing:
      - "Run 'python scripts/run.py' once to regenerate regime_results.csv with all 6 new columns"
      - "After a run, test_regime_results_schema.py::test_required_columns_exist and test_placeholder_columns_are_all_nan will pass"
---

# Phase 7: Daily Pipeline Clean Outputs — Verification Report

**Phase Goal:** Break train.py monolith into a pipeline package, enforce exactly-2-HTML outputs, add cron infrastructure, enrich regime_results.csv with 6 new columns.
**Verified:** 2026-04-24
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `from src.pipeline import Pipeline` succeeds | VERIFIED | Import confirmed in venv; __init__.py exports Pipeline from runner |
| 2 | STAGES registry has 9 entries in correct order | VERIFIED | Registry verified: collect, features, feature_analysis, pca, train_hmm, garch, signals, dashboard, walk_forward |
| 3 | walk_forward runs ONLY when --validate is passed | VERIFIED | runner.py line: `if name == 'walk_forward' and not validate: continue` |
| 4 | Per-stage wall-clock timing logged at end of run | VERIFIED | run_all() uses time.perf_counter() on each stage; prints timing table at end |
| 5 | ANY stage exception causes sys.exit(1) | VERIFIED | sys.exit(1) in run_all, run_stage, run_from exception handlers (3 call sites); no except/pass in run.py |
| 6 | stage_walk_forward imports from src.core.orchestrator (not train.py) | VERIFIED | stages.py line 24: `from src.core.orchestrator import walk_forward as _orchestrator_walk_forward` |
| 7 | Duplicate walk_forward removed from train.py | VERIFIED | `grep -c "^def walk_forward" scripts/pipelines/train.py` returns 0 |
| 8 | Before each run, stale figures/*.html files are deleted | VERIFIED | _cleanup_figures() in runner.py called at top of run_all(); glob scoped to figures/*.html |
| 9 | RotatingFileHandler 10MB/3-backup configured | VERIFIED | runner.py: maxBytes=10*1024*1024, backupCount=3; _setup_logging() called from run_all/run_stage/run_from |
| 10 | cron_run.sh activates venv and logs exit code | VERIFIED | Shell syntax valid; Windows+Unix venv detection; exit code logged to cron_run.log; `exit $RC` propagates |
| 11 | health_check.py exits 0/1 on PASS/FAIL | VERIFIED | PASS/FAIL branches verified; imports DATA_DIR from src.config; MAX_STALENESS_DAYS=5 |
| 12 | test_prob_columns_named_by_regime asserts correct column names | FAILED | Test asserts 'prob_Moderate-Vol' but config.py REGIME_NAMES[3] = 'Medium-Vol'; real CSV has 'prob_Medium-Vol' |
| 13 | regime_results.csv contains all 6 new columns after a run | PARTIAL | Code wiring is correct (enrich_results at train.py:2228 before to_csv at :2229); stale CSV on disk lacks columns until next run |

**Score:** 11/13 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/pipeline/__init__.py` | Pipeline class export | VERIFIED | `from src.pipeline.runner import Pipeline`; `__all__ = ['Pipeline']` |
| `src/pipeline/stages.py` | 9 stage functions + STAGES registry | VERIFIED | 9 functions named correctly; STAGES registry in locked order; GSD_FORCE_STAGE_FAIL hook in all 9 |
| `src/pipeline/runner.py` | Pipeline class + timing + exit-code + cleanup + logging | VERIFIED | class Pipeline with run_all/run_stage/run_from; _cleanup_figures; _setup_logging; 3x sys.exit(1) |
| `scripts/run.py` | argparse entry point with --validate; no silent swallows | VERIFIED | --validate flag present; SystemExit re-raise pattern; no except/pass |
| `scripts/cron_run.sh` | Cron wrapper with venv + exit-code logging | VERIFIED | bash syntax valid; dual venv detection; cron_run.log written |
| `scripts/health_check.py` | Freshness PASS/FAIL reader | VERIFIED | PASS/FAIL logic complete; imports DATA_DIR; sys.exit on return value |
| `src/signals/signals.py` (enrich_results) | enrich_results() + compute_days_in_regime() | VERIFIED | Both functions exist; unit test: [1,2,3,1,2,1] correct; all 6 columns produced; garch=None → garch_vol_forecast all-NaN |
| `scripts/pipelines/train.py` (enrichment wiring) | Single enrich_results call before to_csv | VERIFIED | Line 2228: `results = enrich_results(results, garch_results)`; line 2229: `results.to_csv(...)`; no double-enrichment |
| `tests/test_pipeline_stages.py` | Package import + STAGES + callable checks | VERIFIED | 3 passed; no slow marker |
| `tests/test_pipeline_timing.py` | @pytest.mark.slow; <600s assertion | VERIFIED | slow marker present; subprocess runs scripts/run.py |
| `tests/test_pipeline_idempotent.py` | @pytest.mark.slow; determinism assertion | VERIFIED | slow marker present |
| `tests/test_output_count.py` | @pytest.mark.slow; exactly 2 HTML files | VERIFIED | slow marker present; asserts {'dashboard.html', 'feature_analysis.html'} |
| `tests/test_exit_codes.py` | @pytest.mark.slow; GSD_FORCE_STAGE_FAIL → exit 1 | VERIFIED | slow marker present; env hook contract tested |
| `tests/test_regime_results_schema.py` | Schema contract (column names); NO slow marker | PARTIAL | No slow marker correct; but test_prob_columns_named_by_regime uses wrong column name |
| `tests/test_regime_results_freshness.py` | @pytest.mark.slow; last-row freshness | VERIFIED | slow marker present |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| src/pipeline/__init__.py | src/pipeline/runner.Pipeline | `from src.pipeline.runner import Pipeline` | WIRED | Exact import verified |
| src/pipeline/runner.py | src/pipeline/stages.STAGES | `from src.pipeline.stages import STAGES` | WIRED | Line 10 |
| src/pipeline/stages.py | src.core.orchestrator.walk_forward | `from src.core.orchestrator import walk_forward as _orchestrator_walk_forward` | WIRED | Line 24; stage_walk_forward calls _orchestrator_walk_forward() |
| src/pipeline/runner.py | sys.exit(1) | stage exception handlers | WIRED | 3 call sites: run_all:82, run_stage:104, run_from:124 |
| src/pipeline/runner.py | figures/*.html cleanup | glob.glob in _cleanup_figures | WIRED | Called from run_all before stage loop |
| src/pipeline/runner.py | logs/pipeline.log | RotatingFileHandler in _setup_logging | WIRED | Called from run_all/run_stage/run_from |
| scripts/cron_run.sh | scripts/run.py | `python scripts/run.py` shell invocation | WIRED | Line 23 |
| scripts/pipelines/train.py | src.signals.signals.enrich_results | `from src.signals.signals import compute_signals, enrich_results` | WIRED | Import at line 49; call at line 2228 (before to_csv at 2229) |
| src/signals/signals.enrich_results | garch_results .conditional_volatility | `cond_vol_attr = getattr(res, 'conditional_volatility', None)` | WIRED | Line 803; divided by 100 for decimal vol |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| enrich_results() | days_in_regime | compute_days_in_regime(regime_names) sequential scan | Yes — sequential over regime_name column | FLOWING |
| enrich_results() | regime_entropy | prob_* columns via numpy log | Yes — computed from probability columns | FLOWING |
| enrich_results() | garch_vol_forecast | garch_results[key].conditional_volatility / 100 | Yes — from fitted arch result; NaN when garch_results=None | FLOWING |
| enrich_results() | blended_vol_forecast | np.nan hardcoded | Intentional placeholder for Phase 9 | STATIC (by design) |
| enrich_results() | transition_score | np.nan hardcoded | Intentional placeholder for Phase 11 | STATIC (by design) |
| enrich_results() | structural_anomaly | np.nan hardcoded | Intentional placeholder for Phase 12 | STATIC (by design) |

---

## Behavioral Spot-Checks

Step 7b: SKIPPED for slow tests (requires full pipeline run, ~10+ min). Non-slow tests run below.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Pipeline package imports | `python3 -c "from src.pipeline import Pipeline"` | import OK | PASS |
| STAGES registry order | `from src.pipeline.stages import STAGES` + names check | ['collect', 'features', 'feature_analysis', 'pca', 'train_hmm', 'garch', 'signals', 'dashboard', 'walk_forward'] | PASS |
| Pipeline callable check | test_pipeline_stages.py 3 tests | 3 passed | PASS |
| compute_days_in_regime unit test | ['A','A','A','B','B','A'] -> [1,2,3,1,2,1] | [1, 2, 3, 1, 2, 1] | PASS |
| enrich_results column contract | 6 columns present, placeholders all-NaN, garch=None → garch_vol_forecast NaN | All assertions pass | PASS |
| cron_run.sh shell syntax | `bash -n scripts/cron_run.sh` | exit 0 | PASS |
| run.py --validate flag | `grep "'--validate'" scripts/run.py` | match found | PASS |
| walk_forward gate | `grep "if name == 'walk_forward' and not validate"` | 1 match in runner.py | PASS |
| schema test — prob column name | test_prob_columns_named_by_regime | FAILED: asserts prob_Moderate-Vol; CSV has prob_Medium-Vol | FAIL |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 07-01 | Full daily pipeline in under 10 minutes | SATISFIED (code) | Pipeline package with 8-stage sequence; sys.exit(1) contract; --validate gates walk_forward. Runtime verification requires a full run (slow). |
| PIPE-02 | 07-02 | Exactly 2 HTML outputs: dashboard.html + feature_analysis.html | SATISFIED (code) | _cleanup_figures() in run_all() deletes all *.html before run; stage_feature_analysis writes feature_analysis.html; stage_dashboard writes dashboard.html. test_output_count.py verifies after a run. |
| PIPE-03 | 07-03 | regime_results.csv with today's regime, probs, GARCH VaR, cron-ready | PARTIAL | enrich_results() wired into train.py at line 2228; 6 new columns implemented correctly; stale on-disk CSV lacks new columns until next run. test_regime_results_schema.py::test_prob_columns_named_by_regime has a wrong assertion. |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| tests/test_regime_results_schema.py | 31 | `assert 'prob_Moderate-Vol' in prob_cols` | Blocker | Test permanently fails; config.py REGIME_NAMES[3] is 'Medium-Vol', CSV has 'prob_Medium-Vol'. Wrong name was transcribed from plan spec. |
| src/pipeline/stages.py:stage_signals | 180-193 | Placeholder NaN columns: days_in_regime, regime_entropy, garch_vol_forecast in stage_signals | Warning (known/intentional) | stage_signals adds these as NaN fallback if train() hasn't already written them via enrich_results(). Post-Plan-07-03, this path is a no-op (changed=False). Not a runtime defect. |

---

## Human Verification Required

### 1. Full Pipeline Run — Exactly 2 HTML Files

**Test:** Run `python scripts/run.py` on dev machine. Then run `ls figures/*.html`.
**Expected:** Exactly 2 files: `figures/dashboard.html` and `figures/feature_analysis.html`. No other HTML files.
**Why human:** Requires full data download + model fitting (~10 min); cannot verify in CI without live data.

### 2. regime_results.csv Schema After Run

**Test:** After the pipeline run above, execute:
```
python3 -c "import pandas as pd; df=pd.read_csv('data/regime_results.csv', index_col=0); print(sorted(df.columns.tolist())); print('days_in_regime' in df.columns, 'regime_entropy' in df.columns, 'garch_vol_forecast' in df.columns)"
```
**Expected:** All 6 new columns present; `days_in_regime` and `regime_entropy` 0% NaN; `blended_vol_forecast`, `transition_score`, `structural_anomaly` 100% NaN.
**Why human:** Requires live pipeline run; stale CSV on disk predates enrichment.

### 3. health_check.py PASS After Run

**Test:** After the pipeline run above, execute `python scripts/health_check.py`.
**Expected:** Prints a line beginning with `PASS:` and exits 0.
**Why human:** Requires fresh CSV with today's data; current CSV is stale.

---

## Gaps Summary

Two gaps block full goal achievement:

**Gap 1 — Wrong column name in schema test (Blocker):** `test_regime_results_schema.py` line 31 asserts `'prob_Moderate-Vol' in prob_cols` but `config.py` `REGIME_NAMES[3]` is `['Low-Vol', 'Medium-Vol', 'High-Vol']`. The model produces `prob_Medium-Vol`. This is a test authoring error introduced when the plan spec used "Moderate-Vol" but the config has always used "Medium-Vol". The test will always fail against a real run regardless of enrichment status. Fix: change line 31 to `assert 'prob_Medium-Vol' in prob_cols`.

**Gap 2 — Stale regime_results.csv (Expected, pre-run condition):** The code path is correct — `enrich_results(results, garch_results)` is called at train.py line 2228, immediately before the `to_csv` at line 2229. The on-disk CSV predates this wiring and lacks the 6 new columns. `test_required_columns_exist` and `test_placeholder_columns_are_all_nan` will both fail until the pipeline is re-run. This is not a code defect; it resolves automatically on the next pipeline run. However, per goal-backward verification, the truth "regime_results.csv contains all 6 new columns" is not currently satisfied.

The prob_Medium-Vol test fix is actionable now and does not require a pipeline run.

---

_Verified: 2026-04-24_
_Verifier: Claude (gsd-verifier)_
