"""Regime evaluation metrics and bootstrap confidence intervals.

This module implements:
1. Regime characteristic reporting
2. Bootstrap confidence intervals for regime statistics

IMPORTANT: VaR Backtesting (Phase 2.5.4)
-----------------------------------------
VaR backtesting functions were extracted to `src.core.var_backtesting` in
Phase 6 (MODEL-03). See `docs/MODEL_CARD.md` for the decision record.

Static regime-dependent VaR (fixed quantile per regime) FAILS Christoffersen test,
indicating exceedances cluster (volatility persistence not captured).

GARCH-conditional VaR (regime + volatility-adjusted) PASSES both tests:
  - Kupiec POF: p=0.952 (correct coverage)
  - Christoffersen: p=0.547 (exceedances independent, no clustering)

USE src.core.var_backtesting.compute_var_backtest_garch() for production risk limits.
For details, see docs/RISK_MODEL_CARD.md.

Functions
---------
evaluate(market, labels, name_map, spy_ret, label_source='In-Sample')
    Print regime characteristics
"""

import logging
import numpy as np
import pandas as pd

from src.config import RANDOM_SEED

logger = logging.getLogger(__name__)


# ===================================================================
# Evaluation
# ===================================================================

def evaluate(market, labels, name_map, spy_ret, label_source='In-Sample'):
    """Print regime characteristics using 5-day SPY returns (independent).

    Parameters
    ----------
    market : DataFrame
        Market data with 'VIX' column
    labels : Series or ndarray
        Regime labels
    name_map : dict
        Mapping from regime index to name
    spy_ret : Series
        SPY returns
    label_source : str
        Label for printing ('In-Sample', 'Out-of-Sample', etc.)
    """
    print(f"\nRegime Characteristics ({label_source}):")
    hdr = (f"  {'Regime':<14s} {'Days':>6s} {'Pct':>6s} {'VIX':>7s} "
           f"{'SPY5d':>7s}")
    print(hdr)
    print(f"  {'-' * 44}")

    for r in sorted(name_map.keys()):
        name = name_map[r]
        if hasattr(labels, 'index'):
            idx = labels.index[labels == r]
        else:
            idx = market.index[labels == r]
        n = len(idx)
        pct = n / len(labels) * 100

        vix_m = market.loc[idx, 'VIX'].mean() if 'VIX' in market else np.nan
        sp_m = spy_ret.reindex(idx).mean() * 100

        print(f"  {name:<14s} {n:>6d} {pct:>5.1f}% {vix_m:>7.1f} "
              f"{sp_m:>+6.2f}%")

    # Bootstrap confidence intervals for key statistics
    _print_bootstrap_cis(market, labels, name_map, spy_ret, label_source)


def _print_bootstrap_cis(market, labels, name_map, spy_ret, label_source,
                         n_boot=1000, block_size=21, ci=90):
    """Block bootstrap 90% confidence intervals for regime statistics.

    Parameters
    ----------
    market : DataFrame
        Market data
    labels : Series or ndarray
        Regime labels
    name_map : dict
        Mapping from regime index to name
    spy_ret : Series
        SPY returns
    label_source : str
        Label for output
    n_boot : int
        Number of bootstrap samples
    block_size : int
        Block size for block bootstrap
    ci : int
        Confidence interval (e.g., 90 for 90%)
    """
    label_arr = np.asarray(labels)
    T = len(label_arr)
    if T < block_size * 2:
        return

    n_blocks = (T + block_size - 1) // block_size
    rng = np.random.RandomState(RANDOM_SEED)

    # Pre-extract aligned data
    vix = market['VIX'].values if 'VIX' in market.columns else None
    spy = spy_ret.reindex(market.index).values if spy_ret is not None else None

    boot_stats = {r: {'vix': [], 'duration': [], 'persist': []}
                  for r in name_map}

    for _ in range(n_boot):
        # Draw block-bootstrap indices
        block_starts = rng.randint(0, T - block_size + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, min(s + block_size, T))
                              for s in block_starts])[:T]

        boot_labels = label_arr[idx]
        for r in name_map:
            mask = boot_labels == r
            if mask.sum() < 5:
                continue

            # VIX mean in this regime
            if vix is not None:
                vix_boot = vix[idx]
                boot_stats[r]['vix'].append(vix_boot[mask].mean())

            # Regime duration — transitions marks segment boundaries
            transitions = np.where(np.diff(np.concatenate([[-1], boot_labels, [-1]])) != 0)[0]
            durations = []
            for j in range(len(transitions) - 1):
                seg_start = transitions[j]
                seg_end = transitions[j + 1]
                if boot_labels[seg_start] == r:
                    durations.append(seg_end - seg_start)
            if durations:
                boot_stats[r]['duration'].append(np.mean(durations))

            # Persistence (auto-correlation)
            if mask.sum() > 2:
                curr = (boot_labels[:-1] == r).astype(int)
                next_r = (boot_labels[1:] == r).astype(int)
                if curr.sum() > 0:
                    persist = (curr * next_r).sum() / curr.sum()
                    boot_stats[r]['persist'].append(persist)

    # Print confidence intervals
    print(f"\n  Bootstrap CIs ({ci}%, {n_boot} samples, block_size={block_size}):")
    for r in sorted(name_map.keys()):
        name = name_map[r]
        print(f"    {name}:")

        # VIX CI
        if boot_stats[r]['vix']:
            vix_vals = np.array(boot_stats[r]['vix'])
            lo = np.percentile(vix_vals, (100 - ci) / 2)
            hi = np.percentile(vix_vals, 100 - (100 - ci) / 2)
            print(f"      VIX:      {vix_vals.mean():>6.1f}  [{lo:.1f}, {hi:.1f}]")

        # Duration CI
        if boot_stats[r]['duration']:
            dur_vals = np.array(boot_stats[r]['duration'])
            lo = np.percentile(dur_vals, (100 - ci) / 2)
            hi = np.percentile(dur_vals, 100 - (100 - ci) / 2)
            print(f"      Duration: {dur_vals.mean():>6.1f}  [{lo:.1f}, {hi:.1f}] days")

        # Persistence CI
        if boot_stats[r]['persist']:
            pers_vals = np.array(boot_stats[r]['persist'])
            lo = np.percentile(pers_vals, (100 - ci) / 2)
            hi = np.percentile(pers_vals, 100 - (100 - ci) / 2)
            print(f"      Persist:  {pers_vals.mean():>6.1%}  [{lo:.1%}, {hi:.1%}]")


__all__ = [
    'evaluate',
]
