# Phase 4: Empirical Diagnostics - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 04-empirical-diagnostics
**Areas discussed:** Output format & location, Code organization, Persistence baseline design, Forward return analysis scope

---

## Output format & location

| Option | Description | Selected |
|--------|-------------|----------|
| reports/diagnostics_report.md | Structured markdown, human-readable, git-committable | ✓ |
| figures/diagnostics.html | HTML with embedded figures, matches dashboard.html pattern | |
| Stdout + CSV | Console output + raw data CSV, no visualization | |

**User's choice:** `reports/diagnostics_report.md`
**Notes:** User clarified "don't build new things, just upgrade current setup" — all work extends existing files and patterns

Figure saving:

| Option | Description | Selected |
|--------|-------------|----------|
| Save figures to figures/ | PNG files for vol boxplot, dwell time histogram, transition matrix heatmap | ✓ |
| Markdown only | ASCII tables and printed stats, no saved figures | |

---

## Code Organization

**Decision from user clarification:** Extend existing files only — no new modules or scripts.
- `scripts/analysis/analyze_regime_characterization.py` — extend existing functions, add report writing
- `src/core/evaluation.py` — add DIAG-04 forward return function
- `tests/test_regime_economic_validity.py` — new test file (explicitly specified in REQUIREMENTS.md)

---

## Persistence Baseline Design

| Option | Description | Selected |
|--------|-------------|----------|
| Use existing held-out test split | Same OOS set as v1.0 — apples-to-apples comparison | ✓ |
| Rolling 90-day window | More realistic production simulation, fresh window | |

**User's choice:** Existing held-out test split

| Option | Description | Selected |
|--------|-------------|----------|
| Exact match % per day | % of days model regime == previous day's regime | ✓ |
| Adjusted Rand Index | Cluster-aware metric, accounts for chance agreement | |

**User's choice:** Exact match % per day

---

## Forward Return Analysis Scope

| Option | Description | Selected |
|--------|-------------|----------|
| New function in evaluation.py | All validation logic in one place, called from characterization script | ✓ |
| In analyze_regime_characterization.py directly | Simpler import chain | |

**User's choice:** New function in `evaluation.py`

| Option | Description | Selected |
|--------|-------------|----------|
| Just report p-values | Diagnostic only, human interprets | ✓ |
| Auto-flag with p < 0.05 | VALID/INVALID per regime | |

**User's choice:** Just report p-values

---

## Claude's Discretion

- Figure styling and color scheme
- Report markdown structure and section ordering
- Failure mode analysis criteria (which misclassification patterns to highlight for DIAG-03)

## Deferred Ideas

None.
