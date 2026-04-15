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
    from src.core.hmm_training import (fit_rolling_pca, select_states_bic, check_stability,
                              label_regimes, fit_regime_sv, fit_regime_garch)
    assert callable(fit_rolling_pca)
    assert callable(select_states_bic)
    assert callable(check_stability)
    assert callable(label_regimes)
    assert callable(fit_regime_sv)
    assert callable(fit_regime_garch)


def test_evaluation_imports():
    """Verify all evaluation functions can be imported."""
    from src.core.evaluation import (evaluate, compute_var_backtest, compute_var_backtest_garch,
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
    from train import train
    sig = inspect.signature(train)
    assert 'reload_pca_checkpoint_path' in sig.parameters
    # Check default value is None
    assert sig.parameters['reload_pca_checkpoint_path'].default is None


def test_rebuild_dashboard_signature():
    """Verify rebuild_dashboard() signature is unchanged."""
    from train import rebuild_dashboard
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
    from src.core.hmm_training import fit_rolling_pca
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
    from src.core.evaluation import kupiec_pof_test
    stat = kupiec_pof_test(n_obs=100, n_exc=5, alpha=0.05)
    assert isinstance(stat, (float, np.floating))


def test_christoffersen_test_returns_float():
    """Verify christoffersen_test returns numeric result."""
    from src.core.evaluation import christoffersen_test
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
    from train import train
    sig = inspect.signature(train)
    params = list(sig.parameters.keys())
    assert params == ['reload_pca_checkpoint_path']


def test_rebuild_dashboard_still_callable():
    """Verify rebuild_dashboard() is still callable."""
    from train import rebuild_dashboard
    # Just verify it's callable
    assert callable(rebuild_dashboard)


def test_no_circular_imports():
    """Verify no circular import issues."""
    # This will fail if there are circular imports
    import src.core.inference
    import src.core.hmm_training
    import src.core.evaluation
    import src.core.orchestrator
    import train
    # If we got here, no circular imports
    assert True
