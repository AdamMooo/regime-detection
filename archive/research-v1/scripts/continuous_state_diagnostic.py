#!/usr/bin/env python3
"""Is the latent environment better represented as a CONTINUOUS coordinate than
discrete labels? Falsifiable test of H_cont vs H_fail. (.planning/ROADMAP.md gate.)

Object under test: Z_t = E[mu_{S_t} | X_{1:t}] = sum_k gamma_t(k) mu_k -- the
posterior-mean LOCATION in feature space. Unlike the discrete label (argmax gamma)
or the mixing weights gamma_t, Z_t is LABEL-SWITCHING-INVARIANT: it is a physical
point in the shared feature space, so it can be compared across independent fits
with NO state-identity alignment and NO VIX-merge (the projection we now distrust).
That is the mathematical reason it MIGHT be more stable -- this script tests whether
it actually is, with pre-registered pass/fail bars.

Design: hold the feature representation FIXED (one standardized matrix) and vary only
the training window (expanding / 5y / 3y) + one extra seed on expanding as a pure-SVI
noise floor. All Z_t live in the same space -> directly comparable. (Fixed
standardization isolates the window-length effect for this reproducibility diagnostic;
a faithful rolling model would re-standardize -- that matters for prediction, not for
testing whether the inferred coordinate reproduces.)

Four pre-registered tests + bars:
  A STABILITY  -- cross-window corr(Z_t) vs cross-window label ARI. H_cont needs
     Z-corr clearly > label-ARI and Z-corr >~0.6-0.7. If Z-corr also low -> H_fail.
  B ATTRIBUTION-- R^2 of Z_t explained by a plain causal EWMA smoother of X_t. If
     >~0.9, the 'environment' is just smoothed observables and the HMM is redundant.
  C LOCALIZATION-- on days two fits disagree on the label, is ||Z^A - Z^B|| small
     vs the inter-state-mean scale (boundary/discretization artifact -> H_cont) or
     large (the environment estimate itself moves -> H_fail)?
  D COORD-SYSTEM-- do the state-mean PCA axes reproduce across fits (principal angles,
     participation ratio, Hungarian-matched mean codebook)? If axes rotate fit-to-fit,
     the 2-D geometry was a per-sample artifact.

Reads  : data/processed/features_train.csv
Writes : results/continuous_state_diagnostic.png
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.linalg import subspace_angles
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import FEATURES, HDP_TRUNCATION, DATA_DIR, RESULTS_DIR
from src.core.hdp_hmm import fit_hdp_hmm, posterior_mean_params, get_labels_and_probs

PROC = os.path.join(DATA_DIR, "processed")
WINDOWS = {"exp_s42": (None, 42), "5y_s42": (1260, 42),
           "3y_s42": (756, 42), "exp_s123": (None, 123)}
EVAL = 756   # common tail all windows cover (~last 3y of train)


def fit_one(X, win, seed, mu, sd):
    Xtr = X if win is None else X[-win:]
    _, samples = fit_hdp_hmm(Xtr, K_max=HDP_TRUNCATION, seed=seed)
    params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
    labels, filt, _, active = get_labels_and_probs(X, params, hold_days=1)
    loc_a = params["locs"][active]
    Z = filt @ loc_a                                   # (T,4) posterior-mean location
    diff = loc_a[None] - Z[:, None]                    # between-state spread
    betw = (filt[:, :, None] * diff ** 2).sum(axis=(1, 2))
    Msc = (loc_a - mu) / sd
    Msc = Msc - Msc.mean(0)
    _, s, Vt = np.linalg.svd(Msc, full_matrices=False)
    pr = (s ** 2).sum() ** 2 / (s ** 4).sum()
    return dict(Z=Z, labels=labels, betw=betw, Vt=Vt, pr=pr, loc_std=(loc_a - mu) / sd)


def main():
    feat = pd.read_csv(os.path.join(PROC, "features_train.csv"),
                       parse_dates=["Date"]).set_index("Date")
    X = feat[FEATURES].values
    mu, sd = X.mean(0), X.std(0)
    dates = feat.index
    sl = slice(len(X) - EVAL, len(X))
    print(f"Train N={len(X)}; common eval tail = last {EVAL} days "
          f"({dates[sl][0].date()}..{dates[sl][-1].date()})\n")

    res = {n: fit_one(X, w, s, mu, sd) for n, (w, s) in WINDOWS.items()}
    Vc = res["exp_s42"]["Vt"][:2].T                    # common 2-D coordinate axes
    proj = lambda Z: ((Z - mu) / sd) @ Vc               # -> (T,2) PC1,PC2

    # inter-state-mean scale (for Test C normalization)
    L = res["exp_s42"]["loc_std"]
    inter = np.mean([np.linalg.norm(L[i] - L[j]) for i in range(len(L))
                     for j in range(i + 1, len(L))])

    # ---------- A: stability ----------
    print("(A) STABILITY  cross-window corr(Z_t)  vs  label ARI   [H_cont: Z >> ARI, Z>~0.65]")
    pairs = [("exp_s42", "5y_s42"), ("exp_s42", "3y_s42"),
             ("5y_s42", "3y_s42"), ("exp_s42", "exp_s123")]
    for a, b in pairs:
        Za, Zb = res[a]["Z"][sl], res[b]["Z"][sl]
        zc = np.mean([np.corrcoef(Za[:, d], Zb[:, d])[0, 1] for d in range(4)])
        Pa, Pb = proj(res[a]["Z"][sl]), proj(res[b]["Z"][sl])
        pc1 = np.corrcoef(Pa[:, 0], Pb[:, 0])[0, 1]
        pc2 = np.corrcoef(Pa[:, 1], Pb[:, 1])[0, 1]
        ari = adjusted_rand_score(res[a]["labels"][sl], res[b]["labels"][sl])
        tag = "  (SVI-noise floor)" if b == "exp_s123" else ""
        print(f"    {a:>8} ~ {b:<8}  Z-corr={zc:+.3f}  (PC1={pc1:+.2f} PC2={pc2:+.2f})"
              f"   labelARI={ari:+.3f}{tag}")

    # ---------- B: attribution vs a plain smoother ----------
    print("\n(B) ATTRIBUTION  R^2(Z_t ~ EWMA smoother of X_t)   [>~0.9 => just smoothed features]")
    Xdf = pd.DataFrame(X)
    Zref = res["exp_s42"]["Z"]
    for span in (5, 10, 21, 42, 63):
        S = Xdf.ewm(span=span).mean().values
        r2 = np.mean([np.corrcoef(Zref[sl][:, d], S[sl][:, d])[0, 1] ** 2 for d in range(4)])
        print(f"    EWMA span={span:>2}: mean R^2 = {r2:.3f}")
    r2raw = np.mean([np.corrcoef(Zref[sl][:, d], X[sl][:, d])[0, 1] ** 2 for d in range(4)])
    print(f"    (reference) R^2(Z_t ~ raw X_t, no smoothing) = {r2raw:.3f}")

    # ---------- C: is label disagreement a boundary artifact? ----------
    print("\n(C) LOCALIZATION  ||Z^A-Z^B|| on label-agree vs -disagree days "
          f"(inter-mean scale={inter:.2f})")
    for a, b in [("exp_s42", "3y_s42"), ("exp_s42", "5y_s42")]:
        la, lb = res[a]["labels"][sl], res[b]["labels"][sl]
        d = np.linalg.norm(res[a]["Z"][sl] - res[b]["Z"][sl], axis=1)
        dis = la != lb
        magree = d[~dis].mean() if (~dis).any() else np.nan
        mdis = d[dis].mean() if dis.any() else np.nan
        print(f"    {a} ~ {b}: disagree {dis.mean()*100:4.0f}% of days | "
              f"||dZ|| agree={magree:.2f} disagree={mdis:.2f} "
              f"(disagree/inter-mean={mdis/inter:.2f})")

    # ---------- D: coordinate-system reproducibility ----------
    print("\n(D) COORD-SYSTEM  principal angles to exp_s42's 2-D axes; PR; matched codebook")
    for n in WINDOWS:
        ang = np.degrees(subspace_angles(Vc, res[n]["Vt"][:2].T))
        # Hungarian match of standardized state means to exp_s42's
        A, B = res["exp_s42"]["loc_std"], res[n]["loc_std"]
        C = np.linalg.norm(A[:, None] - B[None, :], axis=2)
        ri, ci = linear_sum_assignment(C)
        matched = C[ri, ci].mean()
        print(f"    {n:>8}: PR={res[n]['pr']:.2f}  principal-angles={np.round(ang,1)} deg  "
              f"matched-codebook dist/inter-mean={matched/inter:.2f}")

    # ---------- figure ----------
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.3), sharex=True)
    for n, c in zip(("exp_s42", "5y_s42", "3y_s42"), ("#2b6cb0", "#dd6b20", "#38a169")):
        P = proj(res[n]["Z"])
        ax[0].plot(dates[sl], P[sl, 0], lw=0.9, color=c, label=n)
        ax[1].plot(dates[sl], P[sl, 1], lw=0.9, color=c, label=n)
    ax[0].set_title("PC1 stress coordinate Z_t across training windows")
    ax[1].set_title("PC2 macro coordinate Z_t across training windows")
    for a in ax:
        a.legend(fontsize=8)
    fig.suptitle("Continuous state coordinate stability (overlay = H_cont; divergence = H_fail)")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "continuous_state_diagnostic.png"), dpi=130)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'continuous_state_diagnostic.png')}")


if __name__ == "__main__":
    main()
