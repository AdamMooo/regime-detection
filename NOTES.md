# Regime-Detection — Session Notes

## Status
A **market-signal research system** (see CLAUDE.md HARD BOUNDARY — market data → independent signals →
historical context → regime relevance → STOP; never allocation/decisions). The equity-ownership / allocation
program was removed from this repo 2026-08-02 (recoverable in git history). Branch: main | Last updated: 2026-08-03

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

## PHASE 1 COMPLETE (2026-08-03) — framework frozen (pending sign-off)

**Phase 1 (Signal Framework) built + verified 7/7.** The shared spec every future signal declares against now
lives under **`.planning/framework/`**:
- `signal-spec-template.md` — semver 8-attribute template (D-04 order: Definition · Mechanism · Measurement ·
  Historical Context · Validation · Assumptions · Confidence · Limitations), question-form, forced "N/A because…".
- `validation-standards.md` — causal/PIT · mechanism gate · confound-check · Japan/Europe OOS · one-look+prereg+
  cooling-off+dated sign-off · TRIPOD completeness checklist · HARD BOUNDARY reviewed-grep audit · D-10 (no
  signal designed around a desired conclusion) · D-12 (optimize for integrity/reproducibility, not prediction).
- `research-charter-template.md` — D-15 six-question pre-registration required BEFORE any future signal is built.
- `signal-output-spec.md` — **unified signal-admission model** (2026-08-03, D-17, REPLACES the four-dimension
  confidence model): a **binary mechanism prerequisite gate** (pass/rejected) + **three graded non-compensatory
  axes** — measurement validity · investment usefulness (important question + unique information, static
  per-signal) · evidence maturity; the **maturity tag is DERIVED** {mechanism pass + 3 axes + sign-off +
  investor-question}, implementation-maturity dimension DROPPED. Assessment = "earned its place," never
  predictive. Descriptive maturity (production NOT "better" than research); Level 0 measurement · Level 1
  historical context · Level 2 regime relevance, STOP at Level 2; composite-scalar forbidden, kept distinct from
  the Phase-10 joint-rarity (Mahalanobis) lens. Level-0 closed `assessment{}` field set + boundary enforced in
  code next pass (schema allowlist + boundary-audit test + repo-structure rule — D-18, architecture not docs).
- `examples/{volatility,stock-bond-corr}-signal-declaration.md` — the two built signals retro-fit the template
  cleanly (fast/production + slow/research shapes).
- `SIGNOFF-CHECKLIST.md` — **everything unsigned; nothing frozen to v1.0.**
- `.planning/REGIME-SENSOR-ARCHITECTURE.md` now cross-links `.planning/framework/` as the governing spec (D-16).

**Observatory-framing refinement (2026-08-03, Adam-directed):** system-level name = **factor observatory /
decision-support layer**; module stays **signal** (canonical); **market-state factor** = informal synonym,
DISTINCT from an equity-return/priced-risk factor and from the killed regime-as-a-factor. Added to the
framework: each signal declares its **investment question** (template Q1.3) + its **cross-signal relationships**
(Q4.3), and Level-0 output gains **trend · extreme_conditions · cross_signal_relationships** — so the set is an
observatory, not disconnected readings. Pipeline (investment view): Market data → signal states → historical
context → *investor interpretation* → *investment decision*; the CODE stops after historical context (Level 2).
Glossary + framing live in `.planning/REGIME-SENSOR-ARCHITECTURE.md` §observatory framing.

Config note: `auto_advance` + `use_worktrees` disabled (sequential docs workflow). ROADMAP SC#3 + architecture
doc still say "three confidence dimensions" — superseded to FOUR (recorded in the new spec, not silently edited);
patch those two frozen docs to "four" once the framework is signed off.

## NEXT ACTION

**Adam to review + dated sign-off `.planning/framework/SIGNOFF-CHECKLIST.md`** before the framework freezes to
v1.0. Open items now **A1 · A2 · A3 · RF · OBS · ADM · ENF**: A1 (three-axis anchor thresholds) · A2
(maturity-derivation rule) · A3 (forbid-composite wording) · RF (the shipped volatility signal's production tag
rests on frozen-US OOS + a universal stylized fact, not literal Japan/Europe OOS — decide whether that satisfies
the maturity rule) · OBS (observatory framing + new output fields — confirm) · **ADM (the unified
signal-admission model, D-17 — confirm)** · **ENF (code-level boundary enforcement is architecture, D-18 —
confirm)**. The old D-06 current-relevance→implementation-maturity swap is RESOLVED (superseded by ADM). Then
patch ROADMAP SC#3 + architecture doc "three→four→admission-model" dims.

**Then Phase 2** — stock-bond correlation intl OOS (gated on JGB/Bund series). First NEW signal is **valuation**
(Phase 3). Per Adam: review Phase 1 before moving to future signal phases; do NOT auto-advance.

## Signal-research discipline (full text in CLAUDE.md)

Causal-only; mechanism-first (orthogonality is a diagnostic, not the gate); confound-check every context stat;
out-of-hypothesis-sample intl confirmation before SUPPORT; one look + prereg + cooling-off + dated sign-off for
any positive claim; NO single-word regime summary; present, never conclude or allocate.
