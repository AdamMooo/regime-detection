"""Property tests for the tail-hazard mathematical core (Adam-written functions).

All tests skip while the core raises NotImplementedError; they go green as the
implementation lands. None of them reveals the recursion — they check the
defining properties (causality, decay, linearity) and likelihood correctness.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from tailhazard_core import bernoulli_nll, excitation_state


def _skip_if_unwritten(fn, *args):
    try:
        return fn(*args)
    except NotImplementedError:
        pytest.skip("core not yet written (Adam)")


def test_causality():
    rng = np.random.default_rng(0)
    e = (rng.random(500) < 0.05).astype(float)
    H1 = _skip_if_unwritten(excitation_state, e, 0.2)
    e2 = e.copy()
    e2[300] = 1.0 - e2[300]
    H2 = excitation_state(e2, 0.2)
    assert np.allclose(H1[:300], H2[:300]), "H before a perturbed future event must not change"
    assert not np.allclose(H1[300:], H2[300:]), "perturbation must actually propagate forward"


def test_single_event_decay():
    e = np.zeros(50)
    e[5] = 1.0
    beta = 0.3
    H = _skip_if_unwritten(excitation_state, e, beta)
    assert np.allclose(H[:5], 0.0)
    assert np.isclose(H[5], 1.0), "H[t] must include e_t (alpha = 1)"
    for m in (1, 3, 10):
        assert np.isclose(H[5 + m], np.exp(-beta * m)), "isolated event must decay as exp(-beta*m)"


def test_superposition():
    rng = np.random.default_rng(1)
    idx = rng.choice(400, size=40, replace=False)
    ea = np.zeros(400)
    eb = np.zeros(400)
    ea[idx[:20]] = 1.0
    eb[idx[20:]] = 1.0
    beta = 0.15
    Ha = _skip_if_unwritten(excitation_state, ea, beta)
    Hb = excitation_state(eb, beta)
    Hab = excitation_state(ea + eb, beta)
    assert np.allclose(Hab, Ha + Hb), "excitation must be linear in the event stream"


def test_nll_hand_computed():
    H = np.array([0.0, 1.0, 0.5])
    X = np.array([[0.0], [1.0], [-1.0]])
    y = np.array([0.0, 1.0, 0.0])
    params = np.array([-2.0, 1.5, 0.5])  # a, b, g
    u = params[0] + params[1] * H + X[:, 0] * params[2]
    p = 1.0 / (1.0 + np.exp(-u))
    expected = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    got = _skip_if_unwritten(bernoulli_nll, params, H, X, y)
    assert np.isclose(got, expected)


def test_nll_stable_extreme():
    H = np.array([0.0, 100.0])
    X = np.zeros((2, 0))
    y = np.array([1.0, 0.0])  # y=0 where p ~ 1: naive log(1-p) is -inf
    params = np.array([-100.0, 2.0])  # logits [-100, +100]
    got = _skip_if_unwritten(bernoulli_nll, params, H, X, y)
    assert np.isfinite(got), "NLL must be finite at extreme logits (stable form required)"
    assert got > 50  # each observation contributes ~|u| = 100 to the mean
