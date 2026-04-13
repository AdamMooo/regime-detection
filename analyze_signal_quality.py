"""
Analyze signal quality: regime persistence, probability trends, confidence, switches.

This script runs standalone (not imported by the pipeline).
It loads regime results to analyze signal quality and regime persistence metrics.

Run: python analyze_signal_quality.py
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config import DATA_DIR


def load_regime_results():
    """Load regime results from CSV."""
    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if os.path.exists(results_path):
        return pd.read_csv(results_path, index_col=0, parse_dates=True)
    return None


def analyze_regime_persistence(results):
    """Analyze regime persistence (duration between switches)."""
    if results is None:
        print("  ERROR: Results not found")
        return

    os.makedirs('analysis', exist_ok=True)

    regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]
    regimes = results[regime_col].dropna()

    # Compute persistence (consecutive days in same regime)
    durations = []
    current_duration = 1

    for i in range(1, len(regimes)):
        if regimes.iloc[i] == regimes.iloc[i - 1]:
            current_duration += 1
        else:
            durations.append(current_duration)
            current_duration = 1

    durations.append(current_duration)

    # Visualize
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Histogram
    ax1.hist(durations, bins=20, edgecolor='black')
    ax1.set_xlabel('Duration (days)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Regime Duration')
    ax1.axvline(np.mean(durations), color='r', linestyle='--', label=f'Mean: {np.mean(durations):.1f}')
    ax1.legend()

    # Box plot
    ax2.boxplot(durations)
    ax2.set_ylabel('Duration (days)')
    ax2.set_title('Regime Duration Box Plot')
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('analysis/regime_persistence.png', dpi=100)
    print("  Saved: analysis/regime_persistence.png")
    plt.close()

    # Print statistics
    print(f"  Persistence statistics:")
    print(f"    Mean duration: {np.mean(durations):.1f} days")
    print(f"    Median duration: {np.median(durations):.1f} days")
    print(f"    Max duration: {np.max(durations)} days")
    print(f"    Min duration: {np.min(durations)} days")


def analyze_regime_probabilities(results):
    """Analyze regime probability trends over time."""
    if results is None:
        return

    os.makedirs('analysis', exist_ok=True)

    # Extract probability columns
    prob_cols = [c for c in results.columns if c.startswith('prob_')]

    if len(prob_cols) == 0:
        print("  WARNING: No probability columns found")
        return

    prob_df = results[prob_cols].copy()
    prob_df.columns = [c.replace('prob_', 'Regime ') for c in prob_cols]

    # Visualize as stacked area chart
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.stackplot(
        range(len(prob_df)),
        *[prob_df[col].values for col in prob_df.columns],
        labels=prob_df.columns,
        alpha=0.7
    )

    ax.set_xlabel('Time (days)')
    ax.set_ylabel('Probability')
    ax.set_title('Regime Probability Time Series')
    ax.legend(loc='upper left')
    ax.set_ylim([0, 1])

    plt.tight_layout()
    plt.savefig('analysis/regime_probabilities.png', dpi=100)
    print("  Saved: analysis/regime_probabilities.png")
    plt.close()


def analyze_regime_confidence(results):
    """Analyze model confidence (max probability across regimes)."""
    if results is None:
        return

    os.makedirs('analysis', exist_ok=True)

    # Extract probability columns
    prob_cols = [c for c in results.columns if c.startswith('prob_')]

    if len(prob_cols) == 0:
        return

    prob_df = results[prob_cols]

    # Confidence = max probability
    confidence = prob_df.max(axis=1)

    # Visualize
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(range(len(confidence)), confidence.values, linewidth=1, alpha=0.7)
    ax.fill_between(range(len(confidence)), confidence.values, alpha=0.3)
    ax.axhline(y=confidence.mean(), color='r', linestyle='--', label=f'Mean: {confidence.mean():.2%}')
    ax.set_xlabel('Time (days)')
    ax.set_ylabel('Confidence')
    ax.set_title('Model Confidence Over Time')
    ax.set_ylim([0, 1])
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('analysis/regime_confidence.png', dpi=100)
    print("  Saved: analysis/regime_confidence.png")
    plt.close()

    # Print statistics
    print(f"  Confidence statistics:")
    print(f"    Mean confidence: {confidence.mean():.2%}")
    print(f"    Median confidence: {confidence.median():.2%}")
    print(f"    Min confidence: {confidence.min():.2%}")


def analyze_regime_switches(results):
    """Analyze regime switches and transitions."""
    if results is None:
        return

    os.makedirs('analysis', exist_ok=True)

    regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]
    regimes = results[regime_col].dropna()

    # Find switches
    switches = []
    for i in range(1, len(regimes)):
        if regimes.iloc[i] != regimes.iloc[i - 1]:
            switches.append(i)

    # Visualize with regime series
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot regime names (numeric encoding for visualization)
    regime_map = {r: i for i, r in enumerate(regimes.unique())}
    regime_nums = [regime_map[r] for r in regimes.values]

    ax.plot(range(len(regime_nums)), regime_nums, linewidth=1, marker='.')

    # Mark switches with vertical lines
    for switch_idx in switches:
        ax.axvline(x=switch_idx, color='r', alpha=0.3, linestyle='--')

    ax.set_xlabel('Time (days)')
    ax.set_ylabel('Regime')
    ax.set_title(f'Regime Switches Over Time ({len(switches)} total switches)')
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('analysis/regime_switches.png', dpi=100)
    print("  Saved: analysis/regime_switches.png")
    plt.close()

    # Print statistics
    print(f"  Switch statistics:")
    print(f"    Total switches: {len(switches)}")
    print(f"    Average duration between switches: {len(regimes) / (len(switches) + 1):.1f} days")


def main():
    """Generate signal quality analysis outputs."""
    print("Signal quality analysis...")

    results = load_regime_results()

    if results is None:
        print("ERROR: No regime results available. Run 'python run.py' first.")
        return

    analyze_regime_persistence(results)
    analyze_regime_probabilities(results)
    analyze_regime_confidence(results)
    analyze_regime_switches(results)

    print("Signal quality analysis complete. Files saved to analysis/")


if __name__ == '__main__':
    main()
