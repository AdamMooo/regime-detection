"""Guards for the tail signal: look-ahead, and the two charter decisions that had to
land in code rather than only in prose (the 2000+ measurement-grade sample, and
`term_slope` never entering the construction)."""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import assert_causal
import tail_skew


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return tail_skew.load_panel()


def test_build_is_causal(panel):
    assert_causal(tail_skew.build, panel)


def test_loader_enforces_the_measurement_grade_start(panel):
    assert panel.index[0] >= tail_skew.START


def test_build_enforces_the_start_on_a_caller_supplied_panel():
    """The 1990s history is really in the file, so the restriction has to be doing work —
    the early strike grid violates the BKM skewness accuracy requirement by ~14x and would
    manufacture a trend in the rarity descriptor."""
    raw = tail_skew._read_raw()
    assert raw.index[0] < tail_skew.START
    assert tail_skew.build(raw).index[0] >= tail_skew.START


def test_term_slope_never_enters_the_construction(panel):
    assert list(panel.columns) == ["skew"]
    assert "term_slope" not in tail_skew.build(panel).columns


def test_native_sign_transform(panel):
    df = tail_skew.build(panel)
    assert (df["rn_skew"] == (100.0 - df["skew"]) / 10.0).all()
    assert df["rn_skew"].median() < 0, "index risk-neutral skewness is persistently negative"
