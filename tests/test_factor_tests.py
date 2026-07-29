"""Validation of the cross-sectional asset-pricing tests against KNOWN results.

The GRS constant is the classic thing to get subtly wrong, so we validate the null distribution by
simulation (size ~ 5%) rather than trusting a single p-value.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from factor_tests import fama_macbeth, factor_spanning, grs_test, time_series_regression


def _sim(T, N, K, alpha=None, premium=None, seed=0):
    """Simulate R_i = alpha_i + beta_i' F + eps_i with factors that carry a known premium.
    premium (K,) sets each factor's per-period mean; alpha (N,) injects pricing errors (default 0)."""
    rng = np.random.default_rng(seed)
    premium = np.zeros(K) if premium is None else np.asarray(premium)
    alpha = np.zeros(N) if alpha is None else np.asarray(alpha)
    F = rng.normal(premium, 0.04, size=(T, K))            # factors ~ 4%/mo vol around the premium
    betas = rng.uniform(0.5, 1.5, size=(N, K))
    eps = rng.normal(0, 0.03, size=(T, N))                # idiosyncratic
    R = alpha + F @ betas.T + eps
    return R, F, betas


def test_grs_null_size_is_five_percent():
    # Under H0 (all alpha = 0) the GRS stat must be F(N, T-N-K)-distributed => rejects ~5% of the
    # time at the 5% level. A wrong scaling constant would blow the size. 400 sims, small panel.
    N, K, T, sims = 5, 1, 200, 400
    rejects = 0
    for s in range(sims):
        R, F, _ = _sim(T, N, K, seed=1000 + s)
        if grs_test(R, F)["p_value"] < 0.05:
            rejects += 1
    size = rejects / sims
    assert 0.02 <= size <= 0.09, f"GRS empirical size {size:.3f} off 5% -> constant likely wrong"


def test_grs_rejects_large_injected_alpha():
    # Inject a big, uniform pricing error -> GRS must reject decisively.
    R, F, _ = _sim(T=600, N=10, K=2, alpha=np.full(10, 0.02), seed=7)
    assert grs_test(R, F)["p_value"] < 1e-4


def test_grs_does_not_reject_when_prices_exactly():
    # Exact factor structure, alpha = 0 -> should not reject at the 1% level on one large sample.
    R, F, _ = _sim(T=800, N=10, K=2, seed=3)
    assert grs_test(R, F)["p_value"] > 0.01


def test_fama_macbeth_recovers_known_premium():
    # If the factors carry a known premium, FM's estimated premia should recover it, and the
    # intercept should be ~0 when the model prices the assets (alpha = 0 by construction).
    prem = np.array([0.007, 0.003])
    R, F, _ = _sim(T=2000, N=25, K=2, premium=prem, seed=11)
    out = fama_macbeth(R, F)
    # names: [intercept, factor0, factor1]
    assert abs(out["premia"][0]) < 0.002, "intercept should be ~0 under exact pricing"
    assert np.allclose(out["premia"][1:], prem, atol=0.003), out["premia"][1:]


def test_fama_macbeth_flags_intercept_when_mispriced():
    # A common non-zero alpha across assets shows up as a nonzero cross-sectional intercept.
    R, F, _ = _sim(T=2000, N=25, K=1, alpha=np.full(25, 0.01), premium=[0.006], seed=5)
    out = fama_macbeth(R, F)
    assert out["premia"][0] > 0.004 and abs(out["tstat"][0]) > 2


def test_factor_spanning_detects_redundant_and_priced():
    rng = np.random.default_rng(2)
    T = 1500
    a = rng.normal(0.006, 0.04, T)                        # base factor
    b_spanned = 1.3 * a + rng.normal(0, 0.001, T)         # spanned: ~ linear in a, ~0 own alpha
    b_priced = 0.7 * a + 0.005 + rng.normal(0, 0.01, T)   # carries +0.5%/period beyond a

    sp = factor_spanning(b_spanned, a.reshape(-1, 1))
    pr = factor_spanning(b_priced, a.reshape(-1, 1))
    assert abs(sp["t_alpha"]) < 2.0 and sp["r2"] > 0.9, sp     # redundant
    assert pr["t_alpha"] > 3.0, pr                              # not spanned


def test_time_series_regression_shapes_and_recovery():
    R, F, betas = _sim(T=3000, N=8, K=3, seed=9)
    alpha, bhat, resid = time_series_regression(R, F)
    assert alpha.shape == (8,) and bhat.shape == (8, 3) and resid.shape == (3000, 8)
    assert np.allclose(bhat, betas, atol=0.05)                 # recovers the true betas (~3.6 SE)
