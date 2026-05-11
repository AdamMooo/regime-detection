#!/usr/bin/env python
"""
Root-level CLI entry point for the regime-detection pipeline.

This wrapper delegates to scripts/run.py to maintain compatibility with
the documented README interface while keeping the implementation in scripts/.

Usage:
    python run.py              # full pipeline (8 stages)
    python run.py --validate   # full pipeline + walk-forward validation
    python run.py collect      # data download only
    python run.py features     # feature engineering only
    python run.py analyze      # feature diagnostics
    python run.py train        # PCA + HMM + GARCH training
    python run.py dashboard    # rebuild dashboard from saved model
    python run.py regime       # print current regime awareness
    python run.py trust        # print trust scorecard only
"""

import sys
import os
from pathlib import Path

# Add scripts/ to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

# Import and run the main pipeline script
from run import main

if __name__ == "__main__":
    sys.exit(main())
