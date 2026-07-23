"""State anatomy (descriptive, frozen OOS labels — instrument work, no prereg needed,
informs but never gates future preregs).

Four questions:
  1. What IS each state, distributionally (moments, tails, best/worst days)?
  2. The re-entry problem, quantified: inside each stressed episode, split crash phase
     (entry..trough) from rebound phase (trough..exit) — how much rebound happens while
     the label still says stressed (what a 0/100 switcher forfeits)?
  3. Exit hazard: given stress has lasted d days, chance it ends within the next month.
  4. Bull anatomy: calm days bucketed by age since the stress exit — is the young bull
     different from the old bull?

Writes results/state_anatomy.csv (+ run log via print capture in the console).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from atlas import episodes_of

ANN = 252


def moments(r):
    r = np.asarray(r, dtype=float)
    m, sd = r.mean(), r.std()
    z = (r - m) / sd
    return dict(n=len(r), ann_ret=m * ANN, ann_vol=sd * np.sqrt(ANN),
                sharpe=m / sd * np.sqrt(ANN), skew=float((z ** 3).mean()),
                ex_kurt=float((z ** 4).mean() - 3),
                var5=float(np.quantile(r, 0.05)), es5=float(r[r <= np.quantile(r, 0.05)].mean()),
                best=float(r.max()), worst=float(r.min()))


def main():
    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True)
    labels = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"])
    df = panel.loc[panel.index.isin(labels["date"])]
    s = labels.set_index("date").loc[df.index, "state"].to_numpy()
    r = df["mkt_ret"].to_numpy()
    dates = df.index
    rows = []

    print("=== 1. WHAT IS EACH STATE (daily market return distribution) ===")
    for st, nm in ((0, "calm"), (1, "stressed")):
        mm = moments(r[s == st])
        rows.append(dict(section="state_moments", key=nm, **mm))
        print(f"  {nm:9} n={mm['n']:5} ret {mm['ann_ret']:+7.1%} vol {mm['ann_vol']:6.1%} "
              f"Sharpe {mm['sharpe']:5.2f} skew {mm['skew']:+5.2f} exkurt {mm['ex_kurt']:5.1f} "
              f"VaR5 {mm['var5']:+.2%} ES5 {mm['es5']:+.2%} "
              f"best {mm['best']:+.1%} worst {mm['worst']:+.1%}")

    print("\n=== 2. INSIDE STRESSED EPISODES: crash phase vs rebound phase ===")
    eps = episodes_of(s)
    crash_days, rebound_days = [], []
    ep_rows = []
    for a, b in eps:
        path = np.cumprod(1.0 + r[a:b + 1])
        t = int(np.argmin(path))
        crash_days.extend(range(a, a + t + 1))
        rebound_days.extend(range(a + t + 1, b + 1))
        rebound_inside = float(path[-1] / path[t] - 1.0)
        after = r[b + 1:b + 1 + 63]
        ep_rows.append(dict(section="episode", key=str(dates[a].date()),
                            days=b - a + 1, trough_day=t + 1,
                            ep_ret=float(path[-1] - 1.0),
                            crash_ret=float(path[t] - 1.0),
                            rebound_inside=rebound_inside,
                            ret_63d_after_exit=float(np.prod(1 + after) - 1)))
    ep = pd.DataFrame(ep_rows)
    rows.extend(ep_rows)
    cm = moments(r[crash_days])
    rm = moments(r[rebound_days])
    rows.append(dict(section="phase_moments", key="crash(entry..trough)", **cm))
    rows.append(dict(section="phase_moments", key="rebound(trough..exit)", **rm))
    print(f"  crash phase   (entry→trough): {cm['n']:5} days, ann ret {cm['ann_ret']:+7.1%}, "
          f"vol {cm['ann_vol']:6.1%}")
    print(f"  rebound phase (trough→exit):  {rm['n']:5} days, ann ret {rm['ann_ret']:+7.1%}, "
          f"vol {rm['ann_vol']:6.1%}")
    print(f"  → the stressed state is ~{len(rebound_days) / (len(crash_days) + len(rebound_days)):.0%} "
          f"rebound days. Median rebound captured INSIDE the state (a switcher forfeits this): "
          f"{ep['rebound_inside'].median():+.1%} per episode "
          f"(mean {ep['rebound_inside'].mean():+.1%}; total across 30 episodes "
          f"{(1 + ep['rebound_inside']).prod() - 1:+.1%} compounded)")
    print(f"  median trough position: day {int(ep['trough_day'].median())} of "
          f"{int(ep['days'].median())} (median episode) — "
          f"{1 - ep['trough_day'].median() / ep['days'].median():.0%} of a median episode is rebound")
    print(f"  63d after exit: median {ep['ret_63d_after_exit'].median():+.1%} "
          f"(the re-entry is not too late once it happens)")

    print("\n=== 3. EXIT HAZARD: given stress has lasted d days, P(exit within 21d) ===")
    durs = ep["days"].to_numpy()
    for d in (0, 21, 42, 63, 126, 252):
        alive = (durs > d).sum()
        if alive < 3:
            break
        exits = ((durs > d) & (durs <= d + 21)).sum()
        rows.append(dict(section="hazard", key=f"age>{d}", n=int(alive),
                         p_exit_21d=float(exits / alive)))
        print(f"  survived {d:3}d: {alive:2} episodes alive, P(exit within 21d) = {exits / alive:.0%}")

    print("\n=== 4. BULL ANATOMY: calm days by age since stress exit ===")
    calm_eps = episodes_of(1 - s)
    buckets = {"young bull (0-63d)": [], "mid bull (63-252d)": [], "old bull (252d+)": []}
    for a, b in calm_eps:
        for i in range(a, b + 1):
            age = i - a
            k = ("young bull (0-63d)" if age < 63 else
                 "mid bull (63-252d)" if age < 252 else "old bull (252d+)")
            buckets[k].append(i)
    for k, idx in buckets.items():
        mm = moments(r[idx])
        rows.append(dict(section="bull_age", key=k, **mm))
        print(f"  {k:20} n={mm['n']:5} ret {mm['ann_ret']:+7.1%} vol {mm['ann_vol']:6.1%} "
              f"Sharpe {mm['sharpe']:5.2f} skew {mm['skew']:+5.2f}")

    print("\n=== 5. MOMENTUM BY STATE (12-1 trailing market return, contemporaneous) ===")
    px = pd.Series(1.0 + df["mkt_ret"].to_numpy()).cumprod()
    mom = (px.shift(21) / px.shift(252) - 1.0).to_numpy()
    ok = ~np.isnan(mom)
    for st, nm in ((0, "calm"), (1, "stressed")):
        m = ok & (s == st)
        pos = float((mom[m] > 0).mean())
        rows.append(dict(section="momentum", key=nm, n=int(m.sum()), frac_mom_pos=pos,
                         med_mom=float(np.median(mom[m]))))
        print(f"  {nm:9} 12-1 momentum positive on {pos:.0%} of days "
              f"(median {np.median(mom[m]):+.1%})")

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results" / "state_anatomy.csv", index=False)
    print(f"\nwrote results/state_anatomy.csv ({len(out)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
