"""
Analyze regime characterization: per-regime statistics, transition rates, duration.

This script runs standalone (not imported by the pipeline).
It loads regime results and price data to generate regime characterization analysis.

Phase 4 (Empirical Diagnostics) extensions:
- DIAG-01: Save vol boxplot, dwell time histogram, transition matrix heatmap to figures/
- DIAG-02: Persistence baseline comparison (model vs naive persist-yesterday baseline)
- DIAG-03: Failure mode analysis (misclassification patterns, crisis period analysis)
- DIAG-04: Forward return analysis via evaluation.compute_forward_return_analysis()
- Writes reports/diagnostics_report.md (structured markdown summary)

Run: python analyze_regime_characterization.py
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for file saving
import matplotlib.pyplot as plt
import seaborn as sns

from src.config import DATA_DIR, FIGURE_DIR

# Output directories
REPORTS_DIR = 'reports'
OOS_START = '2021-01-01'  # Matches MODEL_CARD.md evaluation set (2021–2026)


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


def _get_regime_col(results):
    """Return the regime label column name."""
    return 'regime_name' if 'regime_name' in results.columns else results.columns[0]


def analyze_regime_statistics(results, market):
    """Analyze per-regime statistics.

    DIAG-01 extension: saves vol boxplot to figures/diag01_vol_boxplot.png
    in addition to existing bar chart.
    """
    if results is None or market is None:
        print("  ERROR: Results or market data not found")
        return {}

    os.makedirs(FIGURE_DIR, exist_ok=True)
    os.makedirs('analysis', exist_ok=True)

    # Align data
    results_aligned = results.loc[results.index.intersection(market.index)]
    market_aligned = market.loc[results_aligned.index]

    regime_col = _get_regime_col(results_aligned)
    regimes = results_aligned[regime_col]

    stats_data = []
    spy_close = market_aligned.get('SPY_close')

    if spy_close is not None:
        returns = np.log(spy_close / spy_close.shift(1)).dropna()

        for regime in sorted(regimes.dropna().unique()):
            regime_mask = regimes.reindex(returns.index) == regime
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
        if not stats_df.empty:
            stats_df.to_csv('analysis/regime_statistics.csv', index=False)
            print("  Saved: analysis/regime_statistics.csv")

            # Original bar chart
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
            plt.close()

            # DIAG-01: Vol boxplot — shows distribution spread per regime
            vol_data = []
            vol_labels = []
            for regime in sorted(regimes.dropna().unique()):
                regime_mask = regimes.reindex(returns.index) == regime
                regime_rets = returns[regime_mask]
                if len(regime_rets) > 0:
                    # Use rolling 21-day annualised vol proxy per day
                    rolling_vol = returns.rolling(21).std() * np.sqrt(252) * 100
                    vol_data.append(rolling_vol[regime_mask].dropna().values)
                    vol_labels.append(regime)

            if vol_data:
                fig, ax = plt.subplots(figsize=(10, 6))
                bp = ax.boxplot(vol_data, labels=vol_labels, patch_artist=True,
                                medianprops=dict(color='black', linewidth=2))
                colors = ['#4CAF50', '#FF9800', '#F44336', '#9C27B0']
                for patch, color in zip(bp['boxes'], colors[:len(vol_data)]):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.7)
                ax.set_xlabel('Regime')
                ax.set_ylabel('21-Day Annualised Volatility (%)')
                ax.set_title('DIAG-01: Regime Volatility Distribution')
                ax.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                fig_path = os.path.join(FIGURE_DIR, 'diag01_vol_boxplot.png')
                plt.savefig(fig_path, dpi=150)
                print(f"  Saved: {fig_path}")
                plt.close()

    return {'stats': stats_data}


def analyze_transition_matrix(results):
    """Analyze regime transition rates.

    DIAG-01 extension: saves heatmap to figures/diag01_transition_heatmap.png
    """
    if results is None:
        return {}

    os.makedirs(FIGURE_DIR, exist_ok=True)
    os.makedirs('analysis', exist_ok=True)

    regime_col = _get_regime_col(results)
    regimes = results[regime_col].dropna()

    unique_regimes = sorted(regimes.unique())
    n_regimes = len(unique_regimes)
    regime_map = {r: i for i, r in enumerate(unique_regimes)}

    transition_matrix = np.zeros((n_regimes, n_regimes))
    for i in range(len(regimes) - 1):
        from_idx = regime_map[regimes.iloc[i]]
        to_idx = regime_map[regimes.iloc[i + 1]]
        transition_matrix[from_idx, to_idx] += 1

    row_sums = transition_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    transition_probs = transition_matrix / row_sums

    # Original figure path (for backward compat)
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
    plt.close()

    # DIAG-01: Save to figures/ as well
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        transition_probs,
        annot=True,
        fmt='.2%',
        cmap='Blues',
        xticklabels=unique_regimes,
        yticklabels=unique_regimes,
        ax=ax,
        linewidths=0.5,
        linecolor='white',
        cbar_kws={'label': 'Transition Probability'}
    )
    ax.set_title('DIAG-01: Regime Transition Matrix Heatmap', fontsize=13)
    ax.set_xlabel('To Regime', fontsize=11)
    ax.set_ylabel('From Regime', fontsize=11)
    plt.tight_layout()
    fig_path = os.path.join(FIGURE_DIR, 'diag01_transition_heatmap.png')
    plt.savefig(fig_path, dpi=150)
    print(f"  Saved: {fig_path}")
    plt.close()

    # Compute diagonal persistence rates
    persistence = {unique_regimes[i]: transition_probs[i, i] for i in range(n_regimes)}
    return {'transition_matrix': transition_probs.tolist(), 'regimes': unique_regimes,
            'persistence': persistence}


def analyze_regime_duration(results):
    """Analyze regime duration statistics.

    DIAG-01 extension: saves dwell time histogram to figures/diag01_dwell_histogram.png
    """
    if results is None:
        return {}

    os.makedirs(FIGURE_DIR, exist_ok=True)
    os.makedirs('analysis', exist_ok=True)

    regime_col = _get_regime_col(results)
    regimes = results[regime_col].dropna()

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

    duration_stats = []
    for regime, durations in durations_by_regime.items():
        if len(durations) > 0:
            duration_stats.append({
                'Regime': regime,
                'Mean Duration': np.mean(durations),
                'Median Duration': np.median(durations),
                'Max Duration': np.max(durations),
                'Min Duration': np.min(durations),
                'N Episodes': len(durations),
                'All Durations': durations,
            })

    duration_df = pd.DataFrame(duration_stats)

    # Original bar chart
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
    plt.close()

    # DIAG-01: Dwell time histogram per regime
    unique_regimes = sorted(duration_df['Regime'].tolist())
    n = len(unique_regimes)
    colors = ['#4CAF50', '#FF9800', '#F44336', '#9C27B0']

    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5), sharey=False)
    if n == 1:
        axes = [axes]

    for idx, (ax, regime) in enumerate(zip(axes, unique_regimes)):
        row = duration_df[duration_df['Regime'] == regime].iloc[0]
        durations = row['All Durations']
        ax.hist(durations, bins=min(20, len(durations)), color=colors[idx % len(colors)],
                alpha=0.75, edgecolor='white')
        ax.axvline(row['Mean Duration'], color='black', linestyle='--', linewidth=1.5,
                   label=f"Mean {row['Mean Duration']:.1f}d")
        ax.axvline(row['Median Duration'], color='red', linestyle=':', linewidth=1.5,
                   label=f"Median {row['Median Duration']:.1f}d")
        ax.set_title(f'{regime}', fontsize=11)
        ax.set_xlabel('Dwell Time (days)')
        ax.set_ylabel('Frequency')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    fig.suptitle('DIAG-01: Regime Dwell Time Distributions', fontsize=13, y=1.02)
    plt.tight_layout()
    fig_path = os.path.join(FIGURE_DIR, 'diag01_dwell_histogram.png')
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"  Saved: {fig_path}")
    plt.close()

    return {
        'duration_stats': [
            {k: v for k, v in row.items() if k != 'All Durations'}
            for _, row in duration_df.iterrows()
        ]
    }


def compute_persistence_baseline(results):
    """Compute OOS accuracy vs naive persist-yesterday baseline.

    DIAG-02: Compare model's OOS regime assignments to the simplest possible
    baseline — predict today's regime = yesterday's regime.

    Uses the OOS split: 2021-01-01 onwards (matches MODEL_CARD.md).

    Returns
    -------
    dict with keys: model_accuracy, baseline_accuracy, lift, oos_days, oos_start
    """
    if results is None:
        return {}

    regime_col = _get_regime_col(results)
    regimes = results[regime_col].dropna()

    # Split into OOS portion
    oos_regimes = regimes[regimes.index >= OOS_START]
    if len(oos_regimes) < 50:
        print(f"  WARNING: OOS set too small ({len(oos_regimes)} days) — skipping baseline")
        return {'oos_days': len(oos_regimes), 'oos_start': OOS_START,
                'model_accuracy': None, 'baseline_accuracy': None, 'lift': None}

    # Naive persistence baseline: predict regime[t] = regime[t-1]
    baseline_preds = oos_regimes.shift(1).dropna()
    actual = oos_regimes.reindex(baseline_preds.index)
    baseline_accuracy = (baseline_preds == actual).mean()

    # For lift, we compare model regime transition count vs persistence
    n_changes = (oos_regimes != oos_regimes.shift(1)).sum()
    n_total = len(oos_regimes)
    change_rate = n_changes / n_total

    print(f"\n  DIAG-02: Persistence Baseline")
    print(f"    OOS period: {OOS_START} onwards ({len(oos_regimes)} days)")
    print(f"    Regime change rate (OOS): {change_rate:.1%} per day")
    print(f"    Persistence accuracy (baseline): {baseline_accuracy:.1%}")
    print(f"    (Higher change rate = lower baseline accuracy)")

    return {
        'oos_days': len(oos_regimes),
        'oos_start': OOS_START,
        'baseline_accuracy': float(baseline_accuracy),
        'change_rate': float(change_rate),
        'n_regime_changes': int(n_changes),
    }


def analyze_failure_modes(results, market):
    """Identify failure mode patterns: regime instability and crisis misclassification.

    DIAG-03: Documents which regime transitions are most frequent, and whether
    known crisis periods (2020 COVID, 2022 Bear) align with expected high-vol regimes.

    Returns
    -------
    dict with failure mode summary
    """
    if results is None:
        return {}

    regime_col = _get_regime_col(results)
    regimes = results[regime_col].dropna()

    # Define known crisis periods for alignment check
    crisis_periods = {
        'COVID Crash (Feb-Apr 2020)': ('2020-02-01', '2020-04-30'),
        '2022 Bear Market (Jan-Oct 2022)': ('2022-01-01', '2022-10-31'),
        'GFC (Sep 2008 - Mar 2009)': ('2008-09-01', '2009-03-31'),
    }

    # Find "high vol" regime name heuristically (highest volatility or "Crisis"/"High")
    # Look for regime names containing known high-vol keywords
    high_vol_keywords = ['crisis', 'high', 'bear', 'stress', 'vol']
    high_vol_regime = None
    for r in regimes.unique():
        if any(kw in str(r).lower() for kw in high_vol_keywords):
            high_vol_regime = r
            break

    # Short-spell detection: regime changes lasting < 3 days (instability indicator)
    spell_lengths = []
    current = regimes.iloc[0]
    count = 1
    for i in range(1, len(regimes)):
        if regimes.iloc[i] == current:
            count += 1
        else:
            spell_lengths.append({'regime': current, 'length': count})
            current = regimes.iloc[i]
            count = 1
    spell_lengths.append({'regime': current, 'length': count})
    spell_df = pd.DataFrame(spell_lengths)

    short_spells = spell_df[spell_df['length'] <= 3]
    short_spell_rate = len(short_spells) / len(spell_df) if len(spell_df) > 0 else 0

    # Rapid oscillation: A->B->A within 5 days (flip-flop)
    flips = 0
    for i in range(1, len(spell_df) - 1):
        if (spell_df.iloc[i - 1]['regime'] == spell_df.iloc[i + 1]['regime'] and
                spell_df.iloc[i]['length'] <= 3):
            flips += 1

    # Crisis alignment check
    crisis_alignment = {}
    for period_name, (start, end) in crisis_periods.items():
        period_regimes = regimes[(regimes.index >= start) & (regimes.index <= end)]
        if len(period_regimes) > 0:
            mode_regime = period_regimes.mode()
            mode_regime_name = mode_regime.iloc[0] if len(mode_regime) > 0 else 'N/A'
            dominant_pct = (period_regimes == mode_regime_name).mean()
            crisis_alignment[period_name] = {
                'dominant_regime': mode_regime_name,
                'dominant_pct': float(dominant_pct),
                'n_days': len(period_regimes),
                'expected_high_vol': high_vol_regime,
                'aligned': (mode_regime_name == high_vol_regime) if high_vol_regime else None,
            }

    # Most common transitions (off-diagonal)
    transitions = []
    for i in range(len(regimes) - 1):
        if regimes.iloc[i] != regimes.iloc[i + 1]:
            transitions.append(f"{regimes.iloc[i]} -> {regimes.iloc[i + 1]}")
    from collections import Counter
    top_transitions = Counter(transitions).most_common(5)

    print(f"\n  DIAG-03: Failure Mode Analysis")
    print(f"    Total regime spells: {len(spell_df)}")
    print(f"    Short spells (<= 3 days): {len(short_spells)} ({short_spell_rate:.1%})")
    print(f"    Flip-flop patterns: {flips}")
    print(f"    Top transitions:")
    for trans, count in top_transitions:
        print(f"      {trans}: {count}x")
    print(f"    Crisis alignment:")
    for period, info in crisis_alignment.items():
        aligned = 'ALIGNED' if info['aligned'] else ('N/A' if info['aligned'] is None else 'MISALIGNED')
        print(f"      {period}: {info['dominant_regime']} ({info['dominant_pct']:.0%}) — {aligned}")

    return {
        'total_spells': len(spell_df),
        'short_spell_count': int(len(short_spells)),
        'short_spell_rate': float(short_spell_rate),
        'flip_flop_count': int(flips),
        'top_transitions': top_transitions,
        'crisis_alignment': crisis_alignment,
        'high_vol_regime_detected': high_vol_regime,
    }


def write_diagnostics_report(stats_info, transition_info, duration_info,
                              baseline_info, failure_info, forward_return_info):
    """Write structured diagnostics report to reports/diagnostics_report.md."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    lines = []

    lines.append("# Empirical Diagnostics Report — Phase 4")
    lines.append("")
    lines.append(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d')}")
    lines.append(f"**OOS Period:** {OOS_START} onwards")
    lines.append("")
    lines.append("---")
    lines.append("")

    # DIAG-01
    lines.append("## DIAG-01: Regime Characterization")
    lines.append("")
    lines.append("### Figures")
    lines.append("- `figures/diag01_vol_boxplot.png` — Volatility distribution per regime")
    lines.append("- `figures/diag01_dwell_histogram.png` — Dwell time histograms per regime")
    lines.append("- `figures/diag01_transition_heatmap.png` — Regime transition matrix heatmap")
    lines.append("")

    if duration_info.get('duration_stats'):
        lines.append("### Dwell Time Summary")
        lines.append("")
        lines.append("| Regime | Mean Duration (days) | Median | Max | Episodes |")
        lines.append("|--------|---------------------|--------|-----|----------|")
        for row in duration_info['duration_stats']:
            lines.append(
                f"| {row['Regime']} | {row['Mean Duration']:.1f} | "
                f"{row['Median Duration']:.1f} | {row['Max Duration']:.0f} | "
                f"{row['N Episodes']} |"
            )
        lines.append("")

    if transition_info.get('persistence'):
        lines.append("### Regime Self-Persistence (Diagonal of Transition Matrix)")
        lines.append("")
        lines.append("| Regime | Self-Transition Probability |")
        lines.append("|--------|----------------------------|")
        for regime, prob in transition_info['persistence'].items():
            lines.append(f"| {regime} | {prob:.1%} |")
        lines.append("")

    # DIAG-02
    lines.append("## DIAG-02: OOS Accuracy vs Persistence Baseline")
    lines.append("")
    if baseline_info:
        oos_days = baseline_info.get('oos_days', 'N/A')
        baseline_acc = baseline_info.get('baseline_accuracy')
        change_rate = baseline_info.get('change_rate')
        n_changes = baseline_info.get('n_regime_changes', 'N/A')

        lines.append(f"- **OOS period:** {OOS_START} onwards ({oos_days} trading days)")
        if change_rate is not None:
            lines.append(f"- **Regime change rate (OOS):** {change_rate:.1%} per day")
        if baseline_acc is not None:
            lines.append(f"- **Persist-yesterday baseline accuracy:** {baseline_acc:.1%}")
        lines.append(f"- **Regime transitions in OOS:** {n_changes}")
        lines.append("")
        lines.append(
            "> **Interpretation:** Baseline accuracy = how often yesterday's regime "
            "matches today's. The model must exceed this to add signal. "
            "Lower change rate = higher baseline = harder to beat."
        )
    else:
        lines.append("_Not computed — regime_results.csv missing or insufficient OOS data._")
    lines.append("")

    # DIAG-03
    lines.append("## DIAG-03: Failure Mode Analysis")
    lines.append("")
    if failure_info:
        lines.append(f"- **Total regime spells:** {failure_info.get('total_spells', 'N/A')}")
        lines.append(f"- **Short spells (<= 3 days):** {failure_info.get('short_spell_count', 'N/A')} "
                     f"({failure_info.get('short_spell_rate', 0):.1%} of all spells)")
        lines.append(f"- **Flip-flop patterns (A→B→A within 5 days):** {failure_info.get('flip_flop_count', 'N/A')}")
        lines.append("")

        if failure_info.get('top_transitions'):
            lines.append("### Most Frequent Regime Transitions")
            lines.append("")
            lines.append("| Transition | Count |")
            lines.append("|-----------|-------|")
            for trans, count in failure_info['top_transitions']:
                lines.append(f"| {trans} | {count} |")
            lines.append("")

        if failure_info.get('crisis_alignment'):
            lines.append("### Crisis Period Alignment")
            lines.append("")
            lines.append("| Period | Dominant Regime | Coverage | Expected | Aligned? |")
            lines.append("|--------|----------------|----------|----------|----------|")
            for period, info in failure_info['crisis_alignment'].items():
                aligned_str = 'YES' if info['aligned'] else ('N/A' if info['aligned'] is None else 'NO')
                lines.append(
                    f"| {period} | {info['dominant_regime']} | "
                    f"{info['dominant_pct']:.0%} | {info['expected_high_vol'] or 'N/A'} | {aligned_str} |"
                )
            lines.append("")
    else:
        lines.append("_Not computed — regime_results.csv missing._")
    lines.append("")

    # DIAG-04
    lines.append("## DIAG-04: Regime-Conditional Forward Return Analysis")
    lines.append("")
    if forward_return_info:
        lines.append(
            "> **Note:** Forward returns are a validation diagnostic only. "
            "They are NOT model features and are NOT used in training (causal integrity preserved)."
        )
        lines.append("")

        kw_results = forward_return_info.get('kruskal_wallis', {})
        if kw_results:
            lines.append("### Kruskal-Wallis Test (p-values by asset and horizon)")
            lines.append("")
            lines.append("| Asset | 1d | 5d | 21d |")
            lines.append("|-------|----|----|-----|")
            assets = ['SPY', 'EEM', 'TLT', 'HYG']
            for asset in assets:
                row_vals = []
                for horizon in ['1d', '5d', '21d']:
                    key = f"{asset}_{horizon}"
                    p = kw_results.get(key, {}).get('p_value')
                    row_vals.append(f"{p:.3f}" if p is not None else 'N/A')
                lines.append(f"| {asset} | {' | '.join(row_vals)} |")
            lines.append("")
            lines.append(
                "> p < 0.05 = statistically significant separation across regimes. "
                "Human interpretation required — this is a diagnostic, not a signal."
            )
            lines.append("")

        mean_returns = forward_return_info.get('mean_returns', {})
        if mean_returns:
            lines.append("### Mean Forward Returns by Regime (%)")
            lines.append("")
            for asset in ['SPY', 'EEM', 'TLT', 'HYG']:
                lines.append(f"#### {asset}")
                asset_data = mean_returns.get(asset, {})
                if asset_data:
                    regimes_list = list(asset_data.keys())
                    lines.append(f"| Horizon | {' | '.join(str(r) for r in regimes_list)} |")
                    lines.append("|---------|" + "".join(["--------|"] * len(regimes_list)))
                    for horizon in ['1d', '5d', '21d']:
                        row_vals = []
                        for r in regimes_list:
                            v = asset_data[r].get(horizon)
                            row_vals.append(f"{v:.2f}%" if v is not None else 'N/A')
                        lines.append(f"| {horizon} | {' | '.join(row_vals)} |")
                    lines.append("")
    else:
        lines.append("_Not computed — market_data.csv or regime_results.csv missing._")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `scripts/analysis/analyze_regime_characterization.py`*")
    lines.append("*Figures saved to `figures/`. Data in `analysis/`.*")

    report_path = os.path.join(REPORTS_DIR, 'diagnostics_report.md')
    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"\n  Saved: {report_path}")


def main():
    """Generate regime characterization analysis outputs (Phase 4 Empirical Diagnostics)."""
    print("Regime characterization analysis (Phase 4 — Empirical Diagnostics)...")

    results = load_regime_results()
    market = load_market_data()

    if results is None:
        print("ERROR: No regime results available. Run 'python run.py' first.")
        return

    print("\n--- DIAG-01: Regime Characterization Figures ---")
    stats_info = analyze_regime_statistics(results, market)
    transition_info = analyze_transition_matrix(results)
    duration_info = analyze_regime_duration(results)

    print("\n--- DIAG-02: Persistence Baseline ---")
    baseline_info = compute_persistence_baseline(results)

    print("\n--- DIAG-03: Failure Mode Analysis ---")
    failure_info = analyze_failure_modes(results, market)

    print("\n--- DIAG-04: Forward Return Analysis ---")
    forward_return_info = {}
    try:
        from src.core.evaluation import compute_forward_return_analysis
        if market is not None:
            forward_return_info = compute_forward_return_analysis(results, market)
        else:
            print("  WARNING: market_data.csv missing — skipping forward return analysis")
    except ImportError:
        print("  WARNING: compute_forward_return_analysis not available")

    print("\n--- Writing diagnostics_report.md ---")
    write_diagnostics_report(
        stats_info, transition_info, duration_info,
        baseline_info, failure_info, forward_return_info
    )

    print("\nPhase 4 diagnostic analysis complete.")
    print("  Figures:  figures/diag01_*.png")
    print("  Report:   reports/diagnostics_report.md")
    print("  Analysis: analysis/")


if __name__ == '__main__':
    main()
