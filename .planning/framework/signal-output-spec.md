# Signal Output Specification

**Spec version: v1.0**

The scoring + output half of the framework. `signal-spec-template.md` attribute 7 (Admission Assessment) and the
DERIVED maturity header field point here; `validation-standards.md` supplies the law the admission axes read
from. This document defines three things: the unified signal-admission model (a binary mechanism prerequisite
gate + three graded admission axes), the descriptive DERIVED maturity model, and the Level 0/1/2
historical-context output / assumption-ledger shape (added in the second half of this spec). Frozen to v1.0 by
Adam 2026-08-03; amendable only via semver amendment (see `SIGNOFF-CHECKLIST.md`). RF remains OPEN by design.

---

## 1. Signal-admission model — a prerequisite gate + three graded axes

> **Disclaimer (read first).** The admission assessment describes whether a signal has **EARNED ITS PLACE**,
> never predictive likelihood. It NEVER implies "this signal is more likely to be correct," "this signal is more
> likely to fire," or "this signal predicts the market." It states whether the mechanism survives being known,
> whether the state is measurable, whether it adds unique information, and how far its evidence has matured —
> nothing about what markets will do next. This is a direct consequence of D-01/D-02 (market-state intelligence,
> never prediction) and D-06.

Admission has two parts: a **binary prerequisite gate** (mechanism — pass or rejected) and **three graded axes**
(measurement validity · investment usefulness · evidence maturity). This unified model REPLACES the earlier
four-dimension confidence model (see §3 supersession). The three axes are **orthogonal and non-compensatory**: a
high score on one NEVER offsets a low score on another. Measurable-but-useless, useful-but-research-stage, and
well-studied-but-irrelevant are three distinct admission failures, and none is bought off by strength elsewhere.

### 1.0 Mechanism prerequisite gate (BINARY — pass / rejected, NOT graded)

A **written structural reason** the signal survives being known — a risk-premium or a risk-management channel.
This is not graded H/M/L; it is a pass/fail prerequisite. **Fail = the signal is `rejected` and never admitted.**
"It backtests" / "looks predictive" / novelty / literature-citation alone are **disqualifying**. This PROMOTES
the old graded "mechanism support" dimension into a binary gate (see `validation-standards.md` §The mechanism
gate). A signal that does not pass this gate does not proceed to the three axes.

The three graded axes (each H / M / L with a GRADE-style anchored rubric + a **declared starting point** that
evidence then adjusts — so two people scoring the same signal land on the same label, and the rating is auditable
rather than gestalt):

### 1.1 Measurement validity — *can we measure this state accurately, consistently, causally, from available data?*

- **H:** Causal, point-in-time construction from non-revised data (e.g. asset returns); no vintage look-ahead;
  full usable history; no material proxy substitution.
- **M:** Some vintage / revision sensitivity, handled with a documented point-in-time reconstruction; OR a proxy
  stands in for part of the history; OR usable history is short.
- **L:** Requires revised or not-yet-available data (e.g. options / high-frequency); material vintage look-ahead
  unresolved; or heavy proxying.

**Declared starting point:** a signal built purely from asset returns starts at **H**; a signal needing macro
vintages or options data starts at **M or L**.

### 1.2 Investment usefulness — *does it answer an important investor question AND add unique information?*

The static, per-SIGNAL admission judgment: does this signal answer a question worth asking about the environment
**and** provide UNIQUE INFORMATION beyond the signals already admitted? Both halves are required — an important
question already answered by an existing signal is not useful, and unique noise answering no question is not
useful either. This is a **per-signal admission decision made ONCE at admission**, NEVER a per-reading,
time-varying applicability / prediction score (that is the killed "current-relevance" framing and must not
return — see §3).

- **H:** Answers a concrete, important investor question about the environment AND carries information not
  already captured by an admitted signal (incremental-information requirement met, mechanism-first).
- **M:** Answers a real question but with a declared partial overlap with an admitted signal (e.g. absorption
  ratio is semi-redundant with volatility — kept for the lead only), OR the question it answers is real but
  narrow.
- **L:** Duplicates an admitted signal's information, or answers no question that matters for understanding the
  environment (built because the data existed, not because a question demanded it).

**Supporting diagnostic (never the gate):** the ΔR²-vs-admitted-axes orthogonality DIAGNOSTIC is evidence for the
uniqueness half — mechanism-first. Orthogonality is never a hard statistical accept/reject; a signal that is
statistically correlated but mechanistically distinct is still unique (2008 saw vol, funding, and credit converge
statistically yet stay three distinct assumptions).

**Declared starting point:** starts wherever the written uniqueness argument + investor-question answer land;
absent a distinct mechanism and a concrete question, it cannot start above **L**.

### 1.3 Evidence maturity — *does the descriptive property hold across periods, survive OOS, and is it studied enough to understand?*

- **H:** Property replicates across sub-periods **and** on the out-of-hypothesis-sample panels (Japan / Europe)
  with the pattern intact; confounds checked; behavior sufficiently studied to be understood.
- **M:** Holds in-sample across periods, but international out-of-hypothesis-sample confirmation is not yet run
  or only partial; OR robust with a documented, understood regime-dependence.
- **L:** In-sample / single-period only, OR failed a sub-period or placebo control. *(The killed dispersion-lead
  — US −40d that did not generalize, Japan +154d / Europe +94d — is the reference L.)*

**Declared starting point:** starts at **L** until international out-of-hypothesis-sample confirmation is run —
mirroring the standing rule that nothing is SUPPORT before Japan / Europe replication.

> **Boundary note.** The old third confidence dimension was named "regime-relevance" / "portfolio-relevance
> guard" and the earlier four-dimension proposal named its fourth "current-relevance." Both leaned
> predictive / applicability framing and are **forbidden framings** here — they stay DROPPED. Investment
> usefulness is NOT their replacement: it is a static, one-time admission judgment about unique information + an
> answerable question, never a time-varying "does this currently matter" score. See §3 (Supersession).

**Anchor thresholds + declared starting points for the three axes are `[ADOPTED v1.0 — Adam 2026-08-03; amendable
via semver]`** (research A1). The unified-model *structure* (binary mechanism gate + three non-compensatory axes)
and the threshold wording + starting points are all adopted at v1.0.

---

## 2. Maturity model (descriptive, DERIVED — not a ranking)

The maturity tag — **production / research / rejected** — is a **DERIVED state, not an independent dimension and
not authored**. It is derived from four inputs: **{mechanism = pass · the three graded axes (§1.1–§1.3) · a dated
sign-off · an answerable "why does this deserve to be in front of an investor making decisions?"}**. An author
never hand-sets it. The old "implementation maturity" confidence dimension is DROPPED entirely: it was circular
(it merely equalled this tag), so maturity is no longer an input to itself — it is purely the derived output of
the gate + the three axes + the sign-off + the investor-question.

> **Descriptive, NOT a quality ranking (D-13).** A production signal is **NOT "better"** than a research
> signal. The tag says only **how far the research + validation process has progressed** — not that a higher
> stage is more trustworthy as a market call, more likely correct, or higher predictive quality. All candidates
> are researched freely; maturity is a label on how far along a signal is, never a gate on which signals are
> worth studying and never a statement about predictive value.

Derivation rule (proposed):

| Tag | Derivation rule |
|-----|-----------------|
| **production** | mechanism = **pass** · measurement validity ≥ **M** · investment usefulness = **H** · evidence maturity = **H** (international out-of-hypothesis-sample confirmed) · structural failure modes mapped · dated sign-off present · a clear answer to "why does this deserve to be in front of an investor?". *(Today: volatility only.)* |
| **research** | Mechanism passed and built + characterized, but not all of the above are cleared (e.g. no international OOS yet, an unresolved placebo / control, or a vintage-sensitivity risk). Renders as human context, NOT investor-facing / production. |
| **rejected** | Terminal. Failed the mechanism prerequisite gate, or failed a specific validation gate — did not generalize, no unique information, or a disguised forecast. Recorded WITH the reason so it is not silently revived. *(Today: dispersion-as-lead; raw-credit-as-a-vol-feature; VIX/VRP as a separate axis.)* |

**The derivation rule is `[ADOPTED v1.0 — Adam 2026-08-03; amendable via semver]`** (research A2). The one open
sub-point — whether a documented universal stylized fact substitutes for a literal Japan/Europe OOS in reaching
evidence-maturity = H — is RF, left OPEN by design (see `SIGNOFF-CHECKLIST.md`).

---

## 3. Supersession record

**(0) The four-dimension confidence model is itself now SUPERSEDED by the unified admission model** (this
revision). The four graded dimensions (measurement quality · mechanism support · evidence robustness ·
implementation maturity) are replaced by a **binary mechanism prerequisite gate + three non-compensatory graded
axes + a derived maturity tag**. Mapping:

| Old four-dim | Unified admission model |
|---|---|
| measurement quality | → **measurement validity** (axis) |
| mechanism support (graded H/M/L) | → **mechanism prerequisite gate** (graded → **binary** pass/rejected) |
| evidence robustness | → **evidence maturity** (axis) |
| implementation maturity | → **DROPPED** — becomes the DERIVED maturity tag, no longer an input dimension |
| *(new)* | → **investment usefulness** (axis: important question + unique information) |

`current-relevance` / `regime-relevance` / `portfolio-relevance` stay DROPPED (predictive framing). The A1 anchor
thresholds now apply to the **three axes**, not four dimensions. The two earlier supersessions still stand and
are retained below for the audit trail.

---

The (now-superseded) four-dimension research-maturity confidence model had itself **superseded two earlier
models**:

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
research-process meaning. The current-relevance → implementation-maturity swap (D-06) is **RESOLVED — superseded
by ADM (D-17)** (Adam, 2026-08-03): the entire four-dimension model is replaced by the unified admission model,
so this swap no longer stands as an independent change.

**Upstream docs PATCHED at v1.0 sign-off** (research A5; 2026-08-03). ROADMAP.md SC#3 and
REGIME-SENSOR-ARCHITECTURE.md previously carried the superseded three-dimension ("three confidence dimensions" /
"the three confidence scores") text. At the framework freeze (Adam, 2026-08-03) that stale text was patched to
the unified admission-model wording, so the drift the deferral guarded against is now resolved rather than merely
documented. This supersession record is retained for the audit trail.

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
  assessment: {
     mechanism:            "pass|rejected",   // binary prerequisite gate (§1.0)
     measurement_validity: "H|M|L",
     investment_usefulness:"H|M|L",
     evidence_maturity:    "H|M|L"
  },
  maturity:             "production|research|rejected",   // DERIVED (§2)
  spec_version:         "<semver of the template filled>"
}
```

This is a **closed field set** — the schema the code pass will enforce (see the code-level enforcement note at
the end of §4).

`trend`, `extreme_conditions`, and `cross_signal_relationships` were added 2026-08-03 (the observatory-framing
refinement) so each signal describes not just its level but its *direction*, whether it sits at a historical
*extreme*, and how it *relates* to the other signals — the descriptive richness that makes the set an
observatory rather than disconnected readings. `cross_signal_relationships` carries the *known / characterized*
relationships (template Q4.3); the **live joint** reading (this configuration's joint rarity + analogues) is a
Level-2 lens (§4.3), never collapsed into a per-signal field. These field definitions are **CONFIRMED v1.0 (Adam
2026-08-03)** alongside the other OBS observatory-framing items.

**Zero allocation / decision fields.** No allocation, exposure, weight, sleeve, tilt, cash, action,
recommendation, or "portfolio" — the record names a monitored market assumption and its reading (level, trend,
rarity, extremity, relationships), and STOPS. `trend` and `extreme_conditions` are descriptive state, never a
buy/sell trigger.

### 4.2 Level 1 — historical context (the assumption ledger, THE product)

Each monitored market assumption × `{status ∈ intact | under-test | violated · sensor evidence · rarity ·
the admission assessment}`. **Status is an OBSERVATION, never an instruction** — "the bond-hedge assumption is under test,"
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
human, never a call. **Analogues read strictly as "these conditions occurred before and these were the observed
outcomes," NEVER "this will happen again"** — a nearest-neighbour match is a historical resemblance, not a
forecast.

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

**A3 (forbid any composite-scalar output field) is CONFIRMED v1.0 (Adam, 2026-08-03)** in
`SIGNOFF-CHECKLIST.md`.

### 4.5 No-dominance / co-equal presentation (D-11)

Signals are presented **co-equally**. There is NO weighting, ranking, precedence, or aggregation that lets any
single signal override the vector. Signal **disagreement is information**, not a failure to be resolved into
consensus. This extends D-07 (independent research modules) into the presentation layer and sits alongside the
composite-scalar prohibition: both defend the same invariant — the full per-signal vector is the product, and it
is never collapsed, never rank-ordered, never overruled by one dimension.

### 4.6 Code-level enforcement (architecture, not documentation-only)

The Level-0 `assessment{}` + closed field set above is enforced in the code pass by a **schema allowlist** (only
the enumerated fields may appear in a Level-0 record) plus a runnable **boundary-audit test** (asserts no
allocation / decision / composite-scalar field is ever emitted). Enforcement is part of the architecture — the
boundary lives in executable checks, not in prose alone (D-18). The code itself is built in the next pass; this
spec fixes the field set it will enforce.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
