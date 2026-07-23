import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jumpmodel import _cost, _dp_assign, build_features, filter_states, fit_jump_model


def _synthetic_two_state(T=3000, seed=7, p_stay=(0.995, 0.99)):
    rng = np.random.default_rng(seed)
    s = np.empty(T, dtype=int)
    s[0] = 0
    for t in range(1, T):
        stay = rng.random() < p_stay[s[t - 1]]
        s[t] = s[t - 1] if stay else 1 - s[t - 1]
    mu = np.where(s == 0, 0.0006, -0.0010)
    sig = np.where(s == 0, 0.007, 0.020)
    r = rng.normal(mu, sig)
    return r, s


def _zscore(X):
    return (X - X.mean(axis=0)) / X.std(axis=0)


def test_lambda_zero_is_kmeans_assignment():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 3))
    mu = rng.normal(size=(2, 3))
    s, _ = _dp_assign(_cost(X, mu), lam=0.0)
    assert np.array_equal(s, _cost(X, mu).argmin(axis=1))


def test_huge_lambda_gives_single_state():
    r, _ = _synthetic_two_state()
    X = _zscore(build_features(r).to_numpy()[200:])
    _, s, _, _ = fit_jump_model(X, k=2, lam=1e9, n_init=3)
    assert len(np.unique(s)) == 1


def test_dp_matches_brute_force():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(8, 2))
    mu = rng.normal(size=(2, 2))
    C = _cost(X, mu)
    lam = 0.7
    s_dp, obj_dp = _dp_assign(C, lam)
    best = np.inf
    for seq in itertools.product(range(2), repeat=8):
        seq = np.array(seq)
        obj = C[np.arange(8), seq].sum() + lam * (seq[1:] != seq[:-1]).sum()
        best = min(best, obj)
    assert np.isclose(obj_dp, best)


def test_identification_convention():
    r, _ = _synthetic_two_state()
    X = _zscore(build_features(r).to_numpy()[200:])
    mu, _, _, _ = fit_jump_model(X, k=2, lam=20.0, n_init=5)
    assert mu[0, 0] < mu[1, 0]


def test_recovers_planted_regimes_within_lambda_grid():
    # BAC(lambda) is non-monotone (balanced-split local optimum at low lambda,
    # over-smoothing at high lambda) — the capability claim is that SOME grid
    # value recovers truth; picking it causally is the CV protocol's job.
    r, s_true = _synthetic_two_state()
    X = _zscore(build_features(r).to_numpy()[200:])
    st = s_true[200:]
    best = 0.0
    for lam in (50.0, 100.0, 200.0, 400.0):
        _, s_fit, _, _ = fit_jump_model(X, k=2, lam=lam, n_init=8, seed=1)
        if len(np.unique(s_fit)) < 2:
            continue
        bac = ((s_fit == st)[st == 0].mean() + (s_fit == st)[st == 1].mean()) / 2
        best = max(best, bac)
    assert best > 0.80


def test_nan_input_rejected():
    X = np.random.default_rng(0).normal(size=(50, 3))
    X[0, 0] = np.nan
    try:
        fit_jump_model(X, k=2, lam=1.0, n_init=1)
    except ValueError:
        return
    raise AssertionError("expected ValueError on NaN input")


def test_filter_states_is_causal():
    r, _ = _synthetic_two_state(T=800)
    X = _zscore(build_features(r).to_numpy()[200:])
    mu, _, _, w = fit_jump_model(X, k=2, lam=20.0, n_init=3)
    Xw = X * np.sqrt(w)
    s_a, _ = filter_states(Xw, mu, lam=20.0)
    X_pert = Xw.copy()
    X_pert[400:, 0] += 50.0  # push hard toward the high-downside-dev (stressed) center
    s_b, _ = filter_states(X_pert, mu, lam=20.0)
    assert np.array_equal(s_a[:400], s_b[:400])
    assert (s_b[450:] == 1).all()


def test_filter_states_chaining_equivalence():
    # filtering [A;B] in one pass == filtering A, then B seeded with A's V_end
    r, _ = _synthetic_two_state(T=1000)
    X = _zscore(build_features(r).to_numpy()[200:])
    mu, _, _, w = fit_jump_model(X, k=2, lam=50.0, n_init=3)
    X = X * np.sqrt(w)
    s_full, _ = filter_states(X, mu, lam=50.0)
    s_a, V_end = filter_states(X[:500], mu, lam=50.0)
    s_b, _ = filter_states(X[500:], mu, lam=50.0, V0=V_end)
    assert np.array_equal(s_full, np.concatenate([s_a, s_b]))


def test_filter_states_accumulates_evidence():
    # a sustained small shift toward the other center must eventually flip the
    # filtered state even when no single day clears lam (greedy rule would freeze)
    mu = np.array([[0.0], [3.0]])
    X = np.concatenate([np.full(50, 0.0), np.full(200, 2.0)])[:, None]
    lam = 100.0
    s, _ = filter_states(X, mu, lam)
    assert s[0] == 0 and s[-1] == 1


def test_build_features_is_causal():
    rng = np.random.default_rng(3)
    r = rng.normal(0, 0.01, size=600)
    f_a = build_features(r).to_numpy()
    r_pert = r.copy()
    r_pert[300:] -= 0.05
    f_b = build_features(r_pert).to_numpy()
    assert np.allclose(f_a[:300], f_b[:300], equal_nan=True)
    assert not np.allclose(f_a[300:], f_b[300:], equal_nan=True)


def test_k3_fast_path_matches_general_dp():
    from jumpmodel import _dp_assign_general, _dp_assign_k3
    rng = np.random.default_rng(11)
    for lam in (0.0, 0.5, 5.0, 50.0):
        C = rng.random((400, 3)) * 3.0
        s_fast, obj_fast = _dp_assign_k3(C, lam)
        s_gen, obj_gen = _dp_assign_general(C, lam)
        assert abs(obj_fast - obj_gen) < 1e-9
        assert np.array_equal(s_fast, s_gen)
