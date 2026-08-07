"""Point-in-time guard for the valuation signal.

The valuation reading's one real failure mode is silent look-ahead: CAPE read off
Shiller's file at month t averages earnings that had not been reported yet, so a
construction that looks perfectly causal (all `.rolling`, no `.shift(-1)`) can
still be unbuildable in real time. Two things are therefore tested: that the
build cannot see the future at all (`assert_causal`), and that the declared
reporting lag is actually applied — a constant that is defined but not wired in
would pass the first test and fail the repo's whole premise.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import assert_causal
import valuation


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return valuation.load_panel()


def test_build_is_causal(panel):
    assert_causal(valuation.build, panel)


def test_reporting_lag_is_applied(panel):
    """An earnings print dated month t must not move the reading until t + LAG.

    Spike one month's earnings and follow where it shows up: the readings for the
    LAG months that follow must be bit-identical, and the reading exactly LAG
    months later must move. That pins the lag to its declared value — an
    off-by-one or an unwired constant fails one side or the other.
    """
    lag = valuation.EARNINGS_PUBLICATION_LAG_M
    j = len(panel) - 200
    t0 = panel.index[j]

    spiked = panel.copy()
    spiked.loc[t0, "earnings"] = float(panel["earnings"].iloc[j]) * 10.0

    base, bumped = valuation.build(panel), valuation.build(spiked)
    still_blind = panel.index[j:j + lag]
    pd.testing.assert_series_equal(base.loc[still_blind, "cape"], bumped.loc[still_blind, "cape"])

    first_effect = panel.index[j + lag]
    assert base.loc[first_effect, "cape"] != bumped.loc[first_effect, "cape"], (
        f"earnings dated {t0.date()} never reached the reading at {first_effect.date()} — "
        f"EARNINGS_PUBLICATION_LAG_M={lag} is not wired into build()"
    )


def test_cape_is_within_plausible_bounds(panel):
    df = valuation.build(panel)
    assert df["cape"].between(3.0, 70.0).all(), "CAPE outside its plausible historical range"
    assert df["cape_pctile"].between(0.0, 1.0).all()
