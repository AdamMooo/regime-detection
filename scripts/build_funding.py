"""Funding-stress inputs — the tail-only funding axis (Phase 7, warm-start, NARROW).

Orthogonality verdict: PARTIAL, decouples only in the tail (2008/2020) → a binary
funding-stress FLAG, not a continuous signal. Scoped narrow deliberately.

Sources (free): FRED financial-stress indices with funding components + a
long CP-bill spread. (Preferred strict-PIT source = OFR FSI funding sub-index,
financialresearch.gov — wire later; NFCI/STLFSI are revised, documented.)
  STLFSI4  St. Louis Fed Financial Stress Index (weekly)
  NFCI     Chicago Fed National Financial Conditions Index (weekly)
  CP-bill  3M AA nonfinancial CP (DCPN3M) minus 3M T-bill (DTB3) — daily, late-1990s+
  SOFR/EFFR  secured-funding spread (2018+, structurally short — post-LIBOR)

Writes data/processed/funding_weekly.csv (indices) + funding_daily.csv (spreads).
Run:  python scripts/build_funding.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_intl_bonds import _fred_key, fred_series

WEEKLY = {"stlfsi": "STLFSI4", "nfci": "NFCI"}
DAILY = {"cp3m": "DCPN3M", "tbill3m": "DTB3", "sofr": "SOFR", "effr": "EFFR"}


def _pull(ids, key):
    out = {}
    for name, sid in ids.items():
        try:
            out[name] = fred_series(sid, key)
        except Exception as e:
            print(f"  {name} ({sid}) failed: {str(e)[:60]}")
    return out


def main() -> int:
    key = _fred_key()

    wk = _pull(WEEKLY, key)
    if wk:
        w = pd.concat(wk, axis=1).sort_index()
        w.to_csv(ROOT / "data/processed/funding_weekly.csv")
        print(f"  weekly indices: {w.index[0].date()}..{w.index[-1].date()} n={len(w)} cols={list(w.columns)}")

    dy = _pull(DAILY, key)
    if dy:
        d = pd.concat(dy, axis=1).sort_index()
        if {"cp3m", "tbill3m"}.issubset(d.columns):
            d["cp_bill_spread"] = d["cp3m"] - d["tbill3m"]      # unsecured funding premium, long history
        if {"sofr", "effr"}.issubset(d.columns):
            d["sofr_effr"] = d["sofr"] - d["effr"]              # secured-funding stress, 2018+
        d.to_csv(ROOT / "data/processed/funding_daily.csv")
        print(f"  daily spreads: {d.index[0].date()}..{d.index[-1].date()} n={len(d)} cols={list(d.columns)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
