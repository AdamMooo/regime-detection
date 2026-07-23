#!/usr/bin/env python3
"""Reduced, principled feature-combination search (not brute-force 2^N).

We already know: spy_ret is noise (dropped -> momentum); dispersion-breadth is a
vol proxy (rejected, rho=0.99); the 4 base features aren't collinear. So we test
only the combinations that answer a specific question, adding PARTICIPATION breadth
(% of sectors above their 200-DMA -- can go low while VIX is low, unlike dispersion).

Candidate features:
  M = momentum(63d)   V = VIX   S = yield_slope   N = NFCI(contains VIX)   P = participation breadth

Configs & the question each answers:
  M,V,S,N       swap-baseline (VIX in, macro/credit) -- reference
  M,S,N,P       REMOVE VIX (NFCI still carries partial vol) -- do regimes survive?
  M,S,P         REMOVE VIX & NFCI (no implied-vol input at all) -- do we STILL get a vol ladder?
  M,V,S,P       swap NFCI(=partial VIX) for participation breadth -- is P a better 4th axis?
  V,N           pure vol/credit -- what a minimal vol model looks like

For each: effective K; the canonical (rank-by-raw-VIX) Low->High realized-vol ladder and
mean-VIX separation (does it recover vol regimes even without VIX as an input?); agreement
with the committed 4-feature baseline; and where P is present, the NEW-AXIS check
corr(state realized-vol, state participation) -- near 0 => P carves an independent axis.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.config import DATA_DIR, RANDOM_SEED, START_DATE, END_DATE, TRAIN_END
from src.core.inference import expanding_standardize
from src.core.hdp_hmm import (
    fit_hdp_hmm, posterior_mean_params, get_labels_and_probs, effective_K,
)
from src.core.walk_forward import merge_states_to_regimes, REGIME_NAMES

SECTORS = ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLY', 'XLP', 'XLU', 'XLB']

CONFIGS = {
    'M,V,S,N  (swap-baseline)':   ['momentum', 'vol_index', 'yield_slope', 'nfci'],
    'M,S,N,P  (no VIX)':          ['momentum', 'yield_slope', 'nfci', 'participation'],
    'M,S,P    (no VIX/NFCI)':     ['momentum', 'yield_slope', 'participation'],
    'M,V,S,P  (P instead of N)':  ['momentum', 'vol_index', 'yield_slope', 'participation'],
    'V,N      (vol/credit only)': ['vol_index', 'nfci'],
}


def build_features():
    raw = pd.read_csv(os.path.join(DATA_DIR, 'processed', 'spx_data.csv'),
                      index_col=0, parse_dates=True)
    px = yf.download(SECTORS, start=START_DATE, end=END_DATE, progress=False)
    if isinstance(px.columns, pd.MultiIndex):
        px = px['Close']
    participation = (px > px.rolling(200).mean()).mean(axis=1)

    feats = pd.DataFrame({
        'momentum': raw['spy_ret'].rolling(63).sum(),
        'vol_index': raw['vol_index'],
        'yield_slope': raw['yield_slope'],
        'nfci': raw['nfci'],
        'participation': participation.reindex(raw.index),
    })
    return raw, feats


def canonical_baseline(index):
    base = pd.read_csv(os.path.join('results', 'regime_labels_train.csv'))
    base.index = pd.to_datetime(base['date'])
    n2i = {v: k for k, v in REGIME_NAMES.items()}
    return base.reindex(index)['hdp_regime'].map(n2i)


def run_config(name, cols, raw, feats):
    df = feats[cols].dropna().loc[:TRAIN_END]
    Xstd, _, _ = expanding_standardize(df.values)
    keep = ~np.isnan(Xstd).any(axis=1)
    Xstd, idx = Xstd[keep], df.index[keep]

    _, samples = fit_hdp_hmm(Xstd, seed=RANDOM_SEED)
    params = posterior_mean_params(samples)
    labels, _, _, active = get_labels_and_probs(Xstd, params)
    eff_mode = effective_K(samples)[2]

    r = raw.reindex(idx)
    vix = r['vol_index'].values
    ret = r['spy_ret'].values
    s2r = merge_states_to_regimes(labels, vix, len(active))   # rank by raw VIX (always avail)
    canon = np.array([s2r[l] for l in labels])

    def regime_rv(k):
        m = canon == k
        return ret[m].std() * np.sqrt(252) * 100 if m.sum() > 5 else np.nan

    def regime_vix(k):
        m = canon == k
        return vix[m].mean() if m.sum() > 5 else np.nan

    rv_low, rv_high = regime_rv(0), regime_rv(2)
    vix_low, vix_high = regime_vix(0), regime_vix(2)

    # New-axis check (only meaningful if participation is a feature)
    newaxis = np.nan
    if 'participation' in cols:
        part = feats['participation'].reindex(idx).values
        srv, sp = [], []
        for s in range(len(active)):
            m = labels == s
            if m.sum() > 5:
                srv.append(ret[m].std())
                sp.append(part[m].mean())
        if len(srv) > 2:
            newaxis = np.corrcoef(srv, sp)[0, 1]

    base = canonical_baseline(idx)
    v = ~base.isna().values
    agree = (canon[v] == base.values[v]).mean()

    return {
        'config': name, 'K': eff_mode,
        'RV_low': rv_low, 'RV_high': rv_high, 'RV_spread': rv_high / rv_low,
        'VIX_low': vix_low, 'VIX_high': vix_high,
        'agree_base': agree, 'P_newaxis_rho': newaxis,
    }


def main():
    raw, feats = build_features()
    rows = []
    for name, cols in CONFIGS.items():
        print(f"\n=== {name}  ->  {cols} ===")
        rows.append(run_config(name, cols, raw, feats))

    out = pd.DataFrame(rows)
    pd.set_option('display.width', 200)
    print("\n\n================ REDUCED SEARCH SUMMARY ================\n")
    print(out.round(3).to_string(index=False))
    print("\nRV_low/RV_high = realized vol (%) of the canonical Low/High regime")
    print("RV_spread = High/Low ratio (big => still a vol ladder, even without VIX as input)")
    print("VIX_low/high = mean VIX in those regimes (does it recover vol separation w/o VIX?)")
    print("agree_base = label agreement with committed 4-feature model")
    print("P_newaxis_rho = corr(state realized-vol, state participation); ~0 => P is a new axis")


if __name__ == '__main__':
    main()
