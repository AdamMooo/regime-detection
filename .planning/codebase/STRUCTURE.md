# Codebase Structure

**Analysis Date:** 2026-05-09

## Directory Layout

```
regime-detection/
├── scripts/
│   ├── run.py                        # Top-level CLI entry point (all commands)
│   ├── cron_run.sh                   # Cron wrapper for daily pipeline
│   ├── health_check.py               # Standalone health probe
│   ├── pipelines/
│   │   ├── train.py                  # Training orchestrator + dashboard builder
│   │   └── analyze.py                # Feature analysis HTML report builder
│   └── analysis/                     # One-off research scripts (not in pipeline)
│       ├── analyze_feature_importance.py
│       ├── analyze_feature_selection.py
│       ├── analyze_oos_fragmentation.py
│       ├── analyze_regime_characterization.py
│       ├── analyze_signal_quality.py
│       ├── apply_feature_selection.py
│       ├── compare_hdp_vs_student.py
│       ├── select_k_via_crossval.py
│       ├── signal_combination.py
│       └── walk_forward_feature_selection.py
├── src/
│   ├── config.py                     # All model params, paths, label mapping (source of truth)
│   ├── pipeline/
│   │   ├── runner.py                 # Pipeline class: timing, logging, exit-code contract
│   │   └── stages.py                 # STAGES registry (8 daily + 1 validate-gated)
│   ├── features/
│   │   ├── collect.py                # OHLCV + VIX from yfinance; incremental cache
│   │   └── features.py               # 21-feature engineering; FEATURE_SUBSET selection
│   ├── data/
│   │   └── collect_macro.py          # FRED macro series (yield curve, HY OAS, NFCI)
│   ├── core/
│   │   ├── hdp_hmm.py                # Bayesian HDP-HMM (NumPyro, SVI/NUTS)
│   │   ├── inference.py              # Forward filter, hysteresis labels, expanding standardize
│   │   ├── hmm_training.py           # BIC selection, regime naming, per-regime SV/GARCH
│   │   ├── pca_utils.py              # Rolling PCA (Procrustes-aligned), LinearizedSV
│   │   ├── evaluation.py             # Regime diagnostics, bootstrap CI
│   │   ├── var_backtesting.py        # GARCH VaR (Kupiec + Christoffersen) — production standard
│   │   ├── forward_returns.py        # Regime-conditional forward return analysis (validation only)
│   │   └── orchestrator.py           # Walk-forward OOS validation
│   └── signals/
│       ├── signals.py                # Regime awareness engine; bot_label mapping; GARCH VaR
│       └── trust.py                  # Trust scorecard (data freshness, separation, calibration)
├── data/
│   ├── market_data.csv               # Raw OHLCV + VIX (written by collect)
│   ├── macro_data.csv                # FRED macro series (written by collect_macro)
│   ├── features_transformed.csv      # 14-feature engineered matrix (written by features)
│   ├── features_scaled.csv           # Intermediate scaled features
│   ├── pca_components.csv            # Rolling PCA projections (written by train_hmm)
│   ├── regime_results.csv            # Final output: regime labels + bot_label + GARCH VaR
│   ├── garch_params.json             # Per-regime GARCH(1,1) params (written by garch stage)
│   ├── oos_regime_labels.csv         # Walk-forward OOS labels (written by walk_forward)
│   └── cache/
│       ├── .cache_manifest.json      # Incremental cache metadata (SHA256 hashes, timestamps)
│       ├── {TICKER}_incremental.csv  # Per-ticker delta rows
│       └── {TICKER}_index.feather    # Per-ticker Feather index for fast lookup
├── models/
│   ├── hdp_params.pkl                # HDP-HMM variational parameters (SVI posterior)
│   ├── hdp_samples.pkl               # Posterior samples from trained guide
│   ├── hdp_metadata.json             # HDP metadata (K found, inference mode, timing)
│   ├── hmm_model.pkl                 # Classic StudentTHMM checkpoint (fallback)
│   ├── pca_model.pkl                 # PCA model checkpoint (sklearn PCA object)
│   └── regime_model.pkl              # Full regime model checkpoint (dict with model + results_df)
├── tests/
│   ├── conftest.py                   # Shared fixtures (synthetic regime DataFrames)
│   ├── test_causality.py             # Causality guarantees (10 tests; CI-enforced)
│   ├── test_bot_integration.py       # bot_label schema validation
│   ├── test_train_refactor.py        # Phase 3.1 refactoring regression tests
│   ├── test_features.py              # Feature engineering correctness
│   ├── test_calibration.py           # Regime confidence calibration
│   ├── test_oos_validation.py        # OOS validation metrics
│   ├── test_oos_fragmentation.py     # OOS regime fragmentation checks
│   ├── test_walk_forward.py          # Walk-forward validation
│   ├── test_pipeline_stages.py       # Stage registry and execution
│   ├── test_pipeline_idempotent.py   # Pipeline idempotency
│   ├── test_pipeline_timing.py       # Stage timing contract
│   ├── test_exit_codes.py            # Exit-code contract (uses GSD_FORCE_STAGE_FAIL)
│   ├── test_pca_caching.py           # PCA model persistence
│   ├── test_incremental_collection.py # Incremental cache correctness
│   ├── test_regime_results_schema.py  # regime_results.csv column schema
│   ├── test_regime_results_freshness.py # Data staleness checks
│   ├── test_regime_economic_validity.py # Regime economic plausibility
│   ├── test_regime_count_selection.py   # K=3 regime count
│   ├── test_section_signals.py       # Feature section signal quality
│   ├── test_signal_combination.py    # Signal combination engine
│   ├── test_signal_combination_performance.py
│   ├── test_trust_scorecard.py       # Trust scorecard checks
│   ├── test_output_count.py          # Pipeline output file count
│   ├── test_model_card_validation.py # MODEL_CARD.md validation
│   ├── test_var_backtesting.py       # VaR backtest tests
│   ├── test_validation.py            # General validation checks
│   ├── test_feature_selection_bias.py # Feature selection bias detection
│   ├── test_hdp_decision.py          # HDP vs StudentTHMM decision tests
│   ├── test_dashboard_hardening.py   # Dashboard robustness
│   ├── test_dashboard_refactor.py    # Dashboard refactoring regression
│   └── _hdp_verdict.txt             # Stored regime fixture for reproducibility checks
├── docs/
│   ├── ARCHITECTURE.md               # Historical architecture doc (superseded by .planning/)
│   ├── INTEGRATION.md                # Bot integration guide
│   ├── MODEL_CARD.md                 # Complete model card (architecture, validation, checklist)
│   ├── RISK_MODEL_CARD.md            # VaR analysis (static vs GARCH comparison)
│   ├── KNOWN_ISSUES.md               # 8 Phase 2.5 issues with root causes and mitigations
│   ├── REPRODUCIBILITY.md            # Exact reproduction steps and verification checklist
│   ├── TROUBLESHOOTING.md            # Debug guide for common failures
│   └── NOTES.md                      # Scratch notes
├── logs/
│   ├── pipeline.log                  # RotatingFileHandler output (10 MB, 3 backups)
│   ├── pipeline_run.log              # Run-level log
│   └── cron_run.log                  # Cron execution log
├── figures/                          # Generated HTML dashboards (cleared on each full run)
├── reports/
│   ├── fragmentation_diagnostic.log  # OOS fragmentation diagnostic output
│   └── fragmentation_report.txt      # Human-readable fragmentation report
├── requirements.txt                  # Dependencies with exact pins for jax/numpyro
├── CLAUDE.md                         # Claude session context (architecture, constraints)
├── NOTES.md                          # Current state and next action (read first)
└── README.md                         # Project README
```

## Directory Purposes

**`src/`:**
- Purpose: All importable library code
- Contains: Five sub-packages (`config`, `pipeline`, `features`, `data`, `core`, `signals`)
- Key files: `src/config.py` (single source of truth for all parameters)

**`src/core/`:**
- Purpose: Core model and inference logic (the mathematical heart of the system)
- Contains: HDP-HMM, inference, PCA, evaluation, VaR, walk-forward
- Key constraint: All functions here must be causal (forward-pass only)

**`src/pipeline/`:**
- Purpose: Pipeline orchestration (stage registry, timing, logging, exit codes)
- Contains: `runner.py` (Pipeline class), `stages.py` (STAGES registry)
- Key constraint: STAGES order is locked; do not reorder without updating docs/tests

**`src/features/`:**
- Purpose: Data collection and feature engineering
- Contains: `collect.py` (market data), `features.py` (feature computation)
- Key constraint: `collect.py` schema changes require `features.py` compatibility check

**`src/data/`:**
- Purpose: External data collection beyond market OHLCV
- Contains: `collect_macro.py` (FRED macro series)

**`src/signals/`:**
- Purpose: Translation from regime state to actionable trading signals
- Contains: `signals.py` (regime awareness), `trust.py` (trust scorecard)

**`scripts/`:**
- Purpose: Executable entry points and research scripts
- Contains: `run.py` (main CLI), `cron_run.sh` (daily cron), `pipelines/` (train + analyze orchestrators), `analysis/` (one-off research, not in pipeline)

**`scripts/analysis/`:**
- Purpose: One-off research and diagnostic scripts used during model development
- Contains: Feature selection, OOS fragmentation, signal quality, K selection analysis
- Note: These are NOT part of the daily pipeline; they were used during Phases 2.5-6

**`data/`:**
- Purpose: All pipeline input and output data artifacts
- Generated: Yes (written by pipeline stages)
- Committed: Only `data/garch_params.json` and `data/feature_selection_report.txt` are committed; CSVs are gitignored

**`data/cache/`:**
- Purpose: Incremental data collection cache (avoids full re-download on each run)
- Generated: Yes
- Committed: No (gitignored)

**`models/`:**
- Purpose: Trained model checkpoints (pkl files)
- Generated: Yes (written by train_hmm stage)
- Committed: No (gitignored — too large and environment-specific)

**`figures/`:**
- Purpose: Generated HTML dashboards and diagnostic plots
- Generated: Yes (cleared on each full pipeline run)
- Committed: No (gitignored)

**`tests/`:**
- Purpose: Automated test suite (160+ tests)
- Contains: Unit, integration, and contract tests
- Key files: `conftest.py` (fixtures), `test_causality.py` (CI-enforced causality guarantees)

**`docs/`:**
- Purpose: Human-readable documentation and model cards
- Contains: Architecture docs, integration guide, model card, VaR analysis, troubleshooting

## Naming Conventions

**Files:**
- Snake_case for all Python modules: `collect.py`, `hmm_training.py`, `pca_utils.py`
- Test files prefixed `test_`: `test_causality.py`, `test_bot_integration.py`
- Stage functions prefixed `stage_`: `stage_collect`, `stage_train_hmm`

**Directories:**
- Snake_case: `src/core/`, `src/features/`, `src/signals/`

**Data files:**
- Descriptive snake_case: `regime_results.csv`, `features_transformed.csv`, `garch_params.json`
- Model files: `hdp_params.pkl`, `regime_model.pkl`, `pca_model.pkl`

**Config constants:**
- UPPER_SNAKE_CASE: `N_STATES`, `FEATURE_SUBSET`, `LABEL_MAPPING`, `VOL_BRACKETS`

## Where to Add New Code

**New pipeline stage:**
- Implementation: Add `stage_<name>(config, prev=None)` to `src/pipeline/stages.py`
- Registration: Append to `STAGES` list in `src/pipeline/stages.py:261` (order matters)
- Test: Add `test_pipeline_stages.py` coverage and `GSD_FORCE_STAGE_FAIL` exit-code test

**New feature:**
- Implementation: Add computation to `src/features/features.py::build_features()`
- Registration: Add name to `CURATED_FEATURES` list; add to `FEATURE_SUBSET` in `src/config.py` only after OOS validation
- Test: Add to `tests/test_features.py`

**New regime metric or diagnostic:**
- Implementation: Add to `src/core/evaluation.py` or create new file in `src/core/`
- Wire up: Import and call from `scripts/pipelines/train.py`
- Test: Add to `tests/test_validation.py` or create new test file

**New signal output column:**
- Implementation: Add column in `src/signals/signals.py::enrich_results()` or `src/pipeline/stages.py::stage_signals()`
- Schema: Add to `validate_signal_schema()` in `src/signals/signals.py`
- Test: Add to `tests/test_regime_results_schema.py` and `tests/test_bot_integration.py`

**New research/analysis script:**
- Location: `scripts/analysis/` (not in pipeline, not in `src/`)
- Pattern: Standalone script that reads from `data/` and writes to `reports/` or `figures/`

**New config parameter:**
- Location: `src/config.py` — add at the relevant section with a comment explaining the value
- Do not add default values inside individual modules; all tunable params belong in config

## Special Directories

**`data/cache/`:**
- Purpose: Per-ticker incremental download cache (CSV delta rows + Feather index)
- Generated: Yes, by `src/features/collect.py`
- Committed: No

**`models/`:**
- Purpose: Trained model pkl checkpoints
- Generated: Yes, by `train_hmm` and `garch` stages
- Committed: No — pkl files are environment-specific and too large

**`figures/`:**
- Purpose: HTML dashboards (Plotly interactive, browser-viewable)
- Generated: Yes — cleared at the start of each full `run_all()` run
- Committed: No

**`.planning/`:**
- Purpose: GSD workflow planning documents (STATE.md, phase plans, codebase maps)
- Generated: Partially (codebase docs auto-generated by GSD mapper)
- Committed: Yes

---

*Structure analysis: 2026-05-09*
