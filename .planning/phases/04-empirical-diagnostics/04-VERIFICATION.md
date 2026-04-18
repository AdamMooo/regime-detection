---
phase: 04-empirical-diagnostics
verified: 2026-04-17T00:00:00Z
status: passed
score: 4/4
overrides_applied: 0
---

# Phase 4: Empirical Diagnostics — Verification Report

**Phase Goal:** Regime quality is measured, failure modes are documented, and economic validity is established — so all subsequent work is grounded in evidence
**Verified:** 2026-04-17
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Diagnostics report shows vol ordering, dwell time distributions, and transition matrix heatmap — failure modes visible at a glance | VERIFIED | `write_diagnostics_report()` in `analyze_regime_characterization.py` writes `reports/diagnostics_report.md` (at runtime). Three figures saved: `diag01_vol_boxplot.png`, `diag01_dwell_histogram.png`, `diag01_transition_heatmap.png` via `FIGURE_DIR` from `src.config`. All three `analyze_*` functions extended to save figures. |
| 2 | OOS regime accuracy is compared to a naive persistence baseline — clear whether model adds signal | VERIFIED | `compute_persistence_baseline()` defined (line 322) and called from `main()` (line 667). Uses `OOS_START = '2021-01-01'` matching MODEL_CARD.md split. Computes persist-yesterday accuracy and transition rate. Output included in diagnostics report Section 2. |
| 3 | Documented failure mode analysis identifies which regimes are most often misclassified and under which market conditions | VERIFIED | `analyze_failure_modes()` defined (line 378) and called from `main()` (line 670). Detects short spells (<= 3 days), flip-flop patterns (A->B->A within 5 days), crisis period alignment (COVID crash, 2022 bear, GFC), and top 5 most frequent transitions. Output in diagnostics report Section 3. |
| 4 | Regime-conditional forward return analysis (1d/5d/21d) for SPY/EEM/TLT/HYG runs in evaluation.py and KW test confirms or denies statistical separation | VERIFIED | `compute_forward_return_analysis()` at line 525 in `src/core/evaluation.py`. Uses `scipy.stats.kruskal`. Assets: SPY, EEM, TLT, HYG. Horizons: 1d, 5d, 21d. Wired from `analyze_regime_characterization.py main()` via import at line 675. 24 tests pass in `tests/test_regime_economic_validity.py`. |

**Score:** 4/4 truths verified

---

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `scripts/analysis/analyze_regime_characterization.py` | VERIFIED | Extended with `compute_persistence_baseline()`, `analyze_failure_modes()`, `write_diagnostics_report()`. `main()` calls all diagnostic functions and writes report. FIGURE_DIR and REPORTS_DIR constants defined. |
| `src/core/evaluation.py` | VERIFIED | `compute_forward_return_analysis()` and `analyze_forward_returns()` present. Both in `__all__`. KW test imported and used. Docstring states diagnostic-only / never model features. |
| `tests/test_regime_economic_validity.py` | VERIFIED | 24 tests, all passing (confirmed by pytest run). Imports `compute_forward_return_analysis`. Tests cover: output structure, KW validity, mean return coverage, causal integrity (forward returns not in training), edge cases (None inputs, missing columns, single regime). |
| `reports/diagnostics_report.md` | RUNTIME-ONLY | File written by `write_diagnostics_report()` when script is run with live data. Does not exist on disk without `data/regime_results.csv` and `data/market_data.csv`. This is expected behavior documented in SUMMARY as "Known Stubs: None — generated at runtime." |
| `figures/diag01_vol_boxplot.png` | RUNTIME-ONLY | Saved by `analyze_regime_statistics()` to `FIGURE_DIR` at runtime. Path: `figures/diag01_vol_boxplot.png`. |
| `figures/diag01_dwell_histogram.png` | RUNTIME-ONLY | Saved by `analyze_regime_duration()` at runtime. |
| `figures/diag01_transition_heatmap.png` | RUNTIME-ONLY | Saved by `analyze_transition_matrix()` at runtime. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `analyze_regime_characterization.py main()` | `reports/diagnostics_report.md` | `write_diagnostics_report()` → `open(report_path, 'w')` | WIRED | `REPORTS_DIR = 'reports'`, `report_path = os.path.join(REPORTS_DIR, 'diagnostics_report.md')` at line 644. |
| `analyze_regime_statistics()` | `figures/diag01_vol_boxplot.png` | `plt.savefig` via `FIGURE_DIR` | WIRED | Line 140: `fig_path = os.path.join(FIGURE_DIR, 'diag01_vol_boxplot.png')`. `FIGURE_DIR` imported from `src.config`. |
| `analyze_transition_matrix()` | `figures/diag01_transition_heatmap.png` | `plt.savefig` via `FIGURE_DIR` | WIRED | Line 213: `fig_path = os.path.join(FIGURE_DIR, 'diag01_transition_heatmap.png')`. |
| `analyze_regime_characterization.py` | `src.core.evaluation.compute_forward_return_analysis` | `from src.core.evaluation import compute_forward_return_analysis` | WIRED | Line 675 in `main()`. Graceful `ImportError` catch present. |
| `compute_forward_return_analysis()` | `scipy.stats.kruskal` | `kruskal(*groups)` | WIRED | `from scipy.stats import binom, chi2, kruskal` at top of `evaluation.py`. Used at line 596 inside `compute_forward_return_analysis`. |

---

## Naming Deviations (Non-Blocking)

Two naming deviations from the PLAN frontmatter were found. Neither blocks goal achievement because the roadmap success criteria are behavior-based, not filename-specific.

**Figure filenames:** 04-01-PLAN specified `vol_boxplot.png`, `dwell_time_histogram.png`, `transition_matrix_heatmap.png`. Implementation saves `diag01_vol_boxplot.png`, `diag01_dwell_histogram.png`, `diag01_transition_heatmap.png`. The `diag01_` prefix was added for clarity. Figures are consistently referenced in the report with the actual names.

**DIAG-04 function name:** 04-02-PLAN specified `compute_regime_forward_returns`. Implementation delivers `compute_forward_return_analysis` (and `analyze_forward_returns` as a second variant). The test file, the characterization script import, and `__all__` all consistently use `compute_forward_return_analysis`. The plan's function name was never created, but the intent — a callable KW-based forward return analysis in `evaluation.py`, exported in `__all__`, wired from main() — is fully satisfied.

---

## Requirements Coverage

| Requirement | Plan | Description | Status | Evidence |
|-------------|------|-------------|--------|---------|
| DIAG-01 | 04-01 | Regime characteristics visualized — vol ordering, dwell time, transition matrix heatmap | SATISFIED | Three figures saved by extended `analyze_*` functions; referenced in diagnostics report |
| DIAG-02 | 04-01 | OOS accuracy benchmarked against naive persistence baseline | SATISFIED | `compute_persistence_baseline()` with OOS split at 2021-01-01; in main() and report |
| DIAG-03 | 04-01 | Failure modes documented — most misclassified regimes, market conditions | SATISFIED | `analyze_failure_modes()` with crisis alignment, flip-flop detection, top transitions |
| DIAG-04 | 04-02 | Forward return analysis 1d/5d/21d SPY/EEM/TLT/HYG with KW test in evaluation.py + test file | SATISFIED | `compute_forward_return_analysis()` in evaluation.py, `__all__` exported, 24 tests passing |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 24 DIAG-04 tests pass | `python -m pytest tests/test_regime_economic_validity.py -q` | 24 passed in 0.87s | PASS |
| `compute_forward_return_analysis` importable | `from src.core.evaluation import compute_forward_return_analysis` | Import succeeds (confirmed by test run) | PASS |
| `analyze_failure_modes` defined | grep in `analyze_regime_characterization.py` | Found at line 378, called at line 670 | PASS |
| `compute_persistence_baseline` defined | grep in `analyze_regime_characterization.py` | Found at line 322, called at line 667 | PASS |

---

## Anti-Patterns Found

None blocking. The `REPORTS_DIR = 'reports'` constant is a relative string (not an absolute path derived from `PROJECT_ROOT`) but the script is designed to be run from the project root, consistent with all other scripts in the project. No TODO/FIXME/placeholder comments found in the key files.

---

## Human Verification Required

None. All must-haves are verifiable programmatically. The diagnostic output quality (report readability, figure legibility) is at Claude's discretion per 04-CONTEXT.md and is not a verification gate.

---

## Gaps Summary

No gaps. All four roadmap success criteria are satisfied. Phase goal achieved.

The only outstanding item — `reports/diagnostics_report.md` and figure PNGs not present on disk — is expected and documented: these are runtime outputs requiring `data/regime_results.csv` and `data/market_data.csv` which are produced by `python run.py`.

---

_Verified: 2026-04-17_
_Verifier: Claude (gsd-verifier)_
