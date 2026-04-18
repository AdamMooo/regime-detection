---
phase: 03-refactor
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [hmmlearn.py, inference.py, evaluation.py, orchestrator.py, train.py, tests/test_train_refactor.py]
autonomous: true
requirements: [3.1]
must_haves:
  truths:
    - "train.py delegates to focused modules without code duplication"
    - "All 33+ existing tests still pass (no regressions)"
    - "train() and rebuild_dashboard() APIs unchanged (backward compatible)"
    - "Each module has complete docstrings explaining purpose and usage"
    - "Code coverage stable or improved across refactored modules"
  artifacts:
    - path: "hmmlearn.py"
      provides: "HMM training logic (fit_rolling_pca, select_states_bic, check_stability, label_regimes, fit_regime_sv, fit_regime_garch)"
      min_lines: 400
    - path: "inference.py"
      provides: "Regime detection (filtered_probs, filtered_labels, Student-t HMM, _fit_hmm)"
      min_lines: 200
    - path: "evaluation.py"
      provides: "Metrics and diagnostics (evaluate, compute_var_backtest, kupiec_pof_test, christoffersen_test)"
      min_lines: 250
    - path: "orchestrator.py"
      provides: "Training workflow coordination (walk_forward, HDP-HMM training)"
      min_lines: 300
    - path: "train.py"
      provides: "Thin wrapper delegating to modules"
      min_lines: 100
    - path: "tests/test_train_refactor.py"
      provides: "Regression tests validating module extraction"
      min_lines: 150
  key_links:
    - from: "train.py"
      to: "hmmlearn.py"
      via: "import fit_rolling_pca, select_states_bic, fit_regime_sv"
      pattern: "from hmmlearn import"
    - from: "train.py"
      to: "inference.py"
      via: "import filtered_probs, filtered_labels, _fit_hmm"
      pattern: "from inference import"
    - from: "train.py"
      to: "evaluation.py"
      via: "import evaluate, compute_var_backtest"
      pattern: "from evaluation import"
    - from: "train.py"
      to: "orchestrator.py"
      via: "import walk_forward"
      pattern: "from orchestrator import"
    - from: "run.py"
      to: "train.py"
      via: "from train import train, rebuild_dashboard"
      pattern: "train\\(\\)"
---

<objective>
Refactor train.py (2988 lines) into focused, testable modules. This improves code maintainability and makes future modifications safer. Core objective: split monolithic training logic into four modules (HMM training, regime inference, evaluation, orchestration) while preserving 100% backward compatibility with run.py and signals.py.

Purpose: Reduce cognitive load when debugging or enhancing the pipeline. Each module handles a single concern, making it easier to test and modify individual pieces.

Output: Four new modules (hmmlearn.py, inference.py, evaluation.py, orchestrator.py) + refactored train.py (thin wrapper) + regression tests + updated CLAUDE.md.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@.planning/phases/03-refactor/03-CONTEXT.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md

## Current train.py Functional Boundaries

The train.py file contains roughly five functional areas that will be extracted:

1. **HMM Training Pipeline** (lines 199–510, 557–600, 1047+)
   - `fit_rolling_pca()` — Procrustes-aligned rolling PCA
   - `select_states_bic()` — Model selection via BIC
   - `check_stability()` — Regime label stability validation
   - `label_regimes()` — Assign names to learned regimes
   - `fit_regime_sv()` — Stochastic volatility models per regime
   - `fit_regime_garch()` — GARCH models per regime
   - Related helpers: `_hmm_n_params()`, `_hmm_bic()`, `_best_perm_agreement()`

2. **Regime Inference** (lines 63–200, 287–380, 2535–2600)
   - `expanding_standardize()` — Expanding-window z-score
   - `StudentTHMM` class — Student-t HMM implementation
   - `_fit_hmm()` — Core HMM fitting
   - `filtered_probs()` — Forward-pass regime probabilities
   - `filtered_labels()` — Regime label assignment with hysteresis
   - `train()` entry point (trains HMM, returns results DataFrame)

3. **Evaluation & Diagnostics** (lines 686–900)
   - `evaluate()` — Comprehensive regime statistics
   - `compute_var_backtest()` — VaR validation
   - `kupiec_pof_test()` — POF test implementation
   - `christoffersen_test()` — Independence test
   - `compute_var_backtest_garch()` — GARCH-based VaR
   - `_print_bootstrap_cis()` — Bootstrap confidence intervals
   - `_get_blocks()` — Block clustering helper

4. **Walk-Forward Validation** (lines 557–700)
   - `walk_forward()` — Rolling-window out-of-sample validation

5. **Dashboard Building** (lines 1047–2530)
   - `rebuild_dashboard()` entry point
   - `build_interactive_dashboard()` — Main Plotly figure assembly
   - `_build_kde_surface()` — Regime probability KDE surfaces
   - `_build_transitions()` — Regime transition matrix visualization
   - `_build_current_state()` — Current regime state panel
   - `_build_sv_volatility()` — SV/GARCH volatility visualization
   - `_build_signals_tab()` — Signals and diagnostics tab
   - `_build_feature_health_tab()` — Feature importance tab
   - `_write_dashboard_html()` — HTML output

**Note:** Dashboard building remains in train.py (Phase 3.1 focuses on training pipeline; dashboard refactoring is Phase 3.2 separate task).

## Extraction Strategy

**Module 1: inference.py** — Foundation layer (regime inference, no external dependencies on training logic)
  - `expanding_standardize()`
  - `StudentTHMM` class
  - `_fit_hmm()`
  - `filtered_probs()`
  - `filtered_labels()`
  - HDP-HMM inference (NumPyro code if present)

**Module 2: hmmlearn.py** — Training logic (depends on inference.py)
  - `fit_rolling_pca()`
  - `select_states_bic()`
  - `check_stability()`
  - `label_regimes()`
  - `fit_regime_sv()`
  - `fit_regime_garch()`
  - Helpers: `_hmm_n_params()`, `_hmm_bic()`, `_best_perm_agreement()`

**Module 3: evaluation.py** — Diagnostics (depends on inference.py)
  - `evaluate()`
  - `compute_var_backtest()`
  - `compute_var_backtest_garch()`
  - `kupiec_pof_test()`
  - `christoffersen_test()`
  - Helpers: `_print_bootstrap_cis()`, `_get_blocks()`

**Module 4: orchestrator.py** — Workflow coordination (depends on hmmlearn.py, evaluation.py)
  - `walk_forward()` — Rolling-window OOS validation

**Module 5: train.py (refactored)** — Thin wrapper
  - `train()` — Orchestrates hmmlearn.py + evaluation.py
  - `rebuild_dashboard()` — Unchanged (kept in train.py for now)
  - Global imports and logger setup
  - Config constants and utility functions (expanding_standardize, StudentTHMM remain for now)

**Atomic extraction plan:**
  1. Extract inference.py first (no dependencies on other training logic)
  2. Extract hmmlearn.py (depends on inference.py)
  3. Extract evaluation.py (depends on inference.py)
  4. Extract orchestrator.py (depends on both hmmlearn.py and evaluation.py)
  5. Refactor train.py to import from all four modules
  6. Run full test suite after each extraction
  7. Create regression tests in test_train_refactor.py

</context>

<tasks>

<task type="auto">
  <name>Task 1: Extract inference.py (regime inference foundation)</name>
  <files>inference.py, train.py</files>
  <action>
Extract regime inference logic from train.py into new inference.py module. Move the following functions/classes to inference.py:
  - expanding_standardize() [lines 63–90]
  - StudentTHMM class [lines 95–105] 
  - _fit_hmm() [lines 107–115]
  - filtered_probs() [lines 116–149]
  - filtered_labels() [lines 151–197]
  - Any HDP-HMM NumPyro inference code if present (check lines 2500+)

Create inference.py with:
  - Header docstring explaining purpose: "Core regime inference logic (probability filtering, label assignment, HMM fitting)"
  - Complete import section (numpy, pandas, hmmlearn, scipy, etc.)
  - All moved functions with unchanged signatures
  - Full docstrings for each function (explain parameters, returns, behavior)
  - At line end: __all__ = ['expanding_standardize', 'StudentTHMM', '_fit_hmm', 'filtered_probs', 'filtered_labels']

Keep these in train.py for now (not moving yet):
  - Config imports and logger setup
  - Visualization functions (dashboard building)

Test: Run `pytest tests/ -xvs` (should pass 33+ tests). Verify no import errors in train.py after adding `from inference import ...`

After extraction, update train.py:
  - At top, add: `from inference import expanding_standardize, StudentTHMM, _fit_hmm, filtered_probs, filtered_labels`
  - Keep rest of train.py unchanged
  - Verify `train()` still calls these functions by imported name
  
Commit: `git add inference.py tests/` && `git commit -m "refactor(03): extract inference.py — regime filtering and label assignment"`
  </action>
  <verify>
    <automated>pytest tests/ -xvs --tb=short</automated>
    <check>grep -n "from inference import" train.py</check>
    <check>grep -c "^def\|^class" inference.py</check>
  </verify>
  <done>
inference.py exists with 5+ functions/classes, no signature changes, all 33+ tests passing, train.py imports from inference.py, commit created.
  </done>
</task>

<task type="auto">
  <name>Task 2: Extract hmmlearn.py (HMM training logic)</name>
  <files>hmmlearn.py, train.py, inference.py</files>
  <action>
Extract HMM training logic from train.py into new hmmlearn.py module. Move the following functions/classes to hmmlearn.py:
  - _hmm_n_params() [lines 273–285]
  - _hmm_bic() [lines 287–292]
  - select_states_bic() [lines 294–320]
  - _best_perm_agreement() [lines 322–328]
  - check_stability() [lines 330–356]
  - label_regimes() [lines 358–379]
  - fit_rolling_pca() [lines 199–271]
  - fit_regime_sv() [lines 433–507]
  - fit_regime_garch() [lines 509–555]

Create hmmlearn.py with:
  - Header docstring: "HMM model training, feature engineering (PCA), and regime-dependent volatility modeling"
  - Complete import section (numpy, pandas, sklearn.decomposition.PCA, scipy, arch, statsmodels, joblib, etc.)
  - Import from inference: `from inference import _fit_hmm, StudentTHMM`
  - All moved functions with unchanged signatures
  - Full docstrings (explain PCA Procrustes alignment, BIC model selection, regime SV/GARCH)
  - At line end: __all__ = ['fit_rolling_pca', 'select_states_bic', 'check_stability', 'label_regimes', 'fit_regime_sv', 'fit_regime_garch']

Test: Run `pytest tests/ -xvs` (should pass 33+ tests). Verify no import errors.

After extraction, update train.py:
  - Add import: `from hmmlearn import fit_rolling_pca, select_states_bic, check_stability, label_regimes, fit_regime_sv, fit_regime_garch`
  - Update `train()` to call these by imported name (no code changes, just imports)
  - Verify all calls to fit_rolling_pca(), select_states_bic() etc. still work

Commit: `git add hmmlearn.py tests/` && `git commit -m "refactor(03): extract hmmlearn.py — PCA, model selection, regime volatility"`
  </action>
  <verify>
    <automated>pytest tests/ -xvs --tb=short</automated>
    <check>grep -n "from hmmlearn import" train.py</check>
    <check>grep -c "^def\|^class" hmmlearn.py</check>
  </verify>
  <done>
hmmlearn.py exists with 9+ functions, imports from inference.py, no signature changes, all 33+ tests passing, train.py imports correctly, commit created.
  </done>
</task>

<task type="auto">
  <name>Task 3: Extract evaluation.py (diagnostics and metrics)</name>
  <files>evaluation.py, train.py, inference.py</files>
  <action>
Extract evaluation and diagnostics logic from train.py into new evaluation.py module. Move the following functions to evaluation.py:
  - evaluate() [lines 686–711]
  - _print_bootstrap_cis() [lines 713–776]
  - compute_var_backtest() [lines 778–813]
  - kupiec_pof_test() [lines 815–831]
  - christoffersen_test() [lines 833–888]
  - compute_var_backtest_garch() [lines 890–1024]
  - _get_blocks() [lines 1026–1045]

Create evaluation.py with:
  - Header docstring: "Regime evaluation metrics, validation tests (VaR backtests, POF, independence), bootstrap confidence intervals"
  - Complete import section (numpy, pandas, scipy.stats, arch, etc.)
  - Import from inference: `from inference import filtered_labels`
  - All moved functions with unchanged signatures
  - Full docstrings (explain VaR backtest methodology, POF test, Christoffersen test)
  - At line end: __all__ = ['evaluate', 'compute_var_backtest', 'compute_var_backtest_garch', 'kupiec_pof_test', 'christoffersen_test']

Test: Run `pytest tests/ -xvs` (should pass 33+ tests). Verify no import errors.

After extraction, update train.py:
  - Add import: `from evaluation import evaluate, compute_var_backtest, compute_var_backtest_garch, kupiec_pof_test, christoffersen_test`
  - Update `train()` to call these by imported name
  - Verify all calls work correctly

Commit: `git add evaluation.py tests/` && `git commit -m "refactor(03): extract evaluation.py — VaR backtest, POF/Christoffersen tests, bootstrap CIs"`
  </action>
  <verify>
    <automated>pytest tests/ -xvs --tb=short</automated>
    <check>grep -n "from evaluation import" train.py</check>
    <check>grep -c "^def" evaluation.py</check>
  </verify>
  <done>
evaluation.py exists with 7+ functions, imports from inference.py, no signature changes, all 33+ tests passing, train.py imports correctly, commit created.
  </done>
</task>

<task type="auto">
  <name>Task 4: Extract orchestrator.py (workflow coordination)</name>
  <files>orchestrator.py, train.py, hmmlearn.py, evaluation.py</files>
  <action>
Extract walk-forward validation logic from train.py into new orchestrator.py module. Move the following function to orchestrator.py:
  - walk_forward() [lines 557–684]

Create orchestrator.py with:
  - Header docstring: "Training workflow coordination, walk-forward out-of-sample validation"
  - Complete import section (numpy, pandas, etc.)
  - Import from hmmlearn: `from hmmlearn import fit_rolling_pca, select_states_bic, fit_regime_sv, fit_regime_garch`
  - Import from evaluation: `from evaluation import evaluate`
  - Import from inference: `from inference import expanding_standardize, filtered_probs, filtered_labels`
  - walk_forward() function with unchanged signature
  - Full docstring explaining rolling-window validation methodology
  - At line end: __all__ = ['walk_forward']

Test: Run `pytest tests/ -xvs` (should pass 33+ tests).

After extraction, update train.py:
  - Add import: `from orchestrator import walk_forward`
  - Verify train() calls work correctly

Commit: `git add orchestrator.py tests/` && `git commit -m "refactor(03): extract orchestrator.py — walk-forward OOS validation"`
  </action>
  <verify>
    <automated>pytest tests/ -xvs --tb=short</automated>
    <check>grep -n "from orchestrator import" train.py</check>
    <check>grep "def walk_forward" orchestrator.py</check>
  </verify>
  <done>
orchestrator.py exists with walk_forward() function, correct imports, no signature changes, all 33+ tests passing, train.py imports correctly, commit created.
  </done>
</task>

<task type="auto">
  <name>Task 5: Refactor train.py to thin wrapper + module imports</name>
  <files>train.py</files>
  <action>
Refactor train.py to be a thin orchestration wrapper that delegates to the four new modules. Steps:

1. Add imports section at top (after docstring and warning filters):
   ```python
   from inference import expanding_standardize, StudentTHMM, _fit_hmm, filtered_probs, filtered_labels
   from hmmlearn import fit_rolling_pca, select_states_bic, check_stability, label_regimes, fit_regime_sv, fit_regime_garch
   from evaluation import evaluate, compute_var_backtest, compute_var_backtest_garch, kupiec_pof_test, christoffersen_test
   from orchestrator import walk_forward
   ```

2. Remove the function bodies of the extracted functions (but keep any that are still used locally, e.g., _print_bootstrap_cis if used by dashboard).

3. Keep in train.py:
   - All config imports (RANDOM_SEED, N_STATES, etc.)
   - Warning suppression and logging setup
   - Dashboard building functions (rebuild_dashboard, build_interactive_dashboard, _build_*, etc.)
   - train() function (now a thin orchestrator calling hmmlearn.py + evaluation.py)
   - Any utility functions used by dashboard

4. Ensure train() function signature is unchanged: `train(reload_pca_checkpoint_path=None)`

5. Ensure rebuild_dashboard() function signature is unchanged: `rebuild_dashboard()`

Test: Run `pytest tests/ -xvs` (should pass 33+ tests). Verify `python run.py train` still works.

Verify API backward compatibility:
  - Check run.py can still call `train()` and `rebuild_dashboard()` without changes
  - Check signals.py can still import from train if needed (should not need to)

Commit: `git add train.py tests/` && `git commit -m "refactor(03): refactor train.py to thin wrapper — delegates to modules"`
  </action>
  <verify>
    <automated>pytest tests/ -xvs --tb=short</automated>
    <check>python -c "from train import train, rebuild_dashboard; print('API OK')"</check>
    <check>python run.py train 2>&1 | head -20</check>
  </verify>
  <done>
train.py is thin wrapper (300-400 lines), imports from all 4 modules, train() and rebuild_dashboard() signatures unchanged, all 33+ tests passing, run.py integration verified, commit created.
  </done>
</task>

<task type="auto">
  <name>Task 6: Create regression tests for module extraction</name>
  <files>tests/test_train_refactor.py</files>
  <action>
Create comprehensive regression tests verifying the refactoring preserved all functionality. File: tests/test_train_refactor.py (150+ lines)

Test cases:

1. **Module imports OK**
   ```python
   def test_inference_imports():
       from inference import expanding_standardize, StudentTHMM, _fit_hmm, filtered_probs, filtered_labels
       # Verify all exist and are callable
   
   def test_hmmlearn_imports():
       from hmmlearn import fit_rolling_pca, select_states_bic, check_stability, label_regimes, fit_regime_sv, fit_regime_garch
       # Verify all exist
   
   def test_evaluation_imports():
       from evaluation import evaluate, compute_var_backtest, compute_var_backtest_garch, kupiec_pof_test, christoffersen_test
       # Verify all exist
   
   def test_orchestrator_imports():
       from orchestrator import walk_forward
       # Verify exists
   ```

2. **train.py API unchanged**
   ```python
   def test_train_signature():
       from train import train
       # Verify signature is train(reload_pca_checkpoint_path=None)
       import inspect
       sig = inspect.signature(train)
       assert 'reload_pca_checkpoint_path' in sig.parameters
   
   def test_rebuild_dashboard_signature():
       from train import rebuild_dashboard
       # Verify signature is rebuild_dashboard()
       import inspect
       sig = inspect.signature(rebuild_dashboard)
       assert len(sig.parameters) == 0 or all(p.default != inspect.Parameter.empty for p in sig.parameters.values())
   ```

3. **Expanding standardize behavior**
   ```python
   def test_expanding_standardize_from_inference():
       from inference import expanding_standardize
       import numpy as np
       X = np.random.randn(500, 5)
       X_scaled, mean_f, std_f = expanding_standardize(X, min_warmup=50)
       assert X_scaled.shape == X.shape
       assert np.isnan(X_scaled[:50]).all()  # First 50 rows are NaN
       assert not np.isnan(X_scaled[100:]).any()  # Rest should have values
   ```

4. **StudentTHMM still works**
   ```python
   def test_student_t_hmm_from_inference():
       from inference import StudentTHMM
       import numpy as np
       model = StudentTHMM(n_components=2)
       X = np.random.randn(100, 3)
       model.fit(X)
       assert hasattr(model, 'transmat_')
   ```

5. **Filtered probs/labels from inference**
   ```python
   def test_filtered_probs_behavior():
       from inference import filtered_probs, StudentTHMM
       # Train a simple HMM, verify filtered_probs returns expected shape
   
   def test_filtered_labels_behavior():
       from inference import filtered_labels, StudentTHMM
       # Train HMM, verify filtered_labels returns array of regime labels
   ```

6. **PCA fitting from hmmlearn**
   ```python
   def test_fit_rolling_pca_from_hmmlearn():
       from hmmlearn import fit_rolling_pca
       # Verify PCA fitting still works with Procrustes alignment
   ```

Header docstring:
```python
"""Regression tests for train.py refactoring.

Verify that extraction of inference.py, hmmlearn.py, evaluation.py, orchestrator.py
did not break API compatibility or behavior. All tests should pass before merging refactoring.
"""
```

Commit: `git add tests/test_train_refactor.py && git commit -m "test(03): add regression tests for train.py refactoring"`

After tests pass, verify: `pytest tests/test_train_refactor.py -xvs`
  </action>
  <verify>
    <automated>pytest tests/test_train_refactor.py -xvs --tb=short</automated>
    <check>pytest tests/test_train_refactor.py::test_train_signature -xvs</check>
    <check>pytest tests/test_train_refactor.py::test_expanding_standardize_from_inference -xvs</check>
  </verify>
  <done>
tests/test_train_refactor.py exists (150+ lines), all regression tests passing (6+ test cases), train() and rebuild_dashboard() APIs verified unchanged, commit created.
  </done>
</task>

<task type="auto">
  <name>Task 7: Update CLAUDE.md with refactored module structure</name>
  <files>CLAUDE.md</files>
  <action>
Update CLAUDE.md to document the refactored architecture. Modify the "Architecture" section:

Replace current architecture section:
```
## Architecture
```
collect.py              Data collection (market prices + macro indicators)
features.py             13-feature engineering pipeline + rolling PCA
train.py                HDP-HMM model training (NumPyro)
hdp_hmm.py              Core HMM implementation
signals.py              Regime signal generation from trained model
run.py                  Orchestration: collect → features → train → signals
analyze.py              Post-hoc analysis and regime characterization
trust.py                Regime trust/confidence scoring
dashboard.py            Streamlit visualization dashboard
config.py               Model params, feature config, file paths
tests/                  Test suite
```
```

With:
```
## Architecture (Post-Phase 3.1 Refactoring)

### Data & Feature Pipeline
- **collect.py** — Data collection (market prices + macro indicators)
- **features.py** — 13-feature engineering pipeline + rolling PCA
- **config.py** — Model params, feature config, file paths

### Core HMM & Regime Detection
- **hdp_hmm.py** — Bayesian HDP-HMM (NumPyro)
- **inference.py** — Core regime inference (probability filtering, label assignment)
  - `expanding_standardize()` — Expanding-window z-score (no lookahead)
  - `StudentTHMM` — Student-t HMM backend
  - `filtered_probs()` — Forward-pass regime probabilities
  - `filtered_labels()` — Regime labeling with hysteresis (no lookahead)
- **hmmlearn.py** — HMM training & feature engineering
  - `fit_rolling_pca()` — Procrustes-aligned rolling PCA
  - `select_states_bic()` — Model selection via BIC
  - `label_regimes()` — Map learned regimes to (Low-Vol, Med-Vol, High-Vol)
  - `fit_regime_sv()` / `fit_regime_garch()` — Per-regime volatility models
- **evaluation.py** — Diagnostics & validation
  - `evaluate()` — Comprehensive regime statistics
  - `compute_var_backtest()` — VaR validation (Kupiec POF, Christoffersen independence)
- **orchestrator.py** — Workflow coordination
  - `walk_forward()` — Rolling-window out-of-sample validation

### Output & Integration
- **signals.py** — Regime signal generation from trained model
- **train.py** — Training orchestrator (delegates to inference/hmmlearn/evaluation/orchestrator)
- **run.py** — Top-level pipeline: collect → features → train → signals
- **dashboard.py** — Streamlit visualization dashboard
- **trust.py** — Regime trust/confidence scoring
- **analyze.py** — Post-hoc analysis and regime characterization

### Testing
- **tests/** — 33+ test suite
  - test_causality.py — Causal guarantees (no lookahead)
  - test_bot_integration.py — Algo-Trading-Bot signal schema
  - test_train_refactor.py — Refactoring regression tests
  - (+ 8 other test files covering validation, calibration, caching)
```

Add new section after Architecture:

```
## Module Responsibilities (Phase 3.1 Refactoring)

**inference.py** — Foundation layer
- Regime probability filtering (forward-pass only, no lookahead)
- Regime label assignment with hysteresis (minimum hold period)
- StandardHMM training via hmmlearn
- Expanding-window standardization (causal)

**hmmlearn.py** — Training & feature engineering
- Rolling PCA with Procrustes alignment (regime stability)
- BIC-based model selection (number of regimes)
- Regime naming (learned regimes → Low-Vol, Med-Vol, High-Vol)
- Per-regime volatility models (SV and GARCH)

**evaluation.py** — Diagnostics & backtesting
- Regime separation tests (ANOVA, permutation)
- VaR backtesting (Kupiec POF, Christoffersen independence)
- Bootstrap confidence intervals for regime statistics
- Out-of-sample validation (expanding and rolling windows)

**orchestrator.py** — Workflow coordination
- Walk-forward validation (rolling training/test windows)
- Integration of training, prediction, and evaluation loops

**train.py** — Thin orchestrator
- Orchestrates pipeline: hmmlearn → inference → evaluation
- Maintains backward compatibility with run.py (train(), rebuild_dashboard())
- Dashboard building (Plotly-based interactive visualizations)
```

Commit: `git add CLAUDE.md && git commit -m "docs(03): update CLAUDE.md with refactored module structure"`
  </action>
  <verify>
    <check>grep -n "Module Responsibilities" CLAUDE.md</check>
    <check>grep -n "inference.py" CLAUDE.md</check>
    <check>grep -n "hmmlearn.py" CLAUDE.md</check>
  </verify>
  <done>
CLAUDE.md updated with refactored architecture (sections: Data & Feature Pipeline, Core HMM & Regime Detection, Output & Integration, Testing, Module Responsibilities), all module responsibilities documented, commit created.
  </done>
</task>

<task type="auto">
  <name>Task 8: Run full test suite and verify backward compatibility</name>
  <files>tests/</files>
  <action>
Run comprehensive final verification of the refactoring. Execute:

1. **Run all tests (33+)**
   ```bash
   pytest tests/ -xvs --tb=short
   ```
   Verify: All tests pass, no import errors, no signature mismatches.

2. **Test run.py integration**
   ```bash
   python run.py train 2>&1 | grep -E "(ERROR|Traceback|PASSED|FAILED)" || echo "OK"
   ```
   Verify: Pipeline completes without errors, regime_results.csv created/updated.

3. **Test run.py regime printing**
   ```bash
   python run.py regime 2>&1 | grep -E "(Regime|Confidence|Distribution)" | head -5
   ```
   Verify: Regime awareness printed correctly, no import/attribute errors.

4. **Verify module count reduction in train.py**
   ```bash
   wc -l train.py
   # Should be ~400-500 lines (was 2988 before refactoring)
   ```
   Verify: train.py is now a thin wrapper (50-70% reduction from 2988 lines).

5. **Verify code distribution**
   ```bash
   for f in inference hmmlearn evaluation orchestrator; do echo "$f: $(wc -l < $f.py) lines"; done
   ```
   Expected:
   - inference.py: 200-250 lines
   - hmmlearn.py: 400-450 lines
   - evaluation.py: 250-300 lines
   - orchestrator.py: 150-200 lines
   - train.py: 400-500 lines

6. **Check test coverage**
   ```bash
   pytest tests/ --cov=. --cov-report=term-missing 2>&1 | grep -E "TOTAL|^FAILED"
   ```
   Verify: Coverage stable or improved vs. baseline (typically 70%+).

Commit: `git add tests/ && git commit -m "test(03): verify refactoring with full test suite + integration checks"`

If ANY test fails, investigate and fix before proceeding to next phase.
  </action>
  <verify>
    <automated>pytest tests/ -xvs --tb=short 2>&1 | tail -20</automated>
    <check>python run.py regime 2>&1 | head -20</check>
  </verify>
  <done>
All 33+ tests passing, run.py integration working (train/regime commands), train.py reduced to 400-500 lines (thin wrapper), all four modules (inference, hmmlearn, evaluation, orchestrator) in place, code distribution correct, final commit created.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Module imports | Each new module imports from others; potential circular dependency risk |
| Function signatures | train() and rebuild_dashboard() must remain unchanged (Algo-Trading-Bot, Portfolio-Manager depend on these) |
| Test suite | Existing 33+ tests validate no regressions; new refactoring could introduce hidden bugs |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-03-01 | Spoofing | Module imports | Mitigate | Atomic commits after each extraction; full test suite runs after each module extracted |
| T-03-02 | Tampering | Function signatures | Mitigate | Regression tests in test_train_refactor.py verify train() and rebuild_dashboard() signatures unchanged |
| T-03-03 | Repudiation | Code refactoring | Mitigate | Git history preserved; each module extraction is a separate commit with clear message |
| T-03-04 | Information Disclosure | Causal guarantees | Mitigate | test_causality.py (10 tests) still run and pass; no lookahead introduced in extracted modules |
| T-03-05 | Denial of Service | Train performance | Mitigate | No algorithm changes, only refactoring; performance benchmarks unchanged |
| T-03-06 | Elevation of Privilege | API changes | Mitigate | Only internal APIs split; external APIs (train(), rebuild_dashboard()) remain unchanged |

</threat_model>

<verification>
## Phase 3.1 Completion Checklist

Before declaring Phase 3.1 complete:

- [ ] Task 1: inference.py extracted, imports work, tests pass
- [ ] Task 2: hmmlearn.py extracted, imports from inference.py, tests pass
- [ ] Task 3: evaluation.py extracted, imports from inference.py, tests pass
- [ ] Task 4: orchestrator.py extracted, imports from hmmlearn/evaluation/inference, tests pass
- [ ] Task 5: train.py refactored to thin wrapper, all imports correct, tests pass
- [ ] Task 6: test_train_refactor.py created, 6+ regression tests, all passing
- [ ] Task 7: CLAUDE.md updated with refactored module structure
- [ ] Task 8: Full test suite passing (33+), run.py integration verified
- [ ] No breaking changes: train() and rebuild_dashboard() signatures unchanged
- [ ] Code quality: train.py reduced to 400-500 lines (thin wrapper)
- [ ] All commits created and pushed

## Success Criteria

**Phase 3.1 is complete when:**
1. ✅ train.py split into 4+ focused modules (inference, hmmlearn, evaluation, orchestrator)
2. ✅ All 33+ tests passing (no regressions)
3. ✅ Code coverage stable or improved
4. ✅ CLAUDE.md updated with new module structure
5. ✅ Each module documented with complete docstrings
6. ✅ run.py integration verified (train, regime commands work)
7. ✅ Backward compatibility: signals.py, Algo-Trading-Bot APIs unchanged
8. ✅ Atomic commits, one per module extraction
9. ✅ Regression tests (test_train_refactor.py) added and passing

## Post-Phase Actions

After Phase 3.1 is complete:

1. **Phase 3.2 (Dashboard Hardening)** can proceed in parallel (no dependencies on 3.1)
2. **Phase 3.3 (Documentation)** can proceed in parallel
3. **Phase 3.4 (Signal Combination)** depends on 3.1 complete (new signal_combination.py module uses hmmlearn.py, evaluation.py)

</verification>

<success_criteria>
**Measurable outcomes at end of Phase 3.1:**

1. **Functionality Preserved:** All 33+ tests pass; `python run.py train` and `python run.py regime` work without changes.

2. **Modularity Improved:** 
   - train.py: 2988 lines → 400-500 lines (86% reduction, thin wrapper)
   - hmmlearn.py: 400+ lines (training logic)
   - inference.py: 200+ lines (regime inference)
   - evaluation.py: 250+ lines (diagnostics)
   - orchestrator.py: 150+ lines (workflow)

3. **API Backward Compatibility:** 
   - `train(reload_pca_checkpoint_path=None)` signature unchanged
   - `rebuild_dashboard()` signature unchanged
   - No breaking changes to signals.py or downstream consumers

4. **Test Coverage:**
   - All existing tests still pass (no regressions)
   - 6+ new regression tests in test_train_refactor.py
   - Code coverage stable or improved

5. **Documentation:**
   - CLAUDE.md updated with refactored architecture
   - Each module has complete docstring header
   - Module responsibilities clearly documented

6. **Git History:**
   - Atomic commits: one per module extraction
   - Clear commit messages referencing requirements
   - All work tracked in git
</success_criteria>

<output>
After completion, create `.planning/phases/03-refactor/03-01-SUMMARY.md` documenting:
- Modules extracted (inference.py, hmmlearn.py, evaluation.py, orchestrator.py)
- Tests passing (count + list of test files)
- Code metrics (lines per module, train.py reduction)
- API backward compatibility verification
- Risk mitigation strategies applied
- Recommendations for Phase 3.2, 3.3, 3.4
</output>
