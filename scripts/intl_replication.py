"""International replication break-test (#2): are the failure-mode relationships STRUCTURAL or a US
accident? Tests the core, most-falsifiable claim in local currency, per region:

    does the nominal-bond hedge WORK in deflationary/growth equity bears and FAIL in inflationary ones,
    the same way it does in the US?

Design (per Adam): test whether the DRIVERS produce the same asset-behavior relationship — not merely
"did bonds work." Local-currency, so equity/bond/inflation legs are consistent:
- equity : local price index (Nikkei yen 1990+, DAX eur ~1990+ / STOXX eur fallback) — price, ex-div
- bond   : local 10y government-bond synthetic TR from OECD yields (FRED)
- cpi    : local CPI YoY (FRED)

Honest limit: the INFLATIONARY-bear archetype internationally is essentially 2022 (a global shock), so
the independent power here is on the DEFLATIONARY archetype (Japan's Lost Decades) and on whether the
framework correctly explains the low-inflation regimes. Writes results/intl_replication.csv.
"""

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CRASH_DD = -0.10
INFL_HI = 0.03  # CPI YoY at trough dividing inflationary vs deflationary/low-inflation bears

REGIONS = {
    "Japan":  {"equity": ("ohlc_nikkei.csv", None), "yid": "IRLTLT01JPM156N", "cpi": "JPNCPIALLMINMEI"},
    "Europe": {"equity": ("ohlc_stoxx.csv", "^GDAXI"), "yid": "IRLTLT01DEM156N", "cpi": "DEUCPIALLMINMEI"},
}


def fred_series(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(io.StringIO(requests.get(url, timeout=120).text))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    return df.set_index("date")[series_id].dropna()


def bond_tr_monthly(y_pct):
    """Monthly constant-maturity 10y par-bond total return from a monthly yield (%).
    carry = y_{t-1}/12 ; price = -Dmod*dy + 0.5*C*dy^2 ; annual-unit duration/convexity of a 10y
    par bond at the prevailing yield (n=10 annual coupons)."""
    y = (y_pct / 100.0)
    yp = y.shift(1)
    dy = y - yp
    n = 10
    dur_mod = (1.0 - (1.0 + yp) ** (-n)) / yp / (1.0 + yp)
    conv = ((2.0 / yp ** 2) * (1.0 - (1.0 + yp) ** (-n))
            - 2.0 * n / (yp * (1.0 + yp) ** (n + 1)))
    return (yp / 12.0 - dur_mod * dy + 0.5 * conv * dy ** 2).dropna()


def _equity_monthly(csv_name, yf_ticker):
    """Local-currency monthly equity return. Prefer a longer yfinance index; fall back to the disk OHLC."""
    if yf_ticker:
        try:
            import yfinance as yf
            px = yf.download(yf_ticker, start="1988-01-01", auto_adjust=True, progress=False)["Close"]
            if isinstance(px, pd.DataFrame):
                px = px.iloc[:, 0]
            px = px.dropna()
            if len(px) > 2000:
                m = px.groupby(px.index.to_period("M")).last()
                return m.pct_change().dropna(), yf_ticker
        except Exception:
            pass
    df = pd.read_csv(ROOT / "data" / "processed" / csv_name, index_col=0, parse_dates=True)
    m = df["close"].groupby(df.index.to_period("M")).last()
    return m.pct_change().dropna(), csv_name


def _drawdown(ret):
    w = (1.0 + ret).cumprod()
    return w / w.cummax() - 1.0


def _episodes(dd):
    out, in_dd, start = [], False, None
    for dt, v in dd.items():
        if not in_dd and v < 0:
            in_dd, start = True, dt
        elif in_dd and v >= 0:
            seg = dd.loc[start:dt]
            out.append((start, seg.idxmin(), seg.min()))
            in_dd = False
    if in_dd:
        seg = dd.loc[start:]
        out.append((start, seg.idxmin(), seg.min()))
    return out


def run_region(name, cfg):
    eq, eq_src = _equity_monthly(*cfg["equity"])
    bond = bond_tr_monthly(fred_series(cfg["yid"]).groupby(
        fred_series(cfg["yid"]).index.to_period("M")).last())
    cpi = fred_series(cfg["cpi"])
    cpi_yoy = cpi.groupby(cpi.index.to_period("M")).last().pct_change(12)

    eq.index = eq.index if isinstance(eq.index, pd.PeriodIndex) else eq.index.to_period("M")
    df = pd.concat([eq.rename("equity"), bond.rename("bond"), cpi_yoy.rename("cpi_yoy")],
                   axis=1, sort=True).dropna(subset=["equity"])
    df.index = df.index.to_timestamp("M")

    dd = _drawdown(df["equity"])
    rows = []
    for start, trough, depth in _episodes(dd):
        if depth > CRASH_DD:
            continue
        peak = dd.loc[:start].index[dd.loc[:start].values >= 0]
        peak_date = peak[-1] if len(peak) else start
        span = df.loc[peak_date:trough].iloc[1:]
        br = span["bond"].dropna()
        b_ret = (1.0 + br).prod() - 1.0 if len(br) == len(span) and len(span) > 0 else np.nan
        infl = df.loc[trough, "cpi_yoy"]
        rows.append({"region": name, "peak": peak_date.date(), "trough": trough.date(),
                     "depth": round(depth, 3), "months": len(span),
                     "bond_ret": round(b_ret, 3) if pd.notna(b_ret) else np.nan,
                     "cpi_yoy": round(infl, 3) if pd.notna(infl) else np.nan,
                     "regime": ("inflationary" if pd.notna(infl) and infl >= INFL_HI
                                else "deflationary/low")})
    ep = pd.DataFrame(rows)

    both = df[["bond", "equity"]].dropna()
    crash = dd < CRASH_DD
    cm = both.index.intersection(crash[crash].index)
    rho_all = both["bond"].corr(both["equity"])
    rho_cr = both.loc[cm, "bond"].corr(both.loc[cm, "equity"]) if len(cm) > 20 else np.nan

    print(f"\n########## {name}  (equity={eq_src}, {df.index[0].date()}..{df.index[-1].date()}) ##########")
    print(f"bond-equity corr: full={rho_all:+.2f}  crash={rho_cr:+.2f} (n_crash={len(cm)})")
    if len(ep):
        print(ep.to_string(index=False))
        for reg in ["deflationary/low", "inflationary"]:
            sub = ep[ep["regime"] == reg]["bond_ret"].dropna()
            if len(sub):
                print(f"  -> bonds in {reg:18s} bears: mean {sub.mean():+.1%}  "
                      f"(n={len(sub)}, positive {int((sub > 0).sum())}/{len(sub)})")
    return ep


def main():
    allep = []
    for name, cfg in REGIONS.items():
        try:
            allep.append(run_region(name, cfg))
        except Exception as e:
            print(f"\n{name}: FAILED ({type(e).__name__}: {e})")
    if allep:
        out = pd.concat(allep, ignore_index=True)
        out.to_csv(ROOT / "results" / "intl_replication.csv", index=False)
        print(f"\nwrote results/intl_replication.csv ({len(out)} episodes)")


if __name__ == "__main__":
    main()
    sys.exit(0)
