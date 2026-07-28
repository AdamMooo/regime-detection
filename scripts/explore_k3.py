"""K=3 feasibility probe (instrument exploration, no economic claim, no look spent —
no strategy returns are computed or printed; the λ-selection machinery internally uses
the protocol's validation rule only).

Motivated by the state anatomy: the money-relevant boundary is INSIDE the K=2 stressed
state (crash −42% ann vs rebound +65% ann at lower vol). Questions:
  1. What are the three states (days, return/vol, feature centers)?
  2. How does K=3 partition K=2's stressed days — and does it separate the EX-POST
     crash phase (entry→trough) from the rebound phase (trough→exit)?
  3. Does K=3 clear K=2's stability bar (label agreement under ±2y train-start shifts;
     K=2 scored 1.000)?

Protocol identical to chapter 1 (same walk-forward, grid, validation) with k=3.
Writes results/k3_exploration.csv; run with PYTHONIOENCODING=utf-8 and tee to
results/k3_exploration_run.log.

--smoke: short slice, small grid — code-path check only.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from atlas import episodes_of
from jumpmodel import build_features
from run_config import DELAY, LAMBDA_GRID, N_INIT, REFIT, START, TRAIN0, VAL
from walkforward import walk_forward

ANN = 252


def run_pass(r, F, train0, grid, n_init, val):
    return walk_forward(r, F.to_numpy(), burn=63, train0=train0, refit=REFIT,
                        grid=grid, val=val, n_init=n_init, delay=DELAY, k=3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True).loc[START:]
    train0, grid, n_init, val = TRAIN0, LAMBDA_GRID, N_INIT, VAL
    if args.smoke:
        panel = panel.iloc[-6000:]
        train0, grid, n_init, val = 3024, [50.0, 200.0], 3, 1008
        print("SMOKE MODE: short slice, small grid — code-path check only.", flush=True)

    r = panel["mkt_ret"].to_numpy()
    F = build_features(r)
    idx = panel.index
    t0 = time.time()

    print(f"[1/4] K=3 base pass over {idx[0].date()}..{idx[-1].date()} "
          f"(train0={train0}, grid={grid})", flush=True)
    s3, lam_hist = run_pass(r, F, train0, grid, n_init, val)
    oos = s3 >= 0
    print(f"      done ({(time.time() - t0) / 60:.1f} min). lam_path={lam_hist}", flush=True)

    rows = []
    s_o, r_o, idx_o = s3[oos], r[oos], idx[oos]
    switches = float((s_o[1:] != s_o[:-1]).sum() / len(s_o) * ANN)
    print(f"[2/4] states over OOS {idx_o[0].date()}..{idx_o[-1].date()} "
          f"(n={len(s_o)}, switches/yr={switches:.2f}):", flush=True)
    for st in (0, 1, 2):
        m = s_o == st
        if m.sum() == 0:
            print(f"      state {st}: EMPTY")
            rows.append(dict(section="state", key=str(st), n=0))
            continue
        ann, vol = r_o[m].mean() * ANN, r_o[m].std() * np.sqrt(ANN)
        rows.append(dict(section="state", key=str(st), n=int(m.sum()),
                         frac=float(m.mean()), ann_ret=float(ann), ann_vol=float(vol),
                         sharpe=float(ann / vol)))
        print(f"      state {st}: {m.sum():5} days ({m.mean():5.1%})  "
              f"ret {ann:+7.1%}  vol {vol:6.1%}  Sharpe {ann / vol:5.2f}", flush=True)

    # partition of the FROZEN K=2 states + ex-post crash/rebound alignment
    frozen = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"])
    both = pd.DataFrame({"date": idx_o, "k3": s_o}).merge(frozen, on="date")
    if len(both):
        s2 = both["state"].to_numpy()
        k3 = both["k3"].to_numpy()
        rb = both.merge(pd.DataFrame({"date": idx, "r": r}), on="date")["r"].to_numpy()
        print(f"[3/4] vs frozen K=2 on {len(both)} overlap days:", flush=True)
        for st2, nm in ((0, "k2 calm"), (1, "k2 stressed")):
            m = s2 == st2
            dist = [float((k3[m] == j).mean()) for j in (0, 1, 2)]
            rows.append(dict(section="k2_partition", key=nm,
                             k3_0=dist[0], k3_1=dist[1], k3_2=dist[2]))
            print(f"      {nm:12} → k3 dist: {dist[0]:.0%} / {dist[1]:.0%} / {dist[2]:.0%}",
                  flush=True)
        # ex-post phases within k2 stressed episodes
        crash = np.zeros(len(both), dtype=bool)
        rebound = np.zeros(len(both), dtype=bool)
        for a, b in episodes_of(s2):
            path = np.cumprod(1.0 + rb[a:b + 1])
            t = int(np.argmin(path))
            crash[a:a + t + 1] = True
            rebound[a + t + 1:b + 1] = True
        for msk, nm in ((crash, "crash(entry→trough)"), (rebound, "rebound(trough→exit)")):
            if msk.sum() == 0:
                continue
            dist = [float((k3[msk] == j).mean()) for j in (0, 1, 2)]
            rows.append(dict(section="phase_alignment", key=nm, n=int(msk.sum()),
                             k3_0=dist[0], k3_1=dist[1], k3_2=dist[2]))
            print(f"      {nm:22} n={msk.sum():5} → k3 dist: "
                  f"{dist[0]:.0%} / {dist[1]:.0%} / {dist[2]:.0%}", flush=True)

    # stability bar (K=2 scored 1.000/1.000)
    print(f"[4/4] stability under ±2y train-start shifts:", flush=True)
    for shift, nm in ((504, "start+2y"), (-504, "start-2y")):
        s_sh, _ = run_pass(r, F, train0 + shift, grid, n_init, val)
        m = (s3 >= 0) & (s_sh >= 0)
        agree = float((s3[m] == s_sh[m]).mean())
        rows.append(dict(section="stability", key=nm, agreement=agree, n=int(m.sum())))
        print(f"      {nm}: agreement {agree:.3f} on {m.sum()} joint OOS days "
              f"(K=2 bar: 1.000)", flush=True)

    rows.append(dict(section="meta", key="switches_yr", agreement=switches))
    out = pd.DataFrame(rows)
    if not args.smoke:
        out.to_csv(ROOT / "results" / "k3_exploration.csv", index=False)
        print(f"\nwrote results/k3_exploration.csv "
              f"(total {(time.time() - t0) / 60:.1f} min)", flush=True)
    else:
        print(f"\nSMOKE OK ({(time.time() - t0) / 60:.1f} min) — nothing written", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
