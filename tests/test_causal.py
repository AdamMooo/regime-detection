"""Look-ahead guard for the shared signal spine.

The repo's whole value proposition is point-in-time honesty, so the causal
primitives every signal imports need a test that would actually FAIL if one of
them leaked. `assert_causal` perturbs the future and demands the past not move;
`test_guard_catches_a_real_leak` proves the guard itself has teeth.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import assert_causal, ewma_vol, expanding_percentile, realized_vol
import vol_descriptors


@pytest.fixture(scope="module")
def returns() -> pd.Series:
    """Real US market returns, truncated — real data so the GARCH fits behave
    like production, truncated so the refit loop stays test-speed."""
    df = pd.read_csv(ROOT / "data/processed/market_daily.csv", parse_dates=["date"]).set_index("date")
    return df["mkt_ret"].astype(float).tail(2600)


def test_ewma_vol_is_causal(returns):
    assert_causal(ewma_vol, returns)


def test_realized_vol_is_causal(returns):
    assert_causal(realized_vol, returns)


def test_expanding_percentile_is_causal(returns):
    assert_causal(lambda r: expanding_percentile(ewma_vol(r)), returns)


def test_shock_half_life_is_causal(returns):
    """GARCH refits: each fit must use only its trailing window, and the
    forward-fill between refits must never reach backwards."""
    assert_causal(lambda r: vol_descriptors.shock_half_life(r, garch_window=500, step=250), returns)


def test_vol_descriptors_build_is_causal(returns):
    """The composed signal, as the OOS harness actually calls it."""
    assert_causal(vol_descriptors.build, returns)


def test_stockbond_corr_is_causal():
    """The other built signal, guarded through its REAL `build()` — two-input
    (equity x bond), so this also exercises the guard's DataFrame path, which
    credit / funding / tail will need."""
    import stockbond_corr as sb

    assert_causal(sb.build, sb.load_us_panel().tail(4000))


def test_stockbond_build_is_region_agnostic():
    """`build(panel)` must not reach for the US panel behind the caller's back —
    that was the Phase-2 blocker (it used to take no arguments at all)."""
    import stockbond_corr as sb

    panel = sb.load_us_panel().tail(3000)
    half = sb.build(panel.tail(1500))
    full = sb.build(panel)
    assert len(half) < len(full), "build() ignored the panel it was handed"


def test_stockbond_monthly_is_causal():
    """The monthly construction the OOS one-look actually runs."""
    import stockbond_corr as sb

    assert_causal(sb.build_monthly, sb.load_region_monthly("us"))


def test_guard_catches_a_real_leak(returns):
    """A full-sample (not expanding) rank is the classic leak: today's reading
    depends on the whole future distribution. The guard must reject it."""
    def leaky(r: pd.Series) -> pd.Series:
        return r.rolling(21).std().rank(pct=True).rename("full_sample_rank")

    with pytest.raises(AssertionError, match="LOOK-AHEAD LEAK"):
        assert_causal(leaky, returns)


def test_guard_catches_a_centered_window(returns):
    """A centered rolling window reads forward by half its length — the subtler
    leak, and the one that survives code review."""
    def leaky(r: pd.Series) -> pd.Series:
        return r.rolling(21, center=True).std().rename("centered_vol")

    with pytest.raises(AssertionError, match="LOOK-AHEAD LEAK"):
        assert_causal(leaky, returns)
