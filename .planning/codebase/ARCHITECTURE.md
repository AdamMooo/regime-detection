<!-- refreshed: 2026-07-21 -->
# Architecture

**Analysis Date:** 2026-07-21

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    Entry Points (root / scripts /)                  │
├───────────────────────┬───────────────────────┬─────────────────────┤
│ run_paper_experiments  │  scripts/run.py       │ scripts/generate_   │
│ .py (in-sample paper   │  (CLI: collect/       │ figures.py          │
│ pipeline, one script)  │  features/train/...)  │ (paper PDFs)        │
└───────────┬───────────┴───────────┬───────────┴─────────────────────┘
            │                       │
            ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Pipeline Stages  `src/pipeline/stages.py`           │
│   collect -> features -> train_hmm -> signals -> walk_forward       │
│   (STAGES registry; each stage is a stateless disk-to-disk function)│
└───────────┬───────────────────────────────────────────┬─────────────┘
            │                                            │
            ▼                                            ▼
┌───────────────────────────────┐        ┌──────────────────────────────┐
│  Data Collection               │        │  Core Model + Inference       │
│  `src/data/collect_macro.py`   │        │  `src/core/hdp_hmm.py`        │
│  (yfinance SPY/VIX + FRED      │        │  `src/core/inference.py`      │
│   T10Y2Y/NFCI, causal align)   │        │  `src/core/evaluation.py`     │
│                                 │        │  `src/core/walk_forward.py`   │
└───────────┬─────────────────────┘        └──────────────┬────────────┘
            │                                              │
            ▼                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Baselines (null hypotheses)                    │
│  `src/baselines/threshold_rules.py`  (VIX-threshold — the null)      │
│  `src/baselines/parametric_hmm.py`   (fixed-K Gaussian HMM, hmmlearn)│
└───────────┬───────────────────────────────────────────┬─────────────┘
            │                                            │
            ▼                                            ▼
┌───────────────────────────────┐        ┌──────────────────────────────┐
│  Config (single source of      │        │  Outputs                     │
│  truth) `src/config.py`        │        │  `data/`, `models/`,          │
│                                 │        │  `results/`, `figures/`,      │
│                                 │        │  `paper/figures/`             │
└─────────────────────────────────────────┴──────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Config | All tunable parameters (dates, tickers, HDP hyperparams, vol brackets, walk-forward window list) | `src/config.py` |
| Data collection | Fetch SPY return, VIX, FRED yield slope, FRED NFCI; causal publication-lag alignment; writes `data/processed/spx_data.csv` | `src/data/collect_macro.py` |
| HDP-HMM model | NumPyro sticky HDP-HMM (stick-breaking prior, Gaussian emissions), SVI/NUTS inference, forward-backward decoding, state pruning/merging, regime labeling | `src/core/hdp_hmm.py` |
| Causal inference utilities | Expanding-window z-score standardization; expanding per-regime volatility estimate (both strictly no-lookahead) | `src/core/inference.py` |
| Shared evaluation | `regime_stats()` (within-regime N/return/vol/Sharpe/dwell) and `vol_target_backtest()`, shared between in-sample paper tables and OOS validation | `src/core/evaluation.py` |
| Walk-forward OOS | Anchored/rolling-window walk-forward validation: periodic refit + forward-only filtering on new blocks; multi-window ensemble with majority vote | `src/core/walk_forward.py` |
| Threshold baseline | VIX-threshold regime rule — the null hypothesis the paper argues against | `src/baselines/threshold_rules.py` |
| Parametric HMM baseline | Fixed-K=3 Gaussian HMM (hmmlearn), causal forward-only filtering (not hmmlearn's smoothed default) | `src/baselines/parametric_hmm.py` |
| Pipeline stages | Stateless disk-to-disk stage functions (`stage_collect`, `stage_features`, `stage_train_hmm`, `stage_signals`, `stage_walk_forward`) plus the locked `STAGES` registry | `src/pipeline/stages.py` |
| CLI wrapper | `scripts/run.py` — subcommands (`collect`, `features`, `train`, `signals`, `dashboard`, `regime`, `trust`, `analyze`, `walk_forward`); prefers real stage functions, falls back to cached artifacts when the environment lacks FRED access | `scripts/run.py` |
| Paper experiment runner | End-to-end script: collect → features → HDP-HMM → baselines → LaTeX tables/macros → CSV intermediates for figures | `run_paper_experiments.py` (repo root) |
| Figure generation | Reads `results/regime_labels_train.csv` + `results/transition_matrix.csv`, writes 4 publication PDFs to `paper/figures/` | `scripts/generate_figures.py` |

## Pattern Overview

**Overall:** Script/pipeline pattern for a research + light-production system, not a service. There is no persistent process, API server, or database — everything is disk-to-disk batch computation triggered by running a Python script or CLI command.

**Key Characteristics:**
- Two parallel "front doors" into the same core logic: `run_paper_experiments.py` (monolithic script for paper artifacts) and `scripts/run.py` (modular CLI wrapping `src/pipeline/stages.py` for operational/downstream use). Both ultimately call the same `src/core/` and `src/data/` functions — no logic duplication in the model itself, only in orchestration.
- Causal-by-construction data flow: every function that touches time series is either explicitly "expanding" (uses only past+current data) or explicitly labeled otherwise (e.g. `smoothed` in `forward_backward_numpy`). This causality boundary is enforced by dedicated invariant tests, not just convention.
- Config-driven: `src/config.py` is the single source of truth for feature list, date ranges, HDP hyperparameter priors (only inference settings — `alpha_trans`/`kappa` themselves are Bayesian latents, not config constants), vol brackets, and walk-forward window list.
- Bayesian nonparametric model with a truncated approximation (`HDP_TRUNCATION = 8` max raw states), followed by a deterministic post-processing pipeline (`prune_states` → `merge_similar_states`/VIX-rank merge → `label_regimes_hdp` or `merge_states_to_regimes`) to collapse to human-interpretable regimes.
- Fallback-first CLI (`scripts/run.py`): every subcommand tries the real computation first, then falls back to previously cached CSVs/pickles or a last-resort live VIX-threshold read — so downstream consumers (Portfolio-Manager) always get *some* answer even if FRED/yfinance/training fails.

## Layers

**Configuration layer:**
- Purpose: centralize every tunable constant
- Location: `src/config.py`
- Contains: dates, tickers, FRED series IDs, feature list, HDP/SVI/MCMC hyperparameters, walk-forward settings, vol brackets, output directory names
- Depends on: nothing (leaf module, only imports `os`)
- Used by: every other `src/` module and both entry-point scripts

**Data layer:**
- Purpose: fetch and causally align raw macro/market series
- Location: `src/data/collect_macro.py` (package: `src/data/`)
- Contains: yfinance + FRED (`fredapi`) fetch logic, publication-lag shifting (NFCI +7 days), train/test CSV splits
- Depends on: `src/config.py`, `.env` (`FRED_API_KEY`)
- Used by: `run_paper_experiments.py`, `src/pipeline/stages.py::stage_collect`

**Core model/inference layer:**
- Purpose: the Bayesian HDP-HMM itself, causal transforms, shared evaluation math, OOS validation
- Location: `src/core/` (`hdp_hmm.py`, `inference.py`, `evaluation.py`, `walk_forward.py`)
- Contains: NumPyro model definition, SVI/NUTS fit functions, forward-backward decoding, state pruning/merging/labeling, `expanding_standardize`/`expanding_regime_vol`, `regime_stats`/`vol_target_backtest`, walk-forward fold loop + ensemble
- Depends on: `src/config.py`; `jax`/`numpyro` (hdp_hmm.py); numpy/pandas only (inference.py, evaluation.py)
- Used by: `run_paper_experiments.py`, `src/pipeline/stages.py`, `src/core/walk_forward.py`

**Baselines layer:**
- Purpose: the two comparison models the paper's claims are measured against
- Location: `src/baselines/`
- Contains: `threshold_rules.py` (VIX thresholds), `parametric_hmm.py` (fixed-K Gaussian HMM with causal forward-only filtering, wrapping hmmlearn)
- Depends on: `src/config.py`; hmmlearn, scipy, sklearn
- Used by: `run_paper_experiments.py`; `parametric_hmm.py`'s `get_filtered_states` is also directly imported by `tests/test_causality_invariants.py`

**Pipeline/orchestration layer:**
- Purpose: wire the layers above into a repeatable, resumable, CLI-drivable sequence
- Location: `src/pipeline/stages.py`, `scripts/run.py`
- Contains: 5 named stage functions + `STAGES` registry (order is a documented invariant — "LOCKED"); CLI argument parsing, cached-artifact fallback logic, dashboard/analyze HTML generation
- Depends on: everything above
- Used by: `run_paper_experiments.py` reuses `stage_features`; `scripts/run.py` is the operational entry point for downstream consumers (Portfolio-Manager)

**Paper/reporting layer:**
- Purpose: produce publication artifacts
- Location: `run_paper_experiments.py` (root), `scripts/generate_figures.py`, `paper/`
- Contains: LaTeX table/macro generation (`results/*.tex`), 4 PDF figures, `paper/paper.tex` source, `paper_overleaf.zip` bundle
- Depends on: `results/regime_labels_train.csv`, `results/transition_matrix.csv` (both written by `run_paper_experiments.py`)
- Used by: nothing downstream — terminal output for the academic-paper goal

## Data Flow

### Primary Path — Operational CLI (`scripts/run.py`)

1. `collect` — fetch SPY/VIX/FRED series, write `data/processed/spx_data.csv` (`src/pipeline/stages.py:26` → `src/data/collect_macro.py:38`)
2. `features` — expanding-standardize the 4 features (causal z-score), split train/test by `TRAIN_END`, write `data/processed/features*.csv` (`src/pipeline/stages.py:38` → `src/core/inference.py:14`)
3. `train` — fit HDP-HMM via SVI on `features_train.csv`, prune/label states, write `models/hdp_*.pkl` + `data/regime_results.csv` (`src/pipeline/stages.py:81` → `src/core/hdp_hmm.py:137`)
4. `signals` — enrich `regime_results.csv` with `days_in_regime` (streak count) and `regime_entropy` (from filtered probabilities) (`src/pipeline/stages.py:141`)
5. `walk_forward` (gated by `--validate`) — refit periodically across 3 training-window configs, forward-filter each new out-of-sample block, ensemble via majority vote + agreement fraction, write `data/oos_regime_labels.csv` (`src/pipeline/stages.py:175` → `src/core/walk_forward.py:47,139`)
6. `regime` / `trust` — read the latest label from OOS output (preferred) or cached/paper results, with live-VIX-threshold as the last-resort fallback (`scripts/run.py:43`)

### Secondary Path — Paper Pipeline (`run_paper_experiments.py`)

1. Collect data (`fetch_and_save_data`)
2. `stage_features` (reused from pipeline layer) — expanding standardize + train/test split
3. Fit HDP-HMM (SVI, 4000 steps) on the full training window, prune to active states, merge to 3 canonical regimes by VIX rank (`min(int(i*3/K_eff), 2)`, asserts `K_eff >= 3`)
4. Fit VIX-threshold baseline and parametric HMM baseline on the same training window
5. Compute `regime_stats()` (Table 1), empirical transition matrix (Table 2), information-content regression (Table 3), and 4-strategy vol-target backtest (Table 4) using `src/core/evaluation.py` + `src/core/inference.py::expanding_regime_vol`
6. Write `results/regime_labels_train.csv`, `results/transition_matrix.csv`, `results/paper_*.tex`

### Walk-Forward OOS Fold Loop (`src/core/walk_forward.py::walk_forward_oos`)

1. For each fold (every `WALK_FORWARD_REFIT_DAYS` = 63 trading days past `TRAIN_END`): slice training window (expanding, or trailing `window_days` if rolling), refit HDP-HMM with a fold-specific seed
2. Compute training-window active states, rank by mean VIX, build `state_to_regime` map (must be redone per fold — SVI state indices aren't stable across independent fits)
3. Forward-filter (never smooth) the concatenated train+block window, take only the new block's rows — causal by construction
4. Fold the realized block into the training window before the next iteration (`window_end = block_index[-1]`)
5. `ensemble_oos()` combines multiple fold-loop runs (different `window_days` configs) into a majority-vote label + `agreement_frac`

**State Management:**
- No in-memory server state; all state is CSV/pickle files on disk (`data/`, `models/`, `results/`). Every pipeline stage reads its inputs from disk and writes its outputs to disk — this is what makes stages independently resumable/cacheable.
- `scripts/run.py`'s CLI functions each check for a cached artifact before recomputing (`_cached_spx_data()`, `_cached_features()`, `_cached_results()`), making the CLI idempotent and safe to fall back to prior runs when live data fetch fails.

## Key Abstractions

**Regime label (3-way):**
- Purpose: canonical output type consumed by every downstream system — always one of `Low-Vol` / `Moderate-Vol` / `High-Vol`
- Examples: `src/core/hdp_hmm.py::label_regimes_hdp`, `src/core/walk_forward.py::REGIME_NAMES`, `src/baselines/parametric_hmm.py::relabel_by_vix`, `scripts/run.py::classify_regime_from_vix`
- Pattern: raw HDP states (up to `HDP_TRUNCATION`=8) are always collapsed to exactly 3 named regimes before leaving `src/core/` or `src/baselines/` — either by absolute realized-vol bracket (`VOL_BRACKETS`, in-sample training) or by VIX-rank partition into thirds (walk-forward folds, where a stable absolute bracket per fold isn't guaranteed)

**Causal ("no lookahead") function:**
- Purpose: any function computing a per-timestep quantity from a time series must guarantee row t only depends on rows `<= t` (or `< t` where the row's own outcome is being predicted)
- Examples: `expanding_standardize`, `expanding_regime_vol` (`src/core/inference.py`), `get_filtered_states` (`src/baselines/parametric_hmm.py`), the `filtered` (not `smoothed`) output of `forward_backward_numpy` (`src/core/hdp_hmm.py`)
- Pattern: implemented via `np.cumsum`/running accumulators or `jax.lax.scan`-based forward-only recursion — never `.rolling()` without `.shift(1)`, never backward-pass smoothing for anything claiming causality. Enforced by `tests/test_causality_invariants.py`'s perturb-and-check pattern.

**Params dict (posterior-mean model state):**
- Purpose: portable, JSON/pickle-serializable representation of a fitted HDP-HMM's posterior-mean parameters, decoupled from the NumPyro/JAX runtime objects
- Examples: `posterior_mean_params()` return value in `src/core/hdp_hmm.py`, consumed by `forward_backward_numpy`, `prune_states`, `get_labels_and_probs`, `get_transition_matrix`, and `HDPModelAdapter`
- Pattern: plain dict with keys `beta`, `trans_matrix`, `init_probs`, `locs`, `scale_diag`, `K_max` — every downstream function takes this dict, not the raw `samples` or `svi_result`/`mcmc` object

**HDPModelAdapter:**
- Purpose: give HDP-HMM results the same `.predict()`/`.predict_proba()`/`.transmat_`/`.means_` interface as hmmlearn's `GaussianHMM`, for code that wants to treat both models polymorphically
- Examples: `src/core/hdp_hmm.py:762`
- Pattern: thin wrapper class over the params dict + precomputed labels/filtered-probs

## Entry Points

**`run_paper_experiments.py` (repo root):**
- Location: repo root, run as `python run_paper_experiments.py`
- Triggers: manual invocation when regenerating paper numbers/figures-source
- Responsibilities: full in-sample pipeline — collect → features → HDP-HMM (SVI) → both baselines → Tables 0-4 → `results/*.csv`, `results/*.tex`; writes `results/run_log.txt`

**`scripts/run.py` (CLI):**
- Location: `scripts/run.py`, run as `python scripts/run.py [command] [--validate]`
- Triggers: manual invocation, or downstream consumers (Portfolio-Manager) needing the current regime label
- Responsibilities: subcommands `collect`/`features`/`train`/`signals`/`dashboard`/`regime`/`trust`/`analyze`/`walk_forward`; no-argument invocation runs the full non-validate sequence; each subcommand prefers real computation, falls back to cached/paper artifacts or (last resort) a live VIX-threshold read

**`scripts/generate_figures.py`:**
- Location: `scripts/generate_figures.py`, run as `python scripts/generate_figures.py`
- Triggers: manual invocation after `run_paper_experiments.py` has refreshed `results/regime_labels_train.csv`
- Responsibilities: 4 publication PDFs to `paper/figures/` — no retraining, pure plotting from CSVs (~2s)

**`tests/` (pytest):**
- Location: `tests/test_causality_invariants.py`, `tests/test_cli_runner.py`
- Triggers: `pytest tests/ -v` (manual; `.github/workflows/tests.yml` is `workflow_dispatch`-only — not on push/PR — and its steps reference test files and analysis scripts that no longer exist in this repo, e.g. `tests/test_causality.py`, `analyze_feature_importance.py`; the CI config predates the May 2026 stripping refactor and is stale)
- Responsibilities: causality/no-lookahead invariant checks on the 4 functions that claim causal behavior; CLI smoke test + VIX-threshold classifier unit test

## Architectural Constraints

- **Threading/concurrency:** Single-threaded, synchronous, CPU-only. `jax.config.update("jax_platform_name", "cpu")` explicitly disables GPU search (`src/core/hdp_hmm.py:47`). No async, no multiprocessing, no job queue — every stage runs to completion before the next starts.
- **Global state:** No module-level singletons in `src/`. `run_paper_experiments.py` uses a module-level open `LOG` file handle (`results/run_log.txt`) written throughout the script — this is script-local, not shared across modules.
- **Circular imports:** None observed. Dependency direction is strictly `config -> data/core/baselines -> pipeline -> scripts/entry-points`. `src/core/walk_forward.py` imports from `src/core/hdp_hmm.py`; `src/pipeline/stages.py` imports from `src/core/`, `src/data/`, `src/config`. No back-references.
- **Reproducibility pinning:** `jax==0.9.1` and `numpyro==0.20.0` are pinned exactly in `requirements.txt` and enforced by `.github/workflows/tests.yml`'s `check-version-pins` job (fails CI if `>=` is used instead of `==`) — a hard project constraint per `CLAUDE.md`.
- **64-bit precision:** `jax.config.update("jax_enable_x64", True)` (`src/core/hdp_hmm.py:49`) — required for the forward algorithm's numerical stability; any new JAX code in this codebase must not silently rely on 32-bit defaults.
- **State-index instability across fits:** HDP state indices from independent SVI/NUTS fits are not comparable — every fold in `walk_forward_oos` must re-derive its own VIX-rank state→regime map; code must never assume "state 0 means the same thing" across two separate `fit_hdp_hmm` calls.

## Anti-Patterns

### Smoothed (backward-pass) output used where causality is claimed

**What happens:** `forward_backward_numpy` returns both `filtered` (forward-only) and `smoothed` (forward-backward) posteriors. Any code path that computes a "live" or "OOS" signal must use `filtered`, never `smoothed`.
**Why it's wrong:** `smoothed` uses future observations via the backward pass — using it for anything claiming real-time/causal validity silently reintroduces lookahead. This was exactly bug CR-03 in the 2026-07-20/21 deep review (`src/baselines/parametric_hmm.py`'s `get_filtered_states` was previously using hmmlearn's smoothed `score_samples()` output).
**Do this instead:** Use `forward_backward_numpy(...)[0]` (filtered) or `get_filtered_states()` for anything that will ever be scored on out-of-sample days; reserve `smoothed`/`score_samples()` strictly for in-sample descriptive analysis where lookahead is acceptable.

### Folding a value into a rolling/expanding statistic before computing that day's output

**What happens:** A causal per-timestep estimator (e.g. `expanding_regime_vol`) must compute `vol_series[t]` using only data from rows `< t` (same regime), *then* fold `returns[t]` into the running sums — not the reverse order.
**Why it's wrong:** Folding first (updating `sums[k]`/`counts[k]` with `returns[t]` before reading `vol_series[t]`) means day t's own realized return leaks into its own vol estimate, inflating any vol-targeting backtest that sizes positions off it. This was headline bug CR-04 — it inflated Table 4's HDP vol-target Sharpe from an honest 0.624 to a buggy 0.736.
**Do this instead:** Read the running statistic first, only then update it, as implemented in `expanding_regime_vol` (`src/core/inference.py:87-98`) — the loop reads `vol_series[t]` on lines 89-94 before updating `sums`/`sqsums`/`counts` on lines 96-98. `tests/test_causality_invariants.py::test_expanding_regime_vol_causal` checks index `t` itself is unaffected by a perturbation at `t`, not just indices `< t`.

## Error Handling

**Strategy:** Fail-loud in the modeling core (assertions on invariants that would silently corrupt results), fail-soft with fallback in the operational CLI (never block a downstream consumer from getting *some* answer).

**Patterns:**
- Hard `assert K_eff >= 3` in both `run_paper_experiments.py:117` and `src/core/walk_forward.py:34` (raises `ValueError` in the latter) — if HDP pruning collapses below 3 active states, the VIX-rank-partition-into-thirds merge would otherwise silently never assign "High-Vol". Fail loud rather than produce a mislabeled regime.
- `warnings.warn(...)` (not exceptions) for statistical convergence issues that don't invalidate the run but should be surfaced: SVI ELBO not converged (`src/core/hdp_hmm.py:179`), NUTS R-hat/ESS thresholds exceeded (`src/core/hdp_hmm.py:239-250`)
- `scripts/run.py`'s `run_collect`/`run_features`/`run_train` each wrap the real stage call in `try/except Exception`, falling back to a cached artifact (or the shipped `results/regime_labels_train.csv` for training) and only re-raising if no fallback exists — this is deliberate operational resilience for downstream consumers with no FRED key or no working training stack
- `os.environ.get('GSD_FORCE_STAGE_FAIL')` checks at the top of every `stage_*` function in `src/pipeline/stages.py` — a test-only hook to deterministically simulate a stage failure

## Cross-Cutting Concerns

**Logging:** Two parallel conventions — `run_paper_experiments.py` uses a hand-rolled `log()` helper that tees to stdout and `results/run_log.txt`; `src/pipeline/stages.py` uses the standard `logging` module (`logger = logging.getLogger('pipeline.stages')`). `scripts/run.py` uses plain `print()`. No unified logging config exists across the codebase.

**Validation:** Boundary validation only — e.g. `stage_features` checks required input files/columns exist before proceeding (`src/pipeline/stages.py:44-51`); no validation inside pure numerical helper functions (`expanding_standardize`, `regime_stats`, etc.) beyond what NumPy/pandas raise naturally.

**Authentication:** `FRED_API_KEY` read from `.env` via `python-dotenv` (`load_dotenv()` in `src/data/collect_macro.py:25`); raises `EnvironmentError` if unset or left as the placeholder value. No other auth in the codebase (yfinance requires none).

---

*Architecture analysis: 2026-07-21*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
