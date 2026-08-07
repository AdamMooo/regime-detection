"""Concentration descriptors — the monthly capital-distribution reading (Level-0).

Assumption monitored: "the index is not dependent on a few names."

The reading is the effective number of independent capital buckets,
eff_n = 1 / sum_i s_i^2 over the 25 Ken French ME x BE/ME buckets (the reciprocal
Herfindahl — Herfindahl 1950; Hirschman 1945; "effective number of bets", Meucci
2009), plus the largest bucket's share of index capital. Both are arithmetic
properties of a capital distribution at a point in time, not forecasts.

Two rarity lenses on the level, both causal and both from causal.py:
  - expanding percentile — distribution-free, "how often has it been this low"
  - expanding z          — scale-aware, "how many sigmas from its own past mean"

Neither answers "is concentration too high" — there is no such threshold, and the
measurement cannot separate winner-take-most economics from a narrow re-rating.
Reading + rarity, then STOP.

Charter (DRAFT, unsigned): .planning/phases/04-concentration-signal/
04-CONCENTRATION-CHARTER-DRAFT.md. No validation bar is run here.

Run:  python scripts/concentration.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import expanding_percentile, expanding_z

MIN_MONTHS = 120


def load_panel() -> pd.DataFrame:
    p = ROOT / "data/processed/concentration_monthly.csv"
    return pd.read_csv(p, parse_dates=["date"]).set_index("date").astype(float)


def build(panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """Descriptor spine for a monthly capital-share panel. Defaults to the US
    panel; pass any region's frame (same eff_n / top_share columns) to build the
    same descriptors elsewhere."""
    if panel is None:
        panel = load_panel()
    eff_n = panel["eff_n"].astype(float).rename("eff_n")
    return pd.DataFrame({
        "eff_n": eff_n,
        "top_share": panel["top_share"].astype(float),
        "eff_n_pctile": expanding_percentile(eff_n).rename("eff_n_pctile"),
        "eff_n_z": expanding_z(eff_n, min_periods=MIN_MONTHS),
    })


def _print_latest(df: pd.DataFrame) -> None:
    d = df.dropna(subset=["eff_n", "eff_n_pctile"])
    latest = d.iloc[-1]
    print("=" * 60)
    print(f"CONCENTRATION DESCRIPTORS — as of {d.index[-1].date()}")
    print("=" * 60)
    print(f"  Effective buckets (of 25):  {latest['eff_n']:5.2f}")
    print(f"  Largest bucket's capital:   {latest['top_share'] * 100:5.1f}%")
    print(f"  Level percentile:           {latest['eff_n_pctile'] * 100:5.1f}th  (of its own history to date)")
    print(f"  Level z:                    {latest['eff_n_z']:+5.2f}")


def main() -> int:
    df = build()
    _print_latest(df)
    csv = ROOT / "results" / "concentration_descriptors.csv"
    csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv)
    print(f"\nwrote {csv.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
