#!/usr/bin/env python3
"""EXPLORATORY first pass (not prereg-frozen) — is there a latent continuous
correlation factor?

Model: average pairwise correlation, Fisher-z transformed, follows a discretized
Ornstein-Uhlenbeck / AR(1) state x_t = phi*x_{t-1} + eta_t, observed with noise
z_t = x_t + eps_t. Kalman filter gives the causal (forward-pass only) estimate
x_t|t, fit by expanding-window MLE (same discipline as tailhazard_stage1.py).

PRIMARY QUESTION: does the filtered state x_t|t forecast z_{t+h} (h=21d) better
than the naive persistence baseline (just use z_t itself)? If the OU filter adds
nothing over "assume tomorrow's correlation = today's", there's no latent factor
here worth building on.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from src.config import DATA_DIR, RESULTS_DIR

TICKERS = ["SPY", "IWD", "IWF", "IWM", "IEF", "TLT", "SHY", "LQD", "HYG", "GLD", "DBC", "VNQ", "EFA"]
CACHE = os.path.join(DATA_DIR, "processed", "stage1p_etf.csv")
WIN = 21          # realized-correlation window
H = 21            # forecast horizon
REFIT_EVERY = 63  # quarterly refit, expanding train
BURN = 400        # need WIN + some history before first realized-corr obs
RNG = np.random.default_rng(0)


def load_prices():
    px = pd.read_csv(CACHE, parse_dates=["Date"]).set_index("Date")
    assert list(px.columns) == TICKERS and len(px) > 3000, "cache missing/stale — run stage1p_covariance.py once first"
    return px


def realized_corr_z(R, win=WIN):
    """Causal trailing-window mean pairwise correlation, Fisher-z transformed."""
    N, A = R.shape
    z = np.full(N, np.nan)
    for t in range(win, N):
        C = np.corrcoef(R[t - win:t].T)
        iu = np.triu_indices(A, 1)
        rho = np.clip(C[iu].mean(), -0.999, 0.999)
        z[t] = np.arctanh(rho)
    return z


def kalman_ll(params, z):
    """Negative log-likelihood of the innovations (params on unconstrained scale)."""
    phi = 1 / (1 + np.exp(-params[0]))          # logit -> (0,1)
    q, robs = np.exp(params[1]), np.exp(params[2])
    x, P = z[0], 1.0
    ll = 0.0
    for t in range(1, len(z)):
        xp, Pp = phi * x, phi**2 * P + q
        S = Pp + robs
        innov = z[t] - xp
        ll += 0.5 * (np.log(2 * np.pi * S) + innov**2 / S)
        K = Pp / S
        x, P = xp + K * innov, (1 - K) * Pp
    return ll


def fit_kalman(z_train):
    r = minimize(kalman_ll, x0=[2.0, -3.0, -3.0], args=(z_train,), method="Nelder-Mead",
                 options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 2000})
    phi = 1 / (1 + np.exp(-r.x[0])); q, robs = np.exp(r.x[1]), np.exp(r.x[2])
    return phi, q, robs


def filter_full(z, phi, q, robs):
    """Run the filter over the whole series (causal at every t), return x_t|t."""
    N = len(z)
    x_filt = np.full(N, np.nan)
    t0 = np.where(np.isfinite(z))[0][0]
    x, P = z[t0], 1.0
    x_filt[t0] = x
    for t in range(t0 + 1, N):
        if not np.isfinite(z[t]):
            x_filt[t] = np.nan
            continue
        xp, Pp = phi * x, phi**2 * P + q
        K = Pp / (Pp + robs)
        x = xp + K * (z[t] - xp)
        P = (1 - K) * Pp
        x_filt[t] = x
    return x_filt


def block_boot_mean(x, reps=2000, blk=63):
    n = len(x); out = np.empty(reps)
    for r in range(reps):
        idx, i = [], RNG.integers(0, n)
        while len(idx) < n:
            L = RNG.geometric(1 / blk); idx += [(i + j) % n for j in range(L)]; i = RNG.integers(0, n)
        out[r] = x[np.array(idx[:n])].mean()
    return out


def main():
    px = load_prices()
    R = np.log(px).diff().values[1:]
    dates = px.index[1:]
    N = len(R)
    z = realized_corr_z(R)

    valid0 = np.where(np.isfinite(z))[0][0]
    start = max(valid0 + BURN, BURN)
    refit_points = list(range(start, N - H, REFIT_EVERY))
    print(f"corrfactor stage1 (exploratory)  N={N}  universe={len(TICKERS)} ETFs  "
          f"span={dates[start].date()}..{dates[-1].date()}  refits={len(refit_points)}")

    pred_model = np.full(N, np.nan)   # forecast of z_{t+H} made at t, via OU filter
    pred_naive = np.full(N, np.nan)   # forecast of z_{t+H} made at t, via persistence (z_t)
    pred_ewma = np.full(N, np.nan)    # forecast via a plain fixed-decay EWMA smoother (no fitted state)
    actual = np.full(N, np.nan)
    phis = []

    # fixed EWMA smoother, decay chosen once (not refit) to sit near the fitted phi's -- this is
    # the "any smoother beats a noisy point estimate" confound we need to rule out
    LAM_EWMA = 0.97
    ewma = np.full(N, np.nan)
    t0 = valid0
    ewma[t0] = z[t0]
    for t in range(t0 + 1, N):
        if np.isfinite(z[t]):
            ewma[t] = LAM_EWMA * ewma[t - 1] + (1 - LAM_EWMA) * z[t]
        else:
            ewma[t] = ewma[t - 1]

    for i, r0 in enumerate(refit_points):
        train_end = r0
        z_train = z[valid0:train_end]
        z_train = z_train[np.isfinite(z_train)]
        phi, q, robs = fit_kalman(z_train)
        phis.append(phi)
        seg_end = min(r0 + REFIT_EVERY, N - H)
        z_seg = z[:seg_end]  # filter needs history from the start to stay causal & continuous
        x_filt = filter_full(np.where(np.isfinite(z_seg), z_seg, z_seg), phi, q, robs)
        for t in range(r0, seg_end):
            if not np.isfinite(z[t]) or not np.isfinite(z[t + H]):
                continue
            pred_model[t] = phi**H * x_filt[t]
            pred_naive[t] = z[t]
            pred_ewma[t] = ewma[t]
            actual[t] = z[t + H]
        print(f"  [refit {i+1}/{len(refit_points)}] phi={phi:.3f} q={q:.5f} robs={robs:.5f}", flush=True)

    ok = np.isfinite(pred_model) & np.isfinite(pred_naive) & np.isfinite(pred_ewma) & np.isfinite(actual)
    e_model = (actual[ok] - pred_model[ok])**2
    e_naive = (actual[ok] - pred_naive[ok])**2
    e_ewma = (actual[ok] - pred_ewma[ok])**2
    print(f"\nOOS forecast of z_(t+{H}) from z-history; N={ok.sum()} days, "
          f"{dates[np.where(ok)[0][0]].date()}..{dates[np.where(ok)[0][-1]].date()}")
    print(f"  mean phi across refits = {np.mean(phis):.3f}  (phi->1 = near-unit-root/no mean reversion; "
          f"phi->0 = no memory)")
    print(f"  MSE  model(OU-Kalman) = {e_model.mean():.5f}   naive(persistence) = {e_naive.mean():.5f}"
          f"   EWMA(lam={LAM_EWMA}, unfitted) = {e_ewma.mean():.5f}")

    def report(a, b, label):
        d = a - b  # positive = second arg (b) better
        boot = block_boot_mean(d)
        print(f"  {label}: d = {d.mean():+.6f}  90% CI [{np.percentile(boot,5):+.6f}, "
              f"{np.percentile(boot,95):+.6f}]  P(b better)={np.mean(boot>0):.3f}")

    report(e_naive, e_model, "MSE_naive  - MSE_model (Kalman vs raw persistence)")
    report(e_ewma, e_model, "MSE_ewma   - MSE_model (Kalman vs plain unfitted smoother)")

    out = pd.DataFrame({"date": dates[ok], "z": z[:N][ok], "pred_model": pred_model[ok],
                         "pred_naive": pred_naive[ok], "actual": actual[ok]})
    out.to_csv(os.path.join(RESULTS_DIR, "corrfactor_stage1.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'corrfactor_stage1.csv')}")


if __name__ == "__main__":
    main()
