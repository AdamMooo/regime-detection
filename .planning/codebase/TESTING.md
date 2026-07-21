# Testing Patterns

**Analysis Date:** 2026-07-21

## Test Framework

**Runner:**
- `pytest` 9.0.2 (pinned in `requirements.txt`)
- No config file: no `pytest.ini`, `pyproject.toml` `[tool.pytest.ini_options]`, `setup.cfg`, or `conftest.py` anywhere in the repo. Pytest runs with defaults; test discovery relies purely on the `tests/test_*.py` naming convention.

**Assertion Library:**
- Plain `assert` statements and `numpy.testing.assert_allclose` / `np.allclose` for numeric comparisons. No `unittest.TestCase`, no third-party assertion library (e.g. no `pytest-check`, no `hypothesis`).

**Mocking:**
- No mocking framework of any kind — no `unittest.mock`, no `pytest-mock`, no `responses`/`requests-mock`. Both test files exercise real code paths against synthetic in-memory data (`numpy.random.default_rng`) or real subprocess calls, never mocked collaborators.

**Run Commands:**
```bash
pytest tests/ -v                              # run all tests, verbose
pytest tests/test_causality_invariants.py -v   # run one file
pytest tests/test_cli_runner.py -v
```
No watch mode or coverage tooling is configured (no `pytest-watch`, no `pytest-cov`, no `.coveragerc`). No `Makefile`/`justfile` wraps these commands — run `pytest` directly.

## Test File Organization

**Location:**
- Tests live in a single top-level `tests/` directory, not co-located with source. Mirrors nothing structurally from `src/` — both current test files cut across multiple `src/` modules rather than one test file per source file.

**Naming:**
- `tests/test_<subject>.py`, subject describing the behavior under test rather than the module under test: `test_causality_invariants.py` (property: causality, spanning 4 different functions across 3 source modules), `test_cli_runner.py` (property: the CLI wrapper works).

**Structure:**
```
tests/
  test_causality_invariants.py   # perturb-a-future-value invariant checks
  test_cli_runner.py             # scripts/run.py CLI smoke test + a pure unit test
```
There is currently no `tests/fixtures/` or `tests/data/` directory — all test inputs are generated inline with `numpy.random.default_rng(seed)`, no on-disk fixture files.

## Test Structure

**Suite organization — flat functions, no classes:**
```python
def test_expanding_standardize_causal():
    rng = np.random.default_rng(1)
    X = rng.standard_normal((300, 4))
    X_pert = _bumped(X, T_PERTURB)

    X_scaled, _, _ = expanding_standardize(X, min_warmup=0)
    X_scaled_pert, _, _ = expanding_standardize(X_pert, min_warmup=0)

    np.testing.assert_allclose(X_scaled[:T_PERTURB], X_scaled_pert[:T_PERTURB])
    assert not np.allclose(X_scaled[T_PERTURB:], X_scaled_pert[T_PERTURB:])
```
(`tests/test_causality_invariants.py:48-58`)

- Every test is a bare module-level `def test_*():` function — no test classes, no `setup_method`/`teardown_method`, no fixtures via `@pytest.fixture` (not used anywhere yet).
- Each test builds its own synthetic data locally with a fixed RNG seed (`np.random.default_rng(<int>)`), rather than sharing fixtures across tests — every test is self-contained and reproducible on its own.
- A shared module-level constant `T_PERTURB = 150` (`tests/test_causality_invariants.py:37`) parameterizes where the perturbation is injected across all causality tests in that file — the one piece of shared state, and it's a plain constant, not a fixture.

## The Core Testing Pattern: Causality Invariant Checks

This is the project's signature test pattern (added 2026-07-21) and should be the template for any new "no lookahead" claim:

```python
def _bumped(arr, t, scale=50.0, seed=0):
    """Copy of arr with a large perturbation injected into rows [t:]."""
    out = arr.copy()
    rng = np.random.default_rng(seed)
    out[t:] += scale * rng.standard_normal(out[t:].shape)
    return out
```
(`tests/test_causality_invariants.py:40-45`)

Pattern for each causal function under test:
1. Generate baseline synthetic input with a seeded RNG.
2. Build a perturbed copy via `_bumped()` that only modifies rows from index `T_PERTURB` onward.
3. Run the function under test on both the original and perturbed input.
4. Assert output at indices *before* the perturbation point is bit-for-bit unchanged (`np.testing.assert_allclose`, tight `atol` where needed, e.g. `atol=1e-10` for probability outputs).
5. Include a **positive sanity check** (`assert not np.allclose(...)` on the post-perturbation region) proving the perturbation actually propagated and the test isn't vacuously passing.
6. Where the row's own current-timestep value must not be used in its own estimate (e.g. `expanding_regime_vol`, since `returns[t]` is the outcome being traded on day `t`), the invariant is tightened from "indices `< t` unaffected" to "indices `<= t` unaffected" — see the docstring distinction at `tests/test_causality_invariants.py:9-14`.
7. Where a **negative control** is needed (proving the perturbation is large enough that a *non-causal* computation WOULD change), assert the opposite for the smoothed/non-causal counterpart: `test_forward_backward_numpy_filtered_vs_smoothed` asserts the causal `filtered` output is unaffected before `t`, then asserts the non-causal `smoothed` output DOES change before `t` — proving the filtered-causal assertion has teeth (`tests/test_causality_invariants.py:111-128`).

**Functions currently covered by this pattern** (`tests/test_causality_invariants.py`):
- `expanding_standardize` (`src/core/inference.py`) — invariant: indices `< t` unaffected.
- `expanding_regime_vol` (`src/core/inference.py`) — invariant: indices `<= t` unaffected (tighter, see above).
- `get_filtered_states` (`src/baselines/parametric_hmm.py`) — invariant: indices `< t` unaffected; uses a hand-built toy `GaussianHMM` fixture (`_toy_gaussian_hmm()`, `tests/test_causality_invariants.py:76-82`) rather than a fitted model.
- `forward_backward_numpy`'s `filtered` return value (`src/core/hdp_hmm.py`) — invariant: indices `< t` unaffected, PLUS the negative control on `smoothed`. Uses a hand-built toy HDP params dict (`_toy_hdp_params()`, `tests/test_causality_invariants.py:98-108`).

**When adding a new function that claims "causal" / "no lookahead":** add a matching `test_<function>_causal` test to `tests/test_causality_invariants.py` following the exact `_bumped()` + before/after assertion + sanity-check structure above, rather than creating a new test file or a different pattern.

## CLI Testing Pattern

`tests/test_cli_runner.py` mixes two different test styles in one file:

```python
def test_cli_help_works():
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, 'scripts/run.py', '--help'],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0
    assert 'usage:' in result.stdout.lower()
```
- **Subprocess smoke test:** invokes the real CLI entry point (`scripts/run.py`) as a separate process via `subprocess.run([sys.executable, ...])`, asserting only exit code and stdout shape — no mocking of `argparse` or the environment. Use `timeout=` on every `subprocess.run` call (120s here) to prevent a hang from blocking the suite.
- **Pure unit test on an imported function**, no subprocess:
  ```python
  def test_regime_classifier_uses_current_vix_thresholds():
      assert cli.classify_regime_from_vix(10.0) == 'Low-Vol'
      assert cli.classify_regime_from_vix(18.8) == 'Moderate-Vol'
      assert cli.classify_regime_from_vix(25.0) == 'High-Vol'
  ```
  Imports the CLI module directly by manipulating `sys.path` to include `scripts/` (`tests/test_cli_runner.py:5-6`), then calls its functions in-process for fast, deterministic checks of pure logic (VIX threshold classification). Prefer this in-process style for any new pure-function CLI logic; reserve subprocess tests for verifying the actual entry point/argument parsing wiring.

## Fixtures and Factories

- No `@pytest.fixture` usage anywhere yet. "Fixtures" in this codebase are plain private helper functions returning synthetic data or toy model objects, defined at module scope and called directly inside each test: `_bumped()`, `_toy_gaussian_hmm()`, `_toy_hdp_params()` (all in `tests/test_causality_invariants.py`). Follow this convention (plain helper functions, not `pytest.fixture`) unless multiple test files need to share the same fixture, at which point a `conftest.py` should be introduced for the first time.
- No on-disk fixture files/directories; all test data is synthetic and generated at test-run time with a fixed seed for reproducibility.

## Coverage

**Requirements:** None enforced. No coverage tool installed (`pytest-cov` not in `requirements.txt`), no coverage threshold, no CI gate on coverage.

**Known coverage gaps** (see `.planning/codebase/CONCERNS.md` for detail): `src/core/hdp_hmm.py`'s SVI/NUTS fitting paths (`fit_hdp_hmm`, `_fit_svi`, `_fit_nuts`), `src/core/walk_forward.py`'s `walk_forward_oos`/`ensemble_oos`, and `src/data/collect_macro.py`'s `fetch_and_save_data` have no direct unit tests — they are only exercised end-to-end via manual runs of `run_paper_experiments.py` / `scripts/run.py`, not via `pytest`.

## Test Types

**Unit tests:**
- `tests/test_causality_invariants.py` is unit-level: each test isolates exactly one function against synthetic data, no I/O, no network, no filesystem.
- `tests/test_cli_runner.py::test_regime_classifier_uses_current_vix_thresholds` is also unit-level (pure function, in-process).

**Integration tests:**
- `tests/test_cli_runner.py::test_cli_help_works` is a thin integration/smoke test — spawns the real `python scripts/run.py --help` subprocess and checks it starts and parses arguments correctly. There is no broader integration test exercising the full `collect -> features -> train_hmm -> signals -> walk_forward` pipeline chain under pytest; that chain is only run manually via `run_paper_experiments.py` or `scripts/run.py` (no `--validate`) end-to-end.

**E2E tests:** Not used under pytest. The closest equivalent is manually running `python run_paper_experiments.py` (full pipeline, ~40s) or `python scripts/run.py` (CLI wrapper, all stages) and inspecting output artifacts — not automated as a test.

## Stale / Disabled CI Reference (do not trust)

`.github/workflows/tests.yml` is currently disabled (only `workflow_dispatch`, no `push`/`pull_request` triggers — both commented out) and **references files that no longer exist** in this codebase: `tests/test_causality.py`, `tests/test_bot_integration.py`, `tests/test_incremental_collection.py`, `tests/test_pca_caching.py`, `tests/test_dashboard_refactor.py`, plus top-level scripts `analyze_feature_importance.py`, `analyze_regime_characterization.py`, `analyze_signal_quality.py` — all leftovers from a pre-"stripped, paper-first" architecture (see `NOTES.md` "Current Architecture (Clean)": these were deliberately deleted). Running this workflow as-is will fail on missing files. If re-enabling CI, rewrite the job steps to reference only `tests/test_causality_invariants.py` and `tests/test_cli_runner.py` (or simply `pytest tests/ -v`).

## Common Patterns

**Numeric equality with tolerance:**
```python
np.testing.assert_allclose(filtered[:T_PERTURB], filtered_pert[:T_PERTURB], atol=1e-10)
```
Use `atol=1e-10` for probability/posterior comparisons where floating-point drift is expected but should be negligible; use default tolerance for raw feature-scale comparisons (`expanding_standardize` test uses no explicit `atol`).

**Proving a test isn't vacuous:**
```python
assert not np.allclose(X_scaled[T_PERTURB:], X_scaled_pert[T_PERTURB:])
```
Always pair a "should be unchanged" assertion with a "but this part legitimately changed" assertion — this is the project's standard defense against silently-passing tests.

**Subprocess CLI invocation:**
```python
result = subprocess.run(
    [sys.executable, 'scripts/run.py', '--help'],
    cwd=repo, capture_output=True, text=True, timeout=120,
)
```
Always set `cwd` to the repo root explicitly (`Path(__file__).resolve().parents[1]`) and always pass `timeout=` — the CLI wrapper has network fallback paths (`yfinance` calls) that could hang without one.

---

*Testing analysis: 2026-07-21*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
