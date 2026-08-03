# Framework Sign-Off Checklist

**Status: NOT SIGNED — nothing in the framework is frozen to v1.0.**

This consolidates every `[ASSUMED]` / veto item in the Phase-1 framework that requires Adam's **dated, explicit
sign-off** before the framework freezes at v1.0. Per repo discipline (`CLAUDE.md`), a positive claim or a freeze
is **never inferred from a conversational go-ahead** — it needs the dated line at the bottom of this file.

---

## Items awaiting sign-off

| # | Item | Source | What is decided vs proposed | Disposition needed |
|---|------|--------|-----------------------------|--------------------|
| **A1** | The four confidence-dimension **anchor thresholds + declared starting points** (measurement quality · mechanism support · evidence robustness · implementation maturity) | `signal-output-spec.md` §1 | The four-dimension *structure* is DECIDED (D-06); only the H/M/L threshold wording + starting points are proposed | sign-off / revise |
| **A2** | The **maturity derivation rule** (production / research / rejected from attribute 5 + implementation-maturity dimension) | `signal-output-spec.md` §2 | Derivation *approach* is decided (derived, not authored; descriptive per D-13); the specific threshold combination is proposed | sign-off / revise |
| **A3** | **Forbid any composite-scalar output field entirely** (superseding the architecture doc's "CISS-style composite as a derived secondary view"); joint rarity / Mahalanobis distance stays permitted as a distinct Level-2 lens | `signal-output-spec.md` §4.4 | Recommended default = forbid; needs confirmation Adam does not want a derived composite view retained | sign-off / revise |
| **D-06 swap** | The **current-relevance → implementation-maturity dimension swap** — the old fourth dimension (current-relevance / regime-relevance / portfolio-relevance guard) is DROPPED and replaced by implementation maturity, because current-relevance leaned predictive/applicability framing that D-06 forbids | `signal-output-spec.md` §1.4, §3 | Mandated by the D-06 refinement; surfaced here explicitly for **Adam's dated VETO** if he disagrees | **veto** / accept |
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

- **A1 anchors + starting points:** _______________  (disposition)  ______________  (date)
- **A2 maturity derivation rule:** _______________  (disposition)  ______________  (date)
- **A3 forbid composite-scalar field:** _______________  (disposition)  ______________  (date)
- **D-06 current-relevance → implementation-maturity swap:** _______________  (accept / veto)  ______________  (date)
- **RF production-tag vs Japan/Europe OOS:** _______________  (disposition)  ______________  (date)
- **OBS observatory framing + new output fields:** _______________  (confirm / revise)  ______________  (date)

- **Framework frozen to v1.0:** ______________________________  (Adam, dated)  ______________

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
