"""Shared run constants + arm-construction helpers for the frozen chapter-1 protocol.

Extracted from run_backtest.py (2026-07-27) when the Ch1/Ch2 one-look battery runners were
removed from the tree (one-look spent, chapters closed — see NOTES.md). This module holds only
what the live label pipeline (live_label.py → regime_signal.py → results/regime_card.json) still
needs: the frozen protocol's constants and two small arm-return helpers. Reproducible battery
logic at git commit 51fbeff (last commit before removal).
"""

import numpy as np

from backtest import strategy_returns

START = "1970-01-01"
TRAIN0 = 5040          # ~20y -> scoring starts ~1990 (Adam's era focus, 2026-07-22)
REFIT = 252
VAL = 2016             # 8y lambda-validation window (field standard)
LAMBDA_GRID = [10.0, 25.0, 50.0, 100.0, 200.0, 400.0, 800.0]
N_INIT = 8
DELAY = 2              # next-close execution (headline); delay=1 is sensitivity only
COST = 10.0


def maxdd(ret):
    eq = np.cumprod(1.0 + np.asarray(ret))
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())


def arm_returns(w_full, r_full, rf_full, oos, delay=DELAY, cost=COST):
    return strategy_returns(w_full, r_full, rf_full, cost_bps=cost, delay=delay)[oos]
