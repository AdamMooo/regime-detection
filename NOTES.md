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

## PHASE 1 COMPLETE (2026-08-03) — framework FROZEN v1.0 (signed off; see below)

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

## FRAMEWORK FROZEN v1.0 (2026-08-03) — Phase 1 CLOSED

Adam signed off the framework 2026-08-03 (`.planning/framework/SIGNOFF-CHECKLIST.md`). Dispositions: **A1**
(three-axis anchors) ACCEPTED · **A2** (maturity-derivation rule, structure) ACCEPTED · **A3** (forbid composite
scalar) ACCEPTED · **ADM** (unified admission model, D-17) CONFIRMED · **ENF** (code enforcement is architecture,
D-18) CONFIRMED · **OBS** (observatory framing) CONFIRMED. D-06 swap RESOLVED (superseded by ADM). All framework
docs bumped to v1.0; ROADMAP SC#3 + architecture stale "three confidence dims" text patched to the admission model.

**Enforcement is LIVE (code, not docs):** `scripts/signal_output_schema.py` (closed Level-0 allowlist + denylist +
`validate()`) and `tests/test_boundary_audit.py` (34 passed). On day one it caught a real HARD-BOUNDARY leak that
every prose "reviewed grep" had missed — vindicating D-18.

**Two open/tracked items (do NOT lose):**
- **RF (OPEN, cooling-off):** the shipped volatility signal's `production` tag rests on frozen-US OOS + the
  universal vol-persistence stylized fact, NOT a literal Japan/Europe run. Tag carried PROVISIONALLY. Decide the
  universal-stylized-fact clause vs a literal panel run when volatility is formally admitted (or at Phase 2).
- **`gauge.position` → `gauge.dwell_rank` rename (deferred cleanup):** boundary leak in `results/regime_card.json`
  (produced by `scripts/regime_signal.py`), a downstream contract. Carried as a single documented exception in
  `tests/test_boundary_audit.py` (`KNOWN_DEFERRED_EXCEPTIONS`). Coordinated rename (this repo + downstream repo) +
  remove the exception = end-of-project cleanup.

## NEXT ACTION

**Start building the layers (the signals).** Every signal MUST begin with a research charter (D-15, the six
pre-registration questions) BEFORE any implementation — the framework's own admission discipline. Then it runs
through: charter → research/build → validation (mechanism gate · confound · Japan/Europe OOS) → admission review
(3 non-compensatory axes + "why in front of an investor?") → cooling-off + dated sign-off → production.

Build targets: **Phase 2** = stock-bond correlation intl OOS (GATED on JGB/Bund series — needs data Adam
provides). **Phase 3 = valuation** = the first fully-new signal, buildable now (starting CAPE → long-horizon
return context; present as context, never "avoid equities"). Recommend starting Phase 3 valuation unless the
JGB/Bund data is ready for Phase 2. Per Adam: no auto-advance.

## Signal-research discipline (full text in CLAUDE.md)

Causal-only; mechanism-first (orthogonality is a diagnostic, not the gate); confound-check every context stat;
out-of-hypothesis-sample intl confirmation before SUPPORT; one look + prereg + cooling-off + dated sign-off for
any positive claim; NO single-word regime summary; present, never conclude or allocate.
