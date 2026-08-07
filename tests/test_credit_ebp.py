"""Look-ahead and publication-lag guards for the credit (EBP) construction.

Credit is the first signal in the repo built from a published, revised series
rather than from returns, so it has two failure modes the return-built signals
do not: look-ahead in the code, and a reading attributed to a date before it was
published. One test each. (The third failure mode — vintage revision inside the
DATA — is not testable here by construction; it is stamped, not asserted.)
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import credit_ebp
from causal import assert_causal


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return credit_ebp.load_panel()


def test_build_is_causal(panel):
    assert_causal(credit_ebp.build, panel)


def test_publication_lag_defers_the_live_end(panel):
    out = credit_ebp.build(panel)
    last_published = panel.index[-1]

    readable_now = out.loc[:last_published]
    assert readable_now["obs_date"].iloc[-1] < last_published
    assert readable_now["ebp"].iloc[-1] != panel["ebp"].iloc[-1]

    lag = credit_ebp.PUBLICATION_LAG_MONTHS
    assert readable_now["obs_date"].iloc[-1] == panel.index[-1 - lag]
    assert out.index[-1] == last_published + pd.DateOffset(months=lag)


def test_vintage_is_stamped(panel):
    vintage = credit_ebp.build(panel).attrs["vintage"]
    assert len(vintage["sha256"]) == 64
    assert vintage["built"] and vintage["source"]
