---
type: hub
project: regime-detection
---
# Regime Detection

Bayesian HDP-HMM market regime detection. Two goals: (1) an academic paper proving markets have latent states not recoverable from VIX alone, (2) regime labels consumed downstream by Portfolio-Manager. See [[regime-detection/CLAUDE|CLAUDE.md]] for architecture, hard constraints, and downstream label mapping.

## Status

Paper is upload-ready. A deep causality review (2026-07-20/21) found and fixed 5 lookahead/correctness bugs (commit 185ae8d); numbers below are post-fix. Key result: HDP finds 3 regimes with dwell times ~66/61/41 days vs. VIX-threshold's 8-17 days (persistence advantage holds); backtest Sharpe 0.624 (HDP) vs 0.606 (buy-and-hold) vs 0.766 (RV30) at a fraction of RV30's turnover (13 vs 90 rebalances/yr).

Not GSD-managed in the usual sense — `.planning/` holds a codebase snapshot and a planning doc, not `STATE.md`/`ROADMAP.md`.

Walk-forward OOS validation shipped 2026-07-21 (`scripts/run.py walk_forward`) — the model now produces a genuine live regime signal instead of falling back to a VIX-threshold guess. Same-day follow-up found regime assignment is meaningfully sensitive to training-window length (down to 51% agreement between configs on the same days), so the signal is now a 3-window ensemble reporting cross-window agreement (e.g. "Low-Vol, 2/3 windows agree") rather than one model's overstated posterior confidence. See NOTES.md "Training-Window Sensitivity."

A same-day follow-up pivoted the evaluation framework: instead of asking "does vol-targeting beat buy-and-hold" (never actually established), a block-bootstrap significance test now asks "does the regime label carry real information, honestly tested" on the genuinely-OOS ensemble labels. Answer: forward-return information content is statistically significant but tiny (ΔR²=0.00077); forward-*volatility* information content is significant and ~16x larger (ΔR²=0.0124). The defensible claim is that regimes predict future volatility, not direction. Also found and fixed a real bug: in-sample dwell times were smoothed with 3-day hysteresis while OOS labels used raw argmax — part of the earlier "OOS dwell times are half in-sample" finding was just this mismatch. Corrected re-run (commit `8e2d637`): High-Vol dwell nearly doubled (8.0→15.0 days), still below the in-sample claim (41.4 days) but fairer. Today unchanged: Low-Vol, 2/3 windows agree.

## Next

Two undecided directions (see `NOTES.md`):
- **A) Presentation only:** 3-panel bar chart replacing the Figure 4 equity curve, break-even cost analysis (HDP matches RV30 net of costs below 0.25bps/trade).
- **B) Strengthen the model:** walk-forward OOS validation (highest value — turns in-sample results into real claims), bootstrap CIs on Sharpe, full NUTS posterior for paper-quality uncertainty quantification.

## Memory

- **Operations:** [[regime-detection/CLAUDE|CLAUDE.md]] (architecture, hard constraints, downstream label mapping)
- **Notes:** [[regime-detection/NOTES|NOTES.md]] (session-to-session state, read first)
- **Public docs:** [[regime-detection/README|README]]

## Known Issues

- **Regime assignment is sensitive to training-window length** (2026-07-21) — expanding vs. rolling-5y vs. rolling-3y windows agree on the label only 51-69% of the time, even when each individually reports >99% confidence. `data/oos_regime_labels.csv` is now a 3-window ensemble (majority vote + agreement_frac) rather than one overconfident number, but the in-sample paper Table 1/2/4 numbers still use only the original single (full-history) window — this sensitivity almost certainly applies there too, not yet addressed.
- **Two regime-labeling schemes coexist with no test enforcing agreement**: `label_regimes_hdp()` (absolute VOL_BRACKETS, used by `stage_train_hmm`) vs. `merge_states_to_regimes()` (VIX-rank thirds, used by the paper/walk-forward path). Each has a real tradeoff; cross-referenced in both docstrings but not unified — open decision.
- `data/processed/*.csv` / `models/*.pkl` are committed/regenerable (git bloat); `requirements.txt` has dead deps (`arch`, `plotly`, `pandas_datareader`) — cheap cleanup, not done.
- `CLAUDE.md`/`README.md` still describe deleted modules (`orchestrator.py`, old `evaluation.py`) and call walk-forward "a stub" — stale, not yet updated.
- `.github/workflows/tests.yml` references test/analysis files deleted in the May 2026 refactor — CI may be silently broken or not testing what it claims to.
