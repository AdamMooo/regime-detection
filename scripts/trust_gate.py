#!/usr/bin/env python3
"""Phase 0 gate -- is cross-window agreement a calibrated confidence measure?

.planning/ROADMAP.md Phase 0: the go/no-go for the trustworthy-state program.
Two questions about the walk-forward ensemble's OOS labels, with forward realized
volatility (the one observable the state plausibly tracks) as the target:

  (1) RESOLUTION BY CONFIDENCE. Does the state label separate forward realized vol
      MORE SHARPLY on high-agreement days than low-agreement days? If agreement is
      a real confidence measure, unanimous days are crisp and split days are mush.
      Measured with eta^2 = between-bucket SS / total SS (correlation ratio: the
      one-way-ANOVA fraction of forward-vol variance explained by the bucket).

  (2) SKILL vs THE VIX NULL. Does the learned state beat the project's OWN null
      (VIX 15/25 thresholds, config.THRESH_VOL_*) at forecasting forward realized
      vol? A causal expanding per-bucket mean is the forecast; RMSE is stratified
      by agreement. If state ~ VIX-threshold, the state's apparent trust is just
      VIX's -- Premise 1 / the beyond-VIX null.

Why BOTH: a pure noisy discretization of VIX would ALSO show RMSE falling with
agreement (split days sit near VIX cut-points, where the future is genuinely
ambiguous), so (1) cannot distinguish a real state from discretized VIX. Beating
the VIX-threshold buckets in (2) is the discriminator.

Causal: OOS labels are walk-forward forward-filtered; forward RV is strictly future
(repo build_target convention); the expanding forecast at day t uses only prior OOS
days whose forward window has already CLOSED (j <= t-h) -- otherwise overlapping
windows leak the future. Reuses cached labels; no model refit.

Reads  : data/oos_regime_labels.csv, data/processed/spx_data.csv
Writes : results/trust_gate.csv, results/trust_gate.png
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import DATA_DIR, RESULTS_DIR, THRESH_VOL_LOW, THRESH_VOL_HIGH

H = 21                       # forward horizon (trading days ~ 1 month)
AGREE_BINS = [(1 / 3, "split"), (2 / 3, "majority"), (1.0, "unanimous")]
STATE_NAMES = {0: "Low-Vol", 1: "Moderate-Vol", 2: "High-Vol"}


# ------------------------------------------------------------------ data
def load():
    oos = pd.read_csv(os.path.join(DATA_DIR, "oos_regime_labels.csv"),
                      index_col=0, parse_dates=True)
    mkt = pd.read_csv(os.path.join(DATA_DIR, "processed", "spx_data.csv"),
                      index_col=0, parse_dates=True).reindex(oos.index)
    df = pd.DataFrame({
        "state": oos["regime_idx"].astype(int),
        "agree": oos["agreement_frac"].astype(float),
        "vix": mkt["vol_index"].astype(float),
        "ret": mkt["spy_ret"].astype(float),
    }, index=oos.index)
    df["fwd_rv"] = forward_realized_vol(df["ret"].values, H)
    df["vix_bucket"] = vix_threshold_bucket(df["vix"].values)
    return df


def forward_realized_vol(ret, h):
    """Annualized realized vol (%) of ret[t+1..t+h] -- strictly forward, repo convention."""
    s = pd.Series(ret)
    return (s.rolling(h).std().shift(-h) * np.sqrt(252) * 100).values


def vix_threshold_bucket(vix):
    """The project's null: VIX<15 -> Low(0), 15<=VIX<25 -> Mod(1), VIX>=25 -> High(2)."""
    b = np.ones(len(vix), dtype=int)
    b[vix < THRESH_VOL_LOW] = 0
    b[vix >= THRESH_VOL_HIGH] = 2
    return b


# ------------------------------------------------------------------ metrics
def eta_squared(buckets, y):
    """Correlation ratio: fraction of Var(y) explained by the bucket label (one-way R^2)."""
    y = np.asarray(y, float)
    buckets = np.asarray(buckets)
    ok = np.isfinite(y)
    y, buckets = y[ok], buckets[ok]
    if len(y) < 3:
        return np.nan
    grand = y.mean()
    ss_tot = ((y - grand) ** 2).sum()
    ss_between = sum(len(y[buckets == g]) * (y[buckets == g].mean() - grand) ** 2
                     for g in np.unique(buckets))
    return ss_between / ss_tot if ss_tot > 0 else np.nan


def expanding_bucket_forecast(buckets, y, h, min_n=20):
    """Causal expanding per-bucket-mean forecast of forward RV.

    At day t the forecast is the mean forward-RV of prior days in the same bucket
    whose forward window has already CLOSED (j <= t-h). The h-lag is essential:
    y[j] is the realized vol over (j, j+h], so it is not known until day j+h;
    using it any earlier leaks the future through the overlapping window.
    """
    n = len(y)
    fc = np.full(n, np.nan)
    sums, counts = defaultdict(float), defaultdict(int)
    for t in range(n):
        j = t - h                          # the obs whose window just closed
        if j >= 0 and np.isfinite(y[j]):
            sums[buckets[j]] += y[j]
            counts[buckets[j]] += 1
        b = buckets[t]
        if counts[b] >= min_n:
            fc[t] = sums[b] / counts[b]
    return fc


def rmse(pred, y):
    m = np.isfinite(pred) & np.isfinite(y)
    return float(np.sqrt(np.mean((pred[m] - y[m]) ** 2))) if m.any() else np.nan


# ------------------------------------------------------------------ main
def main():
    df = load()
    y = df["fwd_rv"].values
    state, vixb, agree = df["state"].values, df["vix_bucket"].values, df["agree"].values
    n_eval = int(np.isfinite(y).sum())
    print(f"OOS: {len(df)} days ({df.index[0].date()}..{df.index[-1].date()}); "
          f"{n_eval} with a complete {H}d-forward window.\n")

    fc_state = expanding_bucket_forecast(state, y, H)
    fc_vix = expanding_bucket_forecast(vixb, y, H)

    rows = []
    print(f"{'agreement':<12}{'N':>6}{'eta2_state':>12}{'eta2_VIX':>10}"
          f"{'RMSE_state':>12}{'RMSE_VIX':>10}")
    print("-" * 62)
    for frac, name in AGREE_BINS:
        m = np.isclose(agree, frac)
        n = int((m & np.isfinite(y)).sum())
        e_s, e_v = eta_squared(state[m], y[m]), eta_squared(vixb[m], y[m])
        r_s, r_v = rmse(fc_state[m], y[m]), rmse(fc_vix[m], y[m])
        print(f"{name:<12}{n:>6}{e_s:>12.3f}{e_v:>10.3f}{r_s:>12.2f}{r_v:>10.2f}")
        rows.append({"agreement": name, "frac": frac, "n": n,
                     "eta2_state": e_s, "eta2_vix": e_v,
                     "rmse_state": r_s, "rmse_vix": r_v})
    # overall (all days pooled)
    e_s, e_v = eta_squared(state, y), eta_squared(vixb, y)
    r_s, r_v = rmse(fc_state, y), rmse(fc_vix, y)
    print("-" * 62)
    print(f"{'ALL':<12}{n_eval:>6}{e_s:>12.3f}{e_v:>10.3f}{r_s:>12.2f}{r_v:>10.2f}")
    rows.append({"agreement": "ALL", "frac": np.nan, "n": n_eval,
                 "eta2_state": e_s, "eta2_vix": e_v, "rmse_state": r_s, "rmse_vix": r_v})

    pd.DataFrame(rows).to_csv(os.path.join(RESULTS_DIR, "trust_gate.csv"), index=False)

    # ---- figure: eta^2 and RMSE by agreement, state vs VIX null ----
    res = pd.DataFrame(rows[:-1])
    x = np.arange(len(res))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.bar(x - 0.2, res["eta2_state"], 0.4, label="HMM state", color="#2b6cb0")
    ax1.bar(x + 0.2, res["eta2_vix"], 0.4, label="VIX 15/25 null", color="#a0aec0")
    ax1.set_title(r"Resolution: $\eta^2$ of forward RV by confidence")
    ax1.set_ylabel(r"$\eta^2$ (variance explained)")
    ax2.bar(x - 0.2, res["rmse_state"], 0.4, label="HMM state", color="#2b6cb0")
    ax2.bar(x + 0.2, res["rmse_vix"], 0.4, label="VIX 15/25 null", color="#a0aec0")
    ax2.set_title(f"Skill: RMSE of {H}d forward-RV forecast (lower=better)")
    ax2.set_ylabel("RMSE (ann. vol %)")
    for ax in (ax1, ax2):
        ax.set_xticks(x)
        ax.set_xticklabels(res["agreement"])
        ax.set_xlabel("cross-window agreement")
        ax.legend()
    fig.suptitle("Phase 0 gate -- is agreement a calibrated confidence measure, beyond VIX?")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "trust_gate.png"), dpi=130)
    print(f"\nWrote {os.path.join(RESULTS_DIR, 'trust_gate.csv')} and trust_gate.png")


if __name__ == "__main__":
    main()
