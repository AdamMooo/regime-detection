"""Parametric HMM using statsmodels for thesis baseline."""

import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
from src.config import PARAMETRIC_K_REGIMES


def fit_parametric_hmm(df: pd.DataFrame):
    df['xeg_return'] = df['xeg_price'].pct_change().fillna(0)
    model = MarkovRegression(df['xeg_return'], k_regimes=PARAMETRIC_K_REGIMES, switching_variance=True)
    result = model.fit()
    df['parametric_regime'] = result.smoothed_marginal_probabilities.idxmax(axis=1)
    return df, result


if __name__ == '__main__':
    df = pd.read_csv('data/processed/train.csv', index_col=0, parse_dates=True)
    df, result = fit_parametric_hmm(df)
    print(df['parametric_regime'].value_counts())