# Regime-Detection — Session Notes

## Status
Program: statistical jump model (chapter 1 CLOSED — Case B); instrument-first roadmap
Branch: main
Last updated: 2026-07-23

*Full v1 session history (five nulls → convergence) and the v2 build log live in git
(this file pre-cleanup, commit b6e4b5f and earlier) and in `RESEARCH-RECORD.md` (the durable
narrative, newest-first). This file now tracks only the living program.*

## Current state (2026-07-23, post-cleanup)

**Chapter 1 verdict (frozen prereg Rev 2, one look, 381-min run): Case B.**
- fee(JM−B&H) +487.8 bps/yr [−47.4, +1138.8] — inside ALL THREE null bands (placebo 95th 541.3,
  surrogates [41,1080], iid [179,805]); exposure-matched 71/29 static mix beats the overlay
  (−48.7); γ=1 fee −314 → the "beats B&H" claim is an exposure/utility artifact, not timing.
- fee(JM−VT) **−255.8 [−477.5, −36.7]** — vol targeting dominates significantly; mechanism =
  detection-lag race (proven in silico first: even the ORACLE loses at 10–21d lag).
- The label as an instrument: stability **1.000** under ±2y train-window shifts (incumbent
  ensemble 0.809), 1.66 switches/yr, λ off grid edges, 30 bear episodes all real high-vol
  environments. Estimator instability: solved.
- Chapter written: `RESEARCH-RECORD.md` (2026-07-23 section). Visual dashboard:
  `results/report.html` (regenerate: `.venv/Scripts/python scripts/build_report.py`).

**Repo cleaned + renamed (2026-07-23):** v2_* working code renamed to functional names
(jumpmodel / walkforward / backtest / build_panel / run_backtest / synthetic_validation /
build_report; data → `market_daily.csv`); ~40 v1-era result/data/planning files deleted
(recoverable at tag `v1-convergence`); CI workflow rewritten (was referencing deleted files);
CLAUDE.md rewritten for the new era. Frozen evidence later renamed by Adam to drop v2_ prefixes
(stage1.csv / stage1_run.log / oos_labels.csv — mapping in `results/README.md`); frozen DOCS
still cite the old names. Forward program doc: `.planning/PROGRAM.md` (regime-aware allocation,
graded tilts, never 0/100 — goal set 2026-07-23).

## Roadmap (`.planning/V2-JUMPMODEL-PLAN.md`, Phase-4 tracks)

1. **Track 1 — prove the sensor (NEXT):** benchmark the 30 bear calls vs ex-post bull/bear
   datings (Pagan–Sossounov / Lunde–Timmermann); characterize the two states; build the
   SPY-splice live tail (French publishes 1–2mo lagged) so the label runs to today.
2. **Track 2 — the dial:** λ lag-vs-whipsaw frontier; asymmetric jump penalties (fast into
   bear, slow out); soft-exposure variant from the filter's evidence gap (hypothesis: it
   interpolates toward vol targeting).
3. **Phase 5 candidate — state-conditional asset menu:** what to HOLD per state (duration,
   credit, gold, French daily industry portfolios 1926+) — the lag-tolerant use. Framed as a
   conditional playbook on portfolio outcomes, NOT "info beyond vol" (settled v1 null).
   Exposure-matched controls mandatory. Prereg before running.
4. ~~Portfolio-Manager label swap~~ — DISSOLVED 2026-07-23: grep of portfolio-manager confirmed
   (and Adam confirmed) nothing ever consumed the v1 label; the integration was only an idea in
   notes. **HDP pipeline fully retired same day** (src/, run.py, models/, label CSVs, cached
   inputs, v1 deps — all deleted; recoverable in git history). Any future downstream integration
   is designed fresh against the jump-model label.

## Track 1 — DONE (2026-07-23)

- **Ex-post benchmark** (`scripts/validate_sensor.py`, `results/sensor_validation.csv`): the
  sensor is a VOLATILITY-STATE detector, not a bear-market detector — catches 15/18 LT-15%
  bears (median lag 20d from ex-post peak), precision ~0.32 (also flags vol-without-bear),
  misses fast crashes entirely (1998 LTCM, 2018 Q4 — sub-threshold at deployed λ; documented
  spec limitation; asymmetric-λ is the Track-2 knob for it).
- **Characterization (the headline):** stressed state has HIGHER ann. mean (14.1% vs 11.6%)
  at 2× vol (25% vs 14.3%) — crashes AND rebounds share the state (partly a mechanical
  entry-lag tilt toward rebound days). Sharpe 0.56 vs 0.81 → risk-adjusted logic alone cuts
  stressed exposure to ~40% of calm with NO directional bet. **Conditional value lives in
  second moments** → atlas focuses there. Confidence upgrades queued: calibrated P(state)
  from the filter evidence gap; K=3 crash/rebound split as atlas-phase exploration (must
  re-clear K=2's stability bar; watch the entry-lag confound).
- **Live label operational** (`scripts/live_label.py`, `results/label_live.csv`): SPY splice
  gate PASS (corr 0.9957), label runs to TODAY; 1.0000 agreement with frozen labels on all
  9120 overlap days. Current state: CALM since 2026-04-23.

## Panel expansion — DONE (2026-07-23)

`scripts/build_assets.py` → `data/processed/assets_daily.csv` (regenerable, gitignored),
gates PASS (`results/assets_gate.csv`): 10 FF industries + SMB/HML/MOM (complete-case 1963+),
synthetic 10y bond TR (IEF corr 0.962, ann vol 7.1% — fixed a duration bug that had doubled
vol: half-year periods vs years), gold via GC=F (2000+, GLD corr 0.888, non-synchronous
closes documented; FRED London-fix series unavailable).

## The atlas — DONE (2026-07-23) — STRUCTURE REAL, ONE CLAIM CORRECTED BY AUDIT

`scripts/atlas.py` → `results/atlas.csv` (+ run log). Cross-ASSET conditional structure,
30/30 LOEO-stable at the pooled level: **bonds** corr −0.10→−0.30 in stressed states,
ret +4.4→+7.2%, vol ratio 1.35 vs mkt 1.75; **gold** uncorrelated both states (2000+ only);
**momentum factor** corr FLIPS +0.25→−0.52, premium evaporates (Daniel-Moskowitz crash
dynamic — anti-hedge, design knowledge not a position). **Industries: correlations converge
0.83–0.92 in stress — within-equity rotation is cosmetic** (Page diversification-failure).
Conclusion: conditional value lives in cross-asset SECOND MOMENTS only.

**Audit correction (2026-07-23, pre-freeze):** LOEO sign-stability is robustness of the
POOLED estimate to single-episode drops — NOT per-episode evidence. The stock-bond corr
deepening holds in only 11/23 episodes ≥15d: the 1990s stressed shift is +0.07 (bonds
anti-hedge) and the 2022 inflation bear ran at stress corr +0.11. The vol state can't
distinguish growth-scare from inflation/rates stress (v1 stock-bond lesson: macro/rates
axis is a non-stationary co-trend). The VOL-RATIO structure is era-consistent and survives;
the corr tilt is era-fragile → chapter-2 prereg reframed around scale, not corr.

## CHAPTER 2 — RUN AND CLOSED (2026-07-23): NULL

Prereg frozen at **Rev 2.1** (audit Rev 2 + synthetic-smoke Rev 2.1 fixes: fee_B scored
from activation, F2 = vol-of-vol, verdict precedence, CCD ERC solver; freeze commit
3c3c419 precedes the run). Runner `scripts/run_allocation.py` (--confirm-frozen; --smoke =
synthetic capability check, PASSED: structured fee_a 7.0 vs unstructured 0.5). One look:

- **fee_A(cond−B_match) = +2.8 bps [−3.2, +8.4]** — F1 fires; below placebo 95th (5.8).
- **fee_B(cond−B_react) = −29.1 [−66.8, +8.5]** — F1b fires: **plain EWMA λ=0.97
  covariance beats the state-conditioned estimate**; B_react is the best ERC arm outright
  (Sharpe 0.878 vs 0.826). Era split: +8.4 pre-2000, −37.7 post-2000.
- F2 CLEAR (vol-of-vol 2.11 vs 2.15pp): the mechanism exists — conditioning stabilizes
  risk vs static — it is just dominated by reactive estimation. v1 chapter-3 lesson
  replicated on a new object, preregistered this time.
- Chapter written: RESEARCH-RECORD.md (2026-07-23 latest section). Dashboard:
  `results/report.html` now has the chapter-2 section (equity curves, fee-vs-bands,
  conditional weights, era splits). Evidence: `results/allocation_*.{csv,log}` — frozen,
  do not overwrite.

## Operating rules (Adam's directive 2026-07-23: "no rushing — address every concern")

Four rules from the end-of-day audit, now institutionalized:
1. **Cooling-off** — overnight gap freeze→run + explicit named sign-off for anything that
   could yield a positive claim (now in CLAUDE.md discipline).
2. **Out-of-hypothesis-sample confirmation** — anatomy/atlas-born hypotheses must confirm
   on international panels before SUPPORT (now in CLAUDE.md discipline; binds chapter 3).
3. **Paper-first ordering** — the paper is the decaying asset (2024-25 JM literature is the
   live target); instrument work (K=3, asymmetric λ) runs in the BACKGROUND, paper drafting
   in the foreground. If a session only has energy for one thing, it's the paper.
4. **Comparative-negative claims only** — B_react/VT won matched races; they are baselines,
   not recommendations (Cederburg cuts at them too). The paper must document protocol
   equivalence with Shu-Yu-Mulvey meticulously and never turn prescriptive
   (defensibility section now in paper/OUTLINE.md).

## DECISION (Adam, 2026-07-23): write the paper — option 1, with option 3 in parallel

**The paper is the deliverable.** `paper/OUTLINE.md` is written (full skeleton, real
numbers, figure plan, venue path: SSRN → Journal of Asset Management or Critical Finance
Review). Next session starts at its "Next actions" list (exact-numbers appendix → §2/§6
drafts → figure exports). Sensor-track work (λ frontier, asymmetric penalties, calibrated
P(state)) continues in parallel as instrument work. Chapter 3 (momentum, monthly cadence)
stays behind its gate — prereg only when Adam wants to spend another look.

Outside-research anchors for the paper (2026-07-23 search): Shu–Yu–Mulvey 2024 (JAM) +
JM+MPC 2025 claim regime value vs soft baselines — the paper's target; Cederburg et al.
2020 (vol-managed fails OOS on 103 factors) — the genre + the factor-chapter warning;
Barroso–Santa-Clara 2015 — momentum vol-scaling is the robust exception (chapter-3
incumbent if ever run).

The program lesson the paper argues: **the vol axis is real; every economic use tested is
dominated by a simple reactive estimator (VT for exposure, chapter 1; EWMA for covariance,
chapter 2). State-conditioning loses detection-lag races at daily horizons.** The fork
options were:

1. **Close the economic track** → write the methods/negative paper (the long-standing
   default; now with two preregistered chapters of ammunition + the instrument result).
2. **Chapter 3 only if a use is named where lag-tolerance is STRUCTURAL** (the gate from
   the information-gate discipline) — candidates would need horizon >> detection lag
   (e.g., monthly/quarterly decision cadences where EWMA's speed advantage dies), argued
   in a prereg BEFORE any data touch. **Named candidate (Adam, 2026-07-23): factor
   exposure conditioning** — the atlas's strongest conditional structure is momentum's
   stress behavior (corr flip +0.25→−0.52, premium evaporates; Daniel–Moskowitz crashes).
   Gate to clear in the prereg: the incumbent there is realized-vol scaling
   (Moreira–Muir 2017 vol-managed portfolios; Barroso–Santa-Clara 2015 momentum risk
   management) — the SAME reactive-estimator class that won chapters 1 and 2. A factor
   chapter must be monthly-cadence (where EWMA's speed edge compresses), long-short
   costs included, with the vol-scaled incumbent as the B_react-analog co-primary.
3. Instrument-track continuation regardless: λ frontier / asymmetric penalties (Track 2)
   are about the SENSOR, not allocation, and remain legitimate.

## State anatomy — DONE (2026-07-23, descriptive, no look spent)

`scripts/state_anatomy.py` → `results/state_anatomy.csv` (+ run log). Adam's re-entry
question, quantified on the frozen labels:

- **The stressed state is 53% rebound days.** Crash phase (entry→trough) −42.2% ann at
  29.4% vol; rebound phase (trough→exit) **+64.7% ann at 19.7% vol** — the best
  risk-adjusted environment in the dataset is hiding INSIDE the "bear" label. Median
  trough = day 9 of a 35-day median episode (73% of a median episode is rebound). A 0/100
  switcher forfeits median +6.9%/episode (mean +13.2%, fat right tail: 2008/2020).
- **Exit hazard is non-monotone** (33% → 40% → 17% → 10% per 21d as episodes age): quick
  scares die inside ~6 weeks; episodes that survive become long grinds — two episode
  species, supports the K=3 crash/rebound split idea.
- **The bull is not one thing:** young bull (first 63d post-stress) Sharpe **1.29** at
  12.4% vol — the honeymoon; mid bull (63-252d) is the WORST calm phase (Sharpe 0.51);
  old bull 0.82.
- **Momentum ties in exactly as Daniel–Moskowitz says:** stressed days are 44%
  momentum-positive (median 12-1 = −3.5%) vs calm 97% — the state overlaps momentum-crash
  conditions; design knowledge for the gated chapter 3.
- **Honesty caveat (binding):** trough positions are defined EX-POST. The rebound phase is
  real structure, not a tradeable signal — recognizing the trough in real time is the same
  detection-lag race chapters 1–2 lost. Any economic use needs prereg + honest incumbent.

Next instrument steps this motivates (no prereg needed until an economic claim is made):
K=3 crash/rebound/calm exploration (must re-clear K=2's stability bar; entry-lag confound
check), asymmetric-λ exit dial, calibrated P(state) from the filter evidence gap.

## K=3 probe — MACHINERY DONE, FULL RUN PENDING (2026-07-23)

Built + committed (b1d5bab, 25/25 tests): scalar k=3 DP fast path in `jumpmodel.py`
(tested exact vs the general DP), `k` param through `walkforward.py` (k=2 byte-identical;
k=3 validation weights = (k−1−s)/(k−1)), probe script `scripts/explore_k3.py` (state
characterization, K=2 partition, EX-POST crash/rebound alignment, ±2y stability bar).
Smoke PASS. **Full run was interrupted by laptop shutdown (no partial state — the script
writes only at the end). RERUN (~1-2h, background it):**

    PYTHONIOENCODING=utf-8 .venv/Scripts/python scripts/explore_k3.py 2>&1 | tee results/k3_exploration_run.log

Smoke hint to check against: on the short slice, the third state split stress by SEVERITY
(rare ~44%-vol extreme state), and crash/rebound days got IDENTICAL k3 distributions —
i.e. no phase separation. If the full run confirms: clean instrument finding ("vol features
see levels, not phases"; the sortino coordinates weren't enough) → effort goes to
asymmetric-λ (exit lag) + episode-age/hazard sizing (age is causally observable — the
strongest ch3 candidate from the anatomy). If it DOES separate: phase-aware sensor →
worth drafting the ch3 prereg around a rebound state, honest incumbent = VT.

Also this session: the model math + learning curriculum was written out for Adam in-chat
(statistical jump model = sticky-HMM MAP, λ = 2σ²·log(p_stay/p_switch); the causal filter
= clipped evidence random walk D_t = ΔC_t + clip(D_{t−1}, ±λ) — the derivation of the
asymmetric lag). Standing offer: Adam hand-writes `filter_states` as a learning exercise
next session.

Also queued (not blocking): calibrated P(state) from the filter evidence gap (needed by the
graded variant — calibrate on SYNTHETIC panels pre-freeze); K=3 crash/rebound exploration
(entry-lag confound check); atlas pages in report.html; λ lag-vs-whipsaw frontier.

## CHAPTER 3 PREP (2026-07-23, PM session) — prereg DRAFT Rev 1, gates in flight

Question narrowed by Adam: state-conditioned CONTINUOUS exposure vs vol targeting —
w = (σ*/σ̂)·g(state) vs w = σ*/σ̂, single-delta (g≡1 must recover VT byte-identically),
a decision-rule claim NOT an information claim (information-gate compliant). Registered
prior: interpolates to VT (expected null → completes the negative paper).

- **Prereg:** `.planning/CH3-EXPOSURE-PREREG.md` DRAFT Rev 1 — NOT frozen. Decisions
  recorded: D1 daily (monthly = robustness only), D3 w_max=1.0 long-only, D2 = CONDITIONAL
  rule frozen before the probe result (M3 if K=3 passes phase+stability gate, M2
  episode-age/hazard if it fails, registered null if neither). g family pinned per branch.
  Freeze still blocked on: probe → calibration gate → overnight cooling-off + Adam's
  named+dated sign-off. One look.
- **Margin plumbing:** `filter_states(..., return_path)` + `walk_forward(..., return_margin)`
  emit m_t = (V_calm − V_stressed)/λ (dimensionless evidence gap; λ-normalized because the
  filter clips at ±λ). States byte-identical with/without (27/27 tests).
- **Calibration gate:** `scripts/calibration_gate.py` — 8-cell DGP grid (frequency,
  persistence, severity, SNR; Adam's robustness requirement), pooled Platt on train seeds,
  per-cell acceptance (Cox slope/intercept, Brier vs climatology AND vs log-EWMA-vol
  benchmark, cross-cell stability). SMOKE: machinery works, gate itself FAILS the smoke
  config — margin nearly flat (a=0.25), vol benchmark crushes it (Brier 0.06 vs 0.19),
  weak-SNR cell sign-flips. If full run confirms → pre-committed §6 fallback: A3 uses the
  HARD label, two-point g. AUC diagnostics added to separate discrimination from
  calibration. Full run (32 walk-forwards) launched; K=3 probe rerun also launched.

**GATES RESOLVED (same day, later):** prereg now DRAFT Rev 2, §10a records both:
- **Calibration gate FAILED all 3 criteria in all 8 cells** — margin loses to log-EWMA-vol
  on Brier (2–4×) AND AUC everywhere; per-cell slopes −0.17..2.05. → A3 = HARD label,
  two-point g (pre-committed fallback; Adam concurred: "the filter's classification is
  robust, its internal evidence margin is not a portable confidence measure").
- **K=3 probe (32 min, `results/k3_exploration.csv`):** severity ladder 12.8/16.2/28.3%
  vol; switches 2.57/yr; stability 1.000 at BOTH ±2y shifts (bar 0.95); λ path noisy
  (hits both grid edges — k3 λ selection less stable than k2's). Crash/rebound load
  differentially on state 2 (71%/36%) and MORE than an occupancy-matched σ̂ threshold
  (57%/50% — scratchpad control) → more than a pure vol tier (dd/sortino see drift), BUT
  no state IS a phase (rebound-heavy state 1 = majority state, 58% of calm days).
  **Phase-separation criterion was under-specified in the prereg (defect recorded, not
  cured post hoc). D2 = M2 (episode age) RECOMMENDED — M3's family g={1,g_crash,g_rebound}
  presupposes phase states that didn't materialize. Final ruling = Adam's, at sign-off.**

## EVENING SESSION (2026-07-23): D2 RULED, MONITOR SPEC'D, PLAN FROZEN

- **D2 RULED (Adam): REGISTERED NULL.** Chapter 3 = clean state-only test (VT vs
  VT × two-point hard dial). M2 (episode age) DEFERRED to a screened ch4 candidate —
  full reasoning in `.planning/CH3-D2-MEMO.md` (five-claim separation; single-delta;
  external lit contests duration-dependence sign; Nagel premium partly vol-spanned;
  age-beyond-vol "apparently underexplored"). All three Rev-3 refinements ACCEPTED:
  g_stress ∈ [0,2] (don't assume de-risking), mandatory capability smoke (§6b, power
  AND size — no smoke, no run), F3 = hysteresis signature (positive fee must
  concentrate on within-episode vol-lull days).
- **Conceptual split frozen: measurement validity ≠ decision value.** Layer 1
  measurement (done) / Layer 2 risk characterization (the MONITOR —
  `.planning/MONITOR-VALIDATION-SPEC.md`, claim-by-claim badges [OOS]/[DESC]/
  UNSUPPORTED, forecast-validation machinery: PIT/Christoffersen/CRPS/QW-CRPS/
  Amisano-Giacomini/Giacomini-White) / Layer 3 decision value (ch3, ch4 screens).
  Monitor is a NOWCAST, not early warning (C7 renders the lag stats prominently).
- **Execution plan (Adam-approved, AskUserQuestion 2026-07-23):** Track A ch3 closure
  + Track B paper INTERLEAVED (paper owns the foreground per rule 3, compute in
  background) → Track C monitor gate → Track D ch4 screens. Park/kill list applied;
  PROGRAM.md goal RESTATED (three-layer framing; morning "graded allocation" goal
  superseded). Parked/killed items + re-entry conditions: see PROGRAM.md.

## LATE SESSION (into 2026-07-24 early AM): runner built, smoke run, v3 candidate

- **Ch3 runner + smoke DONE** (`scripts/run_exposure.py`, commit 10e8a20; 28/28 tests,
  g≡1 recovers VT byte-identically; real run hard-blocked pre-freeze). §6b smoke:
  de-risk POWER PASS (+57 bps, g locks to planted answer), SIZE clean 3/3, re-risk
  FAIL (placebo-overlap + γ-variance penalty + downside features can't see
  positive-drift high-vol). Recorded in prereg §6b.
- **Paper moved:** `paper/DRAFT-SECTIONS.md` — §2 Discipline + §6 Mechanism v0 prose
  (framing-invariant; §6 closes with the calibration result as the mechanism's third leg).
- **CANDIDATE direction (NOT a plan change — Adam called it "probably rambling", no
  ruling given): Sensor v3 — vol-structure information.** Implied vol (VIX 1990+ FRED,
  term structure, VVIX, SKEW, VRP), implied correlation (COR1M/3M ~2021+ new methodology),
  DSPX dispersion (2023 launch, backfill to 2014 only — short), and the sleeper: REALIZED
  dispersion from the French cross-section 1926+. Passes the v1 information gate (new
  source; options surface was on the sanctioned successor list). Targets documented
  sensor weaknesses (20d lag, 1998/2018Q4 misses, one-axis blindness). Key discipline
  asset: chapter-1's in-silico lag-decay curve PRICES the economic ceiling from
  instrument metrics alone (measure new lag → read surviving oracle value) BEFORE any
  look; and the honest economic incumbent upgrades to VIX-based VT. Instrument gains
  near-certain; economic gains underdog-with-a-pre-screen.

## RULED 2026-07-24 (Adam): "strong regime tool = the focus" — TOOL-FIRST PIVOT

Both pending rulings dissolve.

- **Ch3 one-look PARKED — NOT spent.** Machinery kept intact (runner 28/28 tests,
  prereg Rev 3). Rationale: the look is scarce+irreversible; the §6b smoke is half-blind
  (de-risk power only, cannot detect re-risking); prior=null with two preregistered nulls
  already banked (Ch1 VT, Ch2 EWMA); reserve the look for a post-v3 economic test where
  lag-tolerance is STRUCTURAL. The §6b one-directional-power result is a **methods finding**
  → folds into the paper's mechanism section, not behind a spent look. Ruling #1 moot.
- **Roadmap = tool-first, three parallel streams** (Adam multi-selected all three):
  1. **Sensor v3 — make it better** (vol-structure info; instrument gains near-certain,
     economic gains gated behind in-silico lag-decay pricing). Ruling #2 = yes/reorder.
  2. **Monitor — validate & ship** (Layer-2 nowcast on the CURRENT label; badges +
     forecast-eval; does not block on v3).
  3. **Paper — reframe instrument-first** (execute the OUTLINE REFRAME OPTION; foreground
     per rule 3, compute in background).
  Track A (ch3 economic) and Track D (age screens) — Layer-3 decision-value work —
  deprioritized. Monitor Track C is NOT paused (Adam kept it).

**Discipline note:** "strong tool" = strong at Layer 1 (measurement, 1.000 stability) +
Layer 2 (risk characterization / monitor). NOT Layer 3 (decision value — three dominated
uses). The tool-first framing must never relaunder a null economic claim; instrument
improvements are the low-risk high-certainty bet, economic value stays gated.

## AUTONOMOUS SESSION 2026-07-24 (Adam: "go for it autonomously, come back when done")

Delivered (uncommitted — commit awaiting Adam's word per global rule):
- **Paper reframed instrument-first** (`paper/OUTLINE.md` rewritten): title flips to
  "Measurement Validity ≠ Decision Value"; §3 = the instrument (front), §§4–6 = three
  Layer-3 races (exposure / covariance / confidence-margin), §7 mechanism, §8 monitor.
  Graded-exposure (ch3) fixed to §10 "parked, not concluded" — §6b one-directional-power
  logged as a methods finding, explicit "no economic result on graded exposure."
- **Paper §1 (intro) + §3 (instrument) drafted** (`paper/DRAFT-SECTIONS.md`, v0). With §2 +
  §7-mechanism already there, §§1–3,7 exist → close to the §§1–7 SSRN-preprint trigger.
  Two [TODO]s in §1: quote Shu–Yu–Mulvey's exact headline + benchmark.
- **Sensor v3 data foundation tier 1 built** (`scripts/build_dispersion.py` →
  `data/processed/dispersion_daily.csv`, `results/dispersion_gate.csv` + run log).
  Realized cross-sectional dispersion from the 10 industries, 1926+, no network. Gate PASS
  (coverage/sane/distinct-axis corr 0.783). Descriptive-only: stressed/calm ratio 1.34×;
  weak pre-onset lead (+0.13 z). NO look spent; NO backtest; contamination caveat in-code.

NEXT ACTION (Adam's call): (a) commit this session; (b) paper — fill §1 SYM quotes, draft
§8 (monitor), export figures; (c) Sensor v3 tier 2 — VIX/VRP via FRED (network fetch; I'll
hand the exact command), and decide whether dispersion's modest incremental axis (0.78 corr
w/ own-vol) justifies the options-implied tier; (d) monitor build on current label.

## EPISODE ANATOMY — DONE (2026-07-23, descriptive, no look; firewalled from ch3)

`scripts/episode_anatomy.py` → `results/episode_anatomy.csv` (+ run log). Real-time
phase coordinates (τ, σ̂ level/trend/accel, DD level/velocity, trailing jump count) vs
forward outcomes, frozen labels:

- **Age profile (causal) is the strongest structure:** τ≤5 = tail-of-crash (fwd5 −23% ann);
  τ 6–42 = sweet zone (fwd +29..+49% ann at BELOW-average vol); τ 127+ = grind (fwd +2..+5%,
  vol RISES to 25%, hazard 8%; 5 episodes/1075 days). "Stay invested in stress" is right
  early, wrong late — the anti-cash rule is as coarse as the cash rule.
- **Vol trajectory = hazard descriptor, not return signal:** lo/falling vol → 35% exit
  hazard but the WEAKEST fwd returns (+8% ann); hi/rising → 2% hazard, +24%. Vol peak is
  COINCIDENT with the price trough (median +1d) — falling vol cannot lead the rebound.
- **Ex-post/causal gap quantified:** last-10-days-before-exit average +66% ann with a crisp
  signature, but conditioning on that signature in real time yields +8% — detection ≠
  prediction ≠ decision value, at phase level.
- Episode species barely visible in first-10d observables (grinds reveal themselves by
  surviving) — another argument for age as THE phase coordinate.

**PRESERVED HYPOTHESIS (Adam, 2026-07-23 — conceptual only, no model/prereg change):**
"The model may correctly detect the stress episode, but the economic behavior within that
episode depends on its duration and phase" — State + Episode age, stress as trajectory
(onset → early → recovery window → grind) compressed into one label; state detection ≠
phase identification. Routes from EITHER ch3 outcome (positive → natural next question;
null → explains why binary state-to-cash failed). Obligations attached at birth: honest
incumbent = REACTIVE age (days since a plain σ̂ trigger — if JM-age only proxies
time-since-vol-spike, vol machinery replicates it); US-anatomy-born → international
confirmation binds; τ inherits the label's entry lag; τ 22–42 numbers are
overlapping-window, era-concentrated, survivor-conditioned (expect shrinkage OOS).
