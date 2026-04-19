# Phase 5: Feature Engineering Overhaul - Pattern Map

**Mapped:** 2026-04-18
**Files analyzed:** 5 (3 new, 2 modified)
**Analogs found:** 5 / 5

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/features/features.py` | feature-engineering utility | transform (expand) | `src/features/features.py` (itself — add to it) | exact (modification) |
| `src/data/collect_macro.py` | data-collection utility | file-I/O (external API → CSV) | `src/features/collect.py` | role-match |
| `scripts/analysis/walk_forward_feature_selection.py` | analysis script | batch (walk-forward CV) | `scripts/analysis/analyze_feature_selection.py` + `src/core/orchestrator.py` | role-match (composite) |
| `src/config.py` | config | N/A (update in-place) | `src/config.py` (itself) | exact (modification) |
| `data/feature_importance_report.md` | report artifact | N/A (write-once output) | `scripts/analysis/analyze_regime_characterization.py` → `reports/diagnostics_report.md` | role-match |

---

## Pattern Assignments

### `src/features/features.py` — add `build_section_signals()` (feature-engineering utility, transform)

**Analog:** `src/features/features.py` — modification of existing file.

**Imports pattern already in file** (lines 18–25):
```python
import pandas as pd
import numpy as np
import os

from src.config import (
    TICKERS, SHORT_WINDOW, MED_WINDOW, LONG_WINDOW,
    DATA_DIR, MODEL_DIR,
)
```
Add to imports: `from sklearn.decomposition import PCA` and `from sklearn.preprocessing import StandardScaler`. These are already used in `prepare_features()` via a local import (line 310); move to module level for `build_section_signals()`.

**Core feature-builder pattern** (lines 86–232) — follow this structure for `build_section_signals()`:
- Accept `features: pd.DataFrame` (output of `build_features()`)
- Guard for missing columns with `[c for c in feat_cols if c in features.columns]`
- Return a `pd.DataFrame` with named columns
- No `dropna()` inside — let the caller decide (consistent with how `build_features()` returns)

**Rolling causal PCA pattern** (lines 333–353 of `prepare_features()`):
```python
# Fit on latest pca_window rows only — CAUSAL (no future data)
fit_data = features.iloc[-pca_window:, :].values
pca = PCA(n_components=5, random_state=42)
pca.fit(fit_data)
# Transform all rows using that PCA
X_pca = pca.transform(features.values)
pca_features = pd.DataFrame(
    X_pca,
    columns=[f'PC{i+1}' for i in range(X_pca.shape[1])],
    index=features.index,
)
```
For `build_section_signals()`, apply this per-section with `n_components=1` and add sign correction (see RESEARCH.md Pattern 1 and Pitfall 1).

**GLD trend feature** — follow the realized-vol pattern (lines 118–122) which computes a rolling transform on a price series:
```python
# Pattern: log ratio over a rolling window (causal by construction)
if spy_close is not None:
    spy_ret = pd.Series(np.log(spy_close / spy_close.shift(1)),
                        index=market.index)
```
Adapt for `GLD_trend`:
```python
if 'GLD_close' in market.columns:
    gld = market['GLD_close']
    f['GLD_trend'] = np.log(gld / gld.shift(LONG_WINDOW)).rename('GLD_trend')
```

**Validation guard pattern** (lines 218–231):
```python
# NaN reporting before dropna — copy this for section signals
na_counts = f.isna().sum()
binding = na_counts[na_counts > 0].sort_values(ascending=False)
if not binding.empty:
    print(f"  Feature NaN counts (top 5 binding constraints):")
    for feat, cnt in binding.head(5).items():
        print(f"    {feat}: {cnt} NaN rows")
f = f.dropna()
assert len(f) >= 252, (...)
```

**CURATED_FEATURES list** (lines 57–83) — extend this list with new FRED features after adding them:
```python
CURATED_FEATURES = [
    'VIX', 'VRP', 'rv_ratio_10_63', 'vix_ts_slope', 'SPY_volvol20',
    'SPY_TLT_corr63', 'credit_stress',
    'SPY_ret', 'SPY_skew20', 'SPY_ac1_20',
    'eigen_conc', 'SPY_dd63',
    'SPY_rel_volume', 'SPY_vol_adj_ret',
    'SPY_rv10_lag5', 'SPY_rv10_lag10',
    'lev_effect20',
    # Phase 5 additions:
    'HY_OAS', 'NFCI', 'yield_curve_slope', 'GLD_trend',
]
```

**Section map and anchor constants** — add at module level below `CURATED_FEATURES` (before `build_features()`). Follow the same convention as `_LOG_TRANSFORM_COLS` (line 242): module-level dict, underscore-private if internal:
```python
# src/features/features.py lines 241-243 pattern for module-level constants:
_LOG_TRANSFORM_COLS = {
    'VIX', 'rv_ratio_10_63',
    'eigen_conc',
}
```

---

### `src/data/collect_macro.py` (NEW — data-collection utility, file-I/O)

**Analog:** `src/features/collect.py` (the yfinance collector)

**Module docstring pattern** (collect.py lines 1–7):
```python
"""
Data collection: OHLCV from yfinance, VIX family from Yahoo.
Aligns everything to SPY's trading-day index and saves raw data.

Supports incremental data collection with cache manifest and delta detection.
"""
```
Mirror for collect_macro.py:
```python
"""
Macro data collection: FRED series via fredapi.
Fetches T10Y2Y, BAMLH0A0HYM2, NFCI. Aligns to business-day frequency
and saves to data/macro_data.csv alongside market_data.csv.
"""
```

**Imports pattern** (collect.py lines 9–21):
```python
import pandas as pd
import numpy as np
import yfinance as yf
import os
import json
import hashlib
from datetime import datetime

from src.config import (
    START_DATE, END_DATE,
    TICKERS, VIX_TICKER, VIX3M_TICKER, VVIX_TICKER,
    DATA_DIR, CACHE_PATH, INCREMENTAL_MODE,
)
```
For collect_macro.py, substitute fredapi-specific imports and config:
```python
import os
import pandas as pd
from fredapi import Fred

from src.config import START_DATE, DATA_DIR, FRED_API_KEY
```

**Data alignment pattern** (collect.py lines 282–300) — aligning multiple series to a reference index with forward-fill:
```python
ref_index = ohlcv['SPY'].index
if not isinstance(ref_index, pd.DatetimeIndex):
    ref_index = pd.to_datetime(ref_index)

market = pd.DataFrame(index=ref_index)

for ticker in TICKERS:
    df = ohlcv[ticker]
    for field in ['Close', 'High', 'Low', 'Open']:
        series = df[field].squeeze()
        market[f'{ticker}_{field.lower()}'] = series.reindex(ref_index).ffill()
```
For FRED data, alignment is `resample('B').last().ffill()` (business-day forward-fill). The causal guarantee is the same pattern as the yfinance `.reindex(ref_index).ffill()`.

**Save pattern** (collect.py lines 308–310):
```python
os.makedirs(DATA_DIR, exist_ok=True)
market.to_csv(os.path.join(DATA_DIR, 'market_data.csv'))
```
Mirror exactly for macro data:
```python
os.makedirs(DATA_DIR, exist_ok=True)
macro_df.to_csv(os.path.join(DATA_DIR, 'macro_data.csv'))
```

**Input validation pattern** (collect.py lines 303–307):
```python
assert len(market) >= 252, (
    f"Insufficient data after alignment: {len(market)} trading days "
    f"(need >= 252). Check date range or data sources."
)
```
Copy this assertion pattern. For FRED data, additionally validate that the response is non-empty before merging (RESEARCH.md Security §V5).

**`__main__` guard pattern** (collect.py lines 417–419):
```python
if __name__ == '__main__':
    mode_used, delta_rows, tickers_refreshed, market = collect()
    print(f"\nResult: mode={mode_used}, delta_rows={delta_rows}, tickers={tickers_refreshed}")
```

**No analog for fredapi call itself** — use RESEARCH.md Pattern 2 (the `fetch_fred_series()` example) as the reference pattern. The key elements: `Fred(api_key=...)`, `fred.get_series(code, observation_start=start)`, `s.resample('B').last().ffill()`.

---

### `scripts/analysis/walk_forward_feature_selection.py` (NEW — analysis script, batch walk-forward)

**Primary analog:** `scripts/analysis/analyze_feature_selection.py` (structural template)
**Secondary analog:** `src/core/orchestrator.py` `walk_forward()` function (walk-forward loop mechanics)

**Module docstring pattern** (analyze_feature_selection.py lines 1–11):
```python
"""
Feature selection bias analysis: Compare original 7 features vs new features...

This script performs out-of-sample feature selection validation:
1. Split data: Train (2010–2020) vs Test (2021–2026, held-out)
2. Evaluate baseline with original 7 features on test set
...
"""
```

**Imports pattern** (analyze_feature_selection.py lines 14–30):
```python
import os
import sys
import numpy as np
import pandas as pd
import logging
from datetime import datetime

from src.config import (
    FEATURE_SUBSET, DATA_DIR, RANDOM_SEED, REGIME_NAMES,
    PCA_MAX_COMPONENTS, PCA_VAR_THRESHOLD, PCA_ROLLING_WINDOW
)
from src.features.features import build_features
from src.core.inference import expanding_standardize, filtered_labels, StudentTHMM
from src.core.hmm_training import fit_rolling_pca, label_regimes, check_stability
from src.core.evaluation import evaluate, compute_var_backtest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```
For the new walk-forward script, additionally import:
```python
from sklearn.feature_selection import mutual_info_classif
from src.features.features import build_section_signals
from src.config import (
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS,
    N_STATES, DATA_DIR, RANDOM_SEED,
)
```

**Data loading pattern** (analyze_feature_selection.py lines 37–68):
```python
def load_and_split_data():
    """Load market data and split into train (2010–2020) and test (2021–2026)."""
    market_path = os.path.join(DATA_DIR, 'market_data.csv')
    features_path = os.path.join(DATA_DIR, 'features_transformed.csv')

    if not os.path.exists(market_path):
        raise FileNotFoundError(f"Market data not found: {market_path}")

    market = pd.read_csv(market_path, index_col=0, parse_dates=True)
    features = pd.read_csv(features_path, index_col=0, parse_dates=True)

    # Align indices
    market = market.loc[features.index]
```
Also load `data/macro_data.csv` and merge with features before passing to `build_section_signals()`.

**Walk-forward loop pattern** (orchestrator.py lines 55–156):
```python
# orchestrator.py lines 55-63 — init pattern
min_train = WALK_FORWARD_TRAIN_YEARS * 252
step = WALK_FORWARD_STEP_DAYS

oos_name_labels = pd.Series(index=features.index, dtype=object)
oos_name_labels[:] = np.nan

t = min_train
step_num = 0
while t < len(features):
    end = min(t + step, len(features))
```

```python
# orchestrator.py lines 65-71 — rolling window slice pattern
if mode == 'rolling':
    # Fixed-length rolling window
    train_start = max(0, t - min_train)
    train_feats = features.iloc[train_start:t]
else:
    # Expanding window (all past data)
    train_feats = features.iloc[:t]
test_feats = features.iloc[t:end]
```

```python
# orchestrator.py lines 91-97 — PCA fit on rolling window, then project all pattern
pca_window = min(PCA_ROLLING_WINDOW, len(X_train))
n_comp = min(n_pca, X_train.shape[1])
pca_wf = PCA(n_components=n_comp, random_state=RANDOM_SEED)
pca_wf.fit(X_train[-pca_window:])
pc_train = pca_wf.transform(X_train)
pc_test = pca_wf.transform(X_test)
```
Replicate this pattern inside the walk-forward loop for section PCA: refit `build_section_signals()` (or section PCA) on `train_feats` only, then compute section signals for test fold using those same PCA weights.

**Section signal MI ranking pattern** (analyze_feature_selection.py lines 75–131 — correlation-based; replace with MI):
```python
# The existing script ranks by variance (line 128). Replace with MI:
# from sklearn.feature_selection import mutual_info_classif
mi_scores = mutual_info_classif(
    X_train, y_train,
    discrete_features=False,
    random_state=RANDOM_SEED,
    n_jobs=-1,
)
```

**Progress print pattern** (orchestrator.py lines 153–155):
```python
step_num += 1
if step_num % 10 == 0:
    print(f"    step {step_num}")
t = end
```

**Config auto-update pattern** — not directly present in analogs; infer from how `FEATURE_SUBSET` is formatted in config.py (lines 38–49). The script should write a Python-parseable assignment. Pattern from analyze_feature_selection.py report-writing (lines 417–467):
```python
report_path = os.path.join(DATA_DIR, 'feature_selection_report.txt')
with open(report_path, 'w') as f:
    f.write("="*70 + "\n")
    ...
    f.write(f"Decision features: {decision_features}\n\n")
```
For config update, read config.py as text, find `FEATURE_SUBSET = [`, replace the block, write back. Preserve old value in a comment above — this is the D-08 requirement.

**`main()` + `if __name__ == '__main__'` pattern** (analyze_feature_selection.py lines 291–493):
```python
def main():
    """Run feature selection bias analysis."""
    print("\n" + "="*70)
    print("FEATURE SELECTION BIAS ANALYSIS")
    print("="*70)
    ...
    # Sections: load data → run analysis → write report → print summary

if __name__ == '__main__':
    main()
```

**Section-structured print pattern** (analyze_regime_characterization.py lines 644–688):
```python
def main():
    print("Regime characterization analysis (Phase 4 — Empirical Diagnostics)...")
    results = load_regime_results()
    market = load_market_data()

    print("\n--- DIAG-01: Regime Characterization Figures ---")
    stats_info = analyze_regime_statistics(results, market)
    ...
    print("\n--- Writing diagnostics_report.md ---")
    write_diagnostics_report(...)

    print("\nPhase 4 diagnostic analysis complete.")
    print("  Figures:  figures/diag01_*.png")
    print("  Report:   reports/diagnostics_report.md")
```
Mirror for walk-forward script: one `main()` function with clearly labelled sections (load → build sections → walk-forward MI → aggregate → write report → update config).

---

### `src/config.py` — add `FRED_API_KEY`, update `FEATURE_SUBSET` (config modification)

**Analog:** `src/config.py` (itself — in-place modification)

**Env-var config pattern** (config.py existing pattern — no direct env var currently; infer from project conventions):
Add after the `import os` at line 6:
```python
# --- External API keys ---
FRED_API_KEY = os.getenv('FRED_API_KEY', '')  # Set env var before running collect_macro.py
```
Follow the existing inline comment style (see lines 52–55) explaining reasoning.

**FEATURE_SUBSET update pattern** (config.py lines 35–49):
```python
# Representative feature subset for PCA (reduces collinearity).
# ...
# Updated per Phase 2.5.2: Feature selection on held-out train set (2010-2020)
# improved OOS regime accuracy from 72.7% to 76.2% and dwell time from 5.6 to 17.7 days.
# See data/feature_selection_report.txt for full analysis.
FEATURE_SUBSET = [
    # Vol state
    'VRP', 'VIX',
    # Return dynamics
    'SPY_skew20',
    # Cross-asset
    'SPY_TLT_corr63',
    # Leverage / fragility
    'lev_effect20',
    # Vol dynamics
    'rv_ratio_10_63',
]
```
When the walk-forward script updates this block, it must:
1. Comment out the old `FEATURE_SUBSET = [...]` with `# Phase 5 replaced:` prefix
2. Write a new `FEATURE_SUBSET = [...]` with inline `# Phase 5 walk-forward selected` comment
3. Preserve the descriptive comment block above (lines 35–38)

---

### `data/feature_importance_report.md` (NEW — report artifact, write-once)

**Analog:** `scripts/analysis/analyze_regime_characterization.py` → `reports/diagnostics_report.md`

**Report-writing function pattern** (analyze_regime_characterization.py lines 475–641):
```python
def write_diagnostics_report(stats_info, transition_info, ...):
    """Write structured diagnostics report to reports/diagnostics_report.md."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    lines = []

    lines.append("# Empirical Diagnostics Report — Phase 4")
    lines.append("")
    lines.append(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d')}")
    lines.append(f"**OOS Period:** {OOS_START} onwards")
    lines.append("")
    lines.append("---")
    ...
    report_path = os.path.join(REPORTS_DIR, 'diagnostics_report.md')
    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"\n  Saved: {report_path}")
```
For `feature_importance_report.md`, mirror this exact structure: build `lines` list, write with `'\n'.join(lines)`, print confirmation.

**Markdown table pattern** (analyze_regime_characterization.py lines 499–509):
```python
lines.append("| Regime | Mean Duration (days) | Median | Max | Episodes |")
lines.append("|--------|---------------------|--------|-----|----------|")
for row in duration_info['duration_stats']:
    lines.append(
        f"| {row['Regime']} | {row['Mean Duration']:.1f} | "
        f"{row['Median Duration']:.1f} | {row['Max Duration']:.0f} | "
        f"{row['N Episodes']} |"
    )
```
Feature importance report needs two tables:
- Section × fold selection matrix (sections as rows, fold index as columns, 1/0 values)
- Summary table: section name, selection frequency (%), mean OOS MI score, economic rationale note

**Report save path:** `data/feature_importance_report.md` (not `reports/`). Follow existing pattern that report artifacts go to `DATA_DIR`:
```python
# analyze_feature_selection.py line 417:
report_path = os.path.join(DATA_DIR, 'feature_selection_report.txt')
```

---

## Shared Patterns

### FRED Data Alignment (causal forward-fill)
**Source:** `src/features/collect.py` lines 282–300 (yfinance alignment) + RESEARCH.md Pattern 2
**Apply to:** `src/data/collect_macro.py`, and inside walk-forward fold when merging macro features

The canonical causal alignment for non-daily series is:
```python
s = fred.get_series(code, observation_start=start)
s = s.resample('B').last().ffill()  # business-day, causal forward-fill
```
This is structurally identical to collect.py's `.reindex(ref_index).ffill()` — same causal guarantee, different frequency source.

### Rolling Causal PCA
**Source:** `src/features/features.py` lines 333–353 (`prepare_features()`), `src/core/orchestrator.py` lines 91–97
**Apply to:** `build_section_signals()` in features.py, and inside each fold of walk_forward_feature_selection.py

Critical invariant shared by both: **fit on `[-pca_window:]` of training data only, transform all rows**. Never fit on full history.

```python
# orchestrator.py lines 92-97 — the canonical pattern to copy:
pca_wf = PCA(n_components=n_comp, random_state=RANDOM_SEED)
pca_wf.fit(X_train[-pca_window:])
pc_train = pca_wf.transform(X_train)
pc_test = pca_wf.transform(X_test)
```

### Config Import Pattern
**Source:** `src/features/features.py` lines 22–25, `src/core/orchestrator.py` lines 15–19
**Apply to:** All new/modified files

Both use explicit named imports from `src.config`, never `from src.config import *`:
```python
# features.py pattern:
from src.config import (
    TICKERS, SHORT_WINDOW, MED_WINDOW, LONG_WINDOW,
    DATA_DIR, MODEL_DIR,
)

# orchestrator.py pattern:
from src.config import (
    RANDOM_SEED, PCA_ROLLING_WINDOW, REGIME_HOLD_DAYS, VIX_BYPASS,
    WALK_FORWARD_TRAIN_YEARS, WALK_FORWARD_STEP_DAYS, WALK_FORWARD_MODE,
    COV_TYPE, VOL_BRACKETS,
)
```

### Report Writing Pattern
**Source:** `scripts/analysis/analyze_regime_characterization.py` lines 475–641
**Apply to:** `data/feature_importance_report.md` write function in walk_forward_feature_selection.py

Key elements: `os.makedirs(dir, exist_ok=True)`, build `lines` list, write with `'\n'.join(lines)`, `print(f"  Saved: {path}")`.

### Standalone Script Guard
**Source:** `src/features/collect.py` lines 417–419, `scripts/analysis/analyze_regime_characterization.py` lines 689–690, `scripts/analysis/analyze_feature_selection.py` line 493
**Apply to:** `src/data/collect_macro.py`, `scripts/analysis/walk_forward_feature_selection.py`

All standalone scripts end with:
```python
if __name__ == '__main__':
    main()
```

### Defensive Column Check Pattern
**Source:** `src/features/features.py` lines 97–100, 124–125, 128–129, 132–133
**Apply to:** `build_section_signals()` in features.py, any macro feature computation

```python
# Pattern: guard every feature computation with column existence check
if 'VIX' in market.columns:
    f['VIX'] = market['VIX']

if 'VIX' in market.columns and rv20 is not None:
    f['VRP'] = market['VIX'] - rv20 * 100
```
For section signals: `available = [c for c in feat_cols if c in features.columns]`

---

## No Analog Found

All files have at least a role-match analog. The following specific sub-patterns have no codebase analog and must follow RESEARCH.md examples:

| Sub-pattern | Needed By | RESEARCH.md Reference |
|-------------|-----------|----------------------|
| `fredapi.Fred.get_series()` call | `collect_macro.py` | Pattern 2 (lines 216–233) |
| PCA sign correction via anchor feature | `build_section_signals()` in features.py | Pattern 1, Pitfall 1 (lines 167–203, 413–415) |
| `mutual_info_classif` walk-forward stability filter | `walk_forward_feature_selection.py` | Pattern 3 (lines 249–312) |
| `SECTION_MAP` / `SECTION_ANCHORS` constants | `features.py` | Code Examples §Section signal construction (lines 497–551) |
| Config FEATURE_SUBSET in-place text replacement | `walk_forward_feature_selection.py` | D-08 in CONTEXT.md |

---

## Metadata

**Analog search scope:** `src/features/`, `src/data/`, `src/core/`, `scripts/analysis/`, `src/config.py`, `tests/`
**Files read:** 8 (features.py, config.py, collect.py, orchestrator.py, analyze_feature_selection.py, analyze_feature_importance.py, analyze_regime_characterization.py, test_causality.py)
**Pattern extraction date:** 2026-04-18

**Key invariant confirmed by two independent analogs:** Rolling causal PCA (fit on `[-pca_window:]`, transform all) appears in both `prepare_features()` (features.py:334) and `walk_forward()` (orchestrator.py:94). This is the single most important pattern to replicate in Phase 5 — any deviation breaks the OOS guarantee.
