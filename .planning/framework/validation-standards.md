# Validation Standards

**Version: v1.0**

The cross-signal law every signal is held to. `signal-spec-template.md` attributes 2 and 5 point here. These
are enforceable rules, not aspirations: a signal that does not meet them does not earn a positive claim.

---

## Governing invariants (cross-signal law)

These bind every signal and every document in this framework.

- **D-01 — market-state intelligence, not prediction.** The system explains what is happening, why it may be
  happening, what historical environments look similar, and how unusual the environment is — then STOPS. It is
  not a trading system and not a prediction engine.
- **D-02 — hard output prohibitions.** Never collapse the market into one score; never produce a single
  bullish / bearish answer; never dictate or imply any downstream investment action; never pretend to predict
  future returns.
- **D-03 — multi-dimensional vector, disagreement preserved.** The output is always a multi-dimensional
  market-state vector. The complexity IS the information. Disagreement between signals is valuable and is
  preserved — signals are never forced into agreement or reconciled into consensus.
- **D-07 — independent research modules.** Each signal has its own research process, validation, assumptions,
  and limitations. The framework must not induce a shared latent state or force cross-signal agreement.

---

## (a) Causal-only / point-in-time

Every construction is trailing / point-in-time: no look-ahead, no forward filtering. Revised macro series must
be reconstructed point-in-time (the vintage available at each date), because a live signal that reads
final-revision data has a look-ahead trap. A signal built purely from asset returns has no vintage
sensitivity and states so explicitly.

## (b) The mechanism gate — the binary admission prerequisite

A signal needs a **written structural reason** — a risk-premium or a risk-management channel — that it survives
being known. This is the **binary admission prerequisite** (pass / rejected, NOT graded H/M/L): a signal that
fails is `rejected` and never admitted, before any graded axis is scored. Novelty, backtest fit, or literature
citation alone are **disqualifying as sole basis**. The reason is stated in spec attribute 2 and frozen in the
charter before implementation. A signal whose only claim is "it backtests" does not pass.

## (c) Confound-check requirement

Every historical-context statistic must rule out its confound before it is trusted. Precedents that make this
concrete:

- The **rate-cycle confound** in the stock-bond signal: use the hedge-behavior-by-state metric, not the
  rate-cycle-confounded average-return-by-state.
- The **dispersion-lead** artifact: a US-only lead that did not survive a confound / generalization check
  (Japan +154d, Europe +94d) and was killed.

A statistic that has not ruled out its confound is not evidence.

## (d) Out-of-hypothesis-sample confirmation

The descriptive property must replicate on the **Japan / Europe** panels before any SUPPORT claim, or a
documented failure is recorded. This is the standing rule that killed the dispersion lead: US in-sample is
never sufficient. Nothing reaches production without international out-of-hypothesis-sample confirmation.

## (e) Temporal freeze — one look, prereg, cooling-off, dated sign-off

The protocol is locked before results:

1. The spec — especially attribute-6 failure modes and the attribute-5 validation plan — is fixed **before**
   the one-look validation run (the charter is the Stage-1 freeze).
2. **One look.** The validation run is not repeated until a wanted answer appears.
3. **Overnight cooling-off** between results and any positive claim.
4. **Explicit dated sign-off** — a positive / SUPPORT claim is never inferred from a conversational go-ahead;
   it requires Adam's dated, written sign-off.
5. **Deviations are disclosed, never silently edited.** Any departure from the frozen protocol is logged with a
   dated note (registered-report discipline).

## (f) Completeness checklist (gates the dated sign-off)

Every item below must be answered before sign-off — one checkbox per header field and one per template
attribute. An unanswered item (or a conditional field not answered `Not applicable, because …`) blocks sign-off.

Header fields:

- [ ] Signal name
- [ ] Assumption monitored
- [ ] Native clock / frequency
- [ ] Maturity tag (DERIVED — not hand-set)
- [ ] Spec/template version
- [ ] Dated sign-off

Template attributes:

- [ ] 1. Definition
- [ ] 2. Mechanism
- [ ] 3. Measurement
- [ ] 4. Historical Context
- [ ] 5. Validation
- [ ] 6. Assumptions
- [ ] 7. Admission Assessment
- [ ] 8. Limitations

## (g) Template versioning discipline

The template is **semver-versioned**. A signal **never edits the template to fit itself**. If a genuine gap
appears, the template gets a versioned amendment applied uniformly:

- **MINOR** — additive (a new conditional question), backward-compatible.
- **MAJOR** — a breaking change to existing attributes.

Every amendment carries a changelog entry. Each signal records the template version it filled, and prior
signals note the version they were signed off against. Deviations are disclosed, not retro-fitted silently.
This is the controlled-room-without-forking rule: one template, versioned, never N per-signal forks.

## (h) HARD BOUNDARY content audit

The invariant: every document names market assumptions and **STOPS**. The market-understanding layer never
carries an allocation, decision, or composite-score concept as a field, value, or instruction.

**Forbidden vocabulary** (may appear ONLY inside an explicit prohibition / out-of-scope / boundary statement,
never as a field, value, or instruction): portfolio · allocation · exposure · weight · sleeve · tilt · cash ·
buy · sell · risk-on · risk-off · any composite / single-score phrasing (e.g. "risk = 73/100").

**Audit procedure — a reviewed grep, never a bare zero-count gate.** Before sign-off, grep each delivered
document for the forbidden vocabulary, then **review every hit** and confirm each one sits inside a prohibition
or boundary statement. A hit that is an actual field, value, or instruction fails the audit. Because prohibition
text legitimately contains the forbidden tokens, `== 0` is the wrong test — the test is "every hit is a
prohibition."

The admission assessment describes whether a signal has **earned its place, never predictive likelihood** — it
never implies a signal is more likely correct or predicts the market. A dimension named "current-relevance" or a
"regime-relevance" / "portfolio-relevance guard" must **not** be reintroduced; the mechanism prerequisite gate +
the three admission axes are defined in `signal-output-spec.md` §1.

## (i) No signal designed around a desired conclusion (D-10)

Named integrity rule, distinct from the mechanism gate and the temporal freeze. Mechanism, metric, and
validation plan are specified **before** results are interpreted. A signal that only "works" because it was
tuned toward a wanted answer is **REJECTED**. Result-driven specification (choosing the metric, sample, or
threshold after seeing what produces the wanted answer) is a rejection condition, not a warning.

## (j) Framework optimization target (D-12)

The framework's explicit optimization target is **research integrity, reproducibility, and understanding of
market structure** — NOT predictive accuracy and NOT decision usefulness. Tie-breaker: where a design choice
trades reproducibility / integrity against apparent usefulness, **integrity wins**.

## (k) Charter before implementation (D-15)

Every future signal phase (2–10) writes a **research charter** (per `research-charter-template.md`) answering
the six charter questions **before any implementation**. No signal is implemented before its charter exists.
This keeps each phase independent and prevents drift.

Follow-up note (do not edit ROADMAP here): the ROADMAP per-phase Definition of Done should later add "research
charter written before implementation."

## (l) Signal admission gate (the unified model)

A signal is admitted only through this sequence:

1. **Mechanism prerequisite (binary, §(b)).** Pass or `rejected`. No graded axis is scored until it passes.
2. **Three graded axes (H/M/L, non-compensatory).** **Measurement validity** (accurate, consistent, causal,
   from available data) · **investment usefulness** (answers an important investor question AND provides unique
   information beyond admitted signals — a static per-signal judgment, not a per-reading applicability score) ·
   **evidence maturity** (holds across sub-periods, survives Japan/Europe out-of-hypothesis-sample, studied
   enough to understand). Non-compensatory: a high axis NEVER offsets a low one.
3. **Derived maturity tag.** production / research / rejected is DERIVED from {mechanism = pass · the three axes ·
   dated sign-off · an answerable "why does this deserve to be in front of an investor?"} — never authored. The
   **investor-question is the production bar**: no clear answer → cannot reach production.

Full anchors + derivation rule in `signal-output-spec.md` §1–§2.

## (m) Boundary enforcement is executable

The HARD BOUNDARY is not documentation alone — it lives in code (D-18):

- **Closed output schema (allowlist).** A Level-0 record may contain ONLY the enumerated fields
  (`signal-output-spec.md` §4.1); any allocation / decision / composite-scalar field is schema-invalid.
- **Runnable boundary-audit test.** An automated test asserts no forbidden field or composite scalar is ever
  emitted — the reviewed-grep of §(h) becomes an executable check.
- **Repo-structure rule.** No code in this repo is aware of, imports, or references any allocation / decision
  system; the boundary is enforced by construction, not by convention.

The code is built in the next pass; this doc fixes the rules it enforces.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
