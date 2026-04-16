# Milestones

## v1.0 Production Ready (Shipped: 2026-04-16)

**Phases completed:** 4 phases, 14 plans, 61 tasks  
**Timeline:** 2026-03-12 → 2026-04-15 (34 days)  
**Lines of code:** ~13,300 Python

**Key accomplishments:**

1. Closed all 4 critical blockers: JAX/NumPyro exact pinning, bot label mapping, causality tests, end-to-end integration test
2. Implemented incremental data collection — delta-only fetching reduces update time from 20 min to <5 min
3. Diagnosed and fixed OOS regime fragmentation (rolling PCA drift up to 74.91°) with hybrid Procrustes alignment
4. Fixed feature selection bias — 6 held-out features improve regime accuracy +3.5%, dwell time stability +3.2×
5. Enforced K=4 regimes via walk-forward validation (BIC justified, 4.9% improvement over K=3)
6. Replaced static VaR with GARCH-conditional VaR — Christoffersen p=0.547 (vs 0.0039 for static)
7. Full production documentation: MODEL_CARD.md, REPRODUCIBILITY.md, KNOWN_ISSUES.md, TROUBLESHOOTING.md
8. Refactored train.py monolith (1452 lines) into 4 focused modules: hmm_training, inference, evaluation, orchestrator

**Test coverage:** 160+ tests passing

---
