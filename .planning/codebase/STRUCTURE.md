# Codebase Structure

**Analysis Date:** 2026-05-11

## Directory Layout

```
[project-root]/
├── src/                        # Thesis source code and experiments
│   ├── baselines/              # Rule-based and parametric regime baselines
│   ├── core/                   # HDP-HMM and model utilities
│   ├── data/                   # Data collection and preprocessing
│   ├── experiments/            # Experiment orchestration scripts
│   ├── pipeline/               # Additional pipeline staging utilities
│   ├── __init__.py             # Python package marker
│   └── config.py               # Central thesis configuration
├── data/processed/             # Generated CSV datasets
├── figures/                    # Generated plots and diagnostics
├── requirements.txt            # Python dependency pins
├── .planning/codebase/         # Codebase mapping docs
├── data_download.py            # Legacy/utility download script
├── parametric_hmm.py           # Legacy standalone HMM script
├── threshold_regimes.py        # Legacy threshold rule script
└── .venv/                      # Virtual environment
```

## Directory Purposes

**`src/`**:
- Purpose: thesis application code
- Contains: data ingest, baseline models, HDP-HMM core model, experiment runner
- Key files: `src/config.py`, `src/experiments/thesis_experiments.py`, `src/core/hdp_hmm.py`

**`src/baselines/`**:
- Purpose: simple baselines for comparison
- Contains: `threshold_rules.py`, `parametric_hmm.py`

**`src/core/`**:
- Purpose: inference and evaluation machinery
- Contains: `hdp_hmm.py`, `evaluation.py`, `inference.py`, `orchestrator.py`

**`src/data/`**:
- Purpose: download and preprocess raw market data
- Contains: `collect_macro.py`

**`src/experiments/`**:
- Purpose: orchestrate thesis experiment workflow and metrics
- Contains: `thesis_experiments.py`

**`src/pipeline/`**:
- Purpose: pipeline staging utilities (not required for Week 1 core thesis path)
- Contains: `runner.py`, `stages.py`

## Key File Locations

**Entry Points:**
- `src/experiments/thesis_experiments.py`: primary thesis experiment driver
- `src/data/collect_macro.py`: SPX/VIX/WTI data refresh

**Configuration:**
- `src/config.py`: all thesis constants, tickers, thresholds, HDP hyperparameters

**Core Logic:**
- `src/core/hdp_hmm.py`: NumPyro HDP-HMM definition and fitting
- `src/baselines/threshold_rules.py`: threshold regime labels
- `src/baselines/parametric_hmm.py`: HMM baseline logic

**Legacy helpers:**
- `data_download.py`: alternative download script
- `parametric_hmm.py`: standalone HMM script outside `src/`
- `threshold_regimes.py`: standalone threshold rule script outside `src/`

## Naming Conventions

**Files:**
- `snake_case.py` for all Python modules
- `src/` subpackages named by responsibility (`baselines`, `core`, `data`, `experiments`)

**Directories:**
- Feature areas grouped by function (data, baselines, core, experiments)

## Where to Add New Code

**New Feature:**
- Primary code: `src/experiments/thesis_experiments.py`
- Tests: create `tests/` and add `tests/test_*.py`

**New Model:**
- Implementation: `src/core/` if core modeling or inference
- Baseline: `src/baselines/`
- Experiment orchestration: `src/experiments/thesis_experiments.py`

**Data collection extension:**
- Add new tickers/features in `src/data/collect_macro.py`
- Add new config values to `src/config.py`

## Special Directories

**`data/processed/`**:
- Purpose: generated dataset CSVs
- Generated: yes
- Committed: no (should remain generated artifacts)

**`figures/`**:
- Purpose: generated diagnostic plots
- Generated: yes
- Committed: maybe if stable figures are part of thesis deliverables

---

*Structure analysis: 2026-05-11*

---
LINKS:AUTO
