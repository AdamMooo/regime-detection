---
type: hub
project: regime-detection
---
# Regime Detection

Market regime detection under prereg/causal discipline. **v1** (HDP-HMM + four successor
formulations): five preregistered nulls, CONVERGED, sealed at git tag `v1-convergence` — durable
narrative in `RESEARCH-RECORD.md`. **v2** (statistical jump model, the field-standard estimator,
on Ken French daily data 1926+): chapter 1 closed 2026-07-23 with a preregistered one-look
backtest.

## Status

**2026-07-23 — Chapters 1 AND 2 CLOSED same day; program direction decided: the paper.**
Chapter 1 (Case B): the "regime switching beats buy-and-hold" claim is an exposure artifact
(fee +488 bps inside every null band); **vol targeting dominates the overlay** (−256 bps, CI
excl. 0). Chapter 2 (NULL, prereg Rev 2.1 after same-day outside audit + synthetic smoke):
state-conditional covariance in a multi-asset ERC adds +2.8 bps vs its unconditional twin
(inside all bands) and **loses −29 bps to a plain EWMA-covariance twin** — the v1 chapter-3
lesson, preregistered. Program lesson: reactive estimators win daily-horizon lag races.
**The label itself remains the asset**: 100.0% stability (±2y shifts), live to today via
SPY splice (CALM since 2026-04-23). Visual: `results/report.html` (rehauled as a living
program report: status tiles, claims-vs-honest-bar ladder, sensor section, fork).

## Next

**Write the paper** — `paper/OUTLINE.md` (skeleton with real numbers, figure plan, venue
path; decision 2026-07-23). Parallel: sensor-track instrument work (λ frontier, asymmetric
penalties, calibrated P(state)). Chapter 3 (momentum at monthly cadence vs Barroso–Santa-Clara
vol-scaling) is gated: prereg before any data touch, only if another look is worth spending.

## Memory

- **Operations:** [[regime-detection/CLAUDE|CLAUDE.md]] (file map, live-vs-frozen, discipline)
- **Notes:** [[regime-detection/NOTES|NOTES.md]] (session state, read first)
- **Research narrative:** [[regime-detection/RESEARCH-RECORD|RESEARCH-RECORD.md]] (newest-first)

## Known Issues

- French data publishes with a 1–2 month lag → the jump-model label is not yet live-capable
  (SPY-splice tail is Track 1 work).
- HDP pipeline fully retired 2026-07-23 (its label was never consumed by anything — the
  Portfolio-Manager integration was only an idea in notes). Recoverable in git history if ever
  needed.
