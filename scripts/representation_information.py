#!/usr/bin/env python3
"""Does the HMM continuous coordinate Z_loc carry incremental OOS information about
forward SPY realized vol beyond the causal observables? (PRE-REGISTERED, upgraded.)

Primary H0: dR2_oos = R2_oos(X_rich + Z) - R2_oos(X_rich) <= 0   vs   H1: > 0
Primary target : SPY forward 21d realized vol (annualized %).
Primary baseline: X + EWMA21(X)  (ladder A/B/C/D pre-declared; B is primary).
Primary rep     : Z_loc = E[mu_S | x_{1:t}] = filt @ loc.
Validation      : 2024-01-02.. (HMM frozen on discovery <=2023-12-31, forward-filtered).
Success(primary): dR2 >= 0.01 AND perm p < 0.05 AND survives richer baselines (Case D+).

FWL caveat: the nested increment isolates only the part of Z NOT LINEARLY explained by
the baseline. Baseline D (squares) is a low-order-nonlinearity robustness check, not a
proof of information-theoretic independence. Positive => "incremental beyond the
pre-specified linear observable baseline", NOT "absent from the observables".

Battery: R2_naive/A..D/+Z, dR2, RMSE, MAE; block-perm p; block-bootstrap CI;
phase-randomized negative control; rolling calendar-year blocks (diagnostic only);
representation-stability (cross-seed/window/feature-subset/K_max) reported SEPARATELY.

Reads : data/processed/features.csv, data/processed/spx_data.csv
Writes: results/representation_information.csv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import FEATURES, HDP_TRUNCATION, TRAIN_END, DATA_DIR, RESULTS_DIR
from src.core.hdp_hmm import fit_hdp_hmm, posterior_mean_params, get_labels_and_probs

PROC = os.path.join(DATA_DIR, "processed")
ALPHAS = np.logspace(-3, 4, 30)
BLOCK = 63
B_PERM = 500
B_BOOT = 500
B_SURR = 200
HORIZONS = [5, 21, 63]
VIX_IDX = FEATURES.index("vol_index")
RNG = np.random.default_rng(0)


def fwd_realized_vol(r, h):
    out = np.full(len(r), np.nan)
    for t in range(len(r) - h):
        out[t] = np.std(r[t + 1:t + 1 + h], ddof=1) * np.sqrt(252) * 100.0
    return out


def fit_Z(Xstd, ntr, win, seed, kmax, cols):
    Xc = Xstd[:, cols]
    Xtr = Xc[:ntr] if win is None else Xc[ntr - win:ntr]
    _, samples = fit_hdp_hmm(Xtr, K_max=kmax, seed=seed)
    params = posterior_mean_params(samples, K_max=kmax)
    _, filt, _, active = get_labels_and_probs(Xc, params, hold_days=1)
    loc_a = params["locs"][active]
    Z = filt @ loc_a
    H = -np.sum(filt * np.log(filt + 1e-12), axis=1, keepdims=True)
    return Z, H, len(active)


def fit_predict(Xtr, ytr, Xva):
    sc = StandardScaler().fit(Xtr)
    m = RidgeCV(alphas=ALPHAS).fit(sc.transform(Xtr), ytr)
    return m.predict(sc.transform(Xva))


def rrm(y, pred):
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return (1 - ss_res / ss_tot, float(np.sqrt(np.mean((y - pred) ** 2))), float(np.mean(np.abs(y - pred))))


def indices(target, ntr, h, N):
    valid = ~np.isnan(target)
    disc = np.array([t for t in range(ntr) if t + h < ntr and valid[t]])
    val = np.array([t for t in range(ntr, N) if valid[t]])
    return disc, val


def block_perm(n, block, rng):
    nb = int(np.ceil(n / block))
    blocks = [np.arange(i * block, min((i + 1) * block, n)) for i in range(nb)]
    return np.concatenate([blocks[i] for i in rng.permutation(nb)])


def phase_randomize(Z, rng):
    T = len(Z)
    F = np.fft.rfft(Z, axis=0)
    ph = np.exp(1j * rng.uniform(0, 2 * np.pi, size=F.shape[0]))
    ph[0] = 1.0
    if T % 2 == 0:
        ph[-1] = 1.0
    return np.fft.irfft(F * ph[:, None], n=T, axis=0)


def evaluate(Xb, Z, y, disc, val, tests=False):
    yd, yv = y[disc], y[val]
    p_naive = np.full(len(val), yd.mean())
    p_base = fit_predict(Xb[disc], yd, Xb[val])
    XZ = np.hstack([Xb, Z])
    p_full = fit_predict(XZ[disc], yd, XZ[val])
    r2n, rn, mn = rrm(yv, p_naive)
    r2b, rb, mb = rrm(yv, p_base)
    r2f, rf, mf = rrm(yv, p_full)
    out = dict(r2_naive=r2n, r2_base=r2b, r2_full=r2f, incr=r2f - r2b,
               rmse_naive=rn, rmse_base=rb, rmse_full=rf, mae_base=mb, mae_full=mf,
               p_base=p_base, p_full=p_full, yv=yv)
    if tests:
        n = len(Z)
        null = np.empty(B_PERM)
        for b in range(B_PERM):
            Zp = Z[block_perm(n, BLOCK, RNG)]
            pf = fit_predict(np.hstack([Xb, Zp])[disc], yd, np.hstack([Xb, Zp])[val])
            null[b] = rrm(yv, pf)[0] - r2b
        out["perm_p"] = (np.sum(null >= out["incr"]) + 1) / (B_PERM + 1)
        out["null_med"] = float(np.median(null))
        nv = len(val)
        boot = np.empty(B_BOOT)
        nb = max(1, nv // BLOCK)
        for b in range(B_BOOT):
            sel = RNG.integers(0, nb, size=nb)
            pick = np.concatenate([np.arange(s * BLOCK, min((s + 1) * BLOCK, nv)) for s in sel])
            boot[b] = rrm(yv[pick], p_full[pick])[0] - rrm(yv[pick], p_base[pick])[0]
        out["ci_lo"], out["ci_hi"] = float(np.percentile(boot, 5)), float(np.percentile(boot, 95))
        surr = np.empty(B_SURR)
        for b in range(B_SURR):
            Zs = phase_randomize(Z, RNG)
            pf = fit_predict(np.hstack([Xb, Zs])[disc], yd, np.hstack([Xb, Zs])[val])
            surr[b] = rrm(yv, pf)[0] - r2b
        out["surr_med"], out["surr_lo"], out["surr_hi"] = (
            float(np.median(surr)), float(np.percentile(surr, 5)), float(np.percentile(surr, 95)))
    return out


def corr_cols(A, B, idx):
    k = min(A.shape[1], B.shape[1])
    return float(np.mean([np.corrcoef(A[idx, d], B[idx, d])[0, 1] for d in range(k)]))


def main():
    feat = pd.read_csv(os.path.join(PROC, "features.csv"), parse_dates=["Date"]).set_index("Date")
    raw = pd.read_csv(os.path.join(PROC, "spx_data.csv"), parse_dates=["Date"]).set_index("Date")
    dates = feat.index
    Xstd = feat[FEATURES].values
    r = raw["spy_ret"].reindex(dates).values
    N = len(Xstd)
    ntr = int((dates <= pd.Timestamp(TRAIN_END)).sum())
    all4 = list(range(4))
    print(f"Aligned N={N} ({dates[0].date()}..{dates[-1].date()}); discovery n={ntr}; validation n={N-ntr}\n")

    Z42, H42, K42 = fit_Z(Xstd, ntr, None, 42, 8, all4)
    print(f"PRIMARY rep: HMM seed=42 expanding, K_eff={K42}, Z_loc={Z42.shape}\n")

    def ewma(a, s):
        return pd.DataFrame(a).ewm(span=s, adjust=False).mean().values
    A = Xstd
    Bb = np.hstack([Xstd, ewma(Xstd, 21)])
    C = np.hstack([Xstd, ewma(Xstd, 5), ewma(Xstd, 21), ewma(Xstd, 63)])
    D = np.hstack([C, Xstd ** 2])
    ladder = {"A_raw": A, "B_ewma21(PRIMARY)": Bb, "C_ewma5_21_63": C, "D_C+squares": D}

    rows = []
    y21 = fwd_realized_vol(r, 21)
    disc, val = indices(y21, ntr, 21, N)

    # ---------------- PRIMARY ----------------
    res = evaluate(Bb, Z42, y21, disc, val, tests=True)
    print("=" * 78)
    print("PRIMARY  Y=fwd21d RV   baseline B=X+EWMA21   rep=Z_loc(seed42)")
    print("=" * 78)
    print(f"  R2_naive(disc-mean) = {res['r2_naive']:+.4f}    RMSE_naive={res['rmse_naive']:.3f}")
    print(f"  R2_base (X_rich)    = {res['r2_base']:+.4f}    RMSE={res['rmse_base']:.3f}  MAE={res['mae_base']:.3f}")
    print(f"  R2_full (X_rich+Z)  = {res['r2_full']:+.4f}    RMSE={res['rmse_full']:.3f}  MAE={res['mae_full']:.3f}")
    print(f"  dR2 (Z increment)   = {res['incr']:+.4f}   [Case D needs >=0.01, p<0.05, survives C/D]")
    print(f"  block-perm  null med={res['null_med']:+.4f}   perm p={res['perm_p']:.4f}")
    print(f"  block-boot  90% CI  = [{res['ci_lo']:+.4f}, {res['ci_hi']:+.4f}]")
    print(f"  neg-control (phase) med={res['surr_med']:+.4f}  90%=[{res['surr_lo']:+.4f},{res['surr_hi']:+.4f}]")
    rows.append(dict(cell="PRIMARY_B_21d", **{k: res[k] for k in
               ("r2_naive", "r2_base", "r2_full", "incr", "perm_p", "null_med", "ci_lo", "ci_hi",
                "surr_med", "surr_lo", "surr_hi", "rmse_base", "rmse_full", "mae_base", "mae_full")}))

    # rolling calendar-year blocks (diagnostic)
    print("\n  rolling validation blocks (diagnostic only, models fixed):")
    yrs = np.array([dates[t].year for t in val])
    for yv_year in sorted(set(yrs)):
        m = yrs == yv_year
        if m.sum() < 20:
            continue
        r2b = rrm(res["yv"][m], res["p_base"][m])[0]
        r2f = rrm(res["yv"][m], res["p_full"][m])[0]
        print(f"    {yv_year}: n={int(m.sum()):3d}  R2_base={r2b:+.4f}  R2_full={r2f:+.4f}  dR2={r2f-r2b:+.4f}")
        rows.append(dict(cell=f"block_{yv_year}", r2_base=r2b, r2_full=r2f, incr=r2f - r2b))

    # ---------------- BASELINE LADDER ----------------
    print("\n" + "=" * 78 + "\nBASELINE LADDER (Z increment vs increasingly flexible observables), 21d all\n" + "=" * 78)
    print(f"  {'baseline':<22}{'R2_base':>9}{'R2_+Z':>9}{'dR2':>9}{'perm_p':>9}")
    for name, Xb in ladder.items():
        res_l = evaluate(Xb, Z42, y21, disc, val, tests=True)
        print(f"  {name:<22}{res_l['r2_base']:>9.4f}{res_l['r2_full']:>9.4f}{res_l['incr']:>9.4f}{res_l['perm_p']:>9.4f}")
        rows.append(dict(cell=f"ladder_{name}", r2_base=res_l["r2_base"], r2_full=res_l["r2_full"],
                         incr=res_l["incr"], perm_p=res_l["perm_p"]))

    # ---------------- PRE-DECLARED PANEL: horizon x region + entropy ----------------
    print("\n" + "=" * 78 + "\nPRE-DECLARED PANEL (Bonferroni): horizon x region, +entropy   [baseline B]\n" + "=" * 78)
    n_sec = len(HORIZONS) * 3 + 1
    bonf = 0.05 / n_sec
    print(f"  Bonferroni alpha = 0.05/{n_sec} = {bonf:.4f}")
    print(f"  {'cell':<20}{'R2_base':>9}{'R2_+Z':>9}{'dR2':>9}{'perm_p':>9}")
    for h in HORIZONS:
        yh = fwd_realized_vol(r, h)
        dh, vh = indices(yh, ntr, h, N)
        rr = evaluate(Bb, Z42, yh, dh, vh, tests=(True))
        vix = Xstd[vh, VIX_IDX]
        hi = vix >= np.median(vix)
        for region, mask in (("all", np.ones(len(vh), bool)), ("hiVIX", hi), ("loVIX", ~hi)):
            r2b = rrm(rr["yv"][mask], rr["p_base"][mask])[0]
            r2f = rrm(rr["yv"][mask], rr["p_full"][mask])[0]
            pv = rr["perm_p"] if region == "all" else np.nan
            star = " *" if (region == "all" and pv < bonf) else ""
            print(f"  {f'h={h} {region}':<20}{r2b:>9.4f}{r2f:>9.4f}{r2f-r2b:>9.4f}"
                  f"{(pv if not np.isnan(pv) else float('nan')):>9.4f}{star}")
            rows.append(dict(cell=f"panel_h{h}_{region}", r2_base=r2b, r2_full=r2f, incr=r2f - r2b, perm_p=pv))
    res_e = evaluate(Bb, np.hstack([Z42, H42]), y21, disc, val, tests=True)
    print(f"  {'21d all +entropy':<20}{res_e['r2_base']:>9.4f}{res_e['r2_full']:>9.4f}"
          f"{res_e['incr']:>9.4f}{res_e['perm_p']:>9.4f}{' *' if res_e['perm_p']<bonf else ''}")
    rows.append(dict(cell="panel_entropy", r2_base=res_e["r2_base"], r2_full=res_e["r2_full"],
                     incr=res_e["incr"], perm_p=res_e["perm_p"]))

    # ---------------- REPRESENTATION STABILITY (separate from usefulness) ----------------
    print("\n" + "=" * 78 + "\nREPRESENTATION STABILITY of Z_loc (mean per-column corr on validation)\n" + "=" * 78)
    Z123, _, K123 = fit_Z(Xstd, ntr, None, 123, 8, all4)
    Z7, _, K7 = fit_Z(Xstd, ntr, None, 7, 8, all4)
    Z5y, _, _ = fit_Z(Xstd, ntr, 1260, 42, 8, all4)
    Z3y, _, _ = fit_Z(Xstd, ntr, 756, 42, 8, all4)
    Zsub, _, _ = fit_Z(Xstd, ntr, None, 42, 8, [1, 2, 3])  # drop spy_ret
    Zk12, _, Kk12 = fit_Z(Xstd, ntr, None, 42, 12, all4)
    stab = {
        "cross-seed 42~123": corr_cols(Z42, Z123, val),
        "cross-seed 42~7": corr_cols(Z42, Z7, val),
        "cross-window exp~5y": corr_cols(Z42, Z5y, val),
        "cross-window exp~3y": corr_cols(Z42, Z3y, val),
        "feature-subset drop spy_ret": corr_cols(Z42[:, 1:4], Zsub, val),
        "model-perturb K_max 8~12": corr_cols(Z42, Zk12, val),
    }
    for k, v in stab.items():
        print(f"  {k:<32}{v:+.3f}")
        rows.append(dict(cell=f"stability_{k}", incr=v))
    print(f"  (K_eff: seed42={K42} seed123={K123} seed7={K7} K_max12->{Kk12})")

    pd.DataFrame(rows).to_csv(os.path.join(RESULTS_DIR, "representation_information.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'representation_information.csv')}")


if __name__ == "__main__":
    main()
