"""
Trust scorecard — single pass/fail/warn verdict for the regime signal.

Aggregates all validation checks so a trader can quickly assess
whether the signal is worth acting on today.
"""

import os
import numpy as np
import pandas as pd
from typing import Any

from config import DATA_DIR, MAX_DATA_STALENESS_DAYS


# ── Individual checks ─────────────────────────────────────────────

def _check_data_freshness(results: pd.DataFrame) -> dict[str, Any]:
    """Is the underlying data current?"""
    last_date = results.index[-1]
    today = pd.Timestamp.now().normalize()
    stale = int(np.busday_count(last_date.date(), today.date()))

    if stale <= 2:
        status = 'PASS'
    elif stale <= 5:
        status = 'WARN'
    else:
        status = 'FAIL'

    return {
        'name': 'Data Freshness',
        'status': status,
        'detail': f'{stale} trading days stale (last: {last_date.date()})',
    }


def _check_from_validation(validation: dict, key: str, name: str,
                           pass_test, warn_test=None,
                           detail_fn=None) -> dict[str, Any]:
    """Generic check builder from validation dict."""
    val = validation.get(key)
    if val is None:
        return {'name': name, 'status': 'N/A', 'detail': 'Not computed'}

    if pass_test(val):
        status = 'PASS'
    elif warn_test and warn_test(val):
        status = 'WARN'
    else:
        status = 'FAIL'

    detail = detail_fn(val) if detail_fn else str(val)
    return {'name': name, 'status': status, 'detail': detail}


# ── Main scorecard ────────────────────────────────────────────────

def compute_trust_scorecard(signals: dict[str, Any]) -> dict[str, Any]:
    """
    Aggregate all validation checks into a single trust verdict.

    Parameters
    ----------
    signals : dict from compute_signals()

    Returns
    -------
    dict with 'overall', 'score', 'checks', 'timestamp'
    """
    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if os.path.exists(results_path):
        results = pd.read_csv(results_path, index_col=0, parse_dates=True)
    else:
        results = None

    checks = []
    val = signals.get('validation', {})
    oos = signals.get('oos_validation', {})
    cal = signals.get('calibration', {})

    # 1. Data freshness
    if results is not None:
        checks.append(_check_data_freshness(results))
    else:
        checks.append({'name': 'Data Freshness', 'status': 'N/A', 'detail': 'No results file'})

    # 2. Regime separation
    checks.append(_check_from_validation(
        val, 'separation_pvalue', 'Regime Separation',
        pass_test=lambda p: p < 0.01,
        warn_test=lambda p: p < 0.05,
        detail_fn=lambda p: f'p={p:.2e}',
    ))

    # 3. Vol ordering
    checks.append(_check_from_validation(
        val, 'vol_ordering_match', 'Vol Ordering',
        pass_test=lambda v: v is True,
        detail_fn=lambda v: 'Match' if v else 'Mismatch',
    ))

    # 4. Persistence
    checks.append(_check_from_validation(
        val, 'median_run_length', 'Persistence',
        pass_test=lambda v: v > 5,
        warn_test=lambda v: v > 3,
        detail_fn=lambda v: f'Median {v:.0f} days',
    ))

    # 5. VaR backtest
    var_bt = val.get('var_backtest', {})
    if var_bt:
        n_total = len(var_bt)
        n_pass = sum(1 for v in var_bt.values() if v.get('ok'))
        ratio = n_pass / n_total if n_total > 0 else 0
        if ratio == 1.0:
            status = 'PASS'
        elif ratio >= 0.5:
            status = 'WARN'
        else:
            status = 'FAIL'
        checks.append({
            'name': 'VaR Backtest',
            'status': status,
            'detail': f'{n_pass}/{n_total} regimes pass',
        })
    else:
        checks.append({'name': 'VaR Backtest', 'status': 'N/A', 'detail': 'Not computed'})

    # 6. OOS agreement
    if oos.get('available'):
        agr = oos['agreement_rate']
        if agr > 0.70:
            status = 'PASS'
        elif agr > 0.50:
            status = 'WARN'
        else:
            status = 'FAIL'
        checks.append({
            'name': 'OOS Agreement',
            'status': status,
            'detail': f'{agr:.1%}',
        })
    else:
        checks.append({'name': 'OOS Agreement', 'status': 'N/A',
                        'detail': oos.get('reason', 'No OOS data')})

    # 7. OOS separation
    if oos.get('available') and 'oos_separation_pvalue' in oos:
        p = oos['oos_separation_pvalue']
        if not np.isnan(p):
            if p < 0.01:
                status = 'PASS'
            elif p < 0.05:
                status = 'WARN'
            else:
                status = 'FAIL'
            checks.append({
                'name': 'OOS Separation',
                'status': status,
                'detail': f'p={p:.2e}',
            })
        else:
            checks.append({'name': 'OOS Separation', 'status': 'N/A', 'detail': 'No p-value'})
    else:
        checks.append({'name': 'OOS Separation', 'status': 'N/A', 'detail': 'No OOS data'})

    # 8. Calibration
    if cal.get('available'):
        ece = cal['ece']
        if ece < 0.05:
            status = 'PASS'
        elif ece < 0.10:
            status = 'WARN'
        else:
            status = 'FAIL'
        checks.append({
            'name': 'Calibration',
            'status': status,
            'detail': f'ECE={ece:.1%}',
        })
    else:
        checks.append({'name': 'Calibration', 'status': 'N/A',
                        'detail': cal.get('reason', 'Not computed')})

    # Overall verdict
    statuses = [c['status'] for c in checks]
    n_pass = statuses.count('PASS')
    n_warn = statuses.count('WARN')
    n_fail = statuses.count('FAIL')
    n_na = statuses.count('N/A')

    if n_fail > 0:
        overall = 'FAIL'
    elif n_warn > 0:
        overall = 'WARN'
    else:
        overall = 'PASS'

    return {
        'overall': overall,
        'score': f'{n_pass} PASS, {n_warn} WARN, {n_fail} FAIL, {n_na} N/A',
        'checks': checks,
        'timestamp': pd.Timestamp.now().isoformat(),
    }


def format_scorecard(scorecard: dict[str, Any], width: int = 62) -> str:
    """Format the trust scorecard as a printable string."""
    lines = []
    lines.append(f"\n{'=' * width}")
    lines.append(f"  Trust Scorecard{' ' * (width - 32)}{scorecard['overall']:>10s}")
    lines.append(f"{'=' * width}")

    for c in scorecard['checks']:
        status = c['status']
        tag = {'PASS': 'PASS', 'WARN': 'WARN', 'FAIL': 'FAIL', 'N/A': 'N/A '}[status]
        lines.append(f"  {c['name']:<21s}: {tag}  ({c['detail']})")

    lines.append(f"{'─' * width}")
    lines.append(f"  Overall{' ' * 14}: {scorecard['overall']}  ({scorecard['score']})")
    lines.append(f"{'=' * width}")
    return '\n'.join(lines)
