# Claude Context — Regime-Detection

## Project Purpose
HDP-HMM Bayesian regime classification pipeline. Produces 3-regime labels (Low-Vol, Moderate, High-Vol) consumed by Algo-Trading-Bot and Portfolio-Manager.

## Current Status
Milestone: v1.1 — Model Quality & Regime Reliability
Phase: 4 complete (Empirical Diagnostics). Phase 5 next: Feature Engineering Overhaul (sectioned funnel architecture).

## Architecture Constraints
- HDP-HMM via NumPyro (variational inference + NUTS)
- Sectioned funnel feature architecture (Phase 5): Macro / Market Structure / Financial Conditions / Volatility sections → section signals → PCA → HMM
- Rolling PCA with Procrustes alignment for label consistency
- Student-t emissions for fat-tailed returns
- K=3 regimes — confirmed academically correct (K=4 BIC gain was statistical artefact; empirically regimes 0&1 overlapped)
- Downstream consumers: Algo-Trading-Bot, Portfolio-Manager — BOTH must be updated when regime label schema changes from 4→3
- Do NOT change public API (`detect()`, `fit()`, regime labels) without coordinating with both consumers

## Key Files
- `src/` — main pipeline (collect, features, train, evaluate)
- `src/config.py` — N_STATES=3, FEATURE_SUBSET, walk-forward config
- `scripts/` — CLI entry points
- `scripts/analysis/` — diagnostic and analysis scripts (Phase 4+)
- `src/core/evaluation.py` — forward return analysis + VaR backtesting
- `tests/test_regime_economic_validity.py` — economic validity tests

## Session Startup
1. Read NOTES.md for last session state and next action
2. Read `.planning/` STATE or ROADMAP for phase context
