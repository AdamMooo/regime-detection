"""H1 — incremental predictive validity (prereg S5). fwd_maxDD ~ z(sigma_hat) + z(g).

Primary: H=60d, NON-OVERLAPPING sampling (every 60th day) — this is the frozen,
gating regression (overlap inflates t-stats per the ceiling finding, S5).
Sensitivity (non-gating, reported alongside): H=20d non-overlapping, and H=60d
overlapping windows with HAC (Newey-West) standard errors.

Usage: python internals_h1.py --panel {us,japan,europe}
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from internals_gauge import build_internals, sigma_hat, z_expand

ROOT = Path(__file__).resolve().parents[1]

PANELS = {
    "us": dict(ind="industry48_daily.csv", mkt="market_daily.csv"),
    "japan": dict(ind="japan_assets_daily.csv", mkt="japan_market_daily.csv"),
    "europe": dict(ind="europe_assets_daily.csv", mkt="europe_market_daily.csv"),
}


def load_panel(name):
    cfg = PANELS[name]
    ind = pd.read_csv(ROOT / "data" / "processed" / cfg["ind"], index_col=0, parse_dates=True)
    mkt = pd.read_csv(ROOT / "data" / "processed" / cfg["mkt"], index_col=0, parse_dates=True)
    return ind, mkt["mkt_ret"]


def fwd_maxdd(ret, h):
    """Forward peak-to-trough max drawdown over the next h days (t+1..t+h)."""
    r = ret.to_numpy()
    n = len(r)
    out = np.full(n, np.nan)
    for t in range(n - h):
        window = r[t + 1:t + 1 + h]
        eq = np.cumprod(1.0 + window)
        peak = np.maximum.accumulate(eq)
        out[t] = (eq / peak - 1.0).min()
    return pd.Series(out, index=ret.index)


def non_overlapping_regression(df, h, gauge_col="g"):
    """df must have columns fwd_maxDD_{h}, sigma_z, gauge_col; samples every h-th row."""
    sub = df.iloc[::h].dropna(subset=[f"fwd_maxDD_{h}", "sigma_z", gauge_col])
    X = sm.add_constant(sub[["sigma_z", gauge_col]])
    y = sub[f"fwd_maxDD_{h}"]
    model = sm.OLS(y, X).fit()
    return model, len(sub)


def overlapping_hac_regression(df, h, gauge_col="g"):
    sub = df.dropna(subset=[f"fwd_maxDD_{h}", "sigma_z", gauge_col])
    X = sm.add_constant(sub[["sigma_z", gauge_col]])
    y = sub[f"fwd_maxDD_{h}"]
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": h})
    return model, len(sub)


def run(panel, gauge_col="g", gauge_series=None):
    ind, mkt = load_panel(panel)
    internals = build_internals(ind) if gauge_series is None else gauge_series
    sigma = sigma_hat(mkt)

    df = pd.DataFrame(index=internals.index)
    df[gauge_col] = internals[gauge_col] if gauge_col in internals else internals
    df["sigma"] = sigma.reindex(df.index)
    df["sigma_z"] = z_expand(df["sigma"])
    df["mkt_ret"] = mkt.reindex(df.index)

    for h in (60, 20):
        df[f"fwd_maxDD_{h}"] = fwd_maxdd(df["mkt_ret"], h)

    results = {}
    model60_no, n60_no = non_overlapping_regression(df, 60, gauge_col)
    results["primary_60_nonoverlap"] = (model60_no, n60_no)

    model20_no, n20_no = non_overlapping_regression(df, 20, gauge_col)
    results["sensitivity_20_nonoverlap"] = (model20_no, n20_no)

    model60_hac, n60_hac = overlapping_hac_regression(df, 60, gauge_col)
    results["sensitivity_60_overlap_hac"] = (model60_hac, n60_hac)

    return results, df


def report(panel, results):
    print(f"\n=== H1 — panel: {panel} ===")
    for label, (model, n) in results.items():
        b2 = model.params.get("g", model.params.iloc[-1])
        t2 = model.tvalues.get("g", model.tvalues.iloc[-1])
        gate = "PRIMARY/GATING" if label == "primary_60_nonoverlap" else "sensitivity, non-gating"
        print(f"{label} ({gate}): n={n}  beta2(g)={b2:.4f}  t={t2:.2f}  "
              f"signed_ok={b2 < 0}  |t|>2={abs(t2) > 2.0}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", choices=list(PANELS), required=True)
    args = ap.parse_args()
    res, _ = run(args.panel)
    report(args.panel, res)
