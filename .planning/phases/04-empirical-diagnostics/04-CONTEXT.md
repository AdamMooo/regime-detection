# Phase 4: Empirical Diagnostics - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Measure regime quality before any changes — produce a diagnostics report covering vol ordering, dwell time, transition matrix, OOS vs persistence baseline, failure mode analysis, and regime-conditional forward return analysis. This is a pure measurement phase: no model changes, no feature changes, no pipeline changes.

</domain>

<decisions>
## Implementation Decisions

### Output Format
- **D-01:** Diagnostic results written to `reports/diagnostics_report.md` — structured markdown, human-readable, git-committable
- **D-02:** Matplotlib figures saved to `figures/` (PNG) — vol boxplot, dwell time histogram, transition matrix heatmap — referenced from the report

### Code Organization
- **D-03:** Extend existing files only — do NOT create new modules or scripts
  - `scripts/analysis/analyze_regime_characterization.py` — add figure saving to existing `analyze_regime_statistics`, `analyze_transition_matrix`, `analyze_regime_duration` functions; add persistence baseline comparison (DIAG-02) and failure mode analysis (DIAG-03); `main()` writes `reports/diagnostics_report.md`
  - `src/core/evaluation.py` — add new function for DIAG-04 forward return analysis + Kruskal-Wallis; called from `analyze_regime_characterization.py main()`
  - `tests/test_regime_economic_validity.py` — new test file for DIAG-04 (specified in REQUIREMENTS.md DIAG-04)

### Persistence Baseline (DIAG-02)
- **D-04:** Use the existing held-out test split from v1.0 (same OOS set used in prior evaluations — apples-to-apples comparison)
- **D-05:** Accuracy metric = exact match % per day (what % of days does model regime == previous day's regime)

### Forward Return Analysis (DIAG-04)
- **D-06:** New function in `evaluation.py` (keeps all validation logic in one place); called from `analyze_regime_characterization.py main()`
- **D-07:** Kruskal-Wallis result reports p-values only — no auto-flag. Human interprets. Diagnostic only.
- **D-08:** Assets: SPY, EEM, TLT, HYG. Horizons: 1d, 5d, 21d.

### Claude's Discretion
- Exact figure styling and color scheme for matplotlib plots
- Report markdown structure and section ordering
- Failure mode analysis criteria (which misclassification patterns to highlight in DIAG-03)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §DIAG-01, DIAG-02, DIAG-03, DIAG-04 — exact acceptance criteria for each diagnostic

### Existing Code to Extend
- `scripts/analysis/analyze_regime_characterization.py` — existing functions to extend (not replace)
- `src/core/evaluation.py` — existing validation module; add forward return function here
- `docs/MODEL_CARD.md` — OOS test split definition and feature set reference

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `analyze_regime_statistics()` in `analyze_regime_characterization.py` — already computes per-regime stats; extend to save figures
- `analyze_transition_matrix()` — already computes transition matrix; add heatmap figure saving
- `analyze_regime_duration()` — already computes dwell time; add histogram figure saving
- `evaluate()` in `evaluation.py` — existing regime characteristic printing; reference for patterns
- `compute_var_backtest_garch()` in `evaluation.py` — reference for how validation functions are structured

### Established Patterns
- Analysis scripts in `scripts/analysis/` are standalone (not pipeline-imported), load from `data/regime_results.csv` and `data/market_data.csv`
- Reports written to `reports/`, figures to `figures/`
- Tests use `pytest` pattern matching existing test files in `tests/`

### Integration Points
- `data/regime_results.csv` — source of regime labels and probabilities for all diagnostics
- `data/market_data.csv` — source of SPY/EEM/TLT/HYG price data for DIAG-04
- OOS test split: defined in `docs/MODEL_CARD.md` (2021–2026 period based on v1.0 train/test split)

</code_context>

<specifics>
## Specific Ideas

- User explicitly stated: "don't build new things, just upgrade current setup" — all Phase 4 work must extend existing files
- DIAG-04 test lives in `tests/test_regime_economic_validity.py` (specified in REQUIREMENTS.md)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-empirical-diagnostics*
*Context gathered: 2026-04-17*
