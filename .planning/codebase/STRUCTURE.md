# Codebase Structure

**Analysis Date:** 2026-07-21

## Directory Layout

```
regime-detection/
├── src/                        # All importable Python package code
│   ├── config.py               # Single source of truth for all parameters
│   ├── data/                   # Data collection subpackage
│   │   └── collect_macro.py    # yfinance + FRED fetch, causal alignment
│   ├── core/                   # Model, causal inference, evaluation, OOS validation
│   │   ├── hdp_hmm.py          # NumPyro Bayesian HDP-HMM
│   │   ├── inference.py        # expanding_standardize, expanding_regime_vol
│   │   ├── evaluation.py       # regime_stats, vol_target_backtest
│   │   └── walk_forward.py     # anchored/rolling walk-forward OOS validation
│   ├── baselines/              # Comparison models (null hypotheses)
│   │   ├── threshold_rules.py  # VIX-threshold baseline
│   │   └── parametric_hmm.py   # Fixed-K Gaussian HMM baseline (hmmlearn)
│   └── pipeline/               # Stage orchestration
│       └── stages.py           # 5 stage functions + STAGES registry
├── scripts/                    # CLI entry points and utility scripts
│   ├── run.py                  # CLI wrapper (collect/features/train/.../walk_forward)
│   └── generate_figures.py     # Paper figure generation (reads results/, writes paper/figures/)
├── tests/                      # pytest suite
│   ├── test_causality_invariants.py  # No-lookahead perturbation checks
│   └── test_cli_runner.py            # CLI smoke test + VIX classifier unit test
├── run_paper_experiments.py    # Root-level: full in-sample paper pipeline (one script)
├── data/                       # Generated data (partially git-tracked, see Special Directories)
│   ├── processed/              # spx_data.csv, features*.csv, train/test splits
│   ├── regime_results.csv      # In-sample HDP regime labels (train stage output)
│   └── oos_regime_labels*.csv  # Walk-forward OOS ensemble + per-window raw outputs
├── models/                     # Generated model artifacts (hdp_checkpoint.pkl, hdp_params.pkl, etc.)
├── results/                    # Generated: paper tables/macros (.tex), regime_labels_train.csv,
│                                #   transition_matrix.csv, run_log.txt
├── figures/                    # Generated: dashboard.html, feature_analysis.html, diagnostics PNG
├── paper/                      # Paper source: paper.tex, references.bib, figures/*.pdf
├── paper_overleaf.zip          # Upload-ready bundle for Overleaf (paper.tex + figures + results)
├── logs/                       # Generated: pipeline/cron run logs
├── reports/                    # Generated: fragmentation diagnostic reports
├── .planning/                  # GSD-managed planning docs + codebase map (this directory)
├── .github/workflows/tests.yml # CI (workflow_dispatch only; references stale pre-refactor test files)
├── src/config.py               # (see above — referenced here for emphasis: read this first)
├── requirements.txt             # Exact-pinned dependencies (JAX/NumPyro pinning enforced by CI)
├── CLAUDE.md                   # Claude Code operating context (read first)
├── NOTES.md                    # Session-to-session state (read first, per CLAUDE.md)
└── .env                        # FRED_API_KEY (not committed; see .gitignore)
```

## Directory Purposes

**`src/`:**
- Purpose: all importable, reusable Python logic — the actual "library" of this project
- Contains: 4 subpackages (`data`, `core`, `baselines`, `pipeline`) plus `config.py` at the top level
- Key files: `src/config.py` (params), `src/core/hdp_hmm.py` (the model)

**`src/data/`:**
- Purpose: fetch and causally align raw feature data from external sources
- Contains: `collect_macro.py` (yfinance + FRED), empty `__init__.py` (docstring references a non-existent `src/features/collect.py` sibling — stale comment, harmless)
- Key files: `src/data/collect_macro.py::fetch_and_save_data()`

**`src/core/`:**
- Purpose: the model itself, causal transforms, and shared evaluation/validation math
- Contains: `hdp_hmm.py`, `inference.py`, `evaluation.py`, `walk_forward.py`
- Key files: `hdp_hmm.py` (model + decoding), `walk_forward.py` (OOS validation, added 2026-07-21), `evaluation.py` (recreated 2026-07-21 with new content — unrelated to a pre-refactor file of the same name that was deleted during the May 2026 stripping)

**`src/baselines/`:**
- Purpose: the two "null hypothesis" comparison models the paper's claims are measured against
- Contains: `threshold_rules.py`, `parametric_hmm.py`
- Key files: both — always read together with `src/core/hdp_hmm.py::label_regimes_hdp` when reasoning about regime-labeling logic

**`src/pipeline/`:**
- Purpose: wire the stages above into an ordered, resumable, CLI-drivable sequence
- Contains: `stages.py` (5 stage functions, `STAGES` registry — order is a documented invariant), empty `__init__.py`
- Key files: `src/pipeline/stages.py`

**`scripts/`:**
- Purpose: user-facing entry points that are not themselves library code
- Contains: `run.py` (CLI), `generate_figures.py` (plotting only, no retraining)
- Key files: `scripts/run.py` — the primary operational entry point consumed by downstream systems (Portfolio-Manager)

**`tests/`:**
- Purpose: pytest suite — currently causality invariants and a CLI smoke test only
- Contains: `test_causality_invariants.py`, `test_cli_runner.py`
- Key files: both; no `conftest.py` — each test file inserts repo root onto `sys.path` manually

**`data/`:**
- Purpose: generated data artifacts (raw fetched series, engineered features, regime label outputs)
- Contains: `data/processed/` (raw + engineered CSVs), `data/regime_results.csv` (in-sample), `data/oos_regime_labels.csv` + per-window variants (`_rolling5y`, `_rolling3y`)
- Generated: Yes (regenerable via `scripts/run.py` or `run_paper_experiments.py`)
- Committed: Partially — `.gitignore` does not exclude `data/processed/*.csv` or `models/*.pkl`; NOTES.md and the hub doc flag this as unresolved git bloat

**`models/`:**
- Purpose: fitted model artifacts (posterior params, samples, metadata)
- Contains: `hdp_checkpoint.pkl`, `hdp_params.pkl`, `hdp_samples.pkl`, `hdp_metadata.json` (written by `save_hdp_results()`)
- Generated: Yes
- Committed: Yes (same bloat concern as `data/`)

**`results/`:**
- Purpose: paper-facing outputs from `run_paper_experiments.py`
- Contains: `paper_results.txt` (full legacy combined output), `paper_macros.tex` (preamble `\newcommand`s), `paper_tables.tex` (Tables 1-5 environments), `paper_desc_stats.tex` (Table 0), `regime_labels_train.csv`, `transition_matrix.csv`, `run_log.txt`
- Generated: Yes (`python run_paper_experiments.py`)
- Committed: Yes

**`figures/`:**
- Purpose: HTML dashboard/analysis views (from `scripts/run.py`) and diagnostic images
- Contains: `dashboard.html`, `feature_analysis.html` (both explicitly untracked per `.gitignore`), `day1_hdp_diagnostics.png` (committed)
- Generated: Yes
- Committed: Partially (see `.gitignore` entries for `figures/dashboard.html` and `figures/feature_analysis.html`)

**`paper/`:**
- Purpose: LaTeX paper source and its 4 publication PDFs
- Contains: `paper.tex`, `references.bib`, `README-overleaf.md`, `figures/*.pdf`
- Generated: `figures/*.pdf` yes (via `scripts/generate_figures.py`); `paper.tex`/`references.bib` no (hand-edited)
- Committed: Yes

**`logs/` / `reports/`:**
- Purpose: run logs (`logs/pipeline.log`, `logs/cron_run.log`) and one-off diagnostic reports (`reports/fragmentation_report.txt`)
- Generated: Yes
- Committed: Yes (not gitignored)

**`.planning/`:**
- Purpose: GSD-managed planning documents and this codebase map
- Contains: `codebase/` (this directory), `regime-detection Planning.md`, `DEEP-REVIEW.md`
- Note: per the project hub doc, this project is "not GSD-managed in the usual sense" — no `STATE.md`/`ROADMAP.md`, just a planning doc and codebase snapshot

## Key File Locations

**Entry Points:**
- `run_paper_experiments.py`: full in-sample paper pipeline (collect → features → HDP-HMM → baselines → LaTeX tables)
- `scripts/run.py`: operational CLI (subcommands `collect`, `features`, `train`, `signals`, `dashboard`, `regime`, `trust`, `analyze`, `walk_forward`; `--validate` flag)
- `scripts/generate_figures.py`: figure generation only, no retraining

**Configuration:**
- `src/config.py`: all parameters (dates, tickers, FRED series, HDP/SVI/MCMC settings, `VOL_BRACKETS`, `WALK_FORWARD_WINDOW_DAYS`)
- `.env`: `FRED_API_KEY` (required, not committed)
- `requirements.txt`: exact-pinned dependencies

**Core Logic:**
- `src/core/hdp_hmm.py`: the Bayesian HDP-HMM model, inference, decoding, labeling
- `src/core/inference.py`: causal standardization and per-regime vol estimators
- `src/core/evaluation.py`: shared within-regime stats and vol-target backtest math
- `src/core/walk_forward.py`: walk-forward OOS fold loop + multi-window ensemble
- `src/pipeline/stages.py`: stage functions wiring everything into a pipeline

**Testing:**
- `tests/test_causality_invariants.py`: perturbation-based no-lookahead checks
- `tests/test_cli_runner.py`: CLI smoke test + VIX-threshold classifier unit test
- Run via `pytest tests/ -v` (per NOTES.md) — `.github/workflows/tests.yml` is stale (references deleted test files, `workflow_dispatch` only, not run on push/PR)

## Naming Conventions

**Files:**
- Snake_case throughout (`collect_macro.py`, `parametric_hmm.py`, `walk_forward.py`) — standard Python module naming
- Module names describe the concept they implement, not a generic "utils"/"helpers" catch-all (only exception: none found — every `src/` file has a specific single responsibility)

**Directories:**
- Lowercase, singular-concept nouns (`data`, `core`, `baselines`, `pipeline`) — a subpackage per architectural layer, not per feature

**Functions:**
- Verb-first for actions (`fetch_and_save_data`, `fit_hdp_hmm`, `apply_threshold_rules`, `expanding_standardize`)
- `stage_*` prefix specifically for pipeline stage functions registered in `STAGES` (`stage_collect`, `stage_features`, `stage_train_hmm`, `stage_signals`, `stage_walk_forward`)
- Private/internal helpers prefixed with a single underscore (`_fit_svi`, `_fit_nuts`, `_logsumexp`, `_apply_hysteresis`, `_svi_diagnostics`)

**Config constants:**
- ALL_CAPS in `src/config.py` (`RANDOM_SEED`, `HDP_TRUNCATION`, `VOL_BRACKETS`, `WALK_FORWARD_WINDOW_DAYS`)

## Where to Add New Code

**New feature/data source:**
- Fetch logic: `src/data/` (new module alongside `collect_macro.py`, or extend it if it's another FRED/yfinance series)
- Add to `FEATURES` list and any new tickers/series constants in `src/config.py`
- Note: `CLAUDE.md` hard-constrains the feature set to the current 4 (`spy_ret`, `vol_index`, `yield_slope`, `nfci`) without re-running the paper's ablation — confirm with the user before adding a 5th feature

**New baseline model:**
- Implementation: `src/baselines/` (new module, following `threshold_rules.py`/`parametric_hmm.py`'s pattern: a `fit_*`/`apply_*` function, a `get_filtered_states`-equivalent causal decoder, and a `relabel_by_*` VIX-rank or vol-bracket mapper)
- Wire into `run_paper_experiments.py`'s baseline section and `src/core/evaluation.py::regime_stats` call sites

**New pipeline stage:**
- Implementation: add a `stage_*` function to `src/pipeline/stages.py`, then add it to the `STAGES` list — order is documented as "LOCKED", so insertions must preserve the existing `collect → features → train_hmm → signals → walk_forward` sequence unless deliberately changing it
- Expose via a new subcommand in `scripts/run.py`'s `command_map`

**New causal/evaluation utility:**
- Causal transforms (no-lookahead time-series functions): `src/core/inference.py`
- Shared stats/backtest math used by both in-sample and OOS code: `src/core/evaluation.py`
- Any new function claiming causality must get a corresponding perturbation test in `tests/test_causality_invariants.py` (project convention, not yet enforced by CI)

**Utilities:**
- No generic `utils.py`/`helpers.py` exists — new shared helpers should go into the most specific existing module (`src/core/inference.py` for causal math, `src/core/evaluation.py` for stats) rather than a new catch-all file

**Tests:**
- `tests/` — no fixtures/conftest directory yet; each test file adds repo root to `sys.path` manually at the top (see both existing test files for the exact pattern)

## Special Directories

**`data/`, `models/`, `results/`, `figures/`, `paper/figures/`:**
- Purpose: generated artifacts from running the pipeline/paper scripts
- Generated: Yes
- Committed: Yes, except `figures/dashboard.html` and `figures/feature_analysis.html` (explicitly gitignored) — NOTES.md flags `data/processed/*.csv` and `models/*.pkl` as committed-but-regenerable git bloat that `.gitignore` does not yet cover

**`.venv/`:**
- Purpose: local Python virtual environment (not yet created per `C:\dev\CLAUDE.md`'s repo table, though `.venv/Scripts/python.exe` exists on disk at analysis time)
- Generated: Yes
- Committed: No (`.gitignore`)

**`__pycache__/` (multiple, under `src/` and root):**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No (`.gitignore`)

---

*Structure analysis: 2026-07-21*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
