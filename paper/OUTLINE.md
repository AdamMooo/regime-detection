# Paper — A Validated Regime Instrument and the Limits of Its Use: Measurement Validity ≠ Decision Value

Status: OUTLINE. Reframe DECIDED 2026-07-24 (Adam: "strong regime tool = the focus") —
system/instrument-first spine now active (superseding the negative-first draft). Ch3
(graded exposure) look PARKED, not spent — see scope note in §10.
Working title above; alternates: "The Detection-Lag Race: Why Regime Signals Lose to
Reactive Estimators" / "Regime-Switching Value Is a Baseline Artifact" (negative-first,
retained as the CFR-genre framing if the venue pulls that way).

Venue path: SSRN preprint → Journal of Asset Management (where Shu–Yu–Mulvey 2024 landed;
the direct conversation). The instrument-first framing weakens the Critical Finance Review
(pure-deflation) fit but strengthens JAM (build + bound).

## The claim in one paragraph (system-first)

We build and validate a market risk-state instrument — a K=2 statistical jump model on
return-only downside features — to an unusual standard: 100.0% label agreement under ±2y
training-window perturbation (vs 80.9% for an HMM ensemble), live operation to today, and
preregistered one-look evaluation of every use we put it to. We then map, under freeze-
before-run discipline, exactly WHERE its information is and is not consumable. Its state
classification is robust (**Layer 1 — measurement**); its conditional risk characterization
is testable and partially validated (**Layer 2 — risk**); and every DECISION use we tested
is dominated by a simple reactive estimator at daily horizons (**Layer 3 — value**):
binary exposure switching loses to volatility targeting (fee −256 bps/yr, CI excludes 0);
covariance conditioning loses to a plain EWMA covariance (−29 bps; the EWMA arm wins
outright); and the filter's own evidence margin, mapped to a state probability, loses to an
EWMA-volatility signal in 8 of 8 synthetic environments on both discrimination and
calibration. The unifying mechanism, shown in silico before any real-data run, is a
detection-lag race: persistent-regime information is genuinely valuable when instantaneous,
but a causal detector's ~5–20 day recognition lag lands it precisely where even an oracle
loses, while reactive estimators pay no recognition toll. The instrument-vs-strategy
distinction, usually a footnote, is the thesis: **measurement validity ≠ decision value,
and the applied regime-switching literature's positive claims live in the gap between
them.**

## Sections & the numbers that go in them

### 1. Introduction
- Lead with the system: a rigorously validated regime instrument, and the honest map of
  where its information is consumable (three layers).
- The applied regime-value claim (Nystrup 2020–21; Shu–Yu–Mulvey 2024; JM+MPC 2025) and
  its baseline problem (B&H-grade comparisons; no exposure match; no reactive incumbent).
- Contributions: (a) an exceptionally stable, live regime instrument; (b) preregistration
  with freeze-before-run in public git history; (c) exposure-matched nulls; (d) reactive
  co-primary baselines; (e) the lag-race mechanism unifying three dominated uses;
  (f) the measurement-validity-vs-decision-value thesis.

### 2. Discipline (methods overview) — DRAFTED (DRAFT-SECTIONS.md §2)
- Prereg → freeze → one look; controls computed before primaries; frozen classifications;
  defects recorded not silently cured. Cooling-off + out-of-hypothesis-sample rules.
- Causality: return-only features (dd10/sortino20/sortino60), expanding windows, per-refit
  frozen params incl. λ (causal 8y-validation), DP-endpoint forward filter, next-close
  execution (delay=2), 10 bps one-way.
- Metric: FKO (2001) quadratic-utility fee, γ=10 headline, γ=1 secondary; paired
  stationary bootstrap 90% CIs (mean block 126d, B=2000).

### 3. The instrument (Layer 1 — measurement validity) [was §5]
- Label stability 1.000/1.000 under ±2y train-start shifts (incumbent ensemble 0.809);
  1.66 switches/yr; 30 episodes, all genuine high-vol environments (calm vol ~14%,
  stressed ~25%).
- Sensor validation: catches 15/18 ex-post −15% bears, median 20d lag; misses fast crashes
  (1998, 2018Q4) — a vol-state sensor, not a bear detector (honest boundary of use).
- Live capability: SPY-splice tail (corr 0.9957 gate), 1.0000 agreement on 9120-day overlap;
  runs to today.

### 4. Race 1 — trading the label directly (Layer 3) [was §3]
- K=2 jump model, French daily TR 1926+, trained from 1970, OOS 1990-03..2026-05 (n=9120).
- fee(JM−B&H) = +487.8 [−47.4, +1138.8]; placebo 95th = 541.3; surrogate [41, 1080];
  iid [179, 805]; matched static mix beats the overlay (−48.7); γ=1 fee = −314.
- fee(JM−VT) = −255.8 [−477.5, −36.7] — significant loss to the honest bar.
- Verdict: the beat-B&H fee is an exposure/utility artifact; timing loses to VT.

### 5. Race 2 — conditioning covariance on the label (Layer 3) [was §4]
- Long-only ERC {equity, 10y Treasury TR, gold, cash}, caps 75/75/25, 8% vol target
  (scale-down only), hard-state conditional covariance (expanding per state, ≥500-day
  activation, 0.5 shrinkage), monthly + state-flip rebalance.
- fee_A(cond−B_match) = +2.8 [−3.2, +8.4]; placebo 95th 5.8, shuffle 95th 4.9,
  iid [−1.8, +1.0] → inside bands.
- fee_B(cond−B_react EWMA λ=0.97) = −29.1 [−66.8, +8.5]; B_react best arm outright
  (Sharpe 0.878 vs 0.826); era split +8.4 pre-2000 / −37.7 post-2000.
- F2 mechanism-check survives: vol-of-vol 2.11 vs 2.15pp — conditioning DOES stabilize
  risk; it is dominated at it.
- Design-provenance warning exhibit: pre-freeze audit corrected the atlas's pooled-vs-per-
  episode fallacy (stock–bond corr deepening holds 11/23 episodes; 1990s +0.07; 2022 stress
  corr +0.11) — a caution about LOEO-style stability claims.

### 6. Race 3 — the confidence margin as a probability (Layer 3)
- Calibration gate on an 8-cell synthetic DGP grid (frequency × persistence × severity ×
  SNR), pooled Platt on train seeds; per-cell Cox slope/intercept, Brier vs climatology
  AND vs log-EWMA-vol, AUC discrimination check, cross-cell stability.
- Result: the filter's λ-normalized evidence margin loses to a plain log-EWMA-vol signal on
  Brier (2–4×) AND AUC in all 8 cells; per-cell slopes −0.17..2.05 → the classification is
  robust but its internal margin is not a portable confidence measure.
- Consequence: probability layer KILLED as a decision input; hard-label is the honest use.

### 7. Mechanism — the detection-lag race (unifies §§4–6) — DRAFTED (DRAFT-SECTIONS.md §6)
- In silico: an oracle switching at true regime boundaries beats VT by +136..+1090 bps/yr;
  delaying its signal 10–21 trading days erases most-to-all of the edge; causal filters lag
  ~5–20d by construction (empirical median detection lag 20d from ex-post peaks).
- Reactive estimators (VT, EWMA) have no recognition step to lose — they harvest the same
  persistent-volatility structure without paying the lag toll. This is why all three races
  break the same way: the state machine knows WHERE it is; everything it knows about
  MAGNITUDE arrives later and coarser than a reactive estimator computing it directly.

### 8. The monitor — what the instrument IS for (Layer 2) [NEW]
- The constructive payoff: a live regime nowcast with claim-by-claim badges
  ([OOS] / [DESC] / UNSUPPORTED) and forecast-evaluation machinery (PIT, Christoffersen,
  CRPS/QW-CRPS, Amisano–Giacomini, Giacomini–White). A NOWCAST, not early warning — the
  lag stats (§3) are rendered prominently.
- Spec: `.planning/MONITOR-VALIDATION-SPEC.md`. Scoreboard doubles as the paper's honest
  ledger of which claims are OOS-validated vs descriptive.

### 9. Related literature
- Regime/JM allocation: Nystrup et al. 2020, 2021; Shu–Yu–Mulvey 2024 (JAM); Aydınhan
  et al. 2024 (continuous JM); JM+MPC (Mathematics, 2025).
- Deflation genre: Cederburg–O'Doherty–Wang–Yan 2020 (vol-managed fails OOS, 103 factors);
  DeMiguel et al. 2024.
- Vol-scaling incumbents: Moreira–Muir 2017; Barroso–Santa-Clara 2015 (momentum, the robust
  exception); Harvey et al. 2018.
- Bootstrap/utility: Fleming–Kirby–Ostdiek 2001; Politis–Romano 1994.

### 10. Discussion — scope and what would falsify us
- Scope: daily-horizon, single-market, cost/delay honest.
- **Named survivor hypotheses (not yet tested):** uses where lag-tolerance is STRUCTURAL —
  monthly/quarterly decision cadences where a reactive estimator's speed edge compresses.
  Momentum is the one factor whose vol-scaled incumbent is itself robust.
- **Parked, not concluded: graded/continuous state-conditioned exposure (Ch3).** The
  experiment was preregistered (Rev 3) and the runner built and tested, but the one-look
  was deliberately NOT spent: the §6b capability smoke showed the downside-feature
  estimator has one-directional power (it can detect de-risking but structurally cannot
  re-risk into positive-drift high-vol regimes) — reported here as a methods finding, and a
  reason the look is reserved for a stronger (post-v3) instrument. We claim no economic
  result on graded exposure.

### 11. Reproducibility
- Public git history: freeze commits precede one-look runs (3c3c419 → run; preregs in
  .planning/); frozen artifacts results/stage1*, oos_labels, allocation_*; numpy/pandas,
  tests pass; report.html regenerates all exhibits.

## Figure plan (export from report.html machinery)
1. Stability exhibit: ±2y label agreement 1.000 vs 0.809 — the instrument's headline (§3).
2. The ladder — every claim vs its honest bar (the program's one picture; §§4–6).
3. Race 1: fee vs null bands; equity curves with bear bands.
4. Race 2: risk-return map; two fees vs bands; conditional weights path.
5. Race 3: calibration/AUC of margin vs EWMA-vol across the 8 DGP cells.
6. Lag-race schematic from synthetic oracle-lag curves (§7).
7. Monitor scoreboard mock (§8).

## Defensibility requirements (pinned 2026-07-23 — Adam's "no rushing" directive)

The pushback we must survive, addressed in the manuscript itself:

1. **"Your variant differs from ours."** Document protocol equivalence with Shu–Yu–Mulvey
   meticulously (same features, estimator family, execution conventions); a dedicated
   appendix table mapping our choices to theirs, every divergence justified. Test their
   claims on their terms.
2. **"Your costs/delay are too harsh."** Surface sensitivity exhibits (delay=1 Race 1;
   break-even cost 305.6 bps); add Race-2 cost scaling from turnover in the appendix.
3. **"So you recommend EWMA/vol targeting?"** No — comparative-negative claims ONLY.
   B_react and VT won matched races; Cederburg et al. 2020 shows vol-managed strategies are
   themselves fragile OOS. The paper deflates a claim and validates an instrument; it
   prescribes no strategy.
4. **Selection-contamination honesty:** the atlas/anatomy are descriptive and hypothesis-
   generating; chapter hypotheses born from them require out-of-sample (international)
   confirmation; Race-2's H2 was reframed pre-freeze with the audit trail in git. The
   discipline is the contribution — exhibit it.
5. **Priority:** SSRN preprint as soon as §§1–7 are drafted — timestamp over polish; the
   2024–25 literature window is open now.

## Next actions (in order)
1. [ ] Assemble exact-numbers appendix tables from stage1.csv + allocation_summary.csv +
       calibration_gate.csv + sensor_validation.csv.
2. [x] ~~Draft §2 (discipline) and §6/§7 (mechanism)~~ — done, DRAFT-SECTIONS.md (framing-
       invariant; §6-mechanism draft now maps to §7).
3. [ ] Draft §3 (the instrument) — the new front-and-center section; pull stability/sensor/
       live numbers from §3 above.
4. [ ] Draft §1 (intro) against Shu–Yu–Mulvey's specific claims (quote their baselines),
       system-first.
5. [ ] Re-run figure exports as standalone SVG/PNG (report machinery → paper/fig/).
6. [ ] Decide LaTeX vs Typst vs Word for the manuscript skeleton.
