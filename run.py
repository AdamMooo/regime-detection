"""
Run the PCA -> HMM -> Regime-Dependent SV pipeline.

Usage:
    python run.py              # full pipeline
    python run.py collect      # data download only
    python run.py features     # feature engineering only
    python run.py analyze      # feature analysis / diagnostics
    python run.py train        # PCA + HMM + GARCH training
"""

import sys
from collect import collect
from features import prepare_features
from analyze import analyze
from train import train


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if step in ('all', 'collect'):
        market = collect()

    if step in ('all', 'features'):
        prepare_features()

    if step in ('all', 'analyze'):
        analyze()

    if step in ('all', 'train'):
        train()


if __name__ == '__main__':
    main()
