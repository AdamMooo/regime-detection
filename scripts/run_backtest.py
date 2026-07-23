"""V2 Stage-1 REAL-DATA runner (era: train 1970+, score ~1990-2026). DO NOT RUN before
.planning/V2-JUMPMODEL-PREREG.md is frozen. Requires --confirm-frozen. One run, one look.

Audit fixes incorporated (2026-07-22 sweep, see prereg §11):
- headline execution = next-close (delay=2, matching Shu/Yu/Mulvey's "one-day trading delay");
  delay=1 (same-close) reported as sensitivity only
- lambda validation window = 2016d (8y, field standard)
- controls C1-C3 use the same rf footing as the primary (paired (r, rf) resampling / rf mean)
- LOTO and era-half fees computed by dropping days from precomputed full-path daily returns
  (fee depends only on marginal moments — exact, no stitched seams)
- VT/SMA weights computed on the full panel then sliced to OOS (fair warmup)
- exhibits: break-even cost, average-exposure-matched static mix, dSharpe bootstrap CI,
  per-arm turnover, lambda path

Primary = FKO fee(JM - B&H), gamma=10 (replication claim). Co-primary deflation exhibit =
fee(JM - VT), pre-declared expectation <= 0 (in-silico capability falsified). Writes
results/backtest_summary.csv + results/backtest_labels.csv (research outputs; live label contract untouched).

--smoke: replaces returns with iid synthetic + shrinks controls/panel — code-path check only,
produces no real-data result (blind preserved)."""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_panel import CRISIS_WINDOWS
from jumpmodel import build_features
from backtest import (fko_fee, jm_weights, sharpe, sma_weights, stationary_bootstrap_ci,
                     strategy_returns, vol_target_weights)
from walkforward import walk_forward

START = "1970-01-01"
TRAIN0 = 5040          # ~20y -> scoring starts ~1990 (Adam's era focus, 2026-07-22)
REFIT = 252
VAL = 2016             # 8y lambda-validation window (field standard)
LAMBDA_GRID = [10.0, 25.0, 50.0, 100.0, 200.0, 400.0, 800.0]
N_INIT = 8
DELAY = 2              # next-close execution (headline); delay=1 is sensitivity only
COST = 10.0
GAMMA = 10.0
N_PLACEBO = 100
N_SURROGATE = 10
N_SIM = 10
N_BOOT = 2000


def maxdd(ret):
    eq = np.cumprod(1.0 + np.asarray(ret))
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())


def run_pipeline(r, train0, n_init=N_INIT):
    F = build_features(r).to_numpy()
    return walk_forward(np.asarray(r, dtype=float), F, burn=63, train0=train0,
                        refit=REFIT, grid=LAMBDA_GRID, val=VAL, n_init=n_init, delay=DELAY)


def arm_returns(w_full, r_full, rf_full, oos, delay=DELAY, cost=COST):
    return strategy_returns(w_full, r_full, rf_full, cost_bps=cost, delay=delay)[oos]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm-frozen", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if not (args.confirm_frozen or args.smoke):
        print("REFUSING TO RUN: freeze .planning/V2-JUMPMODEL-PREREG.md then pass --confirm-frozen.")
        return 2

    train0, n_pl, n_su, n_si, n_boot, n_init = TRAIN0, N_PLACEBO, N_SURROGATE, N_SIM, N_BOOT, N_INIT
    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True).loc[START:]
    if args.smoke:
        panel = panel.iloc[-6000:]
        g = np.random.default_rng(99)
        panel["mkt_ret"] = g.normal(panel["mkt_ret"].mean(), panel["mkt_ret"].std(), len(panel))
        train0, n_pl, n_su, n_si, n_boot, n_init = 3024, 5, 2, 2, 100, 3
        print("SMOKE MODE: synthetic returns, shrunk controls — no real-data result produced.")

    r = panel["mkt_ret"].to_numpy()
    rf = panel["rf"].to_numpy()
    idx = panel.index
    t_start = time.time()

    print(f"[1/12] panel {idx[0].date()}..{idx[-1].date()} n={len(r)} "
          f"(delay={DELAY}, cost={COST}bps, gamma={GAMMA})", flush=True)
    states, lam_hist = run_pipeline(r, train0, n_init)
    oos = states >= 0
    s_o, idx_o = states[oos], idx[oos]
    n_o = int(oos.sum())
    pd.DataFrame({"date": idx_o, "state": s_o}).to_csv(
        ROOT / "results" / "backtest_labels.csv", index=False)
    switches_yr = float((s_o[1:] != s_o[:-1]).sum() / n_o * 252)
    print(f"[2/12] OOS {idx_o[0].date()}..{idx_o[-1].date()} n={n_o} "
          f"bear_frac={float((s_o == 1).mean()):.3f} switches/yr={switches_yr:.2f} "
          f"lam_path={lam_hist}", flush=True)

    # full-path arm construction (weights on full panel -> fair warmup; slice returns to OOS)
    w_jm_full = np.ones(len(r))
    w_jm_full[oos] = jm_weights(s_o)
    ret_jm = arm_returns(w_jm_full, r, rf, oos)
    ret_vt = arm_returns(vol_target_weights(r), r, rf, oos)
    ret_sma = arm_returns(sma_weights(r), r, rf, oos)
    ret_bh = arm_returns(np.ones(len(r)), r, rf, oos, cost=0.0)
    rf_o = rf[oos]

    # ---- controls BEFORE primary (all on the primary's JM-vs-B&H footing, real rf) ----
    rng = np.random.default_rng(0)
    p01 = ((s_o[:-1] == 0) & (s_o[1:] == 1)).sum() / max((s_o[:-1] == 0).sum(), 1)
    p10 = ((s_o[:-1] == 1) & (s_o[1:] == 0)).sum() / max((s_o[:-1] == 1).sum(), 1)
    placebo_fees = []
    for _ in range(n_pl):
        sp = np.empty(n_o, dtype=int)
        sp[0] = s_o[0]
        u = rng.random(n_o)
        for t in range(1, n_o):
            flip = u[t] < (p01 if sp[t - 1] == 0 else p10)
            sp[t] = 1 - sp[t - 1] if flip else sp[t - 1]
        w_p = np.ones(len(r))
        w_p[oos] = jm_weights(sp)
        placebo_fees.append(fko_fee(arm_returns(w_p, r, rf, oos), ret_bh, gamma=GAMMA))
    c1_bar = float(np.quantile(placebo_fees, 0.95))
    print(f"[3/12] C1 exposure-matched placebo (n={n_pl}): 95th pctile fee vs B&H = "
          f"{c1_bar:.1f} bps", flush=True)

    def _null_band(sim_fn, n, label, step):
        fees = []
        for i in range(n):
            r_i, rf_i = sim_fn(i)
            st_i, _ = run_pipeline(r_i, train0, n_init)
            m = st_i >= 0
            w_i = np.ones(len(r_i))
            w_i[m] = jm_weights(st_i[m])
            ret_i = strategy_returns(w_i, r_i, rf_i, cost_bps=COST, delay=DELAY)[m]
            bh_i = strategy_returns(np.ones(len(r_i)), r_i, rf_i, cost_bps=0.0, delay=DELAY)[m]
            fees.append(fko_fee(ret_i, bh_i, gamma=GAMMA))
            print(f"    {label} {i + 1}/{n}: fee={fees[-1]:.1f}", flush=True)
        print(f"[{step}/12] {label} band: [{min(fees):.1f}, {max(fees):.1f}]", flush=True)
        return fees

    def surrogate(i):
        g = np.random.default_rng(100 + i)
        pos = np.empty(len(r), dtype=int)
        t = 0
        while t < len(r):
            start = g.integers(len(r))
            length = min(g.geometric(1.0 / 21), len(r) - t)
            pos[t:t + length] = (start + np.arange(length)) % len(r)
            t += length
        return r[pos], rf[pos]

    c2_fees = _null_band(surrogate, n_su, "C2 surrogate", 4)
    c3_fees = _null_band(
        lambda i: (np.random.default_rng(200 + i).normal(r.mean(), r.std(), len(r)),
                   np.full(len(r), rf.mean())),
        n_si, "C3 iid calibration", 5)

    # ---- primary + deflation exhibit ----
    fee = fko_fee(ret_jm, ret_bh, gamma=GAMMA)
    ci = stationary_bootstrap_ci(ret_jm, ret_bh, lambda a, b: fko_fee(a, b, gamma=GAMMA),
                                 n_boot=n_boot, seed=0)
    fee_vt = fko_fee(ret_jm, ret_vt, gamma=GAMMA)
    ci_vt = stationary_bootstrap_ci(ret_jm, ret_vt, lambda a, b: fko_fee(a, b, gamma=GAMMA),
                                    n_boot=n_boot, seed=0)
    print(f"[6/12] PRIMARY fee(JM-B&H) = {fee:.1f} bps/yr, 90% CI [{ci[0]:.1f}, {ci[1]:.1f}] | "
          f"DEFLATION fee(JM-VT) = {fee_vt:.1f} [{ci_vt[0]:.1f}, {ci_vt[1]:.1f}] "
          f"(pre-declared expectation <= 0)", flush=True)

    # ---- falsifiers ----
    edge = sum(1 for l in lam_hist if l == LAMBDA_GRID[-1]) + \
        sum(1 for l in lam_hist if l == LAMBDA_GRID[0] and switches_yr > 12)
    f2 = edge > len(lam_hist) / 3
    f3 = switches_yr > 12
    f1 = not (fee > 0 and ci[0] > 0)
    controls_clean = (fee > c1_bar) and (fee > max(c2_fees)) and (fee > max(c3_fees))
    print(f"[7/12] F1={f1} F2(lam edge {edge}/{len(lam_hist)})={f2} F3={f3} "
          f"controls_clean={controls_clean}", flush=True)

    # ---- secondaries ----
    table = {}
    for nm, rr, ww in [("JM", ret_jm, pd.Series(w_jm_full).shift(DELAY).fillna(0).to_numpy()[oos]),
                       ("VT", ret_vt, pd.Series(vol_target_weights(r)).shift(DELAY).fillna(0).to_numpy()[oos]),
                       ("SMA200", ret_sma, pd.Series(sma_weights(r)).shift(DELAY).fillna(0).to_numpy()[oos]),
                       ("BH", ret_bh, np.ones(n_o))]:
        table[nm] = dict(sharpe=round(sharpe(rr, rf_o), 3), maxdd=round(maxdd(rr), 3),
                         ann_ret=round(float(np.mean(rr)) * 252, 4),
                         avg_w=round(float(np.mean(ww)), 3),
                         turnover_yr=round(float(np.abs(np.diff(ww)).sum() / n_o * 252), 2))
    print(f"[8/12] arms: {table}", flush=True)

    fee_g1 = fko_fee(ret_jm, ret_bh, gamma=1.0)
    fee_sma = fko_fee(ret_jm, ret_sma, gamma=GAMMA)
    w_bar = table["JM"]["avg_w"]
    ret_mix = arm_returns(np.full(len(r), w_bar), r, rf, oos, cost=0.0)
    fee_mix = fko_fee(ret_jm, ret_mix, gamma=GAMMA)
    ret_jm_d1 = arm_returns(w_jm_full, r, rf, oos, delay=1)
    ret_bh_d1 = arm_returns(np.ones(len(r)), r, rf, oos, delay=1, cost=0.0)
    fee_d1 = fko_fee(ret_jm_d1, ret_bh_d1, gamma=GAMMA)
    fee_c0 = fko_fee(arm_returns(w_jm_full, r, rf, oos, cost=0.0), ret_bh, gamma=GAMMA)
    fee_c20 = fko_fee(arm_returns(w_jm_full, r, rf, oos, cost=20.0), ret_bh, gamma=GAMMA)
    slope = (fee_c20 - fee_c0) / 20.0
    breakeven = -fee_c0 / slope if slope < 0 else np.inf
    ex_jm, ex_bh = ret_jm - rf_o, ret_bh - rf_o
    dsr_ci = stationary_bootstrap_ci(ex_jm, ex_bh, lambda a, b: sharpe(a) - sharpe(b),
                                     n_boot=n_boot, seed=0)
    print(f"[9/12] fee g1={fee_g1:.1f} vsSMA={fee_sma:.1f} vsMix(w={w_bar})={fee_mix:.1f} | "
          f"delay1 sens={fee_d1:.1f} | breakeven cost={breakeven:.1f}bps | "
          f"dSharpe(JM-BH) 90% CI [{dsr_ci[0]:.3f}, {dsr_ci[1]:.3f}]", flush=True)

    halves, loto = {}, {}
    for nm, (a, b) in [("1990_2007", ("1990", "2008")), ("2008_2026", ("2008", "2027"))]:
        m = (idx_o >= a) & (idx_o < b)
        if m.sum() > 252:
            halves[nm] = round(fko_fee(ret_jm[m], ret_bh[m], gamma=GAMMA), 1)
    for name, (a, b) in CRISIS_WINDOWS.items():
        if pd.Timestamp(b) < idx_o[0]:
            continue
        m = ~((idx_o >= a) & (idx_o <= b))
        loto[name] = round(fko_fee(ret_jm[m], ret_bh[m], gamma=GAMMA), 1)
    print(f"[10/12] era halves={halves} LOTO={loto}", flush=True)

    stab = {}
    for shift, label in [(504, "start+2y"), (-504, "start-2y")]:
        st_s, _ = run_pipeline(r, train0 + shift, n_init)
        m = (states >= 0) & (st_s >= 0)
        stab[label] = round(float((states[m] == st_s[m]).mean()), 3)
    print(f"[11/12] label stability vs train-start shift: {stab} (incumbent bar 0.809)", flush=True)

    if (not f1) and (not f2) and (not f3) and controls_clean:
        case = "A"
    elif fee > 0 and f1 and not (f2 or f3):
        case = "B"
    elif f2 or f3:
        case = "D"
    else:
        case = "C"
    print(f"[12/12] CASE {case} (per prereg §9). runtime={(time.time() - t_start) / 60:.1f} min",
          flush=True)

    pd.DataFrame([dict(fee=fee, ci_lo=ci[0], ci_hi=ci[1], fee_vt=fee_vt, ci_vt_lo=ci_vt[0],
                       ci_vt_hi=ci_vt[1], fee_g1=fee_g1, fee_sma=fee_sma, fee_mix=fee_mix,
                       fee_delay1=fee_d1, breakeven_bps=breakeven, switches_yr=switches_yr,
                       case=case, c1_bar=c1_bar, c2_max=max(c2_fees), c3_max=max(c3_fees),
                       dsr_lo=dsr_ci[0], dsr_hi=dsr_ci[1],
                       **{f"stab_{k}": v for k, v in stab.items()},
                       **{f"half_{k}": v for k, v in halves.items()})]
                 ).to_csv(ROOT / "results" / "backtest_summary.csv", index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
