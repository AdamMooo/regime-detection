# Codebase Structure

**Analysis Date:** 2026-04-18

## Directory Layout

```
Regime-Detection/
├── src/                        # Core library modules
│   ├── config.py               # All hyperparameters, paths, feature config (single source of truth)
│   ├── __init__.py
│   ├── core/                   # HMM inference, training, evaluation, orchestration
│   │   ├── inference.py        # Causal regime inference (StudentTHMM, filtered_probs, expanding_standardize)
│   │   ├── hmm_training.py     # Rolling PCA, BIC selection, regime naming, SV/GARCH fitting
│   │   ├── evaluation.py       # VaR backtesting, Kupiec/Christoffersen tests, bootstrap CIs
│   │   ├── orchestrator.py     # Walk-forward OOS validation
│   │   ├── hdp_hmm.py          # Bayesian HDP-HMM (NumPyro, inactive: USE_HDP=False)
│   │   └── __init__.py
│   ├── features/               # Data collection and feature engineering
│   │   ├── collect.py          # yfinance download, incremental cache, validation
│   │   ├── features.py         # 17-feature build, log1p skew fix, expanding winsorization
│   │   └── __init__.py
│   └── signals/                # Output layer for downstream consumers
│       ├── signals.py          # compute_signals() — regime awareness dict, bot_label
│       ├── trust.py            # Trust scorecard (PASS/WARN/FAIL aggregation)
│       └── __init__.py
├── scripts/                    # CLI entry points and orchestration
│   ├── run.py                  # Top-level pipeline: collect → features → analyze → train → signals
│   ├── __init__.py
│   ├── pipelines/
│   │   ├── train.py            # Heavy training orchestrator (PCA→HMM→GARCH→OOS→dashboard)
│   │   ├── analyze.py          # Feature diagnostics (interactive HTML via Plotly)
│   │   └── __init__.py
│   └── analysis/               # Standalone diagnostic scripts (Phase 4 empirical diagnostics)
│       ├── analyze_regime_characterization.py
│       ├── analyze_feature_importance.py
│       ├── analyze_feature_selection.py
│       ├── analyze_oos_fragmentation.py
│       ├── analyze_signal_quality.py
│       ├── select_k_via_crossval.py
│       └── signal_combination.py
├── tests/                      # Pytest test suite (~20 files, 160+ tests)
│   ├── conftest.py             # Shared fixtures
│   ├── test_causality.py       # Causal guarantees (no lookahead) — 10 tests
│   ├── test_bot_integration.py # Signal schema validation for Algo-Trading-Bot
│   ├── test_var_backtesting.py # VaR tests (Kupiec, Christoffersen)
│   ├── test_regime_economic_validity.py  # 24 economic validity checks
│   ├── test_oos_validation.py  # Walk-forward OOS metrics
│   ├── test_pca_caching.py     # PCA checkpoint persistence
│   ├── test_incremental_collection.py    # Cache delta detection
│   ├── test_calibration.py     # Regime probability calibration (ECE)
│   ├── test_train_refactor.py  # Regression tests for Phase 3.1 refactor
│   ├── test_dashboard_refactor.py
│   ├── test_dashboard_hardening.py
│   ├── test_trust_scorecard.py
│   ├── test_signal_combination.py
│   ├── test_signal_combination_performance.py
│   ├── test_feature_selection_bias.py
│   ├── test_oos_fragmentation.py
│   ├── test_regime_count_selection.py
│   ├── test_model_card_validation.py
│   └── test_validation.py
├── data/                       # Generated pipeline outputs (not committed except structure)
│   ├── market_data.csv         # Raw aligned OHLCV + VIX
│   ├── features_transformed.csv
│   ├── features_scaled.csv
│   ├── pca_components.csv
│   ├── regime_results.csv      # PRIMARY OUTPUT — consumed by downstream systems
│   ├── bic_selection.csv
│   ├── feature_selection_report.txt
│   ├── regime_count_selection_report.txt
│   └── cache/                  # Incremental data cache
│       ├── .cache_manifest.json
│       ├── {TICKER}_incremental.csv
│       └── {TICKER}_index.feather (JSON metadata)
├── models/                     # Serialized model artifacts (joblib)
│   ├── hmm_model.pkl
│   ├── pca_model.pkl
│   └── regime_model.pkl
├── figures/                    # Visualization outputs
│   ├── dashboard.html          # Interactive Plotly regime dashboard
│   └── feature_analysis.html   # Feature diagnostics report
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # Legacy architecture doc (pre-Phase 3.1)
│   ├── INTEGRATION.md          # Algo-Trading-Bot integration guide
│   ├── KNOWN_ISSUES.md
│   ├── MODEL_CARD.md
│   ├── NOTES.md
│   ├── REPRODUCIBILITY.md
│   ├── RISK_MODEL_CARD.md
│   └── TROUBLESHOOTING.md
├── reports/                    # Diagnostic reports
│   ├── fragmentation_diagnostic.log
│   └── fragmentation_report.txt
├── .planning/                  # GSD planning artifacts
│   ├── codebase/               # This directory — codebase maps
│   ├── phases/                 # Phase plans and reviews
│   │   ├── 01-blockers/
│   │   ├── 02-incremental/
│   │   ├── 02.5-model-diagnostics-robustness/
│   │   ├── 03-refactor/
│   │   ├── 04-empirical-diagnostics/
│   │   └── 05-feature-engineering-overhaul/
│   └── milestones/
├── .github/workflows/tests.yml # CI: version pin check + full pytest suite
├── requirements.txt            # Exact pinned dependencies
├── src/config.py               # (also root: __init__.py, __pycache__)
├── CLAUDE.md                   # Project-level Claude instructions
├── NOTES.md                    # Session resume state
└── README.md
```

## Directory Purposes

**`src/core/`:**
- Purpose: All model logic — inference, training, evaluation, orchestration
- Key files: `inference.py` (foundation), `hmm_training.py` (training), `evaluation.py` (metrics), `orchestrator.py` (walk-forward), `hdp_hmm.py` (Bayesian alternative)
- Pattern: Each module has explicit `__all__` exports

**`src/features/`:**
- Purpose: Data ingestion and feature construction
- Key files: `collect.py` (Yahoo Finance), `features.py` (17 features + preprocessing)

**`src/signals/`:**
- Purpose: Output layer — translate regime results into structured signals
- Key files: `signals.py` (compute_signals, the downstream API), `trust.py` (scorecard)

**`scripts/`:**
- Purpose: CLI entry points; no library logic
- Key files: `run.py` (top-level dispatcher), `pipelines/train.py` (heavy orchestrator), `pipelines/analyze.py` (diagnostics)
- `scripts/analysis/` contains standalone Phase 4 diagnostic scripts — not part of production pipeline

**`tests/`:**
- Purpose: Automated test suite; pytest fixtures in `conftest.py`
- Critical tests: `test_causality.py` (10 causality guarantees), `test_bot_integration.py` (signal schema), `test_regime_economic_validity.py` (24 validity checks)

**`data/`:**
- Purpose: Pipeline artifacts — generated at runtime, not committed to git (except structure)
- Primary output: `data/regime_results.csv` — consumed by Algo-Trading-Bot and Portfolio-Manager

**`models/`:**
- Purpose: Serialized model checkpoints (joblib)
- Loaded for live inference without retraining

**`docs/`:**
- Purpose: Human-readable documentation including integration guide, model card, risk card
- `INTEGRATION.md` is the contract spec for downstream consumers

## Key File Locations

**Entry Points:**
- `scripts/run.py` — top-level CLI (`python scripts/run.py [step]`)
- `scripts/pipelines/train.py::train()` — full training pipeline
- `scripts/pipelines/train.py::rebuild_dashboard()` — dashboard only

**Configuration:**
- `src/config.py` — all hyperparameters, feature lists, paths, label mappings

**Core Logic:**
- `src/core/inference.py` — causal inference primitives (start here for regime logic)
- `src/core/hmm_training.py` — PCA + HMM training
- `src/core/evaluation.py` — VaR backtesting
- `src/core/orchestrator.py` — OOS validation

**Feature Pipeline:**
- `src/features/features.py::build_features()` — generates all 17 features
- `src/features/features.py::prepare_features()` — end-to-end: build → transform → PCA → save
- `src/features/collect.py::collect()` — data download with incremental cache

**Output / Integration:**
- `src/signals/signals.py::compute_signals()` — produces the downstream API dict
- `src/config.py::LABEL_MAPPING` — regime name → bot label (source of truth)
- `docs/INTEGRATION.md` — integration contract documentation

**Testing:**
- `tests/test_causality.py` — most critical; must pass before any inference changes
- `tests/test_bot_integration.py` — must pass before any signals.py changes

## Naming Conventions

**Files:**
- Source modules: `snake_case.py` (e.g., `hmm_training.py`, `collect.py`)
- Test files: `test_{module_or_area}.py` (e.g., `test_causality.py`)
- Analysis scripts: `analyze_{topic}.py` (e.g., `analyze_oos_fragmentation.py`)
- Data outputs: `{content}_{type}.csv` (e.g., `features_transformed.csv`, `regime_results.csv`)

**Directories:**
- Source packages: `snake_case/` (e.g., `src/core/`, `src/features/`)
- Planning: kebab-case phases (e.g., `04-empirical-diagnostics/`)

**Functions:**
- Public API: `snake_case` (e.g., `compute_signals`, `fit_rolling_pca`)
- Private helpers: `_prefixed_snake_case` (e.g., `_fit_hmm`, `_validate_cache`, `_fix_skew`)

**Config constants:**
- `UPPER_SNAKE_CASE` throughout `src/config.py`

## Where to Add New Code

**New feature (market indicator):**
- Add to `src/features/features.py::build_features()` — append to the existing feature group sections
- Add name to `CURATED_FEATURES` list in `features.py`
- Update `FEATURE_SUBSET` in `src/config.py` if it should be selected for PCA
- Add test to `tests/test_causality.py` if the feature has a causal constraint

**New regime metric or diagnostic:**
- Add function to `src/core/evaluation.py`
- Call from `scripts/pipelines/train.py::train()` in the evaluation block
- If it should appear in the regime awareness output, add to `src/signals/signals.py::compute_signals()`
- Add corresponding key to `tests/test_bot_integration.py` schema validation

**New signal field for downstream consumers:**
- Implement in `src/signals/signals.py`
- Add to `compute_signals()` return dict
- Update schema validation in `tests/test_bot_integration.py`
- Document in `docs/INTEGRATION.md`

**New training variant or model:**
- Add gated by a config flag in `src/config.py` (follow `USE_HDP` pattern)
- Implement in new or existing `src/core/` module
- Add to `scripts/pipelines/train.py` conditional block

**New analysis script (non-production):**
- Place in `scripts/analysis/`
- Import from `src/` modules; do not add production-path dependencies

**Utilities:**
- Shared statistical helpers: add to the relevant `src/core/` module
- Shared data helpers: add to `src/features/collect.py` or `src/features/features.py`
- No dedicated `utils.py` — helpers live in the module that owns their concern

## Special Directories

**`.claude/worktrees/`:**
- Purpose: Agent worktree checkouts from previous GSD agent runs
- Generated: Yes (by GSD tooling)
- Committed: No (should be in `.gitignore`)

**`.clone/`:**
- Purpose: Partial clone worktrees from agent runs
- Generated: Yes
- Committed: No

**`.venv/`:**
- Purpose: Local Python virtual environment
- Generated: Yes (by pip install)
- Committed: No

**`data/cache/`:**
- Purpose: Incremental data cache (ticker CSVs + manifest)
- Generated: Yes (by `collect.py` on first run)
- Committed: Structure only (actual CSVs gitignored)

**`.planning/`:**
- Purpose: GSD planning artifacts — phase plans, reviews, codebase maps
- Generated: Partially (by GSD tooling and manual authoring)
- Committed: Yes

---

*Structure analysis: 2026-04-18*
