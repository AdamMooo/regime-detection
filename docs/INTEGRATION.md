# Integration Guide — Algo-Trading-Bot

Regime-Detection produces signals consumed by Algo-Trading-Bot to adjust trading strategy dynamically based on market regime.

## Signal Output Format

`signals.py::compute_signals()` returns a dict with regime awareness context:

```python
{
  'date': '2024-01-15',
  'current_regime': 'Med-Vol',
  'bot_label': 'MED_VOL',  # ← Use this for bot integration
  'awareness': {
    'confidence': 0.78,          # Probability of current regime
    'days_in_regime': 12,        # How long in this regime
    'median_duration': 45        # Historical median duration for this regime
  },
  'distributions': {
    # Per-regime statistics (annualized vol, skew, VaR, max DD, etc.)
    'Low-Vol': {'ann_vol': 0.15, 'var_5': -0.012, ...},
    'Med-Vol': {'ann_vol': 0.25, 'var_5': -0.020, ...},
    'High-Vol': {'ann_vol': 0.45, 'var_5': -0.045, ...}
  },
  'vol_context': {
    'vix': 18.5,
    'vrp': -2.3  # VIX risk premium
  },
  'transitions': [
    {'regime': 'High-Vol', 'probability': 0.15, 'direction': 'up', ...},
    # Nearby regimes in probability space
  ],
  'validation': {
    'separation_significant': True,  # Regimes statistically distinct?
    'vol_ordering_match': True,      # Vol increases with regime?
    'var_backtest': {                # VaR backtests per regime
      'Low-Vol': {'ok': True, 'exceedances': 2, 'expected': 3},
      'Med-Vol': {'ok': True, 'exceedances': 5, 'expected': 6},
      'High-Vol': {'ok': True, 'exceedances': 9, 'expected': 10}
    }
  },
  'oos_validation': {
    'agreement_rate': 0.73,  # IS-OOS label agreement
    ...
  },
  'calibration': {
    'ece': 0.032,  # Expected Calibration Error
    'interpretation': 'Good calibration'
  }
}
```

## Label Mapping Convention

Regimes are mapped to bot labels via `config.py::LABEL_MAPPING`:

```python
LABEL_MAPPING = {
    'Low-Vol': 'LOW_VOL',      # Regime 0 (calm market, tight ranges)
    'Med-Vol': 'MED_VOL',      # Regime 1 (normal market conditions)
    'High-Vol': 'HIGH_VOL'     # Regime 2 (stressed market, high drawdown risk)
}
```

**Important:** This mapping is the source of truth. All downstream consumers must use `bot_label` from signals, not `current_regime`.

## Consuming Signals in Algo-Trading-Bot

### Step 1: Load regime signals

```python
import pandas as pd
from signals import compute_signals

results = pd.read_csv('regime_results.csv', index_col=0, parse_dates=True)
signals = compute_signals(results)

regime = signals['awareness']['current_regime']      # e.g., 'Med-Vol' (internal)
bot_label = signals['bot_label']                     # e.g., 'MED_VOL' (bot-compatible)
confidence = signals['awareness']['confidence']      # 0.0 – 1.0
distribution = signals['distributions'][regime]     # Per-regime stats
```

### Step 2: Adjust strategy based on regime

Example: Position sizing via Kelly criterion (regime-adjusted)

```python
def kelly_sizing(regime_label: str, baseline_kelly: float = 0.25) -> float:
    """Adjust Kelly fraction based on regime risk."""
    kelly_adjustments = {
        'LOW_VOL': 1.5,      # Increase leverage in calm market
        'MED_VOL': 1.0,      # Normal Kelly
        'HIGH_VOL': 0.5      # Reduce leverage in stressed market
    }
    multiplier = kelly_adjustments.get(regime_label, 1.0)
    return baseline_kelly * multiplier

# In your trading strategy:
adjusted_kelly = kelly_sizing(signals['bot_label'])
position_size = account_risk_budget * adjusted_kelly
```

### Step 3: Monitor regime transitions

Regime changes may indicate risk regime shift. Alert when:
- Regime changes (check `signals['awareness']['days_in_regime']` resets)
- Transition probability to High-Vol increases (check `signals['transitions']`)
- Confidence decreases (check `signals['awareness']['confidence']` < 0.6)

## Adding New Signal Fields

To add a new signal field (e.g., regime forecast, expected duration):

1. Implement the calculation in `signals.py`
2. Add to return dict in `compute_signals()`
3. Update schema validation in `tests/test_bot_integration.py`
4. Document in this guide
5. Update CLAUDE.md
6. Run integration tests: `pytest tests/test_bot_integration.py -xvs`

Example:

```python
# signals.py
def _regime_forecast(results: pd.DataFrame) -> dict:
    """Forecast regime 5–10 days ahead based on transition matrix."""
    # ... calculate forecast ...
    return {'forecast_regime': 'Med-Vol', 'forecast_confidence': 0.65}

# In compute_signals():
forecast = _regime_forecast(results)
return {
    ...
    'forecast': forecast,  # New field
}
```

## Testing Integration

Run integration tests to ensure signal schema matches bot expectations:

```bash
pytest tests/test_bot_integration.py -xvs
```

Tests validate:
- Signal dict has required keys (awareness, distributions, bot_label, etc.)
- bot_label is in LABEL_MAPPING (valid)
- Regime probabilities sum to ~1.0
- No missing or NaN values in critical fields

## Troubleshooting Integration

**Bot fails to consume signals:**
1. Check `signals['bot_label']` matches bot's expected values (LOW_VOL, MED_VOL, HIGH_VOL)
2. Verify LABEL_MAPPING in config.py matches bot's convention
3. Check for NaN or missing values in signal dict
4. Run `pytest tests/test_bot_integration.py -xvs` to diagnose

**Regimes don't match bot expectations:**
1. Verify regime labeling logic in `train.py::label_regimes()` — should assign names based on volatility
2. Check CLAUDE.md causality guarantees are met (no lookahead)
3. Run `python run.py trust` to see regime validation metrics

**Signal schema changed:**
1. Check git diff: what fields were added/removed?
2. Update bot schema validation accordingly
3. Update this guide to document new fields

## Signal Reliability

### Confidence Score Interpretation

The `confidence` field indicates how certain the model is about the current regime:

- **0.80–1.0:** High confidence. Regime assignment is reliable. Use at full position size.
- **0.60–0.80:** Moderate confidence. Regime is likely but uncertain. Consider slight position reduction.
- **0.40–0.60:** Low confidence. Regime could change soon. Reduce position or use conservative sizing.
- **<0.40:** Very low confidence. Regime is ambiguous. Use baseline sizing or wait for clarity.

### Regime Duration Statistics

The `median_duration` field helps anticipate regime persistence:

- If `days_in_regime` is close to `median_duration`, regime may be ending soon
- If `days_in_regime` < `median_duration / 2`, regime is young and may persist longer

Use this to adjust portfolio rebalancing frequency.

### Transition Probabilities

The `transitions` field lists regimes reachable in the next period with their probabilities:

```python
transitions = [
    {'regime': 'Med-Vol', 'probability': 0.70},  # 70% chance stay in Med-Vol
    {'regime': 'High-Vol', 'probability': 0.20},  # 20% chance move to High-Vol
    {'regime': 'Low-Vol', 'probability': 0.10}   # 10% chance move to Low-Vol
]
```

Use this to hedge against imminent regime changes (e.g., reduce position if High-Vol transition prob > 50%).
