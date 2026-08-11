"""Cross-sectional dependency structure — construction only (Phase 11 gate).

This module is a CONSTRUCTION GATE, not a signal. It tests whether the
dependency structure of the industry cross-section is mathematically redundant
with a single scalar (average pairwise correlation). It produces no reading, no
status and no maturity tag, and it does not spend the registered one-look.

Registered design: `.planning/phases/11-cross-section-structure/11-STAGE0-GATE.md`

The four statistics below are the whole experiment; everything else here is
plumbing. No empirical result has been computed from them.

Interpretation limit, carried from the gate (do not soften it in a write-up):
Psi > 0 says only that the correlation matrix is not exactly equicorrelated. It
does NOT establish a new economically meaningful dimension. It is consistent
with sector heterogeneity, with sampling noise, and with another representation
of the same underlying correlation structure. Only the E2 (non-redundancy) and
E4 (pattern-persistence) bars speak to that, and neither is computed here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from causal import realized_vol

W_SIGMA = 21  # registered in the Stage-0 gate; do not tune
_EQUICORR_TOL = 1e-12


# ---------------------------------------------------------------------------
# The four statistics. Specified by Adam 2026-08-11; contracts are binding.
# ---------------------------------------------------------------------------


def common_vol(x: pd.DataFrame) -> pd.Series:
    """c_t = (1/N) * sum_i x_it — the equal-weighted cross-sectional mean of log vols.

    EQUAL-weighted, deliberately: a cap-weighted mean (or index volatility)
    carries the coupling channel rho-bar by the variance identity
    sigma^2_index = sigma-bar^2 * [rho-bar + (1 - rho-bar)/N], which would put
    the very quantity this gate tests for redundancy against into the baseline.

    Returns a Series indexed like `x`. Dates where any industry is NaN
    (burn-in) must yield NaN, not a mean over the surviving subset — a c_t
    computed over a shrinking universe is not comparable through time.
    """
    return x.mean(axis=1, skipna=False)


def divergence(x: pd.DataFrame) -> pd.DataFrame:
    """D_it = x_it - c_t.

    Returns a frame shaped like `x`. Rows sum to ~0 BY CONSTRUCTION, which
    removes one degree of freedom: Cov(D) has rank <= N-1. That deficiency is
    an artifact of the definition and is never a finding.
    """
    return x.sub(common_vol(x), axis=0)


def mean_offdiag(R: np.ndarray) -> float:
    """rho-bar = mean of the off-diagonal entries of R.

    Not merely a convenience. rho-bar is the least-squares projection of R onto
    the one-parameter equicorrelation family: minimising
    sum_{i!=j} (R_ij - rho)^2 over rho gives exactly the off-diagonal mean.
    That projection property is what makes Psi below interpretable, and it is
    asserted in the tests.
    """
    R = np.asarray(R, dtype=float)
    n = R.shape[0]
    return float((R.sum() - np.trace(R)) / (n * (n - 1)))


def structural_residual_share(R: np.ndarray) -> float:
    """Psi = ||R - R_eq||_F / ||R - I||_F, with R_eq = (1-rho-bar)I + rho-bar*J.

    The fraction of off-diagonal structure a single scalar cannot express.
    Orthogonal to the redundancy hazard by construction, which is the only
    reason this statistic was chosen over an eigenvalue or density measure.

    Contract:
      * exact equicorrelation  -> 0.0
      * R = I                  -> 0.0, NOT NaN. R = I is a member of the
                                  equicorrelation family at rho-bar = 0, so the
                                  0/0 is removable and the answer is "no
                                  departure". Branch on it explicitly; do not
                                  let it arrive as a silent nan.
      * ||R - I||_F < _EQUICORR_TOL -> 0.0, for the same reason plus numerical
                                  stability: a vanishing denominator makes the
                                  ratio explode on noise.
      * range                  -> [0, 1]. Follows from the projection property
                                  of rho-bar:
                                     Psi^2 = 1 - N(N-1)*rho-bar^2 / ||R-I||_F^2
                                  Asserted in the tests as an identity.
    """
    R = np.asarray(R, dtype=float)
    n = R.shape[0]
    off_energy = float(np.sum((R - np.eye(n)) ** 2))
    if off_energy < _EQUICORR_TOL:
        return 0.0
    residual = float(np.sum((R - equicorrelation(mean_offdiag(R), n)) ** 2))
    return float(np.sqrt(residual / off_energy))


# ---------------------------------------------------------------------------
# Plumbing — generated scaffolding.
# ---------------------------------------------------------------------------


def build(panel: pd.DataFrame, window: int = W_SIGMA) -> pd.DataFrame:
    """x_it = log(trailing realized volatility of industry i over `window`).

    The causal construction this module is guarded on. Trailing-only by way of
    `causal.realized_vol`; no cross-sectional step here can see the future
    because every column is computed independently from its own past.

    Zero/NaN volatilities map to NaN rather than -inf: an industry with a flat
    return window is not "infinitely calm", it is unmeasured.
    """
    vols = panel.apply(lambda col: realized_vol(col, window=window))
    return np.log(vols.where(vols > 0))


def equicorrelation(rho: float, n: int) -> np.ndarray:
    """R_eq = (1-rho)I + rho*J — the one-parameter family Psi measures against."""
    return (1.0 - rho) * np.eye(n) + rho * np.ones((n, n))


def rolling_correlations(z: pd.DataFrame, window: int):
    """Yield (date, R) for each trailing window of `z` with no missing rows.

    Trailing and right-closed: the matrix stamped at date t uses observations
    up to and including t, never beyond.
    """
    cols = list(z.columns)
    for i in range(window - 1, len(z)):
        block = z.iloc[i - window + 1 : i + 1]
        if block.isna().any().any():
            continue
        yield z.index[i], block[cols].corr().to_numpy()
