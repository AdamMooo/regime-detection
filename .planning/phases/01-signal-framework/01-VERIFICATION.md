---
phase: 01-signal-framework
verified: 2026-08-03T17:22:26Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
---

# Phase 1: Signal Framework Verification Report

**Phase Goal:** The shared signal spec exists — the single template and standards every subsequent signal declares against before it runs.
**Verified:** 2026-08-03T17:22:26Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The 8-attribute template exists and is unambiguously fillable (D-04/D-05, SC#1) | VERIFIED | `.planning/framework/signal-spec-template.md` has 8 sections headed exactly "1. Definition" … "8. Limitations" in D-04 order; every question marked `[universal-required]` or `[conditional]`; conditional fields require forced `Not applicable, because …` (line 7, 37, 59, 67); a D-05 reconciliation table (lines 113-132) folds every architecture-doc field in without loss and explicitly keeps structural failure modes (attr 6) distinct from empirical FP/FN (attr 4) |
| 2 | Validation standards documented in one place: causal/PIT, mechanism gate, confound-check, Japan/Europe OOS, one-look+prereg+cooling-off+dated sign-off (SC#2) | VERIFIED | `.planning/framework/validation-standards.md` §(a) causal/PIT (line 28), §(b) mechanism gate (line 35), §(c) confound-check w/ rate-cycle + dispersion-lead precedents (line 42), §(d) Japan/Europe OOS (line 54), §(e) temporal freeze — one look/prereg/cooling-off/dated sign-off (line 60) — all five in a single document |
| 3 | Output format specifies reading · rarity percentile · assumption monitored · four confidence dims · maturity tag, zero allocation fields; confidence framed as research maturity; maturity descriptive (SC#3, D-06/D-08, D-13) | VERIFIED (with documented deviation from stale ROADMAP text) | `signal-output-spec.md` §1 defines 4 dims (measurement quality/mechanism support/evidence robustness/implementation maturity) each H/M/L anchored with declared starting points and a prominent "research maturity, not predictive likelihood" disclaimer (lines 16-20); §2 states maturity is DERIVED and explicitly NOT a ranking (D-13, lines 100-104); §4.1 Level-0 JSON shows reading/rarity/assumption_monitored/confidence/maturity/spec_version with an explicit "Zero allocation/decision fields" line (184). Note: ROADMAP.md SC#3 literal text still reads "three confidence dimensions (measurement · interpretation · regime-relevance)" — this is *stale text*, and the delivered spec explicitly records this supersession (§3, "Upstream docs are STALE, not silently rewritten") rather than silently diverging; the four-dimension model is the developer's own D-06 decision in 01-CONTEXT.md, so the newer doc is authoritative over the older ROADMAP wording |
| 4 | Level 0/1/2 assumption-ledger shape defined, STOPS at Level 2; composite-scalar prohibition distinct from joint-rarity lens (SC#4, D-14, D-09) | VERIFIED | `signal-output-spec.md` §4 fixes Level 0=measurement, Level 1=historical context, Level 2=regime relevance with explicit "STOPS at Level 2 — there is no Level 3, no action, no decision" (lines 158-160); §4.4 forbids any composite-scalar field ("market risk = 73/100" named forbidden) while explicitly permitting joint rarity/Mahalanobis as a distinct Level-2 lens (lines 213-225); §4.5 states the D-11 no-dominance/co-equal presentation rule |
| 5 | Later signals can declare against the spec without reinterpretation; two retro-fit examples demonstrate this (SC#5) | VERIFIED | `examples/volatility-signal-declaration.md` (fast, production, shipped jump-model) and `examples/stock-bond-corr-signal-declaration.md` (slow, research, pending intl OOS) both fill the header + all 8 attributes + Level 0 record cleanly, including two genuine forced "Not applicable, because …" answers in the stock-bond example (Q3.2, Q4.2) — proving the template fits two heterogeneous shapes without being edited |
| 6 | Research-charter requirement (D-15) and architecture cross-link (D-16) present | VERIFIED | `.planning/framework/research-charter-template.md` poses the six charter questions in order, states it is frozen before implementation, and maps to spec attributes 1/2/5/6/8; `validation-standards.md` §(k) states "no signal is implemented before its charter exists"; `.planning/REGIME-SENSOR-ARCHITECTURE.md` lines 6-12 add a "Governing specification" block naming `.planning/framework/` and the three-doc role split (framework=rules · phases=roadmap · architecture=system design) |
| 7 | [ASSUMED] items remain gated on dated sign-off, never asserted as frozen | VERIFIED | `.planning/framework/SIGNOFF-CHECKLIST.md` states "Status: NOT SIGNED — nothing in the framework is frozen to v1.0" (line 3), lists A1/A2/A3/D-06-swap/RF with blank disposition + date lines (lines 44-50); both example declarations leave "Dated sign-off" blank with an explanatory note rather than asserting sign-off |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.planning/framework/signal-spec-template.md` | Merged 8-attribute question-form template | VERIFIED | Exists, contains "8. Limitations", header block with 6 universal-required fields, semver `v0.1-draft` |
| `.planning/framework/research-charter-template.md` | Six-question pre-registration charter | VERIFIED | Exists, contains "would falsify", maps to spec attributes |
| `.planning/framework/validation-standards.md` | Cross-signal validation law | VERIFIED | Exists, contains "mechanism gate", all (a)-(k) sections present |
| `.planning/framework/signal-output-spec.md` | Confidence model + maturity + Level 0/1/2 shape | VERIFIED | Exists, contains "implementation maturity", all 4 sections present |
| `.planning/framework/SIGNOFF-CHECKLIST.md` | Consolidated [ASSUMED]/veto items | VERIFIED | Exists, A1/A2/A3/D-06-swap/RF all listed, sign-off lines blank |
| `.planning/framework/examples/volatility-signal-declaration.md` | Retro-fit of shipped vol/jump-model signal | VERIFIED | Exists, full header + 8 attributes + Level 0 record + confidence vector |
| `.planning/framework/examples/stock-bond-corr-signal-declaration.md` | Retro-fit of stock-bond corr signal | VERIFIED | Exists, full header + 8 attributes + Level 0 record + confidence vector, 2 genuine N/A answers |
| `.planning/REGIME-SENSOR-ARCHITECTURE.md` | Cross-linked to `.planning/framework/` as governing spec | VERIFIED | Contains "governing specification" block (lines 6-12) naming all 3 framework files + 3-doc role split; existing content preserved, not restructured |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `signal-spec-template.md` attr 2/5 | `validation-standards.md` | named reference | WIRED | Line 50 ("`validation-standards.md` §The mechanism gate"), line 81-82 (cross-signal law reference) |
| `signal-spec-template.md` attr 7 + maturity header | `signal-output-spec.md` | named reference | WIRED | Line 25-26 (maturity field: "See `signal-output-spec.md` for the derivation rule"), line 98-99 (confidence attr points there, does not restate anchors) |
| `research-charter-template.md` | `signal-spec-template.md` | maps to attrs 1/2/5/6/8 | WIRED | Each of the six charter questions states "Maps to spec attribute N" (lines 28, 32, 36, 41, 46, 51) |
| `REGIME-SENSOR-ARCHITECTURE.md` | `.planning/framework/` | governing-spec cross-link | WIRED | Lines 6-12 name all three framework files by path and state "Where this doc's per-sensor spec or confidence text differs from the framework, the framework governs" |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| FRWK-01 | 01-01-PLAN, 01-02-PLAN | The shared signal spec exists — 8-attribute template, validation standards, output/ledger format, maturity model | SATISFIED | All artifacts above exist and are substantively complete and cross-wired; REQUIREMENTS.md already marks FRWK-01 `[x]` Complete and its Traceability table lists Phase 1 = Complete |

No orphaned requirements: REQUIREMENTS.md maps only FRWK-01 to Phase 1, and both plans declare `requirements: [FRWK-01]` — fully accounted for.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers found in any of the 7 framework docs | — | None — clean |
| `examples/volatility-signal-declaration.md` | 1, 11, 33, 77, 97 | "Risk-Off" used as the shipped signal's established name / per-signal state label (not a market-wide summary) | Info | Matches the pre-existing project convention (CLAUDE.md itself calls this "the volatility/risk-off (shipped)" signal) — describes ONE signal's internal state (calm vs stressed), not the forbidden system-wide single-word risk-on/risk-off verdict D-02 prohibits. Not a HARD BOUNDARY violation, but flagged because the plan's own Task-3 verify grep (`portfolio|allocat|exposure|sleeve|tilt|/100`) did not include `risk-on|risk-off` tokens, so this usage was never actually grepped by the executor's own audit command — a minor audit-scope gap, not a content violation |

**Independent full-vocabulary grep** (`portfolio|allocat|exposure|sleeve|tilt|risk-on|risk-off|/100|composite score|cash |buy |sell `) run across all 7 delivered docs by the verifier: every hit sits inside a forbidden-vocabulary list, a prohibition/boundary statement, a supersession note naming a dropped term, or (per the note above) the pre-existing shipped-signal name. Zero hits are a live allocation/decision field, value, or instruction.

### Human Verification Required

None. This is a documentation/specification phase; all must-haves are verifiable by reading the delivered Markdown files and cross-referencing frontmatter/grep evidence. No visual, real-time, or external-service behavior is in scope.

### Gaps Summary

No gaps. All 7 derived must-have truths verified, all 8 required artifacts exist and are substantive (not stubs — each contains genuine, specific, cross-referenced content rather than placeholder text), all 4 key links are wired by name, FRWK-01 is satisfied, and the HARD BOUNDARY reviewed-grep audit passes (every forbidden-token hit is a prohibition/supersession statement or an established pre-existing signal name, never a live field).

One noteworthy but non-blocking observation: ROADMAP.md's Phase 1 Success Criterion #3 still literally reads "three confidence dimensions (measurement · interpretation · regime-relevance)" — stale wording that predates the developer's own D-06 decision (in 01-CONTEXT.md) to move to four dimensions. The delivered `signal-output-spec.md` §3 explicitly documents this as a recorded supersession rather than silently diverging, and flags updating ROADMAP.md as an optional follow-up for Adam. Since D-06 is the developer's own explicit, dated decision overriding the earlier ROADMAP text, this is treated as satisfied-with-documented-deviation, not a gap.

---

_Verified: 2026-08-03T17:22:26Z_
_Verifier: Claude (gsd-verifier)_

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/01-signal-framework/01-01-PLAN|01-01-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-01-SUMMARY|01-01-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-02-PLAN|01-02-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-02-SUMMARY|01-02-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-CONTEXT|01-CONTEXT]]
- [[_planning/regime-detection/phases/01-signal-framework/01-RESEARCH|01-RESEARCH]]

<!-- LINKS:END -->
