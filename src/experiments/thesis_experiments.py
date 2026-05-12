"""Thesis experiments: Run baselines and HDP-HMM, compute metrics."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.core.hdp_hmm import fit_hdp_hmm
from src.baselines.threshold_rules import apply_threshold_rules
from src.baselines.parametric_hmm import fit_parametric_hmm
from src.config import FEATURES, COVID_START, COVID_END, COVID_DRAWDOWN_THRESH


def load_train():
    return pd.read_csv('data/processed/train.csv', index_col=0, parse_dates=True)


def run_baselines(df):
    df = apply_threshold_rules(df)
    df, param_result = fit_parametric_hmm(df)
    return df, param_result


def run_hdp_hmm(df):
    obs = df[FEATURES].values
    svi_result, samples = fit_hdp_hmm(obs)
    # Add regime to df
    # For simplicity, use argmax of posterior mean
    beta_mean = samples['beta'].mean(axis=0)
    # But for regimes, need to assign per time step
    # This is simplified; in reality, use filtered probs
    df['hdp_regime'] = 0  # placeholder
    return df, svi_result, samples


def compute_metrics(df):
    # Simplified metrics
    covid_period = df.loc[COVID_START:COVID_END]
    if len(covid_period) > 0:
        covid_f1 = len(covid_period) / len(df)  # placeholder
    else:
        covid_f1 = 0
    stability = df['hdp_regime'].value_counts().max() / len(df)
    return {'covid_f1': covid_f1, 'stability': stability}


def plot_diagnostics(svi_result):
    plt.plot(svi_result.losses)
    plt.title('HDP-HMM SVI Convergence')
    plt.savefig('figures/day1_hdp_diagnostics.png')
    plt.close()


def day1_experiment():
    df = load_train()
    df, param_result = run_baselines(df)
    df, svi_result, samples = run_hdp_hmm(df)
    metrics = compute_metrics(df)
    plot_diagnostics(svi_result)
    print("Day 1 complete.")
    print(f"Metrics: {metrics}")


if __name__ == '__main__':
    day1_experiment()