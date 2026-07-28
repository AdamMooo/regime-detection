"""Sensor-v3 credit-stress data foundation: Moody's Baa-Aaa spread (FRED DBAA - DAAA, daily 1986+).

Credit spreads are the strongest LEADING-and-orthogonal candidate against the label's ~20-day
detection lag: credit is a senior claim, so it prices distress before equity does, and — being a
market price — it carries NO release-date/vintage lookahead trap (unlike PMI/claims/confidence).

WHY Baa-Aaa and NOT HY OAS: the natural first pick, ICE BofA HY OAS (BAMLH0A0HYM2), was LICENSE-
TRUNCATED on FRED to a rolling ~3y window (FRED's own metadata reports observation_start=2023-07-31,
verified 2026-07-28) after an ICE redistribution-license change — it now contains no crisis and is
useless for lag testing. Moody's Baa-Aaa is the fully-available, daily, long-history (1986+)
investment-grade substitute: a blunter lead than HY, but real and it spans 2008/2011/2015-16/2020.
The credit-augmented label is therefore a MODERN-ERA (1986+) instrument, NOT an extension of the
frozen 1926+ label.

DATA FOUNDATION + GATE ONLY. No economic claim, no look spent (cf. build_dispersion.py). A positive
lag result from adding this feature is US-panel-contaminated hypothesis-strengthening and binds the
out-of-hypothesis-sample rule before any SUPPORT claim.

Pulls from the API host (api.stlouisfed.org) via FRED_API_KEY in .env — the public fredgraph.csv
endpoint is unreliable (caps/ignores query). Raw pulls snapshotted to data/raw/ with the pull date.

Writes data/processed/credit_daily.csv + results/credit_gate.csv + results/credit_run.log.
"""

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BAA, AAA = "DBAA", "DAAA"
HALF_LIVES = (5, 10, 20)
MAX_FFILL = 5  # business days; longer source gaps are surfaced, not silently filled


def read_key():
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if line.startswith("FRED_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("FRED_API_KEY not found in .env")


def fetch():
    from fredapi import Fred
    f = Fred(api_key=read_key())
    baa = f.get_series(BAA).rename("baa")
    aaa = f.get_series(AAA).rename("aaa")
    for s in (baa, aaa):
        s.index = pd.to_datetime(s.index)
    snap = ROOT / "data" / "raw"
    snap.mkdir(parents=True, exist_ok=True)
    for name, s in ((BAA, baa), (AAA, aaa)):
        s.to_csv(snap / f"{name}_api_{date.today():%Y%m%d}.csv")
    return baa, aaa


def build(baa, aaa):
    both = pd.concat([baa, aaa], axis=1).sort_index()
    raw_na = int(both.isna().any(axis=1).sum())
    spread = (both["baa"] - both["aaa"]).rename("credit")
    obs = spread.dropna()
    gap_days = obs.index.to_series().diff().dt.days
    long_gaps = gap_days[gap_days > 7]
    filled = spread.ffill(limit=MAX_FFILL)
    out = pd.DataFrame({"credit": filled, "baa": both["baa"].ffill(limit=MAX_FFILL),
                        "aaa": both["aaa"].ffill(limit=MAX_FFILL)})
    for hl in HALF_LIVES:
        out[f"credit_ew{hl}"] = filled.ewm(halflife=hl, adjust=False).mean()
    return out.dropna(), dict(raw_na=raw_na, n_long_gaps=int(len(long_gaps)), long_gaps=long_gaps)


def gate(df, gapinfo):
    g = []
    g.append(("C1_coverage",
              df.index[0].date() <= date(1987, 6, 30) and len(df) > 8000,
              f"{df.index[0].date()}..{df.index[-1].date()} n={len(df)}"))
    v = df["credit"]
    g.append(("C2_sane",
              bool((v > 0).all()) and 0.1 < v.min() and v.max() < 6.0 and int(v.isna().sum()) == 0,
              f"min={v.min():.2f} max={v.max():.2f} pct; nan={int(v.isna().sum())}"))
    # anchor validation vs known Baa-Aaa history (percent): 2008 peak ~3.4, 2020 ~1.7, calm ~0.7-0.9
    anchors = {"2008-12-01": (2.6, 3.9), "2020-04-15": (1.2, 2.3),
               "2007-06-01": (0.6, 1.1), "2021-06-30": (0.5, 1.0)}
    ok, detail = True, []
    for dt, (lo, hi) in anchors.items():
        val = float(v.reindex([pd.Timestamp(dt)], method="nearest").iloc[0])
        hit = lo <= val <= hi
        ok = ok and hit
        detail.append(f"{dt}={val:.2f}[{lo}-{hi}]{'OK' if hit else 'BAD'}")
    g.append(("C3_anchors", ok, " ".join(detail)))
    g.append(("C4_gaps", gapinfo["n_long_gaps"] == 0,
              f"raw_na={gapinfo['raw_na']} long_gaps(>7d)={gapinfo['n_long_gaps']}"))
    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True)
    mkt = panel["mkt_ret"].reindex(df.index).dropna()
    own_vol = np.sqrt((mkt ** 2).ewm(halflife=20, adjust=False).mean())
    j = pd.DataFrame({"credit": df["credit_ew20"], "vol": own_vol}).dropna()
    corr = float(j["credit"].corr(j["vol"]))
    g.append(("C5_distinct_axis", 0.30 <= corr <= 0.90,
              f"corr(credit_ew20, mkt_ew20_vol)={corr:.3f} on n={len(j)} (want moderate, not redundant)"))
    return pd.DataFrame(g, columns=["gate", "passed", "detail"]), corr


def main():
    log = ["credit foundation (Sensor-v3, Moody's Baa-Aaa) — run log"]
    baa, aaa = fetch()
    log.append(f"fetched {BAA},{AAA} via api.stlouisfed.org: "
               f"baa {baa.dropna().index[0].date()}..{baa.dropna().index[-1].date()} "
               f"aaa {aaa.dropna().index[0].date()}..{aaa.dropna().index[-1].date()}")
    df, gapinfo = build(baa, aaa)
    df.to_csv(ROOT / "data" / "processed" / "credit_daily.csv")
    g, corr = gate(df, gapinfo)
    g.to_csv(ROOT / "results" / "credit_gate.csv", index=False)
    log.append(g.to_string(index=False))
    if gapinfo["n_long_gaps"]:
        log.append("\nLONG GAPS (>7d) in source — surfaced, not silently filled:")
        log.append(gapinfo["long_gaps"].to_string())
    passed = bool(g["passed"].all())
    log.append("\nCREDIT GATE: " + ("PASS" if passed else "FAIL"))
    log.append(f"series {df.index[0].date()}..{df.index[-1].date()} rows={len(df)} "
               f"cols={list(df.columns)}")
    text = "\n".join(str(x) for x in log)
    (ROOT / "results" / "credit_run.log").write_text(text, encoding="utf-8")
    print(text)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
