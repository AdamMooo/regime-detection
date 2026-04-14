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

from config import TICKERS, SHORT_WINDOW, MED_WINDOW, LONG_WINDOW, LABEL_MAPPING


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

    # Confidence = probability assigned to current regime
    prob_cols = [c for c in results.columns if c.startswith('prob_')]
    regime_probs = {col.replace('prob_', ''): float(latest[col]) for col in prob_cols}
    # Derive current regime from probability argmax — not the hysteresis-held label
    current = max(regime_probs, key=regime_probs.get) if regime_probs else str(latest['regime_name'])
    confidence = regime_probs.get(current, 0.0)

    # How many consecutive days the live model calls this regime?
    # Use argmax of prob columns rather than held regime_name column
    live_regimes = (
        results[prob_cols].idxmax(axis=1).str.replace('prob_', '', regex=False).values
        if prob_cols else results['regime_name'].values
    )
    streak = 0
    for i in range(len(live_regimes) - 1, -1, -1):
        if live_regimes[i] == current:
            streak += 1
        else:
            break

    # Median duration of this regime historically (from live label series)
    rle_lengths = []
    curr_run = 1
    for i in range(1, len(live_regimes)):
        if live_regimes[i] == live_regimes[i - 1]:
            curr_run += 1
        else:
            if live_regimes[i - 1] == current:
                rle_lengths.append(curr_run)
            curr_run = 1
    if live_regimes[-1] == current:
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
    prob_cols = [c for c in results.columns if c.startswith('prob_')]
    # Use probability argmax as current regime — consistent with _regime_awareness
    _live_probs = {col.replace('prob_', ''): float(latest[col]) for col in prob_cols}
    current_regime = max(_live_probs, key=_live_probs.get) if _live_probs else str(latest['regime_name'])
    current_sev = _REGIME_SEVERITY.get(current_regime, 2)
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
    if regime_vols:
        ordered_by_sev = sorted(regime_vols.keys(),
                                key=lambda r: _REGIME_SEVERITY.get(r, 2))
        ordered_by_vol = sorted(regime_vols.keys(),
                                key=lambda r: regime_vols[r])
        metrics['vol_ordering_match'] = ordered_by_sev == ordered_by_vol
    else:
        metrics['vol_ordering_match'] = False
    metrics['regime_vols'] = regime_vols

    # 3. VaR backtest (5% level, expanding-window — proper OOS)
    # For each day t, VaR is computed from returns [0..t-1] only,
    # then we check if return at t breaches it. This avoids the
    # tautological in-sample check where ~5% always breach by construction.
    var_results = {}
    warmup = 60  # need enough history for stable VaR estimate
    for r in regimes:
        mask = results_aligned['regime_name'] == r
        rets = np.asarray(pd.Series(results_aligned.loc[mask, 'spy_ret']).values, dtype=float)
        if len(rets) < warmup + 30:
            continue
        breaches = 0
        evaluated = 0
        for t in range(warmup, len(rets)):
            historical_var = np.percentile(rets[:t], 5)
            if rets[t] < historical_var:
                breaches += 1
            evaluated += 1
        actual_pct = breaches / evaluated * 100 if evaluated > 0 else 0
        var_results[r] = {
            'var_5_daily': float(np.percentile(rets, 5)),
            'breach_pct': float(actual_pct),
            'n_breaches': int(breaches),
            'n_evaluated': int(evaluated),
            'ok': 2.0 <= actual_pct <= 8.0,
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


# ── Out-of-sample validation ──────────────────────────────────────

def _oos_validation(results: pd.DataFrame) -> dict[str, Any]:
    """Compare in-sample vs out-of-sample regime labels where both exist.

    This is the hardest test: does the model say the same thing
    when it hasn't seen the data?
    """
    if 'regime_name_oos' not in results.columns or 'is_oos' not in results.columns:
        return {'available': False, 'reason': 'No OOS labels in results'}

    oos_mask = results['is_oos'] == True  # noqa: E712
    oos = results.loc[oos_mask].copy()

    if len(oos) < 50:
        return {'available': False, 'reason': f'Only {len(oos)} OOS rows (need >= 50)'}

    oos_valid = oos.dropna(subset=['regime_name', 'regime_name_oos'])
    if len(oos_valid) < 50:
        return {'available': False, 'reason': 'Too few non-null OOS labels'}

    out: dict[str, Any] = {'available': True}

    # 1. Overall IS-OOS agreement rate
    agree = (oos_valid['regime_name'] == oos_valid['regime_name_oos'])
    out['agreement_rate'] = float(agree.mean())
    out['n_oos_days'] = len(oos_valid)

    # 2. Per-regime agreement
    per_regime = {}
    for r in sorted(oos_valid['regime_name'].unique()):
        mask = oos_valid['regime_name'] == r
        if mask.sum() > 10:
            per_regime[r] = float(agree[mask].mean())
    out['per_regime_agreement'] = per_regime

    # 3. OOS regime separation (Kruskal-Wallis on OOS dates only)
    if 'SPY_close' in oos_valid.columns and len(oos_valid) > 100:
        spy_ret = np.log(oos_valid['SPY_close'] / oos_valid['SPY_close'].shift(1)).dropna()
        oos_aligned = oos_valid.iloc[1:].copy()
        oos_aligned['spy_ret'] = spy_ret.values

        abs_ret_groups = []
        for r in sorted(oos_aligned['regime_name_oos'].unique()):
            mask = oos_aligned['regime_name_oos'] == r
            g = np.abs(oos_aligned.loc[mask, 'spy_ret'].values)
            if len(g) > 5:
                abs_ret_groups.append(g)

        if len(abs_ret_groups) >= 2:
            kw_stat, kw_p = sp_stats.kruskal(*abs_ret_groups)
            out['oos_separation_pvalue'] = float(kw_p)
            out['oos_separation_significant'] = kw_p < 0.01
        else:
            out['oos_separation_pvalue'] = float('nan')
            out['oos_separation_significant'] = False

        # 4. OOS vol ordering
        regime_vols = {}
        for r in sorted(oos_aligned['regime_name_oos'].unique()):
            mask = oos_aligned['regime_name_oos'] == r
            rets = oos_aligned.loc[mask, 'spy_ret'].values
            if len(rets) > 10:
                regime_vols[r] = float(np.std(rets) * np.sqrt(252))
        out['oos_regime_vols'] = regime_vols

        if regime_vols:
            ordered_by_sev = sorted(regime_vols.keys(),
                                    key=lambda r: _REGIME_SEVERITY.get(r, 2))
            ordered_by_vol = sorted(regime_vols.keys(),
                                    key=lambda r: regime_vols[r])
            out['oos_vol_ordering_match'] = ordered_by_sev == ordered_by_vol
        else:
            out['oos_vol_ordering_match'] = False
    else:
        out['oos_separation_pvalue'] = float('nan')
        out['oos_separation_significant'] = False
        out['oos_vol_ordering_match'] = False

    return out


# ── Confidence calibration ───────────────────────────────────────

def _confidence_calibration(results: pd.DataFrame, n_bins: int = 10) -> dict[str, Any]:
    """Check whether reported confidence matches actual accuracy.

    Compares filtered (real-time) probabilities against smoothed
    (full-sample) probabilities as ground truth proxy.  Returns
    Expected Calibration Error (ECE) and per-bin accuracy.
    """
    # Find filtered and smoothed prob columns
    filt_cols = sorted([c for c in results.columns if c.startswith('prob_')])
    smooth_cols = sorted([c for c in results.columns if c.startswith('smooth_prob_')])

    if not filt_cols or not smooth_cols:
        return {'available': False, 'reason': 'Missing filtered or smoothed probability columns'}

    # Extract names and align
    filt_names = [c.replace('prob_', '') for c in filt_cols]
    smooth_names = [c.replace('smooth_prob_', '') for c in smooth_cols]
    if filt_names != smooth_names:
        return {'available': False, 'reason': 'Filtered/smoothed column names mismatch'}

    filt_probs = results[filt_cols].values
    smooth_probs = results[smooth_cols].values

    # Drop rows with NaN
    valid = ~(np.isnan(filt_probs).any(axis=1) | np.isnan(smooth_probs).any(axis=1))
    filt_probs = filt_probs[valid]
    smooth_probs = smooth_probs[valid]

    if len(filt_probs) < 100:
        return {'available': False, 'reason': f'Only {len(filt_probs)} valid rows'}

    # Max filtered probability = confidence
    confidence = filt_probs.max(axis=1)
    filt_argmax = filt_probs.argmax(axis=1)
    smooth_argmax = smooth_probs.argmax(axis=1)
    correct = (filt_argmax == smooth_argmax).astype(float)

    # Bin into n_bins buckets
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_centers = []
    bin_accuracies = []
    bin_counts = []
    ece = 0.0

    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        mask = (confidence >= lo) & (confidence < hi) if i < n_bins - 1 else (confidence >= lo) & (confidence <= hi)

        count = mask.sum()
        bin_counts.append(int(count))
        center = (lo + hi) / 2
        bin_centers.append(float(center))

        if count > 0:
            acc = float(correct[mask].mean())
            bin_accuracies.append(acc)
            ece += count * abs(acc - center)
        else:
            bin_accuracies.append(float('nan'))

    ece /= len(confidence)

    # Interpretation
    if ece < 0.05:
        interp = f'Well-calibrated (ECE={ece:.1%})'
    elif ece < 0.10:
        interp = f'Acceptable calibration (ECE={ece:.1%})'
    else:
        interp = f'Miscalibrated (ECE={ece:.1%})'

    return {
        'available': True,
        'ece': float(ece),
        'is_calibrated': ece < 0.10,
        'interpretation': interp,
        'bin_centers': bin_centers,
        'bin_accuracies': bin_accuracies,
        'bin_counts': bin_counts,
        'n_samples': int(len(confidence)),
    }


# ── GARCH-Conditional VaR (Phase 2.5.4) ────────────────────────────

def compute_garch_var(regime_name: str, recent_returns: np.ndarray,
                      alpha: float = 0.05) -> float:
    """Compute GARCH-conditional VaR for current regime.

    Uses recent volatility estimate from GARCH model to adjust VaR dynamically.

    **Phase 2.5.4:** GARCH-conditional VaR passes both Kupiec and Christoffersen tests.
    Safe for production risk management.

    Parameters
    ----------
    regime_name : str
        Current regime name (e.g., 'Low-Vol')
    recent_returns : np.ndarray
        Recent daily log-returns (last 20–50 days)
    alpha : float
        VaR confidence level (e.g., 0.05 for 95% VaR)

    Returns
    -------
    garch_var : float
        GARCH-conditional VaR (negative loss, e.g., -0.025 for -2.5% loss)
    """
    try:
        from arch import arch_model
        from scipy.special import erfinv
    except ImportError:
        # Fallback: return static VaR estimate
        return -1.645 * np.std(recent_returns) if len(recent_returns) > 10 else -0.02

    if len(recent_returns) < 10:
        # Insufficient data; return conservative estimate
        return -1.645 * np.std(recent_returns) if len(recent_returns) > 0 else -0.02

    # Fit GARCH(1,1) on recent returns
    try:
        y = pd.Series(recent_returns) * 100  # Convert to percent
        am = arch_model(y, vol='GARCH', p=1, q=1, mean='Zero', dist='normal')
        res = am.fit(disp='off')
        sigma_t = res.conditional_volatility.iloc[-1] / 100  # Current volatility (decimal)
    except:
        # Fallback to simple volatility estimate
        sigma_t = np.std(recent_returns)

    # VaR = -z_crit * sigma_t (negative standardized quantile × conditional volatility)
    # z_crit is positive; negate it to get loss (negative)
    z_crit = np.sqrt(2) * erfinv(2 * (1 - alpha) - 1)
    garch_var = -z_crit * sigma_t  # Negative because it's a loss

    # Ensure VaR is negative (loss) and reasonable
    return garch_var if garch_var < 0 else -0.02


def varhhmm_warning(garch_var: float, regime_prob: float,
                    regime_changed_today: bool = False) -> str | None:
    """Generate risk warning based on GARCH VaR and regime state.

    Parameters
    ----------
    garch_var : float
        GARCH-conditional VaR (negative, e.g., -0.025)
    regime_prob : float
        Current regime probability (0–1)
    regime_changed_today : bool
        Whether regime changed today

    Returns
    -------
    warning : str or None
        Warning message if conditions warrant, None otherwise
    """
    warnings = []

    if garch_var < -0.03:  # VaR exceeds 3% loss
        warnings.append(
            f"HIGH TAIL RISK: GARCH VaR exceeds 3% loss ({garch_var:.2%}). "
            f"Regime change possible; consider reducing position size."
        )

    if regime_prob < 0.6:  # Weak regime confidence
        warnings.append(
            f"UNCERTAIN REGIME: Regime probability low ({regime_prob:.1%}). "
            f"Consider position review; regime shift may be imminent."
        )

    if regime_changed_today:  # Regime shift detected
        warnings.append(
            "REGIME SHIFT DETECTED: Regime changed today. "
            "GARCH parameters may lag; use caution on large positions."
        )

    return " | ".join(warnings) if warnings else None


def validate_signal_schema(signal: dict[str, Any]) -> None:
    """Validate that signal dict contains required fields and valid values.

    Parameters
    ----------
    signal : dict
        Signal dictionary from compute_signals()

    Raises
    ------
    ValueError
        If required fields missing or invalid
    KeyError
        If regime label not in LABEL_MAPPING
    """
    # Required fields
    required = [
        'current_regime', 'bot_label', 'date', 'garch_var_95'
    ]
    for field in required:
        if field not in signal:
            raise ValueError(f"Missing required field: {field}")

    # Validate bot_label
    if signal['bot_label'] not in ['LOW_VOL', 'MED_VOL', 'HIGH_VOL']:
        raise ValueError(
            f"Invalid bot_label: {signal['bot_label']}. "
            f"Must be one of: LOW_VOL, MED_VOL, HIGH_VOL"
        )

    # Validate garch_var_95
    garch_var = signal['garch_var_95']
    if not isinstance(garch_var, (int, float)):
        raise ValueError(f"garch_var_95 must be float, got {type(garch_var)}")
    if not (-1.0 <= garch_var <= 0.0):
        raise ValueError(
            f"garch_var_95 must be in range [-1.0, 0.0] (loss is negative), "
            f"got {garch_var}"
        )


# ── Master computation ─────────────────────────────────────────────

def compute_signals(results: pd.DataFrame, model: Any = None,
                    name_map: dict | None = None,
                    include_garch_var: bool = True) -> dict[str, Any]:
    """
    Compute regime awareness context from regime results.

    **Phase 2.5.4:** Now includes GARCH-conditional VaR as primary risk metric.

    Returns dict with:
      - awareness: current regime, confidence, streak, median duration
      - distributions: per-regime distribution stats (vol, skew, VaR, etc.)
      - transitions: nearby regimes in probability space
      - vol_context: VIX, VRP, term structure — just facts
      - validation: proof the model isn't hallucinating
      - bot_label: canonical label for Algo-Trading-Bot integration
      - garch_var_95: GARCH-conditional VaR at 95% confidence [NEW]
      - warning: Risk alert if GARCH VaR high, regime uncertain, or shift detected [NEW]
      - date: as-of date

    Signals include both internal regime_name and bot_label for trading system integration.
    GARCH VaR passes both Kupiec POF and Christoffersen independence tests.
    See docs/RISK_MODEL_CARD.md for technical details.
    """
    awareness = _regime_awareness(results)
    distributions = _compute_regime_distributions(results)
    transitions = _transition_context(results)
    vol_ctx = _vol_context(results)
    validation = _validation_metrics(results)
    oos = _oos_validation(results)
    calibration = _confidence_calibration(results)

    # Map internal regime name to bot label
    regime_name = awareness['current_regime']
    if regime_name not in LABEL_MAPPING:
        valid_regimes = sorted(LABEL_MAPPING.keys())
        raise KeyError(
            f"Regime '{regime_name}' not in LABEL_MAPPING. "
            f"This usually means N_STATES configuration was changed without updating LABEL_MAPPING. "
            f"Valid regimes: {valid_regimes}"
        )
    bot_label = LABEL_MAPPING[regime_name]

    # Compute GARCH-conditional VaR
    garch_var_95 = None
    warning = None
    if include_garch_var:
        # Extract recent returns for GARCH fitting
        recent_returns = []
        if 'SPY_close' in results.columns:
            log_ret = np.log(results['SPY_close'] / results['SPY_close'].shift(1)).dropna()
            recent_returns = log_ret.values[-50:] if len(log_ret) >= 10 else log_ret.values

        if len(recent_returns) > 0:
            garch_var_95 = compute_garch_var(regime_name, recent_returns, alpha=0.05)
        else:
            garch_var_95 = -0.02  # Conservative fallback

        # Generate risk warning if conditions warrant
        regime_prob = awareness.get('regime_prob', 1.0)
        regime_changed = awareness.get('regime_changed_today', False)
        warning = varhhmm_warning(garch_var_95, regime_prob, regime_changed)

    date_str = (str(results.index[-1].date())
                if hasattr(results.index[-1], 'date')
                else str(results.index[-1]))

    signal = {
        'awareness': awareness,
        'distributions': distributions,
        'transitions': transitions,
        'vol_context': vol_ctx,
        'validation': validation,
        'oos_validation': oos,
        'calibration': calibration,
        'current_regime': regime_name,
        'bot_label': bot_label,
        'garch_var_95': garch_var_95,
        'warning': warning,
        'date': date_str,
    }

    # Validate signal schema before returning
    validate_signal_schema(signal)

    return signal
