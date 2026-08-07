"""Valuation descriptors — the price-level axis (Level-0).

Where the broad equity market's price sits relative to its own history, measured
as CAPE (Shiller PE10 — the Campbell-Shiller 1988 object) and expressed as a
level plus how unusual that level is against its OWN past. Descriptive
measurement only: nothing here claims, tests or implies anything about forward
returns — that is the frozen charter's single one-look
(.planning/phases/03-valuation-signal/), not this module's business.

POINT-IN-TIME is the whole difficulty. CAPE read straight off Shiller's file is
NOT what an observer could have computed at the time: the trailing-10y earnings
average dated month t contains quarters that had not been reported yet, and the
CPI deflating it had not been released. Both legs therefore carry an explicit,
named publication lag; the price leg carries none, because the price IS
observable today. Guarded by `assert_causal` in tests/test_valuation.py.

Run:  python scripts/valuation.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import expanding_percentile, expanding_z

CAPE_WINDOW_M = 120

# Lags are in ROWS of a contiguous monthly grid (guaranteed + gated by build_valuation.py).
#
# S&P's aggregate quarterly as-reported earnings land ~3 months after the quarter
# ends, and Shiller's monthly earnings series linearly interpolates BETWEEN quarter
# endpoints, so month t can embed the endpoint up to 2 months ahead of it: 5 months
# is the first lag that uses only figures already published. The source file agrees
# from its own side — its Aug-2026 vintage carries earnings through Mar-2026.
EARNINGS_PUBLICATION_LAG_M = 5

# BLS releases month t's CPI in mid-month t+1.
CPI_PUBLICATION_LAG_M = 1

# ~20y of monthly readings before the "how unusual" z-score is meaningful; the
# percentile is distribution-free and needs no such floor.
Z_MIN_MONTHS = 240


def load_panel() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data/processed/valuation_monthly.csv",
                       parse_dates=["date"]).set_index("date")


def build(panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """Descriptor frame for a monthly valuation panel (price, earnings, cpi).

    Panel-argument by signature so the shared OOS harness can drive the same
    construction on another region; defaults to the US home panel.
    """
    if panel is None:
        panel = load_panel()

    cpi = panel["cpi"].shift(CPI_PUBLICATION_LAG_M)
    real_price = (panel["price"] / cpi).rename("real_price")
    real_earnings = panel["earnings"] / cpi

    # the lag binds on the EARNINGS leg only — today's price is observable, the
    # trailing-earnings average behind it is not
    e10 = (real_earnings.shift(EARNINGS_PUBLICATION_LAG_M)
           .rolling(CAPE_WINDOW_M).mean().rename("real_earn_10y"))
    cape = (real_price / e10).rename("cape")

    return pd.DataFrame({
        "real_price": real_price,
        "real_earn_10y": e10,
        "cape": cape,
        "cape_pctile": expanding_percentile(cape).rename("cape_pctile"),
        "cape_z": expanding_z(cape, min_periods=Z_MIN_MONTHS),
    }).dropna(subset=["cape"])


def _print_latest(df: pd.DataFrame, panel: pd.DataFrame) -> None:
    latest = df.iloc[-1]
    d = df.index[-1].date()
    print("=" * 66)
    print(f"VALUATION DESCRIPTORS - as of {d}")
    print("=" * 66)
    print(f"  CAPE (point-in-time):   {latest['cape']:6.1f}")
    print(f"  Level percentile:       {latest['cape_pctile'] * 100:6.1f}th  (of its own history to date)")
    if pd.notna(latest["cape_z"]):
        print(f"  Level z:                {latest['cape_z']:+6.2f}   (vs its own past, expanding)")
    tail = df["cape"].tail(13)
    if len(tail) == 13:
        print(f"  12-month change:        {tail.iloc[-1] - tail.iloc[0]:+6.1f}  points")
    published = panel["cape"].reindex(df.index).iloc[-1]
    print(f"\n  construction: earnings lagged {EARNINGS_PUBLICATION_LAG_M} months, CPI "
          f"{CPI_PUBLICATION_LAG_M} month; as-published CAPE for the same month "
          f"{published:.1f} (diff {latest['cape'] - published:+.1f})")


def main() -> int:
    panel = load_panel()
    df = build(panel)
    _print_latest(df, panel)
    (ROOT / "results").mkdir(exist_ok=True)
    csv = ROOT / "results" / "valuation_descriptors.csv"
    df.to_csv(csv)
    print(f"\nwrote {csv.relative_to(ROOT)}  rows={len(df)}  "
          f"span={df.index[0].date()}..{df.index[-1].date()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
