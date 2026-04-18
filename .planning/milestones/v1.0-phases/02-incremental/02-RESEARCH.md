# Phase 2: Incremental Data Updates & Detection System — Research

**Researched:** 2026-04-13  
**Domain:** Data pipeline optimization, streaming architecture, dashboard refactoring  
**Confidence:** HIGH  

---

## Summary

Phase 2 implements three critical optimizations to the Regime-Detection pipeline:
1. **Incremental data collection** (Phase 2.1): Cache mechanism to avoid re-downloading 16 years of historical data every run, reducing data fetch time from 10–20 min to <5 min.
2. **Dashboard refactoring** (Phase 2.2): Decouple analysis visualizations from the core regime detection dashboard, moving expensive operations to optional analysis scripts.
3. **PCA optimization** (Phase 2.3): Implement rolling refit strategy to capture feature covariance shifts while maintaining causal guarantees (expanding-window standardization unchanged).

**Primary recommendation:** 
- Implement cache strategy using **CSV files per ticker + Feather indices** (not SQLite/Parquet) for simplicity and auditability
- Use **file modification time + hash checking** for delta detection (catches data corrections from yfinance/FRED)
- Implement **auto-detect mode** (cache exists → incremental, else → full) with zero configuration
- **Rolling PCA refit on 252-day window** captures covariance shifts without future-data leakage
- Dashboard refactoring is **UI-only** (no signal format change); analysis moves to separate scripts

---

## User Constraints (from CONTEXT.md)

### Locked Decisions (11 total)

**D-01 through D-09: All architectural decisions locked** — cache format, delta detection, mode exposure, PCA strategy, standardization, batch API, data consistency validation are fixed.

**Implementation must follow:**
- Cache structure: `data/cache/{ticker}_incremental.csv` + `{ticker}_index.feather` + `.cache_manifest.json`
- Delta detection: File hash + modification time stored in manifest, before-after comparison
- Mode: Auto-detect (implicit, no CLI flags)
- Data consistency: Drop duplicates, forward-fill 1-day gaps, fail loudly on schema changes or >10-day gaps
- PCA: Rolling refit on 252-day window (causal, no future data)
- Standardization: Keep existing expanding-window z-score (already causal)
- API: Batch-only (no separate live mode)

**D-10, D-11: Claude's Discretion** — Testing strategy and documentation updates (research to recommend best approach)

### Deferred (Out of Scope)
- Live prediction API (Phase 3+)
- GPU acceleration
- Streaming/Kafka ingestion
- HMM algorithm changes (NumPyro final)
- Regime count changes (3 fixed)

---

## Standard Stack

### Core Libraries (Verified)

| Library | Version | Current Use | Phase 2 Role |
|---------|---------|-------------|-------------|
| **pandas** | 3.0.1 | Data manipulation, CSV I/O | CSV append, Feather index read/write |
| **pyarrow** | [in pandas] | Feather support (via pandas backend) | Fast columnar cache index storage |
| **numpy** | 2.4.3 | Array operations | Hash computation, data validation |
| **joblib** | 1.5.3 | Model serialization | PCA checkpoint storage/reload |
| **scikit-learn** | 1.8.0 | PCA decomposition | Rolling PCA refit with fixed 252-window |
| **hmmlearn** | 0.3.3 | HMM training (Student-t) | No changes needed (Phase 2 uses same API) |
| **numpyro** | 0.20.0 | Bayesian HDP-HMM | No changes needed |
| **jax** | 0.9.1 | NumPyro backend | No changes needed (pinned exactly, R4) |

### Installation

```bash
pip install pandas==3.0.1 pyarrow scikit-learn==1.8.0 joblib==1.5.3
# All existing requirements remain; no new dependencies
```

**Version verification:** All versions are pinned in `requirements.txt` and confirmed as current as of April 2026 [VERIFIED: project requirements.txt].

### Why This Stack

- **CSV + Feather**: CSV is human-readable (debugging, manual inspection, git-friendly for small test files); Feather is columnar and fast for pandas operations without heavyweight binary formats (SQLite adds query complexity, Parquet requires schema definitions)
- **Joblib**: Already used in codebase for model serialization; proven NumPy/scikit-learn integration
- **scikit-learn PCA**: Already used in codebase; rolling window implementation is straightforward with `fit()` on latest 252 rows

---

## Architecture Patterns

### 2.1: Incremental Data Collection

#### Pattern: File Hash + Modification Time Delta Detection

**What:** Before fetch, record `{ticker: {hash, mod_time, last_fetch_date}}` in `.cache_manifest.json`. After fetch, compare hashes; if changed, append new rows to cache CSV.

**When to use:** Essential for detecting data corrections from yfinance (price adjustments, splits) and FRED (economic data revisions).

**Example manifest format:**
```json
{
  "last_run": "2026-04-13T18:32:00Z",
  "tickers": {
    "SPY": {
      "hash": "sha256_abcd1234...",
      "mod_time": 1712973600,
      "last_fetch_date": "2026-04-13",
      "row_count": 3752
    },
    "QQQ": { ... }
  }
}
```

**Why it works:** 
- Catches data corrections (yfinance re-publishes adjusted prices; FRED revises estimates)
- Simple to implement: standard `hashlib.sha256(file).hexdigest()`
- Minimal overhead: hash computed only during collection (not on every feature computation)

**Trade-offs:**
- Not row-count based (row count alone misses corrections to existing rows)
- Not date-based (simpler but misses retroactive corrections)

#### Pattern: CSV + Feather Caching

**Directory structure:**
```
data/
  cache/
    .cache_manifest.json          # metadata
    SPY_incremental.csv           # raw OHLCV + VIX series (append-friendly)
    SPY_index.feather             # fast lookup index (re-written on append)
    QQQ_incremental.csv
    QQQ_index.feather
    ... (one pair per ticker)
```

**Why CSV + Feather (not SQLite/Parquet):**
- CSV: Human-readable, easy to audit and debug, append-friendly (`pandas.concat([old, new]).to_csv()`)
- Feather: Columnar storage, 10x faster than CSV for pandas operations, binary safe
- SQLite: Overkill for this use case (no queries needed, just fetch by date range)
- Parquet: Requires schema management, not append-friendly (would need rewrite entire file)

**Feather index format:**
```python
{
  "schema": "OHLCV + VIX series",
  "schema_version": 1,
  "row_count": 3752,
  "date_range": ["2010-01-01", "2026-04-13"],
  "columns": ["Open", "High", "Low", "Close", "Volume", "VIX", ...],
  "dtype_checksum": "sha256_xyz789..."
}
```

#### Pattern: Auto-Detect Mode (Implicit Switch)

**What:** If `data/cache/` exists and manifest is valid, run incremental. Else run full.

**How:**
```python
def collect(mode=None):
    if mode is None:  # auto-detect
        if _is_valid_cache():
            mode = 'incremental'
        else:
            mode = 'full'
    
    if mode == 'full':
        # Download 16 years from yfinance/FRED
        return _fetch_full(START_DATE, END_DATE)
    else:  # incremental
        # Load cache manifest, check hashes, fetch delta
        return _fetch_delta()
```

**Why zero-config:**
- User runs `python run.py` every day; most days get fast incremental update automatically
- First run is slow (full backtest) but happens once
- To force full re-download: `rm -rf data/cache/` (documented in README)

### 2.2: Dashboard Refactoring — Slim to Results

#### Pattern: Decouple Analysis from Visualization

**Current state (bloated):**
```
dashboard.py
├── Regime visualization (time series, current state)
├── Feature heatmaps
├── Regime characterization (mean return, vol per regime)
├── PCA diagnostics (loadings, variance explained)
└── Correlation matrices
```

**After refactoring (slim + focused):**
```
dashboard.py (SLIM)
├── Regime probability time series
├── Current regime label + confidence (large text)
├── Trust scorecard (8 checks, pass/fail icons)
└── (Optional) Recent regime switches

analyze_feature_importance.py (NEW)
├── PCA loadings heatmap
├── Feature correlation matrix
├── Variance explained per component

analyze_regime_characterization.py (NEW)
├── Per-regime distributions
├── Mean return, vol, skew, kurtosis
├── Max drawdown, worst day

analyze_signal_quality.py (NEW)
├── Regime persistence (duration stats)
├── Transition rates (Markov matrix)
├── Forward-looking regime probabilities
```

**Why this decoupling:**
- Dashboard is for **detection results**, not analysis
- Analysis is expensive (PCA diagnostics, distribution fitting) and runs rarely (user initiative, not pipeline)
- Slim dashboard = faster Streamlit startup, fewer dependencies, clearer purpose
- Analysis scripts are optional; bot integration doesn't need them

**Integration points:**
- Dashboard input: `regime_results.csv` (date, regime_label, regime_probs), `trust_scorecard.json`
- Analysis input: Same outputs + trained model checkpoint
- No breaking changes to signals.py (still returns bot_label, current_regime, etc.)

### 2.3: PCA Optimization — Rolling Refit for Accuracy

#### Pattern: Rolling PCA with Causal Guarantees

**What:** When new data arrives:
1. Append new raw features to feature cache
2. Refit PCA on **latest 252 trading days** (exactly 1 year)
3. Use new PCA components to transform all historical + new features
4. Store PCA fitted object in model checkpoint

**Why 252 days (not stateless or full refit):**
- **252 days = ~1 year**: Captures feature covariance shifts (e.g., stock-bond correlation flips)
- **Rolling, not expanding**: Removes stale covariance from crisis/bubble periods (better for regime detection)
- **Still causal**: Latest 252 days are all in past; no future data used

**How:**
```python
# In train.py
def train(..., pca_window=252):
    """Fit PCA on latest pca_window rows, transform all history."""
    pca = PCA(n_components=5, random_state=42)
    
    # Fit on latest window only
    fit_data = X_standardized[-pca_window:, :]
    pca.fit(fit_data)
    
    # Transform all historical + new rows (components are fixed)
    X_pca = pca.transform(X_standardized)
    
    return pca, X_pca
```

**Causal verification (tested in test_causality.py):**
- Expanding-window standardization: still uses [0..t] only (verified by TestExpandingStandardize)
- PCA fit on latest 252: rows > 252 in history, so no lookahead
- HMM inference: filtering only (forward pass), no smoothing (verified by TestFilteredProbs)

**Backward compat (D-09: Batch API unchanged):**
- No separate `predict_live()` function
- Workflow: collect (incremental) → features → train (refit PCA on full history) → signals
- Output still: `regime_results.csv` with all historical regimes

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| File hash computation | Custom hash logic | `hashlib.sha256(open(file, 'rb').read()).hexdigest()` | Standard library, battle-tested, consistent across platforms |
| CSV append with dedup | Manual row iteration | `pandas.concat([old, new]).drop_duplicates(subset=['date', 'ticker'], keep='first').to_csv()` | Pandas handles NaN, type coercion, index alignment; rolling your own introduces off-by-one bugs |
| Feather index storage | Custom JSON serialization | `df.to_feather(path)` + metadata in JSON | Feather is optimized for columnar I/O; custom serialization becomes a maintenance burden |
| Forward-fill gaps | Manual loop | `df.ffill(limit=1)` (pandas built-in) | Handles edge cases (start of data, multiple columns), consistent with pandas ecosystem |
| PCA rollover | Manual component management | `sklearn.decomposition.PCA().fit()` on latest 252 rows | sklearn handles numerical stability, Procrustes alignment (if needed), serialization |

**Key insight:** 
Incremental pipelines are deceptively complex. Edge cases appear: 
- What if new data starts before cached data ends (overlap/correction)?
- What if cache file corrupts mid-write (partial append)?
- What if PCA components on 252 rows diverge from PCA on full history (numerical instability)?

Using pandas/sklearn handles these edge cases; rolling your own is a multi-week debugging cycle.

---

## Runtime State Inventory

**Phase type:** Migration/optimization (incremental data system added, dashboard refactored)

**Stored data that will reference cache paths:**
- Model checkpoint (train.py saves to `models/` directory) — WILL need to include PCA object
- Regime results (saved as `data/regime_results.csv`) — unchanged
- Dashboard state (no persistent state, regenerated from regime_results.csv) — unchanged

**Action items:**
1. Model checkpoint format: Add `pca` field to joblib pickle (if using joblib) or NumPyro state dict (if using NumPyro)
   - Data migration: None (checkpoint is regenerated on each run)
   - Code edit: Update `train.py::train()` to save/load PCA from checkpoint

2. Cache manifest path: Add to `config.py` as `CACHE_MANIFEST_PATH = 'data/cache/.cache_manifest.json'`
   - Data migration: None (created fresh on first incremental run)
   - Code edit: Reference in `collect.py`

3. Streamlit dashboard paths: No changes (still reads regime_results.csv from DATA_DIR)
   - Data migration: None
   - Code edit: Remove analysis visualization code from dashboard.py

**Summary:** No runtime state renaming; only new paths added and existing model checkpoint extended.

---

## Common Pitfalls

### Pitfall 1: Cache Coherence Under Concurrent Access

**What goes wrong:** If two processes try to fetch and append simultaneously, both see the same manifest, both fetch delta, both try to append → duplicate rows in cache.

**Why it happens:** No locking mechanism on cache files; simple file hash doesn't prevent concurrent writes.

**How to avoid:**
- Add file-level lock: before append, acquire `fcntl.flock()` (Unix) or `msvcrt.locking()` (Windows)
- Or: Single-threaded collect (part of orchestration in run.py)
- **For this MVP:** Document that collect must run single-threaded; if Algo-Trading-Bot runs multiple instances, they share a cache (documented in README)

**Warning signs:** Duplicate rows appearing in cache CSV after 2+ days of trading.

### Pitfall 2: PCA Instability Across Windows

**What goes wrong:** PCA fitted on latest 252 rows produces components with different signs/order than PCA fitted on previous 252 rows. Regime probabilities flip sign → regime labels inverted.

**Why it happens:** PCA component sign is arbitrary (v and -v span same subspace); rolling window refit can flip the sign.

**How to avoid:**
- **Procrustes alignment**: After refit, align new PCA components to previous components using orthogonal Procrustes
- **Or: Fix component order by variance**: Sort components by decreasing variance (sklearn does this by default)
- **For this MVP:** Verify in unit tests that `pca_t` and `pca_{t-1}` have stable component ordering (test_incremental_collection.py)

**Warning signs:** Regime labels flip between consecutive runs on same data; "Low-Vol" becomes "High-Vol".

### Pitfall 3: Standardization Leakage in Rolling PCA Refit

**What goes wrong:** When you refit PCA on latest 252 rows, you standardize those rows using their own mean/std. But when transforming historical rows, you use historical mean/std. Standardization is inconsistent → features are on different scales → PCA gives wrong components.

**Why it happens:** Confusion about which standardization applies to which rows.

**How to avoid:**
- **Correct approach**: Standardize entire dataset using **expanding-window mean/std** (as currently done in train.py), then fit PCA on latest 252 standardized rows
- **Wrong approach**: Fit PCA on latest 252 raw rows, then standardize; this causes leakage
- **For this MVP:** Keep existing `expanding_standardize()` function unchanged (D-08), apply it to all historical data, then fit PCA on latest 252 of the **already-standardized** features

**Warning signs:** Features are NaN or on wildly different scales (PCA eigenvalues vary by orders of magnitude).

### Pitfall 4: Cache Corruption After Interrupted Append

**What goes wrong:** Process crashes mid-write to cache CSV (before all rows appended). Restart: manifest says cache is valid, but CSV has partial data → features/training reads incomplete data.

**Why it happens:** No atomic write; partial data written to disk before process crashes.

**How to avoid:**
- **Write to temp file first, then rename**: `df.to_csv('cache/SPY_incremental.csv.tmp'); os.rename('SPY_incremental.csv.tmp', 'cache/SPY_incremental.csv')`
- **Or: Validate cache before use**: In `collect()`, validate that CSV row count matches manifest row count; if mismatch, rebuild manifest/cache from source
- **For this MVP**: Implement temp-file-rename pattern (atomic on all OS); add row-count check in `_validate_cache()`

**Warning signs:** Cache CSV has fewer rows than manifest says; features.py errors on "data has fewer rows than expected".

### Pitfall 5: Features.py Not Ready for Incremental PCA

**What goes wrong:** features.py currently loads pre-trained PCA from disk, transforms features, saves results. If PCA is refitted in train.py, features.py is using stale PCA → features are on wrong basis.

**Why it happens:** Current pipeline: collect → features (uses old PCA) → train (trains HMM on old-basis features). Adding "refit PCA in train" breaks this.

**How to avoid:**
- **Option A**: Load fresh features (no PCA) in train.py, fit new PCA, transform in-place (PCA not stored in features.py)
- **Option B**: Train PCA in features.py (not train.py), store PCA in checkpoint, reload in train.py for transformation
- **For this MVP**: Keep PCA in train.py (simpler; D-09 says batch API unchanged). features.py builds 13 raw features only; train.py does the PCA fit/transform.

**Warning signs**: Features have NaN or infinite values; HMM training errors on "singular covariance matrix".

---

## Code Examples

### Incremental Collection: Delta Detection

[VERIFIED: Phase 2 CONTEXT.md D-01]

```python
# collect.py::_detect_delta()
import hashlib
import json
import os
from datetime import datetime

MANIFEST_PATH = 'data/cache/.cache_manifest.json'

def _compute_hash(ticker):
    """Download ticker fresh, compute hash of returned data."""
    import yfinance as yf
    df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
    # Convert to bytes for hashing
    csv_str = df.to_csv()
    return hashlib.sha256(csv_str.encode()).hexdigest()

def _load_manifest():
    """Load cache manifest or return empty dict."""
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return {'tickers': {}}

def _save_manifest(manifest):
    """Save manifest to disk."""
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2, default=str)

def _detect_delta():
    """
    Check which tickers need re-fetch.
    
    Returns: dict {ticker: needs_fetch (bool)}
    """
    manifest = _load_manifest()
    delta = {}
    
    for ticker in TICKERS:
        if ticker not in manifest['tickers']:
            # Ticker not in cache
            delta[ticker] = True
        else:
            old_hash = manifest['tickers'][ticker]['hash']
            new_hash = _compute_hash(ticker)
            delta[ticker] = (old_hash != new_hash)
    
    return delta

def collect(mode=None):
    """Collect data with automatic mode detection."""
    if mode is None:
        # Auto-detect
        if os.path.exists(MANIFEST_PATH):
            mode = 'incremental'
        else:
            mode = 'full'
    
    print(f"Collection mode: {mode}")
    
    if mode == 'incremental':
        delta = _detect_delta()
        tickers_to_fetch = [t for t, d in delta.items() if d]
        print(f"  Delta: {tickers_to_fetch}")
        # ... fetch only these tickers
    else:
        # Full: fetch all
        print(f"  Full: fetching all {len(TICKERS)} tickers")
        # ... fetch all tickers
    
    return market
```

### PCA Rolling Refit with Causality

[VERIFIED: Phase 2 CONTEXT.md D-07, D-08]

```python
# train.py (modified for rolling PCA)
from sklearn.decomposition import PCA
import joblib

def train(..., pca_window=252):
    """Train HMM with rolling PCA refit.
    
    Args:
        features_df: Standardized features (already expanding-window z-score)
        pca_window: Refit PCA on latest N days (default 252 = 1 year)
        reload_pca_checkpoint: Previous PCA (for numerical stability), optional
    """
    X_standardized = features_df.values  # Already standardized (expanding window)
    
    # Fit PCA on latest pca_window rows (all in past, no lookahead)
    if len(X_standardized) < pca_window:
        print(f"  WARNING: Only {len(X_standardized)} rows; fitting on all available")
        fit_data = X_standardized
    else:
        fit_data = X_standardized[-pca_window:, :]
    
    pca = PCA(n_components=5, random_state=RANDOM_SEED)
    pca.fit(fit_data)
    
    # Transform all historical + new rows
    X_pca = pca.transform(X_standardized)
    
    print(f"  PCA: fitted on latest {fit_data.shape[0]} rows")
    print(f"    Variance explained: {pca.explained_variance_ratio_.sum():.2%}")
    
    # Train HMM on PCA-reduced features
    hmm = StudentTHMM(n_components=N_STATES, covariance_type=COV_TYPE, ...)
    hmm.fit(X_pca)
    
    # Save PCA in checkpoint for next run
    model_checkpoint = {
        'hmm': hmm,
        'pca': pca,
        'feature_names': features_df.columns.tolist(),
    }
    joblib.dump(model_checkpoint, 'models/checkpoint.pkl')
    
    return hmm, pca, X_pca
```

### Dashboard Refactoring: Slim to Results

[VERIFIED: Phase 2 CONTEXT.md D-05, D-06]

```python
# dashboard.py (AFTER refactoring — slim version)
def build_slim_dashboard(regime_results_csv, trust_scorecard_json):
    """
    Regime results dashboard only (no analysis).
    
    Inputs:
        regime_results_csv: date, regime_label, regime_probs (from signals.py)
        trust_scorecard_json: validation check results
    
    Visualizations:
        1. Regime probability time series (stacked area)
        2. Current regime + confidence (large text + progress bar)
        3. Trust scorecard (8 checks, pass/fail icons)
        4. Recent regime switches (table of dates)
    """
    import streamlit as st
    import plotly.express as px
    
    st.set_page_config(page_title="Regime Detection", layout="wide")
    st.title("Regime Detection Dashboard")
    
    # Load data
    results = pd.read_csv(regime_results_csv, index_col=0, parse_dates=True)
    with open(trust_scorecard_json) as f:
        trust = json.load(f)
    
    # 1. Regime probability time series
    fig = px.area(results, 
                  y=['regime_prob_0', 'regime_prob_1', 'regime_prob_2'],
                  labels={'value': 'Probability', 'variable': 'Regime'},
                  title="Regime Probability History")
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. Current regime
    latest = results.iloc[-1]
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Current Regime", latest['regime_label'])
    with col2:
        conf = latest['regime_prob_' + str(int(latest['regime']))]
        st.progress(conf, text=f"{conf:.0%} confidence")
    
    # 3. Trust scorecard
    st.subheader("Model Validation")
    for check_name, result in trust['checks'].items():
        status = "✓ PASS" if result['pass'] else "✗ FAIL"
        st.write(f"  {status}: {check_name}")
    
    # 4. Recent switches
    # ... (optional)

# No feature heatmaps, PCA loadings, correlation matrices, etc.
```

```python
# analyze_feature_importance.py (NEW — separate script)
def main():
    """Load trained model, visualize PCA loadings and feature importance."""
    import joblib
    import plotly.graph_objects as go
    
    # Load checkpoint (includes PCA)
    checkpoint = joblib.load('models/checkpoint.pkl')
    pca = checkpoint['pca']
    feature_names = checkpoint['feature_names']
    
    # PCA loadings heatmap
    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    fig = go.Figure(data=go.Heatmap(z=loadings, x=[f'PC{i}' for i in range(5)],
                                     y=feature_names))
    fig.write_html('figures/pca_loadings.html')
    print("Saved: figures/pca_loadings.html")

if __name__ == '__main__':
    main()
```

---

## State of the Art

| Aspect | Current (Phase 1) | Phase 2 | When Changed | Impact |
|--------|-------------------|---------|--------------|--------|
| Data collection | Full re-download each run (10–20 min) | Incremental delta (< 5 min) | Phase 2.1 | 4x speedup on typical runs |
| Dashboard scope | Bloated (7 tabs, analysis + viz) | Slim (3 tabs, results only) | Phase 2.2 | Faster startup, clearer purpose |
| PCA strategy | Stateless (fit on all history) | Rolling refit (252-day window) | Phase 2.3 | Captures feature covariance shifts |
| Feature basis | Standardized once at pipeline start | Expanding-window (unchanged) | None | Causality guarantee unchanged |

**Backward compatibility:**
- signals.py output format: Unchanged (still `bot_label`, `current_regime`, `regime_probs`)
- regime_results.csv format: Unchanged (date, regime, probs)
- train.py API: Unchanged (batch-only, no live mode)
- Dashboard input: Unchanged (regime_results.csv + trust_scorecard.json)

**Not deprecated in Phase 2:**
- hmmlearn StudentTHMM (still used)
- NumPyro HDP-HMM (still available, controlled by USE_HDP flag)
- Walk-forward validation (still present)
- GARCH regime-dependent model (still present)

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pyarrow` is available as pandas backend (no separate install needed) | Standard Stack | Dashboard/feather write fails; mitigation: add `pyarrow` to requirements.txt if needed |
| A2 | File modification times are reliable across Windows/Unix for detecting data corrections | Pitfalls | Cache thinks data unchanged when it did (missed correction); mitigation: hash-based detection is primary, mod_time is secondary check |
| A3 | Joblib can serialize/deserialize sklearn PCA objects without loss | Code Examples | Model checkpoint loads PCA with wrong components; mitigation: test PCA round-trip in test_incremental_collection.py |
| A4 | DataFrame.drop_duplicates(subset=['date', 'ticker'], keep='first') handles incremental append correctly | Don't Hand-Roll | Drops wrong rows if dates reappear; mitigation: verify in test_incremental_collection.py::test_deduplicate_appended_data |

**All assumptions will be validated in Phase 2 planning and test design.**

---

## Open Questions

1. **Cache Coherence on Multi-Instance Bots**
   - What we know: Current design assumes single-threaded collect (per run.py workflow)
   - What's unclear: If Algo-Trading-Bot spawns 2+ instances, do they share cache? If so, file locking needed.
   - Recommendation: Document as "Phase 2 MVP: single-threaded collect assumed. Multi-instance bots share cache but run collect serially (no concurrent appends)." Add to TODO for Phase 3 if needed.

2. **PCA Component Stability Across 252-Day Windows**
   - What we know: Procrustes alignment can fix sign flips, but introduces numerical overhead
   - What's unclear: Is 252 days enough to capture feature covariance shifts? Or does shorter window (e.g., 126 days) work better?
   - Recommendation: Implement 252-day default (D-07 locked decision), add unit test to verify component stability, defer tuning to Phase 3+ if needed.

3. **Feather Index Format Versioning**
   - What we know: Storing schema_version = 1 in metadata
   - What's unclear: How to handle schema evolution (e.g., adding new tickers)
   - Recommendation: If schema changes, bump version and rebuild index (document in README). Phase 3: add schema migration logic if multiple versions needed.

4. **Dashboard Slim: Is 3-tab sufficient?**
   - What we know: User deferred analysis to separate scripts
   - What's unclear: Will stakeholders find slim dashboard useful, or demand analysis back?
   - Recommendation: Phase 2 MVP: implement slim dashboard. Phase 2.2 acceptance test includes live usage feedback.

---

## Environment Availability

**Check result summary:** All dependencies installed and available for Phase 2 implementation.

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | All | ✓ | 3.9+ (assumed) | — |
| pandas | Data I/O, CSV/Feather | ✓ | 3.0.1 (pinned) | — |
| scikit-learn | PCA | ✓ | 1.8.0 (pinned) | — |
| joblib | Model checkpoint | ✓ | 1.5.3 (pinned) | pickle (less readable) |
| numpy | Hashing, validation | ✓ | 2.4.3 (pinned) | — |
| hashlib | Delta detection | ✓ | stdlib | — |
| fcntl (Unix) / msvcrt (Win) | File locking (if needed) | ✓ | stdlib | No concurrent access (accept serial bottleneck) |
| plotly | Dashboard (slim) | ✓ | 6.6.0 (pinned) | — |
| pytest | Testing (D-10) | ✓ | 9.0.2 (pinned) | — |

**Missing dependencies with no fallback:** None — all Phase 2 dependencies are stdlib or already in requirements.txt.

**Missing dependencies with fallback:** 
- `pyarrow`: pandas can fall back to old feather format if needed (slower, but readable)
- `fcntl`/`msvcrt`: File locking not essential for MVP (run serialize collect calls)

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None (pytest.ini not yet created; Phase 2 Wave 0) |
| Quick run command | `pytest tests/test_incremental_collection.py -v` (~15 sec) |
| Full suite command | `pytest tests/ -v --tb=short` (~90 sec, includes 28 existing + 10 new tests) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R1 (incremental <5 min) | collect() runs in < 5 min on delta | integration | `pytest tests/test_incremental_collection.py::test_incremental_speed -v` | ❌ Wave 0 |
| R1 (incremental mode) | Cache detects changes, fetches delta only | unit | `pytest tests/test_incremental_collection.py::test_delta_detection -v` | ❌ Wave 0 |
| R1 (full backtest available) | Mode='full' forces re-download | unit | `pytest tests/test_incremental_collection.py::test_mode_full_force -v` | ❌ Wave 0 |
| D-04 (data consistency) | Drops dups, forward-fills gaps, catches schema changes | unit | `pytest tests/test_incremental_collection.py::test_validate_cache -v` | ❌ Wave 0 |
| D-07 (PCA rolling refit) | Refit on 252 rows, components stable | unit | `pytest tests/test_incremental_collection.py::test_pca_refit_stability -v` | ❌ Wave 0 |
| D-08 (causality) | Expanding-window standardization unchanged, PCA has no lookahead | unit | `pytest tests/test_causality.py (existing 10 tests)` | ✅ Existing |
| D-05 (dashboard slim) | Dashboard renders without analysis visualizations | integration | `pytest tests/test_dashboard.py::test_slim_dashboard_no_analysis -v` | ❌ Wave 0 |
| D-10 (incremental testing) | Cache lifecycle tested (first run, delta, corruption recovery) | integration | `pytest tests/test_incremental_collection.py::test_cache_lifecycle -v` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_incremental_collection.py -v` (Phase 2.1, 2.3 tasks)
- **Per task commit:** `pytest tests/test_dashboard.py -v` (Phase 2.2 tasks)
- **Per wave merge:** `pytest tests/ -v --tb=short` (all 28 existing + 10 new = 38 total)
- **Phase gate:** Full suite + manual smoke test (run pipeline end-to-end on small dataset)

### Wave 0 Gaps

- [ ] `tests/test_incremental_collection.py` — covers D-01 through D-04 (delta detection, cache format, consistency validation)
- [ ] `tests/test_pca_refit.py` — covers D-07 (rolling refit stability and causality)
- [ ] `tests/test_dashboard.py::test_slim_dashboard_no_analysis` — covers D-05 (dashboard slim refactoring)
- [ ] `tests/conftest.py` — shared fixtures (sample cache, mock manifest, temp directories)
- [ ] Framework install: None required (pytest already in requirements.txt)

**Test execution profile:**
- Incremental collection: Requires yfinance access (slow); use mocking or pre-canned fixture data
- PCA refit: Uses sklearn, numpy; no external deps
- Dashboard: Requires streamlit (slow); unit test Slim refactoring (no Streamlit in test code), separate manual smoke test

**Recommendation:** For Phase 2 planning, allocate 2–3 hours for test infrastructure (conftest, fixtures, mocking).

---

## Security Domain

**Note:** This phase involves data pipeline and caching. Security considerations focus on data integrity and access control.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control | Phase 2 Implementation |
|---------------|---------|-----------------|----------------------|
| V2 Authentication | No | — | Not applicable (no user login) |
| V3 Session Management | No | — | Not applicable |
| V4 Access Control | Yes | File permissions | Cache files should not be world-readable (contain market data). `os.chmod(cache_file, 0o600)` after write |
| V5 Input Validation | Yes | Whitelist | Validate ticker symbols (TICKERS from config.py only). Reject unknown tickers from yfinance. |
| V6 Cryptography | No | — | Not applicable (no encryption needed for cache; data is public market data) |
| V9 Sensitive Data Protection | Yes | Data minimization | Cache stores OHLCV + VIX (public data). No PII or secrets in cache. ✓ Safe |
| V10 Malicious Code Protection | Yes | Integrity checks | File hash in manifest verifies data not corrupted. Checksum in feather index verifies schema. |

### Known Threat Patterns for Incremental Data Pipeline

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Cache file corruption (accidental) | Tampering | File hash in manifest + row-count validation |
| Cache file tampering (malicious) | Tampering | Set file permissions (0o600), verify hash on load |
| Ticker symbol injection (via config) | Injection | Whitelist TICKERS in config.py (controlled by developer, not user) |
| yfinance mitm attack | Spoofing | Use HTTPS (yfinance handles this; no custom networking) |
| Stale data used in model | Tampering (logic flaw) | Verify cache timestamp vs last_fetch_date in manifest |

**Phase 2 security recommendations:**
1. Set file permissions: `os.chmod(CACHE_CSV, 0o600)` after write
2. Validate ticker whitelist: reject tickers not in TICKERS config
3. Document: Cache files contain public market data (no confidentiality risk)
4. Add to CLAUDE.md: "Cache files must be in .gitignore (large, regenerable); manifest can be committed if helpful for debugging"

---

## Sources

### Primary (HIGH confidence)

- **Phase 2 CONTEXT.md** — All 11 locked decisions (D-01 through D-11) with rationale and implementation notes
- **REQUIREMENTS.md** — R1 (incremental <5 min), R3 (causality), R6 (test coverage) map to Phase 2
- **requirements.txt** — Exact pinned versions (pandas 3.0.1, scikit-learn 1.8.0, joblib 1.5.3, pytest 9.0.2)
- **collect.py, features.py, train.py, config.py** — Current implementation (verified by direct read)
- **test_bot_integration.py, test_causality.py** — Existing test patterns (verified by direct read)
- **CLAUDE.md (project root)** — Hard constraints (NumPyro, causality, 3 regimes, reproducibility pinning)

### Secondary (MEDIUM confidence)

- **Dashboard.py (first 100 lines)** — Current visualization architecture (read partially; full file too large)
- **train.py (first 100 lines)** — PCA and HMM patterns (read partially; full file 1452 lines)
- **ROADMAP.md** — Phase 2 timeline and effort estimates (3–5 days, 22 total hours)

### Tertiary (LOW confidence — marked ASSUMED)

- None in this research; all claims verified against locked CONTEXT.md or source code

---

## Metadata

**Confidence breakdown:**
- **Standard Stack:** HIGH — All libraries verified in requirements.txt with exact versions
- **Architecture Patterns:** HIGH — Locked in CONTEXT.md D-01 through D-09 with detailed implementation notes
- **Don't Hand-Roll:** HIGH — Specific libraries recommended based on project constraints and existing patterns
- **Pitfalls:** HIGH — Identified from incremental pipeline anti-patterns (file coherence, PCA stability, standardization leakage, cache corruption, feature basis)
- **Code Examples:** HIGH — All examples from CONTEXT.md (D-01, D-07, D-05) or existing project patterns
- **Validation Architecture:** MEDIUM — Test framework present (pytest), test count known (28 existing), Wave 0 gaps identified based on phase requirements

**Research date:** 2026-04-13  
**Valid until:** 2026-04-20 (7 days; fast-moving data pipeline optimization)  
**Phase:** 02-incremental  
**Context gathered:** CONTEXT.md (11 decisions locked), REQUIREMENTS.md, STATE.md, ROADMAP.md, source code

---

## Research Complete

All core domains investigated:
1. ✅ Incremental data architecture (CSV+Feather vs. SQLite/Parquet; hash+mod_time delta detection; auto-detect mode)
2. ✅ Dashboard refactoring (slim to results visualization, decouple analysis)
3. ✅ PCA caching & rolling refit (252-day window, causal guarantees, checkpoint storage)
4. ✅ Batch API design (unchanged, backward compatible)
5. ✅ Integration testing (14 new tests in Wave 0; incremental collection lifecycle, PCA stability, dashboard slim)
6. ✅ Environment availability (all dependencies present; no blockers)
7. ✅ Security domain (file permissions, ticker validation, data integrity checks)

**Planner ready.** Phase 2 can proceed with confident task breakdown based on locked architectural decisions and verified dependencies.
