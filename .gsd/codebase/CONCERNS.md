# Codebase Concerns

**Analysis Date:** 2026-03-16 (updated)

## Resolved Issues (from PLAN.md audit)

| # | Issue | Status | Resolution |
|---|-------|--------|------------|
| 1 | Winsorization lookahead | **RESOLVED** | `_winsorize()` now uses `expanding(min_periods=252).quantile()` — causal |
| 2 | Walk-forward standardization mismatch | **RESOLVED** | `walk_forward()` uses `expanding_standardize()` — same as `train()` |
| 3 | Walk-forward Viterbi instead of filtered | **RESOLVED** | `walk_forward()` uses `filtered_labels()` — same as `train()` |
| 4 | FRED publication lag bias | **N/A** | FRED data not used in current pipeline |
| 5 | No stationarity / VIF / importance testing | **RESOLVED** | `_validate_features()` has ADF, VIF, PCA loadings, Jarque-Bera |
| 6 | `features_raw.csv` is not raw | **RESOLVED** | Renamed to `features_transformed.csv` everywhere |
| 7 | Redundant FEATURE_SUBSET + unused scaler.pkl | **RESOLVED** | Duplicate filtering removed; `scaler.pkl` no longer produced |

## Tech Debt

**`train.py` is 2941 lines — monolithic module:**
- Issue: A single file contains expanding standardization, PCA, HMM fitting, SV/GARCH fitting, walk-forward validation, VaR backtests, 7 dashboard tab builders, and HTML generation
- Files: `train.py`
- Impact: Hard to navigate, test, or modify one area without risk of affecting others
- Fix approach: Split into `pca.py`, `validation.py`, `dashboard.py` sub-modules; `train.py` becomes a thin orchestrator

**`requirements.txt` uses semver ranges, not pinned versions:**
- Issue: `numpyro>=0.16`, `jax>=0.4.30` etc. mean fresh installs may break with future releases
- Files: `requirements.txt`
- Impact: Reproducibility risk — a JAX or NumPyro minor version bump has broken API before
- Fix approach: Pin to exact versions with `pip freeze > requirements.lock`

**Unused dependencies in `requirements.txt`:**
- Issue: `fredapi` and `matplotlib` are listed but never imported or used in any source file
- Files: `requirements.txt`
- Impact: Unnecessary install size; misleading about project capabilities
- Fix approach: Remove `fredapi` and `matplotlib` from `requirements.txt`

**Vestigial FRED references in `train.py`:**
- Issue: `evaluate()` and dashboard code reference `hy_spread`, `yield_slope` columns that don't exist in `market_data.csv`. Handled gracefully with `if col in market` guards, but misleading
- Files: `train.py` (lines 678-679, 1656-1657, 2833-2836)
- Impact: Confusing dead branches; dashboard tables show N/A for those rows
- Fix approach: Remove FRED column references or add actual FRED data back to `collect.py`

**Stale comment in `features.py` (`CURATED_FEATURES`):**
- Issue: Comment says "All 19 features" and "15 are selected" — actual counts are 17 features total, 13 selected by `FEATURE_SUBSET`
- Files: `features.py` lines 55-56
- Impact: Documentation mismatch
- Fix approach: Update comment to "17 features" and "13 selected"

**Legacy data files on disk:**
- Issue: `data/features_raw.csv`, `data/features_scaled.csv` (old), `models/scaler.pkl` still exist from prior runs but are no longer produced or consumed by current code
- Impact: Confusion about which files are active
- Fix approach: Delete legacy files; add them to `.gitignore`

**`run.py` argument dispatch uses if/elif chain:**
- Issue: `main()` uses a plain `if/elif` chain on `sys.argv[1]`; no `argparse` or `click`
- Files: `run.py`
- Impact: Adding new subcommands requires editing the chain carefully; unknown commands now caught but still fragile
- Fix approach: Replace with `argparse` subparsers or `click` commands

## Security Considerations

**API key in `.env`:**
- Risk: If `.env` is accidentally committed, any API key is exposed in git history
- Files: `.env`
- Current mitigation: `.env` should be listed in `.gitignore`
- Recommendations: Verify `.gitignore` includes `.env`

## Performance Bottlenecks

**JAX SVI training (3000 steps on CPU):**
- Problem: HDP-HMM inference is the dominant cost — ~5–15 minutes per full pipeline run
- Files: `hdp_hmm.py`, `config.py` (`SVI_NUM_STEPS=3000`)
- Cause: JAX is forced to CPU; SVI runs 3000 gradient steps over the full time series
- Improvement path: Reduce `SVI_NUM_STEPS` for exploratory runs; enable GPU if available; cache SVI results

**`build_interactive_dashboard()` builds all 7 tabs sequentially:**
- Problem: Dashboard generation is single-threaded; KDE surface computation is slow
- Files: `train.py` (line 1040)
- Improvement path: Compute tabs in parallel via `concurrent.futures.ThreadPoolExecutor`

**`walk_forward()` refits full model on every 21-day step:**
- Problem: OOS validation multiplies training time by number of steps
- Files: `train.py` (line 556)
- Cause: By design — rolling/expanding windows require re-fit
- Improvement path: Make walk-forward optional via config flag

## Fragile Areas

**Rolling PCA Procrustes alignment (`train.py::fit_rolling_pca()`):**
- Files: `train.py` line 198
- Why fragile: Procrustes aligns consecutive PCA loading matrices via `orthogonal_procrustes`; if the PCA subspace changes abruptly, alignment can fail silently, causing PC sign flips
- Safe modification: Always verify `mode_ratio` output; changing `PCA_ROLLING_WINDOW` requires checking alignment stability

**`HDPModelAdapter` interface shim (`hdp_hmm.py`):**
- Files: `hdp_hmm.py` line 689
- Why fragile: Provides `.transmat_` and `.n_components` to satisfy code in `train.py` written for `hmmlearn`. Any change to how `train.py` consumes the model object may break the adapter silently.
- Safe modification: When adding new accesses to the model object in `train.py`, check whether `HDPModelAdapter` needs a matching attribute

**`merge_similar_states()` in `hdp_hmm.py`:**
- Files: `hdp_hmm.py` line 478
- Why fragile: Merges HDP states down to `HDP_MAX_REGIMES=6` by KL-divergence; if merging produces degenerate state assignments, downstream code may silently mislabel regimes
- Safe modification: Add assertion that each merged state has at least `MIN_REGIME_OBS=50` observations

**In-training standardization depends on `FEATURE_SUBSET` alignment:**
- Files: `train.py::train()`, `config.py`
- Why fragile: `train.py` applies `FEATURE_SUBSET` to columns from `features_transformed.csv`; if `features.py` changes column names, `train.py` silently drops features
- Safe modification: After adding/renaming features in `features.py`, update `FEATURE_SUBSET` in `config.py` and verify column names match

## Scaling Limits

**Single-asset focus (SPY-centric):**
- Current capacity: Designed around SPY daily OHLCV; cross-asset features use 6 other tickers as context only
- Limit: Adding a second primary asset would require significant refactoring
- Scaling path: Parameterize `PRIMARY_TICKER` in `config.py`

## Dependencies at Risk

**`jax` / `jaxlib` version coupling:**
- Risk: JAX and `jaxlib` must be exact matching versions; `requirements.txt` uses `>=` which allows mismatched installs
- Impact: Import-time crash with cryptic error
- Migration plan: Pin `jax==X.Y.Z` and `jaxlib==X.Y.Z` to the same version

**`hmmlearn` (classic HMM path):**
- Risk: `hmmlearn` is the fallback when `USE_HDP=False`; it is less actively maintained
- Impact: Low — `USE_HDP=True` is the default
- Migration plan: Keep as fallback; no urgent action

## Missing Critical Features

**No automated data freshness check:**
- Problem: If `collect()` is skipped and existing `market_data.csv` is stale, the pipeline runs on stale data silently
- Suggested fix: Add data-age check in `train.py::train()` — warn if `market_data.csv` is older than 2 trading days

**No incremental update path:**
- Problem: Every pipeline run re-downloads all data and re-trains from scratch
- Suggested fix: Add `append_only=True` mode to `collect.py`; add `incremental=True` mode to `train.py`

## Test Coverage Gaps

**`filtered_probs()` (no lookahead guarantee):**
- What's not tested: No automated verification that forward-only filtering is actually applied
- Files: `train.py` line 115
- Risk: A refactor that accidentally uses `.predict()` (smoother) could introduce future lookahead undetected
- Priority: High

**`expanding_standardize()` (causality guarantee):**
- What's not tested: No automated verification that row t only uses data from [0..t]
- Files: `train.py` line 62
- Risk: A refactor could break the causal property
- Priority: High

**`features.py` individual indicators:**
- What's not tested: Garman-Klass vol, Parkinson vol, realized vol, VRP, VIX term structure
- Files: `features.py`
- Risk: A pandas API change could silently produce NaN or wrong values
- Priority: Medium

**`hdp_hmm.py` stick-breaking and forward algorithm:**
- What's not tested: `stick_breaking()`, `_diag_mvt_logpdf_batch()`, JAX `lax.scan` forward pass
- Files: `hdp_hmm.py`
- Risk: Silent numerical error in JAX could corrupt regime probabilities
- Priority: Medium

---

*Concerns audit: 2026-03-16 (updated)*
