"""Sensor-v3 data foundation, tier 1: realized cross-sectional return dispersion.

The "sleeper" vol-structure axis (Sensor v3 candidate, 2026-07-24): realized dispersion
across the Ken French cross-section, available on our longest, cleanest history (10
industry portfolios, complete-case 1926-09-17+), needing no external fetch. Cross-sectional
dispersion (Stivers 2003; Garcia, Mantilla-Garcia & Martellini 2014 as an equity-vol proxy)
is a distinct market-structure signal from own-vol and, unlike options-implied series
(VIX 1990+, implied correlation 2021+), spans the full panel.

DATA FOUNDATION + DESCRIPTIVE CHARACTERIZATION ONLY. No economic claim, no backtest, no
look is spent here (cf. atlas.py, state_anatomy.py). The pre-onset lead-lag peek is
hypothesis-generating and US-panel-contaminated: any signal it suggests binds the
out-of-hypothesis-sample rule (international confirmation) before any SUPPORT claim.

Writes data/processed/dispersion_daily.csv + results/dispersion_gate.csv + a run log.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

HALF_LIVES = (10, 20, 60)


def cross_sectional_dispersion(ind_ret):
    """Daily cross-sectional std of industry returns around the cross-sectional mean."""
    xbar = ind_ret.mean(axis=1)
    return np.sqrt(((ind_ret.sub(xbar, axis=0)) ** 2).mean(axis=1)).rename("csd")


def ew_smooth(s, half_life):
    return s.ewm(halflife=half_life, adjust=False).mean()


def build():
    panel = pd.read_csv(ROOT / "data" / "processed" / "assets_daily.csv",
                        index_col=0, parse_dates=True)
    ind_cols = [c for c in panel.columns if c.startswith("ind_")]
    ind = panel[ind_cols].dropna(how="any")

    csd = cross_sectional_dispersion(ind)
    out = pd.DataFrame({"csd": csd})
    for hl in HALF_LIVES:
        out[f"csd_ew{hl}"] = ew_smooth(csd, hl)
    # market own-vol on the same window, for the orthogonality gate
    mkt = panel.loc[csd.index, "mkt_ret"]
    out["mkt_ew20_vol"] = np.sqrt((mkt ** 2).ewm(halflife=20, adjust=False).mean())
    return out.dropna()


def gate(disp):
    g = []
    g.append(("D1_coverage",
              disp.index[0].year <= 1927 and len(disp) > 25000,
              f"{disp.index[0].date()}..{disp.index[-1].date()} n={len(disp)}"))
    csd = disp["csd"]
    g.append(("D2_sane",
              (csd > 0).all() and 0.001 < csd.mean() < 0.05 and csd.isna().sum() == 0,
              f"mean={csd.mean():.4f} min={csd.min():.4f} max={csd.max():.4f} nan={csd.isna().sum()}"))
    # orthogonality: dispersion should co-move with own-vol (both rise in stress) but not be
    # a redundant restatement of it — a distinct axis is the whole point (info-gate).
    corr = disp["csd_ew20"].corr(disp["mkt_ew20_vol"])
    g.append(("D3_distinct_axis", 0.30 <= corr <= 0.90,
              f"corr(csd_ew20, mkt_ew20_vol)={corr:.3f} (want moderate, not redundant)"))
    return pd.DataFrame(g, columns=["gate", "passed", "detail"])


def characterize(disp, log):
    """Descriptive vs the frozen label. Hypothesis-generating, US-contaminated."""
    lab = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"]) \
        .set_index("date")["state"]
    df = disp.join(lab, how="inner").dropna(subset=["state"])
    df["state"] = df["state"].astype(int)

    log.append("\n[DESCRIPTIVE — no look; hypothesis-generating; US-panel-contaminated]")
    log.append(f"overlap with frozen label: {df.index[0].date()}..{df.index[-1].date()} "
               f"n={len(df)}")
    by = df.groupby("state")["csd"].agg(["mean", "median", "std"])
    log.append("csd by state (0=calm, 1=stressed):")
    log.append(by.to_string())
    ratio = by.loc[1, "mean"] / by.loc[0, "mean"]
    log.append(f"stressed/calm mean dispersion ratio: {ratio:.2f}x")

    # Lead-lag probe: is dispersion ELEVATED before a stressed onset (the lag-attack thesis)?
    # onset = first day of each 0->1 transition. Compare csd in the 20d window BEFORE onset
    # (strictly calm-labeled days) to the calm baseline. Purely descriptive.
    st = df["state"].values
    onsets = np.where((st[1:] == 1) & (st[:-1] == 0))[0] + 1
    csd_z = ((df["csd"] - df["csd"].rolling(252, min_periods=60).mean())
             / df["csd"].rolling(252, min_periods=60).std())
    pre = []
    for o in onsets:
        lo = max(0, o - 20)
        w = csd_z.iloc[lo:o]
        if len(w) >= 5:
            pre.append(w.mean())
    calm_base = csd_z[df["state"] == 0].mean()
    log.append(f"\nlead-lag probe: {len(onsets)} stressed onsets; "
               f"mean csd-zscore in 20d BEFORE onset (calm-labeled) = {np.nanmean(pre):+.2f} "
               f"vs calm baseline {calm_base:+.2f}")
    log.append("  (>0 and above baseline => dispersion tends to rise before the label flips "
               "— a lead candidate against the 20d detection lag. DESCRIPTIVE ONLY: needs "
               "international confirmation + a preregistered causal test before any claim.)")


def main():
    log = ["dispersion foundation (Sensor-v3 tier 1) — run log"]
    disp = build()
    disp.to_csv(ROOT / "data" / "processed" / "dispersion_daily.csv")
    g = gate(disp)
    g.to_csv(ROOT / "results" / "dispersion_gate.csv", index=False)
    log.append(g.to_string(index=False))
    log.append(f"\nseries {disp.index[0].date()}..{disp.index[-1].date()} rows={len(disp)} "
               f"cols={list(disp.columns)}")
    passed = g["passed"].all()
    log.append("DISPERSION GATE: " + ("PASS" if passed else "FAIL"))
    try:
        characterize(disp, log)
    except Exception as e:
        log.append(f"[characterize skipped: {e}]")

    text = "\n".join(str(x) for x in log)
    (ROOT / "results" / "dispersion_run.log").write_text(text, encoding="utf-8")
    print(text)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
