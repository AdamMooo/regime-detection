# Architecture

**Analysis Date:** 2026-03-16 (updated)

## Pattern Overview

**Overall:** Linear Pipeline — Sequential stages with flat-file handoffs between stages

**Key Characteristics:**
- Each stage reads CSV/PKL from `data/` or `models/`, writes outputs back there
- No shared in-memory state between pipeline stages (except when called from `run.py` directly)
- CPU-only execution; JAX forced to CPU backend
- No web server, API, or streaming — pure offline batch analytics

## Pipeline Stages

```
collect.py  →  data/market_data.csv
   │
features.py →  data/features_transformed.csv
   │
analyze.py  →  figures/feature_analysis.html   (optional diagnostics)
   │
train.py    →  data/regime_results.csv  +  data/features_scaled.csv
              + models/  +  figures/dashboard.html
   │
signals.py  →  (called by train.py & run.py; reads regime_results.csv)
run.py      →  orchestrates all stages; CLI entrypoint
```

## Layers

**Data Collection (`collect.py`):**
- Purpose: Download and align raw market data
- Location: `collect.py` (93 lines)
- Contains: `collect()` function; `yfinance` calls for OHLCV + VIX family
- Depends on: `config.py` (tickers, date range)
- Output: `data/market_data.csv` — single aligned DataFrame on SPY trading-day index
- Note: No FRED / macro series

**Feature Engineering (`features.py`):**
- Purpose: Build 17-feature panel from raw OHLCV + VIX data
- Location: `features.py` (435 lines)
- Key functions: `build_features()`, `prepare_features()`, `_fix_skew()`, `_winsorize()`, `_validate_features()`
- Feature groups: vol state (2), vol dynamics (3), cross-asset (2), return dynamics (3), market structure (2), liquidity (2), SV-specific (2), leverage (1)
- Log1p transform applied to right-skewed features (`_LOG_TRANSFORM_COLS`) before winsorization
- Causal expanding-window winsorization (no future leakage)
- Validation includes ADF stationarity, VIF multicollinearity, PCA loadings, Jarque-Bera normality
- Output: `data/features_transformed.csv` (log1p + winsorized, NOT standardized)
- Note: No `features_scaled.csv`, no `scaler.pkl` produced here — `train.py` handles its own causal standardization

**Feature Diagnostics (`analyze.py`):**
- Purpose: Interactive EDA — correlation heatmap, histograms, time-series explorer, stats table
- Location: `analyze.py` (235 lines)
- Key function: `analyze()`
- Reads: `data/features_transformed.csv`
- Output: `figures/feature_analysis.html` (self-contained Plotly HTML)

**Model Training (`train.py` — 2941 lines, the core module):**
- Purpose: Rolling PCA → HMM regime detection → SV + GARCH volatility models → validation → dashboard
- Location: `train.py`
- Sub-pipeline:
  1. `expanding_standardize()` — causal z-score (shared by train + walk-forward)
  2. Rolling PCA with Procrustes alignment → `pcs`, `mode_ratio`
  3. Bayesian HDP-HMM (via `hdp_hmm.py`) or Classic Student-t HMM → `labels`, `probs`
  4. Regime labeling by VIX rank → `name_map`
  5. Linearized SV (Kalman filter per regime) → `sv_results`
  6. GARCH(1,1) per regime → `garch_results`
  7. Walk-forward OOS validation (expanding-window standardization + filtered_labels)
  8. Evaluation + VaR back-testing (Kupiec POF, Christoffersen)
  9. Interactive Plotly dashboard → `figures/dashboard.html`
- Output: `data/regime_results.csv`, `data/features_scaled.csv`, `models/`, `figures/dashboard.html`

**Bayesian HMM (`hdp_hmm.py`):**
- Purpose: Nonparametric Bayesian HDP-HMM inference via NumPyro + JAX
- Location: `hdp_hmm.py` (729 lines)
- Inference: SVI (`AutoNormal` guide, Adam) default; NUTS available
- Key functions: `fit_hdp_hmm()`, `get_labels_and_probs()`, `merge_similar_states()`, `HDPModelAdapter`
- Output: `models/hdp_params.pkl`, `models/hdp_samples.pkl`, `models/hdp_metadata.json`

**Regime Awareness (`signals.py`):**
- Purpose: Translate regime labels into actionable context (NOT return predictions)
- Location: `signals.py` (367 lines)
- Key function: `compute_signals(results, model, name_map)` → dict
- Sub-computations: `_compute_regime_distributions()`, `_regime_awareness()`, `_transition_context()`, `_validation_metrics()`, `_vol_context()`
- Called by both `train.py` (for dashboard) and `run.py` (`python run.py regime`)

**Orchestration (`run.py`):**
- Purpose: CLI entry point; chains all stages
- Location: `run.py` (157 lines)
- Steps: `collect` → `features` → `analyze` → `train`; also `regime`, `dashboard` sub-commands
- Unknown commands produce an error message with valid step list

## Data Flow

**Full Pipeline (`python run.py`):**

1. `collect()` downloads OHLCV + VIX family → `market_data.csv`
2. `prepare_features(market)` engineers 17 features → `features_transformed.csv`
3. `analyze()` reads features → `feature_analysis.html`
4. `train()` reads `market_data.csv` + `features_transformed.csv`:
   - Applies `FEATURE_SUBSET` (13 of 17 features) to reduce collinearity
   - Expanding-window causal standardization via `expanding_standardize()`
   - Rolling PCA (63-day window, Procrustes-aligned) → PC scores
   - HDP-HMM (or classic HMM) on PC scores → integer labels + filtered probabilities
   - Labels regime integers 0..K by ascending VIX level → human names (Low-Vol, Moderate, etc.)
   - Fits `LinearizedSV` per regime on SPY log²-returns (Kalman filter)
   - Fits GARCH(1,1) per regime as benchmark
   - Walk-forward OOS with `WALK_FORWARD_TRAIN_YEARS=5` years train, `21`-day steps
   - Computes VaR backtests (Kupiec + Christoffersen)
   - Builds 7-tab Plotly dashboard
   - Saves `regime_results.csv`, `features_scaled.csv`, model artifacts

**Regime-Only Query (`python run.py regime`):**

1. Reads existing `data/regime_results.csv`
2. Calls `compute_signals(results)` → prints colored ASCII summary to terminal

**State Management:**
- No in-memory global state; all intermediate state written to and read from disk files
- `config.py` provides global constants (no mutation at runtime)

## Key Abstractions

**`StudentTHMM` (class, `train.py` line 94):**
- Purpose: HMM with multivariate Student-t emissions (heavier tails than Gaussian)
- Pattern: Extends `hmmlearn.hmm.GaussianHMM`, overrides `_compute_log_likelihood`

**`LinearizedSV` (class, `train.py` line 380):**
- Purpose: AR(1) log-volatility model via Kalman filter
- Pattern: Extends `statsmodels.tsa.statespace.mlemodel.MLEModel`
- Observation: $z_t = \log(r_t^2) = c + h_t + \xi_t$
- State: $h_t = \mu(1-\phi) + \phi h_{t-1} + \sigma_\eta \eta_t$
- Parameters: `mu` (long-run log-vol), `phi` (persistence), `sigma_eta` (vol-of-vol)

**`HDPModelAdapter` (class, `hdp_hmm.py` line 689):**
- Purpose: Wraps HDP posterior parameters to mimic `hmmlearn` model interface
- Pattern: Provides `.transmat_`, `.n_components` to be compatible with dashboard code expecting classic HMM

**`expanding_standardize` (function, `train.py` line 62):**
- Purpose: Causal expanding-window z-score shared by `train()` and `walk_forward()`
- Row t is z-scored using mean/std from rows [0..t] only — no future leakage
- First `min_warmup` rows set to NaN (unstable statistics)

**`filtered_probs` / `filtered_labels` (functions, `train.py` lines 115, 150):**
- Purpose: Forward-only (causal) regime probabilities — no future lookahead
- Critical design choice: uses forward algorithm only, NOT forward-backward (smoother), to prevent data leakage in real-time application
- `filtered_labels` adds hysteresis: `REGIME_HOLD_DAYS=2` to prevent 1-2 day noise flips

## Entry Points

**`run.py`:**
- Location: `run.py`
- Triggers: `python run.py [collect|features|analyze|train|regime|dashboard]`
- Responsibilities: Orchestrates pipeline steps, handles per-step errors, validates commands

**`train.py::train()`:**
- Location: `train.py` line 2541
- Responsibilities: Full model training pipeline; saves all artifacts

**`train.py::rebuild_dashboard()`:**
- Location: `train.py` line 2844
- Responsibilities: Regenerates dashboard from saved model files without retraining
- Reads: `data/features_scaled.csv` saved by `train()`

## Error Handling

**Strategy:** Fail-fast with `assert` for data quality; `try/except` around individual model fits to allow partial results

**Patterns:**
- `assert len(data) >= 252` — data sufficiency checks in `collect.py`, `features.py`, `train.py`
- `try/except Exception` around `LinearizedSV.fit()` and `arch_model.fit()` — logs failure, continues with `None` result
- `run.py` catches pipeline-stage errors, prints `[ERROR]`, exits if running a single step
- `run.py` validates unknown commands against a `known` set and exits with usage hint

## Cross-Cutting Concerns

**Reproducibility:** `RANDOM_SEED = 42` in `config.py`; passed to all `PCA(random_state=...)`, `numpy.random.seed()`, `hmmlearn` constructors

**Feature Leakage Prevention:**
- `_winsorize()` uses expanding-window percentiles (causal — no future leakage)
- `expanding_standardize()` uses cumulative mean/std (causal — no future leakage)
- `filtered_probs()` uses forward algorithm only (not smoother)
- Walk-forward uses `expanding_standardize()` matching `train()` exactly
- Walk-forward uses `filtered_labels()` matching `train()` exactly

**Validation:** `signals.py::_validation_metrics()` runs Kruskal-Wallis separation test, vol ordering check, VaR Kupiec POF test, persistence check — printed to terminal and shown in dashboard

---

*Architecture analysis: 2026-03-16 (updated)*
