# Testing Patterns

**Analysis Date:** 2026-03-22 (verified)

## Test Framework

**Runner:** pytest >= 8.0 (added to `requirements.txt`)

**Run Commands:**
```bash
pytest tests/ -v          # run all 28 tests (~4 seconds)
pytest tests/ -v -k causality   # run only causality tests
python run.py             # full pipeline integration smoke test
```

## Test File Organization

**Location:** `tests/`

| File | Tests | Coverage Area |
|------|-------|---------------|
| `test_causality.py` | 10 | Forward-only guarantees: `expanding_standardize`, `filtered_probs`, `filtered_labels`, `_winsorize` |
| `test_oos_validation.py` | 5 | OOS agreement rate, separation, graceful fallback |
| `test_calibration.py` | 5 | ECE computation, bin structure, missing data handling |
| `test_trust_scorecard.py` | 5 | Trust scorecard aggregation: PASS/WARN/FAIL propagation |
| `test_validation.py` | 3 | Expanding-window VaR backtest (non-tautological) |

**Total: 28 tests, all passing**

**Shared fixtures:** `tests/conftest.py` provides `rng`, `synthetic_array`, `synthetic_features` fixtures.

## What Each Test Proves

### Causality Tests (`test_causality.py`)
These are the bedrock — if any fail, every regime label is fraudulent.

- `test_uses_only_past_data` (expanding_standardize): Modifying rows after t doesn't change z-score at t
- `test_warmup_is_nan`: First `min_warmup` rows are NaN, row `min_warmup` is not
- `test_manual_computation`: Small 5x1 array matches hand-computed z-scores
- `test_uses_only_past_data` (filtered_probs): Replacing rows t+1..T with garbage doesn't change `probs[t]`
- `test_differs_from_smoother`: `filtered_probs()` != `model.predict_proba()` (proves forward-only)
- `test_probabilities_sum_to_one`: Row-wise probability normalization
- `test_hysteresis_suppresses_brief_blip`: 1-day blip doesn't flip label with `hold_days=3`
- `test_hold_days_1_equals_raw_argmax`: Hysteresis disabled = raw argmax
- `test_uses_only_past_data` (winsorize): Late outliers don't affect early winsorized values
- `test_warmup_period_unchanged`: First `min_warmup` rows pass through unclipped

### OOS Validation Tests (`test_oos_validation.py`)
- Agreement rate computation matches expected value
- Missing OOS columns handled gracefully (`{'available': False}`)
- Too few OOS rows → graceful fallback
- OOS separation (Kruskal-Wallis) runs without error
- Per-regime agreement breakdown is correct

### Calibration Tests (`test_calibration.py`)
- Perfect confidence-accuracy alignment → ECE near 0
- Random calibration baseline
- Missing smooth probability columns → graceful N/A
- Bin structure and interpretation string format

### Trust Scorecard Tests (`test_trust_scorecard.py`)
- All checks passing → overall PASS
- Single FAIL → overall FAIL (fail propagation)
- WARN without FAIL → overall WARN
- Missing OOS data → N/A (not crash)
- `format_scorecard()` produces non-empty string with expected content

### VaR Backtest Tests (`test_validation.py`)
- Expanding-window VaR breach rate is ~5% for normal returns
- `n_evaluated` < `n_total` (warmup excluded)
- Mean-shifted data produces non-trivial breach rate (proves test is not tautological)

## Baked-in Validation (Not Unit Tests)

Beyond the test suite, the codebase has runtime validation:

1. **Feature validation** (`features.py::_validate_features()`): ADF, VIF, PCA loadings, Jarque-Bera
2. **Statistical model validation** (`signals.py::_validation_metrics()`): Kruskal-Wallis, vol ordering, Kupiec POF, persistence
3. **Walk-forward OOS** (`train.py::walk_forward()`): Re-fits model on rolling windows
4. **HDP stability check** (`hdp_hmm.py::hdp_stability_check()`): Pairwise label agreement across 10 posterior draws
5. **Trust scorecard** (`trust.py::compute_trust_scorecard()`): Aggregates 8 checks into PASS/WARN/FAIL

## Remaining Coverage Gaps

**Medium priority:**
- `features.py` individual indicators (Garman-Klass, Parkinson, VRP)
- `hdp_hmm.py` stick-breaking, forward algorithm, `merge_similar_states`
- `fit_rolling_pca` + Procrustes alignment sign stability

**Low priority:**
- `collect.py` data download (requires mocking yfinance)
- `config.py` path construction

---

*Testing analysis: 2026-03-20 (updated — 28 tests added, causality gaps resolved)*
