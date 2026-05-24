# Regime-Detection — Session Notes

## Status
Architecture: stripped HDP-HMM, paper-first
Branch: main
Last updated: 2026-05-24

## Current Architecture (Clean)

The pipeline has been stripped to the minimum needed for the paper:
- 4 features: spy_ret, vol_index, yield_slope, nfci (no PCA, no GARCH, no Student-t)
- HDP-HMM with Gaussian emissions, sticky transitions
- SVI for fast runs, NUTS for paper-quality posterior
- VOL_BRACKETS labeling (absolute realized vol)

## What Changed (2026-05-24 session)

- Fixed feature set: `vol_index + wti_shock` → `spy_ret + vol_index + yield_slope + nfci`
- Fixed broken import chain in `stages.py` (called non-existent `src.features.*`)
- Fixed `VOL_BRACKETS` and `MCMC_NUM_*` used in hdp_hmm.py but never imported
- Rewrote `collect_macro.py`: now fetches FRED T10Y2Y + NFCI (not WTI)
- Rewrote `baselines/parametric_hmm.py`: uses spy_ret, hmmlearn, 10 restarts
- Rewrote `baselines/threshold_rules.py`: VIX-only threshold (the null hypothesis)
- Stripped `stages.py` to 5 clean stages (removed dashboard, feature_analysis)
- Rewrote `CLAUDE.md` to match actual architecture

## Import Check (2026-05-24)

All imports pass:
```
config OK: ['spy_ret', 'vol_index', 'yield_slope', 'nfci']
hdp_hmm OK
inference OK
evaluation OK
threshold_rules OK
parametric_hmm OK
stages OK: ['collect', 'features', 'train_hmm', 'signals', 'walk_forward']
```

## Next Action

**Run the pipeline for the first time with the 4-feature set:**
```bash
python -c "from src.pipeline.runner import Pipeline; Pipeline().run_all()"
```
Or stage by stage:
```bash
python -c "from src.pipeline.stages import stage_collect; stage_collect(None)"
python -c "from src.pipeline.stages import stage_features; stage_features(None)"
python -c "from src.pipeline.stages import stage_train_hmm; stage_train_hmm(None)"
```

Requires `.env` with `FRED_API_KEY` (already set).

## After First Run

1. Check regime distribution — should be roughly Low-Vol 50%, Moderate-Vol 30%, High-Vol 20%
2. Implement `thesis_experiments.py` properly (currently has a placeholder `hdp_regime = 0`)
3. Build Figure 1: find two days with same VIX but different posterior (money shot)
4. Implement `walk_forward()` in `orchestrator.py` for OOS validation

## Stale Files (root level — can delete when ready)

- `data_download.py` — old XEG.TO fetcher, superseded by collect_macro.py
- `fit_toy_hdp.py` — toy experiment on old feature set (tsx_vol, boc_spread, wti_shock)
- `parametric_hmm.py` — duplicate of src/baselines/parametric_hmm.py
- `threshold_regimes.py` — duplicate of src/baselines/threshold_rules.py

## Key Files

- `src/config.py` — single source of truth: FEATURES, VOL_BRACKETS, all params
- `src/core/hdp_hmm.py` — the model (844 lines, clean)
- `src/data/collect_macro.py` — data collection (4 features via yfinance + FRED)
- `src/pipeline/stages.py` — pipeline stages (5 stages, all wired)
- `.env` — FRED_API_KEY (required, already set)
