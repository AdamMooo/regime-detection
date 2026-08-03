---
phase: 01-signal-framework
plan: 02
subsystem: framework
tags: [confidence-model, maturity-model, output-spec, assumption-ledger, retro-fit, hard-boundary, grade, signoff]

# Dependency graph
requires:
  - "01-01 — signal-spec-template.md (attr 7 + DERIVED maturity header point here) + validation-standards.md"
provides:
  - "signal-output-spec.md — four research-maturity confidence dimensions (anchored H/M/L + starting points), descriptive maturity model, Level 0/1/2 output shape, composite-scalar prohibition + joint-rarity distinction, D-11 co-equal presentation"
  - "examples/volatility-signal-declaration.md — retro-fit of the frozen template against the shipped jump-model signal"
  - "examples/stock-bond-corr-signal-declaration.md — retro-fit against the built stock-bond correlation signal (heterogeneous shape)"
  - "SIGNOFF-CHECKLIST.md — consolidated [ASSUMED]/veto items awaiting Adam's dated sign-off before v1.0"
affects: ["02-stock-bond", "03-valuation", "04-concentration", "05-diversification", "06-credit", "07-funding", "08-crowding", "09-tail", "10-presentation"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "GRADE-style anchored H/M/L confidence dimensions with declared starting points"
    - "DERIVED descriptive maturity tag (not authored, not a quality ranking)"
    - "Level 0/1/2 output shape (measurement / historical context / regime relevance), STOP at Level 2"
    - "Composite-scalar prohibition kept distinct from the permitted joint-rarity (Mahalanobis) lens"
    - "Retro-fit of the frozen template against real heterogeneous signals before freeze"
    - "Consolidated [ASSUMED]/veto sign-off checklist gating v1.0 freeze"

key-files:
  created:
    - .planning/framework/signal-output-spec.md
    - .planning/framework/examples/volatility-signal-declaration.md
    - .planning/framework/examples/stock-bond-corr-signal-declaration.md
    - .planning/framework/SIGNOFF-CHECKLIST.md
  modified: []

key-decisions:
  - "Confidence is four research-maturity dimensions (measurement quality / mechanism support / evidence robustness / implementation maturity), never predictive likelihood (D-06)"
  - "Maturity tag is DERIVED from attribute 5 + the implementation-maturity dimension, descriptive not a ranking (D-13)"
  - "Both the earlier 3-dim and earlier 4-dim confidence models recorded as superseded; current-relevance dropped for implementation maturity"
  - "Any composite-scalar output field forbidden (A3); joint rarity (Mahalanobis) preserved as a distinct Level-2 lens"
  - "Nothing frozen to v1.0 in-plan — all [ASSUMED]/veto items consolidated for Adam's dated sign-off"

patterns-established:
  - "Every signal renders into the same Level 0 record + assumption-ledger shape, never a score"
  - "Template proven against real signals before freeze; misfits become versioned amendments, not inline edits"

requirements-completed: [FRWK-01]

# Metrics
duration: 14min
completed: 2026-08-03
---

# Phase 1 Plan 02: Confidence Model + Maturity Model + Output Shape + Retro-Fit Summary

**The four-dimension research-maturity confidence model, the descriptive derived maturity model, the Level 0/1/2 assumption-ledger output shape (STOP at Level 2, no composite scalar), retro-fitted against both already-built signals, with every [ASSUMED]/veto item consolidated for Adam's dated sign-off.**

## Performance

- **Duration:** ~14 min
- **Completed:** 2026-08-03
- **Tasks:** 3
- **Files modified:** 4 (all created)

## Accomplishments

- `signal-output-spec.md` §1 — Confidence model: the four D-06 dimensions (measurement quality · mechanism support · evidence robustness · implementation maturity), each GRADE-anchored H/M/L with a declared starting point (returns-only → measurement quality H; macro/options → M/L; evidence robustness starts L until Japan/Europe OOS; implementation maturity starts L / spec-only). Prominent not-predictive disclaimer. Anchors + starting points marked `[ASSUMED — requires sign-off]` (A1).
- `signal-output-spec.md` §2 — Maturity model: production/research/rejected DERIVED from attribute 5 + the implementation-maturity dimension (whose discrete expression IS the tag); explicitly descriptive, NOT a quality ranking (D-13). Derivation rule marked `[ASSUMED]` (A2).
- `signal-output-spec.md` §3 — Supersession: both the earlier 3-dim (measurement · interpretation · regime-relevance) and earlier 4-dim (data-quality · historical-robustness · mechanism · current-relevance) models recorded superseded with full mappings; current-relevance DROPPED for implementation maturity; ROADMAP SC#3 + REGIME-SENSOR-ARCHITECTURE.md named stale (upstream edits left as optional follow-up, A5).
- `signal-output-spec.md` §4 — Output shape: Level 0 = measurement (exact D-08 fields, zero allocation/decision fields) · Level 1 = historical context (assumption ledger, status as observation, six-reading canonical example) · Level 2 = regime relevance (joint rarity + analogues); STOP at Level 2. Composite-scalar output field forbidden (A3) while joint rarity (Mahalanobis) explicitly permitted as a distinct Level-2 lens. D-11 no-dominance / co-equal presentation rule.
- `examples/volatility-signal-declaration.md` — retro-fit of the shipped fast jump-model signal (maturity = production), full header + 8 attributes + four-dimension confidence vector + Level 0 record.
- `examples/stock-bond-corr-signal-declaration.md` — retro-fit of the slow returns-based correlation-sign signal (maturity = research, Japan/Europe OOS pending), including two genuine forced `Not applicable, because …` answers — proving heterogeneous fit.
- `SIGNOFF-CHECKLIST.md` — consolidates A1, A2, A3, the D-06 current-relevance→implementation-maturity swap (flagged for VETO), and the retro-fit-surfaced production-vs-Japan/Europe-OOS tension; records both retro-fits filled cleanly; unfilled dated sign-off lines (nothing frozen).

## Task Commits

1. **Task 1: confidence model + maturity model + supersession** - `a79bbb0` (feat)
2. **Task 2: Level 0/1/2 output shape + composite-scalar prohibition + D-11** - `80bee7c` (feat)
3. **Task 3: retro-fit both signals + sign-off checklist** - `ccd19c7` (feat)

## Files Created/Modified

- `.planning/framework/signal-output-spec.md` - confidence model + maturity model + supersession + Level 0/1/2 output shape + prohibitions + D-11
- `.planning/framework/examples/volatility-signal-declaration.md` - retro-fit (production, fast)
- `.planning/framework/examples/stock-bond-corr-signal-declaration.md` - retro-fit (research, slow)
- `.planning/framework/SIGNOFF-CHECKLIST.md` - consolidated sign-off/veto items, unsigned

## Decisions Made

- Followed D-06/D-13/D-14 exactly; kept the composite-scalar prohibition distinct from the permitted joint-rarity lens per research A3 + the Phase-10 requirement.
- Recorded supersession in the delivered spec rather than editing ROADMAP/architecture upstream (research A5) — surfaced as an optional follow-up.
- Retro-fits are declared as fit-checks, not new SUPPORT claims (per the plan's retro-fit note); no new validation asserted.

## Deviations from Plan

### Auto-added (within scope)

**1. [Rule 2 - Completeness] Added an RF item to the sign-off checklist surfaced by the retro-fit**
- **Found during:** Task 3 (volatility retro-fit)
- **Issue:** The maturity derivation rule (§2) requires evidence robustness = H via literal Japan/Europe OOS, but the shipped volatility signal's production tag rests on frozen-US OOS + the universal vol-persistence stylized fact rather than a literal Japan/Europe panel run — a genuine tension the retro-fit exists to expose.
- **Fix:** Recorded as a versioned-amendment candidate in the volatility declaration and as an `RF` line in `SIGNOFF-CHECKLIST.md` (decide with A2). No template edit; no maturity rule change asserted.
- **Files modified:** examples/volatility-signal-declaration.md, SIGNOFF-CHECKLIST.md
- **Committed in:** `ccd19c7`

---

**Total deviations:** 1 auto-added (surfaced, documented, not silently resolved).
**Impact on plan:** None to scope — the retro-fit did its job (exposed a real fit/rule tension) and the tension is routed to sign-off rather than decided here.

## Issues Encountered

None.

## HARD BOUNDARY Audit (reviewed grep)

- `signal-output-spec.md` Task 1 grep (`portfolio|allocat|exposure|sleeve|tilt|current-relevance`): 6 hits, all inside the §3 supersession record or the §1.4 boundary note naming dropped/old wording. Zero live definitions.
- `signal-output-spec.md` Task 2 grep (`/100|composite score|risk score|weight|sleeve|tilt|buy |sell `): 4 hits, all inside prohibition statements (Level 0 zero-fields line, the "market risk = 73/100" forbidden example ×2, the D-11 "NO weighting" rule).
- Task 3 grep (`portfolio|allocat|exposure|sleeve|tilt|/100`) across all three files: 1 hit — "portfolio-relevance guard" in the SIGNOFF-CHECKLIST D-06 supersession line naming dropped old wording. Both example declarations: zero hits.
- Every hit is a prohibition / supersession / boundary statement; no hit is a field, value, or instruction. Audit passes.

## Next Phase Readiness

- Framework is complete and internally consistent: template (01-01) + validation law (01-01) + confidence/maturity/output shape (01-02), proven against both built signals.
- Open item carried forward: `SIGNOFF-CHECKLIST.md` — A1 (anchors), A2 (maturity rule), A3 (forbid composite scalar), the D-06 dimension swap (VETO), and the RF production-vs-OOS tension all await Adam's dated sign-off before any v1.0 freeze. Nothing is frozen.
- Phase 2 (stock-bond intl OOS, SIG-01) remains gated on JGB/Bund series — consistent with the stock-bond retro-fit's evidence-robustness = M / maturity = research read.

---
*Phase: 01-signal-framework*
*Completed: 2026-08-03*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/01-signal-framework/01-01-PLAN|01-01-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-01-SUMMARY|01-01-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-02-PLAN|01-02-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-CONTEXT|01-CONTEXT]]
- [[_planning/regime-detection/phases/01-signal-framework/01-RESEARCH|01-RESEARCH]]

<!-- LINKS:END -->

## Self-Check: PASSED

All four framework files + SUMMARY exist on disk; all three task commits (a79bbb0, 80bee7c, ccd19c7) present in git log.
