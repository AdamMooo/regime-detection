"""Reusable regime-label statistics.

Shared between run_paper_experiments.py (in-sample paper tables) and
src/core/walk_forward.py (out-of-sample validation), so both compute
within-regime stats and the vol-target backtest the same way.
"""

import numpy as np


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
