#!/usr/bin/env python3
"""Corr-factor stage 2 — CONTEMPORANEOUS/incremental-information test (exploratory, disciplined).

Question: does the Kalman-filtered latent correlation state x_t add information about the
covariance structure the portfolio is exposed to TODAY (hold period t..t+21), beyond the
matched vol-only baseline? This deliberately reuses the stage1p_covariance.py architecture,
universe, metrics, costs, and inference byte-for-byte so the result is directly comparable
to the Chapter-3 covariance-conditioning null. Forecasting is NOT the lens here.

PRE-SPECIFIED before running (do not reinterpret after):
  Model A  = Bm  (similarity kernel, state=[vol])            -- unchanged stage1p baseline
  Model B  = SK  (state=[vol, kalman x_t])                   -- PRIMARY treatment
  Model C  = KO  (state=[x_t] only)                          -- diagnostic only
  Hierarchy (attribution if SK shows value): SR raw z(21d) -> SW rolling 252d -> SE EWMA(0.97) -> SK.
  Negative control: SP = [vol, phase-randomized surrogate of x_t].
  PRIMARY test: SK vs Bm on M1 (GMV net-3bps var ratio, block-boot 90% CI, support <1 excl 1)
  AND M2 (dQLIK + dcorrFrob, support <0 excl 0). Both required, same rule as the frozen prereg.
  Everything else is secondary/exploratory and labeled as such in output.

Causality: x_t built real-time — params (phi,q,r) refit on expanding window every 63d, filter
run forward, each segment records values under params fitted strictly before it. History before
the first refit is backfilled under first-fit params: at every decision date t >= burn those
values use only obs <= s (<= t) and params from data <= burn (<= t), i.e. inside t's info set.
All states expanding-z-scored (causal). Kalman core copied verbatim from corrfactor_stage1.py;
estimator/metric helpers copied verbatim from stage1p_covariance.py.
"""
from __future__ import annotations
import os, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from src.config import DATA_DIR, RESULTS_DIR

TICKERS = ["SPY", "IWD", "IWF", "IWM", "IEF", "TLT", "SHY", "LQD", "HYG", "GLD", "DBC", "VNQ", "EFA"]
CACHE = os.path.join(DATA_DIR, "processed", "stage1p_etf.csv")
TAU_SIM, H_BW, SHRINK = 126.0, 1.0, 0.2
REB, BURN, C = 21, 504, 3e-4
WIN, LAM_EWMA, REFIT_EVERY = 21, 0.97, 63
RNG = np.random.default_rng(0)

KINDS = ["B1", "Bm", "SR", "SW", "SE", "SK", "SP", "KO"]
COLS = {"Bm": ["vol"], "SR": ["vol", "zraw"], "SW": ["vol", "zroll"], "SE": ["vol", "zewma"],
        "SK": ["vol", "xkal"], "SP": ["vol", "plac"], "KO": ["xkal"]}


# ---------- helpers copied verbatim from stage1p_covariance.py ----------

def zexp(s, mp=252):
    return ((s - s.expanding(mp).mean()) / s.expanding(mp).std())


def phase_rand(x):
    x = np.nan_to_num(x - np.nanmean(x)); F = np.fft.rfft(x)
    ph = np.exp(1j * RNG.uniform(0, 2 * np.pi, len(F))); ph[0] = 1
    if len(x) % 2 == 0: ph[-1] = 1
    return np.fft.irfft(F * ph, n=len(x))


def shrink_cc(S):
    d = np.sqrt(np.diag(S)); R = S / np.outer(d, d); np.fill_diagonal(R, 1.0)
    rbar = (R.sum() - len(R)) / (len(R) * (len(R) - 1)); F = rbar * np.outer(d, d); np.fill_diagonal(F, d * d)
    Sh = SHRINK * F + (1 - SHRINK) * S
    return Sh + 1e-4 * np.mean(np.diag(Sh)) * np.eye(len(Sh))


def wcov(R, w):
    good = np.isfinite(R).all(1) & np.isfinite(w) & (w > 1e-12)
    Rh, wv = R[good], w[good]; wv = wv / wv.sum()
    mu = (wv[:, None] * Rh).sum(0); Rc = Rh - mu
    return shrink_cc((Rc * wv[:, None]).T @ Rc)


def est_cov(R, t, kind, states):
    idx = np.arange(0, t); dt = (t - idx).astype(float)
    if kind == "B1":
        w = 0.94 ** dt
    else:
        w = np.exp(-dt / TAU_SIM)
        d2 = np.zeros(len(idx))
        for c in COLS[kind]:
            st = states[c]; d2 += ((st[idx] - st[t]) / H_BW) ** 2
        w = w * np.exp(-0.5 * d2)
    return wcov(R[idx], w)


def gmv_lo(S):
    n = len(S)
    r = minimize(lambda w: w @ S @ w, np.ones(n) / n, jac=lambda w: 2 * S @ w, method="SLSQP",
                 bounds=[(0, 1)] * n, constraints={"type": "eq", "fun": lambda w: w.sum() - 1},
                 options={"maxiter": 200, "ftol": 1e-12})
    return r.x if r.success else np.ones(n) / n


def qlik(Sig, RC):
    n = len(Sig); M = np.linalg.solve(Sig, RC + 1e-8 * np.eye(n)); s, ld = np.linalg.slogdet(M)
    return 0.5 * (np.trace(M) - ld - n)


def cfrob(Sig, RC):
    def cc(S): d = np.sqrt(np.diag(S)); return S / np.outer(d, d)
    return np.linalg.norm(cc(Sig) - cc(RC), "fro")


def block_boot_ratio(a, b, reps=1000, blk=63):
    n = len(a); out = np.empty(reps)
    for r in range(reps):
        idx, i = [], RNG.integers(0, n)
        while len(idx) < n:
            L = RNG.geometric(1 / blk); idx += [(i + j) % n for j in range(L)]; i = RNG.integers(0, n)
        idx = np.array(idx[:n]); out[r] = np.var(a[idx]) / np.var(b[idx])
    return out


def bootdiff(x, reps=1000):
    n = len(x); o = np.empty(reps)
    for r in range(reps):
        idx = RNG.integers(0, n, n); o[r] = x[idx].mean()
    return o


# ---------- Kalman core copied verbatim from corrfactor_stage1.py ----------

def realized_corr_z(R, win=WIN):
    N, A = R.shape
    z = np.full(N, np.nan)
    for t in range(win, N):
        Cm = np.corrcoef(R[t - win:t].T)
        iu = np.triu_indices(A, 1)
        rho = np.clip(Cm[iu].mean(), -0.999, 0.999)
        z[t] = np.arctanh(rho)
    return z


def kalman_ll(params, z):
    phi = 1 / (1 + np.exp(-params[0]))
    q, robs = np.exp(params[1]), np.exp(params[2])
    x, P = z[0], 1.0
    ll = 0.0
    for t in range(1, len(z)):
        xp, Pp = phi * x, phi ** 2 * P + q
        S = Pp + robs
        innov = z[t] - xp
        ll += 0.5 * (np.log(2 * np.pi * S) + innov ** 2 / S)
        K = Pp / S
        x, P = xp + K * innov, (1 - K) * Pp
    return ll


def fit_kalman(z_train):
    r = minimize(kalman_ll, x0=[2.0, -3.0, -3.0], args=(z_train,), method="Nelder-Mead",
                 options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 2000})
    phi = 1 / (1 + np.exp(-r.x[0])); q, robs = np.exp(r.x[1]), np.exp(r.x[2])
    return phi, q, robs


def filter_full(z, phi, q, robs):
    N = len(z)
    x_filt = np.full(N, np.nan)
    t0 = np.where(np.isfinite(z))[0][0]
    x, P = z[t0], 1.0
    x_filt[t0] = x
    for t in range(t0 + 1, N):
        if not np.isfinite(z[t]):
            x_filt[t] = np.nan
            continue
        xp, Pp = phi * x, phi ** 2 * P + q
        K = Pp / (Pp + robs)
        x = xp + K * (z[t] - xp)
        P = (1 - K) * Pp
        x_filt[t] = x
    return x_filt


def realtime_kalman_state(z):
    """Real-time filtered state: params refit expanding every REFIT_EVERY days; each segment's
    values use params fitted strictly before the segment. Pre-BURN history backfilled under
    first-fit params (inside the info set of every decision date t >= BURN)."""
    N = len(z)
    valid0 = np.where(np.isfinite(z))[0][0]
    x_rt = np.full(N, np.nan)
    refits = list(range(BURN, N, REFIT_EVERY))
    fitlog = []
    for i, r0 in enumerate(refits):
        z_train = z[valid0:r0]; z_train = z_train[np.isfinite(z_train)]
        phi, q, robs = fit_kalman(z_train)
        fitlog.append((r0, phi, q, robs))
        seg_end = min(r0 + REFIT_EVERY, N)
        xf = filter_full(z[:seg_end], phi, q, robs)
        if i == 0:
            x_rt[:r0] = xf[:r0]
        x_rt[r0:seg_end] = xf[r0:seg_end]
        if (i + 1) % 10 == 0 or i == len(refits) - 1:
            print(f"  [kalman refit {i + 1}/{len(refits)}] phi={phi:.4f} q={q:.6f} r={robs:.6f}", flush=True)
    return x_rt, fitlog


# ---------- main ----------

def main():
    px = pd.read_csv(CACHE, parse_dates=["Date"]).set_index("Date")
    assert list(px.columns) == TICKERS and len(px) > 3000, "cache missing — run stage1p_covariance.py once"
    R = np.log(px).diff().values[1:]; dates = px.index[1:]
    A = R.shape[1]; N = len(R)
    print(f"universe A={A}  N={N}  {dates[0].date()}..{dates[-1].date()}")

    # --- state candidates (all causal) ---
    ew = R.mean(1)
    vol = pd.Series(ew).rolling(63).std().values * np.sqrt(252) * 100
    z_raw = realized_corr_z(R, WIN)
    z_roll = realized_corr_z(R, 252)
    valid0 = np.where(np.isfinite(z_raw))[0][0]
    z_ewma = np.full(N, np.nan); z_ewma[valid0] = z_raw[valid0]
    for t in range(valid0 + 1, N):
        z_ewma[t] = LAM_EWMA * z_ewma[t - 1] + (1 - LAM_EWMA) * z_raw[t] if np.isfinite(z_raw[t]) else z_ewma[t - 1]
    print("building real-time kalman state ...", flush=True)
    x_kal, fitlog = realtime_kalman_state(z_raw)
    # absorption ratio: prior chapter's coordinate, DIAGNOSTIC ONLY here (redundancy check)
    ar = np.full(N, np.nan); k3 = max(1, round(0.2 * A))
    for t in range(252, N):
        Cm = np.corrcoef(R[t - 252:t].T); evs = np.sort(np.linalg.eigvalsh(Cm))[::-1]
        ar[t] = evs[:k3].sum() / evs.sum()

    states = {
        "vol": zexp(pd.Series(vol)).values,
        "zraw": zexp(pd.Series(z_raw)).values,
        "zroll": zexp(pd.Series(z_roll)).values,
        "zewma": zexp(pd.Series(z_ewma)).values,
        "xkal": zexp(pd.Series(x_kal)).values,
        "plac": zexp(pd.Series(phase_rand(np.nan_to_num(x_kal, nan=np.nanmean(x_kal))))).values,
    }

    # --- redundancy diagnostics (descriptive, full-sample, labeled) ---
    print("\n" + "=" * 78 + "\nREDUNDANCY DIAGNOSTICS (descriptive)\n" + "=" * 78)
    diag = pd.DataFrame({"vol": states["vol"], "ar": zexp(pd.Series(ar)).values,
                         "zraw": states["zraw"], "zewma": states["zewma"], "xkal": states["xkal"]})
    print("state correlation matrix (daily, full sample):")
    print(diag.corr().round(3).to_string())
    dk = (diag["xkal"] - diag["zewma"]).abs()
    print(f"corr(xkal, zewma) = {diag['xkal'].corr(diag['zewma']):.4f}   mean|xkal - zewma| (z-units) = {dk.mean():.4f}")

    # --- OOS loop, identical structure to stage1p ---
    rebs = list(range(BURN, N - REB, REB))
    print(f"\nOOS rebalances={len(rebs)} ({dates[rebs[0]].date()}..{dates[rebs[-1]].date()})")
    net = {k: np.full(N, np.nan) for k in KINDS}
    gross = {k: np.full(N, np.nan) for k in KINDS}
    ql = {k: [] for k in KINDS}; fr = {k: [] for k in KINDS}
    hedge_red = {k: [] for k in KINDS}; divr = {k: [] for k in KINDS}
    tos = {k: [] for k in KINDS}; wprev = {k: None for k in KINDS}
    spy, ief, tlt = TICKERS.index("SPY"), TICKERS.index("IEF"), TICKERS.index("TLT")

    for t in rebs:
        hold = np.arange(t, min(t + REB, N)); RCf = np.cov(R[hold].T)
        for k in KINDS:
            S = est_cov(R, t, k, states)
            w = gmv_lo(S)
            wp = wprev[k]
            to = w.sum() if wp is None else np.abs(w - wp).sum()
            wprev[k] = w; tos[k].append(to)
            g = R[hold] @ w; gross[k][hold] = g
            net[k][hold] = g; net[k][hold[0]] -= C * to
            ql[k].append(qlik(S, RCf)); fr[k].append(cfrob(S, RCf))
            try:
                bi = [ief, tlt]; h = np.linalg.lstsq(S[np.ix_(bi, bi)], S[np.ix_(bi, [spy])], rcond=None)[0].ravel()
                hedged = R[hold][:, spy] - R[hold][:, bi] @ h
                hedge_red[k].append(1 - np.var(hedged) / np.var(R[hold][:, spy]))
            except Exception:
                hedge_red[k].append(np.nan)
            sig = R[hold].std(0); pv = np.sqrt(w @ np.cov(R[hold].T) @ w)
            divr[k].append((w @ sig) / pv if pv > 0 else np.nan)

    def annvol(x): x = x[np.isfinite(x)]; return np.std(x) * np.sqrt(252) * 100
    def maxdd(x):
        x = x[np.isfinite(x)]; c = np.cumprod(1 + x); return (c / np.maximum.accumulate(c) - 1).min() * 100

    print("\n" + "=" * 78 + "\nESTIMATOR LADDER — GMV long-only, net 3bps\n" + "=" * 78)
    print(f"  {'kind':<6}{'state':<22}{'vol%':>8}{'maxDD%':>9}{'QLIK':>10}{'corrFrob':>10}{'hedgeRed':>10}{'divR':>7}{'turnover':>9}")
    labels = {"B1": "EWMA0.94 (context)", "Bm": "vol only (MODEL A)", "SR": "vol+raw z21",
              "SW": "vol+roll252", "SE": "vol+EWMA0.97", "SK": "vol+KALMAN (MODEL B)",
              "SP": "vol+placebo (ctrl)", "KO": "kalman only (MODEL C)"}
    for k in KINDS:
        q = np.array(ql[k], float)
        print(f"  {k:<6}{labels[k]:<22}{annvol(net[k]):>8.3f}{maxdd(net[k]):>9.1f}{np.nanmean(q):>10.4f}"
              f"{np.nanmean(fr[k]):>10.4f}{np.nanmean(hedge_red[k]):>10.3f}{np.nanmean(divr[k]):>7.3f}"
              f"{np.mean(tos[k]):>9.3f}")

    def compare(kA, kB, label, full=False):
        """kB vs kA: M1 var ratio (net, <1 = kB better) + M2 loss diffs (<0 = kB better)."""
        m = np.isfinite(net[kA]) & np.isfinite(net[kB])
        ratio = np.var(net[kB][m]) / np.var(net[kA][m])
        line = f"  {label:<44} M1={ratio:.4f}"
        if full:
            boot = block_boot_ratio(net[kB][m], net[kA][m])
            line += f" CI[{np.percentile(boot, 5):.4f},{np.percentile(boot, 95):.4f}]"
        dq = np.array(ql[kB]) - np.array(ql[kA]); dq = dq[np.isfinite(dq)]
        df_ = np.array(fr[kB]) - np.array(fr[kA]); df_ = df_[np.isfinite(df_)]
        line += f"  dQLIK={dq.mean():+.4f}"
        if full:
            bq = bootdiff(dq); line += f" CI[{np.percentile(bq, 5):+.4f},{np.percentile(bq, 95):+.4f}]"
        line += f"  dFrob={df_.mean():+.4f}"
        if full:
            bf = bootdiff(df_); line += f" CI[{np.percentile(bf, 5):+.4f},{np.percentile(bf, 95):+.4f}]"
        print(line)
        return ratio, dq.mean(), df_.mean()

    print("\n" + "=" * 78 + "\nPRIMARY: SK (vol+kalman) vs Bm (vol only) — support needs BOTH M1<1 & M2<0, CIs clear\n" + "=" * 78)
    r_sk, dq_sk, df_sk = compare("Bm", "SK", "SK vs Bm  [PRIMARY]", full=True)

    print("\nSECONDARY — attribution hierarchy (raw -> rolling -> EWMA -> Kalman), each vs Bm:")
    for k in ("SR", "SW", "SE"):
        compare("Bm", k, f"{k} ({labels[k]}) vs Bm")
    print("\nCONTROLS / DIAGNOSTICS:")
    compare("Bm", "SP", "SP placebo vs Bm (extra-dim artifact control)")
    compare("Bm", "KO", "KO state-only vs Bm (diagnostic)")
    compare("B1", "Bm", "Bm vs B1 (architecture context)")

    # --- exploratory: residual/incremental information (Approach 4, descriptive) ---
    print("\n" + "=" * 78 + "\nEXPLORATORY (descriptive, full-sample): partial corr of x_t with hold-period corr\n" + "=" * 78)
    iu = np.triu_indices(A, 1)
    tgt = np.full(len(rebs), np.nan)
    for i, t in enumerate(rebs):
        hold = np.arange(t, min(t + REB, N))
        Cm = np.corrcoef(R[hold].T)
        tgt[i] = np.arctanh(np.clip(Cm[iu].mean(), -0.999, 0.999))
    Xb = np.column_stack([states["vol"][rebs], states["zraw"][rebs]])
    xk = states["xkal"][rebs]
    okm = np.isfinite(tgt) & np.isfinite(Xb).all(1) & np.isfinite(xk)
    Xb1 = np.column_stack([np.ones(okm.sum()), Xb[okm]])
    beta_t = np.linalg.lstsq(Xb1, tgt[okm], rcond=None)[0]
    beta_x = np.linalg.lstsq(Xb1, xk[okm], rcond=None)[0]
    res_t = tgt[okm] - Xb1 @ beta_t
    res_x = xk[okm] - Xb1 @ beta_x
    pc = np.corrcoef(res_t, res_x)[0, 1]
    prods = res_t * res_x / (res_t.std() * res_x.std())
    bpc = bootdiff(prods)
    print(f"  partial corr(x_t, hold-corr | vol, raw z) = {pc:+.4f}  90% CI [{np.percentile(bpc, 5):+.4f},"
          f" {np.percentile(bpc, 95):+.4f}]   raw corr(x_t, hold-corr) = {np.corrcoef(xk[okm], tgt[okm])[0, 1]:+.4f}")

    # --- subperiod stability of the primary ---
    print("\n" + "=" * 78 + "\nSUBPERIOD STABILITY of SK vs Bm\n" + "=" * 78)
    yrs = np.array([d.year for d in dates])
    m0 = np.isfinite(net["SK"]) & np.isfinite(net["Bm"])
    for cr in (2008, 2020, 2022):
        m = m0 & (yrs != cr)
        print(f"  leave-out {cr}:  M1 = {np.var(net['SK'][m]) / np.var(net['Bm'][m]):.4f}")
    days = np.where(m0)[0]; half = days[len(days) // 2]
    for lab, m in (("early half", m0 & (np.arange(N) < half)), ("late half", m0 & (np.arange(N) >= half))):
        print(f"  {lab}:  M1 = {np.var(net['SK'][m]) / np.var(net['Bm'][m]):.4f}")
    reb_arr = np.array(rebs)
    volmed = np.nanmedian(states["vol"][reb_arr]); cormed = np.nanmedian(states["zraw"][reb_arr])
    qd = np.array(ql["SK"]) - np.array(ql["Bm"])
    for lab, mm in (("high-vol rebs", states["vol"][reb_arr] > volmed), ("low-vol rebs", states["vol"][reb_arr] <= volmed),
                    ("high-corr rebs", states["zraw"][reb_arr] > cormed), ("low-corr rebs", states["zraw"][reb_arr] <= cormed)):
        print(f"  {lab}:  dQLIK = {np.nanmean(qd[mm]):+.4f}")
    print(f"  cost=0 (gross):  M1 = {np.var(gross['SK'][m0]) / np.var(gross['Bm'][m0]):.4f}")

    phis = [f[1] for f in fitlog]
    print(f"\nkalman params: phi mean={np.mean(phis):.4f} min={np.min(phis):.4f} max={np.max(phis):.4f}  refits={len(fitlog)}")

    pd.DataFrame([{"metric": "M1_var_ratio_SK_Bm", "value": r_sk},
                  {"metric": "M2_dQLIK_SK_Bm", "value": dq_sk},
                  {"metric": "M2_dcorrFrob_SK_Bm", "value": df_sk},
                  {"metric": "partial_corr_x_given_baseline", "value": pc},
                  {"metric": "corr_xkal_zewma", "value": diag['xkal'].corr(diag['zewma'])}]).to_csv(
                  os.path.join(RESULTS_DIR, "corrfactor_stage2.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'corrfactor_stage2.csv')}")


if __name__ == "__main__":
    main()
