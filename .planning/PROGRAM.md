# Regime Program — Goal & Roadmap

Last updated: 2026-07-23 (evening restatement, Adam-approved). Forward-looking program
doc. Receipts: `V2-JUMPMODEL-PREREG.md` (frozen, ch1) + chapter-2 allocation prereg +
`CH3-EXPOSURE-PREREG.md` (draft Rev 3) + `CH3-D2-MEMO.md` + `MONITOR-VALIDATION-SPEC.md`
+ `RESEARCH-RECORD.md` (newest-first narrative).

## Goal (restated 2026-07-23, supersedes the morning "regime-aware allocation" goal)

**A validated risk-state instrument, a rigorous negative/methods paper, and an honest
risk monitor — allocation only if the evidence forces it.**

The three-layer hierarchy is the program's spine:

1. **Layer 1 — Measurement:** the K=2 jump-model label is stable (1.000 under ±2y
   shifts, re-confirmed at K=3), causal, live to today. Largely ESTABLISHED.
2. **Layer 2 — Risk characterization:** does the state support reliable conditional
   risk statements (vol fans, tails, episode structure)? Validated claim-by-claim per
   `MONITOR-VALIDATION-SPEC.md` (badges: OOS / descriptive / unsupported).
3. **Layer 3 — Decision value:** does the state improve any DECISION beyond reactive
   incumbents (VT/EWMA)? Three preregistered races run so far; reactive estimators won
   all. Chapter 3 (state-only exposure dial, registered-null prior) is the last
   daily-cadence test; chapter 4 (episode duration) only if it survives its screens.

Measurement validity ≠ decision value. The label describing the world well and the
label making money are different claims with different validation machinery; the
program stopped conflating them on 2026-07-23.

## Execution order (Adam, 2026-07-23)

- **Track A — Chapter 3 closure:** runner + capability smoke (power AND size on
  synthetic) → smoke recorded in prereg → freeze Rev 3 with named+dated sign-off →
  overnight cooling-off → one look → chapter written. All Rev-3 refinements accepted
  (g_stress ∈ [0,2]; mandatory smoke; F3 = hysteresis signature).
- **Track B — The paper (foreground default, rule 3):** exact-numbers appendix →
  §2/§6 drafts → figures; ch3 slots in when it lands; monitor gate supplies the
  constructive section. Computation runs in background; drafting owns the foreground.
- **Track C — Monitor gate:** `monitor_gate.py` (C1 flip-race, C2 coverage, C3 daily
  tails, C6 incremental-information battery) → badges → UI only after badges exist.
- **Track D — Chapter-4 screens (M2, episode age):** planted-effect power test,
  reactive-age race, era-split, label-only duration test → kill or graduate. Japan/
  Germany/UK panels stay SEALED for out-of-hypothesis-sample confirmation.

## Parked / killed (2026-07-23, with re-entry conditions)

- **KILLED — graded P(state) / probability layer:** calibration gate failed all 3
  criteria in all 8 DGP cells; the evidence margin is not a portable confidence
  measure. Re-entry only with a fundamentally different uncertainty estimator.
- **PARKED — K=3 sensor development:** stable severity ladder, phase-tilted loadings
  beyond a matched vol threshold (instrument finding, recorded). Re-entry: a named
  consumer for a severity dial.
- **PARKED — asymmetric-λ, λ lag-vs-whipsaw frontier:** re-entry: something
  downstream needs sensor speed (nothing currently does).
- **PARKED — atlas pages in report.html:** folded into the monitor UI when Track C
  reaches presentation.
- **EXCLUDED — factor selection / sector rotation / cross-asset menus:** preregistered
  out of chapter 3 (§10); any revival is a new prereg and a new look.

## Candidate — cross-sectional defensive rotation (Path B, Adam 2026-07-26, NOT launched)

Prompted by Shu–Yu–Mulvey 2025 (Annals of OR, arXiv:2406.09578) — but a deliberate move
AWAY from their design, not toward it. Status: GATED CANDIDATE. No look spent, no prereg
frozen. Re-entry to Layer 3 is Adam's explicit call under cooling-off; this note only
records the design so it is ready if he rules to spend a look.

- **Why it might have hope (the one structural argument):** every Layer-3 null so far lost
  to a reactive estimator of the SAME quantity (VT for exposure, EWMA for covariance).
  Cross-sectional *asset selection* produces a quantity no single-axis vol estimator can
  output ("hold gold/bonds not equities, now"), so the auto-loss condition is absent. Plus
  breadth: ~N semi-independent per-asset regime bets vs the single-asset program's breadth≈1
  (Grinold fundamental law). This is the only door where the structural reason we keep
  losing does not apply.
- **What we take from them / what we reject:** take the per-asset JM regime label (plays to
  our Layer-1 strength — the stable downside instrument). REJECT their μ-forecast bet (first
  moment, fragile; their own JM-vs-XGB is inconclusive and they concede forecast delay).
  Frame as robust/defensive allocation (uncertainty-set / risk-based), NOT return forecasting.
- **Objective:** capital protection primary; occasional outperformance of a MATCHED blend
  secondary. Modest by design — "be in the mathematically acceptable space, not always right."
- **The non-negotiable honest bar (the ch.1 trap in cross-sectional costume):** the benchmark
  is NOT SPY. SPY is 100% equity; any diversified multi-asset book beats it in drawdowns by
  holding bonds/gold — that is diversification, not regime skill, and lower average equity
  exposure reads as "outperformance" under risk-averse utility = the ch.1 exposure artifact.
  Honest bar = a matched static multi-asset blend (same universe, same average exposure/risk)
  + a vol-target on that same universe. Beat THAT or the result is uninterpretable.
- **Gate (data first, look later):** requires a clean multi-asset panel. `assets_daily.csv`
  already carries equity(mkt+10 industries)/bond10/gold — enough for the precondition screen;
  a fuller global panel (DE/JP equity, REIT, broad commodities) is future data work.
- **PRECONDITION RESULT (2026-07-26, `scripts/rotation_precondition.py`, descriptive, no look):**
  per-asset own-downside JM labels on the common 2001–2026 window, robust across lam∈{25..200}.
  A cross-section EXISTS: assets are in MIXED states ~74–80% of days (all-three-same only ~23%;
  all-bear only ~11%). Refuge when equity is bear: somewhere to rotate ~61% of equity-bear days.
  BUT the conditional refuge is MODEST and asset-specific: bond-in-bull lift 1.2–1.4× (genuine
  but small flight-to-quality — the relationship we already know), gold-in-bull lift ≈1.0
  (gold is an INDEPENDENT diversifier, NOT a conditional refuge). equity~bond bear-phi −0.1..−0.2
  (divergent, good); within-equity industries co-move (mean phi +0.44) → rotation must be
  ACROSS asset classes, sector rotation is a weak lever. VERDICT: GREEN-but-modest — the door is
  open, the edge is not obviously large, and it leans on bonds.
- **HEDGE ANATOMY + FEATURE-SET FORK RESOLVED (2026-07-26, `scripts/hedge_anatomy.py`,
  ETF panel 2004–2026, 10 SPY-stress episodes, descriptive):**
  - Adam's "bonds aren't a hedge in this market" CONFIRMED: IEF hedged 8/10 episodes but
    FAILED the two inflation/rates episodes (2022: IEF −10.6, TLT −24.0, LQD −12.4, TIP −8.5
    all negative; 2025 selloff similar). Bonds hedge DEFLATIONARY stress, fail INFLATIONARY.
  - The regime-robust hedge is GOLD: positive in 9/10 episodes, +8.1% mean when bonds hedge
    AND +7.3% when bonds fail — the only asset up in BOTH regimes. Commodities (DBC), dollar
    (UUP), cash (BIL) are the specific bond-FAILURE complements (DBC −9.1 when bonds hedge,
    +3.6 when they fail — an anti-bond, not a standalone hedge).
  - **FEATURE-SET FORK → LENS B WINS.** Own-downside features are the WRONG lens for rotation.
    Proof: GLD own-bull lift 1.05 (its own vol-regime is BLIND to equity stress) yet it returns
    +18.3%/yr annualized DURING equity bears; DBC lift 1.14 ("own-calm") yet −11.7%/yr (loses).
    Own-vol regime ≠ conditional payoff. Rotation must key on CONDITIONAL RETURN / co-movement
    behavior in the market's stress, not each asset's autonomous downside regime.
  - **Design implication:** a robust defensive sleeve = gold as always-on diversifier + a
    commodity/dollar/cash sleeve for the bond-failure (inflation) regime; do NOT lean on
    nominal bonds. Caveats: only ~10 episodes, bond-failure rests on 2022 (+small 2025);
    modern ETF era (pre-2004 inflation excluded — would only strengthen the commodity point).
  - **Next honest-bar question (before any prereg):** gold pays in equity bears, but does
    regime-TIMED rotation beat simply HOLDING a static gold+diversified sleeve? If gold is
    unconditionally good, static allocation captures it without regime timing. That control
    (matched static blend, PROGRAM.md rule 2) is the real test the candidate must pass.
- **WIDENED FINGERPRINT (2026-07-26, `scripts/hedge_anatomy.py`, 20 assets, +carry lens):**
  added trend/MF (DBMF, KMLM), haven FX (FXY, FXF), min-vol/intl/EM equity, REIT, silver, BTC.
  Web-checked first (crisis-alpha real for PROLONGED crises, mixed for equity corrections;
  inflation-conditional gold hedge is mainstream 2025; "dynamic beats static" claims exist but
  are the soft-baseline genre we deflate — inadmissible).
  - TREND is the standout add: KMLM +19.6% / DBMF +18.1% in the 2022 bonds-FAILED crisis
    (beat gold's +3.2), AND positive carry (DBMF carry +10.8). But short history (2019/2020+,
    can't see 2008) and regime-DEPENDENT (whipsaws short corrections: DBMF −6.0 in bonds-hedged
    episodes) — exactly the literature's "prolonged crises only."
  - CARRY LENS is decisive: only GOLD (stress +18.3, carry +9.8) and TREND pay in stress
    WITHOUT bleeding in calm. Bonds/yen bleed or fail. "Defensive equity" (USMV −2.8 stress),
    intl/EM (EFA −13.8, EEM −3.1), REIT (−11.4) are just equity beta — high carry, NO hedge.
    Kills the within-equity/defensive-factor angle (reconfirms: rotate ACROSS classes).
  - CRYPTO answered: BTC is an AMPLIFIER not a hedge (stress −29.4, INFL22 −58.8, carry +85.5).
  - FXF (swiss franc) = quiet all-weather (positive-ish all three crises, low carry) — minor.
  - Feature lens B RECONFIRMED across 19 assets (GLD lift 1.05 / trend lift 0.5–0.8, all big
    positive stress payoff → own-vol regime blind to the payoff).
  - Robust kit is SMALL: gold (always) + trend (prolonged/inflation) + commodity/dollar/franc/
    cash sleeve for bonds-failed. Caveats: 10 episodes total (2 bonds-failed ≈ 2022+2025 only),
    descriptive in-sample SPY regime, trend funds short-history.
- **TREND PROXY BUILT + GATED (2026-07-26, `scripts/build_trend_proxy.py`):** solves the
  short-ETF-history problem. TSMOM (Moskowitz–Ooi–Pedersen 12m momentum, inverse-vol sized,
  monthly rebalance, causal) over a 10-ETF universe (equity/bond/commodity/FX, per-market
  availability so GFC is covered via equity/bond/gold; FX joins 2008). GATE PASS: corr vs
  DBMF **0.69** (bar 0.50), corr vs KMLM 0.45, ann vol 10.2%, +12.8% in the 2022 crisis
  (crisis alpha independently reproduced), Sharpe 0.62 over 2005–2026. → the trend sleeve now
  has a faithful long-history return series for the static-vs-timed backtest.
- **NEXT STEP (the go/no-go test, not yet run):** Portfolio A (static hold: enhanced 60/20/20
  = equity/gold/trend + bonds, fixed weights, monthly) vs Portfolio B (regime-timed: JM
  risk-on/off × realized-stock-bond-corr bonds↔trend switch, gold core), through 2008/2020/2022
  after costs, on Sharpe / maxDD / FKO fee. Verdict rule pre-committed: B beats A robustly →
  worth a prereg; B≈A → "just statically hold gold+trend" (still a useful finding). Offense
  (beta-tilt) piece must separately beat vol-targeting (ch1). Switch signal must be REACTIVE
  (realized corr), never predictive (stock-bond Stage-1 null).
- **Discipline:** literature-born, not anatomy-born → the international-firewall rule does not
  bind, but out-of-sample robustness still wanted. Prereg → cooling-off → named+dated sign-off
  before ANY look, per CLAUDE.md.

## Design rules (carried, non-negotiable)

1. Matched baseline: conditional arm vs the IDENTICAL arm with conditioning removed
   (single-delta).
2. Exposure-matched controls mandatory (placebo persistent states, surrogates,
   matched static mixes).
3. Shrinkage logic wherever per-state estimates appear (~30 episodes).
4. CLAUDE.md discipline: prereg/one-look, causal-only, next-close execution, identical
   costs, honest reactive incumbents, cooling-off, out-of-hypothesis-sample
   confirmation for anatomy-born hypotheses.

## Status

- Ch1 CLOSED (Case B: exposure artifact + exceptional instrument). Ch2 CLOSED (NULL:
  EWMA beats state-conditioned covariance). Probability layer KILLED (2026-07-23).
  K=3 probe DONE (severity, not phase; stability 1.000). Episode anatomy DONE
  (phase structure real; ex-post rebound premium collapses under causal conditioning;
  age = the surviving causal coordinate, unvalidated).
- Ch3: draft Rev 3, D2 = registered null (Adam ruling), awaiting smoke + sign-off.
- Monitor: validation spec frozen; gate unbuilt.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
