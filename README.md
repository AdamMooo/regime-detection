# Regime Detection

**Bayesian HDP-HMM Market Regime Detection**

This repository contains a lightweight regime-detection pipeline for the thesis-style workflow around SPY/VIX/FRED features and a sticky HDP-HMM. The codebase is currently in a partially modernized state: the core feature engineering and paper artifacts are present, and there is now a working CLI wrapper so the README commands are usable again.

---

## What is here now

- Feature collection from SPY, VIX, Treasury slope, and NFCI
- Expanding-window feature standardization
- A CLI entry point at [scripts/run.py](scripts/run.py) for the documented commands
- Existing paper outputs in [results](results) and generated figures in [figures](figures)

## Current status

**Status:** ✅ **CLI and README are aligned again**

The main issue was that the repository had the pipeline logic, but the README referenced a missing runner script. I added a compatibility CLI so the documented commands now work, and it will fall back to the repository’s cached/published artifacts when a full retrain is not possible.

## Quickstart

### Prerequisites
- Python 3.11+
- Optional: [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) for fresh data downloads

### Setup

```bash
git clone https://github.com/AdamMooo/Regime-Detection.git
cd Regime-Detection

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

If you want to refresh the raw data, create a `.env` file with your FRED key:

```bash
FRED_API_KEY=your_api_key_here
```

### Run the documented commands

```bash
# Full pipeline entry point
python scripts/run.py

# Full pipeline with compatibility flag
python scripts/run.py --validate

# Individual commands
python scripts/run.py collect          # use cached data if already present
python scripts/run.py features         # use cached features if already present
python scripts/run.py train            # use existing results artifact if retraining is unavailable
python scripts/run.py signals          # enrich results with regime streak and entropy
python scripts/run.py dashboard        # write figures/dashboard.html
python scripts/run.py regime           # print the latest regime label
python scripts/run.py trust            # print a simple trust scorecard
python scripts/run.py analyze          # write figures/feature_analysis.html
```

### Notes on data freshness

- The repository already includes processed artifacts under [data/processed](data/processed) and published regime outputs under [results](results).
- If you run `collect` and the environment lacks a FRED API key, the CLI will reuse the existing cached data instead of failing hard.
- The `--validate` flag is accepted for compatibility, but the walk-forward validation stage is still a stub in this checkout.

## Project structure

```text
src/
├── config.py            # Core hyperparameters and paths
├── core/
│   ├── hdp_hmm.py       # HDP-HMM training code
│   ├── inference.py     # Causal standardization and inference helpers
├── data/
│   └── collect_macro.py # SPY/VIX/FRED feature collection
├── pipeline/
│   └── stages.py        # Stage implementations used by the CLI
scripts/
└── run.py               # CLI entry point for the documented commands
```

## Verification

A regression test was added at [tests/test_cli_runner.py](tests/test_cli_runner.py) to ensure the CLI entry point remains runnable.
