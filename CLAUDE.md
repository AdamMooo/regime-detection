# Claude Context — Regime-Detection

**Read NOTES.md first** — it has the current state and next action.

## Purpose
HDP-HMM market regime detection from macro and price features. Produces regime labels
(3 regimes expected) consumed downstream by Algo-Trading-Bot and Portfolio-Manager.

## Architecture (Post-Phase 3.1 Refactoring)

### Data & Feature Pipeline
- **collect.py** — Data collection (market prices + macro indicators)
- **features.py** — 13-feature engineering pipeline + rolling PCA
- **config.py** — Model params, feature config, file paths

### Core HMM & Regime Detection (Modularized)
- **hdp_hmm.py** — Bayesian HDP-HMM (NumPyro)
- **inference.py** — Core regime inference (probability filtering, label assignment)
  - `expanding_standardize()` — Expanding-window z-score (no lookahead)
  - `StudentTHMM` — Student-t HMM backend
  - `_fit_hmm()` — Model fitting wrapper
  - `filtered_probs()` — Forward-pass regime probabilities
  - `filtered_labels()` — Regime labeling with hysteresis (no lookahead)
- **hmm_training.py** — HMM training & feature engineering
  - `fit_rolling_pca()` — Procrustes-aligned rolling PCA
  - `select_states_bic()` — Model selection via BIC
  - `check_stability()` — Regime label stability (multi-seed)
  - `label_regimes()` — Map learned regimes to (Low-Vol, Med-Vol, High-Vol)
  - `fit_regime_sv()` / `fit_regime_garch()` — Per-regime volatility models
- **evaluation.py** — Diagnostics & validation
  - `evaluate()` — Comprehensive regime statistics
  - `compute_var_backtest()` — VaR validation (Kupiec POF, Christoffersen independence)
  - `compute_var_backtest_garch()` — GARCH-based VaR
- **orchestrator.py** — Workflow coordination
  - `walk_forward()` — Rolling-window out-of-sample validation

### Output & Integration
- **signals.py** — Regime signal generation from trained model
- **train.py** — Training orchestrator (delegates to inference/hmm_training/evaluation/orchestrator)
- **run.py** — Top-level pipeline: collect → features → train → signals
- **dashboard.py** — Streamlit visualization dashboard
- **trust.py** — Regime trust/confidence scoring
- **analyze.py** — Post-hoc analysis and regime characterization

### Testing
- **tests/** — 128 test suite
  - test_causality.py — Causal guarantees (no lookahead)
  - test_bot_integration.py — Algo-Trading-Bot signal schema
  - test_train_refactor.py — Refactoring regression tests
  - (+ 8 other test files covering validation, calibration, caching)

## Current State
- No formal GSD plan yet
- Core pipeline functional (collect → PCA → HMM → signals)
- Next: run /gsd-new-project to create a formal roadmap
- GitHub: https://github.com/AdamMooo/Regime-Detection

## Hard Constraints
- Use NumPyro for HMM — not hmmlearn, pomegranate, or other libraries
- 6 features (selected on held-out train set 2010–2020) → rolling PCA reduction → HDP-HMM (do not skip PCA)
  - Features: VRP, SPY_skew20, VIX, SPY_TLT_corr63, lev_effect20, rv_ratio_10_63
  - Improvement over original 7: 72.7% → 76.2% regime accuracy, 5.6 → 17.7 day dwell time
  - Decision made in Phase 2.5.2; see `analyze_feature_selection.py` and `data/feature_selection_report.txt`
- 3 regime target: match labels to Algo-Trading-Bot convention when integrating
- Do not use K-means — probabilistic regime detection only

### Reproducibility Guarantees
JAX and NumPyro versions are pinned exactly (==, not >=) to guarantee regime label reproducibility across all environments. Breaking changes in these libraries silently corrupt regime assignments; loose constraints are unacceptable for production trading.
- JAX and NumPyro versions are specified in requirements.txt with exact version numbers (e.g., `jax==0.9.1`, not `jax>=0.4.30`)
- CI/CD validation step rejects any PR loosening these constraints
- Reference: `requirements.txt`, `.github/workflows/tests.yml` (check-version-pins job)

## Bot Integration: Label Mapping
Regime labels are mapped to Algo-Trading-Bot canonical format:
- Regime 0 (Low-Vol) → LOW_VOL
- Regime 1 (Medium-Vol) → MED_VOL
- Regime 2 (High-Vol) → HIGH_VOL

All signals output both:
- `current_regime`: Internal regime name (e.g., "Low-Vol") — human-readable, economic meaning
- `bot_label`: Canonical label for Algo-Trading-Bot (e.g., "LOW_VOL") — always use this when communicating with the bot

The mapping is defined in `config.py` as `LABEL_MAPPING` (source of truth for all downstream integrations).
Signals are validated via `signals.py::compute_signals()` to ensure bot_label is always present and valid.

## Causality Guarantees (No Lookahead)
Regime assignments are causal: they use only past/present data, never future data. This is verified by automated tests in `tests/test_causality.py` and is essential for live trading.

The pipeline guarantees:
1. **Features:** All features computed using expanding windows (past data only). No fill-forward, no smoothing. Reference: `test_causality.py::TestExpandingStandardize` (3 tests)
2. **Standardization:** Expanding-window z-score uses only past data (mean/std computed on past only). Reference: `test_causality.py::TestExpandingStandardize::test_uses_only_past_data`
3. **Winsorization:** Expanding-window clipping uses only past quantiles (future outliers don't affect past values). Reference: `test_causality.py::TestWinsorize` (2 tests)
4. **PCA:** Fitted incrementally on past data; new components computed using only historical covariance. Verified by test suite.
5. **HMM Inference:** In production, regime probabilities use filtering (Kalman-like forward pass), not smoothing (forward-backward). No retrospective regime relabeling. Reference: `test_causality.py::TestFilteredProbs` (3 tests)
6. **Label Hysteresis:** Regime labels stick for minimum hold period (hold_days) to suppress noise. Reference: `test_causality.py::TestFilteredLabels` (2 tests)

All causality guarantees are automated in `tests/test_causality.py` (10 tests total, 100% coverage). CI/CD fails if any guarantee is violated. Live trading and backtesting are on equal footing.

Last verified: 2026-04-13 against `tests/test_causality.py` (10 tests, all PASSED).

## Module Responsibilities (Phase 3.1 Refactoring)

**inference.py** — Foundation layer
- Regime probability filtering (forward-pass only, no lookahead)
- Regime label assignment with hysteresis (minimum hold period)
- HMM training via StudentTHMM
- Expanding-window standardization (causal, no future data)

**hmm_training.py** — Training & feature engineering
- Rolling PCA with Procrustes alignment (regime stability)
- BIC-based model selection (number of regimes)
- Regime naming (learned regimes → Low-Vol, Med-Vol, High-Vol)
- Per-regime volatility models (SV and GARCH)

**evaluation.py** — Diagnostics & backtesting
- Regime separation tests (VaR, POF, independence)
- Bootstrap confidence intervals for regime statistics
- Out-of-sample validation metrics

**orchestrator.py** — Workflow coordination
- Walk-forward validation (rolling training/test windows)
- Integration of training, prediction, and evaluation loops

**train.py** — Thin orchestrator
- Orchestrates pipeline: hmm_training → inference → evaluation
- Maintains backward compatibility with run.py (train(), rebuild_dashboard())
- Dashboard building (Plotly-based interactive visualizations)

## Do Not
- Use K-means or hard clustering for regime assignment
- Skip PCA before HMM (dimensionality too high otherwise)
- Change the collect.py schema without checking features.py compatibility
- Build production execution logic here (that's Algo-Trading-Bot's job)

## Session Close Checklist
- Update NOTES.md with progress + next action
- Commit and push to GitHub
