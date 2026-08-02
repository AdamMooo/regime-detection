"""Descriptive characterization (NO look, Phase 1-4 discipline per PRODUCT-PLAN.md): does the
proposed gold+trend diversifier layer add a distinct return source to the 48-industry momentum
sleeve, or double up on the same trend/autocorrelation factor?

Prompted by two research findings (2026-08-01):
  - CAIA: trend-following and momentum/factor strategies "had the same performance drivers for
    almost a decade" -> real risk the sleeve and trend proxy are one bet, not two.
  - The trend proxy's own universe (build_trend_proxy.py) already trades GLD via a long/short
    12m-momentum signal -- that is NOT the same exposure as a permanent long-only gold holding,
    so this script checks trend and gold SEPARATELY, not as one bundled "gold+trend" leg.

Reports: full-sample correlation (sleeve vs trend, sleeve vs standalone long gold, trend vs gold),
36-month rolling correlation (does overlap spike specifically in trend-driven episodes, e.g. 2022),
and what trend/gold actually did in the sleeve's own worst months (the only thing that matters for
"does this diversify the sleeve's drawdowns").
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from momentum_breadth import load_industry, buffered_momentum

ROLL_WINDOW = 36  # months


def sleeve_monthly():
    rf = ((1 + pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)["rf"])
          .resample("ME").prod() - 1)
    R = load_industry(48)
    m = (1 + R).resample("ME").prod() - 1
    rfc = rf.reindex(m.index)
    r, _ = buffered_momentum(m, rfc)
    return r.rename("sleeve")


def trend_monthly():
    trend = pd.read_csv(ROOT / "data/processed/trend_proxy_daily.csv", index_col=0, parse_dates=True)["trend_ret"]
    return ((1 + trend).resample("ME").prod() - 1).rename("trend")


def gold_monthly():
    """Standalone long-only gold (GLD), NOT the trend engine's momentum-signal gold leg --
    this is the permanent, unconditional hold the product plan actually proposes."""
    px = pd.read_csv(ROOT / "data/raw/trend_universe_prices.csv", index_col=0, parse_dates=True)["GLD"].dropna()
    ret = px.pct_change().dropna()
    return ((1 + ret).resample("ME").prod() - 1).rename("gold")


def report():
    sleeve = sleeve_monthly()
    trend = trend_monthly()
    gold = gold_monthly()

    df = pd.concat([sleeve, trend, gold], axis=1).dropna()
    print(f"Common sample: {df.index[0].date()} .. {df.index[-1].date()}  n={len(df)} months\n")

    corr = df.corr()
    print("Full-sample correlation matrix:")
    print(corr.round(3).to_string())

    print("\n36-month rolling correlation (sleeve vs trend, sleeve vs gold):")
    roll_st = df["sleeve"].rolling(ROLL_WINDOW).corr(df["trend"])
    roll_sg = df["sleeve"].rolling(ROLL_WINDOW).corr(df["gold"])
    print(f"  sleeve-trend: mean={roll_st.mean():.3f}  max={roll_st.max():.3f}  "
          f"({roll_st.idxmax().date() if roll_st.notna().any() else 'n/a'})")
    print(f"  sleeve-gold:  mean={roll_sg.mean():.3f}  max={roll_sg.max():.3f}  "
          f"({roll_sg.idxmax().date() if roll_sg.notna().any() else 'n/a'})")

    # 2022 window specifically -- the episode that motivated this whole layer
    infl22 = df.loc["2022-01":"2022-12"]
    if len(infl22):
        print(f"\n2022 (the bonds-failed episode), n={len(infl22)} months:")
        print(f"  sleeve cum={((1+infl22['sleeve']).prod()-1):+.1%}  "
              f"trend cum={((1+infl22['trend']).prod()-1):+.1%}  "
              f"gold cum={((1+infl22['gold']).prod()-1):+.1%}")
        print(f"  corr(sleeve,trend) in 2022={infl22['sleeve'].corr(infl22['trend']):.3f}  "
              f"corr(sleeve,gold) in 2022={infl22['sleeve'].corr(infl22['gold']):.3f}")

    # what did trend/gold do in the sleeve's own worst months? (the only thing that
    # actually matters for "does this diversify the sleeve's drawdowns")
    worst = df.nsmallest(10, "sleeve")
    print(f"\nSleeve's 10 worst months -- what trend/gold did concurrently:")
    print(worst.round(4).to_string())
    print(f"\n  mean(trend | sleeve worst-10) = {worst['trend'].mean():+.2%}   "
          f"mean(gold | sleeve worst-10) = {worst['gold'].mean():+.2%}")
    print(f"  fraction of sleeve worst-10 where trend was positive: {(worst['trend']>0).mean():.0%}")
    print(f"  fraction of sleeve worst-10 where gold was positive:  {(worst['gold']>0).mean():.0%}")


if __name__ == "__main__":
    report()
