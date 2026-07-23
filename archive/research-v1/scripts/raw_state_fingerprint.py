#!/usr/bin/env python3
"""What did the model actually find? Raw 8-state geometry, NO VIX projection.

Every prior evaluation ran on labels produced by merge_states_to_regimes(): sort the
raw states by mean VIX, cut into thirds. That projection collapses each state's 4-D
location to a single VIX rank BEFORE anything is measured -- so "the states are VIX"
may be an artifact of the projection, not a property of what the model learned.

This script never sorts or buckets by VIX. It refits the baseline HDP-HMM (seed 42 =
paper) and asks one assumption-free, geometric question of the raw state means in
standardized feature space (spy_ret, vol_index, yield_slope, nfci):

  HOW MANY INDEPENDENT AXES do the 8 states actually span, and which features
  separate them?

  (1) PER-FEATURE SPREAD -- std of the 8 state-means per feature (normalized by the
      data's own per-feature std). Large only for VIX => states separate on vol only.
  (2) EFFECTIVE DIMENSIONALITY -- SVD of the centered, scale-normalized state-mean
      matrix. PC1 variance fraction + participation ratio PR=(sum s^2)^2/sum s^4.
      PR~1 => the 8 states lie on ONE line (a ladder); PR~2-3 => real multivariate
      structure the VIX-sort destroyed.
  (3) AXIS INDEPENDENCE -- cross-state corr of each feature-mean with the VIX-mean.
      |rho|~1 everywhere => everything rides the vol axis; a low |rho| => a feature
      that separates states independently of VIX (the "hidden" axis).
  (4) TRANSITION GEOMETRY -- order states by PC1, is the transition matrix a
      band-diagonal ladder (1-D dynamics) or is there off-ladder structure?

VIX and realized vol are computed only to ANNOTATE each raw state (so we can read what
it is), never to order or define them.

Reads  : data/processed/features_train.csv, data/processed/spx_data.csv
Writes : results/raw_state_fingerprint.csv
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

from src.config import FEATURES, HDP_TRUNCATION, RANDOM_SEED, DATA_DIR, RESULTS_DIR
from src.core.hdp_hmm import fit_hdp_hmm, posterior_mean_params, get_labels_and_probs

PROC = os.path.join(DATA_DIR, "processed")
VIX_COL = FEATURES.index("vol_index")


def main():
    feat = pd.read_csv(os.path.join(PROC, "features_train.csv"),
                       parse_dates=["Date"]).set_index("Date")
    raw = pd.read_csv(os.path.join(PROC, "spx_data.csv"),
                      parse_dates=["Date"]).set_index("Date").reindex(feat.index)
    X = feat[FEATURES].values
    vix_raw, ret_raw = raw["vol_index"].values, raw["spy_ret"].values
    print(f"Train N={len(X)} ({feat.index[0].date()}..{feat.index[-1].date()}), "
          f"features={FEATURES}\n")

    _, samples = fit_hdp_hmm(X, K_max=HDP_TRUNCATION, seed=RANDOM_SEED)
    params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
    labels, _, _, active = get_labels_and_probs(X, params, hold_days=1)  # raw argmax
    locs = params["locs"]                    # (K, 4) state means, standardized space
    K = params["K_max"]

    # ---- annotate each raw state (VIX/vol used ONLY to describe, not to order) ----
    rows = []
    for k in range(K):
        m = labels == k
        n = int(m.sum())
        rows.append({
            "state": k, "n_days": n, "occupancy": n / len(X),
            "active": k in active,
            "ann_realized_vol": (float(ret_raw[m].std() * np.sqrt(252) * 100)
                                 if n > 5 else np.nan),
            "mean_VIX": float(vix_raw[m].mean()) if n > 0 else np.nan,
            **{f"mu_{f}": float(locs[k, i]) for i, f in enumerate(FEATURES)},
        })
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 160, "display.max_columns", 30)
    print("Raw states (means in STANDARDIZED feature space; VIX/vol are annotation):")
    print(df.round(3).to_string(index=False), "\n")

    # ---- geometry on the state-mean matrix, scale-normalized per feature ----
    data_sd = X.std(axis=0)                          # per-feature spread of the data
    M = locs / data_sd                               # comparable units across features
    spread = M.std(axis=0)                           # per-feature spread of state means
    print("(1) Per-feature spread of state means (/ data std) -- what states separate on:")
    for f, s in zip(FEATURES, spread):
        print(f"      {f:<12} {s:6.3f}")

    Mc = M - M.mean(axis=0)
    U, s, Vt = np.linalg.svd(Mc, full_matrices=False)
    var = s ** 2
    frac = var / var.sum()
    pr = (var.sum() ** 2) / (var ** 2).sum()          # participation ratio
    print(f"\n(2) Effective dimensionality of the 8 state means:")
    print(f"      PC variance fractions: {np.round(frac, 3)}")
    print(f"      PC1 alone: {frac[0]*100:.1f}%   participation ratio: {pr:.2f} (of 4)")
    print(f"      PC1 loadings: " +
          "  ".join(f"{f}={v:+.2f}" for f, v in zip(FEATURES, Vt[0])))
    print(f"      PC2 loadings: " +
          "  ".join(f"{f}={v:+.2f}" for f, v in zip(FEATURES, Vt[1])))

    print(f"\n(3) Cross-state corr of each feature-mean with the VIX-mean:")
    vixcoord = M[:, VIX_COL]
    for i, f in enumerate(FEATURES):
        rho = np.corrcoef(M[:, i], vixcoord)[0, 1] if i != VIX_COL else 1.0
        print(f"      {f:<12} rho={rho:+.3f}")

    # ---- transition geometry: order by PC1, band-diagonal? ----
    order = np.argsort(U[:, 0] * s[0])
    T = params["trans_matrix"][np.ix_(order, order)]
    band = sum(T[i, j] for i in range(K) for j in range(K) if abs(i - j) <= 1)
    print(f"\n(4) Transition matrix reordered by PC1 axis:")
    print("      " + np.array2string(T.round(2), prefix="      "))
    print(f"      mass on |i-j|<=1 band: {band / K * 100:.0f}% of row-sum "
          f"(high => 1-D ladder dynamics)")

    df.to_csv(os.path.join(RESULTS_DIR, "raw_state_fingerprint.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'raw_state_fingerprint.csv')}")


if __name__ == "__main__":
    main()
