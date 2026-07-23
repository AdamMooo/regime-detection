"""V2 Stage-1 REAL-DATA runner. DO NOT RUN before .planning/V2-JUMPMODEL-PREREG.md is signed
(frozen). Requires --confirm-frozen. One run, one look (§10).

Order: pipeline -> controls (C1 placebo, C2 surrogates, C3 iid calibration) -> primary fee + CI
-> falsifier checks (F1-F3) -> secondaries (gamma=1, other baselines, era halves, LOTO,
stability +/-2y) -> case classification (A-D per §9). ~4-5h dominated by the 20 control pipelines.

Writes results/v2_stage1.csv, results/v2_oos_labels.csv (research output only — does NOT touch
the live data/oos_regime_labels*.csv contract).
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from v2_build import CRISIS_WINDOWS
from v2_core import build_features
from v2_eval import (fko_fee, jm_weights, sharpe, sma_weights, stationary_bootstrap_ci,
                     strategy_returns, vol_target_weights)
from v2_pipeline import walk_forward

TRAIN0 = 3024
REFIT = 252
VAL = 1008
LAMBDA_GRID = [10.0, 25.0, 50.0, 100.0, 200.0, 400.0, 800.0]
N_INIT = 8
START = "1950-01-01"
GAMMA_PRIMARY = 10.0
N_PLACEBO = 100
N_SURROGATE = 10
N_SIM = 10


def load_panel(start=START):
    panel = pd.read_csv(ROOT / "data" / "processed" / "v2_daily.csv",
                        index_col=0, parse_dates=True).loc[start:]
    return panel


def run_pipeline(r, train0=TRAIN0):
    F = build_features(r).to_numpy()
    return walk_forward(np.asarray(r, dtype=float), F, burn=63, train0=train0,
                        refit=REFIT, grid=LAMBDA_GRID, val=VAL, n_init=N_INIT)


def maxdd(ret):
    eq = np.cumprod(1.0 + np.asarray(ret))
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())


def fee_for(states_oos, r_oos, rf_oos, gamma=GAMMA_PRIMARY):
    ret_jm = strategy_returns(jm_weights(states_oos), r_oos, rf_oos)
    ret_vt = strategy_returns(vol_target_weights(r_oos), r_oos, rf_oos)
    return fko_fee(ret_jm, ret_vt, gamma=gamma), ret_jm, ret_vt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm-frozen", action="store_true",
                    help="assert the prereg is signed/frozen before any real-data fitting")
    args = ap.parse_args()
    if not args.confirm_frozen:
        print("REFUSING TO RUN: prereg must be signed (see .planning/V2-JUMPMODEL-PREREG.md), "
              "then pass --confirm-frozen.")
        return 2

    t_start = time.time()
    panel = load_panel()
    r = panel["mkt_ret"].to_numpy()
    rf = panel["rf"].to_numpy()
    idx = panel.index

    print(f"[1/12] panel {idx[0].date()}..{idx[-1].date()} n={len(r)}", flush=True)
    states, lam_hist = run_pipeline(r)
    oos = states >= 0
    s_o, r_o, rf_o, idx_o = states[oos], r[oos], rf[oos], idx[oos]
    pd.DataFrame({"date": idx_o, "state": s_o}).to_csv(
        ROOT / "results" / "v2_oos_labels.csv", index=False)
    switches_yr = float((s_o[1:] != s_o[:-1]).sum() / len(s_o) * 252)
    print(f"[2/12] OOS {idx_o[0].date()}..{idx_o[-1].date()} n={len(s_o)} "
          f"bear_frac={float((s_o == 1).mean()):.3f} switches/yr={switches_yr:.2f} "
          f"lam_hist={lam_hist}", flush=True)

    # ---- controls BEFORE primary (§7) ----
    rng = np.random.default_rng(0)
    p01 = ((s_o[:-1] == 0) & (s_o[1:] == 1)).sum() / max((s_o[:-1] == 0).sum(), 1)
    p10 = ((s_o[:-1] == 1) & (s_o[1:] == 0)).sum() / max((s_o[:-1] == 1).sum(), 1)
    placebo_fees = []
    for _ in range(N_PLACEBO):
        sp = np.empty(len(s_o), dtype=int)
        sp[0] = s_o[0]
        u = rng.random(len(s_o))
        for t in range(1, len(s_o)):
            flip = u[t] < (p01 if sp[t - 1] == 0 else p10)
            sp[t] = 1 - sp[t - 1] if flip else sp[t - 1]
        ret_p = strategy_returns(jm_weights(sp), r_o, rf_o)
        ret_vt_ = strategy_returns(vol_target_weights(r_o), r_o, rf_o)
        placebo_fees.append(fko_fee(ret_p, ret_vt_, gamma=GAMMA_PRIMARY))
    c1_bar = float(np.quantile(placebo_fees, 0.95))
    print(f"[3/12] C1 placebo (n={N_PLACEBO}): 95th pctile fee={c1_bar:.1f} bps", flush=True)

    def _null_band(sim_fn, n, label, step):
        fees = []
        for i in range(n):
            r_i = sim_fn(i)
            st_i, _ = run_pipeline(r_i)
            m = st_i >= 0
            fee_i, _, _ = fee_for(st_i[m], r_i[m], np.zeros(m.sum()))
            fees.append(fee_i)
            print(f"    {label} {i + 1}/{n}: fee={fee_i:.1f}", flush=True)
        print(f"[{step}/12] {label} band: [{min(fees):.1f}, {max(fees):.1f}]", flush=True)
        return fees

    def surrogate(i):
        g = np.random.default_rng(100 + i)
        out = np.empty(len(r))
        t = 0
        while t < len(r):
            start = g.integers(len(r))
            length = min(g.geometric(1.0 / 21), len(r) - t)
            out[t:t + length] = r[(start + np.arange(length)) % len(r)]
            t += length
        return out

    c2_fees = _null_band(surrogate, N_SURROGATE, "C2 surrogate", 4)
    c3_fees = _null_band(
        lambda i: np.random.default_rng(200 + i).normal(r.mean(), r.std(), len(r)),
        N_SIM, "C3 iid calibration", 5)

    # ---- primary (§5) ----
    fee, ret_jm, ret_vt = fee_for(s_o, r_o, rf_o)
    ci = stationary_bootstrap_ci(ret_jm, ret_vt,
                                 lambda a, b: fko_fee(a, b, gamma=GAMMA_PRIMARY),
                                 n_boot=2000, seed=0)
    print(f"[6/12] PRIMARY fee(JM-VT, g=10) = {fee:.1f} bps/yr, 90% CI [{ci[0]:.1f}, {ci[1]:.1f}]",
          flush=True)

    # ---- falsifiers (§6) ----
    edge = sum(1 for l in lam_hist if l == LAMBDA_GRID[-1]) + \
        sum(1 for l in lam_hist if l == LAMBDA_GRID[0] and switches_yr > 12)
    f2 = edge > len(lam_hist) / 3
    f3 = switches_yr > 12
    f1 = not (fee > 0 and ci[0] > 0)
    controls_clean = (fee > c1_bar) and (fee > max(c2_fees)) and (fee > max(c3_fees))
    print(f"[7/12] F1(econ null)={f1} F2(lam edge {edge}/{len(lam_hist)})={f2} "
          f"F3(switches)={f3} controls_clean={controls_clean}", flush=True)

    # ---- secondaries (§8) ----
    ret_sma = strategy_returns(sma_weights(r_o), r_o, rf_o)
    ret_bh = strategy_returns(np.ones(len(r_o)), r_o, rf_o, cost_bps=0.0)
    table = {}
    for nm, rr in [("JM", ret_jm), ("VT", ret_vt), ("SMA200", ret_sma), ("BH", ret_bh)]:
        table[nm] = dict(sharpe=round(sharpe(rr, rf_o), 3), maxdd=round(maxdd(rr), 3),
                         ann_ret=round(float(np.mean(rr)) * 252, 4))
    print(f"[8/12] strategies: {table}", flush=True)
    fee_g1, _, _ = fee_for(s_o, r_o, rf_o, gamma=1.0)
    fee_sma = fko_fee(ret_jm, ret_sma, gamma=GAMMA_PRIMARY)
    fee_bh = fko_fee(ret_jm, ret_bh, gamma=GAMMA_PRIMARY)
    print(f"[9/12] fees: g1={fee_g1:.1f} vsSMA={fee_sma:.1f} vsBH={fee_bh:.1f}", flush=True)

    halves = {}
    for nm, (a, b) in [("era1", ("1962", "1989")), ("era2", ("1990", "2027"))]:
        m = (idx_o >= a) & (idx_o < b)
        f_h, _, _ = fee_for(s_o[m], r_o[m], rf_o[m])
        halves[nm] = round(f_h, 1)
    loto = {}
    for name, (a, b) in CRISIS_WINDOWS.items():
        m = ~((idx_o >= a) & (idx_o <= b))
        f_l, _, _ = fee_for(s_o[m], r_o[m], rf_o[m])
        loto[name] = round(f_l, 1)
    print(f"[10/12] era halves={halves} LOTO={loto}", flush=True)

    stab = {}
    for shift, label in [(504, "start+2y"), (-504, "start-2y")]:
        st_s, _ = run_pipeline(r, train0=TRAIN0 + shift)
        m = (states >= 0) & (st_s >= 0)
        stab[label] = round(float((states[m] == st_s[m]).mean()), 3)
    print(f"[11/12] label stability vs train-start shift: {stab} (incumbent bar: 0.809)", flush=True)

    if (not f1) and (not f2) and (not f3) and controls_clean:
        case = "A"
    elif fee > 0 and f1 and not (f2 or f3):
        case = "B"
    elif f2 or f3:
        case = "D"
    else:
        case = "C"
    print(f"[12/12] CASE {case} (per §9). runtime={((time.time() - t_start) / 60):.1f} min", flush=True)

    pd.DataFrame([dict(fee=fee, ci_lo=ci[0], ci_hi=ci[1], fee_g1=fee_g1, fee_sma=fee_sma,
                       fee_bh=fee_bh, switches_yr=switches_yr, case=case,
                       c1_bar=c1_bar, c2_max=max(c2_fees), c3_max=max(c3_fees),
                       **{f"stab_{k}": v for k, v in stab.items()},
                       **{f"half_{k}": v for k, v in halves.items()})]
                 ).to_csv(ROOT / "results" / "v2_stage1.csv", index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
