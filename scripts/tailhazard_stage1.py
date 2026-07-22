#!/usr/bin/env python3
"""STAGE-1 frozen battery for the tail-hazard MVE (.planning/CONTINUOUS-JUMP-STATE-DECISION.md §8).

Reads data/processed/tailhazard_daily.csv (from tailhazard_build.py). Target y[t] = event[t+1]
(H[t] includes e_t, so contemporaneous pairing would leak the target — see prereg §5).
Ladder A / B_vol / B_lev / C (spline+ridge) / D (C + H_t(beta)); primary = OOS mean
dlogscore(D-C) with stationary block bootstrap + leave-one-crisis-out; increment curve
D-A / D-B_vol / D-B_lev / D-C; hazard-shape diagnostic; Case-D screen; controls
(positive-tail placebo, shifted-history surrogate, simulation calibration); VIX-era kill-check.

ALL rungs are fit by penalized MLE over bernoulli_nll with H from excitation_state
(scripts/tailhazard_core.py, Adam-written) — the battery cannot run until the core exists.

Usage: python scripts/tailhazard_stage1.py [panel_csv] [--quick]
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.preprocessing import StandardScaler, SplineTransformer

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from src.config import DATA_DIR, RESULTS_DIR  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tailhazard_build import EPISODES  # noqa: E402
from tailhazard_core import bernoulli_nll, excitation_state  # noqa: E402

BVOL = ["log_sigma", "log_rv21", "log_rv63"]
BLEV = BVOL + ["r_neg_1d", "r_neg_5d", "r_neg_21d", "rs_share_21d", "down_days_21d"]
HALF_LIVES = [1, 2, 5, 10, 21, 63]          # frozen beta grid, beta = ln2/hl
ALPHAS = np.logspace(-4, 1, 6)              # ridge grid for rung C (blocked CV, training only)
ALPHA_B = 1e-4                              # conditioning-only ridge for the low-dim B rungs
CLIP = 1e-5                                 # frozen probability clip for log-scores
BURN = 0.40
CV_FOLDS = 5
N_SURR, N_SIM = 10, 10
RNG = np.random.default_rng(0)


def fit_hazard(X, Hc, y, alpha):
    """Penalized MLE over Adam's bernoulli_nll. Ridge on g = params[2:] only —
    intercept a and excitation b unpenalized (shrinking b would shrink the tested effect).
    Gradient here is scaffolding calculus, not core math: d(mean NLL)/du = (sigmoid(u)-y)/n."""
    k = X.shape[1]
    p0 = np.zeros(2 + k)
    ybar = min(max(y.mean(), 1e-4), 1 - 1e-4)
    p0[0] = np.log(ybar / (1 - ybar))

    def obj(p):
        return bernoulli_nll(p, Hc, X, y) + alpha * np.sum(p[2:] ** 2)

    def grad(p):
        r = expit(p[0] + p[1] * Hc + X @ p[2:]) - y
        g = np.empty_like(p)
        g[0] = r.mean()
        g[1] = (r * Hc).mean()
        g[2:] = X.T @ r / len(y) + 2 * alpha * p[2:]
        return g

    return minimize(obj, p0, jac=grad, method="L-BFGS-B", options={"maxiter": 500}).x


def predict(p, Hc, X):
    return expit(p[0] + p[1] * Hc + X @ p[2:])


def blocked_cv(X, Hc, y, alphas, hls=None, folds=None):
    """Contiguous-fold CV on the training block only. If hls given, selects half-life at
    fixed alpha (Hc is then a dict hl->array); else selects alpha (Hc an array)."""
    folds = CV_FOLDS if folds is None else folds  # read global at call time (--quick reassigns it)
    n = len(y)
    edges = np.linspace(0, n, folds + 1).astype(int)
    grid = hls if hls is not None else alphas
    scores = np.zeros(len(grid))
    for i, g in enumerate(grid):
        for f in range(folds):
            lo, hi = edges[f], edges[f + 1]
            tr = np.r_[0:lo, hi:n]
            H_tr = (Hc[g][tr] if hls is not None else Hc[tr])
            H_va = (Hc[g][lo:hi] if hls is not None else Hc[lo:hi])
            a = alphas if np.isscalar(alphas) else g
            p = fit_hazard(X[tr], H_tr, y[tr], a if hls is None else alphas)
            scores[i] += logscore(y[lo:hi], predict(p, H_va, X[lo:hi])).mean()
    return grid[int(np.argmin(scores))]


def logscore(y, p):
    p = np.clip(p, CLIP, 1 - CLIP)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def oos_run(F_vol, F_lev, e_hist, y, idx, alphas_fixed=None, rungs=("A", "B_vol", "B_lev", "C", "D")):
    """Rolling-origin expanding OOS. e_hist = event series used to build H (the surrogate
    control passes a shifted copy); y = target (event at t+1). Returns preds + refit log."""
    n = len(idx)
    burn = int(BURN * n)
    refits = list(range(burn, n, 252)) + [n]
    H_by_hl = {hl: excitation_state(e_hist, np.log(2) / hl) for hl in HALF_LIVES}
    preds = {k: np.full(len(y), np.nan) for k in rungs}
    log = []
    for r in range(len(refits) - 1):
        R, Rn = refits[r], refits[r + 1]
        gR = idx[R]
        tr = idx[:R]
        tr = tr[tr + 1 < gR]  # drop training rows whose target is the first test-day event
        te = idx[R:Rn]
        if len(tr) < 500 or len(te) == 0:
            continue
        sc_v = StandardScaler().fit(F_vol[tr])
        sc_l = StandardScaler().fit(F_lev[tr])
        Xv_tr, Xv_te = sc_v.transform(F_vol[tr]), sc_v.transform(F_vol[te])
        Xl_tr, Xl_te = sc_l.transform(F_lev[tr]), sc_l.transform(F_lev[te])
        sp = SplineTransformer(n_knots=4, degree=3, knots="quantile",
                               extrapolation="linear").fit(Xl_tr)
        Xc_tr, Xc_te = sp.transform(Xl_tr), sp.transform(Xl_te)
        z_tr, z_te = np.zeros(len(tr)), np.zeros(len(te))
        ytr = y[tr]

        if "A" in preds:
            pA = fit_hazard(np.zeros((len(tr), 0)), z_tr, ytr, 0.0)
            preds["A"][te] = predict(pA, z_te, np.zeros((len(te), 0)))
        if "B_vol" in preds:
            pB = fit_hazard(Xv_tr, z_tr, ytr, ALPHA_B)
            preds["B_vol"][te] = predict(pB, z_te, Xv_te)
        if "B_lev" in preds:
            pL = fit_hazard(Xl_tr, z_tr, ytr, ALPHA_B)
            preds["B_lev"][te] = predict(pL, z_te, Xl_te)

        alpha_c = (alphas_fixed[min(r, len(alphas_fixed) - 1)] if alphas_fixed is not None
                   else blocked_cv(Xc_tr, z_tr, ytr, ALPHAS))
        if "C" in preds:
            pC = fit_hazard(Xc_tr, z_tr, ytr, alpha_c)
            preds["C"][te] = predict(pC, z_te, Xc_te)
        if "D" in preds:
            Htr = {hl: H_by_hl[hl][tr] for hl in HALF_LIVES}
            hl = blocked_cv(Xc_tr, Htr, ytr, alpha_c, hls=HALF_LIVES)
            pD = fit_hazard(Xc_tr, H_by_hl[hl][tr], ytr, alpha_c)
            preds["D"][te] = predict(pD, H_by_hl[hl][te], Xc_te)
            log.append({"refit": r, "alpha_c": alpha_c, "half_life": hl, "b": pD[1],
                        "n_train": len(tr)})
        else:
            log.append({"refit": r, "alpha_c": alpha_c})
    return preds, log


def stationary_boot(d, reps=1000, meanblock=126):
    n = len(d)
    out = np.empty(reps)
    prob = 1.0 / meanblock
    for b in range(reps):
        take, i = [], RNG.integers(0, n)
        while len(take) < n:
            take.append(i)
            i = RNG.integers(0, n) if RNG.random() < prob else (i + 1) % n
        out[b] = d[np.array(take[:n])].mean()
    return out


def christoffersen_lr(e):
    """First-order Markov LR independence test on the event sequence (Christoffersen 1998)."""
    from scipy.stats import chi2
    a, b_ = e[:-1].astype(int), e[1:].astype(int)
    n00 = np.sum((a == 0) & (b_ == 0)); n01 = np.sum((a == 0) & (b_ == 1))
    n10 = np.sum((a == 1) & (b_ == 0)); n11 = np.sum((a == 1) & (b_ == 1))
    p01, p11 = n01 / max(n00 + n01, 1), n11 / max(n10 + n11, 1)
    p = (n01 + n11) / (n00 + n01 + n10 + n11)
    def ll(x, k, n):
        return 0.0 if x in (0, 1) else k * np.log(x) + (n - k) * np.log(1 - x)
    lr = 2 * (ll(p01, n01, n00 + n01) + ll(p11, n11, n10 + n11) - ll(p, n01 + n11, len(a)))
    return lr, 1 - chi2.cdf(lr, 1), p01, p11


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quick = "--quick" in sys.argv
    global ALPHAS, HALF_LIVES, N_SURR, N_SIM, CV_FOLDS
    if quick:
        ALPHAS, HALF_LIVES = np.logspace(-3, 0, 3), [2, 5, 21]
        N_SURR, N_SIM, CV_FOLDS = 3, 3, 3
    path = args[0] if args else os.path.join(DATA_DIR, "processed", "tailhazard_daily.csv")
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    df["y"] = df["event"].shift(-1)
    feat_ok = np.isfinite(df[BLEV].values).all(1)
    ok = feat_ok & df["event"].notna().values & df["y"].notna().values
    idx = np.where(ok)[0]
    e = np.where(ok, df["event"].values, 0.0)   # zero outside eligibility; H burn-in >> OOS start
    y = df["y"].values
    F_vol, F_lev = df[BVOL].values, df[BLEV].values
    dates = df.index

    print("=" * 78)
    print(f"TAIL-HAZARD STAGE 1 (frozen prereg §8)   eligible N={len(idx)}  "
          f"events={int(np.nansum(y[idx]))}  {dates[idx[0]].date()}..{dates[idx[-1]].date()}"
          + ("   [QUICK]" if quick else ""))
    print("=" * 78)

    preds, log = oos_run(F_vol, F_lev, e, y, idx)
    logdf = pd.DataFrame(log)
    mask = np.zeros(len(y), bool)
    mask[idx] = True
    for k in preds:
        mask &= np.isfinite(preds[k])
    yv = y[mask]
    ls = {k: logscore(yv, preds[k][mask]) for k in preds}
    br = {k: np.mean((np.clip(preds[k][mask], CLIP, 1 - CLIP) - yv) ** 2) for k in preds}
    print(f"OOS days N={mask.sum()} ({dates[mask][0].date()}..{dates[mask][-1].date()}), "
          f"OOS events={int(yv.sum())}")
    print("\nMean OOS log-score (nats/day, lower better) and increment vs D (+ = D better):")
    for k in ("A", "B_vol", "B_lev", "C", "D"):
        print(f"  {k:<6} LS={ls[k].mean():.5f}  Brier={br[k]:.5f}  "
              f"dLS(D-{k})={ls[k].mean() - ls['D'].mean():+.5f}")
    d = ls["C"] - ls["D"]
    boot = stationary_boot(d)
    print(f"\nPRIMARY dlogscore(D-C) = {d.mean():+.5f}  "
          f"block-boot 90% CI [{np.percentile(boot, 5):+.5f}, {np.percentile(boot, 95):+.5f}]  "
          f"P(>0)={np.mean(boot > 0):.2f}")

    print("\nLeave-one-crisis-out (pooled dLS(D-C) with that episode's OOS days removed):")
    mdates = dates[mask]
    for nm, (a, b_) in EPISODES.items():
        keep = ~((mdates >= a) & (mdates <= b_))
        if (~keep).sum() > 0:
            print(f"  drop {nm:<26} dLS={d[keep].mean():+.5f}  (removed {(~keep).sum()} days)")

    print("\nPer-refit rung-D estimates (b = excitation coefficient, training MLE):")
    h1 = logdf[logdf["refit"] < logdf["refit"].median()]
    h2 = logdf[logdf["refit"] >= logdf["refit"].median()]
    print(f"  b: mean={logdf['b'].mean():+.3f}  early-half mean={h1['b'].mean():+.3f}  "
          f"late-half mean={h2['b'].mean():+.3f}  sign-consistent="
          f"{bool(np.sign(h1['b'].mean()) == np.sign(h2['b'].mean()))}")
    print(f"  chosen half-life (days): {sorted(logdf['half_life'].value_counts().to_dict().items())}")

    print("\nCase-D screen (in-sample, eligible span): Christoffersen first-order independence")
    lr, pval, p01, p11 = christoffersen_lr(df["event"].values[idx].astype(float))
    print(f"  P(event|no event)={p01:.4f}  P(event|event)={p11:.4f}  LR={lr:.2f}  p={pval:.4f}")
    print("  (screen only — the frozen falsifier is the OOS D-C primary, not this)")

    print("\nHazard-shape diagnostic (in-sample): P(event at lag tau | event at 0) / base rate")
    ev = df["event"].values[idx].astype(bool)
    base = ev.mean()
    prof = [(tau, ev[tau:][ev[:-tau]].mean() / base) for tau in (1, 2, 3, 5, 10, 21)]
    print("  " + "  ".join(f"tau={t}: {v:.2f}x" for t, v in prof))

    # ---- controls ----
    alphas_fixed = logdf["alpha_c"].values
    print("\n" + "=" * 78 + "\nCONTROLS\n" + "=" * 78)
    ep = np.where(ok, (df["z"].values > 2.0).astype(float), 0.0)
    yp = np.full(len(y), np.nan)
    yp[idx[:-1]] = ep[idx[1:]]
    pp, _ = oos_run(F_vol, F_lev, ep, yp, idx[:-1], alphas_fixed, rungs=("C", "D"))
    mp = np.zeros(len(y), bool); mp[idx[:-1]] = True
    mp &= np.isfinite(pp["C"]) & np.isfinite(pp["D"]) & np.isfinite(yp)
    dp = logscore(yp[mp], pp["C"][mp]) - logscore(yp[mp], pp["D"][mp])
    print(f"positive-tail placebo (z>+2 events): dLS(D-C)={dp.mean():+.5f}  "
          f"(expect weaker than primary if mechanism is crash-specific)")

    surr = []
    for s in range(N_SURR):
        shift = int(RNG.integers(500, len(e) - 500))
        es = np.roll(e, shift)
        ps, _ = oos_run(F_vol, F_lev, es, y, idx, alphas_fixed, rungs=("C", "D"))
        ms = np.zeros(len(y), bool); ms[idx] = True
        ms &= np.isfinite(ps["C"]) & np.isfinite(ps["D"])
        surr.append((logscore(y[ms], ps["C"][ms]) - logscore(y[ms], ps["D"][ms])).mean())
    print(f"shifted-history surrogate (x{N_SURR}): dLS(D-C) mean={np.mean(surr):+.5f} "
          f"range [{np.min(surr):+.5f}, {np.max(surr):+.5f}]  (must be ~0)")

    sims = []
    pC_full = np.clip(np.where(np.isfinite(preds["C"]), preds["C"],
                               np.nanmean(preds["C"])), CLIP, 1 - CLIP)
    for s in range(N_SIM):
        ysim = np.where(ok, (RNG.random(len(y)) < pC_full).astype(float), np.nan)
        esim = np.where(ok, ysim, 0.0)
        esim_hist = np.roll(esim, 1)  # simulated event known end-of-day: history shifts by one
        psim, _ = oos_run(F_vol, F_lev, esim_hist, ysim, idx, alphas_fixed, rungs=("C", "D"))
        msim = np.zeros(len(y), bool); msim[idx] = True
        msim &= np.isfinite(psim["C"]) & np.isfinite(psim["D"]) & np.isfinite(ysim)
        sims.append((logscore(ysim[msim], psim["C"][msim])
                     - logscore(ysim[msim], psim["D"][msim])).mean())
    print(f"simulation calibration (x{N_SIM}, y*~Bern(p_C), no excitation): "
          f"dLS(D-C) mean={np.mean(sims):+.5f} range [{np.min(sims):+.5f}, {np.max(sims):+.5f}]"
          f"  (false-positive scale for the primary)")

    # ---- VIX-era kill-check ----
    print("\n" + "=" * 78 + "\nVIX-ERA KILL-CHECK (1990+, prior-day VIX close in every rung)\n" + "=" * 78)
    vix = np.log(df["vix"].shift(1).values)
    okv = ok & np.isfinite(vix)
    idxv = np.where(okv)[0]
    Fv_vol = np.column_stack([F_vol, vix])
    Fv_lev = np.column_stack([F_lev, vix])
    pv, _ = oos_run(Fv_vol, Fv_lev, e, y, idxv, rungs=("C", "D"))
    mv = np.zeros(len(y), bool); mv[idxv] = True
    mv &= np.isfinite(pv["C"]) & np.isfinite(pv["D"])
    dv = logscore(y[mv], pv["C"][mv]) - logscore(y[mv], pv["D"][mv])
    bootv = stationary_boot(dv)
    print(f"  dLS(D-C)={dv.mean():+.5f}  90% CI [{np.percentile(bootv, 5):+.5f}, "
          f"{np.percentile(bootv, 95):+.5f}]  N={mv.sum()}  "
          f"(kill-check: primary must independently hold here)")
    print("\nNFCI-added variant (1971+): SKIPPED — NFCI not yet in panel (session-3 item).")

    out = pd.DataFrame([
        {"metric": "primary_dLS_D_C", "value": d.mean()},
        {"metric": "ci_lo", "value": np.percentile(boot, 5)},
        {"metric": "ci_hi", "value": np.percentile(boot, 95)},
        {"metric": "p_gt0", "value": np.mean(boot > 0)},
        {"metric": "dLS_D_A", "value": ls["A"].mean() - ls["D"].mean()},
        {"metric": "dLS_D_Bvol", "value": ls["B_vol"].mean() - ls["D"].mean()},
        {"metric": "dLS_D_Blev", "value": ls["B_lev"].mean() - ls["D"].mean()},
        {"metric": "placebo_dLS", "value": dp.mean()},
        {"metric": "surrogate_dLS_mean", "value": np.mean(surr)},
        {"metric": "sim_dLS_mean", "value": np.mean(sims)},
        {"metric": "vix_era_dLS", "value": dv.mean()},
        {"metric": "vix_era_ci_lo", "value": np.percentile(bootv, 5)},
        {"metric": "b_mean", "value": logdf["b"].mean()},
        {"metric": "christoffersen_p", "value": pval},
    ])
    out.to_csv(os.path.join(RESULTS_DIR, "tailhazard_stage1.csv"), index=False)
    pd.DataFrame({("pred_" + k): preds[k] for k in preds}, index=dates)[mask].assign(
        y=yv).to_csv(os.path.join(RESULTS_DIR, "tailhazard_stage1_preds.csv"))
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'tailhazard_stage1.csv')} (+ _preds.csv)")


if __name__ == "__main__":
    main()
