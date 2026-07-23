#!/usr/bin/env python3
"""Feature-discovery run: test a candidate feature set against the anti-collinearity
gate + the 'does it carve a new axis' test.

Candidate set here: {momentum(63d), VIX, yield_slope, breadth} -- drops the noisy
daily spy_ret for a slow trend axis, and adds cross-sectional sector dispersion
(breadth), the one candidate that varies daily AND should be orthogonal to vol.

Pipeline: build features -> correlation/VIF gate -> expanding-standardize ->
fit HDP -> raw-state fingerprints -> NEW-AXIS CHECK (do states with similar VIX
differ in breadth?) -> VIX-rank canonical agreement with the committed baseline.

Breadth = daily cross-sectional std of log returns across the 9 full-history SPDR
sectors (XLK/XLF/XLE/XLV/XLI/XLY/XLP/XLU/XLB). High = rotation/divergence,
low = everything moving together (e.g. broad crashes or melt-ups).
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
FEATS = ['momentum', 'vol_index', 'yield_slope', 'breadth']


def build_breadth():
    px = yf.download(SECTORS, start=START_DATE, end=END_DATE, progress=False)
    if isinstance(px.columns, pd.MultiIndex):
        px = px['Close']
    rets = np.log(px).diff()
    disp = rets.std(axis=1)
    disp.name = 'breadth'
    return disp


def vif(X):
    Z = (X - X.mean()) / X.std()
    cols = list(X.columns)
    out = {}
    for c in cols:
        y = Z[c].values
        others = Z[[k for k in cols if k != c]].values
        A = np.column_stack([np.ones(len(others)), others])
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        r2 = 1 - np.var(y - A @ coef) / np.var(y)
        out[c] = 1 / (1 - r2) if r2 < 1 else np.inf
    return out


def main():
    raw = pd.read_csv(os.path.join(DATA_DIR, 'processed', 'spx_data.csv'),
                      index_col=0, parse_dates=True)
    breadth = build_breadth().reindex(raw.index)
    momentum = raw['spy_ret'].rolling(63).sum()

    df = pd.DataFrame({
        'momentum': momentum,
        'vol_index': raw['vol_index'],
        'yield_slope': raw['yield_slope'],
        'breadth': breadth,
    }).dropna().loc[:TRAIN_END]

    print(f"\nCandidate set {FEATS}   N={len(df)}  "
          f"({df.index[0].date()}..{df.index[-1].date()})\n")
    print("Correlation:")
    print(df.corr().round(2).to_string(), "\n")
    print("VIF (>5 collinear):")
    for k, v in vif(df).items():
        print(f"  {k:12s} {v:.2f}")

    # Fit on expanding-standardized candidate features
    Xstd, _, _ = expanding_standardize(df.values)
    keep = ~np.isnan(Xstd).any(axis=1)
    Xstd, idx = Xstd[keep], df.index[keep]
    rawf = df.loc[idx]

    _, samples = fit_hdp_hmm(Xstd, seed=RANDOM_SEED)
    params = posterior_mean_params(samples)
    labels, _, _, active = get_labels_and_probs(Xstd, params)
    eff = effective_K(samples)
    print(f"\nEffective K: mean={eff[0]:.1f}, mode={eff[2]}")

    # Raw-state fingerprints (the object where a new axis would show up)
    vixv = rawf['vol_index'].values
    brv = rawf['breadth'].values
    fp = []
    for s in range(len(active)):
        m = labels == s
        if m.sum() < 5:
            continue
        fp.append({'state': s, 'days': int(m.sum()),
                   'VIX': vixv[m].mean(), 'breadth': brv[m].mean(),
                   'momentum': rawf['momentum'].values[m].mean(),
                   'slope': rawf['yield_slope'].values[m].mean()})
    fpdf = pd.DataFrame(fp).sort_values('VIX').reset_index(drop=True)
    print("\nRaw-state fingerprints (sorted by mean VIX):")
    print(fpdf.round(4).to_string(index=False))

    # NEW-AXIS CHECK: across states, is breadth ordering independent of VIX ordering?
    if len(fpdf) > 2:
        rho = np.corrcoef(fpdf['VIX'], fpdf['breadth'])[0, 1]
        print(f"\nNEW-AXIS CHECK: corr(state mean VIX, state mean breadth) = {rho:+.2f}")
        print("  |rho| near 0 => breadth carves states independently of vol (a real new axis).")
        print("  |rho| near 1 => breadth just re-orders on vol (no new axis, like slope/nfci did).")

    # Canonical agreement with committed 4-feature baseline
    s2r = merge_states_to_regimes(labels, vixv, len(active))
    canon = np.array([s2r[l] for l in labels])
    base = pd.read_csv(os.path.join('results', 'regime_labels_train.csv'))
    base.index = pd.to_datetime(base['date'])
    base = base.reindex(idx)
    n2i = {v: k for k, v in REGIME_NAMES.items()}
    bidx = base['hdp_regime'].map(n2i).values
    v = ~pd.isna(bidx)
    print(f"\nCanonical-label agreement with committed 4-feature baseline: "
          f"{(canon[v] == bidx[v]).mean():.1%}\n")


if __name__ == '__main__':
    main()
