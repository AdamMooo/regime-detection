# Claude Context — Regime-Detection

**Read NOTES.md first** — it has the current state and next action.

## Purpose
HDP-HMM market regime detection from macro and price features. Produces regime labels
(3 regimes expected) consumed downstream by Algo-Trading-Bot and Portfolio-Manager.

## Architecture
```
collect.py              Data collection (market prices + macro indicators)
features.py             13-feature engineering pipeline + rolling PCA
train.py                HDP-HMM model training (NumPyro)
hdp_hmm.py              Core HMM implementation
signals.py              Regime signal generation from trained model
run.py                  Orchestration: collect → features → train → signals
analyze.py              Post-hoc analysis and regime characterization
trust.py                Regime trust/confidence scoring
dashboard.py            Streamlit visualization dashboard
config.py               Model params, feature config, file paths
tests/                  Test suite
```

## Current State
- No formal GSD plan yet
- Core pipeline functional (collect → PCA → HMM → signals)
- Next: run /gsd-new-project to create a formal roadmap
- GitHub: https://github.com/AdamMooo/Regime-Detection

## Hard Constraints
- Use NumPyro for HMM — not hmmlearn, pomegranate, or other libraries
- 13 features → rolling PCA reduction → HDP-HMM (do not skip PCA)
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

## Do Not
- Use K-means or hard clustering for regime assignment
- Skip PCA before HMM (dimensionality too high otherwise)
- Change the collect.py schema without checking features.py compatibility
- Build production execution logic here (that's Algo-Trading-Bot's job)

## Session Close Checklist
- Update NOTES.md with progress + next action
- Commit and push to GitHub
