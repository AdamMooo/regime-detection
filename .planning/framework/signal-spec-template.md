# Signal Specification Template

**Template version: v1.1**

This is the single source of truth every signal declares against. It is filled **question-form**: each
attribute is a question the signal author must answer explicitly. No field may be left blank — a conditional
field that does not apply is answered `Not applicable, because …`, never omitted.

**The Stage-0 Relevance Gate precedes this template and the charter** (`validation-standards.md` §Stage 0 —
Relevance Gate, D-19). A candidate that has not passed the pre-charter triage (5 questions, default = NO,
leave-one-out test) is never declared against this template — no research time is spent filling it. v1.1
(2026-08-03) records this ordering; no attribute changed.

Version discipline: this template is semver-versioned and is never edited to fit one signal. A genuine gap
becomes a versioned amendment applied uniformly (see `validation-standards.md` §Template versioning). Each
signal records the version it filled. Frozen to v1.0 by Adam 2026-08-03; amendable only via semver amendment.

---

## Header block

Carries the fields that travel with the output and do not belong inside a single attribute. All six are
universal-required.

- **Signal name** —
- **Assumption monitored** — the ledger key: the abstract market assumption this signal exists to check
  (e.g. "bonds hedge equity drawdowns"). Also surfaced in attribute 1.
- **Native clock / frequency** — daily / weekly / monthly / structural. Also surfaced in attribute 3.
- **Maturity tag** — production / research / rejected. **DERIVED, not authored** — derived from {the mechanism
  prerequisite gate = pass · the three admission axes (attribute 7) · a dated sign-off · an answerable
  investor-question (see below)}. See `signal-output-spec.md` §2 for the derivation rule. Do not hand-set this
  field.
- **Investor question (production bar)** — the answer to *"Why does this deserve to be in front of an investor
  making decisions?"* This is a required question gating the **production** tag: a signal with no clear answer
  cannot reach production (it stays research). It is a question about understanding-relevance, never a forecast
  or an action.
- **Spec/template version** — semver of the template this declaration was filled against (e.g. `v1.0`).
- **Dated sign-off** — the registered-report freeze marker: the dated, explicit sign-off gating any positive
  claim. Blank until signed.

---

## The 8 attributes (D-04 order)

Each attribute lists its questions. Every question is marked **[universal-required]** or **[conditional]**.
Universal-required questions must be answered for every signal. Conditional questions must still be answered —
if they do not apply to this signal's shape, answer `Not applicable, because …`.

### 1. Definition

- Q1.1 What exactly does the signal measure? **[universal-required]**
- Q1.2 Which market assumption does it monitor (the ledger key from the header)? **[universal-required]**
- Q1.3 What specific **investment question** does this signal answer (e.g. "valuation: where do forward returns
  start from relative to history?")? This is the anti-disconnection anchor — a signal earns its place only by
  answering one concrete question about the environment, never for its own sake. **[universal-required]**
- Q1.4 **Why does that question matter** for understanding the market environment? Justify the signal's
  existence by its contribution to understanding — never by data availability. Data being available is *not* a
  sufficient reason to build a signal. (This is a declaration about understanding-relevance, not a forecast or
  applicability claim.) **[universal-required]**
- Q1.5 **What UNIQUE INFORMATION does this signal provide that existing signals do not?** The
  incremental-information declaration feeding the investment-usefulness admission axis. Supported by the
  ΔR²-vs-admitted-axes orthogonality diagnostic, **mechanism-first** — a signal statistically correlated with an
  admitted one is still unique if its mechanism is distinct; orthogonality is never a hard statistical
  accept/reject. **[universal-required]**

### 2. Mechanism

- Q2.1 Why should this contain information — the behavioral / economic / market-structure reason it survives
  being known? **[universal-required]**
- Q2.2 Is that reason a risk-premium or a risk-management channel (not "it backtests")? **[universal-required]**

The mechanism gate is enforced in `validation-standards.md` §The mechanism gate — a written structural reason
is required before the signal is preregistered. This attribute is where that reason is stated.

### 3. Measurement

- Q3.1 How is the reading calculated — the exact, causal construction (trailing / point-in-time, no
  look-ahead)? **[universal-required]**
- Q3.2 What data sources are required, and how sensitive are they to vintage / revision? Macro series get
  revised — state the point-in-time reconstruction, or answer `Not applicable, because …` (e.g. built from
  asset returns). **[conditional]**
- Q3.3 What is the native clock (daily / weekly / monthly / structural)? **[universal-required]**
- Q3.4 What are the limitations of this measurement? **[universal-required]**

### 4. Historical Context

- Q4.1 How has the signal behaved historically, and what regimes has it identified? **[universal-required]**
- Q4.2 What is its empirical false-positive / false-negative record — the errors it actually produced in
  history? **[conditional]** (answer `Not applicable, because …` if the signal has no back-history yet)
- Q4.3 What are its known **relationships to the other signals** — co-movement, lead/lag, redundancy, or
  conditioning? This keeps the signal connected to the set (not standalone) and feeds the Level-2 joint lenses;
  it describes *joint historical behavior only* and never implies a combined action. **[universal-required]**
  (answer `Not applicable, because …` only if it is the first signal with no others to relate to)

The empirical false-positive / false-negative record lives **here** (attribute 4). This is distinct from the
structural failure modes declared *before* testing, which live in attribute 6. Attribute-6 failure modes are
the hypotheses; the attribute-4 record is the observed confirmation-or-update of them, with any deviation
disclosed (see `validation-standards.md` §Temporal freeze).

### 5. Validation

- Q5.1 Does the relationship hold across sub-periods? **[universal-required]**
- Q5.2 Does the descriptive property survive out-of-hypothesis-sample confirmation on the Japan / Europe
  panels, or is a documented failure recorded? **[universal-required]**
- Q5.3 Is the relationship robust or regime-dependent, and are confounds ruled out? **[universal-required]**

Held to the cross-signal law in `validation-standards.md` (causal-only / point-in-time, confound-check,
out-of-hypothesis-sample confirmation, the one-look + prereg + cooling-off + dated sign-off freeze).

### 6. Assumptions

- Q6.1 What does the signal assume to be true? **[universal-required]**
- Q6.2 What are the structural failure modes — the conditions under which those assumptions break — declared
  **before** any validation run? **[universal-required]**

These declared-before-testing failure modes are the pre-registration artifact. They are echoed in attribute 8.

### 7. Admission Assessment

- Q7.1 State the admission assessment: **(a)** the mechanism prerequisite gate (**pass / rejected** — binary, a
  written structural reason it survives being known; fail = rejected, never admitted), then **(b)** the reading
  on each of the three graded axes — **measurement validity · investment usefulness · evidence maturity** — each
  anchored H/M/L, never a single number, and **non-compensatory** (a high axis never offsets a low one).
  **[universal-required]**

The admission assessment describes whether the signal has **earned its place, not predictive likelihood** — it
never implies the signal is more likely to be correct or predicts the market. The mechanism gate, the three axes,
and their anchored rubric are defined in `signal-output-spec.md` §1; point at it, do not restate the anchors
here.

### 8. Limitations

- Q8.1 What can this signal tell us? **[universal-required]**
- Q8.2 What can it explicitly NOT tell us? **[universal-required]**
- Q8.3 State the per-signal boundary: this reading names a monitored market assumption and STOPS; it implies
  no action. **[universal-required]**

Attribute 8 echoes the attribute-6 failure modes as user-facing caveats and carries the HARD BOUNDARY at the
per-signal level.

---

## Reconciliation note (D-05)

This template is authoritative and refines the earlier mini-study spec + six-point evaluation in
`.planning/REGIME-SENSOR-ARCHITECTURE.md`. Every architecture-doc field folds in without loss:

| Architecture-doc field | Folds into |
|---|---|
| assumption tested / research question | attribute 1 (also header: assumption monitored) |
| hypothesis / the mechanism gate | attribute 2 |
| data (+ vintage/revision), frequency/clock, statistical method / metric | attribute 3 (clock also in header) |
| historical-context output; false positives / false negatives | attribute 4 |
| validation process = the six-point evaluation; intl OOS; confound-check | attribute 5 |
| failure modes (declared before testing) | attribute 6 (echoed in attribute 8) |
| the admission assessment (mechanism gate + three axes) | attribute 7 |
| model-card "caveats" pattern | attribute 8 |
| maturity tag | header (DERIVED — mechanism gate + three axes + sign-off + investor-question) |

The deliberate split preserved here: **structural failure modes → attribute 6** (declared before testing);
**empirical false-positives / false-negatives → attribute 4** (the observed record). The two are kept
distinct.

A worked, filled example is not inlined here — retro-fit examples against the two already-built signals are
produced in Plan 01-02.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
