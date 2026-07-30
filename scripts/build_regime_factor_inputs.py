"""Step 1 of the regime-as-a-factor test (NO look, plumbing only).

Reproduces the FROZEN chapter-1 walk-forward on the French US market panel and additionally
exports the filter's causal evidence margin (return_margin=True), then resamples the daily
label to a monthly regime series aligned to the factor-test panel's month-end dates.

Integrity gate: the daily `state` regenerated here MUST match the frozen results/oos_labels.csv
on their overlap byte-for-byte. If it does not, the frozen protocol was not reproduced and the
build aborts — we never silently ship a different label.

Continuous stress score = m_t = (V_calm - V_stressed)/lam, the filter's normalized accumulated
evidence gap (jumpmodel.filter_states V_path). m_t > 0 => evidence favors stressed. This is the
causal, look-ahead-free stress score §5 of FACTOR-MODEL-DIRECTION calls for.

Outputs:
  data/processed/regime_monthly.csv   date(month-end), state_eom, stress_eom, stress_mean, frac_stressed
  results/regime_factor_inputs_gate.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from jumpmodel import build_features
from run_config import LAMBDA_GRID, N_INIT, REFIT, START, TRAIN0, VAL, DELAY
from walkforward import walk_forward


def build_daily():
    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True).loc[START:]
    r = panel["mkt_ret"]
    F = build_features(r.to_numpy())
    states, _lam, margins = walk_forward(
        r.to_numpy(), F.to_numpy(), burn=63, train0=TRAIN0, refit=REFIT,
        grid=LAMBDA_GRID, val=VAL, n_init=N_INIT, delay=DELAY, return_margin=True)
    daily = pd.DataFrame({"state": states, "margin": margins}, index=r.index)
    return daily.dropna(subset=["state"])


def integrity_check(daily):
    frozen = pd.read_csv(ROOT / "results" / "oos_labels.csv",
                         parse_dates=["date"]).set_index("date")["state"]
    ours = daily["state"].reindex(frozen.index)
    n = int(ours.notna().sum())
    mismatch = int((ours.dropna().astype(int) != frozen.reindex(ours.dropna().index).astype(int)).sum())
    return n, mismatch


def to_monthly(daily):
    d = daily.copy()
    d["state"] = d["state"].astype(int)
    d["stressed"] = (d["state"] == 1).astype(float)
    g = d.resample("ME")
    m = pd.DataFrame({
        "state_eom": g["state"].last(),
        "stress_eom": g["margin"].last(),
        "stress_mean": g["margin"].mean(),
        "frac_stressed": g["stressed"].mean(),
    })
    return m.dropna(subset=["state_eom"])


def main():
    daily = build_daily()
    n, mismatch = integrity_check(daily)
    if mismatch != 0:
        raise SystemExit(f"INTEGRITY FAIL: {mismatch}/{n} daily states differ from frozen oos_labels")

    monthly = to_monthly(daily)

    panel = pd.read_csv(ROOT / "data" / "processed" / "factor_test_monthly.csv",
                        index_col=0, parse_dates=True)
    aligned = monthly.reindex(panel.index).dropna(subset=["state_eom"])

    out = ROOT / "data" / "processed" / "regime_monthly.csv"
    monthly.to_csv(out)

    gate = pd.DataFrame([
        ("daily_overlap_vs_frozen", n),
        ("daily_state_mismatches", mismatch),
        ("monthly_rows", len(monthly)),
        ("monthly_first", monthly.index.min().date()),
        ("monthly_last", monthly.index.max().date()),
        ("aligned_to_panel_rows", len(aligned)),
        ("frac_stressed_overall", round(float((daily['state'] == 1).mean()), 4)),
        ("margin_min", round(float(daily['margin'].min()), 4)),
        ("margin_max", round(float(daily['margin'].max()), 4)),
    ], columns=["check", "value"])
    gate.to_csv(ROOT / "results" / "regime_factor_inputs_gate.csv", index=False)

    print(f"PASS integrity: {n} overlap, {mismatch} mismatch")
    print(gate.to_string(index=False))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
