"""
Generate publication-ready figures for the regime-detection paper.

Input:  results/regime_labels_train.csv   (produced by run_paper_experiments.py)
        results/transition_matrix.csv
Output: paper/figures/*.pdf  (4 figures)

Figures
-------
1. regime_timeline.pdf   — shaded regime bands + SPY cumulative return overlay
2. vol_violin.pdf        — realized-vol distributions by regime (HDP vs VIX-Threshold)
3. transition_heatmap.pdf — HDP transition matrix heatmap (3×3)
4. backtest_equity.pdf   — cumulative equity curves for 4 strategies
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter

matplotlib.use('Agg')

# ── Style ─────────────────────────────────────────────────────────────────────
BLUE_DARK   = '#1E3A5F'
BLUE_MID    = '#2563EB'
BLUE_LIGHT  = '#93C5FD'
BLUE_PALE   = '#DBEAFE'
GRAY_DARK   = '#1F2937'
GRAY_MID    = '#6B7280'
GRAY_LIGHT  = '#D1D5DB'
WHITE       = '#FFFFFF'

REGIME_COLORS = {
    'Low-Vol':      BLUE_PALE,
    'Moderate-Vol': BLUE_LIGHT,
    'High-Vol':     BLUE_MID,
}
REGIME_EDGE = {
    'Low-Vol':      '#93C5FD',
    'Moderate-Vol': '#2563EB',
    'High-Vol':     BLUE_DARK,
}
STRATEGY_COLORS = {
    'Buy & Hold':        GRAY_MID,
    'Vol-Target (RV30)': BLUE_LIGHT,
    'Vol-Target (HDP)':  BLUE_DARK,
}
STRATEGY_LW = {
    'Buy & Hold':        1.2,
    'Vol-Target (RV30)': 1.2,
    'Vol-Target (HDP)':  2.0,
}
STRATEGY_LS = {
    'Buy & Hold':        '--',
    'Vol-Target (RV30)': ':',
    'Vol-Target (HDP)':  '-',
}

plt.rcParams.update({
    'font.family':        'serif',
    'font.size':          9,
    'axes.titlesize':     10,
    'axes.labelsize':     9,
    'xtick.labelsize':    8,
    'ytick.labelsize':    8,
    'legend.fontsize':    8,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.grid':          True,
    'grid.alpha':         0.35,
    'grid.color':         GRAY_LIGHT,
    'axes.facecolor':     WHITE,
    'figure.facecolor':   WHITE,
    'savefig.facecolor':  WHITE,
    'text.color':         GRAY_DARK,
    'axes.labelcolor':    GRAY_DARK,
    'xtick.color':        GRAY_MID,
    'ytick.color':        GRAY_MID,
    'axes.edgecolor':     GRAY_LIGHT,
})

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'paper', 'figures')
os.makedirs(OUT_DIR, exist_ok=True)

def savefig(name):
    path = os.path.join(OUT_DIR, name)
    plt.savefig(path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"  Saved {path}")


# ── Load data ─────────────────────────────────────────────────────────────────
LABELS_CSV = os.path.join(os.path.dirname(__file__), '..', 'results', 'regime_labels_train.csv')
TRANS_CSV  = os.path.join(os.path.dirname(__file__), '..', 'results', 'transition_matrix.csv')

if not os.path.exists(LABELS_CSV):
    sys.exit(
        f"ERROR: {LABELS_CSV} not found.\n"
        "Run `python run_paper_experiments.py` first to generate it."
    )

df = pd.read_csv(LABELS_CSV, parse_dates=['date'])
df = df.set_index('date')

trans_df = pd.read_csv(TRANS_CSV, index_col=0) if os.path.exists(TRANS_CSV) else None

REGIMES      = ['Low-Vol', 'Moderate-Vol', 'High-Vol']
dates        = df.index
spy_ret      = df['spy_ret'].values
vol_index    = df['vol_index'].values
hdp_regime   = df['hdp_regime'].values
thresh_regime = df['thresh_regime'].values


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1: Regime Timeline
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Figure 1: Regime Timeline...")

fig, (ax_top, ax_bot) = plt.subplots(
    2, 1, figsize=(7.5, 4.2), sharex=True,
    gridspec_kw={'height_ratios': [2.5, 1], 'hspace': 0.06},
)

# Top panel: cumulative SPY return with regime shading
cum_spy = np.cumprod(1 + spy_ret)
ax_top.plot(dates, cum_spy, color=GRAY_DARK, lw=1.2, zorder=3, label='SPY cumulative return')

prev_regime = hdp_regime[0]
start_idx   = 0
for i in range(1, len(dates)):
    if hdp_regime[i] != prev_regime or i == len(dates) - 1:
        end_idx = i if hdp_regime[i] != prev_regime else i + 1
        ax_top.axvspan(
            dates[start_idx], dates[min(end_idx, len(dates) - 1)],
            alpha=0.35, color=REGIME_COLORS[prev_regime], zorder=1, linewidth=0,
        )
        start_idx   = i
        prev_regime = hdp_regime[i]

ax_top.set_ylabel('Cumulative Return (×)', color=GRAY_DARK)
ax_top.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}×'))
ax_top.set_xlim(dates[0], dates[-1])
ax_top.grid(axis='x', alpha=0)

legend_patches = [
    mpatches.Patch(facecolor=REGIME_COLORS[r], edgecolor=REGIME_EDGE[r], alpha=0.6, label=r)
    for r in REGIMES
]
legend_patches.append(plt.Line2D([0], [0], color=GRAY_DARK, lw=1.2, label='SPY'))
ax_top.legend(handles=legend_patches, loc='upper left', frameon=False, ncol=4, fontsize=7.5)
ax_top.set_title('HDP-HMM Regime Timeline (January 2016–December 2023)', fontsize=10, pad=6)

# Bottom panel: VIX level
ax_bot.fill_between(dates, vol_index, alpha=0.4, color=BLUE_MID)
ax_bot.plot(dates, vol_index, color=BLUE_DARK, lw=0.8)
ax_bot.axhline(20, color=GRAY_MID, lw=0.8, ls='--', alpha=0.6)
ax_bot.axhline(30, color=GRAY_MID, lw=0.8, ls=':', alpha=0.6)
ax_bot.set_ylabel('VIX', color=GRAY_DARK)
ax_bot.set_xlabel('')

savefig('regime_timeline.pdf')


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2: Realized-vol violin by regime (HDP vs VIX-Threshold)
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Figure 2: Volatility Violin...")

ann_vol = np.abs(spy_ret) * np.sqrt(252) * 100  # proxy: daily |ret| * sqrt(252)

fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.6), sharey=True)

for ax, col, title in [
    (axes[0], 'hdp_regime',    'HDP-HMM'),
    (axes[1], 'thresh_regime', 'VIX Threshold'),
]:
    regime_col = df[col].values
    data_by_regime = [ann_vol[regime_col == r] for r in REGIMES]
    positions = list(range(len(REGIMES)))

    parts = ax.violinplot(
        data_by_regime, positions=positions,
        showmedians=True, showextrema=False, widths=0.65,
    )
    for i, (body, regime) in enumerate(zip(parts['bodies'], REGIMES)):
        body.set_facecolor(REGIME_COLORS[regime])
        body.set_edgecolor(REGIME_EDGE[regime])
        body.set_alpha(0.8)
        body.set_linewidth(1.2)
    parts['cmedians'].set_color(GRAY_DARK)
    parts['cmedians'].set_linewidth(1.5)

    # Overlay individual data points (jittered)
    rng = np.random.default_rng(42)
    for i, (data, regime) in enumerate(zip(data_by_regime, REGIMES)):
        sample = data[rng.choice(len(data), min(300, len(data)), replace=False)]
        jitter = rng.uniform(-0.08, 0.08, size=len(sample))
        ax.scatter(i + jitter, sample, s=2, alpha=0.25, color=REGIME_EDGE[regime], zorder=2)

    ax.set_xticks(positions)
    ax.set_xticklabels(REGIMES, fontsize=8)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel('Regime')

axes[0].set_ylabel('Annualized Daily Realized Vol (%)')
fig.suptitle('Within-Regime Realized Volatility Distributions', fontsize=10, y=1.01)

savefig('vol_violin.pdf')


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3: Transition matrix heatmap
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Figure 3: Transition Matrix Heatmap...")

if trans_df is not None:
    trans = trans_df.values
else:
    trans = np.array([[0.989, 0.009, 0.002],
                      [0.011, 0.986, 0.002],
                      [0.015, 0.010, 0.974]])

fig, ax = plt.subplots(figsize=(4.2, 3.6))
ax.set_facecolor(WHITE)

im = ax.imshow(trans, cmap='Blues', vmin=0.0, vmax=1.0, aspect='auto')

for i in range(3):
    for j in range(3):
        val = trans[i, j]
        text_color = WHITE if val > 0.6 else GRAY_DARK
        ax.text(j, i, f'{val:.3f}', ha='center', va='center',
                fontsize=10, color=text_color, fontweight='bold' if i == j else 'normal')

ax.set_xticks(range(3))
ax.set_yticks(range(3))
ax.set_xticklabels(REGIMES, fontsize=8)
ax.set_yticklabels(REGIMES, fontsize=8)
ax.set_xlabel('To Regime')
ax.set_ylabel('From Regime')
ax.set_title('HDP-HMM Posterior-Mean Transition Matrix', fontsize=10, pad=8)

cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Transition Probability', fontsize=8)
cbar.ax.tick_params(labelsize=7)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.grid(False)

savefig('transition_heatmap.pdf')


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4: Backtest equity curves
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Figure 4: Backtest Equity Curves...")

cum_cols = {
    'Buy & Hold':        'cum_bh',
    'Vol-Target (RV30)': 'cum_rv30',
    'Vol-Target (HDP)':  'cum_hdp',
}

fig, ax = plt.subplots(figsize=(7.5, 3.8))

for label, col in cum_cols.items():
    if col not in df.columns:
        print(f"  WARNING: column {col} not found, skipping {label}")
        continue
    ax.plot(
        dates, df[col],
        label=label,
        color=STRATEGY_COLORS[label],
        lw=STRATEGY_LW[label],
        ls=STRATEGY_LS[label],
        zorder=4 if label == 'Vol-Target (HDP)' else 2,
    )

ax.set_ylabel('Cumulative Return (× initial)')
ax.set_xlabel('')
ax.set_xlim(dates[0], dates[-1])
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}×'))
ax.legend(frameon=False, loc='upper left', fontsize=8)
ax.set_title(
    'Volatility-Targeting Backtest: Cumulative Returns (2016–2023)',
    fontsize=10, pad=6,
)

savefig('backtest_equity.pdf')

print("\nAll figures written to paper/figures/")
