# Phase 6: Model Architecture Experiments - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-20
**Phase:** 06-model-architecture-experiments
**Areas discussed:** HDP-HMM eval design, Dead code outcome, Refactor strategy, Decision documentation

---

## HDP-HMM Eval Design

| Option | Description | Selected |
|--------|-------------|----------|
| OOS regime accuracy | Same OOS test split from Phase 4/5. Exact-match accuracy. | |
| Regime stability / dwell time | Longer dwell times, fewer noise-flips on OOS data. | |
| Both accuracy + stability | Compound metric: must beat on both dimensions. | ✓ |

**User's choice:** Both accuracy + stability

---

| Option | Description | Selected |
|--------|-------------|----------|
| SVI only | Fast (~5-10 min CPU). Configured as HDP_INFERENCE='svi'. | ✓ |
| NUTS only | Gold-standard, very slow on CPU. | |
| SVI first, NUTS tiebreaker | Escalate to NUTS only if results are close. | |

**User's choice:** SVI only

---

| Option | Description | Selected |
|--------|-------------|----------|
| +2% accuracy AND longer dwell | Hard bar — HDP must beat on both by meaningful margin. | ✓ |
| Any statistically significant improvement | Even a small edge counts. | |
| No threshold — judgment call | Decide after seeing results. | |

**User's choice:** +2% accuracy AND longer dwell
**Notes:** User mentioned OOS shading on HTML looks poor and in-sample is visually good — skeptical prior going in.

---

## Dead Code Outcome

| Option | Description | Selected |
|--------|-------------|----------|
| Delete entirely | Remove hdp_hmm.py and all references. Clean codebase. | ✓ |
| Leave with DEPRECATED comment | Keep but mark deprecated. | |

**User's choice:** Delete it entirely (if HDP loses)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Keep StudentTHMM as fallback | HDP becomes default but StudentTHMM code stays. | ✓ |
| Delete StudentTHMM too | Full commitment to HDP. | |

**User's choice:** Keep StudentTHMM as fallback (if HDP wins)

---

## Refactor Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Split by concern | evaluation.py → evaluation + var_backtesting + forward_returns | ✓ |
| Split by caller | Keep functions together if always called together. | |
| Claude's discretion | Let Claude decide split points. | |

**User's choice:** Split by concern — evaluation.py → evaluation.py + var_backtesting.py + forward_returns.py

---

| Option | Description | Selected |
|--------|-------------|----------|
| Extract pca_utils.py | fit_rolling_pca + related to pca_utils.py; LinearizedSV also moves. | ✓ |
| Claude's discretion | Let Claude decide what to extract from hmm_training.py. | |
| Don't split hmm_training | Light cleanup only to get under 500 lines. | |

**User's choice:** Extract pca_utils.py from hmm_training.py

---

| Option | Description | Selected |
|--------|-------------|----------|
| Update all imports cleanly | Fix all import paths. One-time churn, clean result. | ✓ |
| Re-export from original file | New files hold code, originals re-export. Less churn, more indirection. | |

**User's choice:** Update all imports cleanly

---

## Decision Documentation

| Option | Description | Selected |
|--------|-------------|----------|
| Section in MODEL_CARD.md | Add "Model Architecture Decision" section to docs/MODEL_CARD.md. | ✓ |
| New ADR file in docs/ | docs/adr-hdp-decision.md — standalone ADR. | |
| Comment in config.py only | Block comment above USE_HDP. | |

**User's choice:** Section in MODEL_CARD.md

---

## Claude's Discretion

- Exact split point within evaluation.py if concern-based split leaves a file slightly over 500 lines
- Whether LinearizedSV goes into pca_utils.py or its own sv_model.py
- Format of the MODEL_CARD.md comparison table

## Deferred Ideas

None.
