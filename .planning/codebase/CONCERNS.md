# Codebase Concerns

**Analysis Date:** 2026-05-11

## Tech Debt

**Configuration drift:**
- Issue: `src/config.py` still contains legacy XEG/TSX references and unused constants from prior thesis direction.
- Files: `src/config.py`
- Impact: Hard to maintain SPX pivot and may confuse future feature changes.
- Fix approach: Keep `src/config.py` minimal and SPX-specific, remove legacy XEG constants.

**Legacy scripts:**
- Issue: `data_download.py`, `parametric_hmm.py`, and `threshold_regimes.py` duplicate functionality already present under `src/`.
- Files: `data_download.py`, `parametric_hmm.py`, `threshold_regimes.py`
- Impact: Confusion over canonical code path and possible stale behavior.
- Fix approach: Archive or remove legacy scripts once `src/` path is verified.

## Known Bugs

**Data collection script inconsistency:**
- Issue: `src/data/collect_macro.py` may have been overwritten with broken multi-line heredoc input; verify current file contents.
- Files: `src/data/collect_macro.py`
- Trigger: manual edits via terminal can break script body.
- Workaround: Use a clean version of the script and test `python -m src.data.collect_macro`.

## Security Considerations

**Environment variables:**
- Risk: `requirements.txt` includes `python-dotenv` and `fredapi` although no `.env` secrets are required for current SPX work.
- Files: `requirements.txt`
- Recommendation: Remove unused dependencies if truly unnecessary.

## Performance Bottlenecks

**HDP-HMM SVI compile cost:**
- Problem: JAX/NumPyro model compile cost can take tens of seconds on first run.
- Files: `src/core/hdp_hmm.py`, `src/experiments/thesis_experiments.py`
- Improvement path: Cache compiled model or lower SVI steps for early prototyping.

## Fragile Areas

**Threat to correctness:**
- Issue: `run_hdp_hmm()` in `src/experiments/thesis_experiments.py` uses placeholder `df['hdp_regime'] = 0` without actual posterior filtering.
- Files: `src/experiments/thesis_experiments.py`
- Why fragile: Metrics and analysis are invalid until regime labels are derived correctly.
- Safe modification: Implement filtered regime assignment using posterior state probabilities.
- Test coverage: None.

## Scaling Limits

**File-based pipeline:**
- Current capacity: small thesis dataset, single experiment run
- Limit: no support for parallel experiments, versioned datasets, or reproducible artifacts beyond CSVs
- Scaling path: add `src/pipeline/runner.py` integration and artifact versioning later

## Dependencies at Risk

**JAX/NumPyro pinning:**
- Risk: exact versions are required for reproducibility; changing them can silently alter HDP behavior.
- Impact: model results may become non-reproducible.
- Migration plan: keep strict pinning and record version lock in `requirements.txt`.

## Missing Critical Features

**Test suite:**
- Problem: No tests exist to validate data pipeline, thresholds, or model integration.
- Files: none
- Blocks: safe refactors and reproducibility checks
- Priority: High

**SPX-specific data module:**
- Problem: no dedicated function or script that clearly documents SPX data schema and saved CSV paths.
- Files: `src/data/collect_macro.py`
- Priority: Medium

## Test Coverage Gaps

**Untested experiment logic:**
- What's not tested: `src/experiments/thesis_experiments.py` orchestration, `src/baselines/threshold_rules.py`, and `src/baselines/parametric_hmm.py`
- Files: `src/experiments/thesis_experiments.py`, `src/baselines/*.py`
- Risk: hidden bugs in baseline metrics
- Priority: High

---

*Concerns audit: 2026-05-11*

---
LINKS:AUTO
