---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: paused
stopped_at: Phase 10 plan 10-02 shipped (informativeness map). All four remaining phases await an owner ruling.
last_updated: "2026-08-10T17:20:04.000Z"
last_activity: 2026-08-10
progress:
  total_phases: 8
  completed_phases: 4
  total_plans: 15
  completed_plans: 12
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-02)

**Core value:** Each independently-validated signal surfaces a market assumption worth monitoring — fewer blind spots for the human's judgment, never a forecast, never an action.
**Current focus:** none in flight — **four phases (3, 4, 6, 9) each await an owner ruling.**

## Current Position

**4 of 8 LIVE phases COMPLETE. 3 phases DROPPED. All 4 remaining phases are blocked on an owner
RULING, not on engineering work.**

Phase: none executing. Complete: **1** (framework, 2026-08-03) · **1.5** (volatility, 2026-08-06, `production`) ·
**2** (stock-bond, 2026-08-07, `research`) · **10** (presentation, 2026-08-10, shipped + reframed).
Dropped at the charter stage: **5** (MI-007, 2026-08-06) · **7** (MI-008, 2026-08-06) · **8** (MI-013, 2026-08-05).
Plan: 12 of 15 live plans complete
Status: paused — awaiting four owner rulings
Last activity: 2026-08-10 — Phase 10 plan 10-02 shipped (`scripts/informativeness_map.py`); 215 tests passing

Progress: [█████░░░░░] 50%  *(4 of 8 live phases)*

**Frontmatter reading.** `progress.total_phases: 8` counts **live** phases; `.planning/ROADMAP.md` retains
**10** numbered phase sections because three were dropped and their sections + ledger rows are kept
deliberately (numbering is cited across the ledger, charters and NOTES.md and must not be renumbered).
The schema has no key for dropped phases, so the count lives here in prose. `status: paused` is the closest
honest value the schema's enum admits — GSD normalizes to
`paused | executing | planning | discussing | verifying | completed`, and there is **no `blocked` value**;
nothing is in flight and nothing advances without a human decision.

**The four open rulings — each needs a decision, not code:**

| Phase | The ruling | State of the work |
|-------|-----------|-------------------|
| 3 Valuation | **The R9 disposition.** V6 (bias-aware inference) FAILED — bootstrap p = 0.07–0.26 at every horizon; both defensible readings are written into the charter. Do NOT rerun the bootstrap with another seed or block length | One look **SPENT** 2026-08-07 → `results/valuation_validation.txt`. **Zero build work remains.** Level-0 emission deliberately withheld while R9 is open (MI-009) |
| 4 Concentration | **5 open charter items + the V3 (resolution) ruling** — the draft expects R3 to fire ("seven names *inside* one bucket") | Built + construction-gated (`concentration_gate.csv` C1–C5 True; 1200 months). Charter v0.2 UNSIGNED, **no bar run**. Renders as a CANDIDATE in the Phase-10 artifact (MI-011) |
| 6 Credit (EBP) | **Adam writes the four V2 statistics** (`revisions`/`bar_a`/`bar_b`/`bar_c`) in `scripts/validate_credit.py` — Learning Mode. Registered consequence of R2 firing is **DROP**, not demotion | Charter v1.0 SIGNED 2026-08-09; scaffolding self-tests 6/6; **one look UNSPENT**; 20 EBP vintages 2022-08-18..2026-03-23 harvested (MI-010) |
| 9 Tail | **Accept or reject the price-of-protection reframe.** DROP is registered as defensible — **the phase dies if the reframe is not accepted** | Built (`scripts/tail_skew.py`). Charter v0.2 UNSIGNED, none of V1–V8 run. Own registered prior: **R4 likely fires** (MI-012) |

## Performance Metrics

**Velocity:**

- Total plans completed: 12 (of 15 live plans)
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 12 | 3 tasks | 4 files |
| Phase 01 P02 | 14 | 3 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: GSD scoped strictly to signal modules — Phase 1 framework + one phase per signal + presentation
- [Init]: Build order after framework = stock-bond intl OOS → valuation → concentration → absorption → EBP → funding → crowding → tail
- [Init]: Each signal is its own phase — never merged (independent research module; coarse granularity applies as plan-count compression, not phase-merging)
- [Phase ?]: 01-01: framework adopts analog enforcement machinery (model cards + datasheets + GRADE + TRIPOD + registered reports), not a bespoke framework
- [Phase ?]: 01-01: maturity tag is DERIVED (from validation status + confidence vector), not an authored spec attribute
- [Phase ?]: 01-01: charter-before-implementation — no Phase 2-10 signal is built before its six-question charter exists (D-15)
- [Phase ?]: 01-02: confidence is four research-maturity dimensions (measurement quality/mechanism support/evidence robustness/implementation maturity), never predictive likelihood (D-06)
- [Phase ?]: 01-02: maturity tag DERIVED + descriptive (not a quality ranking, D-13); composite-scalar output forbidden, joint rarity preserved as distinct Level-2 lens
- [Phase ?]: 01-02: nothing frozen to v1.0 — A1/A2/A3 + D-06 dimension swap + retro-fit tension consolidated in SIGNOFF-CHECKLIST.md for Adam's dated sign-off
- [2026-08-10, reconciliation]: **the [Init] build order above is SUPERSEDED.** Absorption, funding and crowding were dropped at the charter stage (MI-007 / MI-008 / MI-013) and presentation shipped ahead of 3/4/6/9. Live order: `1 → 1.5 → 2 → 10 (shipped) → {3, 4, 6, 9}`, the last four unordered and mutually independent. Phase numbers are NOT renumbered — they are cited across the ledger, charters, archive records and NOTES.md.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- ~~Phase 2 (SIG-01) needs JGB/Bund series for Japan/Europe OOS confirmation before any SUPPORT claim.~~ **RESOLVED 2026-08-07** — `build_intl_bonds.py` → `intl_bonds_monthly.csv`; the OOS ran and is monotone in all three regions; Phase 2 closed at `research`.
- ~~Phase 9 (SIG-08 tail) is data-gated (options / high-frequency) — resolve data availability first.~~ **Data resolved** (Cboe SKEW, sha-stamped vintage; metric built). The live blocker is now the **price-of-protection reframe ruling**, and descope is still a defensible outcome.
- **All four remaining phases (3, 4, 6, 9) are blocked on an owner ruling, not on engineering work.** See the table in §Current Position. None blocks another.
- **Do NOT spend any look or run any `validate_*.py` without the ruling that authorizes it.** Valuation's look is spent and must not be rerun with a different seed or block length; credit's is unspent and its script refuses to run without `--i-am-spending-the-one-look`.
- Phase 10 delivery is built but **no schedule is enabled** — `.github/workflows/assumption-ledger.yml` has `schedule:` commented out with a dated reason and no credentials exist. Enabling it is Adam's call.
- **Level 2 (joint rarity + historical analogues) is NOT built** — an explicit seam at `assumption_ledger.level2_context()`. No distance is computed anywhere in this repo.
- **MI-004 is the only open ledger row with real upside and nothing on the roadmap resolves it** — the jump-model regime as a priced cross-sectional factor, `TESTING (ambiguous)`, two constructions disagree, the Step-4 preregistered confirmatory test was never run.
- HARD BOUNDARY standing guard: no phase may drift toward allocation/decision content or a composite/single-word summary.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-08-10
Stopped at: Phase 10 plan 10-02 shipped — `scripts/informativeness_map.py` → `results/informativeness_map.{json,html}`; 215 tests passing. Nothing is mid-flight.
Resume file: None — the next move is a ruling, not a plan. See §Current Position for the four. Full narrative state: `NOTES.md`.
</content>

---
<!-- LINKS:AUTO -->

## Related

**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
