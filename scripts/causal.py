"""Shared causal primitives (D-20).

Built ONCE here and reused by every signal + the OOS harness, so there is a
single audited implementation of each look-ahead-free construction rather than
one re-derivation per signal. Every function in this module is causal: the value
at t uses only data through t. If a function ever needs the future, it does not
belong here.

Volatility signal (Phase 1.5) is the first consumer; later signals import the
same primitives.
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def ewma_vol(r: pd.Series, lam: float = 0.94, burn_in: int = TRADING_DAYS) -> pd.Series:
    """Annualised EWMA volatility, causal (RiskMetrics / IGARCH).

        sigma2_t = lam * sigma2_{t-1} + (1 - lam) * r_t**2

    Seeded with the year-1 sample variance; NaN through the burn-in window.
    """
    x = r.to_numpy(dtype=float)
    r2 = x * x
    n = len(x)
    sig2 = np.full(n, np.nan)
    prev = float(np.nanvar(x[:burn_in]))
    for t in range(burn_in, n):
        prev = lam * prev + (1.0 - lam) * r2[t]
        sig2[t] = prev
    vol = np.sqrt(sig2) * np.sqrt(TRADING_DAYS)
    return pd.Series(vol, index=r.index, name="vol_annual")


def realized_vol(r: pd.Series, window: int = 21) -> pd.Series:
    """Annualised trailing realized volatility over a rolling window, causal.

    A LIGHTLY-smoothed vol series (short window) — the right input for the
    persistence/half-life estimator, which must read the market's mean-reversion
    speed, not the ~11-day smoothing memory that the lam=0.94 EWMA bakes in.
    """
    return (r.rolling(window).std() * np.sqrt(TRADING_DAYS)).rename("realized_vol")


def expanding_percentile(x: pd.Series) -> pd.Series:
    """Causal expanding-window percentile in [0, 1].

    p_t = fraction of valid {x_s : s <= t} with x_s <= x_t. Expanding (not
    full-sample) is what keeps it causal — a full-sample rank would leak the
    future distribution into today's reading.
    """
    return x.expanding().rank(pct=True).rename("vol_pctile")
