# Valuation Signal — Research Charter

**Charter v1.0** — filled against framework template **v1.1** (`research-charter-template.md`).

This is a **pre-registration** artifact, frozen **before any data look**. It answers the six charter questions in
order (mapping to spec attributes 1 / 2 / 3-context / 5 / 6 / 8) and declares, in advance, both what would make
valuation **earn admission** and the specific results that would **REJECT** it. No look has been spent; there are
no results in this document. Any later positive / SUPPORT claim requires one-look + the frozen protocol +
overnight cooling-off + Adam's dated sign-off (`validation-standards.md` §(e)). Deviations from the analysis
spec below are disclosed with a dated note, never silently edited (registered-report discipline).

**Objective:** determine whether valuation *earns admission under the framework* — NOT to prove valuation works.

---

## Header

- **Signal name** — Valuation
- **Assumption monitored** — *"Equities are priced for near-normal long-horizon returns."*
- **Native clock / frequency** — structural / slow (monthly-anchored read; the signal is a very slow conditioner)
- **Maturity tag** — DERIVED, not yet assessed. Pre-validation (no look spent). `research` at the earliest, and
  only after the full chain (validation → 3 axes → cooling-off → dated sign-off); `production` requires
  international OOS + an answerable investor-question. Do not hand-set.
- **Investor question (production bar)** — *"Given today's price level relative to history, is the starting point
  for long-horizon equity returns historically normal, high, or low?"* A context reading about the environment,
  never a forecast or an action.
- **Charter/spec version** — v1.0
- **Charter dated** — 2026-08-03 (frozen pre-registration; dated sign-off pending)

---

## Stage-0 Relevance Gate (PASSED — carried verbatim from `03-CHARTER-KICKOFF.md`)

The gate is the pre-charter triage, default = NO. Valuation cleared all five before this charter was opened.

- **G1 — investment question:** where do long-horizon (≈4–10yr) forward equity returns start from, given today's
  valuation relative to history?
- **G2 — why it matters to long-term investors:** starting valuation is the most robust conditioner of
  long-horizon real returns (Campbell–Shiller); it governs whether long-horizon return *expectations* are
  reasonable.
- **G3 — unique information:** distinct from the volatility axis (PC1) and the stock-bond-correlation axis (PC2);
  a slow *level/price* dimension neither existing signal carries.
- **G4 — leave-one-out:** removing it leaves the observatory blind to "expensive vs cheap" — a first-order blind
  spot for long-horizon return context. Meaningful loss ⇒ keep.
- **G5 — ex-ante prior:** strong. Decades of literature (Campbell–Shiller CAPE; discount-rate / price-of-ERP);
  strong at 4–10yr horizons, ≈0 sub-1yr.

---

## The six charter questions

### 1. What question does the signal answer?

*Where do long-horizon (≈4–10yr) forward equity returns start from, given today's price level relative to
history?* The signal measures how expensive the broad equity market is versus its own history and expresses it as
a historical percentile plus a long-horizon-return *context* reading. It is a slow price/level dimension: it does
not describe near-term risk (volatility, PC1) or the inflation/real-rate hedge axis (stock-bond correlation, PC2),
but the *starting valuation* from which multi-year returns compound.

Unique information (feeds the investment-usefulness axis): valuation carries a level/price signal that neither
admitted signal contains. A market can be low-volatility *and* expensive, or high-volatility *and* cheap — the
axes are mechanistically distinct. Removing valuation leaves the observatory unable to say whether long-horizon
return *expectations* are starting from a historically normal base.

### 2. What market assumption does it monitor?

The ledger key: **"Equities are priced for near-normal long-horizon returns."** Read as a status observation, never
an instruction — e.g. *under-test — CAPE at the 95th percentile, a historically low starting point for 10yr real
returns.* Status ∈ {intact | under-test | violated} describes the assumption; it never implies an action.

### 3. What mechanism supports it — why does it survive being known?

**Registered mechanism: risk-premium-primary (discount-rate channel). Behavioral effects are a permitted secondary
amplifier but are NOT load-bearing.**

**The identity.** Log-linearizing the one-period return around the mean log dividend–price ratio and iterating
forward under no-bubbles (Campbell–Shiller 1988) gives the present-value identity

> p_t − d_t ≈ const + Σ_{j≥0} ρ^j [ Δd_{t+1+j} − r_{t+1+j} ],  ρ ≈ 0.96 annually.

This is an **accounting identity, not a theory** (up to the log-linear approximation it holds by construction).
Valuation today is therefore a sufficient statistic for the market's *joint* expectation of {future cashflow
growth, future returns}: a high price must imply high expected growth, low expected returns (low discount rates),
or a mix. There is no third term.

**Which term moves.** The empirical record (Cochrane 2011 AFA presidential "Discount Rates"; Cochrane 2008 "The
Dog That Did Not Bark") is that dividend/earnings growth is nearly unforecastable from the price–dividend ratio,
while returns *are* forecastable. Valuation variation maps overwhelmingly to the **discount-rate** term. Since the
discount rate = risk-free rate + equity risk premium, this is a **risk-premium channel**: high valuation ⟺ low
discount rate ⟺ low expected forward return.

**Why it survives being known (the mechanism gate).** This is not an arbitrage. Harvesting "low expected return
from high valuation" requires shorting equities and bearing undiversifiable equity risk — exactly the risk being
(under-)compensated. A low risk premium cannot be traded away by public knowledge; it is a property of the
discount rate, not a mispricing that disappears once recognized. That is why the relationship remains informative
after everyone knows it — the requirement the mechanism gate exists to enforce. A persistent-mispricing
(behavioral) mechanism would also predict reversal but is more fragile to being known; it is therefore admitted
here only as a non-load-bearing amplifier.

**The horizon structure is a prediction of the mechanism, not an accident to discover.** The discount rate
mean-reverts slowly (half-life of years). Over ~1yr, realized returns are dominated by unforecastable news, so the
small predictable component is swamped → R² ≈ 0. Over 4–10yr, noise variance averages down *and* the slow
reversion has time to play out → the predictable component accumulates → R² rises. "Strong at 4–10yr, silent
sub-1yr" is thus the mechanism's signature, which is what makes it a sharp pre-registration target.

Maps to spec attribute 2; gated by `validation-standards.md` §(b) The mechanism gate.

### 4. What evidence would validate it?

The descriptive properties to test (each paired with its reject condition in Q5). Held to the full cross-signal law
(causal / point-in-time, confound-check, Japan/Europe out-of-hypothesis-sample, one-look freeze).

- **V1 — horizon-conditional structure.** Forward real return regressed on starting valuation shows a *negative*
  slope whose magnitude and R² **rise with horizon**: strong at 4–10yr, ≈0 sub-1yr. The *shape* (not a single
  point estimate) is the signature of the slow discount-rate channel.
- **V2 — excess returns.** The relationship holds for returns in **excess of the short real risk-free rate** (the
  clean risk-premium object), not only total real returns. This is the primary discriminator separating repeatable
  risk-premium reversion from a one-time discount-rate re-rating.
- **V3 — sub-period stability.** The negative sign holds across sub-periods **including *and* excluding the
  1982–2021 secular rate-decline window.** A relationship that exists only *because of* that window is the rate
  regime, not repeatable reversion.
- **V4 — metric robustness.** Sign + horizon structure survive on a pre-committed **payout-/accounting-robust
  metric panel** (see analysis spec), not on CAPE alone — so the reading is not a denominator artifact
  (buyback / accounting / composition).
- **V5 — out-of-hypothesis-sample.** The property replicates on the **Japan and Europe** panels with the correct
  sign and horizon structure, or a documented failure is recorded. Japan is the deliberately hard test (the
  canonical "expensive predicted disaster, but on a decade-scale clock; cheap stayed cheap").
- **V6 — bias-aware inference.** Predictability survives correction for the persistent-regressor / overlapping-data
  bias (see analysis spec). Raw OLS long-horizon R² is treated as **descriptive only**, never as the evidence.

Maps to spec attribute 5.

### 5. What would falsify it?

Declared before any testing. Each reject condition is paired with the validation test it trips.

- **R1 (primary, per Adam) — no excess-return information consistent with the mechanism.** The reject condition is
  NOT "growth predictability exists." If valuation forecasts *cashflow growth* rather than *returns*, the
  accounting identity is still satisfied but the signal has **changed category** — it would be a separate
  growth-expectation signal, not a validation of valuation as a forward-return signal, and it fails *this*
  charter's objective. Reject when there is **no evidence valuation carries useful information about future excess
  returns consistent with the proposed discount-rate mechanism.** (Trips V2.)
- **R2 — no horizon structure.** Relationship flat across horizons, or strongest at *short* horizons. Kills the
  slow-discount-rate mechanism. (Trips V1.)
- **R3 — sign instability.** Sign flips across sub-periods. (Trips V3.)
- **R4 — real-rate confound not cleared.** The relationship vanishes on excess returns, or once the real-rate
  level is controlled, or once 1982–2021 is excluded. Then valuation is a secular-rate proxy — a one-time regime,
  not repeatable reversion — and it would duplicate the stock-bond/real-rate PC2 axis, failing leave-one-out.
  (Trips V2 + V3.)
- **R5 — payout confound.** Disappears under a total-payout-yield metric (dividends + net buybacks). Buybacks
  displaced dividends post-1982; a dividend-based reading can look artificially expensive. Then it was a
  payout-policy artifact. (Trips V4.)
- **R6 — accounting confound.** Disappears under accounting-robust metrics (cap/GDP, price/dividend, price/sales,
  Tobin's Q). GAAP write-off treatment (FAS 142; the 2008–09 GAAP-earnings collapse) transiently craters trailing
  E and spikes CAPE — the Siegel critique. Then it was an earnings-definition artifact. (Trips V4.)
- **R7 — composition-drift confound.** The entire "expensive vs history" reading is explained by index drift
  toward asset-light, high-ROIC businesses that legitimately command higher multiples, making the level comparison
  apples-to-oranges across composition regimes. (Trips V4; hardest to fully clear — partial defense is
  sector-neutral valuation, otherwise the signal leans on the *relationship*, not the absolute level.)
- **R8 — OOS failure.** Fails to replicate on Japan / Europe, or replicates with the wrong sign or no horizon
  structure. (Trips V5.)
- **R9 — statistical null.** Once the persistent-regressor / overlapping-data bias is corrected, predictability is
  statistically indistinguishable from the spurious-R² null. Note the bias direction: the Stambaugh (1999) bias is
  *upward* on the slope for the dp→return case (persistent regressor, innovations negatively correlated with
  return innovations), so raw in-sample R² is **anti-conservative** — biased toward finding a signal — and cannot
  count as strength on its own (Boudoukh–Richardson–Whitelaw 2008 "Myth of Long-Horizon Predictability";
  Valkanov 2003). (Trips V6.)

Maps to spec attribute 6 (echoed as user-facing caveats in attribute 8).

### 6. What does it explicitly NOT claim?

The per-signal boundary. Valuation names the monitored assumption — *"equities are priced for near-normal
long-horizon returns"* — reports its reading (level · percentile · trend · long-horizon-return context), and
**STOPS**. It implies no action.

Explicit prohibitions (this list is a boundary statement; the forbidden vocabulary below appears only to prohibit
it): valuation is **NOT** a market-timing trigger; **NOT** an instruction to "avoid equities" or reduce exposure;
**NOT** a return forecast (it states where returns *start from* relative to history, never what they *will be*);
and never a buy / sell / risk-on / risk-off statement or any single-number market-safety score. It is strong at
long horizons and deliberately **silent at short ones** — uselessness as a short-horizon trigger is a *feature*
(it monitors a long-horizon assumption), not a defect. Investment decisions live in a separate system and with the
human; this signal only reduces a blind spot in that human's judgment.

Maps to spec attribute 8.

---

## Pre-registered analysis specification (frozen before the look)

Operationalizes V1–V6 / R1–R9. Any deviation is logged with a dated note.

- **Primary metric:** **CAPE (Shiller PE10)** — 10-year trailing real-earnings smoothing — as the primary object
  (canonical Campbell–Shiller measure, longest point-in-time-reconstructable history, best-studied).
- **Robustness panel (pre-committed, not metric-shopping):** **total-market-cap/GDP**, **price/dividend**, and
  **total-payout yield** (dividends + net buybacks, where buyback history supports it). Declared *before* the look
  precisely so admission cannot rest on "whichever metric worked" — V4 requires the sign + horizon structure to
  survive on this panel, not just on CAPE.
- **Return object:** forward **real** returns; **primary discriminator = excess over the short real risk-free
  rate**; excess-over-10yr-bonds reported as a secondary lens.
- **Horizons:** a sweep from sub-1yr through 10yr (e.g. 1, 3, 5, 7, 10yr) — the horizon *profile*, not a single
  horizon, is the V1 test.
- **Rate-regime separation battery (Adam's spine):** (i) excess returns [V2] + (ii) sub-period stability including
  and excluding 1982–2021 [V3] + (iii) international OOS where the rate path differs [V5], with a real-rate-level
  bivariate control as a supporting diagnostic. Passing requires the relationship to survive the battery, not any
  single test.
- **Inference standard [V6/R9]:** raw OLS long-horizon R² is descriptive only. Evidence requires
  Stambaugh-bias-aware estimation, overlapping-observation-robust inference (Hodrick 1992 / correctly-applied
  Newey–West), and an explicit effective-independent-N accounting (~150yr / 10yr ≈ 15 non-overlapping decades).
- **Point-in-time discipline:** valuation inputs are revised (as-reported earnings, CPI for real earnings).
  Reconstruct the vintage available at each date; no look-ahead. A live signal that reads final-revision earnings
  has a look-ahead trap.
- **Out-of-hypothesis-sample:** Japan + Europe, same construction, before any SUPPORT claim.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/03-valuation-signal/03-CHARTER-KICKOFF|03-CHARTER-KICKOFF]]

<!-- LINKS:END -->
