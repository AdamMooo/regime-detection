"""Walk-forward (anchored/expanding-window) out-of-sample regime validation.

Standard walk-forward CV for time series: refit the HDP-HMM periodically
on all data known up to that point, then forward-filter -- never smooth
-- the next block using those frozen params. This is exactly the causal
machinery in forward_backward_numpy's `filtered` output, verified in
tests/test_causality_invariants.py. The realized block is then folded
into the training window before the next refit.

This exists because run_paper_experiments.py only ever fits/evaluates
through config.TRAIN_END (2023-12-31) -- everything after that has
never actually been scored by the model (see NOTES.md "Known Issues").
"""

import numpy as np
import pandas as pd

from src.config import HDP_TRUNCATION, TRAIN_END, WALK_FORWARD_REFIT_DAYS
from src.core.hdp_hmm import (
    fit_hdp_hmm, forward_backward_numpy, get_labels_and_probs, posterior_mean_params,
)

REGIME_NAMES = {0: 'Low-Vol', 1: 'Moderate-Vol', 2: 'High-Vol'}


def merge_states_to_regimes(labels_raw, vix_values, K_eff):
    """Map K_eff active HDP states to 3 canonical regimes by mean-VIX rank.

    Same method run_paper_experiments.py uses in-sample: sort active
    states by mean VIX, partition into thirds. Must be redone per fold
    since state indices aren't stable across independent SVI fits.
    """
    if K_eff < 3:
        raise ValueError(
            f"HDP pruned to only {K_eff} active state(s) this fold -- cannot "
            f"map to 3 canonical regimes (Low/Moderate/High-Vol)."
        )
    labels_raw = np.asarray(labels_raw)
    mean_vix_per_state = {
        s: float(vix_values[labels_raw == s].mean()) if (labels_raw == s).sum() > 0 else 0.0
        for s in range(K_eff)
    }
    sorted_by_vix = sorted(range(K_eff), key=mean_vix_per_state.get)
    return {s: min(int(i * 3 / K_eff), 2) for i, s in enumerate(sorted_by_vix)}


def walk_forward_oos(feat_full, vix_full, refit_every=WALK_FORWARD_REFIT_DAYS,
                      train_end=TRAIN_END, K_max=HDP_TRUNCATION, seed_base=1000):
    """Expanding-window walk-forward OOS regime labels for dates after train_end.

    Parameters
    ----------
    feat_full : DataFrame (T, D)
        Expanding-standardized features, full history (see
        src.core.inference.expanding_standardize -- causal by construction,
        so it's safe to compute once over the whole series and slice).
    vix_full : Series (T,)
        Raw VIX level aligned to feat_full.index, used only for the
        VIX-rank state->regime relabeling, never fed to the model.
    refit_every : int
        Trading days per fold between HDP-HMM refits.
    train_end : str or Timestamp
        Last in-sample date; the first fold's training window.
    K_max : int
        HDP truncation level.
    seed_base : int
        RANDOM_SEED offset per fold so folds don't share identical SVI
        initialization noise.

    Returns
    -------
    DataFrame indexed by date: regime_label, regime_idx, filt_prob_max.
    Every row here was produced using only data available at or before
    that date -- no full-sample statistics, no future observations.
    """
    train_end = pd.Timestamp(train_end)
    test_index = feat_full.index[feat_full.index > train_end]
    if len(test_index) == 0:
        raise ValueError(f"No data after train_end={train_end.date()} to validate on")

    oos_rows = []
    window_end = train_end

    for fold_num, start in enumerate(range(0, len(test_index), refit_every)):
        block_index = test_index[start:start + refit_every]
        train_idx = feat_full.index[feat_full.index <= window_end]
        obs_train = feat_full.loc[train_idx].values
        obs_window = feat_full.loc[train_idx.append(block_index)].values

        _, samples = fit_hdp_hmm(obs_train, K_max=K_max, seed=seed_base + fold_num)
        params = posterior_mean_params(samples, K_max=K_max)

        # Active states + training-window labels, using the model's own
        # pruning logic (no hysteresis -- only used to rank states by VIX).
        train_labels_raw, _, _, active = get_labels_and_probs(obs_train, params, hold_days=1)
        K_eff = len(active)

        vix_train = vix_full.reindex(train_idx).values
        state_to_regime = merge_states_to_regimes(train_labels_raw, vix_train, K_eff)

        # Forward-filter the whole window with THIS fold's params, then take
        # only the new block's rows. Causal: row t of the block depends on
        # obs_window[0..t] inclusive, nothing after it.
        filtered_window, _ = forward_backward_numpy(obs_window, params)
        block_filtered = filtered_window[-len(block_index):][:, active]
        block_filtered = block_filtered / block_filtered.sum(axis=1, keepdims=True)
        block_labels_raw = block_filtered.argmax(axis=1)
        block_filt_prob_max = block_filtered.max(axis=1)
        block_regime_idx = np.array([state_to_regime[l] for l in block_labels_raw])

        for i, date in enumerate(block_index):
            oos_rows.append({
                'date': date,
                'regime_idx': int(block_regime_idx[i]),
                'regime_label': REGIME_NAMES[block_regime_idx[i]],
                'filt_prob_max': float(block_filt_prob_max[i]),
            })

        print(f"  Fold {fold_num}: refit on {len(obs_train)} rows through "
              f"{window_end.date()}, scored {len(block_index)} OOS days "
              f"({block_index[0].date()} -> {block_index[-1].date()})")

        window_end = block_index[-1]

    return pd.DataFrame(oos_rows).set_index('date')
