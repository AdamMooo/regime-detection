import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from regime_factor import beta_sort_factor, mimicking_factor, regime_innovation


def _planted(T=400, N=10, window=60, noise=0.002, seed=0):
    """Assets with known loadings on a latent innovation g: R_i,t = beta_i * g_t + eps."""
    rng = np.random.default_rng(seed)
    g = rng.normal(0.0, 0.02, T)                       # the latent regime innovation
    betas = np.linspace(-1.0, 1.0, N)                  # known cross-sectional loadings
    R = betas[None, :] * g[:, None] + rng.normal(0.0, noise, (T, N))
    return R, g


def test_regime_innovation_diff_is_first_difference():
    s = np.array([0.0, 1.0, 0.5, 2.0])
    d = regime_innovation(s, "diff")
    assert np.isnan(d[0])
    assert np.allclose(d[1:], [1.0, -0.5, 1.5])


def test_beta_sort_recovers_planted_factor():
    R, g = _planted()
    reg = beta_sort_factor(R, g, window=60, frac=0.3)["reg"]
    ok = np.isfinite(reg)
    # long high-beta / short low-beta => REG tracks +g strongly
    assert np.corrcoef(reg[ok], g[ok])[0, 1] > 0.9


def test_mimicking_recovers_planted_factor():
    R, g = _planted()
    reg = mimicking_factor(R, g, window=60)["reg"]
    ok = np.isfinite(reg)
    assert np.corrcoef(reg[ok], g[ok])[0, 1] > 0.9


def _perturb_future(R, g, t0, seed):
    """Random (not constant) future shock — a constant cancels in a long-short spread."""
    rng = np.random.default_rng(seed)
    Rp, gp = R.copy(), g.copy()
    Rp[t0 + 1:] += rng.normal(0.0, 0.05, Rp[t0 + 1:].shape)
    gp[t0 + 1:] += rng.normal(0.0, 0.05, gp[t0 + 1:].shape)
    return Rp, gp


def test_beta_sort_is_causal():
    R, g = _planted(seed=1)
    t0 = 250
    base = beta_sort_factor(R, g, window=60)["reg"]
    Rp, gp = _perturb_future(R, g, t0, seed=11)
    pert = beta_sort_factor(Rp, gp, window=60)["reg"]
    assert np.allclose(base[:t0 + 1], pert[:t0 + 1], equal_nan=True)
    assert not np.allclose(base[t0 + 1:], pert[t0 + 1:], equal_nan=True)


def test_mimicking_is_causal():
    R, g = _planted(seed=2)
    t0 = 250
    base = mimicking_factor(R, g, window=60)["reg"]
    Rp, gp = _perturb_future(R, g, t0, seed=12)
    pert = mimicking_factor(Rp, gp, window=60)["reg"]
    assert np.allclose(base[:t0 + 1], pert[:t0 + 1], equal_nan=True)
    assert not np.allclose(base[t0 + 1:], pert[t0 + 1:], equal_nan=True)
