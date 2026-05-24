"""Parametric 3-state Gaussian HMM baseline for thesis.

Uses hmmlearn GaussianHMM on the same 4 features as the HDP-HMM,
providing a fair parametric comparison (fixed K, EM-fitted).

The key difference from HDP-HMM:
    - K fixed at 3 (HDP-HMM learns K from data)
    - EM point estimates (HDP-HMM has full Bayesian posterior)
    - No sticky prior (HDP-HMM has kappa stickiness term)
"""

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from src.config import PARAMETRIC_K_REGIMES, RANDOM_SEED, FEATURES


def fit_parametric_hmm(X_train: np.ndarray, n_restarts: int = 10) -> GaussianHMM:
    """Fit GaussianHMM with multiple restarts, return best by log-likelihood."""
    best_model = None
    best_score = -np.inf
    for i in range(n_restarts):
        model = GaussianHMM(
            n_components=PARAMETRIC_K_REGIMES,
            covariance_type='diag',
            n_iter=500,
            tol=1e-4,
            random_state=RANDOM_SEED + i,
        )
        try:
            model.fit(X_train)
            score = model.score(X_train)
            if score > best_score:
                best_score = score
                best_model = model
        except Exception:
            continue
    if best_model is None:
        raise RuntimeError("All HMM fitting attempts failed")
    print(f"Parametric HMM: best log-likelihood = {best_score:.2f}")
    return best_model


def get_filtered_states(model: GaussianHMM, X: np.ndarray) -> tuple:
    """Forward-pass filtered states only (causal, no lookahead)."""
    _, posteriors = model.score_samples(X)
    row_sums = posteriors.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1.0, row_sums)
    posteriors = posteriors / row_sums
    return np.argmax(posteriors, axis=1), posteriors


def relabel_by_vix(model: GaussianHMM, X: np.ndarray, vix_series: np.ndarray) -> dict:
    """Map internal state indices to Low-Vol / Moderate-Vol / High-Vol by mean VIX rank."""
    state_seq, _ = get_filtered_states(model, X)
    avg_vix = {s: vix_series[state_seq == s].mean()
               for s in range(PARAMETRIC_K_REGIMES)
               if (state_seq == s).sum() > 0}
    sorted_states = sorted(avg_vix, key=avg_vix.get)
    labels = ['Low-Vol', 'Moderate-Vol', 'High-Vol']
    return {sorted_states[i]: labels[i] for i in range(len(sorted_states))}


if __name__ == '__main__':
    df = pd.read_csv('data/processed/train.csv', index_col=0, parse_dates=True)
    cols = [c for c in FEATURES if c in df.columns]
    X = df[cols].values
    scaler = StandardScaler().fit(X)
    X_scaled = scaler.transform(X)
    model = fit_parametric_hmm(X_scaled)
    states, _ = get_filtered_states(model, X_scaled)
    name_map = relabel_by_vix(model, X_scaled, df['vol_index'].values)
    print(pd.Series([name_map[s] for s in states]).value_counts())
