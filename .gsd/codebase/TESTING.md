# Testing Patterns

**Analysis Date:** 2026-03-16 (updated)

## Test Framework

**Runner:**
- None — no formal test framework is installed or configured
- No `pytest`, `unittest`, or equivalent present in `requirements.txt` or project root

**Assertion Library:**
- Python `assert` statements used inline for data quality guards (not unit tests)

**Run Commands:**
```bash
# No test commands available
# Full pipeline acts as integration smoke test:
python run.py
```

## Test File Organization

**Location:**
- No test files present — no `tests/`, `test_*.py`, or `*_test.py` files

## What Exists Instead of Tests

The codebase has several forms of baked-in validation that partially substitute for tests:

**1. Data quality assertions (`collect.py`, `features.py`, `train.py`):**
```python
assert len(market) >= 252, "Need at least 1 year of data"
```
These fail-fast if data is insufficient but do not test logic correctness.

**2. Feature validation (`features.py::_validate_features()`, line 276):**
- Infinity checks (hard fail)
- Near-zero variance detection
- Heavy skew warnings (|skew| > 5)
- Pairwise correlation > 0.95 warnings
- Extreme kurtosis warnings (> 20)
- ADF stationarity test per feature
- VIF multicollinearity check per feature
- PCA loadings (feature importance)
- Jarque-Bera normality test per feature

**3. Statistical model validation (`signals.py::_validation_metrics()`):**
- Kruskal-Wallis H-test — verifies regimes are statistically distinct on returns
- Vol ordering check — verifies regimes sort by volatility as expected
- Kupiec POF test — verifies VaR 5% violation rate is within 95% CI
- Persistence check — verifies regimes persist > 1 day on average

**4. Walk-forward out-of-sample validation (`train.py::walk_forward()`, line 556):**
- Rolls a 5-year training window forward in 21-day steps
- Re-fits full model on each window; assigns regimes on next 21-day period
- Uses identical pipeline to `train()`: `expanding_standardize()` + `filtered_labels()`
- Produces OOS labels stored in `regime_results.csv` for comparison

**5. Stability check (`train.py::check_stability()`, line 329):**
- Fits HMM with N_SEEDS (20) different random seeds; checks label agreement score
- Only used on the classic HMM path (USE_HDP=False)

**6. HDP posterior diagnostics (`hdp_hmm.py`):**
- `effective_K(samples)` computes posterior mean/mode of active states from SVI samples
- SVI ELBO loss tracked across 3000 steps; convergence visible in terminal output

## Coverage

**Requirements:** None enforced

**Untested modules:**
- `config.py` — no tests for path construction
- `collect.py` — no mocked tests for `yfinance` calls
- `features.py` — no unit tests for individual feature formulas (`_garman_klass_vol`, `_parkinson_vol`, etc.)
- `hdp_hmm.py` — no unit tests for stick-breaking, forward algorithm, or `merge_similar_states`
- `signals.py` — no unit tests for individual context functions
- `train.py` — no unit tests for `filtered_probs`, `expanding_standardize`, `fit_rolling_pca`, `label_regimes`

## Recommended Test Additions (Priority Order)

**High priority — logic correctness:**
- `filtered_probs`: verify forward-only (no future data leaks into probabilities)
- `expanding_standardize`: verify row t only uses data from rows [0..t], warm-up rows are NaN
- `_winsorize`: verify expanding-window percentiles (no future leakage)
- `fit_rolling_pca` + Procrustes alignment: verify loadings don't flip sign between windows
- `_fix_skew` / `_LOG_TRANSFORM_COLS`: verify log1p applied correctly and no negative values pre-transform
- `label_regimes`: verify regimes sort by ascending VIX mean correctly

**Medium priority — data pipeline:**
- `features.py::build_features()`: smoke test with synthetic OHLCV DataFrame
- `collect.py::collect()`: verify reindex + ffill produces correct aligned dates

**Low priority — statistical:**
- `signals.py::_validation_metrics()`: verify Kruskal-Wallis runs without error on synthetic labels

---

*Testing analysis: 2026-03-16 (updated)*
