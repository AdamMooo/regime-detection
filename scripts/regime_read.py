"""The synthesized human-facing regime READ (instrument QA, NO look, NO timing claim).

Built from ONLY the pieces that survived the literature stress-test:
  - DIRECTION lens (trend): price vs SMA200 — the one genuinely orthogonal axis (leverage /
    down-market effect: Black 1976; French-Schwert-Stambaugh; Patton-Sheppard good/bad vol).
  - TURBULENCE, as DOWNSIDE semivariance (Barndorff-Nielsen et al.; Patton-Sheppard 2015) — the
    "bad vol" that actually drives forward risk — as a CONTINUOUS causal percentile severity
    (not a naive count of thresholded detectors, per the CISS/PCA critique).
  - The JUMP-MODEL label as the STABLE anchor for "are we in a confirmed regime" (its documented
    value is stability, not detection — so it flags the durable regime, severity grades it).

The read a human gets = quadrant (calm/stress x up/down) + a continuous severity + the historical
base rate for that state + nearest historical analogs. Descriptive communication only.

Prints the latest read + sanity-check reads for known episodes. Writes results/regime_read_latest.json.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def build():
    panel = pd.read_csv(ROOT / "data/processed/market_daily.csv", index_col=0,
                        parse_dates=True).loc["1970-01-01":]
    labels = pd.read_csv(ROOT / "results/oos_labels.csv", parse_dates=["date"]).set_index("date")
    r = panel["mkt_ret"]
    px = (1.0 + r).cumprod()

    # turbulence = annualized 21d DOWNSIDE semivol (bad vol), as a causal expanding percentile
    semivar = (np.minimum(r, 0.0) ** 2).rolling(21).mean()
    dsv = np.sqrt(semivar) * np.sqrt(252)
    turb_pct = dsv.expanding(min_periods=252).apply(lambda x: (x <= x.iloc[-1]).mean(), raw=False)

    trend_down = (px < px.rolling(200).mean())
    jm = pd.Series(np.nan, index=panel.index)
    jm.loc[labels.index] = labels["state"].values

    fwd_vol = r.rolling(21).std().shift(-21) * np.sqrt(252)

    df = pd.DataFrame({"dsvol": dsv, "turb_pct": turb_pct, "trend_down": trend_down.astype(float),
                       "jm": jm, "fwd_vol": fwd_vol, "ret": r})
    return df.dropna(subset=["turb_pct", "jm"])


def severity_label(p):
    return ("EXTREME" if p >= 0.95 else "HIGH" if p >= 0.80 else
            "ELEVATED" if p >= 0.60 else "NORMAL" if p >= 0.30 else "LOW")


def quadrant(jm, down):
    if jm == 1 and down:
        return "CONFIRMED BEAR (stress + downtrend)"
    if jm == 1 and not down:
        return "SHAKEOUT (stress + uptrend)"
    if jm == 0 and down:
        return "GRIND (calm + downtrend)"
    return "BENIGN (calm + uptrend)"


def read_on(df, date):
    row = df.loc[date]
    jm, down, p = int(row["jm"]), bool(row["trend_down"]), float(row["turb_pct"])
    quad = quadrant(jm, down)
    # base rate: forward 21d vol historically for this quadrant (context, not a forecast)
    same = df[(df["jm"] == jm) & (df["trend_down"] == row["trend_down"])]
    base_fwd = float(same["fwd_vol"].mean())
    # nearest analogs: same quadrant, closest turbulence percentile, distinct years
    cand = same.assign(dist=(same["turb_pct"] - p).abs()).sort_values("dist")
    yrs, seen = [], set()
    for d in cand.index:
        if d.year not in seen and abs((d - date).days) > 180:
            yrs.append(d.year); seen.add(d.year)
        if len(yrs) == 3:
            break
    return dict(date=str(date.date()), quadrant=quad, severity=severity_label(p),
                turbulence_pctile=round(p, 2), downside_vol_ann=round(float(row["dsvol"]), 3),
                jm_state=jm, trend="down" if down else "up",
                base_rate_fwd_vol=round(base_fwd, 3), historical_analogs=yrs)


def line(rd):
    return (f"{rd['date']}  {rd['quadrant']}  |  severity {rd['severity']} "
            f"({rd['turbulence_pctile']:.0%} turb)  |  hist. fwd-vol for this state "
            f"~{rd['base_rate_fwd_vol']:.0%}  |  looks like: {rd['historical_analogs']}")


def main():
    df = build()
    print("=" * 92)
    print("REGIME READ — latest")
    print("=" * 92)
    latest = read_on(df, df.index[-1])
    print(line(latest))
    (ROOT / "results/regime_read_latest.json").write_text(json.dumps(latest, indent=2))

    print("\nSANITY — known episodes:")
    for label, d in [("2008 GFC (Oct)", "2008-10-15"), ("2018 Q4 selloff", "2018-12-20"),
                     ("2020 COVID", "2020-03-20"), ("2022 bear", "2022-06-16"),
                     ("2017 calm bull", "2017-06-15")]:
        d = pd.Timestamp(d)
        near = df.index[df.index.get_indexer([d], method="nearest")[0]]
        print(f"  {label:20} {line(read_on(df, near))}")
    print("\nwrote results/regime_read_latest.json")


if __name__ == "__main__":
    main()
