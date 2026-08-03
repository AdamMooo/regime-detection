# Phase 1 Plan 06: Framework v1.1 Amendment — Stage-0 Relevance Gate Summary

The framework's first semver amendment (v1.0 → v1.1): a **pre-charter Relevance Gate** (Stage 0, default = NO, 5
questions incl. the leave-one-out / marginal-information test) added ahead of the charter and all research time,
plus the **quality-over-quantity curated-observatory philosophy** (scarce resource = research time / validation /
maintenance / investor attention, NOT code). Purely additive — no frozen v1.0 decision was altered.

## What Changed

**Framework spec docs (all bumped v1.0 → v1.1):**
- `validation-standards.md` — new **Stage 0 — Relevance Gate** section (5 questions · default = NO · leave-one-out ·
  no charter / no research time until it passes · quality-over-quantity · gate-vs-axis relationship) + a **signal
  lifecycle** (relevance gate → charter → research/build → validation → admission review → cooling-off + sign-off →
  production) + amendment-log line.
- `research-charter-template.md` — charter may be opened **only after the Stage-0 gate passes**; five gate answers
  (G1–G5) carried as the charter's opening block.
- `signal-output-spec.md` — investment-usefulness axis (§1.2) gains the **leave-one-out / marginal-information**
  consideration and the note that it is the rigorous post-research form of the pre-research Relevance Gate.
- `signal-spec-template.md` — note that the relevance gate precedes the template/charter.

**Governing design + planning docs:**
- `REGIME-SENSOR-ARCHITECTURE.md` — new "Observatory philosophy: quality over quantity (D-19)" subsection (curated
  research system; default-no; scarce resource = research time/attention not code; leave-one-out litmus; TA faces
  an extremely high bar; popularity is not evidence).
- `01-CONTEXT.md` — **D-19** added to `<decisions>` (pre-charter Relevance Gate + quality-over-quantity, v1.1).
- `SIGNOFF-CHECKLIST.md` — new **## Amendment log** with the v1.1 (2026-08-03) entry; the v1.0 sign-off record,
  open RF item, and tracked `gauge.position` rename left untouched.
- `ROADMAP.md` — per-phase **gate-zero precondition**: every signal phase must pass the Relevance Gate before
  opening its charter.

## Deviations from Plan

None. Executed exactly as specified — additive v1.1 amendment across the eight listed files.

## HARD BOUNDARY Check

Reviewed-grep clean on all eight touched files. Forbidden tokens (portfolio · allocation · exposure · weight ·
sleeve · tilt · cash · buy · sell · risk-on/risk-off · composite-score) appear only in pre-existing
prohibition/glossary/boundary statements (the forbidden-vocabulary list itself, the one-way-boundary and
schema-allowlist notes), legitimate domain terms ("cap-weight structure" = index construction; "risk-off" = the
volatility signal's monitored market state; "vintage/revision exposure"), or the "zero allocation/decision"
prohibitions. My v1.1 additions introduced none as a field, value, or instruction.

## Not Touched (per objective)

`scripts/`, `results/`, `tests/` — no code change in this amendment. The frozen v1.0 decisions, the open RF item,
and the `gauge.position` deferred rename are unchanged.

## Commits

- `8c59d67` — feat(01-06): add Stage-0 Relevance Gate + lifecycle to framework (v1.1) — 4 files
- `36c50b1` — docs(01-06): add observatory quality-over-quantity philosophy (D-19) — 1 file
- `9993018` — docs(01-06): record D-19 in CONTEXT, SIGNOFF amendment log, ROADMAP DoD — 3 files

## Self-Check: PASSED

- SUMMARY file created: `.planning/phases/01-signal-framework/01-06-SUMMARY.md`
- All three commits exist in git log (`8c59d67`, `36c50b1`, `9993018`)
- All four framework spec docs read **v1.1**; D-19 present in CONTEXT, SIGNOFF, ROADMAP, architecture
- No file deletions; no untracked files; reviewed-grep clean

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/01-signal-framework/01-01-PLAN|01-01-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-01-SUMMARY|01-01-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-02-PLAN|01-02-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-02-SUMMARY|01-02-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-03-SUMMARY|01-03-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-04-SUMMARY|01-04-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-05-SUMMARY|01-05-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-CONTEXT|01-CONTEXT]]
- [[_planning/regime-detection/phases/01-signal-framework/01-RESEARCH|01-RESEARCH]]
- [[_planning/regime-detection/phases/01-signal-framework/01-VERIFICATION|01-VERIFICATION]]

<!-- LINKS:END -->
