import numpy as np
import pandas as pd
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from allocation import (CovProviders, ExpandingCov, decision_positions, erc_weights,
                        ewma_cov_track, simulate_multi, vol_scale)


def rc(w, cov):
    return w * (cov @ w)


def make_cov(vols, corr):
    corr = np.asarray(corr, dtype=float)
    d = np.diag(vols)
    return d @ corr @ d


CALM = make_cov([0.143, 0.065, 0.15], [[1, -0.1, 0.05], [-0.1, 1, 0.1], [0.05, 0.1, 1]])
STRESS = make_cov([0.25, 0.088, 0.15], [[1, -0.3, 0.0], [-0.3, 1, 0.15], [0.0, 0.15, 1]])


def test_erc_uncapped_equal_rc():
    for cov in (CALM, STRESS):
        w = erc_weights(cov, caps=np.ones(3))
        assert np.isclose(w.sum(), 1.0)
        contribs = rc(w, cov)
        assert np.abs(contribs - contribs.mean()).max() < 1e-8


def test_erc_caps_respected_and_free_rc_equal():
    caps = np.array([0.75, 0.75, 0.25])
    cov = make_cov([0.20, 0.20, 0.02], np.eye(3))  # low-vol asset wants >> 25%
    w = erc_weights(cov, caps)
    assert np.isclose(w.sum(), 1.0)
    assert (w <= caps + 1e-9).all()
    assert np.isclose(w[2], 0.25)
    free = rc(w, cov)[:2]
    assert np.abs(free - free.mean()).max() < 1e-8


def test_erc_random_matrices_converge():
    rng = np.random.default_rng(7)
    for _ in range(50):
        A = rng.normal(size=(3, 3))
        cov = A @ A.T + 0.05 * np.eye(3)
        w = erc_weights(cov, caps=np.array([0.75, 0.75, 0.25]))
        assert np.isclose(w.sum(), 1.0) and (w >= 0).all()


def test_vol_scale_scale_down_only():
    w = np.array([0.4, 0.5, 0.1])
    sig = np.sqrt(w @ STRESS @ w)
    assert np.isclose(vol_scale(w, STRESS, target=0.08), min(1.0, 0.08 / sig))
    assert vol_scale(w, CALM * 1e-6, target=0.08) == 1.0


def test_expanding_cov_matches_pandas():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(400, 2))
    X[50:60, 1] = np.nan
    mask = ~np.isnan(X).any(axis=1)
    ec = ExpandingCov(X, mask)
    df = pd.DataFrame(X[mask])
    for t in (100, 399):
        n, c = ec.cov(t)
        sub = df.iloc[:n]
        assert np.allclose(c, sub.cov().to_numpy())


def test_ewma_burn_in_and_psd():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(600, 3)) * 0.01
    mask = np.ones(600, dtype=bool)
    track = ewma_cov_track(X, mask, lam=0.97, burn=250)
    assert np.isnan(track[248]).all()
    assert not np.isnan(track[260]).any()
    eig = np.linalg.eigvalsh(track[599])
    assert (eig > -1e-12).all()


def test_conditional_activation_and_shrinkage():
    rng = np.random.default_rng(3)
    T = 3000
    X = np.column_stack([rng.normal(0, 0.01, T), rng.normal(0, 0.005, T),
                         np.full(T, np.nan)])
    label = np.full(T, -1)
    label[1000:] = (np.arange(2000) // 100) % 2  # alternating 100d blocks
    prov = CovProviders(X, label, min_state_days=500, shrink=0.5)
    assert prov.era(2999) == 1  # no gold -> era-2 never starts
    t_early = 1150  # ~75 stressed days seen -> below activation
    assert np.allclose(prov.conditional(t_early, 1), prov.unconditional(t_early))
    t_late = 2999
    cu = prov.unconditional(t_late)
    cs = prov.state[(1, 1)].cov(t_late)[1]
    assert np.allclose(prov.conditional(t_late, 1), 0.5 * cu + 0.5 * cs)


def test_simulate_multi_delay_and_costs():
    T = 6
    W = np.zeros((T, 3))
    W[2:, 0] = 0.5  # decided at t=2
    R = np.full((T, 3), 0.01)
    R[:, 1:] = 0.0
    rf = np.zeros(T)
    ret, W_exec = simulate_multi(W, R, rf, cost_bps=100.0, delay=2)
    assert np.allclose(W_exec[:4, 0], 0.0) and np.allclose(W_exec[4:, 0], 0.5)
    assert np.isclose(ret[4], 0.5 * 0.01 - 0.5 * 100 * 1e-4)  # entry day pays cost
    assert np.isclose(ret[5], 0.5 * 0.01)


def test_decision_positions_monthly_plus_flips():
    dates = pd.date_range("2020-01-01", periods=90, freq="B")
    label = np.zeros(90, dtype=int)
    label[40:60] = 1
    score = np.ones(90, dtype=bool)
    pos = decision_positions(dates, label, score)
    assert 0 in pos and 40 in pos and 60 in pos
    months = dates[pos].to_period("M")
    assert len(set(months)) >= 4  # every month represented
