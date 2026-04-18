---
phase: 04-empirical-diagnostics
fixed_at: 2026-04-18T19:27:49Z
review_path: .planning/phases/04-empirical-diagnostics/04-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-04-18T19:27:49Z
**Source review:** .planning/phases/04-empirical-diagnostics/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: compute_persistence_baseline — model accuracy is identical to baseline by construction

**Files modified:** `scripts/analysis/analyze_regime_characterization.py`
**Commit:** 2327bb2
**Applied fix:** Removed the three dead variables (`model_preds`, `model_actual`, `model_match_rate`) from lines 354-356. These were computed identically to the baseline variables and never used in the returned dict. Also removed the dead stale comment above them. The comment for the `n_changes` block was retained.

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
**Note:** This finding requires human verification — the logic computes the Christoffersen statistic inline rather than calling the existing `christoffersen_test()` helper (which requires a returns Series, not pre-computed indicator arrays). The math is equivalent but should be confirmed against the existing function's output.

---

### WR-04: compute_forward_return_analysis — dead `fwd` variable shadows correct calculation

**Files modified:** `src/core/evaluation.py`
**Commit:** c4fbb24
**Applied fix:** Deleted the dead `fwd = log_ret.shift(-h_days).rolling(h_days).sum()` line and its prerequisite `log_ret = np.log(price / price.shift(1))` line (which was only needed by the now-deleted `fwd`). The loop now directly computes `fwd_ret` as the correct forward return.

---

### WR-05: _print_bootstrap_cis — off-by-one in duration block extraction

**Files modified:** `src/core/evaluation.py`
**Commit:** c4fbb24
**Applied fix:** Replaced the paired-index loop (`for i in range(0, len(runs) - 1, 2)`) with the correct segment-boundary approach. The `np.where(...) != 0` call already returns all transition points (including sentinels from the prepended/appended `-1`). The new loop iterates consecutive pairs of transition points — `transitions[j]` to `transitions[j+1]` — and appends the duration when the segment belongs to regime `r`. This correctly handles all segments including the final one, which the old loop missed.

---

_Fixed: 2026-04-18T19:27:49Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
