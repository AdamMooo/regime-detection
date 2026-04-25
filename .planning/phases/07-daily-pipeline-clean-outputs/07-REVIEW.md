---
phase: 07-daily-pipeline-clean-outputs
reviewed: 2026-04-24T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - scripts/cron_run.sh
  - scripts/health_check.py
  - scripts/pipelines/train.py
  - scripts/run.py
  - src/pipeline/__init__.py
  - src/pipeline/runner.py
  - src/pipeline/stages.py
  - src/signals/signals.py
  - tests/test_exit_codes.py
  - tests/test_output_count.py
  - tests/test_pipeline_idempotent.py
  - tests/test_pipeline_stages.py
  - tests/test_pipeline_timing.py
  - tests/test_regime_results_freshness.py
  - tests/test_regime_results_schema.py
findings:
  critical: 2
  warning: 7
  info: 5
  total: 14
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-04-24
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

This phase introduces a daily pipeline orchestration layer (`src/pipeline/`), a health check script, schema enrichment for `regime_results.csv`, and a comprehensive test suite. The architecture is clean and the stage registry pattern is well-executed. Two critical issues were found: a bare `except` block that silently swallows exceptions in a GARCH computation (affecting risk signal quality), and a silent data-alignment gap in `rebuild_dashboard()` that can produce a dimension mismatch between PCA components and results dates without raising any error. Seven warnings cover logic errors and unhandled edge cases that could produce incorrect outputs or test fragility. Five info items cover dead code, magic numbers, and minor style issues.

---

## Critical Issues

### CR-01: Bare `except` silently discards GARCH fit errors, returning stale sigma

**File:** `src/signals/signals.py:551-553`
**Issue:** The inner try/except around the GARCH fit uses a bare `except:` clause, catching all exceptions including `KeyboardInterrupt` and `SystemExit`. When `arch_model.fit()` raises any error, execution falls through to `sigma_t = np.std(recent_returns)` — a silent fallback that produces a different (usually lower) VaR estimate with no indication that the fit failed. Because `compute_garch_var` is called for every row of `regime_results.csv` during training (train.py:2222), a systematic GARCH fitting failure would populate `garch_var_95` with wrong values without any warning log or raised exception.

```python
# Current (dangerous):
    try:
        y = pd.Series(recent_returns) * 100
        am = arch_model(y, vol='GARCH', p=1, q=1, mean='Zero', dist='normal')
        res = am.fit(disp='off')
        sigma_t = res.conditional_volatility.iloc[-1] / 100
    except:                          # catches everything including SystemExit
        sigma_t = np.std(recent_returns)

# Fix — catch only expected fitting exceptions and log:
    except Exception as e:
        import logging as _log
        _log.getLogger('signals').warning(
            'GARCH fit failed (%s: %s); falling back to std-dev estimate',
            type(e).__name__, e,
        )
        sigma_t = np.std(recent_returns)
```

---

### CR-02: Silent dimension mismatch in `rebuild_dashboard()` corrupts PCA tab

**File:** `scripts/pipelines/train.py:2331-2346`
**Issue:** `rebuild_dashboard()` re-runs `fit_rolling_pca` on `feat_scaled.values` (all rows, not just valid dates) and then applies a boolean mask to trim the resulting `pcs` array to `pca_valid_dates.isin(valid_dates)`. If `feat_scaled` has been updated since the last `train()` run (e.g., new data added), `pca_valid_dates` and `valid_dates` may not align perfectly, and `pcs[mask_in_results]` can silently produce an array shorter than `valid_dates`. This shortened `pcs` array is then passed directly to `build_interactive_dashboard` where it indexes into `labels` without any length guard, leading to either a silent mismatch or a confusing IndexError deep in the Plotly rendering code.

```python
# After line 2339, add a length assertion before VIX bypass:
assert len(pcs) == len(valid_dates), (
    f"PCA/results length mismatch after trim: "
    f"pcs={len(pcs)}, valid_dates={len(valid_dates)}. "
    f"Run 'python run.py train' to regenerate aligned artifacts."
)
```

---

## Warnings

### WR-01: `stage_signals` log message counts all placeholder columns, not only newly-added ones

**File:** `src/pipeline/stages.py:193`
**Issue:** The log message counts `sum(1 for c in placeholder_cols if c in df.columns)` — which counts all 6 columns that are present in `df`, not just the `changed` ones. On the second and subsequent runs, `changed` is `False` (all columns already exist), the `df.to_csv()` write is skipped, but the code after the `if changed:` block is never reached anyway. However if the intent was to log how many columns were *added*, the count should be based on what was added in this run. As written, if `changed` is True the count will always equal `len(placeholder_cols)` on first run and the message is correct; but the guard `if changed:` around the log means this is a latent bug if the logic changes. More importantly, the log string says "enriched … with N placeholder columns" which implies work was done, but the enrichment already happened and the signal stage never calls `enrich_results` — it only adds raw NaN placeholders. This is misleading for operators debugging runs where `enrich_results` (called in `train()`) already populated `days_in_regime` and `regime_entropy` with real values, and the signal stage then overwrites them with NaN if those columns were somehow absent.

```python
# Fix — track added columns explicitly:
added = []
for col in placeholder_cols:
    if col not in df.columns:
        df[col] = np.nan
        added.append(col)
if added:
    df.to_csv(results_path)
    logger.info("signals: added %d placeholder column(s): %s", len(added), added)
```

---

### WR-02: `compute_garch_var` returns a positive value when `erfinv` computation yields positive result

**File:** `src/signals/signals.py:557-561`
**Issue:** The formula `z_crit = np.sqrt(2) * erfinv(2 * (1 - alpha) - 1)` with `alpha=0.05` gives `erfinv(0.9)` which is a positive number (~1.163), so `z_crit` is positive and `garch_var = -z_crit * sigma_t` is correctly negative. However, the guard on line 561 `return garch_var if garch_var < 0 else -0.02` silently substitutes a magic constant if the calculation somehow produces a non-negative result. The constant `-0.02` is a 2% VaR fallback but is never explained or configurable, making it a hidden assumption in the risk model. A non-negative `garch_var` would only occur if `sigma_t <= 0` (which implies a GARCH convergence failure), so the fallback guard masks the root cause. The fix from CR-01 would also address the root cause here, but the fallback itself should at least log a warning.

```python
# Fix:
if garch_var >= 0:
    import logging as _log
    _log.getLogger('signals').warning(
        'compute_garch_var: non-negative VaR (%s) — sigma_t=%s; returning -0.02 fallback',
        garch_var, sigma_t,
    )
    return -0.02
return garch_var
```

---

### WR-03: `_regime_awareness` median duration RLE includes the current (still-open) run

**File:** `src/signals/signals.py:119-130`
**Issue:** The run-length encoding loop appends `curr_run` to `rle_lengths` only when `live_regimes[i - 1] == current` (completed runs). But after the loop, `if live_regimes[-1] == current: rle_lengths.append(curr_run)` appends the *current, ongoing* run to the historical durations. This inflates the median when the current streak is unusually long (e.g., a 200-day bull run would add 200 to the list of median-duration samples), making the "median duration" output statistically misleading. Only completed runs should be included in the historical distribution used for the median.

```python
# Fix — remove the final append:
# Do NOT add the current open run to historical durations.
# The streak (days_in_regime) already communicates the current run length.
median_dur = float(np.median(rle_lengths)) if rle_lengths else 0.0
```

---

### WR-04: `test_output_count` runs the full pipeline twice in CI without `@pytest.mark.slow` scope limitation on subprocess behavior

**File:** `tests/test_output_count.py:12`
**Issue:** `subprocess.run([sys.executable, 'scripts/run.py'], check=True)` is called without `cwd` being explicitly set. In CI or when `pytest` is invoked from a directory other than the project root, the subprocess will look for `scripts/run.py` relative to whatever the current working directory is, not relative to the test file. `test_pipeline_timing.py:16` correctly passes `cwd=os.getcwd()` — `test_output_count.py` should do the same. Additionally, `check=True` means a pipeline failure raises `CalledProcessError` from within the test body, which pytest will report as an ERROR (not a FAIL), making it harder to diagnose.

```python
# Fix:
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
result = subprocess.run(
    [sys.executable, 'scripts/run.py'],
    check=False, cwd=PROJECT_ROOT,
)
assert result.returncode == 0, f"Pipeline failed: {result.stderr.decode()[-2000:]}"
```

---

### WR-05: `_validation_metrics` aligns `results_aligned` by slicing rows with `.iloc[1:]` and assigning `spy_ret.values`, assuming index alignment

**File:** `src/signals/signals.py:207-208`
**Issue:** `results_aligned = results.iloc[1:].copy()` and then `results_aligned['spy_ret'] = spy_ret.values` aligns by positional order, not by index. `spy_ret = pd.Series(np.log(results['SPY_close'] / results['SPY_close'].shift(1))).dropna()` — if there is a NaN in `SPY_close` somewhere in the middle of the series (not just the first row), `dropna()` will remove interior rows, making `len(spy_ret)` shorter than `len(results) - 1`. The subsequent `spy_ret.values` assignment to `results_aligned` would then raise a `ValueError: Length of values does not match length of index`. This is a latent bug triggered whenever `SPY_close` has any internal NaN values.

```python
# Fix — use index-based alignment:
spy_ret = pd.Series(
    np.log(results['SPY_close'] / results['SPY_close'].shift(1)),
    index=results.index,
).dropna()
results_aligned = results.loc[spy_ret.index].copy()
results_aligned['spy_ret'] = spy_ret.values
```

---

### WR-06: `run_from()` in `runner.py` does not `_cleanup_figures` and does not log total time

**File:** `src/pipeline/runner.py:106-130`
**Issue:** `run_from()` mirrors `run_all()` but omits the `_cleanup_figures()` call. If `run_from('feature_analysis')` is used to restart a partial pipeline, stale HTML figures from a previous failed run remain in `figures/`. This violates the PIPE-02 contract (exactly 2 HTML files after a complete run). Additionally, `run_from()` does not log total time or print the per-stage summary that `run_all()` does, making operator debugging harder. This is a behavioral inconsistency that can cause `test_output_count` to fail when `run_from` is used instead of `run_all`.

**Fix:** Add `_cleanup_figures()` at the start of `run_from()` and add the summary print after the loop (same as `run_all`).

---

### WR-07: `enrich_results` maps integer GARCH keys by positional order of `unique()`, which is non-deterministic

**File:** `src/signals/signals.py:799`
**Issue:** When `key_str.isdigit()`, the code maps `int(key_str)` to `regime_names_in_data[int(key_str)]` where `regime_names_in_data = out['regime_name'].unique().tolist()`. The order of `pandas.unique()` is insertion-order (order of first appearance in the column), which depends on the sorted order of regime labels in the data. If `garch_results` uses integer keys `{0: ..., 1: ..., 2: ...}` corresponding to HMM state indices, but the first-appearance order in `regime_name` column differs from state-index order, the GARCH results will be silently matched to the wrong regime. The fix is to build the mapping from the `name_map` dict (which has the authoritative int->name mapping) passed through GARCH fitting.

**Fix:** Pass `name_map` into `enrich_results` or change `stage_garch` to use string keys when building `garch_results` before passing to `enrich_results`.

---

## Info

### IN-01: Duplicate `compute_var_backtest` and `kupiec_pof_test` / `christoffersen_test` definitions

**File:** `scripts/pipelines/train.py:161-270`
**Issue:** `train.py` defines local `compute_var_backtest`, `kupiec_pof_test`, and `christoffersen_test` functions (lines 161–270) that shadow the imports of the same names from `src.core.var_backtesting` (line 54). The local versions are the ones actually called by `train()` at lines 2173–2186. The imports are thus dead code. This creates maintenance risk — a bug fixed in `src.core.var_backtesting` will not be reflected in `train.py`'s behavior.

**Fix:** Remove the local re-definitions and rely solely on the imported versions from `src.core.var_backtesting`.

---

### IN-02: `compute_days_in_regime` uses `days.iloc[i] = count` inside a loop (slow for large DataFrames)

**File:** `src/signals/signals.py:745-752`
**Issue:** Setting values via `.iloc[i]` inside a Python loop triggers a pandas SettingWithCopyWarning-class operation on each iteration and is O(n) with high constant overhead. For a DataFrame with 5,000+ rows (several years of daily data) this is acceptably fast but is an antipattern. A vectorized implementation using `groupby` + `cumcount` is more idiomatic and ~50x faster.

```python
# Vectorized alternative:
def compute_days_in_regime(regime_names: pd.Series) -> pd.Series:
    groups = (regime_names != regime_names.shift()).cumsum()
    return regime_names.groupby(groups).cumcount() + 1
```

---

### IN-03: Magic constant `-0.02` used as VaR fallback in three places without a named constant

**File:** `src/signals/signals.py:539, 543, 703`
**Issue:** The value `-0.02` (2% daily loss fallback) appears three times as a hardcoded literal. It represents an assumption about "conservative default daily VaR" but is not documented or configurable. It should be a named constant at the module level.

```python
_DEFAULT_VAR_FALLBACK = -0.02  # Conservative 2% daily VaR fallback
```

---

### IN-04: `test_regime_results_schema.py` `test_prob_columns_named_by_regime` hardcodes 3-state regime names

**File:** `tests/test_regime_results_schema.py:29-32`
**Issue:** The test asserts `'prob_Low-Vol' in prob_cols`, `'prob_Moderate-Vol' in prob_cols`, and `'prob_High-Vol' in prob_cols` — hardcoding the assumption that the model will produce exactly those three regime names. If `N_STATES` or `REGIME_NAMES` config changes (e.g., adding a 'Crisis' state), this test will fail with a confusing assertion error rather than a clear configuration mismatch message. The test would be more robust if it validated that at least one `prob_*` column exists and that each matches the `LABEL_MAPPING` keys.

---

### IN-05: `scripts/run.py` catches `SystemExit` explicitly and re-raises it, which is redundant

**File:** `scripts/run.py:196-197`
**Issue:** The `except SystemExit: raise` block is necessary to prevent `sys.exit(0)` called inside pipeline stages from being caught by the outer `except Exception as e` block — this is correct and intentional. However the comment `# pipeline already called sys.exit(...) — propagate as-is` is the only explanation, and the pattern is subtle enough that future maintainers may remove it thinking it is dead code. A brief docstring note on this contract in the `main()` function would prevent regression.

---

_Reviewed: 2026-04-24_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
