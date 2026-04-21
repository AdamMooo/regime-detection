"""Regression tests for train.py refactoring.

Verify that extraction of inference.py, hmm_training.py, evaluation.py, orchestrator.py
did not break API compatibility or behavior. All tests should pass before merging refactoring.
"""

import pytest
import numpy as np
import pandas as pd
import inspect


def test_inference_imports():
    """Verify all inference functions can be imported."""
    from src.core.inference import expanding_standardize, StudentTHMM, _fit_hmm, filtered_probs, filtered_labels
    assert callable(expanding_standardize)
    assert callable(_fit_hmm)
    assert callable(filtered_probs)
    assert callable(filtered_labels)


def test_hmmlearn_imports():
    """Verify all hmm_training functions can be imported."""
    from src.core.hmm_training import (select_states_bic, check_stability,
                              label_regimes, fit_regime_sv, fit_regime_garch)
    from src.core.pca_utils import fit_rolling_pca
    assert callable(fit_rolling_pca)
    assert callable(select_states_bic)
    assert callable(check_stability)
    assert callable(label_regimes)
    assert callable(fit_regime_sv)
    assert callable(fit_regime_garch)


def test_evaluation_imports():
    """Verify all evaluation functions can be imported."""
    from src.core.evaluation import evaluate
    from src.core.var_backtesting import (compute_var_backtest, compute_var_backtest_garch,
                            kupiec_pof_test, christoffersen_test)
    assert callable(evaluate)
    assert callable(compute_var_backtest)
    assert callable(compute_var_backtest_garch)
    assert callable(kupiec_pof_test)
    assert callable(christoffersen_test)


def test_orchestrator_imports():
    """Verify orchestrator functions can be imported."""
    from src.core.orchestrator import walk_forward
    assert callable(walk_forward)


def test_train_signature():
    """Verify train() signature is unchanged."""
    from scripts.pipelines.train import train
    sig = inspect.signature(train)
    assert 'reload_pca_checkpoint_path' in sig.parameters
    # Check default value is None
    assert sig.parameters['reload_pca_checkpoint_path'].default is None


def test_rebuild_dashboard_signature():
    """Verify rebuild_dashboard() signature is unchanged."""
    from scripts.pipelines.train import rebuild_dashboard
    sig = inspect.signature(rebuild_dashboard)
    # Should have no required parameters
    assert len([p for p in sig.parameters.values()
                if p.default == inspect.Parameter.empty]) == 0


def test_expanding_standardize_from_inference():
    """Verify expanding_standardize behavior from inference module."""
    from src.core.inference import expanding_standardize
    X = np.random.randn(500, 5)
    X_scaled, mean_f, std_f = expanding_standardize(X, min_warmup=50)

    assert X_scaled.shape == X.shape
    assert np.isnan(X_scaled[:50]).all()  # First 50 rows are NaN
    assert not np.isnan(X_scaled[100:]).any()  # Rest should have values
    assert isinstance(mean_f, np.ndarray)
    assert isinstance(std_f, np.ndarray)


def test_student_t_hmm_from_inference():
    """Verify StudentTHMM class works from inference module."""
    from src.core.inference import StudentTHMM
    model = StudentTHMM(n_components=2)
    X = np.random.randn(100, 3)
    model.fit(X)

    assert hasattr(model, 'transmat_')
    assert hasattr(model, 'means_')
    assert hasattr(model, 'covars_')
    assert model.transmat_.shape == (2, 2)


def test_filtered_probs_shape():
    """Verify filtered_probs returns expected shape."""
    from src.core.inference import StudentTHMM, filtered_probs
    import numpy as np
    X = np.random.randn(100, 3)
    model = StudentTHMM(n_components=2)
    model.fit(X)

    probs = filtered_probs(model, X)
    assert probs.shape == (100, 2)
    # Each row should sum to ~1
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-10)


def test_filtered_labels_basic():
    """Verify filtered_labels returns regime labels."""
    from src.core.inference import StudentTHMM, filtered_labels
    X = np.random.randn(100, 3)
    model = StudentTHMM(n_components=2)
    model.fit(X)

    labels = filtered_labels(model, X)
    assert labels.shape == (100,)
    assert set(labels).issubset({0, 1})


def test_fit_rolling_pca_output():
    """Verify fit_rolling_pca returns expected structure."""
    from src.core.pca_utils import fit_rolling_pca
    X_scaled = np.random.randn(300, 5)
    pcs, mr, valid_mask, n_selected, pca = fit_rolling_pca(X_scaled, window=50)

    assert pcs.shape[0] > 0
    assert pcs.shape[1] > 0
    assert mr.shape[0] == pcs.shape[0]
    assert valid_mask.shape == (300,)
    assert isinstance(n_selected, (int, np.integer))
    assert n_selected > 0


def test_select_states_bic_best_selection():
    """Verify select_states_bic returns best model."""
    import os
    from src.core.hmm_training import select_states_bic
    from src.config import DATA_DIR

    # Create data directory if it doesn't exist (for test environments)
    os.makedirs(DATA_DIR, exist_ok=True)

    X = np.random.randn(100, 3)
    best_k, best_model, bic_df = select_states_bic(X, n_range=[2, 3])

    assert best_k in [2, 3]
    assert best_model is not None
    assert hasattr(best_model, 'transmat_')
    assert len(bic_df) == 2  # One row per K


def test_evaluate_runs_without_error():
    """Verify evaluate function runs."""
    from src.core.evaluation import evaluate
    import pandas as pd

    dates = pd.date_range('2020-01-01', periods=100)
    market = pd.DataFrame({'VIX': np.random.uniform(10, 30, 100)}, index=dates)
    labels = np.random.randint(0, 2, 100)
    name_map = {0: 'Low', 1: 'High'}
    spy_ret = pd.Series(np.random.randn(100) * 0.01, index=dates)

    # Should not raise
    evaluate(market, labels, name_map, spy_ret)


def test_kupiec_pof_test_returns_float():
    """Verify kupiec_pof_test returns numeric result."""
    from src.core.var_backtesting import kupiec_pof_test
    stat = kupiec_pof_test(n_obs=100, n_exc=5, alpha=0.05)
    assert isinstance(stat, (float, np.floating))


def test_christoffersen_test_returns_float():
    """Verify christoffersen_test returns numeric result."""
    from src.core.var_backtesting import christoffersen_test
    import pandas as pd

    dates = pd.date_range('2020-01-01', periods=100)
    spy_ret = pd.Series(np.random.randn(100) * 0.01, index=dates)
    labels = np.random.randint(0, 2, 100)
    name_map = {0: 'Low', 1: 'High'}

    stat = christoffersen_test(spy_ret, labels, name_map, alpha=0.05)
    # May return nan in some cases
    assert isinstance(stat, (float, np.floating))


def test_walk_forward_basic():
    """Verify walk_forward returns expected structure."""
    from src.core.orchestrator import walk_forward
    import pandas as pd

    dates = pd.date_range('2015-01-01', periods=2000)
    features = pd.DataFrame(np.random.randn(2000, 3), index=dates)
    market = pd.DataFrame({'VIX': np.random.uniform(10, 30, 2000),
                           'SPY_Close': np.cumprod(1 + np.random.randn(2000) * 0.005)},
                          index=dates)

    valid, name_map = walk_forward(market, features, n_states=2, n_pca=2, mode='expanding')
    assert isinstance(valid, pd.Series)
    assert isinstance(name_map, dict)
    assert len(valid) > 0


def test_train_still_callable():
    """Verify train() is still callable and has correct signature."""
    from scripts.pipelines.train import train
    sig = inspect.signature(train)
    params = list(sig.parameters.keys())
    assert params == ['reload_pca_checkpoint_path']


def test_rebuild_dashboard_still_callable():
    """Verify rebuild_dashboard() is still callable."""
    from scripts.pipelines.train import rebuild_dashboard
    # Just verify it's callable
    assert callable(rebuild_dashboard)


def test_no_circular_imports():
    """Verify no circular import issues."""
    # This will fail if there are circular imports
    import src.core.inference
    import src.core.hmm_training
    import src.core.evaluation
    import src.core.orchestrator
    import scripts.pipelines.train as train
    # If we got here, no circular imports
    assert True


# ===================================================================
# Phase 6 MODEL-03: Module size gate + new module smoke-checks
# ===================================================================

from pathlib import Path


def test_module_size():
    """Assert every src/core/*.py file is <= 500 lines (MODEL-03 gate).

    hdp_hmm.py is excluded — it is production inference code retained by
    human override in Plan 01 and accepted as a documented exception per
    docs/MODEL_CARD.md.
    """
    core = Path(__file__).parent.parent / 'src' / 'core'
    # hdp_hmm.py is accepted as >500-line exception (Plan 01 human override)
    ACCEPTED_EXCEPTIONS = {'hdp_hmm.py'}
    oversized = []
    for py in sorted(core.glob('*.py')):
        if py.name == '__init__.py':
            continue
        if py.name in ACCEPTED_EXCEPTIONS:
            continue
        n = len(py.read_text(encoding='utf-8').splitlines())
        if n > 500:
            oversized.append(f"{py.name}: {n} lines")
    assert not oversized, f"Modules exceed 500 lines: {oversized}"


def test_pca_utils_exposes_fit_rolling_pca():
    """pca_utils.py must export fit_rolling_pca as a callable."""
    from src.core.pca_utils import fit_rolling_pca
    assert callable(fit_rolling_pca)


def test_pca_utils_exposes_linearized_sv():
    """pca_utils.py must export LinearizedSV as a class."""
    from src.core.pca_utils import LinearizedSV
    assert isinstance(LinearizedSV, type)


def test_var_backtesting_exposes_symbols():
    """var_backtesting.py must export all six VaR symbols."""
    from src.core.var_backtesting import (
        compute_var_backtest,
        compute_var_backtest_garch,
        compare_var_methods,
        kupiec_pof_test,
        christoffersen_test,
        warn_static_var_deprecated,
    )
    assert callable(compute_var_backtest)
    assert callable(compute_var_backtest_garch)
    assert callable(compare_var_methods)
    assert callable(kupiec_pof_test)
    assert callable(christoffersen_test)
    assert callable(warn_static_var_deprecated)


def test_forward_returns_exposes_symbols():
    """forward_returns.py must export both forward-return analysis functions."""
    from src.core.forward_returns import (
        compute_forward_return_analysis,
        analyze_forward_returns,
    )
    assert callable(compute_forward_return_analysis)
    assert callable(analyze_forward_returns)


def test_no_var_or_forward_in_evaluation_all():
    """evaluation.__all__ must contain only 'evaluate' — no moved symbols."""
    import src.core.evaluation as e
    moved_symbols = {
        'compute_var_backtest', 'compute_var_backtest_garch',
        'compare_var_methods', 'kupiec_pof_test', 'christoffersen_test',
        'warn_static_var_deprecated', 'compute_forward_return_analysis',
        'analyze_forward_returns',
    }
    eval_all = set(e.__all__ or [])
    leaked = eval_all & moved_symbols
    assert not leaked, f"evaluation.__all__ still contains moved symbols: {leaked}"
    assert 'evaluate' in eval_all, "evaluation.__all__ must still contain 'evaluate'"


def test_hmm_training_imports_pca_from_pca_utils():
    """hmm_training.py must import fit_rolling_pca directly from pca_utils (D-12)."""
    core = Path(__file__).parent.parent / 'src' / 'core'
    text = (core / 'hmm_training.py').read_text(encoding='utf-8')
    assert 'from src.core.pca_utils import fit_rolling_pca' in text, (
        "hmm_training.py must contain 'from src.core.pca_utils import fit_rolling_pca' "
        "(D-12: direct import, no re-export indirection)"
    )
