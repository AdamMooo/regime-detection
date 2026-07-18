# Claude Context — Regime-Detection

**Read NOTES.md first** — it has the current state and next action.

## Purpose

Two goals simultaneously:
1. **Academic paper** — publishable paper proving markets have latent states not recoverable from VIX alone
2. **Practical tool** — regime labels consumed by Algo-Trading-Bot and Portfolio-Manager

Core thesis: *"Markets have latent states not directly observable from any single indicator — a Bayesian HDP-HMM can recover them."*
Null hypothesis: *"Regimes are just VIX thresholds."*

## Architecture (Stripped — Paper-First)

```
src/
  config.py                  — All params: features, HDP, MCMC, VOL_BRACKETS, paths
  data/
    collect_macro.py         — Fetch 4 features: SPY return, VIX, yield slope, NFCI
  core/
    hdp_hmm.py               — Bayesian HDP-HMM (NumPyro): SVI + NUTS, forward-backward
    inference.py             — expanding_standardize() — causal z-score (no lookahead)
    evaluation.py            — evaluate() + block bootstrap CIs
    orchestrator.py          — walk_forward() stub (not yet implemented)
  baselines/
    threshold_rules.py       — VIX-threshold baseline (the null hypothesis)
    parametric_hmm.py        — Fixed-K Gaussian HMM baseline (hmmlearn)
  experiments/
    thesis_experiments.py    — Top-level experiment runner
  pipeline/
    runner.py                — Pipeline runner (timing, error handling)
    stages.py                — Stage functions: collect, features, train_hmm, signals
```

## Features (4 direct, no PCA)

| Feature | Source | Economic meaning |
|---------|--------|-----------------|
| `spy_ret` | yfinance ^GSPC | Market direction (log return) |
| `vol_index` | yfinance ^VIX | Implied volatility level |
| `yield_slope` | FRED T10Y2Y | Macro cycle (10y minus 2y spread) |
| `nfci` | FRED NFCI | Financial stress (Chicago Fed) |

No PCA needed at 4 dimensions — feed directly to HMM. Reviewers cannot argue with it.

## Model

- HDP stick-breaking prior — K learned from data (core contribution)
- Sticky transitions — `pi_k ~ Dir(alpha*beta + kappa*e_k)` — markets are persistent
- Gaussian emissions — cleaner math for the paper than Student-t
- Forward-pass filtering only (causal, no lookahead) — essential for live trading
- Inference: SVI (fast, daily use) or NUTS (full posterior, paper-quality)

## Paper Proof Structure

**Figure 1 (money shot):** Two days with identical VIX but different posterior distributions — model sees something VIX doesn't
**Figure 2:** Within-regime return distributions: HDP-HMM vs VIX-threshold. Tighter violins = more coherent hidden structure
**Figure 3:** Walk-forward OOS stability — states findable in real time, not just hindsight

**Table 1:** Within-regime stats (mean return, vol, Sharpe, dwell time) — HDP-HMM vs VIX-threshold vs buy-and-hold
**Table 2:** Transition matrix — high diagonal = persistent real states
**Table 3:** Information content regression — regime dummies add R² beyond VIX alone (cleanest statistical proof)

## Downstream Integration

Bot label mapping must survive any further changes:
- Low-Vol → `LOW_VOL`
- Moderate-Vol → `MED_VOL`
- High-Vol → `HIGH_VOL`

## Hard Constraints

- NumPyro for HMM — not hmmlearn, pomegranate, etc.
- 4 features, no PCA
- K=3 regimes (target), learned via HDP (actual K may vary)
- Causal inference only — forward-pass filtering, expanding-window standardization
- JAX 0.9.1 and NumPyro 0.20.0 pinned exactly (reproducibility)

## Data Requirements

FRED API key required — add to `.env` as `FRED_API_KEY=<your_key>` (free at fred.stlouisfed.org)

## Do Not

- Add rolling PCA, GARCH VaR, Student-t emissions, or signal combination logic
- Change the 4-feature set without re-running the paper's ablation
- Add complexity that can't be directly cited to a paper section
- Build production execution logic here (that's Algo-Trading-Bot's job)

## Session Close Checklist

- Update NOTES.md with progress + next action
- Commit and push to GitHub
