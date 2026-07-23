"""V2 Phase-1 synthetic validation battery (SYNTHETIC DATA ONLY — blind preserved).

Rehearses the full Phase-3 pipeline shape on simulated panels with known truth:
expanding walk-forward, annual refits, lambda selected causally per refit by
validation-window strategy Sharpe (last 4y of train), centers fit on train,
greedy online classification of the next year with frozen parameters.

Configs:
  R  realistic 2-state (calm ~11%/+15% ann, bear ~32%/-25% ann, dwell ~200/100d)
  S  strong-separation 2-state (easy detection sanity)
  N  iid null, matched unconditional moments (calibration control)

Bars:
  B1 (S): mean OOS balanced accuracy >= 0.85 and mean fee(JM - VolTarget) > 0
  B2 (R): mean OOS balanced accuracy >= 0.70
  B3 (N): fee(JM - VolTarget) 90% bootstrap CI contains 0 for >= 2/3 seeds

Writes results/synthetic_validation.csv.
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jumpmodel import build_features
from backtest import fko_fee, jm_weights, sharpe, stationary_bootstrap_ci, strategy_returns, vol_target_weights
from walkforward import walk_forward as pipeline_walk_forward

T_TOTAL = 6300
TRAIN0 = 3024
REFIT = 252
VAL = 1008
LAMBDA_GRID = [10.0, 25.0, 50.0, 100.0, 200.0, 400.0, 800.0]
N_INIT = 5
SEEDS = [11, 12, 13]

CONFIGS = {
    "R": dict(p_stay=(0.995, 0.99), mu=(0.0006, -0.0010), sig=(0.007, 0.020)),
    "S": dict(p_stay=(0.997, 0.992), mu=(0.0008, -0.0030), sig=(0.006, 0.030)),
    "N": None,
}


def simulate(config, seed):
    rng = np.random.default_rng(seed)
    if config is None:
        return rng.normal(0.0004, 0.011, T_TOTAL), np.zeros(T_TOTAL, dtype=int)
    s = np.empty(T_TOTAL, dtype=int)
    s[0] = 0
    for t in range(1, T_TOTAL):
        s[t] = s[t - 1] if rng.random() < config["p_stay"][s[t - 1]] else 1 - s[t - 1]
    r = rng.normal(np.where(s == 0, *config["mu"]), np.where(s == 0, *config["sig"]))
    return r, s


def walk_forward(r):
    F = build_features(r).to_numpy()
    return pipeline_walk_forward(r, F, burn=63, train0=TRAIN0, refit=REFIT,
                                 grid=LAMBDA_GRID, val=VAL, n_init=N_INIT)


def main():
    rows = []
    for name, cfg in CONFIGS.items():
        for seed in SEEDS:
            tic = time.time()
            r, s_true = simulate(cfg, seed)
            states, lam_hist = walk_forward(r)
            oos = states >= 0
            s_o, r_o, t_o = states[oos], r[oos], s_true[oos]

            bac = np.nan
            if name != "N":
                bac = ((s_o == t_o)[t_o == 0].mean() + (s_o == t_o)[t_o == 1].mean()) / 2

            ret_jm = strategy_returns(jm_weights(s_o), r_o, 0.0)
            ret_vt = strategy_returns(vol_target_weights(r_o), r_o, 0.0)
            fee = fko_fee(ret_jm, ret_vt, gamma=10.0)
            fee_oracle = fee_oracle_lag10 = np.nan
            if name != "N":
                # capability ceiling diagnostics: perfect detection, and perfect
                # detection delayed 10d (intrinsic-lag cost of any causal filter)
                ret_or = strategy_returns(jm_weights(t_o), r_o, 0.0)
                s_lag = np.concatenate([t_o[:1].repeat(10), t_o[:-10]])
                ret_ol = strategy_returns(jm_weights(s_lag), r_o, 0.0)
                fee_oracle = fko_fee(ret_or, ret_vt, gamma=10.0)
                fee_oracle_lag10 = fko_fee(ret_ol, ret_vt, gamma=10.0)
            ci = stationary_bootstrap_ci(ret_jm, ret_vt,
                                         lambda a, b: fko_fee(a, b, gamma=10.0),
                                         n_boot=300, seed=seed)
            rows.append(dict(
                config=name, seed=seed, oos_days=int(oos.sum()), bac=round(float(bac), 3),
                bear_frac=round(float((s_o == 1).mean()), 3),
                switches_yr=round(float((s_o[1:] != s_o[:-1]).sum() / len(s_o) * 252), 2),
                lam_median=float(np.median(lam_hist)),
                sharpe_jm=round(sharpe(ret_jm), 3), sharpe_vt=round(sharpe(ret_vt), 3),
                sharpe_bh=round(sharpe(r_o), 3),
                fee_jm_vs_vt_bps=round(fee, 1),
                fee_ci_lo=round(ci[0], 1), fee_ci_hi=round(ci[1], 1),
                fee_oracle=round(float(fee_oracle), 1),
                fee_oracle_lag10=round(float(fee_oracle_lag10), 1),
                runtime_s=round(time.time() - tic, 1),
            ))
            print(rows[-1], flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results" / "synthetic_validation.csv", index=False)

    g = df.groupby("config")
    b1 = (g["bac"].mean()["S"] >= 0.85) and (g["fee_jm_vs_vt_bps"].mean()["S"] > 0)
    b2 = g["bac"].mean()["R"] >= 0.70
    n_rows = df[df["config"] == "N"]
    b3 = ((n_rows["fee_ci_lo"] <= 0) & (n_rows["fee_ci_hi"] >= 0)).mean() >= 2 / 3
    print("\nB1 (S capability):", "PASS" if b1 else "FAIL")
    print("B2 (R realistic):", "PASS" if b2 else "FAIL")
    print("B3 (N calibration):", "PASS" if b3 else "FAIL")
    print("SYNTHETIC VALIDATION:", "PASS" if (b1 and b2 and b3) else "FAIL")
    return 0 if (b1 and b2 and b3) else 1


if __name__ == "__main__":
    sys.exit(main())
