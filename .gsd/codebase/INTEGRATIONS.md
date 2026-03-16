# External Integrations

**Analysis Date:** 2026-03-16 (updated)

## APIs & External Services

**Market Data:**
- Yahoo Finance — OHLCV price data for 7 equity/bond tickers + VIX family
  - SDK/Client: `yfinance` (`yf.download()`)
  - Auth: None (public API)
  - Tickers: `SPY`, `QQQ`, `IWM`, `EEM`, `TLT`, `HYG`, `GLD`, `^VIX`, `^VIX3M`, `^VVIX`
  - Config: `TICKERS`, `VIX_TICKER`, `VIX3M_TICKER`, `VVIX_TICKER` in `config.py`

**Macroeconomic Data:**
- None currently used. `fredapi` is listed in `requirements.txt` but is not imported or called anywhere.
- `train.py` has vestigial references to `hy_spread` and `yield_slope` columns (gracefully handled with `if col in market` guards) but these columns do not exist in `market_data.csv`.

## Data Storage

**Databases:**
- None — all persistence is flat CSV and pickle files

**File Storage (local):**
- `data/market_data.csv` — raw aligned OHLCV + VIX family (output of `collect.py`)
- `data/features_transformed.csv` — 17 engineered features, log1p + causal winsorization applied (output of `features.py`)
- `data/features_scaled.csv` — expanding-window standardized features (output of `train.py`, used by `rebuild_dashboard()`)
- `data/regime_results.csv` — final time-series with regime labels + probabilities + OOS labels
- `data/bic_selection.csv` — BIC scores per K (produced when `USE_HDP=False`)
- `models/pca_model.pkl` — last-window PCA object (loadings, variance ratios)
- `models/hmm_model.pkl` — fitted model object (classic HMM or `HDPModelAdapter`)
- `models/hdp_params.pkl` — posterior mean parameters dict (HDP path)
- `models/hdp_samples.pkl` — `SVI_NUM_SAMPLES` posterior samples (HDP path)
- `models/hdp_metadata.json` — human-readable HDP metadata (K, states, inference type)

**Caching:**
- None — every pipeline run re-downloads unless `collect()` is skipped

## Authentication & Identity

**Auth Provider:**
- None required. Yahoo Finance is a public API.
- `.env` file exists but its contents are not required by the current pipeline code.

## Monitoring & Observability

**Error Tracking:**
- None — errors surface as Python exceptions with `print(f"[ERROR] ...")`

**Logs:**
- `print()` statements throughout pipeline; no structured logging framework
- `hmmlearn` and `statsmodels` loggers suppressed to `ERROR` level in `train.py`
- JAX/NumPyro FutureWarning/DeprecationWarning suppressed globally

## CI/CD & Deployment

**Hosting:**
- Local workstation only — no cloud deployment

**CI Pipeline:**
- None

## Environment Configuration

**Required env vars:**
- None strictly required by current code

**Secrets location:**
- `.env` file at project root (gitignored)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-03-16 (updated)*
