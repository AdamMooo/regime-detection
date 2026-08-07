"""Track-1 sensor validation (descriptive diagnostics — no economic claim, no prereg needed).

(1) Benchmarks the frozen chapter-1 OOS bear labels (results/oos_labels.csv) against ex-post
bull/bear datings a la Lunde-Timmermann (2004): threshold dating on the cumulative total-return
index, phases backdated to their peak/trough turning points (ground truth is allowed to use the
future; the sensor is not). Variants: 20%/20% and 15%/15%.
(2) Characterizes the two states statistically on OOS days.

Writes results/sensor_validation.csv; prints the report.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def lunde_timmermann(prices, threshold):
    """Ex-post phase labels (0 bull / 1 bear), phases backdated to turning points."""
    p = np.asarray(prices, dtype=float)
    n = len(p)
    phase = np.zeros(n, dtype=int)
    turning = []
    bull = True
    ext_i = 0  # index of running peak (bull) or trough (bear)
    for t in range(1, n):
        if bull:
            if p[t] > p[ext_i]:
                ext_i = t
            elif p[t] <= p[ext_i] * (1.0 - threshold):
                turning.append(("peak", ext_i))
                bull = False
                ext_i = t
        else:
            if p[t] < p[ext_i]:
                ext_i = t
            elif p[t] >= p[ext_i] * (1.0 + threshold):
                turning.append(("trough", ext_i))
                bull = True
                ext_i = t
    for kind, i in turning:
        if kind == "peak":
            phase[i + 1:] = 1
        else:
            phase[i + 1:] = 0
    return phase, turning


def main():
    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True).loc["1970-01-01":]
    labels = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"])
    r = panel["mkt_ret"]
    px = (1.0 + r).cumprod()

    oos_mask = panel.index.isin(labels["date"])
    s = pd.Series(-1, index=panel.index)
    s.loc[labels["date"].values] = labels["state"].values

    rows = []
    print("=" * 72)
    print("SENSOR VALIDATION — jump-model bear label vs ex-post LT datings")
    print("=" * 72)
    for thr in (0.20, 0.15):
        phase, turning = lunde_timmermann(px.to_numpy(), thr)
        lt = pd.Series(phase, index=panel.index)
        both = oos_mask & (s.to_numpy() >= 0)
        ours = s[both].to_numpy()
        truth = lt[both].to_numpy()
        tp = int(((ours == 1) & (truth == 1)).sum())
        prec = tp / max((ours == 1).sum(), 1)
        rec = tp / max((truth == 1).sum(), 1)
        bac = (((ours == truth)[truth == 0]).mean() + ((ours == truth)[truth == 1]).mean()) / 2
        # per-LT-bear-episode coverage + detection lag from the (ex-post) peak
        idx = panel.index[both]
        lt_o = pd.Series(truth, index=idx)
        s_o = pd.Series(ours, index=idx)
        episodes = []
        in_b = False
        for i, (d, v) in enumerate(lt_o.items()):
            if v == 1 and not in_b:
                in_b, start = True, d
            elif v == 0 and in_b:
                in_b = False
                episodes.append((start, prev_d))
            prev_d = d
        if in_b:
            episodes.append((start, prev_d))
        ep_stats = []
        for a, b in episodes:
            seg = s_o.loc[a:b]
            cov = float((seg == 1).mean())
            flagged = seg[seg == 1]
            lag = (flagged.index[0] - a).days if len(flagged) else None
            ep_stats.append((a.date(), b.date(), len(seg), round(cov, 2), lag))
        lags = [e[4] for e in ep_stats if e[4] is not None]
        print(f"\nLT {int(thr*100)}%: bear days {int((truth == 1).sum())} of {len(truth)} OOS | "
              f"precision {prec:.2f}  recall {rec:.2f}  BAC {bac:.3f}")
        print(f"  LT bear episodes in OOS: {len(ep_stats)}; detected (coverage>0): "
              f"{sum(1 for e in ep_stats if e[3] > 0)}; "
              f"median lag from ex-post peak: {np.median(lags) if lags else float('nan'):.0f} days")
        for e in ep_stats:
            print(f"    {e[0]} .. {e[1]}  ({e[2]}d)  coverage={e[3]:.2f}  lag={e[4]}d")
        rows.append(dict(variant=f"LT{int(thr*100)}", precision=round(prec, 3),
                         recall=round(rec, 3), bac=round(bac, 3),
                         episodes=len(ep_stats),
                         detected=sum(1 for e in ep_stats if e[3] > 0),
                         median_lag_days=float(np.median(lags)) if lags else np.nan))

    # ---- state characterization on OOS days ----
    both = oos_mask & (s.to_numpy() >= 0)
    r_o = r[both]
    s_o = s[both]
    print("\nSTATE CHARACTERIZATION (OOS days, causally labeled)")
    hdr = f"{'':14}{'ann ret':>9}{'ann vol':>9}{'sharpe':>8}{'skew':>7}{'kurt':>7}{'worst d':>9}{'days':>7}"
    print(hdr)
    for st, name in [(0, "calm/bull"), (1, "stressed")]:
        rr = r_o[s_o == st]
        ann = rr.mean() * 252
        vol = rr.std() * np.sqrt(252)
        print(f"{name:14}{ann:9.2%}{vol:9.2%}{ann / vol:8.2f}{rr.skew():7.2f}"
              f"{rr.kurtosis():7.1f}{rr.min():9.2%}{len(rr):7d}")
        rows.append(dict(variant=f"state_{name}", ann_ret=round(float(ann), 4),
                         ann_vol=round(float(vol), 4), sharpe=round(float(ann / vol), 3),
                         skew=round(float(rr.skew()), 3), kurt=round(float(rr.kurtosis()), 2),
                         worst_day=round(float(rr.min()), 4), days=int(len(rr))))
    trans = pd.crosstab(s_o.shift(), s_o, normalize="index")
    print(f"\npersistence: P(stay calm)={trans.loc[0, 0]:.4f}  P(stay stressed)={trans.loc[1, 1]:.4f}")
    dwell = s_o.groupby((s_o != s_o.shift()).cumsum()).agg(["first", "size"])
    for st, name in [(0, "calm"), (1, "stressed")]:
        d = dwell[dwell["first"] == st]["size"]
        print(f"dwell {name}: mean {d.mean():.0f}d  median {d.median():.0f}d  "
              f"min {d.min()}d  max {d.max()}d  n={len(d)}")

    pd.DataFrame(rows).to_csv(ROOT / "results" / "sensor_validation.csv", index=False)
    print("\nwrote results/sensor_validation.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
