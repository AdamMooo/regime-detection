# Troubleshooting Guide

## Common Issues & Solutions

### Issue 1: "Regimes Keep Flipping Every 1–2 Days"

**Symptom:** Regime label changes frequently (Low-Vol → Med-Vol → Low-Vol).

**Root cause:** Either (a) PCA is unstable, or (b) hysteresis is too short.

**Debug steps:**
1. Check config: `REGIME_HOLD_DAYS` should be ≥5 (minimum hold period)
   ```python
   # In config.py
   REGIME_HOLD_DAYS = 5  # Require 5 consecutive days in new regime before switching
   ```

2. Verify PCA stability:
   ```bash
   python -c "
   from features import build_features, fit_rolling_pca
   import pandas as pd
   market = pd.read_csv('data/market_data.csv')
   features = build_features(market)
   pcs, model = fit_rolling_pca(features)
   print(f'PCA variance explained: {model.explained_variance_ratio_}')
   print(f'PC stability: check if components flip signs')
   "
   ```

3. Run causality tests to ensure no lookahead:
   ```bash
   pytest tests/test_causality.py -xvs
   ```
   If any test fails, there's lookahead bias in features or standardization.

**Solution:**
- Increase `REGIME_HOLD_DAYS` to 7–10 days (more stable, adds lag)
- Or: Inspect PCA fitting — ensure rolling window is wide enough (e.g., 252 days)

---

### Issue 2: "Model Accuracy Degraded; Regime Assignment Doesn't Match Market Conditions"

**Symptom:** Model says Low-Vol but VIX is 30 (should be High-Vol).

**Root cause:** Data is stale, or model overfitting to historical regime structure.

**Debug steps:**
1. Check data freshness:
   ```bash
   python run.py collect  # Download latest data
   ```
   Verify no gaps: `python -c "import pandas as pd; d = pd.read_csv('data/market_data.csv'); print(f'Latest: {d.index[-1]}')"
   ```

2. Run OOS validation:
   ```bash
   python run.py train  # Full training with walk-forward CV
   python run.py regime  # Print validation metrics
   ```
   Check "OOS Separation" and "OOS Vol Ordering" (should both be PASS).

3. Inspect regime distributions:
   ```bash
   python -c "
   import pandas as pd
   from signals import compute_signals
   results = pd.read_csv('regime_results.csv', index_col=0, parse_dates=True)
   sigs = compute_signals(results)
   dists = sigs['distributions']
   for regime, stats in dists.items():
       print(f'{regime}: vol={stats[\"ann_vol\"]:.1%}')
   "
   ```
   Verify Low-Vol has lowest vol, High-Vol highest vol.

4. Check regime definitions (problem: regime 0, 1, 2 may have flipped):
   ```bash
   # In train.py::label_regimes(), ensure:
   # - Regime with lowest vol → 'Low-Vol'
   # - Regime with highest vol → 'High-Vol'
   ```

**Solution:**
- Retrain model: `python run.py train`
- Or: Adjust PCA window to be more recent-data-focused
- Or: Add new feature that better captures current market regime

---

### Issue 3: "Dashboard Crashes With 'NaN' or 'KeyError'"

**Symptom:** `python run.py dashboard` fails or renders blank.

**Root cause:** Missing data (NaN) in regime results or invalid color in config.

**Debug steps:**
1. Check regime_results.csv for NaN:
   ```bash
   python -c "
   import pandas as pd
   results = pd.read_csv('regime_results.csv', index_col=0, parse_dates=True)
   print(f'NaN count: {results.isna().sum().sum()}')
   print(f'Columns with NaN: {results.columns[results.isna().any()]}')
   "
   ```

2. Check color definitions in config.py:
   ```bash
   python -c "from config import REGIME_COLORS; print(REGIME_COLORS)"
   ```
   Verify all are valid hex colors: `#RRGGBB` format.

3. Run dashboard tests:
   ```bash
   pytest tests/test_dashboard_hardening.py -xvs
   ```
   Specific test: `test_hex_color_validation_invalid` (catches malformed colors).

**Solution:**
- Clean data: `python -c "results.dropna(); results.to_csv('regime_results.csv')"`
- Or: Fix colors in config.py to valid hex format
- Or: Run `python run.py train` to regenerate regime_results.csv with no gaps

---

### Issue 4: "Integration Test Fails: 'KeyError: Regime X not in LABEL_MAPPING'"

**Symptom:** `pytest tests/test_bot_integration.py` fails with KeyError.

**Root cause:** Regime count mismatch (N_STATES changed but LABEL_MAPPING not updated).

**Debug steps:**
1. Check N_STATES in config.py:
   ```bash
   python -c "from config import N_STATES; print(f'N_STATES = {N_STATES}')"
   ```
   Should be 3.

2. Check LABEL_MAPPING in config.py:
   ```bash
   python -c "from config import LABEL_MAPPING; print(LABEL_MAPPING)"
   ```
   Should have 3 entries: 'Low-Vol', 'Med-Vol', 'High-Vol'.

3. If N_STATES was changed, retrain:
   ```bash
   python run.py train
   ```
   This will produce 3 regimes and assign names via label_regimes().

**Solution:**
- Ensure N_STATES = 3 in config.py
- Ensure LABEL_MAPPING has 3 entries
- Retrain: `python run.py train`
- Re-test: `pytest tests/test_bot_integration.py -xvs`

---

## Debug Workflow

When something goes wrong:

1. **Check tests first:**
   ```bash
   pytest tests/ -xvs  # Run full suite
   ```
   Which tests fail? This narrows the problem.

2. **Check logs:**
   ```bash
   # Logs are written to stdout and (if configured) log files
   # Look for ERROR or WARNING messages
   ```

3. **Inspect intermediate data:**
   ```bash
   python -c "
   # Load regime_results.csv and inspect
   import pandas as pd
   results = pd.read_csv('regime_results.csv', index_col=0, parse_dates=True)
   print(results.tail(10))
   print(f'Dtypes: {results.dtypes}')
   print(f'NaN: {results.isna().sum()}')
   "
   ```

4. **Run specific pipeline step:**
   ```bash
   python run.py collect   # Just data collection
   python run.py features  # Just feature engineering
   python run.py train     # Just HMM training
   python run.py regime    # Just print signals
   ```

5. **Re-run full pipeline:**
   ```bash
   python run.py all  # Full pipeline: collect → features → train → signals
   ```

## Performance Issues

### Dashboard is slow (>5 sec render time)

Check:
1. Data size: `wc -l data/*.csv` — if >20 years (5200+ days), normal slowness
2. Plotly complexity: How many subplots/traces in dashboard? Can reduce
3. PCA/HMM computation: Already cached; check if cache is stale

Run benchmark:
```bash
pytest tests/test_dashboard_hardening.py::test_performance_benchmarks -xvs
```

### Training takes >10 minutes

Check:
1. Data size: `wc -l data/market_data.csv` — 16 years = ~4000 rows, should be <10 min
2. GARCH fitting: Can be slow; skip if not needed (set config flag)
3. Walk-forward CV: Can be slow if many folds; reduce WALK_FORWARD_STEP_DAYS

Optimize:
```bash
python run.py train  # Time this; should be 5–10 min for 16 years
```

## When All Else Fails

1. **Nuke and rebuild:**
   ```bash
   rm -rf data/*.csv  # Delete cached data
   rm -rf models/*    # Delete cached models
   python run.py all  # Full refresh
   ```

2. **Check CLAUDE.md for design constraints:**
   - NumPyro is HMM backend (not hmmlearn)
   - 13→PCA→HMM pipeline (don't skip PCA)
   - No K-means (probabilistic only)
   - Causal guarantees (no lookahead)

3. **Ask a human:** If no obvious issue, escalate to domain expert (Adam Morris).

## Validation Checklist

Before deploying regime signals to production:

- [ ] All tests pass: `pytest tests/ -xvs`
- [ ] Causality tests pass: `pytest tests/test_causality.py -xvs`
- [ ] Integration tests pass: `pytest tests/test_bot_integration.py -xvs`
- [ ] Regime distributions match market conditions (low-vol = calm, high-vol = stressed)
- [ ] Regime labels are stable (not flipping >2x per month)
- [ ] Bot signals have no NaN or missing values
- [ ] LABEL_MAPPING in config.py matches bot's expected convention
- [ ] README links to all documentation
