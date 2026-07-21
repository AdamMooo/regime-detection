---
type: hub
project: regime-detection
---
# Regime Detection

Bayesian HDP-HMM market regime detection. Two goals: (1) an academic paper proving markets have latent states not recoverable from VIX alone, (2) regime labels consumed downstream by Portfolio-Manager. See [[regime-detection/CLAUDE|CLAUDE.md]] for architecture, hard constraints, and downstream label mapping.

## Status

Paper is upload-ready. A deep causality review (2026-07-20/21) found and fixed 5 lookahead/correctness bugs (commit 185ae8d); numbers below are post-fix. Key result: HDP finds 3 regimes with dwell times ~66/61/41 days vs. VIX-threshold's 8-17 days (persistence advantage holds); backtest Sharpe 0.624 (HDP) vs 0.606 (buy-and-hold) vs 0.766 (RV30) at a fraction of RV30's turnover (13 vs 90 rebalances/yr).

Not GSD-managed in the usual sense — `.planning/` holds a codebase snapshot and a planning doc, not `STATE.md`/`ROADMAP.md`.

## Next

Two undecided directions (see `NOTES.md`):
- **A) Presentation only:** 3-panel bar chart replacing the Figure 4 equity curve, break-even cost analysis (HDP matches RV30 net of costs below 0.25bps/trade).
- **B) Strengthen the model:** walk-forward OOS validation (highest value — turns in-sample results into real claims), bootstrap CIs on Sharpe, full NUTS posterior for paper-quality uncertainty quantification.

## Memory

- **Operations:** [[regime-detection/CLAUDE|CLAUDE.md]] (architecture, hard constraints, downstream label mapping)
- **Notes:** [[regime-detection/NOTES|NOTES.md]] (session-to-session state, read first)
- **Public docs:** [[regime-detection/README|README]]

## Known Issues

- No walk-forward OOS validation yet — all current results are in-sample; treat backtest Sharpe as provisional until direction B lands.
- `data/processed/*.csv` / `models/*.pkl` are committed/regenerable (git bloat); `requirements.txt` has dead deps (`arch`, `plotly`, `pandas_datareader`) — cheap cleanup, not done.
