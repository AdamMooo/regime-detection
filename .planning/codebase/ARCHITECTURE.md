# Architecture

**Analysis Date:** 2026-04-18

## Pattern Overview

**Overall:** Linear pipeline with modular layers — data collection → feature engineering → dimensionality reduction → probabilistic regime detection → signal generation

**Key Characteristics:**
- Strictly causal (no lookahead): every transformation at time t uses only data from [0..t]
- File-based integration: outputs CSV files consumed by downstream systems, no HTTP API
- Two HMM backends: classic Student-t HMM (active, `USE_HDP=False`) and Bayesian HDP-HMM via NumPyro (available, disabled)
- Thin orchestrator pattern: `scripts/run.py` delegates to pipeline modules; `scripts/pipelines/train.py` is the heavy orchestrator
- Configuration centralized: all hyperparameters in `src/config.py`; no scattered magic numbers

## Layers

**Data Collection Layer:**
- Purpose: Download and cache OHLCV + VIX data from Yahoo Finance
- Location: `src/features/collect.py`
- Contains: Full and incremental collection modes, SHA256 cache manifest, validation
- Depends on: yfinance, `src/config.py`
- Used by: `scripts/run.py`, `scripts/pipelines/train.py`
- Output: `data/market_data.csv`

**Feature Engineering Layer:**
- Purpose: Transform raw prices into 17 market features spanning 7 regime dimensions
- Location: `src/features/features.py`
- Contains: `build_features()`, `prepare_features()`, `_fix_skew()`, `_winsorize()`, `_validate_features()`
- Feature groups: volatility state (VIX, VRP), vol dynamics (rv_ratio, vix_ts_slope, volvol), cross-asset risk (SPY-TLT corr, credit stress), return dynamics (skew, autocorrelation), market structure (eigenvalue concentration, drawdown), liquidity (rel volume, vol-adj return), SV-specific (lagged realized vol), leverage effect
- Active subset (6 features selected Phase 2.5.2): VRP, VIX, SPY_skew20, SPY_TLT_corr63, lev_effect20, rv_ratio_10_63
- Depends on: `src/config.py`, pandas, numpy
- Used by: `scripts/pipelines/train.py`, `src/features/collect.py`
- Output: `data/features_transformed.csv`

**Core Inference Layer:**
- Purpose: Expanding-window standardization, HMM fitting, causal regime probability filtering
- Location: `src/core/inference.py`
- Contains: `expanding_standardize()`, `StudentTHMM`, `_fit_hmm()`, `filtered_probs()`, `filtered_labels()`
- Critical design: `filtered_probs()` uses forward-pass ONLY (not forward-backward), guaranteeing no future lookahead
- Depends on: hmmlearn, scipy, numpy, `src/config.py`
- Used by: `src/core/hmm_training.py`, `src/core/orchestrator.py`, `scripts/pipelines/train.py`

**HMM Training Layer:**
- Purpose: Rolling PCA, BIC state selection, regime naming, per-regime volatility models
- Location: `src/core/hmm_training.py`
- Contains: `fit_rolling_pca()`, `select_states_bic()`, `check_stability()`, `label_regimes()`, `fit_regime_sv()`, `fit_regime_garch()`, `LinearizedSV`
- PCA: Rolling 63-day window with Procrustes alignment for label stability across windows
- Regime naming: Sorted by ascending VIX mean → Low-Vol, Medium-Vol, High-Vol
- Depends on: `src/core/inference.py`, sklearn, arch, statsmodels, scipy, `src/config.py`
- Used by: `scripts/pipelines/train.py`

**Bayesian HDP-HMM Layer (available, inactive):**
- Purpose: Auto-discover regime count via truncated stick-breaking Dirichlet process prior
- Location: `src/core/hdp_hmm.py`
- Contains: `hdp_hmm_model()`, `fit_hdp_hmm()`, `forward_backward_numpy()`, `merge_similar_states()`, `label_regimes_hdp()`, `HDPModelAdapter`
- Inference: SVI (fast, `HDP_INFERENCE='svi'`) or NUTS (`HDP_INFERENCE='nuts'`)
- Gated by: `USE_HDP = False` in `src/config.py`
- Depends on: NumPyro, JAX, scipy, numpy
- Used by: `scripts/pipelines/train.py` (conditional on `USE_HDP`)

**Orchestration Layer:**
- Purpose: Walk-forward out-of-sample validation with expanding/rolling windows
- Location: `src/core/orchestrator.py`
- Contains: `walk_forward()` — fits HMM per fold, assigns vol-bracket names, returns OOS labels
- Fold logic: expanding-window standardize → rolling PCA → multi-seed HMM → vol-bracket naming
- Depends on: `src/core/inference.py`, sklearn, numpy, pandas, `src/config.py`
- Used by: `scripts/pipelines/train.py`

**Evaluation Layer:**
- Purpose: Regime diagnostics, VaR backtesting (Kupiec POF + Christoffersen), bootstrap CIs
- Location: `src/core/evaluation.py`
- Contains: `evaluate()`, `compute_var_backtest()` (deprecated), `compute_var_backtest_garch()` (production), `compare_var_methods()`, `kupiec_pof_test()`, `christoffersen_test()`
- GARCH-conditional VaR passes both Kupiec (p=0.952) and Christoffersen (p=0.547) tests
- Depends on: scipy, arch (GARCH), numpy, pandas, `src/config.py`
- Used by: `scripts/pipelines/train.py`

**Signal Generation Layer:**
- Purpose: Translate raw regime results into structured signals for downstream consumers
- Location: `src/signals/signals.py`
- Contains: `compute_signals()` — returns full awareness dict with regime, confidence, distributions, transitions, calibration, OOS validation
- Output includes `bot_label` (canonical: `LOW_VOL`/`MED_VOL`/`HIGH_VOL`) mapped via `LABEL_MAPPING`
- Depends on: `src/config.py`, pandas, numpy, scipy
- Used by: `scripts/run.py`, downstream trading systems via CSV + `compute_signals()`

**Trust Scoring Layer:**
- Purpose: Single PASS/WARN/FAIL verdict aggregating all validation checks
- Location: `src/signals/trust.py`
- Contains: `compute_trust_scorecard()`, `format_scorecard()`
- Checks: data freshness, regime separation, OOS agreement, calibration, VaR backtest
- Depends on: `src/config.py`, numpy, pandas
- Used by: `scripts/run.py` (`print_trust()`), `scripts/pipelines/train.py`

## Data Flow

**Full Pipeline (python scripts/run.py):**

1. `collect()` downloads Yahoo Finance OHLCV + VIX → `data/market_data.csv`
2. `prepare_features()` builds 17 features → applies log1p + expanding winsorization → `data/features_transformed.csv`
3. `analyze()` generates interactive feature diagnostics → `figures/feature_analysis.html`
4. `train()` executes:
   a. Load features, apply `expanding_standardize()` for causal z-scoring
   b. Select 6-feature FEATURE_SUBSET, apply `fit_rolling_pca()` (63-day Procrustes-aligned window)
   c. `select_states_bic()` — K=3 enforced (single-element `N_STATES_RANGE`)
   d. `check_stability()` — multi-seed agreement check across N_SEEDS=20
   e. `label_regimes()` — sorted VIX-mean naming → Low-Vol/Medium-Vol/High-Vol
   f. `filtered_labels()` — forward-pass only, hysteresis
   g. `evaluate()` — regime characteristics + bootstrap CIs
   h. `fit_regime_sv()` + `fit_regime_garch()` — per-regime volatility models
   i. `walk_forward()` — OOS validation (rolling 5yr train, 21-day steps)
   j. `compute_var_backtest_garch()` — GARCH-conditional VaR validation
   k. Save: `data/regime_results.csv`, `models/*.pkl`
5. `compute_signals()` reads CSV → structured signal dict → downstream consumers

**Inference (real-time / online):**

1. Load saved `models/regime_model.pkl`, `models/pca_model.pkl`
2. Apply `expanding_standardize()` on new data (uses running stats)
3. Transform via loaded PCA
4. `filtered_probs()` — forward pass only → regime probabilities
5. `filtered_labels()` — argmax + hysteresis → current regime label
6. `compute_signals()` → `bot_label` for downstream

## Key Abstractions

**StudentTHMM:**
- Purpose: Extends hmmlearn GaussianHMM with multivariate Student-t emissions (fat tails, df=4)
- Location: `src/core/inference.py`
- Pattern: Override `_compute_log_likelihood()` using `scipy.stats.multivariate_t.logpdf`

**HDPModelAdapter:**
- Purpose: Wraps Bayesian HDP-HMM results to expose the same interface as StudentTHMM
- Location: `src/core/hdp_hmm.py`
- Methods: `.predict()`, `.predict_proba()`, `.score()`, `._compute_log_likelihood()`

**LinearizedSV:**
- Purpose: Linearized stochastic volatility via Kalman filter (log(r²) observation, AR(1) state)
- Location: `src/core/hmm_training.py`
- Pattern: Extends `statsmodels.tsa.statespace.mlemodel.MLEModel`; parameters: μ (mean log-vol), φ (persistence), σ_η (vol-of-vol)

**Vol-Bracket Regime Naming:**
- Purpose: Name regimes by absolute realized vol rather than rank, enabling IS/OOS label comparability
- Location: `src/config.py::VOL_BRACKETS`, used in `src/core/hdp_hmm.py::label_regimes_hdp()` and `src/core/orchestrator.py::walk_forward()`
- Thresholds: 0-10% → Low-Vol, 10-18% → Moderate-Vol, 18-28% → Elevated-Vol, 28%+ → Crisis-Vol

## Entry Points

**Full Pipeline:**
- Location: `scripts/run.py::main()`
- Triggers: `python scripts/run.py [step]`
- Steps: `all`, `collect`, `features`, `analyze`, `train`, `regime`, `trust`, `dashboard`

**Training Only:**
- Location: `scripts/pipelines/train.py::train()`
- Triggers: `python scripts/run.py train`

**Live Regime Check:**
- Location: `scripts/run.py::print_regime()`
- Triggers: `python scripts/run.py regime`
- Reads `data/regime_results.csv`, no retraining

**Analysis Scripts (diagnostics):**
- Location: `scripts/analysis/` — 7 standalone scripts
- `analyze_regime_characterization.py` — Phase 4 comprehensive diagnostics
- `analyze_feature_importance.py`, `analyze_feature_selection.py`
- `analyze_oos_fragmentation.py`, `analyze_signal_quality.py`
- `select_k_via_crossval.py`, `signal_combination.py`

## Error Handling

**Strategy:** Assert-based contract validation with exception wrapping in `run.py`

**Patterns:**
- `assert len(market) >= 252` — minimum data requirements in `collect.py` and `features.py`
- `assert len(f) >= 252` — features pipeline minimum rows
- `assert pca is not None` — rolling PCA must produce at least one valid window
- `run.py` wraps each pipeline step in try/except, prints `[ERROR]` and exits on non-`all` steps
- GARCH/SV fitting wrapped in try/except (graceful skip if < MIN_REGIME_OBS=50 or numeric failure)
- Cache validation raises `ValueError` on schema mismatch or >10-day gaps; caller falls back to full collect

## Cross-Cutting Concerns

**Causality / No Lookahead:**
- All standardization: expanding windows (`src/core/inference.py::expanding_standardize()`)
- All winsorization: expanding quantiles (`src/features/features.py::_winsorize()`)
- HMM inference: forward-pass only (`src/core/inference.py::filtered_probs()`)
- Regime hold: hysteresis on forward labels only (`src/core/inference.py::filtered_labels()`)
- Verified by `tests/test_causality.py` (10 tests)

**Reproducibility:**
- `RANDOM_SEED = 42` passed to all PCA, HMM, multi-seed fitting
- Exact version pins in `requirements.txt`
- JAX `jax_enable_x64 = True` for numerical stability

**Validation:**
- `src/features/features.py::_validate_features()` — checks for infinities and near-zero variance
- `src/features/collect.py::_validate_cache()` — duplicate removal, forward-fill, gap detection
- `src/signals/signals.py` — validates signal schema before returning to consumers

**Logging:**
- `logging.getLogger(__name__)` per module
- hmmlearn and statsmodels loggers set to ERROR level during training to suppress noise

---

*Architecture analysis: 2026-04-18*
