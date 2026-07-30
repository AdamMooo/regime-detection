"""Regime PANEL characterization (NO look — instrument QA, human-facing-tool work).

Not one label — a panel of regime views across TIMESCALE and LENS, where the product is how they
AGREE and DIVERGE. This is the honest way to make the human-facing read richer WITHOUT falling into
the timing trap (Ch1/Ch2/Path-B all closed): consensus + divergence is a confidence/severity
communication instrument, NOT a trade trigger.

Panel:
  vol_fast  short-window (10d) realized-vol threshold, no persistence  -> reacts in days (cries wolf)
  vol_med   20d threshold + 5d hysteresis                              -> weeks
  vol_slow  the frozen jump-model label (oos_labels)                   -> the stable anchor
  trend     market direction: price < SMA200 => downtrend (a DIFFERENT lens, not just a slower vol)

Across timescale (vol_fast/med/slow) everything is the vol axis (they are correlated by construction —
"everything collapses onto vol"), so their RELATIONSHIP is a term-structure of stress / early-warning,
not new information. Across LENS (turbulence vs direction) you get a genuine 2x2 the vol axis can't give.

Characterizes (descriptive, no return/timing claim):
  1. agreement + LEAD-LAG: does vol_fast lead vol_slow at stress onsets, and by how many days?
  2. CONSENSUS count (0..3 vol models stressed) vs forward realized vol -> is the severity gradient real?
  3. the vol x trend 2x2 quadrant: occupancy + forward realized vol + example historical episodes.

Writes results/regime_panel.csv; prints the report.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from benchmark_detector import deterministic_baseline, persistence_filter


def onsets(state):
    """Indices where a 0/1 series transitions 0->1."""
    s = state.fillna(0).to_numpy()
    return np.where((s[1:] == 1) & (s[:-1] == 0))[0] + 1


def lead_lag(fast, slow, index, window=60):
    """For each slow-model stress onset, days since the nearest preceding fast onset within `window`.
    Positive median => fast leads slow (early warning)."""
    fo = index[onsets(fast)]
    so = index[onsets(slow)]
    leads = []
    for d in so:
        prior = fo[(fo <= d) & (fo >= d - pd.Timedelta(days=window))]
        if len(prior):
            leads.append((d - prior[-1]).days)
    return leads


def main():
    panel = pd.read_csv(ROOT / "data/processed/market_daily.csv", index_col=0,
                        parse_dates=True).loc["1970-01-01":]
    labels = pd.read_csv(ROOT / "results/oos_labels.csv", parse_dates=["date"]).set_index("date")
    r = panel["mkt_ret"]
    px = (1.0 + r).cumprod()

    jm = pd.Series(np.nan, index=panel.index)
    jm.loc[labels.index] = labels["state"].values
    oos = jm.notna()
    tf = float(jm.dropna().mean())

    vol_fast = deterministic_baseline(r, tf, calib_mask=oos.to_numpy(), vol_win=10)
    vol_med = persistence_filter(deterministic_baseline(r, tf, calib_mask=oos.to_numpy(), vol_win=20), 5)
    vol_slow = jm
    sma200 = px.rolling(200).mean()
    trend_down = (px < sma200).astype(float)               # 1 = downtrend lens

    fwd_vol = r.rolling(21).std().shift(-21) * np.sqrt(252)  # forward 21d realized vol (annualized)

    # restrict to OOS window where all views exist
    m = oos & vol_fast.notna() & vol_med.notna() & trend_down.notna()
    idx = panel.index[m]
    vf, vm, vs, td = vol_fast[m], vol_med[m], vol_slow[m], trend_down[m]
    fv = fwd_vol[m]

    rows = []
    print("=" * 74)
    print("REGIME PANEL — timescale (fast/med/slow vol) + lens (trend direction)")
    print("=" * 74)

    # 1. lead-lag
    leads = lead_lag(vf, vs, idx)
    print(f"\n[1] LEAD-LAG (fast vol -> slow JM stress onsets, n={len(leads)}): "
          f"median {np.median(leads):.0f}d  mean {np.mean(leads):.0f}d  "
          f"(fast leads slow => early-warning value)")
    agree = float((vf.to_numpy() == vs.to_numpy()).mean())
    print(f"    fast/slow agreement: {agree:.1%} of days")
    rows.append(dict(metric="fast_leads_slow_median_days", value=round(float(np.median(leads)), 1)))
    rows.append(dict(metric="fast_slow_agreement", value=round(agree, 3)))

    # 2. consensus count vs forward vol (severity gradient)
    consensus = (vf + vm + vs).astype(int)
    print("\n[2] CONSENSUS (# of 3 vol models stressed) vs forward 21d realized vol:")
    for c in range(4):
        sel = consensus == c
        print(f"    {c}/3 stressed: {sel.mean():5.1%} of days   fwd-vol {fv[sel].mean():.1%}   "
              f"days={int(sel.sum())}")
        rows.append(dict(metric=f"consensus{c}_fwdvol", value=round(float(fv[sel].mean()), 4),
                         frac=round(float(sel.mean()), 3)))

    # 3. vol x trend 2x2 quadrant
    print("\n[3] QUADRANT  vol-state (slow JM) x trend (SMA200):")
    names = {(0, 0): "benign (calm+up)", (1, 0): "shakeout (stress+up)",
             (0, 1): "grind (calm+down)", (1, 1): "confirmed bear (stress+down)"}
    for v in (0, 1):
        for t in (0, 1):
            sel = (vs == v) & (td == t)
            if sel.sum() == 0:
                continue
            eps = idx[sel]
            yrs = sorted({d.year for d in eps})
            span = f"{yrs[0]}..{yrs[-1]}" if yrs else "-"
            print(f"    {names[(v,t)]:28} {sel.mean():5.1%} of days  fwd-vol {fv[sel].mean():.1%}  "
                  f"worst-day {r[m][sel].min():.1%}  yrs {span}")
            rows.append(dict(metric=names[(v, t)], value=round(float(fv[sel].mean()), 4),
                             frac=round(float(sel.mean()), 3)))

    pd.DataFrame(rows).to_csv(ROOT / "results/regime_panel.csv", index=False)
    print("\nwrote results/regime_panel.csv")


if __name__ == "__main__":
    main()
