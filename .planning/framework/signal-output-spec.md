# Signal Output Specification

**Spec version: v0.1-draft**

The scoring + output half of the framework. `signal-spec-template.md` attribute 7 (Confidence) and the DERIVED
maturity header field point here; `validation-standards.md` supplies the law the confidence dimensions read
from. This document defines three things: the four-dimension research-maturity confidence model, the
descriptive maturity model, and the Level 0/1/2 historical-context output / assumption-ledger shape (added in
the second half of this spec). Nothing here freezes to v1.0 until Adam's dated sign-off (see
`SIGNOFF-CHECKLIST.md`).

---

## 1. Confidence model — four research-maturity dimensions

> **Disclaimer (read first).** Confidence in this framework describes **RESEARCH MATURITY**, not predictive
> likelihood. A confidence reading NEVER implies "this signal is more likely to be correct," "this signal is
> more likely to fire," or "this signal predicts the market." It states how far the research + validation +
> implementation process has progressed and how well-grounded the reading is — nothing about what markets will
> do next. This is a direct consequence of D-01/D-02 (market-state intelligence, never prediction) and D-06.

Confidence is **multidimensional, never a single number** (D-06). Every reading travels with four separate,
anchored dimensions; collapsing them into one score hides exactly the failure this system exists to prevent.
Each dimension is graded **H / M / L** with written criteria (GRADE-style anchored rubric) and a **declared
starting point** that evidence then adjusts — so two people scoring the same signal land on the same label, and
the rating is auditable rather than gestalt.

The four dimensions (D-06, authoritative):

### 1.1 Measurement quality — *can we observe it reliably, causally, from available data?*

- **H:** Causal, point-in-time construction from non-revised data (e.g. asset returns); no vintage look-ahead;
  full usable history; no material proxy substitution.
- **M:** Some vintage / revision sensitivity, handled with a documented point-in-time reconstruction; OR a proxy
  stands in for part of the history; OR usable history is short.
- **L:** Requires revised or not-yet-available data (e.g. options / high-frequency); material vintage look-ahead
  unresolved; or heavy proxying.

**Declared starting point:** a signal built purely from asset returns starts at **H**; a signal needing macro
vintages or options data starts at **M or L**.

### 1.2 Mechanism support — *do we understand WHY (a durable structural reason), not just a correlation?*

- **H:** A written, literature-grounded structural reason — a risk-premium or a risk-management channel — that
  it survives being known; passes the mechanism gate cleanly.
- **M:** A plausible mechanism with an unresolved ambiguity (e.g. concentration's healthy-vs-fragile reading) or
  a declared partial redundancy (e.g. absorption ratio semi-redundant with volatility).
- **L:** Correlation without a durable structural reason, or the "mechanism" is a disguised forecast → fails the
  gate (`validation-standards.md` §The mechanism gate).

**Declared starting point:** starts wherever the written mechanism argument lands; the mechanism gate is a
prerequisite for any positive claim, so a signal cannot reach production at **L** here.

### 1.3 Evidence robustness — *does the descriptive property hold across periods and out-of-hypothesis-sample?*

- **H:** Property replicates across sub-periods **and** on the out-of-hypothesis-sample panels (Japan / Europe)
  with the pattern intact; confounds checked.
- **M:** Holds in-sample across periods, but international out-of-hypothesis-sample confirmation is not yet run
  or only partial; OR robust with a documented, understood regime-dependence.
- **L:** In-sample / single-period only, OR failed a sub-period or placebo control. *(The killed dispersion-lead
  — US −40d that did not generalize, Japan +154d / Europe +94d — is the reference L.)*

**Declared starting point:** starts at **L** until international out-of-hypothesis-sample confirmation is run —
mirroring the standing rule that nothing is SUPPORT before Japan / Europe replication.

### 1.4 Implementation maturity — *how far has the research + validation + build process actually progressed?*

This is the research-process dimension. Its **discrete expression IS the maturity tag** (§2): confidence and
maturity are one coherent research-process concept, never a likelihood. It reads strictly as process progress —
never as regime applicability, current importance, or anything predictive.

- **H:** Built, characterized, validated (including international out-of-hypothesis-sample), failure-mapped, and
  carrying a dated sign-off — the process is complete. → maturity tag **production**.
- **M:** Built and characterized, but an open discipline gap remains (international OOS not yet run, an
  unresolved placebo / control, or an unresolved vintage-sensitivity risk). → maturity tag **research**.
- **L:** Failed a specific gate (did not generalize, no distinct mechanism, or a disguised forecast), OR not yet
  built (spec / charter only). → maturity tag **rejected** (for a failed gate) or pre-build.

**Declared starting point:** starts at **L** (spec-only) and advances only as validation-standards gates are
cleared.

> **Boundary note.** The old third confidence dimension was named "regime-relevance" / "portfolio-relevance
> guard" and the earlier four-dimension proposal named its fourth "current-relevance." Both leaned
> predictive / applicability framing and are **forbidden framings** here. Implementation maturity replaces them
> and is phrased strictly as research-process progress. See §3 (Supersession).

**Anchor thresholds + declared starting points are `[ASSUMED — requires Adam's dated sign-off before the
confidence model is frozen at v1.0]`** (research A1). The four-dimension *structure* is decided (D-06); only the
threshold wording and starting points are proposed.

---

## 2. Maturity model (descriptive, DERIVED — not a ranking)

The maturity tag — **production / research / rejected** — is **DERIVED, not authored**. It is computed from
template attribute 5 (Validation) plus the implementation-maturity confidence dimension (§1.4); an author never
hand-sets it. As stated in §1.4, the implementation-maturity dimension's discrete expression *is* this tag —
confidence and maturity are the same research-process concept expressed at two grains.

> **Descriptive, NOT a quality ranking (D-13).** A production signal is **NOT "better"** than a research
> signal. The tag says only **how far the research + validation + implementation process has progressed** — not
> that a higher stage is more trustworthy as a market call, more likely correct, or higher predictive quality.
> All candidates are researched freely; maturity is a label on how far along a signal is, never a gate on which
> signals are worth studying and never a statement about predictive value.

Derivation rule (proposed):

| Tag | Derivation rule |
|-----|-----------------|
| **production** | measurement quality ≥ M · mechanism support = H (gate passed) · evidence robustness = H (international out-of-hypothesis-sample confirmed) · structural failure modes mapped · dated sign-off present. *(Today: volatility only.)* |
| **research** | Built + characterized, but an open discipline gap remains (no international OOS yet, an unresolved placebo / control, or an unresolved vintage-sensitivity risk). Renders as human context only. |
| **rejected** | Failed a specific gate — did not generalize, no distinct mechanism, or a disguised forecast. Recorded WITH the reason so it is not silently revived. *(Today: dispersion-as-lead; raw-credit-as-a-vol-feature; VIX/VRP as a separate axis.)* |

**The derivation rule is `[ASSUMED — requires Adam's dated sign-off]`** (research A2). A wrong rule could
over-trust an under-validated signal, so the specific thresholds are proposed, not frozen.

---

## 3. Supersession record

This four-dimension research-maturity confidence model **supersedes two earlier models**:

**(a) The earlier three-dimension model** — measurement · interpretation · regime-relevance — recorded in
`.planning/REGIME-SENSOR-ARCHITECTURE.md` §"The three confidence dimensions" and in ROADMAP.md Success-Criterion
#3 (which still reads "three confidence dimensions"). Mapping:

| Old three-dim | New four-dim |
|---|---|
| Measurement confidence | → measurement quality |
| Interpretation confidence | → split into **mechanism support** + **evidence robustness** |
| Regime-relevance confidence (the subordination guard) | → DROPPED; replaced by **implementation maturity** |

**(b) The earlier four-dimension proposal** — data-quality · historical-robustness · mechanism ·
current-relevance (the interim naming in 01-RESEARCH §Confidence Model). Mapping:

| Old four-dim proposal | New four-dim |
|---|---|
| data-quality | → measurement quality |
| mechanism | → mechanism support |
| historical-robustness | → evidence robustness |
| current-relevance | → **DROPPED and replaced by implementation maturity** |

**Why current-relevance was dropped:** it leaned predictive / regime-applicability framing (whether a reading
"currently matters"), which D-06 now forbids. Implementation maturity replaces it with a strictly
research-process meaning. The current-relevance → implementation-maturity swap (D-06) is flagged for Adam's
dated **veto** in `SIGNOFF-CHECKLIST.md`.

**Upstream docs are STALE, not silently rewritten** (research A5). ROADMAP.md SC#3 and
REGIME-SENSOR-ARCHITECTURE.md §"The three confidence dimensions" / §"Level 0" (which lists "the three confidence
scores") still carry the superseded three-dimension text. Editing those upstream docs is an **optional
follow-up for Adam**, not performed here — this spec records the supersession so the drift is documented rather
than left as a silent contradiction.

---

## 4. Output shape — Level 0 / 1 / 2 (STOP at Level 2)

The output is a three-level object (D-08 / D-09 / D-14). The levels are named concretely: **Level 0 =
measurement · Level 1 = historical context · Level 2 = regime relevance.** The system **STOPS at Level 2** —
there is no Level 3, no action, no decision. This is the composition target Phase 10 renders into.

### 4.1 Level 0 — measurement (the per-signal record)

The state-vector element. Exactly the D-08 fields, no more:

```
{
  signal:               "<name>",
  assumption_monitored: "<the ledger key, e.g. 'bonds hedge equity drawdowns'>",
  reading:              "<qualitative + quantitative, e.g. 'stock-bond corr positive, +0.35'>",
  rarity:               "<historical percentile + how computed, e.g. '85th pctile, trailing 60y'>",
  trend:                "<direction of change over a stated window, e.g. 'rising over trailing 6m' | 'flat'>",
  extreme_conditions:   "<explicit at-a-historical-extreme flag + which tail, e.g. 'at 95th-pctile extreme' | 'not extreme'>",
  cross_signal_relationships: "<known relationships to other signals from template Q4.3, e.g. 'co-moves with concentration; leads credit ~1-2y' | 'none characterized yet'>",
  clock:                "<daily|weekly|monthly|structural>",
  confidence: {
     measurement_quality:    "H|M|L",
     mechanism_support:      "H|M|L",
     evidence_robustness:    "H|M|L",
     implementation_maturity:"H|M|L"
  },
  maturity:             "production|research|rejected",   // DERIVED (§2)
  spec_version:         "<semver of the template filled>"
}
```

`trend`, `extreme_conditions`, and `cross_signal_relationships` were added 2026-08-03 (the observatory-framing
refinement) so each signal describes not just its level but its *direction*, whether it sits at a historical
*extreme*, and how it *relates* to the other signals — the descriptive richness that makes the set an
observatory rather than disconnected readings. `cross_signal_relationships` carries the *known / characterized*
relationships (template Q4.3); the **live joint** reading (this configuration's joint rarity + analogues) is a
Level-2 lens (§4.3), never collapsed into a per-signal field. These field definitions are `[ASSUMED — pending
Adam's dated sign-off]` alongside the other v1.0 items.

**Zero allocation / decision fields.** No allocation, exposure, weight, sleeve, tilt, cash, action,
recommendation, or "portfolio" — the record names a monitored market assumption and its reading (level, trend,
rarity, extremity, relationships), and STOPS. `trend` and `extreme_conditions` are descriptive state, never a
buy/sell trigger.

### 4.2 Level 1 — historical context (the assumption ledger, THE product)

Each monitored market assumption × `{status ∈ intact | under-test | violated · sensor evidence · rarity ·
confidence}`. **Status is an OBSERVATION, never an instruction** — "the bond-hedge assumption is under test,"
never any directive to act. The canonical worked example (from CONTEXT.md §Specific Ideas), which must stay
legible as independent readings:

| Market assumption | Signal(s) | Status (example read) |
|---|---|---|
| "Bonds will hedge an equity drawdown" | inflation / real-rate (stock-bond corr) | under-test — corr turned positive, 85th pctile |
| "The index isn't dependent on a few names" | concentration | under-test — HHI 95th pctile |
| "Diversification is functioning" | absorption ratio | intact |
| "Factor premia aren't crowded" | crowding | intact |

The six-reading vector from CONTEXT.md — **valuation: expensive · volatility: elevated · breadth: weakening ·
liquidity: supportive · credit: stable · concentration: historically high** — must stay legible as six
independent readings. It must **NEVER** be reduced to a single number such as "market risk = 73/100"; the whole
point of the shape is that the readings remain independent and the disagreement between them survives.

### 4.3 Level 2 — regime relevance (context)

Joint rarity ("how unusual is the whole configuration") + nearest-neighbour historical analogues (configurations
— "resembles 2018-Q4 / early-2022"), forecasting-free. **The system STOPS here** — Level 2 is context for the
human, never a call.

### 4.4 The composite-scalar prohibition AND the joint-rarity distinction

These two must be kept distinct — cutting the joint-rarity lens is itself a failure, and admitting a composite
scalar is the other failure.

- **FORBIDDEN — any composite-scalar output field.** No single number that claims the market is safer or
  riskier, implies an action, or erases the per-signal stories. "market risk = 73/100" is the named forbidden
  form. This supersedes the architecture doc's note that a CISS-style composite is permitted "as a derived
  secondary view" (research A3): this framework forbids any composite-scalar output field entirely.
- **PERMITTED — joint rarity (Mahalanobis / turbulence distance)** as a Level-2 distance lens. It is
  forecasting-free; it is a *distance*, not a rank of good/bad — two configurations equally far from normal can
  be opposite worlds; it is computed FROM the preserved vector and sits BESIDE it, never replacing the
  per-signal readings. Allowed form: "joint configuration at the 92nd percentile of historical unusualness,
  driven by concentration + stock-bond-corr."

**A3 (forbid any composite-scalar output field) is flagged for Adam's dated sign-off** in
`SIGNOFF-CHECKLIST.md`.

### 4.5 No-dominance / co-equal presentation (D-11)

Signals are presented **co-equally**. There is NO weighting, ranking, precedence, or aggregation that lets any
single signal override the vector. Signal **disagreement is information**, not a failure to be resolved into
consensus. This extends D-07 (independent research modules) into the presentation layer and sits alongside the
composite-scalar prohibition: both defend the same invariant — the full per-signal vector is the product, and it
is never collapsed, never rank-ordered, never overruled by one dimension.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
