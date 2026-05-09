<!-- refreshed: 2026-05-09 -->
# Architecture

**Analysis Date:** 2026-05-09

## System Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Entry Points                                  │
│   scripts/run.py (CLI)      scripts/cron_run.sh (cron)          │
└──────────────────────────────┬──────────────────────────────────┘
                               │ instantiates
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                src/pipeline/Pipeline                             │
│   runner.py (timing, logging, exit-code contract)               │
│   stages.py (STAGES registry — 8 daily + 1 validate-gated)      │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┬───────┘
   │collect   │features  │train_hmm │garch     │signals   │dashboard
   ▼          ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌──────────────────────────────────┐ ┌────────┐
│collect│ │features│ │         Core Layers               │ │signals │
│.py   │ │.py     │ │  hdp_hmm.py   (NumPyro BHM)      │ │.py     │
│      │ │        │ │  inference.py (forward filter)    │ │trust.py│
│macro │ │pca_    │ │  hmm_training.py (BIC, naming)   │ └────────┘
│.py   │ │utils.py│ │  evaluation.py (diagnostics)      │
└──────┘ └────────┘ │  orchestrator.py (walk-forward)  │
                    │  var_backtesting.py (GARCH VaR)   │
                    │  forward_returns.py (validation)  │
                    └──────────────┬───────────────────┘
                                   │ writes
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Disk Artifacts                                                  │
│  data/market_data.csv   data/macro_data.csv                     │
│  data/features_transformed.csv  data/pca_components.csv         │
│  data/regime_results.csv        data/garch_params.json          │
│  models/hdp_params.pkl  models/regime_model.pkl  models/pca_model.pkl │
│  figures/dashboard.html  data/oos_regime_labels.csv             │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Pipeline | Stage registry, timing, exit-code contract | `src/pipeline/runner.py`, `src/pipeline/stages.py` |
| collect | OHLCV + VIX family from yfinance; incremental cache | `src/features/collect.py` |
| collect_macro | FRED macro series (T10Y2Y, HY OAS, NFCI) | `src/data/collect_macro.py` |
| features | 21-feature engineering; 14 selected via FEATURE_SUBSET | `src/features/features.py` |
| pca_utils | Rolling PCA with Procrustes alignment; LinearizedSV | `src/core/pca_utils.py` |
| hdp_hmm | Bayesian HDP-HMM (NumPyro, SVI or NUTS inference) | `src/core/hdp_hmm.py` |
| inference | Forward-pass filter, hysteresis labels, StudentTHMM, expanding standardize | `src/core/inference.py` |
| hmm_training | BIC state selection, regime naming, per-regime SV/GARCH | `src/core/hmm_training.py` |
| evaluation | Regime diagnostics, bootstrap CI, OOS metrics | `src/core/evaluation.py` |
| var_backtesting | GARCH-conditional VaR (Kupiec + Christoffersen tests) | `src/core/var_backtesting.py` |
| forward_returns | Regime-conditional forward return analysis (validation only) | `src/core/forward_returns.py` |
| orchestrator | Walk-forward OOS validation (expanding/rolling windows) | `src/core/orchestrator.py` |
| signals | Regime awareness engine; bot_label mapping; GARCH VaR | `src/signals/signals.py` |
| trust | Trust scorecard (data freshness, separation, calibration) | `src/signals/trust.py` |
| train.py | Thin orchestrator delegating to core layers; dashboard builder | `scripts/pipelines/train.py` |
| config | All model params, feature config, file paths, label mapping | `src/config.py` |

## Pattern Overview

**Overall:** Disk-to-disk pipeline with stateless stages. Each stage reads from known paths and writes to known paths. A small `prev` dict passes ephemeral data between adjacent stages (only `train_hmm` → `garch` → `signals`).

**Key Characteristics:**
- All stages are causal: no lookahead into future data at any point
- Model artifacts (pkl files) checkpoint state between runs; the pipeline can resume from any stage
- HDP-HMM is the production model (NumPyro SVI); StudentTHMM (hmmlearn) is retained as a fallback backend in `inference.py`
- K=3 regimes locked: Low-Vol, Medium-Vol, High-Vol (mapped to LOW_VOL, MED_VOL, HIGH_VOL for downstream bots)
- `walk_forward` stage is gated by `--validate` flag (takes ~4h); never runs in daily cron

## Layers

**Data Collection Layer:**
- Purpose: Fetch and cache raw market + macro data
- Location: `src/features/collect.py`, `src/data/collect_macro.py`
- Contains: yfinance OHLCV download, incremental cache (CSV + Feather index), FRED API calls
- Depends on: `src/config.py` (TICKERS, dates, CACHE_PATH)
- Used by: `src/pipeline/stages.py` (stage_collect)

**Feature Engineering Layer:**
- Purpose: Compute 21 engineered features from raw data; select 14 via FEATURE_SUBSET
- Location: `src/features/features.py`
- Contains: Volatility estimators (Parkinson, Garman-Klass), rolling statistics, macro feature joins
- Depends on: `src/config.py` (FEATURE_SUBSET, windows)
- Used by: `scripts/pipelines/train.py` (via `build_features`)

**Dimensionality Reduction Layer:**
- Purpose: Rolling PCA (window=63 days) with Procrustes alignment to stabilize component directions across windows
- Location: `src/core/pca_utils.py`
- Contains: `fit_rolling_pca()`, `LinearizedSV` (Kalman-filter SV model)
- Depends on: scipy Procrustes, sklearn PCA
- Used by: `scripts/pipelines/train.py`, `src/core/orchestrator.py`
- Hard constraint: PCA must always precede HMM; skip is not allowed

**Model Layer (HDP-HMM):**
- Purpose: Bayesian nonparametric HMM with auto-K via stick-breaking prior
- Location: `src/core/hdp_hmm.py`
- Contains: NumPyro model definition, JAX forward algorithm (jax.lax.scan), SVI + NUTS inference paths
- Depends on: jax==pinned, numpyro==pinned (exact pins in requirements.txt for reproducibility)
- Used by: `scripts/pipelines/train.py`

**Inference Layer:**
- Purpose: Causal regime probability filtering and label assignment
- Location: `src/core/inference.py`
- Contains: `expanding_standardize()`, `filtered_probs()`, `filtered_labels()`, `StudentTHMM` (hmmlearn wrapper), `_fit_hmm()`
- Key guarantee: Forward-pass only (filtered, not smoothed). No future data ever touches regime probabilities at time t.
- Used by: `scripts/pipelines/train.py`, `src/core/orchestrator.py`, `src/core/hmm_training.py`

**Training Utilities Layer:**
- Purpose: Higher-level training helpers above raw inference
- Location: `src/core/hmm_training.py`
- Contains: `select_states_bic()`, `check_stability()`, `label_regimes()`, `fit_regime_sv()`, `fit_regime_garch()`
- Depends on: `src/core/inference.py`, `src/core/pca_utils.py`, arch library
- Used by: `scripts/pipelines/train.py`, `src/pipeline/stages.py` (stage_garch)

**Evaluation Layer:**
- Purpose: Regime diagnostics and validation metrics
- Location: `src/core/evaluation.py`, `src/core/var_backtesting.py`, `src/core/forward_returns.py`
- Contains: Regime stat tables, bootstrap CI, Kupiec POF test, Christoffersen independence test, GARCH VaR
- Note: VaR backtesting extracted to var_backtesting.py in Phase 6; forward returns in forward_returns.py
- Used by: `scripts/pipelines/train.py`

**Signal Layer:**
- Purpose: Translate regime state into actionable trading context
- Location: `src/signals/signals.py`, `src/signals/trust.py`
- Contains: `compute_signals()` (regime awareness dict), `compute_garch_var()`, `enrich_results()`, `compute_trust_scorecard()`, `format_scorecard()`
- Outputs: `current_regime` (human-readable), `bot_label` (canonical for Algo-Trading-Bot)
- Used by: `scripts/run.py` (regime/trust commands), `scripts/pipelines/train.py`

**Validation Layer:**
- Purpose: Walk-forward OOS validation
- Location: `src/core/orchestrator.py`
- Contains: `walk_forward()` with expanding or rolling window modes
- Depends on: `src/core/inference.py`, `src/core/pca_utils.py`
- Used by: `src/pipeline/stages.py` (stage_walk_forward, gated by --validate)

## Data Flow

### Daily Pipeline (Full Run)

1. **collect** (`src/features/collect.py`) — incremental download from yfinance; writes `data/market_data.csv`
2. **collect_macro** (`src/data/collect_macro.py`) — FRED series fetch; writes `data/macro_data.csv`
3. **features** (`src/features/features.py::prepare_features`) — 21 features computed, 14 selected, winsorized; writes `data/features_transformed.csv`
4. **pca** (embedded inside train_hmm) — rolling PCA (window=63d, Procrustes-aligned) on 14 features; writes `data/pca_components.csv`, `models/pca_model.pkl`
5. **hdp_hmm** (`src/core/hdp_hmm.py`) — SVI inference on PCA components; writes `models/hdp_params.pkl`, `models/hdp_samples.pkl`, `models/hdp_metadata.json`
6. **inference** (`src/core/inference.py::filtered_probs` + `filtered_labels`) — forward-pass filter produces regime probabilities and hysteresis labels
7. **label_regimes** (`src/core/hmm_training.py`) — maps learned states to Low-Vol/Medium-Vol/High-Vol by VIX level
8. **garch** (`src/core/hmm_training.py::fit_regime_garch`) — per-regime GARCH(1,1); writes `data/garch_params.json`
9. **signals** (`src/signals/signals.py::enrich_results`) — appends PIPE-03 schema columns; writes final `data/regime_results.csv`
10. **dashboard** (`scripts/pipelines/train.py::rebuild_dashboard`) — writes `figures/dashboard.html`

### Incremental Data Collection

1. Cache manifest checked (`data/cache/.cache_manifest.json`)
2. Delta rows fetched if cache exists; full download on cache miss
3. SHA256 hash written to manifest for integrity verification

### Regime Assignment Causality Chain

1. `expanding_standardize(X_raw)` — expanding z-score, row t uses only [0..t] (`src/core/inference.py:41`)
2. `fit_rolling_pca(X_scaled, window=63)` — PCA fitted on past window; new projection from past covariance only (`src/core/pca_utils.py:41`)
3. `filtered_probs(model, X)` — Kalman-like forward pass; never looks at future observations (`src/core/inference.py`)
4. `filtered_labels(model, X, hold_days=1)` — hysteresis: regime sticks for `REGIME_HOLD_DAYS` before switching (`src/core/inference.py`)

**State Management:**
- Large arrays (model parameters, regime results) are persisted to disk as pkl/CSV artifacts between stages
- The `prev` dict in `runner.py` passes `results_df` and `market_v` from `train_hmm` to downstream stages within a single run
- No global Python state; each stage is stateless against the module

## Key Abstractions

**STAGES registry:**
- Purpose: Ordered list of (name, fn) tuples defining pipeline execution order (LOCKED)
- Location: `src/pipeline/stages.py:261`
- Pattern: Each fn signature is `(config, prev=None) -> dict | None`

**FEATURE_SUBSET:**
- Purpose: 14 features selected from 21 via walk-forward CV (held-out 2010-2020)
- Location: `src/config.py:63`
- Pattern: Config-driven; changing this list changes PCA input and therefore all regime labels

**LABEL_MAPPING:**
- Purpose: Maps internal regime names to bot canonical labels (LOW_VOL, MED_VOL, HIGH_VOL)
- Location: `src/config.py:138`
- Pattern: Single source of truth for all downstream integrations (algo-trading-bot, portfolio-manager)

**VOL_BRACKETS:**
- Purpose: Absolute vol-based regime naming for HDP model (avoids rank-order confusion between runs)
- Location: `src/config.py:166`
- Pattern: `[(low, high, name), ...]` — each state named by its realized vol, not rank

## Entry Points

**Daily pipeline:**
- Location: `scripts/run.py`
- Triggers: `python scripts/run.py` (manual) or `scripts/cron_run.sh` (cron)
- Responsibilities: Argument parsing, thread env vars, instantiates `Pipeline`, delegates to `run_all()` or `run_stage()`

**Pipeline class:**
- Location: `src/pipeline/runner.py:52`
- Triggers: Instantiated by `scripts/run.py`
- Responsibilities: Stage sequencing, per-stage timing, RotatingFileHandler logging, `sys.exit(1)` on any stage failure

**Regime awareness (no retrain):**
- Location: `scripts/run.py::print_regime()`
- Triggers: `python scripts/run.py regime`
- Responsibilities: Reads saved `data/regime_results.csv`, calls `compute_signals()`, prints regime context + trust scorecard

## Architectural Constraints

- **Causality:** All transformations at time t use only data from [0..t]. Enforced by expanding windows, forward-pass filter, and Procrustes PCA. Verified by `tests/test_causality.py` (10 tests, CI-enforced).
- **K=3 locked:** `N_STATES = 3` in `src/config.py`. BIC range is `N_STATES_RANGE = [3]`. Changing K invalidates downstream bot label mapping.
- **PCA mandatory:** `fit_rolling_pca` must run before HMM input. Skipping PCA is not allowed (raw 14-feature space is too correlated for HMM).
- **VIX bypass:** `VIX_BYPASS=True` in config appends scaled VIX directly to PCA components, forcing HMM to cluster on implied vol level.
- **Version pins:** `jax` and `numpyro` are exact-version pinned (`==`) in `requirements.txt`. Loose pins silently corrupt regime labels. CI enforces exact pins via `check-version-pins` job in `.github/workflows/tests.yml`.
- **GARCH VaR only:** `compute_var_backtest()` is deprecated. Production VaR uses `compute_var_backtest_garch()` (`src/core/var_backtesting.py`). Static VaR fails Christoffersen test (p=0.0039).
- **Global state:** `jax.config` is set module-level in `src/core/hdp_hmm.py` (CPU backend, 64-bit precision). These are process-global.
- **Threading:** CPU-only JAX; OMP/MKL/BLAS thread counts set via env vars in `scripts/run.py:29-33` before JAX import.

## Anti-Patterns

### Skipping PCA before HMM

**What happens:** Passing raw `features_transformed.csv` directly to HMM training
**Why it's wrong:** 14 correlated features cause the vol cluster to dominate all PCA components. BIC selects wrong K and regimes fragment.
**Do this instead:** Always call `fit_rolling_pca()` (`src/core/pca_utils.py:41`) on standardized features before HMM fitting.

### Using smoothed (forward-backward) probabilities in production

**What happens:** Calling HMM's `predict_proba` or similar smoothed posterior
**Why it's wrong:** Smoothing uses future observations to update past regime assignments — lookahead bias that inflates backtest performance.
**Do this instead:** Use `filtered_probs(model, X)` from `src/core/inference.py` which performs a forward-only pass.

### Loosening JAX/NumPyro version pins

**What happens:** Changing `jax==X.Y.Z` to `jax>=X.Y.Z` in `requirements.txt`
**Why it's wrong:** Breaking changes in these libraries silently change regime label assignments across environments.
**Do this instead:** Keep exact pins. To upgrade, test against stored regime fixture labels and update pins atomically.

### Using static regime VaR for risk limits

**What happens:** Computing per-regime historical quantile and using it as VaR
**Why it's wrong:** Fails Christoffersen independence test (p=0.0039) — exceedances cluster during volatility spikes.
**Do this instead:** Use `compute_var_backtest_garch()` or `compute_garch_var()` from `src/core/var_backtesting.py` and `src/signals/signals.py`.

## Error Handling

**Strategy:** Stage-level exception catch with `logger.exception()` + `sys.exit(1)`. Pipeline never masks errors silently.

**Patterns:**
- Any unhandled exception in a stage terminates the pipeline with exit code 1 (`src/pipeline/runner.py:81-83`)
- Missing model artifacts are logged as warnings and the stage returns `None` (graceful skip for optional stages like `garch`)
- `GSD_FORCE_STAGE_FAIL` env var allows CI to inject failures for exit-code contract testing

## Cross-Cutting Concerns

**Logging:** `pipeline` logger with `RotatingFileHandler` to `logs/pipeline.log` (10 MB, 3 backups). Each stage logs `[START]`, `[DONE]`, timing. Child loggers use `__name__` (e.g., `src.core.inference`).

**Validation:** Schema validation in `src/signals/signals.py::validate_signal_schema()` ensures `bot_label` is always present and valid before output. Test coverage: `tests/test_bot_integration.py`.

**Reproducibility:** `RANDOM_SEED = 42` in `src/config.py`. JAX seed passed explicitly to all NumPyro inference calls. Regime label reproducibility verified by `tests/test_causality.py` and stored fixture `tests/_hdp_verdict.txt`.

**Bot Integration:** `bot_label` field in `data/regime_results.csv` uses `LABEL_MAPPING` from `src/config.py`. The mapping is the single source of truth; all downstream consumers (algo-trading-bot, portfolio-manager) read `bot_label`, never `regime_name` directly.

---

*Architecture analysis: 2026-05-09*
