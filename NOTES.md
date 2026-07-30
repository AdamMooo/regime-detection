# Regime-Detection — Session Notes

## Status
Program: statistical jump model. **Identity = regime DETECTION + methods/negative PAPER, NOT
trading.** Branch: main | Last updated: 2026-07-30

*Durable narrative (all chapters, anatomy, every null) lives in `RESEARCH-RECORD.md`
(newest-first). Forward roadmap + parked/killed ledger in `.planning/PROGRAM.md`. This file =
current state + next action only. Full session-by-session history is in git + RESEARCH-RECORD.*

## Current state (2026-07-30 eve) — PRODUCT CONVERGENCE: momentum = engine, crash = the gate

Goal locked with Adam: **A (make money) + B (advisor-usable tool), as ONE product.** Worked through the
strategy question and converged (all in-sample/QA, no look-gated claim):
- Timing/prediction/JM-as-signal = dead (5 nulls). Diversification = the only free lunch. Vol-targeting
  & trend = drawdown reducers, NOT alpha (`risk_engine.py`, `strategy_combo.py`: adding trend to
  vol-target did NOT lift Sharpe, only cut drawdown).
- `oracle_exposure.py` (in-sample-optimal per turbulence×trend cell, JM REMOVED — it's a weak detector,
  comms-only): once the JM is dropped, the "best move" is mostly risk-scaling (corr w/ inv-vol 0.18→0.62);
  residual = a trend tilt = momentum.
- **`cross_sectional_momentum.py` = the one real return-adder:** industry cross-sectional momentum
  (10 French industries, 12-1, long-only tilt) beat equal-weight on Sharpe (0.67→0.76) AND return,
  decade-ROBUST (alive 2010-now 0.75 vs 0.63; only failed 2000-09 the known momentum-crash decade),
  LOW overfit (no tuned params). **BUT −64/−72% crash drawdowns → un-holdable → fails B.**
- **Crash fix FAILED as tested:** vol-scaling (Barroso-Santa-Clara) did NOT tame it on industry momentum
  (2000-09 Sharpe −0.15→−0.36, DD −64→−72%). Likely too-coarse universe / 6m-vol lag — NOT tweaked
  further (spec-search refused).

**Convergence: momentum is the engine; its drawdown is the ONE problem between "real edge" and
"holdable product."** Next = (1) broaden universe (48 French industries → breadth diversifies the crash),
(2) a crash-control that actually works (Daniel-Moskowitz dynamic; residual/idiosyncratic momentum;
multi-factor), (3) OOS/walk-forward, (4) wrap with regime comms layer (B), (5) maybe single-stock
graduation. Regime/JM demoted to comms skin. **Deep-research launched 2026-07-30 on how professionals
build a HOLDABLE momentum product + solve the crash (was over-reliant on in-repo backtests — Adam).**

## Current state (2026-07-30 pm) — DETECTOR reframed as a COMMUNICATION instrument; multi-view read built + stress-tested

Adam's direction: "improve the detector" → then "how do we get VALUE / make it better." Landed here:

- **Detector skill benchmark** (`benchmark_detector.py`, `results/detector_benchmark.csv`): at matched
  exposure (29.1%) vs Lunde-Timmermann bears, a DUMB 20d-vol threshold + 5d hysteresis MATCHES/beats
  the JM on recall/precision/BAC/lag/episode-coverage; JM only wins raw switch-count (1.66 vs 2.76/yr).
  Reproduces the frozen `sensor_validation` numbers (machinery trusted). **Conclusion: the JM is NOT a
  superior detector and NOT an alpha/timing signal (5 nulls). Its value = a STABLE, trustworthy
  human-facing COMMUNICATION instrument** (advisor/client behavioral use), not a trade signal.
- **Multi-view regime READ** (`regime_read.py`, `results/regime_read_latest.json`): the defensible
  better instrument = turbulence (downside semivariance, continuous causal percentile) × direction
  (price vs SMA200) quadrant + severity + historical analogs. JM = the stable anchor. Reads sensibly on
  2008/2020/2022 (CONFIRMED BEAR EXTREME) and **catches 2018Q4 (which the bare JM misses)** as
  HIGH/GRIND — concrete proof the multi-view read beats the single label on its blind spot.
- **Two deep-research audits done this session** (both grounded/cited, in git via agent transcripts):
  1. regime-as-a-factor methodology → flipped my "spanned" call (see correction block below).
  2. multi-view design stress-test → ontology sound, but MECHANISMS naive: (#2) consensus-COUNT is the
     naive version of CISS/PCA composites — use first-PC/correlation-weighted, not counting; (#4)
     lifecycle state-machine is superseded (field uses latent stress PROBABILITY + hazard — BUT our
     probability layer is KILLED, tension to respect); (#1) "fast leads slow 16d" likely MECHANICAL
     smoothing lag — must beat a phase-lag null before believing it; (#3) turbulence×trend = textbook
     leverage effect, KEEP (sharpen w/ signed semivariance — done in regime_read); (#5) drawdown depth
     redundant (Magdon-Ismail) unless path-persistence residual; (#6) the behavioral premise ("stable >
     twitchy for humans") is UNTESTED (rests on cockpit/ICU analogy) — cheap randomized-vignette test,
     and it's a NEW use that clears the Layer-3 rule.

**Next action (not yet done, awaiting go):** wire the `regime_read` quadrant+severity+analog line into
`regime_card.json` + the portfolio-manager email (replace the bare binary label). Then optionally: the
behavioral vignette test (the actual thesis), and rebuild the composite as PC1 not a count.
Parked exploratory: `regime_panel.py` (consensus-count version — superseded by the PC1 critique);
`build_ohlc_panel.py` + `data/processed/ohlc_*` (range-based-feature idea, untracked, not pursued).

## Current state (2026-07-30) — REGIME-AS-A-FACTOR: AMBIGUOUS candidate, escalated to Step-4 (my "closed" verdict was WRONG)

Ran the pivot's first real question (FACTOR-MODEL-DIRECTION §5-6, Steps 1-3, all NO-look). I first wrote
this up as "SPANNED, closed cheaply." **That verdict was an over-claim — corrected after a deep-research
methodology audit Adam demanded.** Honest status: an **ambiguous candidate**, now at the Step-4 gate.

Built (all sound, all NO-look) + committed:
- `build_regime_factor_inputs.py` — frozen ch1 walk-forward + causal evidence-margin; **integrity gate
  0/9120 mismatch** vs frozen `oos_labels`; monthly regime series (state+stress), 435 mo 1990-2026.
- `build_bab.py` — AQR monthly BAB (USA ann Sharpe 0.70). `regime_factor.py` — regime FMP (beta-sort +
  Lamont/BGL mimicking, causal betas; recovery + no-lookahead tests). `factor_tests.py` +Newey-West
  spanning + max-Sharpe². `explore_regime_spanning.py`. 34 tests pass.

**Why the verdict flipped (audit findings, cited in RESEARCH-RECORD 2026-07-30):**
- Wrong bar: HLZ **t>3** is for factor DISCOVERY; a nested spanning test uses **|t|>2** — under which the
  mimicking α (**t=−2.09**) is significant.
- Wrong reading: a marginally-sig NEGATIVE α on a hedge candidate is the **FVIX signature** (AHXZ 2006,
  aggregate-vol priced negative) — a candidate priced hedge, not "spanned".
- ΔSh² eyeballed with no BKRS SE = no inferential weight. BAB-only under-controls the vol/IVOL axis.
- Constructions DISAGREE (beta-sort α t=−1.30 n.s.; mimicking t=−2.09) → caution.
- SOUND: the FMP construction (Lamont/BGL) + first-difference innovation (AHXZ FVIX method).

**Not closed, not supported.** Next = a preregistered Step-4 confirmatory test written BEFORE seeing any
augmented result (adding IVOL/BAC + re-reading α now would be spec-searching on the answer sheet).

## Prior state (2026-07-29) — dispersion CLOSED (didn't generalize); tree cleaned; PIVOT to cross-sectional factor model

Two big moves this session, after the PAT integration went live (below):

1. **Dispersion 4th-feature lead CLOSED — does not generalize.** Built `build_intl_panel.py`
   (French International daily — Japan + Europe, market factor + 25 size/BE-ME portfolios,
   1990+, gates PASS) and reran the identical lag probe (`explore_dispersion_intl.py`). Both
   panels move OPPOSITE the US: **Japan +154d, Europe +94d** LT20 lag (US was −40d), recall
   collapses (0.56→0.08, 0.73→0.28). Out-of-hypothesis-sample gate FAILED cleanly. Likely a
   US-specific *sector*-dispersion artifact (US feature used 10 industries; French has no daily
   industry sort internationally, so the proxy used size/BE-ME). Recorded in RESEARCH-RECORD
   2026-07-29; reproduction at commit `c370cfb`.

2. **Tree cleaned + PIVOT decided.** Adam: three closed Layer-3 nulls (Ch1/Ch2/Path-B) all tested
   *market timing* and all lost to vol-targeting/EWMA — the textbook result (Asness 2016). The
   mistake was the sport: everything was single-time-series timing, none was cross-sectional
   factor investing. **New direction = build a real cross-sectional factor model** (rank names by
   a characteristic, harvest the long/short spread) — a genuinely new information source, the one
   condition the Layer-3-closed rule permits reopening on. Removed all dead/failed probe code
   (`calibration_gate`, `explore_k3`, credit×2, dispersion×3, `rotation_precondition`,
   `hedge_anatomy`, `run_exposure`, anatomy trio) + orphaned results/data; kept the living
   instrument + `build_intl_panel`/`build_trend_proxy` as factor-data foundation. Suite green
   (18 passed). **Next: a literature-grounded gap analysis of professional factor construction
   BEFORE any prereg or look** (see next-actions).

## Prior state (2026-07-29) — portfolio-manager integration LIVE and verified end-to-end

`REGIME_REPO_PAT` created and set (fine-grained, read-only, `contents:read` on this repo only).
Confirmed via real GH Actions runs, not just a dry-run:
- `Weekly Regime Card` (this repo) — green, committing `regime_card.json` on schedule.
- `Daily Market Brief` + `Weekly Regime Brief` (portfolio-manager) — both green on their own
  cron **and** on manual `workflow_dispatch` (run IDs `30463577874`/`30463598842`,
  2026-07-29), both pulling the card successfully. The integration built 2026-07-27 is no
  longer blocked or hypothetical — it is live in the actual daily/weekly emails.
- Known non-bug fragility: the PAT has an expiry Adam set at creation; on lapse the regime
  sections silently self-omit (by design, not a crash) rather than erroring — no automated
  alert exists for that lapse, worth a manual calendar check before it expires.

**Next focus shifts from "ship the integration" to "improve the reports"** — the pipe is done;
content/presentation quality in the daily one-liner and weekly deep-dive is now the open work
(see Next action(s) below).

## Prior state (2026-07-28) — dispersion 4th-feature lag probe: candidate lead, needs intl confirmation

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

## Current state (2026-07-29 cont.) — Path A factor bench BUILT + validated

Gap analysis done (`.planning/FACTOR-MODEL-DIRECTION.md`, cited). **Fork decided: Path A first**
(portfolio-level cross-section, no new data). Built + validated:
- `build_factor_test_panel.py` → 25 size/BE-ME + FF3 monthly panel, 1926+, gates pass.
- `factor_tests.py` (GRS + Fama-MacBeth + factor-spanning), 7 tests incl. GRS size simulation.
- Validated on real data (descriptive, no look): GRS rejects CAPM & FF3 (p~1e-7, the known FF
  result); HML priced (t=3.5), not spanned; SMB weak. FM market-premium unidentified on these
  low-beta-dispersion assets (known issue, noted). Suite 25 passing.

**JM's only honest role = risk-scaler, never exposure-timer** (Asness "siren song"; our 3 nulls =
the literature).

**Regime-as-a-FACTOR idea researched + test designed (2026-07-29, `.planning/FACTOR-MODEL-DIRECTION.md`
§5–6).** Adam's question: is regime a priced *cross-sectional* factor (do assets that covary with
regime shifts earn a premium)? Deep-research honest prior: **most likely SPANNED by Mkt + BAB /
low-vol** (our label is a market-vol transform → a regime-spread re-loads the low-vol anomaly). One
narrow survival door: if the JUMP model isolates discontinuous tail/jump risk orthogonal to
diffusive vol (Kelly-Jiang, Bollerslev-Todorov). Cleanest test = build a regime factor-mimicking
portfolio (from the label INNOVATION, causal betas), spanning-regress on FF3+BAB (α at t>3),
Barillas-Shanken max-Sharpe check, GRS on broadened test assets; sign must be NEGATIVE
(hedging), positive = timing artifact. Steps 1–3 are NO-look; the look is gated behind
cooling-off + sign-off + international confirmation.

## Next action(s) — draft the Step-4 regime-factor prereg (NO look)

The regime-as-a-factor question is an OPEN Step-4 candidate (not closed, not supported). Next:

1. **Draft the Step-4 confirmatory prereg (NO look, written BEFORE any augmented run).** Lock, in
   advance: control set = FF3 + BAB + a distinct low-vol/IVOL factor (AHXZ IVOL and/or Betting-Against-
   Correlation, Asness-Frazzini-Gormsen-Pedersen 2020); decision bar = **|t|>2** on the spanning α
   (NOT HLZ t>3 — that's a discovery bar, wrong for a nested spanning test); proper inference = BKRS
   (2020) SE / GRS, not eyeballed ΔSh²; a **REQUIRED negative (hedge) sign** (positive = timing
   artifact → reject); pre-commit BOTH constructions must agree; international confirmation (Japan/Europe
   panels). Then overnight cooling-off + explicit dated sign-off → the one look.
   Data still needed (no look): an IVOL and/or BAC factor series (AHXZ / AQR).
2. **Housekeeping (no look):** add beta-dispersed test assets (industry / size-mom) to fix the
   Fama-MacBeth market-premium identification issue on the 25-portfolio set (§3b caveat).
3. **Separate Path-A target (later):** JM label as a **risk-scaler** (not the factor itself) — does
   scaling a factor's exposure by the state improve risk-adjusted return? Also look-gated.

Parked/killed unchanged (do not re-propose): all Layer-3 market-timing (Ch1/Ch2/Path-B/dispersion);
Ch3 graded-exposure; VIX/VRP detection axis. Reopening requires genuinely new orthogonal information.

## Older next-action list (superseded above; kept for context)

1. **Factor-model gap analysis (the pivot's first step — NO look, NO prereg yet).** A
   literature-grounded audit of how professionals construct a cross-sectional factor book
   (point-in-time fundamentals, cross-sectional z-score/winsorization, industry neutralization,
   alpha-model / risk-model / portfolio-construction separation, Ledoit-Wolf shrinkage,
   turnover/cost control, the multiple-testing hurdle — Harvey-Liu-Zhu, McLean-Pontiff), mapped
   against what this repo has. Output = a ranked "here's what we're doing wrong / missing"
   document. This is the honest prerequisite before deciding the factor program is real and
   scoping a prereg. Grounded in cited sources, not memory.
2. **Watch the live emails land** — next daily brief + Monday's weekly; confirm the
   sparkline/track-record/health rows read cleanly on iPhone Mail (first live observation now
   that the PAT works).
3. **Paper** — the negative/methods paper is still a real deliverable; the dispersion int'l
   null is a clean new "candidate that didn't survive confirmation" story for it. Fold in when
   returning to `paper/main.tex` (paper collapsed to one file 2026-07-29; to-do in `paper/README.md`).
   No new experiments, no reopening closed nulls.

Parked/killed (do not re-propose): all Layer-3 market-timing (Ch1/Ch2/Path-B/dispersion —
dominated by reactive baselines, closed); Ch3 graded-exposure (deleted); VIX/VRP detection axis
(killed). Reopening Layer-3 requires genuinely new orthogonal information — the cross-sectional
factor path is the one candidate that qualifies, and only after the gap analysis + a fresh prereg
+ overnight cooling-off + explicit dated sign-off.

Parked, no action needed — do not re-propose without new information: Ch3 graded exposure
(reserved for a future consumer); asymmetric-λ / K=3 severity speed work (reconsidered
2026-07-27, stays parked — see `PROGRAM.md`). Background streams, not urgent: monitor
(Layer-2 nowcast, `MONITOR-VALIDATION-SPEC.md`); Sensor v3 tier-2 decision (VIX/VRP via FRED,
0.78 own-vol overlap — genuinely orthogonal axis still unfound).
