# V2 Prereg — Statistical Jump Model, Economic-Value Evaluation (Chapter 1 of v2)

Status: **DRAFT — DESIGN REVISION PENDING, DO NOT SIGN AS-IS.** The Phase-1 synthetic battery
(2026-07-22, `results/v2_synthetic_validation.csv`) falsified the §5 primary as a capability: on
panels with TRUE regimes, oracle detection beats vol targeting by +136..+1090 bps, but a 10-21d
detection lag erases most/all of it, and the causal pipeline captures ≈none (fee −1027..+263).
The pipeline DOES beat buy-and-hold when regimes exist (the literature's actual claim). §5 must be
re-decided by Adam before freeze — candidate revision: primary = fee(JM−B&H) replication claim,
co-primary deflation exhibit = fee(JM−VT) with pre-declared expectation ≤ 0. No real-data model
result exists as of writing; blind intact.
Written: 2026-07-22. Companion plan: `.planning/V2-JUMPMODEL-PLAN.md`.
Construction gate: PASSED 2026-07-22 (`results/v2_construction_gate.csv`) — data built, no model run on it.
Synthetic validation: `results/v2_synthetic_validation.csv` (synthetic panels only; blind intact).

## §1 Hypothesis

H1: A K=2 statistical jump model (Bemporad et al. 2018; Nystrup et al. 2020; Shu/Yu/Mulvey 2024)
on return-derived downside features, fit and deployed under fully causal protocol, delivers positive
economic value over a matched volatility-targeting baseline, net of costs — measured as a positive
Fleming/Kirby/Ostdiek performance fee.

This does NOT re-ask v1's "information beyond vol" question statistically; the vol-target baseline IS
the vol axis, and the claim under test is the field's own (economic value of persistent regime
switching), imported into our discipline. Scope: US equity market, daily, 1950+.

## §2 Data (frozen)

`data/processed/v2_daily.csv`: Ken French daily market total return (Mkt-RF + RF) and RF,
1926-09..2026-05, construction gate G1-G5 PASSED. Panel truncated to **1950-01-01** for this
experiment (post-war market structure; matches the literature's avoidance of depression-era training).
Features (from `v2_core.build_features`, frozen): dd10 = EWM downside deviation (halflife 10d);
sortino20, sortino60 = EWM mean / EWM downside deviation (halflives 20d, 60d). Return-derived only —
no revised macro series, no VIX; the vintage-lookahead problem class is out of scope by construction.

## §3 Model & causal protocol (frozen)

- K=2 jump model, `v2_core.fit_jump_model` (n_init=8, seed=0), identification: state 0 = lower dd10
  center (calm), state 1 = stressed.
- Expanding walk-forward: initial training window = first 3024 trading days (~12y: 1950–1961);
  refit every 252 trading days; OOS scoring ≈ 1962-01 .. 2026-05.
- Per refit: λ selected from the frozen grid {10, 25, 50, 100, 200, 400, 800} by strategy Sharpe on
  the last 1008 days of the training window (validation), sub-train z-scoring, net of costs and delay
  (`v2_synthetic_validation.select_lambda`, same code path). Ties → larger λ.
- Standardization: feature mean/std computed on the training window at each refit, frozen for the
  next block (causal).
- OOS inference: greedy online classification (`v2_core.online_classify`) with centers/λ/z-params
  frozen between refits, state chained across refit boundaries. Filtered only; no smoothing.
- One look: the primary is computed once, after all controls are in place.

## §4 Strategy & baselines (frozen)

All strategies: long-only w ∈ [0,1], 1-day execution delay, 10 bps one-way proportional costs,
cash leg earns RF. (`v2_eval.strategy_returns`)
- JM: w=1 in state 0, w=0 in state 1.
- **VT (primary baseline): vol targeting** — w = clip(10% / EWM-vol(halflife 20d, annualized), 0, 1).
- SMA200: w=1 iff cum-TR index > its 200-day SMA (secondary baseline).
- B&H: w≡1 (secondary baseline, costless).

## §5 Primary metric & support bar (frozen)

**Fee(JM − VT) at γ=10** (`v2_eval.fko_fee`), annualized bps over the full OOS era, with 90% CI from
the paired stationary bootstrap (mean block 126d, B=2000, seed=0).
**SUPPORT requires: fee > 0 AND the 90% CI excludes 0 AND all §7 controls clean.**

## §6 Pre-declared falsifiers

- F1 Economic null: fee ≤ 0 or CI includes 0 → the field's positive claim does not survive causal,
  cost-aware evaluation. (Chapter recorded as null; see §9.)
- F2 Estimator not in working regime: chosen λ sits at a grid edge (800, or 10 with >12 switches/yr)
  in more than 1/3 of refits → verdict "not identified", not "supported".
- F3 Persistence failure: OOS regime switches > 12/yr → untradeable label; economic result moot.

## §7 Pre-declared controls (run before looking at the primary)

- C1 Placebo signal: 100 random 2-state Markov signals with switch frequency matched to the JM's OOS
  label; JM fee must exceed the placebo 95th percentile.
- C2 Surrogate panels: 10 stationary-block-bootstrap surrogates of the return series (mean block 21d;
  destroys genuine regime timing, keeps unconditional moments/clustering blocks); full pipeline fee on
  surrogates forms a null band; a positive primary must exceed its max.
- C3 Simulation calibration: 10 iid panels with matched unconditional moments through the full
  pipeline; primary must lie outside this null band for support.

## §8 Secondaries (reported, not gating)

Fee at γ=1; fee vs SMA200 and B&H; Sharpe/MaxDD/Calmar/turnover table for all strategies; era halves
(1962–1989 / 1990–2026, the latter = Shu/Mulvey replication comparison); leave-one-crisis-out over the
10 pre-named windows (`v2_build.CRISIS_WINDOWS`); λ-choice history; **label stability**: re-run with
train start shifted ±2y, report OOS label agreement (variance-sorted identification) vs the incumbent
ensemble's 80.9% mean agreement.

## §9 Case classification & consequences (frozen wording)

- **Case A** (fee>0, CI excl. 0, controls clean, F2/F3 clear): field claim survives. Proceed to
  Phase 4 instrument swap evaluation.
- **Case B** (fee>0, CI incl. 0, stability ≥ incumbent, switches/yr < incumbent): research verdict
  null-leaning; instrument swap may still proceed on stability/turnover grounds alone (practical-win
  path, pre-authorized here).
- **Case C** (fee ≤ 0, stability ≥ incumbent): economic claim refuted under discipline — recorded as
  the v2 Chapter-1 null (a deflation of Shu/Mulvey-class claims); swap decision on stability grounds
  only if Adam separately approves.
- **Case D** (F2 or F3 triggered): estimator rejected in this configuration; no swap; record.
- Incumbent head-to-head fee comparison is NOT part of this prereg (incumbent OOS labels span only
  2024+, unpowered); the Phase-4 swap criterion is stability + turnover + this experiment's verdict.

## §10 Stopping rule

One run, one look, frozen case classification. No design change after freeze; any construction bug
discovered before the primary is looked at → fix, document, re-freeze (v1 Case-E convention).
Results go to RESEARCH-RECORD.md as v2 Chapter 1 regardless of outcome.

---
**FREEZE SIGN-OFF (Adam):** ______________  date: __________

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
