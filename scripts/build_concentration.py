"""Phase-4 data build: monthly US index capital-share distribution across the
Ken French 5x5 (ME x BE/ME) buckets.

Source: 25_Portfolios_5x5_CSV.zip from the public Dartmouth library (no key).
The file carries eight blocks; two are used here and both are MONTHLY:

  "Number of Firms in Portfolios"  -> n_i, the bucket's firm count
  "Average Market Cap"             -> c_i, the bucket's average firm capitalisation

Bucket capital mass is n_i * c_i, so the capital-share vector is
s_i = n_i c_i / sum_j n_j c_j, and the standard reciprocal-Herfindahl summary of
that vector is eff_n = 1 / sum_i s_i^2 -- the effective number of independent
capital buckets. It is bounded by [1, 25]: 1 when every dollar sits in one
bucket, 25 when capital is spread evenly across all of them.

No look, no economic claim -- a data build + construction gate only, mirroring
build_panel.py / build_intl_panel.py.

Gate bars:
  C1 coverage      -- monthly, >= 1000 months, starts <= 1930-01, ends within 120 days
  C2 blocks agree  -- firm-count and market-cap blocks share an identical 25-column
                      bucket set on an identical month index
  C3 eff_n bounds  -- eff_n lies strictly inside [1, 25] on every month
  C4 shares sum    -- the reconstructed share vector sums to 1 (max |dev| <= 1e-9)
  C5 no gaps       -- zero NaNs in eff_n / top_share, and no missing calendar months

Writes: data/raw/ff_25_portfolios_5x5.csv, data/processed/concentration_monthly.csv,
        results/concentration_gate.csv

Run:  python scripts/build_concentration.py
"""

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]

FF_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
          "25_Portfolios_5x5_CSV.zip")

FIRMS_BLOCK = "Number of Firms in Portfolios"
CAP_BLOCK = "Average Market Cap"

MISSING = (-99.99, -999.0, -99.0)


def download_ff_25() -> str:
    raw_path = ROOT / "data" / "raw" / "ff_25_portfolios_5x5.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(FF_URL, timeout=180)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")
    raw_path.write_text(text, encoding="utf-8")
    return text


def _is_month_row(parts: list[str]) -> bool:
    return len(parts) > 1 and len(parts[0]) == 6 and parts[0].isdigit()


def parse_block(text: str, title: str) -> pd.DataFrame:
    """Monthly rows of one named block, indexed by month end.

    The vendor stacks eight blocks in one file, each opening with a title line
    then a bucket-name header. Rows are collected only while they carry a YYYYMM
    key, which both skips the annual sub-blocks and terminates cleanly at the
    next title line.
    """
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.strip() == title]
    if len(starts) != 1:
        raise ValueError(f"expected exactly one '{title}' block, found {len(starts)}")

    columns, rows = None, []
    for ln in lines[starts[0] + 1:]:
        parts = [p.strip() for p in ln.split(",")]
        if _is_month_row(parts):
            rows.append(parts)
        elif rows:
            break
        elif columns is None and len(parts) > 1 and parts[0] == "" and any(parts[1:]):
            columns = parts[1:]

    if columns is None or not rows:
        raise ValueError(f"no parsable monthly rows under '{title}'")

    width = len(rows[0]) - 1
    df = pd.DataFrame([r[1:width + 1] for r in rows], columns=columns[:width])
    df.index = pd.to_datetime([r[0] for r in rows], format="%Y%m") + pd.offsets.MonthEnd(0)
    df.index.name = "date"
    return df.apply(pd.to_numeric, errors="coerce").replace(list(MISSING), np.nan).sort_index()


def capital_shares(firms: pd.DataFrame, caps: pd.DataFrame) -> pd.DataFrame:
    mass = (firms * caps).where(firms > 0, 0.0)
    return mass.div(mass.sum(axis=1), axis=0)


def build_concentration(text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    firms = parse_block(text, FIRMS_BLOCK)
    caps = parse_block(text, CAP_BLOCK)
    shares = capital_shares(firms, caps)
    panel = pd.DataFrame({
        "eff_n": 1.0 / (shares ** 2).sum(axis=1),
        "top_share": shares.max(axis=1),
    })
    return panel, shares


def gate(panel: pd.DataFrame, shares: pd.DataFrame, firms: pd.DataFrame,
         caps: pd.DataFrame) -> pd.DataFrame:
    g = []

    start_ok = panel.index[0] <= pd.Timestamp("1930-01-31")
    end_ok = (pd.Timestamp.today() - panel.index[-1]).days <= 120
    g.append(("C1_coverage", bool(start_ok and end_ok and len(panel) >= 1000),
              f"n={len(panel)} span={panel.index[0].date()}..{panel.index[-1].date()}"))

    same_cols = list(firms.columns) == list(caps.columns) and firms.shape[1] == 25
    same_index = firms.index.equals(caps.index)
    g.append(("C2_blocks_agree", bool(same_cols and same_index),
              f"cols={firms.shape[1]}/{caps.shape[1]} index_match={same_index}"))

    lo, hi = panel["eff_n"].min(), panel["eff_n"].max()
    g.append(("C3_eff_n_bounds", bool(1.0 <= lo and hi <= 25.0),
              f"eff_n range={lo:.3f}..{hi:.3f}"))

    dev = float((shares.sum(axis=1) - 1.0).abs().max())
    g.append(("C4_shares_sum", dev <= 1e-9, f"max|sum(s)-1|={dev:.2e}"))

    expected = pd.date_range(panel.index[0], panel.index[-1], freq="ME")
    nan_count = int(panel.isna().sum().sum())
    g.append(("C5_no_gaps", bool(nan_count == 0 and panel.index.equals(expected)),
              f"nans={nan_count} missing_months={len(expected.difference(panel.index))}"))

    return pd.DataFrame(g, columns=["gate", "passed", "detail"])


def main() -> int:
    text = download_ff_25()
    firms = parse_block(text, FIRMS_BLOCK)
    caps = parse_block(text, CAP_BLOCK)
    panel, shares = build_concentration(text)

    out = ROOT / "data" / "processed" / "concentration_monthly.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out)

    res = gate(panel, shares, firms, caps)
    (ROOT / "results").mkdir(parents=True, exist_ok=True)
    res.to_csv(ROOT / "results" / "concentration_gate.csv", index=False)

    print(res.to_string(index=False))
    print(f"\npanel rows={len(panel)}  span={panel.index[0].date()}..{panel.index[-1].date()}")
    print(f"eff_n     min={panel['eff_n'].min():.2f}  median={panel['eff_n'].median():.2f}  "
          f"max={panel['eff_n'].max():.2f}")
    print(f"top_share min={panel['top_share'].min():.3f}  median={panel['top_share'].median():.3f}  "
          f"max={panel['top_share'].max():.3f}")
    print(f"wrote {out.relative_to(ROOT)}")
    print("CONSTRUCTION GATE:", "PASS" if res["passed"].all() else "FAIL")
    return 0 if res["passed"].all() else 1


if __name__ == "__main__":
    sys.exit(main())
