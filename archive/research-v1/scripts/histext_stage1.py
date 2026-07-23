#!/usr/bin/env python3
"""STAGE-1 frozen test battery (.planning/STOCKBOND-MACRO-PREREG.md). Reads histext_daily.csv.

Primary: dR2_OOS(D-C) for forward-63d corr(SPX, synthetic 10y par-bond TR), rolling-origin expanding OOS,
annual refit, 40% burn-in. C = flexible spline(stress {rv21,rv63,nfci,credit}) + ridge; D = C + macro
{slope,infl}. Primary criterion dR2>0 with block-bootstrap CI + leave-one-regime-out. Plus: sign test,
alt vol proxies, detrend/turning-point, coefficient/direction + calibration stability, maturity
robustness, -dy corroborator. Classifies Case A-E. Thresholds/hypothesis FROZEN.
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV, LogisticRegression
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from src.config import DATA_DIR, RESULTS_DIR

ALPHAS = np.logspace(-3, 4, 20)
H = 63
STRESS = ["rv21", "rv63", "nfci", "credit"]
MACRO = ["slope", "infl"]
RNG = np.random.default_rng(0)
BURN = 0.40


def fwd_corr(a, b, h=H):
    a, b = np.asarray(a, float), np.asarray(b, float)
    out = np.full(len(a), np.nan)
    for t in range(len(a) - h):
        x, y = a[t + 1:t + 1 + h], b[t + 1:t + 1 + h]
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() >= int(0.8 * h):
            out[t] = np.corrcoef(x[m], y[m])[0, 1]
    return out


def r2(y, p):
    return 1.0 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)


def build_X(kind, Ss, Ms, spline):
    if kind == "A":
        return Ss
    if kind == "B":
        return np.hstack([Ss, Ss ** 2])
    if kind == "C":
        return spline.transform(Ss)
    if kind == "D":
        return np.hstack([spline.transform(Ss), Ms])


def rolling_oos(S, M, y, kinds, extra_train=None):
    """Expanding-window rolling-origin OOS predictions for each model kind.
    extra_train: optional boolean mask of rows ALLOWED in training (for leave-one-regime-out)."""
    ok = np.isfinite(y) & np.all(np.isfinite(S), 1) & np.all(np.isfinite(M), 1)
    idx = np.where(ok)[0]
    n = len(idx)
    burn = int(BURN * n)
    # annual refit points (every ~252 valid obs)
    refits = list(range(burn, n, 252)) + [n]
    preds = {k: np.full(len(y), np.nan) for k in kinds}
    pos = {g: i for i, g in enumerate(idx)}
    for r in range(len(refits) - 1):
        R, Rn = refits[r], refits[r + 1]
        tr_local = idx[:R]
        # target realized by R: t + H < global index of R-th valid row
        gR = idx[R]
        tr_local = tr_local[(tr_local + H < gR)]
        if extra_train is not None:
            tr_local = tr_local[extra_train[tr_local]]
        te_local = idx[R:Rn]
        if len(tr_local) < 300 or len(te_local) == 0:
            continue
        sc_s, sc_m = StandardScaler().fit(S[tr_local]), StandardScaler().fit(M[tr_local])
        Ss_tr, Ms_tr = sc_s.transform(S[tr_local]), sc_m.transform(M[tr_local])
        Ss_te, Ms_te = sc_s.transform(S[te_local]), sc_m.transform(M[te_local])
        spline = SplineTransformer(n_knots=4, degree=3, knots="quantile",
                                   extrapolation="linear").fit(Ss_tr)
        for k in kinds:
            Xtr = build_X(k, Ss_tr, Ms_tr, spline)
            Xte = build_X(k, Ss_te, Ms_te, spline)
            m = RidgeCV(alphas=ALPHAS).fit(Xtr, y[tr_local])
            preds[k][te_local] = m.predict(Xte)
    return preds, ok


def eval_pair(preds, y, mask):
    m = mask & np.isfinite(preds["C"]) & np.isfinite(preds["D"]) & np.isfinite(y)
    yv = y[m]
    return r2(yv, preds["C"][m]), r2(yv, preds["D"][m]), m


def stationary_block_boot(y, pc, pd_, reps=1000, meanblock=126):
    n = len(y)
    out = np.empty(reps)
    p = 1.0 / meanblock
    for b in range(reps):
        idx, i = [], RNG.integers(0, n)
        while len(idx) < n:
            idx.append(i)
            i = RNG.integers(0, n) if RNG.random() < p else (i + 1) % n
        idx = np.array(idx[:n])
        out[b] = r2(y[idx], pd_[idx]) - r2(y[idx], pc[idx])
    return out


def main():
    df = pd.read_csv(os.path.join(DATA_DIR, "processed", "histext_daily.csv"),
                     parse_dates=["Date"]).set_index("Date")
    dates = df.index
    S = df[STRESS].values
    M = df[MACRO].values
    spy = df["spy_ret"].values
    yr = np.array([d.year for d in dates])
    # regimes: R1 positive pre-2000, R2 negative 2000-2021, R3 positive 2022+
    reg = np.where(yr < 2000, 1, np.where(yr <= 2021, 2, 3))

    tgt = {"rho10_h63": fwd_corr(spy, df["tr10"].values, 63)}

    print("=" * 78)
    print("PRIMARY: dR2_OOS(D-C), fwd63d corr(SPX,10y TR), rolling-origin expanding OOS")
    print("=" * 78)
    preds, ok = rolling_oos(S, M, tgt["rho10_h63"], ["A", "B", "C", "D"])
    y = tgt["rho10_h63"]
    mask = ok & np.isfinite(preds["C"]) & np.isfinite(preds["D"])
    yv = y[mask]
    r2A = r2(yv, preds["A"][mask]); r2B = r2(yv, preds["B"][mask])
    r2C = r2(yv, preds["C"][mask]); r2D = r2(yv, preds["D"][mask])
    print(f"  OOS points N={mask.sum()} ({dates[mask][0].date()}..{dates[mask][-1].date()})")
    print(f"  R2_OOS  A(lin stress)={r2A:+.4f}  B(+sq)={r2B:+.4f}  C(spline stress)={r2C:+.4f}  D(C+macro)={r2D:+.4f}")
    print(f"  PRIMARY dR2_OOS(D-C) = {r2D - r2C:+.4f}   [primary criterion: >0 with CI excl 0 + LOTO]")
    boot = stationary_block_boot(yv, preds["C"][mask], preds["D"][mask])
    print(f"  block-bootstrap 90% CI = [{np.percentile(boot,5):+.4f}, {np.percentile(boot,95):+.4f}]  "
          f"(P(dR2>0)={np.mean(boot>0):.2f})")

    # leave-one-regime-out (pooled) + per-regime
    print("\n  Leave-one-regime-out (pooled dR2 with that regime's OOS points removed) + per-regime dR2:")
    for g, nm in [(1, "R1 pos pre-2000"), (2, "R2 neg 2000-2021"), (3, "R3 pos 2022+")]:
        mm = mask & (reg == g)
        if mm.sum() > 30:
            drin = r2(y[mm], preds["D"][mm]) - r2(y[mm], preds["C"][mm])
        else:
            drin = np.nan
        mo = mask & (reg != g)
        drout = r2(y[mo], preds["D"][mo]) - r2(y[mo], preds["C"][mo])
        print(f"    {nm:<20} per-regime dR2={drin:+.4f} (n={int(mm.sum())})   leave-it-out pooled dR2={drout:+.4f}")

    # ---- SECONDARY: sign prediction ----
    print("\n" + "=" * 78 + "\nSECONDARY: sign prediction  I(rho>0)   C vs C+macro (logistic, rolling-origin)\n" + "=" * 78)
    sign_preds = sign_rolling(S, M, y)
    ms = ok & np.isfinite(sign_preds["C"]) & np.isfinite(sign_preds["D"]) & np.isfinite(y)
    yb = (y[ms] > 0).astype(int)
    if len(set(yb)) == 2:
        for k in ("C", "D"):
            pk = np.clip(sign_preds[k][ms], 1e-6, 1 - 1e-6)
            print(f"  {k}: AUC={roc_auc_score(yb,pk):.3f}  logloss={log_loss(yb,pk):.4f}  Brier={brier_score_loss(yb,pk):.4f}")
        pc = np.clip(sign_preds['C'][ms],1e-6,1-1e-6); pdd=np.clip(sign_preds['D'][ms],1e-6,1-1e-6)
        print(f"  dAUC(D-C)={roc_auc_score(yb,pdd)-roc_auc_score(yb,pc):+.3f}  "
              f"dBrier(C-D, +=better)={brier_score_loss(yb,pc)-brier_score_loss(yb,pdd):+.4f}")

    # ---- alt vol proxies ----
    print("\n" + "=" * 78 + "\nALT VOL PROXIES: does the macro increment survive a different stress control?\n" + "=" * 78)
    ewm = pd.Series(spy, index=dates).pow(2).ewm(span=33).mean().pow(0.5).values * np.sqrt(252) * 100  # ~RiskMetrics
    proxies = {
        "RV63-only": df[["rv63"]].values,
        "EWMA-vol": ewm.reshape(-1, 1),
        "full{rv21,rv63,nfci,credit}(primary)": S,
        "VIX(1990+ overlap)": df[["vix"]].values,
    }
    for nm, Sx in proxies.items():
        sub = np.isfinite(Sx).all(1)
        pr, okx = rolling_oos(Sx, M, y, ["C", "D"])
        mm = okx & np.isfinite(pr["C"]) & np.isfinite(pr["D"])
        if mm.sum() > 200:
            print(f"  stress={nm:<38} dR2(D-C)={r2(y[mm],pr['D'][mm])-r2(y[mm],pr['C'][mm]):+.4f}  (N={int(mm.sum())})")

    # ---- detrend + turning-point ----
    print("\n" + "=" * 78 + "\nDETREND + TURNING-POINT\n" + "=" * 78)
    tindex = (np.arange(len(df)) / len(df)).reshape(-1, 1)
    Sd = np.hstack([S, tindex])   # add time trend to the stress/control block
    prd, okd = rolling_oos(Sd, M, y, ["C", "D"])
    md = okd & np.isfinite(prd["C"]) & np.isfinite(prd["D"])
    print(f"  with linear time trend in control: dR2(D-C)={r2(y[md],prd['D'][md])-r2(y[md],prd['C'][md]):+.4f}")
    # turning points: +-1yr around the two major transitions
    tp = ((dates >= "1998-06-01") & (dates <= "2001-06-01")) | ((dates >= "2021-06-01") & (dates <= "2023-06-01"))
    mtp = mask & tp
    print(f"  near the 2 major transitions (+-~1.5y): dR2(D-C)={r2(y[mtp],preds['D'][mtp])-r2(y[mtp],preds['C'][mtp]):+.4f} (n={int(mtp.sum())})")

    # ---- coefficient / direction stability (standardized macro coef of D per regime) ----
    print("\n" + "=" * 78 + "\nCOEFFICIENT / DIRECTION STABILITY (standardized macro effect, per regime)\n" + "=" * 78)
    for g, nm in [(1, "R1 pos"), (2, "R2 neg"), (3, "R3 pos"), (0, "ALL")]:
        m = ok & ((reg == g) if g else np.ones(len(y), bool)) & np.isfinite(y)
        if m.sum() < 100:
            continue
        sc_s, sc_m = StandardScaler().fit(S[m]), StandardScaler().fit(M[m])
        sp = SplineTransformer(n_knots=4, degree=3, knots="quantile", extrapolation="linear").fit(sc_s.transform(S[m]))
        Xd = np.hstack([sp.transform(sc_s.transform(S[m])), sc_m.transform(M[m])])
        mdl = RidgeCV(alphas=ALPHAS).fit(Xd, y[m])
        cs, ci = mdl.coef_[-2], mdl.coef_[-1]
        print(f"    {nm:<8} slope_coef={cs:+.3f}  infl_coef={ci:+.3f}  (std units; sign=direction)")

    # ---- calibration stability (per regime, OOS) ----
    print("\n" + "=" * 78 + "\nCALIBRATION STABILITY (per regime, OOS predicted vs realized)\n" + "=" * 78)
    for g, nm in [(1, "R1 pos"), (2, "R2 neg"), (3, "R3 pos")]:
        mm = mask & (reg == g)
        if mm.sum() > 30:
            print(f"    {nm:<8} mean_realized={y[mm].mean():+.2f} mean_predD={preds['D'][mm].mean():+.2f} "
                  f"R2_D={r2(y[mm],preds['D'][mm]):+.3f}")

    # ---- maturity robustness + horizon + -dy corroborator ----
    print("\n" + "=" * 78 + "\nMATURITY / HORIZON ROBUSTNESS + -dy CORROBORATOR   (dR2 D-C)\n" + "=" * 78)
    variants = {
        "rho2_h63": fwd_corr(spy, df["tr2"].values, 63),
        "rho5_h63": fwd_corr(spy, df["tr5"].values, 63),
        "rho30_h63": fwd_corr(spy, df["tr30"].values, 63),
        "rho10_h21": fwd_corr(spy, df["tr10"].values, 21),
        "rho10_h126": fwd_corr(spy, df["tr10"].values, 126),
        "rho_negdy_h63(corrob)": fwd_corr(spy, df["negdy10"].values, 63),
    }
    for nm, yy in variants.items():
        pr, okx = rolling_oos(S, M, yy, ["C", "D"])
        mm = okx & np.isfinite(pr["C"]) & np.isfinite(pr["D"]) & np.isfinite(yy)
        if mm.sum() > 200:
            print(f"  {nm:<24} dR2(D-C)={r2(yy[mm],pr['D'][mm])-r2(yy[mm],pr['C'][mm]):+.4f} (N={int(mm.sum())})")

    pd.DataFrame([{"metric": "primary_dR2_D_C", "value": r2D - r2C},
                  {"metric": "ci_lo", "value": np.percentile(boot, 5)},
                  {"metric": "ci_hi", "value": np.percentile(boot, 95)},
                  {"metric": "R2_C", "value": r2C}, {"metric": "R2_D", "value": r2D}]
                 ).to_csv(os.path.join(RESULTS_DIR, "histext_stage1.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR,'histext_stage1.csv')}")


def sign_rolling(S, M, y):
    ok = np.isfinite(y) & np.all(np.isfinite(S), 1) & np.all(np.isfinite(M), 1)
    idx = np.where(ok)[0]
    n = len(idx); burn = int(BURN * n)
    refits = list(range(burn, n, 252)) + [n]
    preds = {k: np.full(len(y), np.nan) for k in ("C", "D")}
    for r in range(len(refits) - 1):
        R, Rn = refits[r], refits[r + 1]
        gR = idx[R]
        tr = idx[:R]; tr = tr[tr + H < gR]
        te = idx[R:Rn]
        if len(tr) < 300 or len(te) == 0:
            continue
        yb = (y[tr] > 0).astype(int)
        if len(set(yb)) < 2:
            continue
        sc_s, sc_m = StandardScaler().fit(S[tr]), StandardScaler().fit(M[tr])
        sp = SplineTransformer(n_knots=4, degree=3, knots="quantile", extrapolation="linear").fit(sc_s.transform(S[tr]))
        Xc_tr = sp.transform(sc_s.transform(S[tr]))
        Xd_tr = np.hstack([Xc_tr, sc_m.transform(M[tr])])
        Xc_te = sp.transform(sc_s.transform(S[te]))
        Xd_te = np.hstack([Xc_te, sc_m.transform(M[te])])
        preds["C"][te] = LogisticRegression(C=1.0, max_iter=2000).fit(Xc_tr, yb).predict_proba(Xc_te)[:, 1]
        preds["D"][te] = LogisticRegression(C=1.0, max_iter=2000).fit(Xd_tr, yb).predict_proba(Xd_te)[:, 1]
    return preds


if __name__ == "__main__":
    main()
