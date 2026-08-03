# Phase 1: Signal Framework - Context

**Gathered:** 2026-08-03
**Status:** Ready for planning
**Source:** Design decisions captured directly from the developer (in lieu of interactive discuss-phase)

<domain>
## Phase Boundary

Phase 1 delivers the **frozen framework every future signal must follow** — and nothing else. No
individual market signal is built in this phase. The deliverable is documentation/specification only:

1. The single **signal-specification template** (the 8-attribute evaluation standard) that every later
   signal fills in unambiguously.
2. The **validation standards** every signal is held to (causal-only / point-in-time, the mechanism gate,
   confound-check, out-of-hypothesis-sample intl confirmation, and the one-look + prereg + cooling-off +
   dated sign-off protocol).
3. The **historical-context output format** and **multidimensional confidence model**.
4. The **maturity model** and the **assumption-ledger output shape** (the composition target) so validated
   signals have a known, consistent place to render — never a score.

The purpose of freezing this first is to prevent each future signal from becoming its own custom framework
and to keep the assumption ledger consistent across all signals.

**In scope:** the template, the standards, the output/confidence/maturity/ledger specification — as
written artifacts under version control.
**Out of scope:** building, measuring, or validating any actual signal; any data pipeline; any downstream
consumer. Those are Phases 2–10.

</domain>

<decisions>
## Implementation Decisions

### System Philosophy (invariants that govern every phase)
- **D-01:** The system is a **market-state intelligence** system, not a trading system and not a
  prediction engine. It explains: *what is happening in markets · why it may be happening · what
  historical environments look similar · how unusual the current environment is · what risks and
  opportunities are present* — then STOPS.
- **D-02:** Hard prohibitions on every output: never collapse the market into one score; never produce a
  single bullish/bearish (or risk-on/risk-off) answer; never dictate or imply any downstream investment
  action or decision (those live in a separate system + the human); never pretend to predict future
  returns.
- **D-03:** The output is always a **multi-dimensional market-state vector**. The complexity IS the
  information. Disagreement between signals is valuable information and must be preserved — signals are
  never forced into agreement or reconciled into consensus.

### Signal Evaluation Standard (the frozen template)
- **D-04:** Every signal declares against the **same 8-attribute standard**, in this order:
  (1) **Definition** — what exactly the signal measures + the economic mechanism it represents;
  (2) **Mechanism** — why the signal should contain information (the behavioral / economic / market-
  structure reason for its relevance, i.e. why it survives being known);
  (3) **Measurement** — how it is calculated, what data sources are required, what the limitations of that
  measurement are;
  (4) **Historical Context** — how it has behaved historically, what regimes it has identified, and its
  false positives / false negatives;
  (5) **Validation** — whether it holds across periods, whether it survives international out-of-sample
  testing, and whether the relationship is robust or regime-dependent;
  (6) **Assumptions** — what assumptions the signal requires and when those assumptions would fail;
  (7) **Confidence** — multidimensional, never a single number (see D-06);
  (8) **Limitations** — what the signal can tell us and, explicitly, what it cannot.
- **D-05:** This 8-attribute standard is **authoritative**. It refines the earlier attribute list in
  `.planning/REGIME-SENSOR-ARCHITECTURE.md` (research question · mechanism · data · metric · validation ·
  failure modes · historical-context · maturity). The planner must **reconcile** the two into one template,
  treating this list as the source of truth where they differ, while preserving anything from the
  architecture doc not contradicted here (notably the maturity tag — see D-08 — and the intl-OOS +
  mechanism-gate + prereg standards, which map onto attributes 2/5).

### Confidence Model
- **D-06:** Confidence is **multidimensional**, never a single score. The dimensions are:
  **data-quality confidence · historical-robustness confidence · mechanism confidence · current-relevance
  confidence.** (This authoritatively replaces the earlier 3-dimension model —
  measurement / interpretation / relevance-guard — from the architecture doc/memory; the planner should
  note the mapping: measurement→data-quality, interpretation→historical-robustness + mechanism,
  relevance-guard→current-relevance. "Current-relevance" is the boundary-safe rename — no
  implementation/allocation concept is implied.)

### Signal Independence
- **D-07:** Signals are **independent research modules**. Each has its own research process, its own
  validation, its own assumptions, and its own limitations. Independence between signals is prioritized;
  the framework must not induce a shared latent state or force cross-signal agreement.

### Output Format
- **D-08:** The historical-context output format must specify, per signal: the current **reading**, its
  historical **rarity** (percentile), the **assumption monitored**, the four confidence dimensions (D-06),
  and a **maturity tag** (production / research / rejected). Zero allocation/decision fields.
- **D-09:** The composed output preserves the **full per-signal vector** — one reading per dimension
  (e.g. valuation: expensive vs history · volatility: elevated · breadth: weakening · liquidity:
  supportive · credit: stable · concentration: historically high). It is explicitly forbidden to transform
  this into any composite scalar (e.g. "market risk = 73/100"). The **assumption-ledger shape** is the
  composition target (Level 0 state vector · Level 1 assumption ledger · Level 2 context), defined here so
  later signals render into a known place — never a combined score.

### Claude's Discretion
- File format/serialization of the template (Markdown spec doc vs. a fillable schema), file locations
  within the repo, and section ordering of the standards doc — provided D-01…D-09 are honored.
- How to physically split the work across the two roadmap plans (01-01 template+standards, 01-02
  output/confidence/maturity/ledger), as long as both plans together cover every decision above.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Governing design (authoritative)
- `CLAUDE.md` (project root) — the **HARD BOUNDARY** (market data → independent signals → historical
  context → regime relevance → STOP; zero allocation/implementation references) and the signal-research
  discipline. Non-negotiable; do not regenerate.
- `.planning/REGIME-SENSOR-ARCHITECTURE.md` — the governing signal-sensor architecture (signal set,
  per-signal spec, validation standards, maturity model, assumption-ledger output). Reconcile the
  8-attribute standard against this per D-05.
- `.planning/ROADMAP.md` §"Phase 1: Signal Framework" — the five success criteria this phase must satisfy.
- `.planning/REQUIREMENTS.md` — FRWK-01.

### Prior decisions (memory)
- Mechanism gate: never preregister a signal without a written structural reason it survives being known
  (maps to attribute 2).
- Sensor orthogonality evidence: why independence between signals (D-07) is the design priority.

</canonical_refs>

<specifics>
## Specific Ideas

Worked example of the full-vector output that must be preservable (from the developer), to be used as the
canonical illustration in the output-format spec:

- Valuation: expensive relative to history
- Volatility: elevated
- Breadth: weakening
- Liquidity: supportive
- Credit: stable
- Concentration: historically high

This must never be reduced to a single number such as "market risk = 73/100" — the point of the format is
that the six readings stay legible and independent.

</specifics>

<deferred>
## Deferred Ideas

None new — every individual signal (valuation, concentration, absorption, credit/EBP, funding, crowding,
tail, stock-bond intl OOS) is already scoped to its own later phase (2–9), and the presentation/assumption
-ledger assembly to Phase 10. This phase only freezes the framework they declare against.

</deferred>

---

*Phase: 01-signal-framework*
*Context gathered: 2026-08-03*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
