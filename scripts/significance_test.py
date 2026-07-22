#!/usr/bin/env python3
"""Reproducible significance test for regime information content (Experiment 1).

Question: does the out-of-sample ensemble regime label carry information about
future returns / future realized volatility BEYOND what VIX alone provides?

The statistic is delta-R^2 = R^2(VIX + regime dummies) - R^2(VIX alone), fit and
scored in-sample on the OOS-labelled period (see src.core.evaluation.regime_delta_r2).
Two complementary tests, both block-based because daily vol/returns are serially
correlated (VIX AC(1) ~ 0.9):

  1. block_bootstrap_ci     -- error bars on the observed delta-R^2.
  2. block_permutation_test -- the test that actually matters. In-sample delta-R^2
     is >= 0 by construction (adding OLS regressors never lowers in-sample R^2), so
     a bootstrap CI excluding 0 is nearly automatic and proves nothing. The
     permutation null block-shuffles the regime label (holding VIX + target fixed),
     so its delta-R^2 distribution reflects pure degrees-of-freedom overfit from two
     spuriously-placed dummies. The p-value asks whether the REAL labels beat that.

This exists because the delta-R^2 numbers previously lived only in NOTES.md prose --
block_bootstrap_ci / regime_delta_r2 were defined in evaluation.py but called by no
committed script (2026-07-21 audit, Finding 4). Running this file regenerates them.

Usage
-----
    python scripts/significance_test.py                 # defaults
    python scripts/significance_test.py --n-perm 5000   # tighter permutation p

Reads  : data/oos_regime_labels.csv, data/processed/spx_data.csv
Writes : results/significance_test.txt, results/significance_test.csv
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Windows consoles default to cp1252; keep output pure-ASCII to stay portable.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.config import DATA_DIR, RESULTS_DIR
from src.core.evaluation import (
    block_bootstrap_ci,
    block_permutation_test,
    regime_delta_r2,
)

# (target_kind, horizon_days) grid. Four tests -> Bonferroni across all four.
HORIZONS = [5, 21]
TARGET_KINDS = ['return', 'realized_vol']
FAMILY_ALPHA = 0.10   # family-wise error rate for the Bonferroni flag


# ===================================================================
# Data loading + target construction
# ===================================================================

def load_aligned():
    """Load OOS regime labels aligned with VIX and SPY returns on the same dates.

    Returns a DataFrame indexed by date with columns: regime_idx (int), vix,
    spy_ret. Every row is a genuinely out-of-sample day (post-TRAIN_END), labelled
    by the walk-forward ensemble in data/oos_regime_labels.csv.
    """
    oos_path = os.path.join(DATA_DIR, 'oos_regime_labels.csv')
    mkt_path = os.path.join(DATA_DIR, 'processed', 'spx_data.csv')
    if not os.path.exists(oos_path):
        raise FileNotFoundError(f"{oos_path} not found -- run walk-forward first "
                                f"(scripts/run.py walk_forward)")
    if not os.path.exists(mkt_path):
        raise FileNotFoundError(f"{mkt_path} not found -- run 'collect' first")

    oos = pd.read_csv(oos_path, index_col=0, parse_dates=True)
    mkt = pd.read_csv(mkt_path, index_col=0, parse_dates=True).reindex(oos.index)

    out = pd.DataFrame({
        'regime_idx': oos['regime_idx'].astype(int),
        'vix':        mkt['vol_index'],
        'spy_ret':    mkt['spy_ret'],
    }, index=oos.index)
    return out


def build_target(ret, kind, h):
    """Strictly-forward target over the h days AFTER each row (no leakage of day t).

    'return'       -> cumulative log return over ret[t+1 .. t+h]
    'realized_vol' -> annualized std (%) of ret[t+1 .. t+h]

    Both use rolling(h) (which looks back over [i-h+1 .. i]) then .shift(-h) to
    re-anchor onto day t, so day t's target depends only on returns strictly after t.
    """
    s = pd.Series(ret)
    if kind == 'return':
        return s.rolling(h).sum().shift(-h).values
    if kind == 'realized_vol':
        return (s.rolling(h).std().shift(-h) * np.sqrt(252) * 100).values
    raise ValueError(f"unknown target kind: {kind}")


# ===================================================================
# One (target, horizon) cell
# ===================================================================

def run_cell(df, kind, h, n_boot, n_perm, block_size, seed):
    """Run bootstrap + permutation for one (target, horizon) cell.

    Returns a result dict. perm_p is None if the permutation test isn't
    implemented yet (block_permutation_test raises NotImplementedError).
    """
    target = build_target(df['spy_ret'].values, kind, h)
    vix = df['vix'].values
    regime = df['regime_idx'].values

    mask = np.isfinite(target) & np.isfinite(vix)
    regime, vix, target = regime[mask].astype(int), vix[mask], target[mask]
    arrays = (regime, vix, target)

    observed, ci_lo, ci_hi, _ = block_bootstrap_ci(
        arrays, regime_delta_r2, n_boot=n_boot, block_size=block_size, seed=seed)

    perm_p = None
    try:
        _, perm_p, _ = block_permutation_test(
            arrays, regime_delta_r2, permute_arg=0,
            n_perm=n_perm, block_size=block_size, seed=seed)
    except NotImplementedError:
        pass

    return {
        'target': kind, 'horizon': h, 'n': int(mask.sum()),
        'delta_r2': observed, 'ci_low': ci_lo, 'ci_high': ci_hi,
        'perm_p': perm_p,
    }


# ===================================================================
# Reporting
# ===================================================================

def format_report(rows, n_tests):
    """Fixed-width ASCII table + Bonferroni flag. Returns the text block."""
    per_test_alpha = FAMILY_ALPHA / n_tests
    lines = []
    lines.append("=" * 78)
    lines.append("REGIME INFORMATION CONTENT -- SIGNIFICANCE TEST (out-of-sample)")
    lines.append(f"Generated: {pd.Timestamp.now():%Y-%m-%d %H:%M}")
    lines.append(f"Family-wise alpha={FAMILY_ALPHA:.2f} over {n_tests} tests "
                 f"-> Bonferroni per-test alpha={per_test_alpha:.4f}")
    lines.append("=" * 78)
    header = (f"{'Target':<14}{'Horiz':>6}{'N':>6}{'dR2':>10}"
              f"{'Boot 90% CI':>22}{'Perm p':>10}{'Signif':>8}")
    lines.append(header)
    lines.append("-" * 78)
    for r in rows:
        ci = f"[{r['ci_low']:.4f}, {r['ci_high']:.4f}]"
        if r['perm_p'] is None:
            perm, signif = "  --  ", "  --  "
        else:
            perm = f"{r['perm_p']:.4f}"
            signif = "YES" if r['perm_p'] < per_test_alpha else "no"
        lines.append(f"{r['target']:<14}{r['horizon']:>5}d{r['n']:>6}"
                     f"{r['delta_r2']:>10.5f}{ci:>22}{perm:>10}{signif:>8}")
    lines.append("-" * 78)
    if any(r['perm_p'] is None for r in rows):
        lines.append("")
        lines.append("PERMUTATION TEST NOT YET IMPLEMENTED.")
        lines.append("Bootstrap CIs above are real, but remember dR2 >= 0 by "
                     "construction -- the CI excluding 0 is expected and weak.")
        lines.append("Resume point: fill in block_permutation_test() in "
                     "src/core/evaluation.py (spec in the placeholder comment).")
    else:
        lines.append("Interpretation: 'Signif=YES' means the observed dR2 exceeds "
                     "the block-permuted null")
        lines.append("at the Bonferroni-corrected level -- the regime label carries "
                     "information beyond VIX.")
    return "\n".join(lines)


# ===================================================================
# Main
# ===================================================================

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n-boot', type=int, default=1000)
    ap.add_argument('--n-perm', type=int, default=1000)
    ap.add_argument('--block-size', type=int, default=21)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    df = load_aligned()
    print(f"Loaded {len(df)} OOS days ({df.index[0].date()} -> {df.index[-1].date()})")

    rows = []
    for kind in TARGET_KINDS:
        for h in HORIZONS:
            rows.append(run_cell(df, kind, h, args.n_boot, args.n_perm,
                                 args.block_size, args.seed))

    report = format_report(rows, n_tests=len(rows))
    print("\n" + report)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    txt_path = os.path.join(RESULTS_DIR, 'significance_test.txt')
    csv_path = os.path.join(RESULTS_DIR, 'significance_test.csv')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(report + "\n")
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f"\nWrote {txt_path} and {csv_path}")


if __name__ == '__main__':
    main()
