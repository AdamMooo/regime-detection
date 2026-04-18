> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 05-feature-engineering-overhaul
**Areas discussed:** Candidate pool, Walk-forward CV design, Feature selection metric, Output & integration

---

## Candidate Pool (FEAT-01)

| Option | Description | Selected |
|--------|-------------|----------|
| All 17 from build_features() | Use every feature already generated as a candidate | ✓ |
| 17 existing + add new ones | Add macro momentum, GLD vol, etc. before running selection | |
| Curated subset of 12-13 | Manually pick before CV runs | |

**User's choice:** All 17 from build_features()
**Notes:** No new feature engineering needed — 17 already cover 8 regime dimensions with causal guarantees.

| Option | Description | Selected |
|--------|-------------|----------|
| No always-in — let CV decide | Every feature competes equally | ✓ |
| VIX always-in | Lock VIX, select from remaining 16 | |
| VIX + VRP always-in | Lock both, select from remaining 15 | |

**User's choice:** No always-in — let CV decide

---

## Walk-Forward CV Design (FEAT-02)

| Option | Description | Selected |
|--------|-------------|----------|
| 5yr train / 1yr test, rolling | ~9 folds, matches config.py default | |
| 3yr train / 1yr test, rolling | ~11 folds, catches regime shifts | ✓ |
| Expanding train / 1yr test | More history per fold, fewer folds | |

**User's choice:** 3yr / 1yr rolling (free-text: "want a balance, more on the shifting quickly side")

| Option | Description | Selected |
|--------|-------------|----------|
| Top-N by mutual information | Fast, causal, no model for selection | ✓ |
| Greedy forward selection | O(k²) model fits per fold | |
| Fixed-size stability filter | Kruskal-Wallis p<0.05 sub-window filter | |

**User's choice:** Mutual information (auto-selected after user noted: "if features are bad does this even matter" — valid observation, MI is the lowest-overhead method)

| Option | Description | Selected |
|--------|-------------|----------|
| Stability threshold ≥60% of folds | Feature must appear in majority of folds | ✓ |
| Majority vote only | >50% binary in/out | |
| Always-selected only | Must appear in every fold | |

**User's choice:** Stability threshold ≥60%

---

## Feature Selection Metric

| Option | Description | Selected |
|--------|-------------|----------|
| Mutual information (Recommended) | Pure information measure, no model needed | ✓ |
| Kruskal-Wallis H-statistic | p-value filter before MI ranking | |
| Composite: MI + dwell time stability | MI + stability penalty | |

**User's choice:** Mutual information

| Option | Description | Selected |
|--------|-------------|----------|
| 6–8 features | Match current range | |
| 8–10 features | Wider net | |
| Let 60% threshold decide | Data-driven count | ✓ |

**User's choice:** Let the 60% threshold decide

---

## Output & Integration (FEAT-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-update config.py (Recommended) | Script writes new FEATURE_SUBSET directly | ✓ |
| Report only — manual update | Human decides | |

**User's choice:** Auto-update config.py

| Option | Description | Selected |
|--------|-------------|----------|
| Markdown report + table (Recommended) | data/feature_importance_report.md | ✓ |
| HTML figure | Visual bar chart in figures/ | |
| Both — markdown + figure | Complete but more to maintain | |

**User's choice:** Markdown report + selection frequency table

| Option | Description | Selected |
|--------|-------------|----------|
| scripts/analysis/ (Recommended) | Consistent with Phase 4 | ✓ |
| scripts/ root | Simpler path | |
| src/features/ | Closer to features.py | |

**User's choice:** scripts/analysis/

---

## Claude's Discretion

- Exact top-N cutoff per fold before 60% aggregation
- Whether to run validation re-run on new FEATURE_SUBSET after update

## Deferred Ideas

None.
