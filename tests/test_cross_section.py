"""Deterministic contracts for the Phase 11 construction gate.

These are written BEFORE the four statistics exist, and they are the spec for
them. Each one encodes a property that must hold on inputs whose answer is
known analytically — no data, no estimation, no judgement. A statistic that
cannot pass these cannot be trusted on 100 years of returns.

The four are unimplemented, so their contracts SKIP with a visible reason
rather than failing the suite. The skip list is the worklist.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import assert_causal
import cross_section
from cross_section import (
    common_vol,
    divergence,
    equicorrelation,
    mean_offdiag,
    structural_residual_share,
)


def _or_skip(fn, *args, **kwargs):
    """Run `fn`, or skip the test if Adam has not written it yet."""
    try:
        return fn(*args, **kwargs)
    except NotImplementedError as exc:
        pytest.skip(f"awaiting implementation: {fn.__name__} ({exc})")


def _random_correlation(n: int, seed: int) -> np.ndarray:
    """A genuine correlation matrix: unit diagonal, PSD, non-equicorrelated."""
    rng = np.random.default_rng(seed)
    a = rng.normal(size=(n, 4 * n))
    cov = a @ a.T
    d = np.sqrt(np.diag(cov))
    return cov / np.outer(d, d)


# ---------------------------------------------------------------------------
# structural_residual_share — the statistic the whole gate rests on
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rho", [-0.05, 0.0, 0.1, 0.5, 0.9])
@pytest.mark.parametrize("n", [3, 10, 25])
def test_exact_equicorrelation_gives_zero(rho, n):
    """THE first sanity test. If this fails, every later number is meaningless."""
    psi = _or_skip(structural_residual_share, equicorrelation(rho, n))
    assert psi == pytest.approx(0.0, abs=1e-10)


def test_identity_matrix_is_zero_not_nan():
    """R = I is 0/0 and must be handled, not discovered in production.

    R = I IS a member of the equicorrelation family, at rho-bar = 0, so the
    removable singularity resolves to "no departure" — 0.0. A silent nan here
    would propagate into every downstream summary as a hole rather than a
    number, and a nan that means "no structure" is indistinguishable from a nan
    that means "the window was short".
    """
    psi = _or_skip(structural_residual_share, np.eye(10))
    assert np.isfinite(psi), "R = I produced a non-finite Psi"
    assert psi == pytest.approx(0.0, abs=1e-10)


@pytest.mark.parametrize("eps", [1e-6, 1e-9, 1e-13])
def test_near_identity_is_numerically_stable(eps):
    """The real hazard is not R = I exactly, it is R almost-I.

    The denominator ||R - I||_F vanishes continuously, so a bare ratio explodes
    on an arbitrarily small perturbation. An exact-zero guard does not catch
    this; a tolerance does.
    """
    n = 10
    R = np.eye(n)
    R[0, 1] = R[1, 0] = eps
    psi = _or_skip(structural_residual_share, R)
    assert np.isfinite(psi), f"Psi blew up at eps={eps}"
    assert 0.0 <= psi <= 1.0


@pytest.mark.parametrize("seed", range(5))
def test_psi_lies_in_the_unit_interval(seed):
    psi = _or_skip(structural_residual_share, _random_correlation(10, seed))
    assert 0.0 <= psi <= 1.0


@pytest.mark.parametrize("seed", range(5))
def test_psi_matches_the_projection_identity(seed):
    """Psi^2 = 1 - N(N-1)*rho-bar^2 / ||R - I||_F^2.

    This holds only because rho-bar is the least-squares projection of R onto
    the equicorrelation family. It is the identity that licenses reading Psi as
    "the share of off-diagonal energy one scalar cannot explain" — so it is
    worth asserting rather than assuming.
    """
    n = 10
    R = _random_correlation(n, seed)
    psi = _or_skip(structural_residual_share, R)
    rho_bar = _or_skip(mean_offdiag, R)

    off_energy = np.sum((R - np.eye(n)) ** 2)
    expected = 1.0 - n * (n - 1) * rho_bar**2 / off_energy
    assert psi**2 == pytest.approx(expected, rel=1e-9)


def test_psi_is_invariant_to_row_column_permutation():
    """Relabelling the industries cannot change how much structure there is."""
    R = _random_correlation(10, seed=7)
    perm = np.random.default_rng(0).permutation(10)
    a = _or_skip(structural_residual_share, R)
    b = _or_skip(structural_residual_share, R[np.ix_(perm, perm)])
    assert a == pytest.approx(b, rel=1e-12)


# ---------------------------------------------------------------------------
# mean_offdiag
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(3))
def test_mean_offdiag_is_the_least_squares_projection(seed):
    """rho-bar must MINIMISE ||R - R_eq(rho)||_F, not merely summarise R.

    A grid search is a crude check and that is the point: it tests the property
    the interpretation needs, independently of the closed form.
    """
    n = 10
    R = _random_correlation(n, seed)
    rho_bar = _or_skip(mean_offdiag, R)

    def loss(rho):
        return np.sum((R - equicorrelation(rho, n)) ** 2)

    grid = np.linspace(rho_bar - 0.25, rho_bar + 0.25, 2001)
    assert loss(rho_bar) <= min(loss(r) for r in grid) + 1e-12


def test_mean_offdiag_excludes_the_diagonal():
    """A rho-bar that includes the unit diagonal is biased up by 1/N and would
    make every matrix look more coupled than it is."""
    R = equicorrelation(0.4, 10)
    assert _or_skip(mean_offdiag, R) == pytest.approx(0.4, abs=1e-12)


# ---------------------------------------------------------------------------
# common_vol / divergence
# ---------------------------------------------------------------------------


def test_divergence_rows_sum_to_zero():
    x = pd.DataFrame(
        np.random.default_rng(0).normal(size=(50, 10)),
        index=pd.date_range("2000-01-03", periods=50, freq="B"),
    )
    D = _or_skip(divergence, x)
    assert np.allclose(D.sum(axis=1).to_numpy(), 0.0, atol=1e-12)


def test_common_vol_is_nan_when_the_cross_section_is_incomplete():
    """A mean over the surviving subset is not comparable through time.

    Industries enter with different burn-in, so a c_t silently averaging 7 of
    10 columns would carry a level shift that looks exactly like a change in
    common volatility.
    """
    x = pd.DataFrame(
        np.ones((10, 4)),
        index=pd.date_range("2000-01-03", periods=10, freq="B"),
    )
    x.iloc[0, 2] = np.nan
    c = _or_skip(common_vol, x)
    assert np.isnan(c.iloc[0])
    assert c.iloc[1] == pytest.approx(1.0)


def test_common_vol_is_equal_weighted_not_cap_weighted():
    """Registered in the gate: an index-volatility baseline carries rho-bar by
    the variance identity, which is the quantity under test."""
    x = pd.DataFrame(
        [[0.0, 10.0]] * 5,
        index=pd.date_range("2000-01-03", periods=5, freq="B"),
    )
    assert _or_skip(common_vol, x).iloc[0] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Causal guard — cross_section.build() must not see the future
# ---------------------------------------------------------------------------


def test_cross_section_build_is_causal():
    rng = np.random.default_rng(0)
    panel = pd.DataFrame(
        rng.normal(0.0, 1.0, size=(600, 10)),
        index=pd.date_range("2000-01-03", periods=600, freq="B"),
        columns=[f"ind{i}" for i in range(10)],
    )
    assert_causal(cross_section.build, panel)


def test_rolling_correlations_are_trailing_only():
    """The matrix stamped at t uses observations up to t, never beyond."""
    rng = np.random.default_rng(1)
    z = pd.DataFrame(
        rng.normal(size=(200, 5)),
        index=pd.date_range("2000-01-03", periods=200, freq="B"),
    )
    cut = z.index[120]

    before = dict(cross_section.rolling_correlations(z, window=60))
    z2 = z.copy()
    z2.loc[z2.index > cut] = rng.normal(size=z2.loc[z2.index > cut].shape)
    after = dict(cross_section.rolling_correlations(z2, window=60))

    for date, R in before.items():
        if date <= cut:
            assert np.allclose(R, after[date]), f"correlation at {date} moved"
