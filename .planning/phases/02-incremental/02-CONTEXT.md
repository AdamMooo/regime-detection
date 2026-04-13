# Phase 2: Incremental Data Updates & Detection System — Context

**Gathered:** 2026-04-13 (Session #7)  
**Status:** Ready for planning  
**Mode:** Interactive discuss (core architecture decisions locked)

---

<domain>

## Phase Boundary

Optimize pipeline for incremental data updates and build a focused regime detection system. Remove analysis bloat from dashboard; decouple analysis into testing/research scripts.

**Sub-phases:**
- 2.1: Implement incremental data collection (delta detection + caching)
- 2.2: Dashboard refactoring (slim to results visualization)
- 2.3: Feature computation optimization (rolling PCA for accuracy)

</domain>

---

<decisions>

## Implementation Decisions

### 2.1 Incremental Data Collection

#### D-01: Delta Detection Strategy — File Hash + Modification Time
- **What:** Use file modification time + content hash to detect if source data changed since last fetch
- **Why:** Defensive approach catches data corrections from yfinance/FRED (price adjustments, economic revisions). Simple to implement.
- **How:** 
  - Before fetch: record `(ticker, file_hash, last_mod_time)` for each ticker
  - After fetch: compare hash/mod_time; if changed, fetch latest data
  - Store hashes in `.cache_manifest.json` alongside cached data
- **Alternative rejected:** Date-based delta (simpler but misses corrections) 
- **Implementation:** `collect.py::_detect_delta()` function checks manifest

---

#### D-02: Cache Format — CSV + Feather Index
- **What:** Store incremental data as plain CSV files (per ticker); maintain lightning-fast `.feather` index for quick lookups
- **Why:** 
  - CSV is human-readable (easy to debug, audit, manually inspect)
  - Feather provides columnar speedup for pandas operations
  - Parquet/SQLite add complexity; CSV+Feather is minimal overhead
  - Append-friendly (just append new rows to CSV)
- **How:**
  - Directory structure: `data/cache/{ticker}_incremental.csv` + `{ticker}_index.feather`
  - On append: write new rows to CSV, update feather index
  - Feather index stores: row_count, date_range, schema checksum
- **Alternative rejected:** SQLite (too heavy), Parquet (less debuggable), HDF5 (scientific overkill)
- **Implementation:** `collect.py` uses pandas to append CSV, pyarrow to write feather

---

#### D-03: Mode Exposure — Auto-Detect (Implicit Mode Switch)
- **What:** If cache exists, run in incremental mode (fetch deltas); otherwise full mode (16-year backtest)
- **Why:**
  - Zero configuration (no CLI flags or config params)
  - User still gets full backtest on first run (automatic)
  - Subsequent runs are fast (incremental by default)
  - Simplest mental model: "run script, it figures out what to do"
- **How:**
  - `run.py` checks if cache directory exists + has valid manifest
  - If cache valid → call `collect(mode='incremental')`
  - If cache missing/invalid → call `collect(mode='full')`
  - Log which mode was triggered (so user sees it)
  - User can force full mode via `rm -rf data/cache/` before running
- **Alternative rejected:** CLI flags (too many options), config param (less discoverable)
- **Implementation:** `collect.py::collect()` returns `(mode_used, delta_rows_fetched)`

---

#### D-04: Data Consistency — Hybrid Strategy
- **What:** 
  - Silently drop duplicate rows (keep first occurrence)
  - Silently forward-fill single missing values (align to SPY trading days)
  - **Fail loudly** if schema changes (new/missing tickers) or large gaps (>10 consecutive trading days missing)
- **Why:**
  - Duplicates and single-day gaps are expected in incremental updates (data source quirks)
  - Schema changes and large gaps indicate corruption/misconfiguration (must investigate)
  - Safe for trading: minor data quality losses don't break signal integrity; schema corruption does
- **How:**
  - After appending new rows to cache: `_validate_cache(cache_df)`
  - Check: column names match (schema), row count >= expected, no >10-day gaps
  - Drop duplicates by `(date, ticker)`, keep first
  - Forward-fill up to 1 missing value per ticker
  - Raise ValueError if schema or gap check fails
- **Implementation:** `collect.py::_validate_cache()` function

---

### 2.2 Dashboard Refactoring — Slim to Results

#### D-05: Dashboard Scope — Regime Visualization Only
- **What:** Dashboard shows:
  - Current regime label (Low-Vol / Medium-Vol / High-Vol) + confidence
  - Regime probability history (time series)
  - Trust scorecard (8 validation checks, all pass/fail)
  - (Optional) Recent regime switches (dates and magnitudes)
  - **Remove:** Feature heatmaps, regime characterization, PCA diagnostics, correlation matrices
- **Why:**
  - Regime detection system purpose is to **detect regimes**, not analyze why
  - Analysis (feature importance, regime economics) belongs in research scripts, not dashboard
  - Slim dashboard = faster to render, easier to maintain, clearer UX
- **How:**
  - Dashboard input: `regime_results.csv` (date, regime, probs)
  - Dashboard input: `trust_scorecard.json` (validation results)
  - Remove all feature/PCA visualization code from `dashboard.py`
  - Keep: line plot (regime probs over time), bar chart (current confidence)
  - Defer "why are we in this regime?" to `analyze.py` scripts
- **Implementation:** Refactor `dashboard.py` to load only regime results + trust scores

---

#### D-06: Analysis Decoupled — Separate Scripts
- **What:** Move analysis to separate `analyze_*.py` scripts (not imported by pipeline or dashboard)
- **Examples:**
  - `analyze_feature_importance.py` — PCA loadings, feature correlation
  - `analyze_regime_characterization.py` — regime mean returns, vol, skew per regime
  - `analyze_signal_quality.py` — regime persistence, transition rates
- **Why:**
  - Research and debugging don't need to run every time
  - Dashboard stays focused (faster, less dependency churn)
  - Analysis can be expensive (feature PCA diagnostics, backtesting metrics)
- **How:**
  - Move code from `dashboard.py` to new scripts
  - Scripts import regime_results + trained model, produce plots/reports
  - Run manually when user wants analysis: `python analyze_feature_importance.py`
  - Do NOT import analysis code in run.py or train.py
- **Implementation:** Create `analyze_*.py` modules, remove analysis from pipeline

---

### 2.3 Feature Computation Optimization (Accuracy First)

#### D-07: PCA Update Strategy — Rolling Refit
- **What:** When new data arrives:
  1. Append new raw features to cache
  2. Refit PCA on **latest N rows** (e.g., last 252 trading days = 1 year)
  3. Use new PCA components for all predictions (backtest and forward)
  4. Store PCA components in model checkpoint
- **Why:**
  - Most accurate: PCA components reflect current feature covariance
  - Captures regime shifts in feature correlations (e.g., stock-bond correlation flips)
  - Doesn't use future data (rolling window is causal)
  - Trade-off: slower than stateless, but accuracy > speed (per user priority)
- **How:**
  - `features.py::prepare_features()` now accepts optional `pca_window` param
  - If incremental: fit PCA on latest 252 rows, transform all historical + new rows
  - Store PCA fitted object in model checkpoint (joblib or pickle)
  - On reload: load PCA from checkpoint, use to transform new rows
- **Alternative rejected:** Stateless (fast but drifts), no incremental (current behavior)
- **Implementation:** Modify `features.py` and `train.py` to support rolling PCA refit

---

#### D-08: Standardization — Expanding Window (Already Causal)
- **What:** Keep existing expanding-window standardization (no change needed)
- **Why:** Already implements causality correctly (z-score computed only on past data)
- **How:** No refactoring; reuse existing `_expanding_standardize()` function
- **Note:** This is verified by `test_causality.py::TestExpandingStandardize` (3 tests)
- **Implementation:** No code change

---

#### D-09: Backward Compatibility — Keep Batch API Unchanged
- **What:** Training and prediction remain batch-oriented (no separate "live" mode API)
- **Why:** 
  - Phase 2 focus is detection system quality, not live trading API
  - Batch pipeline is simpler to reason about (no stateful inference)
  - Live updates can be added later (Phase 3+) if needed
- **How:**
  - `run.py` workflow: collect (delta or full) → features → train (refit on full history)
  - Output: `regime_results.csv` with all historical regimes (batch results)
  - No separate `predict_live()` function; incremental just means "fetch delta, retrain"
- **Implementation:** No API changes; just optimize data collection

---

### Claude's Discretion

#### D-10: Testing for Incremental Collection
- **What:** Add tests to verify incremental collection works correctly
  - Test: first run (empty cache) → full download
  - Test: second run (cache exists) → delta only
  - Test: hash mismatch → re-fetch affected ticker
  - Test: data consistency validation (drops dups, catches schema changes)
- **How:** New test file `tests/test_incremental_collection.py`
- **Why:** Incremental logic is new; regression testing essential

---

#### D-11: Documentation Updates
- **What:** Update README + CLAUDE.md to explain incremental mode
  - First run: `python run.py` downloads 16 years (20 min)
  - Subsequent runs: `python run.py` fetches only new data (<5 min)
  - To force full re-download: `rm -rf data/cache/`
- **How:** Add section "Incremental Data Mode" to README
- **Why:** Users need to know this changed

---

</decisions>

---

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 2 Requirements
- `.planning/REQUIREMENTS.md` — R1 (incremental mode <5 min), R6 (test coverage)
- `.planning/ROADMAP.md` — Phase 2 full specification (2.1 + 2.2)

### Hard Constraints (from Phase 1)
- `CLAUDE.md` (project root) — NumPyro, 3 regimes, causal pipeline, reproducibility
- `.planning/STATE.md` — Architecture decisions (NumPyro final, 3 regimes fixed)

### Existing Code References
- `collect.py` — Current data collection (no caching)
- `features.py` — Feature engineering (expand for PCA cache)
- `train.py` — HMM training (update to use cached PCA)
- `dashboard.py` — Streamlit app (to be refactored)
- `analyze.py` — Post-hoc analysis (move to separate scripts)
- `config.py` — Configuration (add CACHE_PATH, INCREMENTAL_MODE)

### Downstream Integration
- Algo-Trading-Bot expects regime signals in `regime_results.csv` format
- Dashboard must consume regime_results.csv + trust_scorecard.json
- Analysis scripts are **optional** (not required for bot integration)

</canonical_refs>

---

<code_context>

## Existing Code Insights

### Reusable Assets
- `collect.py` — Download logic; extend with cache checking + delta detection
- `features.py` — Feature engineering; extend with PCA caching
- `train.py` — Training logic; update to reload cached PCA
- `dashboard.py` — Streamlit rendering; gut analysis code, keep visualization

### Established Patterns
- **Config centralization:** All params in `config.py`; add `CACHE_PATH`, `CACHE_WINDOW` params
- **CSV-based persistence:** Results saved as CSV (regime_results.csv); cache will also use CSV
- **Pandas-native:** All data manipulation via pandas; feather index is pandas-compatible

### Integration Points
- `collect()` → `prepare_features()` → `train()` → `compute_signals()` → dashboard
- Incremental update affects collect() output (should be same schema, just fewer rows on append)
- PCA caching affects features.py and train.py (must pass PCA object through pipeline)

</code_context>

---

<specifics>

## Specific Ideas

### Cache Directory Structure
```
data/
  cache/
    .cache_manifest.json          # metadata: {ticker: {hash, mod_time, last_fetch_date}}
    SPY_incremental.csv           # raw OHLCV + VIX series for SPY
    SPY_index.feather             # feather index (row count, date range, schema)
    QQQ_incremental.csv
    QQQ_index.feather
    ... (one pair per ticker)
```

### Feather Index Format
```json
{
  "schema": "OHLCV + VIX series",
  "schema_version": 1,
  "row_count": 3752,
  "date_range": ["2010-01-01", "2026-04-13"],
  "columns": ["Open", "High", "Low", "Close", "Volume", "VIX"],
  "dtype_checksum": "sha256..."
}
```

### Cache Validation Example
When appending new data:
1. Check schema (columns match, dtypes match)
2. Check row count increases (at least 1 new row)
3. Check dates are continuous (no >10-day gaps)
4. Drop duplicates on `(date, ticker)`
5. Forward-fill single missing values
6. Update feather index
7. Log: "Appended 5 new rows to SPY_incremental.csv"

---

### PCA Caching Strategy
```python
# In train.py
pca = train_hmp_hmm(
    features_df=features_df,
    pca_window=252,  # refit on latest 1 year
    reload_pca_checkpoint=model_checkpoint['pca']  # if available
)
# Save PCA in checkpoint for next run
model_checkpoint['pca'] = pca
```

### Dashboard Slim Example
**Before (bloated):**
- Regime probability time series
- Feature heatmap (13 features over time)
- Regime characterization (mean return, vol per regime)
- PCA loadings visualization
- Correlation matrix
- Trust scorecard

**After (focused):**
- Regime probability time series (regime 0 | 1 | 2 stacked bars)
- Current regime + confidence (large text)
- Trust scorecard (8 checks, all pass/fail icons)
- Maybe: recent regime switches (table of dates)

</specifics>

---

<deferred>

## Deferred Ideas

### Backlog (Phase 3+)
- Live prediction API (train.py::predict_live) — separate from batch
- GPU acceleration (NumPyro on GPU) — performance, not blocking
- Parallel data collection (concurrent ticker downloads) — marginal speedup
- Streaming mode (Kafka/Redis ingestion) — infrastructure, not MVP

### Out of Scope
- Change HMM algorithm (NumPyro final)
- Add new regimes (3 fixed)
- Change dashboard tech (Streamlit final)

</deferred>

---

*Phase: 02-incremental*  
*Context gathered: 2026-04-13*  
*Mode: Interactive discuss with architectural refocus (dashboard slim, analysis decoupled)*
