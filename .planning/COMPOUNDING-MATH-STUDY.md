# COMPOUNDING-MATH STUDY — the most efficient way to own equity risk

**Status: DESIGN (no look, no code yet).** The point where OFFENSE (own the engine) and DEFENSE (preserve
ownership capacity) fuse — and the **real-math spine of the eventual paper**.
**Last updated:** 2026-08-02.

---

## Objective

Maximize **sustainable geometric wealth under a real drawdown constraint** (the −30% budget), while keeping
the ability to stay invested and deploy. **NOT** max Sharpe, **NOT** max return, **NOT** min drawdown. The
question the math must answer: *"what is the most efficient way to own equity risk?"* — never "how much
leverage can we add?"

## What this study OUTPUTS (it feeds the allocation framework — NOT "Kelly says X%")

This study is a TOOL inside the decision framework (`PORTFOLIO-CONSTITUTION.md` → "The product is a decision
framework"). Its results map to the framework's four questions, with **confidence as an explicit output**, not
a point estimate:
- **Q1 engine selection →** framework Q1 (*what engine to own + why*) **and Q2** (*how much confidence* —
  measured as robustness across periods/countries + mechanism strength + post-publication decay, not a single
  in-sample number).
- **Q2 sizing →** framework Q4 (*what allocation maximizes expected compounding*) given framework Q3 (*risks to
  staying invested* — the drawdown budget + behavioral-failure threshold from the defense study).
- **Q3 diversifier-as-capacity →** the bridge to the defense: which sleeves raise within-budget geometric
  growth (ownership capacity), feeding Q4.
The deliverable is a confidence-weighted allocation *decision*, never "Kelly f* = X%."

**Q1 engine selection is CONFIDENCE-ADJUSTED, not max historical CAGR.** The question: *"given a set of possible
engines, which exposure gives the highest **confidence-adjusted** ability to compound wealth over decades?"* —
never "which had the highest geometric growth" (that selects the winner after seeing results). **Anti-selection
safeguard: the evidence/confidence score is PRE-COMMITTED from the mechanism map** (`EQUITY-OFFENSE-LITMAP.md`,
written before any compounding number) — BAB/low-vol strongest survives-being-known, momentum via limits-to-arb,
value unresolved, quality crisis-positive — so the CAGR numbers cannot retro-pick the engine. Per engine the
output answers: (1) what MECHANISM am I owning? (2) how strong is the evidence it persists? (3) how efficiently
does the exposure convert RISK into geometric growth? (4) how much CONFIDENCE to allocate?

**First-implementation output per engine:** g(f) curve · drawdown-by-exposure curve · volatility drag (empirical
vs Gaussian gap) · downside behavior (tail/skew) · evidence-confidence score (from the mechanism research).
**Decision rule = best combination of durable mechanism + compounding efficiency + confidence** — NOT "Engine A
had the highest CAGR." Only after the engine is selected do we study sizing → diversification → leverage →
deployment.

## The core math (the paper spine)

Terminal wealth is multiplicative: `W_T = W_0 · ∏ₜ(1 + f·rₜ)`, `f` = equity exposure. Its long-run growth is
the time-average of log returns, so the objective is `max E[log(1 + f·r)]` — the **Kelly / growth-optimal
criterion** (Kelly 1956; Latané 1959; Breiman 1961 — growth-optimal a.s. beats any other strategy long-run).

Taylor expansion:
```
g(f) ≈ f·μ  −  ½·f²·σ²        (return linear ; VOLATILITY DRAG quadratic)
f*   = μ / σ²                  (Kelly optimum)
g(2f*) = 0                     (over-betting ceiling — all return handed back to variance)
g(f*) = ½ · μ²/σ² = ½ · Sharpe²   (the max achievable geometric growth)
```

**The load-bearing result — `g(f*) = ½·Sharpe²`** — and its two consequences that structure the whole study:
1. **Under free leverage, engine selection collapses to "maximize Sharpe," and leverage CANNOT rescue a weak
   engine.** A low-Sharpe engine has a low growth ceiling that no sizing can lift (sizing up just hits the
   drag ceiling at `2f*`). Adam's "don't let leverage hide a weak engine" is thus *proven by the math*, not
   asserted.
2. **Low-volatility's advantage is ENTIRELY a constraint phenomenon.** Equal Sharpe ⇒ equal ceiling; low-vol
   only wins under a **drawdown/leverage constraint** by getting *closer* to that ceiling (its lower σ hits
   the −30% wall later). That's the real world, and where low-vol + the diversifiers earn their keep.

We are **drawdown-constrained, not growth-constrained**: Kelly `f*` usually sits *above* the budget-allowed
exposure, so the real question is the geometric growth forfeited by capping at the budget. Real returns are
fat-tailed/skewed → use the **empirical** `E[log(1+f·r)]` on real data (report the Gaussian approx alongside;
the gap = the higher-moment cost).

## The two separated questions (sequence: mechanism → exposure → geometric efficiency → sizing)

**Q1 — ENGINE SELECTION (sizing-neutral, leverage-honest).** Rank mechanism-backed engines — broad beta,
low-vol/BAB, quality/profitability, momentum, and combinations — by BOTH:
- (a) **Sharpe** — the leverage-free efficiency ceiling `½·Sharpe²`; and
- (b) **geometric growth achievable within the −30% budget at capped/zero leverage** — the *usable* efficiency.
Reporting both exposes whether an engine's edge is *intrinsic* (higher Sharpe) or merely *leverable capacity*
(same Sharpe, lower σ). No engine can hide behind sizing.

**Q2 — EXPOSURE SIZING (given the engine).** `max g(f)` s.t. `maxDD(f) ≤ 30%`, leverage **explicit and
capped**. Deliver the growth-vs-exposure curve, Kelly `f*` vs. the budget-constrained `f`, the growth forfeited
to the constraint, and the half-Kelly comparison (≈¾ the growth, far less drawdown).

**Q3 — DIVERSIFIER AS OWNERSHIP CAPACITY (the defense fusion).** A diversifier is justified **only if it
raises the geometric growth achievable *within the budget*** — via (i) lower portfolio σ → more equity-
ownership capacity, (ii) the **rebalancing bonus / diversification return** ≈ `½(Σwᵢσᵢ² − σ_p²)` (Booth-Fama
1992; Fernholz volatility harvesting), and (iii) deployment convexity (buying equity at drawdown lows) — NET
of its calm-period drag. Not "it's defensive." Gold's 27-year drought FAILS this test if its drag exceeds its
capacity + rebalancing value. This is the precise, quantitative restatement of the defense thesis.

## Discipline

- Leverage is a capped **output**, never the lever that flatters a weak engine. The sequence above is enforced.
- No look; this is characterization + closed-form/empirical math on historical data. The eventual PORTFOLIO
  SUPPORT claim (driver-balanced vs. 60/40, `PORTFOLIO-TEST-PREREG.md`) still needs the paused prereg +
  overnight cooling-off + dated sign-off.
- Engine tilts (low-vol/quality/momentum) must clear the mechanism gate + the lit-map durability (McLean-
  Pontiff decay, net of cost); this study measures geometric EFFICIENCY — a tilt's actual inclusion still
  needs its Tier-2 falsification.

## Data

Monthly: equity (`mkt`), cash (`rf`), bond, gold, trend, commod (`econ_driver_monthly.csv`, `assets_daily.csv`).
Engines: market beta; low-vol/BAB (`build_bab.py`); quality/profitability (RMW); momentum (`mom` /
`cross_sectional_momentum.py`). International (Japan/Europe) for the robustness leg.

## Build plan

`scripts/compounding_math.py` — three parts mapping to Q1/Q2/Q3, Gaussian vs. empirical `E[log W]` throughout.

## OPEN CONFIRMS before coding (the only things to settle)

1. **Leverage cap — LOCKED (Adam, 2026-08-02): strictly unlevered baseline (f ≤ 1.0).** "What should we own
   and why" precedes "how much leverage." Leverage is a later implementation question, shown only as a
   clearly-separate sensitivity, and only if the evidence (a lower-vol engine / structural opportunity) earns it.
2. **Build approach:** scaffold I/O + plotting and **guide Adam through writing the ~15-line `g(f)` /
   empirical-Kelly core himself**, vs. build whole and read together. (Adam's standing learning-mode pref =
   guide the core.)

## Paper note

This study is the real-math spine of the eventual paper: **geometric ownership efficiency under a drawdown
constraint, with diversifiers reframed as ownership capacity.** Mechanism-based, survives being known, not a
backtest — exactly the "valid thing + valid paper with real math" goal.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
