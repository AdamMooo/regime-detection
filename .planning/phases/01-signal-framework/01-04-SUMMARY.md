# Phase 1 Plan 04: Code-Level Boundary Enforcement — Summary

Realized the HARD BOUNDARY as executable architecture (D-18): a closed Level-0 output schema (allowlist +
forbidden-vocabulary denylist + `validate()`), a runnable boundary-audit test (schema conformance +
repo-structure guard), running GREEN on the current shipped outputs. The enforcement caught one real
pre-existing boundary leak (`gauge.position`), which was deferred via a single tracked exception rather than a
premature downstream-contract change.

## What was built

- `scripts/signal_output_schema.py` (stdlib only) — the closed §4.1 field set as two allowlists
  (`LEVEL0_ALLOWED` top-level, `ASSESSMENT_ALLOWED` nested), the forbidden-vocabulary `FORBIDDEN` denylist,
  `is_forbidden_key()` (whole-key + snake-case-segment matching; only single-token denylist entries seed the
  segment set, so `entry_point` never leaks a benign "point" match and `measurement_validity` is not flagged),
  `collect_keys()` (recursive key collector, reused by the test), and `validate()` — raises `ValueError` on an
  unknown top-level/assessment key, any forbidden key anywhere, or an out-of-range enum
  (`mechanism∈{pass,rejected}`, the three axes `∈{H,M,L}`, `maturity∈{production,research,rejected}`,
  `clock∈{daily,weekly,monthly,structural}`), while tolerating unfilled `<placeholder>` values.
- `tests/test_boundary_audit.py` (pytest, project `sys.path` convention) — four checks:
  - **A** — every `results/*.json` recursively carries no forbidden field name.
  - **B** — the fenced Level-0 block in each `framework/examples/*-signal-declaration.md` parses (leniently, no
    `json.loads`) to keys that are a subset of the allowlist and disjoint from the denylist.
  - **C** — `validate()` rejects a forbidden key, an unknown key, and a bad enum; accepts a minimal valid record
    and a `<placeholder>` enum.
  - **D** — no `scripts/*.py` import line references a downstream allocation/decision system
    (`portfolio|allocation|alloc|broker|execution|order`); `signal_output_schema.py` excluded (it holds the
    tokens as denylist data).

## Verification

`.venv/Scripts/python.exe -m pytest tests/ -q` → **34 passed in 1.98s** (23 pre-existing + 11 new; no regression).

## Deviations from Plan

### Real boundary leak caught, then deferred by decision (not a code auto-fix)

**[Finding] `results/regime_card.json` → `gauge.position` is a field named with the denylist token `position`.**
- **Found during:** Test A (the enforcement working as designed).
- **What it is:** a dwell-rank descriptor — "Nth percentile of completed episodes" — produced by
  `scripts/regime_signal.py:95`. Semantically a rarity/rank, NOT a trading position; but by the project's own
  audit standard (validation-standards §(h): a hit that is an actual field fails) it is a genuine
  vocabulary leak.
- **Why not auto-fixed:** `regime_card.json` is a downstream contract (consumed by a separate repo's daily
  Market Brief + weekly positioning email, per `regime_signal.py:3`). Renaming it (`gauge.position` →
  `gauge.dwell_rank`) is a breaking API change requiring coordinated downstream update — a Rule-4 decision, not
  an inline fix.
- **Decision (Adam, Option B):** defer the rename to an end-of-project cleanup; keep `position` a globally
  forbidden token; add ONE narrowly-scoped, documented, tracked exception
  `KNOWN_DEFERRED_EXCEPTIONS = {("regime_card.json", "position")}` in Test A. Every other file and every other
  key stays zero-tolerance; `position` stays forbidden everywhere else. The denylist was NOT weakened, no compat
  shim was added, and `regime_signal.py` / `regime_card.json` were NOT changed.

## Pending cleanup (end-of-project)

The coordinated rename — `scripts/regime_signal.py` (dict key + refs at lines 64, 73, 85, 88, 95),
`results/regime_card.json` (`gauge.position` key), and the downstream repo that reads `gauge.position` — is
deferred. Removing `gauge.dwell_rank`'s predecessor will let `KNOWN_DEFERRED_EXCEPTIONS` shrink to empty and the
exception be deleted. Tracked against SIGNOFF-CHECKLIST.md.

## Self-Check: PASSED

- `scripts/signal_output_schema.py` — FOUND (commit 49d701d)
- `tests/test_boundary_audit.py` — FOUND (commit 03c29de)
- Full suite GREEN: 34 passed.

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
- [[_planning/regime-detection/phases/01-signal-framework/01-CONTEXT|01-CONTEXT]]
- [[_planning/regime-detection/phases/01-signal-framework/01-RESEARCH|01-RESEARCH]]
- [[_planning/regime-detection/phases/01-signal-framework/01-VERIFICATION|01-VERIFICATION]]

<!-- LINKS:END -->
