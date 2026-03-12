"""
Quality checks and visualizations for the 4-feature set.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import os

from config import DATA_DIR, FIGURE_DIR


def _add_regime_shading(ax, regime_results):
    """Add regime shading to an axes if regime_results is available."""
    if regime_results is None:
        return
    colors = {"Low-Risk": "green", "Elevated-Risk": "gold", "Crisis": "red", "Moderate": "dodgerblue"}
    alphas = {"Low-Risk": 0.12, "Elevated-Risk": 0.18, "Crisis": 0.28, "Moderate": 0.12}
    for name, grp in regime_results.groupby("regime_name"):
        idx = grp.index
        if len(idx) == 0:
            continue
        # Find contiguous blocks
        breaks = [0] + list(np.where(np.diff(regime_results.index.get_indexer(idx)) > 1)[0] + 1) + [len(idx)]
        for i in range(len(breaks) - 1):
            block = idx[breaks[i]:breaks[i+1]]
            ax.axvspan(block[0], block[-1], alpha=alphas.get(name, 0.15), color=colors.get(name, "gray"))


def plot_features_overlaid(market, regime_results=None):
    """4-panel overlaid plot: VIX, HY spread, GARCH vol, yield spread with regime shading."""
    import yfinance as yf
    spy = yf.download("SPY", start=market.index.min(), end=market.index.max(), progress=False)["Close"].squeeze()
    spy = spy.reindex(market.index, method="ffill")

    colors = {"Low-Risk": "green", "Elevated-Risk": "gold", "Crisis": "red", "Moderate": "dodgerblue"}
    legend_patches = [
        Patch(facecolor="green", alpha=0.4, label="Low-Risk"),
        Patch(facecolor="dodgerblue", alpha=0.4, label="Moderate"),
        Patch(facecolor="gold", alpha=0.4, label="Elevated-Risk"),
        Patch(facecolor="red", alpha=0.4, label="Crisis"),
    ]

    fig, axes = plt.subplots(5, 1, figsize=(16, 18), sharex=True)
    ax_spy, ax_vix, ax_hy, ax_garch, ax_yld = axes

    for ax in axes:
        _add_regime_shading(ax, regime_results)

    ax_spy.plot(spy.index, spy, "k-", linewidth=0.7)
    ax_spy.set_ylabel("SPY")
    ax_spy.set_title("Features with Regime Shading", fontsize=13, fontweight="bold")
    ax_spy.grid(alpha=0.3)
    ax_spy.legend(handles=legend_patches, loc="upper left", fontsize=8)

    ax_vix.plot(market.index, market["vix"], "b-", linewidth=0.6)
    ax_vix.axhline(20, color="orange", linestyle="--", alpha=0.5, linewidth=0.8)
    ax_vix.axhline(30, color="red", linestyle="--", alpha=0.5, linewidth=0.8)
    ax_vix.set_ylabel("VIX")
    ax_vix.grid(alpha=0.3)

    ax_hy.plot(market.index, market["hy_spread"], "r-", linewidth=0.6)
    ax_hy.axhline(5, color="orange", linestyle="--", alpha=0.5, linewidth=0.8)
    ax_hy.set_ylabel("HY Spread (%)")
    ax_hy.grid(alpha=0.3)

    if "garch_vol" in market.columns:
        ax_garch.plot(market.index, market["garch_vol"], color="purple", linewidth=0.6)
        ax_garch.set_ylabel("GARCH Vol")
        ax_garch.grid(alpha=0.3)

    if "yield_spread" in market.columns:
        ax_yld.plot(market.index, market["yield_spread"], color="teal", linewidth=0.6)
        ax_yld.axhline(0, color="red", linestyle="--", alpha=0.5, linewidth=0.8)
        ax_yld.set_ylabel("2y-10y Spread")
        ax_yld.set_xlabel("Date")
        ax_yld.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def analyze():
    os.makedirs(FIGURE_DIR, exist_ok=True)

    market = pd.read_csv(f"{DATA_DIR}/market_data.csv", index_col=0, parse_dates=True)

    print(f"{len(market)} days | Missing: {market.isnull().sum().sum()}")
    print(market.describe().round(2))
    print(f"Correlation VIX/HY: {market['vix'].corr(market['hy_spread']):.3f}")

    # Load regime results if available (for shading)
    regime_results = None
    regime_path = f"{DATA_DIR}/regime_results.csv"
    if os.path.exists(regime_path):
        regime_results = pd.read_csv(regime_path, index_col=0, parse_dates=True)

    # --- Distributions ---
    n_features = len(market.columns)
    fig, axes = plt.subplots(1, n_features + 1, figsize=(6 * (n_features + 1), 5))

    axes[0].scatter(market["vix"], market["hy_spread"], alpha=0.12, s=4, c="black")
    axes[0].set_xlabel("VIX")
    axes[0].set_ylabel("HY Spread (%)")
    axes[0].set_title("VIX vs HY Spread")
    axes[0].grid(alpha=0.3)

    for i, col in enumerate(market.columns):
        ax = axes[i + 1]
        ax.hist(market[col], bins=80, alpha=0.7, edgecolor="black", linewidth=0.3)
        ax.axvline(market[col].median(), color="red", linestyle="--", alpha=0.6, label="Median")
        ax.set_title(col)
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{FIGURE_DIR}/feature_analysis.png", dpi=150)

    # --- Overlaid 5-panel time series with regime shading ---
    fig = plot_features_overlaid(market, regime_results)
    fig.savefig(f"{FIGURE_DIR}/features_overlaid.png", dpi=150)

    plt.show()
    plt.close("all")

    return market


if __name__ == "__main__":
    analyze()
