# Testing Patterns

**Analysis Date:** 2026-05-09

## Test Framework

**Runner:**
- pytest 9.0.2
- Config: no `pytest.ini` or `pyproject.toml` — pytest discovers tests from `tests/` automatically

**Assertion Library:**
- pytest `assert` statements with inline messages
- `numpy.testing` — `assert_allclose`, `assert_array_equal` for numeric precision checks
- `pandas.testing` — `assert_series_equal` for Series comparisons
- `inspect` module for API signature regression tests

**Run Commands:**
```bash
# Activate venv first
source .venv/bin/activate

pytest tests/ -v --tb=short              # Run all tests
pytest tests/ -v -m "not slow"           # Skip slow integration tests (fast CI)
pytest tests/test_causality.py -v        # Causality guarantees only
pytest tests/test_bot_integration.py -v  # Bot signal schema only
pytest tests/ -v                         # Full suite (277 test functions)
```

## Test File Organization

**Location:** All tests in `tests/` directory — not co-located with source.

**Naming:** `test_<subject>.py`

**Shared fixtures:** `tests/conftest.py` — three project-wide fixtures.

**Total:** 277 test functions across 32 test files (~5,974 lines). One file entirely skipped (`test_dashboard_hardening.py`).

## Test File Inventory

| File | Tests | Subject |
|------|-------|---------|
| `tests/test_causality.py` | 10 | No-lookahead guarantees — critical, CI priority |
| `tests/test_bot_integration.py` | 6 | Algo-Trading-Bot signal schema |
| `tests/test_train_refactor.py` | 22 | Refactoring regression + module size gate |
| `tests/test_var_backtesting.py` | 18 | VaR backtest (Kupiec, Christoffersen) |
| `tests/test_feature_selection_bias.py` | varies | Feature selection on held-out set |
| `tests/test_dashboard_hardening.py` | all skipped | Dashboard stress tests (functions removed in Phase 3 refactor) |
| `tests/test_regime_count_selection.py` | varies | K=3 regime count validation |
| `tests/test_model_card_validation.py` | varies | Model card completeness |
| `tests/test_regime_economic_validity.py` | varies | Regime economic interpretation |
| `tests/test_oos_fragmentation.py` | varies | OOS regime stability (requires live data fetch) |
| `tests/test_pca_caching.py` | varies | PCA checkpoint save/load |
| `tests/test_incremental_collection.py` | varies | Data cache append logic |
| `tests/test_dashboard_refactor.py` | varies | Dashboard module structure post-refactor |
| `tests/test_signal_combination.py` | varies | Signal combination logic |
| `tests/test_walk_forward.py` | varies | Walk-forward orchestrator |
| `tests/test_validation.py` | varies | VaR expanding-window validation |
| `tests/test_calibration.py` | varies | Regime calibration metrics |
| `tests/test_pipeline_stages.py` | 3 | Pipeline stage registry |
| `tests/test_pipeline_timing.py` | 1 (slow) | Full pipeline < 600s |
| `tests/test_exit_codes.py` | 1 (slow) | Stage failure returns exit code 1 |
| `tests/test_output_count.py` | 1 (slow) | Output file count |
| `tests/test_regime_results_freshness.py` | 1 (slow) | Results file age check |
| `tests/test_regime_results_schema.py` | varies | Results DataFrame schema |
| `tests/test_section_signals.py` | varies | Section signal building |
| `tests/test_signal_combination_performance.py` | varies | Signal combination perf |
| `tests/test_hdp_decision.py` | varies | HDP-HMM vs standard HMM decision |
| `tests/test_pipeline_idempotent.py` | varies | Pipeline re-run idempotency |
| `tests/test_oos_validation.py` | varies | OOS validation metrics |
| `tests/test_trust_scorecard.py` | varies | Regime trust scoring |
| `tests/test_features.py` | varies | Feature engineering |

## Test Structure

**Class-based grouping** — used when multiple tests share a subject or fixtures:
```python
class TestExpandingStandardize:
    def test_uses_only_past_data(self, rng): ...
    def test_warmup_is_nan(self, rng): ...
    def test_manual_computation(self): ...

class TestStaticVarFailure:
    def test_static_var_kupiec_passes(self, test_data_split): ...
    def test_static_var_christoffersen_fails(self, test_data_split): ...
```

**Function-based** — used for standalone import/API regression checks:
```python
def test_inference_imports():
    from src.core.inference import expanding_standardize, StudentTHMM, _fit_hmm, filtered_probs, filtered_labels
    assert callable(expanding_standardize)
```

**Docstring convention:** Each test function has a one-line docstring stating what it verifies, plus inline comments explaining the test mechanics:
```python
def test_uses_only_past_data(self, rng):
    """Modifying future rows must NOT change z-score at row t."""
    # Full run
    result_full, _, _ = expanding_standardize(X, min_warmup=50)
    # Truncated: only first 300 rows
    result_trunc, _, _ = expanding_standardize(X[:300], min_warmup=50)
    # Row 250 should be identical in both runs
    np.testing.assert_allclose(...)
```

## Shared Fixtures (conftest.py)

```python
@pytest.fixture
def rng():
    """Deterministic random state."""
    return np.random.RandomState(42)

@pytest.fixture
def synthetic_array(rng):
    """500x3 array with known statistical properties."""
    return rng.randn(500, 3) * np.array([1, 2, 3]) + np.array([10, 20, 30])

@pytest.fixture
def synthetic_features(rng):
    """DataFrame mimicking features_transformed.csv (500 rows, 5 cols)."""
    dates = pd.bdate_range('2020-01-01', periods=500)
    data = rng.randn(500, 5) * np.array([1, 2, 0.5, 3, 1.5])
    cols = ['VIX', 'VRP', 'rv_ratio_10_63', 'SPY_ret', 'credit_stress']
    return pd.DataFrame(data, index=dates, columns=cols)
```

File-local fixtures defined with `@pytest.fixture` inside the test file when only used by that file. Session-scoped fixtures used for expensive operations (live data fetch):
```python
@pytest.fixture(scope="session")
def market_data():
    """Load 2010-2026 market data for test suite."""
    _, _, _, market = collect()
    return market
```

## Mocking

**Framework:** `unittest.mock` — `patch`, `MagicMock` (used in `test_dashboard_hardening.py`).

**MockBotSignalHandler pattern** — custom mock class (not `unittest.mock`) used in `test_bot_integration.py` to simulate downstream bot consuming signals without depending on actual `algo-trading-bot` code:
```python
class MockBotSignalHandler:
    def consume_signal(self, signal: dict[str, Any]) -> bool:
        validate_signal_schema(signal)
        self.last_signal = signal
        self.signal_count += 1
        return True
```

**What to mock:** External data fetches (yfinance, FRED), filesystem I/O in unit tests, downstream bot consumers.

**What NOT to mock:** Core inference functions (`expanding_standardize`, `filtered_probs`, `filtered_labels`), the HMM model itself — these must be tested with real computation to verify causality guarantees.

## Pytest Markers

**`@pytest.mark.slow`** — marks tests that invoke the full pipeline via `subprocess.run`:
- `tests/test_pipeline_timing.py::test_pipeline_under_600s` — asserts pipeline < 600s
- `tests/test_exit_codes.py::test_stage_failure_returns_exit_1` — asserts exit code 1 on failure
- `tests/test_regime_results_freshness.py` — checks results file age
- `tests/test_output_count.py` — checks output file count

**`pytestmark = pytest.mark.skip(...)`** — module-level skip for `test_dashboard_hardening.py`. Reason: dashboard.py functions removed in Phase 3 refactor; tests are stale and must be rewritten against `scripts.pipelines.train.build_interactive_dashboard`.

Run fast tests only during development:
```bash
pytest tests/ -v -m "not slow"
```

## Causality Tests — Critical Priority

`tests/test_causality.py` contains 10 tests that are the highest-priority gate in the test suite. A failure here means regime labels are contaminated with future data and cannot be used for live trading.

**The three causality classes and what they verify:**

| Class | Tests | What would break |
|-------|-------|-----------------|
| `TestExpandingStandardize` | 3 | Future rows influence past z-scores |
| `TestFilteredProbs` | 3 | Backward pass (smoother) used instead of forward pass (filter) |
| `TestFilteredLabels` | 2 | Hysteresis not working; raw argmax used |
| `TestWinsorize` | 2 | Future outliers affect past winsorized values |

**Causality test pattern** — truncation comparison:
```python
# Full run
result_full, _, _ = expanding_standardize(X, min_warmup=50)
# Truncated: only first 300 rows
result_trunc, _, _ = expanding_standardize(X[:300], min_warmup=50)
# Row 250 must be identical (future rows 300-499 must not affect it)
np.testing.assert_allclose(result_full[250], result_trunc[250], rtol=1e-12,
    err_msg="expanding_standardize leaked future data into row 250")
```

**Smoother vs filter verification:**
```python
filtered = filtered_probs(model, X)
smoothed = model.predict_proba(X)
# They must NOT be identical — smoother uses future info
assert not np.allclose(filtered, smoothed, atol=1e-6), (
    "filtered_probs matches predict_proba — may be accidentally using backward pass"
)
```

## Refactoring Regression Tests (test_train_refactor.py)

Verifies that modularization of `train.py` into `inference.py`, `hmm_training.py`, `evaluation.py`, `orchestrator.py` did not break API compatibility. Key patterns:

**Import smoke tests:**
```python
def test_inference_imports():
    from src.core.inference import expanding_standardize, StudentTHMM, _fit_hmm, filtered_probs, filtered_labels
    assert callable(expanding_standardize)
```

**Signature regression:**
```python
def test_train_signature():
    from scripts.pipelines.train import train
    sig = inspect.signature(train)
    assert 'reload_pca_checkpoint_path' in sig.parameters
    assert sig.parameters['reload_pca_checkpoint_path'].default is None
```

**Module size gate (MODEL-03):**
```python
def test_module_size():
    """Assert every src/core/*.py file is <= 500 lines (MODEL-03 gate)."""
    core = Path(__file__).parent.parent / 'src' / 'core'
    ACCEPTED_EXCEPTIONS = {'hdp_hmm.py'}  # documented human override
    oversized = []
    for py in sorted(core.glob('*.py')):
        if py.name in ACCEPTED_EXCEPTIONS or py.name == '__init__.py':
            continue
        n = len(py.read_text(encoding='utf-8').splitlines())
        if n > 500:
            oversized.append(f"{py.name}: {n} lines")
    assert not oversized, f"Modules exceed 500 lines: {oversized}"
```

**Import origin enforcement (D-12):**
```python
def test_hmm_training_imports_pca_from_pca_utils():
    text = (core / 'hmm_training.py').read_text(encoding='utf-8')
    assert 'from src.core.pca_utils import fit_rolling_pca' in text
```

## Bot Integration Tests (test_bot_integration.py)

Tests the full signal pipeline → downstream bot compatibility. Uses a `MockBotSignalHandler` class that validates signal schema without depending on actual `algo-trading-bot` code.

**Key validations:**
- `bot_label` is one of `{LOW_VOL, MED_VOL, HIGH_VOL}` (never internal names like `Low-Vol`)
- `regime_probs` dict has exactly 3 keys summing to 1.0 (tolerance `1e-6`)
- `awareness` dict structure present
- `date` field is ISO-parseable string
- `LABEL_MAPPING` covers all regime names for all supported `N_STATES` values (2–6)

## VaR Backtesting Tests (test_var_backtesting.py)

Documents the architectural decision to use GARCH-conditional VaR over static VaR:

| Test Class | What it proves |
|------------|---------------|
| `TestStaticVarFailure` | Static VaR passes Kupiec but fails Christoffersen (exceedances cluster) |
| `TestGarchVarSuccess` | GARCH VaR passes both Kupiec and Christoffersen |
| `TestVarComparison` | Side-by-side comparison of both methods |
| `TestGarchVarComputation` | GARCH VaR numerical correctness and regime sensitivity |
| `TestVarValidation` | Signal schema includes `garch_var_95` field |
| `TestKupiecTest` | Kupiec POF test implementation correctness |

## CI/CD Pipeline (.github/workflows/tests.yml)

Manual trigger only (`workflow_dispatch`). Push/PR triggers are commented out.

**Job order:**
1. `check-version-pins` — rejects any `jax>=` or `numpyro>=` in `requirements.txt`; fails fast
2. `test` (needs `check-version-pins`) — runs on Python 3.10

**Test execution order within CI:**
```bash
pytest tests/test_causality.py -v           # Step 1: causality (most critical)
pytest tests/test_bot_integration.py -v     # Step 2: bot schema
pytest tests/test_incremental_collection.py -v  # Step 3: data cache
pytest tests/test_pca_caching.py -v        # Step 4: PCA checkpoint
pytest tests/test_dashboard_refactor.py -v  # Step 5: dashboard structure
pytest tests/ -v --tb=short                 # Step 6: full suite
```

## Test Data Patterns

**Synthetic DataFrames** with business-day date indices:
```python
dates = pd.bdate_range('2020-01-01', periods=500)
data = rng.randn(500, 5) * np.array([1, 2, 0.5, 3, 1.5])
```

**Synthetic price data** (random walk):
```python
returns = np.random.normal(0.0005, 0.01, n_days)
prices = 100 * np.exp(np.cumsum(returns))
```

**Synthetic regime assignments** (Dirichlet for valid probability simplex):
```python
raw_probs = np.random.dirichlet([1, 1, 1], size=n_days)
regime_indices = np.argmax(raw_probs, axis=1)
```

**Seed discipline:** `np.random.RandomState(42)` from the shared `rng` fixture, or `np.random.seed(42)` inline for standalone tests. `RANDOM_SEED = 42` used in model training via `src/config.py`.

## Coverage Gaps

**Known stale/skipped:** `tests/test_dashboard_hardening.py` — entire file skipped. Dashboard stress tests (20+ years data, malformed colors, NaN, performance benchmarks) are not covered after Phase 3 refactor removed `dashboard.py`. Rewrite target: `scripts.pipelines.train.build_interactive_dashboard`.

**Live data dependency:** `tests/test_oos_fragmentation.py` uses `scope="session"` fixtures that call `collect()` (live yfinance/FRED fetch). These tests cannot run in isolated CI environments without network access or pre-cached data.

**Phase 9 calibration failures not yet tested:**
- High-Vol dominance (61% of days assigned High-Vol, should be 15-25%)
- Label variant explosion (OOS walk-forward producing 8 variants instead of 3)
- GARCH VaR scaling bug (returns in wrong units in GARCH path)

These are active bugs as of 2026-05-09 with no test coverage yet — tracked in `.planning/STATE.md` and Phase 9.

**`hdp_hmm.py` (NumPyro HDP-HMM):** No dedicated unit test file. The Bayesian HDP-HMM implementation is the stated production-target model but tests exercise `StudentTHMM` (hmmlearn-backed) throughout. `test_hdp_decision.py` covers the decision logic but not the NumPyro inference itself.

---

*Testing analysis: 2026-05-09*
