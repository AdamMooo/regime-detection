"""Threshold-based regime detection for thesis baseline.

Rules (VIX only — the null hypothesis the paper fights):
    VIX < 15  -> Low-Vol
    VIX > 25  -> High-Vol
    else      -> Moderate-Vol

This is deliberately simple. The paper's core argument is that the HDP-HMM
recovers structure that VIX thresholds cannot.
"""

import numpy as np
import pandas as pd
from src.config import THRESH_VOL_LOW, THRESH_VOL_HIGH


def apply_threshold_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Assign threshold regime labels to dataframe rows.

    Expects 'vol_index' column (VIX level). Adds 'threshold_regime' column
    with integer labels 0=Low-Vol, 1=Moderate-Vol, 2=High-Vol.
    """
    conditions = [
        df['vol_index'] < THRESH_VOL_LOW,
        df['vol_index'] > THRESH_VOL_HIGH,
    ]
    choices = [0, 2]
    df['threshold_regime'] = np.select(conditions, choices, default=1)
    return df


def threshold_regime_name(label: int) -> str:
    return {0: 'Low-Vol', 1: 'Moderate-Vol', 2: 'High-Vol'}[label]


if __name__ == '__main__':
    df = pd.read_csv('data/processed/train.csv', index_col=0, parse_dates=True)
    df = apply_threshold_rules(df)
    print(df['threshold_regime'].value_counts().sort_index())
