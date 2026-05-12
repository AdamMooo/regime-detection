"""Threshold-based regime detection for thesis.

Rules: bull if vol_index < 15 and wti_shock > 0, bear if vol_index > 25 or wti_shock < -5%, else neutral.
"""

import pandas as pd
import numpy as np
from src.config import THRESH_VOL_LOW, THRESH_VOL_HIGH, THRESH_WTI_POS, THRESH_WTI_NEG


def apply_threshold_rules(df: pd.DataFrame) -> pd.DataFrame:
    conditions = [
        (df['vol_index'] < THRESH_VOL_LOW) & (df['wti_shock'] > THRESH_WTI_POS),
        (df['vol_index'] > THRESH_VOL_HIGH) | (df['wti_shock'] < THRESH_WTI_NEG),
        True
    ]
    regimes = [0, 2, 1]  # bull, bear, neutral
    df['threshold_regime'] = np.select(conditions, regimes)
    return df


if __name__ == '__main__':
    df = pd.read_csv('data/processed/train.csv', index_col=0, parse_dates=True)
    df = apply_threshold_rules(df)
    print(df['threshold_regime'].value_counts())