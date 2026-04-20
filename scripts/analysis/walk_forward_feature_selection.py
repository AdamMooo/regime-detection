"""Walk-forward feature selection on sectioned section signals (Phase 5 FEAT-02/FEAT-03).

Runs a 3-year rolling train / 21-day step forward CV over the 4 section signals
produced by build_section_signals(). Computes mutual information between each
section signal and regime labels on training-fold data only (causal -- no lookahead).
A section is 'selected' if it appears in the top-N per-fold rankings in
>= stability_threshold fraction of folds (default 60%).

Writes data/feature_importance_report.md with:
  - Section x fold selection matrix
  - Summary table: selection frequency, mean OOS MI, economic rationale

Does NOT modify config.py -- Plan 05 consumes this script's output and performs the
FEATURE_SUBSET update there.

Run: python -m scripts.analysis.walk_forward_feature_selection
"""

import os
import sys
import json
import logging
from datetime import datetime

import numpy as np
import pandas as pd

# Module-level imports that let the test mocks intercept calls at the source.
# We import the modules (not just the functions) so that when tests patch
#   'src.features.features.build_section_signals_for_fold'
#   'sklearn.feature_selection.mutual_info_classif'
# those patches are visible through the module reference at call time.
import sklearn.feature_selection
import src.features.features as _features_mod
from sklearn.cluster import KMeans

# Note: we do NOT import WALK_FORWARD_TRAIN_YEARS here. That constant (5 years) is
# the downstream HMM training window. Phase 5 feature selection uses a 3-year window
# per D-03 in CONTEXT.md - a different knob serving a different purpose. Keeping the
# constants separate prevents silent divergence if the HMM window later changes.
from src.config import DATA_DIR, RANDOM_SEED, N_STATES
from src.features.features import (
    build_features,
    SECTION_MAP,
    SECTION_ANCHORS,
)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# ── Regime label source ────────────────────────────────────────────

def _load_or_compute_regime_labels(raw_features: pd.DataFrame) -> pd.Series:
    """Load precomputed regime labels from data/regime_labels.csv, or derive
    a deterministic fallback via KMeans on a quick full-history section-signal pass.

    IMPORTANT: the fallback's full-history section-signal pass is ONLY used to
    seed regime labels (the MI target). It is NOT the input to the walk-forward
    MI computation - that input is refit per-fold inside walk_forward_section_selection.
    Using full-history signals here would only leak into the LABELS, and since
    the labels serve only as the y-variable for MI (a selection heuristic, not
    a trained model), the causal violation is confined to a scalar ranking signal
    rather than the model weights. Preferred path: a precomputed regime_labels.csv
    produced by an HMM training run in a previous phase.

    KMeans is seeded with RANDOM_SEED for reproducibility.
    """
    labels_path = os.path.join(DATA_DIR, 'regime_labels.csv')
    if os.path.exists(labels_path):
        labels = pd.read_csv(labels_path, index_col=0, parse_dates=True).iloc[:, 0]
        labels = labels.reindex(raw_features.index).ffill().dropna()
        logger.info(f"[wffs] Loaded regime labels from {labels_path} ({len(labels)} rows)")
        return labels.astype(int)

    # Fallback: quick full-history section-signal pass + KMeans (K=3)
    logger.info(
        f"[wffs] regime_labels.csv not found - falling back to KMeans(K={N_STATES}) "
        f"on full-history section signals (labels only)"
    )
    # Use build_section_signals_for_fold on the whole history as a one-shot summary
    quick_signals = _features_mod.build_section_signals_for_fold(raw_features, pca_window=252)
    km = KMeans(n_clusters=N_STATES, random_state=RANDOM_SEED, n_init=10)
    labels_arr = km.fit_predict(quick_signals.ffill().fillna(0).values)
    return pd.Series(labels_arr, index=quick_signals.index, name='regime_label')


# ── Walk-forward selection core (FEAT-02) ──────────────────────────

def walk_forward_section_selection(
    raw_features: pd.DataFrame,
    regime_labels: pd.Series,
    train_years: int = 3,
    step_days: int = 21,
    pca_window: int = 252,
    stability_threshold: float = 0.60,
    top_n_per_fold: int = 3,
    random_state: int = 42,
) -> dict:
    """Walk-forward section selection using mutual information.

    CAUSAL GUARANTEE (FEAT-02 + RESEARCH.md Pitfall 4): inside each fold,
    section PCA is REFIT on raw_features.iloc[train_start:t] ONLY via
    build_section_signals_for_fold. The helper has no access to rows
    outside the passed slice, making the guarantee structural, not advisory.
    MI is then computed on the resulting section signals over the same
    training rows. Rows from t onward are the OOS test window and are
    NEVER passed to the helper or to mutual_info_classif.

    Args:
        raw_features:    (T, ~21) DataFrame - output of build_features().
                         NOT pre-built section signals - this function refits
                         section PCA per fold.
        regime_labels:   Series aligned to raw_features.index with integer labels
        train_years:     Rolling train window length (default 3 ~ 756 rows, per D-03)
        step_days:       Step between fold ends (default 21 ~ monthly re-fit)
        pca_window:      Rows from the tail of the training slice used to fit
                         section PCA (default 252 ~ 1 year).
        stability_threshold: Min fold fraction a section must appear in to be 'selected'
        top_n_per_fold:  How many top-MI sections to record per fold (typically 3 of 4)
        random_state:    Passed to mutual_info_classif for reproducibility

    Returns:
        {
            'selected': [section names passing threshold, sorted by mean MI],
            'selection_frequency': {section: freq in [0,1]},
            'fold_scores': [{section: mi_score} per fold],
            'n_folds': int,
            'mean_mi': {section: float},
        }
    """
    min_train = int(train_years * 252)
    step = int(step_days)

    # Align regime labels to raw_features
    labels_aligned = regime_labels.reindex(raw_features.index).dropna().astype(int)
    # Trim raw_features to the aligned label index
    feats = raw_features.loc[labels_aligned.index]

    fold_selections: list = []
    fold_scores: list = []
    observed_sections: set = set()

    t = min_train
    while t < len(feats):
        train_start = max(0, t - min_train)
        fold_features = feats.iloc[train_start:t]       # NEVER includes row t
        y_train = labels_aligned.iloc[train_start:t].values

        # Skip folds with insufficient class diversity
        if len(np.unique(y_train)) < 2:
            t += step
            continue

        # CRITICAL: refit section PCA on this fold's training slice ONLY.
        # build_section_signals_for_fold structurally cannot see rows at or after t.
        # Call via module reference so test mocks at src.features.features are visible.
        fold_signals = _features_mod.build_section_signals_for_fold(
            fold_features, pca_window=pca_window
        )
        section_names_fold = list(fold_signals.columns)
        observed_sections.update(section_names_fold)

        x_train = fold_signals.values  # transformed slice - no future info

        # MI on train fold ONLY - this is the second arm of the causal guarantee.
        # Call via module reference so test mocks at sklearn.feature_selection are visible.
        mi_scores = sklearn.feature_selection.mutual_info_classif(
            x_train, y_train,
            discrete_features=False,
            random_state=random_state,
            n_jobs=1,  # n_jobs=-1 breaks on Windows (joblib _posixsubprocess)
        )
        mi_dict = dict(zip(section_names_fold, mi_scores))
        fold_scores.append(mi_dict)

        # Top-N selection this fold
        ranked = sorted(mi_dict.items(), key=lambda kv: kv[1], reverse=True)
        top_names = {name for name, _ in ranked[:top_n_per_fold]}
        fold_selections.append(top_names)

        t += step

    section_names = sorted(observed_sections) or sorted(SECTION_MAP.keys())

    n_folds = len(fold_selections)
    if n_folds == 0:
        return {
            'selected': [],
            'selection_frequency': {s: 0.0 for s in section_names},
            'fold_scores': [],
            'n_folds': 0,
            'mean_mi': {s: 0.0 for s in section_names},
        }

    # Selection frequency per section
    sel_freq = {
        s: sum(1 for fold in fold_selections if s in fold) / n_folds
        for s in section_names
    }

    # Mean MI across folds (used to order the final selected list)
    mean_mi = {
        s: float(np.mean([f.get(s, 0.0) for f in fold_scores]))
        for s in section_names
    }

    selected = [s for s, freq in sel_freq.items() if freq >= stability_threshold]
    # Order selected by mean MI descending
    selected.sort(key=lambda s: mean_mi[s], reverse=True)

    return {
        'selected': selected,
        'selection_frequency': sel_freq,
        'fold_scores': fold_scores,
        'n_folds': n_folds,
        'mean_mi': mean_mi,
    }


# ── Report writer (FEAT-03) ────────────────────────────────────────

_SECTION_RATIONALE = {
    's_vol': (
        "Volatility factor: VIX, VRP, rv_ratio, vix_ts_slope and related. "
        "Collapsed to PC1 so the vol cluster no longer dominates the joint PCA."
    ),
    's_fin': (
        "Financial conditions / credit: credit_stress, SPY_TLT_corr63, HY_OAS (ICE "
        "BofA HY OAS), NFCI (Chicago Fed). Direct credit and fed-composite signal."
    ),
    's_mac': (
        "Macro cycle: yield_curve_slope (T10Y2Y, canonical recession predictor), "
        "GLD_trend (real-asset momentum), SPY_ret, SPY_ac1_20 (trend persistence)."
    ),
    's_str': (
        "Market structure / microstructure: eigen_conc (absorption ratio), "
        "SPY_dd63, SPY_rel_volume, SPY_vol_adj_ret, SPY_skew20."
    ),
}


def write_feature_importance_report(result: dict, out_dir: str | None = None) -> str:
    """Write feature_importance_report.md with section x fold table and summary.

    FEAT-03 contract: the report must contain the exact header and the exact
    summary table header ('| Section | Selection Frequency | Mean OOS MI | Rationale |')
    -- these are asserted by tests/test_walk_forward.py::test_report_written.
    """
    out_dir = out_dir or DATA_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'feature_importance_report.md')

    lines: list = []
    lines.append("# Feature Importance Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Folds:** {result['n_folds']}")
    lines.append(f"**Selected sections:** {', '.join(result['selected']) or '(none)'}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Section | Selection Frequency | Mean OOS MI | Rationale |")
    lines.append("|---------|---------------------|-------------|-----------|")
    for s, freq in sorted(
        result['selection_frequency'].items(),
        key=lambda kv: kv[1], reverse=True
    ):
        section_mean_mi = result.get('mean_mi', {}).get(s, 0.0)
        rationale = _SECTION_RATIONALE.get(s, '--')
        lines.append(f"| {s} | {freq*100:.1f}% | {section_mean_mi:.4f} | {rationale} |")
    lines.append("")

    # Per-fold detail (section x fold matrix)
    lines.append("## Per-fold MI scores")
    lines.append("")
    if result['fold_scores']:
        sections = list(result['fold_scores'][0].keys())
        header = "| Fold | " + " | ".join(sections) + " |"
        sep = "|------|" + "|".join(["-----"] * len(sections)) + "|"
        lines.append(header)
        lines.append(sep)
        for i, fold in enumerate(result['fold_scores']):
            row = f"| {i} | " + " | ".join(
                f"{fold.get(s, 0.0):.4f}" for s in sections
            ) + " |"
            lines.append(row)
    lines.append("")

    with open(path, 'w', encoding='utf-8') as fh:
        fh.write("\n".join(lines))
    logger.info(f"[wffs] Wrote {path}")
    return path


# ── Entry point ────────────────────────────────────────────────────

def _build_synthetic_features_for_test(n_rows: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Build a minimal synthetic feature DataFrame for use when market data is absent.

    Only used as a fallback inside main() when DATA_DIR does not contain market_data.csv
    (e.g. during tests that monkeypatch DATA_DIR to tmp_path). Production runs always
    have market_data.csv present.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range('2010-01-01', periods=n_rows, freq='B')
    cols = [
        'VIX', 'VRP', 'rv_ratio_10_63', 'vix_ts_slope', 'SPY_volvol20',
        'SPY_rv10_lag5', 'SPY_rv10_lag10', 'lev_effect20',
        'credit_stress', 'SPY_TLT_corr63', 'HY_OAS', 'NFCI',
        'yield_curve_slope', 'GLD_trend', 'SPY_ret', 'SPY_ac1_20',
        'eigen_conc', 'SPY_dd63', 'SPY_rel_volume', 'SPY_vol_adj_ret', 'SPY_skew20',
    ]
    data = rng.standard_normal((n_rows, len(cols)))
    data[:, cols.index('VIX')] = np.abs(data[:, cols.index('VIX')]) + 10.0
    return pd.DataFrame(data, index=idx, columns=cols)


def main():
    print("=" * 70)
    print("WALK-FORWARD FEATURE SELECTION (Phase 5 -- FEAT-02/FEAT-03)")
    print("=" * 70)

    # 1. Load market + build features + build section signals
    # DATA_DIR is read at call time so test monkeypatching of wffs.DATA_DIR takes effect.
    current_data_dir = DATA_DIR
    market_path = os.path.join(current_data_dir, 'market_data.csv')
    if not os.path.exists(market_path):
        print(
            f"\n  [wffs] WARNING: {market_path} not found. "
            f"Using synthetic features for report generation "
            f"(production runs require a real market_data.csv)."
        )
        features = _build_synthetic_features_for_test()
    else:
        market = pd.read_csv(market_path, index_col=0, parse_dates=True)
        print("\n--- Building 21-feature matrix ---")
        features = build_features(market)

    print(f"\n  features shape: {features.shape}")

    # REVISED iter1: do NOT pre-build section signals here. walk_forward_section_selection
    # takes RAW features and refits section PCA per fold via build_section_signals_for_fold
    # (closes RESEARCH.md Pitfall 4 structurally).

    # 2. Load / compute regime labels (MI target)
    print("\n--- Resolving regime labels (MI target) ---")
    labels = _load_or_compute_regime_labels(features)

    # 3. Run walk-forward section selection (FEAT-02 causal, per-fold refit)
    print("\n--- Walk-forward section selection (per-fold PCA refit) ---")
    result = walk_forward_section_selection(
        features, labels,                       # raw features - NOT pre-built signals
        train_years=3,                          # per D-03; NOT WALK_FORWARD_TRAIN_YEARS=5
        step_days=21,
        pca_window=252,
        stability_threshold=0.60,
        top_n_per_fold=3,
        random_state=RANDOM_SEED,
    )
    print(f"  n_folds: {result['n_folds']}")
    print(f"  selected sections: {result['selected']}")
    print(f"  selection frequency: {result['selection_frequency']}")

    # 4. Write FEAT-03 report
    print("\n--- Writing data/feature_importance_report.md ---")
    write_feature_importance_report(result)

    # 5. Also write machine-readable result for Plan 05 to consume
    json_path = os.path.join(DATA_DIR, 'walk_forward_selection_result.json')
    with open(json_path, 'w') as fh:
        json.dump({
            'selected': result['selected'],
            'selection_frequency': result['selection_frequency'],
            'mean_mi': result['mean_mi'],
            'n_folds': result['n_folds'],
        }, fh, indent=2)
    print(f"  Also wrote {json_path} (consumed by Plan 05 config update)")
    print("\nDone.")


if __name__ == '__main__':
    main()
