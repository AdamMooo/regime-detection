"""Variant of build_trend_proxy.py testing a CONFIDENCE DEAD-ZONE refinement (Adam's direction,
2026-08-01): rather than always committing to sign(12m momentum) long or short, go FLAT (0)
whenever the momentum signal isn't statistically distinguishable from noise. Motivated by a
concrete failure found in the original proxy: gold's Nov 2008 short position (a real, sign()-
driven directional bet after the Oct crash) missed a +12.6% rebound, and self-timed gold NET
LOST MORE than a static long hold over Aug-Dec 2008 (-5.5% vs -4.0%) once that whipsaw is
included. A dead-zone version of just the gold leg, tested standalone, recovered to -2.4% by
sitting out Sep-Dec entirely (momentum genuinely ambiguous after the vol spike).

This script generalizes that dead-zone rule to the FULL trend universe (not just gold) and reruns
the same validation gate as the original, so the refinement is judged broadly, not on one
cherry-picked episode. NO look / no economic claim — this is instrument characterization
(Phase 1-4 discipline, PRODUCT-PLAN.md), a candidate refinement to an already-gated tool, not a
new preregistered hypothesis.

Dead-zone rule: take a position only if |12m cumulative return| exceeds one trailing-vol-implied
"noise band" for a 12-month horizon (daily vol * sqrt(mom_lookback)) -- i.e. only when the trend
is bigger than what pure random-walk noise at that asset's own volatility would produce. Otherwise
flat. Same inverse-vol sizing and leverage cap as the original when a position IS taken.

Writes data/processed/trend_proxy_deadzone_daily.csv + results/trend_proxy_deadzone_gate.csv --
does NOT touch the original trend_proxy_daily.csv / trend_proxy_gate.csv (already gated, kept).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_trend_proxy import (
    load_prices, UNIVERSE, VALIDATION, MOM_LB, VOL_LB,
    TARGET_INST_VOL, TARGET_PORT_VOL, LEV_CAP, PORT_VOL_LB,
)


def build_proxy_deadzone(px):
    mkts = list(UNIVERSE)
    prices = px[mkts]
    rets = prices.pct_change()
    month_ends = prices.resample("ME").last().index

    pos_me = pd.DataFrame(index=month_ends, columns=mkts, dtype=float)
    for me in month_ends:
        hist = prices.loc[:me]
        if len(hist) < MOM_LB + 1:
            continue
        for m in mkts:
            s = hist[m].dropna()
            if len(s) < MOM_LB + 1:
                continue
            mom = s.iloc[-1] / s.iloc[-1 - MOM_LB] - 1.0
            daily_vol = rets[m].loc[:me].dropna().iloc[-VOL_LB:].std()
            if not np.isfinite(daily_vol) or daily_vol <= 0:
                continue
            ann_vol = daily_vol * np.sqrt(252)
            noise_band = daily_vol * np.sqrt(MOM_LB)  # 12m random-walk noise band
            if abs(mom) < noise_band:
                pos_me.loc[me, m] = 0.0  # dead zone: signal not distinguishable from noise
            else:
                pos_me.loc[me, m] = np.sign(mom) * min(TARGET_INST_VOL / ann_vol, LEV_CAP)

    pos_daily = pos_me.reindex(prices.index, method="ffill").shift(1)
    contrib = pos_daily * rets
    raw = contrib.mean(axis=1, skipna=True)
    raw = raw.dropna()

    pvol = raw.rolling(PORT_VOL_LB).std().shift(1) * np.sqrt(252)
    scaler = (TARGET_PORT_VOL / pvol).clip(upper=3.0)
    trend = (raw * scaler).dropna()
    n_active = pos_daily.notna().sum(axis=1).reindex(trend.index)
    n_flat = (pos_daily == 0.0).sum(axis=1).reindex(trend.index)
    return trend.rename("trend_ret"), n_active, n_flat


def main():
    px = load_prices()
    trend, n_active, n_flat = build_proxy_deadzone(px)
    ann_vol = trend.std() * np.sqrt(252)
    ann_ret = trend.mean() * 252
    print(f"deadzone proxy {trend.index[0].date()}..{trend.index[-1].date()}  n={len(trend)}")
    print(f"  markets active: median {int(n_active.median())}  "
          f"(median in dead-zone/flat: {int(n_flat.median())})")
    print(f"  annualized: ret {ann_ret:+.2%}  vol {ann_vol:.2%}  Sharpe {ann_ret/ann_vol:.2f}")

    tm = (1 + trend).resample("ME").prod() - 1
    gate = []
    for v in VALIDATION:
        vr = px[v].dropna().pct_change()
        vm = (1 + vr).resample("ME").prod() - 1
        both = pd.DataFrame({"proxy": tm, v.lower(): vm}).dropna()
        c = both["proxy"].corr(both[v.lower()])
        print(f"  corr(deadzone_proxy, {v}) = {c:.3f}  (n={len(both)} months)")
        if v == "DBMF":
            dbmf_c = c

    infl22 = trend.loc["2022-01-19":"2023-01-10"]
    cum22 = (1 + infl22).prod() - 1
    print(f"  2022 crisis cumulative: {cum22:+.1%}")

    # the episode that motivated this whole variant
    crash08 = trend.loc["2008-08-01":"2008-12-31"]
    print(f"  Aug-Dec 2008 cumulative: {(1+crash08).prod()-1:+.1%}")

    gate.append(("G1_dbmf_corr", dbmf_c >= 0.50, f"corr={dbmf_c:.3f} (bar 0.50)"))
    gate.append(("G2_vol_sane", 0.05 <= ann_vol <= 0.15, f"ann_vol={ann_vol:.2%} (target ~10%)"))
    gate.append(("G3_crisis_alpha_2022", cum22 > 0, f"2022 cum={cum22:+.1%} (>0 expected)"))
    res = pd.DataFrame(gate, columns=["gate", "passed", "detail"])

    out = pd.DataFrame({"trend_ret": trend, "n_active": n_active, "n_flat": n_flat})
    out.to_csv(ROOT / "data" / "processed" / "trend_proxy_deadzone_daily.csv")
    res.to_csv(ROOT / "results" / "trend_proxy_deadzone_gate.csv", index=False)
    print("\n" + res.to_string(index=False))
    print("\nDEAD-ZONE TREND PROXY GATE:", "PASS" if res["passed"].all() else "FAIL")

    # direct comparison vs the original (already-gated) proxy
    orig = pd.read_csv(ROOT / "data" / "processed" / "trend_proxy_daily.csv",
                        index_col=0, parse_dates=True)["trend_ret"]
    both = pd.DataFrame({"deadzone": trend, "original": orig}).dropna()
    print(f"\ncorr(deadzone, original) = {both['deadzone'].corr(both['original']):.3f}")
    print(f"Sharpe: deadzone={both['deadzone'].mean()/both['deadzone'].std()*np.sqrt(252):.2f}  "
          f"original={both['original'].mean()/both['original'].std()*np.sqrt(252):.2f}")
    print(f"Ann ret: deadzone={both['deadzone'].mean()*252:+.2%}  "
          f"original={both['original'].mean()*252:+.2%}")
    from run_config import maxdd
    print(f"Max DD: deadzone={maxdd(both['deadzone']):.1%}  original={maxdd(both['original']):.1%}")

    return 0 if res["passed"].all() else 1


if __name__ == "__main__":
    sys.exit(main())
