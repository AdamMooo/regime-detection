"""Fetch AQR's monthly Betting-Against-Beta (BAB) equity factor (Frazzini-Pedersen 2014).

BAB is the spanning control the regime-as-a-factor test hinges on (§5 FACTOR-MODEL-DIRECTION):
our JM label is a market-downside-vol transform, so a regime-beta spread most likely re-loads the
low-vol / high-beta cross-sectional axis BAB already harvests. Any regime-factor alpha MUST survive
after controlling for BAB or it's a false positive rediscovering the low-vol anomaly.

Source: AQR "Betting Against Beta: Equity Factors, Monthly" (self-financing long/short excess
returns; long low-beta, short high-beta). We keep USA (the label's home cross-section) and Global
(for the later international confirmation). Month-end dated to align with factor_test_monthly.csv.

Outputs:
  data/processed/bab_monthly.csv   date(month-end), bab_us, bab_global
  results/bab_gate.csv
Cached raw at data/raw/bab_monthly.xlsx (re-download by deleting it).
"""

from pathlib import Path
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
URL = ("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/"
       "Betting-Against-Beta-Equity-Factors-Monthly.xlsx")
RAW = ROOT / "data" / "raw" / "bab_monthly.xlsx"


def fetch():
    if RAW.exists():
        return
    RAW.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    RAW.write_bytes(urllib.request.urlopen(req, timeout=120).read())


def main():
    fetch()
    df = pd.read_excel(RAW, "BAB Factors", header=18)
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"])
    bab = df[["date", "USA", "Global"]].rename(columns={"USA": "bab_us", "Global": "bab_global"})
    bab = bab.set_index("date").dropna(how="all")
    # snap to month-end to match the factor panel's index convention
    bab.index = bab.index + pd.offsets.MonthEnd(0)

    out = ROOT / "data" / "processed" / "bab_monthly.csv"
    bab.to_csv(out)

    panel = pd.read_csv(ROOT / "data" / "processed" / "factor_test_monthly.csv",
                        index_col=0, parse_dates=True)
    aligned = bab.reindex(panel.index)
    us = bab["bab_us"].dropna()
    gate = pd.DataFrame([
        ("us_first", us.index.min().date()),
        ("us_last", us.index.max().date()),
        ("us_n", int(us.notna().sum())),
        ("global_n", int(bab["bab_global"].notna().sum())),
        ("us_mean_monthly", round(float(us.mean()), 5)),
        ("us_ann_sharpe", round(float(us.mean() / us.std() * (12 ** 0.5)), 3)),
        ("aligned_to_panel_us_n", int(aligned["bab_us"].notna().sum())),
    ], columns=["check", "value"])
    gate.to_csv(ROOT / "results" / "bab_gate.csv", index=False)
    print(gate.to_string(index=False))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
