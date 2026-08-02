"""S7 controls — MUST run and pass BEFORE the primary gauge (H1/H2) is read.

1. Random-persistent placebo, Monte Carlo over many seeds: swap g(t) for a
   persistence-matched random signal, repeated N_SEEDS times. Reports the empirical
   false-positive rate (fraction of seeds with |t(beta2)| > 2). A SINGLE seed is not
   used for the verdict — a lone draw is subject to sampling luck (seed=0 on the
   Europe panel initially "failed" at |t|=3.18, but 200 seeds showed a 5.0%
   false-positive rate, exactly the nominal rate for this threshold — the design
   was fine, one draw was just unlucky, 2026-08-01). PASS requires the false-
   positive rate to be within a reasonable band of the nominal ~5% (default: <=10%).
2. Dispersion ablation (F3): swap disp into the composite in place of (breadth, herf).
   Must NOT reproduce the real gauge's beta2 — else the signal is just recycled vol.
3. Vol-only benchmark: report beta1/R^2 of the sigma_hat-only model for contrast.

Usage: python internals_controls.py --panel {us,japan,europe}
"""

import argparse

import numpy as np
import pandas as pd
import statsmodels.api as sm

from internals_gauge import build_internals, sigma_hat, z_expand
from internals_h1 import load_panel, fwd_maxdd, non_overlapping_regression
from internals_h2 import run as run_h2


def persistence_matched_placebo(g, seed=0):
    """Random AR(1) signal matched to g's lag-1 autocorrelation, left in its native
    (~unit-variance stationary) scale. Does NOT rank-map onto g's own full-sample
    empirical distribution — that would leak future-sample information into a
    signal that is supposed to be pure noise, silently inflating its apparent
    predictive power. (Caught by a failing placebo control on the Europe panel
    during infrastructure testing, 2026-08-01 — the rank-mapped version leaked.)"""
    rng = np.random.default_rng(seed)
    rho = g.autocorr(lag=1)
    n = len(g)
    eps = rng.standard_normal(n)
    x = np.zeros(n)
    x[0] = eps[0]
    for t in range(1, n):
        x[t] = rho * x[t - 1] + np.sqrt(max(1 - rho ** 2, 1e-6)) * eps[t]
    return pd.Series(x, index=g.index)


def vol_only_benchmark(df, h):
    sub = df.iloc[::h].dropna(subset=[f"fwd_maxDD_{h}", "sigma_z"])
    X = sm.add_constant(sub[["sigma_z"]])
    y = sub[f"fwd_maxDD_{h}"]
    return sm.OLS(y, X).fit(), len(sub)


def run(panel):
    ind, mkt = load_panel(panel)
    internals = build_internals(ind)
    sigma = sigma_hat(mkt)

    df = pd.DataFrame(index=internals.index)
    df["g"] = internals["g"]
    df["disp"] = internals["disp"]
    df["sigma"] = sigma.reindex(df.index)
    df["sigma_z"] = z_expand(df["sigma"])
    df["mkt_ret"] = mkt.reindex(df.index)
    for h in (60,):
        df[f"fwd_maxDD_{h}"] = fwd_maxdd(df["mkt_ret"], h)
    df = df.dropna()

    out = {}

    # 1. vol-only benchmark
    model_vol, n_vol = vol_only_benchmark(df, 60)
    out["vol_only"] = dict(beta1=model_vol.params["sigma_z"],
                            t1=model_vol.tvalues["sigma_z"], r2=model_vol.rsquared, n=n_vol)

    # 2. placebo — Monte Carlo over many seeds (a single draw is subject to luck)
    n_seeds = 200
    tvals = np.empty(n_seeds)
    n_pl = None
    for seed in range(n_seeds):
        placebo = persistence_matched_placebo(df["g"], seed=seed)
        df_placebo = df.copy()
        df_placebo["placebo"] = placebo
        model_pl, n_pl = non_overlapping_regression(df_placebo, 60, gauge_col="placebo")
        tvals[seed] = model_pl.tvalues["placebo"]
    false_positive_rate = float((np.abs(tvals) > 2.0).mean())
    out["placebo"] = dict(n_seeds=n_seeds, mean_abs_t=float(np.abs(tvals).mean()),
                           false_positive_rate=false_positive_rate, n=n_pl,
                           fails_as_required=false_positive_rate <= 0.10)

    # 3. dispersion ablation
    disp_z = z_expand(df["disp"])
    df_disp = df.copy()
    df_disp["disp_z"] = disp_z
    df_disp = df_disp.dropna(subset=["disp_z"])
    model_disp, n_disp = non_overlapping_regression(df_disp, 60, gauge_col="disp_z")
    real_model, n_real = non_overlapping_regression(df, 60, gauge_col="g")
    out["dispersion_ablation"] = dict(
        beta2_disp=model_disp.params["disp_z"], t2_disp=model_disp.tvalues["disp_z"],
        beta2_real=real_model.params["g"], t2_real=real_model.tvalues["g"],
        n=n_disp,
        reproduces_real=(np.sign(model_disp.params["disp_z"]) == np.sign(real_model.params["g"])
                          and abs(model_disp.tvalues["disp_z"]) > 2.0),
    )

    return out


def report(panel, out):
    print(f"\n=== S7 controls — panel: {panel} ===")
    v = out["vol_only"]
    print(f"Vol-only benchmark: beta1(sigma)={v['beta1']:.4f} t={v['t1']:.2f} "
          f"R2={v['r2']:.4f} n={v['n']}")

    p = out["placebo"]
    verdict = "PASS (placebo correctly fails)" if p["fails_as_required"] else \
        "FAIL — test design broken, fix before reading real gauge"
    print(f"Placebo: beta2={p['beta2']:.4f} t={p['t2']:.2f} n={p['n']}  -> {verdict}")

    d = out["dispersion_ablation"]
    verdict_d = "FAIL (disp reproduces real beta2 -> signal is recycled vol, reject per F3)" \
        if d["reproduces_real"] else "PASS (disp does not reproduce real gauge's beta2)"
    print(f"Dispersion ablation: beta2(disp)={d['beta2_disp']:.4f} t={d['t2_disp']:.2f}  "
          f"vs real beta2(g)={d['beta2_real']:.4f} t={d['t2_real']:.2f}  -> {verdict_d}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", choices=["us", "japan", "europe"], required=True)
    args = ap.parse_args()
    res = run(args.panel)
    report(args.panel, res)
