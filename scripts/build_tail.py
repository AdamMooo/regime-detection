"""Tail signal inputs — options-implied tail / jump risk (Phase 9, warm-start).

Orthogonality verdict: separately priced, own time-variation vol can't explain
(Bollerslev-Todorov 2011). Options-implied is the FEASIBLE lens (free, long, PIT);
high-frequency realized-jump/bipower is data-gated (Oxford-Man library closed 2022)
→ options-implied is the warm-start scope.

Sources (free, PIT — computed same-day from live option quotes):
  CBOE SKEW    risk-neutral 30d skewness of S&P 500 (fat-left-tail pricing), 1990+.
  VIX term     VIX9D / VIX / VIX3M — the slope (inversion = near-term tail fear).
  NOTE: CBOE re-based methodology over time — series continuous, not perfectly
  methodology-homogeneous; document before any SUPPORT claim.

Writes data/processed/tail_daily.csv.
Run:  python scripts/build_tail.py
"""
import io
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CBOE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{}_History.csv"
IDX = ["SKEW", "VIX9D", "VIX", "VIX3M"]


def cboe(name: str) -> pd.Series:
    txt = requests.get(CBOE.format(name), timeout=60).text
    df = pd.read_csv(io.StringIO(txt))
    datecol = df.columns[0]
    df[datecol] = pd.to_datetime(df[datecol])
    val = name if name in df.columns else df.columns[-1]   # SKEW file: DATE,SKEW; VIX: DATE,OPEN,HIGH,LOW,CLOSE
    s = pd.Series(pd.to_numeric(df[val], errors="coerce").values, index=df[datecol]).dropna()
    return s.rename(name.lower())


def main() -> int:
    out = {}
    for name in IDX:
        try:
            out[name.lower()] = cboe(name)
        except Exception as e:
            print(f"  {name} failed: {str(e)[:60]}")
    if not out:
        print("  ALL CBOE FETCHES FAILED — wire manually next session")
        return 1
    df = pd.concat(out, axis=1).sort_index()
    if {"vix", "vix3m"}.issubset(df.columns):
        df["term_slope"] = df["vix3m"] / df["vix"] - 1.0      # >0 normal (upward), <0 inverted = near-term fear
    df.to_csv(ROOT / "data/processed/tail_daily.csv")
    print(f"  tail: {df.index[0].date()}..{df.index[-1].date()} n={len(df)} cols={list(df.columns)}")
    if "skew" in df.columns:
        print(f"    latest SKEW={df['skew'].iloc[-1]:.1f}"
              + (f"  term_slope={df['term_slope'].iloc[-1]:+.3f}" if "term_slope" in df.columns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
