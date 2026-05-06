# Phase 9: Regime Calibration — Context

**Gathered:** 2026-05-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 9 fixes the 3 model-quality failures discovered during the first live Phase 7 pipeline run (2026-04-27), plus the dashboard NaN crash that causes exit code 1 on every pipeline run. No new features, no architecture changes — pure bug fixes and calibration.

The 4 problems to fix, in execution order:

1. **Dashboard NaN crash** — `stage_dashboard` calls PCA on a DataFrame that contains NaN rows → "Input X contains NaN" → exit code 1 on every run. HTML is already written at crash time so output looks correct, but the pipeline never exits 0.
2. **GARCH VaR scaling bug** — `mean_vol=700%+`, `VaR=-546%`. Returns are passed in the wrong units (basis points instead of decimals) somewhere in the GARCH path (`src/core/var_backtesting.py`).
3. **OOS label variant explosion** — Walk-forward produces 8 distinct `regime_name_oos` values instead of 3. Procrustes fold alignment in `orchestrator.py` is producing degenerate mappings.
4. **High-Vol dominance** — 61% of days labeled High-Vol (target: 15–25%). Regime boundaries are not well-calibrated; either `VOL_BRACKETS` thresholds or HDP-HMM concentration prior needs tuning.

Phase does NOT include: new pipeline stages, new features, changes to the public signals API (`detect()`, `fit()`, `bot_label`), or UI work.

</domain>

<decisions>
## Implementation Decisions

### Plan Structure

- **D-01:** 3 separate plans, executed in sequence. Each plan is self-contained with its own fix + regression test. Plan 1 is the unblock plan (dashboard NaN + GARCH), Plan 2 is label alignment, Plan 3 is High-Vol calibration.
- **D-02:** Plan 1 bundles the dashboard NaN crash fix with the GARCH unit fix. Both are small, isolated code fixes. Having exit code 0 and correct GARCH output is a prerequisite for validating Plans 2 and 3 end-to-end.

### Plan 1: Dashboard NaN + GARCH Fix

- **D-03:** Dashboard NaN fix — drop NaN rows before the PCA call in `stage_dashboard`. Do not impute, do not catch-and-continue. The fix is a `df.dropna()` guard on the PCA input; the HTML output is unaffected since it was already written before the crash.
- **D-04:** GARCH fix — surgical unit correction in `src/core/var_backtesting.py`. Find where returns are passed in basis points (or percentage × 100) instead of decimals and normalize. No broader GARCH audit.
- **D-05:** Regression assertion — add `assert mean_vol < 1.0` (i.e., mean vol < 100%) immediately after GARCH parameter estimation. This catches future unit regressions without requiring a full backtest.

### Plan 2: Label Alignment Fix

- **D-06:** Replace the broken Procrustes fold alignment in `src/core/orchestrator.py::walk_forward()` with Hungarian matching via `scipy.optimize.linear_sum_assignment`. Cost matrix = overlap/confusion counts between fold label assignments and in-sample regime names. `scipy` is already a dependency.
- **D-07:** Regression test — after `walk_forward()`, assert that the number of distinct `regime_name_oos` values is `<= K` (K=3). This is a direct test of the failure condition.

### Plan 3: High-Vol Calibration

- **D-08:** Diagnostic-first approach. Before tuning any thresholds or priors, run a diagnostic script to inspect the actual vol distribution across regimes (post-GARCH-fix, since the GARCH unit bug may have inflated vol readings). Let the diagnostic findings determine which lever to pull.
- **D-09:** Calibration levers available (pick based on diagnostic findings):
  - Primary: Tune `VOL_BRACKETS` thresholds in `src/config.py` (fast, deterministic, no retrain).
  - Secondary: Tune HDP-HMM Dirichlet concentration prior (`kappa`/`alpha`) if the threshold-only fix is insufficient (principled, requires full retrain).
- **D-10:** Acceptance threshold — High-Vol frequency must fall in the range 15–25% of all days in the full history. This matches the NOTES.md target and aligns with empirical High-Vol frequency in SPY data.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Bug Locations

- `src/core/var_backtesting.py` — GARCH VaR computation; unit bug is here
- `src/core/orchestrator.py` — `walk_forward()` function; Procrustes fold alignment is here (replace with Hungarian)
- `src/pipeline/` — `stage_dashboard` function; NaN rows before PCA are the crash site
- `src/config.py` — `VOL_BRACKETS`, `USE_HDP`, `N_STATES`, `FEATURE_SUBSET`, `WALK_FORWARD_MODE` — calibration levers

### Phase Context

- `.planning/phases/07-daily-pipeline-clean-outputs/07-UAT.md` — Phase 7 UAT with full details on the 3 failures (exact error messages, confirmed across 3 runs)
- `NOTES.md` — Phase 9 priority order, target High-Vol range, list of key files

### Architecture

- `.planning/codebase/ARCHITECTURE.md` — pipeline layers, orchestration pattern, data flow
- `src/core/hmm_training.py` — `label_regimes()`, `fit_rolling_pca()`, `fit_regime_garch()` — context for the HMM calibration path
- `src/core/hmm_training.py` — `VOL_BRACKETS` usage via `src/core/hdp_hmm.py::label_regimes_hdp()` and `src/core/orchestrator.py::walk_forward()`

### Constraints

- `.planning/REQUIREMENTS.md` — K=3 locked, public signals API frozen (`detect()`, `fit()`, `bot_label`), no lookahead
- `.planning/PROJECT.md` — downstream consumers (Algo-Trading-Bot, Portfolio-Manager) depend on `regime_results.csv` schema — do not change column names

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `scipy.optimize.linear_sum_assignment` — already a dep via `scipy`; use for Hungarian matching in Plan 2
- `src/core/hmm_training.py::label_regimes()` — vol-bracket naming logic; reference for understanding the calibration path
- `scripts/analysis/analyze_regime_characterization.py` — Phase 4 diagnostic script; use as a template for the Plan 3 diagnostic
- `src/signals/trust.py::compute_trust_scorecard()` — aggregates validation checks; may need updating after GARCH fix

### Established Patterns

- All unit tests live in `tests/`; regression tests for each fix must follow the existing pytest pattern
- Config changes go in `src/config.py` only — no scattered magic numbers
- GARCH fitting is wrapped in try/except for graceful skip (< MIN_REGIME_OBS=50) — preserve this pattern when fixing units

### Integration Points

- `stage_dashboard` in `src/pipeline/` calls PCA — the NaN guard goes before this call
- `orchestrator.py::walk_forward()` is the single integration point for OOS label alignment — Plan 2 changes are contained here
- `src/config.py::VOL_BRACKETS` is used in both `hdp_hmm.py::label_regimes_hdp()` and `orchestrator.py::walk_forward()` — threshold changes in Plan 3 affect both

</code_context>

<specifics>
## Specific Ideas

- NOTES.md already defined the fix priority order: GARCH first → labels second → High-Vol third. This order is locked — Plan 1 is the unblock plan.
- The dashboard NaN crash has been confirmed across 3 consecutive runs (2026-04-25, 2026-04-26 manual, 2026-04-26 cron) per Phase 7 UAT. The HTML output is correct; only the exit code is wrong.
- High-Vol diagnostic should check vol distribution AFTER the GARCH fix is applied, since mean_vol=700%+ may have inflated the Vol Bracket assignments.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 9-Regime Calibration*
*Context gathered: 2026-05-05*
