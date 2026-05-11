"""Train HDP-HMM regime detection model.

Pipeline:
  1. Load features (4 features: VIX, yield_curve_slope, NFCI, VRP)
  2. Lag 1 day (causality — no lookahead)
  3. Expanding-window standardize
  4. Fit HDP-HMM (Gaussian emissions, auto-K via stick-breaking prior)
  5. Label regimes by realized volatility brackets
  6. Write data/regime_results.csv + models/ checkpoint
"""

import logging
import os
import warnings

import joblib
import numpy as np
import pandas as pd

from src.config import (
    RANDOM_SEED, FEATURE_SUBSET, REGIME_HOLD_DAYS,
    HDP_INFERENCE, HDP_MAX_REGIMES, HDP_TRUNCATION,
    DATA_DIR, MODEL_DIR, MAX_DATA_STALENESS_DAYS,
    LABEL_MAPPING, VOL_BRACKETS,
)
from src.core.inference import expanding_standardize
from src.core.hdp_hmm import (
    fit_hdp_hmm, effective_K, posterior_mean_params,
    get_labels_and_probs, label_regimes_hdp,
    mcmc_diagnostics, save_hdp_results,
    HDPModelAdapter, hdp_stability_check,
)

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
logger = logging.getLogger(__name__)


def train():
    np.random.seed(RANDOM_SEED)
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # ── 1. Load data ──────────────────────────────────────────────────
    market = pd.read_csv(
        os.path.join(DATA_DIR, 'market_data.csv'),
        index_col=0, parse_dates=True,
    )
    feat_raw = pd.read_csv(
        os.path.join(DATA_DIR, 'features_transformed.csv'),
        index_col=0, parse_dates=True,
    )

    # Data freshness warning
    trading_days_stale = int(np.busday_count(
        market.index[-1].date(), pd.Timestamp.now().normalize().date()
    ))
    if trading_days_stale > MAX_DATA_STALENESS_DAYS:
        warnings.warn(
            f"market_data.csv is {trading_days_stale} trading days old. "
            f"Run 'python run.py collect' to refresh.",
            UserWarning, stacklevel=2,
        )

    # ── 2. Select & lag features (1-day lag = causality) ─────────────
    available = [f for f in FEATURE_SUBSET if f in feat_raw.columns]
    missing = [f for f in FEATURE_SUBSET if f not in feat_raw.columns]
    if missing:
        warnings.warn(f"Features not found in data: {missing}", UserWarning)
    if not available:
        raise ValueError(f"None of FEATURE_SUBSET found in features_transformed.csv")

    features = feat_raw[available].shift(1).dropna()
    print(f"\nFeatures: {available}  ({len(features)} days after 1-day lag)")

    # ── 3. Expanding-window standardize (causal) ──────────────────────
    X_scaled, _, _ = expanding_standardize(features.values, min_warmup=252)
    valid_mask = ~np.isnan(X_scaled[:, 0])
    X = X_scaled[valid_mask]
    dates = features.index[valid_mask]
    print(f"After warm-up: {len(dates)} valid days  ({dates[0].date()} → {dates[-1].date()})")

    # SPY daily log-returns (for regime vol labeling — not fed into HMM)
    spy_close = market['SPY_close'].reindex(dates)
    spy_ret = np.log(spy_close / spy_close.shift(1)).fillna(0).values

    # ── 4. Fit HDP-HMM ────────────────────────────────────────────────
    print(f"\nFitting HDP-HMM ({HDP_INFERENCE.upper()}, K_max={HDP_TRUNCATION})...")
    result, samples = fit_hdp_hmm(X, K_max=HDP_TRUNCATION, inference=HDP_INFERENCE, seed=RANDOM_SEED)

    diagnostics = mcmc_diagnostics(result, samples)
    k_mean, k_std, k_mode = effective_K(samples)
    print(f"Effective K: {k_mean:.1f} ± {k_std:.1f}  (mode={k_mode})")

    params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
    labels, filt_probs, smooth_probs, active_states = get_labels_and_probs(
        X, params, hold_days=REGIME_HOLD_DAYS,
    )

    # ── 5. Label regimes by realized vol ─────────────────────────────
    name_map, state_vols = label_regimes_hdp(labels, active_states, spy_ret)
    print(f"Regimes: {list(name_map.values())}")
    print(f"Realized vols: { {name_map[k]: f'{v:.1f}%' for k, v in state_vols.items()} }")

    # Posterior stability
    stability = hdp_stability_check(samples, X, n_draws=10)
    print(f"Posterior stability: {stability['mean_agreement']:.1%} label agreement "
          f"across {stability['n_draws']} draws")

    # ── 6. Build results DataFrame ───────────────────────────────────
    regime_names = [name_map[l] for l in labels]
    bot_labels = [LABEL_MAPPING.get(n, 'UNKNOWN') for n in regime_names]

    prob_cols = {f'prob_{name_map[i]}': filt_probs[:, i]
                 for i in range(filt_probs.shape[1])}

    results_df = pd.DataFrame({
        'regime': labels,
        'regime_name': regime_names,
        'bot_label': bot_labels,
        **prob_cols,
        'SPY_close': market['SPY_close'].reindex(dates).values,
        'VIX': market['VIX'].reindex(dates).values,
    }, index=dates)

    out_path = os.path.join(DATA_DIR, 'regime_results.csv')
    results_df.to_csv(out_path)
    print(f"\nWrote {out_path}  ({len(results_df)} rows)")

    # Regime distribution summary
    counts = results_df['regime_name'].value_counts()
    total = len(results_df)
    for name, count in counts.items():
        print(f"  {name}: {count} days ({count/total:.1%})")

    # ── 7. Save model checkpoint ──────────────────────────────────────
    checkpoint = {
        'params': params,
        'samples': {k: v for k, v in samples.items() if v.nbytes < 50_000_000},
        'active_states': active_states,
        'name_map': name_map,
        'state_vols': state_vols,
        'feature_names': available,
        'diagnostics': diagnostics,
        'date_start': str(dates[0].date()),
        'date_end': str(dates[-1].date()),
    }
    ckpt_path = os.path.join(MODEL_DIR, 'hdp_checkpoint.pkl')
    joblib.dump(checkpoint, ckpt_path)
    print(f"Wrote {ckpt_path}")

    return results_df, name_map


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    logging.basicConfig(level=logging.INFO)
    train()
