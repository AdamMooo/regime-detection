import pandas as pd
import numpy as np

def threshold_regimes(df):
    # Threshold rules: vol<15% and wti>0 = bull (0), vol>25% or wti<-5% = bear (2), else neutral (1)
    conditions = [
        (df['tsx_vol'] < 15) & (df['wti_shock'] > 0),
        (df['tsx_vol'] > 25) | (df['wti_shock'] < -0.05),
        True  # neutral
    ]
    choices = [0, 2, 1]  # bull, bear, neutral
    df['regime'] = np.select(conditions, choices)
    return df

if __name__ == '__main__':
    df = pd.read_csv('data/processed/xeg_macros.csv', index_col=0, parse_dates=True)
    df = threshold_regimes(df)
    print(df['regime'].value_counts())
    print("Threshold regimes applied.")