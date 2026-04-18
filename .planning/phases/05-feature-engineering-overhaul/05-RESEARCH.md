# Phase 5: Feature Engineering Overhaul — Research

**Researched:** 2026-04-18
**Domain:** Sectioned funnel feature architecture for HMM-based equity regime detection
**Confidence:** MEDIUM — architecture pattern is validated by analogy; no canonical "sectioned funnel HMM" paper found. Feature candidates and aggregation methods are HIGH confidence.

---

> **NOTE ON CONTEXT.MD:** The 05-CONTEXT.md file is OUTDATED. It describes the original
> scope (walk-forward selection from existing 17 features, no new engineering). The user has
> since redirected Phase 5 to a sectioned funnel architecture redesign. This RESEARCH.md
> reflects the new direction. The planner MUST use this file, not CONTEXT.md.

---

## Summary

The current pipeline feeds 17 flat features directly into a single PCA, then into the HMM. Because 9–10 of the 17 features are volatility-derived (VIX, VRP, rv_ratio_10_63, SPY_volvol20, vix_ts_slope, lev_effect20, SPY_rv10_lag5, SPY_rv10_lag10, and credit_stress which correlates with vol), PC1 of the joint PCA captures the vol factor and PC2–PC5 fragment the remaining signal. The HMM then receives a vol-heavy rotation.

The sectioned funnel redesign addresses this by grouping features into thematic sections, reducing each section to a single balanced signal (via PC1 or equal-weight z-score), then feeding the K=3–4 section signals into PCA and HMM. This guarantees each economic dimension contributes equally at the HMM input stage, regardless of how many raw features it contributed.

This pattern is structurally identical to how the Chicago Fed constructs CFNAI (85 indicators → PC1 per conceptual group → composite index) and how the Macrosynergy `linear_composite` function builds thematic macro scores. It is not a named "sectioned funnel" in the literature, but is a well-established composite indicator construction methodology applied to HMM inputs. [CITED: chicagofed.org/research/data/cfnai/about]

**Primary recommendation:** Implement 4 sections (Macro/Economic Cycle, Financial Conditions/Credit, Volatility, Market Structure/Trend). Reduce each section to PC1 using rolling causal PCA (same pattern as current rolling PCA in features.py). Feed 4 section signals into existing PCA → HMM pipeline. Walk-forward selection runs on section signals, not raw features.

---

<user_constraints>
## User Constraints (from CONTEXT.md — NOTE: CONTEXT.md scope is superseded by this research)

### Original Locked Decisions (OUTDATED — superseded by new direction)
The CONTEXT.md decisions (D-01 through D-10) described walk-forward selection from existing 17 features with no new engineering. The user has redirected to a sectioned funnel architecture that:
- Organizes features into thematic sections
- Reduces each section to one balanced signal
- Adds new features to under-represented sections
- Uses walk-forward validation on section signals

### Preserved Constraints (still apply)
- Walk-forward validation is required (FEAT-02) — 3yr train / 1yr OOS, rolling
- Walk-forward stability threshold ≥60% of folds
- Primary metric: mutual information with regime label (FEAT-03)
- Auto-update config.py FEATURE_SUBSET with results
- Report to data/feature_importance_report.md
- Script in scripts/analysis/

### Claude's Discretion (from original context — still applicable)
- Exact top-N cutoff per fold before applying the 60% aggregation threshold
- Whether to run a final validation pass after updating FEATURE_SUBSET

### Deferred Ideas (OUT OF SCOPE)
None defined.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FEAT-01 | Feature candidate set expanded to 12+ with economic rationale | Sectioned architecture adds 4–6 new FRED-derived features (T10Y2Y, BAMLH0A0HYM2, NFCI, GLD_trend) to under-represented sections; total candidates expand from 17 to ~22 |
| FEAT-02 | Feature selection uses walk-forward CV — no held-out split bias | Walk-forward runs on section signals (4–5 signals) using existing orchestrator pattern; 3yr/1yr rolling windows, ≥60% fold stability |
| FEAT-03 | Feature importance documented — which features drive regime separation on OOS data | Section MI scores per fold, final selection frequency table, short economic rationale per section |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Within-section aggregation (raw → signal) | `src/features/features.py` | — | Feature engineering lives here; section PC1 is another transform step |
| FRED data collection for new features | `src/data/collect.py` or new `src/data/collect_macro.py` | — | Existing collect.py fetches yfinance; FRED requires separate fredapi call |
| Section signal construction | `src/features/features.py` (new `build_section_signals()`) | — | Keeps feature pipeline in one place |
| Walk-forward feature selection script | `scripts/analysis/walk_forward_feature_selection.py` | — | Consistent with Phase 4 pattern |
| Config update (FEATURE_SUBSET) | `src/config.py` | — | Config is the single source of truth for downstream pipeline |
| Section signal → HMM integration | `src/core/orchestrator.py` (no change needed if FEATURE_SUBSET updated) | — | Orchestrator already reads FEATURE_SUBSET; updating that list is sufficient |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scikit-learn | 1.7.0 [VERIFIED: local install] | `mutual_info_classif`, `PCA`, `StandardScaler` | Already in project; mutual_info_classif supports n_jobs parallelism since 1.5 |
| fredapi | 0.5.2 [VERIFIED: local install] | Fetch FRED macro series | Installed; direct API access without browser |
| pandas-datareader | 0.10.0 [VERIFIED: local install] | Alternative FRED access via `pdr.get_data_fred()` | Installed; works for batch series download |
| pandas | 2.3.1 [VERIFIED: local install] | Rolling operations, resampling, forward-fill | Core data layer |
| numpy | 2.3.1 [VERIFIED: local install] | Array operations for section aggregation | Core compute layer |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yfinance | existing in project | GLD price data for Macro section trend | Already collected in collect.py; reuse existing GLD_close |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PC1 section signal | Equal-weight z-score composite | Equal-weight is simpler but loses within-section variance structure; PC1 preserves the dominant direction of co-movement and is the approach used by CFNAI [CITED: chicagofed.org] |
| PC1 section signal | MI-ranked top-1 feature | Top-1 feature discards within-section diversification; PC1 blends all section features |
| fredapi | requests + FRED CSV download | fredapi is cleaner, handles rate limits; both valid |

**Installation:** No new installs needed — all required libraries are present. [VERIFIED: local pip show]

---

## Architecture Patterns

### System Architecture Diagram

Current architecture:
```
FRED + yfinance raw data
         |
    build_features()  ←── 17 flat features (vol-heavy)
         |
   rolling PCA (all 17 → 5 PCs)
         |
   vol dominates PC1
         |
    HMM (K=3)
```

New sectioned funnel architecture:
```
FRED + yfinance raw data
         |
    build_features()  ←── expanded to ~22 features
         |
    ┌────────────────────────────────────────────────┐
    │  Section grouping (4 sections)                 │
    │                                                │
    │  [Macro/Cycle features] → rolling PC1 → s_mac │
    │  [FinCond/Credit feat.] → rolling PC1 → s_fin │
    │  [Volatility features]  → rolling PC1 → s_vol │
    │  [Mkt Structure feat.]  → rolling PC1 → s_str │
    └────────────────────────────────────────────────┘
         |
    4-column section signal DataFrame
         |
   walk-forward MI selection (which sections survive ≥60% folds)
         |
   update FEATURE_SUBSET in config.py
         |
   rolling PCA on selected section signals → HMM (K=3)
```

### Recommended Project Structure
```
src/features/
├── features.py          # existing — add new FRED features + build_section_signals()
src/data/
├── collect.py           # existing yfinance collect
├── collect_macro.py     # NEW: fredapi calls for T10Y2Y, BAMLH0A0HYM2, NFCI
scripts/analysis/
├── walk_forward_feature_selection.py  # NEW: operates on section signals
data/
├── macro_data.csv        # NEW: FRED series cached to disk (same pattern as market_data.csv)
├── feature_importance_report.md  # NEW: per-section fold selection table
```

### Pattern 1: Rolling Causal Section PC1

**What:** For each section, fit PCA(n_components=1) on the last `pca_window` rows of section features (causal), then transform full history. This yields a single scalar time series that captures the dominant direction of co-movement within the section.

**When to use:** Whenever a section has 2+ features. Single-feature sections pass through directly (no PCA needed).

**Example:**
```python
# Source: Adapted from existing prepare_features() rolling PCA pattern in src/features/features.py
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

def section_to_signal(section_df: pd.DataFrame, pca_window: int = 252) -> pd.Series:
    """Reduce N-feature section to PC1 signal using causal rolling PCA.
    
    Causal: PCA fitted on latest pca_window rows only (no future data leakage).
    If section has only 1 feature, returns that feature directly.
    """
    if section_df.shape[1] == 1:
        return section_df.iloc[:, 0].rename(section_df.columns[0])
    
    # Standardize features before PCA (required for fair weighting within section)
    scaler = StandardScaler()
    fit_data = section_df.iloc[-pca_window:].values
    scaler.fit(fit_data)
    X_std = scaler.transform(section_df.values)
    
    # Fit PCA on latest window (causal)
    pca = PCA(n_components=1, random_state=42)
    pca.fit(X_std[-pca_window:])
    
    # Transform all rows
    signal = pca.transform(X_std).squeeze()
    
    # Sign-correct: ensure signal positively correlated with vol (high = stressed)
    # or define a canonical direction per section (see Pitfall 2)
    return pd.Series(signal, index=section_df.index,
                     name=f"s_{section_df.columns[0].split('_')[0]}")
```

### Pattern 2: FRED Data Fetch with Forward-Fill

**What:** FRED macro series have different frequencies (T10Y2Y: daily, NFCI: weekly, BAMLH0A0HYM2: daily). All must be aligned to the daily business calendar of the market data.

**When to use:** Whenever a new FRED series is added to the pipeline.

**Example:**
```python
# Source: fredapi 0.5.2 documentation + pandas_datareader 0.10.0
# [VERIFIED: fredapi installed, pandas_datareader installed]
from fredapi import Fred
import pandas as pd

def fetch_fred_series(series_codes: list[str], start: str, api_key: str) -> pd.DataFrame:
    """Fetch FRED series and align to daily business frequency.
    
    Uses forward-fill for weekly/monthly series (NFCI, CFNAI).
    Forward-fill is CAUSAL: no lookahead (weekly NFCI reflects prior Friday).
    """
    fred = Fred(api_key=api_key)
    frames = {}
    for code in series_codes:
        s = fred.get_series(code, observation_start=start)
        # Resample to business day frequency, forward fill gaps (weekends, holidays)
        s = s.resample('B').last().ffill()
        frames[code] = s
    return pd.DataFrame(frames)
```

**Causal note:** Forward-fill for weekly NFCI is causal because NFCI reflects the period ending the prior Friday, published Wednesday. Using ffill on a Wednesday-aligned daily index means every business day gets the most recently published NFCI reading, with no future data. [ASSUMED — standard econometric practice, not verified in NFCI documentation]

### Pattern 3: Walk-Forward on Section Signals

**What:** The walk-forward loop runs on the 4-column section signal DataFrame, not on the raw 22-feature matrix. MI is computed between each section signal and the regime label (from prior full-data training run or from within-fold HMM labels).

**Critical design question resolved:** Sectioning happens BEFORE walk-forward. The section PC1 computation uses only training-fold data (causal). Walk-forward then selects which section signals are stable predictors of regime labels.

```python
# Source: Adapted from orchestrator.py walk_forward() pattern
# [VERIFIED: orchestrator.py reviewed in session]
from sklearn.feature_selection import mutual_info_classif
import numpy as np
import pandas as pd

def walk_forward_section_selection(
    section_signals: pd.DataFrame,  # (T, 4) — one column per section
    regime_labels: pd.Series,        # integer regime labels aligned with section_signals
    train_years: int = 3,
    step_days: int = 21,
    stability_threshold: float = 0.60,
    top_n_per_fold: int = 3,          # top-N sections per fold before stability filter
    random_state: int = 42,
) -> dict:
    """Walk-forward section selection using mutual information.
    
    Returns:
        selected: list of section names passing stability threshold
        fold_table: DataFrame (section × fold) with 1/0 selection
        oos_scores: mean MI per section across OOS folds
    """
    min_train = train_years * 252
    step = step_days
    n_sections = section_signals.shape[1]
    section_names = list(section_signals.columns)
    
    fold_selections = []  # list of sets
    fold_scores = []      # list of dicts {section_name: mi_score}
    
    t = min_train
    while t < len(section_signals):
        end = min(t + step, len(section_signals))
        
        # Rolling 3-year train window
        train_start = max(0, t - min_train)
        X_train = section_signals.iloc[train_start:t].values
        y_train = regime_labels.iloc[train_start:t].values
        
        if len(np.unique(y_train)) < 2:
            t = end
            continue
        
        # MI on train fold only — CRITICAL for avoiding selection bias
        mi_scores = mutual_info_classif(
            X_train, y_train,
            discrete_features=False,
            random_state=random_state,
            n_jobs=-1,  # parallel since sklearn 1.5
        )
        
        # Select top-N sections this fold
        top_idx = np.argsort(mi_scores)[-top_n_per_fold:]
        fold_selections.append(set(section_names[i] for i in top_idx))
        fold_scores.append(dict(zip(section_names, mi_scores)))
        
        t = end
    
    # Stability filter: section selected if in ≥60% of folds
    n_folds = len(fold_selections)
    selection_freq = {s: sum(s in fold for fold in fold_selections) / n_folds
                      for s in section_names}
    selected = [s for s, freq in selection_freq.items()
                if freq >= stability_threshold]
    
    return {
        'selected': selected,
        'selection_frequency': selection_freq,
        'fold_scores': fold_scores,
    }
```

### Anti-Patterns to Avoid

- **Fitting section PCA on full history:** Leaks future vol regime into PC1 direction. Always fit section PCA on `iloc[-pca_window:]` of the TRAINING fold only, then transform test fold.
- **Running MI on test fold to select sections:** Any selection using test data invalidates the walk-forward guarantee. MI must be computed on training fold data only.
- **Using NFCI at publication lag = 0:** NFCI is published Wednesday with lag to previous Friday. In a strict causal setting, a dataset aligned to daily trading dates should treat Wednesday's NFCI reading as available from Wednesday forward, not retroactively applied to Monday/Tuesday. Forward-fill from the publication date is correct.
- **Equal-weighting within a section without sign-alignment:** If one section feature is negatively correlated with the others (e.g., VRP is sometimes negative during complacency while VIX is positive), equal-weighting without sign-alignment creates a cancellation effect. PC1 handles this automatically; equal-weight requires manual sign correction.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Within-section dimensionality reduction | Custom weighted average or eigen-decomposition | `sklearn.decomposition.PCA(n_components=1)` | Handles sign ambiguity, centering, scaling edge cases; well-tested |
| Feature importance ranking | Custom correlation measure | `sklearn.feature_selection.mutual_info_classif` | Non-linear, model-free, well-calibrated for classification |
| FRED data fetching | requests + JSON parsing | `fredapi.Fred.get_series()` | Handles FRED API pagination, rate limits, observation_start |
| Frequency alignment | Custom interpolation loop | `pd.Series.resample('B').last().ffill()` | Causal forward-fill, business-day aligned, pandas-native |
| Section sign correction | Manual sign flip heuristics | Anchor sign to known direction: `if pca.components_[0, anchor_idx] < 0: signal *= -1` | Deterministic, reproducible, no future data |

**Key insight:** The section-to-signal step is structurally identical to what the Chicago Fed does for CFNAI and NFCI subindices. Those are well-established tools — replicate their pattern (standardize → PC1 → sign anchor), not a custom weighting scheme.

---

## Feature Inventory: Current 17 Features by Proposed Section

This maps existing features to their natural sections and identifies gaps.

### Section 1: Volatility (currently over-represented)
| Feature | Source | Keep/Add |
|---------|--------|---------|
| VIX | yfinance `^VIX` | KEEP |
| VRP | derived (VIX - rv20*100) | KEEP |
| rv_ratio_10_63 | derived (rv10/rv63) | KEEP |
| vix_ts_slope | yfinance `^VIX`, `^VIX3M` | KEEP |
| SPY_volvol20 | derived | KEEP |
| SPY_rv10_lag5 | derived | KEEP (SV support) |
| SPY_rv10_lag10 | derived | KEEP (SV support) |
| lev_effect20 | derived | KEEP (leverage effect) |

**Action:** All 8 features kept, BUT they all collapse to ONE section signal. Vol section contributes 1 of N signals to HMM, not 8 of N features.

### Section 2: Financial Conditions / Credit (currently under-represented)
| Feature | Source | Keep/Add |
|---------|--------|---------|
| credit_stress (HYG-TLT spread, 20d) | yfinance HYG, TLT | KEEP |
| SPY_TLT_corr63 | yfinance SPY, TLT | KEEP |
| **HY_OAS** (ICE BofA HY spread) | FRED `BAMLH0A0HYM2` | ADD |
| **NFCI** (National Financial Conditions Index) | FRED `NFCI` (weekly) | ADD |

**FRED verification:**
- `BAMLH0A0HYM2`: Daily, from 1996-12-31, still updated 2024+ [VERIFIED: FRED SSRN / web search]
- `NFCI`: Weekly (Friday), from 1971, available via fredapi [VERIFIED: chicagofed.org/research/data/nfci]

**Economic rationale:** credit_stress and SPY_TLT_corr63 are market-price proxies for credit conditions. HY_OAS is a direct credit risk premium measure. NFCI is the Fed's composite financial conditions index (105 indicators). Together these 4 features capture credit tightness from multiple angles: equity-implied, bond-implied, credit-market direct, and Fed composite.

### Section 3: Macro / Economic Cycle (currently absent — zero features)
| Feature | Source | Keep/Add |
|---------|--------|---------|
| **yield_curve_slope** (T10Y2Y) | FRED `T10Y2Y` (daily) | ADD |
| **GLD_trend** (GLD 63d momentum) | yfinance GLD (already in TICKERS) | ADD |
| SPY_ret | yfinance SPY | KEEP (cycle momentum proxy) |
| SPY_ac1_20 | derived | KEEP (return autocorrelation = trend persistence) |

**FRED verification:**
- `T10Y2Y`: Daily, from 1976, available [VERIFIED: fred.stlouisfed.org/series/T10Y2Y — confirmed in web search]

**Note on ISM PMI:** ISM data was REMOVED from FRED in June 2016. [VERIFIED: St. Louis Fed press release found in web search] Do NOT attempt to fetch `NAPM` from fredapi — it will fail for 2016+. Use yield curve (T10Y2Y) as the primary leading macro indicator instead. T10Y2Y is daily, longer history, and is a well-established recession/expansion predictor.

**Economic rationale:** Yield curve slope is the canonical macro cycle signal — inversion precedes recessions, steepening signals expansion [CITED: Federal Reserve Board, 2022 FEDS note]. GLD trend captures real-asset/inflation/risk-off signal separate from equity. SPY_ret and SPY_ac1_20 carry equity-momentum information for cycle phase.

### Section 4: Market Structure / Microstructure (currently thin)
| Feature | Source | Keep/Add |
|---------|--------|---------|
| eigen_conc | derived (multi-asset covariance) | KEEP |
| SPY_dd63 | derived | KEEP |
| SPY_rel_volume | derived | KEEP |
| SPY_vol_adj_ret | derived | KEEP |
| SPY_skew20 | derived | KEEP |

**Economic rationale:** eigen_conc (absorption ratio) measures systemic co-movement [CITED: Kritzman et al. 2011, SSRN 1633027]. SPY_dd63 and SPY_skew20 capture distributional regime characteristics. Relative volume and vol_adj_ret proxy liquidity conditions.

### Summary: Expanded Feature Matrix
| Section | Features | New FRED | Total |
|---------|----------|----------|-------|
| Volatility | 8 existing | 0 | 8 |
| Financial Conditions/Credit | 2 existing | 2 (BAMLH0A0HYM2, NFCI) | 4 |
| Macro/Economic Cycle | 2 existing | 1 (T10Y2Y) + 1 GLD_trend | 4 |
| Market Structure | 5 existing | 0 | 5 |
| **Total** | **17 existing** | **3 FRED + 1 GLD_trend** | **21** |

This satisfies FEAT-01 (12+ candidates with economic rationale). [ASSUMED: GLD_trend adds genuine macro signal; GLD already collected but momentum feature not currently computed]

---

## Common Pitfalls

### Pitfall 1: Section PCA Sign Ambiguity
**What goes wrong:** PCA eigenvector sign is arbitrary. On one training fold PC1 of the Vol section loads positively on VIX; on the next fold it might flip sign. The HMM then receives a signal that flips direction between folds, making training unstable.
**Why it happens:** sklearn PCA does not guarantee sign consistency across fits. This is a known limitation [CITED: sklearn PCA documentation — "signs of components are not unique"].
**How to avoid:** After fitting section PCA, check the sign of the dominant loading. If the anchor feature (e.g., VIX for vol section, T10Y2Y for macro section) has a negative loading on PC1, multiply `pca.components_[0]` by -1 before transforming. This is deterministic and causal.
**Warning signs:** Section signal has near-zero correlation with its anchor feature on any given fold.

### Pitfall 2: NFCI Publication Lag Lookahead
**What goes wrong:** NFCI is published Wednesday for the period ending the prior Friday. If the daily time series is aligned to the calendar date of the measurement period (Friday) rather than the publication date (Wednesday), the model uses data that wasn't available until 3 days later.
**Why it happens:** FRED returns observations with the observation date (Friday), not the publication date.
**How to avoid:** Shift NFCI by 3 business days (`s.shift(3)`) before merging into the feature matrix. Or use the default FRED observation date and note that the max lookahead is 3 days — acceptable for a daily regime model. [ASSUMED: the 3-day publication lag is standard for NFCI; not re-verified in this session]
**Warning signs:** NFCI feature has implausibly high MI with forward returns.

### Pitfall 3: Monthly FRED Data Creates Stale Features
**What goes wrong:** Monthly series (CFNAI, ISM if sourced elsewhere) only update once per month. Forward-filling 20 business days with the same value means the feature is constant for long stretches, producing near-zero variance in short training folds.
**Why it happens:** Monthly frequency doesn't align with daily regime detection.
**How to avoid:** Prefer daily or weekly FRED series: T10Y2Y (daily) over CFNAI (monthly), NFCI (weekly) over CFNAI (monthly). If a monthly series must be used, compute its 1-month change (which removes the constant stretches) rather than the level.
**Warning signs:** Feature variance ≈ 0 in any training fold shorter than 1 month.

### Pitfall 4: Walk-Forward Selection Bias via Section PCA Fitted on Full Data
**What goes wrong:** If section PCA is fitted on all available data (full history), then walk-forward MI is computed using that full-history PC1. This leaks future data into the section signal, invalidating the OOS guarantee.
**Why it happens:** It's tempting to fit section PCA once (efficiently) and reuse it across folds.
**How to avoid:** Inside each walk-forward fold, refit section PCA on `X_train[-pca_window:]` only. This mirrors the existing rolling PCA pattern in `prepare_features()`.
**Warning signs:** OOS MI scores are suspiciously close to in-sample MI scores across all folds.

### Pitfall 5: ISM PMI Is Not on FRED After 2016
**What goes wrong:** `fredapi.get_series('NAPM')` raises an exception or returns no data after 2016-06-24 when ISM removed its data from FRED.
**Why it happens:** ISM revoked FRED's distribution rights in June 2016. [VERIFIED: St. Louis Fed official notice found in web search]
**How to avoid:** Do NOT include ISM PMI as a feature. Use T10Y2Y (daily yield curve slope) as the primary leading macro indicator. It has longer history, daily frequency, and is equally well-established as a macro cycle signal.
**Warning signs:** fredapi call for 'NAPM' returns empty Series or series ending in 2016.

### Pitfall 6: N_STATES Config Mismatch
**What goes wrong:** CLAUDE.md says K=4 (Expansion, Neutral, Contraction, Crisis). config.py currently has N_STATES=3 (confirmed in codebase read). Walk-forward regime labels will be generated with the current N_STATES value — if the script uses config.py directly, it will use K=3 not K=4.
**Why it happens:** The config.py N_STATES was reverted to 3 after Phase 2.5-03, but CLAUDE.md architectural constraint still says K=4. There is a discrepancy in the project state.
**How to avoid:** Walk-forward selection script must explicitly document which N_STATES it uses. The researcher cannot resolve this discrepancy — flag for planner to confirm N_STATES with user before implementing.
**Warning signs:** Regime label distribution is only 3 values when CLAUDE.md expects 4.

---

## Code Examples

### Fetch and align FRED macro features (causal)
```python
# Source: fredapi 0.5.2 + pandas 2.3.1 — verified installed
import os
from fredapi import Fred
import pandas as pd

FRED_SERIES = {
    'T10Y2Y':         'yield_curve_slope',   # daily
    'BAMLH0A0HYM2':   'HY_OAS',              # daily
    'NFCI':           'NFCI',                # weekly — will forward-fill
}

def collect_fred_features(start_date: str, fred_api_key: str) -> pd.DataFrame:
    fred = Fred(api_key=fred_api_key)
    frames = {}
    for code, name in FRED_SERIES.items():
        s = fred.get_series(code, observation_start=start_date)
        s.name = name
        # Align to business day, forward fill (causal: no future data used)
        s = s.resample('B').last().ffill()
        frames[name] = s
    df = pd.DataFrame(frames)
    df.index.name = 'Date'
    return df
```

### Build GLD trend feature (reuses existing GLD_close)
```python
# Source: Adapted from existing build_features() pattern in src/features/features.py
def compute_gld_trend(market: pd.DataFrame, window: int = 63) -> pd.Series:
    """GLD 63-day log return momentum. Proxy for inflation/risk-off macro signal.
    Causal: uses only past data (log(P_t / P_{t-window}))."""
    if 'GLD_close' not in market.columns:
        return pd.Series(dtype=float, name='GLD_trend')
    gld = market['GLD_close']
    return (np.log(gld / gld.shift(window))).rename('GLD_trend')
```

### Section signal construction (rolling causal PC1)
```python
# Source: Adapted from prepare_features() PCA pattern + sklearn 1.7.0
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pandas as pd, numpy as np

SECTION_MAP = {
    's_vol':  ['VIX', 'VRP', 'rv_ratio_10_63', 'vix_ts_slope', 'SPY_volvol20',
               'SPY_rv10_lag5', 'SPY_rv10_lag10', 'lev_effect20'],
    's_fin':  ['credit_stress', 'SPY_TLT_corr63', 'HY_OAS', 'NFCI'],
    's_mac':  ['yield_curve_slope', 'GLD_trend', 'SPY_ret', 'SPY_ac1_20'],
    's_str':  ['eigen_conc', 'SPY_dd63', 'SPY_rel_volume', 'SPY_vol_adj_ret', 'SPY_skew20'],
}

# Anchor features for sign correction (higher value = more stressed / risk-off)
SECTION_ANCHORS = {
    's_vol':  'VIX',            # positive VIX loading means signal rises with vol
    's_fin':  'HY_OAS',         # positive HY_OAS loading means signal rises with credit stress
    's_mac':  'yield_curve_slope',  # positive T10Y2Y = expansion; NOTE: signal may need NEGATION
    's_str':  'SPY_dd63',       # drawdown negative by construction; sign-flip to positive
}

def build_section_signals(features: pd.DataFrame, pca_window: int = 252) -> pd.DataFrame:
    """Reduce thematic feature sections to one PC1 signal each.
    
    Uses causal rolling PCA: fitted on last pca_window rows only.
    Applies sign correction anchored to a canonical feature per section.
    Returns DataFrame with one column per section.
    """
    signals = {}
    for section_name, feat_cols in SECTION_MAP.items():
        available = [c for c in feat_cols if c in features.columns]
        if not available:
            continue
        section_df = features[available].copy()
        
        if len(available) == 1:
            signals[section_name] = section_df.iloc[:, 0].rename(section_name)
            continue
        
        # Standardize on rolling window (causal)
        fit_data = section_df.iloc[-pca_window:].values
        scaler = StandardScaler()
        scaler.fit(fit_data)
        X_std = scaler.transform(section_df.values)
        
        # Fit PCA on rolling window
        pca = PCA(n_components=1, random_state=42)
        pca.fit(X_std[-pca_window:])
        
        # Sign correction: anchor to canonical feature
        anchor = SECTION_ANCHORS.get(section_name)
        if anchor and anchor in available:
            anchor_idx = available.index(anchor)
            if pca.components_[0, anchor_idx] < 0:
                pca.components_[0] *= -1  # flip all loadings
        
        signal = pca.transform(X_std).squeeze()
        signals[section_name] = pd.Series(signal, index=section_df.index, name=section_name)
    
    return pd.DataFrame(signals)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat feature list → joint PCA → HMM | Sectioned features → per-section PC1 → joint PCA → HMM | Phase 5 redesign | Vol section no longer dominates PC1 of joint PCA |
| 17 purely market-price features | 21 features including 3 FRED macro series | Phase 5 | Adds true macro cycle signal absent from current feature set |
| ISM PMI via FRED | T10Y2Y yield curve slope | ISM removed from FRED 2016 | Daily frequency, longer history, equally valid leading indicator |
| Walk-forward selection on raw features | Walk-forward selection on section signals (4 signals, not 17 features) | Phase 5 | Fewer degrees of freedom in selection reduces overfitting risk |

**Deprecated/outdated:**
- FEATURE_SUBSET of 6 raw features: replaced by walk-forward-selected section signals (N_selected of 4 signals)
- Single rolling PCA on 17 features: retained but operates on section signals, not raw features

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | GLD_trend adds genuine macro signal independent of SPY_ret | Feature Inventory §Macro | If GLD_trend is redundant with SPY_ret in Macro section, PC1 still works but wastes a slot — low risk |
| A2 | NFCI forward-fill from Wednesday publication is causal with ≤3 business day lag | Pitfall 2, Code Examples | If FRED alignment uses observation date (Friday) not publication date, lookahead of ~3 days exists — acceptable for daily model |
| A3 | N_STATES config discrepancy (CLAUDE.md says K=4, config.py says K=3) does not block Phase 5 implementation | Pitfall 6 | If user intended K=4 and walk-forward runs with K=3, regime label quality may differ — must confirm with user |
| A4 | SPY_ac1_20 belongs in Macro section rather than Market Structure | Feature Inventory §Macro | If autocorrelation is a microstructure signal rather than macro, reassigning it could weaken one section — low risk, plannable |
| A5 | 4 sections is the right granularity (not 3 or 5) | Section Summary table | If Macro and Market Structure are too similar, merging to 3 sections is fine — section count is discretionary |

---

## Open Questions

1. **N_STATES Discrepancy**
   - What we know: config.py has N_STATES=3; CLAUDE.md architectural constraint says K=4 (Expansion, Neutral, Contraction, Crisis). Phase 2.5-03 confirmed K=4 by BIC, but a subsequent session reverted to K=3.
   - What's unclear: Which K should Phase 5 walk-forward use? Walk-forward generates regime labels for MI computation — those labels must match the intended production K.
   - Recommendation: Planner should present this to user before task 1. If K=4, update config.py N_STATES back to 4 as a prerequisite step.

2. **FRED API Key**
   - What we know: fredapi is installed. Collect functions need a FRED API key.
   - What's unclear: Where the key is stored (env var? config.py? .env file?). current collect.py doesn't use FRED.
   - Recommendation: Add `FRED_API_KEY = os.getenv('FRED_API_KEY', '')` to config.py. User must set the env var. Free key obtainable at fred.stlouisfed.org/docs/api/api_key.html.

3. **Section PCA Refitting in Walk-Forward**
   - What we know: The walk-forward loop must refit section PCA on each training fold to avoid lookahead.
   - What's unclear: Whether to refit section PCA at the same granularity as the outer walk-forward step (21-day step) or at a coarser granularity (annual). Refitting every 21 days is computationally cheap and correct.
   - Recommendation: Refit section PCA every fold iteration. Computational cost is negligible (PCA on ≤8 features, ≤252 rows).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| fredapi | FRED macro data collection | Yes | 0.5.2 | pandas-datareader (also installed) |
| pandas-datareader | Alt. FRED access | Yes | 0.10.0 | fredapi |
| scikit-learn | MI ranking, section PCA | Yes | 1.7.0 | — |
| pandas | Data alignment, resampling | Yes | 2.3.1 | — |
| numpy | Array ops | Yes | 2.3.1 | — |
| FRED API key | fredapi authenticated calls | Unknown | — | Unauthenticated FRED CSV download as fallback |
| ISM PMI via FRED | Macro section leading indicator | No (removed 2016) | — | T10Y2Y (daily, available) |

**Missing dependencies with no fallback:**
- FRED API key: required for fredapi. Fallback is pandas-datareader `pdr.get_data_fred()` which uses the public FRED API (no key for basic access, but rate-limited). In practice, free FRED API key takes 2 minutes to obtain.

**Missing dependencies with fallback:**
- ISM PMI: replaced by T10Y2Y (already researched and confirmed available)

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing 160+ tests) |
| Config file | pytest.ini or pyproject.toml (check existing) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEAT-01 | build_section_signals() returns 4 columns with expected names | unit | `pytest tests/test_section_signals.py -x` | No — Wave 0 gap |
| FEAT-01 | New FRED features present in expanded feature matrix | unit | `pytest tests/test_features.py::test_fred_features -x` | No — Wave 0 gap |
| FEAT-02 | Walk-forward folds do not use future data for section PCA | unit | `pytest tests/test_walk_forward.py::test_no_lookahead -x` | No — Wave 0 gap |
| FEAT-02 | MI computed on train fold only | unit | `pytest tests/test_walk_forward.py::test_mi_train_only -x` | No — Wave 0 gap |
| FEAT-03 | Selection frequency table present in feature_importance_report.md | integration | `pytest tests/test_walk_forward.py::test_report_written -x` | No — Wave 0 gap |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- `tests/test_section_signals.py` — covers FEAT-01 section construction
- `tests/test_walk_forward.py` — covers FEAT-02 causal guarantee, FEAT-03 report

---

## Security Domain

Step 2.6 / Security: This phase is code/config changes with one external API call (FRED). No authentication flows, user data, or stored secrets beyond an API key in env var.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | — |
| V5 Input Validation | Partial | Validate FRED response is non-empty before merging into feature matrix |
| V6 Cryptography | No | — |

Only relevant: FRED API key must not be hardcoded in source code. Use `os.getenv('FRED_API_KEY')`.

---

## Sources

### Primary (HIGH confidence)
- scikit-learn 1.7.0 local install — mutual_info_classif, PCA, StandardScaler verified present and working
- fredapi 0.5.2 local install — verified fetchable
- pandas-datareader 0.10.0 local install — verified present
- `src/features/features.py` — current 17-feature implementation reviewed directly
- `src/config.py` — FEATURE_SUBSET, N_STATES, window parameters reviewed directly
- `src/core/orchestrator.py` — walk_forward() pattern reviewed directly

### Secondary (MEDIUM confidence)
- [Chicago Fed CFNAI methodology](https://www.chicagofed.org/research/data/cfnai/about) — PC1 aggregation of 85 indicators into composite
- [FRED NFCI series](https://fred.stlouisfed.org/series/NFCI) — weekly frequency, 105 indicators, risk/credit/leverage subindices confirmed
- [FRED BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) — daily HY OAS, confirmed available 1996–present
- [FRED T10Y2Y](https://fred.stlouisfed.org/series/T10Y2Y) — daily yield curve spread, confirmed available
- [ISM removal from FRED notice](https://news.research.stlouisfed.org/2016/06/institute-for-supply-management-data-to-be-removed-from-fred/) — ISM PMI not available via FRED API after 2016-06-24
- [Dynamic Factor Allocation arxiv 2410.14841v1](https://arxiv.org/html/2410.14841v1) — confirms yield curve slope (T10Y2Y) and VIX as standard macro-environment features in factor regime models; no composite signal step used
- [Tactical Asset Allocation arxiv 2503.11499v1](https://arxiv.org/html/2503.11499v1) — confirms FRED-MD sectioning (7 thematic groups); pure PCA rather than per-section composite

### Tertiary (LOW confidence — not verified via official docs)
- sklearn documentation cached summary — mutual_info_classif n_jobs added in v1.5, confirmed present in v1.7.0 via local install
- Macrosynergy linear_composite pattern — web search summary; not directly verified via package docs

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — all libraries verified locally installed and working
- Architecture (sectioned funnel): MEDIUM — pattern is justified by analogy to CFNAI/NFCI but no canonical "sectioned funnel HMM" paper exists; original design by user and validated by researcher
- Feature candidates: HIGH — specific FRED series codes verified against FRED directly
- Pitfalls: HIGH — PCA sign ambiguity and FRED data availability issues are well-documented; ISM removal from FRED verified

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (FRED API availability is stable; sklearn API stable until next major release)
