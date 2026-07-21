# Regime-Detection — Session Notes

## Status
Architecture: stripped HDP-HMM, paper-first
Branch: main
Last updated: 2026-07-21

## Causality Deep-Review (2026-07-20/21) — Fixed and Committed (185ae8d)

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
- `data/processed/*.csv` and `models/*.pkl` are committed/regenerable and bloat git; `.gitignore` doesn't cover them.
- `requirements.txt` has dead deps (`arch`, `plotly`, `pandas_datareader`).

**2026-07-21 (later):** Added `tests/test_causality_invariants.py` — perturb-a-future-value / assert-nothing-before-it-changes checks for the 4 functions claiming causality (`expanding_standardize`, `expanding_regime_vol`, `get_filtered_states`, HDP `forward_backward_numpy`'s filtered output). Includes a negative control (smoothed output *does* change before t) proving the perturbation is large enough to matter. Verified the `expanding_regime_vol` test fails against the pre-fix buggy version (fold-before-compute) — the test has teeth, not just vacuously passing. Run with `pytest tests/ -v`.

**2026-07-21 merge:** `origin/main` had diverged with a same-day-earlier commit (`70849ae`, pushed from a different machine before this deep-review session) adding `scripts/run.py` (CLI wrapper for collect/features/train/signals/dashboard/regime/trust/analyze, with cached-artifact fallback) + `tests/test_cli_runner.py` + a README.md rewrite. Non-overlapping with the causality fixes — merged clean (`8dc349c`), both new tests pass. README staleness is now resolved.

## Walk-Forward OOS Validation — Implemented (2026-07-21, commit d4f4872)

`stage_walk_forward` was a no-op stub — the model had never actually been scored on anything after `TRAIN_END` (2023-12-31), meaning `scripts/run.py regime` was silently falling back to a live VIX-threshold guess (the null hypothesis this whole project argues against). Implemented properly: `src/core/walk_forward.py` refits the HDP-HMM quarterly (63 trading days, `config.WALK_FORWARD_REFIT_DAYS`) on an expanding window, forward-filters (never smooths) each new block, then folds it into the training window before the next refit. Run via `scripts/run.py walk_forward` or `--validate`; writes `data/oos_regime_labels.csv`.

**First real OOS run, 2024-01-02 → 2026-07-21 (11 folds):**
- **Today (2026-07-21) is genuinely Low-Vol at 99.99% posterior confidence** — the first real (non-VIX-threshold) live signal this project has ever produced.
- Mean confidence across all 635 OOS days: 96.5%; 26 days (4%) below 0.7 (real uncertainty on transition days, not degenerate always-100%-confident output).
- Distribution: Moderate-Vol 55.3%, Low-Vol 38.4%, High-Vol 6.3% — notably different mix than the in-sample training period (50/40/10).
- **Dwell times OOS (30.5 / 35.1 / 8.0 days) are much shorter than the in-sample claim (65.9 / 61.2 / 41.4 days)** — the "persistence advantage over VIX-threshold" story holds much less dramatically out-of-sample; High-Vol dwell (8.0 days) is right at the VIX-threshold baseline's range. Not yet root-caused: could be genuine 2024-2026 market character, or partial refit-boundary instability (fold-boundary check showed 7/10 boundaries label-stable, so not fully explained by that alone).
- **OOS vol-target(HDP) backtest Sharpe (1.062) slightly trails buy-and-hold (1.098)** over this period — the modest in-sample edge (0.624 vs 0.606) does not clearly replicate OOS. Both OOS Sharpes are much higher than in-sample simply because 2024-2026 was a strong bull run overall — only the HDP-vs-B&H *relative* comparison is meaningful here.

These are reported as-is, not smoothed over — exactly the kind of honest OOS grounding the paper needs. Next: investigate the dwell-time shrinkage (refit-artifact vs real) and whether the backtest edge is period-specific.

## Training-Window Sensitivity — Discovered and Addressed (2026-07-21, commit 8b06545)

Investigating the dwell-time shrinkage above turned up something bigger. Compared three training-window configurations for the same 635 OOS days (2024-01-02 → 2026-07-21): **expanding** (full history since 2015, the original design), **rolling 5-year** (1260 trading days), **rolling 3-year** (756 trading days).

**Pairwise agreement on the regime label:**
| | Expanding | Rolling 5y |
|---|---|---|
| Rolling 5y | 68.8% | — |
| Rolling 3y | 51.2% | 67.2% |

That's a **smooth gradient, not a threshold** — adjacent choices (5y vs 3y) disagree almost as much as the extremes (32.8% vs 31.2%/48.8%), which rules out "it's just about whether COVID is in the window." It's a pervasive sensitivity to training-window length, likely compounded by (a) genuine SVI estimation noise with less data per state, and (b) the coarse "sort states by mean VIX, chop into thirds by index" merge heuristic being brittle to small shifts in state ordering.

**The important part: even on days where BOTH configs independently reported >99% posterior confidence, they disagreed 22% of the time** (88/394 such days). A single model's `filt_prob_max` only measures uncertainty *within* one fixed training-window choice — it says nothing about uncertainty *about* that choice, which this shows is large. Today's own classification wasn't even unanimous: expanding and 5y both said Low-Vol (99.99%/99.8% confidence), but 3y said **Moderate-Vol at 98.8% confidence** — a different regime, stated with comparable certainty.

**Fix shipped:** `data/oos_regime_labels.csv` is now an ensemble of `config.WALK_FORWARD_WINDOW_DAYS = [expanding, 5y, 3y]` (see `ensemble_oos()` in `src/core/walk_forward.py`) — majority vote + `agreement_frac` as the real confidence measure, replacing any single window's overstated posterior. `scripts/run.py regime`/`trust` now report cross-window agreement (e.g. "Low-Vol, 2/3 windows agree, 67% confidence") instead of a single model's 99%+ number. Cost: `stage_walk_forward` now runs 3 window configs (~24 min total, up from ~8).

**Not yet done:** this same sensitivity almost certainly affects the in-sample paper Table 1/2/4 numbers too (only one training-window choice — full history — has ever been used there). Whether/how to report this as an explicit robustness section in the paper is still open. Raw per-config runs kept for reproducibility: `data/oos_regime_labels_rolling5y.csv`, `data/oos_regime_labels_rolling3y.csv`.

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
