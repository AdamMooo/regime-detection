# Regime-Detection — Session Resume

## Status
Phase: GSD Planning Complete → Ready for Phase 1 Execution
Last session: Session 3 (2026-04-12) — Full GSD initialization
Branch: main

## Last Session Work (Session 3)
- Completed full GSD reset with codebase analysis
- Created PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json
- Identified 4 critical production blockers (JAX pinning, bot mapping, incremental updates, integration test)
- Verified core HMM is sound — this is unblocking + optimization, not rewrite
- 48-hour execution plan: Phase 1 (blockers), Phase 2 (incremental), Phase 3 (backlog)

## Next Action
**Immediate:** Run `/gsd-plan-phase 1` to create detailed phase plan and execute Phase 1 blockers
**Timeline:** Phase 1 should be complete by 2026-04-16, Phase 2 by 2026-04-26
**Success:** All 4 blockers closed, tests passing, integration test green, ready for 2026-04-30 deployment

## Key Files
- collect.py: Data collection (market + macro features)
- features.py: 13 feature engineering pipeline + rolling PCA
- train.py: HDP-HMM model training (NumPyro)
- hdp_hmm.py: Core HMM implementation
- signals.py: Regime signal generation from trained model
- run.py: Orchestration script
- analyze.py: Post-hoc analysis tools
- dashboard.py: Streamlit visualization dashboard
- config.py: Model params, feature config, paths
- trust.py: Regime trust/confidence scoring

## Architecture Constraints
- NumPyro for HMM (not hmmlearn or pomegranate)
- 13 features → rolling PCA → HDP-HMM (3 regimes expected)
- Do not use K-means for regime detection — HDP-HMM is the approach
- Regime labels should align with Algo-Trading-Bot label convention when integrated

## Notes for Claude
This project feeds signals to Algo-Trading-Bot. Before adding new features, check
how the regime labels are consumed downstream. The HMM pipeline is already functional —
the next step is productionization + GSD planning, not rebuilding the model.
