"""Shared causal primitives (D-20).

Built ONCE here and reused by every signal + the OOS harness, so there is a
single audited implementation of each look-ahead-free construction rather than
one re-derivation per signal. Every function in this module is causal: the value
at t uses only data through t. If a function ever needs the future, it does not
belong here.

Volatility signal (Phase 1.5) is the first consumer; later signals import the
same primitives.
"""

from typing import Callable

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


def downside_features(r) -> pd.DataFrame:
    """EWM downside deviation (halflife 10d) and EWM Sortino ratios (halflife
    20d, 60d). Causal by construction — EWMs only look back.

    Generic return descriptors (Shu/Yu/Mulvey 2024), NOT jump-model specific:
    lifted out of the retired estimator 2026-08-06 so `build_panel.py` keeps its
    construction gate (G4 crisis coverage / G5 episode count both key off `dd10`)
    while the jump model itself moves to archive/. Math and column order are
    unchanged, so `market_daily.csv` is byte-identical across the move.
    """
    r = pd.Series(np.asarray(r, dtype=float))
    neg2 = np.minimum(r, 0.0) ** 2
    feats = {"dd10": np.sqrt(neg2.ewm(halflife=10).mean())}
    for hl in (20, 60):
        dd = np.sqrt(neg2.ewm(halflife=hl).mean())
        feats[f"sortino{hl}"] = r.ewm(halflife=hl).mean() / dd.replace(0.0, np.nan)
    return pd.DataFrame(feats)


def expanding_z(x: pd.Series, min_periods: int = TRADING_DAYS) -> pd.Series:
    """Causal expanding-window z-score: how unusual is today's level against its
    OWN past only. The full-sample mean/std that most write-ups use leaks the
    future distribution into every historical reading.

    Companion to `expanding_percentile`: the z-score is scale-aware (how many
    sigmas), the percentile is distribution-free (how often). Signals with
    fat-tailed or bounded readings should prefer the percentile.
    """
    mean = x.expanding(min_periods=min_periods).mean()
    std = x.expanding(min_periods=min_periods).std()
    return ((x - mean) / std.replace(0.0, np.nan)).rename(f"{x.name or 'x'}_z")


# ── the look-ahead guard ────────────────────────────────────────────────────────

def _as_frame(obj: pd.Series | pd.DataFrame) -> pd.DataFrame:
    return obj.to_frame() if isinstance(obj, pd.Series) else obj


def assert_causal(
    build_fn: Callable[[pd.Series | pd.DataFrame], pd.Series | pd.DataFrame],
    r: pd.Series | pd.DataFrame,
    cut: pd.Timestamp | None = None,
    seed: int = 0,
) -> None:
    """Property check that a construction cannot see the future.

    Every reading at or before `cut` must be BIT-IDENTICAL when the input
    strictly after `cut` is replaced with different data. This is the one test
    that actually proves the absence of look-ahead: reading the code proves
    intent, this proves behaviour. Reasoning about `.rolling()` vs `.expanding()`
    vs a stray `.shift(-1)` is exactly the kind of thing that is right in review
    and wrong in the pipeline.

    Every signal's `build()` is required to pass this before its one-look
    (validation-standards §(b), causal/PIT). Raises AssertionError naming the
    first column and date that moved.
    """
    if cut is None:
        cut = r.index[int(len(r) * 0.7)]

    base = _as_frame(build_fn(r))

    rng = np.random.default_rng(seed)
    perturbed = r.copy()
    future = perturbed.index > cut
    n_future = int(future.sum())
    if isinstance(r, pd.DataFrame):
        for col in r.columns:
            perturbed.loc[future, col] = rng.normal(0.0, 5.0 * float(r[col].std()), n_future)
    else:
        perturbed.loc[future] = rng.normal(0.0, 5.0 * float(r.std()), n_future)
    pert = _as_frame(build_fn(perturbed))

    a = base.loc[:cut]
    b = pert.loc[:cut].reindex(a.index)

    for col in a.columns:
        if a[col].equals(b[col]):
            continue
        same = (a[col] == b[col]) | (a[col].isna() & b[col].isna())
        first = a.index[~same][0]
        raise AssertionError(
            f"LOOK-AHEAD LEAK in column '{col}': the reading at {first.date()} changed "
            f"when data after {pd.Timestamp(cut).date()} was replaced "
            f"({a[col][first]!r} -> {b[col][first]!r})."
        )
