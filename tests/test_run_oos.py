"""Guards for the shared out-of-hypothesis-sample harness.

The harness itself asserts nothing, so what needs testing is its loaders: a
monthly reading that quietly reached into the next month, or that landed on a
different grid per region, would corrupt every monthly signal's OOS run at once.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import assert_causal
from run_oos import load_region, load_region_monthly, run_oos

REGIONS = ("us", "japan", "europe")


def test_monthly_compounding_is_causal():
    """Each month may use only its own days."""
    daily = load_region("us").tail(4000)
    assert_causal(lambda r: (1.0 + r).resample("ME").prod() - 1.0, daily)


def test_monthly_is_month_end_and_gapless():
    for region in REGIONS:
        m = load_region_monthly(region)
        assert m.notna().all(), region
        assert (m.index == m.index + pd.offsets.MonthEnd(0)).all(), region
        steps = pd.Series(m.index.to_period("M").astype("int64")).diff().dropna()
        assert (steps == 1).all(), region


def test_monthly_compounds_its_own_daily_month():
    daily = load_region("us")
    m = load_region_monthly("us")
    at = m.index[-40]
    days = daily[(daily.index > at - pd.offsets.MonthEnd(1)) & (daily.index <= at)]
    assert m.loc[at] == pytest.approx(float((1.0 + days).prod() - 1.0))


def test_harness_honours_the_loader():
    daily = run_oos(lambda r: r.to_frame("x"), regions=("us",))
    monthly = run_oos(lambda r: r.to_frame("x"), regions=("us",), loader=load_region_monthly)
    assert len(monthly["us"]) < len(daily["us"]) / 15
