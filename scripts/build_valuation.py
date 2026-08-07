"""Valuation signal inputs — Shiller's CAPE dataset (Phase 3).

Primary source: Robert Shiller's `ie_data.xls` — the canonical Campbell-Shiller
object (S&P composite price, dividend, as-reported earnings, CPI, GS10; monthly
since 1871), the longest point-in-time-reconstructable valuation history and the
series the frozen charter registers as primary.

The Yale-hosted copy named in the charter froze in 2023, so the builder falls
back to the file Shiller currently publishes on shillerdata.com whenever the Yale
copy is stale, and records which one it used. The raw workbook is snapshotted to
data/raw/ie_data.xls — that snapshot IS the vintage (the file is restated every
month, so "ie_data.xls" is not a stable identifier for a dataset).

Short rate: Ken French monthly RF (one-month T-bill, 1926-07+). Shiller's file
carries no short rate, and the daily RF already in market_daily.csv is rounded to
1bp/day, i.e. ~2.5%/yr steps — too coarse to deflate.

NOT carried through from the source workbook:
  - its trailing "10 Year Annualized ... Real Return" columns are REALIZED FORWARD
    returns (look-ahead by construction, and the object of the frozen one-look);
  - its Real Price / Real Earnings columns are rescaled to the LATEST CPI vintage,
    a full-sample base. The signal deflates the nominal inputs itself under its own
    publication lag, so only nominal inputs are written.

Rates are stored as decimals (0.0475), not percent, to match the rest of the repo.

Writes data/processed/valuation_monthly.csv
Run:  python scripts/build_valuation.py
"""

import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from valuation import CPI_PUBLICATION_LAG_M

SHILLER_YALE_URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
SHILLER_HOME = "https://shillerdata.com/"
STALE_MONTHS = 6
FF_MONTHLY_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
                  "F-F_Research_Data_Factors_CSV.zip")
UA = "Mozilla/5.0"

SHEET = "Data"
HEADER_ROWS = 8          # rows 0-7 are the workbook's title/legend block
SOURCE_COLUMNS = ["date", "price", "dividend", "earnings", "cpi", "date_frac", "long_rate",
                  "real_price", "real_dividend", "real_tr_price", "real_earnings",
                  "real_tr_scaled_earnings", "cape"]
KEEP = ["price", "dividend", "earnings", "cpi", "long_rate", "cape"]

# published CAPE landmarks, for a data-integrity spot check (not a hypothesis test)
LANDMARKS = {"1929-08-31": 31.5, "1920-12-31": 4.8, "1999-12-31": 44.2, "2009-03-31": 13.3}
LANDMARK_TOL = 1.5

CAPE_BOUNDS = (3.0, 70.0)


def _download(url: str) -> bytes:
    resp = requests.get(url, timeout=180, headers={"User-Agent": UA})
    resp.raise_for_status()
    return resp.content


def _current_file_url() -> str:
    """Shiller publishes updates on shillerdata.com behind a href carrying a
    rotating ?ver= token, so the link is scraped rather than hard-coded."""
    html = requests.get(SHILLER_HOME, timeout=60, headers={"User-Agent": UA}).text
    m = re.search(r'href="(//[^"]*ie_data\.xls[^"]*)"', html)
    if not m:
        raise RuntimeError(f"no ie_data.xls download link found on {SHILLER_HOME}")
    return "https:" + m.group(1)


def parse_shiller(raw: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(raw), sheet_name=SHEET, header=None,
                       skiprows=HEADER_ROWS, usecols=range(len(SOURCE_COLUMNS)))
    df.columns = SOURCE_COLUMNS
    stamp = pd.to_numeric(df["date"], errors="coerce")
    df = df[stamp.notna()].copy()          # drops the trailing footnote row
    stamp = stamp.dropna()

    # the sheet's date is a float 1871.01 = Jan 1871, 1871.10 = Oct 1871
    year = np.floor(stamp + 1e-9).astype(int)
    month = np.round((stamp - year) * 100).astype(int)
    df.index = pd.DatetimeIndex(
        pd.to_datetime(dict(year=year, month=month, day=1)) + pd.offsets.MonthEnd(0),
        name="date")

    for col in KEEP:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    out = df[KEEP].copy()
    out["long_rate"] = out["long_rate"] / 100.0
    return out


def fetch_shiller() -> tuple[pd.DataFrame, str]:
    url = SHILLER_YALE_URL
    raw = _download(url)
    df = parse_shiller(raw)
    if (pd.Timestamp.today() - df.index[-1]).days > STALE_MONTHS * 31:
        print(f"  {url} ends {df.index[-1].date()} (stale) -> falling back to {SHILLER_HOME}")
        url = _current_file_url()
        raw = _download(url)
        df = parse_shiller(raw)
    snapshot = ROOT / "data" / "raw" / "ie_data.xls"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes(raw)
    return df, url


def ff_short_rate() -> pd.Series:
    """Annualised one-month T-bill, monthly (Ken French RF, in percent per month)."""
    with zipfile.ZipFile(io.BytesIO(_download(FF_MONTHLY_URL))) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5 and len(parts[0]) == 6 and parts[0].isdigit():
            rows.append((parts[0], parts[4]))
    ym, rf = zip(*rows)
    idx = pd.to_datetime(list(ym), format="%Y%m") + pd.offsets.MonthEnd(0)
    monthly = pd.to_numeric(list(rf)) / 100.0
    return pd.Series((1.0 + monthly) ** 12 - 1.0, index=idx, name="short_rate")


def main() -> int:
    df, url = fetch_shiller()
    retrieved = pd.Timestamp.today().normalize()

    df["short_rate"] = ff_short_rate().reindex(df.index)
    # ex-post real short rate: nominal deflated by trailing 12m inflation, and the
    # CPI leg carries its publication lag so the row is readable at its own date
    infl = (df["cpi"] / df["cpi"].shift(12) - 1.0).shift(CPI_PUBLICATION_LAG_M)
    df["short_rate_real"] = (1.0 + df["short_rate"]) / (1.0 + infl) - 1.0

    out = ROOT / "data" / "processed" / "valuation_monthly.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out)

    gate = []
    grid = pd.date_range(df.index[0], df.index[-1], freq="ME")
    span_ok = df.index[0] <= pd.Timestamp("1871-01-31") and (retrieved - df.index[-1]).days <= 120
    gate.append(("G1_span", span_ok, f"start={df.index[0].date()} end={df.index[-1].date()} n={len(df)}"))

    contiguous = df.index.equals(grid) and not df.index.has_duplicates
    gate.append(("G2_monthly_grid", contiguous,
                 f"contiguous={df.index.equals(grid)} dups={int(df.index.duplicated().sum())}"))

    core = df[["price", "cpi", "long_rate"]].isna().sum()
    gate.append(("G3_core_missingness", core.sum() == 0, f"missing={core.to_dict()}"))

    cape = df["cape"].dropna()
    lo, hi = CAPE_BOUNDS
    gate.append(("G4_cape_bounds", bool((cape > lo).all() and (cape < hi).all()),
                 f"min={cape.min():.2f} ({cape.idxmin().date()}) max={cape.max():.2f} "
                 f"({cape.idxmax().date()}) first={cape.index[0].date()}"))

    misses = {d: round(float(df.loc[d, "cape"]), 2) for d, v in LANDMARKS.items()
              if abs(float(df.loc[d, "cape"]) - v) > LANDMARK_TOL}
    gate.append(("G5_cape_landmarks", not misses, f"off={misses or 'none'}"))

    sr = df["short_rate"].dropna()
    sr_ok = sr.index[0] <= pd.Timestamp("1926-12-31") and (df.index[-1] - sr.index[-1]).days <= 120
    gate.append(("G6_short_rate", bool(sr_ok),
                 f"{sr.index[0].date()}..{sr.index[-1].date()} latest={sr.iloc[-1]:.2%} "
                 f"real={df['short_rate_real'].dropna().iloc[-1]:+.2%}"))

    res = pd.DataFrame(gate, columns=["gate", "passed", "detail"])
    print(res.to_string(index=False))

    e_last = df["earnings"].last_valid_index()
    d_last = df["dividend"].last_valid_index()
    print(f"\nreporting frontier: price through {df.index[-1].date()}, earnings through "
          f"{e_last.date()} ({(df.index[-1].year - e_last.year) * 12 + df.index[-1].month - e_last.month}"
          f" months behind), dividends through {d_last.date()}")
    print(f"source:    {url}")
    print(f"retrieved: {retrieved.date()}  (raw snapshot -> data/raw/ie_data.xls)")
    print(f"wrote {out.relative_to(ROOT)}  rows={len(df)}  cols={list(df.columns)}")
    print("CONSTRUCTION GATE:", "PASS" if res["passed"].all() else "FAIL")
    return 0 if res["passed"].all() else 1


if __name__ == "__main__":
    sys.exit(main())
