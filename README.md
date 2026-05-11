# Regime Detection

**Bayesian HDP-HMM Market Regime Detection**

A quantitative pipeline that automatically discovers market regimes using a Hierarchical Dirichlet Process Hidden Markov Model (HDP-HMM) with sticky transitions. The system computes 23 curated features spanning volatility, cross-asset risk, microstructure, and macro conditions. A configurable subset (`FEATURE_SUBSET`) is selected for HMM input, currently set to 4 features. The system produces regime labels and signals consumed downstream by Algo-Trading-Bot and Portfolio-Manager.

---

## Pipeline Architecture

```
collect.py          features.py           train.py              signals.py
┌──────────┐       ┌──────────────┐      ┌────────────────┐    ┌────────────────┐
│  Yahoo   │──────>│ 23 Curated   │─────>│  Select 4 via  │───>│ Regime Signals │
│  Finance │       │  Features    │      │  FEATURE_SUBSET│    │ + Trust Score  │
│  + FRED  │       │  (vol, macro,│      │  → HDP-HMM     │    └───────┬────────┘
└──────────┘       │  structure,  │      │  (NumPyro/JAX) │            │
                   │  microstruc) │      └────────────────┘    ┌───────▼────────┐
                   └──────────────┘                            │   Dashboard    │
                                                               │  (Plotly HTML) │
                                                               └────────────────┘
```

## Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** — HDP-HMM design rationale, feature selection decisions, causal guarantees, and performance validation
- **[Integration Guide](docs/INTEGRATION.md)** — Signal output schema, label mapping (LOW_VOL/MED_VOL/HIGH_VOL), how Algo-Trading-Bot consumes regime signals
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** — Common issues, debug workflows, recovery procedures

## Production Status & Validation

**Status:** ✅ **PRODUCTION READY** (as of 2026-04-14)

- **[MODEL_CARD.md](docs/MODEL_CARD.md)** — Architecture, validation results, limitations, production checklist
- **[REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)** — Exact reproduction steps (JAX and NumPyro pinned for deterministic regime labels)
- **[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)** — Known issues with root causes and mitigations

**Validation Summary:**
- ✅ Causality verified — no lookahead, expanding windows, forward-pass inference only
- ✅ Reproducibility — JAX and NumPyro version-pinned, seed=42 deterministic
- ✅ Regime stability — OOS stable, not fragmented
- ✅ Feature generalization — re-selected on held-out train set 2010–2020
- ✅ Bot integration — signals match Algo-Trading-Bot schema, label mapping validated
- ✅ 18 test files, 2000+ lines of test coverage

## Features

`features.py` computes 23 curated features, saved to `data/features_transformed.csv`. `FEATURE_SUBSET` in `src/config.py` selects which of these feed the HDP-HMM (currently: VIX, VRP, NFCI, yield_curve_slope). Features are standardized with expanding-window z-score at training time — causal, no future data.

| Category | Features |
|----------|----------|
| **Volatility state** | `VIX`, `VRP` |
| **Vol dynamics** | `rv_ratio_10_63`, `vix_ts_slope`, `SPY_volvol20`, `SPY_skew20` |
| **Cross-asset risk** | `SPY_TLT_corr63`, `credit_stress`, `eigen_conc`, `SPY_dd63` |
| **Microstructure** | `SPY_ret`, `SPY_ac1_20`, `SPY_rel_volume`, `SPY_vol_adj_ret`, `amihud_illiq20`, `roll_spread20`, `lev_effect20` |
| **SV-specific** | `SPY_rv10_lag5`, `SPY_rv10_lag10` |
| **Macro (FRED)** | `HY_OAS`, `NFCI`, `yield_curve_slope`, `GLD_trend` |

Right-skewed features are log-transformed before winsorization.

## Regime Labels

Regimes are named by absolute realized volatility bracket — labels are stable across IS/OOS windows:

| Regime | Ann. Vol | Bot Label |
|--------|----------|-----------|
| Low-Vol | 0–10% | `LOW_VOL` |
| Moderate-Vol | 10–18% | `MED_VOL` |
| Elevated-Vol | 18–28% | `HIGH_VOL` |
| Crisis-Vol | 28%+ | `HIGH_VOL` |

The `LABEL_MAPPING` in `src/config.py` is the source of truth for all downstream consumers.

## Quickstart

### Prerequisites
- Python 3.11+
- [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) (free)

### Setup

```bash
git clone https://github.com/AdamMooo/Regime-Detection.git
cd Regime-Detection

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
FRED_API_KEY=your_api_key_here
```

### Run

```bash
# Full pipeline (collect → features → train → signals → dashboard)
python scripts/run.py

# Full pipeline + walk-forward OOS validation
python scripts/run.py --validate

# Individual stages
python scripts/run.py collect          # download market + macro data
python scripts/run.py features         # build + scale features
python scripts/run.py train            # fit HDP-HMM → regime_results.csv
python scripts/run.py signals          # assemble signals from saved results
python scripts/run.py dashboard        # rebuild dashboard (no retraining)
python scripts/run.py regime           # print current regime (CLI)
python scripts/run.py trust            # print trust scorecard (CLI)
python scripts/run.py analyze          # feature diagnostics → feature_analysis.html
```

The interactive dashboard is saved to `figures/dashboard.html`.

## Incremental Data Mode

The pipeline caches downloaded data and fetches only new data on subsequent runs.

**First run** (~20 min): downloads all historical data from FRED and yfinance (2010–present).

**Subsequent runs** (<5 min): detects the cache and fetches only new data.

**Force full re-download:**
```bash
rm -rf data/cache/
python scripts/run.py
```

## Configuration

All parameters are in `src/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `START_DATE` | 2010-01-01 | Data start date |
| `TICKERS` | SPY, QQQ, IWM, EEM, TLT, HYG, GLD | Universe for price features |
| `FEATURE_SUBSET` | VIX, VRP, NFCI, yield_curve_slope | Features fed into HDP-HMM |
| `HDP_TRUNCATION` | 6 | Max states for stick-breaking |
| `HDP_KAPPA` | 10.0 | Sticky self-transition weight |
| `HDP_INFERENCE` | svi | `svi` (fast) or `nuts` (gold-standard, overnight) |
| `SVI_NUM_STEPS` | 3000 | Variational inference steps |
| `VOL_BRACKETS` | 0-10-18-28% | Absolute vol thresholds for regime naming |
| `MAX_DATA_STALENESS_DAYS` | 3 | Warn if market data is stale |

## Project Structure

```
src/
├── config.py            # All hyperparameters & paths
├── core/
│   ├── hdp_hmm.py       # Bayesian HDP-HMM (NumPyro/JAX)
│   ├── inference.py     # Regime inference (filtering, labeling, standardization)
│   ├── evaluation.py    # Diagnostics & walk-forward validation
│   └── orchestrator.py  # Walk-forward coordination
├── features/
│   ├── collect.py       # Market data download (yfinance)
│   └── features.py      # Feature engineering + expanding-window scaling
├── data/
│   └── collect_macro.py # Macro data download (FRED)
├── pipeline/
│   ├── stages.py        # Stateless disk-to-disk stage functions
│   └── runner.py        # Pipeline orchestration
└── signals/
    ├── signals.py       # Signal assembly & validation
    └── trust.py         # Trust scorecard aggregation
scripts/
├── run.py               # CLI entry point
└── pipelines/
    ├── train.py         # HMM training orchestrator
    └── analyze.py       # Feature diagnostics
tests/                   # 18 test files covering causality, OOS, calibration, integration
requirements.txt         # Version-pinned dependencies (JAX/NumPyro exact pins)
```

## Causality Guarantees

Regime assignments are strictly causal — only past/present data, never future data:

1. **Features** — all computed with expanding windows (no fill-forward, no smoothing)
2. **Standardization** — expanding-window z-score uses only past mean/std
3. **HMM inference** — forward-pass filtering only (no forward-backward smoothing)
4. **Labels** — `REGIME_HOLD_DAYS` hysteresis suppresses noise without lookahead

Verified by `tests/test_causality.py`. CI fails if any guarantee is violated.

## References

- Teh, Y. W., Jordan, M. I., Beal, M. J., & Blei, D. M. (2006). *Hierarchical Dirichlet Processes.* JASA.
- Fox, E. B., Sudderth, E. B., Jordan, M. I., & Willsky, A. S. (2011). *A Sticky HDP-HMM with Application to Speaker Diarization.* Annals of Applied Statistics.
- Phan, D., Pradhan, N., & Jankowiak, M. (2019). *Composable Effects for Flexible and Accelerated Probabilistic Programming in NumPyro.*
