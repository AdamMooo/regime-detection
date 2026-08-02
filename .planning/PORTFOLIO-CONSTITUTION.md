# Portfolio Constitution & Strategic Framework

**Status:** ACTIVE DESIGN / brainstorming — no look spent, nothing preregistered, nothing implemented.
**Last updated:** 2026-08-02

This is the living design doc for a decades-holdable systematic ETF portfolio, being built layer by
layer with Adam. It **reframes/supersedes the momentum-centric `PRODUCT-PLAN.md`**: momentum is
demoted from "the whole equity book" to a small *cross-sectional tilt* inside a broad strategic core.
This is the "make it truly useful, not BDH-HMM-with-an-algo bolted on" direction.

---

## Thesis (crystallized with Adam, 2026-08-02) — the north star everything else serves

This is **NOT an asset-allocation problem. It is an equity-ownership optimization problem.**

> The objective is to maximize lifetime compounded wealth through ownership of equity risk. Alternative
> sleeves are justified ONLY if they improve the ability to MAINTAIN, REBALANCE, or INCREASE equity exposure
> through adverse regimes. They are not return substitutes for equities; they are structural tools that
> protect the compounding engine.

The ultimate question is not *"can we make a portfolio that hurts less?"* It is: **"can we own the same
economic engine with fewer interruptions to compounding?"** So the headline metric is **EQUITY
PARTICIPATION** — how much of equity's upside we capture vs. how much of its downside we avoid (up-/down-
capture ratios). A book near **~95% up / ~70% down** owns the engine more efficiently. A diversifier that
reduces equity exposure or substitutes for equity return has FAILED its purpose; one that supplies dry powder
to rebalance INTO beaten-down equity — or lets us hold MORE equity within the drawdown budget — has served it.

---

## The product is a decision framework, not a number (Adam, 2026-08-02)

The end goal is NOT a theoretical Kelly portfolio or a factor model for its own sake. It is **an allocation
framework that increases confidence in capital-allocation decisions over decades.** The final output is never
"Kelly says X% exposure" — it is a confidence-weighted answer to four questions:

1. **What is the expected long-term return engine?** (what to own + why)
2. **How much confidence do we have in that engine?** (robustness / durability / mechanism strength)
3. **What risks could impair staying invested?** (the failure modes + behavioral/drawdown limits)
4. **Given those risks, what allocation maximizes expected compounding?** (sizing under the real constraint)

Everything else — the defense study, the mechanism map, the compounding math — is the **evidence pipeline**
that gives confidence in those four answers. The studies are tools; **the allocation framework is the
product.** Defense answered *what threatens compounding / what protects / what capital to preserve*; offense
answers *what engine to own / how much can we rationally hold / when does more risk improve compounding vs.
just raise the probability of behavioral failure*. **Unlevered (f ≤ 1) is the baseline** — "what should we own
and why" precedes "how much leverage"; leverage is a later implementation question, only if the evidence
earns it.

## Phase 0 — Investment Constitution

- **Goal:** maximize long-term wealth *while* holding a portfolio through severe drawdowns — AND
  participate efficiently, not merely defend. (A bunker that never participates is also a failure.)
- **Horizon:** multi-decade.
- **Constraints:** no leverage; no forced selling; no market timing; limited turnover; every rule executable.
- **THE binding design variable — ~-30% drawdown budget.** The depth beyond which Adam would start
  wanting to *meddle* (NOT capitulate — he holds most drawdowns intellectually; the risk is
  discretionary override, not selling). Treat as a *target shape* for a normal bad bear, tolerating
  ~-32/-35% only in a genuine tail. **The whole portfolio is solved BACKWARD from this:**
  `maximize wealth s.t. drawdown <= budget`. (Standard-lit: drawdown control / CDaR — Grossman-Zhou,
  Chekhlov-Uryasev-Zabarankin.)

## The edge — structural alpha, not forecasting alpha (Adam, 2026-08-02)

The opportunity is NOT a regime model that predicts the future (that contradicts everything the closed nulls
taught). The edge is that **most investors optimize an incomplete problem** — they allocate on *unconditional*
average returns, correlations, and Sharpe ratios that HIDE state-dependent exposures. Identify the independent
risks that actually drive outcomes, build efficient exposure to each, and the portfolio is more efficient than
the naive one WITH NO FORECAST:
- higher return for the same drawdown budget, or similar return with materially better downside control;
- greater ability to STAY INVESTED through hard periods (the behavioral edge);
- better deployment of risk when opportunities are genuinely attractive.

This is mechanism-gate compliant precisely because it **survives being known** — it is architecture, not a
signal to arbitrage. Everyone can SEE 60/40, yet its hidden bet persists because it is structural/behavioral,
not informational.

**The success test (Adam, 2026-08-02) — geometric compounding, NOT drawdown or Sharpe.** The PRIMARY
objective is long-term wealth COMPOUNDING: sustainable geometric CAGR from productive assets, primarily
equities. Drawdown control is a TOOL, not the objective — large drawdowns damage compounding (forced/
behavioral selling, capital unavailable when opportunities appear, multi-year recovery = lost compounding),
so the −30% budget is a **constraint / feasibility boundary, never the optimization target.** The real
question: *does understanding independent risk drivers let us own EQUITY RISK MORE EFFICIENTLY — capture
equity-LIKE long-term CAGR while cutting the severity and duration of the drawdowns that threaten staying
invested?* **REJECT any portfolio that merely lowers volatility by sacrificing CAGR.** Evaluate on:
(1) long-term CAGR vs 100%-equity and 60/40; (2) return retained through difficult periods; (3) maxDD +
recovery time as compounding damage; (4) probability of remaining invested through historical stress;
(5) whether diversification improves the GEOMETRIC return, not just the risk statistics. Never predictive
accuracy. The point is not a safer portfolio — it is more efficient ownership of equity risk.

**First worked example (already in the episode data):** 60/40 implicitly assumes the bond hedge works in
EVERY equity crisis. The study falsifies that — in the inflationary/rate bear (2022) the bond "ballast" was
**−16.6% while equity also fell**, a second source of loss, not a hedge. 60/40 is a concentrated, hidden bet
that *all bears are deflationary*. That hidden bet is the kind of thing this architecture exists to remove.

## Architecture hierarchy (locked, confirmed by Adam 2026-08-02)

Four tiers of *decision authority*, in strict order. Construction constraints are mechanics applied across
tiers, not a tier of their own.

1. **Strategic Core (L1) — the majority (~85-90%).** Permanent exposures designed around long-term
   risk/return objectives and the drawdown budget. STATIC. **Never changed because of a short-term market
   view.** The whole portfolio is solved backward from this.
2. **Evidence-Based Tilts (L2A) — bounded budget (~10-15%).** High-conviction, cross-sectional deviations
   from the core: momentum, factor, geographic, sector tilts. A tilt earns its place only by clearing the
   evidence gate (below) — economic mechanism + robust evidence + OOS validation + realistic implementation
   + bounded risk. Cross-sectional composition only; never moves total exposure.
3. **Diagnostics / Monitoring (L4).** Understand the environment; flag when assumptions are being
   challenged; prevent emotional overrides. A DASHBOARD — a panel of independent reads, no single-model
   authority. **Diagnostics do NOT automatically control allocations.** Live (`regime_card.json` ->
   portfolio-manager).
4. **Research Vault.** Experimental ideas that are NOT authorized portfolio decisions: regime models,
   time-series allocation, dynamic risk management. **Not banned — but a much higher evidence threshold**
   than a cross-sectional tilt, because changing TOTAL exposure introduces timing risk (closed 5×). Nothing
   here moves money until it graduates on its own independent validation.

**Construction constraints (L3, mechanics):** position/sector caps, turnover budget, tracking-error ceiling,
diversifier sizing — applied across L1+L2A to keep a good signal from becoming a bad portfolio.

**Option A confirmed** (derived from roles, not asserted): everything with a STRATEGIC risk-shaping
job (equity / bonds / diversifiers) is core; only cross-sectional tilts are satellite.

## Sleeve roles (the "is NOT" lines are the guardrails against drift)

- **Global equity core** — JOB: capture the equity risk premium, the dominant source of long-run
  wealth. IS NOT a diversifier or crash hedge; it is the thing that crashes (that's it doing its job).
- **Nominal bonds** — JOB: reduce drawdown (ballast) + be dry powder to rebalance into equity. IS NOT a
  return engine, and NOT a reliable equity hedge (2022 correlation flip).
- **Diversifiers (gold / trend, trend-tilted)** — JOB: cover the regime where bonds fail (inflation,
  prolonged trending crises). IS NOT a return engine, NOT a timing signal (held STATICALLY — Path-B closed).
- **Momentum satellite** — JOB: small, capped cross-sectional active bet for marginal excess return.
  IS NOT the growth engine, NOT a timer, NOT allowed to move total risk. Gated on IMPLEMENTABILITY
  (research-object validity != tradeable-ETF validity), not just economic validity.
- **Diagnostics** — JOB: report where we are, for holding-power + client comms. IS NOT an allocator.

## The two hard rules that keep it honest

1. **Every signal is one of two things, never in between:** (a) mechanical + backtested (pre-committed
   rule, must beat the no-signal version OOS net of complexity) OR (b) behavioral + never moves money.
   Ban the fuzzy "informs a discretionary decision that happens to move money" middle.
2. **Bright line — tilt the composition, never the dial.** CROSS-SECTIONAL tilts (always fully
   invested; tilt toward better-compensated exposures) = the permitted door. TIME-SERIES tilting
   (dial total exposure up/down by how attractive the environment looks) = market timing = CLOSED 5x.
   "Systematic/evidence-based" does NOT rescue time-series timing — the five nulls WERE systematic.
   Mechanism gate agrees: cross-sectional = a paid risk premium; time-series timing = forecasting
   (arbitraged away if it worked and were known).

## Falsification battery — what would prove this framework WRONG (Adam, 2026-08-02)

A structural-alpha thesis is only worth anything if it survives attempts to break it. Before optimizing
ANYTHING, run the tests that could kill it. Each has an explicit FAILURE condition:

1. **Small-sample / event-fitting.** Independent drivers, or a handful of memorable events? The inflationary-
   bear archetype rests on ~2 episodes (1973-74, 2022) — only ONE with investable commod/trend. FAILS IF the
   two-axis structure / bond-fails-in-inflation doesn't survive subsampling, or effective-N ≈ 1.
2. **Out-of-US.** Does failure-mode coverage hold in Japan & Europe (data in hand, did NOT generate the
   hypothesis)? FAILS IF bonds don't fail in int'l inflationary bears, or the archetypes don't replicate.
3. **Right metric.** Judge the TOTAL portfolio's return/drawdown/survivability — not a sleeve's crisis return.
   FAILS IF sleeves with great crisis returns don't improve the portfolio frontier.
4. **Selection bias / cost of insurance.** Include the periods these assets FAILED (gold 1980-2000,
   commodities 2010s, trend 2010-19), not just where they worked. FAILS IF calm-period drag at a reasonable
   weight exceeds the crisis payoff.
5. **Complexity.** Add sleeves one at a time; does each marginally improve the frontier after costs? FAILS IF
   a simpler book matches the complex one — then the simpler book WINS.

**Gold / commod / trend — the redundancy (spanning) test.** NOT "did it work in event X" but "does it provide
a UNIQUE exposure not replicable by the combination of the others?" Regress each on {other diversifiers +
bond + cash}; redundant iff high R² AND ~0 unique payoff in the uncovered failure mode. Resolve on >1 event.

**The final test (needs prereg + cooling-off — it is a POSITIVE claim):** does a driver-balanced STATIC book
beat a traditional allocation on the efficient frontier AFTER implementation, costs, complexity, and the long
boring periods where nothing happens? If not, the naive portfolio wins and that is the correct answer.

## The complexity test (the final gate before adding anything)

Before adding any sleeve, tilt, signal, or model, ask: *"Does this improve the investment process enough to
justify the additional complexity, implementation burden, and behavioral risk?"* **If the answer is unclear,
simplicity wins.** The goal is not maximum diversification or maximum sophistication — it is the MINIMUM set
of independent, understandable exposures needed for a robust portfolio.

## Tilt budget & evidence gate (bounded active views ARE part of the architecture)

The constitution does **not** ban active views. It *separates* two things and governs each differently —
the goal is discipline, not the elimination of deviation:

- **Permanent strategic allocation (L1, dominant, ~85-90% of the book):** static, held always, sized by
  the drawdown budget and the driver-spanning requirement. Never moved by a view.
- **Evidence-based deviations (L2 tilts, bounded):** a *legitimate* architectural element — capped, and
  usable only once the specific tilt has cleared an explicit evidence gate.

**The tilt budget (the hard cap on active risk):**
- ≤ ~10-15% of the book may express active tilts; equivalently, an active tracking-error ceiling set in L3.
- A tilt reallocates *within* the fully-invested book (cross-sectional composition). It may **never** move
  total portfolio risk / net market exposure — that is the dial, and the dial is closed (bright line).
- No tilt may breach the L3 position / sector caps.

**The evidence gate (what a candidate tilt must clear BEFORE it may draw on the budget):**
1. **Mechanism** ([[mechanism-gate]]): a written structural reason it survives being *known* — a paid risk
   premium or a durable risk-management fact. Novelty / backtest-fit / "it's in the literature" = disqualified.
2. **OOS net of complexity:** beats the no-tilt static version out-of-sample, net of costs *and* net of the
   complexity it adds.
3. **Pre-committed mechanical rule** (hard rule 1a): fully specified before the look; no discretionary
   "informs a decision that moves money" middle.
4. **Implementability:** research-object validity ≠ tradeable-ETF validity (the momentum gate).

Momentum is the one tilt that has cleared (validated cross-sectional). Value / quality remain *eligible but
unproven* at satellite weight (the long-only +0.96-corr trap) — they may draw on the budget only if they
later pass this same gate. A tilt that has not cleared the gate does not exist as far as the book is concerned.

**Boundary (unchanged, not reopened here):** time-series exposure-dialing — moving gross/net exposure by how
attractive the environment looks — is **not** a tilt and is **not** in this budget. It is the dial, closed
5×. Any future dynamic-allocation research lives in the **Research Vault (tier 4)** on its own independent
validation; it does not borrow the tilt budget's legitimacy.

## Output contract for the economic-driver study (LOCKED — the study reports into this shape)

**This study is a STRUCTURAL CHARACTERIZATION study, not a tactical allocation model.** It does not
answer "what should we overweight in this regime?" It answers: *"What economic risks exist, and which
permanent sleeves historically provide exposure that helps address those risks?"*

> **This document is a portfolio constitution, not a tactical model. Economic regimes are used only to
> understand historical asset behavior and structural risks. They do not authorize allocation changes.
> Any future dynamic allocation research must be treated as a separate hypothesis requiring independent
> validation.**

**The one and only deliverable** — one row per candidate sleeve (Adam's five fields, 2026-08-02):

| Sleeve | Economic role | Problem it solves | Evidence FOR inclusion | Evidence AGAINST inclusion | Conditions to remove / reconsider |
|---|---|---|---|---|---|

- Every sleeve must have **a reason it exists, a reason it might fail, and a clear role.** The last two
  columns are mandatory — a constitution without a falsifier and a removal trigger is a story.
- Goal is **not** maximum diversification. Goal = the MINIMUM set of *independent, understandable*
  exposures needed for a robust portfolio (the complexity test applies to every candidate row).
- State conditioning is used *diagnostically to characterize a sleeve's risk exposure* — to justify its
  **presence and static size-band** — never *prescriptively to vary its weight*. The sleeve is held
  ALWAYS, because the latent risk is always present and we have conceded we cannot time it.

**How a sleeve is judged (Adam, 2026-08-02) — COVERAGE, not per-asset verdicts.** A sleeve is NOT removed
just because its payoff is CONDITIONAL — insurance is conditional by nature. The test is: *does it provide
enough UNIQUE protection across the SET of failure modes to justify permanent inclusion at a reasonable
weight?* — never *does it hedge every crisis?* No single sleeve works everywhere; the COLLECTION covers
each other's weaknesses. For a conditional hedge (e.g. gold): the question is whether its FAILURE regime
OVERLAPS the rest of the portfolio's failures (redundant → drop) or fills an otherwise-UNCOVERED gap (keep).
A mechanism must survive MORE THAN ONE event (commodities cannot rest on 2022 alone). Architecture comes
from the smallest number of independent risks we actually need to cover — not from opinions about individual
assets.

**Epistemics (Adam, 2026-08-02) — the drivers are HYPOTHESES, not assumptions.** Growth / inflation /
real-rate / liquidity / risk-appetite are *candidate* axes the data must **support or SIMPLIFY** — they may
collapse into each other or fail to earn a seat. Do **not** pre-impose them as buckets and condition. The
one non-negotiable conditioning axis is *the core's own drawdown* (that IS the objective, not a hypothesis);
the macro drivers are the thing under test. **Learn the asset relationships first** (co-movement + tail
structure + how many independent axes actually exist), *then* decide membership.

**The study output must NOT produce** (any of these = the study has failed its own contract; they belong
to a separate research track with a different, prereg-gated evidence standard):
- regime-based weights
- allocation switches
- entry / exit signals
- tactical recommendations

**The goal is the MINIMUM set of permanent exposures** required to build a portfolio that (1) captures
long-term growth, (2) survives different economic environments, (3) remains behaviorally holdable,
(4) avoids unnecessary complexity. Not a more complicated portfolio — the fewest sleeves that leave no
axis un-hedged.

## Economic-driver framework (current design frontier)

Choose the universe from INDEPENDENT ECONOMIC RISK DRIVERS, then map to ETFs — not from an asset list.
**These axes are HYPOTHESES the data must support or simplify (see Epistemics above), not settled buckets.**
The working candidate set — to be empirically confirmed, collapsed, or dropped:

- **Growth surprise** (dominant equity driver)
- **Inflation surprise** (absorbs "deflation" + "currency/inflation concerns" — one axis)
- **Real-rate / discount-rate shock** (what "valuation compression" really is; the 2022 axis;
  Campbell-Vuolteenaho cash-flow vs discount-rate shocks)
- **Liquidity / financial stress** (2008, Mar-2020; Brunnermeier-Pedersen) [+ optional 5th: risk-appetite/vol]

Driver -> hedge map (key insights): **cash uniquely covers the real-rate + liquidity axes** (why
"cash as optionality" is right); **gold != commodities** (share the inflation axis but split it by the
GROWTH sign — commodities pro-cyclical, gold counter-cyclical; testable, not assumed); **growth-UP
needs no hedge — equity participates.** Each sleeve's role IS its mechanism-gate justification (paid to
bear a specific bad environment).

**Variance philosophy (Adam's framing):** we can't capture all market variance; the goal is to span the
top ~3-4 principal axes and hold through the idiosyncratic residual. PCA-style dimensionality reduction
— pragmatic, not Platonic. There is no canonical "true" regime set.

## Data state

- **HAVE** (`data/processed/assets_daily.csv`): `mkt_ret` (broad US equity) 1926+, `bond10_ret` 1962+,
  `gold_ret` 2000-08+ (short), `rf` 1926+. Also `trend_proxy_daily.csv` 2005+; japan/europe market 1990+.
- **FETCHED + VERIFIED this session, NOT yet persisted to repo:** monthly gold **1833-2026** (LBMA) from
  `https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv`. Egress works; FRED OK
  (`DGS10` fetched fine) but the FRED London-gold IDs are 404/discontinued; Stooq is bot-walled.
- **NEED (next action):** long broad-commodity ~1970 (GSCI-type), CPI (FRED `CPIAUCSL` 1947+), a
  real-rate proxy (10y - trailing CPI).

## Built this session (no look)

- `scripts/drawdown_budget.py` + `results/drawdown_budget.csv` — the payoff table. Key result (matched
  2005+ window): the -30% mixes (~70-75% equity) give CAGR ~10.5% vs 100%-equity 11.4% — only ~0.85-0.9%
  CAGR cost — for maxDD ~-35/-38% vs -50%, and *higher* Sharpe (0.77-0.80 vs 0.67). Long-history table
  shows 60/40 breached the budget in 2022 (bonds failed with stocks). Vol-drag + rebalancing bonus +
  the behavior gap make the return cost ~a wash in what you actually KEEP.

## NEXT ACTION — resume here

**DEFENSE STUDY COMPLETE (2026-08-02).** The equity-risk *defense* study (structural drivers, failure-mode
spanning, falsification battery incl. international replication, equity-drawdown decomposition) is done — see
"Falsification results" below and the results/*.csv artifacts. Confidence map: equity+bonds cover the
deflationary axis (cross-country structural); inflation/real-rate axis is real-but-thin (size humbly); the
risk-premium/liquidity residual is the ERP itself (endure/deploy, don't hedge). Spanning set structurally
complete. Diversifiers reframed as a **WAR CHEST** for countercyclical deployment ("go all-in when it's
cheap", mechanical tranche ladder — PORTFOLIO-TEST-PREREG.md H3/rung 6).

**>>> NEXT = the OFFENSE study (`.planning/EQUITY-ENGINE-OFFENSE.md`).** Before freezing the portfolio
constitution we run an equally rigorous equity-ENGINE study: what equity exposure are we preserving/
maximizing? Levers, each mechanism-gated + falsification-tested: factors → leverage → growth/tech →
concentration. **The `PORTFOLIO-TEST-PREREG.md` freeze is PAUSED** — the baseline equity engine is an open
input to it. Offense study → then freeze the combined prereg feeding the best-justified engine into the
deployment ladder.

---

*(defense-study plan, now complete — kept for the record):*

Run the **structural sleeve study** in two phases (no look; static-design use, NOT the closed Ch2
dynamic-timing null). Data layer DONE: `scripts/economic_driver_study.py` +
`data/processed/econ_driver_monthly.csv` + `gold_monthly_1833.csv`.

**PHASE 1 — learn the structure FIRST (no assumed states):**
1. Enumerate the large equity-drawdown episodes (the events that threaten the -30% budget); for each,
   record depth/duration, every sleeve's return through it, and the contemporaneous macro signature.
   *What actually drives drawdowns, and what actually helped?*
2. Asset relationships: full-sample vs crash-conditional (left-tail) correlation to equity — separate
   GENUINE diversifiers from assets that only *look* diversified on the unconditional average.
3. Dimensionality: how many independent axes actually exist (PCA on sleeve returns; PCA/clustering on the
   candidate driver proxies) — let growth/inflation/real-rate/liquidity/risk-appetite prove or SIMPLIFY.
   Data caveats already surfaced: gold restricted to post-1971 float; PPIACO is the inflation *proxy*,
   an investable GSCI/BCOM series is the commodity *sleeve return*.

**PHASE 2 — only then, membership:** fill the five-field roster (above). Minimum set of independent,
understandable exposures — no axis left un-hedged, drop any two sharing a conditional profile. **No
weights, switches, or signals — those fail the contract.**

Then (separate steps, higher evidence bar, AFTER the core is understood): L2A cross-sectional tilt spec
must COMPETE against the simplicity/robustness of the core, not merely beat zero -> L3 constraints.

## Discipline status

Everything this session = design + no-look characterization. No look spent, nothing preregistered,
nothing deployed. A deploy/SUPPORT claim still needs prereg + overnight cooling-off + explicit dated sign-off.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
