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
from src.core.evaluation import analyze_forward_returns


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


def analyze_forward_return_figures(results, market, fwd_results):
    """Save forward return boxplots by regime for SPY (1d, 5d, 21d)."""
    if results is None or market is None or not fwd_results:
        return

    os.makedirs('figures', exist_ok=True)

    regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]
    spy_prices = market.get('SPY_close')
    if spy_prices is None:
        return

    for horizon in [1, 5, 21]:
        key = ('SPY', horizon)
        if key not in fwd_results:
            continue

        fwd_ret = np.log(spy_prices.shift(-horizon) / spy_prices)
        common_idx = results.index.intersection(fwd_ret.index)
        regimes = results.loc[common_idx, regime_col]
        returns = fwd_ret.reindex(common_idx)
        valid = returns.notna()
        regimes = regimes[valid]
        returns = returns[valid] * 100  # convert to percent

        fig, ax = plt.subplots(figsize=(10, 5))
        regime_list = sorted(regimes.unique())
        data_by_regime = [returns[regimes == r].values for r in regime_list]

        bp = ax.boxplot(data_by_regime, labels=regime_list, patch_artist=True,
                        medianprops={'color': 'black', 'linewidth': 2})
        colors = ['#4C9BE8', '#F5A623', '#E84C4C', '#7ED321']
        for patch, color in zip(bp['boxes'], colors[:len(regime_list)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Regime')
        ax.set_ylabel(f'SPY {horizon}d Forward Return (%)')
        ax.set_title(f'SPY {horizon}-Day Forward Returns by Regime (DIAG-04)')
        kw_p = fwd_results[key]['kw_pvalue']
        ax.text(0.98, 0.02, f'Kruskal-Wallis p={kw_p:.4f}',
                transform=ax.transAxes, ha='right', va='bottom',
                fontsize=9, color='dimgray')
        plt.tight_layout()
        fname = f'figures/fwd_returns_SPY_{horizon}d.png'
        plt.savefig(fname, dpi=100)
        print(f"  Saved: {fname}")
        plt.close()


def write_diagnostics_report(results, market, fwd_results):
    """Write reports/diagnostics_report.md with DIAG-04 forward return section."""
    os.makedirs('reports', exist_ok=True)

    report_path = 'reports/diagnostics_report.md'

    # Build forward return section
    horizons = [1, 5, 21]
    assets = ['SPY', 'EEM', 'TLT', 'HYG']

    lines = []
    lines.append("# Empirical Diagnostics Report (Phase 4)\n")
    lines.append(f"_Generated by analyze_regime_characterization.py_\n")
    lines.append("")

    # DIAG-04 section
    lines.append("## DIAG-04: Regime-Conditional Forward Return Analysis\n")
    lines.append(
        "> Forward returns are **diagnostic outputs only**. They are never added as model "
        "features or used in training (Decision 5 in STATE.md).\n"
    )
    lines.append(
        "> Kruskal-Wallis p-value: p < 0.05 suggests the regime label corresponds to "
        "statistically different return distributions for that asset/horizon.\n"
    )
    lines.append("")

    if fwd_results:
        # Kruskal-Wallis p-value table
        lines.append("### Kruskal-Wallis p-values (asset × horizon)\n")
        header = "| Asset |" + "".join(f" {h}d |" for h in horizons)
        sep = "|-------|" + "".join("-------|" for _ in horizons)
        lines.append(header)
        lines.append(sep)
        for asset in assets:
            row = f"| {asset:<5s} |"
            for h in horizons:
                key = (asset, h)
                if key in fwd_results:
                    p = fwd_results[key]['kw_pvalue']
                    flag = " *" if p < 0.05 else "  "
                    row += f" {p:.4f}{flag}|"
                else:
                    row += " N/A   |"
            lines.append(row)
        lines.append("")
        lines.append("_\\* p < 0.05_\n")
        lines.append("")

        # Per-regime median return table for SPY
        lines.append("### Per-Regime Median Forward Returns — SPY (%)\n")
        if results is not None:
            regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]
            unique_regimes = sorted(results[regime_col].dropna().unique())
            header2 = "| Regime |" + "".join(f" {h}d |" for h in horizons)
            sep2 = "|--------|" + "".join("--------|" for _ in horizons)
            lines.append(header2)
            lines.append(sep2)
            for reg in unique_regimes:
                row = f"| {str(reg):<6s} |"
                for h in horizons:
                    key = ('SPY', h)
                    if key in fwd_results and reg in fwd_results[key]['median_returns']:
                        val = fwd_results[key]['median_returns'][reg] * 100
                        row += f" {val:>+6.2f}% |"
                    else:
                        row += "  N/A   |"
                lines.append(row)
            lines.append("")

        # Figure references
        lines.append("### Figures\n")
        for h in horizons:
            fname = f"figures/fwd_returns_SPY_{h}d.png"
            lines.append(f"- [{h}d SPY forward return boxplot]({fname})")
        lines.append("")
    else:
        lines.append("_No forward return data available. Run 'python run.py' first._\n")

    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"  Saved: {report_path}")


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

    # DIAG-04: forward return analysis
    print("\nRunning forward return analysis (DIAG-04)...")
    fwd_results = analyze_forward_returns(results, market)
    analyze_forward_return_figures(results, market, fwd_results)
    write_diagnostics_report(results, market, fwd_results)

    print("\nRegime characterization analysis complete. Files saved to analysis/, figures/, reports/")


if __name__ == '__main__':
    main()
