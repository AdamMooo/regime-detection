# Phase 1: Signal Framework - Research

**Researched:** 2026-08-03
**Domain:** Rigorous per-item specification / evaluation standards (documentation design), not software
**Confidence:** HIGH (analog frameworks verified; reconciliation grounded in project's own authoritative docs; proposed rubric anchor wording is ASSUMED design and needs sign-off)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** The system is a **market-state intelligence** system, not a trading system and not a prediction engine. It explains: *what is happening · why it may be happening · what historical environments look similar · how unusual the current environment is · what risks and opportunities are present* — then STOPS.
- **D-02:** Hard prohibitions on every output: never collapse the market into one score; never produce a single bullish/bearish (or risk-on/risk-off) answer; never dictate or imply any downstream investment action or decision; never pretend to predict future returns.
- **D-03:** The output is always a **multi-dimensional market-state vector**. The complexity IS the information. Disagreement between signals is valuable and must be preserved — signals are never forced into agreement or reconciled into consensus.
- **D-04:** Every signal declares against the **same 8-attribute standard**, in this order: (1) **Definition** — what it measures + the economic mechanism it represents; (2) **Mechanism** — why it should contain information (why it survives being known); (3) **Measurement** — how calculated, data sources required, limitations of that measurement; (4) **Historical Context** — how it has behaved historically, regimes identified, false positives / false negatives; (5) **Validation** — holds across periods, survives international OOS, robust or regime-dependent; (6) **Assumptions** — what assumptions it requires and when they fail; (7) **Confidence** — multidimensional, never a single number (see D-06); (8) **Limitations** — what it can tell us and, explicitly, what it cannot.
- **D-05:** The 8-attribute standard is **authoritative**. It refines the earlier attribute list in `.planning/REGIME-SENSOR-ARCHITECTURE.md` (research question · mechanism · data · metric · validation · failure modes · historical-context · maturity). The planner must **reconcile** the two into one template, treating D-04 as source of truth where they differ, while preserving anything from the architecture doc not contradicted (notably the maturity tag — D-08 — and the intl-OOS + mechanism-gate + prereg standards, which map onto attributes 2/5).
- **D-06:** Confidence is **multidimensional**, never a single score. The dimensions are: **data-quality confidence · historical-robustness confidence · mechanism confidence · current-relevance confidence.** This authoritatively replaces the earlier 3-dimension model (measurement / interpretation / relevance-guard). Mapping: measurement→data-quality, interpretation→historical-robustness + mechanism, relevance-guard→current-relevance. "Current-relevance" is the boundary-safe rename — no implementation/allocation concept implied.
- **D-07:** Signals are **independent research modules**. Each has its own research process, validation, assumptions, limitations. Independence is prioritized; the framework must not induce a shared latent state or force cross-signal agreement.
- **D-08:** The historical-context output format must specify, per signal: current **reading**, historical **rarity** (percentile), the **assumption monitored**, the four confidence dimensions (D-06), and a **maturity tag** (production / research / rejected). Zero allocation/decision fields.
- **D-09:** The composed output preserves the **full per-signal vector** — one reading per dimension. It is forbidden to transform this into any composite scalar (e.g. "market risk = 73/100"). The **assumption-ledger shape** is the composition target (Level 0 state vector · Level 1 assumption ledger · Level 2 context), defined here so later signals render into a known place — never a combined score.

### Claude's Discretion
- File format/serialization of the template (Markdown spec doc vs. a fillable schema), file locations within the repo, and section ordering of the standards doc — provided D-01…D-09 are honored.
- How to physically split the work across the two roadmap plans (01-01 template+standards, 01-02 output/confidence/maturity/ledger), as long as both plans together cover every decision above.

### Deferred Ideas (OUT OF SCOPE)
- None new. Every individual signal (valuation, concentration, absorption, credit/EBP, funding, crowding, tail, stock-bond intl OOS) is already scoped to its own later phase (2–9); the presentation/assumption-ledger assembly to Phase 10. This phase only freezes the framework they declare against.
- **Also out of scope (from CLAUDE.md HARD BOUNDARY):** any allocation / exposure / weight / sleeve / tilt / cash concept; the word "portfolio"; any one-word regime summary; any composite score; any prediction/forecast as the deliverable.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FRWK-01 | The shared signal spec exists — 8-attribute template, validation standards, the historical-context/assumption-ledger output format, and the maturity model — that every subsequent signal declares against before it runs. | This research supplies: (a) established analog specification frameworks to borrow structure and *enforcement mechanisms* from (§Standard Stack, §Architecture Patterns); (b) a concrete merged 8-attribute template reconciling D-04 with the architecture doc, resolving where maturity / failure-modes / FP-FN live (§Reconciliation); (c) an anchored 4-dimension confidence rubric so scores are reproducible not hand-wavy (§Confidence Model); (d) a concrete full-vector output + 3-level ledger spec that renders without a composite scalar (§Output Format); (e) template-freezing pitfalls + a versioning discipline that leaves controlled room without per-signal forking (§Common Pitfalls). |
</phase_requirements>

## Summary

This is a **documentation/specification** phase. The deliverable is written artifacts — a signal-spec template, a validation-standards doc, and an output/confidence/maturity/ledger spec — under version control. No signal, no code, no data pipeline. The core design problem is therefore identical to a well-studied class of problems: **how to build a rigorous, reusable per-item reporting/evaluation standard that many independent authors fill in consistently over time without each one silently reinterpreting it.** The mature analogs are ML **model cards** (Mitchell et al. 2019), **datasheets for datasets** (Gebru et al. 2018), clinical **GRADE** evidence-certainty grading, **TRIPOD** prediction-model reporting checklists, and **registered reports / preregistration** protocols. Each has solved a piece of exactly this problem, and their *enforcement mechanisms* — not just their field lists — are what the planner should borrow.

The five enforcement patterns that make those analogs work and map directly onto this framework: (1) **question-form fields with a forced explicit "N/A because…" answer** (datasheets) — prevents silent omission across heterogeneous signals; (2) **anchored H/M/L rubric levels with explicit criteria and a declared starting point** (GRADE) — makes the 4 confidence dimensions reproducible instead of gestalt; (3) **a completeness checklist that gates sign-off** (TRIPOD); (4) **a temporal freeze — protocol locked before results, deviations disclosed not hidden** (registered reports) — this is already the project's prereg + cooling-off + dated sign-off discipline; (5) **an explicit "intended use / out-of-scope / what it cannot tell us" section** (model cards) — which is the natural home for the HARD BOUNDARY inside every signal declaration.

Two reconciliations must be handled explicitly and are flagged throughout: (a) **the confidence model — CONTEXT.md D-06 (four dimensions) overrides both the architecture doc (three: measurement/interpretation/regime-relevance) and ROADMAP.md Success-Criterion #3 (which still says "three confidence dimensions")**; the ROADMAP text is stale on this point. (b) **The 8-attribute standard (D-04) vs the architecture doc's mini-study spec + six-point evaluation** — everything in the architecture doc maps cleanly into the D-04 attributes plus a small header block, losing nothing.

**Primary recommendation:** Do not invent a bespoke framework. Adopt the **model-card document shape** (attribute sections + an explicit limits/out-of-scope section), the **datasheet question-form + forced-N/A discipline**, the **GRADE anchored-rubric method** for the four confidence dimensions, the **TRIPOD completeness-checklist** as the sign-off gate, and the **registered-report temporal freeze** as the validation-standards backbone. Then **retro-fit the template against the two already-built signals (volatility, stock-bond correlation) before declaring it frozen** — that back-fill is the cheap test that the template actually fits real, heterogeneous signals.

## Architectural Responsibility Map

The phase produces documents, so the "tiers" are the documents and where each responsibility is owned. This mirrors the two-plan split under Claude's discretion.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| The 8-attribute spec template (what every signal declares) | Template doc (Plan 01-01) | — | Single source of truth; signals fill this in |
| Validation standards (causal/PIT, mechanism gate, confound-check, intl-OOS, prereg+cooling-off+sign-off) | Standards doc (Plan 01-01) | Template attributes 2 & 5 reference it | Standards are cross-signal law; the template *points at* them |
| Multidimensional confidence model (4 dims + anchored rubric) | Output/confidence spec (Plan 01-02) | Template attribute 7 references it | Confidence is a scoring method reused by every signal |
| Historical-context output format (per-signal record) | Output/confidence spec (Plan 01-02) | Template attribute 4 & 7 feed it | The output is derived from the filled template |
| Maturity model (production/research/rejected + derivation rule) | Output/confidence spec (Plan 01-02) | Derived from attributes 5 & 7 | Maturity is a *derived label*, not a spec attribute |
| Assumption-ledger shape (Level 0/1/2 composition target) | Output/confidence spec (Plan 01-02) | Consumed later by Phase 10 | Composition target defined now so signals render into a known place |
| HARD BOUNDARY enforcement (no allocation/decision/score/"portfolio") | Every document | A dedicated boundary-check subsection in the standards doc | Boundary is invariant across all artifacts |

## Standard Stack

For a specification phase, the "stack" is the set of established reporting/evaluation frameworks to borrow *structure and enforcement mechanisms* from. All are public standards, not software dependencies — nothing is installed.

### Core (borrow structure + enforcement from these)
| Framework | Purpose | Why standard | What to borrow |
|-----------|---------|--------------|----------------|
| **Model Cards** (Mitchell et al. 2019, arXiv 1810.03993) | Short doc accompanying an ML model: details, intended use, factors, metrics, ethical considerations, caveats | The de-facto ML transparency standard; 9 fixed sections | The **"Intended Use" + explicit out-of-scope + "Caveats and Recommendations"** pattern → the natural home for the HARD BOUNDARY and attribute-8 Limitations. Disaggregated FP/FN/FDR/FOR metrics → the attribute-4 false-positive/false-negative record |
| **Datasheets for Datasets** (Gebru et al. 2018, arXiv 1803.09010) | 57 **questions** across 7 categories documenting a dataset's provenance/composition/uses | Forces authors to *answer questions*, not fill blanks | The **question-form field + forced explicit answer** discipline — every attribute is phrased as a question the signal author MUST answer (including "not applicable, because…"), which is what stops heterogeneous signals from silently leaving fields blank |
| **GRADE** (evidence-certainty grading; Cochrane / GRADE Working Group) | Rates a body of evidence: High / Moderate / Low / Very-low across explicit domains, with a declared starting point | The dominant reproducible evidence-grading method in medicine | **Anchored rating levels + explicit per-domain downgrade/upgrade criteria + a declared starting point** → the method for making the four confidence dimensions reproducible instead of gestalt |
| **Registered Reports / Preregistration** (COS; Nature/Scientific Reports policies) | Stage-1 protocol frozen and reviewed *before* data; in-principle acceptance; deviations disclosed transparently | The gold-standard defense against HARKing / result-driven analysis | **The temporal freeze**: protocol locked before results, deviations *disclosed not hidden*. This IS the project's existing prereg + overnight cooling-off + dated sign-off rule — cite it as the lineage for the validation-standards doc |
| **TRIPOD** (Transparent Reporting of prediction models; 22-item checklist / 2015 expansion 37 items) | A reporting checklist tied to study sections, enforced as a submission requirement | Standard completeness gate for prediction-model reporting | **A checklist that gates completeness** → a per-signal completeness checklist that must be fully answered before dated sign-off |

### Supporting (context, lighter borrow)
| Framework | Purpose | When to use |
|-----------|---------|-------------|
| Semantic Versioning (semver.org) | Version scheme (MAJOR.MINOR.PATCH) | Versioning the template itself so signals declare which version they filled (see §Common Pitfalls / versioning) |
| Kritzman-Li "Financial Turbulence" (2010) | Mahalanobis distance of a vector from its historical normal | The forecasting-free definition of **joint rarity** in Level 2 — already cited in the architecture doc; the planner should note it is *not* a composite risk score (see §Output Format pitfall) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Borrowing from established analogs | A bespoke framework invented from scratch | Reinvents solved problems; loses the battle-tested enforcement mechanisms; higher risk each signal reinterprets it. **Do not do this** — it is the central "don't hand-roll" of this phase |
| Markdown spec doc (prose template) | A machine-fillable schema (YAML/JSON Schema) | Schema enforces field presence programmatically but is heavier and less readable for a solo research workflow; prose + a completeness checklist gets most of the benefit. **Claude's discretion (D)** — recommend Markdown template + checklist for a 1-person research repo, matching the project's minimal-tooling bias |
| GRADE-style H/M/L | A numeric confidence score per dimension | A number invites false precision and re-collapse into a composite; anchored H/M/L labels resist that and match D-06's "never a single number" spirit per-dimension too |

**Installation:** None. This phase installs nothing and writes only Markdown documents under `.planning/` (and/or a repo `docs/`-style home — Claude's discretion D). No package legitimacy audit or environment audit applies (see those sections).

## Package Legitimacy Audit

**Not applicable.** This phase installs no external packages. The deliverable is prose specification documents under version control. No registry, no dependencies, no postinstall surface.

## Architecture Patterns

### System (information-flow) Diagram

How a single signal's declaration flows through the frozen framework into the composed ledger. This is the object the three documents jointly define; it is the reference the planner uses to check that the two plans together cover every decision.

```
                        ┌─────────────────────────────────────────────┐
   A NEW SIGNAL  ─────▶ │  8-ATTRIBUTE TEMPLATE  (Plan 01-01)          │
   (Phases 2–9)         │  header: name · assumption monitored · clock │
                        │          · spec-version · dated sign-off      │
                        │  1 Definition   5 Validation ───┐            │
                        │  2 Mechanism ───┐               │            │
                        │  3 Measurement  │               │            │
                        │  4 Hist.Context │               │            │
                        │  6 Assumptions  │               │            │
                        │  7 Confidence   │               │            │
                        │  8 Limitations  │               │            │
                        └───────┬─────────┼───────────────┼────────────┘
                                │         │               │
                 references     ▼         ▼               ▼
        ┌───────────────────────────────────────────────────────────┐
        │  VALIDATION STANDARDS  (Plan 01-01)                        │
        │  causal/point-in-time · mechanism gate · confound-check ·  │
        │  intl OOS (Japan/Europe) · prereg + cooling-off +          │
        │  dated sign-off · HARD-BOUNDARY check                      │
        └───────────────────────────────┬───────────────────────────┘
                                         │  attributes 5 & 7 pass through
                                         ▼
        ┌───────────────────────────────────────────────────────────┐
        │  CONFIDENCE MODEL + MATURITY  (Plan 01-02)                 │
        │  4 dims (data-quality · historical-robustness · mechanism  │
        │  · current-relevance), each anchored H/M/L                 │
        │  ─▶ maturity tag DERIVED (production / research / rejected)│
        └───────────────────────────────┬───────────────────────────┘
                                         ▼
   LEVEL 0  per-signal record: {reading · rarity pctile · assumption ·
            4 conf dims · maturity · clock · spec-version}   ← the state vector element
                                         │
                                         ▼
   LEVEL 1  ASSUMPTION LEDGER (the product): each assumption ×
            {status intact/under-test/violated · evidence · rarity · confidence}
                                         │
                                         ▼
   LEVEL 2  CONTEXT: joint rarity (Mahalanobis / turbulence) +
            nearest-neighbour historical analogues (configurations)

   ══════════════════════════════════════════════════════════════════
   HARD STOP.  No composite scalar. No score. No summary. No decision.
```

### Recommended Document Structure
```
.planning/  (or a docs/ home — Claude's discretion D)
├── signal-spec-template.md      # Plan 01-01: the 8-attribute template (question-form)
├── validation-standards.md      # Plan 01-01: the cross-signal law + completeness checklist
└── signal-output-spec.md        # Plan 01-02: confidence model + maturity + Level 0/1/2 ledger shape
```
Each references the others by name; a signal author reads the template, which points at the standards for attributes 2 & 5 and at the output spec for attribute 7.

### Pattern 1: Question-form fields with forced explicit answers (from datasheets)
**What:** Every attribute is written as a question the signal author must answer; leaving it blank is not permitted — the answer "Not applicable, because X" is required instead.
**When to use:** Every attribute, especially those that will legitimately differ across signal shapes (a fast binary funding flag genuinely has no multi-year historical-return context; a valuation conditioner genuinely has no fast-clock rarity).
**Example (illustrative template fragment — not code):**
```markdown
### 3. Measurement
- Q3.1 How is the reading calculated? (exact, causal construction)
- Q3.2 What data sources are required, and what is their vintage/revision exposure?
        (macro series get revised — state the point-in-time reconstruction, or "N/A: from asset returns")
- Q3.3 What is the native clock (daily / weekly / monthly / structural)?
- Q3.4 What are the limitations of this measurement?
```

### Pattern 2: Anchored rubric levels (from GRADE)
**What:** Each confidence dimension gets H/M/L with *written criteria* for each level and a declared starting point, so two people scoring the same signal land on the same label.
**When to use:** The four confidence dimensions (D-06). See §Confidence Model for the full proposed anchors.

### Pattern 3: Temporal freeze + disclosed deviations (from registered reports)
**What:** The signal's spec (esp. failure modes and validation plan) is fixed *before* the one-look validation run; any later deviation is logged with a dated note rather than silently edited in. This is the project's existing "one look, prereg + overnight cooling-off + explicit dated sign-off."
**When to use:** The validation-standards doc backbone. Attribute-6 failure modes are declared *before* testing; attribute-4 confirms or updates them after, with the deviation disclosed.

### Pattern 4: "Intended use / what it cannot tell us" section (from model cards)
**What:** An explicit, required Limitations section stating what the signal can and — emphatically — cannot support, plus an out-of-scope statement.
**When to use:** Attribute 8. This is also where the HARD BOUNDARY lives per-signal: "this reading names a monitored market assumption and STOPS; it implies no action."

### Anti-Patterns to Avoid
- **A single numeric confidence score.** Violates D-06. Even per-dimension, prefer anchored labels over numbers to resist re-collapse.
- **A composite market score / "risk = 73/100".** Violates D-02/D-09. See the joint-rarity distinction in §Output Format — joint rarity is *not* this.
- **A blank field left unanswered.** Violates the datasheet discipline; use forced "N/A because…".
- **Editing the template to fit one signal.** Violates the single-source-of-truth goal; use versioning instead (§Common Pitfalls).
- **Any allocation/decision/"portfolio" vocabulary anywhere.** Violates the HARD BOUNDARY.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| A per-item spec/reporting standard | A bespoke framework invented from first principles | Model-card section shape + datasheet question discipline | These solved "consistent documentation by many independent authors over time"; reinventing loses their enforcement mechanisms |
| Reproducible confidence ratings | Free-text confidence prose, or ad-hoc numbers | GRADE-style anchored H/M/L with per-level criteria + declared starting point | Anchoring is the difference between reproducible and gestalt; numbers invite false precision + re-collapse |
| A completeness gate | Trusting the author to remember every field | A TRIPOD-style checklist that must be fully answered before dated sign-off | A checklist is the cheapest enforcement that a heterogeneous set of signals all declared fully |
| Defense against result-driven specs | Informal "be honest" norms | The registered-report temporal freeze (already the project's prereg + cooling-off + sign-off) | The freeze is structural, not aspirational; it's already project law |
| Joint "how unusual overall" | A homegrown composite risk index | Mahalanobis/turbulence distance (Kritzman-Li 2010), presented as a Level-2 lens, never the primary object | Rarity is forecasting-free and distance-not-score; a composite index is a forbidden scalar |

**Key insight:** The entire phase is a "don't hand-roll" — the temptation is to design a clever bespoke evaluation framework. The evidence-grading, model-documentation, and preregistration communities have each already built and stress-tested the exact machinery (anchored rubrics, question-form fields, completeness checklists, temporal freezes, explicit-limits sections). Borrow the machinery; spend the creativity on the market-domain content and the HARD BOUNDARY.

## The Reconciliation (D-05) — merged template

This is the load-bearing planning deliverable. Everything in the architecture doc's mini-study spec + six-point evaluation maps into the D-04 attributes plus a small header block. **D-04 is authoritative on wording and order; nothing from the architecture doc is lost.**

### Merged template: header + 8 attributes

**Header block** (carries the fields that must travel with the output and that don't belong inside a single attribute):
- **Signal name**
- **Assumption monitored** — the ledger key (architecture "assumption tested"; also D-08 output field). *Load-bearing enough to be a header field AND surfaced in attribute-1 Definition.*
- **Native clock / frequency** — daily/weekly/monthly/structural (architecture "frequency"). Also surfaces in attribute-3 Measurement and in the Level-0 record.
- **Maturity tag** — production / research / rejected (see below: derived, not authored).
- **Spec/template version** — semver of the template this declaration was filled against (§Common Pitfalls).
- **Dated sign-off** — the registered-report freeze marker.

**The 8 attributes (D-04 order) with architecture-doc fields folded in:**

| # | D-04 Attribute | Architecture-doc fields folded in | Notes |
|---|----------------|-----------------------------------|-------|
| 1 | **Definition** | "assumption tested" / "research question" | What it measures + the assumption it monitors (also in header) |
| 2 | **Mechanism** | "hypothesis"; the **mechanism gate** | Why it survives being known — the gate is enforced here (points at validation-standards doc) |
| 3 | **Measurement** | "data" (+ **vintage/revision**), "frequency/clock", "statistical method" / "metric" | How calculated, sources, PIT/vintage handling, native clock, measurement limitations |
| 4 | **Historical Context** | historical-context output; **false positives / false negatives** (D-04 explicit) | The *empirical* record of behavior + the FP/FN it actually produced |
| 5 | **Validation** | "validation process" = the **six-point evaluation**; **intl OOS**; confound-check | Holds across periods? survives Japan/Europe OOS? robust or regime-dependent? Points at validation-standards doc |
| 6 | **Assumptions** | **failure modes** (declared *before* testing) | What the signal assumes + *when those assumptions fail* — the declared-before-testing failure conditions live here |
| 7 | **Confidence** | the confidence dimensions | 4 anchored dims (D-06); points at the confidence model in the output spec |
| 8 | **Limitations** | (model-card "caveats" pattern) | What it can and — explicitly — cannot tell us; the per-signal HARD-BOUNDARY statement |

### The specific questions the objective asked

- **Where does the maturity tag live?** In the **header block / Level-0 output record**, and it is **derived**, not authored — computed from attribute-5 Validation status + the attribute-7 Confidence vector (see §Maturity model). It is *not* one of the 8 spec attributes. This matches D-08 (maturity is an output field) and the architecture doc (the tag "travels with the output into the understanding layer").
- **Where do failure modes vs false-positive/false-negative live?** Split deliberately, and the split is meaningful:
  - **Failure modes** = the *structural conditions under which the signal is expected to break*, **declared before testing** → **attribute 6 (Assumptions)** ("when those assumptions would fail"), and echoed in **attribute 8 (Limitations)**. This is the registered-report prereg artifact.
  - **False positives / false negatives** = the *empirical record* of what the signal actually got wrong in history → **attribute 4 (Historical Context)** (D-04 names FP/FN explicitly there). This is the model-card disaggregated-error pattern.
  - The relationship: attribute-6 failure modes are the *hypotheses*; attribute-4 FP/FN are the *observed confirmation-or-update* of those hypotheses, with any deviation disclosed (registered-report discipline).

### Confidence-model reconciliation (D-06 vs architecture vs ROADMAP)

| Old 3-dim (architecture doc + memory + ROADMAP SC#3) | New 4-dim (D-06, AUTHORITATIVE) |
|---|---|
| Measurement confidence | → **Data-quality confidence** |
| Interpretation confidence | → **Mechanism confidence** *and* **Historical-robustness confidence** (split into two) |
| Regime-relevance confidence (the subordination guard) | → **Current-relevance confidence** (boundary-safe rename) |

**⚠ Flag for the planner (documentation drift to resolve):** ROADMAP.md Success-Criterion #3 for Phase 1 still reads "the three confidence dimensions (measurement · interpretation · regime-relevance)". CONTEXT.md D-06 **overrides** this to four dimensions. The architecture doc §"The three confidence dimensions" is likewise superseded. The plans should (a) implement the four-dimension model, and (b) note in the delivered docs that they supersede the three-dimension text in ROADMAP SC#3 and REGIME-SENSOR-ARCHITECTURE.md, so the drift is recorded rather than left as a silent contradiction. Whether to *edit* those upstream docs is a planner/Adam call (GSD owns `.planning/`); at minimum the new spec should state the supersession.

## Confidence Model (the four dimensions, anchored)

Proposed GRADE-style anchors so the four D-06 dimensions are reproducible. **These anchor definitions are a design proposal `[ASSUMED]` and need Adam's sign-off** — confidence rubrics are exactly the "multiple valid approaches" case where wording must be confirmed, not asserted. The *structure* (four dims, anchored H/M/L, declared starting point) is grounded in D-06 + GRADE; the *thresholds* are the proposal.

### 1. Data-quality confidence — *can we observe it reliably, causally, from available data?* (was: measurement)
- **H:** Causal construction from point-in-time / non-revised data (e.g. asset returns); no vintage look-ahead; full usable history; no material proxy substitution.
- **M:** Some vintage/revision exposure, handled with a documented point-in-time reconstruction; OR a proxy stands in for part of the history; OR history is short.
- **L:** Requires revised or un-sourced data (e.g. options/HF not yet available); material vintage look-ahead unresolved; or heavy proxying. *(Architecture flags the tail signal L here by design.)*

### 2. Historical-robustness confidence — *does the descriptive property hold across periods and out-of-sample?* (from splitting: interpretation)
- **H:** Property replicates across sub-periods **and** on the out-of-hypothesis-sample panels (Japan/Europe) with the pattern intact; confounds checked.
- **M:** Holds in-sample across periods, but international OOS not yet run or only partial; OR robust with a documented, understood regime-dependence.
- **L:** In-sample / single-period only, OR failed a sub-period or placebo control. *(Compare the killed dispersion-lead: US −40d did not generalize → would be L.)*

### 3. Mechanism confidence — *do we understand WHY (a durable structural reason), not just a correlation?* (from splitting: interpretation)
- **H:** A written, literature-grounded structural reason (a risk-premium or risk-management channel) it survives being known; passes the mechanism gate cleanly.
- **M:** A plausible mechanism with an unresolved ambiguity (e.g. concentration's healthy-vs-fragile) or a declared partial redundancy (e.g. absorption ratio "is a factor of" vol).
- **L:** Correlation without a durable structural reason, or the mechanism is a disguised forecast → fails the gate.

### 4. Current-relevance confidence — *does a named market assumption genuinely depend on this reading being true?* (boundary-safe rename of: regime-relevance / subordination guard)
- **H:** Monitors a load-bearing market assumption whose truth genuinely matters to understanding the environment (e.g. "bonds hedge equity drawdowns").
- **M:** Relevant but conditional or narrow (tail-insurance-only; long-horizon-only; factor-crowding-only).
- **L:** Interesting but **no monitored market assumption depends on it** — a research curiosity that must NOT be surfaced as a trusted input.

**Boundary note on dimension 4:** phrase this dimension strictly in terms of *whether a named market assumption depends on the reading* — never in terms of a decision, action, exposure, or "portfolio-relevance." That phrasing is the boundary-safe form of the old subordination guard (the architecture doc's "regime-relevance"/"portfolio-relevance guard" wording must NOT be copied verbatim — it leaks implementation framing).

**Declared starting point (GRADE lesson):** state where each dimension *starts* before evidence adjusts it. Recommend: a signal built purely from asset returns starts data-quality at H; a signal needing macro vintages or options data starts data-quality at M or L. Historical-robustness starts at L until intl-OOS is run (mirrors the standing rule that nothing is SUPPORT before Japan/Europe confirmation). This makes the ratings auditable, not gestalt.

## Maturity model (derived label)

Maturity is **derived** from the Validation status (attribute 5) and the Confidence vector (attribute 7); it is not independently authored and it is **not a gate on research** (all candidates are explored freely) — it is a label on how far the output is trusted. Grounded in the architecture doc's maturity section.

| Tag | Derivation rule (proposed — `[ASSUMED]`, needs sign-off) |
|-----|----------------------------------------------------------|
| **PRODUCTION** | Data-quality ≥ M, mechanism = H (gate passed), historical-robustness = H (international OOS confirmed), failure-mapped, with a dated sign-off. *(Today: volatility only.)* |
| **RESEARCH** | Built + characterized, but an open discipline gap (no intl OOS yet, unresolved placebo/control, or unresolved vintage risk). Renders as human context only. |
| **REJECTED** | Failed a specific gate (did not generalize, no distinct mechanism, or is a disguised forecast). Recorded with the reason so it is not silently revived. *(Today: dispersion-as-lead; credit-as-a-vol-feature; VIX/VRP as a separate axis.)* |

## Output Format (D-08 / D-09 / D-03) — full-vector, no scalar

### Level 0 — per-signal record (the state-vector element)
Exactly the D-08 fields, no more:
```
{
  signal:              "<name>",
  assumption_monitored:"<the ledger key, e.g. 'bonds hedge equity drawdowns'>",
  reading:             "<qualitative + quantitative, e.g. 'stock-bond corr positive, +0.35'>",
  rarity:              "<historical percentile + how computed, e.g. '85th pctile, trailing 60y>'",
  clock:               "<daily|weekly|monthly|structural>",
  confidence: {
     data_quality:         "H|M|L",
     historical_robustness:"H|M|L",
     mechanism:            "H|M|L",
     current_relevance:    "H|M|L"
  },
  maturity:            "production|research|rejected",
  spec_version:        "<semver of the template filled>"
}
```
**Zero allocation/decision fields.** No weight, exposure, sleeve, tilt, cash, action, recommendation, or "portfolio."

### Level 1 — the assumption ledger (the product)
Each monitored assumption × `{status ∈ intact | under-test | violated, sensor evidence, rarity, confidence}`. **Status is an observation, never an instruction** — "the bond-hedge assumption is under test," never "sell bonds." The canonical worked example (from CONTEXT.md §Specific Ideas), which must be preservable and legible:

| Market assumption | Signal(s) | Status (example read) |
|---|---|---|
| "Bonds will hedge an equity drawdown" | inflation / real-rate (stock-bond corr) | under test — corr turned positive, 85th pctile |
| "The index isn't dependent on a few names" | concentration | under test — HHI 95th pctile |
| "Diversification is functioning" | absorption ratio | intact |
| "Factor premia aren't crowded" | crowding | intact |

The six-reading vector from CONTEXT.md (valuation: expensive · volatility: elevated · breadth: weakening · liquidity: supportive · credit: stable · concentration: historically high) must stay legible as six independent readings and **must never** become "market risk = 73/100."

### Level 2 — context
Joint rarity + nearest-neighbour historical analogues (configurations, e.g. "resembles 2018-Q4 / early-2022"), forecasting-free.

### ⚠ The joint-rarity vs composite-scalar distinction (a genuine trap for the planner)
D-09 forbids collapsing the per-signal vector into a scalar. **Joint rarity (Mahalanobis / turbulence distance) is not that forbidden scalar** and must be allowed — it appears in ROADMAP Phase-10 SC#2 and the architecture doc's Level 2. The distinction the spec must state explicitly:
- **Allowed:** joint rarity = "how far the *whole configuration* is from historical normal." It is a distance, forecasting-free, and it **does not rank-order into good/bad or better/worse** — two configurations equally far from normal can be opposite worlds. It is computed *from* the preserved vector and sits *beside* it as a Level-2 lens; it never replaces the per-signal readings.
- **Forbidden:** a composite "risk score" that (a) claims market is safer/riskier, (b) implies an action, or (c) erases the per-signal stories. "market risk = 73/100" is forbidden; "joint configuration at the 92nd percentile of historical unusualness, driven by concentration + stock-bond-corr" is allowed.

The output spec should carry this paragraph verbatim-in-spirit, because a reader could otherwise misread D-09 as banning the very joint-rarity lens Phase 10 requires. (The architecture doc's note that a CISS-style composite is permitted *only as a derived secondary view* is superseded by D-09 for this framework: recommend the spec forbid any composite-scalar output field entirely, and permit only joint rarity as defined above. Flag this as a reconciliation for Adam.)

## Common Pitfalls

### Pitfall 1: Freezing the template before any real signal has been filled against it
**What goes wrong:** The template looks clean in the abstract but doesn't fit real, heterogeneous signals — a fast binary funding flag, a very-slow valuation conditioner, and an eigenstructure absorption ratio have genuinely different shapes.
**Why it happens:** Designing a template top-down without a test case.
**How to avoid:** **Retro-fit the template against the two already-built signals — volatility (shipped) and stock-bond correlation (built) — before declaring it frozen.** These are free, real, heterogeneous test cases. If both fill cleanly (including honest "N/A because…" answers), the template fits. This is the single highest-value planning recommendation and should be an explicit task in Plan 01-01.
**Warning signs:** An attribute that only makes sense for one signal shape; fields that would be blank rather than "N/A because…" for a whole class of signals.

### Pitfall 2: Over-rigid template forces "N/A" noise or silent forking
**What goes wrong:** A one-shape-fits-all template makes some signals leave fields blank (looks incomplete) or quietly reinterpret an attribute to fit (silent fork) — the exact thing FRWK-01 exists to prevent.
**Why it happens:** Not distinguishing universal-required attributes from signal-shape-conditional ones.
**How to avoid:** Mark each attribute/question as **universal-required** vs **conditional**, and require the datasheet-style forced explicit "Not applicable, because X" for conditional ones. Every attribute is answered; none is blank; none is reinterpreted.
**Warning signs:** Two signals answering the same attribute in incompatible senses.

### Pitfall 3: The template forks per-signal instead of being versioned
**What goes wrong:** Signal 5 needs a field the template lacks, so its author edits the template — now there are effectively N templates and the single-source-of-truth is gone.
**Why it happens:** No versioning discipline; no rule against editing to fit.
**How to avoid:** **Semver the template.** Each signal declaration records the template version it filled. A signal never edits the template to fit itself; if a genuine gap appears, the template gets a versioned amendment (MINOR for additive, MAJOR for a breaking change) applied uniformly, with a changelog, and prior signals note which version they were signed off against (registered-report "deviations disclosed" discipline). This is the "controlled room without forking" answer the objective asks for.
**Warning signs:** Any diff to the template inside a signal-phase branch that isn't a deliberate, changelogged version bump.

### Pitfall 4: The subordination guard leaks implementation framing
**What goes wrong:** The fourth confidence dimension, described as "regime-relevance" or "portfolio-relevance guard" (its historical names), smuggles decision/allocation framing back into the boundary-clean repo.
**Why it happens:** Copying the old wording from the architecture doc / memory verbatim.
**How to avoid:** Use **current-relevance**, phrased strictly as "does a named market assumption depend on this reading" — no decision, action, exposure, or "portfolio" vocabulary. (D-06 mandates exactly this rename.)
**Warning signs:** The word "portfolio," "allocation," "decision," or "exposure" anywhere in the confidence definitions.

### Pitfall 5: A composite scalar (or joint rarity misclassified as one)
**What goes wrong:** Either a forbidden "risk = 73/100" composite creeps in, OR the required joint-rarity lens gets cut because someone over-applies D-09. Both are failures.
**Why it happens:** The distinction between "distance-from-normal" and "risk score" is subtle.
**How to avoid:** State the §Output-Format distinction explicitly in the spec; forbid composite-scalar output fields; permit joint rarity defined as forecasting-free distance that does not rank good/bad.
**Warning signs:** Any single number presented as *the* market read; or a Phase-10 plan with no joint-rarity lens.

## Runtime State Inventory

Not a rename/refactor/migration phase — this phase creates new specification documents. **No runtime state to inventory.** The only "state" adjacent to this phase is documentation drift (ROADMAP SC#3 and the architecture doc carry the superseded 3-dimension confidence model); that is handled in §Reconciliation and §Open Questions, not as runtime state.

## Environment Availability

**SKIPPED (no external dependencies).** The phase produces Markdown specification documents. No tools, services, runtimes, or CLIs are required beyond a text editor and git, both already in use.

## Security Domain

`security_enforcement` is not set in `.planning/config.json` (absent = enabled), so this section is included — but the phase produces **prose specification documents only**: no executable code, no data ingestion, no authentication, no input handling, no network surface. Standard application-security threat modeling does not apply.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface — documents only |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Git repo access governs the files; no app access control |
| V5 Input Validation | no | No inputs processed |
| V6 Cryptography | no | No secrets, no crypto |

**The one relevant integrity control is domain-specific, not ASVS:** the **HARD BOUNDARY** — the specification must contain zero allocation/decision/composite-score/"portfolio" content. Treat this as a content-governance check, enforced by a boundary-audit step in the standards doc and a grep-style review before sign-off (search the delivered docs for: portfolio, allocation, exposure, weight, sleeve, tilt, cash, buy, sell, risk-on, risk-off, and any composite-score phrasing). This is the phase's true "security" gate.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The proposed H/M/L **anchor definitions** for the four confidence dimensions | §Confidence Model | Anchors that are too loose/strict make ratings non-reproducible or mis-tag signals; needs Adam's sign-off (structure is grounded; thresholds are proposed) |
| A2 | The proposed **maturity derivation rule** (which confidence/validation combination yields production vs research) | §Maturity model | A wrong rule could over-trust an under-validated signal; needs sign-off |
| A3 | Recommendation to **forbid any composite-scalar output field entirely** (superseding the architecture doc's "CISS-style composite allowed as a derived secondary view") | §Output Format | If Adam wants a derived composite view retained, the spec would need to permit it as strictly secondary; D-09 reads as forbidding it, so default to forbid + flag |
| A4 | Markdown template + checklist recommended over a machine-fillable schema | §Standard Stack | If future signals are consumed programmatically, a schema might be preferred; low risk given solo research workflow + minimal-tooling bias |
| A5 | Recommendation to **record supersession of the 3-dim model in the delivered docs** rather than edit ROADMAP/architecture upstream | §Reconciliation | If Adam prefers upstream edits, that's a separate small task; either way the drift must be resolved, not left silent |

## Open Questions

1. **Should the superseded 3-dimension confidence text in ROADMAP.md SC#3 and REGIME-SENSOR-ARCHITECTURE.md be edited, or only noted as superseded by the new spec?**
   - What we know: D-06 (four dims) is authoritative and overrides both.
   - What's unclear: whether to touch the upstream docs (GSD owns `.planning/`).
   - Recommendation: the new spec states the supersession explicitly; the planner surfaces the upstream edit as an optional follow-up for Adam.
2. **Serialization: Markdown prose template vs a machine-fillable schema (YAML/JSON Schema)?** (Claude's discretion D.)
   - Recommendation: Markdown template + completeness checklist, matching the minimal-tooling bias; revisit only if a downstream consumer needs to parse declarations.
3. **Exact anchor thresholds for the four confidence dimensions and the maturity derivation rule.**
   - Recommendation: adopt the proposed anchors (A1/A2) as the draft, get Adam's dated sign-off, and freeze them as v1.0 of the confidence model.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 3-dimension confidence (measurement · interpretation · regime-relevance) | 4-dimension confidence (data-quality · historical-robustness · mechanism · current-relevance) | CONTEXT.md D-06, 2026-08-03 | Interpretation split into robustness + mechanism; relevance renamed boundary-safe. ROADMAP SC#3 + architecture doc are now stale on this |
| Architecture doc mini-study spec + six-point evaluation | D-04 8-attribute standard (authoritative) | CONTEXT.md D-04/D-05, 2026-08-03 | The 8-attribute list is the single template; architecture fields fold in without loss |
| Composite (CISS-style) permitted as a derived secondary view (architecture doc) | Composite-scalar output field forbidden; only joint rarity (distance-from-normal) permitted | CONTEXT.md D-09, 2026-08-03 | Removes an ambiguity that could have re-admitted a scalar risk score |

**Deprecated/outdated for this phase:**
- The "three confidence dimensions" text in ROADMAP.md Phase-1 SC#3 and in REGIME-SENSOR-ARCHITECTURE.md §"The three confidence dimensions" — superseded by D-06.
- The "regime-relevance" / "portfolio-relevance guard" naming — replaced by "current-relevance" (boundary-safe).

## Sources

### Primary (HIGH confidence)
- CONTEXT.md (D-01…D-09), REQUIREMENTS.md (FRWK-01), ROADMAP.md (Phase-1 SCs), REGIME-SENSOR-ARCHITECTURE.md, CLAUDE.md (HARD BOUNDARY) — the project's own authoritative decision + architecture docs.
- Model Cards for Model Reporting (Mitchell et al. 2019), arXiv 1810.03993 — 9-section structure; intended-use / out-of-scope / caveats pattern; disaggregated FP/FN metrics. [CITED]
- Datasheets for Datasets (Gebru et al. 2018), arXiv 1803.09010 — 57 questions across 7 categories; question-form discipline. [CITED]
- GRADE (Cochrane Handbook ch.14; GRADE Working Group) — 4 certainty levels, explicit domains, declared starting point. [CITED]
- Registered Reports / Preregistration (Center for Open Science; Nature / Scientific Reports policies) — Stage-1 frozen protocol, in-principle acceptance, disclosed deviations. [CITED]
- TRIPOD statement (2015; 22→37-item checklist) — reporting-checklist-as-completeness-gate. [CITED]

### Secondary (MEDIUM confidence)
- Kritzman-Li, "Skulls, Financial Turbulence, and Risk Management" (2010) — Mahalanobis-distance rarity; already cited in the architecture doc. [ASSUMED — from architecture doc, not re-verified this session]

### Tertiary (LOW confidence)
- None relied upon.

## Metadata

**Confidence breakdown:**
- Analog frameworks (structure + enforcement): HIGH — verified via web search against primary sources (arXiv, Cochrane, COS, TRIPOD).
- Reconciliation (D-04 vs architecture; D-06 vs 3-dim): HIGH — derived directly from the project's authoritative CONTEXT.md, cross-checked against ROADMAP/architecture text.
- Confidence-rubric anchors + maturity derivation: MEDIUM — structure grounded in D-06 + GRADE; specific thresholds are a design proposal `[ASSUMED]` needing Adam's sign-off (A1/A2).
- Output-format / joint-rarity distinction: HIGH — grounded in D-09 + architecture doc; the forbid-composite recommendation (A3) flagged for sign-off.

**Research date:** 2026-08-03
**Valid until:** ~2026-09-03 (stable — the analog frameworks are mature standards; the only volatility is internal doc reconciliation, which the plans resolve)

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/01-signal-framework/01-CONTEXT|01-CONTEXT]]

<!-- LINKS:END -->
