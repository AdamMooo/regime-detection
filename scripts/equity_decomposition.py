"""Equity-drawdown decomposition — the last structural question before the portfolio test.

Is the ~33% of driver-PCA variance we don't explain a MISSING portfolio-relevant risk driver, or just
idiosyncratic equity variation / the equity risk premium we're already paid to hold? Method = a
transparent, causal (ex-post accounting) version of the Campbell-Shiller / Campbell-Vuolteenaho
"Bad Beta, Good Beta" (2004) decomposition, applied to each large US equity drawdown:

    Price = Earnings x (P/E)   =>   Dlog(P) = Dlog(Earnings)  +  Dlog(P/E)
                                              [cash-flow shock]   [discount-rate / multiple shock]

    Dlog(P/E) is then split:  real-rate part (b * D real_rate, b from a level regression of log P/E on
    the real rate = the equity multiple's rate sensitivity / "duration") + a residual = the equity
    RISK-PREMIUM / risk-appetite shock (compensation demanded beyond real rates).

Then the SPANNING test: map each shock type to which sleeve/axis covered it (join to
results/drawdown_episodes.csv). If cash-flow / real-rate / risk-premium shocks all map onto the two axes
already identified (risk-off severity ; inflation/real-rate), the residual variance is NOT a missing
spanning dimension. Fundamentals = Shiller (S&P earnings/P-E, 1871+). Writes results/equity_decomposition.csv.

Caveat: trailing reported earnings LAG price (2008 earnings cratered after the price bottom), so the
peak->trough split understates the cash-flow share; a peak->trough+12m earnings column is reported as the
lag-robustness check.
"""

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
SHILLER_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv"
CRASH_DD = -0.10


def load_shiller():
    df = pd.read_csv(io.StringIO(requests.get(SHILLER_URL, timeout=90).text))
    df["date"] = pd.to_datetime(df["Date"])
    df = df.set_index("date").sort_index()
    out = pd.DataFrame({
        "price": df["SP500"],
        "earn": df["Earnings"].replace(0, np.nan),
        "cpi": df["Consumer Price Index"].replace(0, np.nan),
        "rate": df["Long Interest Rate"].replace(0, np.nan),
    })
    out["cpi_yoy"] = out["cpi"].pct_change(12)
    out["real_rate"] = out["rate"] / 100.0 - out["cpi_yoy"]
    out["logp"] = np.log(out["price"])
    out["loge"] = np.log(out["earn"])
    out["logpe"] = out["logp"] - out["loge"]
    return out


def _episodes(dd):
    out, in_dd, start = [], False, None
    for dt, v in dd.items():
        if not in_dd and v < 0:
            in_dd, start = True, dt
        elif in_dd and v >= 0:
            seg = dd.loc[start:dt]
            out.append((start, seg.idxmin()))
            in_dd = False
    if in_dd:
        out.append((start, dd.loc[start:].idxmin()))
    return out


def main():
    s = load_shiller()
    w = (s["price"] / s["price"].cummax())
    dd = w - 1.0

    # equity multiple's real-rate sensitivity (level regression, robust full-sample estimate)
    reg = s[["logpe", "real_rate"]].dropna()
    b1, b0 = np.polyfit(reg["real_rate"], reg["logpe"], 1)
    r2 = np.corrcoef(reg["real_rate"], reg["logpe"])[0, 1] ** 2
    print(f"log(P/E) on real_rate: slope={b1:.2f} (per 1.0 = 100bp), R^2={r2:.2f}, "
          f"n={len(reg)} — how much valuation tracks real rates")

    ep = pd.read_csv(ROOT / "results" / "drawdown_episodes.csv") \
        if (ROOT / "results" / "drawdown_episodes.csv").exists() else None

    rows = []
    for pk, tr in _episodes(dd):
        if dd.loc[pk:tr].min() > CRASH_DD:
            continue
        peaks = dd.loc[:pk].index[dd.loc[:pk].values >= 0]
        p0 = peaks[-1] if len(peaks) else pk
        if pd.isna(s.loc[p0, "loge"]) or pd.isna(s.loc[tr, "loge"]):
            continue
        dP = s.loc[tr, "logp"] - s.loc[p0, "logp"]
        dE = s.loc[tr, "loge"] - s.loc[p0, "loge"]           # cash-flow shock
        dPE = dP - dE                                        # multiple shock
        dRR = s.loc[tr, "real_rate"] - s.loc[p0, "real_rate"]
        rate_part = b1 * dRR                                 # multiple move explained by real rates
        riskprem = dPE - rate_part                           # residual = risk-premium / risk-appetite
        # lag-robustness: earnings measured peak -> trough+12m
        tr12 = tr + pd.DateOffset(months=12)
        near = s.index[s.index.get_indexer([tr12], method="nearest")][0]
        dE12 = s.loc[near, "loge"] - s.loc[p0, "loge"] if pd.notna(s.loc[near, "loge"]) else np.nan
        rows.append({"peak": p0.date(), "trough": tr.date(), "dP": round(dP, 2),
                     "cashflow": round(dE, 2), "cashflow_12m": round(dE12, 2) if pd.notna(dE12) else np.nan,
                     "multiple": round(dPE, 2), "mult_realrate": round(rate_part, 2),
                     "mult_riskprem": round(riskprem, 2), "dRR": round(dRR, 3)})
    dec = pd.DataFrame(rows)

    def dom(r):
        cf, mu = abs(r["cashflow"]), abs(r["multiple"])
        base = "cash-flow" if cf >= mu else "multiple"
        if base == "multiple":
            base += ("/real-rate" if abs(r["mult_realrate"]) >= abs(r["mult_riskprem"]) else "/risk-prem")
        return base
    dec["dominant"] = dec.apply(dom, axis=1)

    # spanning: attach the strongest-helping sleeve per episode (match by trough year +/-1)
    if ep is not None:
        ep["tyr"] = pd.to_datetime(ep["trough"]).dt.year
        sleeves = ["bond10", "gold", "commod", "cash", "trend"]
        best = []
        for _, r in dec.iterrows():
            yr = pd.Timestamp(r["trough"]).year
            m = ep[(ep["tyr"] - yr).abs() <= 1]
            if len(m):
                row = m.iloc[0]
                helped = [f"{sv}{row[sv]:+.2f}" for sv in sleeves
                          if pd.notna(row[sv]) and row[sv] >= 0.05]
                best.append(", ".join(helped) if helped else "(none strong)")
            else:
                best.append("")
        dec["sleeves_that_helped"] = best

    dec.to_csv(ROOT / "results" / "equity_decomposition.csv", index=False)
    print("\n=== EQUITY-DRAWDOWN DECOMPOSITION (log changes; cash-flow vs multiple; multiple split) ===")
    print(dec.to_string(index=False))
    print("\nDominant-shock tally:")
    print(dec["dominant"].value_counts().to_string())
    return dec


if __name__ == "__main__":
    main()
    sys.exit(0)
