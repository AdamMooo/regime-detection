# Paper — Does Regime Detection Add Investment Value? Two Preregistered Nulls Against Honest Baselines

Status: OUTLINE (started 2026-07-23, decision: this is the program's chosen deliverable).
Working title above; alternates: "Regime-Switching Value Is a Baseline Artifact" /
"The Detection-Lag Race: Why Regime Signals Lose to Reactive Estimators".

Venue path: SSRN preprint → Journal of Asset Management (where Shu–Yu–Mulvey 2024 landed;
the direct conversation) or Critical Finance Review (the replication/deflation genre).

## The claim in one paragraph

The applied regime-switching literature (statistical jump models: Nystrup et al. 2020–21;
Shu, Yu & Mulvey 2024; JM+MPC 2025) reports that regime-aware strategies beat buy-and-hold
and improve risk-adjusted returns. We run the field-standard estimator under preregistered,
one-look discipline with two additions the literature omits: (i) exposure-matched null
distributions (random persistent signals with matched transition rates, timing-destroyed
surrogates, iid pipelines) and (ii) reactive incumbents as co-primary baselines (volatility
targeting; EWMA covariance). Both economic claims die. The overlay's +488 bps/yr utility fee
vs buy-and-hold sits inside every null band and loses to vol targeting by a significant
−256 bps/yr; feeding the same label to a covariance-conditioned multi-asset allocator adds
+2.8 bps/yr vs its unconditional twin (inside all bands) and loses −29 bps/yr to a plain
EWMA twin. The mechanism is a detection-lag race: in silico, even an oracle regime signal
loses its edge at 10–21 day recognition lags, and causal filters lag ~5–20 days. The one
durable positive is statistical, not economic: the jump-model label is an exceptionally
stable instrument (100.0% label agreement under ±2y training-window shifts vs 80.9% for an
HMM ensemble), making it a useful market-state sensor even though conditioning on it is
economically dominated at daily horizons.

## Sections & the numbers that go in them

### 1. Introduction
- The regime-value claim and its baseline problem (B&H-grade comparisons).
- Contributions: (a) preregistration with freeze-before-run in public git history;
  (b) exposure-matched nulls; (c) reactive co-primary baselines; (d) the lag-race
  mechanism; (e) the instrument-vs-strategy distinction.

### 2. Discipline (methods overview)
- Prereg → freeze → one look; controls computed before primaries; frozen classifications.
- Causality: expanding windows, per-refit frozen params, DP-endpoint filter, next-close
  execution (delay=2), 10 bps one-way.
- Metric: FKO (2001) quadratic-utility fee, γ=10 headline, γ=1 secondary; paired
  stationary bootstrap 90% CIs (mean block 126d, B=2000).

### 3. Experiment 1 — trading the label (the literature's claim)
- K=2 jump model, downside features (dd10/sortino20/sortino60), λ by 8y-validation
  Sharpe, annual refits; French daily TR 1926+, trained from 1970, OOS 1990-03..2026-05
  (n=9120).
- fee(JM−B&H) = +487.8 [−47.4, +1138.8]; placebo 95th = 541.3; surrogate band
  [41, 1080]; iid band [179, 805]; matched static mix beats the overlay (−48.7);
  γ=1 fee = −314.
- fee(JM−VT) = −255.8 [−477.5, −36.7] — significant loss to the honest bar.
- Verdict: the beat-B&H fee is an exposure/utility artifact.

### 4. Experiment 2 — conditioning covariance on the label
- Long-only ERC {equity, 10y Treasury TR, gold, cash}, caps 75/75/25, 8% vol target
  (scale-down only), hard-state conditional covariance (expanding per state, ≥500-day
  activation, 0.5 shrinkage), monthly + state-flip rebalance.
- fee_A(cond−B_match) = +2.8 [−3.2, +8.4]; placebo 95th 5.8, shuffle 95th 4.9, iid
  [−1.8, +1.0] → inside bands.
- fee_B(cond−B_react EWMA λ=0.97, from activation) = −29.1 [−66.8, +8.5]; B_react best
  arm outright (Sharpe 0.878 vs 0.826); era split +8.4 pre-2000 / −37.7 post-2000.
- Mechanism check survives: vol-of-vol 2.11 vs 2.15pp (F2 clear) — conditioning does
  stabilize risk; it is dominated at it.
- Design provenance: pre-freeze audit corrected the atlas's pooled-vs-per-episode
  fallacy (stock–bond corr deepening holds 11/23 episodes; 1990s +0.07; 2022 stress
  corr +0.11) — include as a warning exhibit about LOEO-style stability claims.

### 5. The instrument result
- Label stability 1.000/1.000 under ±2y train-start shifts (incumbent ensemble 0.809);
  1.66 switches/yr; 30 episodes, all genuine high-vol environments (calm vol ~14%,
  stressed ~25%); catches 15/18 ex-post −15% bears, median 20d lag, misses fast crashes
  (1998, 2018Q4) — a vol-state sensor, not a bear detector.
- Live capability: SPY-splice tail (corr 0.9957 gate), 1.0000 agreement on overlap.

### 6. Mechanism — the detection-lag race
- In-silico: oracle regime knowledge beats VT; at 10–21d recognition lag even the
  oracle loses; causal filters lag ~5–20d. Reactive estimators (VT, EWMA) need no
  recognition step. Frame: regime value is an information-timing claim, and the timing
  is the binding constraint at daily horizons.

### 7. Related literature
- Regime/JM allocation: Nystrup et al. 2020, 2021; Shu–Yu–Mulvey 2024 (JAM); Aydınhan
  et al. 2024 (continuous JM); JM+MPC (Mathematics, 2025).
- The deflation genre: Cederburg–O'Doherty–Wang–Yan 2020 (vol-managed portfolios fail
  OOS across 103 factors); DeMiguel et al. 2024 (multifactor nuance).
- Vol scaling incumbents: Moreira–Muir 2017; Barroso–Santa-Clara 2015 (momentum, the
  robust exception); Harvey et al. 2018 (vol targeting impact).
- Bootstrap/utility metrics: Fleming–Kirby–Ostdiek 2001; Politis–Romano 1994.

### 8. Discussion — what would falsify us
- Scope: daily-horizon, single-market, cost/delay honest. Named survivor hypothesis:
  uses where lag-tolerance is structural (monthly-cadence factor exposure; momentum is
  the one factor where the vol-scaled incumbent is itself robust). Pre-committed gate
  for any chapter 3.

### 9. Reproducibility
- Public git history: freeze commits precede one-look runs (3c3c419 → run; prereg docs
  in .planning/); frozen artifacts results/stage1*, oos_labels, allocation_*; all code
  numpy/pandas, tests 24/24; report.html regenerates all exhibits.

## Figure plan (export from report.html machinery)
1. The ladder — every claim vs its honest bar (program's one picture).
2. Ch1 fee vs null bands; equity curves with bear bands.
3. Ch2 risk-return map; the two fees vs bands; conditional weights path.
4. Lag-race schematic from synthetic oracle-lag curves.
5. Stability exhibit: ±2y label agreement (1.000 vs 0.809).

## Defensibility requirements (pinned 2026-07-23 — Adam's "no rushing" directive)

The pushback we must survive, addressed in the manuscript itself:

1. **"Your variant differs from ours."** Document protocol equivalence with Shu–Yu–Mulvey
   meticulously: same features (dd10/sortino20/sortino60), same estimator family, same
   execution conventions; a dedicated appendix table mapping our choices to theirs, with
   every divergence justified. Their claims must be tested on THEIR terms.
2. **"Your costs/delay are too harsh."** Sensitivity exhibits already exist (delay=1
   chapter 1; break-even cost 305.6 bps) — surface them prominently; add chapter-2 cost
   scaling from turnover in the appendix.
3. **"So you recommend EWMA/vol targeting?"** No — comparative-negative claims ONLY.
   B_react and VT won matched races; Cederburg et al. 2020 shows vol-managed strategies
   are themselves fragile OOS. The paper deflates a claim; it prescribes nothing.
4. **Selection-contamination honesty:** state plainly that the atlas/anatomy are
   descriptive and hypothesis-generating, that chapter hypotheses born from them require
   out-of-sample confirmation (international panels), and that chapter 2's H2 was
   reframed pre-freeze with the audit trail in git. Our discipline is the contribution —
   exhibit it, don't bury it.
5. **Priority:** SSRN preprint as soon as §§1–6 are drafted — the timestamp matters more
   than polish; the 2024–25 literature window is open now.

## Next actions (in order)
1. [ ] Assemble exact-numbers appendix tables from stage1.csv + allocation_summary.csv.
2. [ ] Draft §2 (discipline) and §6 (mechanism) — they carry the paper's identity.
3. [ ] Re-run figure exports as standalone SVG/PNG (report machinery → paper/fig/).
4. [ ] Intro draft against Shu–Yu–Mulvey's specific claims (quote their baselines).
5. [ ] Decide LaTeX vs Typst vs Word for the manuscript skeleton.
