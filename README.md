# Regime Detection

**Bayesian HDP-HMM Market Regime Detection with Stochastic Volatility**

A quantitative research pipeline that automatically discovers market regimes using a Hierarchical Dirichlet Process Hidden Markov Model (HDP-HMM) with sticky transitions and Student-t emissions. The system extracts 13 curated features from multi-asset market data, applies rolling PCA for dimensionality reduction, fits a Bayesian nonparametric regime model via variational inference, and estimates regime-dependent stochastic volatility dynamics.

---

## Pipeline Architecture

```
collect.py          features.py           train.py              train.py
┌──────────┐       ┌──────────────┐      ┌───────────────┐     ┌──────────────┐
│  Yahoo   │──────>│ 13 Curated   │─────>│  Rolling PCA  │────>│  HDP-HMM     │
│  Finance │       │  Features    │      │  (Procrustes  │     │  (NumPyro    │
│  + FRED  │       │  + Scaling   │      │   aligned)    │     │   SVI/NUTS)  │
└──────────┘       └──────────────┘      └───────────────┘     └──────┬───────┘
                                                                      │
                         ┌────────────────────────────────────────────┘
                         │
              ┌──────────▼─────────┐     ┌──────────────────┐
              │  Regime Labeling   │────>│  Regime-Dep SV   │
              │  + State Merging   │     │  + GARCH + VaR   │
              └────────────────────┘     └──────────────────┘
                                                  │
                                         ┌────────▼────────┐
                                         │   Interactive   │
                                         │   Dashboard     │
                                         │  (Plotly HTML)  │
                                         └─────────────────┘
```

## Key Features

- **Bayesian nonparametric regime discovery** — HDP-HMM with stick-breaking prior automatically determines the number of market regimes (no manual K selection)
- **Absolute vol-bracket labeling** — Regimes are named by realized volatility level (e.g., "Moderate-Vol" = 10-18% annualized), not by rank — labels are stable across IS/OOS windows
- **Sticky transitions** — Dirichlet-weighted self-transition bias prevents spurious regime switching
- **Student-t emissions** — Heavy-tailed observation model captures market fat tails
- **13 curated features** spanning volatility state, vol dynamics, cross-asset risk, return dynamics, market structure, and leverage/fragility — hand-picked to minimize multicollinearity (max |r| < 0.85, VIF-validated)
- **Rolling PCA with Procrustes alignment** — Dimensionality reduction that maintains temporal consistency across windows
- **Regime-dependent stochastic volatility** — Linearized SV (Harvey 1994) and GARCH(1,1) per regime
- **Walk-forward validation** — Out-of-sample regime prediction with configurable rolling/expanding windows
- **Trust scorecard** — Aggregated PASS/WARN/FAIL verdict across 8 validation checks (regime separation, vol ordering, persistence, VaR backtest, OOS agreement, OOS separation, calibration, data freshness)
- **Expanding-window VaR backtesting** — Per-regime Value-at-Risk with proper out-of-sample exceedance testing
- **Confidence calibration** — Expected Calibration Error (ECE) verifying that reported confidence matches actual accuracy
- **Interactive Plotly dashboard** — Single self-contained HTML file with 7 tabbed panels
- **CLI regime awareness** — Terminal command showing current regime, distribution profile, trust scorecard, and model validation
- **28 automated tests** — Causality guarantees, OOS validation, calibration, VaR backtest, trust scorecard


## Feature Engineering (13 curated indicators)

| Category | Features | Description |
|----------|----------|-------------|
| **Volatility State** | VIX, VRP | Implied vol, vol risk premium (VIX − RV20) |
| **Vol Dynamics** | rv_ratio_10_63, vix_ts_slope | Short/long RV ratio, VIX term structure |
| **Cross-Asset Risk** | SPY_TLT_corr63, credit_stress, hy_spread | Stock-bond correlation, HY flow, credit spread |
| **Macro** | yield_slope | 10Y−2Y yield curve slope |
| **Return Dynamics** | SPY_ret, SPY_skew20 | Daily log return, rolling skewness |
| **Market Structure** | eigen_conc, SPY_dd63 | Eigenvalue concentration, 63d drawdown |
| **Leverage / Fragility** | lev_effect20 | Return-volatility correlation |

Features are log-transformed where right-skewed (VIX, rv_ratio, hy_spread, eigen_conc), then z-score standardized.


## Dashboard

The pipeline outputs a single `figures/dashboard.html` with 7 interactive tabs:

1. **Timeline** — SPY price with regime shading (in-sample + out-of-sample), VIX overlay, market-mode ratio
2. **SV Volatility** — Latent stochastic volatility vs VIX; per-regime SV parameter comparison (φ, σ_η)
3. **KDE Surfaces** — PCA eigenvector loadings, per-regime density contour panels, combined 3D surface
4. **Transitions** — Sankey flow diagram, transition probability matrix heatmap, regime statistics table
5. **Current State** — Live market context panel, probabilistic regime outlook, duration analysis, conditional transition risk
6. **Regime Awareness** — Distribution profile (VaR, CVaR, skew, kurtosis), vol context, model validation checks (Kruskal-Wallis, vol ordering, VaR backtest)
7. **Feature Health** — Correlation heatmap, VIF / skew / kurtosis PASS/FAIL table, PCA loadings, summary scorecard


## Quickstart

### Prerequisites
- Python 3.11+
- [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) (free)

### Setup

```bash
git clone https://github.com/AdamMooo/Regime-Detection.git
cd Regime-Detection

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
FRED_API_KEY=your_api_key_here
```

### Run

```bash
# Full pipeline (collect → features → train)
python run.py

# Individual steps
python run.py collect     # download market data
python run.py features    # build + scale features
python run.py analyze     # feature diagnostics (figures/feature_analysis.html)
python run.py train       # PCA → HDP-HMM → SV → dashboard
python run.py dashboard   # rebuild dashboard from saved model (no retraining)
python run.py regime      # current regime awareness (CLI)
python run.py trust       # standalone trust scorecard
```

The interactive dashboard will be saved to `figures/dashboard.html`.


## Configuration

All parameters are centralized in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `START_DATE` | 2010-01-01 | Data start date |
| `TICKERS` | SPY, QQQ, IWM, EEM, TLT, HYG, GLD | Equity/bond/commodity universe |
| `PCA_ROLLING_WINDOW` | 63 | Rolling PCA window (~1 quarter) |
| `PCA_VAR_THRESHOLD` | 0.90 | Cumulative variance for component selection |
| `USE_HDP` | True | Bayesian HDP-HMM vs classic fixed-K HMM |
| `HDP_TRUNCATION` | 20 | Max states for stick-breaking |
| `HDP_KAPPA` | 10.0 | Sticky self-transition weight |
| `HDP_INFERENCE` | svi | `svi` (fast) or `nuts` (gold-standard) |
| `SVI_NUM_STEPS` | 3000 | Variational inference optimization steps |
| `HDP_MAX_REGIMES` | 6 | Merge down to at most this many regimes |
| `VOL_BRACKETS` | 0-10-18-28% | Absolute vol thresholds for regime naming |
| `MAX_DATA_STALENESS_DAYS` | 3 | Warn if market data is stale |


## Project Structure

```
├── config.py        # All hyperparameters & paths
├── collect.py       # Data download (yfinance + FRED)
├── features.py      # 13-feature engineering + scaling
├── hdp_hmm.py       # Bayesian HDP-HMM (NumPyro/JAX)
├── train.py         # PCA, HMM fitting, SV, GARCH, dashboard
├── signals.py       # Regime awareness & validation metrics
├── trust.py         # Trust scorecard aggregation
├── analyze.py       # Feature diagnostics
├── run.py           # CLI entry point
├── tests/           # 28 automated tests (causality, OOS, calibration, VaR)
├── requirements.txt # Pinned dependencies
├── .env             # FRED API key (git-ignored)
├── data/            # Generated CSVs (git-ignored)
├── models/          # Fitted model artifacts (git-ignored)
└── figures/         # dashboard.html output (git-ignored)
```

## References

- Teh, Y. W., Jordan, M. I., Beal, M. J., & Blei, D. M. (2006). *Hierarchical Dirichlet Processes.* JASA.
- Fox, E. B., Sudderth, E. B., Jordan, M. I., & Willsky, A. S. (2011). *A Sticky HDP-HMM with Application to Speaker Diarization.* Annals of Applied Statistics.
- Harvey, A. C., Ruiz, E., & Shephard, N. (1994). *Multivariate Stochastic Variance Models.* Review of Economic Studies.
- Parkinson, M. (1980). *The Extreme Value Method for Estimating the Variance of the Rate of Return.* Journal of Business.
- Garman, M. B. & Klass, M. J. (1980). *On the Estimation of Security Price Volatilities from Historical Data.* Journal of Business.
- Phan, D., Pradhan, N., & Jankowiak, M. (2019). *Composable Effects for Flexible and Accelerated Probabilistic Programming in NumPyro.*
