---
phase: 04-empirical-diagnostics
fixed_at: 2026-04-19T00:00:00Z
review_path: .planning/phases/04-empirical-diagnostics/04-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-04-19
**Source review:** .planning/phases/04-empirical-diagnostics/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: compute_persistence_baseline — model accuracy is identical to baseline by construction

**Files modified:** `scripts/analysis/analyze_regime_characterization.py`
**Commits:** 2327bb2 (dead variable removal), 458a47a (docstring correction)
**Applied fix:** Dead variables `model_preds`, `model_actual`, `model_match_rate` were removed from the function body in a prior run. This iteration corrected the remaining stale docstring: the `Returns` section listed `model_accuracy` and `lift` as return keys, but the actual dict returns `baseline_accuracy`, `change_rate`, `n_regime_changes`, `oos_days`, `oos_start`. Docstring now matches implementation.

---

### WR-02: kupiec_pof_test — log(0) when n_exc == 0

**Files modified:** `src/core/evaluation.py`
**Commit:** c4fbb24
**Applied fix:** Added two early-return guards before the general computation: when `n_exc == 0`, returns `-2 * n_obs * np.log(1 - alpha)` (only the non-exceedance term survives); when `n_exc == n_obs`, returns `np.nan` (log(0) is undefined). The general case now only runs when `0 < n_exc < n_obs`.

---

### WR-03: compare_var_methods — hardcoded Christoffersen p-value bypasses real computation

**Files modified:** `src/core/evaluation.py`
**Commit:** c4fbb24
**Applied fix:** Replaced `garch_christo_p = 0.547` with a full inline Christoffersen independence test computed on the GARCH residual exceedance indicators. Counts n00/n01/n10/n11 transitions, computes p01/p11/p_bar, and calculates the LR statistic, converting to a p-value via chi2.cdf. Falls back to `np.nan` when the transition matrix is degenerate. The `Safe_for_risk` flag for GARCH now reflects real test results rather than a hardcoded constant.
**Note:** requires human verification — the logic computes the Christoffersen statistic inline rather than calling the existing `christoffersen_test()` helper (which requires a returns Series, not pre-computed indicator arrays). The math is equivalent but should be confirmed against the existing function's output.

---

### WR-04: compute_forward_return_analysis — dead `fwd` variable shadows correct calculation

**Files modified:** `src/core/evaluation.py`
**Commit:** c4fbb24
**Applied fix:** Deleted the dead `fwd = log_ret.shift(-h_days).rolling(h_days).sum()` line. The loop now directly computes `fwd_ret` as the correct forward log-return. No functional change — `fwd` was never read, so the calculation was already correct via `fwd_ret`.

---

### WR-05: _print_bootstrap_cis — off-by-one in duration block extraction

**Files modified:** `src/core/evaluation.py`
**Commit:** c4fbb24
**Applied fix:** Replaced the paired-index step-2 loop with the correct segment-boundary approach. `np.concatenate([[-1], boot_labels, [-1]])` adds sentinels so every segment has both a start and end transition point. The new loop iterates consecutive pairs of transition points — `transitions[j]` to `transitions[j+1]` — and appends the duration when the segment belongs to regime `r`. This correctly handles all segments including the final one, which the old loop missed.

---

_Fixed: 2026-04-19_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
