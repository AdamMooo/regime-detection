# Valuation Signal — Charter Kickoff (start-here for a fresh context window)

**Purpose:** everything a cold session needs to open the **valuation research charter** — the first real signal
lifecycle — without re-reading the framework-building conversation. Read this + the framework files below; do not
reopen framework design.

## Where we are
- **Phase 1 framework is FROZEN v1.1 and enforced** (schema allowlist + `tests/test_boundary_audit.py`, 34 passed).
  Do NOT redesign the architecture unless a genuine contradiction is found.
- Valuation was chosen as the **first candidate signal**. It has already **PASSED the Stage-0 Relevance Gate**
  (answers below — drop them into the charter's G1–G5 opening block verbatim).
- Roadmap note: this is Phase 3. Phase 2 (stock-bond intl OOS) is deferred — it is data-gated on JGB/Bund series.
  Starting valuation first was Adam's explicit direction.

## The task (this session)
Open the valuation **research charter** = a **pre-registration** artifact, frozen **before any data look**.
- **Objective:** determine whether valuation *earns admission under the framework* — NOT to prove valuation works.
- **Scientific skepticism is the point.** Declare, in advance, the specific results that would **REJECT** admission,
  not only those that would support it. The framework exists to reject weak signals as much as to admit strong ones.
- **No look spent, no results.** The charter is hypotheses + pre-commitments only. Any positive/SUPPORT claim later
  needs one-look + prereg + cooling-off + dated sign-off (repo discipline).
- Write it against the frozen template and save to:
  `.planning/phases/03-valuation-signal/03-VALUATION-CHARTER.md`

## Files to read first
- `.planning/framework/research-charter-template.md` — the v1.1 charter template (six questions + G1–G5 block).
- `.planning/framework/validation-standards.md` — mechanism gate, causal/PIT, confound-check, Japan/Europe OOS,
  the lifecycle (Relevance Gate → Charter → Research → Validation → Admission → cooling-off → Production).
- `.planning/framework/signal-spec-template.md` — the 8-attribute spec the charter is the front-matter subset of.
- `.planning/framework/signal-output-spec.md` — admission model (mechanism prerequisite + 3 non-compensatory axes:
  measurement validity · investment usefulness · evidence maturity; DERIVED maturity tag) + Level 0/1/2 output shape.
- `CLAUDE.md` — the HARD BOUNDARY (zero allocation/decision content; present, never conclude).
- `NOTES.md` — current state.

## Relevance Gate result (PASSED) — carry into the charter G1–G5 block
- **G1 — investment question:** where do long-horizon (≈4–10yr) forward equity returns start from, given today's
  valuation relative to history?
- **G2 — why it matters to long-term investors:** starting valuation is the most robust conditioner of long-horizon
  real returns (Campbell–Shiller); it governs whether long-horizon return *expectations* are reasonable.
- **G3 — unique information:** distinct from the volatility axis (PC1) and the stock-bond-correlation axis (PC2);
  a slow *level/price* dimension neither of the existing signals carries.
- **G4 — leave-one-out:** removing it leaves the observatory blind to "expensive vs cheap" — a first-order blind
  spot for long-horizon return context. Meaningful loss ⇒ keep.
- **G5 — ex-ante prior:** strong. Decades of literature (Campbell–Shiller CAPE; discount-rate / price-of-ERP);
  strong at 4–10yr horizons, ≈0 sub-1yr.

## The six charter questions (fill in order; map to spec attributes 1/2/5/6/8)
1. **What investment question does valuation answer?** (attr 1)
2. **What market assumption does it monitor?** (the ledger key — e.g. "equities are priced for near-normal
   long-horizon returns") (attr 1 / header)
3. **What mechanism supports it — why does it survive being known?** (attr 2) — Campbell–Shiller decomposition
   (price = f(expected cashflows, discount rates)); mean-reversion in the discount-rate / equity-risk-premium
   component. State it as a risk-premium channel, not a forecasting trick.
4. **What evidence would VALIDATE it?** (attr 5) — horizon-conditional relationship (sign + magnitude; strong
   4–10yr, weak sub-1yr), robust across sub-periods, confounds addressed, and out-of-hypothesis-sample
   confirmation on Japan/Europe.
5. **What would FALSIFY / REJECT it?** (attr 6) — declared-before-testing: e.g. no horizon structure; sign
   instability; the relationship fully explained by a confound (secular real-rate decline; buyback/payout shifts
   changing the earnings denominator; accounting/earnings-definition changes; smoothing-window artifacts;
   trailing-earnings look-ahead; survivorship); failure to replicate on Japan/Europe.
6. **What does it explicitly NOT claim?** (attr 8) — names a monitored assumption and STOPS; NOT a market-timing
   trigger, NOT "avoid equities," NOT a return forecast. Strong at long horizons, silent at short ones.

## Skepticism scaffold (address honestly in Q4/Q5 — do not resolve here; the charter only pre-registers)
- **Metric choice is itself a decision:** CAPE / Shiller PE10 vs alternatives (aggregate P/E, P/B, Tobin's Q,
  total-market-cap/GDP, dividend yield). Pre-commit to one primary + why, and state the smoothing window.
- **Known confounds to pre-declare:** secular real-rate / discount-rate decline; buyback-driven payout changes;
  earnings-definition / accounting-standard shifts (GAAP changes, write-off treatment); sector-mix drift
  (higher-margin, asset-light composition → structurally higher "fair" CAPE); trailing-earnings vintage /
  look-ahead; index survivorship.
- **The known limitation up front:** valuation is a *very slow conditioner*, useless as a short-horizon trigger —
  that is a feature (it monitors a long-horizon assumption), not a bug. The production representation must reflect
  this: a level/percentile + long-horizon-return *context* reading, never a buy/sell or exposure statement.

## Production representation (Q6 / output) — pre-commit direction
A Level-0 record per the frozen `assessment{}` schema: `reading` (current valuation + qualitative), `rarity`
(historical percentile), `trend`, `extreme_conditions`, `cross_signal_relationships`, `clock` = structural/slow,
`assessment{mechanism, measurement_validity, investment_usefulness, evidence_maturity}`, DERIVED `maturity`.
Zero allocation/decision fields — enforced by the boundary-audit test.

## Discipline reminders
Causal-only, point-in-time (valuation inputs get revised — reconstruct point-in-time). Charter frozen before the
validation look. Present, never conclude, never allocate. Maturity starts low; production requires the full chain.

---
*Created 2026-08-03 as the fresh-context kickoff for the valuation signal charter. Delete or supersede once
`03-VALUATION-CHARTER.md` exists.*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
