"""
Diagnostics and visualization for the PCA -> HMM -> SV pipeline.
Produces a single consolidated feature_overview.png.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

from config import DATA_DIR, FIGURE_DIR


def plot_feature_overview(features):
    """Combined: distributions (left) + correlation matrix (right)."""
    n_feat = len(features.columns)
    cols_hist = min(4, n_feat)
    rows_hist = (n_feat + cols_hist - 1) // cols_hist

    fig = plt.figure(figsize=(22, 4 * rows_hist))
    gs = fig.add_gridspec(rows_hist, cols_hist + 2, wspace=0.35, hspace=0.4)

    # Left: histograms
    for i, col in enumerate(features.columns):
        r, c = divmod(i, cols_hist)
        ax = fig.add_subplot(gs[r, c])
        ax.hist(features[col].dropna(), bins=50, alpha=0.7,
                edgecolor='black', lw=0.2, color='steelblue')
        ax.axvline(features[col].median(), color='red', ls='--', alpha=0.6, lw=0.8)
        ax.set_title(col, fontsize=8, fontweight='bold')
        ax.tick_params(labelsize=6)
        ax.grid(alpha=0.2)

    # Right: correlation matrix
    corr = features.corr()
    ax_corr = fig.add_subplot(gs[:, cols_hist:])
    im = ax_corr.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    ax_corr.set_xticks(range(len(corr.columns)))
    ax_corr.set_yticks(range(len(corr.columns)))
    ax_corr.set_xticklabels(corr.columns, rotation=45, ha='right', fontsize=7)
    ax_corr.set_yticklabels(corr.columns, fontsize=7)
    fig.colorbar(im, ax=ax_corr, shrink=0.6)
    ax_corr.set_title('Correlation Matrix', fontsize=10, fontweight='bold')

    fig.suptitle('Feature Overview', fontsize=14, fontweight='bold', y=1.01)
    return fig


def analyze():
    os.makedirs(FIGURE_DIR, exist_ok=True)

    market = pd.read_csv(os.path.join(DATA_DIR, 'market_data.csv'),
                         index_col=0, parse_dates=True)

    features = None
    feat_path = os.path.join(DATA_DIR, 'features_raw.csv')
    if os.path.exists(feat_path):
        features = pd.read_csv(feat_path, index_col=0, parse_dates=True)

    print(f"{len(market)} days  |  Missing: {market.isnull().sum().sum()}")
    if features is not None:
        print(f"Features: {features.shape[1]} x {features.shape[0]}")

        fig = plot_feature_overview(features)
        fig.savefig(os.path.join(FIGURE_DIR, 'feature_overview.png'),
                    dpi=150, bbox_inches='tight')

    plt.close('all')
    return market


if __name__ == '__main__':
    analyze()
