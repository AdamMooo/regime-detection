"""Chapter-2 REAL-DATA runner: state-conditional ERC vs matched baselines.
DO NOT RUN before .planning/ALLOCATION-PREREG.md (Rev 2) is FROZEN. Requires
--confirm-frozen. One run, one look.

Battery order (controls before primary): C1 placebo (100) -> C2 episode-shuffle (50)
-> C3 iid panels (20) -> primary fee_A (cond - B_match) + co-primary fee_B
(cond - B_react) with 90% bootstrap CIs -> falsifiers F1/F1b/F2/F3 -> secondaries
(gamma=1, dMaxDD, dSharpe CI, vol-tracking RMSE post-activation, turnover, era splits,
from-activation fees). Writes results/allocation_summary.csv, allocation_controls.csv,
allocation_arms.csv.

--smoke: synthetic two-state panels (known truth), shrunk controls — capability +
code-path check only; writes nothing to results/ (blind preserved)."""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from allocation import (CovProviders, build_target_weights, decision_positions,
                        rolling_vol, simulate_multi)
from backtest import fko_fee, sharpe, stationary_bootstrap_ci, strategy_returns, \
    vol_target_weights

PANEL_START = "1963-01-01"
CAPS = np.array([0.75, 0.75, 0.25])
VOL_TARGET = 0.08
COST = 10.0
DELAY = 2
GAMMA = 10.0
MIN_STATE_DAYS = 500
SHRINK = 0.5
EWMA_LAM = 0.97
N_PLACEBO = 100
N_SHUFFLE = 50
N_IID = 20
N_BOOT = 2000
EP2022 = ("2022-02-14", "2023-06-07")   # named corr-regime failure-mode episode


def maxdd(ret):
    eq = np.cumprod(1.0 + np.asarray(ret))
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())


def erc_arm(X, rf, dates, label, score, providers, kind):
    dec = decision_positions(dates, label, score)
    W = build_target_weights(len(X), dec, label, providers, kind, CAPS,
                             target=VOL_TARGET)
    ret, W_exec = simulate_multi(W, X, rf, cost_bps=COST, delay=DELAY)
    return ret[score], W_exec[score]


def conditional_fees(X, rf, dates, label, score, base_prov, ret_match, ret_react,
                     act_mask):
    """fee_A on the full scored window (pre-activation difference is exactly 0);
    fee_B on the from-activation window (pre-activation cond ≡ B_match, so the full
    window would measure match-vs-react, not conditioning)."""
    prov = CovProviders(X, label, min_state_days=MIN_STATE_DAYS, shrink=SHRINK,
                        lam=EWMA_LAM, base=base_prov)
    ret_c, _ = erc_arm(X, rf, dates, label, score, prov, "cond")
    return (fko_fee(ret_c, ret_match, gamma=GAMMA),
            fko_fee(ret_c[act_mask], ret_react[act_mask], gamma=GAMMA))


def markov_placebo(s_scored, rng):
    p01 = ((s_scored[:-1] == 0) & (s_scored[1:] == 1)).sum() / max((s_scored[:-1] == 0).sum(), 1)
    p10 = ((s_scored[:-1] == 1) & (s_scored[1:] == 0)).sum() / max((s_scored[:-1] == 1).sum(), 1)
    n = len(s_scored)
    sp = np.empty(n, dtype=int)
    sp[0] = s_scored[0]
    u = rng.random(n)
    for t in range(1, n):
        flip = u[t] < (p01 if sp[t - 1] == 0 else p10)
        sp[t] = 1 - sp[t - 1] if flip else sp[t - 1]
    return sp


def episode_shuffle(s_scored, rng):
    """Relocate the real stressed episodes (count + durations preserved, order
    shuffled, non-overlapping) via random gap splitting."""
    n = len(s_scored)
    d = np.diff(np.r_[0, s_scored, 0])
    durs = np.flatnonzero(d == -1) - np.flatnonzero(d == 1)
    durs = rng.permutation(durs)
    calm_total = n - durs.sum()
    gaps = rng.dirichlet(np.ones(len(durs) + 1)) * calm_total
    gaps = np.floor(gaps).astype(int)
    gaps[-1] = calm_total - gaps[:-1].sum()
    sp = np.zeros(n, dtype=int)
    t = 0
    for g, dur in zip(gaps[:-1], durs):
        t += g
        sp[t:t + dur] = 1
        t += dur
    return sp


def synthetic_panel(T, structured, seed):
    """Two-state panel with known truth: stressed = higher vols (+ deeper negative
    stock-bond corr when structured); calm otherwise. Gold NaN for the first fifth
    (era logic exercised). Returns X, rf, label."""
    rng = np.random.default_rng(seed)
    s = np.empty(T, dtype=int)
    s[0] = 0
    u = rng.random(T)
    for t in range(1, T):
        flip = u[t] < (0.010 if s[t - 1] == 0 else 0.025)
        s[t] = 1 - s[t - 1] if flip else s[t - 1]

    def cov_of(vols, r_sb):
        c = np.eye(3)
        c[0, 1] = c[1, 0] = r_sb
        d = np.diag(vols)
        return d @ c @ d / 252.0

    # deliberately strong structure so the capability check is legible: stressed
    # vols push the ERC portfolio above the 8% target (scale channel exercised)
    c_calm = cov_of([0.143, 0.065, 0.15], -0.10)
    c_str = (cov_of([0.36, 0.11, 0.20], -0.50) if structured else c_calm)
    X = np.empty((T, 3))
    for st, c in ((0, c_calm), (1, c_str)):
        m = s == st
        X[m] = rng.multivariate_normal([0.0003, 0.0002, 0.0002], c, size=int(m.sum()))
    X[: T // 5, 2] = np.nan
    return X, np.full(T, 0.0001), s


def run_battery(X, rf, dates, label, score, n_pl, n_sh, n_iid, n_boot, log):
    t0 = time.time()
    s_scored = label[score]
    n_o = int(score.sum())
    prov = CovProviders(X, label, min_state_days=MIN_STATE_DAYS, shrink=SHRINK,
                        lam=EWMA_LAM)
    era2_d = dates[prov.era2_t].date() if prov.era2_t is not None else None
    log(f"[1/9] scoring {dates[score][0].date()}..{dates[score][-1].date()} n={n_o} "
        f"stressed_frac={float((s_scored == 1).mean()):.3f} era2_start={era2_d} "
        f"(delay={DELAY}, cost={COST}bps, gamma={GAMMA}, target={VOL_TARGET:.0%})")

    # activation = first scored date with >=500 labeled days in BOTH states (label
    # counts only — no returns looked at); fee_B and F2 are scored from here
    act = None
    for t in np.flatnonzero(score):
        if (prov.state[(1, 0)].n[t] >= MIN_STATE_DAYS
                and prov.state[(1, 1)].n[t] >= MIN_STATE_DAYS):
            act = t
            break
    if act is None:
        raise SystemExit("conditioning never activates — window too short")
    act_mask = np.flatnonzero(score) >= act
    log(f"      conditioning activation: {dates[act].date()} "
        f"({int(act_mask.sum())} of {n_o} scored days follow)")

    ret_match, W_match = erc_arm(X, rf, dates, label, score, prov, "match")
    ret_react, W_react = erc_arm(X, rf, dates, label, score, prov, "react")
    ret_cond, W_cond = erc_arm(X, rf, dates, label, score, prov, "cond")

    # context arms
    W6040 = np.tile([0.6, 0.4, 0.0], (len(X), 1))
    W6040[np.isnan(X[:, 1])] = [0.6, 0.4, 0.0]
    ret_6040, _ = simulate_multi(W6040, X, rf, cost_bps=COST, delay=DELAY)
    ret_6040 = ret_6040[score]
    mkt = np.nan_to_num(X[:, 0])
    ret_vt = strategy_returns(vol_target_weights(mkt), mkt, rf, cost_bps=COST,
                              delay=DELAY)[score]
    ret_bh = strategy_returns(np.ones(len(X)), mkt, rf, cost_bps=0.0,
                              delay=DELAY)[score]
    rf_o = rf[score]

    # ---- controls BEFORE primary ----
    rng = np.random.default_rng(0)
    ctrl_rows = []
    for name, n_draws, maker in (("C1_placebo", n_pl, markov_placebo),
                                 ("C2_shuffle", n_sh, episode_shuffle)):
        fees_a, fees_b = [], []
        for i in range(n_draws):
            lab_i = np.full(len(X), -1)
            lab_i[score] = maker(s_scored, rng)
            fa, fb = conditional_fees(X, rf, dates, lab_i, score, prov,
                                      ret_match, ret_react, act_mask)
            fees_a.append(fa)
            fees_b.append(fb)
            ctrl_rows.append(dict(control=name, draw=i, fee_a=fa, fee_b=fb))
        log(f"[{2 if name == 'C1_placebo' else 3}/9] {name} (n={n_draws}): "
            f"fee_a 95th={np.quantile(fees_a, 0.95):.1f} "
            f"fee_b 95th={np.quantile(fees_b, 0.95):.1f}")
        if name == "C1_placebo":
            c1a, c1b = np.quantile(fees_a, 0.95), np.quantile(fees_b, 0.95)
        else:
            c2a, c2b = np.quantile(fees_a, 0.95), np.quantile(fees_b, 0.95)

    iid_a, iid_b = [], []
    for i in range(n_iid):
        g = np.random.default_rng(300 + i)
        Xs = np.full_like(X, np.nan)
        m3 = ~np.isnan(X).any(axis=1)
        m2 = ~np.isnan(X[:, :2]).any(axis=1) & ~m3
        for msk, k in ((m2, 2), (m3, 3)):
            if msk.sum() < 300:
                continue
            sub = X[msk][:, :k]
            Xs[np.flatnonzero(msk)[:, None], np.arange(k)] = g.multivariate_normal(
                sub.mean(axis=0), np.cov(sub.T), size=int(msk.sum()))
        prov_i = CovProviders(Xs, label, min_state_days=MIN_STATE_DAYS,
                              shrink=SHRINK, lam=EWMA_LAM)
        rm_i, _ = erc_arm(Xs, rf, dates, label, score, prov_i, "match")
        rr_i, _ = erc_arm(Xs, rf, dates, label, score, prov_i, "react")
        rc_i, _ = erc_arm(Xs, rf, dates, label, score, prov_i, "cond")
        fa = fko_fee(rc_i, rm_i, gamma=GAMMA)
        fb = fko_fee(rc_i[act_mask], rr_i[act_mask], gamma=GAMMA)
        iid_a.append(fa)
        iid_b.append(fb)
        ctrl_rows.append(dict(control="C3_iid", draw=i, fee_a=fa, fee_b=fb))
    log(f"[4/9] C3 iid (n={n_iid}): fee_a band [{min(iid_a):.1f}, {max(iid_a):.1f}] "
        f"fee_b band [{min(iid_b):.1f}, {max(iid_b):.1f}]")

    # ---- primary + co-primary ----
    fee_a = fko_fee(ret_cond, ret_match, gamma=GAMMA)
    ci_a = stationary_bootstrap_ci(ret_cond, ret_match,
                                   lambda a, b: fko_fee(a, b, gamma=GAMMA),
                                   n_boot=n_boot, seed=0)
    fee_b = fko_fee(ret_cond[act_mask], ret_react[act_mask], gamma=GAMMA)
    ci_b = stationary_bootstrap_ci(ret_cond[act_mask], ret_react[act_mask],
                                   lambda a, b: fko_fee(a, b, gamma=GAMMA),
                                   n_boot=n_boot, seed=0)
    log(f"[5/9] PRIMARY fee_A(cond-B_match, full) = {fee_a:.1f} bps/yr, 90% CI "
        f"[{ci_a[0]:.1f}, {ci_a[1]:.1f}] | CO-PRIMARY fee_B(cond-B_react, from "
        f"activation) = {fee_b:.1f} [{ci_b[0]:.1f}, {ci_b[1]:.1f}]")

    # ---- falsifiers ----
    rv_c = rolling_vol(ret_cond[act_mask])
    rv_m = rolling_vol(ret_match[act_mask])
    volvol_c, volvol_m = float(rv_c.std()), float(rv_m.std())
    rmse_c = float(np.sqrt(((rv_c - VOL_TARGET) ** 2).mean()))
    rmse_m = float(np.sqrt(((rv_m - VOL_TARGET) ** 2).mean()))
    to_c = float(np.abs(np.diff(W_cond, axis=0)).sum() / n_o * 252)
    to_m = float(np.abs(np.diff(W_match, axis=0)).sum() / n_o * 252)
    to_r = float(np.abs(np.diff(W_react, axis=0)).sum() / n_o * 252)
    f1 = not (fee_a > 0 and ci_a[0] > 0)
    f1b = not (fee_b > 0 and ci_b[0] > 0)
    f2 = volvol_c > volvol_m
    f3 = to_c > 5 * to_m
    controls_clean = (fee_a > c1a and fee_a > c2a and fee_a > max(iid_a)
                      and fee_b > c1b and fee_b > c2b and fee_b > max(iid_b))
    log(f"[6/9] F1={f1} F1b={f1b} F2={f2} (vol-of-vol cond {volvol_c:.4f} vs match "
        f"{volvol_m:.4f}; rmse-vs-target {rmse_c:.4f}/{rmse_m:.4f}) F3={f3} "
        f"(turnover c/m/r {to_c:.2f}/{to_m:.2f}/{to_r:.2f}) "
        f"controls_clean={controls_clean}")

    # ---- secondaries ----
    table = {}
    for nm, rr in (("cond", ret_cond), ("B_match", ret_match), ("B_react", ret_react),
                   ("60_40", ret_6040), ("VT_eq", ret_vt), ("BH_eq", ret_bh)):
        table[nm] = dict(ann_ret=round(float(np.mean(rr)) * 252, 4),
                         ann_vol=round(float(np.std(rr)) * np.sqrt(252), 4),
                         sharpe=round(sharpe(rr, rf_o), 3), maxdd=round(maxdd(rr), 3))
    log(f"[7/9] arms: {table}")

    fee_a_g1 = fko_fee(ret_cond, ret_match, gamma=1.0)
    fee_b_g1 = fko_fee(ret_cond, ret_react, gamma=1.0)
    dmaxdd = maxdd(ret_cond) - maxdd(ret_match)
    ex_c, ex_m = ret_cond - rf_o, ret_match - rf_o
    dsr_ci = stationary_bootstrap_ci(ex_c, ex_m, lambda a, b: sharpe(a) - sharpe(b),
                                     n_boot=n_boot, seed=0)
    d_scored = dates[score]
    splits = {}
    for nm, msk in (("pre2000", d_scored < "2000-01-01"),
                    ("post2000", d_scored >= "2000-01-01"),
                    ("ex2022ep", ~((d_scored >= EP2022[0]) & (d_scored <= EP2022[1]))),
                    ("from_act", pd.Series(act_mask).to_numpy())):
        m = np.asarray(msk)
        splits[nm] = (round(fko_fee(ret_cond[m], ret_match[m], gamma=GAMMA), 1),
                      round(fko_fee(ret_cond[m], ret_react[m], gamma=GAMMA), 1))
    log(f"[8/9] gamma1 A/B={fee_a_g1:.1f}/{fee_b_g1:.1f} dMaxDD={dmaxdd:.3f} "
        f"dSharpe(cond-match) 90% CI [{dsr_ci[0]:.3f}, {dsr_ci[1]:.3f}] | "
        f"era splits (fee_a, fee_b): {splits}")

    if (not f1) and (not f1b) and (not f2) and (not f3) and controls_clean:
        verdict = "SUPPORT"
    elif f1:
        verdict = "NULL"
    elif f1b:
        verdict = "NULL_F1B_replicates_reactive"
    elif f2 or f3:
        verdict = "MECHANISM_FAIL"
    else:
        verdict = "NULL_controls_dirty"
    log(f"[9/9] VERDICT: {verdict} (per prereg §5-§7). "
        f"runtime={(time.time() - t0) / 60:.1f} min")

    summary = dict(fee_a=fee_a, ci_a_lo=ci_a[0], ci_a_hi=ci_a[1], fee_b=fee_b,
                   ci_b_lo=ci_b[0], ci_b_hi=ci_b[1], fee_a_g1=fee_a_g1,
                   fee_b_g1=fee_b_g1, c1a_95=c1a, c1b_95=c1b, c2a_95=c2a, c2b_95=c2b,
                   c3a_max=max(iid_a), c3b_max=max(iid_b), f1=f1, f1b=f1b, f2=f2,
                   f3=f3, controls_clean=controls_clean, verdict=verdict,
                   volvol_cond=volvol_c, volvol_match=volvol_m,
                   rmse_cond=rmse_c, rmse_match=rmse_m, turnover_cond=to_c,
                   turnover_match=to_m, turnover_react=to_r, dmaxdd=dmaxdd,
                   dsr_lo=dsr_ci[0], dsr_hi=dsr_ci[1],
                   activation=str(dates[act].date()),
                   **{f"split_{k}_a": v[0] for k, v in splits.items()},
                   **{f"split_{k}_b": v[1] for k, v in splits.items()},
                   **{f"{nm}_{k}": v for nm, d in table.items() for k, v in d.items()})
    arms = pd.DataFrame({"date": d_scored, "ret_cond": ret_cond,
                         "ret_match": ret_match, "ret_react": ret_react,
                         "ret_6040": ret_6040, "ret_vt": ret_vt, "ret_bh": ret_bh,
                         "w_cond_eq": W_cond[:, 0], "w_cond_bd": W_cond[:, 1],
                         "w_cond_au": W_cond[:, 2], "w_match_eq": W_match[:, 0],
                         "w_match_bd": W_match[:, 1], "w_match_au": W_match[:, 2],
                         "w_react_eq": W_react[:, 0], "w_react_bd": W_react[:, 1],
                         "w_react_au": W_react[:, 2]})
    return summary, pd.DataFrame(ctrl_rows), arms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm-frozen", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if not (args.confirm_frozen or args.smoke):
        print("REFUSING TO RUN: freeze .planning/ALLOCATION-PREREG.md then pass "
              "--confirm-frozen.")
        return 2

    if args.smoke:
        print("SMOKE MODE: synthetic panels, shrunk controls — no real-data result.")
        fees = {}
        for structured in (True, False):
            X, rf, s = synthetic_panel(6000, structured, seed=42)
            dates = pd.date_range("2001-01-03", periods=6000, freq="B")
            label = np.full(6000, -1)
            label[1500:] = s[1500:]
            score = label >= 0
            summary, _, _ = run_battery(X, rf, dates, label, score,
                                        n_pl=5, n_sh=3, n_iid=2, n_boot=100,
                                        log=lambda m: print("  " + m, flush=True))
            fees[structured] = summary
            print(f"SMOKE structured={structured}: fee_a={summary['fee_a']:.1f} "
                  f"fee_b={summary['fee_b']:.1f} volvol c/m="
                  f"{summary['volvol_cond']:.4f}/{summary['volvol_match']:.4f} "
                  f"verdict={summary['verdict']}\n", flush=True)
        ok = (fees[True]["fee_a"] > max(5.0, 3.0 * abs(fees[False]["fee_a"]))
              and fees[True]["volvol_cond"] < fees[True]["volvol_match"])
        print(f"SMOKE CAPABILITY {'PASS' if ok else 'FAIL'}: structured fee_a "
              f"{fees[True]['fee_a']:.1f} vs unstructured {fees[False]['fee_a']:.1f}; "
              f"risk-stabilization holds={fees[True]['volvol_cond'] < fees[True]['volvol_match']}")
        return 0 if ok else 1

    panel = pd.read_csv(ROOT / "data" / "processed" / "assets_daily.csv",
                        index_col=0, parse_dates=True).loc[PANEL_START:]
    labels = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"])
    lab = labels.set_index("date")["state"].reindex(panel.index).fillna(-1).astype(int)
    X = panel[["mkt_ret", "bond10_ret", "gold_ret"]].to_numpy()
    rf = panel["rf"].to_numpy()
    label = lab.to_numpy()
    score = label >= 0

    lines = []

    def log(msg):
        print(msg, flush=True)
        lines.append(msg)

    summary, controls, arms = run_battery(X, rf, panel.index, label, score,
                                          n_pl=N_PLACEBO, n_sh=N_SHUFFLE,
                                          n_iid=N_IID, n_boot=N_BOOT, log=log)
    pd.DataFrame([summary]).to_csv(ROOT / "results" / "allocation_summary.csv",
                                   index=False)
    controls.to_csv(ROOT / "results" / "allocation_controls.csv", index=False)
    arms.to_csv(ROOT / "results" / "allocation_arms.csv", index=False)
    (ROOT / "results" / "allocation_run.log").write_text("\n".join(lines),
                                                         encoding="utf-8")
    print("wrote results/allocation_summary.csv, allocation_controls.csv, "
          "allocation_arms.csv, allocation_run.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
