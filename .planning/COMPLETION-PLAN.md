# HMM Pipeline Completion Plan
**Last updated:** 2026-04-21  
**Purpose:** Finish the v1.1 pipeline (Phase 7) in a way that deliberately leaves clean extension points for the research layers defined in RESEARCH-STRATEGY.md  
**Next action:** Run `/gsd-plan-phase 7` to break Phase 7 into executable plans

---

## The Core Principle

Finish Phase 7 not just to satisfy the PIPE requirements, but to ensure that every research addition described in RESEARCH-STRATEGY.md can be bolted on **without refactoring the core pipeline again**. Each extension point is identified below so the Phase 7 design consciously accommodates it.

---

## What "Done" Looks Like for the HMM Pipeline

The pipeline is complete when:

1. `python scripts/run.py` runs end-to-end in under 10 minutes on incremental data
2. Exactly 2 HTML outputs exist: `figures/dashboard.html` + `figures/feature_analysis.html`
3. `data/regime_results.csv` is written every run with today's regime, filtered probs, and GARCH VaR
4. The pipeline is cron-deployable (no interactive prompts, clean exit codes, idempotent)
5. The architecture has clean seams where research layers can plug in — documented below

---

## Phase 7 — Daily Pipeline & Clean Outputs

**Requirements:** PIPE-01, PIPE-02, PIPE-03  
**Depends on:** Phase 6 ✅ (complete)

### Plan 07-01: Pipeline Modularization + Timing Gate

**Goal:** Break `train.py` (1,000+ lines) into a proper pipeline class with discrete stages. Each stage is independently callable and timed.

**Why now:** The current `train()` function is monolithic. Any research extension (vol forecast blending, backtesting, transition predictor) needs to hook into a specific stage output. Without clear stage boundaries, those extensions create circular imports and tangled state.

**What to build:**

```
src/pipeline/
    __init__.py
    stages.py          — PipelineStage base + stage registry
    runner.py          — Pipeline class: run_all(), run_from(), run_stage()
```

**Stages (in order):**

| Stage | Input | Output | Max time |
|-------|-------|--------|----------|
| `collect` | config | `data/market_data.csv`, `data/macro_data.csv` | 5 min (incremental) |
| `features` | market CSVs | `data/features_transformed.csv` | 30 sec |
| `pca` | features CSV | `data/principal_components.csv` | 30 sec |
| `train_hmm` | PCs | fitted HMM + filtered labels | 2 min (no walk-forward) |
| `garch` | regime labels + returns | per-regime GARCH params | 30 sec |
| `signals` | regime results | `data/regime_results.csv` | 10 sec |
| `dashboard` | regime results + signals | `figures/dashboard.html` | 30 sec |
| `walk_forward` | features | OOS labels (slow, optional flag) | 4 hr — skip in daily |

**Key design decisions:**
- Each stage reads its own inputs from disk and writes its own outputs to disk
- No stage holds state from another stage in memory (stages are stateless functions)
- Walk-forward runs separately (`--validate` flag), not in the daily pipeline
- `runner.py` records timing per stage; prints wall-clock summary at end

**Tests to add:**
- `test_pipeline_stages.py` — each stage runs in isolation and produces expected output files
- `test_pipeline_timing.py` — full pipeline (no walk-forward) completes in <600 seconds
- `test_pipeline_idempotent.py` — running twice produces identical regime_results.csv

---

### Plan 07-02: Clean Output Enforcement + Cron Readiness

**Goal:** Exactly 2 HTML files after any run. Exit codes. Log file. Cron-safe.

**What to build:**
- `figures/` cleanup: delete stale HTML files before each run, write exactly 2
- Exit code 0 on success, 1 on any stage failure (currently some failures are swallowed)
- `logs/pipeline.log` — rotating log file (10MB cap, 3 backups) with timestamps per stage
- `scripts/cron_run.sh` — minimal shell wrapper: activate venv, run, log exit code
- `scripts/health_check.py` — reads `regime_results.csv`, checks freshness, prints PASS/FAIL

**Tests to add:**
- `test_output_count.py` — run pipeline twice, assert exactly 2 HTML files exist
- `test_exit_codes.py` — force a stage failure, assert exit code = 1

---

### Plan 07-03: regime_results.csv Schema Hardening

**Goal:** `regime_results.csv` has a stable, documented schema that downstream consumers (Algo-Trading-Bot, Portfolio-Manager) and future research layers can rely on.

**Current schema (inferred from signals.py):**

| Column | Type | Description |
|--------|------|-------------|
| date | index | Business day |
| regime_name | str | Low-Vol / Moderate / High-Vol |
| regime_id | int | 0, 1, 2 |
| prob_0 | float | P(regime=0 \| x_{1:t}) filtered |
| prob_1 | float | P(regime=1 \| x_{1:t}) filtered |
| prob_2 | float | P(regime=2 \| x_{1:t}) filtered |
| confidence | float | max(prob_k) |
| VIX | float | Raw VIX close |
| SPY_close | float | SPY close |
| garch_var_5 | float | GARCH-conditional 5% VaR |
| garch_var_1 | float | GARCH-conditional 1% VaR |

**What to add in Plan 07-03:**

| New column | Description | Research use |
|------------|-------------|--------------|
| `days_in_regime` | Consecutive days in current regime | Transition predictor input |
| `regime_entropy` | -Σ p_k log(p_k) | Uncertainty measure |
| `garch_vol_forecast` | σ̂_t from GARCH(1,1) | Vol targeting input |
| `blended_vol_forecast` | Σ_k P(Z_t=k) · σ̂_{k,t} | **Research Phase 9 output slot** |
| `transition_score` | placeholder NaN | **Research Phase 11 output slot** |
| `structural_anomaly` | placeholder NaN | **Research Phase 12 output slot** |

**Why placeholder columns:** They are `NaN` until the corresponding research phase implements them. Downstream consumers see the column immediately and can handle NaN gracefully. No schema change needed when phases 9–12 activate.

**Tests to add:**
- `test_regime_results_schema.py` — assert all columns exist, correct dtypes, no missing dates
- `test_regime_results_freshness.py` — today's date is the last row after a run

---

## Extension Points — Deliberately Designed Into Phase 7

The following seams are created during Phase 7 so that research phases bolt on without refactoring:

### Extension Point 1: Vol Forecast Blending (Research Phase 9)
**Where:** After `garch` stage, before `signals` stage  
**Contract:** Stage reads `data/regime_results.csv` (with per-regime GARCH params), writes `blended_vol_forecast` column  
**Files to add later:** `src/core/vol_forecast.py` → `blend_vol_forecasts(regime_probs, garch_params) → pd.Series`  
**How Phase 7 enables it:** `garch` stage writes per-regime GARCH params to `data/garch_params.json`, readable by vol_forecast stage later

---

### Extension Point 2: Strategy Backtester (Research Phase 10)
**Where:** Standalone script, reads `regime_results.csv`, `market_data.csv`  
**Contract:** `scripts/research/backtest_strategy.py --strategy tactical_allocation --cost 0.0005 --lag 1`  
**Files to add later:** `src/backtest/strategy.py`, `src/backtest/metrics.py`  
**How Phase 7 enables it:** `regime_results.csv` schema is stable and documented; `days_in_regime` column available for position logic; GARCH vol forecast column available for vol-targeting

---

### Extension Point 3: Transition Predictor (Research Phase 11)
**Where:** After `signals` stage  
**Contract:** Reads `regime_results.csv` + `features_transformed.csv`, writes `transition_score` column  
**Files to add later:** `src/signals/transition_predictor.py` → `predict_transition(results, features) → pd.Series`  
**How Phase 7 enables it:** `days_in_regime` column in schema; walk-forward OOS labels saved separately as `data/oos_regime_labels.csv` for training the classifier

---

### Extension Point 4: Structural Anomaly Layer (Research Phase 12, conditional)
**Where:** After `signals` stage  
**Contract:** Reads per-asset rolling windows, writes `structural_anomaly` column  
**Files to add later:** `src/signals/anomaly.py` → `score_structural_anomaly(market, regime_labels) → pd.Series`  
**How Phase 7 enables it:** `structural_anomaly` column placeholder in schema; market_data.csv contains all needed asset series

---

## Research Phase Sequence (Post Phase 7)

```
Phase 7   — Pipeline completion (this document)
              → Operational finish line for v1.1
              → Extension points created

Phase 8   — HDP-HMM Inference Optimization (already planned)
              → joblib parallelization of walk-forward folds
              → ELBO early stopping
              → Goal: 4hr → <90min

Phase 9   — Regime-Weighted GARCH Vol Forecast  [Research Path 1]
              → src/core/vol_forecast.py
              → Blend per-regime GARCH using filtered probs
              → Validate: QLIKE vs. single-GARCH OOS
              → Gate: must beat single GARCH on QLIKE OOS
              → Activates blended_vol_forecast column in regime_results.csv

Phase 10  — Strategy Backtester + Tactical Allocation  [Research Path 2, CRITICAL]
              → src/backtest/strategy.py + src/backtest/metrics.py
              → Walk-forward tactical SPY/TLT allocation using regime signal
              → Costs: 5–10bp, 1-day lag
              → Gate: must beat buy-and-hold Sharpe OOS after costs
              → If no edge → document honestly, HMM is risk tool only

Phase 11  — Transition Early Warning  [Research Path 3, conditional]
              → src/signals/transition_predictor.py
              → Only if Phase 10 shows timing is the binding constraint
              → Logistic regression only (no trees), walk-forward CV
              → Gate: Brier score must beat HMM transition matrix baseline

Phase 12+ — Structural Anomaly / Graph Features  [conditional on Phase 11]
              → Only if Phase 11 leaves unexplained residual
              → Visibility-graph features from rolling return windows
              → Must show incremental AUC over VIX + NFCI + eigen_conc
```

---

## What Must NOT Be Added During Phase 7

- No alpha logic in `regime_results.csv` (placeholder columns are NaN — not computed)
- No backtesting code inside `train.py` or `signals.py`
- No new features added to the HMM training (feature set is locked at Phase 5 selection)
- No graph or TDA code — premature

---

## Files Touched in Phase 7

**Created:**
- `src/pipeline/__init__.py`
- `src/pipeline/stages.py`
- `src/pipeline/runner.py`
- `scripts/cron_run.sh`
- `scripts/health_check.py`
- `data/garch_params.json` (written by garch stage, read by Phase 9)
- `data/oos_regime_labels.csv` (written by walk-forward stage, read by Phase 11)

**Modified:**
- `scripts/run.py` — delegates to `Pipeline.run_all()`
- `scripts/pipelines/train.py` — refactored into discrete stage functions
- `src/signals/signals.py` — adds `days_in_regime`, `regime_entropy` computation
- `data/regime_results.csv` — schema extended with new + placeholder columns

**Not touched:**
- `src/core/hdp_hmm.py` — model is locked
- `src/core/inference.py` — filtering logic is locked
- `src/features/features.py` — feature set is locked
- `tests/` — existing tests unchanged; new tests added only

---

## How to Execute

```bash
# Start Phase 7
/gsd-plan-phase 7

# After Phase 7 complete — verify
python scripts/run.py            # Should finish in <10 min
python scripts/health_check.py   # Should print PASS
ls figures/                      # Should show exactly 2 HTML files

# Then continue
/gsd-plan-phase 8                # Inference optimization
# After Phase 8 — research begins
/gsd-plan-phase 9                # Vol forecast blending
```

---

*Read alongside RESEARCH-STRATEGY.md. Phase 7 is operational; Phases 9–12 are research. The distinction matters — do not mix them.*
