"""Credit descriptors — the excess bond premium as a continuous reading (Level-0).

The EBP (Gilchrist-Zakrajsek 2012; Favara-Gilchrist-Lewis-Zakrajsek, Fed FEDS
Notes, monthly) is the corporate credit spread purged of the modelled
expected-default component — the price of bearing credit risk that expected
losses do not explain. Raw spreads were REJECTED as the reading (~85% shared
with the equity-volatility axis); only the residual is admitted.

Descriptors, in the same shape as `vol_descriptors.build`: the level, its causal
expanding-window rarity, and its causal expanding z. No state, no label, no
forecast — this module measures and STOPS.

TWO THINGS THIS SIGNAL HAS THAT NONE OF THE RETURN-BUILT SIGNALS DO:

1. A VINTAGE SURFACE. The EBP is a regression residual refit monthly on the full
   sample, so the Board warns that "the entire history of the EBP may revise each
   month" — the value printed today for March 2008 embeds coefficients estimated
   through today. `assert_causal` cannot see this: the code is causal, the DATA is
   not. So every build stamps the sha256 of its source and the date it ran
   (`results/credit_vintage.json`), and any later result can be tied to the exact
   vintage it was computed from.

2. A PUBLICATION LAG. Month t is published during month t+1, so a causal read may
   not use month t before the end of t+1 — see PUBLICATION_LAG_MONTHS.

Run:  python scripts/credit_ebp.py
"""

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import expanding_percentile, expanding_z

SOURCE = ROOT / "data/processed/credit_monthly.csv"

# Month t publishes during month t+1 and is unavailable until the END of t+1; on a
# month-start index that is the t+2 row, so the whole descriptor frame is shifted
# forward two rows onto an "as of" index — the date a reader could actually hold
# the reading. Conservative vs the ~5-7 week lag verified in archived vintages.
PUBLICATION_LAG_MONTHS = 2

BURN_IN_MONTHS = 120


def _vintage(payload: bytes, source: str) -> dict:
    return {
        "source": source,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "built": date.today().isoformat(),
    }


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(SOURCE, parse_dates=["date"]).set_index("date").sort_index()
    df.attrs["vintage"] = _vintage(SOURCE.read_bytes(), str(SOURCE.relative_to(ROOT)).replace("\\", "/"))
    return df


def build(panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """Descriptor frame for a monthly credit panel (column `ebp`, month-start index).

    Returns a frame indexed by AS-OF date — the month from which the reading is
    publishable — carrying the observation month it refers to. `est_prob` is
    excluded entirely: it is an explicit recession forecast and has no place here.
    Causal throughout; guarded by `assert_causal` in tests/test_credit_ebp.py.
    """
    if panel is None:
        panel = load_panel()

    ebp = panel["ebp"].astype(float).rename("ebp")
    warm = ebp.notna().cumsum() >= BURN_IN_MONTHS

    out = pd.DataFrame({
        "obs_date": ebp.index,
        "ebp": ebp,
        "ebp_pctile": expanding_percentile(ebp).where(warm),
        "ebp_z": expanding_z(ebp, min_periods=BURN_IN_MONTHS),
    })
    out.index = out.index + pd.DateOffset(months=PUBLICATION_LAG_MONTHS)
    out.index.name = "as_of"
    out.attrs["vintage"] = panel.attrs.get("vintage") or _vintage(panel.to_csv().encode(), "in-memory panel")
    return out


# ── driver / presentation ───────────────────────────────────────────────────────

def _print_latest(df: pd.DataFrame) -> None:
    d = df.dropna(subset=["ebp_pctile"])
    latest = d.iloc[-1]
    print("=" * 62)
    print(f"CREDIT / EBP DESCRIPTORS — publishable as of {d.index[-1].date()}")
    print("=" * 62)
    print(f"  observation month:      {latest['obs_date'].date()}  (publication lag {PUBLICATION_LAG_MONTHS} months)")
    print(f"  excess bond premium:    {latest['ebp']:+.3f} pp")
    print(f"  level percentile:       {latest['ebp_pctile'] * 100:5.1f}th  (of its own history to date)")
    print(f"  level z:                {latest['ebp_z']:+5.2f}")
    print("  vintage: the published EBP restates each month — this reading is stamped, not settled.")


def main() -> int:
    df = build()
    _print_latest(df)
    csv = ROOT / "results" / "credit_descriptors.csv"
    df.to_csv(csv)
    stamp = ROOT / "results" / "credit_vintage.json"
    stamp.write_text(json.dumps(df.attrs["vintage"], indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {csv.relative_to(ROOT)}  and  {stamp.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
