"""Credit signal inputs — excess bond premium (EBP) + OAS proxies (Phase 6, warm-start).

Orthogonality verdict: raw spreads are ~85% shared with VIX (redundant); the EBP
RESIDUAL (spread purged of expected default, Gilchrist-Zakrajsek 2012) is the
orthogonal, leading part → that is the signal, not raw OAS.

Sources (all free):
  EBP   Fed FEDS-Notes published monthly CSV (Favara-Gilchrist-Lewis-Zakrajsek).
        NOTE: restated each month — snapshot for strict PIT, else a near-real-time
        smoothed read. This builder saves today's vintage.
  OAS   FRED ICE BofA IG/HY option-adjusted spreads + Moody's Baa-10y (daily proxies,
        market prices → unrevised/PIT).

Writes data/processed/credit_monthly.csv (EBP) + credit_daily.csv (OAS proxies).
Run:  python scripts/build_credit.py
"""
import io
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_intl_bonds import _fred_key, fred_series

EBP_URL = "https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv"
OAS = {"ig_oas": "BAMLC0A0CM", "hy_oas": "BAMLH0A0HYM2", "baa_10y": "BAA10Y"}


def main() -> int:
    key = _fred_key()

    # EBP (monthly, published series)
    try:
        txt = requests.get(EBP_URL, timeout=60).text
        ebp = pd.read_csv(io.StringIO(txt))
        ebp.columns = [c.strip().lower() for c in ebp.columns]
        datecol = next(c for c in ebp.columns if "date" in c)
        ebp[datecol] = pd.to_datetime(ebp[datecol])
        ebp = ebp.set_index(datecol).sort_index()
        ebp.to_csv(ROOT / "data/processed/credit_monthly.csv")
        col = "ebp" if "ebp" in ebp.columns else ebp.columns[0]
        print(f"  EBP: {ebp.index[0].date()}..{ebp.index[-1].date()} n={len(ebp)} cols={list(ebp.columns)} "
              f"latest {col}={ebp[col].iloc[-1]:+.3f}")
    except Exception as e:
        print(f"  EBP FETCH FAILED: {str(e)[:80]} — wire manually next session")

    # OAS daily proxies (FRED)
    daily = {}
    for name, sid in OAS.items():
        try:
            daily[name] = fred_series(sid, key)
        except Exception as e:
            print(f"  {name} ({sid}) failed: {str(e)[:60]}")
    if daily:
        df = pd.concat(daily, axis=1).sort_index()
        df.to_csv(ROOT / "data/processed/credit_daily.csv")
        print(f"  OAS daily: {df.index[0].date()}..{df.index[-1].date()} n={len(df)} cols={list(df.columns)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
