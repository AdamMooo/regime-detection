# Signal Specification Template

**Template version: v0.1-draft**

This is the single source of truth every signal declares against. It is filled **question-form**: each
attribute is a question the signal author must answer explicitly. No field may be left blank — a conditional
field that does not apply is answered `Not applicable, because …`, never omitted.

Version discipline: this template is semver-versioned and is never edited to fit one signal. A genuine gap
becomes a versioned amendment applied uniformly (see `validation-standards.md` §Template versioning). Each
signal records the version it filled. Nothing freezes to v1.0 until Adam's dated sign-off.

---

## Header block

Carries the fields that travel with the output and do not belong inside a single attribute. All six are
universal-required.

- **Signal name** —
- **Assumption monitored** — the ledger key: the abstract market assumption this signal exists to check
  (e.g. "bonds hedge equity drawdowns"). Also surfaced in attribute 1.
- **Native clock / frequency** — daily / weekly / monthly / structural. Also surfaced in attribute 3.
- **Maturity tag** — production / research / rejected. **DERIVED, not authored** — computed from the
  attribute-5 validation status and the attribute-7 confidence vector. See `signal-output-spec.md` for the
  derivation rule. Do not hand-set this field.
- **Spec/template version** — semver of the template this declaration was filled against (e.g. `v0.1-draft`).
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

### 7. Confidence

- Q7.1 What is the reading on each of the four confidence dimensions (measurement quality · mechanism support ·
  evidence robustness · implementation maturity), each anchored, never a single number? **[universal-required]**

Confidence describes **research maturity, not predictive likelihood** — it never implies the signal is more
likely to be correct or predicts the market. The four dimensions and their anchored rubric are defined in
`signal-output-spec.md`; point at it, do not restate the anchors here.

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
| the confidence dimensions | attribute 7 |
| model-card "caveats" pattern | attribute 8 |
| maturity tag | header (DERIVED) |

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
