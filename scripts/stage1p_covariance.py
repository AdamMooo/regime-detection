#!/usr/bin/env python3
"""STAGE-1' frozen test — .planning/COVARIANCE-CONDITIONING-PREREG.md.

Does an observable NON-volatility coordinate (absorption ratio primary) improve OOS covariance estimation
and portfolio risk beyond a MATCHED volatility-only similarity-weighted estimator?
PRIMARY: T vs B_match on (M1) GMV realized vol net 3bps and (M2) covariance forecast loss.
Closure is scoped to THIS approach/universe/features/architecture (see prereg). Frozen; no post-hoc search.
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

TICKERS = ["SPY","IWD","IWF","IWM","IEF","TLT","SHY","LQD","HYG","GLD","DBC","VNQ","EFA"]
CACHE = os.path.join(DATA_DIR, "processed", "stage1p_etf.csv")
TAU_SIM, H_BW, SHRINK = 126.0, 1.0, 0.2
REB = 21
RNG = np.random.default_rng(0)


def load_prices():
    if os.path.exists(CACHE):
        px = pd.read_csv(CACHE, parse_dates=["Date"]).set_index("Date")
        if list(px.columns) == TICKERS and len(px) > 3000:
            print(f"loaded cache {CACHE} ({px.index[0].date()}..{px.index[-1].date()}, N={len(px)})")
            return px
    import yfinance as yf
    df = yf.download(TICKERS, start="2007-01-01", auto_adjust=True, progress=False)["Close"][TICKERS]
    df = df.dropna()
    df.index.name = "Date"; df.to_csv(CACHE)
    print(f"downloaded {len(df)} rows ({df.index[0].date()}..{df.index[-1].date()})")
    return df


def zexp(s, mp=252):
    return ((s - s.expanding(mp).mean()) / s.expanding(mp).std())


def phase_rand(x):
    x = np.nan_to_num(x - np.nanmean(x)); F = np.fft.rfft(x)
    ph = np.exp(1j * RNG.uniform(0, 2*np.pi, len(F))); ph[0] = 1
    if len(x) % 2 == 0: ph[-1] = 1
    return np.fft.irfft(F*ph, n=len(x))


def shrink_cc(S):
    d = np.sqrt(np.diag(S)); R = S/np.outer(d, d); np.fill_diagonal(R, 1.0)
    rbar = (R.sum()-len(R))/(len(R)*(len(R)-1)); F = rbar*np.outer(d, d); np.fill_diagonal(F, d*d)
    Sh = SHRINK*F + (1-SHRINK)*S
    return Sh + 1e-4*np.mean(np.diag(Sh))*np.eye(len(Sh))   # ridge floor -> always PD/non-singular


def wcov(R, w):
    good = np.isfinite(R).all(1) & np.isfinite(w) & (w > 1e-12)
    Rh, wv = R[good], w[good]; wv = wv/wv.sum()
    mu = (wv[:, None]*Rh).sum(0); Rc = Rh - mu
    return shrink_cc((Rc*wv[:, None]).T @ Rc)


def est_cov(R, t, kind, states):
    idx = np.arange(0, t); dt = (t-idx).astype(float)
    if kind == "B0":
        w = (dt <= 252).astype(float)                         # equal-weight last 252
    elif kind == "B1":
        w = 0.94**dt                                          # EWMA lambda=0.94
    else:
        w = np.exp(-dt/TAU_SIM)
        cols = {"Bm": ["vol"], "Bp": ["vol", "placebo"], "T": ["vol", "ar"],
                "Tp": ["vol", "ar", "slope", "infl", "credit"]}[kind]
        d2 = np.zeros(len(idx))
        for c in cols:
            st = states[c]; d2 += ((st[idx]-st[t])/H_BW)**2
        w = w*np.exp(-0.5*d2)
    return wcov(R[idx], w)


def states_row(states, t):
    return np.array([states[c][t] for c in states])


def gmv_lo(S):
    n = len(S)
    r = minimize(lambda w: w@S@w, np.ones(n)/n, jac=lambda w: 2*S@w, method="SLSQP",
                 bounds=[(0, 1)]*n, constraints={"type": "eq", "fun": lambda w: w.sum()-1},
                 options={"maxiter": 200, "ftol": 1e-12})
    return r.x if r.success else np.ones(n)/n


def erc(S):
    n = len(S)
    r = minimize(lambda w: 0.5*w@S@w-(1/n)*np.sum(np.log(w)), 1/np.sqrt(np.diag(S)),
                 jac=lambda w: S@w-(1/n)/w, method="L-BFGS-B", bounds=[(1e-9, None)]*n)
    w = np.abs(r.x); return w/w.sum()


def qlik(Sig, RC):
    n = len(Sig); M = np.linalg.solve(Sig, RC+1e-8*np.eye(n)); s, ld = np.linalg.slogdet(M)
    return 0.5*(np.trace(M)-ld-n)


def cfrob(Sig, RC):
    def cc(S): d = np.sqrt(np.diag(S)); return S/np.outer(d, d)
    return np.linalg.norm(cc(Sig)-cc(RC), "fro")


def block_boot_ratio(a, b, reps=1000, blk=63):
    n = len(a); out = np.empty(reps)
    for r in range(reps):
        idx, i = [], RNG.integers(0, n)
        while len(idx) < n:
            L = RNG.geometric(1/blk); idx += [(i+j) % n for j in range(L)]; i = RNG.integers(0, n)
        idx = np.array(idx[:n]); out[r] = np.var(a[idx])/np.var(b[idx])
    return out


def main():
    px = load_prices()
    R = np.log(px).diff().values[1:]; dates = px.index[1:]
    A = R.shape[1]; N = len(R)
    ew = R.mean(1)
    vol = pd.Series(ew).rolling(63).std().values*np.sqrt(252)*100
    # absorption ratio: top-3 eigenvalue share of trailing 252d correlation
    ar = np.full(N, np.nan); k = max(1, round(0.2*A))
    for t in range(252, N):
        W = R[t-252:t]; C = np.corrcoef(W.T); ev = np.sort(np.linalg.eigvalsh(C))[::-1]
        ar[t] = ev[:k].sum()/ev.sum()
    mac = pd.read_csv(os.path.join(DATA_DIR, "processed", "histext_daily.csv"),
                      parse_dates=["Date"]).set_index("Date").reindex(px.index).ffill()
    states = {
        "vol": zexp(pd.Series(vol)).values,
        "ar": zexp(pd.Series(ar)).values,
        "placebo": zexp(pd.Series(phase_rand(np.nan_to_num(ar, nan=np.nanmean(ar))))).values,
        "slope": zexp(mac["slope"]).values[1:], "infl": zexp(mac["infl"]).values[1:],
        "credit": zexp(mac["credit"]).values[1:],
    }
    for c in states:  # pad/trim to N
        v = states[c]; states[c] = (v[:N] if len(v) >= N else np.concatenate([v, np.full(N-len(v), np.nan)]))

    burn = 504
    rebs = list(range(burn, N-REB, REB))
    kinds = ["B0", "B1", "Bm", "Bp", "T", "Tp"]
    spy, ief, tlt = TICKERS.index("SPY"), TICKERS.index("IEF"), TICKERS.index("TLT")

    net = {k: np.full(N, np.nan) for k in kinds}   # daily GMV net returns
    gross = {k: np.full(N, np.nan) for k in kinds}
    rp_net = {k: np.full(N, np.nan) for k in kinds}
    ql = {k: [] for k in kinds}; fr = {k: [] for k in kinds}
    hedge_red = {k: [] for k in kinds}; wprev = {k: None for k in kinds}; rpprev = {k: None for k in kinds}
    divr = {k: [] for k in kinds}
    C = 3e-4
    print(f"universe A={A}; OOS rebalances={len(rebs)} ({dates[rebs[0]].date()}..{dates[rebs[-1]].date()})")

    for t in rebs:
        hold = np.arange(t, min(t+REB, N)); RCf = np.cov(R[hold].T)
        for k in kinds:
            S = est_cov(R, t, k, states)
            w = gmv_lo(S)
            wr = erc(S) if k in ("Bm", "T") else None
            # turnover/cost
            wp = wprev[k]
            if wp is None: to = w.sum()
            else:
                drift = wp*(1+R[t-REB:t].sum(0) if t-REB >= 0 else wp); drift = drift/drift.sum() if wp is not None else wp
                to = np.abs(w-wp).sum()
            wprev[k] = w
            g = R[hold]@w; net[k][hold] = g; net[k][hold[0]] -= C*to; gross[k][hold] = g
            if wr is not None:
                if rpprev[k] is None: tor = wr.sum()
                else: tor = np.abs(wr-rpprev[k]).sum()
                rpprev[k] = wr; rn = R[hold]@wr; rn[0] -= C*tor; rp_net[k][hold] = rn
            ql[k].append(qlik(S, RCf)); fr[k].append(cfrob(S, RCf))
            # hedge: SPY hedged by IEF,TLT
            try:
                bi = [ief, tlt]; h = np.linalg.lstsq(S[np.ix_(bi, bi)], S[np.ix_(bi, [spy])], rcond=None)[0].ravel()
                hedged = R[hold][:, spy] - R[hold][:, bi]@h
                hedge_red[k].append(1 - np.var(hedged)/np.var(R[hold][:, spy]))
            except Exception:
                hedge_red[k].append(np.nan)
            # diversification ratio (realized on this block)
            sig = R[hold].std(0); pv = np.sqrt(w@np.cov(R[hold].T)@w)
            divr[k].append((w@sig)/pv if pv > 0 else np.nan)

    def annvol(x): x = x[np.isfinite(x)]; return np.std(x)*np.sqrt(252)*100
    def maxdd(x):
        x = x[np.isfinite(x)]; c = np.cumprod(1+x); return (c/np.maximum.accumulate(c)-1).min()*100

    print("\n" + "="*78 + "\nESTIMATOR LADDER — GMV long-only, net 3bps (context + primary)\n" + "="*78)
    print(f"  {'estimator':<10}{'realized vol%':>14}{'maxDD%':>10}{'mean QLIK':>12}{'corr-Frob':>11}{'hedgeRed':>10}{'divRatio':>10}{'degen%':>8}")
    for k in kinds:
        q = np.array(ql[k], float); f = np.array(fr[k], float); degen = 100*np.mean(~np.isfinite(q))
        print(f"  {k:<10}{annvol(net[k]):>14.3f}{maxdd(net[k]):>10.1f}{np.nanmean(q):>12.4f}"
              f"{np.nanmean(f):>11.4f}{np.nanmean(hedge_red[k]):>10.3f}{np.nanmean(divr[k]):>10.3f}{degen:>8.1f}")

    print("\n" + "="*78 + "\nPRIMARY: T vs B_match (matched vol-only). M1 portfolio + M2 forecast loss\n" + "="*78)
    a = net["T"][np.isfinite(net["T"]) & np.isfinite(net["Bm"])]; b = net["Bm"][np.isfinite(net["T"]) & np.isfinite(net["Bm"])]
    ratio = np.var(a)/np.var(b); boot = block_boot_ratio(a, b)
    print(f"  M1  Var(GMV_T)/Var(GMV_Bmatch) = {ratio:.4f}  90%CI [{np.percentile(boot,5):.4f},{np.percentile(boot,95):.4f}]  (support: <1, CI excl 1)")
    dq = np.array(ql["T"])-np.array(ql["Bm"]); dfrob = np.array(fr["T"])-np.array(fr["Bm"])
    dq = dq[np.isfinite(dq)]; dfrob = dfrob[np.isfinite(dfrob)]
    def bootdiff(x, reps=1000):
        n=len(x); o=np.empty(reps)
        for r in range(reps):
            idx=RNG.integers(0,n,n); o[r]=x[idx].mean()
        return o
    bq, bf = bootdiff(dq), bootdiff(dfrob)
    print(f"  M2  d QLIK(T-Bm)      = {dq.mean():+.4f}  90%CI [{np.percentile(bq,5):+.4f},{np.percentile(bq,95):+.4f}]  (support: <0)")
    print(f"  M2  d corrFrob(T-Bm)  = {dfrob.mean():+.4f}  90%CI [{np.percentile(bf,5):+.4f},{np.percentile(bf,95):+.4f}]  (support: <0)")
    print(f"  negative control T vs B_placebo: Var ratio = {np.var(net['T'][np.isfinite(net['T'])&np.isfinite(net['Bp'])])/np.var(net['Bp'][np.isfinite(net['T'])&np.isfinite(net['Bp'])]):.4f}")
    print(f"  architecture context B_match vs B1(EWMA): Var ratio = {np.var(net['Bm'][np.isfinite(net['Bm'])&np.isfinite(net['B1'])])/np.var(net['B1'][np.isfinite(net['Bm'])&np.isfinite(net['B1'])]):.4f}")

    print("\n" + "="*78 + "\nROBUSTNESS\n" + "="*78)
    # risk parity realized vol
    print(f"  risk-parity realized vol%:  T={annvol(rp_net['T']):.3f}  B_match={annvol(rp_net['Bm']):.3f}")
    # cost sensitivity (recompute net GMV from gross minus c*turnover already only at reb day -> approximate via ratios at c=0)
    a0 = gross["T"][np.isfinite(gross["T"])&np.isfinite(gross["Bm"])]; b0 = gross["Bm"][np.isfinite(gross["T"])&np.isfinite(gross["Bm"])]
    print(f"  cost=0bps  Var(GMV_T)/Var(GMV_Bmatch) (gross) = {np.var(a0)/np.var(b0):.4f}")
    # leave-one-crisis-out
    yrs = np.array([d.year for d in dates])
    for cr in (2008, 2020, 2022):
        m = np.isfinite(net["T"]) & np.isfinite(net["Bm"]) & (yrs != cr)
        print(f"  leave-out {cr}: Var(GMV_T)/Var(GMV_Bmatch) = {np.var(net['T'][m])/np.var(net['Bm'][m]):.4f}")
    # T+ combined conditioners
    m = np.isfinite(net["Tp"]) & np.isfinite(net["Bm"])
    print(f"  T+ (vol,ar,slope,infl,credit) vs B_match: Var ratio = {np.var(net['Tp'][m])/np.var(net['Bm'][m]):.4f}  "
          f"d QLIK={np.mean(np.array(ql['Tp'])-np.array(ql['Bm'])):+.4f}")

    pd.DataFrame([{"metric":"M1_var_ratio_T_Bm","value":ratio},{"metric":"M1_ci_lo","value":np.percentile(boot,5)},
                  {"metric":"M1_ci_hi","value":np.percentile(boot,95)},{"metric":"M2_dQLIK","value":dq.mean()},
                  {"metric":"M2_dcorrFrob","value":dfrob.mean()}]).to_csv(
                  os.path.join(RESULTS_DIR,"stage1p_covariance.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR,'stage1p_covariance.csv')}")


if __name__ == "__main__":
    main()
