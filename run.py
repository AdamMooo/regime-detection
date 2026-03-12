"""
Run the full regime detection pipeline.

Usage:
    python run.py              # full pipeline
    python run.py collect      # data only
    python run.py analyze      # feature analysis only
    python run.py train        # model training only
"""

import sys
from collect import collect
from analyze import analyze
from train import train


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if step in ('all', 'collect'):
        collect()

    if step in ('all', 'analyze'):
        analyze()

    if step in ('all', 'train'):
        train()


if __name__ == '__main__':
    main()
