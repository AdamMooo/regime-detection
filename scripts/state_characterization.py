#!/usr/bin/env python3
"""Finish Q1: characterize the object before choosing any outcome to condition on.

Three descriptive, hypothesis-free questions about the raw HDP-HMM output (seed 42):

  (A) CLUSTERS or CONTINUUM? Is the joint feature cloud multimodal (real discrete
      states) or a single blob we are arbitrarily gridding? -> silhouette of the state
      assignment (near 0 => tiling a continuum; >0.25 => real separation) + GMM BIC
      curve shape (clear minimum => natural K; monotone => no natural K) + a 2-D map.

  (B) TIME-SIGNATURE of each axis (the common gate on ALL Tier-3 conditioning tests).
      corr(daily PC-score, calendar time) for the stress axis (PC1) and the macro axis
      (PC2). A recurring axis oscillates (low |corr| with time, many median crossings);
      a secular axis is a one-way drift (high |corr|, few crossings). Plus how much of
      the state-to-state MOVEMENT is along each axis (few transitions across the macro
      axis => it is slow background context, not a switching regime).

  (C) SCALE structure (guard against narrowing to the means). Does within-state
      dispersion (scale_diag) vary independently of location -- a 'turbulent vs quiet'
      dimension the mean-geometry missed?

Reads  : data/processed/features_train.csv, data/processed/spx_data.csv
Writes : results/state_characterization.png
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
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import FEATURES, HDP_TRUNCATION, RANDOM_SEED, DATA_DIR, RESULTS_DIR
from src.core.hdp_hmm import fit_hdp_hmm, posterior_mean_params, get_labels_and_probs

PROC = os.path.join(DATA_DIR, "processed")


def main():
    feat = pd.read_csv(os.path.join(PROC, "features_train.csv"),
                       parse_dates=["Date"]).set_index("Date")
    raw = pd.read_csv(os.path.join(PROC, "spx_data.csv"),
                      parse_dates=["Date"]).set_index("Date").reindex(feat.index)
    X = feat[FEATURES].values
    dates = feat.index
    tnorm = np.linspace(0, 1, len(X))
    print(f"Train N={len(X)} ({dates[0].date()}..{dates[-1].date()})\n")

    _, samples = fit_hdp_hmm(X, K_max=HDP_TRUNCATION, seed=RANDOM_SEED)
    params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
    labels, _, _, active = get_labels_and_probs(X, params, hold_days=1)
    locs, scales, K = params["locs"], params["scale_diag"], params["K_max"]

    # axes from the state-mean geometry (standardized space)
    mu, sd = X.mean(0), X.std(0)
    Xs = (X - mu) / sd
    Ms = (locs - mu) / sd
    Msc = Ms - Ms.mean(0)
    _, _, Vt = np.linalg.svd(Msc, full_matrices=False)
    day = Xs @ Vt.T                              # daily scores on the state axes
    pc1, pc2 = day[:, 0], day[:, 1]

    # ---------- (A) clusters vs continuum ----------
    sil = silhouette_score(Xs, labels)
    bics = [GaussianMixture(k, covariance_type="diag", n_init=5,
                            random_state=RANDOM_SEED).fit(Xs).bic(Xs)
            for k in range(1, 13)]
    bics = np.array(bics)
    bic_min_k = int(np.argmin(bics) + 1)
    print("(A) CLUSTERS vs CONTINUUM")
    print(f"      silhouette of state assignment: {sil:+.3f} "
          f"(<0.15 ~ tiling a continuum; >0.25 ~ real clusters)")
    print(f"      GMM BIC argmin at K={bic_min_k} of 12 "
          f"(=12 => no natural K, keeps subdividing => continuum)")
    print(f"      BIC drop K1->K2 {bics[0]-bics[1]:.0f}, "
          f"K5->K6 {bics[4]-bics[5]:.0f}, K11->K12 {bics[10]-bics[11]:.0f} "
          f"(flattening => diminishing structure)")

    # ---------- (B) time-signature ----------
    def crossings(z):
        s = np.sign(z - np.median(z))
        return int((np.diff(s) != 0).sum())

    print("\n(B) TIME-SIGNATURE (the gate on Tier-3 conditioning)")
    print(f"      corr(stress axis PC1, time) = {np.corrcoef(pc1, tnorm)[0,1]:+.3f}   "
          f"median-crossings={crossings(pc1)}")
    print(f"      corr(macro  axis PC2, time) = {np.corrcoef(pc2, tnorm)[0,1]:+.3f}   "
          f"median-crossings={crossings(pc2)}")
    print(f"      (raw sanity) corr(yield_slope, time)={np.corrcoef(X[:,FEATURES.index('yield_slope')], tnorm)[0,1]:+.3f}  "
          f"corr(VIX, time)={np.corrcoef(X[:,FEATURES.index('vol_index')], tnorm)[0,1]:+.3f}")

    # movement along each axis (transitions ranked by PC1 vs PC2)
    r1 = np.argsort(np.argsort(Msc @ Vt.T[:, 0]))   # state rank on PC1
    r2 = np.argsort(np.argsort(Msc @ Vt.T[:, 1]))   # state rank on PC2
    chg = np.where(np.diff(labels) != 0)[0]
    d1 = sum(abs(r1[labels[i+1]] - r1[labels[i]]) for i in chg)
    d2 = sum(abs(r2[labels[i+1]] - r2[labels[i]]) for i in chg)
    print(f"      state-to-state movement: {d1/(d1+d2)*100:.0f}% along stress axis, "
          f"{d2/(d1+d2)*100:.0f}% along macro axis "
          f"(little macro movement => slow background, not a switching regime)")

    # per-state mean calendar position (secular states cluster in time)
    print("      per-state mean sample-position (0=start,1=end) & PC2 rank:")
    for k in sorted(active, key=lambda s: (Msc @ Vt.T[:, 1])[s]):
        m = labels == k
        if m.sum() > 5:
            print(f"        state {k}: PC2={(Msc @ Vt.T[:,1])[k]:+.2f}  "
                  f"mean_t={tnorm[m].mean():.2f}  n={m.sum()}")

    # ---------- (C) scale structure ----------
    loc_norm = np.linalg.norm(Ms, axis=1)
    scl_norm = np.linalg.norm(scales / sd, axis=1)
    print("\n(C) SCALE structure")
    print(f"      corr(state location-norm, state scale-norm) = "
          f"{np.corrcoef(loc_norm[active], scl_norm[active])[0,1]:+.3f}")
    print(f"      scale-norm range across active states: "
          f"{scl_norm[active].min():.2f}..{scl_norm[active].max():.2f} "
          f"(wide + uncorrelated w/ location => a dispersion dimension)")

    # ---------- figure ----------
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.3))
    hb = ax1.hexbin(pc1, pc2, gridsize=30, cmap="Blues", mincnt=1)
    ax1.scatter((Msc @ Vt.T[:, 0])[active], (Msc @ Vt.T[:, 1])[active],
                c="red", s=60, marker="x")
    ax1.set(title="(A) data cloud on state axes\n(blob=continuum, islands=clusters)",
            xlabel="PC1 stress", ylabel="PC2 macro/curve")
    ax2.plot(dates, pc2, lw=0.7, color="#b7791f", label="macro PC2")
    ax2.plot(dates, pc1, lw=0.5, color="#2b6cb0", alpha=0.6, label="stress PC1")
    ax2.axhline(np.median(pc2), color="#b7791f", ls=":", lw=0.8)
    ax2.set(title="(B) axis scores over time\n(PC2 drift=secular, oscillation=recurring)")
    ax2.legend(fontsize=8)
    ax3.plot(range(1, 13), bics, "o-")
    ax3.set(title="(A) GMM BIC vs K\n(clear min=natural K; monotone=continuum)",
            xlabel="K components", ylabel="BIC")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "state_characterization.png"), dpi=130)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'state_characterization.png')}")


if __name__ == "__main__":
    main()
