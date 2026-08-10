# Roadmap: Regime-Detection — Market-Signal Research System

> **STATUS 2026-08-10 — 4 of 8 LIVE phases are COMPLETE. 3 phases were DROPPED. All 4 remaining
> phases are blocked on an owner RULING, not on engineering work.**
>
> - **Complete:** 1 (framework, 2026-08-03) · 1.5 (volatility, 2026-08-06) · 2 (stock-bond, 2026-08-07) · 10 (presentation, 2026-08-10)
> - **Dropped at the charter stage, no look spent:** 5 (MI-007) · 7 (MI-008) · 8 (MI-013). Sections and rows kept below; removed from the execution order only.
> - **Remaining, and independent of each other** — each waits on a named decision, not on a predecessor phase:
>   - **3 Valuation** — the R9 disposition. One look SPENT 2026-08-07; zero build work remains.
>   - **4 Concentration** — 5 open charter items + the V3 (resolution) ruling. Built and construction-gated; charter UNSIGNED.
>   - **6 Credit (EBP)** — Adam writes the four V2 statistics in `scripts/validate_credit.py`. Charter v1.0 SIGNED; one look UNSPENT.
>   - **9 Tail** — accept or reject the price-of-protection reframe. Built; charter UNSIGNED; the phase dies if the reframe is rejected.
>
> Tests: **215 passing** (bare `pytest`). Per-phase rulings are tabulated in §Progress.

## Overview

This is a market-*understanding* research program, not an application build. It delivers a set of independent
market-signal modules, each validated on a real economic mechanism, that surface which abstract market
assumptions are currently supported or challenged — then STOP. The journey: first lock the shared signal
framework every module declares against; then build and validate ONE signal at a time (each an independent
research module with an identical Definition of Done — Find → Validate → Present → STOP); finally compose the
validated signals into an assumption ledger that organizes them into multiple lenses. No phase decides,
recommends, or implies any investment action. The intelligence is the quality of each individual signal, never
a combination of them into a score.

**Definition of Done (identical for every signal phase):** Find → Validate → Present → STOP. A signal is done
only when it (a) declares its 8-attribute spec, (b) passes the mechanism gate with a written structural reason
it survives being known, (c) is validated causally with confound-checks, (d) is confirmed
out-of-hypothesis-sample on Japan/Europe before any SUPPORT claim, and (e) emits its historical-context output
(reading · rarity · assumption monitored) with zero allocation/decision content.

**Gate-zero precondition (framework v1.1, D-19):** before opening its research charter, every signal phase MUST
first pass the **Stage-0 Relevance Gate** (`.planning/framework/validation-standards.md` §Stage 0 — 5 questions,
default = NO, leave-one-out / marginal-information test). No charter is opened and no research time is spent on a
candidate that has not passed the gate — the observatory is a curated set, not an indicator library.

**Build discipline (efficiency, D-20):** the DoD is IDENTICAL across signals, so its machinery is built ONCE and
reused, never rebuilt per signal. Shared harness — causal primitives (expanding percentile · EWMA · drift ·
rarity), the Japan/Europe OOS runner (one dynamic `run_oos(construct_fn, regions)` over
`build_intl_panel.build_region`), and the historical-context output (through `signal_output_schema.validate`).
Each signal contributes only its construct-function + charter; no signal builds its own panel loader, OOS
harness, or output schema. Built first on Phase 1.5 (vol) as the template, then reused by every later signal.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Signal Framework** - The shared 8-attribute spec, validation standards, output format, and maturity model every signal declares against (completed 2026-08-03)
- [x] **Phase 1.5: Volatility Signal (INSERTED 2026-08-04)** - Continuous vol descriptors (level · percentile · drift · rarity) replacing the inherited jump-model STATE; the foundational (PC1) barometer, buildable now; executes before the data-gated Phase 2 (completed 2026-08-06 — results signed off, maturity `production`, ledger MI-002)
- [x] **Phase 2: Stock-Bond Correlation Signal (intl OOS)** - Complete the built inflation/real-rate signal to SUPPORT via Japan/Europe confirmation (completed 2026-08-07 — results signed off, maturity `research`, ledger MI-003 VALIDATED)
- [ ] **Phase 3: Valuation Signal** - Starting-valuation → long-horizon-return context, monitoring "equities priced for normal returns" — BLOCKED on the R9 disposition; one look SPENT 2026-08-07, no build work remains (ledger MI-009)
- [ ] **Phase 4: Concentration Signal** - Index concentration / breadth, monitoring "the index isn't dependent on a few names" — BLOCKED on 5 open charter items + the V3 ruling; built + construction-gated, charter UNSIGNED (ledger MI-011)
- [ ] **Phase 5: Diversification / Correlation Signal** - Absorption ratio (cross-asset correlation compression), monitoring "diversification is intact" — **DROPPED 2026-08-06** (ledger MI-007; record at `.planning/archive/dropped-signals/05-ABSORPTION-DROPPED.md`)
- [ ] **Phase 6: Credit Signal (EBP)** - Excess bond premium, monitoring "credit conditions are benign" — BLOCKED on Adam writing the four V2 statistics; charter v1.0 SIGNED 2026-08-09, one look UNSPENT (ledger MI-010)
- [ ] **Phase 7: Funding-Stress Signal** - Funding-market stress flag, monitoring "funding markets function" (tail-relevant) — **DROPPED 2026-08-06** (ledger MI-008; record at `.planning/archive/dropped-signals/07-FUNDING-DROPPED.md`)
- [ ] **Phase 8: Crowding Signal** - Factor/position crowding, monitoring "factor premia aren't crowded" — **DROPPED 2026-08-05** (ledger MI-013; **no charter was written and no Stage-0 record exists** — the only record is `.planning/archive/dropped-signals/README.md:59-62`)
- [ ] **Phase 9: Tail Signal** - Priced tail / jump risk, monitoring "the distribution is its normal shape" (data-gated; may descope) — BLOCKED on accepting the price-of-protection reframe; built, charter UNSIGNED (ledger MI-012)
- [x] **Phase 10: Presentation / Assumption Ledger** - Organize validated signals into multiple lenses; no score, no summary, no decision (SHIPPED 2026-08-10 on two admitted signals + concentration as a candidate; reframed — the informativeness map is the output object and carries the ledger as a section; Level 2 is an explicit unbuilt seam)

## Phase Details

### Phase 1: Signal Framework

**Goal**: The shared signal spec exists — the single template and standards every subsequent signal declares against before it runs
**Depends on**: Nothing (first phase)
**Requirements**: FRWK-01
**Success Criteria** (what must be TRUE):

  1. A written 8-attribute signal-spec template exists (research question · mechanism · data+vintage · metric · validation · failure modes · historical-context output · maturity) that a new signal can be filled in against unambiguously
  2. The validation standards are documented in one place: causal-only / point-in-time rule, the mechanism gate (a written structural reason the signal survives being known), confound-check requirement, out-of-hypothesis-sample (Japan/Europe) confirmation rule, and the one-look + prereg + cooling-off + dated sign-off protocol for any SUPPORT claim
  3. The historical-context output format is specified — reading · rarity percentile · assumption monitored, carried with the signal-admission assessment (a binary mechanism prerequisite gate + three non-compensatory axes: measurement validity · investment usefulness · evidence maturity) and a DERIVED maturity tag (production / research / rejected) — with zero allocation/decision fields
  4. The assumption-ledger output shape is defined as the composition target (Level 0 state vector · Level 1 assumption ledger · Level 2 context) so validated signals have a known place to render, never a score
  5. Each later signal phase can declare against this spec without reinterpreting it (the template is the single source of truth)

**Plans**: 2 plans

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — merged 8-attribute signal-spec template + validation-standards doc

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — historical-context output format, four-dimension confidence model, maturity model, assumption-ledger shape (L0/1/2) + retro-fit

### Phase 1.5: Volatility Signal (INSERTED 2026-08-04)

**Status**: COMPLETE — results signed off by Adam 2026-08-06 (`1.5-VOLATILITY-CHARTER.md` §RESULTS SIGN-OFF), derived maturity `production`, ledger MI-002 VALIDATED. `observations/volatility/history.ndjson` carries 1190 records from 1927-07-30
**Goal**: The inherited jump-model vol signal is replaced by continuous volatility descriptors (level · percentile · drift · rarity) — measured, never a CALM/STRESSED state — and earns admission through the standard DoD
**Depends on**: Phase 1
**Why inserted**: the no-look detector benchmark (`results/detector_benchmark.csv`) showed the jump-model STATE loses to a continuous vol + hysteresis read on every skill axis (LT20 BAC 0.75 vs 0.66; 11/11 vs 9/11 episodes; 21d vs 56d lag) and the threshold step destroys σ's graded information; vol is the foundational (PC1) barometer and is buildable now, whereas Phase 2 is data-gated
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec (a measured level + percentile + drift, no latent state); the charter names vol as a CONTEXT dimension, not an intact/violated assumption-monitor
  2. The mechanism gate is passed: volatility clustering (Mandelbrot 1963 / Engle 1982 / Bollerslev 1986) — a written structural reason it survives being known (a proven stylized fact)
  3. Causal validation with confound-checks: EWMA σ + expanding percentile are causal/PIT; the JM-vs-vol+hysteresis benchmark is formalized as the skill evidence
  4. Out-of-hypothesis-sample confirmation on Japan/Europe (`ohlc_nikkei` / `ohlc_stoxx`): the clustering + percentile construction replicates — closes the long-standing RF open item (the vol production tag never had a literal intl run)
  5. The historical-context output is emitted through `signal_output_schema.validate` — reading · rarity percentile · drift, zero decision content; the continuous read (`vol_read.py`) feeds the daily brief's vol row, replacing VIX

**Plans**: 2 plans (2/2 complete)

Plans:

- [x] 1.5-01: Charter + Stage-0 gate; centralize causal primitives + build the generic `run_oos` harness (D-20, reused by all later signals)
- [x] 1.5-02: Japan/Europe OOS replication + emit historical-context output + dated sign-off

### Phase 2: Stock-Bond Correlation Signal (intl OOS)

**Status**: COMPLETE — results signed off by Adam 2026-08-07 (`02-STOCKBOND-CHARTER.md` §RESULTS SIGN-OFF), derived maturity `research` (not `production`: both intl panels start 1990-07, so the OOS sample holds no 1970s–80s inflation regime). Japan/Europe OOS RAN and is monotone in all three regions (US 28→44→56% · Japan 25→29→51% · Europe 27→32→48%). Ledger MI-003 VALIDATED. `observations/stock_bond_correlation/history.ndjson` carries 756 records from 1963-12-31
**Goal**: The built inflation/real-rate signal reaches SUPPORT standard — its hedge-behavior mechanism confirmed out-of-hypothesis-sample
**Depends on**: Phase 1
**Requirements**: SIG-01
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the Phase 1 framework
  2. The mechanism gate is passed: a written structural reason the hedge-behavior signal (inflation-growth covariance → bonds hedge vs bet) survives being known
  3. Causal validation with confound-checks is reconfirmed — the hedge-behavior-by-state metric is used (not the rate-cycle-confounded avg-return-by-state), monthly-anchored, no look-ahead
  4. Out-of-hypothesis-sample confirmation on Japan/Europe: the monotone hedge-behavior-by-state pattern replicates (JGB/Bund panels), or a documented failure is recorded before any SUPPORT
  5. The historical-context output is emitted — reading (correlation sign / regime) · rarity percentile · assumption monitored ("bonds hedge equity drawdowns") — with zero decision content

**Plans**: 2 plans (2/2 complete)

Plans:

- [x] 02-01: Build Japan/Europe panels and run the hedge-behavior-by-state OOS replication
- [x] 02-02: Emit the historical-context output and record the maturity tag with dated sign-off

### Phase 3: Valuation Signal

**Status**: BLOCKED on an owner ruling — **the R9 disposition. Zero build work remains.** Charter v1.1 signed 2026-08-07; the **one look is SPENT** the same day → `results/valuation_validation.txt`. Five of six bars clear; **V6 (bias-aware inference) does NOT** — block-bootstrap p = 0.07–0.26 at every horizon on both return objects, ρ = 0.9965, corr(return innovation, regressor innovation) = +0.96, Stambaugh removes 64–72% of the raw 1-month slope. Both defensible readings are written into the charter. **Do NOT rerun the bootstrap with another seed or block length.** R5 (payout confound) is a registered UNTESTABLE reject condition. No `observations/valuation/` log exists, deliberately, while R9 is open. Ledger MI-009 VALIDATING
**Goal**: A valuation signal reads current starting-valuation and its historically-conditioned long-horizon-return context, monitoring "forward returns are near normal"
**Depends on**: Phase 1 (framework) only. The former "Phase 2" dependency was sequencing, not a real input — corrected 2026-08-10; this phase is independent of 4, 6 and 9
**Requirements**: SIG-02
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework (statistical method appropriate to a very-slow conditioner, never a trigger)
  2. The mechanism gate is passed: a written structural reason (discount-rate / price-of-ERP, Campbell-Shiller) it survives being known — strong at 4–10yr, ~0 sub-1yr
  3. Causal validation with confound-checks: the starting-valuation → long-horizon-return relationship is measured point-in-time with confounds addressed
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — current valuation reading · historical rarity · long-horizon-return context — presented as context, never "avoid equities", with zero decision content

**Plans**: 2 plans (1/2 complete)

Plans:

- [x] 03-01: Construct the valuation metric and its historically-conditioned long-horizon-return context
- [ ] 03-02: Run intl OOS confirmation and emit the historical-context output — **intl OOS RAN** (V5, log D/P 1975-2025, inside the spent one-look); the historical-context emission is **deliberately withheld while R9 is open**, which is why no `observations/valuation/` log exists. Not engineering work — it resumes the moment R9 is ruled

### Phase 4: Concentration Signal

**Status**: BLOCKED on an owner ruling — **5 open charter items + the V3 (resolution) decision.** Built and construction-gated: `scripts/build_concentration.py` + `scripts/concentration.py`, `results/concentration_gate.csv` C1–C5 all True, `data/processed/concentration_monthly.csv` 1200 months 1926-07-31..2026-06-30, `build()` under `assert_causal`. **Charter is v0.2 DRAFT, UNSIGNED; no validation bar has been run; no look spent.** Rendered as an explicit CANDIDATE axis in `results/informativeness_map.json` (own list, dashed section, `maturity: null`, reading recomputed because no `observations/concentration/` log exists, excluded from `--known-at` replay). V3 is make-or-break and the draft expects R3 to fire ("the Mag-7 question is seven names *inside* one bucket"). Ledger MI-011 IDEA
**Goal**: A concentration signal reads index concentration / breadth and its rarity, monitoring "the index isn't dependent on a few names"
**Depends on**: Phase 1 (framework) only. The former "Phase 3" dependency was sequencing — corrected 2026-08-10; this phase is independent of 3, 6 and 9. Its own charter's binding precondition (a written de-confliction against Phase 5, or one of the two drops) was satisfied for free when Phase 5 was dropped
**Requirements**: SIG-03
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework (a measured level + percentile, no latent state)
  2. The mechanism gate is passed: a written structural reason (cap-weight structure inherits a few megacaps' idiosyncratic risk) it survives being known — and it is kept distinct from crowding by mechanism, not statistics
  3. Causal validation with confound-checks: concentration decouples from vol where expected (e.g. 2021 / early-2024), with the healthy-vs-fragile ambiguity surfaced honestly
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — concentration reading · rarity percentile · assumption monitored — with zero decision content

**Plans**: 2 plans (1/2 complete)

Plans:

- [x] 04-01: Construct the concentration/breadth metric and characterize its decoupling from vol — construction + gate only (`concentration_gate.csv` C1–C5 True); no validation bar run
- [ ] 04-02: Run intl OOS confirmation and emit the historical-context output — blocked on the charter sign-off (5 open items + V3), not on code

### Phase 5: Diversification / Correlation Signal

**Status**: **DROPPED 2026-08-06** at the charter stage, no look spent. Ledger row **MI-007** (REJECTED). Archive record: `.planning/archive/dropped-signals/05-ABSORPTION-DROPPED.md` (kickoff: `05-KICKOFF.md`). Killed on readability, not mechanism: its only unique content over volatility is a ~1-month lead and the matched panel publishes at a verified 69-day lag. Section kept — a deleted row loses the record of why. Removed from the execution order only.
**Goal**: A diversification signal reads the absorption ratio (cross-asset correlation compression) and its rarity, monitoring "diversification is intact"
**Depends on**: Phase 4
**Requirements**: SIG-04
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework (an eigenstructure object)
  2. The mechanism gate is passed: a written structural reason (eigenstructure compaction, Kritzman 2011) it survives being known — kept for its LEAD, with its partial redundancy with vol declared up front
  3. Causal validation with confound-checks: the absorption-ratio construction is causal and its lead property is characterized against vol
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — absorption-ratio reading · rarity percentile · assumption monitored — with zero decision content

**Plans**: 2 plans (0/2 — phase DROPPED)

Plans:

- [ ] 05-01: Construct the absorption-ratio metric and characterize its lead vs vol — **NOT RUN (phase DROPPED 2026-08-06)**
- [ ] 05-02: Run intl OOS confirmation and emit the historical-context output — **NOT RUN (phase DROPPED 2026-08-06)**

### Phase 6: Credit Signal (EBP)

**Status**: BLOCKED on an owner ruling — **Adam writes the four V2 statistics** (`revisions` / `bar_a` / `bar_b` / `bar_c`) in `scripts/validate_credit.py` (Learning Mode; scaffolding self-tests 6/6, refuses to run without `--i-am-spending-the-one-look`). Charter **v1.0 FROZEN and SIGNED 2026-08-09**; build authorised; **the one look is UNSPENT — no cross-vintage statistic has been computed.** V2's evidence base is harvested: **20 distinct vintages, 2022-08-18..2026-03-23**, in `data/vintages/ebp/`. Registered pre-look and not reopenable: maturity capped at `research`; **R2 firing ⇒ DROP, not demotion** (A ≤ 0.25 · B ≥ 0.95 · **C ≥ 0.90 decisive**). Two specification gaps must close before the look (bar-B aggregation across vintages; bar-C pooled vs per-vintage). G4 uniqueness is **UNOPPOSED, not confirmed** — the registered leave-one-out was against MI-008, which was dropped. Ledger MI-010 IDEA
**Goal**: A credit signal reads the excess bond premium and its rarity, monitoring "credit conditions are benign"
**Depends on**: Phase 1 (framework) only. The former "Phase 5" dependency is **dead — Phase 5 was DROPPED 2026-08-06**; corrected 2026-08-10. Independent of 3, 4 and 9
**Requirements**: SIG-05
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework, including the GZ micro-panel construction and its vintage/revision exposure
  2. The mechanism gate is passed: a written structural reason (intermediary risk-appetite / credit supply, Gilchrist-Zakrajšek) it survives being known — the EBP *residual*, not raw credit (which duplicates vol's Merton channel)
  3. Causal validation with confound-checks: point-in-time construction, no look-ahead, its leading (1–2yr) property characterized
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — EBP reading · rarity percentile · assumption monitored — with zero decision content

**Plans**: 2 plans (1/2 complete)

Plans:

- [x] 06-01: Construct the GZ excess-bond-premium residual point-in-time — `scripts/build_credit.py` + `scripts/credit_ebp.py` → `results/credit_descriptors.csv` + `results/credit_vintage.json`; 20 vintages archived. `scripts/validate_credit.py` scaffolded, look UNSPENT
- [ ] 06-02: Run intl OOS confirmation and emit the historical-context output — blocked on the four V2 statistics Adam writes, then the one look

### Phase 7: Funding-Stress Signal

**Status**: **DROPPED 2026-08-06** at the charter stage, no look spent. Ledger row **MI-008** (REJECTED). Archive record: `.planning/archive/dropped-signals/07-FUNDING-DROPPED.md` (kickoff: `07-KICKOFF.md`). Killed on measurability: the only PIT-clean, credit-free, unspliced construction (`SOFR99 − SOFR`) starts 2018 with two episodes; `cp3m` missingness is endogenous, so the flag goes dark exactly when funding seizes. `scripts/build_funding.py` and both funding panels deleted 2026-08-10 (recoverable in git history). Section kept. Removed from the execution order only.
**Goal**: A funding-stress signal reads a funding-market stress flag and its rarity, monitoring "funding markets function" (tail-relevant)
**Depends on**: Phase 6
**Requirements**: SIG-06
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework (an episodic binary flag on a fast clock)
  2. The mechanism gate is passed: a written structural reason (funding-liquidity spirals, Brunnermeier-Pedersen) it survives being known — high confidence when it fires, silent otherwise
  3. Causal validation with confound-checks: the flag construction is causal and its tail-episodic behavior is characterized honestly (including when it goes silent)
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — funding-stress flag · rarity percentile · assumption monitored — with zero decision content

**Plans**: 2 plans (0/2 — phase DROPPED)

Plans:

- [ ] 07-01: Construct the funding-stress flag and map its firing/silent episodes — **NOT RUN (phase DROPPED 2026-08-06)**
- [ ] 07-02: Run intl OOS confirmation and emit the historical-context output — **NOT RUN (phase DROPPED 2026-08-06)**

### Phase 8: Crowding Signal

**Status**: **DROPPED 2026-08-05**. Ledger row **MI-013** (REJECTED). **No charter was ever written and there is no Stage-0 record** — unlike MI-007/MI-008, which each have a full dropped-signal memo. The entire rationale is three lines at `.planning/archive/dropped-signals/README.md:59-62`. MI-013 records two problems with that record (the "real positioning data infeasible solo" objection targets a form `REGIME-SENSOR-ARCHITECTURE.md:368` had already scoped out; "risks re-reading the volatility axis" was never tested) **without reopening the drop.** Section kept. Removed from the execution order only.
**Goal**: A crowding signal reads factor/position crowding and its rarity, monitoring "factor premia aren't crowded"
**Depends on**: Phase 7
**Requirements**: SIG-07
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework, with the return-based comomentum construction and its narrowness (factor-crowding only) declared as a scope limit
  2. The mechanism gate is passed: a written structural reason (consensus + leverage → fire-sale externality, Stein 2009) it survives being known — kept distinct from concentration by mechanism (forced-unwind vs index-dependence)
  3. Causal validation with confound-checks: the comomentum construction is causal, with confounds addressed
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — crowding reading · rarity percentile · assumption monitored — with zero decision content

**Plans**: 2 plans (0/2 — phase DROPPED)

Plans:

- [ ] 08-01: Construct the return-based comomentum crowding metric — **NOT RUN (phase DROPPED 2026-08-05; no charter, no Stage-0 record)**
- [ ] 08-02: Run intl OOS confirmation and emit the historical-context output — **NOT RUN (phase DROPPED 2026-08-05)**

### Phase 9: Tail Signal

**Status**: BLOCKED on an owner ruling — **accept or reject the price-of-protection reframe** (monitored assumption moves from "the return distribution is its normal shape", physical and unmeasurable from this data, to "downside protection is priced normally", risk-neutral). **The phase dies if the reframe is not accepted; DROP is registered as defensible.** Built: `scripts/build_tail.py` → `tail_daily.csv`, `scripts/tail_skew.py` → `results/tail_skew.csv` + `results/tail_vintage.json`. **Charter is v0.2 DRAFT, UNSIGNED; V1–V8 registered, none run; no look spent.** Its own registered prior is that **R4 (redundancy with vol) likely fires** — "given Kozhan et al., R4 firing is likely, not a surprise". Maturity capped at `research` permanently: intl replication is impossible, not unattempted (no risk-neutral skew index exists for JP/EU), so `run_oos.py` cannot serve this signal. Nine `[recommended]` items await a ruling. Ledger MI-012 IDEA
**Goal**: A tail signal reads priced tail / jump risk and its rarity, monitoring "the distribution is its normal shape" (data-gated)
**Depends on**: Phase 1 (framework) only. The former "Phase 8" dependency is **dead — Phase 8 was DROPPED 2026-08-05**; corrected 2026-08-10. Independent of 3, 4 and 6
**Requirements**: SIG-08
**Success Criteria** (what must be TRUE):

  1. Data availability is resolved first — the options / high-frequency inputs are sourced, or the phase is explicitly descoped with the data gap documented (measurement confidence is L by design)
  2. If built: the signal declares its 8-attribute spec and passes the mechanism gate (separately-priced jump/crash premium, Bollerslev-Todorov / Kelly-Jiang) with a written structural reason it survives being known
  3. If built: causal validation with confound-checks on the priced-tail construction
  4. If built: out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. If built: the historical-context output is emitted — tail-risk reading · rarity percentile · assumption monitored — with zero decision content; if descoped, the descope decision and reason are recorded

**Plans**: 1 plan (1/1 complete)

Plans:

- [x] 09-01: Resolve options/HF data availability; build the priced-tail metric or record the descope decision — data resolved (Cboe SKEW, sha-stamped vintage) and the metric is BUILT (`scripts/tail_skew.py`). The descope/keep decision is the open ruling: the price-of-protection reframe is UNACCEPTED and the charter is UNSIGNED

### Phase 10: Presentation / Assumption Ledger

**Status**: **SHIPPED 2026-08-10 — and REFRAMED.** Delivered `scripts/assumption_ledger.py` (Level 0 state vector + Level 1 ledger → `results/assumption_ledger.{json,html}`) **and** `scripts/informativeness_map.py` (→ `results/informativeness_map.{json,html}`). **The informativeness map is the output object; the assumption ledger is a SECTION inside it.** Every axis is a first-class row whether or not it carries a status, because the `{intact|under_test|violated}` vocabulary is only honest for a quantity with a mechanical boundary and exactly one here has one (correlation sign) — volatility, concentration and tail each refused a status in their own charters and those refusals stand. Two independent dimensions per axis (`standing`, `novelty`), never merged, no one-word axis summary. **Success criteria 1 and 4 are met; criteria 2 (joint rarity) and 3 (historical analogues) are Level 2 and deliberately NOT built — the seam is `assumption_ledger.level2_context()`.** Delivery is built (`scripts/mailer.py` + `scripts/send_ledger.py`, `--dry-run` default, works offline) but **no schedule is enabled**: `.github/workflows/assumption-ledger.yml` has `schedule:` commented out with a dated reason; `workflow_dispatch` retained. Enabling it is Adam's call.
**Goal**: The validated signals are organized into an assumption ledger with multiple lenses — never a score, never a summary, never a decision
**Depends on**: Shipped on the **two admitted signals** (volatility, stock-bond correlation) plus concentration rendered as an explicit CANDIDATE — not on Phases 2–9. Recorded 2026-08-10; the original "Phases 2–9" dependency never held, and 3/4/6/9 remain open behind it
**Requirements**: PRES-01
**Success Criteria** (what must be TRUE):

  1. An assumption-ledger artifact renders every validated signal's monitored assumption with its status (intact / under test / violated), sensor evidence, rarity, and the three confidence scores — status as an observation, never an instruction
  2. Joint rarity across signals is computed and shown (Mahalanobis distance of the sensor vector from historical normal), preserving the full per-signal vector — never collapsed to a scalar
  3. Closest historical analogues are surfaced (nearest-neighbour *configurations*, e.g. "resembles 2018-Q4 / early-2022"), forecasting-free
  4. The output contains zero composite score, zero single-word / risk-on-risk-off summary, and zero allocation/decision content — verified against the HARD BOUNDARY

**Plans**: 2 plans (2/2 complete)

Plans:

- [x] 10-01: Assemble the assumption ledger (Level 0 vector + Level 1 ledger) from validated signals — SHIPPED 2026-08-10; source is `observations/<signal>/history.ndjson` through `current_view()`, never the `results/*.csv` spines, enforced by an AST scan
- [x] 10-02: Add joint rarity and historical-analogue lenses; run the HARD BOUNDARY audit — SHIPPED 2026-08-10 **as the informativeness map**, not as the two Level-2 lenses. The HARD BOUNDARY audit RAN (both artifacts' prose + HTML, closed key sets, forward-looking-key ban, no-negative-`.shift()`). **Joint rarity and historical analogues are NOT built** — they are Level 2 and attach at `assumption_ledger.level2_context()`; no distance is computed anywhere in this repo

## Progress

**4 of 8 LIVE phases COMPLETE. 3 phases DROPPED. All 4 remaining phases are blocked on an owner RULING, not on engineering work.**

**Execution Order (corrected 2026-08-10):**
`1 → 1.5 → 2 → 10 (shipped) → {3, 4, 6, 9}`

The old strict numeric order was wrong twice over: it routed through three phases that were DROPPED (5, 7, 8), and Phase 10 already shipped **ahead of** 3/4/6/9. **The four remaining phases are independent of each other** — none is a predecessor of another, and each is blocked on a named ruling rather than on sequence, so they can be taken in any order. `{}` denotes an unordered set. Dropped phases are removed from the order and keep their sections and ledger rows below.

Recommended pick order if capacity is scarce (not a dependency): **6 credit → 4 concentration → 9 tail** — credit is the only one whose own charter does not pre-call its decisive bar against it; tail's own draft names it "first phase to cut if capacity is tight."

| Phase | Plans Complete | Status | Completed | Blocked on |
|-------|----------------|--------|-----------|------------|
| 1. Signal Framework | 2/2 | Complete   | 2026-08-03 | — |
| 1.5 Volatility Signal (INSERTED) | 2/2 | Complete | 2026-08-06 | — (maturity `production`, MI-002) |
| 2. Stock-Bond Correlation (intl OOS) | 2/2 | Complete | 2026-08-07 | — (maturity `research`, MI-003 VALIDATED) |
| 3. Valuation Signal | 1/2 | Blocked — one look SPENT | - | **Adam's R9 disposition.** V6 failed; zero build work remains (MI-009) |
| 4. Concentration Signal | 1/2 | Blocked — built + construction-gated | - | **5 open charter items + the V3 (resolution) ruling.** Charter UNSIGNED, no bar run (MI-011) |
| 5. Diversification / Correlation Signal | 0/2 | **DROPPED 2026-08-06** | - | n/a — MI-007; `.planning/archive/dropped-signals/05-ABSORPTION-DROPPED.md` |
| 6. Credit Signal (EBP) | 1/2 | Blocked — charter SIGNED, look UNSPENT | - | **Adam writes the four V2 statistics** in `scripts/validate_credit.py` (MI-010) |
| 7. Funding-Stress Signal | 0/2 | **DROPPED 2026-08-06** | - | n/a — MI-008; `.planning/archive/dropped-signals/07-FUNDING-DROPPED.md` |
| 8. Crowding Signal | 0/2 | **DROPPED 2026-08-05** | - | n/a — MI-013; no charter, no Stage-0 record; `.planning/archive/dropped-signals/README.md:59-62` |
| 9. Tail Signal | 1/1 | Blocked — built, charter UNSIGNED | - | **Accept or reject the price-of-protection reframe.** The phase dies if rejected (MI-012) |
| 10. Presentation / Assumption Ledger | 2/2 | **SHIPPED — reframed** | 2026-08-10 | — for delivery; **Level 2 is an explicit unbuilt seam** and **no schedule is enabled** (Adam's call) |

**Live-phase totals:** 8 live phases, **4 complete (50%)**; 15 live plans, 12 complete. Dropped phases (5, 7, 8) are excluded from both denominators and from the execution order; their 6 plans were never run.

---
---
---
---
---
---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
</content>
</invoke>
