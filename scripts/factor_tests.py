"""Path-A core: cross-sectional asset-pricing tests on portfolio grids.

Three standard tests (see .planning/FACTOR-MODEL-DIRECTION.md Stage 5), all operating on a panel
of excess returns R (T x N test assets) and factor returns F (T x K):

  grs_test        — Gibbons, Ross & Shanken (1989): joint test that ALL test-asset alphas are zero
                    given the factors. "Does this factor model fully price these assets?"
  fama_macbeth    — Fama & MacBeth (1973) two-pass: are the factor RISK PREMIA priced in the
                    cross-section? Returns premia estimates + the FM time-series standard errors.
  factor_spanning — is factor X redundant given the others? (regress X on the rest; alpha ~ 0 => X
                    is spanned / adds nothing). e.g. "is HML subsumed by a quality factor?"

All returns are decimals per period (monthly here), test assets already in EXCESS form (R_i - Rf);
FF factors (Mkt-RF, SMB, HML) are already excess/zero-cost.

NOTE (errors-in-variables): plain Fama-MacBeth ignores that betas are ESTIMATED (Shanken 1992
correction shrinks the t-stats). We report standard FM t-stats and flag this; Shanken is a future
refinement, not needed to characterize whether premia are even in the ballpark.
"""

import numpy as np
from scipy import stats


def _ols(X, Y):
    """Multi-output OLS. X (T x p) incl. intercept col, Y (T x N). Returns B (p x N), resid (T x N)."""
    B, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return B, Y - X @ B


def time_series_regression(R, F):
    """Per-asset time-series regression R_i = alpha_i + beta_i' F + eps_i (the GRS/FF first pass).

    R (T x N) excess returns, F (T x K) factors. Returns:
      alpha (N,), betas (N x K), resid (T x N), and ML factor mean/cov for the GRS adjustment.
    """
    T = R.shape[0]
    X = np.column_stack([np.ones(T), F])            # T x (K+1): intercept + factors
    B, resid = _ols(X, R)                            # B: (K+1) x N
    alpha = B[0]                                      # the pricing errors
    betas = B[1:].T                                   # N x K
    return alpha, betas, resid


def grs_test(R, F):
    """Gibbons-Ross-Shanken (1989) F-test of H0: alpha_1 = ... = alpha_N = 0.

    Statistic (Cochrane 2005, eq. 12.4; MacKinlay 1995):
        J = ((T - N - K) / N) * (1 / (1 + mu' Omega^{-1} mu)) * (alpha' Sigma^{-1} alpha)   ~  F(N, T-N-K)

    where alpha = time-series-regression intercepts (N), Sigma = ML residual covariance (N x N, /T),
    mu = factor means (K), Omega = ML factor covariance (K x K, /T). The middle term divides by
    (1 + max squared Sharpe of the factors): a factor set that itself earns a high Sharpe leaves
    less "unexplained alpha room", so the same raw alpha is less damning. Requires T > N + K.
    """
    T, N = R.shape
    K = F.shape[1]
    if T <= N + K:
        raise ValueError(f"GRS needs T > N + K; got T={T}, N={N}, K={K}")

    alpha, _, resid = time_series_regression(R, F)
    Sigma = resid.T @ resid / T                       # ML residual cov (divide by T, not T-K-1)
    mu = F.mean(axis=0)
    Fc = F - mu
    Omega = Fc.T @ Fc / T                             # ML factor cov
    sh2 = mu @ np.linalg.solve(Omega, mu)             # mu' Omega^{-1} mu  = max squared Sharpe of F
    a_term = alpha @ np.linalg.solve(Sigma, alpha)    # alpha' Sigma^{-1} alpha

    J = ((T - N - K) / N) * a_term / (1.0 + sh2)
    p_value = stats.f.sf(J, N, T - N - K)
    return dict(grs_stat=float(J), p_value=float(p_value), df1=N, df2=T - N - K,
                sh2_factors=float(sh2), mean_abs_alpha=float(np.mean(np.abs(alpha))),
                alpha=alpha)


def fama_macbeth(R, F):
    """Fama-MacBeth (1973) two-pass cross-sectional test of the factor risk premia.

    Pass 1 (time series): full-sample betas b_i for each asset (from time_series_regression).
    Pass 2 (cross section): for EACH period t, regress the cross-section of returns on the betas:
        R_{.,t} = gamma_0t + gamma_t' b + e_t     ->  a time series of gammas (one per period).
    FM estimate = time-series MEAN of the gammas; the FM standard error = std(gammas)/sqrt(T_cs).
    The averaging over periods IS the standard-error trick: it sidesteps the cross-sectional
    residual correlation that would wreck a single pooled regression.

    Returns per-coefficient (intercept + one per factor): mean (premium), se, t-stat, and the full
    per-period gamma time series. A well-specified model has intercept ~ 0 and factor premia whose
    sign/scale match the factors' own average returns.
    """
    _, betas, _ = time_series_regression(R, F)        # N x K full-sample betas
    T, N = R.shape
    K = F.shape[1]
    Xc = np.column_stack([np.ones(N), betas])         # N x (K+1): cross-sectional design (const + betas)

    gammas = np.empty((T, K + 1))
    for t in range(T):
        g, _ = _ols(Xc, R[t])                         # cross-sectional regression at period t
        gammas[t] = g
    gbar = gammas.mean(axis=0)
    gse = gammas.std(axis=0, ddof=1) / np.sqrt(T)     # FM time-series standard error
    tstat = gbar / gse

    names = ["intercept"] + [f"factor{j}" for j in range(K)]
    return dict(names=names, premia=gbar, se=gse, tstat=tstat, gammas=gammas)


def _newey_west_var(X, resid, lags):
    """Newey-West (1987) HAC covariance of the OLS coefficients for design X (T x p), residuals
    (T,). Bartlett-kernel weights w_l = 1 - l/(lags+1). Returns the (p x p) coefficient covariance."""
    T, p = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    u = X * resid[:, None]                             # T x p score contributions
    S = u.T @ u                                        # lag-0
    for l in range(1, lags + 1):
        w = 1.0 - l / (lags + 1.0)
        G = u[l:].T @ u[:-l]
        S += w * (G + G.T)
    return XtX_inv @ S @ XtX_inv


def factor_spanning_nw(target, others, lags=6):
    """Spanning regression of `target` on `others` + intercept with a Newey-West HAC t-stat on the
    alpha (the intercept) — the correct SE when factor returns are autocorrelated/heteroskedastic.
    Decision bar (Harvey-Liu-Zhu 2016): |t_alpha| > 3 to call `target` NOT spanned. lags default 6
    (monthly). Returns alpha, its NW t-stat, OLS t-stat (for reference), and R^2."""
    T = target.shape[0]
    X = np.column_stack([np.ones(T), others])
    B, resid = _ols(X, target.reshape(-1, 1))
    alpha = float(B[0, 0])
    r = resid[:, 0]
    nw_var = _newey_west_var(X, r, lags)
    se_nw = float(np.sqrt(nw_var[0, 0]))
    s2 = float((r ** 2).sum()) / (T - X.shape[1])
    se_ols = float(np.sqrt(s2 * np.linalg.inv(X.T @ X)[0, 0]))
    tss = float(((target - target.mean()) ** 2).sum())
    r2 = 1.0 - float((r ** 2).sum()) / tss
    return dict(alpha=alpha, t_alpha_nw=alpha / se_nw, t_alpha_ols=alpha / se_ols, r2=r2)


def max_sharpe2(F):
    """Maximum squared Sharpe attainable from a set of zero-cost factor returns F (T x K):
    Sh^2 = mu' Sigma^{-1} mu (mu = mean, Sigma = ML covariance). The Barillas-Shanken (2017)
    model-comparison object: factor set A dominates B iff it delivers a higher Sh^2. NOTE the
    sampling error in a Sh^2 DIFFERENCE is large (BKRS 2020) — treat raw deltas as descriptive only."""
    F = np.asarray(F, dtype=float)
    mu = F.mean(axis=0)
    Fc = F - mu
    Sigma = Fc.T @ Fc / F.shape[0]
    return float(mu @ np.linalg.solve(Sigma, mu))


def factor_spanning(target, others):
    """Is `target` factor spanned by `others`? Regress target (T,) on others (T x M) + intercept.
    Returns the alpha (unexplained mean return), its Newey-West-free OLS t-stat, and R^2.
    alpha ~ 0 (insignificant) => target adds no mean return beyond the others (it is redundant).
    """
    T = target.shape[0]
    X = np.column_stack([np.ones(T), others])
    B, resid = _ols(X, target.reshape(-1, 1))
    alpha = float(B[0, 0])
    rss = float((resid ** 2).sum())
    s2 = rss / (T - X.shape[1])
    XtX_inv = np.linalg.inv(X.T @ X)
    se_alpha = np.sqrt(s2 * XtX_inv[0, 0])
    tss = float(((target - target.mean()) ** 2).sum())
    r2 = 1.0 - rss / tss
    return dict(alpha=alpha, t_alpha=alpha / se_alpha, r2=r2)
