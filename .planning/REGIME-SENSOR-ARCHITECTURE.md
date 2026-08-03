# Market-Assumption Stress-Testing System — (independent market signals as measurement instruments)

**Status:** ARCHITECTURE LOCKED, sensors EXPLORATORY. No look spent, nothing preregistered, nothing
implemented. This documents the *framework*, not any sensor build.
**Last updated:** 2026-08-02

This is the governing design doc for what regime-detection becomes. The decisive reframe (Adam, 2026-08-02):
this is **high-resolution regime detection.** It still finds *what regime we are in* — but in full detail,
rather than forcing the world into a coarse bull / bear / neutral label. Operationally that makes it a
**MARKET-ASSUMPTION STRESS-TESTING system**: it does not collapse the regime to a label and it does not produce
actions; it **continuously tests whether the market assumptions it monitors remain supported.** The
*resolution* of the regime read — a mechanism-distinct vector, not one hidden state — is the whole point, and
(Adam's conviction, 2026-08-02) is exactly what prior approaches missed: they forced a rich, multi-mechanism
regime into one coarse label and lost the information. The shipped jump model is demoted from "the regime
model" to one *measurement instrument* — the volatility sensor — among several.

**Where the edge is — and isn't.** The value is *fewer blind spots*: a more accurate, more complete map of the
environment feeding the human's judgment. The edge is in the RESOLUTION and ACCURACY of each dot — never in a
conclusion. It is NOT a return-timing engine and NOT a decision engine: detecting the regime in detail must not
smuggle back the prediction goal three closed nulls already killed, nor drift into deciding what to do about it.
*Better-informed human judgment* is the claim; *forecasts, or machine decisions,* is the trap.

## The flow (and where it STOPS)

> **Market data → independent sensors → historical context → regime relevance → STOP.**
> *(Downstream, in a SEPARATE system and a separate human step: the investment decision. Not modeled in this repo.)*

The system knows only *which abstract assumptions to monitor* — e.g. "bonds hedge equity drawdowns," "the broad
index is genuinely diversified," "factor premia aren't crowded." It does **not** know any capital-allocation or
construction detail — not weights, sleeves, tilt budgets, or deployment rules. Knowing those would make the sensors hunt
for action-shaped answers — the exact contamination this boundary exists to prevent. Each sensor measures whether
its assumption still holds, contextualizes it historically, names the assumption, and STOPS.

**Sensors are instruments, not the product.** The product is the **assumption ledger** — a map of which
assumptions are currently supported or challenged, each with observation + history + relevance. It contains no
conclusion, no allocation, no recommendation. A sensor earns its place only by monitoring a market assumption
that genuinely matters — never for its own sake (the regime-relevance confidence dimension
enforces this).

**Two separate repos, two different problems.** This repo answers *"what is the environment, and which
assumptions are being tested?"* The downstream decision layer (separate repo) + the human answer *"given
judgment, objectives, constraints, and research, what do I want to own?"* This system never crosses that line —
it improves the *quality of the inputs* to the decision; it does not make or shape the decision.

---

## Why this exists — the failure this architecture fixes

The v1 program established *regimes are vol regimes*: many candidate representations of "the regime" collapsed
onto the volatility axis. That was not a modelling bug — it is what **any monolithic model** does to signals of
different character. Cram volatility, breadth, concentration, and correlation into one feature vector with one
distance metric, and the highest-variance, spikiest signal (vol) dominates the geometry; everything else is
absorbed into "the vol axis" and its distinct information is destroyed.

So modelling each dimension **individually** is not merely cleaner — it is the *structural fix* for the collapse
problem. Separate models preserve the orthogonal information a joint model erases. The credit sensor is the proof
in miniature: this repo already "killed" credit — but only as a *feature crammed into the vol model* (it made
detection lag worse). As its **own** sensor, credit is a distinct economic axis and is fully reopenable. The
failure was the monolith, not the dimension.

---

## The six locked principles (Adam, 2026-08-02)

### 1. Regime detection is NOT one monolithic model.

We are **not** building `sensor inputs → one regime score → an action`.
We **are** building `independent models → market-understanding layer → context for the human`.

Each sensor represents a distinct economic dimension with its **own** hypothesis, data, frequency, statistical
method, failure modes, and validation process. A jump/HMM state is right for volatility, wrong for inflation
(which wants a slow, vintage-aware regime), wrong for concentration (a measured level, no latent state needed),
wrong for correlation (an eigenstructure object). No single model form serves more than one dimension.

### 2. The sensors are parallel, not sequential.

Volatility does not feed breadth; breadth does not feed credit; credit does not feed macro. **Each model
independently observes the market.** They meet only at the understanding layer, which combines them as a
**vector of information, not a single score.**

**The reason:** a scalar regime score destroys the exact information we are trying to discover. Consider *low
volatility + high concentration + deteriorating breadth + expensive valuation* — a single "low risk" score
hides the fragility. **The configuration is the information.** (Concretely: 2021 / early-2024 read "calm" on
vol alone while three other sensors were flashing.)

### 3. The output is understanding, not prediction.

The system answers four questions — all forecasting-free, each mapped to a computable object:

| Question | What computes it |
|---|---|
| **What is happening?** | the current sensor vector (observation) |
| **How unusual is it?** | statistical rarity — per-sensor percentile + joint Mahalanobis distance from historical normal |
| **What risks are present?** | which dimensions are elevated → resemblance to historical risk archetypes |
| **Which market assumptions are stressed?** | diagnostics on *existing* exposures (e.g. a hedge whose correlation has flipped from its design) |

It does **not** answer *"what should we buy?"*

**Keystone — "how unusual is it?"** is the most rigorous output and the natural spine of the understanding
layer, because rarity has a precise, forecasting-free definition: the Mahalanobis distance of the current
sensor vector from its historical normal (financial turbulence — Kritzman-Li 2010 — generalized from returns
to the full sensor space). It says *how far from normal the joint configuration is*, never what happens next.

### 4. Candidate sensors remain exploratory.

The candidate universe is a **research universe, not a final production list**. Each candidate earns a
maturity tag by evidence (§ maturity model): **production · research · rejected**. Volatility being the only
production-grade dimension *today* does not privilege it as the only one worth researching.

### 5. The understanding layer preserves information.

Permitted tools: sensor-vector representation, historical-similarity / analogue matching, percentile & rarity
measures, joint distance metrics, clustering / state analysis. **Hard constraint:** no output may become a
hidden forecast, and no reduction may collapse the vector into a scalar that erases the per-sensor stories. A
composite (CISS-style scalar) is permitted only as a *derived summary view*, never as the primary object.

### 6. The downstream boundary.

This system answers *"what is the environment, and which market assumptions are being tested?"* A SEPARATE
downstream system + the human answer *"what, if anything, to do about it."* This system informs awareness; it
never decides. The interface to that downstream system is deliberately **deferred** until signals mature —
designing it now would write checks the signals cannot yet cash (see the downstream-boundary section).

---

## The per-sensor research spec (the mini-study template)

Each sensor is its own small study. Before any characterization, it declares:

- **Assumption tested** — the specific monitored market assumption this instrument exists to check. If no
  monitored market assumption depends on it, it is not a sensor for this system (however interesting).
- **Hypothesis** — the distinct economic *mechanism* it claims to observe, and why that mechanism carries
  *durable, observable* information about market conditions (not "it backtests" — the mechanism must be
  economically real).
- **Data** — native inputs, source, and the **vintage/revision** exposure (macro series get revised; a live
  sensor must use point-in-time data or it has a look-ahead trap the vol sensor never had).
- **Frequency** — native clock (daily / weekly / monthly). Mixed frequencies are **not** stacked naively;
  each sensor stays on its own clock and the understanding layer aligns them explicitly.
- **Statistical method** — the model form appropriate to *this* dimension (state model / level+percentile /
  eigenstructure / diffusion index / nowcast probability / …), not a house default.
- **Failure modes** — where it is expected to break, declared *before* testing.
- **Validation process** — the six-point evaluation below.

### The six-point evaluation (every candidate, same protocol)

1. **What exactly is being measured?** Precise, causal construction.
2. **Observation or prediction?** Is it measuring the *present state* or forecasting a *future* one? The
   forecasting version is flagged, not built.
3. **Distinct mechanism? — the gate, with orthogonality as a *diagnostic* not the rule.** Does it measure a
   different economic *mechanism* / test a different assumption? That is the accept/reject gate. Statistical
   orthogonality (correlation, ΔR² vs PC1/PC2) is *measured* — it tells us how much sensors co-move and when,
   which the interaction layer needs — but it never accepts or rejects. Reject only for mechanical identity or
   mechanism-duplication; **keep** signals that are statistically correlated yet mechanistically distinct
   (concentration vs crowding is the clean case). *(This is what stops us building nine sensors that all
   re-measure volatility — without wrongly cutting a distinct mechanism just because it co-moves.)*
4. **Does it improve understanding of historical environments?** Episode-by-episode: does conditioning on it
   sharpen the read of known periods?
5. **Does it survive out-of-sample?** The descriptive property must replicate on the Japan/Europe panels (the
   standing out-of-hypothesis-sample rule — exactly how the dispersion lead was killed: US −40d did not
   generalize, Japan +154d / Europe +94d).
6. **Where does it fail?** The failure-environment map — the honest catalogue of where it misleads or goes
   silent.

---

## Honest comparison — how sensors are compared without cheating

- **The low-dimensional prior is the yardstick.** The environment is known to be ~2-axis (PC1 risk-off
  severity = growth/liquidity/vol; PC2 = inflation/real-rate). Every sensor is scored on which axis it loads:
  PC1 (redundant with vol), PC2 (the under-covered axis), or a genuine third axis. Orthogonality is *earned by
  evidence*, not asserted.
- **Benchmarks are external and public.** A homegrown composite that cannot beat CISS (Holló-Kremer-Lo Duca
  2012) / Chicago Fed NFCI / OFR FSI is not adding information — those are the bar.
- **Stability never travels alone.** A constant is perfectly stable. Every stability/persistence number is
  paired with a skill/rarity number, or it manufactures false confidence.
- **Rarity is measured jointly, not just per-sensor**, so the comparison rewards a sensor for the *configurations*
  it distinguishes, not just its own marginal wiggle.

---

## Maturity model — how a sensor earns its tag

The tag is a **label on the sensor's output that travels with it into the understanding layer** — it is *not*
a gate on research. All candidates are explored freely; the tag only controls whether the reading is trusted
enough to be surfaced as a decision-relevant input downstream (vs research-only context).

- **PRODUCTION** — causal, validated, OOS-confirmed on international panels, failure-mapped, and orthogonality
  established. Trusted enough to be surfaced as a decision-relevant input downstream. *(Today: volatility only.)*
- **RESEARCH** — built and characterized, but with an open discipline gap (unresolved placebo, vintage risk,
  no intl confirmation yet). Renders as human context only; never feeds a rule.
- **REJECTED** — tested and failed a specific gate (did not generalize, no orthogonal information, or is a
  disguised forecast). Documented with the reason so it is not silently revived. *(Today: dispersion-as-lead;
  credit-as-a-vol-feature; VIX/VRP as a separate axis — all rejected in their tested form; credit-as-its-own-
  sensor is a distinct, un-tested candidate.)*

---

## The sensor set — organized by PURPOSE (instruments, not co-equal inputs)

Organizing the sensors **by purpose, not as a flat list, is deliberate** — a flat co-equal list would recreate
the HMM mistake of treating everything as inputs to one hidden state. Each sensor is a measurement *instrument*
testing a specific monitored market assumption. Evidence & citations: the `sensor-orthogonality-evidence` memory
(four-stream literature research, 2026-08-02) — from ~14 raw candidates the mechanism gate keeps a SHORT list;
raw stress series ~85–94% collapse onto one risk-off factor and re-converge in crises, so survivors are distinct
by *mechanism* + *clock*, not by statistical orthogonality. Columns: **assumption it tests · clock · mechanism.**

### Core state — "what is the market's operating condition?"

| Sensor | Assumption it tests | Clock | Mechanism / status |
|---|---|---|---|
| **Volatility / risk-off** | "the market is in its normal low-stress operating range" | fast (days–wks) | vol clustering; risk-off severity (PC1). **PRODUCTION** (shipped JM); caveat coincident-to-lagging |
| **Inflation / real-rate** | "bonds will hedge an equity drawdown" (the deflationary premise) | slow (qtrs–yrs) | inflation-growth covariance → bonds hedge vs bet (PC2), read via stock-bond corr SIGN. **PRIORITY**, buildable from returns |
| **Tail distribution** | "the return distribution is its normal shape" | fast | separately-priced jump/crash premium (Bollerslev-Todorov; Kelly-Jiang). DATA-HEAVY (options/HF) → deferred |

### Structural fragility — "how would the market break?"

| Sensor | Assumption it tests | Clock | Mechanism / status |
|---|---|---|---|
| **Concentration** | "the index isn't dependent on a few holdings" | slow (structural) | cap-weight structure; index inherits a few megacaps' idiosyncratic risk. Decouples from vol (2021/2024); AMBIGUOUS (healthy vs fragile) |
| **Crowding** | "participants aren't positioned alike / vulnerable to a forced unwind" | slow-med | consensus + leverage → fire-sale externality (Stein 2009). Buildable ONLY as return-based comomentum (Lou-Polk) = *factor*-crowding, narrow; general form needs proprietary/stale data |

*Concentration and crowding are the clean proof of the mechanistic gate: they overlap (both elevate in a
tech-led melt-up) yet fail through **different mechanisms** — index-dependence-on-few-names vs
forced-unwind-of-crowded-positioning (Aug-2007 quant quake = crowded, not concentrated, zero index-vol at onset).*

### Long-horizon context — "what return environment are we in?"

| Sensor | Assumption it tests | Clock | Mechanism / status |
|---|---|---|---|
| **Valuation** | "forward returns are near normal" | very slow (multi-yr) | discount-rate / price-of-ERP (Campbell-Shiller). STRONG @ 4–10yr, ~0 <1yr → slow conditioner, NEVER a trigger |

### Conditional diagnostics — informative only in specific phases

| Sensor | Assumption it tests | Clock | Mechanism / status |
|---|---|---|---|
| **EBP** (excess bond premium) | "credit supply is normal" | slow, LEADING (1–2yr) | intermediary risk-appetite / credit supply (Gilchrist-Zakrajšek); needs GZ micro-panel construction |
| **Funding stress** | "funding markets function" | fast, EPISODIC (tail) | funding-liquidity spirals (Brunnermeier-Pedersen); binary flag, high conf when it fires, silent otherwise |
| **Absorption ratio** | "diversification is working" | fast-med, LEADING | eigenstructure compaction (Kritzman 2011); PARTIAL — *is a factor of* index vol, keep for the LEAD only |

### The three confidence dimensions (every sensor carries all three)

Every reading travels with three separate confidence scores — collapsing them into one hides exactly the
failure this system prevents:

1. **Measurement confidence** — can we observe it reliably, causally, from available data?
2. **Interpretation confidence** — do we understand the *mechanism* (not just a correlation)?
3. **Regime-relevance confidence** — does anything downstream actually *depend* on this assumption being true (is it a market assumption that matters, not a curiosity)?

The third is the subordination guard: a signal can score high on measurement + interpretation yet low on
relevance — *a fascinating research signal that must NOT become an important input.* Maturity
(production / research / rejected) is derived from all three together, never from backtest fit.

First-pass scorecard (H / M / L):

| Sensor | Measurement | Interpretation | Regime-relevance |
|---|---|---|---|
| Volatility | H (shipped) | H | H |
| Inflation / real-rate | H (from returns) | H | H (defense study's core assumption) |
| Concentration | H (cap data) | M (healthy-vs-fragile ambiguity) | M |
| Tail | **L** (needs options/HF) | H | M |
| Crowding | M (comomentum, narrow) | H | M–H (factor-premium reliability) |
| Valuation | H | H | M (long-horizon only) |
| EBP | M (GZ construction) | H | M |
| Funding stress | M | H | M (tail insurance) |
| Absorption ratio | M | M (semi-redundant w/ vol) | **L–M** |

### The gate is MECHANISM, not statistics

The selection gate is **mechanistic independence** — does the sensor measure a distinct economic mechanism /
test a distinct assumption. **Statistical orthogonality is a *diagnostic*, not the gate**: it tells us how much
sensors co-move and *when* (the interaction layer needs this), but it never accepts or rejects. Reject only for
**(a) mechanical identity** (dispersion `= σ̄²(1−ρ̄)` is the same object as correlation) or **(b) mechanism-
duplication** (raw credit re-expresses vol's Merton channel — keep the EBP *residual*, drop the raw). **Keep**
sensors that are statistically correlated but mechanistically distinct. This rescues the crisis case: in a crash
the sensors *statistically* converge (corr → 1) yet stay mechanistically distinct — 2008 was high-vol AND
funding-frozen AND credit-supply-collapsed, three assumptions breaking at once, and the ledger still reports
*which* broke.

### Rejected / redundant — do NOT build as separate sensors

Raw credit spreads (~85% shared with VIX) · market liquidity (Amihud/bid-ask co-move with vol) · dispersion
(`D²≈σ̄²(1−ρ̄)`, same object as correlation) · breadth (correlation+trend blend) · aggregate earnings (PC1
growth pole) · coincident recession nowcast (=PC1; the leading piece is the rate curve = PC2) · VIX/VRP as a
separate axis (collapses onto vol). Rejection is for **mechanism-duplication or mechanical identity**, never for
statistical correlation alone.

---

## The output object — the assumption ledger

The output is **not a regime label and not a flat dashboard.** It is a three-layer object whose middle layer —
the ledger — is the product; the sensors are the instruments beneath it. This is the "regime in detail": the
full-resolution state, expressed as which market assumptions currently hold.

**Level 0 — Measurement (the state vector).** Per sensor: `{reading, rarity percentile, clock, the three
confidence scores, maturity tag}`. The raw substrate; necessary, not yet decision-useful.

**Level 1 — The assumption ledger (THE product).** Each monitored market assumption, with `status ∈ {intact /
under test / violated}`, the sensor evidence, how unusual, and confidence. Status is an **observation, never an
instruction** — "the bond-hedge assumption is under test," *never* "sell bonds." The human owns what to do about it.

| Market assumption | Sensor(s) | Status (example read) |
|---|---|---|
| "Bonds will hedge an equity drawdown" | inflation / real-rate | **under test** — stock-bond corr turned positive, 85th pctile |
| "The index isn't dependent on a few names" | concentration | **under test** — HHI 95th pctile |
| "Factor premia aren't crowded / vulnerable to unwind" | crowding (comomentum) | intact |
| "Diversification is functioning" | absorption ratio | intact |
| "The distribution is its normal shape" | tail | intact |
| "Funding markets function" | funding flag | intact |

**Level 2 — Context.** Joint rarity ("how unusual overall" — Mahalanobis distance of the vector from normal,
turbulence generalized) + historical analogues (nearest-neighbour *configurations*: "resembles 2018-Q4 /
early-2022"). Forecasting-free.

So: **the state vector is the substrate, analogue matching is context, the assumption ledger is the product.**
The configuration is preserved — never collapsed to one scalar (`{low-vol + high-concentration + deteriorating
stock-bond-corr}` and `{high-vol + positive corr + cheap valuation}` are opposite worlds a single "risk" score
erases). *(Later, gated: archetype clustering of the historical vector — but only causal, reproducible, and
OOS-stable; the literature warns GMM clusters need ~100 restarts + a Jaccard check to be called real.)*

**The crisis caveat, mechanistically framed:** the sensors *statistically* re-converge in crises
(cross-correlations → 1, CISS), so the vector's *statistical* disambiguation degrades in the tail — but the
*assumptions* stay distinct, so the ledger still reports which ones broke. Trust the statistical configuration
most when quiet; trust the assumption ledger throughout.

---

## <a name="downstream"></a>The downstream boundary

The assumption ledger is consumed by a **separate downstream decision layer (a different repo)** and, above it,
by the human. **How that layer uses the information is out of scope for this repo, deliberately.** This repo does
not define allocation rules, exposure changes, tilts, sleeves, or any investment action — and must not:
specifying them here would pull construction knowledge into the sensors and turn an understanding layer into a
hidden allocation model, the exact thing this whole design exists to avoid. The regime system stops at
*regime relevance* — it names the assumption a reading relates to, and hands over. Nothing here moves money
or recommends that money be moved.

---

## Discipline — free to explore, gated to graduate

- **Exploration is no-look.** Measuring a sensor, characterizing its properties, testing orthogonality, and
  checking international replication are *descriptive* — the same class as the atlas/anatomy work. No look
  spent, no mechanism gate. This is the freedom principle #4 protects.
- **Graduation is gated.** A sensor only meets the look-gate and mechanism gate when proposed as a
  *decision-useful signal* that would inform a real decision downstream. Then: out-of-hypothesis-sample confirmation, mechanism
  reasoning (does the *observation* remain informative — for a pure observation the gate is lighter than for
  an alpha claim), overnight cooling-off, explicit dated sign-off.
- **The shipped instrument keeps running.** `regime_card.json` → its downstream consumer (a separate repo) continues as-is
  (the volatility sensor, PRODUCTION). Nothing here disturbs it.

---

## What this doc does NOT do

- It does **not** build nine sensors. The next step is this framework, then sensors one at a time against it.
- It does **not** finalize the sensor list, the composite, or the downstream interface.
- It does **not** reopen any closed market-timing null — this is an *understanding* layer, not a strategy.

## Next step

Build sensors one at a time against the per-sensor spec. **Priority sensor = INFLATION / REAL-RATE (PC2), read
via the stock-bond correlation regime** — it is the highest-value orthogonal axis (the one vol is *provably*
blind to: 2008 vs 2022 same equity vol, opposite bond behavior), it monitors a load-bearing assumption
("bonds hedge equity drawdowns") that vol cannot see, it is the sharpest orthogonality proof, and — unlike
the raw macro series — it is **buildable from asset returns**, so it is causally clean with no vintage
look-ahead. Concentration is the strong second (also confirmed, partial infra). Tail/jump is deferred pending
options/high-frequency data.

Each sensor's mini-study is a no-look descriptive characterization producing a maturity tag. The understanding
layer (vector + joint rarity + analogue matching) is built *after* there are ≥2 validated sensors to compose —
and with the crisis-reconvergence caveat above front of mind.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
