---
phase: "04"
plan: "01"
subsystem: diagnostics
tags: [empirical-diagnostics, regime-characterization, forward-returns, kruskal-wallis]
dependency_graph:
  requires: [data/regime_results.csv, data/market_data.csv]
  provides: [reports/diagnostics_report.md, figures/diag01_*.png, compute_forward_return_analysis]
  affects: [scripts/analysis/analyze_regime_characterization.py, src/core/evaluation.py]
tech_stack:
  added: [scipy.stats.kruskal]
  patterns: [standalone analysis script, validation-only diagnostics]
key_files:
  created:
    - tests/test_regime_economic_validity.py
    - .planning/phases/04-empirical-diagnostics/04-01-PLAN.md
  modified:
    - scripts/analysis/analyze_regime_characterization.py
    - src/core/evaluation.py
decisions:
  - "Forward returns computed in percent scale via log(price[t+h]/price[t])*100"
  - "Kruskal-Wallis p-values reported only — no auto-flag per CONTEXT D-07"
  - "Causal integrity enforced via 4 test assertions that forward returns never enter training"
  - "matplotlib Agg backend set to prevent display errors in headless execution"
metrics:
  duration: "~45 minutes"
  completed: "2026-04-17"
  tasks_completed: 3
  files_modified: 4
  tests_added: 24
---

# Phase 4 Plan 1: Empirical Diagnostics Summary

**One-liner:** Regime diagnostic pipeline — vol boxplots, dwell histograms, transition heatmaps, persistence baseline, crisis alignment, and Kruskal-Wallis forward return analysis across SPY/EEM/TLT/HYG at 1d/5d/21d horizons.

## What Was Built

All 4 DIAG requirements implemented by extending existing files (no new modules):

### DIAG-01: Regime Characterization Figures
Extended `analyze_regime_statistics()`, `analyze_transition_matrix()`, `analyze_regime_duration()` in `analyze_regime_characterization.py` to save three figures to `figures/`:
- `diag01_vol_boxplot.png` — 21-day annualised volatility distribution per regime (boxplot)
- `diag01_transition_heatmap.png` — transition probability heatmap (Blues colormap)
- `diag01_dwell_histogram.png` — dwell time histograms per regime with mean/median lines

### DIAG-02: Persistence Baseline
New `compute_persistence_baseline()` function:
- Splits regimes at `OOS_START = '2021-01-01'` (matching MODEL_CARD.md eval set)
- Computes persist-yesterday accuracy and regime change rate for OOS period
- Reports how often the model changes regime vs the trivial baseline

### DIAG-03: Failure Mode Analysis
New `analyze_failure_modes()` function:
- Detects short spells (<= 3 days) as instability indicator
- Detects flip-flop patterns (A->B->A within 5 days)
- Checks crisis period alignment: COVID crash, 2022 bear, GFC vs expected high-vol regime
- Reports top 5 most frequent regime transitions

### DIAG-04: Forward Return Analysis
New `compute_forward_return_analysis()` in `src/core/evaluation.py`:
- Computes 1d/5d/21d forward log-returns in % for SPY, EEM, TLT, HYG
- Groups by regime, runs Kruskal-Wallis for statistical separation
- Returns p-values only — no auto-flagging (human interpretation per CONTEXT D-07)
- Called from `analyze_regime_characterization.py main()` for report integration

### Report
`write_diagnostics_report()` writes `reports/diagnostics_report.md` covering all 4 diagnostics with tables, figures references, and interpretation notes.

### Tests (24 passing)
`tests/test_regime_economic_validity.py`:
- Structure, KW validity, mean return coverage, causal integrity, edge cases

## Commits

| Commit | Hash | Description |
|--------|------|-------------|
| 1 | 1a5ab92 | feat(04-01): DIAG-01/02/03 figures+report and DIAG-04 forward return analysis |
| 2 | 3930796 | test(04-01): add DIAG-04 economic validity tests (24 tests) |
| 3 | d076556 | docs(04-01): add 04-01-PLAN.md |

## Deviations from Plan

None — all requirements implemented as specified in CONTEXT.md.

## Known Stubs

None — all diagnostic functions return real computed values. Report generation
(`reports/diagnostics_report.md` and `figures/diag01_*.png`) requires live data files
(`data/regime_results.csv`, `data/market_data.csv`) which are produced by `python run.py`.

## Threat Flags

None — this plan adds no network endpoints, auth paths, or schema changes. All new
code is read-only analysis consuming existing CSV files.

## Self-Check: PASSED

Files created/modified:
- FOUND: scripts/analysis/analyze_regime_characterization.py
- FOUND: src/core/evaluation.py
- FOUND: tests/test_regime_economic_validity.py
- FOUND: .planning/phases/04-empirical-diagnostics/04-01-PLAN.md

Commits verified:
- FOUND: 1a5ab92
- FOUND: 3930796
- FOUND: d076556

Tests: 24/24 passed
