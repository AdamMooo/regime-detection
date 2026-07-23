# Allocation Prereg — State-Conditional Covariance, Graded Multi-Asset Allocation (Chapter 2)

Status: **DRAFT — awaiting Adam's review + freeze sign-off. No real-data allocation backtest
has been run.** Written 2026-07-23, informed by the descriptive atlas (`results/atlas.csv`,
30/30 LOEO-stable cross-asset structure) — the atlas informs the design; it does not
constitute a look at the confirmatory result.

## §1 Hypothesis

H2: conditioning the COVARIANCE structure of a long-only multi-asset portfolio on the
jump-model volatility state adds economic value over the identical allocator built on
unconditional covariance — because stock-bond correlation deepens (−0.10 → −0.30), and
relative asset vols shift, reliably (30/30 episodes) in stressed states.

**Means are not used anywhere.** The allocator consumes second moments only — the object the
atlas showed is stable and the moment family where statistical confidence is highest.

Relation to prior nulls (the information gate): this HARVESTS the vol axis v1 proved is the
only real one — it does not claim information beyond it. v1 Chapter 3 (covariance
conditioning null) tested equity-internal eigenstructure with similarity kernels on 13 ETFs;
this tests cross-ASSET-CLASS covariance switching on a 2-state vol label with 60y of data —
different object, different mechanism (stock-bond corr sign, not equity eigenstructure),
explicitly acknowledged here.

## §2 Object & universe (to freeze)

- Universe: market equity (French mkt TR), 10y Treasury (synthetic TR), gold (GC=F, 2000+;
  weight forced 0 before gold data begins), cash (RF). Industries EXCLUDED (atlas: stressed
  correlations converge 0.83–0.92 — no reliable within-equity structure); factor legs
  EXCLUDED (long-short implementability; momentum's corr flip is design knowledge, not a
  position).
- Allocator: **equal-risk-contribution (ERC)** long-only over {equity, bond, gold}, cash as
  residual under a portfolio vol target of 8% ann. ERC uses only the covariance matrix — no
  expected returns. Weight caps: equity ≤ 0.75, bond ≤ 0.75, gold ≤ 0.25.
- Conditioning: covariance estimated per state from expanding causal windows of state-labeled
  days (min 500 days per state before conditioning activates; before that, unconditional),
  shrunk toward the unconditional estimate with fixed weight 0.5 (pinned; no tuning).
  Blend at each date by the filtered state: graded variant uses P(stressed) mapped from the
  filter evidence gap by a fixed logistic calibrated ON SYNTHETIC panels only (pre-freeze);
  hard-state variant is the pre-declared robustness check.
- States: the frozen chapter-1 label protocol, run causally (as in live_label.py).

## §3 Matched baseline & other arms (to freeze)

- **B_match (primary baseline): the IDENTICAL ERC allocator on the unconditional expanding
  covariance** — same universe, caps, vol target, costs, delay. The only difference is
  state-conditioning. This isolates the regime increment exactly.
- Context arms (secondary): 60/40 (monthly rebalance), vol-targeted equity (chapter-1 VT),
  B&H equity.

## §4 Execution (identical to chapter 1)

Next-close (delay=2), 10 bps one-way on |Δw| summed across assets, daily evaluation,
monthly rebalance (turnover discipline; pre-declared daily-rebalance sensitivity).
OOS scoring 1990+ (label availability), panel from 1963.

## §5 Primary metric & support bar (to freeze)

Fee(conditional ERC − B_match) at γ=10, annualized bps, 90% CI from the paired stationary
bootstrap (mean block 126d, B=2000, seed=0). SUPPORT requires fee > 0, CI excluding 0, and
§6 controls clean. Secondary: γ=1 fee; ΔMaxDD; ΔSharpe bootstrap CI; realized-vol tracking
error vs the 8% target per arm (a conditioning-value diagnostic: better vol tracking IS the
mechanism); turnover per arm.

## §6 Controls (pre-declared, run before the primary is looked at)

- C1 placebo states: 100 random persistent 2-state signals (transition rates matched to the
  real label) through the FULL conditional-ERC pipeline; fee vs B_match must exceed the 95th
  percentile.
- C2 episode-shuffled states: real stressed episodes relocated in time (preserving count and
  durations, non-overlapping); 10 draws; null band.
- C3 iid calibration: 10 simulated panels (matched unconditional moments, no state
  structure); null band.

## §7 Falsifiers

- F1: fee ≤ 0 or CI includes 0 → conditional covariance adds no allocation value net of
  costs (recorded as chapter-2 null; the atlas structure is then real but not economically
  harvestable at this cost/delay).
- F2: conditional arm's realized portfolio vol tracks the 8% target WORSE than B_match →
  mechanism failure regardless of fee.
- F3: turnover > 5× B_match → untradeable conditioning.

## §8 One look

One run, one look, frozen classification, results to RESEARCH-RECORD.md as chapter 2.
Runner will be `scripts/run_allocation.py` requiring `--confirm-frozen`.

---
**FREEZE SIGN-OFF (Adam):** ______________  date: __________

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
