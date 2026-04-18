---
phase: 02-incremental
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - config.py
  - collect.py
  - features.py
  - train.py
  - dashboard.py
  - run.py
  - tests/test_incremental_collection.py
  - tests/test_pca_caching.py
  - tests/test_dashboard_refactor.py
  - analyze_feature_importance.py
  - analyze_regime_characterization.py
  - analyze_signal_quality.py
  - README.md
autonomous: true
requirements: [R1, R2, R3, R6, R7, R8, R9]
must_haves:
  truths:
    - "First run downloads 16 years of data (~20 min), caches it"
    - "Subsequent runs fetch only new data (~5 min) via delta detection"
    - "PCA is cached and reloaded, refitted on latest 252-day window"
    - "Dashboard shows regime labels + probabilities + trust scorecard only"
    - "Analysis scripts run independently; not imported by pipeline"
    - "All 28 existing tests pass; 10+ new tests added"
  artifacts:
    - path: "config.py"
      provides: "CACHE_PATH, CACHE_WINDOW, INCREMENTAL_MODE configuration"
      min_lines: 10
    - path: "collect.py"
      provides: "Incremental data collection with cache manifest and delta detection"
      exports: ["collect()"]
    - path: "features.py"
      provides: "PCA state management (reload_pca parameter)"
      exports: ["prepare_features()"]
    - path: "train.py"
      provides: "PCA checkpoint save/load in model training"
      exports: ["train()"]
    - path: "dashboard.py"
      provides: "Slim regime visualization (no analysis)"
      min_lines: 150
    - path: "analyze_feature_importance.py"
      provides: "PCA loadings + feature correlation analysis"
      exports: ["main()"]
    - path: "analyze_regime_characterization.py"
      provides: "Per-regime statistics (mean return, vol, skew)"
      exports: ["main()"]
    - path: "analyze_signal_quality.py"
      provides: "Regime persistence + transition matrix analysis"
      exports: ["main()"]
    - path: "tests/test_incremental_collection.py"
      provides: "8 test cases for cache lifecycle, delta detection, consistency"
      min_lines: 200
    - path: "tests/test_pca_caching.py"
      provides: "5 test cases for PCA checkpoint and causal verification"
      min_lines: 150
    - path: "tests/test_dashboard_refactor.py"
      provides: "6 test cases for dashboard and analysis script validation"
      min_lines: 100
  key_links:
    - from: "collect.py"
      to: "data/cache/.cache_manifest.json"
      via: "manifest tracking (hash, mod_time, last_fetch_date per ticker)"
      pattern: "json.dump|json.load"
    - from: "collect.py"
      to: "data/cache/{ticker}_incremental.csv"
      via: "CSV append on delta detection"
      pattern: "to_csv.*mode=.a"
    - from: "features.py"
      to: "train.py"
      via: "prepare_features() returns (df, pca_object)"
      pattern: "return.*pca"
    - from: "train.py"
      to: "models/regime_model.pkl"
      via: "joblib.dump(pca_object) in checkpoint"
      pattern: "joblib.dump.*pca"
    - from: "dashboard.py"
      to: "data/regime_results.csv"
      via: "loads regime probabilities and labels only"
      pattern: "read_csv.*regime_results"

---

<objective>
Phase 2 optimizes the Regime-Detection pipeline for incremental data updates and refactors the dashboard to focus on regime detection results (removing analysis bloat).

**What:** Implement 3 sub-phases:
- 2.1: Incremental data collection (cache + delta detection, <5 min per run)
- 2.2: Dashboard refactoring (slim to results visualization)
- 2.3: PCA optimization (rolling refit with causal guarantees)

**Why:** Eliminate 10–20 min overhead on every pipeline run; decouple analysis from detection system; maintain causality guarantees.

**Output:** 
- Optimized `collect.py` with CSV+Feather caching + auto-detect mode
- Refactored `dashboard.py` (regime labels, probabilities, trust scorecard only)
- PCA checkpoint save/load in `train.py`
- 3 analysis scripts (`analyze_*.py`) decoupled from pipeline
- 19+ tests (28 existing + 11 new, all passing)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/02-incremental/02-CONTEXT.md (11 locked decisions: D-01 to D-11)
@.planning/phases/02-incremental/02-RESEARCH.md (architecture patterns, standard stack)
@.planning/REQUIREMENTS.md (R1–R10 functional/non-functional requirements)
@.planning/ROADMAP.md (Phase 2 spec)
@.planning/STATE.md (Phase 1 complete, 28 tests baseline)
@CLAUDE.md (hard constraints: NumPyro, causality, 3 regimes, reproducibility)

## Key Design Decisions (Locked, D-01 to D-09)

**D-01: Delta Detection Strategy**
File hash + modification time comparison. Catches data corrections from yfinance/FRED.
Stored in `.cache_manifest.json` alongside cache.

**D-02: Cache Format**
CSV per ticker (human-readable, append-friendly) + Feather index (columnar, fast).
Structure: `data/cache/{ticker}_incremental.csv` + `{ticker}_index.feather` + `.cache_manifest.json`

**D-03: Mode Exposure**
Auto-detect (implicit): If cache exists + valid → incremental mode; else → full mode.
Zero configuration, no CLI flags.

**D-04: Data Consistency**
Hybrid: Drop duplicates (keep first), forward-fill 1-day gaps, fail loudly on schema changes or >10-day gaps.

**D-05: Dashboard Scope**
Slim to regime visualization: current regime, probability history, trust scorecard.
Remove: feature heatmaps, PCA diagnostics, regime characterization, correlation matrices.

**D-06: Analysis Decoupled**
Separate `analyze_*.py` scripts (not imported by pipeline/dashboard).
Run manually when user wants analysis, optional for bot integration.

**D-07: PCA Update Strategy**
Rolling refit on latest 252 trading days (1 year window).
Captures feature covariance shifts; still causal (no future data).

**D-08: Standardization**
Keep existing expanding-window z-score (already causal, verified by test_causality.py).

**D-09: Backward Compatibility**
Batch API unchanged; no separate live mode (Phase 3+).
Workflow: collect (delta or full) → features → train (refit on full history) → signals.

## Standard Stack

- **pandas 3.0.1**: CSV I/O, Feather support, data manipulation
- **pyarrow**: Feather index storage (fast columnar cache)
- **numpy 2.4.3**: Hash computation, data validation
- **joblib 1.5.3**: PCA checkpoint serialization
- **scikit-learn 1.8.0**: Rolling PCA with 252-day window
- **hashlib** (stdlib): File hash delta detection (SHA256)

## Existing Code References

**Current implementation:**
- `collect.py` (80 lines) — Downloads OHLCV+VIX; extend with caching
- `features.py` (300+ lines) — Feature engineering; add PCA state management
- `train.py` (1452 lines) — HMM training; update to cache/reload PCA
- `config.py` (100+ lines) — Add CACHE_PATH, CACHE_WINDOW, INCREMENTAL_MODE
- `dashboard.py` (600+ lines) — Streamlit app; refactor to remove analysis
- `run.py` (150+ lines) — Orchestration; minimal changes (mode detection)

**Existing test suite:**
- 28 tests: causality (10), validation, bot_integration (5), oos_validation, trust_scorecard, calibration
- All must pass after Phase 2 changes (no regressions)
- CI/CD target: <2 min runtime

</context>

<tasks>

<task type="auto">
  <name>Task 1: Extend config.py with Cache Paths and PCA Window</name>
  <files>config.py</files>
  <action>
Add 5–10 lines to config.py to define incremental caching parameters:
- CACHE_PATH = 'data/cache' (where to store CSV files and manifest)
- CACHE_WINDOW = 252 (trading days for rolling PCA refit; must be > 252 to guarantee history exists)
- INCREMENTAL_MODE = 'auto' (auto-detect based on cache existence)
- Add DATA_DIR if not already present (required by collect.py imports)

These parameters are referenced in subsequent tasks (collect.py, features.py, train.py).
No breaking changes to existing config; all new params have sensible defaults.
Verify all 100+ existing config params remain unchanged.
  </action>
  <verify>
    <automated>grep -n "CACHE_PATH\|CACHE_WINDOW\|INCREMENTAL_MODE\|DATA_DIR" config.py | head -10</automated>
  </verify>
  <done>config.py includes CACHE_PATH, CACHE_WINDOW, INCREMENTAL_MODE, DATA_DIR. Existing params unchanged. File is valid Python (no syntax errors).</done>
</task>

<task type="auto">
  <name>Task 2: Create Analysis Stub Scripts</name>
  <files>
    - analyze_feature_importance.py
    - analyze_regime_characterization.py
    - analyze_signal_quality.py
  </files>
  <action>
Create three stub Python modules. Each:
1. Has docstring explaining its purpose
2. Imports regime results CSV + trained model (paths TBD in Wave 2)
3. Implements empty main() function
4. Can be run standalone: `python analyze_*.py`
5. Does NOT import from collect.py, features.py, train.py, or run.py (standalone modules)

Stubs are 20–30 lines each, filled in Wave 2. Prevents import errors later when scripts are referenced.

Example stub:
```python
"""
Analyze feature importance: PCA loadings, feature correlation, variance explained.
Run standalone: python analyze_feature_importance.py
"""

def main():
    # Placeholder: to be implemented in Wave 2
    print("Feature importance analysis — placeholder")

if __name__ == '__main__':
    main()
```
  </action>
  <verify>
    <automated>for f in analyze_feature_importance.py analyze_regime_characterization.py analyze_signal_quality.py; do python "$f" 2>&1 | head -1; done</automated>
  </verify>
  <done>Three analysis scripts exist, each callable as `python analyze_*.py` without errors. Docstrings present.</done>
</task>

<task type="auto">
  <name>Task 3: Implement Cache Manifest and Delta Detection</name>
  <files>collect.py</files>
  <action>
Add to collect.py:

1. Function `_create_cache_manifest(tickers)` returns dict with {ticker: {hash, mod_time, last_fetch_date}}
   - Uses hashlib.sha256() on cached CSV files
   - Uses os.stat() for modification time
   - Returns dict with structure matching 02-RESEARCH.md example

2. Function `_detect_delta(manifest, tickers)` compares hashes and returns list of tickers needing refresh
   - Reads current manifest from `.cache_manifest.json`
   - Computes current hashes of cached CSV files
   - Compares; if hash changed → ticker needs re-fetch
   - Returns list of tickers with changed hashes (delta set)

3. Manifest file I/O
   - Write manifest to `data/cache/.cache_manifest.json` (use json.dump)
   - Load manifest from same path (use json.load)
   - First run with no cache → manifest created with all tickers marked as needing download
   - Second run → delta detection skips unchanged tickers

**Implementation notes:**
- Use hashlib.sha256(open(file, 'rb').read()).hexdigest() for file hash
- Use int(os.stat(file).st_mtime) for modification time
- Manifest structure:
  ```json
  {
    "last_run": "2026-04-13T18:32:00Z",
    "tickers": {
      "SPY": {"hash": "sha256_...", "mod_time": 1712973600, "last_fetch_date": "2026-04-13", "row_count": 3752},
      ...
    }
  }
  ```
- Per D-01, this catches data corrections (yfinance re-publishes adjusted prices, FRED revises estimates)
  </action>
  <verify>
    <automated>python -c "from collect import _create_cache_manifest, _detect_delta; print('Delta detection functions imported successfully')"</automated>
  </verify>
  <done>Manifest functions exist and are importable. Manifest JSON structure matches spec. File hash delta detection works.</done>
</task>

<task type="auto">
  <name>Task 4: Implement CSV+Feather Cache Layer</name>
  <files>collect.py</files>
  <action>
Add to collect.py:

1. Function `_load_cached_data(ticker, cache_path)` reads `{ticker}_incremental.csv` if exists
   - Returns DataFrame with columns matching input schema
   - Returns None/empty if no cache file exists
   - Uses pandas.read_csv(cache_path)

2. Function `_append_cache(df, ticker, cache_path)` appends new rows to CSV + updates feather index
   - If cache file exists: load it, concat with new data, drop duplicates by (date, ticker), write back to CSV
   - If cache file doesn't exist: write df as new CSV
   - Uses pandas.concat([old, new]).drop_duplicates(subset=['date', 'ticker'], keep='first').to_csv()
   - Creates/updates `{ticker}_index.feather` with metadata
   - Feather index format:
     ```json
     {
       "schema": "OHLCV + VIX series",
       "schema_version": 1,
       "row_count": <N>,
       "date_range": [<min_date>, <max_date>],
       "columns": [...],
       "dtype_checksum": "sha256..."
     }
     ```

3. Cache directory structure
   - `data/cache/` created if doesn't exist
   - One pair per ticker: `{ticker}_incremental.csv` + `{ticker}_index.feather`
   - Both files in same directory

**Implementation notes:**
- Use pandas.to_csv(..., mode='a', header=False) for append (if cache file exists; first write is normal)
- Use pandas.DataFrame.to_feather() to write feather index
- Feather index is JSON metadata (not a real pandas feather file), stored as JSON for auditability
  </action>
  <verify>
    <automated>python -c "from collect import _load_cached_data, _append_cache; print('Cache layer functions imported successfully')"</automated>
  </verify>
  <done>Cache functions exist and are importable. CSV append logic is implemented. Feather index structure matches spec.</done>
</task>

<task type="auto">
  <name>Task 5: Implement Hybrid Consistency Validation</name>
  <files>collect.py</files>
  <action>
Add to collect.py:

Function `_validate_cache(df, expected_schema)` performs all checks:
1. Silently drop duplicate rows: df.drop_duplicates(subset=['date', 'ticker'], keep='first')
2. Silently forward-fill single missing values: df.ffill(limit=1) per column
3. Raise ValueError if schema mismatch (different columns or dtypes)
4. Raise ValueError if gap >10 consecutive trading days detected
5. Log all actions (dups dropped, values filled, schema OK, etc.)

**Validation flow:**
```python
def _validate_cache(df, expected_schema):
    # Check schema (columns, dtypes)
    if set(df.columns) != set(expected_schema):
        raise ValueError(f"Schema mismatch: {set(df.columns)} vs {set(expected_schema)}")
    
    # Drop duplicates
    n_before = len(df)
    df = df.drop_duplicates(subset=['date', 'ticker'], keep='first')
    if len(df) < n_before:
        print(f"Dropped {n_before - len(df)} duplicate rows")
    
    # Forward-fill single gaps
    n_nan_before = df.isna().sum().sum()
    df = df.ffill(limit=1)
    n_nan_after = df.isna().sum().sum()
    if n_nan_after < n_nan_before:
        print(f"Forward-filled {n_nan_before - n_nan_after} missing values")
    
    # Check for >10-day gaps (trading days)
    df['date'] = pd.to_datetime(df['date'])
    date_diff = df['date'].diff().dt.days
    max_gap = date_diff.max()
    if max_gap > 10:
        raise ValueError(f"Gap of {max_gap} days detected (threshold: 10)")
    
    print("Cache validation passed")
    return df
```

**Integration with Task 4:**
- _validate_cache() is called in _append_cache() before writing to CSV
- Per D-04, this ensures data consistency (hybrid strategy)
  </action>
  <verify>
    <automated>python -c "from collect import _validate_cache; print('Validation function imported successfully')"</automated>
  </verify>
  <done>Validation function exists and is importable. Schema checks, duplicate drops, gap detection implemented.</done>
</task>

<task type="auto">
  <name>Task 6: Auto-Detect Mode in collect() Orchestration</name>
  <files>collect.py</files>
  <action>
Modify `collect()` function to auto-detect cache and choose mode:

1. Check if cache exists and is valid
   - Cache valid if: `data/cache/` exists AND `.cache_manifest.json` exists AND manifest is valid JSON
   - Cache invalid if: any check fails

2. Implement `_is_valid_cache()` helper
   - Returns True if cache directory exists, manifest file exists, manifest is valid JSON
   - Returns False otherwise

3. Update main collect() logic
   - If cache valid: call `_incremental_collect()` (new function, logic TBD in features.py)
   - If cache invalid/missing: call `_full_collect()` (current behavior)
   - Log which mode was triggered: "Mode: incremental, fetched 5 new rows for SPY"

4. Return tuple: (mode_used, delta_rows_count, tickers_refreshed)
   - mode_used: 'incremental' or 'full'
   - delta_rows_count: number of new rows fetched
   - tickers_refreshed: list of tickers that had new data

**Implementation notes:**
- _full_collect() is the current collect() logic (16-year backtest)
- _incremental_collect() is new: loads manifest → detects delta → fetches only new rows per ticker
- Per D-03, this is auto-detect mode (zero configuration)
- User runs `python run.py`, gets delta update if cache exists
- First run experience: user runs `python run.py`, gets 16-year backtest (slow but automatic)
  </action>
  <verify>
    <automated>python -c "from collect import collect; mode, delta, tickers = collect(); print(f'Mode: {mode}, Delta rows: {delta}, Tickers refreshed: {tickers}')"</automated>
  </verify>
  <done>collect() returns (mode_used, delta_rows_count, tickers_refreshed). Auto-detect logic works. First run and subsequent runs behave correctly.</done>
</task>

<task type="auto">
  <name>Task 7: Test Suite for Incremental Collection</name>
  <files>tests/test_incremental_collection.py</files>
  <action>
Create comprehensive test file with 8 test cases covering cache lifecycle, delta detection, consistency validation.

**Test cases:**

1. test_first_run_no_cache()
   - Verify: collect() with no cache → full download, cache created
   - Assert: cache directory exists, manifest file exists, CSV files created

2. test_second_run_with_cache()
   - Verify: second collect() with cache → delta only, fewer rows than first run
   - Assert: mode == 'incremental', delta_rows_count >= 1 and < first run row count

3. test_hash_mismatch_retriggers_fetch()
   - Verify: modify cached CSV file → hash mismatch → ticker re-fetched
   - Assert: ticker in tickers_refreshed list

4. test_cache_with_duplicates_validation()
   - Verify: inject duplicate rows in cache → validation drops dups
   - Assert: df after validation has no duplicates

5. test_cache_with_large_gap_fails()
   - Verify: create cache with >10-day gap → validation raises ValueError
   - Assert: _validate_cache() raises with message about gap

6. test_schema_change_raises_error()
   - Verify: change cache schema (new/missing column) → validation raises ValueError
   - Assert: _validate_cache() raises with message about schema mismatch

7. test_forward_fill_single_missing_value()
   - Verify: inject 1 missing value in cache → validation fills it silently
   - Assert: df after validation has no NaN in that position

8. test_existing_tests_still_pass()
   - Verify: all 28 existing tests pass after incremental changes
   - Assert: pytest tests/ -x returns 0 (all tests pass)

**Implementation notes:**
- Use pytest fixtures for mock data (small DataFrames with 100+ rows)
- Use temporary directories (tmpdir) for cache testing
- All tests should run in <30 sec total
- Tests should be independent (no shared state)
  </action>
  <verify>
    <automated>pytest tests/test_incremental_collection.py -v 2>&1 | tail -20</automated>
  </verify>
  <done>All 8 incremental collection tests pass. Coverage includes cache lifecycle, delta detection, consistency, and regression checks.</done>
</task>

<task type="auto">
  <name>Task 8: Extend features.py for PCA State Management</name>
  <files>features.py</files>
  <action>
Modify `prepare_features()` to accept and return PCA state:

1. Update function signature
   - From: `prepare_features(market, ...)`
   - To: `prepare_features(market, reload_pca=None, pca_window=252, ...)`
   - reload_pca: optional scikit-learn PCA object from prior run
   - pca_window: number of trading days for rolling PCA refit (default 252)

2. Implement PCA state logic
   - If reload_pca provided: use it to transform features (call pca.transform())
   - If not provided: compute PCA from scratch on latest pca_window rows
     ```python
     if reload_pca is None:
         pca = PCA(n_components=5, random_state=42)
         pca.fit(standardized_features[-pca_window:, :])
     else:
         pca = reload_pca
     X_pca = pca.transform(standardized_features)
     ```

3. Return tuple: (features_df, pca_fitted_object)
   - features_df: DataFrame with PCA-transformed features (5 components)
   - pca_fitted_object: fitted scikit-learn PCA object (for checkpoint)

4. Maintain causality
   - Standardization uses expanding window (unchanged, verified by test_causality.py)
   - PCA fitted on latest 252 rows (never uses future data)
   - All existing causality guarantees preserved

5. Reuse existing functions
   - Use existing `_expanding_standardize()` for z-score (don't change)
   - Use scikit-learn PCA (already imported?)

**Implementation notes:**
- Per D-07, rolling refit on 252 days captures feature covariance shifts
- Per D-08, standardization is expanding-window (no change)
- PCA object must be serializable (scikit-learn PCA is; joblib can pickle it)
  </action>
  <verify>
    <automated>python -c "from features import prepare_features; import inspect; sig = inspect.signature(prepare_features); print('Signature:', sig)"</automated>
  </verify>
  <done>prepare_features() has reload_pca and pca_window parameters. Returns (features_df, pca_fitted_object). Causality maintained.</done>
</task>

<task type="auto">
  <name>Task 9: Update train.py to Cache and Reload PCA</name>
  <files>train.py</files>
  <action>
Modify `train()` to cache and reload PCA state:

1. Update train() signature
   - Add parameter: `reload_pca_checkpoint_path=None`
   - On first run: checkpoint_path is None → compute PCA from scratch
   - On subsequent runs: load PCA from checkpoint and pass to prepare_features()

2. Implement PCA checkpoint save/load
   ```python
   # Load PCA (if available)
   if reload_pca_checkpoint_path and os.path.exists(reload_pca_checkpoint_path):
       pca_checkpoint = joblib.load(reload_pca_checkpoint_path)
       reload_pca = pca_checkpoint.get('pca')
   else:
       reload_pca = None
   
   # Call features with PCA
   features_df, pca_fitted = prepare_features(market, reload_pca=reload_pca, ...)
   
   # Save PCA in checkpoint
   model_checkpoint = {
       'pca': pca_fitted,
       'model': trained_hmm_model,
       'regime_results': regime_results_df,
   }
   joblib.dump(model_checkpoint, checkpoint_path)
   ```

3. Checkpoint format
   - Use joblib (already used in codebase for model serialization)
   - Path: `models/regime_model.pkl` (consistent with existing patterns)
   - Include: pca object, trained HMM model, regime results

4. Return value
   - train() should return: (model, pca_object, regime_results_df)
   - Allows downstream to use both model and PCA if needed

5. Maintain all guarantees
   - All 28 existing tests must pass
   - Causality tests verify no future data (test suite reuses existing causality patterns)
   - No breaking changes to train() API (backward compatible)

**Implementation notes:**
- joblib is already imported (check train.py imports)
- Checkpoint path should be configurable (use config.py if needed)
- Per D-09, batch API unchanged (no separate live mode)
  </action>
  <verify>
    <automated>python -c "from train import train; import inspect; sig = inspect.signature(train); print('Signature:', sig)"</automated>
  </verify>
  <done>train() has reload_pca_checkpoint_path parameter. PCA is saved to checkpoint on first run and reloaded on subsequent runs. Model checkpoint includes pca field.</done>
</task>

<task type="auto">
  <name>Task 10: Test Suite for PCA Caching and Causality</name>
  <files>tests/test_pca_caching.py</files>
  <action>
Create test file with 5 test cases for PCA checkpoint lifecycle and causality verification.

**Test cases:**

1. test_first_run_computes_pca()
   - Verify: first train() call computes PCA from scratch, saves to checkpoint
   - Assert: checkpoint file exists, contains 'pca' field, PCA object is sklearn.decomposition.PCA

2. test_second_run_reloads_pca()
   - Verify: second train() call loads PCA from checkpoint, uses it identically
   - Assert: mode behavior unchanged, new regimes computed using reloaded PCA

3. test_pca_fitted_on_latest_252_rows()
   - Verify: PCA is fitted only on latest 252 rows (1-year rolling window)
   - Assert: pca.n_features_in_ == feature_count, training data is latest 252 rows (not full history)

4. test_standardization_uses_expanding_window()
   - Verify: standardization still uses expanding window (per D-08)
   - Assert: early rows have different std than late rows (expanding window behavior)

5. test_no_future_data_in_pca()
   - Verify: PCA fitting does not use future data (causal guarantee)
   - Assert: reuse pattern from test_causality.py; fit PCA on t < T, verify transform at T doesn't depend on t+1..N

**Implementation notes:**
- Use pytest fixtures for mock market data (100+ rows of OHLCV)
- Use temporary directories (tmpdir) for checkpoint testing
- Reuse test data from existing causality tests (test_causality.py patterns)
- All tests should run in <20 sec total
- Tests should be independent
  </action>
  <verify>
    <automated>pytest tests/test_pca_caching.py -v 2>&1 | tail -20</automated>
  </verify>
  <done>All 5 PCA caching tests pass. Checkpoint lifecycle, causal verification, window sizes verified.</done>
</task>

<task type="auto">
  <name>Task 11: Refactor dashboard.py to Slim Visualization</name>
  <files>dashboard.py</files>
  <action>
Refactor dashboard.py to show regime labels, probabilities, and trust scorecard only.

**Keep (regime visualization):**
- Streamlit page structure (st.title, st.write, etc.)
- Load regime_results.csv (date, regime, prob_0, prob_1, prob_2)
- Load trust_scorecard.json (validation results)
- Display current regime label (large text, colored by regime)
- Display regime probability time series (line plot or stacked bars)
- Display trust scorecard table (8 validation checks, pass/fail icons)
- Optional: recent regime switches (table of dates and magnitudes)

**Remove (analysis code):**
- Feature heatmaps (PCA loadings, feature correlation) → move to analyze_feature_importance.py
- Regime characterization (mean return, vol, skew per regime) → move to analyze_regime_characterization.py
- PCA diagnostics (variance explained, loadings distribution) → move to analyze_feature_importance.py
- Correlation matrices → move to analyze_feature_importance.py
- Drawdown analysis, regime persistence → move to analyze_signal_quality.py
- Any code importing features.py, train.py, or model checkpoints (analysis scripts handle this)

**Target output:**
- dashboard.py ~150–200 lines (current ~600+ lines)
- Startup time <10 sec (current >15 sec with analysis)
- No imports from train.py or features.py
- Inputs: regime_results.csv, trust_scorecard.json only

**Implementation notes:**
- Keep: plotly or matplotlib for simple line plots
- Keep: Streamlit library and standard widgets
- Use pandas.read_csv() to load regime_results.csv
- Use json.load() to load trust_scorecard.json
- Organize code: separate functions for each section (current_regime(), probability_history(), scorecard_table())
  </action>
  <verify>
    <automated>python -c "import streamlit as st; import sys; sys.argv = ['streamlit', 'run', 'dashboard.py']; exec(open('dashboard.py').read()); print('Dashboard loads without errors')" 2>&1 | head -5</automated>
  </verify>
  <done>dashboard.py refactored to slim visualization. Loads regime_results.csv + trust_scorecard.json. Shows regime labels, probabilities, scorecard. Analysis code removed. Startup <10 sec.</done>
</task>

<task type="auto">
  <name>Task 12: Implement analyze_feature_importance.py</name>
  <files>analyze_feature_importance.py</files>
  <action>
Replace stub with full implementation:

**Purpose:** Analyze feature importance via PCA loadings and feature correlation.

**Inputs:**
- Load model checkpoint: `joblib.load('models/regime_model.pkl')` → extract pca object
- Load regime_results.csv for date range context
- Load raw market data (if available) for feature correlation matrix

**Analysis:**
1. PCA Loadings Heatmap
   - Extract pca.components_ (5 components × 13 features)
   - Plot as heatmap: y-axis = PC1, PC2, PC3, PC4, PC5; x-axis = feature names
   - Save to `analysis/pca_loadings.png`

2. Feature Correlation Matrix
   - Compute pairwise Pearson correlation of standardized features
   - Plot as heatmap with colorbar
   - Save to `analysis/feature_correlation.png`

3. Variance Explained
   - Extract pca.explained_variance_ratio_
   - Plot cumulative variance explained (line plot)
   - Save to `analysis/pca_variance_explained.png`

**Output:**
- Three PNG files in `analysis/` directory
- Console output: "Feature analysis complete. Files saved to analysis/"

**Implementation notes:**
- Do NOT import from collect.py, features.py, train.py, or run.py
- Use standalone joblib.load() to load checkpoint
- Use matplotlib or plotly for plots
- Create `analysis/` directory if doesn't exist
- Per D-06, this script is optional (not imported by pipeline)
  </action>
  <verify>
    <automated>python analyze_feature_importance.py 2>&1 | tail -5</automated>
  </verify>
  <done>analyze_feature_importance.py runs standalone. Generates PCA loadings heatmap, feature correlation, variance explained plots in analysis/ directory.</done>
</task>

<task type="auto">
  <name>Task 13: Implement analyze_regime_characterization.py</name>
  <files>analyze_regime_characterization.py</files>
  <action>
Replace stub with full implementation:

**Purpose:** Characterize regimes via statistics (mean return, vol, skew, kurtosis) and transition rates.

**Inputs:**
- Load regime_results.csv (date, regime, probs)
- Load raw market data (price returns) to compute regime-conditional statistics

**Analysis:**
1. Per-Regime Distributions
   - For each regime (0, 1, 2):
     - Filter regime_results to dates in regime
     - Compute SPY daily returns on those dates (from price data)
     - Calculate: mean return, volatility, skewness, kurtosis
     - Store in DataFrame: {regime: [mean_ret, vol, skew, kurt]}
   - Plot as bar chart or table
   - Save to `analysis/regime_statistics.csv` and `analysis/regime_stats.png`

2. Regime Transition Rates
   - Compute Markov transition matrix: P[regime_t+1 | regime_t]
   - Example: P[0→0] = n(0→0) / n(0_total), etc.
   - Plot as heatmap (3×3 transition matrix)
   - Save to `analysis/transition_matrix.png`

3. Regime Duration Stats
   - For each regime: compute duration (number of consecutive days)
   - Calculate: mean duration, median duration, min, max
   - Plot as bar chart (duration per regime)
   - Save to `analysis/regime_duration.png`

**Output:**
- regime_statistics.csv (per-regime stats)
- regime_stats.png (bar chart)
- transition_matrix.png (heatmap)
- regime_duration.png (bar chart)
- Console output: "Regime characterization complete. Files saved to analysis/"

**Implementation notes:**
- Do NOT import from collect.py, features.py, train.py, or run.py
- Use standalone pandas and numpy for calculations
- Use matplotlib or plotly for plots
- Create `analysis/` directory if doesn't exist
- Per D-06, this script is optional (not imported by pipeline)
  </action>
  <verify>
    <automated>python analyze_regime_characterization.py 2>&1 | tail -5</automated>
  </verify>
  <done>analyze_regime_characterization.py runs standalone. Generates regime statistics table, transition matrix, duration heatmaps in analysis/ directory.</done>
</task>

<task type="auto">
  <name>Task 14: Implement analyze_signal_quality.py</name>
  <files>analyze_signal_quality.py</files>
  <action>
Replace stub with full implementation:

**Purpose:** Analyze signal quality via regime persistence, transition rates, and forward-looking probabilities.

**Inputs:**
- Load regime_results.csv (date, regime, prob_0, prob_1, prob_2)

**Analysis:**
1. Regime Persistence
   - For each regime: compute number of consecutive days before regime switch
   - Calculate: mean persistence, median persistence, min, max
   - Plot as distribution (histogram or box plot)
   - Save to `analysis/regime_persistence.png`

2. Regime Probability Trends
   - For each regime: plot probability time series (prob_0, prob_1, prob_2 over time)
   - Use stacked area plot or line plot with colors
   - Save to `analysis/regime_probabilities.png`

3. Regime Confidence
   - For each timestamp: compute max(prob_0, prob_1, prob_2) (confidence)
   - Plot confidence time series
   - Calculate: mean confidence, median, min
   - Save to `analysis/regime_confidence.png`

4. Regime Switches
   - Count number of regime switches (regime_t ≠ regime_t+1)
   - Plot switch dates as vertical lines on regime time series
   - Save to `analysis/regime_switches.png`

**Output:**
- regime_persistence.png (distribution of regime duration)
- regime_probabilities.png (prob time series)
- regime_confidence.png (max prob time series)
- regime_switches.png (annotated regime changes)
- Console output: "Signal quality analysis complete. Files saved to analysis/"

**Implementation notes:**
- Do NOT import from collect.py, features.py, train.py, or run.py
- Use standalone pandas and numpy for calculations
- Use matplotlib or plotly for plots
- Create `analysis/` directory if doesn't exist
- Per D-06, this script is optional (not imported by pipeline)
  </action>
  <verify>
    <automated>python analyze_signal_quality.py 2>&1 | tail -5</automated>
  </verify>
  <done>analyze_signal_quality.py runs standalone. Generates regime persistence, probability time series, confidence, switches visualizations in analysis/ directory.</done>
</task>

<task type="auto">
  <name>Task 15: Test Suite for Dashboard and Analysis Scripts</name>
  <files>tests/test_dashboard_refactor.py</files>
  <action>
Create test file with 6 test cases for dashboard and analysis scripts.

**Test cases:**

1. test_dashboard_loads_regime_results()
   - Verify: dashboard loads regime_results.csv without errors
   - Assert: DataFrame has columns [date, regime, prob_0, prob_1, prob_2]

2. test_dashboard_renders()
   - Verify: streamlit dashboard page renders without exceptions
   - Assert: Streamlit session state initialized, no crashes

3. test_analyze_feature_importance_runs()
   - Verify: analyze_feature_importance.py runs without errors
   - Assert: analysis/ directory created, PNG files exist

4. test_analyze_regime_characterization_runs()
   - Verify: analyze_regime_characterization.py runs without errors
   - Assert: analysis/ directory created, CSV and PNG files exist

5. test_analyze_signal_quality_runs()
   - Verify: analyze_signal_quality.py runs without errors
   - Assert: analysis/ directory created, PNG files exist

6. test_all_existing_tests_pass()
   - Verify: all 28 existing tests still pass after refactoring
   - Assert: pytest tests/ -x returns 0 (no regressions)

**Implementation notes:**
- Use pytest fixtures for mock data (small regime_results.csv)
- Use temporary directories (tmpdir) for analysis script testing
- Mock Streamlit session if needed (import streamlit; mock st.write, etc.)
- All tests should run in <30 sec total
- Tests should be independent
  </action>
  <verify>
    <automated>pytest tests/test_dashboard_refactor.py -v 2>&1 | tail -20</automated>
  </verify>
  <done>All 6 dashboard and analysis tests pass. Dashboard loads and renders; all analysis scripts run without errors. No regressions in existing tests.</done>
</task>

<task type="auto">
  <name>Task 16: Update README with Incremental Mode Documentation</name>
  <files>README.md</files>
  <action>
Add section "Incremental Data Mode" to README explaining new behavior:

**Section content:**

```markdown
## Incremental Data Mode

The Regime-Detection pipeline automatically detects and uses incremental data collection to avoid re-downloading 16 years of historical data on every run.

### First Run (Full Backtest)
```bash
python run.py
```
First run downloads all historical data from FRED and yfinance (2010–present):
- Duration: ~20 minutes
- Creates cache: `data/cache/`
- Output: `data/regime_results.csv` with full regime history

### Subsequent Runs (Incremental Update)
```bash
python run.py
```
Subsequent runs detect the cache and fetch only new data:
- Duration: <5 minutes (typically 1–2 min)
- Detects changes via file hash + modification time
- Updates cache: `data/cache/{ticker}_incremental.csv`
- Output: `data/regime_results.csv` with updated regimes

### Force Full Re-Download
To force a full backtest re-download (ignoring cache):
```bash
rm -rf data/cache/
python run.py
```

### Analysis Scripts (Optional)
Analysis and visualization are decoupled from the core pipeline.

Run analysis manually when needed:
```bash
python analyze_feature_importance.py       # PCA loadings, feature correlation
python analyze_regime_characterization.py  # Per-regime statistics, transition rates
python analyze_signal_quality.py           # Regime persistence, probability trends
```

Analysis scripts are **optional** — not required for bot integration or dashboard.
```

**Integration notes:**
- Document that first run is slow but automatic
- Emphasize that incremental mode is zero-configuration
- Explain how to force full re-download (rm -rf data/cache/)
- List analysis scripts as optional
- Keep existing sections (Installation, Usage, Integration with Algo-Trading-Bot, etc.) unchanged
  </action>
  <verify>
    <automated>grep -A 5 "Incremental Data Mode" README.md</automated>
  </verify>
  <done>README updated with "Incremental Data Mode" section. Documents first run, subsequent runs, force full re-download, analysis scripts.</done>
</task>

<task type="auto">
  <name>Task 17: Update CI/CD for Test Validation</name>
  <files>.github/workflows/tests.yml</files>
  <action>
Update CI/CD workflow to validate all 38+ tests (28 existing + 11 new) and analysis scripts:

**Workflow steps:**

1. Test suite validation
   - Run all tests: `pytest tests/ -x --tb=short`
   - Assert: all tests pass (28 existing + 11 new = 39+)
   - Timeout: <2 min

2. Analysis script validation
   - Verify analyze_*.py files are importable and runnable
   - Run each script (with small mock data): `python analyze_*.py`
   - Assert: no errors, all complete in <30 sec

3. Linting (if applicable)
   - Run black or flake8 on refactored code
   - Assert: no linting errors in dashboard.py, analyze_*.py, test_*.py

4. Reproducibility check
   - Verify JAX/NumPyro versions are pinned exactly (per PHASE 1)
   - Assert: no `>=` constraints in requirements.txt

**Configuration:**
- Add test discovery: `pytest tests/test_incremental_collection.py tests/test_pca_caching.py tests/test_dashboard_refactor.py`
- Add analysis script checks: `for script in analyze_*.py; do python $script; done`
- Keep existing CI/CD checks (causality, bot_integration, etc.)

**Notes:**
- If .github/workflows/tests.yml doesn't exist, create it with basic pytest + linting
- Per Phase 1, CI/CD already has version-pin validation (keep it)
  </action>
  <verify>
    <automated>ls -la .github/workflows/ 2>&1 | head -10</automated>
  </verify>
  <done>CI/CD workflow validates all 38+ tests and analysis scripts. Runs in <2 min. Reproducibility checks in place.</done>
</task>

<task type="auto">
  <name>Task 18: Integration Verification and Final Test Run</name>
  <files>
    - config.py
    - collect.py
    - features.py
    - train.py
    - dashboard.py
    - run.py
    - tests/test_*.py
  </files>
  <action>
Final integration check: verify all components work together as a system.

**Test sequence:**

1. Verify config.py loads correctly
   - `python -c "from config import CACHE_PATH, CACHE_WINDOW, INCREMENTAL_MODE, DATA_DIR; print('OK')"`

2. Verify incremental collection works end-to-end
   - Run `python run.py` (first run, full download)
   - Check: cache created at data/cache/
   - Check: manifest file exists at data/cache/.cache_manifest.json
   - Check: CSV files exist for all tickers

3. Verify second run uses incremental mode
   - Run `python run.py` again (second run, incremental)
   - Check: mode printed as "Mode: incremental, fetched X new rows"
   - Check: runtime <5 min
   - Check: regime_results.csv updated with latest data

4. Verify dashboard loads
   - Start dashboard: `streamlit run dashboard.py`
   - Check: no errors, renders in <10 sec
   - Check: shows regime labels, probabilities, trust scorecard

5. Verify analysis scripts run
   - `python analyze_feature_importance.py` → creates analysis/ directory
   - `python analyze_regime_characterization.py` → creates analysis/ directory
   - `python analyze_signal_quality.py` → creates analysis/ directory

6. Run full test suite
   - `pytest tests/ -x --tb=short`
   - Assert: all 39+ tests pass
   - Assert: runtime <2 min

7. Run linting (if applicable)
   - `black --check . || black .` (or flake8)
   - Assert: no errors

**Success criteria:**
- First run completes (16-year backtest)
- Second run uses incremental mode (<5 min)
- Dashboard renders without errors
- All analysis scripts run successfully
- All 39+ tests pass
- No linting errors
  </action>
  <verify>
    <automated>pytest tests/ -x --tb=short 2>&1 | tail -5</automated>
  </verify>
  <done>All integration checks pass. Incremental collection works (first run full, subsequent runs delta). Dashboard renders. Analysis scripts run. All 39+ tests green. No regressions.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| External data sources → cache | yfinance/FRED API calls return data; cache stores it locally (potential for corruption, missing data) |
| Cache files → pipeline | Cached CSV files read by collect.py; corruption or tampering could corrupt regime signals |
| PCA checkpoint → train.py | Serialized PCA object loaded from disk; corruption could cause training failure or incorrect transforms |
| Dashboard input (CSV) → display | regime_results.csv loaded and rendered; missing/malformed data could cause display errors |
| Analysis scripts → file system | Scripts write PNG/CSV files to analysis/; permission errors or disk full could cause silent failures |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-01 | Tampering | Cache manifest (.cache_manifest.json) | Mitigate | Compute file hash of cached CSV files on every read (D-01); mismatch triggers re-fetch |
| T-02-02 | Spoofing | External data sources (yfinance/FRED) | Accept | Third-party responsibility; code trusts API responses as valid |
| T-02-03 | Repudiation | PCA checkpoint serialization | Mitigate | Save model checkpoints with version metadata (joblib includes version); incompatible versions caught at load-time |
| T-02-04 | Information Disclosure | Cache files (market data) | Accept | Cache contains publicly available market data (no PII, low-value target); stored locally with standard filesystem permissions |
| T-02-05 | Denial of Service | Cache corruption (large gap detected) | Mitigate | _validate_cache() detects >10-day gaps, raises ValueError; pipeline fails loudly (not silently) |
| T-02-06 | Elevation of Privilege | Analysis scripts write to analysis/ | Mitigate | Create analysis/ directory with restricted permissions; fail if write fails |

</threat_model>

<verification>
**Phase 2 Integration Verification:**

After all tasks complete, verify:

1. **Incremental Collection:**
   - [ ] First run downloads 16 years (cache created)
   - [ ] Second run fetches delta only (<5 min)
   - [ ] Mode auto-detected (no CLI flags)
   - [ ] Delta detection catches file hash changes

2. **PCA Optimization:**
   - [ ] PCA cached in checkpoint on first train
   - [ ] PCA reloaded and reused on subsequent trains
   - [ ] Rolling window (252 days) verified
   - [ ] Causality guarantees maintained (test_causality.py still green)

3. **Dashboard Refactoring:**
   - [ ] Dashboard loads regime_results.csv only (no analysis imports)
   - [ ] Shows regime labels, probabilities, trust scorecard
   - [ ] Analysis code removed (no heatmaps, PCA diagnostics, etc.)
   - [ ] Startup <10 sec (faster than current ~15 sec)

4. **Analysis Decoupling:**
   - [ ] analyze_feature_importance.py runs standalone (no pipeline imports)
   - [ ] analyze_regime_characterization.py runs standalone
   - [ ] analyze_signal_quality.py runs standalone
   - [ ] All produce outputs to analysis/ directory

5. **Test Coverage:**
   - [ ] All 28 existing tests pass (no regressions)
   - [ ] 11 new tests added (8 incremental + 5 PCA + 6 dashboard)
   - [ ] Total: 39+ tests passing
   - [ ] Runtime: <2 min

6. **Documentation:**
   - [ ] README updated with incremental mode docs
   - [ ] CLAUDE.md updated with Phase 2 notes (if applicable)
   - [ ] CI/CD validates all tests + analysis scripts

</verification>

<success_criteria>
Phase 2 complete when:

1. ✅ Incremental data collection implemented
   - Cache manifest + delta detection working
   - First run: full backtest (~20 min)
   - Subsequent runs: delta only (<5 min)
   - Auto-detect mode (zero configuration)

2. ✅ PCA optimization implemented
   - PCA state saved to checkpoint on first train
   - PCA reloaded and reused on subsequent trains
   - Rolling 252-day window for accuracy
   - Causality verified (no future data)

3. ✅ Dashboard refactored
   - Slim to regime visualization (labels, probabilities, scorecard)
   - Analysis removed (moved to separate scripts)
   - Startup <10 sec
   - No regressions (dashboard still loads and renders)

4. ✅ Analysis decoupled
   - 3 analyze_*.py scripts created (feature importance, regime characterization, signal quality)
   - Scripts run standalone (no pipeline imports)
   - Optional (not required for bot integration)

5. ✅ Test coverage
   - 28 existing tests pass (no regressions)
   - 11 new tests added (19+ total)
   - All tests passing in <2 min
   - CI/CD validates all tests + analysis scripts

6. ✅ Documentation updated
   - README: incremental mode section
   - Atomic commits: 18 tasks, each with clear commit message
   - No regressions in Phase 1 work

</success_criteria>

<output>
After completion, create `.planning/phases/02-incremental/02-01-SUMMARY.md` with:
- Execution summary (what was completed)
- All success criteria verified (checkmarks)
- Test results (39+ tests passing)
- Performance metrics (first run time, second run time, dashboard startup)
- Known issues or deviations (if any)
- Next steps (Phase 3, backlog work)
</output>
