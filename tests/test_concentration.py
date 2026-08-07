"""Construction guards for the concentration signal (Phase 4).

Two properties only — that the descriptors cannot see the future, and that the
effective-bucket count stays inside the [1, 25] bound its own arithmetic
implies. No validation bar and no hypothesis test lives here; the charter is
unsigned and the one look is unspent.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import assert_causal
import concentration

N_BUCKETS = 25


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return concentration.load_panel()


def test_build_is_causal(panel):
    assert_causal(concentration.build, panel)


def test_eff_n_within_bucket_bounds(panel):
    eff_n = concentration.build(panel)["eff_n"]
    assert eff_n.notna().all()
    assert eff_n.min() >= 1.0
    assert eff_n.max() <= N_BUCKETS


def test_top_share_is_a_share(panel):
    top = concentration.build(panel)["top_share"]
    assert top.between(1.0 / N_BUCKETS, 1.0).all()
