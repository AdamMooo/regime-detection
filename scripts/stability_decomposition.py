"""E2 -- Is the training-window instability genuine, or a tertile-cut artifact?

The prior finding "regime labels agree only 51-69% across training windows" was measured
ONLY on the 3-regime canonical labels produced by the brittle "sort states by VIX, chop
into thirds" merge. That raw-agreement number conflates two very different verdicts:
  - fundamentally unstable latent structure                       (bad)
  - stable gross structure, fragile only at the tertile boundaries (a discretization
    artifact -- "stable coarse / unstable fine")

This script decomposes it, reusing the committed OOS ensemble labels (no recompute):

  (a) ARI -- Adjusted Rand Index (Hubert & Arabie 1985). Chance-corrected partition
      agreement: raw % agreement looks bad partly because 3 imbalanced classes agree
      ~40% by chance alone. ARI subtracts that baseline (0 = chance, 1 = identical).
  (b) RESOLUTION -- collapse 3 regimes to a 2-way calm/stressed cut and re-measure. If
      the binary is far more stable than the 3-way, the instability is fine-grained.
  (c) DISAGREEMENT LOCALITY -- when two windows disagree, is it almost always an ADJACENT
      boundary (Low<->Mod or Mod<->High) rather than the extreme (Low<->High)? All-adjacent
      is the signature of a boundary/discretization artifact, not deep instability.

Run: .venv/Scripts/python.exe scripts/stability_decomposition.py
"""

import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import DATA_DIR, RESULTS_DIR

NAME2IDX = {"Low-Vol": 0, "Moderate-Vol": 1, "High-Vol": 2}
WINDOWS = {"expanding": "expanding_label", "rolling5y": "rolling_1260d_label",
           "rolling3y": "rolling_756d_label"}


def main():
    df = pd.read_csv(os.path.join(DATA_DIR, "oos_regime_labels.csv"), parse_dates=["date"])
    N = len(df)
    labs = {w: df[col].map(NAME2IDX).values for w, col in WINDOWS.items()}
    print(f"OOS ensemble: N={N} days ({df['date'].iloc[0].date()}..{df['date'].iloc[-1].date()})")
    print(f"Ensemble agreement_frac: mean={df['agreement_frac'].mean():.3f}; "
          f"unanimous={int((df['agreement_frac']==1.0).sum())}, "
          f"2of3={int(np.isclose(df['agreement_frac'],2/3).sum())}, "
          f"split={int(np.isclose(df['agreement_frac'],1/3).sum())}")

    # binarizations
    def calm_stressed_A(a):  # Low vs {Mod, High}
        return (a >= 1).astype(int)

    def calm_stressed_B(a):  # {Low, Mod} vs High
        return (a >= 2).astype(int)

    print(f"\n{'='*70}\n(a)+(b) Pairwise agreement & ARI by resolution\n{'='*70}")
    print(f"{'pair':<22}{'3-regime':>18}{'2-reg Low|MH':>16}{'2-reg LM|H':>14}")
    print(f"{'':<22}{'raw%   ARI':>18}{'raw%   ARI':>16}{'raw%   ARI':>14}")
    rows = []
    for w1, w2 in combinations(WINDOWS, 2):
        a, b = labs[w1], labs[w2]
        cells = []
        for transform in (lambda x: x, calm_stressed_A, calm_stressed_B):
            ta, tb = transform(a), transform(b)
            raw = float((ta == tb).mean())
            ari = float(adjusted_rand_score(ta, tb))
            cells.append((raw, ari))
        (r3, a3), (rA, aA), (rB, aB) = cells
        print(f"{w1+'~'+w2:<22}{r3*100:>7.1f}{a3:>8.3f}  {rA*100:>7.1f}{aA:>6.3f}  {rB*100:>6.1f}{aB:>6.3f}")
        rows.append({"pair": f"{w1}~{w2}", "raw3": r3, "ari3": a3,
                     "raw_LvMH": rA, "ari_LvMH": aA, "raw_LMvH": rB, "ari_LMvH": aB})

    print(f"\n{'='*70}\n(c) Disagreement locality (of days where the pair disagrees)\n{'='*70}")
    for w1, w2 in combinations(WINDOWS, 2):
        a, b = labs[w1], labs[w2]
        dis = a != b
        gap = np.abs(a[dis] - b[dis])
        n = int(dis.sum())
        adj = int((gap == 1).sum())
        ext = int((gap == 2).sum())
        print(f"  {w1}~{w2}: {n} disagreements  |  adjacent(Low<->Mod / Mod<->High)={adj} "
              f"({adj/n*100:.0f}%)  extreme(Low<->High)={ext} ({ext/n*100:.0f}%)")

    # how much 3-regime disagreement vanishes under the calm/stressed collapse
    print(f"\n{'='*70}\n(c') Fraction of 3-regime disagreements that SURVIVE binarization\n{'='*70}")
    for w1, w2 in combinations(WINDOWS, 2):
        a, b = labs[w1], labs[w2]
        dis3 = a != b
        for label, transform in (("Low|Mod-High", calm_stressed_A), ("Low-Mod|High", calm_stressed_B)):
            ta, tb = transform(a), transform(b)
            survive = int(((ta != tb) & dis3).sum())
            print(f"  {w1}~{w2} [{label}]: {survive}/{int(dis3.sum())} disagreements survive "
                  f"({survive/max(dis3.sum(),1)*100:.0f}%)")

    pd.DataFrame(rows).to_csv(os.path.join(RESULTS_DIR, "stability_decomposition.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'stability_decomposition.csv')}")


if __name__ == "__main__":
    main()
