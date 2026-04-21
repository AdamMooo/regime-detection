"""
HDP-HMM vs StudentTHMM Comparison (Phase 6, MODEL-02)

Compares HDP-HMM (SVI) vs StudentTHMM on the same OOS split used in
Phase 4/5 diagnostics to lock the USE_HDP decision.

Procedure:
1. Load feature data and market data from DATA_DIR
2. Run StudentTHMM via walk_forward harness (OOS labels + dwell time)
3. Run HDP-HMM via manual fold loop on identical PCs (SVI inference only, D-02)
4. Compute OOS accuracy and mean dwell time for both models
5. Apply verdict logic (D-03): HDP wins only if +2pp accuracy AND meaningfully longer dwell
6. Print comparison table; write full results to data/hdp_comparison_results.json
7. Append "Model Architecture Decision (Phase 6)" section to docs/MODEL_CARD.md

Output:
- data/hdp_comparison_results.json: machine verdict + per-fold convergence + metrics
- stdout: formatted comparison table
"""

import os
import sys
import json
import logging
import warnings

import numpy as np
import pandas as pd

# Add repo root to path (matches select_k_via_crossval.py pattern)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import (
    HDP_TRUNCATION, N_STATES, DATA_DIR, MODEL_DIR,
    FEATURE_SUBSET, PCA_ROLLING_WINDOW, RANDOM_SEED,
)
from src.core.orchestrator import walk_forward
from src.core.hdp_hmm import (
    fit_hdp_hmm, posterior_mean_params,
    get_labels_and_probs, label_regimes_hdp, mcmc_diagnostics,
    hdp_stability_check,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


# ===================================================================
# Data Loading
# ===================================================================

def load_data():
    pass


# ===================================================================
# StudentTHMM OOS Path
# ===================================================================

def run_studenthmm_oos(market, features):
    pass


# ===================================================================
# HDP-HMM OOS Path
# ===================================================================

def run_hdp_oos(market, features, spy_returns):
    pass


# ===================================================================
# Metric Helpers
# ===================================================================

def mean_dwell_time(labels):
    pass


def oos_accuracy(is_named, oos_named):
    pass


# ===================================================================
# Verdict Logic
# ===================================================================

def compare_and_verdict(student_metrics, hdp_metrics):
    pass


# ===================================================================
# Main
# ===================================================================

def main():
    pass


if __name__ == '__main__':
    main()
