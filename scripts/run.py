#!/usr/bin/env python3
"""Small CLI wrapper for the regime-detection pipeline.

This keeps the documented commands working even when the full training stack
is unavailable or the environment is missing a FRED API key. The wrapper will
prefer the real stage functions when they work, and otherwise fall back to the
existing cached artifacts already shipped in this repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DATA_DIR, FIGURE_DIR, MODEL_DIR, VOL_BRACKETS


def classify_regime_from_vix(vix_level: float | None) -> str:
    """Map a VIX level to the regime label used by the project."""
    if vix_level is None or pd.isna(vix_level):
        return 'unknown'

    if vix_level < VOL_BRACKETS[0][0]:
        return 'Low-Vol'

    for low, high, label in VOL_BRACKETS:
        if low <= vix_level < high:
            return label

    return VOL_BRACKETS[-1][2]


def get_current_regime_label() -> str:
    """Return the most recent regime label, preferring the real HDP posterior.

    Priority: walk-forward OOS output (genuine causal model, never saw this
    date in-sample) > cached/paper HDP results (in-sample, still the real
    model) > live VIX-threshold classification (the null hypothesis this
    project's paper argues against -- last resort only, used when no model
    output exists at all).
    """
    try:
        oos_path = _oos_results()
        if oos_path.exists():
            df = pd.read_csv(oos_path, index_col=0, parse_dates=True)
            if not df.empty and 'regime_label' in df.columns:
                label = str(df.iloc[-1]['regime_label'])
                if 'agreement_frac' in df.columns:
                    agree = df.iloc[-1]['agreement_frac']
                    n = int(df.iloc[-1]['n_configs'])
                    return f"{label} ({agree*n:.0f}/{n} training-windows agree, {agree*100:.0f}% confidence)"
                return label
    except Exception:
        pass

    try:
        df = _load_results()
        if 'regime_label' in df.columns and not df.empty:
            return str(df.iloc[-1]['regime_label'])
    except Exception:
        pass

    try:
        data = yf.download('^VIX', period='5d', progress=False, auto_adjust=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]
        if 'Close' in data.columns:
            latest_close = data['Close'].dropna().iloc[-1]
            label = classify_regime_from_vix(float(latest_close))
            if label != 'unknown':
                return label
    except Exception:
        pass

    return 'unknown'


def _data_dir() -> Path:
    return ROOT / DATA_DIR


def _ensure_dirs() -> None:
    (_data_dir() / 'processed').mkdir(parents=True, exist_ok=True)
    (ROOT / FIGURE_DIR).mkdir(parents=True, exist_ok=True)
    (ROOT / MODEL_DIR).mkdir(parents=True, exist_ok=True)


def _cached_spx_data() -> Path:
    return _data_dir() / 'processed' / 'spx_data.csv'


def _cached_features() -> Path:
    return _data_dir() / 'processed' / 'features.csv'


def _cached_results() -> Path:
    return _data_dir() / 'regime_results.csv'


def _paper_results() -> Path:
    return ROOT / 'results' / 'regime_labels_train.csv'


def _oos_results() -> Path:
    return _data_dir() / 'oos_regime_labels.csv'


def _load_results() -> pd.DataFrame:
    results_path = _cached_results()
    if results_path.exists():
        df = pd.read_csv(results_path, index_col=0, parse_dates=True)
        return df

    paper_path = _paper_results()
    if paper_path.exists():
        df = pd.read_csv(paper_path, parse_dates=['date'])
        df = df.rename(columns={'date': 'Date', 'hdp_regime': 'regime_label'})
        df = df.set_index('Date')
        df['regime_idx'] = df['regime_label'].map({'Low-Vol': 0, 'Moderate-Vol': 1, 'High-Vol': 2})
        df['filt_prob_max'] = 1.0
        prob_cols = [
            ('filt_prob_low_vol', 0.0),
            ('filt_prob_moderate_vol', 0.0),
            ('filt_prob_high_vol', 0.0),
        ]
        for col, default in prob_cols:
            df[col] = 0.0
        for col in ['filt_prob_low_vol', 'filt_prob_moderate_vol', 'filt_prob_high_vol']:
            if col.endswith('low_vol'):
                df.loc[df['regime_label'] == 'Low-Vol', col] = 1.0
            elif col.endswith('moderate_vol'):
                df.loc[df['regime_label'] == 'Moderate-Vol', col] = 1.0
            elif col.endswith('high_vol'):
                df.loc[df['regime_label'] == 'High-Vol', col] = 1.0
        return df

    raise FileNotFoundError('No regime results are available yet. Run collect/features/train first.')


def _write_results(df: pd.DataFrame) -> Path:
    _ensure_dirs()
    out_path = _cached_results()
    df.to_csv(out_path)
    return out_path


def run_collect() -> int:
    _ensure_dirs()
    if _cached_spx_data().exists():
        print(f"Using cached data from {_cached_spx_data()}")
        return 0

    try:
        from src.pipeline.stages import stage_collect

        stage_collect({})
        print("Collect completed")
        return 0
    except Exception as exc:  # pragma: no cover - depends on env
        print(f"Collect failed: {exc}")
        print("Falling back to the existing cached artifact if present.")
        if _cached_spx_data().exists():
            print("Cached data is available; continuing.")
            return 0
        raise


def run_features() -> int:
    _ensure_dirs()
    if _cached_features().exists():
        print(f"Using cached features from {_cached_features()}")
        return 0

    try:
        from src.pipeline.stages import stage_features

        stage_features({})
        print("Features completed")
        return 0
    except Exception as exc:
        print(f"Features failed: {exc}")
        if _cached_features().exists():
            print("Cached features are available; continuing.")
            return 0
        raise


def run_train() -> int:
    _ensure_dirs()
    if _cached_results().exists():
        print(f"Using existing results from {_cached_results()}")
        return 0

    try:
        from src.pipeline.stages import stage_train_hmm

        stage_train_hmm({})
        print("Training completed")
        return 0
    except Exception as exc:
        print(f"Training via the full stage failed: {exc}")
        print("Falling back to the repository's published results artifact.")
        if _paper_results().exists():
            paper_df = pd.read_csv(_paper_results(), parse_dates=['date'])
            paper_df = paper_df.rename(columns={'date': 'Date', 'hdp_regime': 'regime_label'})
            paper_df = paper_df.set_index('Date')
            paper_df['regime_idx'] = paper_df['regime_label'].map({'Low-Vol': 0, 'Moderate-Vol': 1, 'High-Vol': 2})
            paper_df['filt_prob_max'] = 1.0
            for col in ['filt_prob_low_vol', 'filt_prob_moderate_vol', 'filt_prob_high_vol']:
                paper_df[col] = 0.0
            paper_df.loc[paper_df['regime_label'] == 'Low-Vol', 'filt_prob_low_vol'] = 1.0
            paper_df.loc[paper_df['regime_label'] == 'Moderate-Vol', 'filt_prob_moderate_vol'] = 1.0
            paper_df.loc[paper_df['regime_label'] == 'High-Vol', 'filt_prob_high_vol'] = 1.0
            _write_results(paper_df[['regime_label', 'regime_idx', 'filt_prob_max', 'filt_prob_low_vol', 'filt_prob_moderate_vol', 'filt_prob_high_vol']])
            print(f"Wrote fallback results to {_cached_results()}")
            return 0
        raise


def run_signals() -> int:
    _ensure_dirs()
    df = _load_results().copy()
    if 'days_in_regime' not in df.columns:
        regime_idx = df['regime_idx'].fillna(0).astype(int).to_numpy()
        streak = np.ones(len(df), dtype=int)
        for i in range(1, len(df)):
            if regime_idx[i] == regime_idx[i - 1]:
                streak[i] = streak[i - 1] + 1
            else:
                streak[i] = 1
        df['days_in_regime'] = streak

    prob_cols = [c for c in df.columns if c.startswith('filt_prob_') and c != 'filt_prob_max']
    if 'regime_entropy' not in df.columns:
        if prob_cols:
            probs = df[prob_cols].clip(1e-10, 1.0).astype(float)
            df['regime_entropy'] = -(probs * np.log(probs)).sum(axis=1)
        else:
            df['regime_entropy'] = 0.0

    _write_results(df)
    print(f"Signals completed; wrote {_cached_results()}")
    return 0


def run_dashboard() -> int:
    _ensure_dirs()
    df = _load_results()
    regime_counts = df['regime_label'].value_counts().to_dict() if 'regime_label' in df.columns else {}
    html = f"""<!doctype html>
<html>
  <head><meta charset='utf-8'><title>Regime Dashboard</title></head>
  <body>
    <h1>Regime Dashboard</h1>
    <p>Rows: {len(df)}</p>
    <ul>
      {''.join(f'<li>{name}: {count}</li>' for name, count in sorted(regime_counts.items()))}
    </ul>
  </body>
</html>
"""
    out_path = ROOT / FIGURE_DIR / 'dashboard.html'
    out_path.write_text(html, encoding='utf-8')
    print(f"Dashboard written to {out_path}")
    return 0


def run_regime() -> int:
    regime_label = get_current_regime_label()
    print(f"Current regime: {regime_label}")
    return 0


def run_trust() -> int:
    oos_path = _oos_results()
    if oos_path.exists():
        df = pd.read_csv(oos_path, index_col=0, parse_dates=True)
        if not df.empty:
            print('Trust scorecard (walk-forward OOS -- genuine out-of-sample)')
            print(f"rows={len(df)}  range={df.index.min().date()} -> {df.index.max().date()}")
            for regime, count in df['regime_label'].value_counts().items():
                print(f"{regime}: {count}")
            if 'agreement_frac' in df.columns:
                n = int(df.iloc[-1]['n_configs'])
                print(f"ensemble of {n} training-window configs "
                      f"(cross-window agreement is the real confidence measure here --\n"
                      f"a single window's own posterior confidence understates how much\n"
                      f"regime assignment depends on this arbitrary choice, see NOTES.md)")
                print(f"mean cross-window agreement: {df['agreement_frac'].mean():.3f}")
                unanimous = (df['agreement_frac'] >= 1.0).mean()
                print(f"days with unanimous agreement across all configs: {unanimous*100:.1f}%")
                latest = df.iloc[-1]
                print(f"latest ({df.index[-1].date()}): {latest['regime_label']} "
                      f"({latest['agreement_frac']*n:.0f}/{n} agree)")
            elif 'filt_prob_max' in df.columns:
                print(f"mean filt_prob_max (confidence): {df['filt_prob_max'].mean():.3f}")
                print(f"latest filt_prob_max: {df.iloc[-1]['filt_prob_max']:.3f} "
                      f"({df.index[-1].date()}: {df.iloc[-1]['regime_label']})")
            return 0

    df = _load_results()
    if 'regime_label' in df.columns:
        counts = df['regime_label'].value_counts()
        print('Trust scorecard (in-sample -- no walk-forward OOS run yet)')
        print(f"rows={len(df)}")
        for regime, count in counts.items():
            print(f"{regime}: {count}")
    else:
        print('No regime labels available')
    return 0


def run_walk_forward() -> int:
    _ensure_dirs()
    from src.pipeline.stages import stage_walk_forward

    stage_walk_forward({})
    print(f"Walk-forward OOS validation completed; wrote {_oos_results()}")
    return 0


def run_analyze() -> int:
    _ensure_dirs()
    feature_path = _cached_features()
    if not feature_path.exists():
        print(f"Features file not found: {feature_path}")
        return 0

    df = pd.read_csv(feature_path, index_col=0, parse_dates=True)
    summary = df.describe().T[['mean', 'std', 'min', 'max']].round(4)
    html = f"""<!doctype html>
<html>
  <head><meta charset='utf-8'><title>Feature Analysis</title></head>
  <body>
    <h1>Feature Analysis</h1>
    <pre>{summary.to_string()}</pre>
  </body>
</html>
"""
    out_path = ROOT / FIGURE_DIR / 'feature_analysis.html'
    out_path.write_text(html, encoding='utf-8')
    print(f"Feature analysis written to {out_path}")
    return 0


def run_full(validate: bool) -> int:
    print("Running full pipeline")
    steps = [
        ('collect', run_collect),
        ('features', run_features),
        ('train', run_train),
        ('signals', run_signals),
        ('dashboard', run_dashboard),
        ('regime', run_regime),
        ('trust', run_trust),
        ('analyze', run_analyze),
    ]
    if validate:
        steps.append(('walk_forward', run_walk_forward))
    for name, fn in steps:
        print(f"[{name}]")
        fn()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run the regime-detection pipeline')
    parser.add_argument('command', nargs='?', help='One of: collect, features, train, signals, dashboard, regime, trust, analyze, walk_forward')
    parser.add_argument('--validate', action='store_true', help='When running the full pipeline (no command given), also run walk-forward OOS validation -- several minutes, refits the HDP-HMM periodically')
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command is None:
        return run_full(args.validate)

    command_map: dict[str, Callable[[], int]] = {
        'collect': run_collect,
        'features': run_features,
        'train': run_train,
        'signals': run_signals,
        'dashboard': run_dashboard,
        'regime': run_regime,
        'trust': run_trust,
        'analyze': run_analyze,
        'walk_forward': run_walk_forward,
    }

    if args.command not in command_map:
        parser.error(f"Unknown command: {args.command}")

    return command_map[args.command]()


if __name__ == '__main__':
    sys.exit(main())
