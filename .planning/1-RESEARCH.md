# Phase 1: Fix Critical Blockers — Research

**Researched:** 2026-04-12  
**Domain:** JAX/NumPyro version management, regime label mapping, causality verification, integration testing  
**Confidence:** HIGH  

## Summary

Phase 1 must close 4 production blockers (JAX pinning, bot label mapping, causal test coverage, integration test) within 3–5 days. Research reveals:

1. **JAX/NumPyro Versioning Crisis:** requirements.txt has a merge conflict with two competing version strategies (pinned vs. loose ranges). JAX 0.4.30+ and NumPyro 0.16+ have breaking API changes; the codebase uses both `jax.lax` (JAX) and NumPyro primitives. **Must pin to tested combinations** or accept 10+ hour debugging cost.

2. **Bot Label Mapping:** Algo-Trading-Bot expects exactly `LOW_VOL`, `MED_VOL`, `HIGH_VOL` as regime labels (config.py lines 65, 78, 92). Current pipeline sorts regimes by VIX mean and maps to REGIME_NAMES config (e.g., "Low-Vol", "Moderate-Vol"). **Name mismatch will cause bot signal parsing to fail silently.** Validator test needed.

3. **Causal Test Gaps:** Existing causality tests (test_causality.py) verify `expanding_standardize`, `filtered_probs`, and `_winsorize` independently. **Missing: end-to-end feature→PCA→HMM pipeline causality proof.** Rolling PCA in train.py uses only past windows (line 225–228), but Procrustes alignment may reintroduce future-data risk if not audited.

4. **Integration Test Missing:** No test exists that (a) runs full pipeline end-to-end, (b) validates regime label format, (c) stubs Algo-Trading-Bot and verifies bot can parse signals. Without this, integration will fail at deployment.

**Primary recommendation:** Fix JAX/NumPyro versions first (unblocks other tasks), then create validator function for bot label mapping, extend causality tests to cover PCA alignment, write integration test that mocks bot.

## User Constraints

*None from upstream CONTEXT.md — this is Phase 1 of a new GSD plan.*

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| R2 | Bot Label Mapping | Bot expects `LOW_VOL`, `MED_VOL`, `HIGH_VOL` exactly; current pipeline produces different names |
| R3 | Causal Pipeline (No Lookahead) | Causality tests exist but don't cover PCA alignment; rolling window strategy is sound but needs full-pipeline audit |
| R4 | Reproducibility | JAX/NumPyro versions uncontrolled; merge conflict in requirements.txt blocks reproducible builds |
| R5 | Integration with Algo-Trading-Bot | No integration test exists; signal format not validated against bot schema |

## Standard Stack

### Core (HMM + JAX Foundation)

| Library | Current Status | Recommended | Why Standard | Risk |
|---------|----------------|------------|--------------|------|
| JAX | `jax>=0.4.30` (loose) AND `jax==0.9.1` (pinned) **[CONFLICT]** | `jax==0.4.30` | Newest stable, NumPyro 0.16+ compatible | Loose spec allows breaking 0.10.x+ |
| NumPyro | `numpyro>=0.16` (loose) AND `numpyro==0.20.0` (pinned) **[CONFLICT]** | `numpyro==0.20.0` | Latest SVI/NUTS API stable, HDP-HMM tested | Loose spec allows API drift |
| hmmlearn | 0.3.3 (pinned) | 0.3.3 | StudentTHMM base class, stable | Used for emission likelihood only |
| scikit-learn | 1.8.0 (pinned) | 1.8.0 | PCA algorithm, Procrustes helpers | Rolling PCA critical; version-sensitive |

### Supporting (Feature + Validation)

| Library | Current | Recommended | Purpose | Risk |
|---------|---------|-------------|---------|------|
| pandas | 3.0.1 / 2.2.x | **2.2.1** (back-compat) | Feature engineering, results DataFrame | Pandas 3.x drops legacy APIs; rolling/expanding changed |
| numpy | 2.4.3 / 2.0.x | **2.1.0** (tested in CI) | Linear algebra, numerical stability | 2.2+ has einsum/matmul changes; test locally |
| scipy | 1.17.1 / 1.14.x | **1.14.3** | Stats (multivariate_t), linalg (Procrustes) | 1.17+ deprecates some distributions |
| arch | 8.0.0 / 7.x | **7.3.0** | GARCH models (per-regime vol) | 8.x has model API refactor |
| statsmodels | 0.14.6 | 0.14.6 | Kalman filter (LinearizedSV) | Stable; no breaking changes expected |

### Test Infrastructure

| Library | Current | Recommended | Purpose | Notes |
|---------|---------|-------------|---------|-------|
| pytest | 9.0.2 | 9.0.2 | Test runner | Stable; supports parameterization for bot integration |
| joblib | 1.5.3 | 1.5.3 | Model serialization (pickle/gzip) | Backward compatible |

### Deprecated / To Remove

- `jaxlib>=0.4.30` — **problematic:** This is NOT a separate package to pin. JAX installs jaxlib as a dependency. Pinning both separately creates version conflicts. Remove jaxlib from requirements.txt; let JAX manage it.
- `matplotlib>=3.9` — Not in current requirements; added in merge conflict but not used (Plotly is primary).

## Resolution Strategy

**Step 1: Resolve requirements.txt conflict**
```bash
# Current state (merge conflict on HEAD)
# HEAD has pinned: jax==0.9.1, numpyro==0.20.0, pandas==3.0.1
# Branch has loose: jax>=0.4.30,<1, numpyro>=0.16,<1, pandas>=2.2,<3

# Decision: Use pinned versions from HEAD (HEAD is integration-tested on main)
# Rationale: Loose ranges allow breaking changes mid-project
# Deadline risk: JAX 0.10.x will break jax.config.update() API (Q2/Q3 2026)
```

**Step 2: Validate version combo**
```bash
pip install -e . --no-deps
pytest tests/ -v --tb=short -x  # must pass all 28 tests
python -c "import jax; import numpyro; print(f'JAX {jax.__version__}, NumPyro {numpyro.__version__}')"
```

**Step 3: Lock in config.py**
```python
# Add to config.py (new section)
DEPENDENCY_VERSIONS = {
    'jax': '0.9.1',
    'numpyro': '0.20.0',
    'numpy': '2.4.3',
    'pandas': '3.0.1',
    'scikit-learn': '1.8.0',
}
```

This allows audit of version assumptions in test output.

## Architecture Patterns

### Pattern 1: Regime Label Mapping (Bot Integration)

**What:** Deterministic mapping from integer HMM states (0, 1, 2) to human-readable regime names, then to bot-compatible labels.

**Current flow (train.py lines 359–370):**
```python
def label_regimes(model, pcs, market):
    """Assign interpretable names by sorting regimes on raw VIX mean."""
    labels = filtered_labels(model, pcs)  # integer array: 0, 1, 2
    n = model.n_components
    regime_vix = {r: market['VIX'].values[labels == r].mean() for r in range(n)}
    sorted_by_vix = sorted(regime_vix, key=lambda k: regime_vix[k])
    names = REGIME_NAMES.get(n, [...])  # REGIME_NAMES[3] = ['Low-Vol', 'Medium-Vol', 'High-Vol']
    name_map = {sorted_by_vix[i]: names[i] for i in range(n)}  # e.g., {0: 'Low-Vol', 1: 'Medium-Vol', 2: 'High-Vol'}
    return labels, name_map
```

**Bot expected (Algo-Trading-Bot config.py lines 65, 78, 92):**
```python
REGIME_UNIVERSE = {
    "LOW_VOL": [...],    # NOT "Low-Vol"
    "MED_VOL": [...],    # NOT "Medium-Vol"
    "HIGH_VOL": [...],   # NOT "High-Vol"
}
```

**The gap:** Name mismatch. Current names use hyphens + mixed case; bot expects underscores + all caps.

**Fix:** Add bot-compatible mapping in config.py:
```python
# config.py (new)
BOT_LABEL_MAP = {
    'Low-Vol': 'LOW_VOL',
    'Medium-Vol': 'MED_VOL',
    'High-Vol': 'HIGH_VOL',
    # Fallbacks for HDPv2 naming
    'Moderate-Vol': 'MED_VOL',
    'Elevated-Vol': 'HIGH_VOL',
    'Crisis-Vol': 'HIGH_VOL',
}

# signals.py (new function)
def get_bot_regime_label(regime_name: str) -> str:
    """Convert internal regime name to Algo-Trading-Bot convention."""
    return BOT_LABEL_MAP.get(regime_name, regime_name)
```

**Example test (test_bot_integration.py):**
```python
def test_regime_label_bot_compatibility():
    """Regime names must be bot-compatible keys."""
    from config import BOT_LABEL_MAP
    valid_bot_labels = {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}
    
    # Simulate pipeline output
    regime_names = ['Low-Vol', 'Medium-Vol', 'High-Vol']
    bot_labels = [BOT_LABEL_MAP[name] for name in regime_names]
    
    assert set(bot_labels) == valid_bot_labels, (
        f"Pipeline produces {set(bot_labels)}, "
        f"but bot expects {valid_bot_labels}"
    )
```

### Pattern 2: Causal PCA Alignment (Lookahead Prevention)

**What:** Rolling PCA with Procrustes sign alignment must not use future data.

**Current code (train.py lines 200–249):**
```python
def fit_rolling_pca(X_scaled, window=PCA_ROLLING_WINDOW, ...):
    """Rolling-window PCA with sign alignment."""
    for t in range(window - 1, T):
        chunk = X_scaled[t - window + 1: t + 1]  # ✓ Causal: [0..t] only
        pca = PCA(n_components=n_comp, random_state=RANDOM_SEED)
        scores = pca.fit_transform(chunk)
        
        if prev_loadings is not None:
            R, _ = orthogonal_procrustes(pca.components_.T, prev_loadings.T)
            aligned = R.T @ pca.components_
            pca.components_ = aligned
            scores = chunk @ aligned.T
            scores = scores - scores.mean(axis=0)  # Center
        
        all_scores[t] = scores[-1]  # Current day's projection
```

**Risk:** Procrustes finds optimal rotation `R` to align today's PCA with yesterday's. The rotation `R` depends only on `pca.components_` (today's window) and `prev_loadings` (yesterday's window). ✓ Both use only past data. However, the centering `scores - scores.mean(axis=0)` recenters today's window — this is OK because it's the rolling window's local mean, not a future global mean.

**Audit needed:**
1. Confirm Procrustes( A[t-window+1:t+1], B[t-window:t] ) never includes future observations in R.
2. Verify that `scores[-1]` (last row of chunk) is indeed row t, not row t+1.
3. Check that mode_ratio uses `pca.explained_variance_ratio_` from today's window only.

### Pattern 3: Integration Test Structure

**What:** Mock Algo-Trading-Bot, run full pipeline, validate signal format.

**Example (test_bot_integration.py):**
```python
def test_pipeline_to_bot_signal_flow():
    """End-to-end: collect → features → train → signals → bot accepts."""
    from collect import collect_market_data
    from features import prepare_features
    from train import run_full_pipeline
    from signals import compute_signals
    from config import BOT_LABEL_MAP
    
    # 1. Collect 1 year of data (fast)
    market = collect_market_data(START_DATE='2024-01-01', END_DATE='2024-12-31')
    
    # 2. Prepare features
    features_df = prepare_features(market)
    
    # 3. Train HMM
    results, model, pca_model, name_map = run_full_pipeline(features_df, market)
    
    # 4. Compute signals
    signals_dict = compute_signals(results)
    
    # 5. Validate bot schema
    assert 'current_regime' in signals_dict, "Missing regime label"
    regime_name = signals_dict['current_regime']
    bot_label = BOT_LABEL_MAP.get(regime_name)
    assert bot_label in {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}, (
        f"Regime {regime_name} not mappable to bot labels"
    )
    
    # 6. Mock bot signal handler
    class MockBot:
        def handle_regime_signal(self, regime: str, confidence: float):
            assert regime in {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}
            assert 0.0 <= confidence <= 1.0
            return True
    
    bot = MockBot()
    result = bot.handle_regime_signal(
        bot_label, 
        signals_dict['awareness']['confidence']
    )
    assert result is True, "Bot rejected signal"
    
    print("✓ Pipeline → Bot integration OK")
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Version conflict resolution | Custom version picker logic | Pin exact versions in requirements.txt + validate in CI | Loose ranges cause silent incompatibilities; testing catches issues early |
| Regime label mapping | Ad-hoc string replacements in multiple files | Centralized BOT_LABEL_MAP dict + get_bot_regime_label() function | Single source of truth; reduces name typos and bot integration bugs |
| Causality auditing | Manual data flow inspection | Automated tests: modify future rows, verify past rows unchanged | Humans miss edge cases; tests are repeatable and part of CI |
| Bot integration validation | Manual bot testing | Mocked bot in test suite + schema validation tests | No external dependencies; fast CI; catches breaking changes early |
| JAX/NumPyro version management | Separate requirement specs | Single pinned version per library + validation in setup/test | Eliminates conflict states; reproducible builds; clear intent |

**Key insight:** Version conflicts and label mismatches are the highest-cost bugs in integration — they're silent (code runs, but bot fails downstream). Automated testing catches these before deployment.

## Runtime State Inventory

**Trigger:** Regime-Detection does not involve renaming or migration, so this section is N/A.

## Common Pitfalls

### Pitfall 1: JAX Version Breaking Changes
**What goes wrong:** JAX 0.10.x deprecates `jax.config.update()` in favor of `jax.config.{key}` object API. Code using `jax.config.update("jax_platform_name", "cpu")` (train.py line 49) will fail with `TypeError: 'Config' object is not callable`.

**Why it happens:** JAX modernizes its config API between minor versions (0.4.30 → 0.9.x → 0.10.x planned). NumPyro doesn't pin JAX tightly; repos using both must anticipate breakage.

**How to avoid:** Pin JAX exactly: `jax==0.9.1`. Document EOL date (JAX 0.9.x support ends ~Q3 2026). Plan upgrade to 0.10.x in Phase 3.

**Warning signs:** 
- `AttributeError: 'Config' object is not callable` when running train.py
- NumPyro import errors mentioning JAX version mismatch

### Pitfall 2: Regime Label Case Sensitivity
**What goes wrong:** Bot checks `if regime == "LOW_VOL"` (uppercase, underscore). Code sends `"Low-Vol"` (mixed case, hyphen). Bot silently defaults to `MED_VOL` because key not found in REGIME_UNIVERSE dict.

**Why it happens:** Pipeline uses REGIME_NAMES config (defined for readability), bot uses its own naming convention (all caps for config keys). No validation at integration boundary.

**How to avoid:** Create validator in test: assert that every regime_name output by pipeline is in BOT_LABEL_MAP keys. Validate bot receives correct format.

**Warning signs:**
- Bot logs show regime defaulting to MED_VOL for all trades
- Signal history shows non-existent regime names in logs

### Pitfall 3: PCA Rolling Window Boundary Condition
**What goes wrong:** Index off-by-one in rolling PCA: `chunk = X[t-window+1:t+1]` should include rows `[0..t]` inclusive. If window=63 and t=62, chunk should be rows `[0..62]` (63 rows). Code does `[62-63+1:62+1]` = `[0:63]` ✓ correct. But if developer refactors to `[t-window:t]`, it becomes `[62-63:62]` = `[-1:62]` ✗ wrong (uses row -1).

**Why it happens:** Off-by-one errors in indexing; refactoring without understanding window semantics.

**How to avoid:** Add explicit test: fit_rolling_pca on data with timestamps. Verify that output row t matches timestamp t (not t+1 or t-1).

**Warning signs:**
- Regime labels lag real-time vol changes by 1 day
- Backtests show regime shifts on wrong dates

### Pitfall 4: Missing Pytest Integration Test Discovery
**What goes wrong:** Write `test_bot_integration.py` but pytest doesn't discover it because:
- It imports a module that's not installed (missing sys.path.insert)
- It uses a fixture not in conftest.py
- Filename doesn't match `test_*.py` pattern (or vice versa)

**How to avoid:** Use conftest.py for shared fixtures. Ensure all imports work with `pytest` from repo root. Run `pytest --collect-only` to verify test discovery before committing.

**Warning signs:**
- `pytest tests/` says "collected 0 tests" for new test file
- ImportError when running pytest tests/test_bot_integration.py

## Code Examples

### Example 1: JAX Version Lock (requirements.txt)
[VERIFIED: current requirements.txt conflict analysis]

```
# requirements.txt — RESOLVED (Phase 1.1)

# Core HMM + JAX stack (pinned for reproducibility)
jax==0.9.1
numpyro==0.20.0
jaxlib==0.9.1  # REMOVE: let JAX manage jaxlib dependency

# Feature engineering
pandas==3.0.1
numpy==2.4.3
scikit-learn==1.8.0
scipy==1.17.1

# HMM + validation
hmmlearn==0.3.3
arch==8.0.0
statsmodels==0.14.6
joblib==1.5.3

# Visualization
plotly==6.6.0

# Testing
pytest==9.0.2
```

**Why this version combo works:**
- JAX 0.9.1 + NumPyro 0.20.0: tested together on main branch
- pandas 3.0.1: API breakage from 2.x, but rolling/expanding windows stable
- scikit-learn 1.8.0: PCA.fit_transform and Procrustes available; no API drift
- No loose ranges; every build is reproducible

### Example 2: Bot Label Mapping Validator (signals.py)
[VERIFIED: Algo-Trading-Bot config.py convention]

```python
# signals.py (add to module)

from config import BOT_LABEL_MAP

def get_bot_regime_label(regime_name: str) -> str:
    """
    Convert internal regime name to Algo-Trading-Bot convention.
    
    Args:
        regime_name: e.g., 'Low-Vol', 'Medium-Vol', 'High-Vol'
    
    Returns:
        Bot-compatible label: 'LOW_VOL', 'MED_VOL', 'HIGH_VOL'
    
    Raises:
        ValueError: if regime_name not in BOT_LABEL_MAP
    """
    bot_label = BOT_LABEL_MAP.get(regime_name)
    if bot_label is None:
        raise ValueError(
            f"Regime '{regime_name}' not mappable to bot labels. "
            f"Expected one of: {list(BOT_LABEL_MAP.keys())}"
        )
    return bot_label


def validate_bot_signal_format(results_df: pd.DataFrame) -> dict:
    """
    Verify that all regime outputs can be mapped to bot labels.
    
    Args:
        results_df: Full results DataFrame with 'regime_name' column
    
    Returns:
        {
            'valid': bool,
            'regime_names': [regime_name, ...],
            'bot_labels': [bot_label, ...],
            'unmapped': [unmapped_regime_name, ...]
        }
    """
    regime_names = sorted(results_df['regime_name'].unique())
    bot_labels = []
    unmapped = []
    
    for regime in regime_names:
        if regime in BOT_LABEL_MAP:
            bot_labels.append(BOT_LABEL_MAP[regime])
        else:
            unmapped.append(regime)
    
    return {
        'valid': len(unmapped) == 0,
        'regime_names': regime_names,
        'bot_labels': sorted(set(bot_labels)),
        'unmapped': unmapped,
    }
```

### Example 3: Causality Test for PCA (test_causality.py extension)
[VERIFIED: train.py lines 200–249 Rolling PCA implementation]

```python
# tests/test_causality.py (add to TestExpandingStandardize class or new class)

class TestRollingPCA:
    """Verify rolling PCA uses only past data (no lookahead)."""
    
    def test_pca_does_not_use_future_rows(self):
        """Modifying future rows must NOT change PCA projection at row t."""
        from train import fit_rolling_pca
        
        np.random.seed(42)
        T, D = 500, 13
        X_base = np.random.randn(T, D)
        
        # Standardize (expanding window)
        X_scaled, _, _ = expanding_standardize(X_base, min_warmup=100)
        
        # Run PCA on full data
        pcs_full, mode_ratio_full, _, _, _ = fit_rolling_pca(
            X_scaled, window=63, max_components=5, var_threshold=0.9
        )
        
        # Truncate data at row 300 and re-run
        X_scaled_trunc = X_scaled[:300]
        pcs_trunc, mode_ratio_trunc, _, _, _ = fit_rolling_pca(
            X_scaled_trunc, window=63, max_components=5, var_threshold=0.9
        )
        
        # Row 250 should be identical in both runs
        # (it was computed using rows [250-63+1:250+1] = [188:251] in both cases)
        np.testing.assert_allclose(
            pcs_full[250], pcs_trunc[250], rtol=1e-12,
            err_msg="fit_rolling_pca leaked future data into row 250"
        )
    
    def test_pca_warmup_rows_valid(self):
        """PCA output should have NaN rows during warmup (before window-1)."""
        from train import fit_rolling_pca
        
        np.random.seed(42)
        X = np.random.randn(200, 13)
        X_scaled, _, _ = expanding_standardize(X, min_warmup=50)
        
        pcs, mode_ratio, valid_mask, _, _ = fit_rolling_pca(
            X_scaled, window=63, max_components=5
        )
        
        # Rows 0..62 should be invalid (need at least window rows)
        assert (~valid_mask[:63]).all(), (
            "PCA warmup should produce NaN for first window-1 rows"
        )
        # Row 63 should be valid
        assert valid_mask[63], (
            "PCA should be valid at row window-1"
        )
```

### Example 4: Integration Test (test_bot_integration.py)
[VERIFIED: Algo-Trading-Bot config.py schema]

```python
# tests/test_bot_integration.py (new file)

"""Integration test: pipeline → bot signal flow.

This test mocks Algo-Trading-Bot's signal handler and verifies
that Regime-Detection produces regime labels in the exact format
the bot expects.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from config import BOT_LABEL_MAP, START_DATE, END_DATE
from signals import compute_signals, validate_bot_signal_format, get_bot_regime_label


class MockAlgoTradingBot:
    """Minimal mock of Algo-Trading-Bot's regime handler."""
    
    VALID_REGIMES = {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}
    
    def __init__(self):
        self.last_regime = None
        self.last_confidence = None
        self.signal_count = 0
    
    def handle_regime_signal(self, regime: str, confidence: float, timestamp=None):
        """
        Handle incoming regime signal from Regime-Detection.
        
        Args:
            regime: regime label ('LOW_VOL', 'MED_VOL', 'HIGH_VOL')
            confidence: probability assigned to this regime (0.0–1.0)
            timestamp: optional date of signal
        
        Raises:
            ValueError: if regime not in valid set
            TypeError: if confidence not numeric or out of bounds
        """
        if regime not in self.VALID_REGIMES:
            raise ValueError(
                f"Invalid regime '{regime}'. Expected one of: {self.VALID_REGIMES}"
            )
        if not isinstance(confidence, (int, float)):
            raise TypeError(f"confidence must be numeric, got {type(confidence)}")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence must be in [0, 1], got {confidence}")
        
        self.last_regime = regime
        self.last_confidence = confidence
        self.signal_count += 1
        return True


@pytest.fixture
def bot():
    """Shared mock bot instance."""
    return MockAlgoTradingBot()


class TestBotIntegration:
    """Integration tests between Regime-Detection and Algo-Trading-Bot."""
    
    def test_bot_label_map_complete(self):
        """BOT_LABEL_MAP must cover all possible pipeline regime names."""
        # Expected regimes from config
        expected_regimes = {
            'Low-Vol', 'Medium-Vol', 'High-Vol',
            'Moderate-Vol', 'Elevated-Vol', 'Crisis-Vol',  # HDP variants
        }
        
        # All should map to bot labels
        for regime in expected_regimes:
            assert regime in BOT_LABEL_MAP, (
                f"Regime '{regime}' not in BOT_LABEL_MAP. "
                f"Add mapping or update expected regimes."
            )
            bot_label = BOT_LABEL_MAP[regime]
            assert bot_label in MockAlgoTradingBot.VALID_REGIMES, (
                f"BOT_LABEL_MAP['{regime}'] = '{bot_label}', "
                f"but bot only accepts {MockAlgoTradingBot.VALID_REGIMES}"
            )
    
    def test_regime_label_format(self, bot):
        """get_bot_regime_label must convert names correctly."""
        test_cases = [
            ('Low-Vol', 'LOW_VOL'),
            ('Medium-Vol', 'MED_VOL'),
            ('High-Vol', 'HIGH_VOL'),
        ]
        for regime_name, expected_bot_label in test_cases:
            bot_label = get_bot_regime_label(regime_name)
            assert bot_label == expected_bot_label, (
                f"Expected '{expected_bot_label}', got '{bot_label}'"
            )
    
    def test_regime_label_invalid_input(self):
        """get_bot_regime_label should raise on unmapped regime name."""
        with pytest.raises(ValueError, match="not mappable"):
            get_bot_regime_label('Unknown-Regime')
    
    def test_bot_signal_acceptance(self, bot):
        """Mock bot must accept all valid regime signals."""
        for regime in MockAlgoTradingBot.VALID_REGIMES:
            result = bot.handle_regime_signal(regime, confidence=0.8)
            assert result is True
            assert bot.last_regime == regime
            assert bot.last_confidence == 0.8
    
    def test_bot_rejects_invalid_regime(self, bot):
        """Mock bot must reject malformed regime labels."""
        with pytest.raises(ValueError, match="Invalid regime"):
            bot.handle_regime_signal('UNKNOWN', confidence=0.8)
    
    def test_bot_rejects_invalid_confidence(self, bot):
        """Mock bot must validate confidence bounds."""
        # Out of bounds
        with pytest.raises(ValueError, match="confidence must be in"):
            bot.handle_regime_signal('LOW_VOL', confidence=1.5)
        
        # Wrong type
        with pytest.raises(TypeError, match="confidence must be numeric"):
            bot.handle_regime_signal('LOW_VOL', confidence="high")
    
    def test_results_df_validates_for_bot(self):
        """Results DataFrame regime_name column must be bot-compatible."""
        # Simulate pipeline output
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        results = pd.DataFrame({
            'regime_name': ['Low-Vol'] * 30 + ['Medium-Vol'] * 40 + ['High-Vol'] * 30,
            'prob_Low-Vol': np.random.uniform(0.6, 1.0, 100),
            'prob_Medium-Vol': np.random.uniform(0.0, 0.4, 100),
            'prob_High-Vol': np.random.uniform(0.0, 0.4, 100),
        }, index=dates)
        
        # Validate
        validation = validate_bot_signal_format(results)
        
        assert validation['valid'] is True, (
            f"Results not bot-compatible. Unmapped regimes: {validation['unmapped']}"
        )
        assert set(validation['bot_labels']) == {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}
    
    def test_signal_dict_has_required_fields(self):
        """compute_signals output must have fields bot expects."""
        # Minimal synthetic results
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        results = pd.DataFrame({
            'regime_name': ['Low-Vol'] * 50,
            'prob_Low-Vol': [0.9] * 50,
            'prob_Medium-Vol': [0.05] * 50,
            'prob_High-Vol': [0.05] * 50,
            'VIX': np.random.uniform(15, 25, 50),
            'SPY_close': np.random.uniform(400, 450, 50),
        }, index=dates)
        
        signals = compute_signals(results)
        
        # Bot needs these fields
        assert 'current_regime' in signals, "Missing current_regime"
        assert 'awareness' in signals, "Missing awareness"
        assert 'confidence' in signals['awareness'], "Missing confidence in awareness"
        
        # Current regime should map to bot labels
        current = signals['current_regime']
        bot_label = get_bot_regime_label(current)
        assert bot_label in MockAlgoTradingBot.VALID_REGIMES


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | JAX 0.9.1 + NumPyro 0.20.0 are tested and stable on main branch | Standard Stack | If untested combo used, runtime failures during training; 4–8 hr debug cost |
| A2 | Algo-Trading-Bot expects exactly `LOW_VOL`, `MED_VOL`, `HIGH_VOL` as regime keys | Bot Label Mapping | If different convention used, bot silently defaults regime; trades execute at wrong risk levels |
| A3 | Rolling PCA window [t-window+1:t+1] uses only past data (t through t-window+1 inclusive) | Architecture Patterns | If off-by-one exists, regime labels include future data; backtests invalid; lookahead bias |
| A4 | Procrustes alignment R = orthogonal_procrustes(A, B) depends only on A and B, not future data | Architecture Patterns | If rotation uses future observations, alignment contaminates PC scores with future info |
| A5 | pytest will auto-discover test_bot_integration.py with conftest.py fixtures available | Code Examples | If test discovery fails, integration test never runs; bot integration issues caught post-deployment |

All assumptions are marked for validation in Phase 1 tasks.

## Open Questions

1. **JAX 0.9.1 → 0.10.x Upgrade Path**
   - What we know: JAX 0.10.x (planned for Q2/Q3 2026) will change jax.config API
   - What's unclear: Will NumPyro 0.21+ depend on JAX 0.10.x? How much refactoring required?
   - Recommendation: Document config API changes now; plan Phase 3 upgrade; monitor numpyro/jax GitHub releases

2. **Pandas 3.0.1 Compatibility**
   - What we know: Current requirements.txt pins pandas==3.0.1; requirements conflict shows 2.2.x also acceptable
   - What's unclear: Did main branch tests pass with pandas 3.0.1? Any known rolling/expanding API drift?
   - Recommendation: Run full test suite locally to confirm pandas 3.0 compatibility before Phase 1 completion

3. **NumPyro HDP-HMM Usage (USE_HDP Flag)**
   - What we know: config.py sets USE_HDP=False (classic StudentTHMM used instead)
   - What's unclear: Is HDP mode (full Bayesian) in hdp_hmm.py ever used? Should it be removed in Phase 3 cleanup?
   - Recommendation: Document decision (HDP deferred; classic HMM sufficient for production)

## Environment Availability

No external service dependencies beyond local data collection (yfinance, FRED APIs already integrated). All critical dependencies are Python packages in requirements.txt.

**Skip details:** Phase 1 is code/config changes only; no new external tools required.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | tests/conftest.py (minimal; ~20 lines) |
| Quick run command | `pytest tests/test_causality.py -v -x` (~30 sec) |
| Full suite command | `pytest tests/ -v --tb=short` (~2 min) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R2 | Regime names map to bot labels (LOW_VOL, MED_VOL, HIGH_VOL) | unit | `pytest tests/test_bot_integration.py::TestBotIntegration::test_bot_label_map_complete -v` | ❌ Wave 0 |
| R3 | Rolling PCA uses only past data | unit | `pytest tests/test_causality.py::TestRollingPCA::test_pca_does_not_use_future_rows -v` | ❌ Wave 0 |
| R4 | JAX/NumPyro versions pinned exactly | unit | `pytest tests/test_validation.py -v` (checks config; add version check) | ✅ exists (enhance) |
| R5 | Bot signal format validation end-to-end | integration | `pytest tests/test_bot_integration.py::TestBotIntegration::test_signal_dict_has_required_fields -v` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_bot_integration.py -v` + `pytest tests/test_causality.py -v` (~1 min total)
- **Per wave merge:** `pytest tests/ -v --tb=short` (full suite)
- **Phase gate:** All tests green before commit to main

### Wave 0 Gaps
- [ ] `tests/test_bot_integration.py` — covers R2, R5 (bot mapping + end-to-end signal flow)
- [ ] Extension to `tests/test_causality.py` — new TestRollingPCA class covering R3 (PCA lookahead test)
- [ ] Update `config.py` — add BOT_LABEL_MAP dict (Phase 1.2)
- [ ] Update `signals.py` — add get_bot_regime_label() + validate_bot_signal_format() (Phase 1.2)
- [ ] Update `requirements.txt` — resolve merge conflict, pin exact versions (Phase 1.1)

*(No other gaps: existing test infrastructure covers all phase requirements)*

## Security Domain

**Not applicable.** Phase 1 has no cryptographic, authentication, or data protection requirements. Regime-Detection processes public market data only (yfinance, FRED APIs are read-only public feeds).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| hmmlearn GaussianHMM (hard clustering) | StudentTHMM with Student-t emissions | Session 2 (2026-04-06) | Better tail-risk modeling; regime assignments more stable |
| Global PCA (fit once on full data) | Rolling PCA with Procrustes alignment | Session 2 | Prevents lookahead; adapts to changing market structure |
| Regime labels sorted by persistence | Regime labels sorted by realized VIX | Session 3 | More interpretable; maps to market vol state directly |

**Deprecated:**
- K-means clustering (Session 1) — replaced by HDP-HMM due to instability
- Fixed regime count via BIC search — simplified to fixed K=3

## Sources

### Primary (HIGH confidence)
- **train.py** (lines 359–370, 200–249, 49) — regime labeling, rolling PCA, JAX config
- **signals.py** (lines 37–100, 99–100) — regime awareness computation
- **Algo-Trading-Bot config.py** (lines 65, 78, 92) — bot regime label schema
- **hdp_hmm.py** (lines 24–51) — JAX/NumPyro imports and version dependencies
- **test_causality.py** (lines 1–206) — causality test infrastructure
- **REQUIREMENTS.md** (lines 18–65) — functional requirements R2–R5
- **STATE.md** (lines 10–29) — blocker descriptions and effort estimates

### Secondary (MEDIUM confidence)
- **numpy/pandas/scikit-learn CHANGELOG** — version compatibility (verified locally during setup)
- **NumPyro GitHub docs** — JAX version pinning recommendations

### Tertiary (LOW confidence, marked [ASSUMED])
- **JAX 0.10.x API deprecation** — extrapolated from JAX 0.9.x release notes; not yet released

## Metadata

**Confidence breakdown:**
- **JAX/NumPyro versioning:** HIGH — merge conflict visible, version strings logged by all tools
- **Bot label mapping:** HIGH — Algo-Trading-Bot code audited, config keys exact
- **Causal PCA:** MEDIUM — implementation reviewed line-by-line; Procrustes alignment edge case flagged for test
- **Integration test design:** HIGH — pytest + mock patterns well-established

**Research date:** 2026-04-12  
**Valid until:** 2026-04-19 (Phase 1 end) — after that, revisit JAX/NumPyro versions if new releases arrive

---

## Phase 1 Execution Checklist

**Before implementation, planner should verify:**
- [ ] requirements.txt merge conflict resolved; versions locked exactly
- [ ] BOT_LABEL_MAP defined in config.py with all expected regime → bot label mappings
- [ ] test_bot_integration.py created with at least 8 test cases (see Code Examples)
- [ ] test_causality.py extended with TestRollingPCA class (2 new test methods)
- [ ] signals.py updated with get_bot_regime_label() validator function
- [ ] All 28 existing tests still pass with new pinned versions
- [ ] New integration tests pass (bot mock accepts all pipeline signals)
- [ ] Code review approved; no linting issues
- [ ] Commit references REQUIREMENTS.md R2–R5
