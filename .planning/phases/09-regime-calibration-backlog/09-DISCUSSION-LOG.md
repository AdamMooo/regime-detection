# Phase 9: Regime Calibration — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-05
**Phase:** 09-regime-calibration-backlog
**Areas discussed:** Plan structure, Dashboard NaN blocker, High-Vol calibration lever, Label alignment fix

---

## Plan Structure

| Option | Description | Selected |
|--------|-------------|----------|
| 3 separate plans | One plan per bug, sequential. Each has its own fix + regression test. | ✓ |
| 1 combined plan | All 3 bugs in a single plan. Simpler but harder to isolate regressions. | |
| 2 plans: fast fixes + calibration | Plan 1 = GARCH + labels; Plan 2 = High-Vol calibration. Groups by effort type. | |

**User's choice:** 3 separate plans (Recommended)
**Notes:** Plans execute in order: Plan 1 (GARCH + dashboard NaN unblock) → Plan 2 (label alignment) → Plan 3 (High-Vol calibration).

---

## GARCH Fix Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Surgical unit fix + assertion | Fix unit mismatch in var_backtesting.py + assert mean_vol < 1.0 | ✓ |
| Full GARCH audit | Trace GARCH inputs end-to-end across the pipeline. Wider scope. | |
| You decide | Leave GARCH fix scope to the planner. | |

**User's choice:** Surgical unit fix + assertion (Recommended)
**Notes:** Minimal scope: find the basis-point vs decimal mismatch, fix it, add a regression assertion.

---

## Dashboard NaN Blocker

| Option | Description | Selected |
|--------|-------------|----------|
| Bundle into Plan 1 | Fix alongside GARCH fix. Small isolated fix, prerequisite for end-to-end validation. | ✓ |
| Own plan (Plan 0) | Separate plan for the dashboard fix. Clean separation but adds a 4th plan. | |

**User's choice:** Yes — bundle into Plan 1 (Recommended)
**Notes:** The exit code 1 crash blocks validating the calibration fixes end-to-end. Bundling makes Plan 1 the "unblock plan."

---

## Dashboard NaN Fix Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Drop NaN rows before PCA | Minimal guard on PCA input in stage_dashboard. Fast, targeted. | ✓ |
| Impute NaN then PCA | Forward-fill or median-impute before PCA. More complex. | |
| Catch exception, log and continue | Wrap PCA in try/except. Less principled — masks data issues. | |

**User's choice:** Drop NaN rows before PCA call (Recommended)

---

## High-Vol Calibration Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Diagnostic first, then tune | Run diagnostic after GARCH fix, then decide lever based on evidence. | ✓ |
| Tune VOL_BRACKETS only | Adjust config.py thresholds. Fast, no retrain needed. Risk: may mask prior problem. | |
| Tune HDP-HMM prior | Adjust Dirichlet concentration. Principled but requires full retrain. | |

**User's choice:** Diagnostic first, then tune (Recommended)
**Notes:** Diagnostic should run AFTER GARCH fix since mean_vol=700%+ may have inflated vol bracket assignments.

---

## High-Vol Acceptance Threshold

| Option | Description | Selected |
|--------|-------------|----------|
| 15–25% | Matches NOTES.md target, empirically correct for SPY. | ✓ |
| Under 30% | Looser, easier to hit. | |
| Balanced 20–40% each | Forces equal distribution regardless of economic reality. | |

**User's choice:** 15–25% (Recommended)

---

## Label Alignment Fix

| Option | Description | Selected |
|--------|-------------|----------|
| Replace with Hungarian matching | scipy.optimize.linear_sum_assignment, discrete exact assignment. | ✓ |
| Debug existing Procrustes | Investigate why Procrustes produces 8 variants and fix it. | |
| Procrustes + Hungarian fallback | Keep Procrustes, fall back to Hungarian when > K labels produced. | |

**User's choice:** Replace with Hungarian matching (Recommended)
**Notes:** scipy already a dep. Hungarian solves a discrete assignment problem, which is exactly what fold label alignment needs.

---

## Label Alignment Regression Test

| Option | Description | Selected |
|--------|-------------|----------|
| Assert ≤3 distinct OOS labels | Assert unique regime_name_oos count <= K=3. Direct test of the failure. | ✓ |
| Assert label overlap > threshold | Assert IS/OOS share >= 80% of days in same regime. | |
| You decide | Leave test design to the planner. | |

**User's choice:** Assert ≤3 distinct OOS labels (Recommended)

---

## Claude's Discretion

None — all gray areas had explicit user decisions.

## Deferred Ideas

None — discussion stayed within phase scope.
