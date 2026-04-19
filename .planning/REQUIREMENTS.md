# Requirements — Regime-Detection v1.1

## Milestone Goal

Diagnose regime detection failures, overhaul feature engineering, experiment with model
architecture, and wire up a clean daily pipeline. Model quality is the only priority —
no UI work until regimes are economically valid.

---

## v1.1 Requirements

### Diagnostics

- [ ] **DIAG-01**: Regime characteristics are visualized — vol ordering across regimes, dwell
  time distribution, transition matrix heatmap — so failure modes are visible at a glance
- [ ] **DIAG-02**: OOS regime accuracy is benchmarked against a naive baseline (e.g., persist
  yesterday's regime) to establish whether the model adds signal
- [ ] **DIAG-03**: Failure modes are documented — which regimes are most often misclassified,
  and under what market conditions (crisis periods, low-vol regimes, etc.)
- [ ] **DIAG-04**: Regime-conditional forward return analysis is implemented — for each detected
  regime, compute 1d/5d/21d forward returns of SPY, EEM, TLT, HYG as an economic validity
  check. Statistical separation across regimes tested (Kruskal-Wallis). This is a validation
  diagnostic only — NOT a model feature or trading backtest. Lives in evaluation.py +
  tests/test_regime_economic_validity.py

### Feature Engineering

- [ ] **FEAT-01**: Feature candidate set is expanded to 12+ candidates with economic rationale
  for each (current: 6 features)
- [x] **FEAT-02**: Feature selection uses proper walk-forward cross-validation — no held-out
  split bias. Each fold selects features on training data only, tests on OOS fold
- [x] **FEAT-03**: Feature importance is documented — which features drive regime separation,
  measured on OOS data

### Model Architecture

- [ ] **MODEL-01**: K experiment is run with rigorous OOS comparison — K=3, K=4, K=5 tested;
  winner selected on OOS stability + economic validity (DIAG-04), not just BIC
- [ ] **MODEL-02**: Decision on USE_HDP documented and locked — either re-enable NumPyro
  HDP-HMM with evidence it outperforms StudentTHMM, or formally deprecate the dead code
- [ ] **MODEL-03**: train.py monolith is refactored — no single module exceeds 500 lines;
  training, evaluation, and dashboard building are separate concerns

### Pipeline & Outputs

- [ ] **PIPE-01**: `python scripts/run.py` executes the full daily pipeline
  (collect → features → train → signals) in under 10 minutes on new data
- [ ] **PIPE-02**: Exactly 2 HTML outputs exist — figures/dashboard.html and
  figures/feature_analysis.html. No others are created or left over
- [ ] **PIPE-03**: Regime output (regime_results.csv) is written on every run with today's
  regime, probabilities, and GARCH VaR — suitable for nightly cron execution

---

## Future Requirements (Deferred)

- Live trust threshold enforcement before trading (post-model-validation)
- Real-time streaming regime inference
- Automated nightly cron job setup (after pipeline is verified stable)
- Dashboard live regime indicator panel (UI work deferred until model is good)

---

## Out of Scope (v1.1)

- Forward returns as model features — returns are for validation only, never inputs
- Trading execution or backtest (Algo-Trading-Bot's responsibility)
- GPU acceleration
- Changing the public API of signals.py (detect(), fit(), regime labels)
- Adding a third HTML output

---

## Traceability

| REQ-ID | Phase | Plan |
|--------|-------|------|
| DIAG-01 | Phase 4 | TBD |
| DIAG-02 | Phase 4 | TBD |
| DIAG-03 | Phase 4 | TBD |
| DIAG-04 | Phase 4 | TBD |
| FEAT-01 | Phase 5 | TBD |
| FEAT-02 | Phase 5 | TBD |
| FEAT-03 | Phase 5 | TBD |
| MODEL-01 | Phase 6 | TBD |
| MODEL-02 | Phase 6 | TBD |
| MODEL-03 | Phase 6 | TBD |
| PIPE-01 | Phase 7 | TBD |
| PIPE-02 | Phase 7 | TBD |
| PIPE-03 | Phase 7 | TBD |

---
*Last updated: 2026-04-15 — Traceability filled by roadmapper (v1.1 Phases 4–7)*
