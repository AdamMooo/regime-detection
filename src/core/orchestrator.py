"""Training workflow coordination and walk-forward validation.

Walk-forward out-of-sample validation with expanding or rolling windows.

Functions
---------
walk_forward(market, features, n_states, n_pca, cov_type='full', mode='expanding')
    Rolling-window out-of-sample validation
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from src.config import (
    RANDOM_SEED, PCA_ROLLING_WINDOW, REGIME_HOLD_DAYS, VIX_BYPASS,
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS, WALK_FORWARD_MODE,
    COV_TYPE, REGIME_NAMES,
)
from src.core.inference import expanding_standardize, _fit_hmm, filtered_labels


def walk_forward(market, features, n_states, n_pca, cov_type=COV_TYPE,
                 mode=WALK_FORWARD_MODE):
    """Walk-forward validation with expanding or rolling window.

    mode='expanding': training window grows over time (all past data).
    mode='rolling':   fixed-length training window (most recent N years).

    Each fold:  standardize on train -> PCA on last ROLLING_WINDOW days
    -> project full train -> HMM -> predict test

    Parameters
    ----------
    market : DataFrame
        Market data with dates index
    features : DataFrame
        Features with dates index
    n_states : int
        Number of regime states
    n_pca : int
        Number of PCA components
    cov_type : str
        HMM covariance type
    mode : str
        'expanding' or 'rolling'

    Returns
    -------
    valid : Series
        Out-of-sample regime labels
    name_map : dict
        Mapping from regime index to name
    """
    min_train = WALK_FORWARD_TRAIN_YEARS * 252
    step = WALK_FORWARD_STEP_DAYS

    oos_name_labels = pd.Series(index=features.index, dtype=object)
    oos_name_labels[:] = np.nan

    t = min_train
    step_num = 0
    while t < len(features):
        end = min(t + step, len(features))

        if mode == 'rolling':
            # Fixed-length rolling window
            train_start = max(0, t - min_train)
            train_feats = features.iloc[train_start:t]
        else:
            # Expanding window (all past data)
            train_feats = features.iloc[:t]
        test_feats = features.iloc[t:end]

        if len(test_feats) == 0:
            t = end
            continue

        # Expanding-window standardize (match train() pipeline exactly)
        X_combined = np.vstack([train_feats.values, test_feats.values])
        wf_warmup = min(252, max(50, len(train_feats) // 4))
        X_all_scaled, _, _ = expanding_standardize(X_combined, min_warmup=wf_warmup)
        X_train = X_all_scaled[:len(train_feats)]
        X_test = X_all_scaled[len(train_feats):]

        # Drop warm-up NaN rows from training data
        valid_train = ~np.isnan(X_train[:, 0])
        X_train = X_train[valid_train]
        train_feats_valid = train_feats[valid_train]

        # PCA: fit on last ROLLING_WINDOW days of train, project all
        pca_window = min(PCA_ROLLING_WINDOW, len(X_train))
        n_comp = min(n_pca, X_train.shape[1])
        pca_wf = PCA(n_components=n_comp, random_state=RANDOM_SEED)
        pca_wf.fit(X_train[-pca_window:])
        pc_train = pca_wf.transform(X_train)
        pc_test = pca_wf.transform(X_test)

        # VIX bypass: append scaled VIX directly to PCs
        if VIX_BYPASS:
            vix_train = market['VIX'].reindex(train_feats_valid.index).values
            vix_test = market['VIX'].reindex(test_feats.index).values
            v_mean, v_std = vix_train.mean(), vix_train.std()
            pc_train = np.hstack([pc_train, ((vix_train - v_mean) / v_std).reshape(-1, 1)])
            pc_test = np.hstack([pc_test, ((vix_test - v_mean) / v_std).reshape(-1, 1)])

        # HMM (fit on train PCs, pick best seed)
        best_m, best_ll = None, -np.inf
        for seed in range(5):
            m = _fit_hmm(pc_train, n_states, cov_type, seed)
            ll = m.score(pc_train)
            if ll > best_ll:
                best_m, best_ll = m, ll

        assert best_m is not None
        raw_preds = filtered_labels(best_m, pc_test, hold_days=REGIME_HOLD_DAYS)

        # Assign names using VIX-rank order — same logic as label_regimes() in hmm_training.
        # This ensures OOS labels use the same names as IS labels (from REGIME_NAMES[n_states])
        # and guarantees exactly n_states unique names across all folds.
        train_labels = filtered_labels(best_m, pc_train, hold_days=REGIME_HOLD_DAYS)
        vix_train = market['VIX'].reindex(train_feats_valid.index).values
        tl = train_labels[:len(vix_train)]
        regime_vix = {}
        for r in range(n_states):
            mask = (tl == r)
            regime_vix[r] = float(np.nanmean(vix_train[mask])) if mask.sum() > 0 else 0.0
        sorted_by_vix = sorted(regime_vix, key=lambda k: regime_vix[k])
        names = REGIME_NAMES.get(n_states, [f'Regime-{i}' for i in range(n_states)])
        fold_name_map = {sorted_by_vix[i]: names[i] for i in range(n_states)}

        # Store OOS labels as vol-bracket names for direct IS-OOS comparison
        oos_name_labels.iloc[t:end] = [fold_name_map.get(r, f'Regime-{r}') for r in raw_preds]

        step_num += 1
        if step_num % 10 == 0:
            print(f"    step {step_num}")
        t = end

    valid_names = oos_name_labels.dropna()
    # Convert string names to integer labels with a unified name_map
    unique_names = sorted(valid_names.unique())
    name_to_int = {name: i for i, name in enumerate(unique_names)}
    name_map = {i: name for i, name in enumerate(unique_names)}
    valid = valid_names.map(name_to_int).astype(int)
    return valid, name_map


__all__ = ['walk_forward']
