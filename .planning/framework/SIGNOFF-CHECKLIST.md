# Framework Sign-Off Checklist

**Status: NOT SIGNED — nothing in the framework is frozen to v1.0.**

This consolidates every `[ASSUMED]` / veto item in the Phase-1 framework that requires Adam's **dated, explicit
sign-off** before the framework freezes at v1.0. Per repo discipline (`CLAUDE.md`), a positive claim or a freeze
is **never inferred from a conversational go-ahead** — it needs the dated line at the bottom of this file.

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

Nothing above is frozen until this line is completed by Adam:

- **A1 three-axis anchors + starting points:** _______________  (disposition)  ______________  (date)
- **A2 maturity derivation rule:** _______________  (disposition)  ______________  (date)
- **A3 forbid composite-scalar field:** _______________  (disposition)  ______________  (date)
- **ADM unified signal-admission model (D-17):** _______________  (confirm / revise)  ______________  (date)
- **ENF code-level boundary enforcement is architecture (D-18):** _______________  (confirm / revise)  ______________  (date)
- **RF production-tag vs Japan/Europe OOS:** _______________  (disposition)  ______________  (date)
- **OBS observatory framing + new output fields:** _______________  (confirm / revise)  ______________  (date)
- **D-06 current-relevance → implementation-maturity swap:** RESOLVED — superseded by ADM (D-17); no separate disposition.

- **Framework frozen to v1.0:** ______________________________  (Adam, dated)  ______________

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
