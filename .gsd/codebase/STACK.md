# Technology Stack

**Analysis Date:** 2026-03-16 (updated)

## Languages

**Primary:**
- Python 3.10+ - All source code (type hints use `|` union syntax requiring 3.10+)

## Runtime

**Environment:**
- CPython (standard interpreter)
- `.venv/` virtual environment at project root

**Package Manager:**
- pip with `requirements.txt`
- Lockfile: Not present (requirements use semver ranges, not pinned)

## Frameworks

**Core ML / Statistics:**
- `hmmlearn` 0.3.x — Gaussian/Student-t HMM via EM (classic HMM path)
- `numpyro` 0.16.x — Probabilistic programming for Bayesian HDP-HMM
- `jax` / `jaxlib` 0.4.30+ — JAX backend for NumPyro (CPU-forced via `jax_platform_name="cpu"`)
- `arch` 7.0.x — GARCH(1,1) volatility models via `arch_model()`
- `statsmodels` 0.14.x — Kalman filter / State-Space for `LinearizedSV` (extends `MLEModel`); also ADF test and VIF in feature validation
- `scikit-learn` 1.8.x — `PCA` (rolling + diagnostic), `LinearRegression` (for VIF)

**Numerical:**
- `numpy` 2.0+ — Core array operations
- `scipy` 1.14+ — `orthogonal_procrustes`, `gaussian_kde`, statistical tests (`kruskal`, `jarque_bera`, `chi2`)
- `pandas` 2.2+ — All time-series data as `DataFrame`/`Series` with `DatetimeIndex`

**Data I/O:**
- `yfinance` 1.2+ — OHLCV market data downloads (SPY, QQQ, IWM, EEM, TLT, HYG, GLD, VIX family)
- `joblib` 1.4+ — Model serialization (`joblib.dump` / `joblib.load`)

**Visualization:**
- `plotly` 5.20+ / 6.x — All interactive charts; output is a single self-contained HTML file

**Unused but in requirements.txt:**
- `fredapi` 0.5+ — Listed in `requirements.txt` but not imported or used anywhere in source
- `matplotlib` 3.9+ — Listed in `requirements.txt`; referenced only in a comment in `train.py` line 1000 but not actually imported or used for any output

## Key Dependencies

**Critical:**
- `numpyro` + `jax` — Bayesian HDP-HMM inference (`USE_HDP=True` default). JAX is forced to CPU; 64-bit precision enabled.
- `hmmlearn` — Classic Student-t HMM fallback (`USE_HDP=False`)
- `arch` — Regime-dependent GARCH benchmark and probability-weighted VaR
- `statsmodels` — `LinearizedSV` (Kalman-filter log-volatility model via `MLEModel`)

**Infrastructure:**
- `joblib` — Persists `pca_model.pkl`, `hmm_model.pkl`, `hdp_params.pkl`, `hdp_samples.pkl`
- `scipy.linalg.orthogonal_procrustes` — Procrustes alignment of rolling PCA loadings

## Configuration

**Environment:**
- `.env` file at project root (gitignored)
- `config.py` is the single source of truth for all tunable parameters — dates, tickers, feature windows, PCA params, HMM params, GARCH params

**Build:**
- No build step required; plain Python scripts
- `run.py` is the entry point; individual modules can also be run standalone

## Platform Requirements

**Development:**
- Python 3.10+ (union type hints)
- ~4 GB RAM recommended for JAX SVI (3000 steps on CPU)
- Full pipeline (`python run.py`) takes ~5–15 minutes on CPU (JAX SVI dominates)

**Production:**
- No server; fully local batch execution
- Outputs: `data/*.csv`, `models/*.pkl`, `figures/dashboard.html`, `figures/feature_analysis.html`

---

*Stack analysis: 2026-03-16 (updated)*
