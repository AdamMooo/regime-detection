"""Regime evaluation metrics, validation tests, and diagnostics.

This module implements:
1. Regime characteristic reporting
2. VaR backtesting (Kupiec POF, Christoffersen independence tests)
3. Bootstrap confidence intervals for regime statistics

Functions
---------
evaluate(market, labels, name_map, spy_ret, label_source='In-Sample')
    Print regime characteristics
compute_var_backtest(spy_returns, labels, name_map, alpha=0.05)
    Kupiec POF and Christoffersen tests for VaR validity
compute_var_backtest_garch(spy_returns, regime_probs, labels, name_map, alpha=0.05)
    GARCH-based VaR backtest
kupiec_pof_test(n_obs, n_exc, alpha)
    Kupiec proportion of failures test
christoffersen_test(spy_returns, labels, name_map, alpha)
    Christoffersen independence test
"""

import logging
import numpy as np
import pandas as pd
from scipy.stats import binom, chi2

from config import RANDOM_SEED, VAR_ALPHA

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

            # Regime duration
            runs = np.where(np.diff(np.concatenate([[-1], boot_labels, [-1]])) != 0)[0]
            durations = []
            for i in range(0, len(runs) - 1, 2):
                if i + 1 < len(runs):
                    d = runs[i + 1] - runs[i]
                    if boot_labels[runs[i]] == r:
                        durations.append(d)
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


# ===================================================================
# VaR Backtests
# ===================================================================

def compute_var_backtest(spy_returns, labels, name_map, alpha=VAR_ALPHA):
    """Kupiec POF and Christoffersen tests for VaR validity.

    Tests whether the regime's realized volatility and VaR are consistent.

    Parameters
    ----------
    spy_returns : Series
        SPY daily log-returns
    labels : ndarray
        Regime labels
    name_map : dict
        Mapping from regime index to name
    alpha : float
        VaR confidence level (e.g., 0.05 for 95% VaR)

    Returns
    -------
    results : DataFrame
        VaR backtest results per regime
    """
    print(f"\nVaR Backtest ({alpha:.1%} confidence level):")
    print(f"  {'Regime':<14s} {'Obs':>5s} {'Exc':>5s} {'Rate':>6s} "
          f"{'Kupiec':>7s} {'Christo':>7s}")
    print(f"  {'-' * 60}")

    results = []
    for r in sorted(name_map.keys()):
        name = name_map[r]
        mask = labels == r
        if mask.sum() < 10:
            continue

        y = spy_returns[mask].dropna()
        z_crit = np.sqrt(2) * np.erfinv(2 * (1 - alpha) - 1)
        var_threshold = z_crit * y.std()
        n_obs = len(y)
        n_exc = (y < -var_threshold).sum()

        kupiec_stat = kupiec_pof_test(n_obs, n_exc, alpha)
        try:
            christo_stat = christoffersen_test(spy_returns, labels, name_map, alpha)
        except:
            christo_stat = np.nan

        exc_rate = n_exc / n_obs if n_obs > 0 else 0
        kupiec_pval = 1 - chi2.cdf(kupiec_stat, df=1) if not np.isnan(kupiec_stat) else np.nan
        christo_pval = 1 - chi2.cdf(christo_stat, df=1) if not np.isnan(christo_stat) else np.nan

        results.append({
            'regime': r,
            'name': name,
            'n_obs': n_obs,
            'n_exc': n_exc,
            'exc_rate': exc_rate,
            'kupiec_stat': kupiec_stat,
            'christo_stat': christo_stat,
            'kupiec_pval': kupiec_pval,
            'christo_pval': christo_pval,
        })

        print(f"  {name:<14s} {n_obs:>5d} {n_exc:>5d} {exc_rate:>5.1%} "
              f"{kupiec_pval:>7.2%} {christo_pval:>7.2%}")

    return pd.DataFrame(results) if results else pd.DataFrame()


def kupiec_pof_test(n_obs, n_exc, alpha):
    """Kupiec proportion of failures (POF) test.

    Tests whether the number of VaR exceedances is consistent with the
    expected frequency under the null hypothesis.

    Parameters
    ----------
    n_obs : int
        Number of observations
    n_exc : int
        Number of VaR exceedances
    alpha : float
        VaR confidence level

    Returns
    -------
    stat : float
        Test statistic (chi-squared)
    """
    p = alpha  # Expected failure rate
    p_hat = n_exc / n_obs if n_obs > 0 else 0
    lr = 2 * (n_exc * np.log(p_hat / p) + (n_obs - n_exc) * np.log((1 - p_hat) / (1 - p)))
    return lr


def christoffersen_test(spy_returns, labels, name_map, alpha):
    """Christoffersen independence test.

    Tests whether VaR exceedances are independent (no clustering).

    Parameters
    ----------
    spy_returns : Series
        SPY daily log-returns
    labels : ndarray
        Regime labels
    name_map : dict
        Mapping from regime index to name
    alpha : float
        VaR confidence level

    Returns
    -------
    stat : float
        Test statistic (chi-squared with 1 DoF)
    """
    # Combine all regimes for this test
    y = spy_returns.dropna()
    z_crit = np.sqrt(2) * np.erfinv(2 * (1 - alpha) - 1)
    var_threshold = z_crit * y.std()
    indicators = (y < -var_threshold).astype(int).values

    # Count transitions
    n00 = sum((indicators[:-1] == 0) & (indicators[1:] == 0))
    n01 = sum((indicators[:-1] == 0) & (indicators[1:] == 1))
    n10 = sum((indicators[:-1] == 1) & (indicators[1:] == 0))
    n11 = sum((indicators[:-1] == 1) & (indicators[1:] == 1))

    if n01 + n11 == 0 or n10 + n11 == 0:
        return np.nan

    p01 = (n01) / (n00 + n01) if (n00 + n01) > 0 else 0
    p11 = (n11) / (n10 + n11) if (n10 + n11) > 0 else 0
    p = (n01 + n11) / (n00 + n01 + n10 + n11) if (n00 + n01 + n10 + n11) > 0 else 0

    if p == 0 or p == 1:
        return np.nan

    lr_ind = 2 * (n01 * np.log(p01 / p) + n11 * np.log(p11 / p) +
                  (n00 + n10) * np.log((1 - p01) / (1 - p)))
    return lr_ind


def compute_var_backtest_garch(spy_returns, regime_probs, labels, name_map,
                               alpha=VAR_ALPHA):
    """GARCH-based VaR backtest.

    Uses conditional volatility from GARCH model to compute dynamic VaR.

    Parameters
    ----------
    spy_returns : Series
        SPY daily log-returns
    regime_probs : ndarray
        Regime probabilities (T, n_states)
    labels : ndarray
        Regime labels
    name_map : dict
        Mapping from regime index to name
    alpha : float
        VaR confidence level

    Returns
    -------
    results : DataFrame
        VaR backtest results
    """
    try:
        from arch import arch_model
    except ImportError:
        return pd.DataFrame()

    y = spy_returns.dropna() * 100  # percent returns
    am = arch_model(y, vol='GARCH', p=1, q=1, mean='Zero', dist='normal')
    res = am.fit(disp='off')
    cond_vol = res.conditional_volatility.values / 100  # back to decimal

    z_crit = np.sqrt(2) * np.erfinv(2 * (1 - alpha) - 1)
    var_dynamic = z_crit * cond_vol
    n_exc = (y.values < -var_dynamic).sum()
    n_obs = len(y)

    print(f"\nGARCH-based VaR Backtest ({alpha:.1%} confidence):")
    print(f"  Full sample: {n_obs} obs, {n_exc} exceedances "
          f"({n_exc / n_obs:.1%} rate)")

    return pd.DataFrame({
        'regime': ['full'],
        'n_obs': [n_obs],
        'n_exc': [n_exc],
        'exc_rate': [n_exc / n_obs],
    })


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


__all__ = [
    'evaluate',
    'compute_var_backtest',
    'compute_var_backtest_garch',
    'kupiec_pof_test',
    'christoffersen_test',
]
