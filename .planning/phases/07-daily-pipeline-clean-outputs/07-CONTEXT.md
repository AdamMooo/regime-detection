# Phase 7: Daily Pipeline & Clean Outputs — Context

**Gathered:** 2026-04-21
**Status:** Ready for planning
**Source:** COMPLETION-PLAN.md (pre-designed by developer, PRD Express Path)

<domain>
## Phase Boundary

Phase 7 delivers a single-command daily pipeline (`python scripts/run.py`) that:
- Runs collect → features → pca → train_hmm → garch → signals → dashboard in under 10 minutes
- Produces exactly 2 HTML outputs: `figures/dashboard.html` and `figures/feature_analysis.html`
- Writes `data/regime_results.csv` with full regime state on every run, cron-safe

Phase 7 also creates forward extension points so Phases 9–12 (vol forecast, backtester, transition predictor, anomaly layer) can bolt on without refactoring the core pipeline.

This phase does NOT add alpha logic, backtesting code, new HMM features, or graph/TDA code.
The model (hdp_hmm.py, inference.py, features.py) is frozen.

</domain>

<decisions>
## Implementation Decisions

### Plan 07-01: Pipeline Modularization + Timing Gate

**Locked:** Create `src/pipeline/` package with 3 files:
- `src/pipeline/__init__.py` — exports Pipeline class
- `src/pipeline/stages.py` — PipelineStage base + stage registry
- `src/pipeline/runner.py` — Pipeline class with `run_all()`, `run_from()`, `run_stage()`

**Locked:** Pipeline stages (in order):

| Stage | Input | Output | Max time |
|-------|-------|--------|----------|
| `collect` | config | `data/market_data.csv`, `data/macro_data.csv` | 5 min (incremental) |
| `features` | market CSVs | `data/features_transformed.csv` | 30 sec |
| `pca` | features CSV | `data/principal_components.csv` | 30 sec |
| `train_hmm` | PCs | fitted HMM + filtered labels | 2 min (no walk-forward) |
| `garch` | regime labels + returns | per-regime GARCH params | 30 sec |
| `signals` | regime results | `data/regime_results.csv` | 10 sec |
| `dashboard` | regime results + signals | `figures/dashboard.html` | 30 sec |
| `walk_forward` | features | OOS labels (slow, optional) | 4 hr — skip in daily |

**Locked:** Each stage reads its own inputs from disk and writes its own outputs to disk — stateless functions. Walk-forward runs only via `--validate` flag, NOT in daily pipeline.

**Locked:** `runner.py` records timing per stage; prints wall-clock summary at end.

**Locked tests to add:**
- `test_pipeline_stages.py` — each stage runs in isolation and produces expected output files
- `test_pipeline_timing.py` — full pipeline (no walk-forward) completes in <600 seconds
- `test_pipeline_idempotent.py` — running twice produces identical `regime_results.csv`

**Locked:** Refactor `scripts/pipelines/train.py` into the discrete stage functions above.

### Plan 07-02: Clean Output Enforcement + Cron Readiness

**Locked:** `figures/` cleanup — delete stale HTML files before each run, write exactly 2.

**Locked:** Exit codes — exit 0 on success, exit 1 on any stage failure (some failures currently swallowed).

**Locked:** `logs/pipeline.log` — rotating log file (10MB cap, 3 backups), timestamps per stage.

**Locked:** `scripts/cron_run.sh` — minimal shell wrapper: activate venv, run, log exit code.

**Locked:** `scripts/health_check.py` — reads `regime_results.csv`, checks freshness, prints PASS/FAIL.

**Locked tests to add:**
- `test_output_count.py` — run pipeline twice, assert exactly 2 HTML files exist
- `test_exit_codes.py` — force a stage failure, assert exit code = 1

### Plan 07-03: regime_results.csv Schema Hardening

**Locked:** Existing columns (must remain unchanged — RESEARCH Q1 resolved: actual names are canonical, CONTEXT.md placeholders were abstract):
`date` (index), `regime` (int), `regime_name`, `prob_Low-Vol`, `prob_Moderate-Vol`, `prob_High-Vol`, `smooth_prob_<regime_name>`, `VIX`, `SPY_close`, `garch_var_95`, `market_mode_ratio`, `is_oos`, `regime_oos`, `regime_name_oos`

**Locked:** New columns to add:
| Column | Description | Source |
|--------|-------------|--------|
| `days_in_regime` | Consecutive days in current regime | computed in signals.py |
| `regime_entropy` | -Σ p_k log(p_k) | computed in signals.py |
| `garch_vol_forecast` | σ̂_t from GARCH(1,1) | from garch stage |
| `blended_vol_forecast` | Σ_k P(Z_t=k) · σ̂_{k,t} | placeholder NaN (Phase 9 fills) |
| `transition_score` | transition early-warning | placeholder NaN (Phase 11 fills) |
| `structural_anomaly` | structural break indicator | placeholder NaN (Phase 12 fills) |

**Locked:** Placeholder columns are NaN until the research phase implements them. Downstream consumers must handle NaN gracefully.

**Locked:** Extension artifact: `data/garch_params.json` — per-regime GARCH params written by garch stage (Phase 9 reads this).

**Locked:** Extension artifact: `data/oos_regime_labels.csv` — written by walk-forward stage (Phase 11 reads this for transition classifier training).

**Locked tests to add:**
- `test_regime_results_schema.py` — assert all columns exist, correct dtypes, no missing dates
- `test_regime_results_freshness.py` — today's date is the last row after a run

### Extension Points (deliberate seams for Phases 9–12)

- **Phase 9 (vol forecast):** After `garch` stage, reads `data/garch_params.json`, writes `blended_vol_forecast` column. New file: `src/core/vol_forecast.py`.
- **Phase 10 (backtester):** Standalone script reading `regime_results.csv` + `market_data.csv`. New files: `src/backtest/strategy.py`, `src/backtest/metrics.py`.
- **Phase 11 (transition predictor):** After `signals` stage, reads `regime_results.csv` + `features_transformed.csv`, writes `transition_score`. New file: `src/signals/transition_predictor.py`.
- **Phase 12 (anomaly):** After `signals` stage, reads rolling windows, writes `structural_anomaly`. New file: `src/signals/anomaly.py`.

### What Must NOT Be Built in Phase 7

- No alpha logic in `regime_results.csv` (placeholders stay NaN)
- No backtesting code inside `train.py` or `signals.py`
- No new features added to HMM training (feature set locked at Phase 5)
- No graph or TDA code

### Files Not Touched (Frozen)

- `src/core/hdp_hmm.py` — model locked
- `src/core/inference.py` — filtering logic locked
- `src/features/features.py` — feature set locked
- Existing tests — no modifications, only additions

### Claude's Discretion

- Exact internal structure of stage functions (function signatures, args/kwargs)
- Whether `stages.py` uses a registry dict or inheritance
- Exact log format within the rotating log file
- Whether health_check.py uses argparse or hardcoded paths
- Error handling verbosity inside each stage

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Design
- `.planning/COMPLETION-PLAN.md` — Full Phase 7 design with stage table, schema, extension points, and explicit "what NOT to build" list
- `.planning/RESEARCH-STRATEGY.md` — Research sequence and rationale for Phases 8–12; defines what each extension point enables

### Pipeline Entry Point
- `scripts/run.py` — Current entry point; must be updated to delegate to `Pipeline.run_all()`
- `scripts/pipelines/train.py` — Current monolith; must be refactored into stage functions

### Signal Schema
- `src/signals/signals.py` — Adds `days_in_regime`, `regime_entropy` computations; regime_results.csv writer lives here

### Architecture Decisions
- `.planning/STATE.md` (Decision 6) — HDP-HMM enabled as primary model; USE_HDP=True locked
- `src/config.py` — USE_HDP=True, FEATURE_SUBSET, VIX_BYPASS=True — do NOT modify
- `.planning/REQUIREMENTS.md` — PIPE-01, PIPE-02, PIPE-03 definitions

### Existing Core Modules (read before touching imports)
- `src/core/evaluation.py` — 186 lines (post-Phase 6 refactor)
- `src/core/hmm_training.py` — 458 lines (post-Phase 6 refactor)
- `src/core/pca_utils.py` — 181 lines (new in Phase 6)
- `src/core/var_backtesting.py` — 403 lines (new in Phase 6)
- `src/core/forward_returns.py` — 275 lines (new in Phase 6)

</canonical_refs>

<specifics>
## Specific Ideas

**Timing target:** Full daily pipeline (no walk-forward) must complete in <10 min = <600 seconds. Per-stage budgets from COMPLETION-PLAN.md: collect 5min, features 30s, pca 30s, train_hmm 2min, garch 30s, signals 10s, dashboard 30s. Total headroom ~30s.

**HTML exactly-2 enforcement:** Delete `figures/*.html` before each run, then write exactly 2. Test by running twice and counting.

**Walk-forward isolation:** `--validate` flag triggers walk-forward; daily run NEVER triggers it. This is the key design decision enabling the <10min goal.

**garch_params.json format (extension point):** Per-regime dict: `{"0": {"omega": ..., "alpha": ..., "beta": ...}, "1": {...}, "2": {...}}` — enables Phase 9 to blend them.

**oos_regime_labels.csv:** Written with columns `[date, fold_id, regime_id, regime_name]` — enables Phase 11 transition classifier training.

</specifics>

<deferred>
## Deferred Ideas

- Automated cron scheduling (cron_run.sh is provided but not registered — user sets up)
- Docker container for pipeline (out of scope v1.1)
- Real-time streaming inference (out of scope v1.1)
- Dashboard live regime indicator panel (UI deferred until model quality verified)
- StudentTHMM full removal from inference.py (deferred from Phase 6, may be done in Phase 8)

</deferred>

---

*Phase: 07-daily-pipeline-clean-outputs*
*Context gathered: 2026-04-21 via COMPLETION-PLAN.md (developer pre-design)*
