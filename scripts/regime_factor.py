"""Step 2 of the regime-as-a-factor test (NO look — construction + causality only).

Builds a REGIME FACTOR RETURN (a factor-mimicking portfolio, FMP) from the JM regime series, so
Step 3 can ask whether that return is SPANNED by Mkt/SMB/HML/BAB. See FACTOR-MODEL-DIRECTION §5.

WHY AN INNOVATION, NOT A LEVEL. The regime level s_t is by design near-constant (stability 1.000 =>
autocorrelation ~ 1). A factor must be a zero-cost *return*, and the ICAPM prices covariance with
*news* about a state variable (Campbell 1993; Maio & Santa-Clara 2012), not its level. So the driver
is the monthly innovation Δs_t. Default = first difference of the continuous month-end stress margin
(real-valued, magnitude-bearing, needs no estimated AR coefficient => no look-ahead). AR(1)-residual
innovation is a documented refinement, not used here.

WHY CAUSAL BETAS/WEIGHTS. Pitfall #1 (§5): full-sample betas manufacture an in-sample spread that
dies OOS. Every β and every projection weight used to form REG_t is estimated on a window that ends
at t-1 (strictly prior). REG_t is then this month's realized spread/projection — genuinely OOS
relative to its own weights.

Two constructions, for robustness:
  beta_sort_factor      long high-Δs-beta portfolios, short low — a stress-HEDGE minus stress-AMPLIFIER
                        spread. Economic sign of its premium should be NEGATIVE (hedges are expensive).
  mimicking_factor      Lamont (2001) / Breeden-Gibbons-Litzenberger (1989): project Δs on the base
                        excess returns over the prior window; REG_t = w' R_t (max-correlation FMP).

All inputs monthly; R (T x N) excess returns of test assets, aligned row-for-row to `innov` (T,).
"""

import numpy as np


def regime_innovation(stress, method="diff"):
    """Monthly regime innovation Δs from a continuous stress-margin level (T,).

    method='diff'   : Δs_t = stress_t - stress_{t-1}   (φ=1; robust, no estimated parameter)
    method='demean' : Δs_t = stress_t - mean(stress)   (level deviation; sensitivity only)
    Returns (T,) with NaN in row 0 for 'diff'.
    """
    stress = np.asarray(stress, dtype=float)
    if method == "diff":
        d = np.empty_like(stress)
        d[0] = np.nan
        d[1:] = stress[1:] - stress[:-1]
        return d
    if method == "demean":
        return stress - np.nanmean(stress)
    raise ValueError(f"unknown method {method!r}")


def _trailing_betas(R, x, t, window):
    """Univariate β_i = cov(R_i, x)/var(x) for each asset i, over the STRICTLY PRIOR window
    [t-window, t-1]. R (T x N), x (T,) the innovation. Returns (N,) or None if the window has
    insufficient valid rows. NaN rows (innovation warmup) are dropped pairwise."""
    lo = t - window
    if lo < 0:
        return None
    Rw = R[lo:t]                       # window rows, EXCLUDES t (causal)
    xw = x[lo:t]
    ok = np.isfinite(xw) & np.all(np.isfinite(Rw), axis=1)
    if ok.sum() < max(12, window // 3):
        return None
    Rw, xw = Rw[ok], xw[ok]
    xc = xw - xw.mean()
    var = float(xc @ xc)
    if var == 0.0:
        return None
    return (Rw - Rw.mean(axis=0)).T @ xc / var        # (N,) cov(R_i,x)/var(x)


def beta_sort_factor(R, innov, window=60, frac=0.3):
    """Long high-Δs-β, short low-Δs-β spread, rebalanced monthly with trailing-window betas.

    For each month t (that has a full prior window): rank the N assets by their β to the innovation
    estimated on [t-window, t-1]; long the top `frac`, short the bottom `frac`, equal-weight; REG_t =
    mean(long R_t) - mean(short R_t). High β = portfolios that rise when stress rises (hedges); the
    spread is long-hedge / short-amplifier, so its premium should be NEGATIVE if regime risk is priced.

    Returns dict: reg (T,) with NaN before first tradable month; n_side (per-leg count).
    """
    R = np.asarray(R, dtype=float)
    innov = np.asarray(innov, dtype=float)
    T, N = R.shape
    k = max(1, int(round(N * frac)))
    reg = np.full(T, np.nan)
    for t in range(T):
        b = _trailing_betas(R, innov, t, window)
        if b is None or not np.all(np.isfinite(R[t])):
            continue
        order = np.argsort(b)                          # ascending: low β first
        short, long_ = order[:k], order[-k:]
        reg[t] = R[t, long_].mean() - R[t, short].mean()
    return dict(reg=reg, n_side=k)


def mimicking_factor(R, innov, window=60):
    """Max-correlation factor-mimicking portfolio (Lamont 2001; BGL 1989), causal weights.

    For each month t: on the prior window [t-window, t-1] regress the innovation on the base excess
    returns, Δs = a + w'R + e (OLS). REG_t = w' R_t — this month's realized return of last month's
    projection weights (OOS relative to the weight estimation). Weights are NOT renormalized (the FMP
    is defined up to scale; we keep the raw projection so its sign/scale are comparable month to month).

    Returns dict: reg (T,) with NaN before first tradable month.
    """
    R = np.asarray(R, dtype=float)
    innov = np.asarray(innov, dtype=float)
    T, N = R.shape
    reg = np.full(T, np.nan)
    for t in range(T):
        lo = t - window
        if lo < 0 or not np.all(np.isfinite(R[t])):
            continue
        Rw, xw = R[lo:t], innov[lo:t]
        ok = np.isfinite(xw) & np.all(np.isfinite(Rw), axis=1)
        if ok.sum() < max(N + 2, window // 3):
            continue
        Rw, xw = Rw[ok], xw[ok]
        X = np.column_stack([np.ones(len(Rw)), Rw])    # intercept + N base returns
        coef, *_ = np.linalg.lstsq(X, xw, rcond=None)
        w = coef[1:]                                   # projection weights (drop intercept)
        reg[t] = float(w @ R[t])
    return dict(reg=reg)
