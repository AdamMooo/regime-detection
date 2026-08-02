"""Constitution characterization (NO look, a-priori static weights, NO optimization): what does a
~-30% drawdown budget actually cost in return, vs 100% equity? And do candidate strategic mixes
respect the budget in the crashes we know happened?

This is the "is the return so much lower that we might as well hold 100% equity?" question, answered
on the repo's own series instead of mental arithmetic. Strategic-CORE level only: broad equity
(mkt_ret) + 10y bond + gold + trend proxy, monthly-rebalanced, UNLEVERED, no vol-target overlay
(that's a separate Layer-3 lever). The 10-15% momentum SATELLITE is deliberately excluded here --
at that weight it's a whisper on the drawdown/return shape and it's a separate Layer-2 question.

Weights are round a-priori sizings spanning the budget (a sensitivity ladder), NOT fitted to the
data. Two outputs, matched to what the data honestly supports:

  1. Matched-window payoff table (2005+, the common window where ALL four sleeves exist):
     CAGR / arith / vol / Sharpe / maxDD + per-crash trough for every mix, apples-to-apples.
     This is the return-vs-drawdown payoff.
  2. Long-history crash stress: per-crash max drawdown for each mix over the LONGEST window its
     own sleeves support (equity 1926+, +bond 1962+, +gold 2000+, +trend 2005+). Mixes that use
     gold/trend simply cannot be scored on 1973-74 / 2000-02 -- shown as n/a, not fabricated.

Writes results/drawdown_budget.csv (the matched-window payoff table).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_config import maxdd

ANN = 12


def to_monthly(daily):
    return (1 + daily).resample("ME").prod() - 1


def load_sleeves():
    a = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    tr = pd.read_csv(ROOT / "data/processed/trend_proxy_daily.csv", index_col=0, parse_dates=True)["trend_ret"]
    return {
        "EQ": to_monthly(a["mkt_ret"]),
        "BOND": to_monthly(a["bond10_ret"].dropna()),
        "GOLD": to_monthly(a["gold_ret"].dropna()),
        "TREND": to_monthly(tr.dropna()),
        "RF": to_monthly(a["rf"]),
    }


# round a-priori sizings across the budget -- a sensitivity ladder, NOT an optimization
MIXES = {
    "100% equity":               {"EQ": 1.00},
    "60/40 classic":             {"EQ": 0.60, "BOND": 0.40},
    "80/10/10 aggressive":       {"EQ": 0.80, "BOND": 0.10, "GOLD": 0.05, "TREND": 0.05},
    "75/10/15 (~-30% target)":   {"EQ": 0.75, "BOND": 0.10, "GOLD": 0.075, "TREND": 0.075},
    "70/10/20 (~-30% defensive)":{"EQ": 0.70, "BOND": 0.10, "GOLD": 0.10, "TREND": 0.10},
    "65/10/25 (~-25% target)":   {"EQ": 0.65, "BOND": 0.10, "GOLD": 0.125, "TREND": 0.125},
}

CRASHES = {
    "1973-74": ("1973-01", "1974-12"),
    "2000-02": ("2000-03", "2002-12"),
    "2008-09": ("2007-10", "2009-06"),
    "2020":    ("2020-01", "2020-06"),
    "2022":    ("2022-01", "2022-12"),
}


def mix_index(mix, sleeves):
    idx = None
    for k in list(mix) + ["RF"]:
        vi = sleeves[k].dropna().index
        idx = vi if idx is None else idx.intersection(vi)
    return idx.sort_values()


def port_monthly(mix, sleeves, idx):
    r = pd.Series(0.0, index=idx)
    for k, w in mix.items():
        r = r + w * sleeves[k].reindex(idx).fillna(0.0)
    return r


def perf(r, rf):
    r = r.dropna()
    rfa = rf.reindex(r.index).fillna(0.0).to_numpy()
    v = r.to_numpy()
    eq = np.cumprod(1 + v)
    return dict(
        n=len(v),
        cagr=eq[-1] ** (ANN / len(v)) - 1,
        arith=v.mean() * ANN,
        vol=v.std() * np.sqrt(ANN),
        sharpe=(v - rfa).mean() / v.std() * np.sqrt(ANN),
        maxdd=maxdd(v),
    )


def crash_dd(mix, sleeves, start, end):
    """Max drawdown of the mix through a crash window, ONLY if all the mix's sleeves cover it."""
    idx = mix_index(mix, sleeves)
    if len(idx) == 0 or pd.Timestamp(start) < idx.min() or pd.Timestamp(end) > idx.max():
        return np.nan
    r = port_monthly(mix, sleeves, idx)
    seg = r.loc[start:end].dropna()
    return maxdd(seg.to_numpy()) if len(seg) >= 2 else np.nan


def main():
    sleeves = load_sleeves()

    # ---- 1. matched-window payoff (common window across ALL mixes = where trend exists, 2005+) ----
    common = None
    for m in MIXES.values():
        idx = mix_index(m, sleeves)
        common = idx if common is None else common.intersection(idx)
    common = common.sort_values()
    print(f"MATCHED-WINDOW PAYOFF  ({common.min().date()}..{common.max().date()}, {len(common)} months, "
          f"monthly-rebalanced, unlevered, no vol-target)\n")

    base = perf(port_monthly(MIXES["100% equity"], sleeves, common), sleeves["RF"])
    rows = []
    hdr = f"{'mix':28}{'CAGR':>8}{'arith':>8}{'vol':>7}{'Sharpe':>8}{'maxDD':>8}{'vs eq CAGR':>11}{'2008':>8}{'2022':>8}"
    print(hdr)
    print("-" * len(hdr))
    for label, mix in MIXES.items():
        p = perf(port_monthly(mix, sleeves, common), sleeves["RF"])
        dd08 = crash_dd(mix, sleeves, *CRASHES["2008-09"])
        dd22 = crash_dd(mix, sleeves, *CRASHES["2022"])
        d_cagr = p["cagr"] - base["cagr"]
        print(f"{label:28}{p['cagr']:8.2%}{p['arith']:8.2%}{p['vol']:7.1%}{p['sharpe']:8.2f}"
              f"{p['maxdd']:8.1%}{d_cagr:+11.2%}{dd08:8.1%}{dd22:8.1%}")
        rows.append(dict(mix=label, **{k: round(v, 4) for k, v in p.items()},
                         cagr_vs_equity=round(d_cagr, 4),
                         dd_2008=round(dd08, 4), dd_2022=round(dd22, 4)))

    pd.DataFrame(rows).to_csv(ROOT / "results/drawdown_budget.csv", index=False)
    print("\nwrote results/drawdown_budget.csv")

    # ---- 2. long-history crash stress (each mix over the longest window its sleeves allow) ----
    print("\nLONG-HISTORY CRASH DRAWDOWNS (n/a = mix's gold/trend sleeves don't reach that far)\n")
    hdr2 = f"{'mix':28}" + "".join(f"{c:>11}" for c in CRASHES)
    print(hdr2)
    print("-" * len(hdr2))
    for label, mix in MIXES.items():
        cells = []
        for name, (s, e) in CRASHES.items():
            dd = crash_dd(mix, sleeves, s, e)
            cells.append(f"{'   n/a':>11}" if np.isnan(dd) else f"{dd:11.1%}")
        print(f"{label:28}" + "".join(cells))


if __name__ == "__main__":
    main()
