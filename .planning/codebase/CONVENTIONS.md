# Coding Conventions

**Analysis Date:** 2026-07-21

## Naming Patterns

**Files:**
- Lowercase snake_case throughout: `src/core/hdp_hmm.py`, `src/core/inference.py`, `src/data/collect_macro.py`, `src/baselines/threshold_rules.py`, `src/baselines/parametric_hmm.py`, `src/core/walk_forward.py`, `src/pipeline/stages.py`.
- Test files: `tests/test_<subject>.py` (e.g. `tests/test_causality_invariants.py`, `tests/test_cli_runner.py`).
- One-off top-level scripts use verb-first snake_case: `run_paper_experiments.py`, `scripts/run.py`, `scripts/generate_figures.py`.

**Functions:**
- snake_case, verb-first, descriptive of the causal contract where relevant: `expanding_standardize`, `expanding_regime_vol`, `get_filtered_states`, `forward_backward_numpy`, `fit_hdp_hmm`, `posterior_mean_params`, `walk_forward_oos`, `ensemble_oos`.
- Private/internal helpers prefixed with a single underscore: `_fit_svi`, `_fit_nuts`, `_logsumexp`, `_apply_hysteresis`, `_get_fred_api`, `_bumped` (test helper), `_toy_gaussian_hmm` (test fixture builder).
- Functions that assert or claim a "no lookahead" / causal property name that property directly in the docstring's first line (`src/core/inference.py:15`, `src/baselines/parametric_hmm.py:48-49`) — follow this pattern for any new causal function so `tests/test_causality_invariants.py` can be extended consistently.

**Variables:**
- Short, math-adjacent names mirror the paper's notation: `K_max`, `K_eff`, `T_len`, `D`, `beta`, `kappa`, `alpha_dp`, `alpha_trans`, `log_alpha`, `log_beta`, `log_lik`, `trans_matrix`. Acceptable specifically inside model/math code (`src/core/hdp_hmm.py`); do not extend this style to plumbing/CLI code, which uses ordinary descriptive names (`oos_path`, `regime_counts`, `feat_train`).
- Column/dict-key strings for regime labels are the literal strings `'Low-Vol'`, `'Moderate-Vol'`, `'High-Vol'` — never invent new label spellings; they are the fixed contract with downstream consumers (see `CLAUDE.md` "Downstream Integration").

**Types:**
- No classes for data structures — plain `dict` and `pandas.DataFrame` used everywhere for model params/results (e.g. `params = {'beta':..., 'trans_matrix':..., ...}` in `src/core/hdp_hmm.py:286-293`).
- One real class in the codebase: `HDPModelAdapter` (`src/core/hdp_hmm.py:762`), which exists solely to satisfy the `hmmlearn` `GaussianHMM` interface (`.predict`, `.predict_proba`, `.transmat_`, etc.) for code that expects that shape. Don't introduce other classes unless adapting to an external interface the same way.

## Code Style

**Formatting:**
- No formatter (no `black`/`ruff format` config found). Style is hand-maintained but consistent: single quotes for strings, aligned `=` signs in related constant blocks (`src/config.py:14-16`, `19-20`), section-divider comments using `# ---` or full-width `# ===...===` banners (`src/core/hdp_hmm.py:52-54`, `src/pipeline/stages.py:22-24`).
- Line length is informally ~90-100 chars; long f-strings and argument lists are wrapped manually with trailing commas.

**Linting:**
- No `.flake8`, `pyproject.toml`, `ruff.toml`, or `.pre-commit-config.yaml` present in the repo. No enforced linter — do not introduce one per the user's global "no linters/hooks unless there's concrete pain" preference.

## Import Organization

**Order (observed convention, not enforced by tooling):**
1. Standard library (`os`, `sys`, `time`, `json`, `warnings`, `logging`)
2. Third-party (`numpy`, `pandas`, `jax`, `numpyro`, `hmmlearn`, `scipy`, `sklearn`, `yfinance`)
3. Local `src.*` imports, always absolute (`from src.config import ...`, `from src.core.hdp_hmm import ...`) — never relative imports (no `from .config import`, no `from ..core import`).

**Path Aliases:**
- None. Modules doing standalone/CLI execution (`scripts/run.py`, `tests/test_cli_runner.py`) manually insert the repo root onto `sys.path` before importing `src`:
  ```python
  ROOT = Path(__file__).resolve().parents[1]
  if str(ROOT) not in sys.path:
      sys.path.insert(0, str(ROOT))
  ```
  Follow this exact pattern for any new standalone script or test that needs `src.*` imports outside a package context.
- Some functions do lazy/local imports inside function bodies to avoid heavy startup cost or circular imports, e.g. `from collections import Counter` inside `effective_K()` (`src/core/hdp_hmm.py:272`), `from scipy.stats import norm` inside `forward_backward_numpy()` (`src/core/hdp_hmm.py:308`), `from numpyro.diagnostics import summary` inside `_nuts_diagnostics()` (`src/core/hdp_hmm.py:229/576`). This is deliberate, not accidental — mirror it for expensive optional imports.

## Error Handling

**Patterns:**
- Fail fast with a specific exception type and an actionable message at config/data boundaries: `EnvironmentError` for missing `FRED_API_KEY` (`src/data/collect_macro.py:31-33`), `FileNotFoundError` for missing upstream pipeline artifacts (`src/pipeline/stages.py:45`, `88`, `147`), `ValueError` for missing required columns/features (`src/pipeline/stages.py:51`) or an invalid state count (`src/core/walk_forward.py:34-37`).
- Internal library code (`src/core/`, `src/baselines/`) does **not** wrap calls in broad `try/except` — errors propagate. Broad `except Exception` is reserved for two specific situations:
  1. Retry/best-effort loops, e.g. `fit_parametric_hmm`'s multi-restart loop swallows a single failed restart and continues (`src/baselines/parametric_hmm.py:39-40`), but still raises `RuntimeError("All HMM fitting attempts failed")` if every restart failed (line 42).
  2. CLI fallback chains in `scripts/run.py`, where each `run_*()` function tries the real pipeline stage, catches `Exception`, prints a message, and falls back to a cached/paper artifact if one exists, re-raising only if no fallback exists (`scripts/run.py:163-175`, `184-195`, `204-227`).
- Pipeline stages support a test-injection hook at the top of every `stage_*` function: `if os.environ.get('GSD_FORCE_STAGE_FAIL') == '<stage_name>': raise RuntimeError(...)` (`src/pipeline/stages.py:28`, `40`, `83`, `143`, `188`). Preserve this hook if adding new stages.
- Convergence/quality issues (SVI not converged, high R-hat, low ESS) use `warnings.warn(...)` rather than raising — these are non-fatal statistical warnings, not program errors (`src/core/hdp_hmm.py:179-183`, `239-249`).

## Logging

**Framework:** Mixed — `print()` is the dominant mechanism in model/experiment code (`src/core/hdp_hmm.py`, `src/data/collect_macro.py`, `run_paper_experiments.py`, `scripts/run.py`); the stdlib `logging` module is used only in `src/pipeline/stages.py` via `logger = logging.getLogger('pipeline.stages')` with `logger.info(...)` / `logger.warning(...)` calls using `%s`/`%d` placeholders (not f-strings), e.g. `logger.info("features: wrote %d rows (%d train, %d test)", ...)` (`src/pipeline/stages.py:71-74`).

**Patterns:**
- Use `print()` for user-facing progress narration in scripts meant to be watched live (data collection steps `[1/4]`...`[4/4]`, SVI/NUTS training progress, pruning/diagnostics tables).
- Use `logger.info`/`logger.warning` only inside `src/pipeline/stages.py` stage functions — this is the one place structured logging is used; extend it there if adding pipeline stages, but don't introduce `logging` calls into the model/math modules (`src/core/hdp_hmm.py`, `src/core/inference.py`) which are print-only by convention.
- `run_paper_experiments.py` defines its own `log(msg)` helper that both prints and writes to `results/run_log.txt` (`run_paper_experiments.py:28-32`) — a third, standalone logging convention specific to that top-level script.

## Comments

**When to Comment:**
- Comments explain causal/statistical *why*, not *what* — e.g. the 7-day NFCI publication-lag shift (`src/data/collect_macro.py:69-73`), the `t <= T` vs `t < T` distinction between `expanding_standardize` and `expanding_regime_vol` (`src/core/inference.py:55-58`), why `.score_samples()` is wrong for a causal baseline (`src/baselines/parametric_hmm.py:49-54`).
- Section-divider comments (`# ===== Section Name =====`) break long modules into logical blocks — used in `src/core/hdp_hmm.py` and `src/pipeline/stages.py`. Follow this when a module accumulates more than ~3 distinct responsibilities.
- No inline comments for self-evident code (matches user's global "no comments unless the why is non-obvious" preference already in effect throughout this codebase).

**JSDoc/TSDoc equivalent (docstrings):**
- Every public module has a module-level docstring stating its purpose and, where relevant, its causal contract (`src/core/inference.py:1-9`, `src/core/walk_forward.py:1-13`).
- Every public function has a one-line summary docstring; functions with non-trivial parameters/returns use NumPy-style `Parameters` / `Returns` sections (`src/core/inference.py:14-47`, `src/core/hdp_hmm.py:479-501`). Internal/private (`_`-prefixed) helpers get a single-line docstring only, no full NumPy-style block.

## Function Design

**Size:** Functions are generally 10-60 lines; the largest single functions are the NumPyro model definition (`hdp_hmm_model`, ~35 lines of pure math) and stage functions in `src/pipeline/stages.py` (~30-50 lines, disk I/O + one computation each). No function exceeds roughly 80 lines. Split by pipeline stage or by inference method (`_fit_svi` vs `_fit_nuts`) rather than writing one large branching function.

**Parameters:** Config constants (`RANDOM_SEED`, `HDP_TRUNCATION`, `TRAIN_END`, etc.) are imported from `src/config.py` and used as function default arguments, e.g. `def fit_hdp_hmm(pcs, K_max=HDP_TRUNCATION, inference=HDP_INFERENCE, seed=RANDOM_SEED)` (`src/baselines/parametric_hmm.py` uses the same pattern via `PARAMETRIC_K_REGIMES`, `RANDOM_SEED`). New tunable behavior should be added to `src/config.py` first, then threaded through as a default parameter — never hardcode a new magic number inline.

**Return Values:** Functions computing statistics return plain `dict` with descriptive string keys ready to be printed or serialized (`_svi_diagnostics`, `_nuts_diagnostics`, `hdp_stability_check`, `regime_stats`, `vol_target_backtest`). Functions producing per-timestep arrays return `numpy.ndarray` (never pandas Series) — DataFrame wrapping happens one layer up, at the pipeline-stage/script boundary, not inside `src/core/*` math functions.

## Module Design

**Exports:**
- `src/core/inference.py` declares `__all__ = ['expanding_standardize', 'expanding_regime_vol']` explicitly (`src/core/inference.py:103`). Other modules do not use `__all__` and rely on all top-level names being importable — `src/core/inference.py`'s explicit-export pattern is the exception, not yet the rule; follow it when adding new small, tightly-scoped utility modules.
- No barrel/`__init__.py` re-exports: `src/__init__.py`, `src/data/__init__.py`, `src/pipeline/__init__.py` are empty (package markers only). Import from the specific submodule (`from src.core.hdp_hmm import fit_hdp_hmm`), never from the package root.

**Config as single source of truth:**
- `src/config.py` is the only place literal thresholds, dates, tickers, and hyperparameters are defined (per `CLAUDE.md`). Any new tunable value belongs there, not inline in `src/core/*` or `src/baselines/*`. Comments in `config.py` explain *why* a parameter is NOT there when it might be expected (e.g. `alpha_trans`/`kappa` are Bayesian latents, not fixed constants — `src/config.py:36-38`).

---

*Convention analysis: 2026-07-21*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
