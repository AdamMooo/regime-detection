"""H2 — event study (prereg S5 co-primary). Does the gauge elevate ahead of large
drawdowns, and earlier than sigma_hat does, while staying quiet in healthy markets?

Episode set: the 5 largest peak-to-trough drawdowns in the sample, found mechanically
by magnitude (not by name) to avoid cherry-picking (S5).

Usage: python internals_h2.py --panel {us,japan,europe}
"""

import argparse

import numpy as np
import pandas as pd

from internals_gauge import build_internals, sigma_hat, z_expand
from internals_h1 import load_panel, fwd_maxdd


def find_drawdown_episodes(mkt_ret, n=5):
    """Mechanically identify the n largest peak-to-trough drawdown episodes.
    Returns list of dicts: peak_date, trough_date, depth."""
    eq = (1.0 + mkt_ret).cumprod()
    running_peak = eq.cummax()
    dd = eq / running_peak - 1.0

    episodes = []
    remaining = dd.copy()
    for _ in range(n):
        if remaining.isna().all() or remaining.min() >= 0:
            break
        trough_date = remaining.idxmin()
        depth = remaining.loc[trough_date]
        # peak = last date before trough where eq == running_peak at that trough's peak level
        peak_level = running_peak.loc[trough_date]
        pre_trough = eq.loc[:trough_date]
        peak_date = pre_trough[pre_trough == peak_level].index.max()
        # find recovery date (when eq first regains peak_level after trough), else series end
        post_trough = eq.loc[trough_date:]
        recovered = post_trough[post_trough >= peak_level]
        end_date = recovered.index.min() if len(recovered) else mkt_ret.index.max()

        episodes.append(dict(peak_date=peak_date, trough_date=trough_date,
                              end_date=end_date, depth=depth))
        # blank out this episode's span so the next-largest episode is found elsewhere
        remaining.loc[peak_date:end_date] = 0.0

    episodes.sort(key=lambda e: e["depth"])  # deepest first
    return episodes


def first_crossing(series, pctile_series, onset_date, lookback_days=252):
    """First date, in the lookback window before onset_date, where series
    crosses above its own trailing 80th percentile. Returns None if no crossing."""
    window = series.loc[:onset_date].iloc[-lookback_days:]
    thresh = pctile_series.loc[:onset_date].iloc[-lookback_days:]
    crossed = window[window > thresh]
    return crossed.index.min() if len(crossed) else None


def run(panel, lookback_days=252, pctile=0.80):
    ind, mkt = load_panel(panel)
    internals = build_internals(ind)
    sigma = sigma_hat(mkt)

    df = pd.DataFrame(index=internals.index)
    df["g"] = internals["g"]
    df["sigma"] = sigma.reindex(df.index)
    df = df.dropna()

    g_thresh = df["g"].expanding(min_periods=lookback_days).quantile(pctile)
    sig_thresh = df["sigma"].expanding(min_periods=lookback_days).quantile(pctile)

    episodes = find_drawdown_episodes(mkt.reindex(df.index).dropna(), n=5)

    rows = []
    for ep in episodes:
        onset = ep["peak_date"]
        g_cross = first_crossing(df["g"], g_thresh, onset, lookback_days)
        sig_cross = first_crossing(df["sigma"], sig_thresh, onset, lookback_days)

        g_lead = (onset - g_cross).days if g_cross is not None else None
        sig_lead = (onset - sig_cross).days if sig_cross is not None else None
        gauge_leads = (g_lead is not None) and (sig_lead is None or g_lead > sig_lead)

        pre60 = df["g"].loc[:onset].iloc[-60:]
        median_elevated = pre60.median() > df["g"].median()

        rows.append(dict(peak=onset, trough=ep["trough_date"], depth=ep["depth"],
                          g_cross=g_cross, sigma_cross=sig_cross,
                          g_lead_days=g_lead, sigma_lead_days=sig_lead,
                          gauge_leads_vol=gauge_leads,
                          pre60d_median_elevated=median_elevated))

    result = pd.DataFrame(rows)

    # false-alarm rate: g-threshold crossings not followed by a top-decile fwd-60d
    # drawdown (specificity check, S5) — a gauge always elevated is worthless.
    fwd60 = fwd_maxdd(mkt.reindex(df.index).dropna(), 60).reindex(df.index)
    decile_cut = fwd60.quantile(0.10)  # most negative decile = worst drawdowns
    is_crossing = (df["g"] > g_thresh) & (df["g"].shift(1) <= g_thresh.shift(1))
    crossings = df.index[is_crossing]
    followed_by_bad_dd = fwd60.loc[crossings] <= decile_cut
    false_alarm_rate = float(1.0 - followed_by_bad_dd.mean()) if len(crossings) else float("nan")

    return result, df, dict(n_crossings=len(crossings), false_alarm_rate=false_alarm_rate)


def report(panel, result, extra):
    print(f"\n=== H2 event study — panel: {panel} ===")
    print(result.to_string(index=False))
    n_lead = result["gauge_leads_vol"].sum() if len(result) else 0
    n_elevated = result["pre60d_median_elevated"].sum() if len(result) else 0
    print(f"\nGauge leads sigma_hat in {n_lead}/{len(result)} episodes "
          f"(SUPPORT bar: >=3/5). Pre-onset elevation in {n_elevated}/{len(result)}.")
    print(f"Threshold crossings: {extra['n_crossings']}  "
          f"false-alarm rate: {extra['false_alarm_rate']:.2%}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", choices=["us", "japan", "europe"], required=True)
    args = ap.parse_args()
    res, _, extra = run(args.panel)
    report(args.panel, res, extra)
