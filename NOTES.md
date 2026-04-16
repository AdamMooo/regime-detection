# Regime-Detection — Session Resume

## Status
Phase: v1.0 in progress (Phase 2.5 complete)
Last session: 2026-04-15
Branch: main

## Last Session Work
- Phase 2.5 complete: codebase reorganized into src/ and scripts/ packages
- Streamlit dashboard removed
- K=3 reverted and dashboard cleaned
- Model card validation tests fixed (encoding handling)

## Next Action
Run /gsd-progress inside Regime-Detection/ to see current state and plan next phase.
Goal: complete HDP-HMM regime detection pipeline toward production-ready system.

## Key Files
- src/: Main pipeline source (collect, features, train, evaluate)
- scripts/: CLI entry points
- models/: Saved model artifacts
- data/: Raw and processed market data
- reports/: Regime analysis outputs
- app.py: Dashboard entry point

## Architecture Constraints
- HDP-HMM via NumPyro (variational inference + NUTS)
- 13 curated market features from Yahoo Finance + FRED
- Rolling PCA with Procrustes alignment for label consistency
- Student-t emissions for fat-tailed returns
- K=3 regimes (expansion, neutral, contraction)
- Downstream consumers: Algo-Trading-Bot, Portfolio-Manager

## Notes for Claude
MacroRegimeDetector interface shared with Algo-Trading-Bot and Portfolio-Manager.
Do not change the public API (detect(), fit(), regime labels) without coordinating across projects.
