import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from regime_signal import stay_probability


def test_stay_probability_handles_brand_new_state():
    # state 1 appears only on the last day (no day-after to transition from) —
    # crosstab has no row for it; must not KeyError.
    states = pd.Series([0, 0, 0, 0, 1])
    assert stay_probability(states, 1) == 1.0


def test_stay_probability_normal_case():
    states = pd.Series([0, 0, 1, 1, 1, 0, 0])
    p0 = stay_probability(states, 0)
    p1 = stay_probability(states, 1)
    assert 0.0 <= p0 <= 1.0 and 0.0 <= p1 <= 1.0
