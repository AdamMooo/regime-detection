# PROJECT — Regime-Detection

## What This Is

Production-ready HDP-HMM regime detection pipeline. Classifies market conditions into 4 probabilistic regimes from 13 macro + price features. Feeds validated signals to Algo-Trading-Bot and Portfolio-Manager. v1.0 shipped — now entering validation phase before live trading.

## Core Value

Causal, reproducible regime signals that downstream systems can trust. No lookahead, no K-means instability, statistically validated.

## Current State (v1.0 shipped 2026-04-16)

- **Architecture:** NumPyro HDP-HMM, 13 features → rolling PCA → 4 regimes
- **Codebase:** ~13,300 LOC Python, 160+ tests passing
- **VaR:** GARCH-conditional (Christoffersen p=0.547, passes)
- **Reproducibility:** JAX/NumPyro pinned exactly, seeds logged, CI enforced
- **Integration:** Bot label mapping live, end-to-end test passing
- **Known concern:** Model not yet trusted for live trading — v1.1 is full validation

## Requirements

### Validated (v1.0)

- ✓ HDP-HMM produces K=4 regime classes from 13 features — v1.0
- ✓ Rolling PCA with Procrustes alignment for label consistency — v1.0
- ✓ Regime assignments are probabilistic (not hard-clustered) — v1.0
- ✓ Incremental update mode (<5 min on new data) — v1.0
- ✓ Bot label mapping validated in integration test — v1.0
- ✓ No lookahead in features, standardization, or PCA — v1.0 (10 causality tests)
- ✓ JAX/NumPyro versions pinned exactly — v1.0
- ✓ Integration test with Algo-Trading-Bot passing — v1.0
- ✓ 160+ tests passing — v1.0
- ✓ train.py refactored into focused modules — v1.0
- ✓ GARCH-conditional VaR replaces static VaR — v1.0
- ✓ MODEL_CARD.md, REPRODUCIBILITY.md, KNOWN_ISSUES.md — v1.0

### Active (v1.1 — Model Validation & Trust)

- [ ] Out-of-sample regime quality metrics (stability, economic interpretability)
- [ ] Walk-forward backtest: regime-conditional returns vs baseline
- [ ] Regime transition matrix validation (are transitions economically sensible?)
- [ ] Clear "trust threshold" defined and met before live trading
- [ ] Stress test: model behavior during known crisis periods (2008, 2020, 2022)
- [ ] Confidence calibration check (do predicted probabilities match observed frequencies?)

### Out of Scope

- Change underlying HMM algorithm (NumPyro is final)
- Add new regime count or naming (K=4 locked)
- Build trading execution logic (Algo-Trading-Bot's job)
- GPU acceleration (CPU performance sufficient)
- Real-time signal streaming (bot handles that)

## Key Decisions

| Decision | Outcome | Milestone |
|----------|---------|-----------|
| NumPyro over hmmlearn/pomegranate | ✓ Good — stable, causal guarantees | v1.0 |
| K=4 regimes (not K=3) | ✓ Good — walk-forward BIC justified | v1.0 |
| Rolling PCA with Procrustes alignment | ✓ Good — reduces OOS fragmentation | v1.0 |
| GARCH-conditional VaR | ✓ Good — passes Christoffersen test | v1.0 |
| 6 held-out features over original 7 | ✓ Good — +3.5% OOS accuracy | v1.0 |
| Incremental delta fetch (not full re-download) | ✓ Good — 20 min → <5 min | v1.0 |

## Constraints

**Hard (non-negotiable):**
- NumPyro only for HMM
- 13 features → rolling PCA → HDP-HMM pipeline
- No K-means or hard clustering
- K=4 regimes with fixed labels

**Soft:**
- Keep existing test suite (160+ tests minimum)
- Minimize API changes to signals.py
- Dashboard remains Streamlit-based

## Integration Dependencies

- **Downstream:** Algo-Trading-Bot (regime signals → trading decisions)
- **Downstream:** Portfolio-Manager (regime probabilities → risk adjustments)
- **Public API (do not break):** `detect()`, `fit()`, regime labels in signals.py

## References

- Codebase: https://github.com/AdamMooo/Regime-Detection
- Archive: `.planning/milestones/v1.0-ROADMAP.md`
- Model card: `MODEL_CARD.md`

---
*Last updated: 2026-04-16 after v1.0 milestone*
