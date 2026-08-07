"""Tail descriptors — the price of one month of downside protection (Level-0).

Cboe SKEW is a RISK-NEUTRAL price, not a probability. It is the Bakshi-Kapadia-Madan
(2003) third moment of the 30-day SPX log return, published on the scale

    SKEW = 100 - 10 * S      ->      S = (100 - SKEW) / 10

where S is the risk-neutral skewness (negative = the market charges more for
out-of-the-money downside than a symmetric density implies). This module reports S in
its NATIVE sign — the vendor's 100-scale inverts it and reliably reads as "up = safer"
— plus its causal rarity (expanding percentile and expanding z), and STOPS.

The reading is a PRICE, never a probability. A strike cross-section identifies only the
risk-neutral density q = p*m/E[m], never the split into the physical density p and the
pricing kernel m, and Bollerslev-Todorov (2011) find the left/right asymmetry that skew
measures is significant only under q. Nothing here may be translated into a likelihood,
odds, or expected frequency of a decline (charter Q6).

Run:  python scripts/tail_skew.py
"""

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import expanding_percentile, expanding_z

SOURCE = ROOT / "data/processed/tail_daily.csv"

# The BKM strike-grid error is confounded with the index level (1990 SPX ~350 on a $5 grid
# violates the ~0.1%-of-forward accuracy requirement by ~14x; today's 0.083% satisfies it),
# so pre-2000 data would manufacture a downward trend in the rarity descriptor itself.
START = pd.Timestamp("2000-01-01")


def _read_raw() -> pd.DataFrame:
    """Full published history, unrestricted — used ONLY for the vintage stamp, whose whole
    job is to detect revisions to the pre-2000 backfill."""
    df = pd.read_csv(SOURCE, parse_dates=["DATE"]).set_index("DATE").rename_axis("date")
    # `term_slope` (and the VIX legs it is built from) are deliberately not selected: same
    # moment at two horizons, no asymmetry content, three different option universes.
    return df[["skew"]].dropna()


def load_panel() -> pd.DataFrame:
    return _read_raw().loc[START:]


def build(panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """Descriptor spine for the tail signal: the level of the priced asymmetry, how rare
    that level is against its own past, and how many sigmas from its own past it sits.

    Re-applies the START restriction so a caller handing over the raw 1990+ frame still
    gets a measurement-grade sample.
    """
    if panel is None:
        panel = load_panel()
    skew = panel["skew"].astype(float).loc[START:]
    rn_skew = ((100.0 - skew) / 10.0).rename("rn_skew")
    return pd.DataFrame({
        "skew": skew,
        "rn_skew": rn_skew,
        "rn_skew_pctile": expanding_percentile(rn_skew).rename("rn_skew_pctile"),
        "rn_skew_z": expanding_z(rn_skew),
    })


def write_vintage(path: Path | None = None) -> dict:
    """Stamp the source so a silent vendor revision becomes detectable.

    Cboe's 2011 documentation published an all-time low/high of 101.09 (1991-03-21) and
    146.88 (1998-10-16); today's file gives 101.31 and 146.22 on the SAME dates. The
    history has already been revised once without notice, and a further recalculation was
    determined appropriate 2025-07-17 with no effective date. `assert_causal` cannot catch
    this — it guards the construction, not the data — so the extremes are recorded here.
    """
    raw = _read_raw()["skew"]
    stamp = {
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "build_date": dt.date.today().isoformat(),
        "span": [str(raw.index[0].date()), str(raw.index[-1].date())],
        "skew_min": {"value": float(raw.min()), "date": str(raw.idxmin().date())},
        "skew_max": {"value": float(raw.max()), "date": str(raw.idxmax().date())},
    }
    path = path or ROOT / "results" / "tail_vintage.json"
    path.write_text(json.dumps(stamp, indent=2) + "\n")
    return stamp


def _print_latest(df: pd.DataFrame) -> None:
    d = df.dropna(subset=["rn_skew_pctile"])
    latest, when = d.iloc[-1], d.index[-1].date()
    print("=" * 64)
    print(f"TAIL DESCRIPTORS - as of {when}   (a PRICE, not a probability)")
    print("=" * 64)
    print(f"  SKEW (vendor scale):          {latest['skew']:6.2f}")
    print(f"  Risk-neutral skewness S:      {latest['rn_skew']:+6.2f}  (more negative = dearer downside)")
    print(f"  Level percentile:             {latest['rn_skew_pctile'] * 100:5.1f}th  of its own history since {START.date()}")
    print(f"                                (LOW percentile = unusually expensive downside protection)")
    print(f"  Expanding z:                  {latest['rn_skew_z']:+6.2f}")


def main() -> int:
    df = build()
    _print_latest(df)
    csv = ROOT / "results" / "tail_skew.csv"
    df.to_csv(csv)
    stamp = write_vintage()
    print(f"\nwrote {csv.relative_to(ROOT)}  and  results/tail_vintage.json")
    print(f"  vintage sha256 {stamp['sha256'][:16]}...  min {stamp['skew_min']['value']} "
          f"({stamp['skew_min']['date']})  max {stamp['skew_max']['value']} ({stamp['skew_max']['date']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
