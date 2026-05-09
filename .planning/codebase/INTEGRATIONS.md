# External Integrations

**Analysis Date:** 2026-05-09

## APIs & External Services

**Market Data — Yahoo Finance:**
- Provider: yfinance 1.2.0 (`src/features/collect.py`)
- No API key required (public endpoints)
- Tickers (OHLCV): SPY, QQQ, IWM, EEM, TLT, HYG, GLD (configured via `TICKERS` in `src/config.py`)
- Volatility family: `^VIX` (VIX), `^VIX3M` (3-month VIX term structure), `^VVIX` (vol-of-VIX)
- Date range: 2010-01-01 to present (`START_DATE = '2010-01-01'`, `END_DATE = None`)
- Supports incremental fetch: delta-only updates via SHA256 manifest in `data/cache/.cache_manifest.json`
- Output: `data/market_data.csv` — OHLCV aligned to SPY trading-day index

**Macro Data — FRED (Federal Reserve Economic Data):**
- Provider: fredapi >=0.5 (primary path) or pandas_datareader >=0.10 (unauthenticated fallback)
- Auth: `FRED_API_KEY` env var (optional; read via `os.getenv('FRED_API_KEY', '')` in `src/config.py`)
- Implementation: `src/data/collect_macro.py`
- Series fetched:

| FRED Code | Canonical Name | Frequency | Meaning |
|-----------|----------------|-----------|---------|
| `T10Y2Y` | `yield_curve_slope` | Daily | 10Y–2Y Treasury spread |
| `BAMLH0A0HYM2` | `HY_OAS` | Daily | ICE BofA HY Option-Adjusted Spread |
| `NFCI` | `NFCI` | Weekly (forward-filled to business day) | Chicago Fed National Financial Conditions Index |

- Fallback: `pandas_datareader.data.get_data_fred()` — no key needed, rate-limited
- Output: `data/macro_data.csv`

## Data Storage

**Local Files (primary persistence — no external database):**

| File | Purpose |
|------|---------|
| `data/market_data.csv` | Raw aligned OHLCV + VIX (SPY trading-day index) |
| `data/macro_data.csv` | FRED macro series (yield curve, HY OAS, NFCI) |
| `data/features_transformed.csv` | log1p + winsorized features pre-standardization |
| `data/features_scaled.csv` | Expanding-window z-scored features |
| `data/pca_components.csv` | PCA-projected feature matrix |
| `data/regime_results.csv` | **Primary output** — regime labels + probabilities per day |
| `data/garch_params.json` | Per-regime GARCH(1,1) parameters |
| `data/cache/` | Incremental fetch cache (per-ticker CSV + manifest) |
| `models/hdp_params.pkl` | Trained HDP-HMM SVI parameters |
| `models/hdp_samples.pkl` | Posterior samples |
| `models/pca_model.pkl` | Fitted rolling PCA |
| `models/regime_model.pkl` | Full assembled regime model |
| `figures/dashboard.html` | Interactive Plotly dashboard (not served, opened locally) |

**Incremental Cache (`data/cache/`):**
- Per-ticker CSV: `data/cache/{TICKER}_incremental.csv`
- Manifest: `data/cache/.cache_manifest.json` — SHA256 hashes + metadata for delta detection
- Logic in `src/features/collect.py`: full collect on first run; delta-only on subsequent runs
- Controlled by `INCREMENTAL_MODE = 'auto'` in `src/config.py`

**Databases:** None — no SQL, Redis, or cloud storage.

## Authentication & Identity

**Auth Provider:** None — no user authentication.

**Secrets:** One optional secret:
- `FRED_API_KEY` — stored in `.env` file at project root, loaded via `python-dotenv` in `scripts/run.py`
- If absent, macro collection falls back to unauthenticated `pandas_datareader` path (rate-limited)

## Downstream Consumers (Output Integrations)

This project produces outputs consumed by two downstream systems. The integration contract is documented in `docs/INTEGRATION.md`.

**Algo-Trading-Bot:**
- What it consumes: `data/regime_results.csv` → `src/signals/signals.py::compute_signals()`
- Key field: `signals['bot_label']` — one of `LOW_VOL`, `MED_VOL`, `HIGH_VOL`
- Label mapping source of truth: `src/config.py::LABEL_MAPPING`
- Integration validated by: `tests/test_bot_integration.py`

**Portfolio-Manager:**
- Consumes the same `regime_results.csv` / `compute_signals()` interface
- Uses regime probabilities (per-regime `confidence` scores) for position sizing

**Signal consumer pattern (both bots use this):**
```python
import pandas as pd
from src.signals.signals import compute_signals

results = pd.read_csv('data/regime_results.csv', index_col=0, parse_dates=True)
signals = compute_signals(results)

bot_label = signals['bot_label']           # 'LOW_VOL' | 'MED_VOL' | 'HIGH_VOL'
confidence = signals['awareness']['confidence']  # 0.0 – 1.0
garch_var  = signals['awareness'].get('garch_var_95')  # GARCH-conditional 95% VaR
```

**Full signal dict structure** (from `docs/INTEGRATION.md`):
```python
{
  'date': '2024-01-15',
  'current_regime': 'Med-Vol',   # internal human-readable name
  'bot_label': 'MED_VOL',        # canonical bot label — always use this
  'awareness': {
    'confidence': 0.78,
    'days_in_regime': 12,
    'median_duration': 45
  },
  'distributions': {
    'Low-Vol': {'ann_vol': 0.15, 'var_5': -0.012, 'max_dd': -0.08, ...},
    'Med-Vol': {'ann_vol': 0.25, ...},
    'High-Vol': {'ann_vol': 0.45, ...}
  },
  'vol_context': {'vix': 18.5, 'vrp': -2.3},
  'transitions': [{'regime': 'High-Vol', 'probability': 0.15, ...}],
  'validation': {
    'separation_significant': True,
    'vol_ordering_match': True,
    'var_backtest': {'Low-Vol': {'ok': True, ...}, ...}
  },
  'oos_validation': {'agreement_rate': 0.73},
  'calibration': {'ece': 0.032, 'interpretation': 'Good calibration'}
}
```

## Label Mapping (Cross-Project Interface Contract)

`src/config.py::LABEL_MAPPING` is the source of truth. Do not change without coordinating with algo-trading-bot and portfolio-manager.

| Internal Regime Name | bot_label | Notes |
|----------------------|-----------|-------|
| `Low-Vol` | `LOW_VOL` | VIX ~15.3 (K=3 model) |
| `Medium-Vol` / `Moderate` | `MED_VOL` | VIX ~17.4 |
| `High-Vol` / `Elevated` / `Crisis` | `HIGH_VOL` | VIX ~22.8+ |
| `Very-Low` | `LOW_VOL` | 6-state fallback |
| `Moderate-Vol` | `MED_VOL` | HDP vol-bracket naming |
| `Elevated-Vol` / `Crisis-Vol` | `HIGH_VOL` | HDP vol-bracket naming |

## Monitoring & Observability

**Error Tracking:** None (no Sentry, Datadog, etc.)

**Logs:**
- Python `logging` module; per-module loggers via `logging.getLogger(__name__)`
- Pipeline logs written to `logs/pipeline.log`, `logs/pipeline_run.log`, `logs/cron_run.log`
- No centralized log aggregation

**Trust Scorecard:**
- `src/signals/trust.py::compute_trust_scorecard()` — PASS/WARN/FAIL verdict on data freshness, regime separation, calibration, OOS agreement
- Accessible via: `python scripts/run.py trust`

**Data Freshness Check:**
- `src/config.py::MAX_DATA_STALENESS_DAYS = 3` — warns if `data/market_data.csv` is >3 trading days old

**Scheduled Execution:**
- `scripts/cron_run.sh` — cron script for automated pipeline runs; outputs to `logs/cron_run.log`

## CI/CD & Deployment

**Hosting:** Local scripts only — no cloud deployment, no web server.

**CI Pipeline:** GitHub Actions (`.github/workflows/tests.yml`)
- Trigger: `workflow_dispatch` (manual only — push/PR triggers are commented out)
- Python 3.10 on Ubuntu Latest
- Job 1 — `check-version-pins`: rejects any `>=` constraint on JAX or NumPyro
- Job 2 — `test`: runs full pytest suite (causality, bot integration, PCA caching, dashboard, all 160+ tests)

**GitHub Repository:** https://github.com/AdamMooo/Regime-Detection

## Webhooks & Callbacks

**Incoming:** None

**Outgoing:** None

## Adding New Signal Fields

To extend the signal schema consumed by downstream bots:

1. Implement calculation in `src/signals/signals.py`
2. Add field to return dict in `compute_signals()`
3. Update schema validation in `tests/test_bot_integration.py`
4. Update `docs/INTEGRATION.md`
5. Update `CLAUDE.md` under Bot Integration section
6. Run: `pytest tests/test_bot_integration.py -xvs`

---

*Integration audit: 2026-05-09*
