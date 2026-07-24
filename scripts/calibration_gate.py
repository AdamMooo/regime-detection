"""Chapter-3 calibration gate (SYNTHETIC ONLY, pre-freeze — prereg CH3-EXPOSURE §6).

Establishes whether the causal filter's normalized evidence gap m_t = (V[calm] -
V[stressed]) / lambda maps to a CALIBRATED P(stressed) via Platt scaling, robustly
across a DGP grid varying state frequency, persistence, jump severity, and SNR.
The pooled (a, b) fit on TRAIN seeds is the single frozen map the A3 arm may use on
real data; the real panel never enters any fit (one-look boundary).

Acceptance, evaluated PER CELL on held-out eval seeds:
  (a) calibration regression logit P(y|p_hat) = alpha + beta*logit(p_hat):
      beta in [0.8, 1.2] and |alpha| <= 0.1
  (b) Brier(platt) < Brier(pooled-train climatology) and < Brier(log EWMA-vol
      logistic benchmark, halflife 20 = the VT arm's estimator)
  (c) per-cell refit stability: CV(a) <= 20% and range(b) <= 0.2 across cells

Writes results/calibration_gate.csv (+ frozen map results/calibration_map.json on a
passing full run). --smoke = 2 cells x 2 seeds on a reduced lambda grid.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jumpmodel import build_features
from walkforward import walk_forward

T_TOTAL = 6300
TRAIN0 = 3024
REFIT = 252
VAL = 1008
LAMBDA_GRID = [10.0, 25.0, 50.0, 100.0, 200.0, 400.0, 800.0]
N_INIT = 5
TRAIN_SEEDS = (21, 22)
EVAL_SEEDS = (31, 32)

# name: (dwell_calm, dwell_bear, mu(calm, bear), sig(calm, bear)) — spans state
# frequency (rare/frequent), persistence (choppy/long_dwell), severity (asym_sev)
# and signal-to-noise (weak/strong); "base" ~= synthetic_validation config R
CELLS = {
    "base": (400, 100, (0.0006, -0.0010), (0.007, 0.020)),
    "frequent": (150, 60, (0.0006, -0.0010), (0.007, 0.020)),
    "rare": (800, 80, (0.0006, -0.0010), (0.007, 0.020)),
    "choppy": (120, 40, (0.0006, -0.0010), (0.007, 0.020)),
    "long_dwell": (800, 250, (0.0006, -0.0010), (0.007, 0.020)),
    "weak_snr": (400, 100, (0.0005, -0.0005), (0.008, 0.013)),
    "strong_snr": (400, 100, (0.0008, -0.0030), (0.006, 0.030)),
    "asym_sev": (400, 60, (0.0006, -0.0020), (0.007, 0.026)),
}


def simulate(dwell_calm, dwell_bear, mu, sig, T, seed):
    rng = np.random.default_rng(seed)
    p_stay = (1.0 - 1.0 / dwell_calm, 1.0 - 1.0 / dwell_bear)
    s = np.empty(T, dtype=int)
    s[0] = 0
    for t in range(1, T):
        s[t] = s[t - 1] if rng.random() < p_stay[s[t - 1]] else 1 - s[t - 1]
    r = rng.normal(np.where(s == 0, *mu), np.where(s == 0, *sig))
    return r, s


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))


def fit_logistic(x, y, ridge=1e-3, iters=100):
    """2-parameter logistic p = sigmoid(a*x + b) by ridge-stabilized IRLS.
    Returns (a, b)."""
    X = np.column_stack([np.asarray(x, dtype=float), np.ones(len(x))])
    y = np.asarray(y, dtype=float)
    beta = np.zeros(2)
    for _ in range(iters):
        p = _sigmoid(X @ beta)
        W = p * (1.0 - p) + 1e-9
        g = X.T @ (y - p) - ridge * beta
        H = (X * W[:, None]).T @ X + ridge * np.eye(2)
        step = np.linalg.solve(H, g)
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    return float(beta[0]), float(beta[1])


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1.0 - p))


def _auc(score, y):
    """Rank AUC — discrimination only, calibration-free (Murphy-decomposition
    counterpart to the Brier criterion: separates 'ranks days badly' from
    'ranks well but calibrates badly')."""
    ranks = pd.Series(score).rank().to_numpy()
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def collect(cells, train_seeds, eval_seeds, grid, n_init):
    frames = []
    n_runs = len(cells) * (len(train_seeds) + len(eval_seeds))
    done = 0
    for cell, (dc, db, mu, sig) in cells.items():
        for role, seeds in (("train", train_seeds), ("eval", eval_seeds)):
            for seed in seeds:
                tic = time.time()
                r, s_true = simulate(dc, db, mu, sig, T_TOTAL, seed)
                F = build_features(r).to_numpy()
                states, _, m = walk_forward(r, F, burn=63, train0=TRAIN0, refit=REFIT,
                                            grid=grid, val=VAL, n_init=n_init,
                                            return_margin=True)
                sig_ann = pd.Series(r).ewm(halflife=20).std().mul(np.sqrt(252)).to_numpy()
                keep = (states >= 0) & np.isfinite(m) & (sig_ann > 0)
                s_k, y_k = states[keep], s_true[keep]
                bac = ((s_k == y_k)[y_k == 0].mean() + (s_k == y_k)[y_k == 1].mean()) / 2
                frames.append(pd.DataFrame(dict(
                    cell=cell, seed=seed, role=role,
                    m=m[keep], y=y_k, logsig=np.log(sig_ann[keep]))))
                done += 1
                print(f"[{done}/{n_runs}] {cell}/{role}/seed{seed}: "
                      f"{int(keep.sum())} oos days, bear_frac {y_k.mean():.3f}, "
                      f"bac {bac:.3f}, {time.time() - tic:.0f}s", flush=True)
    return pd.concat(frames, ignore_index=True)


def main():
    smoke = "--smoke" in sys.argv
    cells = {k: CELLS[k] for k in (("base", "weak_snr") if smoke else CELLS)}
    train_seeds = (21,) if smoke else TRAIN_SEEDS
    eval_seeds = (31,) if smoke else EVAL_SEEDS
    grid = [25.0, 100.0, 400.0] if smoke else LAMBDA_GRID
    n_init = 3 if smoke else N_INIT

    data = collect(cells, train_seeds, eval_seeds, grid, n_init)
    train, ev = data[data.role == "train"], data[data.role == "eval"]

    a, b = fit_logistic(train.m, train.y)
    a_vol, b_vol = fit_logistic(train.logsig, train.y)
    base_rate = float(train.y.mean())
    print(f"\npooled platt map: p = sigmoid({a:.4f}*m + {b:.4f}); "
          f"vol benchmark: sigmoid({a_vol:.4f}*logsig + {b_vol:.4f}); "
          f"train base rate {base_rate:.3f}", flush=True)

    rows, cell_fits = [], {}
    for cell in cells:
        cell_fits[cell] = fit_logistic(train[train.cell == cell].m,
                                       train[train.cell == cell].y)
        ec = ev[ev.cell == cell]
        p = _sigmoid(a * ec.m.to_numpy() + b)
        p_vol = _sigmoid(a_vol * ec.logsig.to_numpy() + b_vol)
        y = ec.y.to_numpy()
        beta, alpha = fit_logistic(_logit(p), y)
        brier = float(((p - y) ** 2).mean())
        brier_clim = float(((base_rate - y) ** 2).mean())
        brier_vol = float(((p_vol - y) ** 2).mean())
        pass_rel = (0.8 <= beta <= 1.2) and abs(alpha) <= 0.1
        pass_brier = brier < brier_clim and brier < brier_vol
        rows.append(dict(
            cell=cell, n_eval=len(ec), bear_frac=round(float(y.mean()), 3),
            slope=round(beta, 3), intercept=round(alpha, 3),
            brier=round(brier, 4), brier_clim=round(brier_clim, 4),
            brier_vol=round(brier_vol, 4),
            auc_m=round(_auc(ec.m.to_numpy(), y), 3),
            auc_vol=round(_auc(ec.logsig.to_numpy(), y), 3),
            a_cell=round(cell_fits[cell][0], 4), b_cell=round(cell_fits[cell][1], 4),
            pass_reliability=pass_rel, pass_brier=pass_brier,
        ))
        print(rows[-1], flush=True)

    a_cells = np.array([v[0] for v in cell_fits.values()])
    b_cells = np.array([v[1] for v in cell_fits.values()])
    cv_a = float(a_cells.std() / abs(a_cells.mean()))
    range_b = float(b_cells.max() - b_cells.min())
    pass_stab = cv_a <= 0.20 and range_b <= 0.2

    df = pd.DataFrame(rows)
    out = ROOT / "results" / ("calibration_gate_smoke.csv" if smoke else "calibration_gate.csv")
    df.to_csv(out, index=False)

    gate_a = bool(df.pass_reliability.all())
    gate_b = bool(df.pass_brier.all())
    print(f"\n(a) reliability per cell: {'PASS' if gate_a else 'FAIL'}")
    print(f"(b) brier vs climatology + vol benchmark per cell: {'PASS' if gate_b else 'FAIL'}")
    print(f"(c) stability: CV(a)={cv_a:.3f} (<=0.20), range(b)={range_b:.3f} (<=0.2): "
          f"{'PASS' if pass_stab else 'FAIL'}")
    ok = gate_a and gate_b and pass_stab
    print(f"CALIBRATION GATE{' (SMOKE)' if smoke else ''}:", "PASS" if ok else "FAIL")
    if ok and not smoke:
        (ROOT / "results" / "calibration_map.json").write_text(json.dumps(
            dict(a=a, b=b, input="(V_calm - V_stressed)/lambda",
                 fit="pooled train seeds, DGP grid, calibration_gate.py"), indent=2))
        print("frozen map written: results/calibration_map.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
