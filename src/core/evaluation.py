"""Reusable regime-label statistics.

Shared between run_paper_experiments.py (in-sample paper tables) and
src/core/walk_forward.py (out-of-sample validation), so both compute
within-regime stats and the vol-target backtest the same way.

block_bootstrap_ci() / regime_delta_r2() answer a different question than
the backtest above: not "does vol-targeting on these regimes beat buy-and-
hold" (weak, noisy, never actually proven out), but "does the regime label
carry statistically significant information about anything, honestly
tested on genuinely out-of-sample data." See NOTES.md "Training-Window
Sensitivity" and the walk-forward OOS labels in data/oos_regime_labels.csv.
"""

import numpy as np
from sklearn.linear_model import LinearRegression


def regime_stats(labels, name_map, spy_ret, vix, model_name):
    """Within-regime stats: N, %, annualized return/vol, Sharpe, dwell time."""
    rows = []
    T = len(labels)
    label_arr = np.asarray(labels)
    for r in sorted(name_map.keys()):
        name = name_map[r]
        mask = label_arr == r
        n = mask.sum()
        if n < 5:
            continue
        ret = spy_ret[mask]
        ret_ann = float(ret.mean() * 252 * 100)
        vol_ann = float(ret.std() * np.sqrt(252) * 100)
        sharpe = ret_ann / vol_ann if vol_ann > 0 else np.nan
        vix_mean = float(vix[mask].mean())

        spells = []
        in_spell = False
        count = 0
        for t in range(T):
            if label_arr[t] == r:
                in_spell = True
                count += 1
            else:
                if in_spell:
                    spells.append(count)
                    in_spell = False
                    count = 0
        if in_spell:
            spells.append(count)
        dwell = float(np.mean(spells)) if spells else 0.0

        rows.append({
            'Model': model_name, 'Regime': name, 'N': int(n), 'Pct': n / T * 100,
            'AnnRet': ret_ann, 'AnnVol': vol_ann, 'Sharpe': sharpe,
            'VIX': vix_mean, 'Dwell': dwell,
        })
    return rows


def vol_target_backtest(spy_ret, vol_estimate, target_vol_pct=15.0, max_leverage=1.5):
    """Scale daily SPY exposure by target_vol / current_vol_estimate."""
    vol_est = np.where(vol_estimate > 1e-6, vol_estimate, target_vol_pct)
    sizes = np.clip(target_vol_pct / vol_est, 0.0, max_leverage)
    port = spy_ret * sizes

    ann_ret = float(port.mean() * 252 * 100)
    ann_vol = float(port.std() * np.sqrt(252) * 100)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan
    cum = np.cumprod(1 + port)
    roll_max = np.maximum.accumulate(cum)
    max_dd = float(((cum - roll_max) / roll_max).min() * 100)

    size_changes = np.abs(np.diff(sizes))
    turnover_annual = float((size_changes > 0.01).mean() * 252)

    return {
        'Ann. Ret (%)': ann_ret, 'Ann. Vol (%)': ann_vol, 'Sharpe': sharpe,
        'Max DD (%)': max_dd, 'Rebalances/yr': turnover_annual,
    }


def regime_delta_r2(regime_idx, vix, target):
    """R^2 improvement from adding regime dummies to a VIX-only regression.

    Same methodology as the paper's existing Table 3 (information-content
    regression), generalized to any target series -- pass forward returns
    for the original "does the regime predict returns" question, or forward
    realized volatility for "does the regime predict vol" (arguably the more
    honest claim for a volatility-regime detector to make).

    Parameters
    ----------
    regime_idx : ndarray (T,) int -- regime label per row (0/1/2)
    vix : ndarray (T,) -- VIX level per row
    target : ndarray (T,) -- the series being predicted (e.g. forward return
        or forward realized vol). Must already be aligned/shifted by the
        caller -- this function does no shifting itself.

    Returns
    -------
    float: R^2(VIX + regime dummies) - R^2(VIX alone). This is the
    statistic block_bootstrap_ci() resamples to get a confidence interval.
    """
    X_vix = vix.reshape(-1, 1)
    r2_vix = LinearRegression().fit(X_vix, target).score(X_vix, target)

    dummies = np.eye(3)[regime_idx][:, 1:]   # drop_first, matches paper's Table 3
    X_full = np.hstack([X_vix, dummies])
    r2_full = LinearRegression().fit(X_full, target).score(X_full, target)

    return r2_full - r2_vix


def block_bootstrap_ci(arrays, statistic_fn, n_boot=1000, block_size=21, ci=90, seed=42):
    """Block-bootstrap confidence interval for a statistic on time-series data.

    Standard technique when observations are serially correlated (daily
    returns/vol cluster -- VIX's own day-to-day autocorrelation is ~0.9).
    Resampling individual rows independently (an i.i.d. bootstrap) breaks
    that correlation and understates the true sampling variability of any
    statistic computed from the sequence -- it makes noise look significant.
    Resampling whole contiguous BLOCKS of `block_size` consecutive rows (with
    replacement) instead preserves each block's internal serial correlation.

    Parameters
    ----------
    arrays : tuple of ndarrays, all length T
        The raw per-day arrays statistic_fn needs (e.g. (regime_idx, vix,
        target)). All arrays are resampled with the SAME row indices each
        draw, so their joint (same-day) relationship survives resampling.
    statistic_fn : callable
        Takes the same arrays (resampled) and returns a single float --
        e.g. regime_delta_r2.
    n_boot : int
        Number of bootstrap resamples.
    block_size : int
        Trading days per block (21 ~ 1 trading month -- matches this
        project's prior convention from the pre-refactor evaluation.py).
    ci : int
        Confidence level, e.g. 90 for a 90% CI.
    seed : int

    Returns
    -------
    observed : float -- statistic_fn computed on the real (unresampled) data
    ci_low, ci_high : float -- percentile bootstrap CI bounds
    boot_dist : ndarray (n_boot,) -- full bootstrap distribution
    """
    T = len(arrays[0])
    rng = np.random.RandomState(seed)
    observed = statistic_fn(*arrays)

    n_blocks = int(np.ceil(T / block_size))
    boot_stats = np.empty(n_boot)
    for b in range(n_boot):
        block_starts = rng.randint(0, T - block_size + 1, size=n_blocks)
        resample_idx = np.concatenate([np.arange(s, s + block_size) for s in block_starts])[:T]
        resampled_arrays = [a[resample_idx] for a in arrays]
        boot_stats[b] = statistic_fn(*resampled_arrays)

    lo_pct, hi_pct = (100 - ci) / 2, 100 - (100 - ci) / 2
    ci_low, ci_high = np.percentile(boot_stats, [lo_pct, hi_pct])
    return observed, ci_low, ci_high, boot_stats


def block_permutation_test(arrays, statistic_fn, permute_arg=0, n_perm=1000,
                           block_size=21, seed=42):
    """Block-permutation (Monte-Carlo) test: is statistic_fn's value larger than
    what RANDOM rearrangements of ONE input series would produce?

    Why this and not block_bootstrap_ci: for statistics like regime_delta_r2 the
    value is >= 0 *by construction* (adding OLS regressors never lowers in-sample
    R^2), so a bootstrap CI almost always excludes 0 and proves nothing about a
    real effect. This test instead breaks the link between arrays[permute_arg]
    (e.g. the regime label) and the other arrays (VIX, target) by block-shuffling
    it while holding the rest fixed in time. The resulting null distribution is
    "what delta-R^2 do 2 spuriously-placed dummies give?" -- NOT centered at 0 --
    and the p-value asks whether the real labels beat that.

    BLOCK shuffling (permute the order of contiguous blocks), not row shuffling:
    preserves the permuted series' own serial correlation and run structure. Row
    shuffling would turn a persistent regime series into white noise, collapsing
    the null's spread and overstating significance -- the mirror image of why
    block_bootstrap_ci resamples blocks rather than rows.

    Parameters
    ----------
    arrays : tuple of ndarrays, all length T
        Same convention as block_bootstrap_ci -- e.g. (regime_idx, vix, target).
    statistic_fn : callable
        Takes the (possibly permuted) arrays, returns a single float.
    permute_arg : int
        Index into `arrays` of the series to shuffle (0 = the regime label).
        Every other array is held fixed in its original time order.
    n_perm : int
        Number of permutations (null draws).
    block_size : int
        Trading days per block (21 ~ 1 month), matching block_bootstrap_ci.
    seed : int

    Returns
    -------
    observed : float -- statistic_fn on the real (unpermuted) arrays
    p_value  : float -- (1 + #{null >= observed}) / (n_perm + 1)
    null_dist: ndarray (n_perm,) -- the permutation null distribution
    """
    T = len(arrays[0])
    rng = np.random.RandomState(seed)
    observed = statistic_fn(*arrays)

    # Permute the ORDER of contiguous blocks (each row used exactly once) so the
    # permuted series keeps its marginal distribution and within-block serial
    # structure -- only its timing relative to the other arrays is destroyed.
    blocks = [np.arange(i, min(i + block_size, T)) for i in range(0, T, block_size)]
    null_dist = np.empty(n_perm)
    for b in range(n_perm):
        perm_idx = np.concatenate([blocks[i] for i in rng.permutation(len(blocks))])
        permuted = list(arrays)
        permuted[permute_arg] = arrays[permute_arg][perm_idx]
        null_dist[b] = statistic_fn(*permuted)

    # +1 in numerator AND denominator: the observed value counts as one of its own
    # null draws, so a finite Monte-Carlo test can never return exactly 0
    # (North et al. 2002).
    p_value = (1 + np.sum(null_dist >= observed)) / (n_perm + 1)
    return observed, p_value, null_dist
