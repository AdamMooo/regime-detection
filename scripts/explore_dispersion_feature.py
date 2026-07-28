"""Instrument-exploration probe: does adding realized cross-sectional dispersion as a 4th
jump-model feature REDUCE bear-detection lag without sacrificing the K=2 label's 1.000 stability?

NO economic claim, NO look spent (cf. explore_k3.py, build_dispersion.py). The feature and its
lead-lag motivation were peeked at on the US panel (build_dispersion.characterize), so a positive
result here is HYPOTHESIS-STRENGTHENING ON CONTAMINATED DATA, not SUPPORT: any "dispersion improves
the instrument" claim binds the out-of-hypothesis-sample rule (international French/MSCI
confirmation) before it can be made (CLAUDE.md discipline).

Apples-to-apples through the frozen chapter-1 harness (same START/TRAIN0/REFIT/grid/VAL/DELAY):
  BASE  = build_features                 -> dd10, sortino20, sortino60   (reproduces the instrument)
  +DISP = BASE augmented with dispersion -> + csd_ew{HL}                 (the lag-attack candidate)

walk_forward z-scores every feature and the weighted fit down-weights uninformative ones, so the
4th column is low-risk: if dispersion carries nothing the label is ~unchanged.

Per label: LT (Lunde-Timmermann 20/15%) per-episode median detection lag from the ex-post peak,
episode coverage, precision/recall; ±2y train-start stability agreement; switches/yr; label
agreement vs BASE and vs the frozen file. Writes results/explore_dispersion_feature.csv.

--smoke: short slice + small grid, code-path check only.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jumpmodel import build_features
from run_config import DELAY, LAMBDA_GRID, N_INIT, REFIT, START, TRAIN0, VAL
from validate_sensor import lunde_timmermann
from walkforward import walk_forward

ANN = 252
BURN = 63


def load_dispersion(index, col):
    disp = pd.read_csv(ROOT / "data" / "processed" / "dispersion_daily.csv",
                       index_col=0, parse_dates=True)
    if col not in disp.columns:
        raise SystemExit(f"dispersion column {col!r} not in {list(disp.columns)}")
    s = disp[col].reindex(index)
    if s.isna().any():
        # panel dates missing from dispersion: forward-fill within series, then bfill the
        # (pre-1970 warm-up is complete, so any gaps are trading-calendar mismatches, not burn-in)
        s = s.ffill().bfill()
    return s.to_numpy()


def run_pass(r, F, train0, grid, n_init, val):
    states, lam_hist = walk_forward(r, F, burn=BURN, train0=train0, refit=REFIT, grid=grid,
                                    val=val, n_init=n_init, delay=DELAY, k=2)
    return states, lam_hist


def _episode_lags(idx, ours, truth):
    """Per ex-post LT bear episode: coverage + detection lag (days from the ex-post peak to the
    first stressed-labeled day). Mirrors validate_sensor.main's episode loop."""
    lt_o = pd.Series(truth, index=idx)
    s_o = pd.Series(ours, index=idx)
    episodes, in_b, prev_d = [], False, None
    start = None
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
    """LT precision/recall + per-episode lag at 20% and 15% dating; switches/yr."""
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
    """±2y train-start shift agreement vs the base pass on joint OOS days (K=2 bar = 1.000)."""
    res = {}
    worst = 1.0
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--disp-col", default="csd_ew10",
                    help="dispersion column to add as the 4th feature (default csd_ew10)")
    args = ap.parse_args()

    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True).loc[START:]
    train0, grid, n_init, val = TRAIN0, LAMBDA_GRID, N_INIT, VAL
    if args.smoke:
        panel = panel.iloc[-6000:]
        train0, grid, n_init, val = 3024, [50.0, 200.0], 3, 1008
        print("SMOKE MODE: short slice, small grid — code-path check only.", flush=True)

    index = panel.index
    r = panel["mkt_ret"].to_numpy()
    F3 = build_features(r).to_numpy()
    disp = load_dispersion(index, args.disp_col)
    F4 = np.column_stack([F3, disp])
    t0 = time.time()
    print(f"panel {index[0].date()}..{index[-1].date()} n={len(r)} | 4th feature = {args.disp_col}",
          flush=True)

    print("[1/4] BASE pass (dd10, sortino20, sortino60)...", flush=True)
    base_states, base_lam = run_pass(r, F3, train0, grid, n_init, val)
    print(f"      done ({(time.time() - t0) / 60:.1f} min). lam_path={base_lam}", flush=True)

    print("[2/4] +DISP pass (BASE + dispersion)...", flush=True)
    disp_states, disp_lam = run_pass(r, F4, train0, grid, n_init, val)
    print(f"      done ({(time.time() - t0) / 60:.1f} min). lam_path={disp_lam}", flush=True)

    base_sc = score(base_states, r, index)
    disp_sc = score(disp_states, r, index)

    m = (base_states >= 0) & (disp_states >= 0)
    base_vs_disp = float((base_states[m] == disp_states[m]).mean())

    # harness sanity: BASE should reproduce the frozen chapter-1 label
    frozen_agree = float("nan")
    fp = ROOT / "results" / "oos_labels.csv"
    if fp.exists():
        frozen = pd.read_csv(fp, parse_dates=["date"]).set_index("date")["state"]
        oos = base_states >= 0
        bl = pd.Series(base_states[oos], index=index[oos])
        j = bl.to_frame("base").join(frozen.rename("frozen"), how="inner").dropna()
        if len(j):
            frozen_agree = float((j["base"] == j["frozen"]).mean())

    print("[3/4] stability (±2y train-start shifts)...", flush=True)
    base_stab = stability(r, F3, train0, base_states, grid, n_init, val)
    disp_stab = stability(r, F4, train0, disp_states, grid, n_init, val)

    print("\n" + "=" * 96)
    print("DISPERSION-FEATURE LAG PROBE — does a 4th dispersion feature cut detection lag?")
    print("=" * 96)
    print(_fmt("BASE", base_sc, base_stab))
    print(_fmt("+DISP", disp_sc, disp_stab))
    print(f"\nBASE vs +DISP label agreement: {base_vs_disp:.4f} on {int(m.sum())} joint OOS days")
    print(f"BASE vs FROZEN label agreement: {frozen_agree:.4f} (harness sanity; want ~1.000)")
    dl20 = disp_sc["lt20"]["median_lag"] - base_sc["lt20"]["median_lag"]
    print(f"\nLT20 median-lag change (+DISP - BASE): {dl20:+.0f} days   "
          f"(negative = dispersion detects bears EARLIER)")
    print("READ: a lag drop with stability still ~1.000 and switches/yr not blown up = a real")
    print("      lead candidate. CONTAMINATED (US panel) — needs international confirmation before")
    print("      any SUPPORT claim. No economic claim, no look spent.")

    rows = []
    for tag, sc, stab, lam in (("base", base_sc, base_stab, base_lam),
                               ("disp", disp_sc, disp_stab, disp_lam)):
        for var in ("lt20", "lt15"):
            rows.append(dict(arm=tag, section=var, **sc[var]))
        rows.append(dict(arm=tag, section="meta", switches_yr=sc["switches_yr"],
                         n_oos=sc["n_oos"], stab_p2y=stab["start+2y"],
                         stab_m2y=stab["start-2y"], stab_worst=stab["worst"],
                         final_lambda=float(lam[-1])))
    rows.append(dict(arm="cmp", section="agreement", base_vs_disp=round(base_vs_disp, 4),
                     base_vs_frozen=round(frozen_agree, 4), disp_col=args.disp_col))
    if not args.smoke:
        pd.DataFrame(rows).to_csv(ROOT / "results" / "explore_dispersion_feature.csv", index=False)
        print(f"\nwrote results/explore_dispersion_feature.csv "
              f"(total {(time.time() - t0) / 60:.1f} min)", flush=True)
    else:
        print(f"\nSMOKE OK ({(time.time() - t0) / 60:.1f} min) — nothing written", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
