"""Instrument-exploration probe: does adding Moody's Baa-Aaa credit spread as a 4th jump-model
feature REDUCE bear-detection lag without sacrificing the K=2 label's stability? MODERN-ERA
(1986+) head-to-head — credit's daily history starts 1986, so this is a new modern instrument,
not an extension of the frozen 1926+/1970+ label.

Credit cleared the info-gate better than any prior candidate: corr(credit_ew20, own-vol)=0.559
(credit_gate.csv) vs dispersion 0.783 vs killed breadth 0.99 — the most distinct axis tried.

NO economic claim, NO look spent (cf. explore_dispersion_feature.py, explore_k3.py). A lag drop
here is US-panel-contaminated hypothesis-strengthening, NOT SUPPORT — it binds the
out-of-hypothesis-sample rule (international confirmation) before any claim.

BASE  = build_features on the 1986+ panel   (dd10, sortino20, sortino60)
+CRED = BASE + credit_ew10

Frozen protocol constants unchanged (TRAIN0=5040, REFIT, LAMBDA_GRID, VAL, DELAY, k=2); only the
panel start moves to 1986 (credit's start), so OOS scoring runs ~2006+ and spans 2008 / 2011 /
2015-16 / 2018 / 2020 / 2022 — the two most credit-led episodes (GFC, 2015-16 energy) are the
best-case test for a credit lead. Reuses the dispersion probe's scoring/stability machinery.

Writes results/explore_credit_feature.csv. --smoke for a code-path check.
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
from run_config import LAMBDA_GRID, N_INIT, TRAIN0, VAL
from explore_dispersion_feature import run_pass, score, stability, _fmt

START_CREDIT = "1986-01-02"


def load_credit(index, col):
    c = pd.read_csv(ROOT / "data" / "processed" / "credit_daily.csv",
                    index_col=0, parse_dates=True)
    if col not in c.columns:
        raise SystemExit(f"credit column {col!r} not in {list(c.columns)}")
    s = c[col].reindex(index)
    if s.isna().any():
        s = s.ffill().bfill()  # calendar-mismatch fill only; 1986+ start is fully warmed
    return s.to_numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--credit-col", default="credit_ew10",
                    help="credit column to add as the 4th feature (default credit_ew10)")
    args = ap.parse_args()

    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True).loc[START_CREDIT:]
    train0, grid, n_init, val = TRAIN0, LAMBDA_GRID, N_INIT, VAL
    if args.smoke:
        panel = panel.iloc[-5000:]
        train0, grid, n_init, val = 3024, [50.0, 200.0], 3, 1008
        print("SMOKE MODE: short slice, small grid — code-path check only.", flush=True)

    index = panel.index
    r = panel["mkt_ret"].to_numpy()
    F3 = build_features(r).to_numpy()
    cred = load_credit(index, args.credit_col)
    F4 = np.column_stack([F3, cred])
    t0 = time.time()
    print(f"panel {index[0].date()}..{index[-1].date()} n={len(r)} | 4th feature = {args.credit_col}",
          flush=True)

    print("[1/4] BASE pass (dd10, sortino20, sortino60)...", flush=True)
    base_states, base_lam = run_pass(r, F3, train0, grid, n_init, val)
    print(f"      done ({(time.time() - t0) / 60:.1f} min). lam_path={base_lam}", flush=True)

    print("[2/4] +CRED pass (BASE + credit)...", flush=True)
    cred_states, cred_lam = run_pass(r, F4, train0, grid, n_init, val)
    print(f"      done ({(time.time() - t0) / 60:.1f} min). lam_path={cred_lam}", flush=True)

    base_sc, cred_sc = score(base_states, r, index), score(cred_states, r, index)
    m = (base_states >= 0) & (cred_states >= 0)
    base_vs_cred = float((base_states[m] == cred_states[m]).mean())

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
    cred_stab = stability(r, F4, train0, cred_states, grid, n_init, val)

    print("\n" + "=" * 96)
    print("CREDIT-FEATURE LAG PROBE (Baa-Aaa, 1986+) — does a 4th credit feature cut detection lag?")
    print("=" * 96)
    print(_fmt("BASE", base_sc, base_stab))
    print(_fmt("+CRED", cred_sc, cred_stab))
    print(f"\nBASE vs +CRED label agreement: {base_vs_cred:.4f} on {int(m.sum())} joint OOS days")
    print(f"BASE(1986) vs FROZEN(1970) agreement on overlap: {frozen_agree:.4f} "
          f"(sanity; expect high, not 1.000 — different train start)")
    dl20 = cred_sc["lt20"]["median_lag"] - base_sc["lt20"]["median_lag"]
    print(f"\nLT20 median-lag change (+CRED - BASE): {dl20:+.0f} days   "
          f"(negative = credit detects bears EARLIER)")
    print("READ: lag drop + stability ~unchanged + switches/yr not blown up = a real lead.")
    print("      CONTAMINATED (US panel) — needs international confirmation before any SUPPORT.")

    rows = []
    for tag, sc, stab, lam in (("base", base_sc, base_stab, base_lam),
                               ("cred", cred_sc, cred_stab, cred_lam)):
        for var in ("lt20", "lt15"):
            rows.append(dict(arm=tag, section=var, **sc[var]))
        rows.append(dict(arm=tag, section="meta", switches_yr=sc["switches_yr"],
                         n_oos=sc["n_oos"], stab_p2y=stab["start+2y"],
                         stab_m2y=stab["start-2y"], stab_worst=stab["worst"],
                         final_lambda=float(lam[-1])))
    rows.append(dict(arm="cmp", section="agreement", base_vs_cred=round(base_vs_cred, 4),
                     base_vs_frozen=round(frozen_agree, 4), credit_col=args.credit_col))
    if not args.smoke:
        pd.DataFrame(rows).to_csv(ROOT / "results" / "explore_credit_feature.csv", index=False)
        print(f"\nwrote results/explore_credit_feature.csv "
              f"(total {(time.time() - t0) / 60:.1f} min)", flush=True)
    else:
        print(f"\nSMOKE OK ({(time.time() - t0) / 60:.1f} min) — nothing written", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
