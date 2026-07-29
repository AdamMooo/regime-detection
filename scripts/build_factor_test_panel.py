"""Path-A data foundation: monthly cross-sectional asset-pricing test panel.

The factor-model pivot (2026-07-29, see .planning/FACTOR-MODEL-DIRECTION.md) starts at the
PORTFOLIO level — rigorous asset-pricing tests (Fama-MacBeth, GRS, IC, factor spanning) on Ken
French's pre-formed portfolio grids, which needs no single-stock data. This builds the standard
textbook test panel:

  - TEST ASSETS: the 25 size x book-to-market value-weighted portfolios (French
    25_Portfolios_5x5), monthly, 192607+. These are THE canonical GRS/Fama-MacBeth test assets.
  - FACTORS: Mkt-RF, SMB, HML, RF from F-F_Research_Data_Factors (monthly).

MONTHLY (not daily) on purpose: GRS/Fama-MacBeth are asset-pricing tests designed for monthly
returns — daily adds microstructure noise and non-synchronous-trading bias the tests don't model.
This is a deliberate departure from the rest of the repo's daily cadence, correct for this task.

No look, no claim — a data build + gate only (cf. build_panel.py / build_assets.py).
Writes data/processed/factor_test_monthly.csv, results/factor_test_gate.csv.
"""

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
FF_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"


def _ff_monthly_first_block(zip_name, n_expected_cols):
    """Parse the FIRST monthly block of a French CSV (YYYYMM rows). French files append several
    blocks (VW, EW, firm counts, avg size); the value-weight monthly returns is always first and
    ends at the first non-date line after it starts."""
    resp = requests.get(FF_BASE + zip_name, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")

    header, rows, started = None, [], False
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        is_date = len(parts) >= 2 and len(parts[0]) == 6 and parts[0].isdigit()
        if is_date:
            rows.append(parts)
            started = True
        else:
            if started:
                break  # first block ended (blank / annual / next-block header)
            if header is None and len(parts) >= 2 and parts[0] == "" and any(parts[1:]):
                header = ["date"] + [p for p in parts[1:] if p]
    if header is None or len(header) != len(rows[0]):
        header = ["date"] + [f"c{i}" for i in range(1, len(rows[0]))]
    df = pd.DataFrame(rows, columns=header[:len(rows[0])])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m").dt.to_period("M").dt.to_timestamp("M")
    df = df.set_index("date").apply(pd.to_numeric, errors="coerce")
    df = df.replace([-99.99, -999], np.nan) / 100.0
    if n_expected_cols and df.shape[1] != n_expected_cols:
        df = df.iloc[:, :n_expected_cols]
    return df


def build():
    fac = _ff_monthly_first_block("F-F_Research_Data_Factors_CSV.zip", 4)
    fac.columns = ["mkt_rf", "smb", "hml", "rf"]

    ports = _ff_monthly_first_block("25_Portfolios_5x5_CSV.zip", 25)
    # name the 5x5 grid: size quintile S1..S5 (small->big) x value quintile V1..V5 (growth->value)
    ports.columns = [f"s{i}v{j}" for i in range(1, 6) for j in range(1, 6)]

    panel = fac.join(ports, how="inner").dropna(how="any")
    return panel


def gate(panel):
    g = []
    g.append(("F1_coverage",
              panel.index[0].year <= 1927 and len(panel) > 1000,
              f"{panel.index[0].date()}..{panel.index[-1].date()} n={len(panel)} months"))
    port_cols = [c for c in panel.columns if len(c) == 4 and c[0] == "s" and c[2] == "v"]
    g.append(("F2_25_assets", len(port_cols) == 25, f"{len(port_cols)} test portfolios"))
    # factor sanity: monthly Mkt-RF mean in a plausible band, positive over full sample
    mkt = panel["mkt_rf"]
    g.append(("F3_factors_sane",
              0.0 < mkt.mean() < 0.02 and 0.02 < mkt.std() < 0.10,
              f"mkt_rf mean={mkt.mean():.4f}/mo std={mkt.std():.4f}"))
    # a well-known stylized fact as an integrity check: within each size row, high-BE/ME (value,
    # v5) should on average out-return low-BE/ME (growth, v1) -> the value premium exists raw
    val_minus_growth = np.mean([panel[f"s{i}v5"].mean() - panel[f"s{i}v1"].mean() for i in range(1, 6)])
    g.append(("F4_value_premium_raw", val_minus_growth > 0,
              f"avg (V5-V1) monthly = {val_minus_growth:.4f} (>0 = value premium present raw)"))
    return pd.DataFrame(g, columns=["gate", "passed", "detail"])


def main():
    panel = build()
    panel.to_csv(ROOT / "data" / "processed" / "factor_test_monthly.csv")
    gdf = gate(panel)
    gdf.to_csv(ROOT / "results" / "factor_test_gate.csv", index=False)
    print(f"factor test panel: {panel.index[0].date()}..{panel.index[-1].date()} "
          f"n={len(panel)} months, {panel.shape[1]} cols")
    print(gdf.to_string(index=False))
    if not gdf["passed"].all():
        print("\nGATE FAILURE — see results/factor_test_gate.csv")
        sys.exit(1)


if __name__ == "__main__":
    main()
