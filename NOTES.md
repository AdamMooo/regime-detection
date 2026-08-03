# Regime-Detection — Session Notes

## Status
A **market-signal research system** (see CLAUDE.md HARD BOUNDARY — market data → independent signals →
historical context → regime relevance → STOP; never allocation/decisions). The equity-ownership / allocation
program was removed from this repo 2026-08-02 (recoverable in git history). Branch: main | Last updated: 2026-08-02

## Current direction — independent market-signal modules (find → validate → present → STOP)

Governing design: **`.planning/REGIME-SENSOR-ARCHITECTURE.md`**. Each signal is its own research module with 8
attributes (research question · economic mechanism · data · metric · validation · failure modes ·
historical-context output · maturity). The intelligence is the quality of each individual signal; the
presentation layer only organizes validated signals into multiple lenses — never a score, never a decision.

**Built / shipped:**
- **Volatility / risk-off** — the jump-model instrument (shipped: `live_label.py` → `regime_signal.py` →
  `results/regime_card.json`).
- **Stock-bond correlation** (inflation/real-rate) — `scripts/stockbond_corr.py`, built this session. Validated
  on US 1962-2026: sign matches known regimes; hedge-behavior-by-state confirms the signal (on equity-down days
  bonds cushioned 32% of the time in the "intact"/negative-corr regime vs fell-too 57% in the "violated"/
  positive-corr regime — monotone through the states). Design lessons: monthly-anchored regime read (daily
  126d calendar-mean hid the 2022 flip); avg-return-by-state is CONFOUNDED by the rate cycle (use the
  hedge-behavior metric). Still TODO: OOS confirmation on Japan/Europe (needs JGB/Bund series).

**To build (one GSD phase each): valuation · concentration · diversification/correlation (absorption) · credit
(EBP) · funding stress · crowding · tail (data-gated).** Then the presentation layer (assumption ledger + joint
rarity + historical analogues).

## NEXT ACTION

**GSD is set up** (2026-08-02) — a 10-phase roadmap scoped strictly to the signal modules lives in
`.planning/{ROADMAP,PROJECT,REQUIREMENTS,STATE,config}.md/.json`. Structure: Phase 1 = signal framework (shared
8-attribute spec + validation standards + output format + maturity model), Phases 2–9 = one signal each (2
stock-bond intl OOS · 3 valuation · 4 concentration · 5 absorption · 6 credit/EBP · 7 funding · 8 crowding · 9
tail, data-gated), Phase 10 = presentation/assumption ledger. Every phase's DoD is identical: **Find → Validate →
Present → STOP**, with the mechanism gate + intl OOS confirmation baked into each phase's success criteria. Config:
YOLO · coarse · sequential · quality models · Researcher+PlanCheck+Verifier enabled. CLAUDE.md HARD BOUNDARY was
preserved (NOT GSD-regenerated).

**Do next:** `/gsd:plan-phase 1` (Signal Framework) — lock the shared spec before building more signals. The first
NEW signal after that is **valuation** (Phase 3: high starting CAPE → historically lower long-horizon returns;
present as context, never "avoid equities"). Phase 2 (stock-bond intl OOS) is gated on JGB/Bund series.

## Signal-research discipline (full text in CLAUDE.md)

Causal-only; mechanism-first (orthogonality is a diagnostic, not the gate); confound-check every context stat;
out-of-hypothesis-sample intl confirmation before SUPPORT; one look + prereg + cooling-off + dated sign-off for
any positive claim; NO single-word regime summary; present, never conclude or allocate.
