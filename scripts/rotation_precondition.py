"""Cross-sectional rotation PRECONDITION screen (descriptive, look-free, hypothesis-
generating — NOT a backtest, spends no chapter look).

The Path-B candidate (cross-sectional defensive rotation, PROGRAM.md) only has anything
to work with if per-asset regimes DIVERGE. If every asset flips to bear at the same time,
there is nowhere to rotate TO and the idea is dead before any prereg.

This fits a SEPARATE K=2 jump-model label on EACH asset's OWN return series (unlike
atlas.py, which conditions every asset on the single market label), then asks:

  1. How often are all test assets in the same state (no cross-section)?
  2. Distribution of cross-sectional bear-breadth (fraction of assets in bear per day).
  3. THE MONEY QUESTION — conditional refuge: when equity is in bear, how often is a
     bond / gold / any non-equity asset in BULL (somewhere to rotate to)?
  4. Pairwise bear-state agreement (phi) between asset classes — low/negative = divergent.
  5. Within-equity (10 industries) agreement — expected high; tells us rotation must be
     ACROSS asset classes, not sector rotation.

Descriptive full-sample fit (like atlas.py / state_anatomy.py): fine for a precondition
screen. A real test would be causal walk-forward with the matched-blend bar (PROGRAM.md).

Writes results/rotation_precondition.csv + prints the verdict.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from jumpmodel import build_features, fit_jump_model  # noqa: E402

# genuinely distinct asset CLASSES (the cross-asset test) + within-equity cross-section
CROSS_ASSET = ["mkt_ret", "bond10_ret", "gold_ret"]
INDUSTRIES = ["ind_nodur", "ind_durbl", "ind_manuf", "ind_enrgy", "ind_hitec",
              "ind_telcm", "ind_shops", "ind_hlth", "ind_utils", "ind_other"]
LAM = 50.0          # on STANDARDIZED features (grid is [10..800]); ~1/yr switching, standard
BURN = 252          # drop feature warm-up


def label_asset(r):
    """K=2 JM label on one return series, matching the pipeline's feature prep:
    z-standardized features (lam is calibrated to standardized units). 1 = bear."""
    r = r.dropna()
    feats = build_features(r)
    feats.index = r.index                 # build_features drops the index; reattach positionally
    feats = feats.iloc[BURN:].dropna()
    F = feats.to_numpy()
    Z = (F - F.mean(axis=0)) / F.std(axis=0)   # standardize (as walkforward._zapply does)
    _, states, _, _ = fit_jump_model(Z, k=2, lam=LAM, seed=0)
    return pd.Series(states, index=feats.index)


def phi(a, b):
    """Phi coefficient (Pearson corr of two 0/1 indicators)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def main():
    panel = pd.read_csv(ROOT / "data" / "processed" / "assets_daily.csv",
                        index_col=0, parse_dates=True)
    # common window where the distinct asset CLASSES all exist (gold starts 2000);
    # fit every asset on the SAME window so calm/stress splits are apples-to-apples
    win = panel[CROSS_ASSET].dropna().index
    panel = panel.loc[win[0]:win[-1]]

    labels = {}
    rows = []
    for col in CROSS_ASSET + INDUSTRIES:
        if col not in panel.columns:
            continue
        lab = label_asset(panel[col])
        labels[col] = lab
        bear_frac = float(lab.mean())
        switches = int((lab.diff().abs() == 1).sum())
        rows.append(dict(asset=col, days=len(lab), start=lab.index[0].date(),
                         bear_frac=round(bear_frac, 3),
                         switches_per_yr=round(switches / (len(lab) / 252), 2)))
    meta = pd.DataFrame(rows)

    # ---- cross-asset test: align equity/bond/gold on their common dates ----
    L = pd.DataFrame({c: labels[c] for c in CROSS_ASSET}).dropna()
    n = len(L)
    print(f"cross-asset panel: {L.index[0].date()}..{L.index[-1].date()}  ({n} common days)\n")
    print("per-asset bear frequency & switch rate:")
    print(meta.to_string(index=False))

    eq, bond, gold = L["mkt_ret"], L["bond10_ret"], L["gold_ret"]

    # (1) all-same-state fraction
    breadth = L.mean(axis=1)                      # fraction of the 3 in bear, per day
    all_same = float(((breadth == 0) | (breadth == 1)).mean())
    all_bear = float((breadth == 1).mean())
    mixed = float(((breadth > 0) & (breadth < 1)).mean())

    # (3) THE MONEY QUESTION — refuge when equity is bear.
    #     Raw refuge = P(asset in bull | equity bear). LIFT = that / P(asset in bull)
    #     unconditionally — base-rate-fair: >1 means equity-stress makes the refuge MORE
    #     likely than usual (genuine conditional flight-to-safety), ~1 means coincidence.
    eq_bear = eq == 1
    n_eqbear = int(eq_bear.sum())
    base_bond, base_gold = float((bond == 0).mean()), float((gold == 0).mean())
    refuge_bond = float((bond[eq_bear] == 0).mean())
    refuge_gold = float((gold[eq_bear] == 0).mean())
    refuge_any = float(((bond[eq_bear] == 0) | (gold[eq_bear] == 0)).mean())
    lift_bond = refuge_bond / base_bond if base_bond else np.nan
    lift_gold = refuge_gold / base_gold if base_gold else np.nan

    # (4) pairwise bear-state agreement (phi) between classes
    phi_eb = phi(eq, bond)
    phi_eg = phi(eq, gold)
    phi_bg = phi(bond, gold)

    print("\n" + "=" * 68)
    print("CROSS-ASSET DIVERGENCE (equity / bond / gold, own-label each)")
    print("=" * 68)
    print(f"  days all three in SAME state        : {all_same:5.1%}")
    print(f"    of which all-bear simultaneously   : {all_bear:5.1%}")
    print(f"  days MIXED (a cross-section exists)  : {mixed:5.1%}")
    print(f"\n  equity-bear days                     : {n_eqbear} ({n_eqbear/n:.1%} of sample)")
    print(f"  bond bull base rate {base_bond:4.1%} | gold bull base rate {base_gold:4.1%}")
    print(f"  REFUGE | equity bear -> bond in bull : {refuge_bond:5.1%}  (lift {lift_bond:.2f}x)")
    print(f"  REFUGE | equity bear -> gold in bull : {refuge_gold:5.1%}  (lift {lift_gold:.2f}x)")
    print(f"  REFUGE | equity bear -> ANY of the 2 : {refuge_any:5.1%}   <-- somewhere to rotate")
    print(f"\n  bear-state phi  equity~bond          : {phi_eb:+.3f}")
    print(f"  bear-state phi  equity~gold          : {phi_eg:+.3f}")
    print(f"  bear-state phi  bond~gold            : {phi_bg:+.3f}")
    print("  (phi near 0 or negative = divergent = good for rotation)")

    # (5) within-equity synchronization (10 industries)
    IND = pd.DataFrame({c: labels[c] for c in INDUSTRIES if c in labels}).dropna()
    ind_breadth = IND.mean(axis=1)
    ind_same = float(((ind_breadth == 0) | (ind_breadth == 1)).mean())
    # mean pairwise phi across industries
    cols = list(IND.columns)
    phis = [phi(IND[a], IND[b]) for i, a in enumerate(cols) for b in cols[i + 1:]]
    print("\n" + "-" * 68)
    print("WITHIN-EQUITY (10 industries) — is sector rotation an alternative?")
    print("-" * 68)
    print(f"  days all 10 industries same state    : {ind_same:5.1%}")
    print(f"  mean pairwise bear-state phi         : {np.nanmean(phis):+.3f}")
    print("  (high phi = industries move together = sector rotation has little to work with)")

    # verdict
    print("\n" + "=" * 68)
    strong = refuge_any >= 0.40 and phi_eb <= 0.2
    weak = refuge_any >= 0.25
    if strong:
        v = "GREEN — real cross-asset refuge exists; rotation has something to work with."
    elif weak:
        v = "AMBER — some refuge, but equity/bond co-move more than hoped; marginal."
    else:
        v = "RED — assets flip together; nowhere to rotate. Candidate likely dead."
    print("VERDICT:", v)
    print("=" * 68)

    meta.to_csv(ROOT / "results" / "rotation_precondition.csv", index=False)
    summary = pd.DataFrame([dict(
        common_days=n, all_same=all_same, all_bear=all_bear, mixed=mixed,
        eq_bear_days=n_eqbear, refuge_bond=refuge_bond, refuge_gold=refuge_gold,
        refuge_any=refuge_any, phi_eq_bond=phi_eb, phi_eq_gold=phi_eg,
        phi_bond_gold=phi_bg, within_eq_same=ind_same,
        within_eq_mean_phi=float(np.nanmean(phis)))])
    summary.to_csv(ROOT / "results" / "rotation_precondition_summary.csv", index=False)
    print("\nwrote results/rotation_precondition.csv + _summary.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
