"""E1 -- Static clustering (GMM) vs temporal (HDP-HMM) under identical post-processing.

Reframe question (see .planning/REASSESSMENT-PLAN.md): an HMM's ONLY structural
advantage over a static Gaussian mixture is that it models P(S_t | S_{t-1}). Does that
transition structure actually buy a better *state path* -- more persistent, less
whipsawy -- than clustering each day independently? The prior audit never tested this
(no static-clustering baseline existed anywhere in the repo).

Everything is held fixed except the presence of a transition model: same 4
expanding-standardized features, same K, same diagonal-Gaussian emission family, same
VIX-rank 3-bucket merge, same optional hysteresis.

Two isolations:
  (i)  PURE PATH-SMOOTHING -- decode the SAME HDP params two ways:
         - filtered P(z_t|x_{1:t})  (uses the transition matrix)
         - emissions-only argmax     (ignores transitions; classify each day to its
                                       nearest state by emission likelihood)
       Any dwell/whipsaw gap is attributable solely to the transition matrix.
  (ii) FULL MODEL -- HDP-HMM vs an independently-fit GaussianMixture(diag), K=8 & K=3.

Metrics (all under identical processing): mean dwell, regime-changes/yr (whipsaw),
within-regime realized-vol ladder, held-out per-observation log-likelihood.

In-sample by design: this reassesses the paper's in-sample dwell headline (66/61/41).
Run: .venv/Scripts/python.exe scripts/static_vs_temporal.py
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.special import logsumexp
from scipy.stats import norm
from sklearn.mixture import GaussianMixture

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import FEATURES, HDP_TRUNCATION, RANDOM_SEED, DATA_DIR, RESULTS_DIR
from src.core.hdp_hmm import (
    _apply_hysteresis, fit_hdp_hmm, get_labels_and_probs, posterior_mean_params,
)
from src.core.walk_forward import merge_states_to_regimes

PROC = os.path.join(DATA_DIR, "processed")


# ------------------------------------------------------------------ data
def load():
    feat_tr = pd.read_csv(os.path.join(PROC, "features_train.csv"), parse_dates=["Date"]).set_index("Date")
    feat_te = pd.read_csv(os.path.join(PROC, "features_test.csv"), parse_dates=["Date"]).set_index("Date")
    raw = pd.read_csv(os.path.join(PROC, "spx_data.csv"), parse_dates=["Date"]).set_index("Date")
    X_tr = feat_tr[FEATURES].values
    X_te = feat_te[FEATURES].values
    # raw VIX + raw returns aligned to the standardized train index (for merge + fingerprints)
    raw_tr = raw.reindex(feat_tr.index)
    return X_tr, X_te, raw_tr["vol_index"].values, raw_tr["spy_ret"].values, feat_tr.index


# ------------------------------------------------------------------ metrics
def path_metrics(regime_idx, spy_ret, n_years, hold_days):
    """Dwell / whipsaw / realized-vol ladder for a 3-regime label path."""
    r = np.asarray(regime_idx)
    if hold_days > 1:
        r = _apply_hysteresis(r, hold_days)[0]
    # spells (contiguous runs of the same regime)
    changes = int((np.diff(r) != 0).sum())
    spells = []
    cur, length = r[0], 1
    for t in range(1, len(r)):
        if r[t] == cur:
            length += 1
        else:
            spells.append(length)
            cur, length = r[t], 1
    spells.append(length)
    vols = {}
    for k in range(3):
        m = r == k
        vols[k] = float(spy_ret[m].std() * np.sqrt(252) * 100) if m.sum() > 5 else np.nan
    per_regime_dwell = {}
    for k in range(3):
        ks = [s for s, lab in zip(spells, _spell_labels(r)) if lab == k]
        per_regime_dwell[k] = float(np.mean(ks)) if ks else np.nan
    return {
        "mean_dwell": float(np.mean(spells)),
        "n_changes": changes,
        "changes_per_yr": changes / n_years,
        "vol_ladder": vols,
        "per_regime_dwell": per_regime_dwell,
        "dist": {k: int((r == k).sum()) for k in range(3)},
    }


def _spell_labels(r):
    labs = [r[0]]
    for t in range(1, len(r)):
        if r[t] != r[t - 1]:
            labs.append(r[t])
    return labs


def forward_loglik(obs, params):
    """log P(x_{1:T}) under the HMM posterior-mean params (scaled forward algorithm)."""
    T, K = obs.shape[0], params["K_max"]
    locs, sd = params["locs"], params["scale_diag"]
    log_lik = np.zeros((T, K))
    for k in range(K):
        for d in range(obs.shape[1]):
            log_lik[:, k] += norm.logpdf(obs[:, d], locs[k, d], sd[k, d])
    log_trans = np.log(params["trans_matrix"] + 1e-300)
    log_init = np.log(params["init_probs"] + 1e-300)
    la = log_init + log_lik[0]
    total = logsumexp(la)
    la = la - total
    for t in range(1, T):
        pred = logsumexp(la[:, None] + log_trans, axis=0)
        a = pred + log_lik[t]
        c = logsumexp(a)
        total += c
        la = a - c
    return total


def emissions_only_labels(obs, params, active):
    """Classify each day INDEPENDENTLY to its nearest active state by emission
    log-likelihood -- the static analog of the HMM decode, holding emissions fixed
    and discarding the transition matrix."""
    locs, sd = params["locs"], params["scale_diag"]
    ll = np.zeros((obs.shape[0], len(active)))
    for i, k in enumerate(active):
        for d in range(obs.shape[1]):
            ll[:, i] += norm.logpdf(obs[:, d], locs[k, d], sd[k, d])
    return ll.argmax(axis=1)  # local index into `active`


# ------------------------------------------------------------------ main
def main():
    X_tr, X_te, vix_tr, ret_tr, idx = load()
    n_years = len(X_tr) / 252.0
    print(f"Train N={len(X_tr)} ({idx[0].date()}..{idx[-1].date()}, {n_years:.2f}y); Test N={len(X_te)}")

    # ---- fit HDP-HMM (seed 42 = paper) ----
    _, samples = fit_hdp_hmm(X_tr, K_max=HDP_TRUNCATION, seed=RANDOM_SEED)
    params = posterior_mean_params(samples, K_max=HDP_TRUNCATION)
    hdp_raw, _, _, active = get_labels_and_probs(X_tr, params, hold_days=1)  # raw filtered argmax
    K_eff = len(active)

    # filtered decode (uses transitions) -> canonical regimes
    s2r_filt = merge_states_to_regimes(hdp_raw, vix_tr, K_eff)
    hdp_filt_regime = np.array([s2r_filt[s] for s in hdp_raw])

    # emissions-only decode (same params, transitions ignored) -> canonical regimes
    emo_raw = emissions_only_labels(X_tr, params, active)
    s2r_emo = merge_states_to_regimes(emo_raw, vix_tr, K_eff)
    hdp_emo_regime = np.array([s2r_emo[s] for s in emo_raw])

    results = {}
    results["HDP filtered (transitions)"] = (hdp_filt_regime, forward_loglik(X_te, params))
    results["HDP emissions-only (no transitions)"] = (hdp_emo_regime, None)

    # ---- GMM baselines (static; same features, same merge) ----
    for k in (8, 3):
        gmm = GaussianMixture(n_components=k, covariance_type="diag",
                              n_init=10, random_state=RANDOM_SEED, max_iter=500)
        gmm.fit(X_tr)
        gmm_raw = gmm.predict(X_tr)
        s2r = merge_states_to_regimes(gmm_raw, vix_tr, k)
        gmm_regime = np.array([s2r[s] for s in gmm_raw])
        results[f"GMM K={k} (static)"] = (gmm_regime, gmm.score(X_te))

    # ---- report ----
    for hold in (1, 3):
        tag = "RAW (no hysteresis)" if hold == 1 else "with 3-day hysteresis"
        print(f"\n{'='*78}\n{tag}\n{'='*78}")
        print(f"{'model':<38}{'dwell':>7}{'chg/yr':>8}{'RV Low/Mod/High':>22}")
        for name, (regime, _) in results.items():
            m = path_metrics(regime, ret_tr, n_years, hold)
            vl = m["vol_ladder"]
            print(f"{name:<38}{m['mean_dwell']:>7.1f}{m['changes_per_yr']:>8.1f}"
                  f"{vl[0]:>7.1f}{vl[1]:>7.1f}{vl[2]:>7.1f}")

    print(f"\n{'='*78}\nHeld-out per-observation log-likelihood (test N={len(X_te)}, nats/obs)\n{'='*78}")
    for name, (_, ll) in results.items():
        if ll is not None:
            per = ll / len(X_te) if name.startswith("HDP") else ll
            print(f"  {name:<40}{per:>9.4f}")

    # ---- persist a compact CSV ----
    rows = []
    for hold in (1, 3):
        for name, (regime, ll) in results.items():
            m = path_metrics(regime, ret_tr, n_years, hold)
            rows.append({
                "model": name, "hysteresis": hold, "mean_dwell": m["mean_dwell"],
                "changes_per_yr": m["changes_per_yr"], "n_changes": m["n_changes"],
                "rv_low": m["vol_ladder"][0], "rv_mod": m["vol_ladder"][1],
                "rv_high": m["vol_ladder"][2],
                "heldout_ll_per_obs": (ll / len(X_te) if (ll is not None and name.startswith("HDP")) else ll),
            })
    out = os.path.join(RESULTS_DIR, "static_vs_temporal.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
