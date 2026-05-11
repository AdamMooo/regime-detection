"""Pipeline stage functions — stateless disk-to-disk transformations.

Stage order:
1. collect          -> data/market_data.csv, data/macro_data.csv
2. features         -> data/features_transformed.csv
3. feature_analysis -> figures/feature_analysis.html
4. train_hmm        -> data/regime_results.csv, models/hdp_checkpoint.pkl
5. signals          -> data/regime_results.csv (enriched)
6. dashboard        -> figures/dashboard.html
7. walk_forward     -> data/oos_regime_labels.csv  (gated by --validate flag)
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from src.config import DATA_DIR, MODEL_DIR, FIGURE_DIR
from src.core.orchestrator import walk_forward as _orchestrator_walk_forward

logger = logging.getLogger('pipeline.stages')


def stage_collect(config):
    """Collect market and macro data. Writes data/market_data.csv."""
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'collect':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for collect")

    from src.features.collect import collect
    from src.data.collect_macro import collect as collect_macro
    collect()
    collect_macro()
    return None


def stage_features(config):
    """Build and transform features. Writes data/features_transformed.csv."""
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'features':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for features")

    from src.features.features import prepare_features
    prepare_features()
    return None


def stage_feature_analysis(config):
    """Build feature analysis HTML report. Writes figures/feature_analysis.html."""
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'feature_analysis':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for feature_analysis")

    from scripts.pipelines.analyze import analyze
    analyze()
    return None



def stage_train_hmm(config, prev=None):
    """Fit HDP-HMM and produce regime labels. Writes model artifacts to models/.

    Returns a dict with results_df and market_v for downstream stages.
    """
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'train_hmm':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for train_hmm")

    from scripts.pipelines.train import train
    # train() writes regime_results.csv and model artifacts, returns None
    train()
    # Load results from disk for downstream stages
    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if os.path.exists(results_path):
        results_df = pd.read_csv(results_path, index_col=0, parse_dates=True)
        market_path = os.path.join(DATA_DIR, 'market_data.csv')
        market_v = pd.read_csv(market_path, index_col=0, parse_dates=True)
        return {'results_df': results_df, 'market_v': market_v}
    return None



def stage_signals(config, prev=None):
    """Assemble and write data/regime_results.csv.

    NOTE: In the current architecture, train() already writes regime_results.csv.
    This stage enriches it with placeholder columns for PIPE-03 schema compliance
    (days_in_regime, regime_entropy, garch_vol_forecast, blended_vol_forecast,
    transition_score, structural_anomaly). Plan 07-03 wires real data for the
    non-placeholder columns.
    """
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'signals':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for signals")

    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if not os.path.exists(results_path):
        logger.warning("signals: no regime_results.csv found, skipping enrichment")
        return None

    df = pd.read_csv(results_path, index_col=0, parse_dates=True)

    # Add PIPE-03 schema columns as placeholders (all-NaN per Phase 7 contract)
    # Plan 07-03 will wire real data for days_in_regime, regime_entropy,
    # garch_vol_forecast; blended_vol_forecast, transition_score, structural_anomaly
    # remain all-NaN as stubs for future phases.
    changed = False
    placeholder_cols = [
        'days_in_regime', 'regime_entropy', 'garch_vol_forecast',
        'blended_vol_forecast', 'transition_score', 'structural_anomaly',
    ]
    for col in placeholder_cols:
        if col not in df.columns:
            df[col] = np.nan
            changed = True

    if changed:
        df.to_csv(results_path)
        logger.info("signals: enriched regime_results.csv with %d placeholder columns",
                    sum(1 for c in placeholder_cols if c in df.columns))

    return None


def stage_dashboard(config, prev=None):
    """Build interactive dashboard. Writes figures/dashboard.html."""
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'dashboard':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for dashboard")

    from scripts.pipelines.train import rebuild_dashboard
    rebuild_dashboard()
    return None


def stage_walk_forward(config):
    """Run walk-forward OOS validation. Writes data/oos_regime_labels.csv.

    NEVER runs unless the runner passes validate=True (the runner gates this stage).
    Uses the canonical walk_forward from src.core.orchestrator.
    """
    if os.environ.get('GSD_FORCE_STAGE_FAIL') == 'walk_forward':
        raise RuntimeError("GSD_FORCE_STAGE_FAIL triggered for walk_forward")

    from src.config import N_STATES, WALK_FORWARD_MODE
    from src.core.inference import expanding_standardize

    market_path = os.path.join(DATA_DIR, 'market_data.csv')
    feat_path = os.path.join(DATA_DIR, 'features_transformed.csv')

    if not os.path.exists(market_path) or not os.path.exists(feat_path):
        logger.warning("walk_forward: required data files not found, skipping")
        return None

    market = pd.read_csv(market_path, index_col=0, parse_dates=True)
    features = pd.read_csv(feat_path, index_col=0, parse_dates=True)

    # Determine n_pca from existing PCA components if available
    pca_path = os.path.join(DATA_DIR, 'pca_components.csv')
    n_pca = 3  # default
    if os.path.exists(pca_path):
        pca_df = pd.read_csv(pca_path, index_col=0, nrows=1)
        n_pca = len(pca_df.columns)

    oos_labels, oos_name_map = _orchestrator_walk_forward(
        market, features, n_states=N_STATES, n_pca=n_pca, mode=WALK_FORWARD_MODE,
    )

    # Write OOS labels with columns [date, fold_id, regime, regime_name]
    if oos_labels is not None and len(oos_labels) > 0:
        oos_df = pd.DataFrame({
            'date': oos_labels.index,
            'fold_id': 0,  # orchestrator doesn't expose fold_id directly
            'regime': oos_labels.values,
            'regime_name': [oos_name_map.get(int(l), str(l)) for l in oos_labels.values],
        })
        os.makedirs(DATA_DIR, exist_ok=True)
        oos_df.to_csv(os.path.join(DATA_DIR, 'oos_regime_labels.csv'), index=False)
        logger.info("walk_forward: wrote %d OOS labels to oos_regime_labels.csv",
                    len(oos_df))

    return None


# STAGES registry — order is LOCKED
STAGES = [
    ('collect', stage_collect),
    ('features', stage_features),
    ('feature_analysis', stage_feature_analysis),
    ('train_hmm', stage_train_hmm),
    ('signals', stage_signals),
    ('dashboard', stage_dashboard),
    ('walk_forward', stage_walk_forward),
]
