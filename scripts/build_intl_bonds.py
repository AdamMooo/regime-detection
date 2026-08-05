"""Build monthly 10y government-bond total returns for Japan and Germany (Bund).

The out-of-hypothesis-sample bond leg for the stock-bond correlation signal
(Phase 2). Equity legs already exist (japan_market_daily / europe_market_daily);
this adds the bond side so the intl OOS can run.

Source: FRED OECD long-term (10y) government bond yields, MONTHLY:
  Japan   IRLTLT01JPM156N  (1989+)
  Germany IRLTLT01DEM156N  (1956+; the honest pre-euro Bund benchmark for "Europe")
Monthly is the correct frequency: stockbond_corr.py treats the monthly correlation
as the honest read of the regime (daily comovement understates the slow nominal-real
covariance). Yields are market data -> no vintage/revision trap.

Bond returns use the same constant-maturity par-bond recipe as build_assets.py
(duration + convexity), with the carry term scaled to a MONTHLY period.

Reads FRED_API_KEY from .env (falls back to the key-free fredgraph endpoint).
Writes data/processed/intl_bonds_monthly.csv.

Run:  python scripts/build_intl_bonds.py
"""
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]

SERIES = {"jp": "IRLTLT01JPM156N", "de": "IRLTLT01DEM156N"}


def _fred_key() -> str | None:
    env = ROOT / ".env"
    if not env.exists():
        return None
    for line in env.read_text().splitlines():
        if line.startswith("FRED_API_KEY"):
            return line.split("=", 1)[1].strip()
    return None


def fred_series(sid: str, key: str | None) -> pd.Series:
    """Monthly yield series (percent). Official API when a key is present, else the
    key-free fredgraph csv endpoint (same data)."""
    if key:
        j = requests.get("https://api.stlouisfed.org/fred/series/observations",
                         params={"series_id": sid, "api_key": key, "file_type": "json"},
                         timeout=60).json()
        df = pd.DataFrame(j["observations"])
        df = df[df["value"] != "."]
        s = pd.Series(pd.to_numeric(df["value"].values, errors="coerce"),
                      index=pd.to_datetime(df["date"].values))
    else:
        txt = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=60).text
        df = pd.read_csv(io.StringIO(txt))
        s = pd.Series(pd.to_numeric(df.iloc[:, 1], errors="coerce").values,
                      index=pd.to_datetime(df.iloc[:, 0]))
    return s.dropna().sort_index().rename(sid)


def bond_total_return_monthly(y10_pct: pd.Series) -> pd.Series:
    """Constant-maturity 10y par-bond total return over a MONTHLY step. Same
    duration/convexity as build_assets.bond_total_return; carry = y_prev/12."""
    y = y10_pct / 100.0
    y_prev = y.shift(1)
    dy = y - y_prev
    n = 20                       # 10y in half-year periods
    h = y_prev / 2.0
    dur_mod = (1.0 - (1.0 + h) ** (-n)) / h / 2.0 / (1.0 + h)
    conv = ((2.0 / h ** 2) * (1.0 - (1.0 + h) ** (-n))
            - 2.0 * n / (h * (1.0 + h) ** (n + 1))) / 4.0
    tr = y_prev / 12.0 - dur_mod * dy + 0.5 * conv * dy ** 2
    return tr.dropna()


def main() -> int:
    key = _fred_key()
    print(f"FRED key: {'loaded' if key else 'not found (using key-free endpoint)'}")
    out = {}
    for tag, sid in SERIES.items():
        y = fred_series(sid, key)
        y.index = y.index.to_period("M").to_timestamp("M")   # anchor to month-end
        ret = bond_total_return_monthly(y).rename(f"{tag}_bond10_ret")
        out[f"{tag}_y10"] = y
        out[f"{tag}_bond10_ret"] = ret
        vol = float(ret.std() * np.sqrt(12))
        print(f"  {tag}: {sid}  yield {y.index[0].date()}..{y.index[-1].date()} n={len(y)}  "
              f"bond_ret ann_vol={vol:.2%}  {'OK' if 0.03 <= vol <= 0.15 else 'CHECK vol band'}")

    panel = pd.concat(out, axis=1, sort=True)
    dest = ROOT / "data" / "processed" / "intl_bonds_monthly.csv"
    panel.to_csv(dest)
    print(f"\nwrote {dest.relative_to(ROOT)}  ({panel.index[0].date()}..{panel.index[-1].date()}, {len(panel)} months)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
