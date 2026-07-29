"""Out-of-hypothesis-sample data build: international daily panels (Japan, Europe) to
confirm/kill the US-only dispersion lag finding (`explore_dispersion_feature.py`,
2026-07-28: -40d LT20 lag on the US panel, CONTAMINATED — hypothesis-generating only per
CLAUDE.md's out-of-hypothesis-sample rule).

Source: Ken French International data library, daily, both from 1990-07-02 —
  {Region}_3_Factors_Daily_CSV.zip   -> Mkt-RF, SMB, HML, RF  (market return = Mkt-RF + RF)
  {Region}_25_Portfolios_ME_BE-ME_daily_CSV.zip -> 25 size/BE-ME sorted portfolios (value-weight
  block only; the file appends a second equal-weight block with duplicate dates, same structure
  build_assets.py already handles for the US industry file)

No look, no economic claim here — a data build + gate only, mirrors build_panel.py/build_assets.py.
Writes data/processed/{region}_market_daily.csv, data/processed/{region}_assets_daily.csv,
results/intl_panel_gate.csv.
"""

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import requests

FF_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"

REGIONS = ["Japan", "Europe"]


def _ff_daily_table(zip_name):
    resp = requests.get(FF_BASE + zip_name, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")
    header, rows = None, []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and len(parts[0]) == 8 and parts[0].isdigit():
            rows.append(parts)
        elif header is None and len(parts) >= 2 and parts[0] == "" and any(parts[1:]):
            header = ["date"] + [p for p in parts[1:]]
    if rows and header and len(header) != len(rows[0]):
        header = ["date"] + [f"c{i}" for i in range(1, len(rows[0]))]
    df = pd.DataFrame(rows, columns=header[:len(rows[0])])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.set_index("date").sort_index()
    df = df.apply(pd.to_numeric, errors="coerce").replace([-99.99, -999], np.nan) / 100.0
    df = df.dropna(axis=1, how="all")
    df = df[~df.index.duplicated(keep="first")]
    return df


def build_region(region):
    fac = _ff_daily_table(f"{region}_3_Factors_Daily_CSV.zip")
    mkt_ret = (fac["Mkt-RF"] + fac["RF"]).rename("mkt_ret")
    market = pd.DataFrame({"mkt_ret": mkt_ret})

    ports = _ff_daily_table(f"{region}_25_Portfolios_ME_BE-ME_daily_CSV.zip")
    ports = ports.loc[:, [c for c in ports.columns if c not in ("Mkt-RF", "SMB", "HML", "RF")]]
    ports.columns = [f"p{i}" for i in range(len(ports.columns))]

    return market, ports


def gate(region, market, ports):
    g = []
    g.append((f"{region}_I1_coverage",
              market.index[0].year <= 1991 and len(market) > 8500,
              f"{market.index[0].date()}..{market.index[-1].date()} n={len(market)}"))
    r = market["mkt_ret"]
    g.append((f"{region}_I2_sane",
              r.abs().max() < 0.30 and r.std() * np.sqrt(252) < 0.40,
              f"max|r|={r.abs().max():.3f} ann_vol={r.std() * np.sqrt(252):.3f}"))
    joint = ports.dropna(how="any")
    g.append((f"{region}_I3_ports_coverage",
              len(joint) > 8500 and joint.shape[1] == 25,
              f"n={len(joint)} cols={joint.shape[1]}"))
    ew = ports.mean(axis=1)
    corr = ew.corr(r.reindex(ew.index))
    g.append((f"{region}_I4_ports_track_market",
              corr >= 0.85, f"corr(EW(25 ports), mkt_ret)={corr:.3f}"))
    return g


def main():
    all_gates = []
    for region in REGIONS:
        market, ports = build_region(region)
        rl = region.lower()
        market.to_csv(ROOT / "data" / "processed" / f"{rl}_market_daily.csv")
        ports.to_csv(ROOT / "data" / "processed" / f"{rl}_assets_daily.csv")
        all_gates.extend(gate(region, market, ports))
        print(f"{region}: market {market.index[0].date()}..{market.index[-1].date()} "
              f"n={len(market)}; ports {ports.shape}")

    gdf = pd.DataFrame(all_gates, columns=["gate", "passed", "detail"])
    gdf.to_csv(ROOT / "results" / "intl_panel_gate.csv", index=False)
    print(gdf.to_string(index=False))
    if not gdf["passed"].all():
        print("\nGATE FAILURE(S) — see results/intl_panel_gate.csv")
        sys.exit(1)


if __name__ == "__main__":
    main()
