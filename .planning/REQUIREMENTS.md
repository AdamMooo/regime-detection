# Requirements: Regime-Detection — Market-Signal Research System

**Defined:** 2026-08-02
**Core Value:** Each independently-validated signal surfaces a market assumption worth monitoring — fewer blind spots
for the human's judgment, never a forecast, never an action.

**Every requirement's Definition of Done is identical:** Find → Validate → Present → STOP.
A signal is done only when it declares its 8-attribute spec, passes the mechanism gate, is validated causally with
confound-checks, is confirmed out-of-hypothesis-sample (Japan/Europe) before any SUPPORT, and emits its
historical-context output (reading · rarity · assumption monitored) — with zero allocation/decision content.

## Already Validated (shipped — not in v1 build scope)

- ✓ **Volatility / risk-off signal** — jump-model instrument, shipped (`regime_card.json`).
- ✓ **Stock-bond correlation signal** — core built + US-validated 2026-08-02 (intl OOS confirmation tracked as SIG-01).

## v1 Requirements

Each maps to exactly one roadmap phase.

### Framework

- [ ] **FRWK-01**: The shared signal spec exists — 8-attribute template (research question · mechanism · data ·
  metric · validation · failure modes · historical-context output · maturity), validation standards, the
  historical-context/assumption-ledger output format, and the maturity model — that every subsequent signal declares
  against before it runs.

### Signals

- [ ] **SIG-01**: Analyst can read the stock-bond correlation signal's regime with out-of-hypothesis-sample
  (Japan/Europe) confirmation of the hedge-behavior mechanism — completing the built signal to SUPPORT standard.
- [ ] **SIG-02**: Analyst can read a valuation signal — current starting-valuation reading, its historical rarity,
  and the historically-conditioned long-horizon-return context — monitoring the "equities priced for normal returns"
  assumption. Presented as context, never "avoid equities".
- [ ] **SIG-03**: Analyst can read a concentration signal — index concentration / breadth reading and rarity —
  monitoring the "the index is diversified" assumption.
- [ ] **SIG-04**: Analyst can read a diversification/correlation signal — absorption ratio (cross-asset correlation
  compression) reading and rarity — monitoring the "diversification is intact" assumption.
- [ ] **SIG-05**: Analyst can read a credit signal — excess bond premium (EBP) reading and rarity — monitoring the
  "credit conditions are benign" assumption.
- [ ] **SIG-06**: Analyst can read a funding-stress signal — funding-market stress flag and rarity — monitoring the
  "funding is unstressed" assumption (tail-relevant).
- [ ] **SIG-07**: Analyst can read a crowding signal — factor/position crowding reading and rarity — monitoring the
  "factor premia aren't crowded" assumption.
- [ ] **SIG-08**: Analyst can read a tail signal — priced tail / jump risk reading and rarity — monitoring the
  "tail risk is not elevated" assumption (data-gated; may descope if data unavailable).

### Presentation

- [ ] **PRES-01**: Analyst can view the assumption ledger — all validated signals organized into multiple lenses
  (per-assumption reading, joint rarity across signals, closest historical analogues) — with zero score, zero
  single-word summary, zero decision content.

## v2 Requirements

(None — scope beyond the presentation layer is deferred until the signal set is validated.)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Any allocation / exposure / weight / sleeve / tilt / cash decision | HARD BOUNDARY — belongs to a separate system + the human |
| One-word regime summary ("risk-on/risk-off") | Destroys the multi-signal vector that is the whole value |
| Single composite score combining signals | Intelligence is per-signal, not the blend |
| The word "portfolio" / any implementation concept | HARD BOUNDARY — zero references in this repo |
| Prediction / forecasting as the deliverable | Edge is better human decisions, not forecasts |
| Equity-ownership / allocation program | Removed 2026-08-02; separate concern, in git history |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FRWK-01 | Phase 1 | Pending |
| SIG-01 | Phase 2 | Pending |
| SIG-02 | Phase 3 | Pending |
| SIG-03 | Phase 4 | Pending |
| SIG-04 | Phase 5 | Pending |
| SIG-05 | Phase 6 | Pending |
| SIG-06 | Phase 7 | Pending |
| SIG-07 | Phase 8 | Pending |
| SIG-08 | Phase 9 | Pending |
| PRES-01 | Phase 10 | Pending |

**Coverage:**
- v1 requirements: 10 total
- Mapped to phases: 10 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-02*
*Last updated: 2026-08-02 after roadmap creation (traceability populated)*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
</content>
