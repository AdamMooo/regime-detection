# Phase 6: Model Architecture Experiments - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Lock the USE_HDP decision with documented evidence (MODEL-02), and refactor the training pipeline so no module exceeds 500 lines (MODEL-03). K=3 is already confirmed locked (2026-04-18) — K-selection experiment (MODEL-01) is dropped.

</domain>

<decisions>
## Implementation Decisions

### HDP-HMM Evaluation (MODEL-02)

- **D-01:** Primary comparison metrics are **OOS regime accuracy AND regime stability (dwell time)** — HDP-HMM must outperform StudentTHMM on both dimensions to be considered a winner.
- **D-02:** Inference mode for HDP-HMM: **SVI only** (`HDP_INFERENCE='svi'`). NUTS not needed; if SVI can't beat StudentTHMM, NUTS won't change the verdict.
- **D-03:** Win threshold: HDP-HMM must show **+2 percentage points OOS accuracy AND meaningfully longer average dwell time** vs StudentTHMM. Below this bar, simplicity wins — StudentTHMM stays.
- **D-04:** Use the same OOS test split used in Phase 4/5 diagnostics for apples-to-apples comparison.
- **D-05:** User context: in-sample performance is visually good; OOS regime shading on the HTML dashboard looks poor. This is a known prior observation — factor it into interpreting HDP-HMM OOS results.

### Dead Code Outcome

- **D-06:** If HDP-HMM **loses** (does not meet the +2%/dwell bar): **delete `hdp_hmm.py` entirely** and remove all references. No DEPRECATED comments — clean removal. The decision section in MODEL_CARD.md explains why.
- **D-07:** If HDP-HMM **wins**: set `USE_HDP=True` as default; keep StudentTHMM code as a fallback (in case HDP fails on new data or breaks with a dependency update).

### Refactor Strategy (MODEL-03)

Three modules exceed 500 lines: `hdp_hmm.py` (844), `evaluation.py` (821), `hmm_training.py` (606).

- **D-08:** Split **by concern**, not by caller. Each extracted file gets one responsibility.
- **D-09:** `evaluation.py` → split into:
  - `evaluation.py` — regime evaluation logic (keep core)
  - `var_backtesting.py` — VaR/GARCH backtesting functions
  - `forward_returns.py` — forward return analysis (added in Phase 4)
- **D-10:** `hmm_training.py` → extract:
  - `pca_utils.py` — `fit_rolling_pca()` and related PCA utilities; `LinearizedSV` model class also moves here or to its own file
  - `hmm_training.py` — BIC/stability checks/regime labeling stays; target <500 lines after extraction
- **D-11:** If HDP-HMM is deleted: `hdp_hmm.py` deletion counts toward MODEL-03 (844 lines gone). Remaining splits may be smaller in scope.
- **D-12:** **Update all imports cleanly** — fix import paths in `orchestrator.py`, `signals.py`, and all scripts that import from `src/core/`. No re-export indirection. Public API (`detect()`, `fit()` in `signals.py`) does not change.

### Decision Documentation (MODEL-02)

- **D-13:** USE_HDP verdict is recorded in a new **"Model Architecture Decision"** section added to `docs/MODEL_CARD.md`. Include: comparison results (accuracy + dwell time numbers), verdict, and rationale. This is the canonical reference for downstream consumers (Algo-Trading-Bot, Portfolio-Manager).

### Claude's Discretion

- Exact split point within `evaluation.py` if the concern-based split leaves a file slightly over 500 lines — adjust to hit the limit
- Whether `LinearizedSV` goes into `pca_utils.py` or its own `sv_model.py`
- Format of the MODEL_CARD.md comparison table (columns, ordering)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Model Architecture
- `src/config.py` — `USE_HDP`, `HDP_INFERENCE`, `HDP_TRUNCATION`, `HDP_ALPHA`, `HDP_KAPPA`, `N_STATES` — current config values and comments
- `src/core/hdp_hmm.py` — full HDP-HMM implementation (SVI + NUTS paths); target of the comparison or deletion
- `src/core/hmm_training.py` — StudentTHMM training, PCA fitting, BIC, stability, regime labeling — refactor target

### Evaluation
- `src/core/evaluation.py` — regime eval, VaR/GARCH backtesting, forward return analysis — refactor target
- `.planning/REQUIREMENTS.md` §MODEL-02, MODEL-03 — acceptance criteria

### Refactor Scope
- `src/core/orchestrator.py` — imports from hmm_training.py and evaluation.py; must be updated
- `src/signals/signals.py` — public API (`detect()`, `fit()`); imports from core modules; must be updated

### Documentation Target
- `docs/MODEL_CARD.md` — append "Model Architecture Decision" section here with comparison results and verdict

### Prior Phase Context
- `.planning/phases/05-feature-engineering-overhaul/05-CONTEXT.md` — final FEATURE_SUBSET selection that Phase 6 comparison runs on top of

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/core/orchestrator.py:walk_forward()` — existing walk-forward harness; can be used to run both models under the same evaluation protocol
- `src/core/evaluation.py:evaluate()` — regime characteristic evaluation; reuse for both StudentTHMM and HDP-HMM comparison
- `src/core/evaluation.py:compute_forward_return_analysis()` — Phase 4 addition; already measures regime stability metrics

### Established Patterns
- Analysis scripts live in `scripts/analysis/` (not `src/`); comparison script follows this pattern
- Reports/decision docs go to `docs/` (MODEL_CARD.md) or `reports/`
- Import updates across `src/core/` needed when splitting modules — orchestrator.py and signals.py are the key consumers

### Integration Points
- `USE_HDP` flag in `config.py` is the single toggle — all comparison logic routes through this
- After refactor, `src/core/__init__.py` may need updating if it exposes module-level symbols

</code_context>

<specifics>
## Specific Ideas

- User noted that in-sample regime shading looks good but OOS shading on the HTML dashboard looks poor — this is prior observational evidence against HDP-HMM OOS quality, and sets a skeptical prior going into the comparison. The +2%/dwell bar exists partly to ensure any HDP win is substantial enough to justify the added complexity.
- HDP-HMM is likely to be deprecated and deleted given this OOS concern — the comparison exists to confirm this formally and document it, not to rescue the HDP code.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-model-architecture-experiments*
*Context gathered: 2026-04-20*
