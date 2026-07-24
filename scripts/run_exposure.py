"""Chapter-3 runner — state-conditioned exposure dial vs vol targeting.

Arms (prereg CH3-EXPOSURE §3, single-delta): A2 VT w = clip(sigma*/sigma-hat, 0, 1);
A3 = clip(sigma*/sigma-hat * g[s], 0, 1) with g = {1, g_stress}, g_stress in G_GRID
([0, 2] — direction not assumed, Rev-3), chosen per refit by trailing-window Sharpe
(net, delay=2) on already-causal filtered states; g=1 until 1008 OOS days exist
(warm-up biases toward null). g_stress ≡ 1 recovers A2 exactly (tested).

Modes:
  --smoke : §6b capability check, SYNTHETIC only. POWER cells (planted state-conditional
            Sharpe gap, both directions: de-risk and re-risk) must give fee(A3−A2) > 0
            and above the placebo 95th; SIZE cell (mu proportional to sigma — no gap)
            must sit inside the bands. No smoke pass, no real run.
  real run: BLOCKED until the prereg is FROZEN with Adam's named+dated sign-off;
            requires --confirm-frozen. One look.
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from backtest import fko_fee, sharpe, stationary_bootstrap_ci, strategy_returns
from jumpmodel import build_features
from walkforward import walk_forward

G_GRID = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]  # freeze with prereg
TARGET = 0.10
CAP = 1.0
COST = 10.0
DELAY = 2
GAMMA = 10.0
REFIT = 252
G_WARMUP = 1008

T_TOTAL = 6300
TRAIN0 = 3024
SMOKE_GRID = [25.0, 100.0, 400.0]
SMOKE_SEEDS = [11, 12, 13]
N_PLACEBO = 20

# planted DGPs: POWER cells have a state-conditional Sharpe gap a vol scaler cannot
# express (deri: stress drift negative -> true g < 1; reri: stress Sharpe ABOVE calm
# -> true g > 1); SIZE cell has mu proportional to sigma (constant Sharpe -> VT optimal)
SMOKE_CELLS = {
    "power_derisk": dict(mu=(0.0007, -0.0015), sig=(0.007, 0.020)),
    "power_rerisk": dict(mu=(0.0007, 0.0035), sig=(0.007, 0.020)),
    "size_nogap": dict(mu=(0.0006, 0.0006 * 0.020 / 0.007), sig=(0.007, 0.020)),
}
DWELL = (400, 100)


def sig_ann(r):
    return pd.Series(np.asarray(r, dtype=float)).ewm(halflife=20).std().mul(
        np.sqrt(252)).to_numpy()


def dial_weights(sig, states, g_stress):
    """w = clip(TARGET/sigma * g[s], 0, CAP); state -1 (pre-OOS) and warmup -> g = 1.
    g_stress = 1.0 recovers the VT arm exactly."""
    g = np.where(states == 1, g_stress, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        w = TARGET / sig * g
    return np.clip(np.where(np.isfinite(w), w, 1.0), 0.0, CAP)


def select_g(sig_w, s_w, r_w):
    """g from G_GRID maximizing net Sharpe (delay=2) on the trailing window.
    Ties break toward g closest to 1 (parsimony -> toward null)."""
    best = None
    for g in sorted(G_GRID, key=lambda x: abs(x - 1.0)):
        ret = strategy_returns(dial_weights(sig_w, s_w, g), r_w, 0.0,
                               cost_bps=COST, delay=DELAY)
        sr = sharpe(ret)
        if best is None or sr > best[1] + 1e-12:
            best = (g, sr)
    return best[0]


def a3_weights(r, states, sig):
    """Per-refit g selection on trailing G_WARMUP OOS days; g=1 during warmup."""
    oos_idx = np.flatnonzero(states >= 0)
    w = dial_weights(sig, np.full(len(r), -1), 1.0)  # VT everywhere as base
    g_path = []
    t0 = 0
    while t0 < len(oos_idx):
        block = oos_idx[t0:t0 + REFIT]
        if t0 >= G_WARMUP:
            win = oos_idx[t0 - G_WARMUP:t0]
            g = select_g(sig[win], states[win], r[win])
        else:
            g = 1.0
        g_path.append(g)
        w[block] = dial_weights(sig[block], states[block], g)
        t0 += REFIT
    return w, g_path


def placebo_band(r, states, sig, ret_vt, oos, rng, n=N_PLACEBO):
    s_o = states[oos]
    n_o = len(s_o)
    p01 = ((s_o[:-1] == 0) & (s_o[1:] == 1)).sum() / max((s_o[:-1] == 0).sum(), 1)
    p10 = ((s_o[:-1] == 1) & (s_o[1:] == 0)).sum() / max((s_o[:-1] == 1).sum(), 1)
    fees = []
    for _ in range(n):
        sp_o = np.empty(n_o, dtype=int)
        sp_o[0] = s_o[0]
        u = rng.random(n_o)
        for t in range(1, n_o):
            flip = u[t] < (p01 if sp_o[t - 1] == 0 else p10)
            sp_o[t] = 1 - sp_o[t - 1] if flip else sp_o[t - 1]
        sp = np.full(len(r), -1, dtype=int)
        sp[oos] = sp_o
        w_p, _ = a3_weights(r, sp, sig)
        ret_p = strategy_returns(w_p, r, 0.0, cost_bps=COST, delay=DELAY)[oos]
        fees.append(fko_fee(ret_p, ret_vt, gamma=GAMMA))
    return float(np.quantile(fees, 0.95)), float(np.quantile(fees, 0.05))


def simulate(mu, sig, seed):
    rng = np.random.default_rng(seed)
    p_stay = (1.0 - 1.0 / DWELL[0], 1.0 - 1.0 / DWELL[1])
    s = np.empty(T_TOTAL, dtype=int)
    s[0] = 0
    for t in range(1, T_TOTAL):
        s[t] = s[t - 1] if rng.random() < p_stay[s[t - 1]] else 1 - s[t - 1]
    r = rng.normal(np.where(s == 0, *mu), np.where(s == 0, *sig))
    return r, s


def smoke():
    rows = []
    for cell, cfg in SMOKE_CELLS.items():
        for seed in SMOKE_SEEDS:
            tic = time.time()
            r, _ = simulate(cfg["mu"], cfg["sig"], seed)
            F = build_features(r).to_numpy()
            states, _ = walk_forward(r, F, burn=63, train0=TRAIN0, refit=REFIT,
                                     grid=SMOKE_GRID, val=1008, n_init=3)
            oos = states >= 0
            sig = sig_ann(r)
            w_a3, g_path = a3_weights(r, states, sig)
            w_a2 = dial_weights(sig, np.full(len(r), -1), 1.0)
            ret_a3 = strategy_returns(w_a3, r, 0.0, cost_bps=COST, delay=DELAY)[oos]
            ret_a2 = strategy_returns(w_a2, r, 0.0, cost_bps=COST, delay=DELAY)[oos]
            fee = fko_fee(ret_a3, ret_a2, gamma=GAMMA)
            ci = stationary_bootstrap_ci(ret_a3, ret_a2,
                                         lambda a, b: fko_fee(a, b, gamma=GAMMA),
                                         n_boot=300, seed=seed)
            pl95, pl05 = placebo_band(r, states, sig, ret_a2, oos,
                                      np.random.default_rng(seed))
            rows.append(dict(cell=cell, seed=seed,
                             fee_a3_vs_a2=round(fee, 1),
                             ci_lo=round(ci[0], 1), ci_hi=round(ci[1], 1),
                             placebo95=round(pl95, 1), placebo05=round(pl05, 1),
                             g_median=float(np.median(g_path[G_WARMUP // REFIT:])
                                            if len(g_path) > G_WARMUP // REFIT
                                            else np.nan),
                             g_path=str(g_path),
                             runtime_s=round(time.time() - tic, 1)))
            print(rows[-1], flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results" / "exposure_smoke.csv", index=False)
    g = df.groupby("cell")["fee_a3_vs_a2"].mean()
    above = df.groupby("cell").apply(
        lambda d: (d.fee_a3_vs_a2 > d.placebo95).mean(), include_groups=False)
    p_derisk = g["power_derisk"] > 0 and above["power_derisk"] >= 2 / 3
    p_rerisk = g["power_rerisk"] > 0 and above["power_rerisk"] >= 2 / 3
    sz = df[df.cell == "size_nogap"]
    size_ok = ((sz.ci_lo <= 0) & (sz.ci_hi >= 0)).mean() >= 2 / 3
    print(f"\nPOWER de-risk (mean fee {g['power_derisk']:.1f}):",
          "PASS" if p_derisk else "FAIL")
    print(f"POWER re-risk (mean fee {g['power_rerisk']:.1f}):",
          "PASS" if p_rerisk else "FAIL")
    print(f"SIZE no-gap (CI contains 0 in {((sz.ci_lo <= 0) & (sz.ci_hi >= 0)).sum()}"
          f"/{len(sz)} seeds):", "PASS" if size_ok else "FAIL")
    ok = p_derisk and p_rerisk and size_ok
    print("CAPABILITY SMOKE (§6b):", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if "--smoke" in sys.argv:
        return smoke()
    print("REAL RUN BLOCKED: prereg .planning/CH3-EXPOSURE-PREREG.md is DRAFT (not "
          "FROZEN). Requires: recorded §6b smoke PASS + Adam's named+dated sign-off + "
          "overnight cooling-off, then rerun with --confirm-frozen.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
