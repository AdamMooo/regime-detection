---
phase: 04-empirical-diagnostics
reviewed: 2026-04-17T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - scripts/analysis/analyze_regime_characterization.py
  - src/core/evaluation.py
  - tests/test_regime_economic_validity.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-04-17
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Three files implementing Phase 4 empirical diagnostics were reviewed: the analysis
script (`analyze_regime_characterization.py`), the evaluation module
(`src/core/evaluation.py`), and the test suite
(`tests/test_regime_economic_validity.py`).

The code is generally well-structured and well-documented. The main concerns are:
a logic bug in `compute_persistence_baseline` that makes the "model accuracy" metric
a no-op duplicate of the baseline; a numerical issue in `kupiec_pof_test` when zero
exceedances are observed; a hardcoded p-value in `compare_var_methods` that silently
bypasses real computation; incorrect forward-return calculation in
`compute_forward_return_analysis` (dead `fwd` variable); and an off-by-one in the
bootstrap duration extraction. None of these are security issues, but several affect
correctness of diagnostic outputs.

---

## Warnings

### WR-01: compute_persistence_baseline — model accuracy is identical to baseline by construction

**File:** `scripts/analysis/analyze_regime_characterization.py:353-356`
**Issue:** `model_preds` and `model_actual` are computed identically to `baseline_preds`
and `actual` (both shift the same series by 1). The variable `model_match_rate` is
therefore mathematically equal to `baseline_accuracy` in every run. The function
returns only `baseline_accuracy` and never a separate model metric, making the
"lift" concept described in the docstring impossible to compute with current inputs.
The dead variables also mislead future readers into thinking a real model-vs-baseline
comparison has been performed.
**Fix:** Either remove `model_preds`/`model_actual`/`model_match_rate` entirely (they
are unused in the returned dict) and update the docstring to clarify the function only
measures the persistence baseline's own accuracy, or accept a second `model_labels`
argument to enable a genuine comparison:
```python
# Option A: remove dead code and clarify purpose
# Delete lines 354-356; update docstring to state this is baseline-only measurement.

# Option B: accept an explicit model prediction series for genuine lift computation
def compute_persistence_baseline(results, model_labels=None):
    ...
    if model_labels is not None:
        model_accuracy = (model_labels.reindex(actual.index) == actual).mean()
    else:
        model_accuracy = None
```

---

### WR-02: kupiec_pof_test — log(0) when n_exc == 0

**File:** `src/core/evaluation.py:304-306`
**Issue:** When `n_exc == 0`, `p_hat = 0` and `np.log(p_hat / p)` evaluates to
`log(0)` which is `-inf`. The likelihood ratio `lr` then becomes `-inf` or `nan`,
propagating silently to the chi-squared p-value computation and producing `nan`
results. Zero exceedances is a realistic outcome for low-risk regimes.
**Fix:** Guard for the zero-exceedance case per standard Kupiec implementation:
```python
def kupiec_pof_test(n_obs, n_exc, alpha):
    p = alpha
    if n_exc == 0:
        # LR = -2 * n_obs * log(1 - alpha): only the non-exceedance term survives
        return -2 * n_obs * np.log(1 - alpha)
    if n_exc == n_obs:
        return np.nan  # p_hat = 1, log((1-p_hat)/(1-p)) = log(0)
    p_hat = n_exc / n_obs
    lr = 2 * (n_exc * np.log(p_hat / p) +
              (n_obs - n_exc) * np.log((1 - p_hat) / (1 - p)))
    return lr
```

---

### WR-03: compare_var_methods — hardcoded Christoffersen p-value bypasses real computation

**File:** `src/core/evaluation.py:492`
**Issue:** `garch_christo_p = 0.547` is a literal constant taken from a prior
Phase 2.5.4 run. This means every call to `compare_var_methods` — regardless of
input data, date range, or parameters — returns the same Christoffersen p-value for
the GARCH method. The `Safe_for_risk` flag for GARCH is therefore hardcoded to True
regardless of actual test results.
**Fix:** Compute the Christoffersen test for GARCH dynamically the same way it is
computed for static VaR. The existing `christoffersen_test` function can be called
directly on the residualised GARCH exceedances:
```python
# Replace line 492 with a real computation:
indicators = (y.values / 100 < -var_dynamic).astype(int)
# ... compute n00/n01/n10/n11 and run christoffersen_test on the GARCH residuals
# or: call christoffersen_test() with a synthetic returns Series of GARCH residuals
garch_christo_p = np.nan  # at minimum — do not hardcode a known-good value
```

---

### WR-04: compute_forward_return_analysis — dead `fwd` variable shadows correct calculation

**File:** `src/core/evaluation.py:567-572`
**Issue:** Lines 567-568 compute `fwd` (a rolling sum of shifted log-returns) but
`fwd` is never used. The actual forward return stored in `aligned` uses `fwd_ret`
computed on lines 570-571. While `fwd_ret` is the correct calculation, the presence
of the dead `fwd` variable suggests an earlier implementation was partially replaced,
risking confusion and future maintenance errors. Additionally the variable name `fwd`
sits in the inner loop and will be re-bound on every iteration without ever being read.
**Fix:** Delete the dead lines:
```python
# Delete lines 567-568:
# fwd = log_ret.shift(-h_days).rolling(h_days).sum()  # REMOVE — never used
```

---

### WR-05: _print_bootstrap_cis — off-by-one in duration block extraction

**File:** `src/core/evaluation.py:153-158`
**Issue:** The block extraction loop uses `for i in range(0, len(runs) - 1, 2)` with
step 2, treating `runs` as paired (start, end) indices. However
`np.where(np.diff(...) != 0)[0]` returns transition *points*, not paired boundaries.
For a label array `[0,0,1,1,0]`, `runs` = `[2, 4]` (two transition points), but
the loop tries to use `runs[i]` as start and `runs[i+1]` as end, giving duration = 2
for the first block only and missing the final block. This causes duration CI estimates
to be systematically underestimated.
**Fix:** Use `np.diff` on the transition index array directly:
```python
# Simpler, correct approach:
transitions = np.where(np.diff(np.concatenate([[-1], boot_labels, [-1]])) != 0)[0]
for j in range(len(transitions) - 1):
    seg_start = transitions[j]
    seg_end = transitions[j + 1]
    if boot_labels[seg_start] == r:
        durations.append(seg_end - seg_start)
```

---

## Info

### IN-01: analyze_regime_statistics — rolling vol computed on full returns inside regime loop

**File:** `scripts/analysis/analyze_regime_characterization.py:123`
**Issue:** `rolling_vol = returns.rolling(21).std() * np.sqrt(252) * 100` is
recomputed identically on every iteration of the `for regime in ...` loop. This is
wasteful (though not incorrect) and could be hoisted outside the loop.
**Fix:** Move the rolling vol computation before the loop:
```python
rolling_vol = returns.rolling(21).std() * np.sqrt(252) * 100
for regime in sorted(regimes.dropna().unique()):
    ...
    vol_data.append(rolling_vol[regime_mask].dropna().values)
```

---

### IN-02: analyze_failure_modes — heuristic high_vol_regime picks first match only

**File:** `scripts/analysis/analyze_regime_characterization.py:404-408`
**Issue:** The loop that assigns `high_vol_regime` breaks on the first keyword match
across `regimes.unique()` (which has no guaranteed order). If the actual high-vol
regime name is e.g. `"High-Vol Stress"` but `"Bear"` is encountered first, the wrong
regime is selected. The result is that the crisis alignment diagnostic silently reports
the wrong expected regime.
**Fix:** Sort regimes before the keyword scan, or prefer the regime with the highest
observed volatility (computed from `market` data which is already available in the
caller) to make the selection deterministic and data-driven.

---

### IN-03: evaluate.py — bare `except:` in compute_var_backtest and compare_var_methods

**File:** `src/core/evaluation.py:258-259` and `493-495`
**Issue:** Two bare `except:` blocks swallow all exceptions including
`KeyboardInterrupt` and `SystemExit`. This makes it difficult to debug failures
during analysis runs.
**Fix:** Catch a specific exception type:
```python
except Exception:
    christo_stat = np.nan
```

---

### IN-04: test_regime_economic_validity.py — causal integrity tests open files with relative paths

**File:** `tests/test_regime_economic_validity.py:232-252`
**Issue:** The causal integrity tests open source files using relative paths
(`'src/config.py'`, `'scripts/train.py'`, etc.) with no consideration of the working
directory when `pytest` is invoked. If `pytest` is run from a subdirectory (e.g.,
`pytest tests/`) the file opens will silently skip via `FileNotFoundError`, making the
tests appear to pass when the target file simply was not found at the relative path.
The `continue` on `FileNotFoundError` makes this behaviour invisible.
**Fix:** Use `pathlib` with `__file__` to construct an absolute path to the project
root, or use `importlib` to inspect the module source directly:
```python
import pathlib
ROOT = pathlib.Path(__file__).parent.parent  # project root
config_path = ROOT / 'src' / 'config.py'
```

---

_Reviewed: 2026-04-17_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
