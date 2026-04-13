# PROJECT — Regime-Detection

## Vision
Probabilistic regime detection pipeline that feeds clean, validated regime signals to Algo-Trading-Bot and Portfolio-Manager. HDP-HMM discovers market regimes from macro + price features without hand-tuning. Model is causal, tested, and production-ready.

## Scope
- HDP-HMM regime classification (3 regimes: Low-Vol, Moderate-Vol, High-Vol)
- 13-feature engineering pipeline with rolling PCA dimensionality reduction
- Incremental data updates (collect only new data, not full 16-year history)
- Bot label mapping and validation
- Full integration test with Algo-Trading-Bot
- Dashboard for regime visualization and analysis
- **Strategic roadmap:** Foundation for multi-signal combination (Phase 3.4) using Fundamental Law of Active Management (IR = IC × √N)
- **Strategic roadmap:** Foundation for multi-signal combination (Phase 3.4) using Fundamental Law of Active Management (IR = IC × √N)

## Non-Goals
- Change underlying HMM algorithm (NumPyro is final choice)
- Rewrite data collection (collect.py is stable)
- Build trading execution logic (that's Algo-Trading-Bot's job)
- Add new regime count or naming (3 regimes, fixed labels)

## Team
- **Owner:** Adam Morris (mathematics/quant focus)
- **Consumers:** Algo-Trading-Bot, Portfolio-Manager
- **Integration deadline:** This month (2026-04-30)

## Constraints
**Hard constraints (non-negotiable):**
- NumPyro only for HMM (not hmmlearn, pomegranate)
- 13 features → rolling PCA → HDP-HMM pipeline (skip PCA = unstable)
- No K-means or hard clustering (only probabilistic regime assignment)
- 3 regime target with fixed labels: Regime 0 (Low-Vol), Regime 1 (Moderate-Vol), Regime 2 (High-Vol)

**Soft constraints:**
- Keep existing test suite (28 tests minimum)
- Minimize API changes to signals.py (downstream dependency)
- Dashboard must remain Streamlit-based

## Success Metrics
1. ✅ All 4 critical blockers closed (incremental update, bot mapping, JAX pinning, integration test)
2. ✅ Test coverage stable or improved (minimum 28 tests passing)
3. ✅ Regime signals validated against Algo-Trading-Bot convention (round-trip test)
4. ✅ No causal errors (lookhead in features, filtering, or standardization — verified by tests)
5. ✅ Pipeline runs in <5 min with incremental update, <20 min with full backtest
6. ✅ Dashboard renders without crashes
7. ✅ Code is organized, documented, and ready for production handoff

## Known Issues (from Codebase Analysis)
- train.py is 1452 lines (monolithic but functional — refactor is Phase 3 backlog, not Phase 1)
- JAX version constraint too loose (`jax>=0.4.30`)
- No incremental update mode (always re-downloads full history)
- Regime label mapping to bot convention not validated
- No integration test with downstream systems

## Timeline
- **Phase 1 (CRITICAL):** Fix blockers — 1–2 weeks
- **Phase 2:** Incremental update mode — 1–2 weeks
- **Phase 3 (BACKLOG):** Refactor + dashboard hardening — post-deadline

## References
- Codebase: https://github.com/AdamMooo/Regime-Detection
- Downstream: Algo-Trading-Bot (regime signals feed trading decisions)
- Training data: FRED (macro) + market prices (yfinance)
