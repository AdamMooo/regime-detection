"""
Analyze feature importance: PCA loadings, feature correlation, variance explained.

This script runs standalone (not imported by the pipeline).
It loads the trained model checkpoint and regime results to generate feature importance visualizations.

Run: python analyze_feature_importance.py
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from config import DATA_DIR, MODEL_DIR


def load_pca_model():
    """Load PCA model from checkpoint."""
    # Try unified checkpoint first
    checkpoint_path = os.path.join(MODEL_DIR, 'regime_model.pkl')
    if os.path.exists(checkpoint_path):
        try:
            checkpoint = joblib.load(checkpoint_path)
            return checkpoint.get('pca')
        except:
            pass

    # Fall back to individual PCA checkpoint
    pca_path = os.path.join(MODEL_DIR, 'pca_model.pkl')
    if os.path.exists(pca_path):
        try:
            return joblib.load(pca_path)
        except:
            pass

    return None


def load_features():
    """Load scaled features."""
    features_path = os.path.join(DATA_DIR, 'features_scaled.csv')
    if os.path.exists(features_path):
        return pd.read_csv(features_path, index_col=0, parse_dates=True)
    return None


def analyze_pca_loadings(pca_model):
    """Analyze and visualize PCA loadings."""
    if pca_model is None:
        print("  ERROR: PCA model not found")
        return

    os.makedirs('analysis', exist_ok=True)

    # Extract loadings (components)
    loadings = pca_model.components_  # Shape: (n_components, n_features)
    n_features = loadings.shape[1]

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 6))
    feature_names = [f'Feature {i+1}' for i in range(n_features)]
    component_names = [f'PC{i+1}' for i in range(loadings.shape[0])]

    sns.heatmap(
        loadings,
        xticklabels=feature_names,
        yticklabels=component_names,
        cmap='RdBu_r',
        center=0,
        ax=ax,
        cbar_kws={'label': 'Loading'}
    )
    ax.set_title('PCA Loadings Heatmap')
    ax.set_xlabel('Features')
    ax.set_ylabel('Principal Components')
    plt.tight_layout()
    plt.savefig('analysis/pca_loadings.png', dpi=100)
    print("  Saved: analysis/pca_loadings.png")
    plt.close()


def analyze_variance_explained(pca_model):
    """Analyze variance explained by PCA components."""
    if pca_model is None:
        return

    os.makedirs('analysis', exist_ok=True)

    # Extract variance ratios
    var_ratio = pca_model.explained_variance_ratio_
    cumsum_var = np.cumsum(var_ratio)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Individual variance
    ax1.bar(range(1, len(var_ratio) + 1), var_ratio * 100)
    ax1.set_xlabel('Principal Component')
    ax1.set_ylabel('Variance Explained (%)')
    ax1.set_title('Variance Explained per Component')
    ax1.set_xticks(range(1, len(var_ratio) + 1))

    # Cumulative variance
    ax2.plot(range(1, len(cumsum_var) + 1), cumsum_var * 100, 'o-', linewidth=2)
    ax2.axhline(y=90, color='r', linestyle='--', label='90% threshold')
    ax2.set_xlabel('Number of Components')
    ax2.set_ylabel('Cumulative Variance Explained (%)')
    ax2.set_title('Cumulative Variance Explained')
    ax2.legend()
    ax2.grid(alpha=0.3)
    ax2.set_xticks(range(1, len(cumsum_var) + 1))

    plt.tight_layout()
    plt.savefig('analysis/pca_variance_explained.png', dpi=100)
    print("  Saved: analysis/pca_variance_explained.png")
    plt.close()


def analyze_feature_correlation(features):
    """Analyze feature correlation matrix."""
    if features is None or features.empty:
        print("  ERROR: Features not found")
        return

    os.makedirs('analysis', exist_ok=True)

    # Compute correlation
    corr = features.corr()

    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr,
        cmap='coolwarm',
        center=0,
        ax=ax,
        cbar_kws={'label': 'Correlation'},
        square=True,
        vmin=-1, vmax=1
    )
    ax.set_title('Feature Correlation Matrix')
    plt.tight_layout()
    plt.savefig('analysis/feature_correlation.png', dpi=100)
    print("  Saved: analysis/feature_correlation.png")
    plt.close()


def main():
    """Generate feature importance analysis outputs."""
    print("Feature importance analysis...")

    pca_model = load_pca_model()
    features = load_features()

    if pca_model is None and features is None:
        print("ERROR: No model or features available. Run 'python run.py' first.")
        return

    analyze_pca_loadings(pca_model)
    analyze_variance_explained(pca_model)
    analyze_feature_correlation(features)

    print("Feature importance analysis complete. Files saved to analysis/")


if __name__ == '__main__':
    main()
