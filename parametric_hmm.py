import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
import numpy as np

def parametric_hmm(df):
    # Use XEG returns as observation
    df['xeg_return'] = df['xeg_close'].pct_change()
    df = df.dropna()

    # Fit 3-state Markov switching model
    model = MarkovRegression(df['xeg_return'], k_regimes=3, switching_variance=True)
    result = model.fit()

    # Get smoothed probabilities
    probs = result.smoothed_marginal_probabilities
    df['regime'] = np.argmax(probs.values, axis=1)

    print("Parametric HMM fitted.")
    print(f"Regime counts: {df['regime'].value_counts()}")
    return df, result

if __name__ == '__main__':
    df = pd.read_csv('data/processed/xeg_macros.csv', index_col=0, parse_dates=True)
    df, result = parametric_hmm(df)
    print("Parametric HMM done.")