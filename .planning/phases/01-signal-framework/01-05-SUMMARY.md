# Phase 1 Plan 05: Framework v1.0 Freeze Propagation Summary

Mechanical propagation of Adam's 2026-08-03 framework sign-off across the `.planning/framework/` docs and examples: version markers bumped v0.1-draft → v1.0, `[ASSUMED]`/pending/veto language resolved to the decided state, and the stale upstream "three confidence dimensions" text patched to the unified admission model — RF left OPEN by design.

## What Changed

**Version bumps (v0.1-draft → v1.0):**
- `signal-spec-template.md` — header version + example version + "Nothing freezes to v1.0 until sign-off" → frozen note
- `signal-output-spec.md` — header version + frozen note (RF flagged OPEN)
- `research-charter-template.md` — header version + example version
- `validation-standards.md` — header version
- `examples/volatility-signal-declaration.md` — header + Level-0 `spec_version`
- `examples/stock-bond-corr-signal-declaration.md` — header + Level-0 `spec_version`

**Sign-off dispositions resolved (`signal-output-spec.md`):**
- A1 three-axis anchors + starting points: `[ASSUMED — requires sign-off]` → `[ADOPTED v1.0 — Adam 2026-08-03; amendable via semver]`
- A2 maturity derivation rule: `[ASSUMED]` → `[ADOPTED v1.0]`; RF sub-point noted OPEN
- A3 composite-scalar prohibition: "flagged for sign-off" → "CONFIRMED v1.0 (Adam, 2026-08-03)"
- OBS new output-field definitions: `[ASSUMED — pending sign-off]` → "CONFIRMED v1.0 (Adam 2026-08-03)"
- D-06 current-relevance → implementation-maturity swap: "flagged for veto" → "RESOLVED — superseded by ADM (D-17)"

**RF left OPEN (per exception):**
- `examples/volatility-signal-declaration.md` — production maturity tag flagged **carried PROVISIONALLY pending RF**; Q5.2 caveat and versioned-amendment candidate reworded to "OPEN — deferred at the v1.0 freeze under the cooling-off rule"

**Stale confidence-dimension text patched to admission model:**
- `ROADMAP.md` SC#3 — "three confidence dimensions (measurement · interpretation · regime-relevance)" → "the signal-admission assessment (binary mechanism prerequisite gate + three non-compensatory axes: measurement validity · investment usefulness · evidence maturity) with a DERIVED maturity tag"
- `signal-output-spec.md` §3 supersession — "Upstream docs are STALE" note → records the stale text HAS NOW been patched at the v1.0 freeze (2026-08-03)

## Deviations from Plan

None material. Two judgment calls within scope:

1. **`validation-standards.md` version bump** was not in the objective's explicit item-1 list but was required by the success criterion "no v0.1-draft remains as the live version in the framework docs." Bumped to v1.0.
2. **`REGIME-SENSOR-ARCHITECTURE.md` needed no edit.** Its stale-text references were already patched in an earlier plan — Level 0 already reads "the admission assessment (mechanism gate + the three axes)", the only "three confidence dimensions" reference is inside a correctly-framed supersession note ("REPLACES the earlier ... which is superseded"), and "Last updated" is already 2026-08-03. Left as-is per the "admission-model sections added earlier stay as-is" instruction.

## HARD BOUNDARY Check

Reviewed-grep clean on all touched files. Forbidden tokens (portfolio / allocation / exposure / sleeve / tilt / cash / weight / risk-on/risk-off summary) appear only in pre-existing prohibition/glossary/boundary statements (validation-standards §prohibition, signal-output-spec boundary notes, ENF/OBS enforcement) or the volatility signal's legitimate domain name ("risk-off state" = its monitored market state). My additions introduced none.

## Not Touched (per plan)

`scripts/regime_signal.py`, `results/regime_card.json`, `tests/` — the `gauge.position → gauge.dwell_rank` rename is a separately-tracked deferred cleanup, not part of this freeze propagation.

## Commits

- `49d6049` — docs(01-05): propagate v1.0 framework freeze (Adam 2026-08-03) — 7 files, +38/-34

## Self-Check: PASSED

- SUMMARY file created: `.planning/phases/01-signal-framework/01-05-SUMMARY.md`
- Commit `49d6049` exists in git log
- No live `v0.1-draft` remains in framework docs/examples (only in historical PLAN/VERIFICATION artifacts, correctly untouched)
- No file deletions, no untracked files

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
- [[_planning/regime-detection/phases/01-signal-framework/01-CONTEXT|01-CONTEXT]]
- [[_planning/regime-detection/phases/01-signal-framework/01-RESEARCH|01-RESEARCH]]
- [[_planning/regime-detection/phases/01-signal-framework/01-VERIFICATION|01-VERIFICATION]]

<!-- LINKS:END -->
