# External Integrations

**Analysis Date:** 2026-04-18

## APIs & External Services

**Market Data:**
- Yahoo Finance via yfinance 1.2.0
  - OHLCV for: SPY, QQQ, IWM, EEM, TLT, HYG, GLD (`TICKERS` in `src/config.py`)
  - Volatility family: `^VIX`, `^VIX3M`, `^VVIX` (`VIX_TICKER`, `VIX3M_TICKER`, `VVIX_TICKER`)
  - Fetch method: `yf.download(ticker, start=START_DATE, end=END_DATE, auto_adjust=True, progress=False)`
  - No API key required (public data)
  - Date range: 2010-01-01 to present (`START_DATE = '2010-01-01'`, `END_DATE = None`)
  - No FRED or other macro data sources — pure Yahoo Finance

## Data Storage

**Local Files (primary persistence):**

| File | Purpose |
|------|---------|
| `data/market_data.csv` | Raw aligned OHLCV + VIX series (SPY trading-day index) |
| `data/features_transformed.csv` | log1p + winsorized features (pre-standardization) |
| `data/features_scaled.csv` | Standardized features after expanding-window z-score |
| `data/pca_components.csv` | PCA-projected feature matrix |
| `data/regime_results.csv` | Final regime labels + probabilities per trading day |
| `data/bic_selection.csv` | BIC scores from K-selection experiment |
| `data/feature_selection_report.txt` | Phase 2.5.2 feature selection analysis |
| `data/regime_count_selection_report.txt` | K regime count selection report |
| `models/hmm_model.pkl` | Serialized StudentTHMM model (joblib) |
| `models/pca_model.pkl` | Serialized PCA model (joblib) |
| `models/regime_model.pkl` | Serialized full regime model (joblib) |
| `figures/dashboard.html` | Interactive Plotly dashboard |
| `figures/feature_analysis.html` | Feature correlation / distribution report |

**Incremental Cache:**
- Directory: `data/cache/`
- Per-ticker CSVs: `data/cache/{TICKER}_incremental.csv`
- Feather-format index metadata: `data/cache/{TICKER}_index.feather` (actually JSON)
- Manifest: `data/cache/.cache_manifest.json` (SHA256 hashes for delta detection)
- Logic in `src/features/collect.py`: full collect on first run, delta-only on subsequent

**Databases:** None — no SQL, Redis, or external database.

**File Storage:** Local filesystem only.

**Caching:** File-based incremental cache with SHA256 manifest (`src/features/collect.py`).

## Authentication & Identity

**Auth Provider:** None — no user authentication.

**Secrets:** No secrets, API keys, or credentials required. All data is from public Yahoo Finance endpoints.

## Downstream Consumers (Output Integrations)

**Algo-Trading-Bot:**
- Consumes: `data/regime_results.csv` loaded via `pd.read_csv()` → `src/signals/signals.py::compute_signals()`
- Signal format: `signals['bot_label']` returns one of `LOW_VOL`, `MED_VOL`, `HIGH_VOL`
- Label mapping: `src/config.py::LABEL_MAPPING` (source of truth)
- Integration contract documented in `docs/INTEGRATION.md`
- Validated by `tests/test_bot_integration.py`
- Key consumed fields: `current_regime`, `bot_label`, `confidence`, `distributions`, `transitions`, `validation`

**Portfolio-Manager:**
- Consumes the same `regime_results.csv` / `compute_signals()` interface
- No separate integration file; uses the same Algo-Trading-Bot signal schema

**Signal API (no HTTP server — file-based):**
```python
# Downstream consumer pattern:
results = pd.read_csv('data/regime_results.csv', index_col=0, parse_dates=True)
signals = compute_signals(results)
regime = signals['bot_label']  # 'LOW_VOL' | 'MED_VOL' | 'HIGH_VOL'
```

## Monitoring & Observability

**Error Tracking:** None (no Sentry, Datadog, etc.)

**Logs:** Python `logging` module; loggers created per module with `logging.getLogger(__name__)`. No centralized log aggregation.

**Trust Scorecard:** `src/signals/trust.py::compute_trust_scorecard()` — produces PASS/WARN/FAIL verdict on data freshness, regime separation, calibration, OOS agreement. Accessible via `python scripts/run.py trust`.

**Data Staleness Check:** `src/config.py::MAX_DATA_STALENESS_DAYS = 3` — warns if `market_data.csv` is more than 3 trading days old.

## CI/CD & Deployment

**Hosting:** Local scripts only — no cloud deployment.

**CI Pipeline:** GitHub Actions — `.github/workflows/tests.yml`
- Triggers: push to `main`/`develop`, PR to `main`
- Python 3.10 on Ubuntu
- Jobs:
  1. `check-version-pins` — rejects any `>=` constraint on JAX/NumPyro
  2. `test` — runs full pytest suite
- CI enforces causality guarantees (no lookahead), bot integration schema, PCA caching, dashboard tests

## Webhooks & Callbacks

**Incoming:** None

**Outgoing:** None

## Environment Configuration

**Required:** No environment variables or secrets required.

**All configuration** is in `src/config.py` as Python constants. No `.env` file needed.

---

*Integration audit: 2026-04-18*
