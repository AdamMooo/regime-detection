"""Out-of-hypothesis-sample confirmation of the US dispersion lag finding
(`explore_dispersion_feature.py`, 2026-07-28: LT20 median lag 56d -> 16d, -40d, on the
US panel — CONTAMINATED, hypothesis-generating only per CLAUDE.md's out-of-hypothesis-sample
rule). Same methodology, same estimator constants (run_config), applied byte-identically to
Japan and Europe daily panels (French International library, 1990-07-02+, built by
build_intl_panel.py) so a positive result here is a genuine confirmation, not a re-ask.

  BASE  = build_features(mkt_ret)                 -> dd10, sortino20, sortino60
  +DISP = BASE augmented with realized cross-sectional dispersion of the region's 25
          size/BE-ME portfolios (same definition as build_dispersion.py's csd_ew10)

No look, no economic claim spent — this is the descriptive confirmation gate itself, exactly
what the out-of-hypothesis-sample rule requires before any SUPPORT claim about the US finding.

--smoke: short slice + small grid, code-path check only.
Writes results/explore_dispersion_intl_{region}.csv per region.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_dispersion import cross_sectional_dispersion, ew_smooth
from jumpmodel import build_features
from run_config import DELAY, LAMBDA_GRID, N_INIT, REFIT, VAL
from validate_sensor import lunde_timmermann
from walkforward import walk_forward

ANN = 252
BURN = 63
TRAIN0_INTL = 5040  # ~20y burn-in, same as the US harness; panel starts 1990-07-02 -> OOS ~2010+


def load_region(region):
    rl = region.lower()
    market = pd.read_csv(ROOT / "data" / "processed" / f"{rl}_market_daily.csv",
                         index_col=0, parse_dates=True)
    ports = pd.read_csv(ROOT / "data" / "processed" / f"{rl}_assets_daily.csv",
                        index_col=0, parse_dates=True)
    df = market.join(ports, how="inner").dropna()
    return df


def build_dispersion_intl(df):
    ports = df[[c for c in df.columns if c.startswith("p")]]
    csd = cross_sectional_dispersion(ports)
    return ew_smooth(csd, 10).to_numpy()


def run_pass(r, F, train0, grid, n_init, val):
    return walk_forward(r, F, burn=BURN, train0=train0, refit=REFIT, grid=grid,
                        val=val, n_init=n_init, delay=DELAY, k=2)


def _episode_lags(idx, ours, truth):
    lt_o = pd.Series(truth, index=idx)
    s_o = pd.Series(ours, index=idx)
    episodes, in_b, prev_d, start = [], False, None, None
    for d, v in lt_o.items():
        if v == 1 and not in_b:
            in_b, start = True, d
        elif v == 0 and in_b:
            in_b = False
            episodes.append((start, prev_d))
        prev_d = d
    if in_b:
        episodes.append((start, prev_d))
    lags, covs = [], []
    for a, b in episodes:
        seg = s_o.loc[a:b]
        covs.append(float((seg == 1).mean()))
        flagged = seg[seg == 1]
        if len(flagged):
            lags.append((flagged.index[0] - a).days)
    return dict(n_ep=len(episodes),
               detected=int(sum(1 for c in covs if c > 0)),
               median_lag=float(np.median(lags)) if lags else float("nan"),
               mean_cov=float(np.mean(covs)) if covs else float("nan"))


def score(states, r, index):
    px = (1.0 + pd.Series(r, index=index)).cumprod()
    oos = states >= 0
    s_full = pd.Series(states, index=index)
    idx_o = index[oos]
    ours = s_full[oos].to_numpy()
    out = {}
    for thr in (0.20, 0.15):
        phase, _ = lunde_timmermann(px.to_numpy(), thr)
        truth = pd.Series(phase, index=index)[oos].to_numpy()
        tp = int(((ours == 1) & (truth == 1)).sum())
        prec = tp / max(int((ours == 1).sum()), 1)
        rec = tp / max(int((truth == 1).sum()), 1)
        st = _episode_lags(idx_o, ours, truth)
        out[f"lt{int(thr * 100)}"] = dict(precision=round(prec, 3), recall=round(rec, 3), **st)
    s_o = states[oos]
    out["switches_yr"] = float((s_o[1:] != s_o[:-1]).sum() / len(s_o) * ANN)
    out["n_oos"] = int(oos.sum())
    return out


def stability(r, F, train0, base_states, grid, n_init, val):
    res, worst = {}, 1.0
    for shift, nm in ((504, "start+2y"), (-504, "start-2y")):
        s_sh, _ = run_pass(r, F, train0 + shift, grid, n_init, val)
        m = (base_states >= 0) & (s_sh >= 0)
        agree = float((base_states[m] == s_sh[m]).mean())
        res[nm] = round(agree, 4)
        worst = min(worst, agree)
    res["worst"] = round(worst, 4)
    return res


def _fmt(tag, sc, stab):
    l20, l15 = sc["lt20"], sc["lt15"]
    return (f"{tag:10} | LT20 lag {l20['median_lag']:>5.0f}d cov {l20['mean_cov']:.2f} "
            f"det {l20['detected']}/{l20['n_ep']} prec {l20['precision']:.2f} rec {l20['recall']:.2f}"
            f" | LT15 lag {l15['median_lag']:>5.0f}d det {l15['detected']}/{l15['n_ep']}"
            f" | switches/yr {sc['switches_yr']:.2f} | stability {stab['worst']:.3f}")


def run_region(region, smoke):
    df = load_region(region)
    train0, grid, n_init, val = TRAIN0_INTL, LAMBDA_GRID, N_INIT, VAL
    if smoke:
        df = df.iloc[-6000:]
        train0, grid, n_init, val = 3024, [50.0, 200.0], 3, 1008
        print(f"[{region}] SMOKE MODE: short slice, small grid.", flush=True)

    index = df.index
    r = df["mkt_ret"].to_numpy()
    F3 = build_features(r).to_numpy()
    disp = build_dispersion_intl(df)
    F4 = np.column_stack([F3, disp])
    t0 = time.time()
    print(f"\n=== {region} === panel {index[0].date()}..{index[-1].date()} n={len(r)}", flush=True)

    print(f"[{region} 1/4] BASE pass...", flush=True)
    base_states, base_lam = run_pass(r, F3, train0, grid, n_init, val)
    print(f"      done ({(time.time() - t0) / 60:.1f} min).", flush=True)

    print(f"[{region} 2/4] +DISP pass...", flush=True)
    disp_states, disp_lam = run_pass(r, F4, train0, grid, n_init, val)
    print(f"      done ({(time.time() - t0) / 60:.1f} min).", flush=True)

    base_sc = score(base_states, r, index)
    disp_sc = score(disp_states, r, index)
    m = (base_states >= 0) & (disp_states >= 0)
    base_vs_disp = float((base_states[m] == disp_states[m]).mean())

    print(f"[{region} 3/4] stability (±2y train-start shifts)...", flush=True)
    base_stab = stability(r, F3, train0, base_states, grid, n_init, val)
    disp_stab = stability(r, F4, train0, disp_states, grid, n_init, val)

    print("=" * 96)
    print(f"{region} — DISPERSION-FEATURE LAG PROBE (out-of-hypothesis-sample confirmation)")
    print("=" * 96)
    print(_fmt("BASE", base_sc, base_stab))
    print(_fmt("+DISP", disp_sc, disp_stab))
    print(f"BASE vs +DISP label agreement: {base_vs_disp:.4f} on {int(m.sum())} joint OOS days")
    dl20 = disp_sc["lt20"]["median_lag"] - base_sc["lt20"]["median_lag"]
    print(f"LT20 median-lag change (+DISP - BASE): {dl20:+.0f} days "
          f"(negative = dispersion detects bears EARLIER; US finding was -40d)")

    rows = []
    for tag, sc, stab, lam in (("base", base_sc, base_stab, base_lam),
                               ("disp", disp_sc, disp_stab, disp_lam)):
        for var in ("lt20", "lt15"):
            rows.append(dict(arm=tag, section=var, **sc[var]))
        rows.append(dict(arm=tag, section="meta", switches_yr=sc["switches_yr"],
                         n_oos=sc["n_oos"], stab_p2y=stab["start+2y"],
                         stab_m2y=stab["start-2y"], stab_worst=stab["worst"],
                         final_lambda=float(lam[-1])))
    rows.append(dict(arm="cmp", section="agreement", base_vs_disp=round(base_vs_disp, 4)))
    if not smoke:
        pd.DataFrame(rows).to_csv(ROOT / "results" / f"explore_dispersion_intl_{region.lower()}.csv",
                                  index=False)
        print(f"wrote results/explore_dispersion_intl_{region.lower()}.csv "
              f"({(time.time() - t0) / 60:.1f} min)", flush=True)
    else:
        print(f"[{region}] SMOKE OK ({(time.time() - t0) / 60:.1f} min) — nothing written", flush=True)
    return dl20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--region", choices=["japan", "europe", "both"], default="both")
    args = ap.parse_args()
    regions = ["Japan", "Europe"] if args.region == "both" else [args.region.capitalize()]

    deltas = {}
    for region in regions:
        deltas[region] = run_region(region, args.smoke)

    print("\n" + "=" * 96)
    print("SUMMARY — LT20 median-lag change (+DISP - BASE) per panel")
    print("=" * 96)
    print(f"US (2026-07-28, prior run):  -40d  (56d -> 16d)")
    for region, dl in deltas.items():
        print(f"{region:10}: {dl:+.0f}d")
    print("\nREAD: confirms if BOTH international panels also show a lag REDUCTION (negative)")
    print("of comparable direction to the US finding. A null/positive-lag result on either panel")
    print("means the US finding does not generalize and stays a US-only curiosity, not a SUPPORT claim.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
