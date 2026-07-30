"""Detector skill benchmark (NO look — instrument QA): does the jump model beat a DUMB baseline?

The project's paper to-do (NOTES) flags the core unargued weakness: "stability 1.000" is meaningless
without a skill number, because a CONSTANT is also perfectly stable. So the load-bearing question is
not "add a feature" but "does the sophisticated JM detector actually beat a deterministic vol-threshold
rule?" You cannot claim ANY detector improvement until this baseline exists.

BASELINE (deterministic, causal, parameter-free after exposure-matching): trailing realized vol
(rolling 20d std of returns, uses data through day t only) → flag stressed when vol_t exceeds an
EXPANDING-window quantile calibrated so the baseline's stressed-fraction matches the JM's on the same
days (exposure-matched, per the repo's mandatory exposure-control discipline — otherwise a detector
that just flags more days "wins" on recall for free).

Compared head-to-head vs ex-post Lunde-Timmermann bear datings (ground truth may use the future; both
detectors are causal): precision / recall / BAC, per-episode detection + median lag from the ex-post
peak, and switches/yr (the stability proxy). Two clean outcomes: JM wins => the sophistication is
finally argued; threshold matches it => the sophistication is unjustified and THAT is the finding.

Writes results/detector_benchmark.csv; prints the report. No economic/return claim; not look-gated.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_sensor import lunde_timmermann


def deterministic_baseline(r, target_frac, calib_mask, vol_win=20):
    """Causal vol-threshold detector, EXPOSURE-MATCHED to target_frac stressed days on the comparison
    window. vol_t = trailing rolling-std of returns through t (causal signal); the single scalar
    threshold = the (1-target_frac) quantile of vol over calib_mask so the realized stressed-fraction
    equals target_frac exactly (a fixed exposure knob, not a timing signal — the repo's standard
    exposure-matched-control construction). Returns a 0/1 Series aligned to r."""
    vol = r.rolling(vol_win).std()
    thr = float(vol[calib_mask].quantile(1.0 - target_frac))
    state = (vol > thr).astype(float)
    state[vol.isna()] = np.nan
    return state


def persistence_filter(state, k):
    """Hysteresis: flip to a new state only after k consecutive days of raw signal agreeing.
    Buys stability back from a twitchy threshold rule. NaN raw days pass through as NaN."""
    s = state.to_numpy(dtype=float)
    out = np.full(len(s), np.nan)
    cur = None
    run_val, run_len = None, 0
    for i, v in enumerate(s):
        if np.isnan(v):
            out[i] = cur if cur is not None else np.nan
            run_val, run_len = None, 0
            continue
        if v == run_val:
            run_len += 1
        else:
            run_val, run_len = v, 1
        if cur is None:
            cur = v
        elif run_len >= k and v != cur:
            cur = v
        out[i] = cur
    return pd.Series(out, index=state.index)


def skill(label, truth, index):
    """precision/recall/BAC + per-episode detection & median lag + switches/yr for a causal 0/1
    label vs ex-post phase truth (both aligned to `index`). NaN label days are dropped."""
    lab = pd.Series(label, index=index)
    tr = pd.Series(truth, index=index)
    ok = lab.notna()
    lab, tr, idx = lab[ok].astype(int), tr[ok].astype(int), index[ok]
    a, t = lab.to_numpy(), tr.to_numpy()
    tp = int(((a == 1) & (t == 1)).sum())
    prec = tp / max((a == 1).sum(), 1)
    rec = tp / max((t == 1).sum(), 1)
    bac = (((a == t)[t == 0]).mean() + ((a == t)[t == 1]).mean()) / 2

    # per-LT-bear-episode coverage + lag from ex-post peak
    lt_o = pd.Series(t, index=idx)
    s_o = pd.Series(a, index=idx)
    episodes, in_b, prev_d, start = [], False, idx[0], idx[0]
    for d, v in lt_o.items():
        if v == 1 and not in_b:
            in_b, start = True, d
        elif v == 0 and in_b:
            in_b = False
            episodes.append((start, prev_d))
        prev_d = d
    if in_b:
        episodes.append((start, prev_d))
    lags, detected = [], 0
    for aa, bb in episodes:
        seg = s_o.loc[aa:bb]
        flagged = seg[seg == 1]
        if len(flagged):
            detected += 1
            lags.append((flagged.index[0] - aa).days)
    years = (idx[-1] - idx[0]).days / 365.25
    switches = int((s_o.to_numpy()[1:] != s_o.to_numpy()[:-1]).sum())
    return dict(precision=round(prec, 3), recall=round(rec, 3), bac=round(bac, 3),
                episodes=len(episodes), detected=detected,
                median_lag_days=float(np.median(lags)) if lags else np.nan,
                switches_per_yr=round(switches / years, 2), stressed_frac=round(float(lab.mean()), 3))


def main():
    panel = pd.read_csv(ROOT / "data/processed/market_daily.csv", index_col=0,
                        parse_dates=True).loc["1970-01-01":]
    labels = pd.read_csv(ROOT / "results/oos_labels.csv", parse_dates=["date"]).set_index("date")
    r = panel["mkt_ret"]
    px = (1.0 + r).cumprod()

    jm = pd.Series(np.nan, index=panel.index)
    jm.loc[labels.index] = labels["state"].values
    target_frac = float(jm.dropna().mean())                 # JM stressed fraction (the match target)
    oos = jm.notna()                                         # compare only where the JM label exists
    base = deterministic_baseline(r, target_frac, calib_mask=oos.to_numpy())
    base_h3 = persistence_filter(base, 3)
    base_h5 = persistence_filter(base, 5)
    idx = panel.index[oos]
    detectors = [("jump_model", jm[oos].to_numpy()),
                 ("vol_threshold", base[oos].to_numpy()),
                 ("vol_thr_hyst3", base_h3[oos].to_numpy()),
                 ("vol_thr_hyst5", base_h5[oos].to_numpy())]

    rows = []
    print("=" * 74)
    print(f"DETECTOR BENCHMARK — JM vs deterministic vol-threshold (exposure-matched {target_frac:.1%})")
    print("=" * 74)
    for thr in (0.20, 0.15):
        phase, _ = lunde_timmermann(px.to_numpy(), thr)
        truth = pd.Series(phase, index=panel.index)[oos].to_numpy()
        for name, lab in detectors:
            m = skill(lab, truth, idx)
            m.update(variant=f"LT{int(thr*100)}", detector=name)
            rows.append(m)
            print(f"\nLT{int(thr*100)} {name:14} prec {m['precision']:.2f} recall {m['recall']:.2f} "
                  f"BAC {m['bac']:.3f} | episodes {m['detected']}/{m['episodes']} "
                  f"median-lag {m['median_lag_days']:.0f}d | switches/yr {m['switches_per_yr']} "
                  f"| stressed {m['stressed_frac']:.1%}")

    out = pd.DataFrame(rows)[["variant", "detector", "precision", "recall", "bac", "episodes",
                              "detected", "median_lag_days", "switches_per_yr", "stressed_frac"]]
    out.to_csv(ROOT / "results/detector_benchmark.csv", index=False)
    print("\nwrote results/detector_benchmark.csv")


if __name__ == "__main__":
    main()
