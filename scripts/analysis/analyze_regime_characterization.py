"""
Analyze regime characterization: per-regime statistics, transition rates, duration.

This script runs standalone (not imported by the pipeline).
It loads regime results and price data to generate regime characterization analysis.

Run: python analyze_regime_characterization.py
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.config import DATA_DIR


def load_regime_results():
    """Load regime results from CSV."""
    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if os.path.exists(results_path):
        return pd.read_csv(results_path, index_col=0, parse_dates=True)
    return None


def load_market_data():
    """Load market data."""
    market_path = os.path.join(DATA_DIR, 'market_data.csv')
    if os.path.exists(market_path):
        return pd.read_csv(market_path, index_col=0, parse_dates=True)
    return None


def analyze_regime_statistics(results, market):
    """Analyze per-regime statistics."""
    if results is None or market is None:
        print("  ERROR: Results or market data not found")
        return

    os.makedirs('analysis', exist_ok=True)

    # Align data
    results_aligned = results.loc[results.index.intersection(market.index)]
    market_aligned = market.loc[results_aligned.index]

    # Compute returns
    spy_close = market_aligned.get('SPY_close')
    if spy_close is not None:
        returns = np.log(spy_close / spy_close.shift(1)).dropna()

        # Per-regime statistics
        regime_col = 'regime_name' if 'regime_name' in results_aligned.columns else results_aligned.columns[0]
        regimes = results_aligned[regime_col]

        stats_data = []
        for regime in regimes.unique():
            if pd.isna(regime):
                continue

            regime_mask = (regimes == regime) & (returns.index.isin(regimes.index))
            regime_returns = returns[regime_mask]

            if len(regime_returns) > 0:
                stats_data.append({
                    'Regime': regime,
                    'Mean Return (%)': regime_returns.mean() * 100,
                    'Volatility (%)': regime_returns.std() * 100,
                    'Skewness': regime_returns.skew(),
                    'Kurtosis': regime_returns.kurtosis(),
                    'N Days': len(regime_returns),
                })

        stats_df = pd.DataFrame(stats_data)
        stats_df.to_csv('analysis/regime_statistics.csv', index=False)
        print("  Saved: analysis/regime_statistics.csv")

        # Visualize statistics
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(stats_df))
        width = 0.35

        ax.bar(x - width / 2, stats_df['Mean Return (%)'], width, label='Mean Return (%)')
        ax.bar(x + width / 2, stats_df['Volatility (%)'], width, label='Volatility (%)')

        ax.set_xlabel('Regime')
        ax.set_ylabel('Value (%)')
        ax.set_title('Per-Regime Return and Volatility')
        ax.set_xticks(x)
        ax.set_xticklabels(stats_df['Regime'])
        ax.legend()

        plt.tight_layout()
        plt.savefig('analysis/regime_stats.png', dpi=100)
        print("  Saved: analysis/regime_stats.png")
        plt.close()


def analyze_transition_matrix(results):
    """Analyze regime transition rates."""
    if results is None:
        return

    os.makedirs('analysis', exist_ok=True)

    regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]
    regimes = results[regime_col].dropna()

    # Compute transition matrix
    unique_regimes = regimes.unique()
    n_regimes = len(unique_regimes)
    regime_map = {r: i for i, r in enumerate(unique_regimes)}

    transition_matrix = np.zeros((n_regimes, n_regimes))
    for i in range(len(regimes) - 1):
        from_idx = regime_map[regimes.iloc[i]]
        to_idx = regime_map[regimes.iloc[i + 1]]
        transition_matrix[from_idx, to_idx] += 1

    # Normalize to get probabilities
    row_sums = transition_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    transition_probs = transition_matrix / row_sums

    # Visualize
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        transition_probs,
        annot=True,
        fmt='.2%',
        cmap='YlOrRd',
        xticklabels=unique_regimes,
        yticklabels=unique_regimes,
        ax=ax,
        cbar_kws={'label': 'Probability'}
    )
    ax.set_title('Regime Transition Matrix')
    ax.set_xlabel('To Regime')
    ax.set_ylabel('From Regime')

    plt.tight_layout()
    plt.savefig('analysis/transition_matrix.png', dpi=100)
    print("  Saved: analysis/transition_matrix.png")
    plt.close()


def analyze_regime_duration(results):
    """Analyze regime duration statistics."""
    if results is None:
        return

    os.makedirs('analysis', exist_ok=True)

    regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]
    regimes = results[regime_col].dropna()

    # Compute duration of each regime spell
    durations_by_regime = {r: [] for r in regimes.unique()}
    current_regime = regimes.iloc[0]
    duration = 1

    for i in range(1, len(regimes)):
        if regimes.iloc[i] == current_regime:
            duration += 1
        else:
            durations_by_regime[current_regime].append(duration)
            current_regime = regimes.iloc[i]
            duration = 1

    durations_by_regime[current_regime].append(duration)

    # Compute statistics
    duration_stats = []
    for regime, durations in durations_by_regime.items():
        if len(durations) > 0:
            duration_stats.append({
                'Regime': regime,
                'Mean Duration': np.mean(durations),
                'Median Duration': np.median(durations),
                'Max Duration': np.max(durations),
                'Min Duration': np.min(durations),
            })

    duration_df = pd.DataFrame(duration_stats)

    # Visualize
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(duration_df))
    width = 0.2

    ax.bar(x - width, duration_df['Mean Duration'], width, label='Mean')
    ax.bar(x, duration_df['Median Duration'], width, label='Median')
    ax.bar(x + width, duration_df['Max Duration'], width, label='Max')

    ax.set_xlabel('Regime')
    ax.set_ylabel('Duration (days)')
    ax.set_title('Regime Duration Statistics')
    ax.set_xticks(x)
    ax.set_xticklabels(duration_df['Regime'])
    ax.legend()

    plt.tight_layout()
    plt.savefig('analysis/regime_duration.png', dpi=100)
    print("  Saved: analysis/regime_duration.png")
    plt.close()


def main():
    """Generate regime characterization analysis outputs."""
    print("Regime characterization analysis...")

    results = load_regime_results()
    market = load_market_data()

    if results is None:
        print("ERROR: No regime results available. Run 'python run.py' first.")
        return

    analyze_regime_statistics(results, market)
    analyze_transition_matrix(results)
    analyze_regime_duration(results)

    print("Regime characterization analysis complete. Files saved to analysis/")


if __name__ == '__main__':
    main()
