---
phase: 01-signal-framework
plan: 01
subsystem: framework
tags: [signal-spec, validation-standards, research-charter, preregistration, hard-boundary, model-cards, datasheets, grade, tripod]

# Dependency graph
requires: []
provides:
  - "signal-spec-template.md — the merged 8-attribute question-form template (single source of truth every signal declares against)"
  - "research-charter-template.md — six-question pre-registration subset written before implementation (D-15)"
  - "validation-standards.md — the cross-signal validation law: causal/PIT, mechanism gate, confound-check, Japan/Europe OOS, temporal freeze, completeness checklist, template versioning, HARD BOUNDARY audit, D-10/D-12/D-15 rules"
  - "REGIME-SENSOR-ARCHITECTURE.md cross-linked to .planning/framework/ as the governing specification (D-16)"
affects: [01-02, "02-stock-bond", "03-valuation", "04-concentration", "05-diversification", "06-credit", "07-funding", "08-crowding", "09-tail", "10-presentation"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Question-form fields with forced 'Not applicable, because …' (datasheets discipline)"
    - "Universal-required vs conditional attribute marking"
    - "TRIPOD-style completeness checklist gating dated sign-off"
    - "Registered-report temporal freeze (one look + prereg + cooling-off + dated sign-off, deviations disclosed)"
    - "Semver template versioning, no per-signal forking"
    - "Reviewed-grep HARD BOUNDARY audit (never a bare zero-count gate)"

key-files:
  created:
    - .planning/framework/signal-spec-template.md
    - .planning/framework/research-charter-template.md
    - .planning/framework/validation-standards.md
  modified:
    - .planning/REGIME-SENSOR-ARCHITECTURE.md

key-decisions:
  - "Adopted analog enforcement machinery (model cards + datasheets + GRADE + TRIPOD + registered reports) rather than a bespoke framework"
  - "Maturity tag is a DERIVED header field, not a spec attribute (forward-references signal-output-spec.md)"
  - "Structural failure modes (attribute 6, declared before testing) kept distinct from empirical FP/FN (attribute 4, observed record)"
  - "Confidence attribute 7 forward-references the four dimensions defined in 01-02 (measurement quality · mechanism support · evidence robustness · implementation maturity); the dropped current-relevance / regime-relevance wording is not reintroduced"

patterns-established:
  - "Every signal declares against one versioned template; gaps become changelogged amendments, never per-signal forks"
  - "Charter-before-implementation: no Phase 2–10 signal is built before its six-question charter exists"

requirements-completed: [FRWK-01]

# Metrics
duration: 12min
completed: 2026-08-03
---

# Phase 1 Plan 01: Signal Framework (template + charter + validation law) Summary

**The merged 8-attribute question-form signal-spec template, the six-question pre-registration research charter, and the cross-signal validation-standards law — with the architecture doc cross-linked to `.planning/framework/` as the governing specification.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-08-03
- **Tasks:** 3
- **Files modified:** 4 (3 created, 1 edited)

## Accomplishments

- `signal-spec-template.md` — semver-versioned single source of truth: header block (six universal-required fields incl. DERIVED maturity tag) + the 8 attributes in D-04 order, each question-form and marked universal-required vs conditional with a forced "Not applicable, because …" rule. Attribute 2/5 point at validation-standards; attribute 7 + maturity header point at signal-output-spec. D-05 reconciliation table folds every architecture-doc field in without loss (failure modes → attr 6, empirical FP/FN → attr 4).
- `research-charter-template.md` — the D-15 pre-registration subset: six questions in order (question · assumption · mechanism · validating evidence · falsification · what it does NOT claim), mapped to spec attributes 1/2/5/6/8, frozen before implementation.
- `validation-standards.md` — governing invariants (D-01/02/03/07) up front; enforceable rules for causal/PIT, mechanism gate, confound-check (rate-cycle + dispersion-lead precedents), Japan/Europe OOS, temporal freeze; TRIPOD completeness checklist (one item per header field + template attribute); semver versioning discipline; dedicated HARD BOUNDARY content-audit subsection with the forbidden-vocab list and reviewed-grep procedure; D-10 named integrity rule, D-12 optimization target, D-15 charter-before-implementation + ROADMAP-DoD follow-up note.
- `REGIME-SENSOR-ARCHITECTURE.md` — additive cross-link note near the top naming the three framework files and the three-doc role split (framework = research+validation rules · phases = execution roadmap · architecture = system design); existing content untouched.

## Task Commits

1. **Task 1: signal-spec-template + research-charter-template** - `1b2f4ad` (feat)
2. **Task 2: validation-standards** - `6b907cc` (feat)
3. **Task 3: architecture doc cross-link** - `c60ffa6` (docs)

## Files Created/Modified

- `.planning/framework/signal-spec-template.md` - the merged 8-attribute question-form template + header block
- `.planning/framework/research-charter-template.md` - six-question pre-registration charter (D-15)
- `.planning/framework/validation-standards.md` - cross-signal validation law + checklist + versioning + HARD BOUNDARY audit + D-10/D-12/D-15
- `.planning/REGIME-SENSOR-ARCHITECTURE.md` - added governing-specification cross-link (D-16)

## Decisions Made

- Followed the plan and 01-RESEARCH recommendation to borrow analog enforcement machinery rather than invent a bespoke framework.
- Attribute 7 forward-references the four confidence dimensions defined in 01-02 (per the D-06 refinement flagged in the plan's hard_boundary_audit); the dropped "current-relevance" and stale "regime-relevance / portfolio-relevance guard" wording is explicitly not reintroduced.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rephrased two "exposure" usages to pass the reviewed-grep HARD BOUNDARY audit**
- **Found during:** Tasks 1 and 2 (audit step)
- **Issue:** "vintage / revision exposure" (spec Q3.2) and "no vintage exposure" (standards §a) matched the forbidden-token grep as actual field/instruction text, not prohibition text — violating the acceptance criterion that every grep hit must sit inside a prohibition statement. The token "exposure" here is a data-vintage term, unrelated to market exposure, but the audit is token-based.
- **Fix:** Reworded to "how sensitive are they to vintage / revision" and "no vintage sensitivity".
- **Files modified:** signal-spec-template.md, validation-standards.md
- **Verification:** Re-ran the grep; spec/charter now zero hits; validation-standards' remaining four hits are all inside the forbidden-vocab list or "must not be reintroduced" prohibition statements.
- **Committed in:** `1b2f4ad`, `6b907cc` (within the respective task commits)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Wording-only; preserves the exact meaning and keeps the delivered docs boundary-clean under the token-based audit future signals will run. No scope change.

## Issues Encountered

None.

## HARD BOUNDARY Audit (reviewed grep)

- `signal-spec-template.md`: zero hits.
- `research-charter-template.md`: zero hits.
- `validation-standards.md`: 4 hits, all prohibition/boundary statements (the forbidden-vocab list at §HARD BOUNDARY content audit and the "regime-relevance / portfolio-relevance guard must not be reintroduced" line). No hit is a field, value, or instruction.
- `REGIME-SENSOR-ARCHITECTURE.md`: the added block introduces no new allocation vocabulary; all pre-existing hits are the doc's own boundary statements.

## Next Phase Readiness

- Framework backbone ready for Plan 01-02 (four-dimension confidence model with anchored rubric, maturity derivation rule, Level 0/1/2 assumption-ledger output shape, and the retro-fit against the two built signals). `signal-output-spec.md` is referenced by the template but authored in 01-02.
- Open item carried to 01-02: the `[ASSUMED]` confidence anchors and maturity derivation rule still need Adam's dated sign-off before anything freezes to v1.0.

---
*Phase: 01-signal-framework*
*Completed: 2026-08-03*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/01-signal-framework/01-01-PLAN|01-01-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-02-PLAN|01-02-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-CONTEXT|01-CONTEXT]]
- [[_planning/regime-detection/phases/01-signal-framework/01-RESEARCH|01-RESEARCH]]

<!-- LINKS:END -->

## Self-Check: PASSED

All three framework files + SUMMARY exist on disk; all three task commits (1b2f4ad, 6b907cc, c60ffa6) present in git log.
