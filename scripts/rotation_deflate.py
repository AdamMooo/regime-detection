"""Deflation tests for the too-good-looking timed_hot_on (descriptive, no look).

'timed_hot_on' looked unreal (near-SPY return, half the drawdown). Two deflators, because a
backtest that looks unreal usually is:

  (A) VT control — replace the JM risk-on/off equity signal with a plain vol-target (reactive
      incumbent; ch.1 says VT beats the JM at de-risking). Same gold/trend core. If VT matches
      or beats timed_hot_on's drawdown -> the label adds nothing; it's just VT.

  (B) Naive-core — keep the JM timing but swap the hand-picked gold/trend defensive core for a
      boring core (bonds, then cash). Gold+trend were SELECTED as crisis hedges using this same
      2007-2026 sample; if the protection collapses with a boring core, the 'magic' was the
      hindsight asset pick, not the timing.

Reuses the go/no-go engine. Prints a comparison vs timed_hot_on / static@73%.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from rotation_gonogo import load, backtest, metrics  # noqa: E402

VT_TARGET, VT_CAP, VOL_LB = 0.135, 1.5, 63


def eq_core(eq, core):
    rest = 1.0 - eq
    if core == "goldtrend":
        return {"SPY": eq, "GLD": rest / 2, "TREND": rest / 2}
    if core == "bonds":
        return {"SPY": eq, "IEF": rest}
    if core == "cash":
        return {"SPY": eq, "BIL": rest}


def main():
    rets, state = load()
    off = state == 1
    rf = rets["BIL"]
    reb = [d for d in rets.index if d in set(rets.resample("ME").last().index)]

    # causal reactive vol-target equity weight (trailing SPY vol, lagged)
    spy_vol = rets["SPY"].rolling(VOL_LB).std().shift(1) * np.sqrt(252)
    vt_eq = (VT_TARGET / spy_vol).clip(0.0, VT_CAP)

    def run(label, fn):
        net, eqw = backtest(rets, fn, reb)
        ann, vol, sh, mdd, cr = metrics(net, rf)
        return dict(port=label, avg_eq=eqw, ann_ret=ann, vol=vol, sharpe=sh, maxDD=mdd, **cr)

    rows = [
        # the reference: JM timing, gold/trend core (the 'unreal' one) + its static twin
        run("JM_hot goldtrend", lambda dt: eq_core(0.95 if not off.loc[dt] else 0.30, "goldtrend")),
        run("static@73 goldtrend", lambda dt: eq_core(0.73, "goldtrend")),
        # (A) VT control, gold/trend core (reactive signal instead of JM)
        run("VT goldtrend", lambda dt: eq_core(float(vt_eq.loc[dt]) if pd.notna(vt_eq.loc[dt]) else 0.73, "goldtrend")),
        # (B) JM timing but boring cores (isolates the hindsight gold/trend pick)
        run("JM_hot bonds", lambda dt: eq_core(0.95 if not off.loc[dt] else 0.30, "bonds")),
        run("JM_hot cash", lambda dt: eq_core(0.95 if not off.loc[dt] else 0.30, "cash")),
        # VT with boring core too, for completeness
        run("VT bonds", lambda dt: eq_core(float(vt_eq.loc[dt]) if pd.notna(vt_eq.loc[dt]) else 0.73, "bonds")),
    ]
    res = pd.DataFrame(rows)

    print(f"window {rets.index[0].date()}..{rets.index[-1].date()}  n={len(rets)}\n")
    print("=" * 92)
    print("DEFLATION — is timed_hot_on's protection unique to the JM label + gold/trend, or not?")
    print("=" * 92)
    print(f"{'portfolio':<20}{'avgEq':>6}{'annRet':>8}{'vol':>7}{'Sharpe':>8}{'maxDD':>8}"
          f"{'GFC08':>8}{'COVID':>8}{'INFL22':>8}")
    for _, x in res.iterrows():
        print(f"{x.port:<20}{x.avg_eq:>6.0%}{x.ann_ret:>7.1%}{x.vol:>7.1%}{x.sharpe:>8.2f}"
              f"{x.maxDD:>8.1%}{x.GFC08:>8.1%}{x.COVID20:>8.1%}{x.INFL22:>8.1%}")

    ref = res.set_index("port").loc["JM_hot goldtrend"]
    print("\n" + "-" * 92)
    print("verdict logic:")
    vt = res.set_index("port").loc["VT goldtrend"]
    jb = res.set_index("port").loc["JM_hot bonds"]
    print(f"  (A) VT vs JM at gold/trend core: maxDD {vt.maxDD:.1%} vs {ref.maxDD:.1%}  -> "
          f"{'VT MATCHES/BEATS: label adds nothing' if vt.maxDD >= ref.maxDD - 0.03 else 'JM protects more than VT'}")
    print(f"  (B) JM with BONDS core vs gold/trend: maxDD {jb.maxDD:.1%} vs {ref.maxDD:.1%}  -> "
          f"{'protection SURVIVES boring core (timing-driven)' if jb.maxDD >= ref.maxDD - 0.05 else 'protection COLLAPSES: it was the hindsight gold/trend pick'}")
    res.to_csv(ROOT / "results" / "rotation_deflate.csv", index=False)
    print("\nwrote results/rotation_deflate.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
