# Codebase Concerns

**Analysis Date:** 2026-05-09

---

## Critical Blockers (Phase 9 In Progress)

### UAT Failure 1: GARCH VaR Scaling Bug

- Issue: `compute_var_backtest_garch()` scales returns to basis-point units (`spy_returns * 10000`) for GARCH optimizer stability, then uses `cond_vol_scaled` (still in 10000x units) when computing `var_dynamic`. The re-scaling path is correct inside GARCH but the `compare_var_methods()` path duplicates this logic independently — risk of unit mismatch if the duplication drifts.
- Files: `src/core/var_backtesting.py` lines 247–254, 319–327
- Impact: In Phase 7 UAT live run, `mean_vol=700%+` and `VaR=-546%` were observed — returns fed in wrong units somewhere upstream. Risk limits and bot position sizing are unreliable until fixed.
- Fix approach: Normalize to a single authoritative scaling function; audit every callsite that passes `spy_returns` to GARCH functions and assert decimal vs scaled units at function boundary. Phase 9, Step 1.

### UAT Failure 2: Label Variant Explosion (Walk-Forward)

- Issue: OOS walk-forward (`orchestrator.py::walk_forward()`) produces 8 distinct regime name strings instead of the expected 3. The VIX-rank label assignment per fold (`fold_name_map`) works correctly in isolation but can produce combined `unique_names` from `valid_names.unique()` that exceed `n_states` if any fold produced a `Regime-{r}` fallback string (e.g., edge folds with short windows or mismatched `REGIME_NAMES` keys).
- Files: `src/core/orchestrator.py` lines 128–145
- Impact: Downstream bot label mapping (`LABEL_MAPPING` in `config.py`) cannot resolve unknown variant strings. `signals.py` validation fails or silently drops regimes.
- Fix approach: Assert `len(unique_names) == n_states` before returning; add guard so short folds inherit nearest valid fold labels rather than emitting fallback strings. Phase 9, Step 2.

### UAT Failure 3: High-Vol Regime Dominance (61% of Days)

- Issue: HDP-HMM assigns High-Vol to ~61% of trading days; expected frequency is 15–25% (matching historical VIX elevated periods). Root cause is prior miscalibration — `HDP_ALPHA=1.0` (concentration) in `config.py` does not impose parsimony on the global DP.
- Files: `src/config.py` line 93, `src/core/hdp_hmm.py` prior setup
- Impact: Regime signals overstate risk; bot over-hedges in Med-Vol periods mis-labeled as High-Vol.
- Fix approach: Tune `HDP_ALPHA` and regime-assignment thresholds; use empirical VIX quantiles (VIX > 25 = High-Vol ~15% of days historically) as calibration target. Phase 9, Step 3.

---

## Tech Debt

### Static VaR Still Present in Codebase

- Issue: `compute_var_backtest()` is deprecated but remains in `src/core/var_backtesting.py` (exported in `__all__`). `compare_var_methods()` calls it directly. Any new caller can accidentally import the deprecated function — the deprecation warning only fires at runtime, not at import.
- Files: `src/core/var_backtesting.py` lines 38–84, 399
- Impact: Silent production risk if someone calls static VaR; Christoffersen test failure (p=0.0039) means clustering exceedances will not be caught.
- Fix approach: Remove from `__all__`; gate behind an explicit `_deprecated=True` kwarg; add a module-level `__deprecated__` marker.

### Duplicate GARCH Fitting Logic

- Issue: GARCH fitting code is copy-pasted between `compute_var_backtest_garch()` and `compare_var_methods()` (lines 247–254 vs 319–327). Both blocks independently set `y = spy_returns.dropna() * 10000` and refit the full ARCH model.
- Files: `src/core/var_backtesting.py` lines 247–267 and 316–345
- Impact: Any fix to scaling units or GARCH parameters must be applied in two places; the UAT scaling bug (see above) exploits exactly this duplication.
- Fix approach: Extract a private `_fit_garch_model(spy_returns)` returning `(res, y_scaled, cond_vol_decimal)` tuple; both callers use it.

### Procrustes Alignment Applied to Loadings, Not Scores

- Issue: `fit_rolling_pca()` in `src/core/pca_utils.py` applies Procrustes to `pca.components_` (loadings matrix) then re-projects scores. Procrustes minimizes Frobenius norm on loadings, not on score trajectories — optimal rotation for loadings is not identical to score-space stability.
- Files: `src/core/pca_utils.py` lines 94–103
- Impact: Residual PCA drift is the root cause of the OOS fragmentation issue (KNOWN_ISSUES #1). Fixed PCA with Procrustes-aligned loadings is a workaround; true fix would be score-space alignment.
- Fix approach: Future work — apply Procrustes to the score matrix directly (time × components), not loadings. See `docs/KNOWN_ISSUES.md` Issue #1 future work.

### NOTES.md / docs/NOTES.md Divergence

- Issue: Two NOTES.md files exist: `NOTES.md` (root, reflects v1.1 post-Phase 7 state) and `docs/NOTES.md` (reflects Phase 2.5 state as if production-ready). These contain contradictory status information — `docs/NOTES.md` declares "DEPLOY TO PRODUCTION" while `NOTES.md` shows three critical UAT failures.
- Files: `/NOTES.md`, `/docs/NOTES.md`
- Impact: Confusing cold-start for any Claude session or human developer; wrong file read = wrong understanding of current state.
- Fix approach: Archive `docs/NOTES.md` (rename to `docs/NOTES_phase2.5.md`) and add a redirect comment; `NOTES.md` at root is authoritative.

### Feature Count Discrepancy Across Documents

- Issue: `CLAUDE.md` (hard constraints) specifies 6 features selected in Phase 2.5.2; `NOTES.md` (v1.1) specifies 14 active features in `FEATURE_SUBSET`; `docs/NOTES.md` specifies 6 features. `config.py` `FEATURE_SUBSET` is the actual source of truth but the contradiction creates confusion.
- Files: `CLAUDE.md`, `NOTES.md`, `docs/NOTES.md`, `src/config.py`
- Impact: Implementation uncertainty when modifying feature pipeline; Phase 5 expanded features without updating CLAUDE.md constraints.
- Fix approach: Update `CLAUDE.md` hard constraints to reflect current 14-feature set; add comment in `config.py` referencing the Phase 5+6 decision log.

---

## Known Bugs

### `test_dashboard_refactor.py::test_dashboard_loads_regime_results` — Zombie Test

- Symptoms: Tests an import/function that no longer exists after dashboard.py was refactored.
- Files: `tests/test_dashboard_refactor.py` lines 97–107
- Trigger: Any `pytest tests/test_dashboard_refactor.py` run
- Workaround: Test is not currently `xfail`-marked so may or may not pass depending on current state of `dashboard.py`

### `test_model_card_validation.py` — Windows Subprocess Path Failure

- Symptoms: `subprocess.run(["pytest", ...])` fails on Windows due to path separator issues.
- Files: `tests/test_model_card_validation.py` line 123
- Trigger: Running test suite on Windows; WSL2 runs fine.
- Workaround: Run pytest natively via WSL2 only.

### `test_regime_count_selection.py` — Stale K=4 Logic

- Symptoms: Test was written against K=4 regime count; K was reverted to K=3 in Phase 2.5.3. Test also requires live market data download.
- Files: `tests/test_regime_count_selection.py`
- Trigger: Any offline/cached test run; will fail on K assertion and data absence.
- Workaround: Skip manually; `test_model_card_validation.py` references this test as a subprocess call which also fails.

### `collect.py` Bare `pass` in Exception Handler

- Symptoms: Data collection silently swallows an exception at line 169.
- Files: `src/features/collect.py` line 169
- Trigger: If macro data fetch fails, the exception is silently discarded; downstream `features.py` will warn about missing `macro_path` but the root cause is hidden.
- Workaround: Check for the `features.py` warning: `WARNING: {macro_path} missing — FRED features...`

---

## Security Considerations

### FRED API Key in Environment Only

- Risk: `FRED_API_KEY` defaults to empty string (`os.getenv('FRED_API_KEY', '')`) — no validation that the key is present before making FRED API calls. Empty key silently produces no macro data.
- Files: `src/config.py` line 25
- Current mitigation: `features.py` prints a WARNING when macro file is missing, but does not halt the pipeline.
- Recommendation: Raise a `EnvironmentError` at startup if `FRED_API_KEY` is empty and FRED features are in `FEATURE_SUBSET`.

---

## Performance Bottlenecks

### HDP-HMM Training: ~4 Hours Per Full Run

- Problem: Full HDP-HMM training via NumPyro SVI on 16 years of daily data takes approximately 4 hours.
- Files: `src/core/hdp_hmm.py`, `src/core/hmm_training.py`
- Cause: SVI with NUTS sampler on high-dimensional latent state sequences; no GPU acceleration; single-threaded JAX on CPU.
- Improvement path: Phase 8 targets optimization (SVI step count tuning, warm-starting from previous parameters, JAX JIT compilation review).

### Walk-Forward Validation: Quadratic Cost

- Problem: `walk_forward()` in `orchestrator.py` refits the full GARCH model and HMM per fold with no caching of intermediate results.
- Files: `src/core/orchestrator.py`
- Cause: Each fold independently calls `_fit_hmm()` with 5 random seeds and `arch_model().fit()`.
- Improvement path: Cache fitted model parameters per fold; skip refitting if training window unchanged.

### Data Ingestion: 16-Year Full Re-Download

- Problem: Every pipeline run without the incremental cache re-downloads 16 years of market data (~10–20 minutes overhead).
- Files: `src/features/collect.py`, `src/data/collect_macro.py`
- Cause: Incremental cache (Phase 2.1) uses delta detection on CSV/Feather; cache miss triggers full reload.
- Improvement path: Completed in Phase 2.1 for the happy path (~30 sec subsequent runs); concern is cache invalidation logic — any schema change to feature columns forces a full re-download.

---

## Fragile Areas

### `signals.py` — 818 Lines, Multiple Responsibilities

- Files: `src/signals/signals.py`
- Why fragile: Single file handles GARCH VaR computation, regime signal generation, bot label validation, trust scoring integration, and warning flag emission. Any change to one responsibility risks breaking another.
- Safe modification: Run `tests/test_section_signals.py`, `tests/test_bot_integration.py`, and `tests/test_trust_scorecard.py` after any change.
- Test coverage: Partially covered; GARCH VaR path has the active scaling bug showing coverage gaps.

### `hdp_hmm.py` — 838 Lines, Core Model

- Files: `src/core/hdp_hmm.py`
- Why fragile: Bayesian HDP-HMM implementation in NumPyro SVI. JAX tracing semantics make debugging difficult (silent shape errors, traced vs concrete value errors). R-hat and ESS convergence warnings are printed but not enforced as hard failures.
- Safe modification: Only modify with exact JAX/NumPyro version match (`jax==0.9.1`, `numpyro==0.20.0`). Run `tests/test_hdp_decision.py` and `tests/test_calibration.py` after any change. Check R-hat < 1.05 and ESS > 100 in output.
- Test coverage: `tests/test_hdp_decision.py` covers the HDP/non-HDP decision path; the SVI internals are not unit-tested.

### `config.py` — Single Source of Truth for All Parameters

- Files: `src/config.py`
- Why fragile: `LABEL_MAPPING`, `FEATURE_SUBSET`, `N_STATES`, `HDP_ALPHA`, `REGIME_NAMES`, `REGIME_HOLD_DAYS`, cache paths, and all thresholds live in one file. Changing any parameter affects the entire pipeline and downstream bot integration.
- Safe modification: Any change to `LABEL_MAPPING` or `N_STATES` requires coordinating with `algo-trading-bot` and `portfolio-manager`. Run `tests/test_bot_integration.py` first.

### Rolling PCA + Procrustes Alignment — Currently Broken

- Files: `src/core/pca_utils.py`, `src/core/hmm_training.py`
- Why fragile: Procrustes alignment is documented as the fix for OOS regime fragmentation but Phase 7 UAT revealed the label variant explosion bug. The alignment is not producing stable labels across walk-forward folds.
- Safe modification: Do not modify `fit_rolling_pca()` without running `tests/test_oos_fragmentation.py` and verifying OOS regime count stays at 3.

---

## Dependencies at Risk

### JAX / NumPyro / JAXlib — Exact Pins Required

- Risk: Any loosening of `jax==0.9.1`, `numpyro==0.20.0`, `jaxlib==0.9.1` in `requirements.txt` will silently corrupt regime label reproducibility due to breaking changes in these libraries.
- Impact: Regime labels change; bot receives wrong signals; backtest results no longer reproducible.
- Files: `requirements.txt`
- Migration plan: Do not upgrade without a full reproducibility audit comparing regime label sequences before and after. CI job `check-version-pins` in `.github/workflows/tests.yml` rejects loose constraints.

### `arch` Package — Optional Import

- Risk: `compute_var_backtest_garch()` uses `from arch import arch_model` inside the function body (lazy import). If `arch` is not installed, the function silently returns an empty DataFrame instead of raising an error.
- Files: `src/core/var_backtesting.py` lines 242–245
- Impact: GARCH VaR silently drops out of pipeline; signals output will be missing `garch_var_95` field, failing bot schema validation — but only at runtime, not at import.
- Migration plan: Add `arch` to `requirements.txt` with pinned version; move import to module level with a clear `ImportError` message.

---

## Test Coverage Gaps

### GARCH VaR Scaling Path — No Unit Test

- What's not tested: The unit handling inside `compute_var_backtest_garch()` (basis-point scaling and descaling). The scaling bug that produced `VaR=-546%` in Phase 7 UAT was not caught by any test.
- Files: `tests/test_var_backtesting.py`, `src/core/var_backtesting.py`
- Risk: Future scaling regressions will reach production undetected.
- Priority: High — fix alongside Phase 9 GARCH bug.

### Walk-Forward Label Variant Count — No Assertion

- What's not tested: `walk_forward()` has no test asserting that `len(unique_names) == n_states`. The label variant explosion (8 variants instead of 3) passed through undetected.
- Files: `tests/test_walk_forward.py`, `src/core/orchestrator.py`
- Risk: Any future fold-edge-case can re-introduce variant explosion without CI catching it.
- Priority: High — add assertion in Phase 9.

### HDP-HMM SVI Convergence — No Test

- What's not tested: R-hat > 1.05 or ESS < 100 are printed as warnings but never asserted as test failures. A non-converged model silently produces regime labels.
- Files: `src/core/hdp_hmm.py` lines 640–641, `tests/test_hdp_decision.py`
- Risk: Non-converged HDP-HMM passes all CI checks and produces unreliable regime labels for the bot.
- Priority: Medium.

### `collect.py` Error Paths — Bare `pass` Not Tested

- What's not tested: The silent exception handler at line 169 in `src/features/collect.py`. No test covers what happens when a data source fetch fails mid-collection.
- Files: `tests/test_incremental_collection.py`, `src/features/collect.py` line 169
- Risk: Silent data corruption or empty feature columns that only manifest as NaN warnings downstream.
- Priority: Medium.

---

## Scaling Limits

### HDP-HMM: 16-Year Daily Data (Approx 4,000 Observations)

- Current capacity: Handles 2010–2026 daily data well on CPU (4-hour run).
- Limit: Quadratic memory cost in NumPyro's SVI for the HMM forward-backward messages; doubling history to 32 years would roughly quadruple runtime.
- Scaling path: Phase 8 targets runtime optimization; longer term — GPU JAX backend or approximate inference with stochastic mini-batches.

---

## Missing Critical Features

### No End-to-End Bot Validation in CI

- Problem: `tests/test_bot_integration.py` validates signal schema (5 tests) but does not run the full pipeline and pass signals to a mock Algo-Trading-Bot consumer.
- Blocks: Guaranteeing that a full pipeline run from `run.py` produces output the bot can actually consume without schema errors.
- Files: `tests/test_bot_integration.py`

### No Alerting for GARCH Lag During Regime Shifts in Automated Runs

- Problem: `signals.py::varhhmm_warning()` generates a warning string but there is no mechanism to deliver this alert to the bot or to an operator during an automated overnight run.
- Blocks: Timely human intervention during regime shift periods when VaR underestimates tail risk by 5–20 days.
- Files: `src/signals/signals.py`, `src/signals/trust.py`

---

*Concerns audit: 2026-05-09*
