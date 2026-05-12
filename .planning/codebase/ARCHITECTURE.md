<!-- refreshed: 2026-05-11 -->
# Architecture

**Analysis Date:** 2026-05-11

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                     Thesis Experiment Layer                  │
│                     `src/experiments/thesis_experiments.py`   │
└────────┬──────────────────┬──────────────────┬───────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌────────────────────────────┐ ┌────────────────────────────┐ ┌──────────────────────────┐
│      Data Collection       │ │      Baseline Models       │ │   HDP-HMM Model Layer     │
│  `src/data/collect_macro.py`│ │ `src/baselines/*.py`       │ │ `src/core/hdp_hmm.py`     │
└────────┬────────────────────┘ └────────┬────────────────────┘ └────────┬──────────────────┘
         │                          │                         │
         ▼                          ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Shared Configuration & Utilities            │
│                   `src/config.py`                            │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              Output / Artifacts (CSV + Figures)             │
│              `data/processed/`, `figures/`                   │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Thesis experiment orchestration | Loads train data, runs baselines and HDP-HMM, computes simple metrics, saves diagnostics | `src/experiments/thesis_experiments.py` |
| SPX data fetch | Downloads SPX, VIX, WTI from Yahoo Finance, computes WTI shock, writes CSVs | `src/data/collect_macro.py` |
| Threshold baseline | Applies rule-based regime labels from VIX/WTI thresholds | `src/baselines/threshold_rules.py` |
| Parametric HMM baseline | Fits parametric HMM on features, returns labels and model results | `src/baselines/parametric_hmm.py` |
| Sticky HDP-HMM model | Defines NumPyro model, SVI optimization, and fit wrapper | `src/core/hdp_hmm.py` |
| Model utilities | Inference, label filtering, evaluation helpers | `src/core/inference.py`, `src/core/evaluation.py` |
| Shared config | Data, feature, threshold, HDP parameters | `src/config.py` |

## Pattern Overview

**Overall:**
- Simple CLI-first experiment pipeline
- Modular layers: data, baselines, core model, experiments
- Minimal state persisted as CSVs and PNGs

**Key Characteristics:**
- Data pipeline is file-based (`data/processed/*.csv`)
- Models are invoked from a single experiment script
- Configuration is centralized in `src/config.py`

## Layers

**Experiment Layer:**
- Purpose: orchestrate thesis experiment flow
- Location: `src/experiments/thesis_experiments.py`
- Contains: `load_train()`, `run_baselines()`, `run_hdp_hmm()`, `compute_metrics()`, `plot_diagnostics()`
- Depends on: `src/baselines`, `src/core`, `src/config`
- Used by: CLI execution (`python -m src.experiments.thesis_experiments`)

**Data Layer:**
- Purpose: fetch and prepare SPX/VIX/WTI data
- Location: `src/data/collect_macro.py`
- Contains: `fetch_spx_data()`, `save_train_test()`
- Depends on: `yfinance`, `pandas`, `src/config`
- Used by: manual data refresh or experiment setup

**Baseline Layer:**
- Purpose: implement deterministic and parametric regime rules
- Location: `src/baselines/threshold_rules.py`, `src/baselines/parametric_hmm.py`
- Contains: rule-based assignments and HMM fitting
- Depends on: `pandas`, `numpy`, `statsmodels`, `src/config`

**Core Model Layer:**
- Purpose: fit sticky HDP-HMM with NumPyro and evaluate regimes
- Location: `src/core/hdp_hmm.py`
- Contains: NumPyro model, SVI training, posterior sampling
- Depends on: `jax`, `numpyro`, `numpy`, `src/config`

**Configuration Layer:**
- Purpose: store thesis parameters and constants
- Location: `src/config.py`
- Contains: tickers, data dates, threshold cutoffs, HDP/SVI hyperparameters
- Depends on: none

## Data Flow

### Primary Experiment Path
1. `python -m src.experiments.thesis_experiments` → `day1_experiment()`
2. `load_train()` reads `data/processed/train.csv`
3. `run_baselines(df)` applies threshold rules and parametric HMM
4. `run_hdp_hmm(df)` fits sticky HDP-HMM on `FEATURES`
5. `compute_metrics(df)` computes simple stress metrics
6. `plot_diagnostics(svi_result)` writes `figures/day1_hdp_diagnostics.png`

## Key Abstractions

**Regime label:**
- Represented as integer labels in DataFrame columns: `threshold_regime`, `hdp_regime`

**HDP observation matrix:**
- `obs = df[FEATURES].values` passed into `fit_hdp_hmm()`

**Threshold rules:**
- Bull: `vol_index < THRESH_VOL_LOW and wti_shock > THRESH_WTI_POS`
- Bear: `vol_index > THRESH_VOL_HIGH or wti_shock < THRESH_WTI_NEG`
- Neutral: otherwise

## Entry Points

**Main experiment:**
- Location: `src/experiments/thesis_experiments.py`
- Triggers: `python -m src.experiments.thesis_experiments`
- Responsibilities: orchestrate all thesis analysis steps

**Data refresh:**
- Location: `src/data/collect_macro.py`
- Triggers: `python -m src.data.collect_macro`
- Responsibilities: download new SPX/VIX/WTI data and save CSVs

## Architectural Constraints

- **Threading:** single-threaded
- **Global state:** module-level constants in `src/config.py`
- **Circular imports:** None detected in current structure
- **External I/O:** only in data collection and experiment script

## Error Handling

**Strategy:**
- Minimal; scripts raise exceptions on failure
- Data fetch prints progress but does not include retries

**Patterns:**
- `pd.read_csv()` used with `parse_dates=True`
- `dropna()` used after merging tickers
- `np.select()` used for threshold rule labels

## Cross-Cutting Concerns

**Logging:**
- No logger; uses `print()` and `matplotlib` output

**Validation:**
- No schema validation for downloaded data

---

*Architecture analysis: 2026-05-11*

---
LINKS:AUTO
