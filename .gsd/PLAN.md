# Data Engineering & Feature Pipeline Audit — Execution Plan

**Created:** 2026-03-16  
**Scope:** Fix 7 verified issues in the data/feature pipeline; add rigorous feature testing infrastructure  
**Constraint:** Do NOT touch the math (HMM, SV, GARCH, HDP-HMM). Those are correct.

---

## Verified Issues

| # | Severity | Issue | File(s) | Root Cause |
|---|----------|-------|---------|------------|
| 1 | **CRITICAL** | Winsorization lookahead | `features.py` `_winsorize()` | Percentiles computed on full dataset; future extremes leak into early rows |
| 2 | **CRITICAL** | Walk-forward standardization mismatch | `train.py` `walk_forward()` | `train()` uses expanding-window z-score; `walk_forward()` uses `StandardScaler` — OOS tests a different pipeline |
| 3 | **CRITICAL** | Walk-forward uses Viterbi, not filtered labels | `train.py` `walk_forward()` L595 | `train()` uses `filtered_labels()` (forward-only); `walk_forward()` uses `.predict()` (Viterbi smoother) |
| 4 | **MODERATE** | FRED publication lag bias | `collect.py` L83-87 | FRED series treated as available on observation date; most have 1-day delay |
| 5 | **MODERATE** | No stationarity / VIF / importance testing | `features.py` `_validate_features()` | Only checks inf/variance/skew/correlation/kurtosis — no statistical rigor |
| 6 | **MINOR** | `features_raw.csv` is not raw | `features.py` L381-384 | File has log1p + winsorization already applied; name is misleading |
| 7 | **MINOR** | Redundant `FEATURE_SUBSET` filtering + unused `scaler.pkl` | `train.py` L537-539, `features.py` L387-388 | `train()` subsets then passes to `walk_forward()` which subsets again; `prepare_features()` saves scaler never used |

---

## Execution Waves

```
Wave 1 (parallel):  Task 1 + Task 2      — Fix data leakage
Wave 2 (parallel):  Task 3 + Task 4      — Fix pipeline consistency  
Wave 3 (single):    Task 5               — Add feature testing infrastructure
Wave 4 (single):    Task 6               — Cleanup + verification
```

---

## Task 1: Causal Winsorization

**Issues addressed:** #1  
**Files:** `features.py`  
**Wave:** 1

### Context

Current `_winsorize()` (lines 267-278):
```python
def _winsorize(features, lower=0.005, upper=0.995):
    for col in features.columns:
        lo, hi = features[col].quantile([lower, upper])  # <-- FULL dataset
        if lo < hi:
            features[col] = features[col].clip(lo, hi)
    return features
```

This means row 0 (2010-01-01) is clipped using percentiles that include 2020 COVID crash values, March 2023 SVB, etc. PCA sees "pre-warned" feature ranges.

### Action

Replace `_winsorize()` with expanding-window percentile clipping:

```python
def _winsorize(features: pd.DataFrame,
               lower: float = 0.005, upper: float = 0.995,
               min_warmup: int = 252) -> pd.DataFrame:
    """Clip each feature to expanding-window [0.5th, 99.5th] percentile.

    For row t, quantiles are computed from rows [0..t] only (causal).
    First min_warmup rows use the min_warmup-window quantiles (not enough
    history for stable percentile estimates before that).
    """
    result = features.copy()
    vals = features.values
    T = len(vals)

    for j, col in enumerate(features.columns):
        col_vals = vals[:, j]
        for t in range(T):
            window = col_vals[:max(t + 1, min_warmup)]
            lo = np.percentile(window, lower * 100)
            hi = np.percentile(window, upper * 100)
            if lo < hi:
                result.iloc[t, j] = np.clip(col_vals[t], lo, hi)
    return result
```

**Performance note:** This is O(T × D × T) in naive form. For ~3800 rows × 19 features, that's ~274M operations — may be slow. Optimize with sorted insertion or `pd.expanding().quantile()`:

```python
def _winsorize(features: pd.DataFrame,
               lower: float = 0.005, upper: float = 0.995,
               min_warmup: int = 252) -> pd.DataFrame:
    """Expanding-window winsorization (causal — no future leakage)."""
    result = features.copy()
    lo_bounds = features.expanding(min_periods=min_warmup).quantile(lower)
    hi_bounds = features.expanding(min_periods=min_warmup).quantile(upper)
    for col in features.columns:
        lo = lo_bounds[col]
        hi = hi_bounds[col]
        valid = lo.notna()
        result.loc[valid, col] = result.loc[valid, col].clip(
            lower=lo[valid], upper=hi[valid], axis=0,
        )
    return result
```

Use the `pd.expanding().quantile()` version — it's vectorized and fast.

### Verify

```bash
python -c "
import pandas as pd, numpy as np
from features import _winsorize
# Create test data with a late spike
np.random.seed(42)
data = pd.DataFrame({'A': np.concatenate([np.random.randn(100), [10.0], np.random.randn(99)])})
result = _winsorize(data)
# Row 50 should NOT be clipped by the spike at row 100
assert result.iloc[50, 0] == data.iloc[50, 0], 'Lookahead detected: row 50 was clipped by future spike'
print('Causal winsorization: PASS')
"
```

### Done

- `_winsorize()` uses expanding-window percentiles
- No row t sees percentile information from rows > t
- First 252 rows use the 252-window percentiles (stable enough)
- Function signature unchanged (backward compatible)

---

## Task 2: FRED Publication Lag Buffer

**Issues addressed:** #4  
**Files:** `config.py`, `collect.py`  
**Wave:** 1 (parallel with Task 1)

### Context

Current code in `collect.py` lines 83-87:
```python
for col_name, series in fred_data.items():
    market[col_name] = series.reindex(ref_index).ffill()
```

FRED series (yield_slope, hy_spread, yield_10y, yield_2y, ted_spread) are published end-of-day or next business day. Treating them as available on observation date is a subtle lookahead for regime detection at market close.

### Action

1. **`config.py`** — add after `FRED_SERIES` dict (around line 40):
```python
FRED_PUB_LAG_DAYS = 1   # shift FRED data by N days to account for publication delay
```

2. **`collect.py`** — modify the FRED alignment block. After the ffill reindex, shift by the configured lag:
```python
from config import (..., FRED_PUB_LAG_DAYS)

# FRED (forward-fill to trading days — with publication lag + staleness check)
for col_name, series in fred_data.items():
    aligned = series.reindex(ref_index).ffill()
    if FRED_PUB_LAG_DAYS > 0:
        aligned = aligned.shift(FRED_PUB_LAG_DAYS)
    market[col_name] = aligned
    # ... existing staleness check unchanged ...
```

3. **`collect.py`** — update the import line at the top to include `FRED_PUB_LAG_DAYS`.

### Verify

```bash
python -c "
from config import FRED_PUB_LAG_DAYS
assert FRED_PUB_LAG_DAYS >= 1, 'FRED_PUB_LAG_DAYS must be >= 1'
print(f'FRED publication lag: {FRED_PUB_LAG_DAYS} day(s) — OK')
"
```

After running `python run.py collect`, check that FRED columns have NaN on the first trading day (shifted out).

### Done

- FRED series shifted by 1 day after ffill alignment
- Configurable via `FRED_PUB_LAG_DAYS` in `config.py`
- Pipeline only sees FRED data that was available the previous business day

---

## Task 3: Align Walk-Forward with Train Pipeline

**Issues addressed:** #2, #3, #7  
**Files:** `train.py`  
**Wave:** 2 (depends on Task 1)

### Context

Three inconsistencies between `train()` and `walk_forward()`:

**A) Standardization:** `train()` uses expanding-window z-score (lines 2575-2589). `walk_forward()` uses `StandardScaler` (lines 565-568). In-sample and OOS test different systems.

**B) Decoding:** `train()` uses `filtered_labels()` (forward-only, line 329). `walk_forward()` uses `model.predict()` (Viterbi, line 595). Different decoders give different regime assignments.

**C) Redundant subset filtering:** `walk_forward()` lines 537-539 re-filter `FEATURE_SUBSET` on data already filtered by `train()` at line 2546.

### Action

**Step A — Extract expanding-window standardization as a reusable helper:**

Add this function near the top of `train.py` (after imports, before `StudentTHMM`):

```python
def expanding_standardize(X_raw, min_warmup=252):
    """Expanding-window z-score: row t uses mean/std from [0..t] only.

    Parameters
    ----------
    X_raw : ndarray (T, D) — raw feature values
    min_warmup : int — first N rows get NaN (unstable statistics)

    Returns
    -------
    X_scaled : ndarray (T, D) — z-scored values (first min_warmup rows are NaN)
    cum_mean_final : ndarray (D,) — cumulative mean at last row (for OOS transform)
    cum_std_final : ndarray (D,) — cumulative std at last row (for OOS transform)
    """
    X = X_raw.astype(np.float64)
    T, D = X.shape
    cumsum = np.cumsum(X, axis=0)
    cumsq = np.cumsum(X ** 2, axis=0)
    counts = np.arange(1, T + 1, dtype=np.float64).reshape(-1, 1)
    cum_mean = cumsum / counts
    cum_var = cumsq / counts - cum_mean ** 2
    cum_std = np.sqrt(np.maximum(cum_var, 0))
    cum_std[cum_std < 1e-8] = 1.0
    X_scaled = (X - cum_mean) / cum_std
    X_scaled[:min_warmup] = np.nan
    return X_scaled, cum_mean[-1], cum_std[-1]
```

**Step B — Update `train()` to use the helper:**

Replace lines 2575-2591 (the inline expanding-window block) with:
```python
X_scaled, _, _ = expanding_standardize(feat_raw.values)
_MIN_WARMUP = 252
print(f"  Expanding-window standardization: {_MIN_WARMUP}-day warm-up, "
      f"{len(feat_raw) - _MIN_WARMUP} valid days")
```

**Step C — Update `walk_forward()` standardization:**

Replace the StandardScaler block (lines 565-568) with:
```python
# Expanding-window standardize (match train() pipeline exactly)
X_combined = np.vstack([train_feats.values, test_feats.values])
X_all_scaled, _, _ = expanding_standardize(X_combined, min_warmup=min(252, len(train_feats) // 2))
X_train = X_all_scaled[:len(train_feats)]
X_test = X_all_scaled[len(train_feats):]

# Drop warm-up NaN rows from training data
valid_train = ~np.isnan(X_train[:, 0])
X_train = X_train[valid_train]
train_feats_valid = train_feats[valid_train]
```

**Note:** Also update VIX bypass and label remapping to use `train_feats_valid` instead of `train_feats` for index alignment.

**Step D — Replace `.predict()` with `filtered_labels()`:**

Replace line 595:
```python
raw_preds = best_m.predict(pc_test)
```
with:
```python
raw_preds = filtered_labels(best_m, pc_test, hold_days=REGIME_HOLD_DAYS)
```

**Step E — Remove redundant FEATURE_SUBSET filtering:**

Delete lines 537-539:
```python
if FEATURE_SUBSET is not None:
    available = [f for f in FEATURE_SUBSET if f in features.columns]
    features = features[available]
```

Add a comment where it was:
```python
# Note: features are already subset-filtered by train() before this call
```

### Verify

```bash
python -c "
from train import expanding_standardize
import numpy as np
X = np.random.randn(500, 5)
X_s, final_mean, final_std = expanding_standardize(X, min_warmup=50)
assert np.isnan(X_s[:50]).all(), 'Warm-up rows should be NaN'
assert not np.isnan(X_s[50:]).any(), 'Post-warmup should have no NaN'
# Row 100 should use stats from rows 0..100 only
m = X[:101].mean(axis=0)
s = X[:101].std(axis=0, ddof=0)
expected = (X[100] - m) / s
np.testing.assert_allclose(X_s[100], expected, rtol=1e-10)
print('Expanding standardize: PASS')
"
```

### Done

- `expanding_standardize()` is a reusable function used by both `train()` and `walk_forward()`
- Walk-forward uses the same standardization method as in-sample pipeline
- Walk-forward uses `filtered_labels()` not `.predict()` — same decoding as in-sample
- Redundant `FEATURE_SUBSET` filtering removed from `walk_forward()`

---

## Task 4: Rename `features_raw.csv` and Remove Unused Outputs

**Issues addressed:** #6, #7 (scaler)  
**Files:** `features.py`, `train.py`, `analyze.py`  
**Wave:** 2 (parallel with Task 3)

### Context

`prepare_features()` saves three files:
- `features_raw.csv` — actually NOT raw (has log1p + winsorization). Misleading name.
- `features_scaled.csv` — StandardScaler-scaled version. **Never used by `train()`** (which does its own causal standardization).
- `scaler.pkl` — fitted StandardScaler. **Never loaded by `train()`**.

The scaled CSV and scaler create confusion about which standardization the model actually uses.

### Action

1. **`features.py`** — in `prepare_features()`:
   - Change `features_raw.csv` → `features_transformed.csv`
   - Remove the `features_scaled.csv` write
   - Remove the `scaler.pkl` dump
   - Remove the `StandardScaler` import if no longer used elsewhere (check: `standardize()` function still uses it — keep the import)
   - Update the NOTE comment

```python
    # Transformed features (log1p + winsorized, NOT standardized).
    # train.py applies its own causal expanding-window standardization.
    features.to_csv(os.path.join(DATA_DIR, 'features_transformed.csv'))

    print(f"Features: {features.shape[1]} indicators x {features.shape[0]} days")
    print(f"  Columns: {list(features.columns)}")

    return features
```

   - Also update the return signature: return only `features` (remove `X_scaled, scaler` since they're no longer computed). But check if anything calls `prepare_features()` and unpacks 3 return values:

```bash
grep -n "prepare_features" *.py
```

   If `run.py` calls `prepare_features()` without unpacking, this is safe. If anything unpacks 3 values, update the caller too.

2. **`train.py`** — line 2527: change `features_raw.csv` → `features_transformed.csv`:
```python
    feat_raw = pd.read_csv(
        os.path.join(DATA_DIR, 'features_transformed.csv'),
        index_col=0, parse_dates=True,
    )
```

3. **`analyze.py`** — line 212: change `features_raw.csv` → `features_transformed.csv`:
```python
    feat_path = os.path.join(DATA_DIR, 'features_transformed.csv')
```

   Also update the error message on line 214 to say `features_transformed.csv`.

4. **`features.py`** — remove `standardize()` function and `joblib` import ONLY if nothing else uses them. Check:
```bash
grep -rn "standardize\|from features import" *.py
```
   `train.py` imports `standardize` — but check if it actually CALLS it. If not, remove the import from train.py and the function from features.py. If `standardize()` is still called somewhere, keep it.

### Verify

```bash
python -c "
import os
from features import prepare_features
import pandas as pd
f = prepare_features()
assert os.path.exists('data/features_transformed.csv'), 'Renamed file missing'
assert not os.path.exists('data/features_scaled.csv'), 'Scaled CSV should be removed'
# scaler.pkl removal is optional if standardize() is still exported
print('Rename: PASS')
"
```

### Done

- `features_raw.csv` renamed to `features_transformed.csv` everywhere
- `features_scaled.csv` and `scaler.pkl` no longer written by `prepare_features()`
- All consumers (`train.py`, `analyze.py`) updated to new filename
- No broken imports

---

## Task 5: Feature Testing Infrastructure

**Issues addressed:** #5  
**Files:** `features.py`  
**Wave:** 3 (depends on Task 1)

### Context

Current `_validate_features()` only checks: infinities, near-zero variance, heavy skew (>5), pairwise correlation (>0.95), extreme kurtosis (>20). No statistical rigor — no stationarity tests, no VIF, no feature importance analysis, no distribution normality test.

### Action

Add four new diagnostic blocks to `_validate_features()`. All produce **warnings only** — no auto-dropping.

**A) Stationarity (ADF test):**

```python
from statsmodels.tsa.stattools import adfuller

# Stationarity check (Augmented Dickey-Fuller)
print("\n  Stationarity (ADF test, H0: unit root):")
non_stationary = []
for col in features.columns:
    try:
        result = adfuller(features[col].dropna(), maxlag=20, autolag='AIC')
        p = result[1]
        tag = "STATIONARY" if p < 0.05 else "NON-STATIONARY"
        if p >= 0.05:
            non_stationary.append((col, p))
        print(f"    {col:25s}  p={p:.4f}  {tag}")
    except Exception:
        print(f"    {col:25s}  ADF failed")
if non_stationary:
    issues.append(f"Non-stationary features (ADF p>=0.05): "
                  f"{[(c, f'p={p:.3f}') for c, p in non_stationary]}")
```

**B) VIF (Variance Inflation Factor):**

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

# VIF check (multicollinearity)
print("\n  Variance Inflation Factors:")
X_vif = features.dropna().values
vif_data = []
for i, col in enumerate(features.columns):
    try:
        vif = variance_inflation_factor(X_vif, i)
        vif_data.append((col, vif))
    except Exception:
        vif_data.append((col, float('nan')))
vif_data.sort(key=lambda x: -x[1] if not np.isnan(x[1]) else 0)
for col, vif in vif_data:
    tag = " *** HIGH" if vif > 10 else ""
    print(f"    {col:25s}  VIF={vif:8.1f}{tag}")
high_vif = [(c, v) for c, v in vif_data if v > 10]
if high_vif:
    issues.append(f"High VIF (>10, multicollinear): "
                  f"{[(c, f'VIF={v:.1f}') for c, v in high_vif]}")
```

**C) Feature importance (PCA loadings + VIX correlation):**

```python
from sklearn.decomposition import PCA as _DiagPCA

# Feature importance: PCA loadings + VIX correlation
print("\n  Feature Importance (PCA loadings + VIX correlation):")
_pca = _DiagPCA(n_components=min(3, len(features.columns)))
_pca.fit(features.dropna().values)
loadings = pd.DataFrame(
    _pca.components_.T,
    index=features.columns,
    columns=[f'PC{i+1}' for i in range(min(3, len(features.columns)))],
)
loadings['abs_total'] = loadings.abs().sum(axis=1)
# VIX correlation (if VIX is in features or available externally)
if 'VIX' in features.columns:
    vix_corr = features.corrwith(features['VIX']).abs()
    loadings['|corr_VIX|'] = vix_corr

loadings = loadings.sort_values('abs_total', ascending=False)
print(loadings.to_string())
low_contrib = loadings[loadings['abs_total'] < 0.1].index.tolist()
if low_contrib:
    issues.append(f"Low PCA contribution (abs_total < 0.1): {low_contrib}")
```

**D) Distribution normality (Jarque-Bera):**

```python
from scipy.stats import jarque_bera

# Normality check (Jarque-Bera)
print("\n  Normality (Jarque-Bera):")
for col in features.columns:
    stat, p = jarque_bera(features[col].dropna())
    tag = "NORMAL" if p > 0.05 else "non-normal"
    print(f"    {col:25s}  JB={stat:10.1f}  p={p:.4f}  {tag}")
```

**Import placement:** Add the new imports at the top of the function body (inside `_validate_features`), not at module level, to avoid import overhead when validation isn't running.

### Verify

```bash
python -c "
import pandas as pd
from features import prepare_features
# This will run the full pipeline including the new validation
f = prepare_features()
print('Feature testing infrastructure: PASS')
"
```

Expected output should now show:
- Stationarity (ADF) results per feature
- VIF values per feature
- PCA loadings table
- Jarque-Bera normality results

### Done

- `_validate_features()` now runs 4 additional diagnostic checks
- All checks are warnings/diagnostics — nothing auto-drops features
- ADF confirms which features are stationary vs unit-root
- VIF confirms FEATURE_SUBSET doesn't have severe multicollinearity
- PCA loadings confirm each feature contributes signal
- Jarque-Bera flags extreme non-normality (relevant for Student-t emission fit)

---

## Task 6: Cleanup & Full Pipeline Verification

**Issues addressed:** All — integration test  
**Files:** (none modified — verification only)  
**Wave:** 4 (depends on all previous)

### Action

1. **Run full pipeline:**
```bash
python run.py collect
python run.py features
python run.py train
```

2. **Check for regressions:**
   - No crashes
   - Feature validation prints new diagnostic output (stationarity, VIF, importance, normality)
   - Walk-forward validation completes
   - Dashboard generates

3. **Verify causal winsorization:**
   - In the feature validation output, check that early-period features (2011) are NOT clipped by 2020-era extremes
   - Quick sanity: load `data/features_transformed.csv`, check that VIX on a calm 2011 day was NOT upper-clipped to a bound that reflects post-COVID data

4. **Verify FRED lag:**
   - Load `data/market_data.csv`
   - Check that FRED columns (yield_slope, hy_spread) have NaN on the first row (shifted out by 1 day)

5. **Verify pipeline consistency:**
   - Walk-forward output should show OOS labels — confirm they exist and are non-trivial (not all one regime)

6. **Update `.gsd/codebase/CONCERNS.md`:**
   - Mark Issues #1–#7 as RESOLVED
   - Add any new observations from the verification run

### Verify

```bash
python run.py all
# Should complete without errors and produce:
#   data/market_data.csv
#   data/features_transformed.csv  (renamed from features_raw.csv)
#   data/regime_results.csv
#   figures/regime_dashboard.html
#   models/hmm_model.pkl
#   models/pca_model.pkl
```

### Done

- Full pipeline runs end-to-end with all fixes applied
- No regressions in regime detection
- New feature validation output is printed and informative
- `features_scaled.csv` and `scaler.pkl` no longer generated
- `features_raw.csv` → `features_transformed.csv` everywhere
- Walk-forward uses same standardization + decoding as in-sample
- FRED data has publication lag buffer
- Winsorization is causal (expanding-window)

---

## Dependency Graph

```
Wave 1:  [Task 1: Causal Winsorize]  ||  [Task 2: FRED Lag]
              ↓                              ↓
Wave 2:  [Task 3: Walk-Forward Align]  ||  [Task 4: Rename + Cleanup]
              ↓                              ↓
Wave 3:  [Task 5: Feature Testing Infrastructure]
              ↓
Wave 4:  [Task 6: Full Pipeline Verification]
```

## Files Modified Summary

| File | Tasks | Changes |
|------|-------|---------|
| `features.py` | 1, 4, 5 | Causal `_winsorize()`; rename CSV output; remove scaled CSV + scaler writes; expand `_validate_features()` with ADF/VIF/PCA/JB |
| `collect.py` | 2 | FRED publication lag shift; import `FRED_PUB_LAG_DAYS` |
| `config.py` | 2 | Add `FRED_PUB_LAG_DAYS = 1` |
| `train.py` | 3, 4 | Extract `expanding_standardize()` helper; use in both `train()` and `walk_forward()`; switch `walk_forward()` to `filtered_labels()`; remove redundant subset filter; rename CSV path |
| `analyze.py` | 4 | Rename CSV path |

## Risk Assessment

- **Regime labels will shift slightly** after causal winsorization + FRED lag. This is expected and correct — the old labels had subtle lookahead contamination.
- **Walk-forward OOS performance may change** when switching from StandardScaler to expanding-window + from Viterbi to filtered labels. This is expected — we're now testing the actual production pipeline.
- **No math is touched.** HMM, SV, GARCH, HDP-HMM remain unchanged.
- **Feature count stays the same.** All 19 features / 15 in FEATURE_SUBSET remain.
