# Regime-Detection — Market-Signal Research System

## What This Is

A market-*understanding* layer: it finds, validates, and presents independent market signals plus their historical
context, and then STOPS. Each signal is a standalone research module answering one abstract-market question — *what
is happening · how unusual is it · how has this environment behaved historically · which market assumption does it
relate to* — for a human analyst to connect the dots. It is not a predictor and not a decision system.

## Core Value

Fewer blind spots for the human's judgment: each signal, independently validated on a real economic mechanism,
surfaces a market assumption worth monitoring — never a forecast, never an action. The intelligence is the quality
of each individual signal, not any combination of them into a score.

## The HARD BOUNDARY (non-negotiable)

`market data → independent signals → historical context → regime relevance → STOP.`

The repo must NOT decide, recommend, or imply any investment action — no allocation, exposure, cash calls, ETF
selection, sleeves, tilts, or one-word "risk-on/risk-off" summaries (a single label destroys the information; a
market can be low-vol but fragile, cheap but illiquid). It must not know or reference any capital-allocation or
implementation detail — only which ABSTRACT MARKET assumptions to monitor ("bonds hedge equity drawdowns", "the
index is diversified", "factor premia aren't crowded"). The word "portfolio" and every allocation/implementation
concept stay OUT — zero references. Investment decisions live in a separate system + the human.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ **Volatility / risk-off signal** — jump-model instrument, shipped (`live_label.py` → `regime_signal.py` →
  `results/regime_card.json`), consumed by a separate downstream repo.
- ✓ **Stock-bond correlation signal** (inflation/real-rate axis) — built, validated on US 1962–2026; hedge-behavior-
  by-state confirms the mechanism (monotone through states). Intl (Japan/Europe) OOS confirmation still open.

### Active

<!-- Current scope. Each is one signal module; DoD identical: Find → Validate → Present → STOP. -->

- [ ] **Signal framework** — the shared spec every module declares (8-attribute spec, validation standards, historical-
  context output format, maturity model, the assumption-ledger output shape). Written once, before more signals.
- [ ] **Valuation signal** — starting-valuation → long-horizon-return context (e.g. high CAPE → historically lower
  forward returns); present as context, never "avoid equities".
- [ ] **Concentration signal** — index concentration / breadth as a diversification-assumption monitor.
- [ ] **Diversification / correlation signal** — absorption ratio (cross-asset correlation compression).
- [ ] **Credit signal** — excess bond premium (EBP) as a credit-conditions monitor.
- [ ] **Funding-stress signal** — funding-market stress flag (tail-relevant).
- [ ] **Crowding signal** — factor/position crowding as a "premia aren't crowded" monitor.
- [ ] **Tail signal** — priced tail / jump risk (data-gated).
- [ ] **Presentation layer** — assumption ledger + joint rarity + historical analogues; organizes validated signals
  into multiple lenses. Never a score, never a decision.

### Out of Scope

<!-- These are the HARD BOUNDARY. Reasoning included to prevent re-adding. -->

- Any allocation / exposure / weight / sleeve / tilt / cash decision — belongs to a separate system + the human; a
  detector that allocates violates the subordinate-diagnostic boundary (see factor-model-pivot: regime-as-a-factor
  KILLED for exactly this).
- One-word regime summary ("risk-on/risk-off") — destroys the multi-signal vector that is the whole value.
- The word "portfolio" and every implementation/deployment concept — zero references in this repo.
- Combining signals into a single composite score — the intelligence is per-signal, not the blend.
- Prediction / forecasting as the deliverable — edge is better human decisions via fewer blind spots, not forecasts.
- The equity-ownership / allocation program (constitution, offense/defense, factor, momentum) — removed 2026-08-02,
  a separate concern; recoverable in git history.

## Context

- **Brownfield.** Two signals already exist (vol shipped, stock-bond built). Governing design lives in
  `.planning/REGIME-SENSOR-ARCHITECTURE.md` (signal set, per-signal spec, validation standards, maturity model,
  assumption-ledger output). File map in `CLAUDE.md`. State/next-action in `NOTES.md`.
- **Frozen evidence** (never overwrite): `results/{stage1.csv, stage1_run.log, oos_labels.csv, construction_gate.csv,
  sensor_validation.*, synthetic_validation.*}`; `archive/research-v1/` is inert (reproduce v1 at tag `v1-convergence`).
- **Stack:** Python, `.venv`, `requirements.txt`. Tests: `tests/{test_jumpmodel,test_backtest,test_regime_signal}.py`.
- Data-quality / point-in-time consistency is a standing concern — surface gaps/burn-in/source drift proactively.

## Constraints

- **Discipline — causal only**: trailing/forward filtering, no look-ahead, point-in-time data (macro series get revised).
- **Discipline — mechanism gate**: no signal is preregistered without a written structural reason it survives being
  *known* (risk premium or risk-management mechanism). Novelty/backtest/literature disqualifying as sole basis.
- **Discipline — validate honestly**: mechanism first; statistical orthogonality is a diagnostic, not the gate;
  confound-check every context stat; out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT.
- **Discipline — one look**: prereg + overnight cooling-off + explicit dated sign-off for any positive/SUPPORT claim
  (never inferred from a conversational go-ahead).
- **Discipline — present, never conclude**: no single-word summary; preserve the full vector; present, never allocate.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| GSD scoped strictly to signal modules (Phase 0 framework + one phase per signal + presentation) | Formalize the sensor-building program without importing app-build ceremony | — Pending |
| Skip codebase-map + ecosystem-research GSD steps | Program already scoped by REGIME-SENSOR-ARCHITECTURE.md; codebase documented in CLAUDE.md | ✓ Good |
| CLAUDE.md HARD BOUNDARY preserved, not GSD-regenerated | The boundary is the project's non-negotiable spine | ✓ Good |
| Build order: valuation next after framework | Cleanest mechanism, returns-only data, no macro vintage | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-02 after initialization*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
