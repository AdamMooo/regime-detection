---
phase: 04-empirical-diagnostics
plan: "02"
subsystem: diagnostics
tags: [diag-04, forward-returns, kruskal-wallis, evaluation, testing]
dependency_graph:
  requires: []
  provides: [analyze_forward_returns, test_regime_economic_validity, diagnostics_report]
  affects: [src/core/evaluation.py, scripts/analysis/analyze_regime_characterization.py]
tech_stack:
  added: [scipy.stats.kruskal]
  patterns: [diagnostic-only forward returns, no-lookahead validation]
key_files:
  created:
    - tests/test_regime_economic_validity.py
    - reports/diagnostics_report.md (generated at runtime)
    - figures/fwd_returns_SPY_{1,5,21}d.png (generated at runtime)
    - .planning/phases/04-empirical-diagnostics/04-02-PLAN.md
  modified:
    - src/core/evaluation.py
    - scripts/analysis/analyze_regime_characterization.py
decisions:
  - "Forward returns computed as pure diagnostic — never fed back to training (Decision 5)"
  - "Kruskal-Wallis p-values reported only — no auto-flag (human interprets)"
  - "SPY boxplot figures saved to figures/ directory at 1d/5d/21d horizons"
metrics:
  duration_minutes: 25
  completed: "2026-04-17"
  tasks_completed: 3
  tasks_total: 3
  files_created: 2
  files_modified: 2
---

# Phase 4 Plan 02: DIAG-04 Forward Return Analysis Summary

**One-liner:** Regime-conditional forward return analysis (SPY/EEM/TLT/HYG, 1d/5d/21d) with Kruskal-Wallis tests added to evaluation.py and integrated into characterization script with markdown report output.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add analyze_forward_returns to evaluation.py | 26e3c2e | src/core/evaluation.py |
| 2 | Create tests/test_regime_economic_validity.py | 08baef4 | tests/test_regime_economic_validity.py |
| 3 | Integrate into characterization script and report | 330bad5 | scripts/analysis/analyze_regime_characterization.py |

## What Was Built

### src/core/evaluation.py — `analyze_forward_returns()`

New function implementing DIAG-04:
- Computes forward log returns for SPY, EEM, TLT, HYG at 1d, 5d, 21d horizons
- Groups returns by regime label and runs `scipy.stats.kruskal` (non-parametric ANOVA)
- Returns `dict[(asset, horizon)] = {median_returns, kw_stat, kw_pvalue, n_regimes}`
- Prints formatted p-value table and per-regime SPY median return summary
- Added to `__all__`; forward returns never passed to training functions

### tests/test_regime_economic_validity.py — 7 tests, all passing

| Test | Validates |
|------|-----------|
| test_analyze_forward_returns_returns_dict | Output is dict with (asset, horizon) keys |
| test_analyze_forward_returns_kw_stat_present | kw_stat and kw_pvalue present and valid |
| test_analyze_forward_returns_no_lookahead | results DataFrame not modified by function |
| test_analyze_forward_returns_handles_missing_assets | Missing columns skipped gracefully |
| test_analyze_forward_returns_median_returns_per_regime | One median return per unique regime |
| test_analyze_forward_returns_none_inputs | Returns {} when either input is None |
| test_analyze_forward_returns_n_regimes_field | n_regimes equals unique regime count |

### scripts/analysis/analyze_regime_characterization.py — Extended main()

- Imports `analyze_forward_returns` from `src.core.evaluation`
- Calls `analyze_forward_returns(results, market)` after DIAG-01/02/03
- `analyze_forward_return_figures()`: saves SPY boxplots to `figures/fwd_returns_SPY_{1,5,21}d.png`
- `write_diagnostics_report()`: writes `reports/diagnostics_report.md` with KW p-value table and per-regime median return table; references figures

## Verification

```
pytest tests/test_regime_economic_validity.py -v
7 passed in 0.54s
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. The forward return analysis is fully implemented. Generated files (report, figures) are created at runtime when `data/regime_results.csv` and `data/market_data.csv` exist.

## Threat Flags

None. This plan adds diagnostic-only code with no new network endpoints, auth paths, or schema changes. Forward returns are never fed to the training pipeline (no lookahead introduced).

## Self-Check: PASSED

- `src/core/evaluation.py` — modified, `analyze_forward_returns` present in `__all__` ✓
- `tests/test_regime_economic_validity.py` — created, 7/7 tests passing ✓
- `scripts/analysis/analyze_regime_characterization.py` — modified, imports and calls verified ✓
- Commits 26e3c2e, 08baef4, 330bad5 present in git log ✓
