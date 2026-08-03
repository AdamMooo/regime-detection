# Framework Sign-Off Checklist

**Status: FROZEN to v1.0 — signed off by Adam 2026-08-03 (explicit close-off instruction this session).**
Design items A1 · A2 (structure) · A3 · ADM · ENF · OBS are ACCEPTED/CONFIRMED. **One item remains OPEN by
design: RF** (the volatility signal's `production` tag — a signal-level maturity claim held under the
no-rushing / cooling-off rule; the volatility example's production tag is carried PROVISIONALLY until RF is
decided). **One tracked deferred cleanup:** the `gauge.position → gauge.dwell_rank` rename (see Known deferred
issues). Frozen v1.0 rules are amendable only via the semver amendment process, never edited to fit one signal.

This consolidates every item in the Phase-1 framework requiring Adam's **dated, explicit sign-off** before the
framework freezes at v1.0. Per repo discipline (`CLAUDE.md`), a freeze is **never inferred from a casual
remark** — the dispositions below record Adam's explicit close-off decision of 2026-08-03.

---

## Items awaiting sign-off

| # | Item | Source | What is decided vs proposed | Disposition needed |
|---|------|--------|-----------------------------|--------------------|
| **A1** | The **three admission-axis anchor thresholds + declared starting points** (measurement validity · investment usefulness · evidence maturity) | `signal-output-spec.md` §1 | The unified-model *structure* (binary mechanism gate + three non-compensatory axes) is DECIDED (D-17); only the H/M/L threshold wording + starting points are proposed | sign-off / revise |
| **A2** | The **maturity derivation rule** (production / research / rejected DERIVED from {mechanism = pass · the three axes · dated sign-off · answerable investor-question}) | `signal-output-spec.md` §2 | Derivation *approach* is decided (derived, not authored; descriptive per D-13; implementation-maturity dimension dropped per D-17); the specific threshold combination is proposed | sign-off / revise |
| **A3** | **Forbid any composite-scalar output field entirely** (superseding the architecture doc's "CISS-style composite as a derived secondary view"); joint rarity / Mahalanobis distance stays permitted as a distinct Level-2 lens | `signal-output-spec.md` §4.4 | Recommended default = forbid; needs confirmation Adam does not want a derived composite view retained | sign-off / revise |
| **ADM** | The **unified signal-admission model** (D-17) REPLACES the four-dimension confidence model: binary mechanism prerequisite gate + three non-compensatory graded axes (measurement validity · investment usefulness · evidence maturity) + a DERIVED maturity tag; implementation-maturity dimension DROPPED; investment usefulness is a static per-signal judgment (incremental-information + investor-question), never a per-reading applicability score | `signal-output-spec.md` §1–§3, `validation-standards.md` §(l) | Adam-directed this session; model *structure* decided (D-17), listed for confirm-at-freeze | confirm / revise |
| **ENF** | **Code-level boundary enforcement is architecture, not documentation-only** (D-18): a closed Level-0 output schema (allowlist) + a runnable boundary-audit test + a repo-structure rule (no code aware of any allocation/decision system). Rules fixed this pass; code built next pass | `signal-output-spec.md` §4.6, `validation-standards.md` §(m), `REGIME-SENSOR-ARCHITECTURE.md` §boundary enforcement | Adam-directed this session; listed for confirm-at-freeze | confirm / revise |
| **D-06 swap** | ~~The current-relevance → implementation-maturity dimension swap~~ — **SUPERSEDED / RESOLVED by the unified admission model (ADM / D-17).** The entire four-dimension model is replaced: implementation-maturity is DROPPED (becomes the derived tag) and current-relevance / regime-relevance / portfolio-relevance stay DROPPED (predictive framing). No separate disposition needed — subsumed by ADM | `signal-output-spec.md` §3 | Superseded by D-17; recorded for the audit trail | resolved (see ADM) |
| **RF** | Retro-fit surfaced tension: the **production tag vs literal Japan/Europe OOS** for the shipped volatility signal — its production status rests on frozen-US OOS + the universal vol-persistence stylized fact rather than a literal Japan/Europe panel run. Either the A2 rule needs a "universal-stylized-fact" clause, or the volatility signal needs the explicit panel run | `examples/volatility-signal-declaration.md` §Versioned-amendment candidates | Surfaced by the retro-fit; not yet resolved | decide with A2 |
| **OBS** | The **observatory-framing refinement** (2026-08-03, Adam-directed): system-level name = "factor observatory / decision-support layer"; module stays "signal" (canonical), "market-state factor" an informal synonym distinct from equity-return/priced-risk factors; each signal must declare its **investment question** (template Q1.3), **why that question matters** for
understanding (Q1.4 — data availability is not a sufficient reason), and its **cross-signal relationships**
(Q4.3); three new Level-0 output fields **trend · extreme_conditions · cross_signal_relationships**; the
explicit **one-way boundary** (understanding engine ↛ allocation targets / exposure / trades / orders) | `REGIME-SENSOR-ARCHITECTURE.md` §observatory framing + §one-way boundary + glossary; `signal-spec-template.md` Q1.3/Q1.4/Q4.3; `signal-output-spec.md` §4.1 | Adam-directed this session; listed for confirm-at-freeze (field definitions are the only proposed part) | confirm / revise |

---

## Retro-fit readiness evidence

The frozen template was filled against both already-built signals before any freeze:

- **Volatility / jump-model** (`examples/volatility-signal-declaration.md`) — filled cleanly (fast,
  return-derived state model; maturity = production). One cross-signal amendment candidate (clock-vocabulary
  tempo field) and the RF tension above surfaced.
- **Stock-bond correlation** (`examples/stock-bond-corr-signal-declaration.md`) — filled cleanly (slow,
  returns-based correlation-sign signal; maturity = research), including two genuine forced
  `Not applicable, because …` answers — the template working as designed.

**Both retro-fits filled cleanly (no template edit required for fit).** The template accommodates two genuinely
heterogeneous signal shapes — the evidence it is ready to be considered for freeze, subject to the sign-off items
above.

---

## Dated sign-off

Recorded per Adam's explicit close-off decision, 2026-08-03:

- **A1 three-axis anchors + starting points:** ACCEPTED — adopted as v1.0 (Adam, 2026-08-03); amendable via semver if a real signal stresses them.
- **A2 maturity derivation rule:** ACCEPTED (structure) — maturity DERIVED from {mechanism = pass · three axes · dated sign-off · answerable investor-question} (Adam, 2026-08-03). The one open sub-point — whether a documented universal stylized fact substitutes for a literal Japan/Europe OOS in reaching evidence-maturity = H — is RF below.
- **A3 forbid composite-scalar field:** ACCEPTED — forbid entirely; joint-rarity/Mahalanobis lens permitted + distinct (Adam, 2026-08-03).
- **ADM unified signal-admission model (D-17):** CONFIRMED (Adam, 2026-08-03).
- **ENF code-level boundary enforcement is architecture (D-18):** CONFIRMED (Adam, 2026-08-03) — schema + boundary-audit test built + green (34 passed); caught the `gauge.position` leak.
- **RF production-tag vs Japan/Europe OOS:** **OPEN — DEFERRED (cooling-off).** Not blocking the framework freeze (signal-level tag question). Volatility example's `production` tag carried PROVISIONALLY; decide the universal-stylized-fact clause vs a literal Japan/Europe run when the volatility signal is formally admitted (or at Phase 2).
- **OBS observatory framing + new output fields:** CONFIRMED (Adam, 2026-08-03).
- **D-06 current-relevance → implementation-maturity swap:** RESOLVED — superseded by ADM (D-17); no separate disposition.

- **Framework frozen to v1.0:** **ADOPTED — Adam, 2026-08-03** (explicit close-off authorization this session), with RF open and the `gauge.position` rename tracked below.

---

## Amendment log

Amendments to the frozen v1.0 follow the semver amendment process — additive, never editing a v1.0 decision to fit
one signal. The v1.0 sign-off record above, the open **RF** item, and the tracked `gauge.position` rename are
unchanged.

- **v1.1 (2026-08-03)** — **Stage-0 Relevance Gate + quality-over-quantity philosophy (D-19).** Added a
  pre-charter triage (5 questions · default = NO · leave-one-out / marginal-information test) ahead of the charter
  and all research time, plus the curated-observatory philosophy (scarce resource = research time / attention, not
  code; smallest high-quality set; popularity is not evidence; TA faces an extremely high bar). The gate's Q4
  leave-one-out was added to the investment-usefulness admission axis as the rigorous post-research form of the
  same concern. Touched `validation-standards.md`, `research-charter-template.md`, `signal-output-spec.md`,
  `signal-spec-template.md` (all bumped v1.0 → v1.1), `REGIME-SENSOR-ARCHITECTURE.md`, `01-CONTEXT.md` (D-19), and
  `ROADMAP.md` (per-phase DoD). Purely additive; no frozen v1.0 rule altered.

---

## Known deferred issues (tracked, not silent)

- **`gauge.position` → `gauge.dwell_rank` rename.** The boundary-audit test caught a real HARD-BOUNDARY vocabulary
  leak: `results/regime_card.json` → `gauge.position` (a dwell-rank percentile string, produced by
  `scripts/regime_signal.py`), a field literally named `position`. It is semantically benign (position *in the
  distribution*, not a trading position) but violates the boundary by the letter. **Deferred, not fixed**, because
  `regime_card.json` is a downstream contract (consumed by a separate repo); renaming now would break that
  consumer, and downstream coordination is deferred to end-of-project cleanup (Adam, 2026-08-03). Carried as a
  single documented exception in `tests/test_boundary_audit.py` (`KNOWN_DEFERRED_EXCEPTIONS`). **The coordinated
  rename (`regime_signal.py` + `regime_card.json` + the downstream read) must be done at cleanup, and the test
  exception removed then.**

- **RF (above).** Volatility `production` tag provisional pending the universal-stylized-fact-vs-literal-OOS decision.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
