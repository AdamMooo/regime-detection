# Regime-Detection — Session Notes

## Status
Program: statistical jump model. **Identity = regime DETECTION + methods/negative PAPER, NOT
trading.** Branch: main | Last updated: 2026-07-27

*Durable narrative (all chapters, anatomy, every null) lives in `RESEARCH-RECORD.md`
(newest-first). Forward roadmap + parked/killed ledger in `.planning/PROGRAM.md`. This file =
current state + next action only. Full session-by-session history is in git + RESEARCH-RECORD.*

## Current state (2026-07-27) — repo refocused to instrument+paper only; algo-battery scripts removed

Decision: this repo stays regime DETECTION + PAPER + the live instrument feed for
portfolio-manager — never an algo-backtest program again. Chapters 1/2 are closed and their
one-looks spent, so their battery runners no longer earn a place in the tree:

- Removed `scripts/run_backtest.py`, `scripts/run_allocation.py`, `scripts/allocation.py`,
  `tests/test_allocation.py` — reproducible at git commit `51fbeff` (last commit before removal).
  Extracted the constants + helpers the *living* pipeline still needs (`arm_returns`, `maxdd`,
  START/DELAY/LAMBDA_GRID/REFIT/…) into a new `scripts/run_config.py`; rewired
  `live_label.py`/`build_report.py`/`explore_k3.py` to import from it. Full suite green (19
  passed) after the move; `live_label.py` re-verified end-to-end.
- Kept `run_exposure.py` (Ch3, graded exposure) **parked, untouched** — it's not algo-trading
  cruft, it's the "how much should I scale into/out of positions given the regime" question,
  which is directly relevant to the positioning-email goal below. Kept `backtest.py` (core
  Sharpe/vol-target/fee library — `walkforward.py` and `live_label.py` depend on it) and
  `synthetic_validation.py` (instrument QA, not algo backtesting).
- **New direction, started this session:** combine with **portfolio-manager** (not
  vol-diagnostics, which stays a separate showcase/interview piece) into a real weekly +
  daily positioning system. Architecture: regime-detection runs its own weekly GH Action
  (`live_label.py` → `regime_signal.py` → commit `results/regime_card.json`);
  portfolio-manager fetches that file over HTTPS (PAT-authed, private repo) for a daily
  one-liner in the existing Market Brief plus a new standalone weekly deep-dive email.
  Blocked on: finishing `persistence_gauge()` in `regime_signal.py` (still `TODO(human)`,
  uncommitted) — next action.

## Prior state (2026-07-26) — Path-B cross-asset rotation CLOSED NULL; repo cleaned

Prompted by Adam surfacing Shu–Yu–Mulvey **2025** ("Dynamic Asset Allocation with Asset-Specific
Regime Forecasts", arXiv:2406.09578) — the allocation sequel to the 2024 JAM anchor. Opened the
**cross-sectional defensive rotation** candidate (the one Layer-3 door where the
auto-loss-to-reactive condition seemed absent). Explored descriptively, then tested — and closed:

- **Descriptive findings (kept, hypothesis-generating, in RESEARCH-RECORD):** per-asset JM
  regimes diverge (mixed ~76% of days — the market regime is a composite); **bonds fail as a
  hedge in the inflation regime (2022/2025)**; GOLD = only both-regime hedge; TREND = crisis-alpha
  + positive carry; defensive-equity/intl/EM/REIT are just beta; **BTC is an amplifier, not a
  hedge**; feature lens = conditional return (B), not own-vol regime.
- **Tool built (kept):** validated TSMOM trend proxy (`build_trend_proxy.py`, corr 0.69 vs DBMF).
- **Go/no-go backtest → NULL:** regime-timing adds no return/Sharpe beyond exposure (pure beta
  ladder); the bonds↔trend switch adds nothing; a matched-exposure **vol-target matches/beats the
  JM on Sharpe, drawdown AND crisis protection** — ch.1 reconfirmed a 3rd time. No
  weight-optimization run (in-sample overfit, refused). Algo direction DROPPED; backtest scripts
  removed (reproducible at git `d022c09`). All committed + pushed.
- **Repo cleanup (2026-07-26):** removed v1 log/report junk; archived stale v1 audit docs
  (`RESEARCH-AUDIT.md`, `DEEP-REVIEW.md` → `archive/research-v1/`); synced CLAUDE.md file map,
  PROGRAM.md status, NOTES (this compaction); bannered the stale `V2-JUMPMODEL-PLAN.md`.

## Program state — closed / parked ledger (detail: RESEARCH-RECORD + PROGRAM.md)

- **Ch1** (jump-model overlay) CLOSED — Case B: beat-B&H is an exposure artifact; VT dominates
  (−256 bps); the label is an exceptional instrument (stability 1.000).
- **Ch2** (state-conditional covariance) CLOSED NULL — plain EWMA covariance beats it (−29 bps).
- **Ch3** (graded exposure) PARKED — runner + prereg Rev 3 built (28/28 tests), one-look NOT spent
  (2026-07-24 tool-first pivot); reserved for a post-Sensor-v3 instrument.
- **Path-B** (cross-asset rotation) CLOSED NULL 2026-07-26 — timing = beta + VT-replicable drawdown.
- **Probability layer** KILLED — calibration gate failed all 3 criteria in all 8 DGP cells.
- **Layer 3 (economic/algo) is closed** — dominated by reactive estimators 3+ times. Reopens ONLY
  with genuinely NEW orthogonal information. **VIX / implied-vol / VRP is a KILLED axis** (v1:
  "regimes are vol regimes"; everything collapses onto the vol axis) — do NOT re-propose it.

## The instrument (Layer 1 — validated; this is the asset)

- K=2 JM on return-only downside features; **stability 1.000** under ±2y train shifts (HMM
  ensemble 0.809); 1.66 switches/yr; 30 real high-vol episodes. Live to today via SPY splice
  (`live_label.py`, corr 0.9957). A **vol-state sensor, not a bear detector** — catches 15/18
  bears at ~20d median lag, misses fast crashes (1998, 2018Q4).
- **Paper to-do (Adam flagged 2026-07-26):** the 1.000 stability is *under-argued* — a constant is
  also perfectly stable. In §3, pair every stability number with a skill number; harden the
  perturbation (±5y, bootstrap-resample, param jitter → show the degradation curve); add a
  deterministic (vol-threshold) baseline alongside the stochastic HMM.

## Operating rules (institutionalized discipline — full text in CLAUDE.md)

1. **Cooling-off** — overnight freeze→run + explicit named sign-off for any positive-claim run.
2. **Out-of-hypothesis-sample** — anatomy-born hypotheses confirm on international panels first.
3. **Paper-first** — the paper is the decaying asset; instrument work stays background.
4. **Comparative-negative only** — VT/EWMA won matched races as baselines, not recommendations.
5. **Check the record/web before proposing** (added 2026-07-26 — I re-proposed a killed axis
   from memory; grep RESEARCH-RECORD/notes and cite evidence first).

## Next action — build the weekly GH Actions producer workflow in this repo

`persistence_gauge()` is done (2026-07-27): Markov expected-dwell (`1/(1-p_stay)`) + half-life
(`ln(0.5)/ln(p_stay)`), empirical median/n/percentile-position from completed dwell episodes
(current still-open run excluded from its own comparison set — was double-counting itself and
mixing calendar-day/trading-day units in the first draft, fixed). `results/regime_card.json`
now generates correctly (`CALM`, 95d in, 53rd percentile of 30 completed episodes). Verified:
suite green (19/19), `regime_signal.py` runs clean.

Done: `.github/workflows/weekly-regime-card.yml` added (Monday 10:00 UTC, ahead of
portfolio-manager's 11:30 UTC daily brief) — runs `live_label.py` → `regime_signal.py`, commits
`results/label_live.csv` + `regime_card.json` back to main if changed. No secrets needed (SPY
pull is public via yfinance; base panel already tracked). Not yet verified by an actual scheduled
or manual (`workflow_dispatch`) firing — worth a manual trigger once pushed.

Next: switch to portfolio-manager repo — fetch helper (HTTPS + PAT, private repo) + daily
one-liner in `daily_report.py` + new `weekly_regime_brief.py`. Needs a PAT (repo secret) with
read access to `AdamMooo/regime-detection` — Adam to generate.

Then: still this week, the paper (SSRN preprint core) — fold the Path-B null into
`paper/OUTLINE.md` as **Race 4** (cross-asset timing loses to VT at every exposure); complete the
§§1–7 core — draft §1 (vs Shu–Yu–Mulvey), §3 (the instrument, incl. the stability-stress-test
to-do above), §8 (monitor); exact-numbers appendix; export figures. Instrument-first framing.
**No new experiments, no live/Alpaca, no reopening closed nulls.**

Background streams (not this week): monitor (Layer-2 nowcast, `MONITOR-VALIDATION-SPEC.md`);
Sensor v3 tier-1 dispersion built (`build_dispersion.py`, 0.78 own-vol corr = only modestly
distinct — a genuinely orthogonal axis remains unfound, and may not exist).
