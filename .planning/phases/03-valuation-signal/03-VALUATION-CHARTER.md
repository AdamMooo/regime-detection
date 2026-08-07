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
- **Charter/spec version** — v1.1 (data-availability respecification of V4 + V5, 2026-08-07 — see the amendment
  block at the end of the analysis spec). v1.0 was written 2026-08-03 and **never signed**, so this completes an
  unsigned pre-registration rather than amending a frozen one.
- **Charter dated** — 2026-08-03, respecified 2026-08-07. **SIGNED OFF by Adam 2026-08-07** at v1.1, both
  respecifications confirmed (V5 → international D/P; V4 → CAPE + P/D + cap/GDP with the payout leg dropped and
  R5 recorded untestable). Build/run authorised. This signs the *pre-registration* only — a Stage-1 freeze, not a
  positive claim, so no cooling-off applies here. Any SUPPORT claim arising from the run still requires one look +
  overnight cooling-off + a separate dated sign-off of the *results*.

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

## AMENDMENT 2026-08-07 — data-availability respecification (BEFORE any look)

Two registered bars were not runnable as written. Both were checked against the actual sources, not assumed. The
substitutions are registered here **before** the one-look; Adam confirmed both routes 2026-08-07.

### V4 — the robustness panel loses its payout leg

**Registered:** CAPE + cap/GDP + P/D + **total-payout yield** (dividends + net buybacks).
**Amended:** CAPE (primary) + **P/D** (Shiller's dividend series, already in `valuation_monthly.csv`) +
**total market cap / GDP** (FRED, quarterly from 1947). **Total-payout yield is DROPPED — no free history of net
buybacks exists** (S&P publishes S&P-500 buybacks from 1998; longer history is Compustat, paywalled).

**Consequence, registered as a named hole rather than a silent one: R5 (payout confound) becomes UNTESTABLE with
this data.** Buybacks displaced dividends after 1982, so a dividend-based reading can look artificially expensive
in exactly the modern era. The signal therefore cannot clear the payout-policy confound, and that is a standing
limitation on its evidence maturity — not something a strong CAPE result buys off. P/D is retained *because* it is
the metric most exposed to this confound: keeping it makes the hole visible in the panel instead of hiding it.

### V5 — the international sample is respecified

**Registered:** Japan + Europe, same construction (CAPE).
**Fact:** no free CAPE exists for Japan or Europe. Barclays/Research Affiliates CAPE and MSCI are paywalled;
French's regional datasets (Japan / Europe, 1990-07+) publish no valuation ratio at market level.

**Amended source (verified numerically 2026-08-07):** French publishes the **F-F International Indices** as a
matched pair — **`F-F_International_Indices.zip`** (value-weight returns **with** dividends) and
**`F-F_International_Indices_Wout_Div.zip`** (the identical indices **without** dividends) — monthly, **1975-01 to
2025-12**, for **Europe ex UK · Europe incl. UK · UK · Scandinavia · Asia Pacific · All**, in both USD and local
currency.

**The construction:** for the same index and month,

&nbsp;&nbsp;&nbsp;&nbsp;`R_with − R_without = (P_t + D_t)/P_{t−1} − P_t/P_{t−1} = D_t / P_{t−1}`

so the difference of the two published return series **is** the period's dividend yield on lagged price, exactly.
Cumulated over 12 months it is the trailing dividend yield — the canonical Campbell–Shiller **D/P** object. The
numerator, the denominator and the forward-return leg all come from the same file on the same universe, so they
cannot drift apart across sources.

**Integrity check run 2026-08-07 (data construction, NOT the hypothesis test — no valuation-to-return relationship
was examined):** 612 monthly observations per region, **zero negative implied monthly D/P**, and the level series
lands on the right history — Europe ex UK ranges 1.60% (1999, the TMT peak) to 5.95% (1980), Asia Pacific ranges
**0.69% (1989 — the Japanese bubble peak)** to 3.17%. The two canonical valuation extremes outside the US sample
are both present and correctly signed.

**This is stronger than the annual `Value-Weight Ratios` block also present in the same file** (which publishes a
market-level `Mkt` ratio plus High/Low portfolio ratios, annual only). That block is retained as a **secondary
cross-check on market BE/ME**, not as the primary international object.

**Downgrades that remain, disclosed in advance — the international leg is still weaker than the US leg:**
1. **D/P, not CAPE.** No 10-year earnings smoothing exists for these indices. Dividend yield is smoother and more
   internationally comparable than a one-year E/P, and is a canonical object in its own right, but it is exposed
   to the same payout-policy confound that R5 can no longer test (above).
2. **No Japan alone.** Asia Pacific is the closest available aggregate — Japan-dominated by weight through the
   bubble era, but not Japan. The canonical Japan test is *approximated*, not run.
3. **Starts 1975**, so the international leg cannot see any pre-1975 valuation extreme.
4. **Overlapping long-horizon returns on 612 months ⇒ ~5 non-overlapping decades per region** at the 10-year
   horizon. Monthly frequency buys precision on the *level*, not independent observations of the *relationship*.

**V5a — power pre-check, registered to run FIRST and to gate every international contrast** (the device that
turned a feared-underpowered Phase 2 into a clean verdict). Report the effective independent-N per region and
horizon. **A cell below the registered floor is reported as "insufficient coverage" — NOT as a weak finding and
NOT as refutation.** Registered floor: **≥ 10 effective independent observations**.

**V5 bar, as amended:** a **sign-and-direction** check, not a powered R² claim — higher starting D/P must be
associated with higher subsequent returns in the adequately-powered regions, with the horizon profile rising where
estimable. **R8 is correspondingly narrowed:** it trips only on a *sign reversal* in an adequately-powered region,
never on a failure to reach significance in a cell the power pre-check already flagged.

### A third disclosure — the US excess-return leg is shorter than the price history

V2's excess-return object needs a short risk-free rate. Shiller's file carries none; the panel uses **Ken French's
one-month T-bill, which begins 1926-07**. So **V1/V3/V4 run on 1881–2026 while V2 — the primary discriminator —
runs on 1926–2026.** A century is ample, but the two are not the same sample and results must not be reported as
though they were.

### Standing consequence for maturity (written before the look)

R5 untestable + an international leg that is annual, regional-not-Japan, and on a different metric ⇒ **evidence
maturity cannot reach `H` in this phase, so `production` is unavailable and `research` is the ceiling.** Registered
now, before the look, for the same reason Phase 2 registered its ceiling: a strong result is exactly when the cap
is most tempting to drop.

---

## ONE-LOOK RESULTS — 2026-08-07, `results/valuation_validation.txt` — SIGN-OFF PENDING

One look spent (`scripts/validate_valuation.py`, seed 20260807). **Five of six bars clear. The one that does not
is V6 — the pre-registered statistical bar — and R9 is therefore live.** Read below; the disposition is Adam's,
after overnight cooling-off. Nothing here is a claim yet.

### What cleared

| bar | verdict | evidence |
|---|---|---|
| **V1** horizon structure | **PASS on shape** | β −0.0033 (1m) → −0.079 (1y) → −0.331 (5y) → **−0.610 (10y)**; R² 0.001 → 0.034 → 0.140 → **0.257**. Monotone in both, and ~silent sub-1yr (R²=0.001 at 1m, t_NW −1.12). This is the registered signature of a slowly mean-reverting discount rate, not a generic "cheap is good" |
| **V2** excess returns | **PASS on shape** | Same profile on returns in excess of the short rate, slightly stronger: β −0.098 (1y) → −0.347 (5y) → −0.652 (10y), R² 0.045 → 0.131 → 0.251. **The relationship is not merely the falling-rate level**, which is what R4 was written to catch |
| **V3** sub-period stability | **PASS** | β@60m: full −0.331, **pre-1982 −0.522**, 1982–2021 −0.476. Stronger *outside* the secular rate-decline window. `EXCL 1982–2021` is numerically identical to `pre-1982` because post-2021 starting points have no realized 5y/10y returns yet — a structural fact of the test, not a coding accident |
| **V4** metric robustness | **PASS on sign + shape** | All three pre-committed metrics show the same monotone profile with the predicted sign: log CAPE −0.0033→−0.610, log D/P **+0.0035→+0.377**, log cap/GDP −0.0043→−0.653. **cap/GDP contains no earnings at all**, so R6 (the accounting/Siegel confound) does not trip |
| **V5** international | **PASS, heavily qualified** | The power pre-check gated this correctly: at 10y every region has eff N 3–4 ⇒ **INSUFFICIENT COVERAGE**, and the spectacular-looking R² 0.36–0.79 there must be ignored. At the only interpretable horizon (12m, eff N 49) the **primary local-currency specification has the correct positive sign in all six regions** (+0.039 to +0.206). In the secondary USD-real specification **Scandinavia reverses** (−0.033), disclosed |

### What did NOT clear — V6, and it is the load-bearing one

**Bootstrap under the null (2000 block-bootstrap paths, no predictability imposed, (u,v) pairs resampled so the
Stambaugh correlation survives): p = 0.089 / 0.087 / 0.071 / 0.106 / 0.097 / 0.145 / 0.103 across the seven
horizons on real returns, and 0.105 / 0.127 / 0.079 / 0.125 / 0.196 / 0.256 / 0.174 on excess returns.
Not one horizon reaches conventional significance.**

The 10-year cell is the clearest illustration of why the charter registered this bar. Raw OLS gives R² = 0.257 and
t = −23.7; Newey–West still gives t = −4.93. Both look overwhelming. But a regressor with **ρ = 0.9965** and
**corr(return innovation, regressor innovation) = +0.96** reproduces an R² that large, in the predicted direction,
in about **10% of paths with zero true predictability**. That corr(u,v) is near-tautological here — CAPE's
numerator *is* the price, so the same price move drives both the return and the regressor. This is the
maximum-Stambaugh case, not an unlucky one.

**Stambaugh closed-form correction at h=1 removes 64% of the raw slope on real returns (−0.00334 → −0.00120) and
72% on excess returns (−0.00449 → −0.00125).**

**R9 as written — "once the persistent-regressor / overlapping-data bias is corrected, predictability is
statistically indistinguishable from the spurious-R² null" — is satisfied at conventional thresholds.**

### The honest interpretation, stated without spin

Two readings are defensible and the choice between them is a judgment call, which is why it is not being made here:

1. **R9 trips.** The bar was pre-registered at conventional significance, and nothing cleared it. The
   forward-return-predictability claim fails, and the signal is demoted to a pure *measurement* — "CAPE is 41.5,
   the 99.0th percentile of its own history" — with no forward-return claim attached. That is still a real signal
   under this repo's own objective (measurement, not prediction), and it is exactly the shape volatility took.
2. **R9 does not trip, but the evidence is weak-and-consistent.** Every horizon, both return objects, three
   independent metrics, four sub-periods and six international regions point the same way, and the p-values sit
   in the 0.07–0.15 band rather than at 0.5. A single p-value per cell does not capture agreement *across* 20+
   independent specifications. The counter-argument to this reading is that the specifications are not
   independent — they share the same price series — so the agreement is far less informative than it looks.

**What is NOT in dispute:** with ~13 effective independent 10-year observations in 145 years of US data, this
evidence cannot statistically separate the Campbell–Shiller mechanism from a persistent-regressor artifact. That
is not a defect in the analysis; it is the actual information content of the data, and it is precisely what R9
was written to detect. **Reading the raw t = −23.7 as the answer would have been the error the charter existed to
prevent.**

### Registered but deliberately NOT run (each would be a second look)

- No bootstrap was run on the V4 metric panel or the V5 international leg — V4 was specified as a sign-and-shape
  robustness check and V5 as sign-and-direction. Adding significance testing there now is a second look and needs
  its own pre-registration.
- No horizon beyond 120 months, no alternative block length, no alternative seed. Re-running the bootstrap with a
  different seed to see if p crosses 0.05 would be the single worst thing that could be done to this result.

### Maturity, if admitted

Ceiling remains `research` per the pre-look registration. If reading (1) is taken, the derived tag would rest on
measurement validity alone with investment usefulness re-assessed, since the forward-return claim is what made the
signal interesting. **That re-assessment is part of the sign-off decision, not a prerequisite to it.**

---
---
---
---
---
---
---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/03-valuation-signal/03-CHARTER-KICKOFF|03-CHARTER-KICKOFF]]

<!-- LINKS:END -->
