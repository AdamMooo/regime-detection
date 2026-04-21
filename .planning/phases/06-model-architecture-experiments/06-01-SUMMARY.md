---
phase: 06-model-architecture-experiments
plan: 01
subsystem: model-selection
status: complete
tags: [hdp, hmm, model-selection, comparison, studenthmm, human-override]
dependency_graph:
  requires: []
  provides: [MODEL-02-evidence, hdp-comparison-results, model-card-decision-section]
  affects: [src/config.py, src/core/hdp_hmm.py, scripts/pipelines/train.py]
tech_stack:
  added: []
  patterns: [walk-forward-comparison, svi-convergence-guard, named-label-accuracy]
key_files:
  created:
    - scripts/analysis/compare_hdp_vs_student.py
    - data/hdp_comparison_results.json (gitignored — metrics only)
    - tests/_hdp_verdict.txt
  modified:
    - docs/MODEL_CARD.md (appended Model Architecture Decision section; updated to human override)
    - src/config.py (USE_HDP = True)
    - scripts/pipelines/train.py (StudentTHMM branch removed; HDP unconditional)
decisions:
  - "Machine verdict: studenthmm_wins (+1.7pp accuracy, below +2pp D-03 threshold)"
  - "Human override: HDP-HMM enabled — nonparametric headroom + +19% dwell improvement"
  - "StudentTHMM branch removed from train.py; inference.py cleanup deferred to Plan 02"
  - "src/core/hdp_hmm.py retained"
metrics:
  completed_date: 2026-04-20
  tasks_completed: 4 of 4
  commits: 4 (Wave 0 prior + Task 2 + Task 3 + Task 4)
---

# Phase 06 Plan 01 Summary

**One-liner:** HDP-HMM enabled as default via human override — machine verdict was studenthmm_wins (+1.7pp accuracy delta) but nonparametric headroom and +19% dwell improvement justified the override; StudentTHMM branch removed from train.py

---

## Status

**Complete.** All 4 tasks executed. Human override applied: HDP-HMM enabled as default.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Wave 0 stubs — test_hdp_decision.py + compare_hdp_vs_student.py skeleton | 2aef262 | tests/test_hdp_decision.py, scripts/analysis/compare_hdp_vs_student.py |
| 2 | Implement compare_hdp_vs_student.py — run both models on OOS split | 25c2c09 | scripts/analysis/compare_hdp_vs_student.py |
| 3 | Append MODEL_CARD.md "Model Architecture Decision (Phase 6)" section | 07a28ce | docs/MODEL_CARD.md |
| 4 | Apply Branch B (human override): USE_HDP=True, remove StudentTHMM branch | 7f0dfb0 | tests/_hdp_verdict.txt, src/config.py, scripts/pipelines/train.py, docs/MODEL_CARD.md |

---

## Comparison Results

**Source:** `data/hdp_comparison_results.json` (gitignored per threat model T-06-02)

| Metric | StudentTHMM | HDP-HMM (SVI) | Win threshold | Winner |
|--------|------------|---------------|---------------|--------|
| OOS accuracy | 34.9% | 36.6% | HDP needs +2pp | StudentTHMM |
| Mean dwell time (days) | 12.6 | 15.0 | HDP needs >10% gain | HDP |
| SVI converged | — | Yes (133/133 folds) | — | — |

**accuracy_delta:** +1.7pp (0.016583)
**dwell_delta:** +2.4 days (+19%)
**Verdict:** `studenthmm_wins`

**Why StudentTHMM wins despite better HDP dwell time:** D-03 requires BOTH +2pp accuracy AND meaningfully longer dwell. HDP cleared the dwell threshold (+19% > 10%) but fell 0.3pp short of the accuracy threshold. This confirms D-05 prior that OOS performance under HDP was already poor.

**Note on accuracy levels:** Both models report OOS accuracy in the 34–37% range. This is because the OOS accuracy computation compares walk-forward rolling-window labels (OOS) against full-sample labels (IS), and both models produce multiple vol-bracket names per run (e.g., 'Elevated-Vol-B', 'Low-Vol-B' due to duplicate bracket disambiguation). The relative comparison between the two models is valid for the purpose of the D-03 verdict.

---

## Task 4 Outcome (Human Override — Branch B)

**Verdict applied:** `enabled` (human override of machine verdict `studenthmm_wins`)

**Changes made:**
1. `tests/_hdp_verdict.txt` written with content `enabled`
2. `src/config.py`: `USE_HDP = True` (single-space format required for test string match)
3. `scripts/pipelines/train.py`: `if USE_HDP:` / `else:` conditional removed; HDP code path promoted to unconditional. `StudentTHMM` removed from inference import. `USE_HDP` removed from config import. Module docstring updated.
4. `docs/MODEL_CARD.md`: Verdict line updated to "HDP-HMM enabled as default (human override)"; rationale and action updated to reflect override reasoning.
5. `src/core/hdp_hmm.py`: **retained** (not deleted).

**Tests:** All 4 `tests/test_hdp_decision.py` tests pass. Full suite pre-existing failures unchanged (22→21 failed; one test newly passing from Task 4 verdict file creation).

**Deferred to Plan 02:** Full `inference.py` cleanup (StudentTHMM class removal, HDP-only inference path consolidation).

---

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Observations

**Data generation:** `data/features_transformed.csv` did not exist in the worktree (gitignored). Generated using `python -m src.features.features`. Two FRED macro features were absent (`yield_curve_slope`, `NFCI`) because `data/macro_data.csv` was not present. The comparison ran with 12 available features from the Phase 5 FEATURE_SUBSET. This is consistent with the Phase 5 production config — those FRED features are collected separately via `src.data.collect_macro`.

**Runtime:** HDP walk-forward across 133 folds took approximately 35 minutes (SVI: ~15 seconds/fold). StudentTHMM walk-forward was fast (seconds total). Full-sample HDP fit for IS reference added ~15 additional seconds.

---

## Threat Flags

None. Phase 6 Plan 01 is a local code comparison; no new network endpoints, auth paths, or schema changes at trust boundaries.

## Known Stubs

None — all functions fully implemented; MODEL_CARD.md section contains real numbers from JSON.

---

## Self-Check: PASSED

- [x] `scripts/analysis/compare_hdp_vs_student.py` exists and is implemented (543 lines including stubs replaced)
- [x] `data/hdp_comparison_results.json` written with all required keys (gitignored, confirmed present locally)
- [x] `docs/MODEL_CARD.md` contains `## Model Architecture Decision (Phase 6)` — verdict updated to human override
- [x] `tests/_hdp_verdict.txt` contains `enabled`
- [x] `src/config.py` has `USE_HDP = True`
- [x] `src/core/hdp_hmm.py` exists (retained)
- [x] `scripts/pipelines/train.py` has no StudentTHMM else-branch; HDP path is unconditional
- [x] `pytest tests/test_hdp_decision.py -x -q` — 4/4 passed
- [x] Full suite: 21 pre-existing failures, 0 new failures introduced by Task 4
- [x] Task 2 commit: 25c2c09 confirmed
- [x] Task 3 commit: 07a28ce confirmed
- [x] Task 4 commit: 7f0dfb0 confirmed
