import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from backtest import fko_fee, sma_weights, strategy_returns, vol_target_weights


def test_fko_fee_identical_series_is_zero():
    rng = np.random.default_rng(0)
    r = rng.normal(0.0004, 0.01, 2000)
    assert abs(fko_fee(r, r, gamma=10.0)) < 1e-6


def test_fko_fee_recovers_constant_spread():
    rng = np.random.default_rng(1)
    r_b = rng.normal(0.0004, 0.01, 2000)
    delta = 0.0002
    r_a = r_b + delta
    fee = fko_fee(r_a, r_b, gamma=10.0)
    assert abs(fee - delta * 252 * 1e4) < 1.0


def test_strategy_returns_delay_is_causal():
    rng = np.random.default_rng(2)
    r = rng.normal(0, 0.01, 500)
    rf = np.zeros(500)
    w = rng.uniform(0, 1, 500)
    base = strategy_returns(w, r, rf)
    w2 = w.copy()
    w2[300:] = 0.0
    pert = strategy_returns(w2, r, rf)
    # weight change at t=300 first affects returns at t=301 (1-day delay)
    assert np.allclose(base[:301], pert[:301])
    assert not np.allclose(base[301:], pert[301:])


def test_strategy_returns_costs_reduce_pnl():
    rng = np.random.default_rng(3)
    r = rng.normal(0.0005, 0.01, 500)
    rf = np.zeros(500)
    w = (rng.random(500) > 0.5).astype(float)
    gross = strategy_returns(w, r, rf, cost_bps=0.0)
    net = strategy_returns(w, r, rf, cost_bps=10.0)
    assert net.sum() < gross.sum()


def test_weight_functions_are_causal_and_bounded():
    rng = np.random.default_rng(4)
    r = rng.normal(0.0003, 0.012, 800)
    for fn in (vol_target_weights, sma_weights):
        w = fn(r)
        assert np.all((w >= 0) & (w <= 1.0))
        r2 = r.copy()
        r2[600:] -= 0.05
        w2 = fn(r2)
        assert np.allclose(w[:600], w2[:600])
