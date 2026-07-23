"""V2 Phase-0 data build: multi-decade US equity total-return panel + jump-model features.

Primary series: Ken French daily market factor (Mkt-RF + RF), 1926+, survivorship-clean.
Cross-checked against SPY total return (yfinance, auto-adjusted) on the 1993+ overlap.
Features are return-derived only (dd10, sortino20, sortino60) — no NFCI, no VIX, so the
data-vintage lookahead class is out of scope by construction.

Gate bars (all must PASS before Phase 1 uses the panel):
  G1 coverage        — panel starts <= 1963-07 and ends within 75 days of today (French publishes
                       with a ~1-2 month lag; RESEARCH panel only — the live instrument needs an
                       SPY-splice tail, pinned as a Phase-4 item in V2-JUMPMODEL-PLAN.md)
  G2 overlap corr    — corr(mkt_ret, spy_ret) >= 0.99 on 2010+ (data integrity, both series clean)
                       and >= 0.95 on the full 1993+ overlap (CRSP total-market vs S&P 500 universe
                       difference tolerated; diagnosed 2026-07-22: sub-0.98 full-overlap corr comes
                       from 1990s SPY tracking noise + genuine 2000/2008 universe divergence)
  G3 overlap drift   — |annualized return difference| <= 1.5%/yr on the overlap
  G4 crisis coverage — every pre-named crisis window contains a day with dd10 above its full-sample 90th pctile
  G5 episode count   — >= 10 distinct high-stress episodes (dd10 > 90th pctile, separated by > 63 trading days)

Writes: data/raw/ff_factors_daily.csv, data/processed/v2_daily.csv, results/v2_construction_gate.csv
"""

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from v2_core import build_features

FF_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
          "F-F_Research_Data_Factors_daily_CSV.zip")

CRISIS_WINDOWS = {
    "1974_oil":      ("1974-08-01", "1974-12-31"),
    "1987_crash":    ("1987-10-01", "1987-12-31"),
    "1998_ltcm":     ("1998-08-01", "1998-11-30"),
    "2001_dotcom":   ("2001-03-01", "2001-10-31"),
    "2008_gfc":      ("2008-09-01", "2009-01-31"),
    "2011_debt":     ("2011-08-01", "2011-10-31"),
    "2015_yuan":     ("2015-08-01", "2015-10-31"),
    "2018_q4":       ("2018-12-01", "2019-01-15"),
    "2020_covid":    ("2020-02-20", "2020-05-31"),
    "2022_tighten":  ("2022-01-01", "2022-12-31"),
}


def download_ff_daily():
    raw_path = ROOT / "data" / "raw" / "ff_factors_daily.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(FF_URL, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5 and len(parts[0]) == 8 and parts[0].isdigit():
            rows.append(parts[:5])
    df = pd.DataFrame(rows, columns=["date", "mkt_rf", "smb", "hml", "rf"])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    for c in ["mkt_rf", "smb", "hml", "rf"]:
        df[c] = pd.to_numeric(df[c])
    df = df[(df["mkt_rf"] > -99) & (df["rf"] > -99)].set_index("date").sort_index()
    df.to_csv(raw_path)
    return df


def download_spy():
    import yfinance as yf
    px = yf.download("SPY", start="1993-02-01", auto_adjust=True, progress=False)["Close"]
    if isinstance(px, pd.DataFrame):
        px = px.iloc[:, 0]
    return px.pct_change().dropna().rename("spy_ret")


def main():
    ff = download_ff_daily()
    mkt_ret = (ff["mkt_rf"] + ff["rf"]) / 100.0
    rf = ff["rf"] / 100.0
    spy = download_spy()

    feats = build_features(mkt_ret.to_numpy())
    feats.index = mkt_ret.index
    panel = pd.DataFrame({"mkt_ret": mkt_ret, "rf": rf}).join(feats)
    panel = panel.iloc[63:]  # feature burn-in

    out = ROOT / "data" / "processed" / "v2_daily.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out)

    gate = []
    start_ok = panel.index[0] <= pd.Timestamp("1963-07-01")
    end_ok = (pd.Timestamp.today() - panel.index[-1]).days <= 75
    gate.append(("G1_coverage", start_ok and end_ok,
                 f"start={panel.index[0].date()} end={panel.index[-1].date()}"))

    both = pd.DataFrame({"mkt": mkt_ret, "spy": spy}).dropna()
    corr_full = both["mkt"].corr(both["spy"])
    corr_mod = both.loc["2010":, "mkt"].corr(both.loc["2010":, "spy"])
    gate.append(("G2_overlap_corr", corr_mod >= 0.99 and corr_full >= 0.95,
                 f"corr_2010+={corr_mod:.4f} corr_full={corr_full:.4f} n={len(both)}"))

    ann_diff = (both["mkt"].mean() - both["spy"].mean()) * 252
    gate.append(("G3_overlap_drift", abs(ann_diff) <= 0.015, f"ann_ret_diff={ann_diff:+.4%}"))

    thr = panel["dd10"].quantile(0.90)
    misses = [name for name, (a, b) in CRISIS_WINDOWS.items()
              if panel.loc[a:b, "dd10"].max() <= thr]
    gate.append(("G4_crisis_coverage", len(misses) == 0, f"misses={misses or 'none'}"))

    hot = (panel["dd10"] > thr).to_numpy()
    hot_idx = np.flatnonzero(hot)
    episodes = 1 + int((np.diff(hot_idx) > 63).sum()) if len(hot_idx) else 0
    gate.append(("G5_episode_count", episodes >= 10, f"episodes={episodes}"))

    res = pd.DataFrame(gate, columns=["gate", "passed", "detail"])
    res.to_csv(ROOT / "results" / "v2_construction_gate.csv", index=False)
    print(res.to_string(index=False))
    print(f"\npanel rows={len(panel)}  span={panel.index[0].date()}..{panel.index[-1].date()}")
    print("CONSTRUCTION GATE:", "PASS" if res["passed"].all() else "FAIL")
    return 0 if res["passed"].all() else 1


if __name__ == "__main__":
    sys.exit(main())
