# Phase 1: Fix Critical Blockers - Context

**Gathered:** 2026-04-13 (Session #4)  
**Status:** Ready for planning  
**Mode:** Auto-discussed (GSD --auto)

---

<domain>

## Phase Boundary

Fix 4 critical production blockers to unblock integration testing with Algo-Trading-Bot and prepare for v1.0 deployment.

**Sub-blockers:**
- 1.1: Tighten JAX/NumPyro version pinning (reproducibility risk)
- 1.2: Implement bot label mapping + validation (integration compatibility)
- 1.3: Add causal pipeline tests + documentation (no-lookahead guarantee)
- 1.4: Create integration test with Algo-Trading-Bot (E2E validation)

</domain>

---

<decisions>

## Implementation Decisions

### JAX/NumPyro Reproducibility (1.1)
- **D-01:** Pin JAX and NumPyro to exact versions in `requirements.txt` (e.g., `jax==0.4.35`, not `>=0.4.30`)
  - **Rationale:** Regime labels must be reproducible bit-for-bit. Version ranges allow breaking changes that silently corrupt regime assignments.
  - **Conflict Resolution:** requirements.txt has merge conflict — resolve to exact pinning (HEAD uses exact; other branch uses loose). Exact is non-negotiable for trading.
  - **Implementation:** Merge requirements.txt to exact versions, add comment referencing CLAUDE.md hard constraints
- **D-02:** Add CI/CD step that rejects PRs loosening version constraints
  - **Rationale:** Prevents accidental regression to loose constraints
  - **Implementation:** Simple grep check in CI/CD (fail if `>=` found in jax/numpyro lines)

### Bot Label Mapping (1.2)
- **D-03:** Create explicit `LABEL_MAPPING` dict in `config.py`
  - **Current:** config.py has `REGIME_NAMES` (e.g., 'Low-Vol', 'Medium-Vol', 'High-Vol')
  - **Requirement:** Bot expects 'LOW_VOL', 'MED_VOL', 'HIGH_VOL' (uppercase, underscores)
  - **Decision:** Add `LABEL_MAPPING` dict:
    ```python
    LABEL_MAPPING = {
        'Low-Vol': 'LOW_VOL',
        'Medium-Vol': 'MED_VOL',
        'High-Vol': 'HIGH_VOL',
    }
    ```
  - **Rationale:** Single source of truth, explicit, avoids renaming all code
  - **Implementation:** signals.py uses LABEL_MAPPING when outputting regime labels
- **D-04:** Dashboard displays both internal names (Low-Vol) and bot labels (LOW_VOL)
  - **Rationale:** Helps users understand the mapping; visibility into what the bot sees
  - **Implementation:** Add column to dashboard or tooltip showing bot-expected label

### Causality Guarantees (1.3)
- **D-05:** Keep existing test_causality.py coverage (3 tests for 3 guarantees)
  - **Current:** test_causality.py has ~6 tests covering:
    - expanding_standardize uses only past data
    - PCA fitted incrementally (no future data)
    - HMM inference uses filtering (not smoothing) in production
  - **Decision:** Coverage is sufficient (verified in Session 3 analysis); add only documentation updates
  - **Implementation:** Update CLAUDE.md hard constraints section with explicit causality guarantees
- **D-06:** Document the causality contract in CLAUDE.md
  - **What:** Explicit statement that features, standardization, and PCA are causal
  - **Why:** Downstream users (bot, portfolio manager) need confidence that no lookahead occurs
  - **Implementation:** Add section to CLAUDE.md "Causality Guarantees" with references to test_causality.py

### Integration Test (1.4)
- **D-07:** Create `test_bot_integration.py` that validates signal schema without hard Algo-Trading-Bot import
  - **Approach:** Schema validator + mock bot handler
  - **Why:** Keeps test self-contained, no external dependency on Algo-Trading-Bot code
  - **Implementation:**
    - Load a sample regime output from train.py
    - Extract signals via signals.py
    - Validate signal dict has required keys: `timestamp`, `regime_label`, `regime_probs`
    - Verify `regime_label` is one of ['LOW_VOL', 'MED_VOL', 'HIGH_VOL']
    - Verify `regime_probs` is a dict with 3 floats summing to 1.0
    - Optional: mock import bot and verify bot.consume_signal(signals) doesn't raise
- **D-08:** Integration test runs in <5 min and passes on CI/CD
  - **Rationale:** Must be fast enough for development loop (not a barrier to commits)
  - **Implementation:** Use pytest fixture with small data sample (1 year instead of 16 years)

### Claude's Discretion
- **D-09:** Backward compatibility in signals.py output format
  - Users may parse existing signals output; we should keep the output format compatible where possible
  - New bot labels can be added as new fields (e.g., `bot_label`, `regime_label_internal`) rather than renaming existing fields
  - Decision: Keep existing field names; add new fields for bot labels

</decisions>

---

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 Requirements
- `.planning/REQUIREMENTS.md` — R2 (Bot Label Mapping), R3 (Causal Pipeline), R4 (Reproducibility), R5 (Integration with Algo-Trading-Bot)
- `.planning/ROADMAP.md` — Phase 1 full specification (blockers 1.1–1.4)

### Hard Constraints
- `CLAUDE.md` (project root) — NumPyro only, 3 regimes fixed, no K-means, PCA mandatory, causality required
- `.planning/STATE.md` — Architecture decisions locked in (NumPyro, 3 regimes, no incremental in Phase 1)

### Existing Code References
- `config.py` — REGIME_NAMES, VOL_BRACKETS, JAX/NumPyro dependency specs
- `signals.py` — Current signal output format (regime_name, distributions)
- `tests/test_causality.py` — Existing causality tests (3 guarantees)
- `requirements.txt` — Dependency pinning (currently has merge conflict)

### Integration Reference
- Algo-Trading-Bot regime label convention: LOW_VOL, MED_VOL, HIGH_VOL (expected by bot's signal handler)

</canonical_refs>

---

<code_context>

## Existing Code Insights

### Reusable Assets
- `test_causality.py` — 6 existing causality tests; extend rather than rewrite
- `config.py` — REGIME_NAMES dict; add LABEL_MAPPING alongside it
- `signals.py` — `_compute_regime_distributions()` already exists; update output format

### Established Patterns
- **Config structure:** All parameters centralized in config.py (pattern established)
- **Feature output:** Named tuples or dicts used throughout (pattern established)
- **Test organization:** By concern (causality, validation, calibration); add bot_integration to existing structure

### Integration Points
- `signals.py` output consumed by dashboard and (later) Algo-Trading-Bot
- `config.py` consumed by every script in the pipeline
- `requirements.txt` consumed by CI/CD and development setup

</code_context>

---

<specifics>

## Specific Ideas

### Merge Conflict Resolution Strategy
requirements.txt has a merge conflict between:
- **HEAD:** Exact pinning (`jax==0.9.1`, `jaxlib==0.9.1`, etc.)
- **Branch 728b05:** Loose constraints (`jax>=0.4.30,<1`, etc.)

**Decision:** Accept HEAD (exact pinning). This is non-negotiable for reproducibility in trading.

### Bot Label Examples
When users see regime labels in dashboard or bot output:
- **Internal name:** "Low-Vol" (human-readable, economic meaning)
- **Bot label:** "LOW_VOL" (canonical form for Algo-Trading-Bot consumption)
- Both should be visible in outputs and tests

### Causality Audit Trail
The test_causality.py file is the canonical reference for causality guarantees. When updating CLAUDE.md, link directly to these tests so readers can verify the guarantees.

</specifics>

---

<deferred>

## Deferred Ideas

### Backlog (Phase 3, post-deadline)
- train.py refactoring (monolith split into modules) — Phase 3.1
- Dashboard hardening (stress tests, edge cases) — Phase 3.2
- Incremental PCA optimization — Phase 2.2, not Phase 1

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-blockers*  
*Context gathered: 2026-04-13*  
*Mode: Auto-discussion (all gray areas selected, recommended options auto-picked)*
