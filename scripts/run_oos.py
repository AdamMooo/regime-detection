"""Generic out-of-hypothesis-sample harness (D-20).

Built ONCE, reused by every signal — never one OOS pipeline per signal. Given a
signal's `build_region(r: pd.Series) -> pd.DataFrame` callable, it loads each
region's returns and runs the identical construction on Japan / Europe (the
standing out-of-hypothesis-sample panels, `validation-standards.md` §(d)) so the
descriptive property is confirmed to replicate — or a documented failure is
recorded — before any SUPPORT claim.

The harness only RUNS the construction on other regions and returns the frames.
It asserts nothing and makes no claim; interpretation + the one-look freeze live
with the caller. Every region panel shares the `date,mkt_ret` schema.

Usage:
    from run_oos import run_oos
    from vol_descriptors import build
    frames = run_oos(build)            # {"us": df, "japan": df, "europe": df}
"""

from pathlib import Path
from typing import Callable

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

REGION_PANELS = {
    "us": "data/processed/market_daily.csv",
    "japan": "data/processed/japan_market_daily.csv",
    "europe": "data/processed/europe_market_daily.csv",
}


def load_region(region: str) -> pd.Series:
    """Point-in-time daily returns for a region, causal by construction (raw
    returns carry no vintage surface). Raises on an unknown region."""
    path = ROOT / REGION_PANELS[region]
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    return df["mkt_ret"].astype(float).rename(f"mkt_ret_{region}")


def load_region_monthly(region: str) -> pd.Series:
    """Month-end returns for a region, compounded from its daily panel.

    For signals whose registered native clock is monthly (concentration's V5,
    stock-bond). Causal: each month uses only its own days, and the compounding
    convention matches `stockbond_corr._to_monthly` so a monthly reading means
    the same thing wherever it is built.
    """
    daily = load_region(region)
    monthly = (1.0 + daily).resample("ME").prod() - 1.0
    return monthly.rename(f"{daily.name}_monthly")


def run_oos(
    build_region: Callable[[pd.Series], pd.DataFrame],
    regions: tuple[str, ...] = ("us", "japan", "europe"),
    loader: Callable[[str], pd.Series] = load_region,
) -> dict[str, pd.DataFrame]:
    """Run `build_region` on each region's returns. Returns {region: frame}.

    `build_region` is any signal's causal construction that takes a returns
    series and returns a descriptor frame (e.g. `vol_descriptors.build`). Pass
    `loader=load_region_monthly` for a signal on the monthly clock."""
    return {region: build_region(loader(region)) for region in regions}
