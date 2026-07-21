# External Integrations

**Analysis Date:** 2026-07-21

## APIs & External Services

**Market Data:**
- Yahoo Finance (via `yfinance==1.2.0`) — no API key required
  - `^GSPC` (S&P 500 close) — `src/data/collect_macro.py:46` (`fetch_and_save_data`)
  - `^VIX` (CBOE Volatility Index close) — `src/data/collect_macro.py:53`
  - Also called live/ad-hoc from `scripts/run.py:74` (`get_current_regime_label`'s last-resort VIX-threshold fallback) — a 5-day pull of `^VIX` with no caching
  - No auth: public, unauthenticated Yahoo endpoint via `yfinance`

**Macro Data:**
- FRED (Federal Reserve Economic Data), via `fredapi>=0.5`
  - `T10Y2Y` — 10y minus 2y Treasury yield spread (`FRED_YIELD_SERIES` in `src/config.py:23`)
  - `NFCI` — Chicago Fed National Financial Conditions Index (`FRED_NFCI_SERIES` in `src/config.py:24`), shifted forward 7 days in code to correct for FRED's reference-week vs. publication-date lag (`src/data/collect_macro.py:69-73`)
  - Client: `fredapi.Fred`, instantiated in `src/data/collect_macro.py:_get_fred_api()`
  - Auth: `FRED_API_KEY` env var, loaded from `.env` via `python-dotenv`; raises `EnvironmentError` if unset or left as the placeholder `your_fred_api_key_here` (`src/data/collect_macro.py:28-35`)
  - Free tier, sign-up at fred.stlouisfed.org (per `CLAUDE.md` and `README.md`)

## Data Storage

**Databases:**
- None. No SQL/NoSQL database, no ORM, no connection strings anywhere in the codebase.

**File Storage:**
- Local filesystem only, all under the repo tree:
  - `data/processed/` — raw + standardized feature CSVs (`spx_data.csv`, `train.csv`, `test.csv`, `features.csv`, `features_train.csv`, `features_test.csv`); also contains `xeg_macros.csv`, an unexplained/orphaned file unrelated to the SPY/VIX/FRED feature set used by this project (candidate stray artifact, see CONCERNS.md)
  - `data/oos_regime_labels.csv`, `data/oos_regime_labels_rolling5y.csv`, `data/oos_regime_labels_rolling3y.csv` — walk-forward OOS outputs, per training-window config
  - `data/regime_results.csv` — CLI (`scripts/run.py`) cached in-sample results, enriched with `days_in_regime` / `regime_entropy`
  - `models/hdp_checkpoint.pkl`, `models/hdp_params.pkl`, `models/hdp_samples.pkl`, `models/hdp_metadata.json` — model checkpoints (`joblib`-serialized), written by `save_hdp_results()` in `src/core/hdp_hmm.py:620`
  - `results/` — paper-facing outputs: `paper_tables.tex`, `paper_macros.tex`, `paper_desc_stats.tex`, `regime_labels_train.csv`, `transition_matrix.csv`, `run_log.txt`
  - `figures/` — generated PNG/HTML/dashboard outputs (`figures/dashboard.html` and `figures/feature_analysis.html` are gitignored as regenerable; `figures/day1_hdp_diagnostics.png` is committed)
  - `paper/figures/*.pdf` — 4 publication PDFs (regime_timeline, vol_violin, transition_heatmap, backtest_equity), committed for the Overleaf upload
  - `logs/` — `cron_run.log`, `pipeline.log`, `pipeline_run.log` (plain text, no log rotation/structured logging service)

**Caching:**
- No dedicated cache layer (Redis, memcached, etc.). "Caching" in this project means checking for existing CSV/pkl artifacts on disk before recomputing (`scripts/run.py`'s `run_collect`/`run_features`/`run_train` all check `_cached_*()` paths first and skip recomputation if the file already exists).

## Authentication & Identity

**Auth Provider:**
- None. No user auth, no session management, no OAuth. The only "credential" in the system is the FRED API key described above, which authenticates this app to FRED's API — not end users to this app.

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Rollbar/etc.)

**Logs:**
- Python stdlib `logging` module, module-level logger `logging.getLogger('pipeline.stages')` in `src/pipeline/stages.py`
- Plain `print()` statements throughout `src/core/hdp_hmm.py`, `run_paper_experiments.py`, `scripts/run.py` for progress/diagnostics
- `run_paper_experiments.py` additionally tees all `log()` output to `results/run_log.txt` (`src` line ~28)
- Log files under `logs/` (`cron_run.log`, `pipeline.log`, `pipeline_run.log`) suggest a cron-scheduled run exists somewhere (not itself present in this repo — likely an external scheduler invoking `scripts/run.py` or `run_paper_experiments.py`)

## CI/CD & Deployment

**Hosting:**
- None. No deployment target; this is a CLI/research repo, not a hosted service.

**CI Pipeline:**
- GitHub Actions, `.github/workflows/tests.yml`
  - Trigger: `workflow_dispatch` only (manual) — the `push`/`pull_request` triggers are present but commented out, so CI does not run automatically
  - Jobs: `check-version-pins` (greps `requirements.txt` for `jax`/`numpyro` version operators, fails on `>=`), then `test` (Python 3.10 matrix; installs `requirements.txt`; runs several `pytest tests/test_*.py` invocations)
  - **Stale relative to current repo**: references test files (`test_causality.py`, `test_bot_integration.py`, `test_incremental_collection.py`, `test_pca_caching.py`, `test_dashboard_refactor.py`) and root analysis scripts (`analyze_feature_importance.py`, `analyze_regime_characterization.py`, `analyze_signal_quality.py`) that do not exist anywhere in the current repo tree — this workflow would fail immediately if triggered. See CONCERNS.md.

## Environment Configuration

**Required env vars:**
- `FRED_API_KEY` — required only for `stage_collect` / `fetch_and_save_data()`; all other pipeline stages and CLI commands work from cached artifacts without it

**Optional/internal:**
- `GSD_FORCE_STAGE_FAIL` — test-only hook read by every stage function in `src/pipeline/stages.py` (e.g. `GSD_FORCE_STAGE_FAIL=collect`) to force a stage to raise, for testing failure-handling paths

**Secrets location:**
- `.env` at repo root (gitignored via `.gitignore:5`), containing `FRED_API_KEY`. No other secret files detected. No cloud secret manager integration.

## Webhooks & Callbacks

**Incoming:**
- None. No HTTP server, no webhook receiver anywhere in the codebase.

**Outgoing:**
- None. No outbound webhook/callback calls. All "integration" with downstream consumers (Algo-Trading-Bot, Portfolio-Manager per `CLAUDE.md`) is via reading the CSV files this repo writes (`data/regime_results.csv`, `data/oos_regime_labels.csv`) — a file-based hand-off, not an API or message queue.

---

*Integration audit: 2026-07-21*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
