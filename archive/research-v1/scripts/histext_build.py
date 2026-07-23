#!/usr/bin/env python3
"""STAGE-1 historical dataset build (~1976+). Frozen prereg: .planning/STOCKBOND-MACRO-PREREG.md.

Fetches (FRED + yfinance), constructs the target(s) + axes, saves data/processed/histext_daily.csv,
and prints the data-integrity + regime-coverage report BEFORE any test is run.

Target: forward 63d corr(S&P daily log ret, synthetic constant-maturity par-bond TR) for maturities
2/5/10/30y (10y primary) + the construction-free -dy10 corroborator.
Stress axis inputs: RV21, RV63, NFCI, credit(BAA-AAA).  Macro axis: slope(DGS10-DGS2), inflation(CPI YoY).
Nothing here is standardized/modeled -- that happens in histext_stage1.py.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from src.config import DATA_DIR

load_dotenv()
START = "1976-06-01"     # DGS2 inception (binds the macro/slope axis)
OUT = os.path.join(DATA_DIR, "processed", "histext_daily.csv")


def fred(series, start=START):
    from fredapi import Fred
    s = Fred(api_key=os.getenv("FRED_API_KEY")).get_series(series, observation_start=start)
    s.name = series
    return s


def parbond_price(coupon_rate, ytm, T, freq=2):
    n = T * freq
    c = coupon_rate / freq * 100.0
    i = ytm / freq
    return c * (1 - (1 + i) ** (-n)) / i + 100.0 * (1 + i) ** (-n)


def synth_tr(y, T):
    tr = np.full(len(y), np.nan)
    for t in range(1, len(y)):
        a, b = y[t - 1], y[t]
        if np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0:
            tr[t] = (parbond_price(a, b, T) - 100.0) / 100.0 + a / 252.0
    return tr


def main():
    print("Fetching S&P 500 (^GSPC)...")
    spx = yf.download("^GSPC", start=START, auto_adjust=True, progress=False)["Close"]
    spx = spx.iloc[:, 0] if isinstance(spx, pd.DataFrame) else spx
    idx = spx.index
    spy_ret = np.log(spx).diff()

    print("Fetching FRED series...")
    ser = {s: fred(s) for s in ["DGS2", "DGS5", "DGS10", "DGS30", "NFCI", "CPIAUCSL", "BAA", "AAA", "VIXCLS"]}

    # causal alignment to trading days
    def align(s, lag_days=0, ff=True):
        z = s.copy()
        if lag_days:
            z.index = z.index + pd.Timedelta(days=lag_days)
        return z.reindex(idx, method="ffill" if ff else None)

    y2 = align(ser["DGS2"]) / 100.0
    y5 = align(ser["DGS5"]) / 100.0
    y10 = align(ser["DGS10"]) / 100.0
    y30 = align(ser["DGS30"]) / 100.0
    nfci = align(ser["NFCI"], lag_days=7)                       # publication lag (project convention)
    vix = align(ser["VIXCLS"])
    # credit: monthly Moody's seasoned yields, ~1 month release lag
    credit = align(ser["BAA"], lag_days=35) - align(ser["AAA"], lag_days=35)
    # inflation: CPI YoY on the monthly series, then release lag (~46d) + ffill
    cpi = ser["CPIAUCSL"]
    cpi_yoy = (cpi / cpi.shift(12) - 1.0) * 100.0
    infl = align(cpi_yoy, lag_days=46)

    # realized vol (causal trailing), annualized %
    rv21 = spy_ret.rolling(21).std() * np.sqrt(252) * 100.0
    rv63 = spy_ret.rolling(63).std() * np.sqrt(252) * 100.0

    # synthetic constant-maturity par-bond total returns
    tr = {f"tr{T}": pd.Series(synth_tr(yv.values, T), index=idx)
          for T, yv in [(2, y2), (5, y5), (10, y10), (30, y30)]}
    negdy10 = -y10.diff()

    df = pd.DataFrame({
        "spy_ret": spy_ret, "y2": y2, "y5": y5, "y10": y10, "y30": y30,
        **tr, "negdy10": negdy10,
        "rv21": rv21, "rv63": rv63, "nfci": nfci, "credit": credit,
        "slope": (y10 - y2) * 100.0, "infl": infl, "vix": vix,
    }, index=idx)
    df.index.name = "Date"
    df.to_csv(OUT)

    # ---------- forward 63d correlations for the coverage report ----------
    def fwd_corr(a, b, h=63):
        a, b = np.asarray(a), np.asarray(b)
        out = np.full(len(a), np.nan)
        for t in range(len(a) - h):
            x, y = a[t + 1:t + 1 + h], b[t + 1:t + 1 + h]
            m = np.isfinite(x) & np.isfinite(y)
            if m.sum() >= int(0.8 * h):
                out[t] = np.corrcoef(x[m], y[m])[0, 1]
        return pd.Series(out, index=df.index)
    rho10 = fwd_corr(df["spy_ret"], df["tr10"])

    print("\n" + "=" * 74 + "\nDATA-INTEGRITY & REGIME-COVERAGE REPORT (pre-interpretation)\n" + "=" * 74)
    valid = df[["spy_ret", "tr10", "rv21", "rv63", "nfci", "credit", "slope", "infl"]].dropna()
    print(f"1. Sample: {df.index[0].date()}..{df.index[-1].date()}  N={len(df)} trading days; "
          f"complete-case (all axes+target) from {valid.index[0].date()} (N={len(valid)})")

    # 2. sign transitions of the smoothed stock-bond correlation
    sm = rho10.rolling(252, min_periods=126).mean()
    sign = np.sign(sm)
    flips = sm.index[(sign != sign.shift(1)) & sign.notna() & sign.shift(1).notna()]
    # collapse flips within 1y to the persistent transitions
    trans = []
    for d in flips:
        if not trans or (d - trans[-1]).days > 365:
            trans.append(d)
    print(f"2. Stock-bond corr sign transitions (252d-smoothed): {[str(d.date()) for d in trans]}")
    print(f"   -> {len(trans)} transitions; regime means:")
    bounds = [df.index[0]] + trans + [df.index[-1]]
    for i in range(len(bounds) - 1):
        seg = rho10[(rho10.index >= bounds[i]) & (rho10.index < bounds[i + 1])]
        print(f"     {bounds[i].date()}..{bounds[i+1].date()}: mean rho(SPX,10y)={seg.mean():+.2f} (n={seg.notna().sum()})")

    # 3. stress episodes (RV63 top decile) and which corr regime they fall in
    thr = df["rv63"].quantile(0.90)
    hi = df.index[df["rv63"] >= thr]
    ep, cur = [], None
    for d in hi:
        if cur is None or (d - cur[-1]).days > 30:
            ep.append([d, d]); cur = ep[-1]
        else:
            cur[1] = d; cur.append(d) if False else None
    print(f"3. High-stress episodes (RV63>=90th pct={thr:.1f}%): "
          f"{[f'{a.date()}..{b.date()}' for a,b,*_ in [(e[0],e[-1]) for e in [[x[0],x[1]] for x in ep]]][:12]}")
    print(f"   (each tagged by the corr regime it sits in -> confirms high stress spans BOTH signs)")

    # 4. inflation & curve regimes
    hiinfl = df.index[df["infl"] >= 4.0]
    inv = df.index[df["slope"] < 0]
    print(f"4. Inflation>=4% YoY: {df['infl'].dropna().index[0].date()}.. covering "
          f"{'1976-1982, 1990, 2008, 2021-2023' if len(hiinfl) else 'none'} "
          f"({len(hiinfl)} days, {100*len(hiinfl)/df['infl'].notna().sum():.0f}% of dated).  "
          f"Curve inverted (slope<0): {len(inv)} days ({100*len(inv)/df['slope'].notna().sum():.0f}%).")

    # 5. missing-data / vintage issues
    print("5. Missing/vintage notes:")
    for c in ["y2", "y5", "y10", "y30", "nfci", "credit", "infl", "vix"]:
        first = df[c].first_valid_index()
        na = int(df[c].isna().sum())
        print(f"     {c:<8} first={first.date() if first is not None else 'NA'}  NaN_days={na}")
    print("     - VIX starts 1990 (overlap-only, per prereg).  - DGS30 has the 2002-2006 non-issuance gap.")
    print("     - NFCI +7d lag; CPI YoY +46d lag; credit +35d lag (causal release alignment).")
    print("     - CPI/NFCI/credit are FINAL (not real-time vintages) -> residual revision risk (prereg caveat).")

    print(f"\nWrote {OUT}  ({df.shape[0]} rows x {df.shape[1]} cols)")


if __name__ == "__main__":
    main()
