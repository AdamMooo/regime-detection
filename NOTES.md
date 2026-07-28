# Regime-Detection — Session Notes

## Status
Program: statistical jump model. **Identity = regime DETECTION + methods/negative PAPER, NOT
trading.** Branch: main | Last updated: 2026-07-27

*Durable narrative (all chapters, anatomy, every null) lives in `RESEARCH-RECORD.md`
(newest-first). Forward roadmap + parked/killed ledger in `.planning/PROGRAM.md`. This file =
current state + next action only. Full session-by-session history is in git + RESEARCH-RECORD.*

## Current state (2026-07-28) — dispersion 4th-feature lag probe: candidate lead, needs intl confirmation

Built two new descriptive/data tools + lag probes this session (`build_credit.py` +
`explore_credit_feature.py`; `explore_dispersion_feature.py` reuses `build_dispersion.py`'s
existing `csd_ew10`). Both probes compare a BASE JM (dd10/sortino20/sortino60) against
BASE+4th-feature on detection lag, coverage, stability, switches/yr. Runs got killed mid-execution
once (agent closed) and were cleanly rerun to completion — no corruption, just restarted.

- **Credit** (`scripts/build_credit.py`, Moody's Baa-Aaa via FRED, gate PASS; `explore_credit_feature.py`
  → `results/explore_credit_feature.csv`): **negative**. Adding credit_ew10 made LT20 lag *worse*
  (52d → 106d, +54d), fewer bears detected (6/6 → 4/6), fewer switches/yr. Credit spread as a 4th
  feature does not help this instrument.
- **Dispersion** (`scripts/build_dispersion.py` realized cross-sectional dispersion, `csd_ew10`;
  `explore_dispersion_feature.py` → `results/explore_dispersion_feature.csv`): **candidate lead**.
  LT20 median lag dropped 56d → 16d (**−40 days**), more bears caught (9/11 → 10/11, LT15 15/18 →
  17/18), recall 0.56 → 0.79, stability held at 1.000, switches/yr didn't blow up (1.66 → 1.13).
  Script's own read: "a real lead candidate... CONTAMINATED (US panel) — needs international
  confirmation before any SUPPORT claim. No economic claim, no look spent."
- **Discipline note:** per the out-of-hypothesis-sample rule (`CLAUDE.md`), this is a US-panel
  descriptive finding only — it must confirm on French/MSCI developed-market daily panels (Japan,
  Germany, UK) before any SUPPORT claim or paper mention beyond "candidate under investigation."

## Prior state (2026-07-27) — repo refocused to instrument+paper only; algo-battery scripts removed

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
  `persistence_gauge()` done, weekly workflow built + verified live on GH Actions (7m59s).
- **Card enriched (same session, prompted by "what's still missing"):** the first version
  only carried self-referential persistence stats (how long has the label persisted).
  Added three things it was missing per this repo's own discipline
  (`results/README.md` documents the new fields):
  1. **`health`** — today's live-splice-gate correlation + pass/fail + agreement with the
     frozen labels, from a new `results/live_label_meta.json` `live_label.py` now writes.
     Earliest warning if the live SPY splice ever drifts from the French panel.
  2. **`skill`** — the instrument's real track record vs ex-post bear dating
     (`validate_sensor.py` vs frozen ch1 labels, already-run 2026-07-23 numbers: 15/18 bears
     caught at 15% dating, 20d median lag; 9/11 at 20% dating, 56d lag) — the "companion
     skill number" the paper to-do below already calls for, now also in the live card/email.
  3. **`history`** — trailing 24-month state timeline, rendered as a colored strip in the
     weekly email so the current dwell has visual scale.
  portfolio-manager's daily one-liner + weekly deep-dive updated to render all three
  (health only surfaces as a warning row when the gate actually fails — stays quiet
  otherwise). Not yet committed/pushed — verifying end-to-end first.

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

## Session 2026-07-27 close-out — portfolio-manager integration DONE, blocked only on the PAT

Everything planned for this integration is built, tested, and pushed: `persistence_gauge()`,
the weekly `regime_card.json` producer workflow (verified live twice on GH Actions), the
health/skill/history enrichment, portfolio-manager's consumer side (daily one-liner + weekly
`weekly_regime_brief.py`, both dry-run clean on real GH Actions), and both hub docs + this file
synced. Both repos' working trees are clean and fully pushed (verified 2026-07-27 evening).

## Next action(s) — in order

1. **International confirmation for the dispersion lead** — the −40d lag drop
   (`results/explore_dispersion_feature.csv`) is a candidate, not a finding, until it holds on a
   non-US panel (French/MSCI developed markets — Japan, Germany, UK). Build the equivalent
   cross-sectional dispersion feature on one of those panels and rerun the same lag-probe
   methodology before any SUPPORT claim or paper mention.
2. **[Adam, blocking] Create `REGIME_REPO_PAT`** — fine-grained PAT, read-only,
   `contents:read` scope on `AdamMooo/regime-detection` only
   (`https://github.com/settings/personal-access-tokens/new`). Add via
   `gh secret set REGIME_REPO_PAT --repo AdamMooo/portfolio-manager` + the same value in
   portfolio-manager's local `.env`. Until this exists both regime email sections silently
   omit themselves — confirmed safe, not a crash.
3. **Once the PAT is live:** watch the next real daily brief + the next Monday's weekly brief
   land — confirm the sparkline/track-record/health rows read cleanly on iPhone Mail (same
   check already pending from the original Market Brief rollout, now extended to the regime
   sections).
4. **Resume the paper (this integration was a detour from "this week = the paper").** Fold the
   Path-B null into `paper/OUTLINE.md` as **Race 4** (cross-asset timing loses to VT at every
   exposure); complete the §§1–7 core — draft §1 (vs Shu–Yu–Mulvey), §3 (the instrument, incl.
   the stability-stress-test to-do), §8 (monitor); exact-numbers appendix; export figures.
   Instrument-first framing. **No new experiments, no live/Alpaca, no reopening closed nulls.**
5. **(Optional, low priority)** Decide whether the Artifact preview (today's build, static
   snapshot) should become a genuinely live-updating page — would need a safe no-PAT
   read path (a public mirror of the non-sensitive card fields), since embedding the PAT
   client-side would expose it. Not started; fine to leave as a manual on-request refresh.

Parked, no action needed — do not re-propose without new information: Ch3 graded exposure
(reserved for a future consumer); asymmetric-λ / K=3 severity speed work (reconsidered
2026-07-27, stays parked — see `PROGRAM.md`). Background streams, not urgent: monitor
(Layer-2 nowcast, `MONITOR-VALIDATION-SPEC.md`); Sensor v3 tier-2 decision (VIX/VRP via FRED,
0.78 own-vol overlap — genuinely orthogonal axis still unfound).
