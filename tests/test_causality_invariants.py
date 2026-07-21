"""Causality invariants for the ~4 functions that claim "no lookahead".

Each test perturbs the inputs from some index t onward and asserts the
function's output at indices strictly before t is unchanged. This is a
mechanical check for the class of bug found in the 2026-07-21 deep
review (CR-01, CR-03, CR-04): code that *claims* to use only past data
but actually leaks a future value backward.

Where a function's output at t is itself allowed to depend on the
value observed at t (e.g. expanding_standardize), the invariant is
"indices < t are unaffected". Where the row's own current value must
NOT be used (expanding_regime_vol, by construction, since returns[t]
is the outcome being traded on day t), the invariant is tightened to
"indices <= t are unaffected".

test_forward_backward_numpy_filtered_vs_smoothed also asserts smoothed
output DOES change for indices < t -- a negative control proving the
perturbation is large enough to matter, so a passing filtered-causal
assertion isn't just vacuously true.
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from hmmlearn.hmm import GaussianHMM

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.baselines.parametric_hmm import get_filtered_states
from src.core.hdp_hmm import forward_backward_numpy
from src.core.inference import expanding_regime_vol, expanding_standardize

T_PERTURB = 150


def _bumped(arr, t, scale=50.0, seed=0):
    """Copy of arr with a large perturbation injected into rows [t:]."""
    out = arr.copy()
    rng = np.random.default_rng(seed)
    out[t:] += scale * rng.standard_normal(out[t:].shape)
    return out


def test_expanding_standardize_causal():
    rng = np.random.default_rng(1)
    X = rng.standard_normal((300, 4))
    X_pert = _bumped(X, T_PERTURB)

    X_scaled, _, _ = expanding_standardize(X, min_warmup=0)
    X_scaled_pert, _, _ = expanding_standardize(X_pert, min_warmup=0)

    np.testing.assert_allclose(X_scaled[:T_PERTURB], X_scaled_pert[:T_PERTURB])
    # Sanity: the perturbation actually did something past that point.
    assert not np.allclose(X_scaled[T_PERTURB:], X_scaled_pert[T_PERTURB:])


def test_expanding_regime_vol_causal():
    rng = np.random.default_rng(2)
    returns = rng.standard_normal(300) * 0.01
    labels = rng.integers(0, 3, size=300)
    returns_pert = _bumped(returns, T_PERTURB, scale=5.0)

    vol = expanding_regime_vol(returns, labels, n_regimes=3, min_periods=10)
    vol_pert = expanding_regime_vol(returns_pert, labels, n_regimes=3, min_periods=10)

    # Stronger than "< t": row t's own return must not leak into row t's
    # own estimate, so index t itself is included in the unaffected range.
    np.testing.assert_allclose(vol[: T_PERTURB + 1], vol_pert[: T_PERTURB + 1])
    assert not np.allclose(vol[T_PERTURB + 1 :], vol_pert[T_PERTURB + 1 :])


def _toy_gaussian_hmm():
    model = GaussianHMM(n_components=2, covariance_type='diag')
    model.startprob_ = np.array([0.6, 0.4])
    model.transmat_ = np.array([[0.9, 0.1], [0.2, 0.8]])
    model.means_ = np.array([[0.0, 0.0], [3.0, 3.0]])
    model.covars_ = np.array([[1.0, 1.0], [1.0, 1.0]])
    return model


def test_get_filtered_states_causal():
    rng = np.random.default_rng(3)
    X = rng.standard_normal((200, 2))
    X_pert = _bumped(X, T_PERTURB, scale=10.0)
    model = _toy_gaussian_hmm()

    _, posteriors = get_filtered_states(model, X)
    _, posteriors_pert = get_filtered_states(model, X_pert)

    np.testing.assert_allclose(posteriors[:T_PERTURB], posteriors_pert[:T_PERTURB], atol=1e-10)
    assert not np.allclose(posteriors[T_PERTURB:], posteriors_pert[T_PERTURB:])


def _toy_hdp_params(K=2, D=2):
    rng = np.random.default_rng(4)
    beta = np.array([0.6, 0.4])
    return {
        'beta': beta,
        'trans_matrix': np.array([[0.9, 0.1], [0.2, 0.8]]),
        'init_probs': beta,
        'locs': rng.standard_normal((K, D)),
        'scale_diag': np.ones((K, D)),
        'K_max': K,
    }


def test_forward_backward_numpy_filtered_vs_smoothed():
    rng = np.random.default_rng(5)
    obs = rng.standard_normal((200, 2))
    obs_pert = _bumped(obs, T_PERTURB, scale=10.0)
    params = _toy_hdp_params()

    filtered, smoothed = forward_backward_numpy(obs, params)
    filtered_pert, smoothed_pert = forward_backward_numpy(obs_pert, params)

    # The causal claim: filtered (forward-pass-only) output before t is untouched.
    np.testing.assert_allclose(filtered[:T_PERTURB], filtered_pert[:T_PERTURB], atol=1e-10)

    # Negative control: smoothed is NOT causal by construction (uses the
    # backward pass over the full sequence), so it SHOULD change before t.
    # If this assertion ever failed, it would mean the perturbation is too
    # small to prove anything above -- i.e. the filtered-causal check would
    # be vacuous rather than a real test.
    assert not np.allclose(smoothed[:T_PERTURB], smoothed_pert[:T_PERTURB])


if __name__ == '__main__':
    sys.exit(pytest.main([__file__, '-v']))
