# Regime-Detection — Session Notes

## Status
Architecture: stripped HDP-HMM, paper-first
Branch: main
Last updated: 2026-07-21

## Causality Deep-Review (2026-07-20/21) — Fixed, Pending Commit

Deep code review found 5 critical lookahead/correctness bugs (full detail: `.planning/DEEP-REVIEW.md`, untracked). All 5 are now fixed and verified against a clean pipeline run:

- **CR-01** NFCI weekly series was ffill'd on reference date, not release date — 7-day publication-lag shift added (`src/data/collect_macro.py`).
- **CR-02** `HDP_ALPHA`/`HDP_KAPPA` config constants were dead (kappa is Bayesian-learned, not fixed) — removed the dead constants/import.
- **CR-03** Parametric HMM baseline's `get_filtered_states()` used hmmlearn's smoothed (forward-backward) posterior despite claiming causal filtering — replaced with a manual forward-only pass (`src/baselines/parametric_hmm.py`).
- **CR-04** (headline bug) Table 4 vol-target backtest sized positions using full-training-sample realized vol per regime (lookahead). Fixed via `expanding_regime_vol()` in `src/core/inference.py` — causal, point-in-time per-regime vol.
- **CR-05** VIX-rank regime partition could silently drop "High-Vol" if HDP prunes to <3 active states — added `assert K_eff >= 3` stopgap in `run_paper_experiments.py`.

**Table 4 numbers changed after the CR-04 fix** (as expected — removing lookahead should reduce inflated performance):

| | Before (buggy) | After (fixed) |
|---|---|---|
| Vol-Target (HDP) Sharpe | 0.736 | 0.624 |
| Rebalances/yr | 3 | 13 |
| Max DD | — | -29.6% |

Table 1 dwell times also shifted (65.9 / 61.2 / 41.4 days vs previous 82/74/39) — attributable to the CR-01 NFCI feature fix changing what the HDP model learns, not a bug.

**Still open from the review (not yet done):**
- Causality-invariant test (perturb-a-future-value / assert-nothing-before-it-changes) for `expanding_standardize`, `expanding_regime_vol`, `get_filtered_states`, HDP forward pass — recommended as the actual root-cause fix, not yet written.
- `data/processed/*.csv` and `models/*.pkl` are committed/regenerable and bloat git; `.gitignore` doesn't cover them.
- `requirements.txt` has dead deps (`arch`, `plotly`, `pandas_datareader`).
- README.md still describes the old pre-strip-down architecture (separate staleness issue).

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

**Key results (superseded — see "Causality Deep-Review" section above for current numbers):**
- HDP: 8 raw states → 3 regimes, dwell times ~65 / 61 / 41 days
- VIX-threshold dwell: 8–17 days (persistence advantage still holds)
- Backtest Sharpe: HDP 0.624 vs B&H 0.606 vs RV30 0.766
- HDP uses 13 rebalances/yr vs RV30's 90 — lower turnover, but Sharpe no longer leads RV30 (was inflated by the CR-04 lookahead bug)

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
