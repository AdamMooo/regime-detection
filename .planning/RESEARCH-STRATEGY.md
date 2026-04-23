# Research Strategy — Regime-Detection → Alpha & Trading Extensions
**Last updated:** 2026-04-21  
**Based on:** Full codebase audit (senior quant researcher + auditor analysis)  
**Status:** Reference document — consult before adding any new model layer

---

## 0. Honest Baseline Assessment

Before planning any extensions, record what the HMM actually achieves:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Walk-forward OOS accuracy | 35–37% | 2–4pp above random (3-class baseline = 33.3%) |
| OOS / IS agreement | 70–75% | Regime persistence, not overfitting |
| ECE calibration | <5% | Well-calibrated filtered probabilities |
| Median regime dwell | 17.7 days | Slow signal — not a day-trading tool |
| GARCH-VaR Kupiec p | 0.952 | Correct coverage — production-grade risk model |
| Christoffersen p | 0.547 | No exceedance clustering — independence holds |

**Verdict:** The HMM is a solid **regime filter and risk overlay**. It is not validated as an alpha engine. The 35–37% OOS accuracy means any downstream strategy claim must demonstrate incremental value over a naive VIX-threshold regime. No alpha extensions are justified until a backtesting layer exists.

---

## 1. What the HMM Currently Does (Mathematically)

### Observations
14-feature vector → rolling PCA (63-day window, Procrustes-aligned, causal) → 3–5 PCs + VIX appended directly (`VIX_BYPASS=True`)

### Hidden states
K=3 hard-coded: **Low-Vol / Moderate / High-Vol**, labeled by realized-vol brackets on training SPY returns. Economically: risk-on quiet, transition/chop, risk-off/stress.

### Inference
- **SVI (production):** Variational approximation, ~3,000 steps, ~5 min/fold, well-calibrated
- **Forward algorithm only:** `filtered_probs()` = causal, no backward pass, no smoothing
- **Hysteresis:** `filtered_labels(hold_days=1)` suppresses whipsaw switches

### What it outputs today
- `regime_results.csv` — daily regime label + filtered probabilities + GARCH VaR
- `signals.py` — current regime, confidence, days in regime, transition context
- `trust.py` — 8-check PASS/WARN/FAIL scorecard

### What is missing (critical gaps)
- No backtesting framework (zero PnL simulation)
- No signal IC / alpha decay measurement
- No signal-to-position conversion layer
- No experiment tracking (runs overwrite each other)
- No strategy-level Sharpe, drawdown, Calmar comparison

---

## 2. Candidate Model Extensions

### Candidate 1 — Regime-Probability-Weighted GARCH Vol Forecast
**Category:** Risk overlay / vol forecasting  
**Priority: 9/10**

**Mathematical idea:**  
Blend per-regime GARCH forecasts using filtered state probabilities as weights:
```
σ²_t = Σ_k  P(Z_t = k | x_{1:t})  ·  σ²_{k,t}
```
where `σ²_{k,t}` comes from each regime's GARCH(1,1). This is a Mixture-of-GARCHs forecaster with Bayesian-filtered weights.

**Economic mechanism:** A single GARCH underestimates vol during transitions — it is slow to update. The mixture weights regimes by current posterior, reflecting uncertainty (e.g., 60% Low-Vol / 40% Moderate → blended forecast, not a hard switch).

**Why it fits:** All pieces exist — GARCH per regime in `var_backtesting.py` + `hmm_training.py`, filtered probs in `inference.py`. ~50 lines to wire together.

**Why it might fail:** Regimes are defined by vol level, not vol dynamics. A plain GARCH on all data might match performance. Must test this as the null.

**Minimum viable experiment:**  
- Rolling 63-day OOS forecast comparison: regime-weighted GARCH vs. single GARCH vs. EWMA
- Metric: QLIKE loss, MSE vs. RV10, Mincer-Zarnowitz R²

**Complexity:** Low  
**Data required:** None beyond what exists

---

### Candidate 2 — Regime-Conditioned Strategy Backtest (Tactical Allocation)
**Category:** Risk overlay / portfolio layer  
**Priority: 8/10**

**Mathematical idea:**  
Use regime labels to condition exposure. Simplest form:
- High-Vol regime → reduce SPY to 50%, add TLT
- Low-Vol regime → full SPY or slight leverage
- Moderate → neutral

Scale by GARCH-VaR forecast for position sizing. Apply 1-day execution lag and realistic costs (5–10bp round-trip).

**Economic mechanism:** Not alpha — risk reduction. Avoid large drawdowns by de-risking during High-Vol states. Sharpe improvement comes through better denominator (lower vol and drawdown), not higher returns.

**Why it fits:** `forward_returns.py` already computes forward returns for SPY/TLT/HYG/EEM. The Kruskal-Wallis test already shows regime-conditional return separation. `signals.py` already outputs current regime + confidence. This is the natural next use of what exists.

**Why it might fail:** HMM transitions lag by ~17.7 days median — a High-Vol signal may arrive after the drawdown has already started. Need to measure cost of latency explicitly. Vol-targeting creates implicit short-vol bias during fast expansions.

**Minimum viable experiment:**  
- Walk-forward strategy sim (reuse `orchestrator.py` loop)
- SPY buy-and-hold vs. regime-conditioned tactical allocation
- Report: Sharpe, Calmar, max drawdown, hit rate on High-Vol exits
- Cost model: 5bp round-trip, 1-day lag

**Complexity:** Low-Medium  
**Data required:** None beyond what exists (SPY, TLT already collected)

---

### Candidate 3 — Regime-Transition Early Warning Model
**Category:** Transition prediction model  
**Priority: 6/10**

**Mathematical idea:**  
Train a regularized logistic regression to predict `P(regime change within h days)` using:
- Current filtered regime probabilities (3 values)
- Days already spent in current regime
- VIX level + vix_ts_slope
- credit_stress, NFCI, yield_curve_slope
- SPY_TLT_corr63, eigen_conc

Target labels: binary transition events derived from walk-forward OOS `regime_results.csv`.

The HMM transition matrix is stationary — it does not condition on current structural features. A classifier can capture non-stationary dynamics the HMM misses.

**Economic mechanism:** Regime transitions drive almost all large PnL swings. Being 5 days early on a High-Vol entry or exit dramatically improves the risk profile of any regime-conditioned strategy. Even marginal improvement in timing — reducing average lag from 17.7 to 15 days — has compounding PnL impact.

**Why it might fail:**  
- Transitions are rare (~20–30 per year). Severe class imbalance.
- With ~3,500 days of history, training set for transition events is ~70–90 samples.
- Overfitting risk is severe. Any nonlinear model will memorize.
- Null baseline is tough: the HMM transition matrix already captures first-order Markov dynamics.

**Minimum viable experiment:**  
- Logistic regression only (no trees, no neural nets)
- Walk-forward cross-validation (not train/test split)
- Evaluate: Brier score, AUC-ROC, precision-recall — NOT accuracy
- Compare strictly to naive baseline = HMM transition matrix row
- Stop immediately if logistic does not beat naive baseline OOS

**Complexity:** Medium  
**Data required:** Transition labels from existing walk-forward results

---

### Candidate 4 — Cross-Asset Relative Value (Correlation Dislocation)
**Category:** Statistical arbitrage  
**Priority: 5/10**

**Mathematical idea:**  
Within each regime, estimate the expected SPY-TLT (and other cross-asset) correlation. Detect when realized short-window correlation deviates significantly from the regime-conditional mean. Test whether those deviations predict reversion.

```
residual_t = corr_realized(t, window=10) - E[corr | Z_t = k]
```

High positive residual in Low-Vol → correlation anomalously high → potential reversion to lower correlation.

**Why it fits:** `SPY_TLT_corr63` is already a feature. `eigen_conc` is already computed. SPY, TLT, HYG, EEM, GLD are all collected. `forward_returns.py` already has cross-asset return analysis.

**Why it might fail:**  
- Correlation dislocations at daily frequency revert fast — likely not capturable after costs.
- "Anomalously low correlation" may simply be a transition to new regime, not a reversion signal.
- Need to cleanly separate "dislocation within stable regime" from "regime is breaking down."

**Minimum viable experiment:**  
- Compute 10-day rolling SPY-TLT correlation residual vs. regime-conditional mean
- Test: does extreme residual predict positive 5-day return to long-vol / short-beta spread?
- Metric: IC, t-stat, Sharpe after 5bp round-trip
- If t-stat < 2.0 OOS → stop

**Complexity:** Medium  
**Data required:** None beyond what exists

---

### Candidate 5 — Visibility-Graph Structural Anomaly Layer
**Category:** Anomaly detection  
**Priority: 4/10**

**Mathematical idea:**  
Convert rolling 21-day return windows to visibility graphs (ts2vg). Extract degree entropy, clustering, assortativity, edge density, directed asymmetry. Estimate regime-conditional mean and covariance:
```
μ_k = E[X_t | Z_t = k],   Σ_k = Cov(X_t | Z_t = k)
```
Define structural anomaly score:
```
A_t = (X_t - μ_k)ᵀ Σ_k⁻¹ (X_t - μ_k),   where k = current regime
```
Test whether high `A_t` during a stable regime predicts either (a) imminent transition, or (b) cross-asset residual reversion.

**Why it fits:** Rolling return series already exist. Regime labels exist. Transition event labels available from walk-forward. This is a direct extension of the current architecture.

**Why it might fail:**  
- With 21-node graphs from daily returns, degree distributions are too coarse to distinguish states reliably.
- VIX + NFCI + credit_stress + eigen_conc already capture most structural stress information.
- Marginal value over existing features is probably near zero.
- Graph statistics at daily frequency are extremely noisy.

**Verdict:** Do not build until Candidates 1–3 are validated OOS. Only justified if there is a specific residual pattern that existing features miss.

**Complexity:** Medium  
**Data required:** None beyond what exists (but ts2vg library needed)

---

### Candidate 6 — Factor Residual Statistical Arbitrage
**Category:** Statistical arbitrage / cross-sectional  
**Priority: 2/10**

**Why not now:** Requires individual stock data, a factor model (Fama-French or PCA-based), and cross-sectional infrastructure. None of this exists in the current pipeline. TICKERS in config.py are ETFs and indices, not individual stocks. This is a parallel 6-month project, not an extension.

**Verdict:** Do not build. Revisit only if the project explicitly expands to stock-level universe.

---

## 3. Ranking Table

| Candidate | Economic Rationale | Impl Effort | Robustness | Data Hunger | Alpha Durability | Repo Compat |
|-----------|-------------------|-------------|------------|-------------|-----------------|-------------|
| 1. Regime-weighted GARCH vol | Strong — direct risk pricing | Very low | High | None | High (structural) | 10/10 |
| 2. Regime tactical backtest | Strong — risk reduction | Low | High | None | High (structural) | 10/10 |
| 3. Transition predictor | Moderate — timing | Medium | Medium | Low | Moderate | 7/10 |
| 4. Cross-asset rel-val | Moderate — dislocation | Medium | Medium | None | Low-moderate | 6/10 |
| 5. Visibility-graph anomaly | Speculative — structural | Medium | Low | None extra | Low (noisy) | 5/10 |
| 6. Factor residual stat arb | Strong in theory | Very high | High | **Missing** | High | 1/10 |

---

## 4. Final Recommendation — Top 3 Paths

### Path 1 (Safest / Highest Legitimacy): Regime-Weighted GARCH Vol Forecasting

**What:** Extend per-regime GARCH models into a single blended vol forecast using filtered state probabilities as weights. Feed into VaR engine and downstream position sizing.

**Why first:** All pieces exist. ~50 lines. Directly improves risk model. No alpha claim required. Mathematically principled (proper Bayesian model average over vol forecasts).

**Done when:** QLIKE and MSE vs. RV10 show regime-weighted GARCH beats single GARCH OOS over rolling 63-day windows.

**Files to touch:** `var_backtesting.py`, `hmm_training.py` (new blending function), `signals.py` (expose blended forecast)

---

### Path 2 (Medium Complexity, Critical Gap): Regime-Conditioned Strategy Backtester

**What:** Build a minimal walk-forward strategy simulation. Test regime-conditioned tactical SPY/TLT allocation vs. buy-and-hold. Realistic costs (5–10bp, 1-day lag).

**Why second:** The biggest gap in this codebase is no PnL simulation. You cannot justify any further modeling until you know whether following the regime signal makes money. `forward_returns.py` gives raw material; this turns it into a strategy validator.

**Done when:** Honest Sharpe, Calmar, and max drawdown comparison exists between regime-conditioned allocation and buy-and-hold, with costs, OOS only.

**Files to touch:** New `src/backtest/strategy.py`, reuse `orchestrator.py` walk-forward loop, reuse `forward_returns.py` return data

---

### Path 3 (Ambitious Research): Regime-Transition Early Warning

**What:** Regularized logistic regression to predict `P(transition within 5–10 days)` from current features and regime context. Target labels from existing walk-forward results.

**Why third:** Regime transition timing is where economic value is concentrated. If you can improve average exit lag from 17.7 days to 15 days, the compounding PnL impact is real. But this is only worth building if Path 2 shows that timing is the binding constraint on strategy performance.

**Done when:** Brier score beats naive HMM transition matrix baseline OOS, in walk-forward cross-validation. If it does not → stop.

**Files to touch:** New `src/signals/transition_predictor.py`, uses `regime_results.csv` for labels, uses `features_transformed.csv` as inputs

---

## 5. Blockers — What is Missing Before Research Can Start

| Blocker | Impact | When to Fix |
|---------|--------|-------------|
| No backtesting framework | Cannot validate any strategy claim | Path 2 |
| No signal IC / alpha evaluation layer | Cannot measure incremental signal value | Before Path 3 |
| No signal-to-position module | Cannot convert regime probs to weights | Path 2 |
| No experiment tracking | Results overwrite on each run | Before Path 3 |
| `train.py` 1,000+ lines (monolithic) | Research extensions create circular deps | Phase 7 pipeline cleanup |
| `signals.py` mixes diagnosis + state | Hard to backtest cleanly | Path 2 refactor |

---

## 6. What NOT to Build Yet

- **Visibility graphs / TDA:** Existing features (VIX, NFCI, eigen_conc, SPY_TLT_corr63) already capture most of this. No evidence of residual gap yet. Do not build until Paths 1–2 are validated and something specific is missing.
- **Deep learning / neural anything:** Data is ~3,500 trading days, 14 features. Too parameter-rich for the signal available.
- **Persistent homology as alpha:** No mechanism. At best a stress indicator redundant with VIX + credit_stress.
- **Factor residual stat arb:** Missing stock-level data infrastructure entirely.
- **Diffusion on graphs:** Elegant math, weak identification at daily frequency.

---

## 7. Existing Modules That Can Be Reused

| Module | What it gives the research layer |
|--------|----------------------------------|
| `var_backtesting.py` | Per-regime GARCH → extend to vol forecast mixer |
| `forward_returns.py` | Forward return data → extend to IC / signal evaluation |
| `orchestrator.py` | Walk-forward engine → reuse for strategy backtesting loop |
| `inference.py` | `filtered_probs()` + `expanding_standardize()` → causal inputs to any downstream model |
| `signals.py` | Regime context → extend with transition predictor output |
| `trust.py` | Scorecard framework → extend with new signal quality checks |

---

## 8. Precise Build Sequence

```
Phase 7  (operational)
  → Daily pipeline, sub-10-min, cron-ready
  → Modularize train.py (pipeline class with discrete stages)
  → Prerequisite for all research phases

Phase 8  (optimization)
  → HDP-HMM inference speed (joblib, ELBO early stopping)
  → Enables faster walk-forward iteration for research

Phase 9  (research — Path 1)
  → Regime-weighted GARCH vol forecast
  → Extend var_backtesting.py + hmm_training.py
  → Validate: QLIKE vs. single-GARCH OOS
  → Gate: if no improvement → vol model is already good enough

Phase 10  (research — Path 2, CRITICAL)
  → Minimal walk-forward strategy backtester
  → Regime-conditioned SPY/TLT tactical allocation
  → Costs: 5–10bp, 1-day lag
  → Honest Sharpe / Calmar / max DD vs. buy-and-hold
  → Gate: if no edge → HMM is a risk tool only, not a strategy driver
         if edge exists → document and move to Path 3

Phase 11  (research — Path 3, conditional on Phase 10 result)
  → Transition early-warning logistic model
  → Only if Phase 10 shows timing is the binding constraint
  → Walk-forward CV, Brier score, compare vs. HMM transition matrix baseline
  → Gate: if Brier does not beat naive baseline → stop

Phase 12+  (only with evidence from Phase 11)
  → Cross-asset relative value (Candidate 4)
  → Visibility-graph structural anomaly (Candidate 5)
  → Only with a specific, falsifiable hypothesis
```

---

## 9. Evaluation Standards (Non-Negotiable)

Any new model layer must pass these before being considered production-ready:

1. **Baseline comparison:** Must beat a naive vol-threshold regime (VIX > 20 = High-Vol) on the same metric. If it cannot beat VIX thresholding, it is not useful.
2. **Walk-forward OOS only:** No in-sample metrics. No train/test split. Walk-forward with same fold structure as existing orchestrator.
3. **Cost adjustment:** All strategy metrics after realistic costs (5–10bp round-trip, 1-day lag minimum).
4. **Incremental test:** New layer vs. existing layer. If adding graph features, the test is: does IC or Sharpe improve over the HMM-only version?
5. **Stability test:** Roll parameters forward 6 months without refit. Check whether performance degrades gracefully.
6. **Ablation:** For any composite model, test each component separately. Know where the edge comes from.

---

## 10. Key Distinctions to Keep Clear

| Term | What it means in this codebase | Do not confuse with |
|------|--------------------------------|---------------------|
| Regime filter | Conditions downstream estimates | Alpha signal |
| Filtered probabilities | `P(Z_t = k \| x_{1:t})` — causal | Smoothed probs (use backward pass, not valid live) |
| Anomaly score | Distance from regime-typical structure | Trading signal (anomaly ≠ edge) |
| Vol forecast | Predicted realized vol | Return forecast |
| Transition prediction | `P(state change in h days)` | Directional return prediction |
| Risk overlay | Position sizing / exposure scaling | Alpha generation |
| Statistical arbitrage | Convergence of a spread with defined payoff | Generic long/short on a signal |

---

*This document should be updated after each research phase completes with: what was tested, what the OOS result was, and whether the gate was passed.*
