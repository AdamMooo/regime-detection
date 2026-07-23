#!/usr/bin/env python3
"""What does the HMM add over simpler causal smoothing of the same features?

The HMM's Z_t = sum_k gamma_t(k) mu_k is one causal filter of the 4 features. This
pits it against simpler causal filters at the only reliability criterion available for
a latent environment with no ground truth: OUT-OF-SAMPLE prediction of the near-future
environment (the features themselves). A more reliable environment estimate forecasts
the near future better, at lower jitter.

All methods: params fit on train (2016-2023), then applied causally and evaluated on the
genuinely-OOS 2024-2026 block. h-step forecast of X_{t+h}, RMSE over the 4 standardized
features. The competitor set decomposes what the HMM could contribute:

  persistence (RW)      -- null: X_hat = X_t
  EWMA                  -- pure denoising, flat forecast (= steady-state local-level KF)
  VAR(1) raw            -- linear dynamics, no denoising
  VAR(1) on EWMA        -- denoise + linear dynamics  (the strong simple competitor)
  HMM Z_t               -- nonlinear regime denoising + regime dynamics (gamma_t P^h mu)

Decisive line: HMM vs VAR(1)-on-EWMA. If the HMM does not beat smooth-then-linear-forecast
OOS, its regime machinery adds nothing over a simple continuous filter, and the honest
call is to use the simpler filter. Also stratified by VIX regime (does the HMM's
state-dependent filtering help specifically where adaptivity should matter?) and by jitter.

Reads  : data/processed/features.csv
Writes : results/filter_horserace.csv
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import FEATURES, HDP_TRUNCATION, RANDOM_SEED, TRAIN_END, DATA_DIR, RESULTS_DIR
from src.core.hdp_hmm import (fit_hdp_hmm, posterior_mean_params, get_labels_and_probs,
                              get_transition_matrix)

HORIZONS = [1, 5, 21]
VIX_IDX = FEATURES.index("vol_index")


def fit_var1(Xs):
    """VAR(1): X_t ~ A X_{t-1} + b, via OLS. Returns A (D,D), long-run mean m (D,)."""
    Xp, Xn = Xs[:-1], Xs[1:]
    Z = np.hstack([Xp, np.ones((len(Xp), 1))])
    coef, *_ = np.linalg.lstsq(Z, Xn, rcond=None)   # (D+1, D)
    A, b = coef[:-1].T, coef[-1]
    m = np.linalg.solve(np.eye(A.shape[0]) - A, b)
    return A, m


def var_forecast(A, m, X_t, h):
    return m + (X_t - m) @ np.linalg.matrix_power(A, h).T


def rmse(pred, actual):
    return float(np.sqrt(np.nanmean((pred - actual) ** 2)))


def main():
    full = pd.read_csv(os.path.join(DATA_DIR, "processed", "features.csv"),
                       parse_dates=["Date"]).set_index("Date")
    X = full[FEATURES].values
    dates = full.index
    ntr = int((dates <= pd.Timestamp(TRAIN_END)).sum())
    N = len(X)
    oos = np.arange(ntr, N)
    print(f"Train N={ntr} (..{dates[ntr-1].date()}); OOS N={N-ntr} "
          f"({dates[ntr].date()}..{dates[-1].date()})\n")

    # ---- EWMA smoother (span tuned on train 1-step RMSE) ----
    best_span, best = None, np.inf
    for span in (5, 10, 21, 42, 63):
        e = pd.DataFrame(X).ewm(span=span).mean().values
        err = rmse(e[:ntr-1], X[1:ntr])
        if err < best:
            best, best_span = err, span
    ewma = pd.DataFrame(X).ewm(span=best_span).mean().values
    print(f"EWMA span (train-tuned) = {best_span}\n")

    # ---- linear models fit on train ----
    A_raw, m_raw = fit_var1(X[:ntr])
    A_smo, m_smo = fit_var1(ewma[:ntr])

    # ---- HMM frozen on train, forward-filtered through full series ----
    _, samples = fit_hdp_hmm(X[:ntr], K_max=HDP_TRUNCATION, seed=RANDOM_SEED)
    params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
    _, filt, _, active = get_labels_and_probs(X, params, hold_days=1)
    loc_a = params["locs"][active]
    P = get_transition_matrix(params, active)
    Z = filt @ loc_a

    def forecast(method, h):
        if method == "persistence":
            return X
        if method == "EWMA":
            return ewma
        if method == "VAR1_raw":
            return np.vstack([var_forecast(A_raw, m_raw, X[t], h) for t in range(N)])
        if method == "VAR1_EWMA":
            return np.vstack([var_forecast(A_smo, m_smo, ewma[t], h) for t in range(N)])
        if method == "HMM":
            return (filt @ np.linalg.matrix_power(P, h)) @ loc_a

    methods = ["persistence", "EWMA", "VAR1_raw", "VAR1_EWMA", "HMM"]
    vix_oos = X[oos, VIX_IDX]
    hi = vix_oos >= np.median(vix_oos)

    def oos_corr(fc, h, ev):
        """Scale-invariant predictive information: mean per-feature corr(fc_t, X_(t+h)), OOS."""
        return float(np.mean([np.corrcoef(fc[ev, d], X[ev + h, d])[0, 1]
                              for d in range(X.shape[1])]))

    rows, table, corrs = [], {}, {}
    for h in HORIZONS:
        ev = oos[oos + h < N]
        for mth in methods:
            fc = forecast(mth, h)
            all_ = rmse(fc[ev], X[ev + h])
            m_hi = rmse(fc[ev[hi[:len(ev)]]], X[ev[hi[:len(ev)]] + h])
            m_lo = rmse(fc[ev[~hi[:len(ev)]]], X[ev[~hi[:len(ev)]] + h])
            c = oos_corr(fc, h, ev)
            table[(mth, h)] = all_
            corrs[(mth, h)] = c
            rows.append({"method": mth, "h": h, "rmse": all_, "corr": c,
                         "rmse_hiVIX": m_hi, "rmse_loVIX": m_lo})

    # ---- report ----
    print(f"OOS RMSE of predicting X_(t+h)  (standardized units; lower=better)")
    print(f"{'method':<14}" + "".join(f"{f'h={h}':>10}" for h in HORIZONS)
          + f"{'skill@21':>10}")
    print("-" * 64)
    for mth in methods:
        line = f"{mth:<14}" + "".join(f"{table[(mth,h)]:>10.4f}" for h in HORIZONS)
        skill = 1 - table[(mth, 21)] / table[("persistence", 21)]
        print(line + f"{skill:>10.1%}")
    print("-" * 64)
    print("skill@21 = 1 - RMSE/persistence at h=21 (higher=better; captures dynamics)\n")

    print("SCALE-INVARIANT predictive info: OOS corr(forecast, X_(t+h))  (higher=better)")
    print(f"{'method':<14}" + "".join(f"{f'h={h}':>10}" for h in HORIZONS))
    for mth in methods:
        print(f"{mth:<14}" + "".join(f"{corrs[(mth,h)]:>10.3f}" for h in HORIZONS))
    print()

    print("h=21 RMSE by VIX regime (adaptivity: does HMM win where it should?)")
    print(f"{'method':<14}{'hiVIX':>10}{'loVIX':>10}")
    for r in [r for r in rows if r["h"] == 21]:
        print(f"{r['method']:<14}{r['rmse_hiVIX']:>10.4f}{r['rmse_loVIX']:>10.4f}")

    # jitter of the current-state estimate (smoothers only)
    def jit(est):
        return float(np.nanmean(np.linalg.norm(np.diff(est[oos], axis=0), axis=1)))
    print(f"\njitter (mean |d/dt| of current-state estimate, OOS): "
          f"raw={jit(X):.3f}  EWMA={jit(ewma):.3f}  HMM_Z={jit(Z):.3f}")

    pd.DataFrame(rows).to_csv(os.path.join(RESULTS_DIR, "filter_horserace.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'filter_horserace.csv')}")


if __name__ == "__main__":
    main()
