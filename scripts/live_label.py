"""Live label: splice the SPY total-return tail onto the French panel (French publishes
1-2 months lagged), run the frozen chapter-1 walk-forward protocol over the spliced series,
and report the CURRENT state. Instrument operation, not research — the protocol, features,
and hyperparameter selection are exactly the frozen chapter-1 configuration.

Splice gate: daily-return corr >= 0.98 on the last 250 overlapping days (universe difference
tolerated per the construction-gate diagnosis; modern-era corr measured 0.995).

Writes results/label_live.csv; prints current state + agreement with the frozen labels.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_panel import download_spy
from jumpmodel import build_features
from run_config import LAMBDA_GRID, N_INIT, REFIT, START, TRAIN0, VAL, DELAY
from walkforward import walk_forward


def spliced_series():
    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True).loc[START:]
    spy = download_spy()
    ff_end = panel.index[-1]
    overlap = pd.DataFrame({"ff": panel["mkt_ret"], "spy": spy}).dropna().iloc[-250:]
    corr = overlap["ff"].corr(overlap["spy"])
    if corr < 0.98:
        raise SystemExit(f"SPLICE GATE FAIL: overlap corr {corr:.4f} < 0.98")
    tail = spy[spy.index > ff_end]
    r = pd.concat([panel["mkt_ret"], tail])
    rf = pd.concat([panel["rf"], pd.Series(panel["rf"].iloc[-1], index=tail.index)])
    print(f"splice gate PASS (corr {corr:.4f}); French ends {ff_end.date()}, "
          f"SPY tail {len(tail)} days -> {r.index[-1].date()}")
    return r, rf


def main():
    r, rf = spliced_series()
    F = build_features(r.to_numpy())
    states, lam_hist = walk_forward(r.to_numpy(), F.to_numpy(), burn=63, train0=TRAIN0,
                                    refit=REFIT, grid=LAMBDA_GRID, val=VAL,
                                    n_init=N_INIT, delay=DELAY)
    oos = states >= 0
    out = pd.DataFrame({"date": r.index[oos], "state": states[oos]})
    out.to_csv(ROOT / "results" / "label_live.csv", index=False)

    frozen = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"])
    merged = out.merge(frozen, on="date", suffixes=("_live", "_frozen"))
    agree = float((merged["state_live"] == merged["state_frozen"]).mean())

    s = out["state"].to_numpy()
    last_switch = out["date"].iloc[np.flatnonzero(s[1:] != s[:-1])[-1] + 1] \
        if np.any(s[1:] != s[:-1]) else out["date"].iloc[0]
    cur = "STRESSED" if s[-1] == 1 else "CALM"
    print(f"\nCURRENT STATE ({out['date'].iloc[-1].date()}): {cur}")
    print(f"last switch: {last_switch.date()} ({(out['date'].iloc[-1] - last_switch).days} days ago)")
    print(f"agreement with frozen chapter-1 labels on overlap: {agree:.4f} ({len(merged)} days)")
    print(f"final-year lambda: {lam_hist[-1]}")
    print("wrote results/label_live.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
