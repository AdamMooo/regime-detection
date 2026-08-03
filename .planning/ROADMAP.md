# Roadmap: Regime-Detection — Market-Signal Research System

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

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Signal Framework** - The shared 8-attribute spec, validation standards, output format, and maturity model every signal declares against (completed 2026-08-03)
- [ ] **Phase 2: Stock-Bond Correlation Signal (intl OOS)** - Complete the built inflation/real-rate signal to SUPPORT via Japan/Europe confirmation
- [ ] **Phase 3: Valuation Signal** - Starting-valuation → long-horizon-return context, monitoring "equities priced for normal returns"
- [ ] **Phase 4: Concentration Signal** - Index concentration / breadth, monitoring "the index isn't dependent on a few names"
- [ ] **Phase 5: Diversification / Correlation Signal** - Absorption ratio (cross-asset correlation compression), monitoring "diversification is intact"
- [ ] **Phase 6: Credit Signal (EBP)** - Excess bond premium, monitoring "credit conditions are benign"
- [ ] **Phase 7: Funding-Stress Signal** - Funding-market stress flag, monitoring "funding markets function" (tail-relevant)
- [ ] **Phase 8: Crowding Signal** - Factor/position crowding, monitoring "factor premia aren't crowded"
- [ ] **Phase 9: Tail Signal** - Priced tail / jump risk, monitoring "the distribution is its normal shape" (data-gated; may descope)
- [ ] **Phase 10: Presentation / Assumption Ledger** - Organize validated signals into multiple lenses; no score, no summary, no decision

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

### Phase 2: Stock-Bond Correlation Signal (intl OOS)

**Goal**: The built inflation/real-rate signal reaches SUPPORT standard — its hedge-behavior mechanism confirmed out-of-hypothesis-sample
**Depends on**: Phase 1
**Requirements**: SIG-01
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the Phase 1 framework
  2. The mechanism gate is passed: a written structural reason the hedge-behavior signal (inflation-growth covariance → bonds hedge vs bet) survives being known
  3. Causal validation with confound-checks is reconfirmed — the hedge-behavior-by-state metric is used (not the rate-cycle-confounded avg-return-by-state), monthly-anchored, no look-ahead
  4. Out-of-hypothesis-sample confirmation on Japan/Europe: the monotone hedge-behavior-by-state pattern replicates (JGB/Bund panels), or a documented failure is recorded before any SUPPORT
  5. The historical-context output is emitted — reading (correlation sign / regime) · rarity percentile · assumption monitored ("bonds hedge equity drawdowns") — with zero decision content

**Plans**: TBD

Plans:

- [ ] 02-01: Build Japan/Europe panels and run the hedge-behavior-by-state OOS replication
- [ ] 02-02: Emit the historical-context output and record the maturity tag with dated sign-off

### Phase 3: Valuation Signal

**Goal**: A valuation signal reads current starting-valuation and its historically-conditioned long-horizon-return context, monitoring "forward returns are near normal"
**Depends on**: Phase 2
**Requirements**: SIG-02
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework (statistical method appropriate to a very-slow conditioner, never a trigger)
  2. The mechanism gate is passed: a written structural reason (discount-rate / price-of-ERP, Campbell-Shiller) it survives being known — strong at 4–10yr, ~0 sub-1yr
  3. Causal validation with confound-checks: the starting-valuation → long-horizon-return relationship is measured point-in-time with confounds addressed
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — current valuation reading · historical rarity · long-horizon-return context — presented as context, never "avoid equities", with zero decision content

**Plans**: TBD

Plans:

- [ ] 03-01: Construct the valuation metric and its historically-conditioned long-horizon-return context
- [ ] 03-02: Run intl OOS confirmation and emit the historical-context output

### Phase 4: Concentration Signal

**Goal**: A concentration signal reads index concentration / breadth and its rarity, monitoring "the index isn't dependent on a few names"
**Depends on**: Phase 3
**Requirements**: SIG-03
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework (a measured level + percentile, no latent state)
  2. The mechanism gate is passed: a written structural reason (cap-weight structure inherits a few megacaps' idiosyncratic risk) it survives being known — and it is kept distinct from crowding by mechanism, not statistics
  3. Causal validation with confound-checks: concentration decouples from vol where expected (e.g. 2021 / early-2024), with the healthy-vs-fragile ambiguity surfaced honestly
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — concentration reading · rarity percentile · assumption monitored — with zero decision content

**Plans**: TBD

Plans:

- [ ] 04-01: Construct the concentration/breadth metric and characterize its decoupling from vol
- [ ] 04-02: Run intl OOS confirmation and emit the historical-context output

### Phase 5: Diversification / Correlation Signal

**Goal**: A diversification signal reads the absorption ratio (cross-asset correlation compression) and its rarity, monitoring "diversification is intact"
**Depends on**: Phase 4
**Requirements**: SIG-04
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework (an eigenstructure object)
  2. The mechanism gate is passed: a written structural reason (eigenstructure compaction, Kritzman 2011) it survives being known — kept for its LEAD, with its partial redundancy with vol declared up front
  3. Causal validation with confound-checks: the absorption-ratio construction is causal and its lead property is characterized against vol
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — absorption-ratio reading · rarity percentile · assumption monitored — with zero decision content

**Plans**: TBD

Plans:

- [ ] 05-01: Construct the absorption-ratio metric and characterize its lead vs vol
- [ ] 05-02: Run intl OOS confirmation and emit the historical-context output

### Phase 6: Credit Signal (EBP)

**Goal**: A credit signal reads the excess bond premium and its rarity, monitoring "credit conditions are benign"
**Depends on**: Phase 5
**Requirements**: SIG-05
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework, including the GZ micro-panel construction and its vintage/revision exposure
  2. The mechanism gate is passed: a written structural reason (intermediary risk-appetite / credit supply, Gilchrist-Zakrajšek) it survives being known — the EBP *residual*, not raw credit (which duplicates vol's Merton channel)
  3. Causal validation with confound-checks: point-in-time construction, no look-ahead, its leading (1–2yr) property characterized
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — EBP reading · rarity percentile · assumption monitored — with zero decision content

**Plans**: TBD

Plans:

- [ ] 06-01: Construct the GZ excess-bond-premium residual point-in-time
- [ ] 06-02: Run intl OOS confirmation and emit the historical-context output

### Phase 7: Funding-Stress Signal

**Goal**: A funding-stress signal reads a funding-market stress flag and its rarity, monitoring "funding markets function" (tail-relevant)
**Depends on**: Phase 6
**Requirements**: SIG-06
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework (an episodic binary flag on a fast clock)
  2. The mechanism gate is passed: a written structural reason (funding-liquidity spirals, Brunnermeier-Pedersen) it survives being known — high confidence when it fires, silent otherwise
  3. Causal validation with confound-checks: the flag construction is causal and its tail-episodic behavior is characterized honestly (including when it goes silent)
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — funding-stress flag · rarity percentile · assumption monitored — with zero decision content

**Plans**: TBD

Plans:

- [ ] 07-01: Construct the funding-stress flag and map its firing/silent episodes
- [ ] 07-02: Run intl OOS confirmation and emit the historical-context output

### Phase 8: Crowding Signal

**Goal**: A crowding signal reads factor/position crowding and its rarity, monitoring "factor premia aren't crowded"
**Depends on**: Phase 7
**Requirements**: SIG-07
**Success Criteria** (what must be TRUE):

  1. The signal declares its 8-attribute spec against the framework, with the return-based comomentum construction and its narrowness (factor-crowding only) declared as a scope limit
  2. The mechanism gate is passed: a written structural reason (consensus + leverage → fire-sale externality, Stein 2009) it survives being known — kept distinct from concentration by mechanism (forced-unwind vs index-dependence)
  3. Causal validation with confound-checks: the comomentum construction is causal, with confounds addressed
  4. Out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. The historical-context output is emitted — crowding reading · rarity percentile · assumption monitored — with zero decision content

**Plans**: TBD

Plans:

- [ ] 08-01: Construct the return-based comomentum crowding metric
- [ ] 08-02: Run intl OOS confirmation and emit the historical-context output

### Phase 9: Tail Signal

**Goal**: A tail signal reads priced tail / jump risk and its rarity, monitoring "the distribution is its normal shape" (data-gated)
**Depends on**: Phase 8
**Requirements**: SIG-08
**Success Criteria** (what must be TRUE):

  1. Data availability is resolved first — the options / high-frequency inputs are sourced, or the phase is explicitly descoped with the data gap documented (measurement confidence is L by design)
  2. If built: the signal declares its 8-attribute spec and passes the mechanism gate (separately-priced jump/crash premium, Bollerslev-Todorov / Kelly-Jiang) with a written structural reason it survives being known
  3. If built: causal validation with confound-checks on the priced-tail construction
  4. If built: out-of-hypothesis-sample confirmation on Japan/Europe before any SUPPORT, or a documented failure
  5. If built: the historical-context output is emitted — tail-risk reading · rarity percentile · assumption monitored — with zero decision content; if descoped, the descope decision and reason are recorded

**Plans**: TBD

Plans:

- [ ] 09-01: Resolve options/HF data availability; build the priced-tail metric or record the descope decision

### Phase 10: Presentation / Assumption Ledger

**Goal**: The validated signals are organized into an assumption ledger with multiple lenses — never a score, never a summary, never a decision
**Depends on**: Phases 2–9 (the validated signals)
**Requirements**: PRES-01
**Success Criteria** (what must be TRUE):

  1. An assumption-ledger artifact renders every validated signal's monitored assumption with its status (intact / under test / violated), sensor evidence, rarity, and the three confidence scores — status as an observation, never an instruction
  2. Joint rarity across signals is computed and shown (Mahalanobis distance of the sensor vector from historical normal), preserving the full per-signal vector — never collapsed to a scalar
  3. Closest historical analogues are surfaced (nearest-neighbour *configurations*, e.g. "resembles 2018-Q4 / early-2022"), forecasting-free
  4. The output contains zero composite score, zero single-word / risk-on-risk-off summary, and zero allocation/decision content — verified against the HARD BOUNDARY

**Plans**: TBD

Plans:

- [ ] 10-01: Assemble the assumption ledger (Level 0 vector + Level 1 ledger) from validated signals
- [ ] 10-02: Add joint rarity and historical-analogue lenses; run the HARD BOUNDARY audit

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Signal Framework | 2/2 | Complete   | 2026-08-03 |
| 2. Stock-Bond Correlation (intl OOS) | 0/2 | Not started | - |
| 3. Valuation Signal | 0/2 | Not started | - |
| 4. Concentration Signal | 0/2 | Not started | - |
| 5. Diversification / Correlation Signal | 0/2 | Not started | - |
| 6. Credit Signal (EBP) | 0/2 | Not started | - |
| 7. Funding-Stress Signal | 0/2 | Not started | - |
| 8. Crowding Signal | 0/2 | Not started | - |
| 9. Tail Signal | 0/1 | Not started | - |
| 10. Presentation / Assumption Ledger | 0/2 | Not started | - |

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
</content>
</invoke>
