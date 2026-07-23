"""Chapter-2 allocation machinery (prereg: .planning/ALLOCATION-PREREG.md Rev 2).

ERC with caps + scale-down-only vol target, era-aware causal covariance engines
(expanding unconditional / EWMA reactive / state-conditional with per-state activation
and fixed 0.5 shrinkage), and multi-asset strategy simulation under the chapter-1
execution conventions (weight shift by delay, 10 bps one-way on risky |dw| excluding
cash, cash earns rf).

Causality: statistics at decision date t use data through close t only (cumulative sums
inclusive of t); weights decided at t are shifted by `delay` before earning returns.
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _ccd_barrier(cov, w_fixed, free, lam, w0=None, tol=1e-12, max_sweeps=10000):
    """Cyclical coordinate descent for min 0.5 w'Σw - lam * sum_free log w_i with the
    non-free coordinates held at w_fixed (Griveau-Billion/Richard/Roncalli 2013).
    KKT per free coordinate: σ_ii w_i² + β_i w_i - lam = 0 with β_i = Σ_{j≠i}σ_ij w_j,
    so at the solution every free asset's risk contribution w_i(Σw)_i equals lam
    exactly. Globally convergent for PD Σ."""
    w = w_fixed.copy()
    idx = np.flatnonzero(free)
    w[idx] = np.sqrt(lam / np.diag(cov)[idx]) if w0 is None else w0
    for _ in range(max_sweeps):
        delta = 0.0
        for i in idx:
            beta = cov[i] @ w - cov[i, i] * w[i]
            new = (-beta + np.sqrt(beta * beta + 4.0 * cov[i, i] * lam)) / (2.0 * cov[i, i])
            delta = max(delta, abs(new - w[i]))
            w[i] = new
        if delta < tol:
            return w[idx]
    raise RuntimeError("ERC coordinate descent did not converge")


def erc_weights(cov, caps):
    """Long-only ERC with weight caps. Free-set weights solve the log-barrier problem
    (every free asset's risk contribution equals the multiplier lam exactly). With no
    capped assets the KKT system is homogeneous of degree 2, so one solve rescales
    exactly to the budget (equal RC preserved); with capped assets held at their caps
    the homogeneity breaks and lam is set by warm-started bisection. Caps by
    cap-and-redistribute: clip binding assets, freeze them, re-solve the free set.
    Deterministic, pure numpy."""
    cov = np.asarray(cov, dtype=float)
    caps = np.asarray(caps, dtype=float)
    n = cov.shape[0]
    fixed = np.zeros(n, dtype=bool)
    w_full = np.minimum(np.full(n, 1.0 / n), caps)
    for _ in range(n + 1):
        free = ~fixed
        budget = 1.0 - caps[fixed].sum()
        if budget <= 1e-12 or not free.any():
            break
        w_fixed = np.where(fixed, caps, 0.0)
        if not fixed.any():
            x = _ccd_barrier(cov, w_fixed, free, float(np.mean(np.diag(cov))))
            w_full = x * (budget / x.sum())
        elif int(free.sum()) == 1:
            w_full = w_fixed.copy()
            w_full[free] = budget
        else:
            lo, hi = 1e-14, float(np.mean(np.diag(cov)))
            x = _ccd_barrier(cov, w_fixed, free, hi)
            while x.sum() < budget:
                hi *= 10.0
                if hi > 1e12:
                    raise RuntimeError("ERC bisection bracket failed")
                x = _ccd_barrier(cov, w_fixed, free, hi, w0=x)
            for _ in range(200):
                mid = np.sqrt(lo * hi)
                x = _ccd_barrier(cov, w_fixed, free, mid, w0=x)
                if x.sum() > budget:
                    hi = mid
                else:
                    lo = mid
                if hi / lo - 1.0 < 1e-10:
                    break
            w_full = w_fixed.copy()
            w_full[free] = x * (budget / x.sum())
        viol = free & (w_full > caps + 1e-9)
        if not viol.any():
            return w_full
        fixed |= viol
    return np.minimum(w_full, caps)


def vol_scale(w, cov_ann, target=0.08):
    """Scale-down-only vol target: w_final = w * min(1, target/sigma_hat)."""
    sig = float(np.sqrt(max(w @ cov_ann @ w, 0.0)))
    return min(1.0, target / max(sig, 1e-12))


class ExpandingCov:
    """Causal expanding mean/cov over masked (complete-case) days via cumulative sums.
    cov(t) uses masked days u <= t. Returns (n_days, cov) or (n, None) if n < 2."""

    def __init__(self, X, mask):
        X = np.asarray(X, dtype=float)
        mask = np.asarray(mask, dtype=bool)
        Xm = np.where(mask[:, None], np.nan_to_num(X), 0.0)
        self.n = np.cumsum(mask)
        self.s1 = np.cumsum(Xm, axis=0)
        self.s2 = np.cumsum(Xm[:, :, None] * Xm[:, None, :], axis=0)

    def cov(self, t):
        n = int(self.n[t])
        if n < 2:
            return n, None
        m = self.s1[t] / n
        c = (self.s2[t] - n * np.outer(m, m)) / (n - 1)
        return n, c


def ewma_cov_track(X, mask, lam=0.97, burn=250):
    """Causal EWMA covariance about the EWMA mean on masked days; NaN until `burn`
    masked days have accumulated. Returns (T,k,k) array."""
    X = np.asarray(X, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    T, k = X.shape
    out = np.full((T, k, k), np.nan)
    m = np.zeros(k)
    S = np.zeros((k, k))
    cnt = 0
    for t in range(T):
        if mask[t]:
            x = X[t]
            cnt += 1
            m = lam * m + (1.0 - lam) * x
            d = x - m
            S = lam * S + (1.0 - lam) * np.outer(d, d)
        if cnt >= burn:
            out[t] = S
    return out


class CovProviders:
    """The three arms' covariance engines over one panel + one label path, with the
    prereg's two-era structure. Assets columns fixed as [equity, bond, gold]; era-1
    uses the leading 2x2 block, era-2 the full 3x3. label: int array aligned to the
    panel, -1 = unlabeled. era2_t: first position where the 3-asset complete-case
    count reaches `era2_burn` (None disables era-2)."""

    def __init__(self, X, label, min_state_days=500, shrink=0.5, lam=0.97,
                 era2_burn=250, base=None):
        """base: another CovProviders over the SAME X — reuses its unconditional and
        EWMA engines (label-independent), rebuilding only the state engines. Used by
        the placebo/shuffle controls."""
        X = np.asarray(X, dtype=float)
        label = np.asarray(label)
        self.X = X
        mask2 = ~np.isnan(X[:, :2]).any(axis=1)
        mask3 = ~np.isnan(X).any(axis=1)
        n3 = np.cumsum(mask3)
        self.era2_t = int(np.argmax(n3 >= era2_burn)) if n3[-1] >= era2_burn else None
        self.min_state_days = min_state_days
        self.shrink = shrink
        self.uncond = {} if base is None else base.uncond
        self.ewma = {} if base is None else base.ewma
        self.state = {}
        for era, mask, k in ((1, mask2, 2), (2, mask3, 3)):
            if era == 2 and self.era2_t is None:
                continue
            emask = mask if era == 1 else (mask & (np.arange(len(mask)) >=
                                                   int(np.argmax(mask3))))
            if base is None:
                self.uncond[era] = ExpandingCov(X[:, :k], emask)
                self.ewma[era] = ewma_cov_track(X[:, :k], emask, lam=lam, burn=era2_burn)
            for s in (0, 1):
                self.state[(era, s)] = ExpandingCov(X[:, :k], emask & (label == s))

    def era(self, t):
        return 2 if (self.era2_t is not None and t >= self.era2_t) else 1

    def unconditional(self, t):
        _, c = self.uncond[self.era(t)].cov(t)
        return c

    def reactive(self, t):
        c = self.ewma[self.era(t)][t]
        return None if np.isnan(c).any() else c

    def conditional(self, t, s):
        era = self.era(t)
        _, cu = self.uncond[era].cov(t)
        ns, cs = self.state[(era, s)].cov(t)
        if cu is None:
            return None
        if cs is None or ns < self.min_state_days:
            return cu
        return self.shrink * cu + (1.0 - self.shrink) * cs


def build_target_weights(T, decisions, label, providers, kind, caps3, target=0.08):
    """Daily (T,3) decided-at-t target weight matrix for one ERC arm. Weights change
    only at decision positions; gold column forced 0 in era-1. kind: 'cond' |
    'match' | 'react'. Falls back to all-cash while the engine has no estimate."""
    W = np.zeros((T, 3))
    w_cur = np.zeros(3)
    d_set = set(int(d) for d in decisions)
    for t in range(T):
        if t in d_set:
            era = providers.era(t)
            k = 2 if era == 1 else 3
            if kind == "cond":
                cov = providers.conditional(t, int(label[t]))
            elif kind == "match":
                cov = providers.unconditional(t)
            else:
                cov = providers.reactive(t)
            if cov is not None:
                cov_ann = cov * TRADING_DAYS
                w = erc_weights(cov_ann, caps3[:k])
                w = w * vol_scale(w, cov_ann, target=target)
                w_cur = np.zeros(3)
                w_cur[:k] = w
        W[t] = w_cur
    return W


def simulate_multi(W_target, R, rf, cost_bps=10.0, delay=2):
    """Daily returns of a multi-asset arm. W_target: (T,3) decided-at-t weights;
    executed weights are shifted by `delay` (chapter-1 idiom). Missing asset returns
    contribute 0 P&L (NaN policy); costs on risky |dw| only, cash excluded."""
    W = pd.DataFrame(W_target).shift(delay).fillna(0.0).to_numpy()
    Rp = np.nan_to_num(np.asarray(R, dtype=float))
    risky = (W * Rp).sum(axis=1)
    cash = 1.0 - W.sum(axis=1)
    dW = np.abs(np.diff(W, axis=0, prepend=np.zeros((1, W.shape[1])))).sum(axis=1)
    return risky + cash * np.asarray(rf, dtype=float) - dW * cost_bps * 1e-4, W


def decision_positions(dates, label, score_mask):
    """First trading day of each month within the scoring window, plus every position
    where the label flips vs the previous scored day; always includes the first
    scored position."""
    pos = np.flatnonzero(score_mask)
    months = dates[pos].to_period("M")
    first_of_month = np.r_[True, months[1:] != months[:-1]]
    flips = np.r_[True, label[pos][1:] != label[pos][:-1]]
    return pos[first_of_month | flips]


def rolling_vol(ret, window=63):
    """Rolling realized annualized vol (F2 inputs: its std is the risk-stabilization
    metric; its RMSE vs the target is a reported diagnostic)."""
    return (pd.Series(ret).rolling(window).std() * np.sqrt(TRADING_DAYS)).dropna()
