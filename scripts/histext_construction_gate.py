#!/usr/bin/env python3
"""STAGE-1 Case-E gate: does a synthetic constant-maturity 10y par-bond TOTAL RETURN
reproduce the ETF-based stock-bond correlation over the overlap?

Frozen tolerances (.planning/STOCKBOND-MACRO-PREREG.md sec 2/12):
  PASS iff corr(rho_synth, rho_IEF) >= 0.90 AND mean|rho_synth - rho_IEF| <= 0.10.
Also reports the -dy corroborator fidelity (needs no TR construction).

This is a construction-validity check only. It does NOT run the macro/rates test.
Reads yfinance (SPY, IEF, TLT, ^TNX); falls back to data/processed/cross_asset.csv for
the ETFs if the network is unavailable (still needs ^TNX).
Writes: results/histext_construction_gate.csv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import DATA_DIR, RESULTS_DIR

H = 63
T = 10          # constant maturity (years)
START = "2002-07-30"   # IEF/TLT inception


def parbond_price(coupon_rate, ytm, T=T, freq=2):
    n = T * freq
    c = coupon_rate / freq * 100.0
    i = ytm / freq
    return c * (1 - (1 + i) ** (-n)) / i + 100.0 * (1 + i) ** (-n)


def synth_tr(y):
    """Daily total return of a rolling constant-maturity 10y par bond (exact repricing)."""
    tr = np.full(len(y), np.nan)
    for t in range(1, len(y)):
        P = parbond_price(y[t - 1], y[t])          # reprice yesterday's par bond at today's yield
        tr[t] = (P - 100.0) / 100.0 + y[t - 1] / 252.0
    return tr


def load_data():
    try:
        import yfinance as yf
        df = yf.download(["SPY", "IEF", "TLT", "^TNX"], start=START, auto_adjust=True, progress=False)
        close = df["Close"].dropna(how="all")
        if close[["SPY", "IEF", "TLT", "^TNX"]].dropna().shape[0] > 500:
            print(f"yfinance: {close.dropna().shape[0]} aligned rows "
                  f"({close.dropna().index[0].date()}..{close.dropna().index[-1].date()})")
            return close[["SPY", "IEF", "TLT", "^TNX"]]
        raise RuntimeError("insufficient yfinance rows")
    except Exception as e:
        print(f"yfinance path failed ({e}); trying cross_asset.csv + ^TNX only")
        ca = pd.read_csv(os.path.join(DATA_DIR, "processed", "cross_asset.csv"),
                         parse_dates=["Date"]).set_index("Date")[["SPY", "IEF", "TLT"]]
        import yfinance as yf
        tnx = yf.download("^TNX", start=str(ca.index[0].date()), auto_adjust=True, progress=False)["Close"]
        tnx.name = "^TNX"
        out = ca.join(tnx, how="inner").dropna()
        print(f"fallback: {len(out)} aligned rows ({out.index[0].date()}..{out.index[-1].date()})")
        return out


def roll_corr(a, b, h):
    return pd.Series(a).rolling(h).corr(pd.Series(b)).values


def main():
    data = load_data().dropna()
    y = data["^TNX"].values.astype(float)
    if np.nanmedian(y) > 25:          # older ^TNX scale (x10)
        y = y / 10.0
    y = y / 100.0                     # percent -> decimal

    spy_r = np.log(data["SPY"]).diff().values
    ief_r = np.log(data["IEF"]).diff().values
    tlt_r = np.log(data["TLT"]).diff().values
    synth_r = synth_tr(y)
    negdy = -np.diff(y, prepend=np.nan)   # -dy corroborator (bond price ~ -D*dy)

    print(f"\nmean daily corr(SPY,·) contemporaneous (full overlap):")
    for nm, r in (("synth10yTR", synth_r), ("IEF", ief_r), ("TLT", tlt_r), ("-dy", negdy)):
        m = np.isfinite(spy_r) & np.isfinite(r)
        print(f"   SPY~{nm:<10} {np.corrcoef(spy_r[m], r[m])[0,1]:+.3f}")

    rc = {nm: roll_corr(spy_r, r, H) for nm, r in
          (("synth", synth_r), ("IEF", ief_r), ("TLT", tlt_r), ("negdy", negdy))}
    dates = data.index

    # year-by-year rolling corr (confirm the sign flip is reproduced)
    print(f"\nmean forward-ish rolling-{H}d corr by year  (synth vs IEF vs TLT):")
    yrs = np.array([d.year for d in dates])
    for yr in sorted(set(yrs)):
        m = (yrs == yr) & np.isfinite(rc["synth"]) & np.isfinite(rc["IEF"])
        if m.sum() > 40:
            print(f"   {yr}: synth={np.nanmean(rc['synth'][m]):+.2f}  "
                  f"IEF={np.nanmean(rc['IEF'][m]):+.2f}  TLT={np.nanmean(rc['TLT'][m]):+.2f}")

    # fidelity vs IEF (frozen gate) and vs TLT / -dy
    def fidelity(a, b):
        m = np.isfinite(a) & np.isfinite(b)
        return np.corrcoef(a[m], b[m])[0, 1], float(np.mean(np.abs(a[m] - b[m])))

    c_ief, mad_ief = fidelity(rc["synth"], rc["IEF"])
    c_tlt, mad_tlt = fidelity(rc["synth"], rc["TLT"])
    c_ndy, mad_ndy = fidelity(rc["synth"], rc["negdy"])

    print("\n" + "=" * 66)
    print("CASE-E CONSTRUCTION GATE  (frozen: corr>=0.90 AND mean|drho|<=0.10 vs IEF)")
    print("=" * 66)
    print(f"  rho_synth vs rho_IEF : corr={c_ief:+.3f}  mean|drho|={mad_ief:.3f}")
    print(f"  rho_synth vs rho_TLT : corr={c_tlt:+.3f}  mean|drho|={mad_tlt:.3f}")
    print(f"  rho_synth vs rho_-dy : corr={c_ndy:+.3f}  mean|drho|={mad_ndy:.3f}  (construction-free check)")
    passed = (c_ief >= 0.90) and (mad_ief <= 0.10)
    print(f"\n  GATE: {'PASS -- construction valid, proceed to build historical dataset' if passed else 'FAIL -- Case E: do not build economic claim on this target'}")

    pd.DataFrame([{"pair": "synth~IEF", "corr": c_ief, "mad": mad_ief},
                  {"pair": "synth~TLT", "corr": c_tlt, "mad": mad_tlt},
                  {"pair": "synth~negdy", "corr": c_ndy, "mad": mad_ndy},
                  {"pair": "GATE_PASS", "corr": float(passed), "mad": np.nan}]
                 ).to_csv(os.path.join(RESULTS_DIR, "histext_construction_gate.csv"), index=False)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'histext_construction_gate.csv')}")


if __name__ == "__main__":
    main()
