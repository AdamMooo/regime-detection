"""GO/NO-GO backtest (descriptive prototype, look-free) — the rung-1 gate for the Path-B
cross-asset defensive-rotation candidate (PROGRAM.md).

THE QUESTION: does regime-TIMED rotation beat simply HOLDING a static gold+trend+diversified
blend, after costs, through 2008/2020/2022? If yes -> worth a prereg. If B ~ A -> the honest
lesson is "just hold the static blend" (no regime machinery needed).

This is NOT a preregistered look — it is a prototype to decide whether a look is worth spending.
Causality is respected so we do not fool ourselves: the risk-on/off signal is the FROZEN causal
chapter-1 JM label (results/oos_labels.csv, walk-forward filtered — no in-sample refit here);
the inflation-regime switch is a TRAILING realized stock-bond correlation (reactive, lagged one
day, never predictive — the stock-bond Stage-1 null forbids prediction).

Portfolios (monthly rebalance, proper drift-and-rebalance, 10 bps on turnover):
  A  static blend      : SPY .50 / GLD .20 / TREND .20 / IEF .10   (the baseline to beat)
  B  full regime-timed : GLD .20 always; risk-ON  SPY .60 / DEF .20
                                          risk-OFF SPY .20 / DEF .60
                         DEF = IEF if trailing corr(SPY,IEF) < 0 else TREND  (bonds<->trend switch)
  Bd defense-switch    : SPY .50 / GLD .20 / DEF .30   (equity CONSTANT -> isolates the switch
                         from the ch.1-flavored equity timing, which must beat VT on its own)
  SPY buy-hold         : reference

Metrics: annualized return / vol / Sharpe (excess over BIL cash) / max drawdown / cumulative
return in each of GFC08, COVID20, INFL22 / average equity weight (the exposure-artifact check).
Sharpe is the exposure-fair primary (it already penalizes carrying less equity).

Writes results/rotation_gonogo.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

CORR_LB = 63          # trailing window for realized stock-bond correlation (~3 months)
COST_BPS = 10.0
CRISES = {"GFC08": ("2007-11-01", "2009-07-14"),
          "COVID20": ("2020-02-25", "2020-07-13"),
          "INFL22": ("2022-01-19", "2023-01-10")}


def load():
    he = pd.read_csv(ROOT / "data" / "processed" / "hedge_etf_daily.csv",
                     index_col=0, parse_dates=True)
    tp = pd.read_csv(ROOT / "data" / "processed" / "trend_proxy_daily.csv",
                     index_col=0, parse_dates=True)["trend_ret"]
    lab = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"]) \
        .set_index("date")["state"]
    px = he[["SPY", "GLD", "IEF", "BIL"]].pct_change()       # hedge panel is PRICES -> returns
    r = pd.DataFrame({"SPY": px["SPY"], "GLD": px["GLD"], "IEF": px["IEF"],
                      "BIL": px["BIL"], "TREND": tp}).dropna()  # TREND already a return
    state = lab.reindex(r.index, method="ffill")
    r = r[state.notna()]
    state = state.loc[r.index].astype(int)
    return r, state


def backtest(rets, target_fn, rebalance_idx):
    """Proper drift-and-rebalance. target_fn(date)->dict of target weights. Rebalance on the
    given month-end dates; between, weights drift with returns. 10 bps on turnover at rebalance.
    Returns (daily net return series, average equity weight)."""
    assets = list(rets.columns)
    w = None
    out = pd.Series(0.0, index=rets.index)
    eqw = []
    reb = set(rebalance_idx)
    for dt, row in rets.iterrows():
        if w is None:                                   # first day: set initial target
            w = pd.Series(target_fn(dt), index=assets).fillna(0.0)
        gross = float((w * row).sum())
        out[dt] = gross
        eqw.append(w.get("SPY", 0.0))
        # drift weights with today's returns
        w = w * (1.0 + row)
        s = w.sum()
        w = w / s if s != 0 else w
        if dt in reb:                                   # rebalance to fresh target, pay turnover
            tgt = pd.Series(target_fn(dt), index=assets).fillna(0.0)
            turn = float((tgt - w).abs().sum())
            out[dt] -= turn * COST_BPS / 1e4
            w = tgt
    return out, float(np.mean(eqw))


def metrics(net, rf):
    ex = net - rf
    ann = net.mean() * 252
    vol = net.std() * np.sqrt(252)
    sharpe = ex.mean() / ex.std() * np.sqrt(252)
    cum = (1 + net).cumprod()
    mdd = float((cum / cum.cummax() - 1).min())
    cr = {k: float((1 + net.loc[lo:hi]).prod() - 1) for k, (lo, hi) in CRISES.items()}
    return ann, vol, sharpe, mdd, cr


def main():
    rets, state = load()
    print(f"backtest window {rets.index[0].date()}..{rets.index[-1].date()}  n={len(rets)}")
    print(f"risk-off (JM state=1): {(state==1).mean():.1%} of days\n")

    # signals (causal): risk-on/off = frozen JM label; inflation switch = trailing corr, lagged
    corr = rets["SPY"].rolling(CORR_LB).corr(rets["IEF"]).shift(1)
    off = state == 1
    defensive = pd.Series(np.where(corr < 0, "IEF", "TREND"), index=rets.index)  # bonds if corr<0

    month_ends = rets.resample("ME").last().index
    reb = [d for d in rets.index if d in set(month_ends)]

    def A(dt):
        return {"SPY": .50, "GLD": .20, "TREND": .20, "IEF": .10}

    def B(dt):
        d = defensive.loc[dt]
        if off.loc[dt]:
            eq, dfw = .20, .60
        else:
            eq, dfw = .60, .20
        w = {"SPY": eq, "GLD": .20}
        w[d] = w.get(d, 0.0) + dfw
        return w

    def Bd(dt):                                   # defense-switch only, equity constant
        d = defensive.loc[dt]
        w = {"SPY": .50, "GLD": .20}
        w[d] = w.get(d, 0.0) + .30
        return w

    def SPYbh(dt):
        return {"SPY": 1.0}

    rf = rets["BIL"]
    rows = []
    for name, fn in [("A_static", A), ("B_timed", B), ("Bd_defswitch", Bd), ("SPY_bh", SPYbh)]:
        net, eqw = backtest(rets, fn, reb)
        ann, vol, sh, mdd, cr = metrics(net, rf)
        rows.append(dict(port=name, ann_ret=ann, vol=vol, sharpe=sh, maxDD=mdd,
                         avg_eq=eqw, **cr))

    res = pd.DataFrame(rows)
    print("=" * 96)
    print("GO/NO-GO RESULTS")
    print("=" * 96)
    print(f"{'portfolio':<14}{'annRet':>8}{'vol':>7}{'Sharpe':>8}{'maxDD':>8}{'avgEq':>7}"
          f"{'GFC08':>8}{'COVID20':>9}{'INFL22':>8}")
    for _, x in res.iterrows():
        print(f"{x.port:<14}{x.ann_ret:>7.1%}{x.vol:>7.1%}{x.sharpe:>8.2f}{x.maxDD:>8.1%}"
              f"{x.avg_eq:>7.0%}{x.GFC08:>8.1%}{x.COVID20:>9.1%}{x.INFL22:>8.1%}")

    a = res[res.port == "A_static"].iloc[0]
    b = res[res.port == "B_timed"].iloc[0]
    bd = res[res.port == "Bd_defswitch"].iloc[0]
    print("\n" + "-" * 96)
    print("READ (vs the A_static baseline that must be beaten):")
    print(f"  B_timed   Sharpe {b.sharpe:.2f} vs A {a.sharpe:.2f}  (delta {b.sharpe-a.sharpe:+.2f}); "
          f"maxDD {b.maxDD:.1%} vs {a.maxDD:.1%}; avg equity {b.avg_eq:.0%} vs {a.avg_eq:.0%}")
    print(f"  Bd_defonly Sharpe {bd.sharpe:.2f} vs A {a.sharpe:.2f}  (delta {bd.sharpe-a.sharpe:+.2f}) "
          f"-- isolates the bonds<->trend switch from equity timing")
    verdict = ("GO (worth a prereg)" if (b.sharpe - a.sharpe >= 0.15 and b.maxDD > a.maxDD)
               else "NO-GO / marginal -> 'just hold the static blend'")
    print(f"\n  PROTOTYPE VERDICT: {verdict}")
    print("  (exposure caveat: if B wins only via lower avg equity, that is the ch.1 artifact,")
    print("   not timing skill -- Sharpe already penalizes it, but a matched-exposure control is")
    print("   mandatory before any prereg.)")

    res.to_csv(ROOT / "results" / "rotation_gonogo.csv", index=False)
    print("\nwrote results/rotation_gonogo.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
