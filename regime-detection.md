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

**2026-07-23 evening — chapter 3 designed + both gates run; program restated to three
layers (measurement ≠ risk characterization ≠ decision value, `PROGRAM.md`).**
Probability layer KILLED (calibration gate: the filter's evidence margin loses to plain
EWMA vol on Brier AND AUC in all 8 synthetic DGP cells — classification is robust, the
margin is not a portable confidence measure). K=3 probe: stable severity ladder (1.000
both ±2y shifts), phase-tilted but NO phase state → M3 dead. Episode anatomy: real phase
structure, but the ex-post rebound premium collapses under causal conditioning; episode
age = the surviving causal coordinate, unvalidated. **D2 ruled (Adam): REGISTERED NULL** —
chapter 3 is the clean state-only dial (VT vs VT·g(S), g∈[0,2], hard label), draft Rev 3;
M2/age deferred to screened ch4 candidate (`CH3-D2-MEMO.md`). Risk-state monitor spec'd
claim-by-claim (`MONITOR-VALIDATION-SPEC.md`).

## Next

Execution order (Adam, 2026-07-23): **Track A ch3 closure** (runner + capability smoke →
sign-off → overnight → one look) interleaved with **Track B the paper** (foreground
default, rule 3) → **Track C monitor gate** (`monitor_gate.py` per spec) → **Track D
ch4/M2 screens** (power test, reactive-age race, era-split, label-only duration test;
international panels sealed). Parked/killed list with re-entry conditions: `PROGRAM.md`.

## Memory

- **Operations:** [[regime-detection/CLAUDE|CLAUDE.md]] (file map, live-vs-frozen, discipline)
- **Notes:** [[regime-detection/NOTES|NOTES.md]] (session state, read first)
- **Research narrative:** [[regime-detection/RESEARCH-RECORD|RESEARCH-RECORD.md]] (newest-first)

## Known Issues

- French data publishes with a 1–2 month lag — handled by the SPY-splice live tail
  (`scripts/live_label.py`, gate PASS corr 0.9957, 1.0000 agreement on overlap); the
  splice must be refreshed when displaying a current state (monitor claim C0).
- Chapter-3 prereg has one recorded defect (§10a): the M3 phase-separation criterion was
  frozen qualitatively — resolved by Adam's explicit ruling, kept on record for referees.
- HDP pipeline fully retired 2026-07-23 (its label was never consumed by anything — the
  Portfolio-Manager integration was only an idea in notes). Recoverable in git history if ever
  needed.
