# Technology Stack

**Analysis Date:** 2026-07-21

## Languages

**Primary:**
- Python 3.13 (`.venv/pyvenv.cfg` shows 3.13.13; README states "Python 3.11+" as the stated minimum, but the actual dev venv is 3.13) — all source in `src/`, `scripts/`, `tests/`, `run_paper_experiments.py`

**Secondary:**
- LaTeX — `paper/paper.tex`, `paper/references.bib` (paper writeup, compiled on Overleaf, not part of the runtime pipeline)

## Runtime

**Environment:**
- CPython 3.13, single local venv at `.venv/` (Windows-native; `python -m venv .venv` per README)
- JAX is force-pinned to CPU backend in code: `jax.config.update("jax_platform_name", "cpu")` (`src/core/hdp_hmm.py:47`) — no GPU path is used or supported
- `jax.config.update("jax_enable_x64", True)` (`src/core/hdp_hmm.py:49`) — 64-bit precision required for forward-algorithm numerical stability

**Package Manager:**
- pip, `requirements.txt` at repo root (flat pinned list, no Poetry/uv/pyproject)
- No lockfile beyond `requirements.txt` itself — all runtime deps are pinned to exact versions (`==`), not ranges, except 3 utility deps (`python-dotenv`, `fredapi`, `pandas_datareader`) pinned with `>=`
- CI (`.github/workflows/tests.yml`) has a dedicated `check-version-pins` job that fails the build if `jax` or `numpyro` use `>=` instead of `==` — this is a hard project constraint (see `CLAUDE.md`)

## Frameworks

**Core (numerical/ML):**
- NumPyro 0.20.0 — Bayesian HDP-HMM model definition, SVI and NUTS inference (`src/core/hdp_hmm.py`)
- JAX 0.9.1 / jaxlib 0.9.1 — autodiff/JIT backend for NumPyro; `jax.lax.scan` used for the vectorized forward algorithm
- hmmlearn 0.3.3 — parametric fixed-K Gaussian HMM baseline (`src/baselines/parametric_hmm.py`), reaches into hmmlearn's private `_hmmc.forward_log` C extension directly to get a forward-only (causal) filtered posterior instead of hmmlearn's public smoothed API
- scikit-learn 1.8.0 — `StandardScaler` (baseline preprocessing), `LinearRegression` (paper's information-content regression in `run_paper_experiments.py`)
- statsmodels 0.14.6 — listed as a dependency; not directly imported in any `src/` module found (candidate dead dependency, see CONCERNS)
- scipy 1.17.1 — `scipy.stats.norm` for Gaussian log-likelihoods in causal forward-backward decoding (`src/core/hdp_hmm.py`), `scipy.spatial.distance.pdist/squareform` for state-merging

**Testing:**
- pytest 9.0.2 — `tests/test_cli_runner.py`, `tests/test_causality_invariants.py`
- No pytest.ini / conftest.py / pyproject `[tool.pytest]` section found — pytest runs with defaults (`pytest tests/ -v`)

**Build/Dev:**
- No dedicated build tool — this is a script/pipeline project, not a packaged library. No `setup.py`, no `pyproject.toml`.
- VS Code workspace settings only (`.vscode/settings.json`): sets `python.defaultInterpreterPath` to `.venv`, disables auto-activation, defaults integrated terminal to bash

## Key Dependencies

**Critical (paper-reproducibility-pinned, see CLAUDE.md hard constraints):**
- `numpyro==0.20.0`, `jax==0.9.1`, `jaxlib==0.9.1` — the HDP-HMM model itself; any version drift can silently change regime assignments (per `requirements.txt` header comment)
- `yfinance==1.2.0` — SPY (`^GSPC`) and VIX (`^VIX`) price history, the two market-data features
- `fredapi>=0.5` — FRED macro series (`T10Y2Y` yield slope, `NFCI` financial-stress index)
- `hmmlearn==0.3.3` — parametric HMM baseline (the "null-hypothesis-adjacent" comparison model)

**Infrastructure:**
- `python-dotenv>=1.0` — loads `.env` for `FRED_API_KEY` (`src/data/collect_macro.py:16,25`)
- `joblib==1.5.3` — model checkpoint serialization (`models/hdp_checkpoint.pkl`, via `save_hdp_results` in `src/core/hdp_hmm.py`)
- `pandas==3.0.1` / `numpy==2.4.3` — all data handling across the codebase

**Likely dead (flagged in NOTES.md, not yet removed):**
- `arch==8.0.0` — no GARCH usage found in `src/`; CLAUDE.md explicitly forbids adding GARCH ("Do Not: Add rolling PCA, GARCH VaR...")
- `plotly==6.6.0` — no `import plotly` found in `src/`, `scripts/`, or root scripts; dashboard output (`figures/dashboard.html`) is generated with raw f-string HTML in `scripts/run.py`, not Plotly
- `pandas_datareader>=0.10` — no direct import found; FRED access goes through `fredapi` instead

## Configuration

**Environment:**
- `.env` file present at repo root (existence only — contents not read by this analysis; expected to contain `FRED_API_KEY`)
- Loaded via `python-dotenv`'s `load_dotenv()` at import time in `src/data/collect_macro.py`
- No other env vars referenced in `src/` beyond `FRED_API_KEY` and an internal test/debug hook `GSD_FORCE_STAGE_FAIL` (used by `src/pipeline/stages.py` to simulate stage failures in tests)

**Build:**
- `src/config.py` is the single source of truth for all tunable parameters: date ranges, tickers, FRED series IDs, feature list, HDP truncation/inference settings, MCMC settings, walk-forward window configuration, vol-bracket regime-labeling thresholds
- No separate `.env.example` / `.env.template` found

## Platform Requirements

**Development:**
- Windows 11 (observed dev environment; `.venv/Scripts/` layout is Windows-style)
- Python 3.13 locally; README states 3.11+ as the documented minimum (untested claim — CI matrix only tests 3.10, see below)
- FRED API key required only for the `collect` stage (`scripts/run.py collect` / `python run_paper_experiments.py`); all other CLI commands fall back to cached CSV artifacts already committed under `data/processed/` and `results/`

**Production:**
- No deployment target — this is a research/paper-generation repo plus a CLI (`scripts/run.py`) that other repos (Algo-Trading-Bot, Portfolio-Manager per `CLAUDE.md`) are expected to consume regime labels from (via CSV files, not an API/service)
- CI (`.github/workflows/tests.yml`) is `workflow_dispatch`-only (manual trigger) — not run automatically on push/PR (both are commented out in the workflow file); matrix targets Python 3.10 only, which does not match the local 3.13 dev environment
- **CI is currently broken relative to the actual repo**: the workflow references `tests/test_causality.py`, `tests/test_bot_integration.py`, `tests/test_incremental_collection.py`, `tests/test_pca_caching.py`, `tests/test_dashboard_refactor.py`, and root-level `analyze_feature_importance.py` / `analyze_regime_characterization.py` / `analyze_signal_quality.py` — none of these files exist in the current repo (only `tests/test_cli_runner.py` and `tests/test_causality_invariants.py` exist). This workflow reflects a pre-refactor state of the project (see CONCERNS.md).

---

*Stack analysis: 2026-07-21*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
