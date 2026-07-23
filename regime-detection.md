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

**2026-07-23 — Chapter 1 CLOSED (Case B) + repo cleaned/renamed for the new era.**
The literature's "regime switching beats buy-and-hold" claim deflates to an exposure artifact
(fee +488 bps but inside every pre-declared null band; an exposure-matched static mix beats the
overlay); **vol targeting dominates the overlay significantly** (fee −256 bps, CI excludes 0) —
the v1 "vol absorbs everything" conclusion now has a mechanism: a detection-lag race that even a
perfect detector loses. **The label itself is an exceptional instrument**: 100.0% stability under
±2y training-window shifts (v1 ensemble: 80.9%), 1.66 switches/yr. Direction: instrument-first.
Visual results: `results/report.html`. Working code renamed (no more v2_ prefixes); ~40 v1-era
files deleted (recoverable at the tag).

## Next

Track 1 — prove the sensor: benchmark bear calls vs ex-post bull/bear datings
(Pagan–Sossounov / Lunde–Timmermann), characterize the states, build the SPY-splice live tail.
Then: λ speed/stability frontier (Track 2) and the state-conditional asset menu (Phase-5
candidate, French industry portfolios). Full roadmap: `.planning/V2-JUMPMODEL-PLAN.md`.

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
