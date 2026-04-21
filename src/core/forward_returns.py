"""Forward return analysis extracted from evaluation.py (Phase 6, MODEL-03).

Functions
---------
compute_forward_return_analysis(results, market)
    Regime-conditional forward returns with Kruskal-Wallis tests (DIAG-04)
analyze_forward_returns(results, market, horizons, assets)
    Detailed forward return analysis (Phase 4 addition)
"""

import logging
import numpy as np
import pandas as pd
from scipy.stats import kruskal

logger = logging.getLogger(__name__)


# ===================================================================
# Forward Return Analysis
# ===================================================================

def compute_forward_return_analysis(results, market):
    """Compute regime-conditional forward return analysis (DIAG-04).

    For each detected regime, compute 1d/5d/21d forward returns of SPY, EEM, TLT, HYG
    and test for statistical separation across regimes using Kruskal-Wallis.

    This is a VALIDATION DIAGNOSTIC ONLY. Forward returns are never used as model
    features or in training — doing so would introduce lookahead bias.

    Parameters
    ----------
    results : DataFrame
        Regime results with regime_name column and DatetimeIndex
    market : DataFrame
        Market data with price columns (SPY_close, EEM_close, TLT_close, HYG_close)

    Returns
    -------
    dict with keys:
        'kruskal_wallis': dict mapping '{asset}_{horizon}' -> {'statistic', 'p_value'}
        'mean_returns': dict mapping asset -> regime -> horizon -> mean return (%)
        'n_obs': int total observations used
    """
    if results is None or market is None:
        return {}

    regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]
    regimes = results[regime_col].dropna()

    assets = ['SPY', 'EEM', 'TLT', 'HYG']
    horizons = {'1d': 1, '5d': 5, '21d': 21}

    # Build aligned DataFrame: regime + forward returns for each asset/horizon
    aligned = pd.DataFrame({'regime': regimes})

    for asset in assets:
        col = f'{asset}_close'
        if col not in market.columns:
            continue
        price = market[col].reindex(aligned.index)
        for h_name, h_days in horizons.items():
            # Forward return: log(price[t+h] / price[t]) in percent
            fwd_ret = np.log(price.shift(-h_days) / price) * 100  # percent
            aligned[f'{asset}_{h_name}'] = fwd_ret.reindex(aligned.index)

    aligned = aligned.dropna(subset=['regime'])
    unique_regimes = sorted(aligned['regime'].dropna().unique())

    kw_results = {}
    mean_returns = {asset: {r: {} for r in unique_regimes} for asset in assets}

    for asset in assets:
        for h_name in horizons:
            col = f'{asset}_{h_name}'
            if col not in aligned.columns:
                continue

            groups = []
            for regime in unique_regimes:
                grp = aligned.loc[aligned['regime'] == regime, col].dropna()
                groups.append(grp.values)
                mean_returns[asset][regime][h_name] = float(grp.mean()) if len(grp) > 0 else None

            # Kruskal-Wallis: non-parametric test for equal distributions
            if len(groups) >= 2 and all(len(g) >= 5 for g in groups):
                try:
                    stat, p = kruskal(*groups)
                    kw_results[f'{asset}_{h_name}'] = {'statistic': float(stat), 'p_value': float(p)}
                except Exception:
                    kw_results[f'{asset}_{h_name}'] = {'statistic': None, 'p_value': None}

    print(f"\n  DIAG-04: Forward Return Analysis")
    print(f"    Assets: {', '.join(assets)}")
    print(f"    Horizons: {', '.join(horizons.keys())}")
    print(f"    Regimes: {unique_regimes}")
    print(f"\n    Kruskal-Wallis p-values (H0: equal distribution across regimes):")
    for key, val in kw_results.items():
        p = val.get('p_value')
        sig = '**' if p is not None and p < 0.05 else ''
        p_str = f"{p:.4f}" if p is not None else 'N/A'
        print(f"      {key}: p={p_str} {sig}")

    return {
        'kruskal_wallis': kw_results,
        'mean_returns': mean_returns,
        'n_obs': int(len(aligned.dropna())),
    }


def _get_blocks(mask):
    """Identify contiguous blocks of True values in a boolean array.

    Parameters
    ----------
    mask : ndarray
        Boolean array

    Returns
    -------
    blocks : list
        List of (start, end) indices for contiguous blocks
    """
    blocks = []
    in_block = False
    start = None

    for i, val in enumerate(mask):
        if val and not in_block:
            start = i
            in_block = True
        elif not val and in_block:
            blocks.append((start, i - 1))
            in_block = False

    if in_block:
        blocks.append((start, len(mask) - 1))

    return blocks


def analyze_forward_returns(results, market, horizons=None, assets=None):
    """Compute regime-conditional forward return analysis with Kruskal-Wallis tests.

    For each asset/horizon combination, computes forward log returns, groups them
    by regime, and runs a Kruskal-Wallis test to assess whether regime labels
    correspond to statistically different return distributions.

    IMPORTANT: Forward returns are diagnostic outputs only. They are never added
    as model features or used in training. This function is read-only with respect
    to regime assignments.

    Parameters
    ----------
    results : DataFrame
        Regime results with 'regime_name' column and DatetimeIndex.
    market : DataFrame
        Market price data with columns like 'SPY_close', 'EEM_close', etc.
    horizons : list of int, optional
        Forward return horizons in days. Default: [1, 5, 21].
    assets : list of str, optional
        Asset tickers. Default: ['SPY', 'EEM', 'TLT', 'HYG'].

    Returns
    -------
    dict
        Keys are (asset, horizon) tuples. Values are dicts with:
        - 'median_returns': {regime_name: median_forward_return}
        - 'kw_stat': Kruskal-Wallis H statistic
        - 'kw_pvalue': Kruskal-Wallis p-value
        - 'n_regimes': number of regimes tested
        Returns empty dict if data is insufficient.
    """
    if horizons is None:
        horizons = [1, 5, 21]
    if assets is None:
        assets = ['SPY', 'EEM', 'TLT', 'HYG']

    if results is None or market is None:
        logger.warning("analyze_forward_returns: results or market is None — skipping")
        return {}

    regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]

    results_output = {}

    print("\nRegime-Conditional Forward Return Analysis (DIAG-04):")
    print("=" * 70)
    print("Note: p < 0.05 suggests regime separation for this asset/horizon")
    print(f"  {'Asset':<6s} {'Horizon':>8s} {'KW stat':>10s} {'p-value':>10s}")
    print(f"  {'-' * 40}")

    for asset in assets:
        col = f"{asset}_close"
        if col not in market.columns:
            logger.debug("analyze_forward_returns: column %s not found — skipping %s", col, asset)
            continue

        prices = market[col].dropna()

        for horizon in horizons:
            # Compute forward log returns (shift back so t aligns with return over [t, t+h])
            fwd_ret = np.log(prices.shift(-horizon) / prices)

            # Align with regime labels
            common_idx = results.index.intersection(fwd_ret.index)
            if len(common_idx) < 10:
                continue

            regimes = results.loc[common_idx, regime_col]
            returns = fwd_ret.reindex(common_idx)

            # Drop NaN forward returns (last `horizon` rows will be NaN)
            valid = returns.notna()
            regimes = regimes[valid]
            returns = returns[valid]

            unique_regimes = regimes.unique()
            if len(unique_regimes) < 2:
                continue

            # Per-regime median returns
            median_returns = {}
            groups = []
            for reg in sorted(unique_regimes):
                reg_rets = returns[regimes == reg].values
                median_returns[reg] = float(np.median(reg_rets))
                groups.append(reg_rets)

            # Kruskal-Wallis test
            try:
                kw_stat, kw_pvalue = kruskal(*groups)
            except Exception:
                kw_stat, kw_pvalue = np.nan, np.nan

            results_output[(asset, horizon)] = {
                'median_returns': median_returns,
                'kw_stat': float(kw_stat),
                'kw_pvalue': float(kw_pvalue),
                'n_regimes': len(unique_regimes),
            }

            print(f"  {asset:<6s} {horizon:>5d}d     {kw_stat:>10.3f} {kw_pvalue:>10.4f}")

    # Per-regime median return summary
    if results_output:
        print(f"\n  Per-Regime Median Forward Returns (SPY):")
        print(f"  {'Regime':<20s}", end="")
        for h in horizons:
            print(f"  {h}d ret", end="")
        print()
        print(f"  {'-' * 50}")

        if results is not None:
            regime_col_vals = results[regime_col].dropna().unique()
            for reg in sorted(regime_col_vals):
                print(f"  {str(reg):<20s}", end="")
                for h in horizons:
                    key = ('SPY', h)
                    if key in results_output and reg in results_output[key]['median_returns']:
                        val = results_output[key]['median_returns'][reg] * 100
                        print(f"  {val:>+6.2f}%", end="")
                    else:
                        print(f"  {'N/A':>7s}", end="")
                print()

    print()
    return results_output


__all__ = [
    'compute_forward_return_analysis',
    'analyze_forward_returns',
]
