# Regime Detection

**Bayesian HDP-HMM Market Regime Detection with Stochastic Volatility**

A quantitative research pipeline that automatically discovers market regimes using a Hierarchical Dirichlet Process Hidden Markov Model (HDP-HMM) with sticky transitions and Student-t emissions. The system extracts 39 engineered features from multi-asset market data, applies rolling PCA for dimensionality reduction, fits a Bayesian nonparametric regime model via variational inference, and estimates regime-dependent stochastic volatility dynamics.

---

## Pipeline Architecture

```
collect.py          features.py           train.py              train.py
┌──────────┐       ┌──────────────┐      ┌───────────────┐     ┌──────────────┐
│  Yahoo   │──────>│ 39 Features  │─────>│  Rolling PCA  │────>│  HDP-HMM     │
│  Finance │       │  Engineering │      │  (Procrustes  │     │  (NumPyro    │
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
- **Sticky transitions** — Dirichlet-weighted self-transition bias prevents spurious regime switching
- **Student-t emissions** — Heavy-tailed observation model captures market fat tails
- **39 engineered features** spanning volatility surfaces, yield curve dynamics, cross-asset correlations, liquidity stress, and stochastic volatility inputs
- **Rolling PCA with Procrustes alignment** — Dimensionality reduction that maintains temporal consistency across windows
- **VIX bypass** — Scaled VIX appended directly to PCs to prevent information loss in PCA compression
- **Regime-dependent stochastic volatility** — Linearized SV (Harvey 1994) and GARCH(1,1) per regime
- **Walk-forward validation** — Out-of-sample regime prediction with configurable rolling/expanding windows
- **95% VaR backtesting** — Per-regime Value-at-Risk with exceedance ratio evaluation
- **Interactive Plotly dashboard** — Single self-contained HTML file with 5 tabbed panels


## Feature Engineering (39 indicators)

| Category | Features |
|----------|----------|
| **Daily Returns** | SPY, QQQ, IWM, EEM, TLT, HYG, GLD log returns |
| **Realized Volatility** | 10d, 20d, 63d rolling std; Parkinson; Garman-Klass; RV ratio |
| **Implied Volatility** | VIX, VVIX, VVIX/VIX ratio, VIX term structure slope, VRP |
| **Yield Curve / Macro** | 10Y-2Y slope, slope change, HY spread, TED spread |
| **Cross-Asset** | Credit stress, SPY-TLT correlation, IWM/SPY relative, gold flow, EM-DM spread, dispersion, eigenvalue concentration |
| **Return Dynamics** | Rolling skewness, first-order autocorrelation |
| **Liquidity** | Relative volume, volume-adjusted returns |
| **SV-Specific** | Lagged RV (5d, 10d), vol-of-vol, leverage effect proxy |


## Dashboard

The pipeline outputs a single `figures/dashboard.html` with 5 interactive tabs:

1. **Timeline** — SPY price with regime shading (in-sample + out-of-sample), VIX overlay, market-mode ratio
2. **SV Volatility** — Latent stochastic volatility vs VIX; per-regime SV parameter comparison (φ, σ_η)
3. **KDE Surfaces** — PCA eigenvector loadings heatmap, per-regime density contour panels, combined 3D surface
4. **Transitions** — Sankey flow diagram, transition probability matrix heatmap, regime statistics table
5. **Current State** — Live market context panel, probabilistic regime outlook, duration analysis, transition risk assessment


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
python run.py analyze     # feature diagnostics
python run.py train       # PCA → HDP-HMM → SV → dashboard
```

The interactive dashboard will be saved to `figures/dashboard.html`.


## Configuration

All parameters are centralized in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `START_DATE` | 2010-01-01 | Data start date |
| `TICKERS` | SPY, QQQ, IWM, EEM, TLT, HYG, GLD | Equity/bond/commodity universe |
| `PCA_ROLLING_WINDOW` | 63 | Rolling PCA window (~1 quarter) |
| `PCA_VAR_THRESHOLD` | 0.85 | Cumulative variance for component selection |
| `VIX_BYPASS` | True | Append VIX directly to PCs |
| `USE_HDP` | True | Bayesian HDP-HMM vs classic fixed-K HMM |
| `HDP_TRUNCATION` | 10 | Max states for stick-breaking |
| `HDP_KAPPA` | 10.0 | Sticky self-transition weight |
| `HDP_INFERENCE` | svi | `svi` (fast) or `nuts` (gold-standard) |
| `SVI_NUM_STEPS` | 3000 | Variational inference optimization steps |
| `HDP_MAX_REGIMES` | 6 | Merge down to at most this many regimes |


## Project Structure

```
├── config.py        # All hyperparameters & paths
├── collect.py       # Data download (yfinance + FRED)
├── features.py      # 39-feature engineering + scaling
├── hdp_hmm.py       # Bayesian HDP-HMM (NumPyro/JAX)
├── train.py         # PCA, HMM fitting, SV, GARCH, dashboard
├── analyze.py       # Feature diagnostics
├── run.py           # CLI entry point
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


## License

MIT
