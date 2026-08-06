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
    """The other built signal. Two-input (equity x bond), so this also exercises
    the guard's DataFrame path — which credit / funding / tail will need."""
    import stockbond_corr as sb

    eq, bond = sb.load_returns()
    panel = pd.DataFrame({"eq": eq, "bond": bond}).tail(4000)

    def build(d: pd.DataFrame) -> pd.DataFrame:
        corr = sb.rolling_corr(d["eq"], d["bond"], sb.PRIMARY_W)
        return pd.DataFrame({"corr": corr, "z": sb.expanding_z(corr), "state": sb.sign_state(corr)})

    assert_causal(build, panel)


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
