#!/usr/bin/env python3
"""Feature-ablation / discovery harness: refit the HDP-HMM on an arbitrary
feature subset and fingerprint the resulting regimes.

Answers "what happens to the regimes if we drop / swap a feature?" -- and is the
reusable tool for screening candidate features (fit with the candidate in, compare
fingerprints + label agreement + effective K against the current 4-feature model).

Usage
-----
    python scripts/feature_ablation.py                               # default: drop spy_ret
    python scripts/feature_ablation.py --features vol_index,yield_slope,nfci
    python scripts/feature_ablation.py --features spy_ret,vol_index,yield_slope,nfci

Reads data/processed/features_train.csv (standardized) + spx_data.csv (raw, for
fingerprints). Compares canonical (VIX-rank) labels to the committed 4-feature
baseline in results/regime_labels_train.csv.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.config import DATA_DIR, RESULTS_DIR, RANDOM_SEED
from src.core.hdp_hmm import (
    fit_hdp_hmm, posterior_mean_params, get_labels_and_probs, effective_K,
)
from src.core.walk_forward import merge_states_to_regimes, REGIME_NAMES

ALL_FEATURES = ['spy_ret', 'vol_index', 'yield_slope', 'nfci']


def fingerprint(features, seed):
    feat_path = os.path.join(DATA_DIR, 'processed', 'features_train.csv')
    raw_path = os.path.join(DATA_DIR, 'processed', 'spx_data.csv')
    feat = pd.read_csv(feat_path, index_col=0, parse_dates=True).dropna()
    raw = pd.read_csv(raw_path, index_col=0, parse_dates=True).reindex(feat.index)

    obs = feat[features].values
    _, samples = fit_hdp_hmm(obs, seed=seed)
    params = posterior_mean_params(samples)
    labels, _, _, active = get_labels_and_probs(obs, params)
    eff = effective_K(samples)

    vix = raw['vol_index'].values
    ret = raw['spy_ret'].values
    state_to_regime = merge_states_to_regimes(labels, vix, len(active))
    canon = np.array([state_to_regime[l] for l in labels])

    rows = []
    for r in range(3):
        m = canon == r
        if m.sum() == 0:
            continue
        rows.append({
            'Regime': REGIME_NAMES[r], 'N': int(m.sum()), 'Pct': m.mean() * 100,
            'RealVol%': ret[m].std() * np.sqrt(252) * 100,
            'VIX': vix[m].mean(),
            'AnnRet%': ret[m].mean() * 252 * 100,
            'slope': raw['yield_slope'].values[m].mean(),
            'nfci': raw['nfci'].values[m].mean(),
        })
    return pd.DataFrame(rows), eff, canon, feat.index


def baseline_agreement(canon, index):
    base_path = os.path.join(RESULTS_DIR, 'regime_labels_train.csv')
    if not os.path.exists(base_path):
        return None
    base = pd.read_csv(base_path)
    base.index = pd.to_datetime(base['date'])
    base = base.reindex(index)
    name_to_idx = {v: k for k, v in REGIME_NAMES.items()}
    base_idx = base['hdp_regime'].map(name_to_idx).values
    valid = ~pd.isna(base_idx)
    return float((canon[valid] == base_idx[valid]).mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--features', default='vol_index,yield_slope,nfci')
    ap.add_argument('--seed', type=int, default=RANDOM_SEED)
    args = ap.parse_args()
    features = [f.strip() for f in args.features.split(',')]

    print(f"\nAblation: fitting HDP-HMM on {features}\n")
    fp, eff, canon, index = fingerprint(features, args.seed)
    print(f"\nEffective K (raw states): mean={eff[0]:.1f}, mode={eff[2]}")
    print("\nRegime fingerprints (canonical, VIX-rank merged):")
    print(fp.round(2).to_string(index=False))

    agr = baseline_agreement(canon, index)
    if agr is not None:
        print(f"\nLabel agreement with committed 4-feature baseline: {agr:.1%}")
    print()


if __name__ == '__main__':
    main()
