# Regime-Detection — Session Notes

## Status
Architecture: stripped HDP-HMM, paper-first
Branch: main
Last updated: 2026-05-26

## Paper Status — UPLOAD-READY

`paper_overleaf.zip` (206K) is ready to upload to Overleaf. Contains:
- `paper.tex` (root wrapper) + `paper/paper.tex` (full source, no TODOs)
- `paper/references.bib` (all entries fixed)
- `paper/figures/` — 4 publication-ready PDFs
- `results/paper_macros.tex` — preamble macros
- `results/paper_tables.tex` — Tables 1–5
- `results/paper_desc_stats.tex` — Table 0 (descriptive stats)

Overleaf: set main file to `paper.tex`, hit Compile.

## What's In The Paper

**Figures (4):**
1. `regime_timeline.pdf` — shaded regime bands + SPY cumulative return + VIX panel
2. `vol_violin.pdf` — realized-vol distributions HDP vs VIX-threshold
3. `transition_heatmap.pdf` — 3×3 posterior-mean transition matrix
4. `backtest_equity.pdf` — cumulative returns: B&H / RV30 / HDP (VIX-Thr removed)

**Tables (5):**
- Table 1: Descriptive statistics (4 features)
- Table 2: Within-regime characteristics (HDP vs VIX-Thr vs Param HMM)
- Table 3: HDP transition matrix
- Table 4: Information content regression (R² beyond VIX)
- Table 5: Volatility-targeting backtest (B&H / RV30 / HDP)

**Key results:**
- HDP: 8 raw states → 3 regimes, dwell times 82 / 74 / 39 days
- VIX-threshold dwell: 8–17 days (4× less persistent)
- Backtest Sharpe: HDP 0.736 vs B&H 0.587 vs RV30 0.750
- HDP uses 3 rebalances/yr vs RV30's 90 — same Sharpe at 1/30th turnover

## Current Architecture (Clean)

- 4 features: spy_ret, vol_index, yield_slope, nfci (no PCA, no GARCH, no Student-t)
- HDP-HMM with Gaussian emissions, sticky transitions, K_max=8
- SVI (4000 steps, ~40s on CPU) for paper runs
- NUTS available but not yet run for final paper quality
- Dead code removed (data_download.py, fit_toy_hdp.py, parametric_hmm.py,
  threshold_regimes.py, src/experiments/, src/core/orchestrator.py,
  src/core/evaluation.py, src/pipeline/runner.py)

## Key Files

- `run_paper_experiments.py` — full pipeline: data → HDP → baselines → tables + CSVs
- `scripts/generate_figures.py` — reads regime_labels_train.csv, writes 4 PDFs (~2s)
- `src/config.py` — single source of truth for all params
- `src/core/hdp_hmm.py` — the model
- `src/data/collect_macro.py` — data collection (yfinance + FRED)
- `src/pipeline/stages.py` — collect + features stages
- `.env` — FRED_API_KEY (required, already set)

## Regenerate Everything

```bash
python run_paper_experiments.py        # ~40s — data + model + tables + CSVs
python scripts/generate_figures.py     # ~2s  — figures only (no retraining)
# then rebuild zip:
rm paper_overleaf.zip && zip paper_overleaf.zip paper.tex paper/paper.tex \
  paper/references.bib paper/figures/*.pdf \
  results/paper_macros.tex results/paper_tables.tex results/paper_desc_stats.tex
```

## Next Session — Decided Options

Two directions under consideration for strengthening the paper:

**A) Better presentation (no model changes):**
- Replace Figure 4 equity curve with 3-panel bar chart (Sharpe / MaxDD / Rebalances)
- Add break-even cost analysis: at <0.25bps/trade HDP matches RV30 net of costs
- This makes the efficiency story visual without touching the model

**B) Strengthen the model/evaluation:**
- Walk-forward OOS validation (highest value — turns in-sample into real claims)
- Bootstrap CIs on Sharpe (statistically shows HDP ≈ RV30)
- NUTS full posterior (paper-quality uncertainty quantification)
- Adding features is lowest priority (uncertain payoff, requires re-running ablations)
