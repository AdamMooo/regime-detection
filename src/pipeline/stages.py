"""Pipeline stage functions — stateless disk-to-disk transformations.

Stage order:
1. collect       -> data/processed/spx_data.csv (SPY return, VIX, yield slope, NFCI)
2. features      -> data/processed/features.csv (expanding-standardized, train/test split)
3. train_hmm     -> data/regime_results.csv, models/hdp_checkpoint.pkl
4. signals       -> data/regime_results.csv (enriched with days_in_regime, regime_entropy)
5. walk_forward  -> data/oos_regime_labels.csv  (gated by --validate flag)
"""

import logging
import os

import numpy as np
import pandas as pd

from src.config import DATA_DIR, MODEL_DIR, FEATURES, TRAIN_END

logger = logging.getLogger('pipeline.stages')


# ===================================================================
# Stage 1: collect
# ===================================================================

def stage_collect(config):
    """Fetch SPY return, VIX, yield slope, NFCI. Writes data/processed/."""
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'collect':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for collect")
    from src.data.collect_macro import fetch_and_save_data
    fetch_and_save_data()


# ===================================================================
# Stage 2: features
# ===================================================================

def stage_features(config):
    """Load raw data, apply expanding-window standardization, save features.csv."""
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'features':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for features")

    raw_path = os.path.join(DATA_DIR, 'processed', 'spx_data.csv')
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Run 'collect' first: {raw_path} not found")

    df = pd.read_csv(raw_path, index_col=0, parse_dates=True)
    cols = [c for c in FEATURES if c in df.columns]
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features in raw data: {missing}")

    from src.core.inference import expanding_standardize
    X_raw = df[cols].values
    X_scaled, _, _ = expanding_standardize(X_raw)

    out = pd.DataFrame(X_scaled, index=df.index, columns=cols)

    # Drop warmup rows (NaN from expanding_standardize)
    out = out.dropna()

    os.makedirs(os.path.join(DATA_DIR, 'processed'), exist_ok=True)
    feat_path  = os.path.join(DATA_DIR, 'processed', 'features.csv')
    train_path = os.path.join(DATA_DIR, 'processed', 'features_train.csv')
    test_path  = os.path.join(DATA_DIR, 'processed', 'features_test.csv')

    out.to_csv(feat_path)
    out.loc[:TRAIN_END].to_csv(train_path)
    out.loc[TRAIN_END:].to_csv(test_path)

    logger.info("features: wrote %d rows (%d train, %d test)",
                len(out),
                (out.index <= TRAIN_END).sum(),
                (out.index > TRAIN_END).sum())


# ===================================================================
# Stage 3: train_hmm
# ===================================================================

def stage_train_hmm(config, prev=None):
    """Fit HDP-HMM on training features. Writes models/ and data/regime_results.csv."""
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'train_hmm':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for train_hmm")

    feat_path = os.path.join(DATA_DIR, 'processed', 'features_train.csv')
    if not os.path.exists(feat_path):
        raise FileNotFoundError(f"Run 'features' first: {feat_path} not found")

    df_train = pd.read_csv(feat_path, index_col=0, parse_dates=True).dropna()
    obs = df_train.values

    from src.core.hdp_hmm import (
        fit_hdp_hmm, posterior_mean_params, get_labels_and_probs,
        label_regimes_hdp, effective_K, save_hdp_results, mcmc_diagnostics,
    )
    from src.config import RANDOM_SEED, HDP_TRUNCATION, HDP_INFERENCE

    result, samples = fit_hdp_hmm(obs)
    params = posterior_mean_params(samples)
    labels, filt_probs, smooth_probs, active = get_labels_and_probs(obs, params)

    raw_path = os.path.join(DATA_DIR, 'processed', 'spx_data.csv')
    spy_ret = pd.read_csv(raw_path, index_col=0, parse_dates=True)['spy_ret']
    spy_aligned = spy_ret.reindex(df_train.index).values

    name_map, state_vols = label_regimes_hdp(labels, active, spy_aligned)
    eff_k = effective_K(samples)

    diag = mcmc_diagnostics(result, samples)

    os.makedirs(MODEL_DIR, exist_ok=True)
    save_hdp_results(
        MODEL_DIR, result, samples, params, diag, eff_k,
        data_info={'train_end': TRAIN_END, 'n_obs': len(obs)}
    )

    # Write regime_results.csv
    results_df = pd.DataFrame({
        'regime_label': [name_map[l] for l in labels],
        'regime_idx':   labels,
        'filt_prob_max': filt_probs.max(axis=1),
    }, index=df_train.index)

    for k, name in name_map.items():
        col = f'filt_prob_{name.replace("-", "_").lower()}'
        if k < filt_probs.shape[1]:
            results_df[col] = filt_probs[:, k]

    out_path = os.path.join(DATA_DIR, 'regime_results.csv')
    results_df.to_csv(out_path)
    logger.info("train_hmm: wrote %s (%d rows)", out_path, len(results_df))

    return {'results_df': results_df, 'name_map': name_map}


# ===================================================================
# Stage 4: signals
# ===================================================================

def stage_signals(config, prev=None):
    """Compute days_in_regime and regime_entropy. Enriches regime_results.csv."""
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'signals':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for signals")

    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if not os.path.exists(results_path):
        logger.warning("signals: no regime_results.csv found, skipping")
        return None

    df = pd.read_csv(results_path, index_col=0, parse_dates=True)

    # Days in current regime streak
    regime_series = df['regime_idx']
    streak = np.ones(len(df), dtype=int)
    for t in range(1, len(df)):
        if regime_series.iloc[t] == regime_series.iloc[t - 1]:
            streak[t] = streak[t - 1] + 1
    df['days_in_regime'] = streak

    # Regime entropy from filtered probs
    prob_cols = [c for c in df.columns if c.startswith('filt_prob_') and c != 'filt_prob_max']
    if prob_cols:
        probs = df[prob_cols].values.clip(1e-10, 1.0)
        df['regime_entropy'] = -(probs * np.log(probs)).sum(axis=1)

    df.to_csv(results_path)
    logger.info("signals: enriched regime_results.csv")


# ===================================================================
# Stage 5: walk_forward
# ===================================================================

def stage_walk_forward(config):
    """Walk-forward OOS validation. Gated by --validate flag.

    Refits the HDP-HMM periodically across several training-window lengths
    (config.WALK_FORWARD_WINDOW_DAYS) and forward-filters each new block,
    producing regime labels the model never saw in-sample. The per-window
    runs are then combined into a majority-vote label + cross-window
    agreement fraction (see src/core/walk_forward.py ensemble_oos) -- a
    single window's own posterior confidence understates how much regime
    assignment depends on an arbitrary training-window-length choice
    (see NOTES.md "Training-Window Sensitivity"). Writes
    data/oos_regime_labels.csv. Takes ~8 min per window config.
    """
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'walk_forward':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for walk_forward")

    feat_path = os.path.join(DATA_DIR, 'processed', 'features.csv')
    raw_path = os.path.join(DATA_DIR, 'processed', 'spx_data.csv')
    if not os.path.exists(feat_path) or not os.path.exists(raw_path):
        raise FileNotFoundError("Run 'collect' and 'features' first")

    feat_full = pd.read_csv(feat_path, index_col=0, parse_dates=True).dropna()
    raw_df = pd.read_csv(raw_path, index_col=0, parse_dates=True)

    from src.config import WALK_FORWARD_WINDOW_DAYS
    from src.core.walk_forward import ensemble_oos, walk_forward_oos

    run_results = {}
    for window_days in WALK_FORWARD_WINDOW_DAYS:
        name = 'expanding' if window_days is None else f'rolling_{window_days}d'
        logger.info("walk_forward: running config %s (window_days=%s)", name, window_days)
        run_results[name] = walk_forward_oos(feat_full, raw_df['vol_index'], window_days=window_days)

    oos_df = ensemble_oos(run_results)

    out_path = os.path.join(DATA_DIR, 'oos_regime_labels.csv')
    oos_df.to_csv(out_path)
    logger.info("walk_forward: wrote %s (%d OOS rows, ensemble of %d configs)",
                out_path, len(oos_df), len(run_results))
    return {'oos_df': oos_df, 'run_results': run_results}


# ===================================================================
# STAGES registry — order is LOCKED
# ===================================================================

STAGES = [
    ('collect',      stage_collect),
    ('features',     stage_features),
    ('train_hmm',    stage_train_hmm),
    ('signals',      stage_signals),
    ('walk_forward', stage_walk_forward),
]
