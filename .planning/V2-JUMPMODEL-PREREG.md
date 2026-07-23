# V2 Prereg — Statistical Jump Model, Economic-Value Evaluation (Chapter 1 of v2) — REV 2, FROZEN

Status: **FROZEN 2026-07-22** per Adam's session direction ("wire it all up… really focus on 1990+",
after the battery finding and the two-agent backtest-methodology/code audit). Design changes
prohibited from here. No real-data model result exists at freeze; blind intact.
Rev history: Rev 1 (drafted earlier today) had primary = fee(JM−VT); the Phase-1 synthetic battery
falsified that as a capability (oracle beats VT by +136..+1090 bps but 10–21d detection lag erases
it; causal filters lag ~5–20d) — see `results/v2_synthetic_validation.csv`. Rev 2 re-aims the
primary at the literature's actual claim and demotes VT to a pre-declared deflation exhibit.

## §1 Hypothesis

H1 (replication claim, Shu/Yu/Mulvey 2024): a K=2 weighted statistical jump model on return-derived
downside features, deployed fully causally, adds economic value over BUY-AND-HOLD net of costs in the
modern era (1990+) — positive Fleming/Kirby/Ostdiek fee.
D1 (deflation exhibit, pre-declared expectation ≤ 0): the same strategy does NOT add value over
volatility targeting — in-silico analysis says VT subsumes regime value up to detection lag. D1 is
reported with the same rigor but does not gate support for H1.

## §2 Data & era (frozen)

`data/processed/v2_daily.csv` (French daily mkt TR + RF; construction gate PASSED, G1–G5).
Panel from **1970-01-01**; initial training window 5040 trading days (~20y) → OOS scoring starts
~1990 (Adam's era focus: modern, faster, more efficient markets; matches Shu/Mulvey's OOS era) and
ends at panel end (2026-05). Features frozen: dd10, sortino20, sortino60 (return-derived only).

## §3 Model & causal protocol (frozen)

K=2 weighted jump model (`v2_core.fit_jump_model`, n_init=8, seed=0, weight_iters=3, dd-quantile
init; state 0 = lower weighted-dd10 center). Expanding walk-forward, refit every 252d. Per refit:
λ from grid {10,25,50,100,200,400,800} by validation Sharpe on the last **2016d (8y)** of the
training window (field-standard window per the methodology sweep; sub-train z-scoring; same delay
and costs as deployment), ties → larger λ. Feature z-params, centers, weights, λ frozen per block.
OOS inference: causal DP-endpoint filter (`v2_core.filter_states`), V re-initialized per refit by a
forward pass over the training window with the new centers. Filtered only; one look.

## §4 Strategies & execution (frozen)

Long-only w ∈ [0,1]; cash earns RF. **Headline execution = next-close (delay=2)**: a signal from
day-t's close trades at day-t+1's close and first earns day-t+2's return — matching Shu/Mulvey's
"one-day trading delay" (audit finding M1: delay=1 is same-close execution and only a sensitivity).
Costs 10 bps one-way on |Δw| (conservative vs ~1–3 bps futures reality; kept for comparability).
Arms: JM (w=1 calm / 0 bear), VT (10% ann target, EWM hl=20 vol, cap 1), SMA200, B&H (costless).
VT/SMA weights computed on the full panel and sliced to OOS (fair warmup).

## §5 Primary metric & support bar (frozen)

**Fee(JM − B&H) at γ=10** (FKO 2001: quadratic utility on total returns, γ/(2(1+γ)) coefficient,
daily Δ solved in closed form, annualized bps), 90% CI from the paired stationary bootstrap
(mean block 126d — pre-declared, conservative vs Politis-White auto; B=2000, seed=0).
**SUPPORT requires fee > 0, CI excluding 0, and all §7 controls clean.**
Co-primary deflation exhibit: fee(JM − VT), same spec, same CI, expectation ≤ 0, non-gating.

## §6 Falsifiers (frozen)

- F1: fee(JM−B&H) ≤ 0 or CI includes 0.
- F2: λ at a grid edge (800, or 10 with >12 switches/yr) in >1/3 of refits → "not identified".
- F3: OOS switches > 12/yr → untradeable label.

## §7 Controls (run before the primary is looked at; all on the primary's footing — real rf)

- C1: 100 random persistent 2-state Markov signals with transition rates matched to the JM's OOS
  label (matches persistence AND average exposure — kills the beta/exposure confound); JM fee vs
  B&H must exceed the placebo 95th percentile.
- C2: 10 stationary-block surrogates resampling **(r, rf) pairs** (mean block 21d); fee band; a
  positive primary must exceed its max.
- C3: 10 iid panels (matched mean/std, rf = sample mean); same bar.

## §8 Secondaries (reported, non-gating)

fee at γ=1; fee vs SMA200; fee vs average-exposure-matched static mix (w̄ stock / 1−w̄ cash);
delay=1 sensitivity; break-even one-way cost c*; ΔSharpe(JM−B&H) 90% bootstrap CI on excess
returns; per-arm Sharpe/MaxDD/avg-weight/turnover table (Shu/Mulvey turnover benchmark ≈44%/yr);
λ path + churn; era halves (1990–2007 / 2008–2026); LOTO over post-1990 crisis windows (computed
by dropping days from precomputed full-path daily returns — exact for the fee, no stitched seams);
label stability vs train-start ±2y (variance-sort identification; incumbent bar 0.809).

## §9 Case classification (frozen wording)

- **Case A** (H1 supported: fee>0, CI excl 0, controls clean, F2/F3 clear): literature claim
  replicates under causal discipline. Report D1 either way. Proceed to Phase-4 swap evaluation.
- **Case B** (fee>0 but CI incl 0, F2/F3 clear): weak replication; practical path decided on
  stability + turnover vs the incumbent ensemble.
- **Case C** (fee ≤ 0): the field's positive claim fails causal, cost-aware evaluation — recorded
  as the v2 Chapter-1 deflation result.
- **Case D** (F2 or F3): estimator not in working regime; no swap; record.

## §10 Stopping rule

One run (`scripts/v2_stage1.py --confirm-frozen`), one look, frozen classification. Construction
bugs found before looking at the primary → fix, document, re-freeze (Case-E convention). Results
to RESEARCH-RECORD.md as v2 Chapter 1 regardless of outcome.

## §11 Audit trail

Pre-freeze sweeps (2026-07-22): backtest-methodology survey + adversarial code audit (agent
reports in session log; key items in `.planning/V2-JUMPMODEL-PLAN.md`). Fixes applied before
freeze: delay=2 headline (M1), rf footing in C2/C3 (M2), 8y λ-validation window, LOTO/era-half
moment-drop method (m2), 1989 era gap (m1), full-panel baseline warmup (m9), objective/center
resync on non-convergence (m5). Accepted-as-is minors documented in the audit: same-scale λ
selection note (m3), tie-break to larger λ (m4, self-penalizing via F2), k≥3 DP path untested
(m6, never invoked), dd10-separation degeneracy (m7, low probability, visible in stability
exhibit), max-of-10 control bands (m8, C1's 95th-of-100 is the strong leg), feature recompute
from era start (m10, causal and self-consistent).

---
**FROZEN 2026-07-22** — basis: Adam's explicit session direction to wire up and run the proper
backtest with 1990+ focus, primary re-aimed per his acknowledgment of the battery finding.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
