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

## Downstream Integration
When integrating with Algo-Trading-Bot, regime labels must align:
- Regime 0 (expansion) → LOW_VOL
- Regime 1 (neutral) → MED_VOL
- Regime 2 (contraction) → HIGH_VOL

## Do Not
- Use K-means or hard clustering for regime assignment
- Skip PCA before HMM (dimensionality too high otherwise)
- Change the collect.py schema without checking features.py compatibility
- Build production execution logic here (that's Algo-Trading-Bot's job)

## Session Close Checklist
- Update NOTES.md with progress + next action
- Commit and push to GitHub
