"""
Run the PCA -> HMM -> Regime-Dependent SV pipeline.

Usage:
    python run.py              # full pipeline
    python run.py collect      # data download only
    python run.py features     # feature engineering only
    python run.py analyze      # feature analysis / diagnostics
    python run.py train        # PCA + HMM + GARCH training
    python run.py regime       # print current regime awareness
    python run.py dashboard    # rebuild dashboard from saved model
"""

import sys
from collect import collect
from features import prepare_features
from analyze import analyze
from train import train, rebuild_dashboard


def print_regime():
    """Print current regime awareness from saved results (no retraining)."""
    import os
    import numpy as np
    import pandas as pd
    from config import DATA_DIR
    from signals import compute_signals

    path = os.path.join(DATA_DIR, 'regime_results.csv')
    if not os.path.exists(path):
        print("No regime_results.csv — run 'python run.py train' first.")
        return

    results = pd.read_csv(path, index_col=0, parse_dates=True)
    sigs = compute_signals(results)
    aw = sigs['awareness']
    dists = sigs['distributions']
    vol = sigs['vol_context']
    val = sigs['validation']
    current = aw['current_regime']

    W = 62
    print(f"\n{'=' * W}")
    print(f"  Regime Awareness — {sigs['date']}")
    print(f"{'=' * W}")

    # Current state
    conf = aw['confidence']
    conf_bar = '█' * int(conf * 20) + '░' * (20 - int(conf * 20))
    print(f"\n  Regime     : {current}")
    print(f"  Confidence : {conf:.0%}  {conf_bar}")
    print(f"  Streak     : {aw['days_in_regime']} days (median for this regime: {aw['median_duration']:.0f})")

    # Distribution you're playing
    print(f"\n{'─' * W}")
    print(f"  What distribution are you drawing from?")
    print(f"{'─' * W}")
    if current in dists.index:
        d = dists.loc[current]
        print(f"  Ann. Vol    : {d['ann_vol']*100:.1f}%")
        print(f"  Skew        : {d['skew']:.2f}  {'(left tail fatter)' if d['skew'] < -0.3 else '(right tail fatter)' if d['skew'] > 0.3 else '(roughly symmetric)'}")
        print(f"  Kurtosis    : {d['kurtosis']:.1f}  {'(fat tails!)' if d['kurtosis'] > 1 else '(near-normal tails)'}")
        print(f"  Daily VaR 5%: {d['var_5']*100:.2f}%  (expect to lose this much 1-in-20 days)")
        print(f"  Daily CVaR  : {d['cvar_5']*100:.2f}%  (avg loss on those bad days)")
        print(f"  Max DD      : {d['max_dd']*100:.1f}%")
        print(f"  Worst Day   : {d['worst_day']*100:.2f}%")
        is_n = d['is_normal'] if 'is_normal' in d.index else None
        jb = 'Non-normal (fat tails)' if is_n == False else 'Normal' if is_n == True else '?'  # noqa: E712
        print(f"  Normal?     : {jb}")

    # Vol context
    print(f"\n{'─' * W}")
    print(f"  Vol Context")
    print(f"{'─' * W}")
    print(f"  VIX         : {vol['vix']:.1f}" if vol['vix'] else "  VIX: N/A")
    print(f"  VRP         : {vol['vrp']:+.1f}  {vol['vrp_label']}" if vol['vrp'] else "  VRP: N/A")
    print(f"  Term Struct : {vol['term_structure_label']}")

    # Nearby transitions
    trans = sigs['transitions']
    if trans:
        print(f"\n{'─' * W}")
        print(f"  Nearby Regimes (non-trivial probability)")
        print(f"{'─' * W}")
        for t in trans:
            print(f"  {t['regime']:12s}  P={t['probability']:.1%}  ({t['direction']}, jump={t['severity_jump']})")

    # Validation
    print(f"\n{'─' * W}")
    print(f"  Model Validation — Is This Real?")
    print(f"{'─' * W}")
    sep = val.get('separation_significant', False)
    print(f"  Regime Separation: {'PASS' if sep else 'FAIL'}  (p={val.get('separation_pvalue', float('nan')):.2e})")
    print(f"  Vol Ordering     : {'PASS' if val.get('vol_ordering_match') else 'PARTIAL'}")
    print(f"  Persistence      : {val.get('persistence_interpretation', '—')}")
    var_bt = val.get('var_backtest', {})
    passes = sum(1 for v in var_bt.values() if v['ok'])
    print(f"  VaR Backtest     : {passes}/{len(var_bt)} regimes pass")

    print(f"\n{'=' * W}")
    print(f"  This model detects RISK REGIMES, not returns.")
    print(f"  Use it to size positions, set stops, and expect drawdowns.")
    print(f"{'=' * W}\n")


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if step in ('all', 'collect'):
        market = collect()

    if step in ('all', 'features'):
        prepare_features()

    if step in ('all', 'analyze'):
        analyze()

    if step in ('all', 'train'):
        train()

    if step == 'regime':
        print_regime()

    if step == 'dashboard':
        rebuild_dashboard()


if __name__ == '__main__':
    main()
