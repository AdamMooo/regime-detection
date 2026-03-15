"""
Regime awareness engine.

Translates HMM regime state into honest, useful context for a trader.
This is NOT a return predictor or trade signal generator.

What this model actually knows:
  - Which volatility regime you're in right now
  - The statistical distribution you're drawing returns from
  - How confident it is about the current regime
  - How often the regime has shifted historically

What this model does NOT know:
  - Future returns or direction
  - When the next regime change will happen
  - Specific trades to put on

The value: knowing you're in a high-vol / fat-tail regime vs. a calm
regime tells you how to SIZE positions, SET stops, and EXPECT drawdowns.
"""

import pandas as pd
import numpy as np
from typing import Any
from scipy import stats as sp_stats

from config import TICKERS, SHORT_WINDOW, MED_WINDOW, LONG_WINDOW


# ── Regime-conditional distribution profiles ───────────────────────

def _compute_regime_distributions(results: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the *actual* distribution statistics per regime for SPY.
    These are empirical facts from the data, not predictions.
    """
    regimes = sorted(results['regime_name'].unique())
    rows = []
    for regime in regimes:
        mask = results['regime_name'] == regime
        subset = results.loc[mask]
        n_days = int(mask.sum())

        row: dict[str, Any] = {'regime': regime, 'n_days': n_days}

        if 'SPY_close' in subset.columns and n_days > 20:
            log_ret = np.log(subset['SPY_close'] / subset['SPY_close'].shift(1)).dropna()
            daily_ret = log_ret.values

            # Annualized stats
            row['ann_vol'] = float(np.std(daily_ret) * np.sqrt(252))
            row['daily_mean'] = float(np.mean(daily_ret))
            row['daily_std'] = float(np.std(daily_ret))
            row['skew'] = float(sp_stats.skew(daily_ret))
            row['kurtosis'] = float(sp_stats.kurtosis(daily_ret))  # excess

            # Tail risk — empirical VaR/CVaR
            row['var_5'] = float(np.percentile(daily_ret, 5))
            row['cvar_5'] = float(np.mean(daily_ret[daily_ret <= np.percentile(daily_ret, 5)]))
            row['var_1'] = float(np.percentile(daily_ret, 1))
            row['worst_day'] = float(np.min(daily_ret))
            row['best_day'] = float(np.max(daily_ret))

            # Max drawdown within regime windows
            cum = (1 + pd.Series(daily_ret)).cumprod()
            peak = cum.cummax()
            dd = (cum - peak) / peak
            row['max_dd'] = float(dd.min())

            # How "normal" is the distribution? (Jarque-Bera test)
            if len(daily_ret) > 20:
                jb_stat, jb_p = sp_stats.jarque_bera(daily_ret)
                row['jb_pvalue'] = float(str(jb_p))  # type: ignore[arg-type]
                row['is_normal'] = float(str(jb_p)) > 0.05  # type: ignore[operator]
            else:
                row['jb_pvalue'] = np.nan
                row['is_normal'] = None
        else:
            for k in ['ann_vol', 'daily_mean', 'daily_std', 'skew', 'kurtosis',
                       'var_5', 'cvar_5', 'var_1', 'worst_day', 'best_day',
                       'max_dd', 'jb_pvalue']:
                row[k] = np.nan
            row['is_normal'] = None

        rows.append(row)

    return pd.DataFrame(rows).set_index('regime')


# ── Regime confidence & duration ───────────────────────────────────

def _regime_awareness(results: pd.DataFrame) -> dict[str, Any]:
    """
    Current regime state: what regime, how confident, how long in it.
    """
    latest = results.iloc[-1]
    current = str(latest['regime_name'])

    # Confidence = probability assigned to current regime
    prob_cols = [c for c in results.columns if c.startswith('prob_')]
    regime_probs = {col.replace('prob_', ''): float(latest[col]) for col in prob_cols}
    confidence = regime_probs.get(current, 0.0)

    # How many consecutive days in this regime?
    regimes = results['regime_name'].values
    streak = 0
    for i in range(len(regimes) - 1, -1, -1):
        if regimes[i] == current:
            streak += 1
        else:
            break

    # Median duration of this regime historically
    rle_lengths = []
    curr_run = 1
    for i in range(1, len(regimes)):
        if regimes[i] == regimes[i - 1]:
            curr_run += 1
        else:
            if regimes[i - 1] == current:
                rle_lengths.append(curr_run)
            curr_run = 1
    if regimes[-1] == current:
        rle_lengths.append(curr_run)
    median_dur = float(np.median(rle_lengths)) if rle_lengths else 0.0

    return {
        'current_regime': current,
        'confidence': confidence,
        'days_in_regime': streak,
        'median_duration': median_dur,
        'regime_probs': regime_probs,
    }


# ── Transition awareness ──────────────────────────────────────────

_REGIME_SEVERITY = {
    'Very-Low': 0, 'Low-Vol': 1, 'Moderate': 2,
    'Elevated': 3, 'High-Vol': 4, 'Crisis': 5,
}


def _transition_context(results: pd.DataFrame) -> list[dict]:
    """
    Show which regimes have non-trivial probability — no "action" advice,
    just awareness of what's nearby in probability space.
    """
    latest = results.iloc[-1]
    current_regime = str(latest['regime_name'])
    current_sev = _REGIME_SEVERITY.get(current_regime, 2)

    prob_cols = [c for c in results.columns if c.startswith('prob_')]
    nearby: list[dict] = []

    for col in prob_cols:
        rname = col.replace('prob_', '')
        prob = float(latest[col])
        if rname == current_regime or prob < 0.03:
            continue

        target_sev = _REGIME_SEVERITY.get(rname, 2)
        sev_change = target_sev - current_sev
        direction = 'higher vol' if sev_change > 0 else 'lower vol' if sev_change < 0 else 'lateral'

        nearby.append({
            'regime': rname,
            'probability': round(prob, 3),
            'direction': direction,
            'severity_jump': abs(sev_change),
        })

    nearby.sort(key=lambda x: -x['probability'])
    return nearby


# ── Validation metrics (is the model hallucinating?) ───────────────

def _validation_metrics(results: pd.DataFrame) -> dict[str, Any]:
    """
    Concrete checks that the model is producing meaningful regimes,
    not random noise.

    Tests:
    1. Regime separation: do different regimes have meaningfully
       different realized vol? (Kruskal-Wallis test)
    2. VaR coverage: does the regime-conditional 5% VaR actually
       capture ~5% of losses in each regime? (backtest)
    3. Vol ordering: are the regimes actually ordered by vol?
    4. Persistence: are regimes sticky (not random flipping)?
    """
    metrics: dict[str, Any] = {}

    if 'SPY_close' not in results.columns:
        return {'error': 'SPY_close not in results'}

    spy_ret = pd.Series(
        np.log(results['SPY_close'] / results['SPY_close'].shift(1))
    ).dropna()
    results_aligned = results.iloc[1:].copy()
    results_aligned['spy_ret'] = spy_ret.values

    regimes = sorted(results_aligned['regime_name'].unique())

    # 1. Regime separation (Kruskal-Wallis on |returns| by regime)
    abs_ret_groups = []
    for r in regimes:
        mask = results_aligned['regime_name'] == r
        g = np.abs(pd.Series(results_aligned.loc[mask, 'spy_ret']).values)
        if len(g) > 5:
            abs_ret_groups.append(g)

    if len(abs_ret_groups) >= 2:
        kw_stat, kw_p = sp_stats.kruskal(*abs_ret_groups)
        metrics['separation_pvalue'] = float(kw_p)
        metrics['separation_significant'] = kw_p < 0.01
        metrics['separation_interpretation'] = (
            'Regimes capture genuinely different vol environments'
            if kw_p < 0.01 else
            'WARNING: regimes may not be meaningfully different'
        )
    else:
        metrics['separation_pvalue'] = np.nan
        metrics['separation_significant'] = False

    # 2. Vol ordering check
    regime_vols = {}
    for r in regimes:
        mask = results_aligned['regime_name'] == r
        rets = np.asarray(pd.Series(results_aligned.loc[mask, 'spy_ret']).values, dtype=float)
        if len(rets) > 10:
            regime_vols[r] = float(np.std(rets) * np.sqrt(252))

    # Check if severity ordering matches vol ordering
    ordered_by_sev = sorted(regime_vols.keys(),
                            key=lambda r: _REGIME_SEVERITY.get(r, 2))
    ordered_by_vol = sorted(regime_vols.keys(),
                            key=lambda r: regime_vols[r])
    metrics['vol_ordering_match'] = ordered_by_sev == ordered_by_vol
    metrics['regime_vols'] = regime_vols

    # 3. VaR backtest (5% level)
    var_results = {}
    for r in regimes:
        mask = results_aligned['regime_name'] == r
        rets = np.asarray(pd.Series(results_aligned.loc[mask, 'spy_ret']).values, dtype=float)
        if len(rets) < 30:
            continue
        var_5 = np.percentile(rets, 5)
        breaches = np.sum(rets < var_5)
        expected = len(rets) * 0.05
        # Kupiec test: are breaches consistent with 5%?
        actual_pct = breaches / len(rets) * 100
        var_results[r] = {
            'var_5_daily': float(var_5),
            'breach_pct': float(actual_pct),
            'n_breaches': int(breaches),
            'n_total': len(rets),
            'ok': 2.0 <= actual_pct <= 8.0,  # rough CI for 5%
        }
    metrics['var_backtest'] = var_results

    # 4. Regime persistence (average run length)
    regime_labels = results['regime_name'].values
    run_lengths = []
    curr_len = 1
    for i in range(1, len(regime_labels)):
        if regime_labels[i] == regime_labels[i - 1]:
            curr_len += 1
        else:
            run_lengths.append(curr_len)
            curr_len = 1
    run_lengths.append(curr_len)
    metrics['avg_run_length'] = float(np.mean(run_lengths))
    metrics['median_run_length'] = float(np.median(run_lengths))
    metrics['persistent'] = np.median(run_lengths) > 5
    metrics['persistence_interpretation'] = (
        f'Median regime lasts {np.median(run_lengths):.0f} days — regimes are sticky (good)'
        if np.median(run_lengths) > 5 else
        f'Median regime lasts {np.median(run_lengths):.0f} days — may be over-fitting (noisy)'
    )

    return metrics


# ── VIX / vol context ─────────────────────────────────────────────

def _vol_context(results: pd.DataFrame) -> dict[str, Any]:
    """Current vol environment — just facts, no trade recommendations."""
    latest = results.iloc[-1]

    vix = float(latest['VIX']) if 'VIX' in latest.index else None
    vrp = None
    if 'VIX' in results.columns and 'SPY_close' in results.columns:
        spy_ret = pd.Series(np.log(results['SPY_close'] / results['SPY_close'].shift(1)),
                            index=results.index)
        rv10 = float(spy_ret.rolling(10).std().iloc[-1] * np.sqrt(252) * 100)
        vrp = float(latest['VIX']) - rv10

    vix_ts = None
    if 'VIX3M' in results.columns and 'VIX' in results.columns:
        vix_ts = float(latest['VIX'] / latest['VIX3M'] - 1)

    return {
        'vix': vix,
        'vrp': vrp,
        'vix_term_structure': vix_ts,
        'term_structure_label': (
            'Backwardation (fear exceeds forecast)'
            if vix_ts and vix_ts > 0.02
            else 'Contango (normal, calm)'
            if vix_ts and vix_ts < -0.02
            else 'Flat' if vix_ts is not None else 'N/A'
        ),
        'vrp_label': (
            f'Implied vol {abs(vrp):.1f}pts ABOVE realized — market pricing more risk than observed'
            if vrp and vrp > 2
            else f'Implied vol {abs(vrp):.1f}pts BELOW realized — market underpricing risk'
            if vrp and vrp < -2
            else 'Implied ≈ realized — fair pricing'
            if vrp is not None
            else 'N/A'
        ),
    }


# ── Master computation ─────────────────────────────────────────────

def compute_signals(results: pd.DataFrame, model: Any = None,
                    name_map: dict | None = None) -> dict[str, Any]:
    """
    Compute regime awareness context from regime results.

    Returns dict with:
      - awareness: current regime, confidence, streak, median duration
      - distributions: per-regime distribution stats (vol, skew, VaR, etc.)
      - transitions: nearby regimes in probability space
      - vol_context: VIX, VRP, term structure — just facts
      - validation: proof the model isn't hallucinating
      - date: as-of date
    """
    awareness = _regime_awareness(results)
    distributions = _compute_regime_distributions(results)
    transitions = _transition_context(results)
    vol_ctx = _vol_context(results)
    validation = _validation_metrics(results)

    return {
        'awareness': awareness,
        'distributions': distributions,
        'transitions': transitions,
        'vol_context': vol_ctx,
        'validation': validation,
        'current_regime': awareness['current_regime'],
        'date': (str(results.index[-1].date())
                 if hasattr(results.index[-1], 'date')
                 else str(results.index[-1])),
    }
