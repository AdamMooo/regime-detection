"""Aggressiveness / equity-tilt sweep for the Path-B rotation prototype (descriptive, no look).

Adam's steer (2026-07-26): the go/no-go's B was too timid (avg equity 47%, capped returns).
Questions: (1) does more equity (avg 65-75%) buy return? (2) simplify — the bonds<->trend switch
added nothing (Bd result), so focus on the ONE signal that matters: equity risk-on/off timing,
lean HARD into equity out of bear markets. (3) is there a middle ground between static A and the
timid B? (4) THE control: does regime-timing beat a STATIC portfolio at the SAME average equity,
or is any gain just beta?

Simplified strategy family (monthly rebalance, 10 bps, frozen causal JM label for risk-on/off):
  equity = E_on when risk-ON, E_off when risk-OFF; the rest -> gold/trend 50/50 defensive core
  (bonds dropped: unreliable hedge; switch dropped: adds nothing).
  For each timed (E_on,E_off) we also run its MATCHED STATIC twin = constant equity at the timed
  version's realized average, same defensive core -> isolates timing skill from exposure.

Reuses the go/no-go engine. Writes results/rotation_sweep.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from rotation_gonogo import load, backtest, metrics, CRISES  # noqa: E402


def eq_core(eq):
    """equity + gold/trend 50/50 defensive core."""
    rest = 1.0 - eq
    return {"SPY": eq, "GLD": rest / 2, "TREND": rest / 2}


def main():
    rets, state = load()
    off = state == 1
    rf = rets["BIL"]
    month_ends = set(rets.resample("ME").last().index)
    reb = [d for d in rets.index if d in month_ends]
    print(f"window {rets.index[0].date()}..{rets.index[-1].date()}  n={len(rets)}  "
          f"risk-off {off.mean():.0%} of days\n")

    # timed configs: (label, E_on, E_off) — increasingly aggressive on the upside
    timed_cfgs = [
        ("timed_timid",   0.60, 0.20),   # ~ the original B
        ("timed_mid",     0.80, 0.35),
        ("timed_aggr",    0.90, 0.40),
        ("timed_hot_on",  0.95, 0.30),   # very aggressive in calm, still defends hard
        ("timed_vaggr",   1.00, 0.45),
    ]

    rows = []

    def add(label, fn):
        net, eqw = backtest(rets, fn, reb)
        ann, vol, sh, mdd, cr = metrics(net, rf)
        rows.append(dict(port=label, ann_ret=ann, vol=vol, sharpe=sh, maxDD=mdd,
                         avg_eq=eqw, **cr))
        return eqw

    # anchors
    add("A_orig", lambda dt: {"SPY": .50, "GLD": .20, "TREND": .20, "IEF": .10})
    add("SPY_bh", lambda dt: {"SPY": 1.0})

    # timed + matched-static twin at the timed version's realized avg equity
    pairs = []
    for label, e_on, e_off in timed_cfgs:
        def timed_fn(dt, e_on=e_on, e_off=e_off):
            return eq_core(e_off if off.loc[dt] else e_on)
        avg_eq = add(label, timed_fn)
        stat_label = f"stat_{label}"          # unique twin (avg may collide across configs)
        def stat_fn(dt, e=avg_eq):
            return eq_core(e)
        add(stat_label, stat_fn)
        pairs.append((label, stat_label))

    res = pd.DataFrame(rows)
    print("=" * 100)
    print("EQUITY-TILT SWEEP  (timed = regime equity on/off; static = constant equity, matched core)")
    print("=" * 100)
    print(f"{'portfolio':<15}{'avgEq':>6}{'annRet':>8}{'vol':>7}{'Sharpe':>8}{'maxDD':>8}"
          f"{'GFC08':>8}{'COVID':>8}{'INFL22':>8}")
    for _, x in res.iterrows():
        print(f"{x.port:<15}{x.avg_eq:>6.0%}{x.ann_ret:>7.1%}{x.vol:>7.1%}{x.sharpe:>8.2f}"
              f"{x.maxDD:>8.1%}{x.GFC08:>8.1%}{x.COVID20:>8.1%}{x.INFL22:>8.1%}")

    print("\n" + "-" * 100)
    print("TIMING CONTROL — does the regime timing beat a STATIC portfolio at the SAME avg equity?")
    print("-" * 100)
    g = res.set_index("port")
    for tl, sl in pairs:
        t, s = g.loc[tl], g.loc[sl]
        d_sh = t.sharpe - s.sharpe
        d_ret = t.ann_ret - s.ann_ret
        d_dd = t.maxDD - s.maxDD
        tag = "timing HELPS" if (d_sh > 0.05 and d_dd > 0) else (
              "timing ~ neutral" if abs(d_sh) <= 0.05 else "timing HURTS")
        print(f"  {tl:<14} (eq {t.avg_eq:.0%}) vs {sl:<12}: "
              f"dSharpe {d_sh:+.2f}  dRet {d_ret:+.1%}  dMaxDD {d_dd:+.1%}  -> {tag}")

    res.to_csv(ROOT / "results" / "rotation_sweep.csv", index=False)
    print("\nwrote results/rotation_sweep.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
