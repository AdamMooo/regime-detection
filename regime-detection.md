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

**2026-07-29 — portfolio-manager integration LIVE, verified end-to-end.** `REGIME_REPO_PAT`
created; confirmed via real (not dry-run) GH Actions: `Weekly Regime Card` here, plus
`Daily Market Brief` and `Weekly Regime Brief` in portfolio-manager, all green on both their
own cron and manual dispatch. The regime sections now actually populate in the real emails.
One disclosed fragility, not a bug: PAT expiry is a silent self-omit, no alert wired — a
manual calendar check before it lapses is the only safeguard. **Focus now shifts to improving
report content/quality**, not shipping the pipe.

**2026-07-27 — repo refocused to instrument+paper+live-feed only; regime_card.json now feeds
portfolio-manager (daily one-liner + weekly deep-dive email).** Removed the closed-chapter
battery runners (`run_backtest.py`/`run_allocation.py`/`allocation.py` — one-looks spent,
reproducible at commit `51fbeff`); extracted the constants the live pipeline still needs into
`scripts/run_config.py`. Finished `regime_signal.py`'s `persistence_gauge()` (Markov expected
dwell/half-life + empirical position vs history) and added a weekly GH Action
(`weekly-regime-card.yml`, verified live) that regenerates and commits `regime_card.json`.
Enriched the card same day (prompted by "what's still missing"): `health` (today's live-splice
correlation/pass-fail, the earliest warning of a bad reading), `skill` (the real bear-catch
track record — 15/18 at 20d lag, 9/11 at 56d lag — vs `validate_sensor.py`), and `history`
(trailing 24-month state timeline for a sparkline). portfolio-manager consumes all three via
`src/regime.py`; vol-diagnostics is explicitly NOT a consumer (stays a separate showcase
project). Considered reopening the parked asymmetric-λ/K=3-severity speed work now that a real
downstream consumer exists — Adam's call: **stay parked**, the lag is an honest, disclosed
tradeoff (monitor spec C7), not a bug to chase. Only remaining step: Adam creates
`REGIME_REPO_PAT` so the emails actually populate.

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

**2026-07-24 — TOOL-FIRST PIVOT (Adam: "we have a strong regime tool, that's the
focus").** Both pending rulings dissolved: **ch3 one-look PARKED, not spent** (scarce +
irreversible; §6b smoke half-blind — de-risk power only; two nulls already banked; reserve
for a post-Sensor-v3 test), runner/prereg kept intact; §6b one-directional-power logged as
a paper methods finding. Roadmap → three parallel tool streams. Autonomous burst this day:
`paper/OUTLINE.md` reframed instrument-first ("Measurement Validity ≠ Decision Value" —
instrument to §3, three Layer-3 races §§4–6, monitor §8, graded-exposure demoted to §10
"parked"); paper §1 + §3 drafted (v0); Sensor v3 tier-1 data foundation built
(`scripts/build_dispersion.py` — realized cross-sectional dispersion 1926+, gate PASS, 0.78
own-vol corr = modest distinct axis). Guardrail: "strong tool" = Layers 1–2 only; never
relaunder a Layer-3 null.

**2026-07-26 — Path-B cross-asset candidate opened + de-risked (descriptive, no look).**
Adam surfaced Shu–Yu–Mulvey **2025** (allocation sequel); opened cross-sectional defensive
rotation — the one Layer-3 door where the auto-loss-to-reactive condition is absent. Findings
(`PROGRAM.md` candidate; scripts `rotation_precondition` / `hedge_anatomy` / `build_trend_proxy`):
per-asset regimes diverge (mixed ~76% of days); **bonds aren't a reliable hedge in this market
(failed 2022/2025)** — confirmed; **gold = only both-regime hedge, trend = best in the
bonds-failed crisis + positive carry, BTC = amplifier not hedge**; feature lens = conditional
return (B), not own-vol. Trend proxy GATE PASS (corr vs DBMF 0.69). **Go/no-go backtest → NULL:
timing adds no return/Sharpe beyond exposure, and a matched vol-target matches/beats its drawdown
protection (ch.1, 3rd reconfirm). Direction CLOSED.** Survivors: the descriptive hedge facts, the
trend-proxy tool, and a 4th dominated-use race for the paper. All committed + pushed.

## Next

**Improve the live regime reports** (new, replaces "create the PAT" now that the pipe is verified
live) — content/presentation quality in the daily one-liner and weekly deep-dive; review a real
rendered email first to find what's thin. Then, standing work:
1. **International confirmation** for the dispersion 4th-feature lead (−40d lag, US-only so far)
   on a French/MSCI developed-market panel before any SUPPORT claim.
2. **Paper (instrument-first)** — fold Path-B null in as a 4th dominated-use race; fill §1's
   Shu–Yu–Mulvey quotes, draft §8 (monitor), export figures → completes §§1–7 SSRN-preprint core.
3. **Sensor v3 — make it better** — tier-1 dispersion done; decide tier-2 (VIX/VRP via
   FRED fetch) given the 0.78 own-vol overlap; scorecard = beat the incumbent's card
   (20d lag, 15/18 bears, stability 1.000), look-free.
4. **Monitor — validate & ship** — `monitor_gate.py` per `MONITOR-VALIDATION-SPEC.md`,
   Layer-2 nowcast on the current label; does not block on v3.
Deprioritized (Layer-3 economic): ch3 closure, ch4/M2 age screens. Parked/killed list:
`PROGRAM.md`.

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
- HDP pipeline fully retired 2026-07-23 (its label was never consumed by anything). Recoverable
  in git history if ever needed. The jump-model label's Portfolio-Manager integration is real and
  **live** (2026-07-27 built, 2026-07-29 verified via actual GH Actions runs — no longer blocked).
