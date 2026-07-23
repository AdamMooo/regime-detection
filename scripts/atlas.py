"""The state-conditional atlas (descriptive, in-sample on causally-labeled OOS days —
informs but never gates the allocation prereg).

For every asset / industry / factor in assets_daily.csv, conditional on the frozen
chapter-1 labels (results/oos_labels.csv): annualized return, vol, Sharpe, and correlation
with the market, per state — plus the stressed-vs-calm deltas that would drive rotation:
  vol_ratio   = ann_vol_stressed / ann_vol_calm      (defensiveness: lower = safer in stress)
  ret_delta   = ann_ret_stressed - ann_ret_calm      (conditional premium shift)
  corr_shift  = corr_mkt_stressed - corr_mkt_calm    (diversification failure/holding)

Confidence meter: leave-one-episode-out (LOEO) over the stressed episodes — for each
episode dropped, recompute the deltas; report the fraction of drops in which the sign of
each delta is unchanged (30/30 = bulletproof, 16/30 = a story).

Writes results/atlas.csv; prints ranked summary.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

ASSETS = ["mkt_ret", "bond10_ret", "gold_ret", "smb", "hml", "mom",
          "ind_nodur", "ind_durbl", "ind_manuf", "ind_enrgy", "ind_hitec",
          "ind_telcm", "ind_shops", "ind_hlth", "ind_utils", "ind_other"]


def episodes_of(s):
    eps, in_e = [], False
    for i, v in enumerate(s):
        if v == 1 and not in_e:
            in_e, a = True, i
        elif v != 1 and in_e:
            in_e = False
            eps.append((a, i - 1))
    if in_e:
        eps.append((a, len(s) - 1))
    return eps


def stats(r, mkt):
    ann = float(r.mean() * 252)
    vol = float(r.std() * np.sqrt(252))
    return ann, vol, float(r.corr(mkt))


def main():
    panel = pd.read_csv(ROOT / "data" / "processed" / "assets_daily.csv",
                        index_col=0, parse_dates=True)
    labels = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"])
    df = panel.loc[panel.index.isin(labels["date"])].copy()
    s = labels.set_index("date").loc[df.index, "state"].to_numpy()
    eps = episodes_of(s)
    print(f"atlas over {df.index[0].date()}..{df.index[-1].date()}  "
          f"({len(df)} OOS days, {len(eps)} stressed episodes)\n")

    rows = []
    for col in ASSETS:
        r = df[col].dropna()
        if len(r) < 2000:
            continue
        sr = s[df.index.isin(r.index)] if len(r) != len(df) else s
        m = df["mkt_ret"].loc[r.index]
        calm, stre = r[sr == 0], r[sr == 1]
        a0, v0, c0 = stats(calm, m[sr == 0])
        a1, v1, c1 = stats(stre, m[sr == 1])
        vol_ratio = v1 / v0
        ret_delta = a1 - a0
        corr_shift = c1 - c0
        # LOEO sign stability of each delta (recompute stressed stats w/o each episode)
        r_np, m_np = r.to_numpy(), m.to_numpy()
        stre_idx = np.flatnonzero(sr == 1)
        signs_vr, signs_rd, signs_cs = [], [], []
        local_eps = episodes_of(sr)
        for a, b in local_eps:
            keep = stre_idx[(stre_idx < a) | (stre_idx > b)]
            if len(keep) < 200:
                continue
            rs = r_np[keep]
            ms = m_np[keep]
            v1_ = rs.std() * np.sqrt(252)
            a1_ = rs.mean() * 252
            c1_ = np.corrcoef(rs, ms)[0, 1]
            signs_vr.append((v1_ / v0 > 1) == (vol_ratio > 1))
            signs_rd.append(((a1_ - a0) > 0) == (ret_delta > 0))
            signs_cs.append(((c1_ - c0) > 0) == (corr_shift > 0))
        n_ep = len(signs_vr)
        rows.append(dict(
            asset=col, days=len(r),
            calm_ret=round(a0, 4), calm_vol=round(v0, 4), calm_corr=round(c0, 3),
            stress_ret=round(a1, 4), stress_vol=round(v1, 4), stress_corr=round(c1, 3),
            vol_ratio=round(vol_ratio, 3), ret_delta=round(ret_delta, 4),
            corr_shift=round(corr_shift, 3),
            loeo_n=n_ep,
            loeo_vol=round(np.mean(signs_vr), 3) if n_ep else np.nan,
            loeo_ret=round(np.mean(signs_rd), 3) if n_ep else np.nan,
            loeo_corr=round(np.mean(signs_cs), 3) if n_ep else np.nan))

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results" / "atlas.csv", index=False)

    mkt_vr = out.loc[out["asset"] == "mkt_ret", "vol_ratio"].iloc[0]
    print(f"market vol ratio (stressed/calm): {mkt_vr:.2f}\n")
    print("DEFENSIVENESS (vol_ratio vs market's, LOEO = sign stability across episode drops)")
    d = out.sort_values("vol_ratio")
    for _, x in d.iterrows():
        tag = "DEFENSIVE" if x.vol_ratio < mkt_vr - 0.15 else (
            "amplifier" if x.vol_ratio > mkt_vr + 0.15 else "")
        print(f"  {x.asset:12} vol {x.calm_vol:6.1%}->{x.stress_vol:6.1%} "
              f"ratio {x.vol_ratio:5.2f}  ret {x.calm_ret:+7.1%}->{x.stress_ret:+7.1%} "
              f"corr {x.calm_corr:+5.2f}->{x.stress_corr:+5.2f}  "
              f"LOEO v/r/c {x.loeo_vol:.2f}/{x.loeo_ret:.2f}/{x.loeo_corr:.2f}  {tag}")
    print("\nwrote results/atlas.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
