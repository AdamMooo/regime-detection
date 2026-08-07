# Research Charter — Funding-Stress Signal (Phase 7)

**DRAFT — NOT FROZEN, NOT SIGNED.** Written 2026-08-06. This is a pre-registration *draft* for Adam's review.
It is not a Stage-1 freeze, it carries no sign-off, and no positive claim rests on it.

**No look has been spent.** Nothing in this document reports a computed statistic about whether the funding
signal works. Data inspection was restricted to coverage — row counts, first/last dates, missingness, gap-run
lengths, column names — plus published documentation of how the candidate series are constructed. No funding
series has been correlated with, regressed on, or compared to any other signal. Every question of the form
"is it redundant?" is registered below as a test to be run, not answered here.

**Charter filled against framework template v1.1** (`research-charter-template.md`), held to
`validation-standards.md` v1.1.

---

## Verdict up front

**Stage-0 Relevance Gate: FAILS as a standalone signal.** G1, G2 and G5 pass convincingly. **G3 and G4 — the
unique-information and leave-one-out questions — fail**, and G4 is the sharp bar the framework calls decisive
(§Stage 0, D-19). The kickoff's own words are the finding: *"its everyday value is ~zero."*

**Recommendation: FOLD INTO PHASE 9 (Tail), with DROP as the fallback.** The mechanism is real, distinct and
well-supported; what fails is the case for a *separate research module* with its own charter, validation
programme, international replication, maturity tag and maintenance burden. Reasoning in full at
[§ Recommendation](#recommendation).

The six charter questions are answered anyway, below. They are answered *because* the recommendation is to fold:
Phase 9 needs a specified object to inherit, and a gate failure should be as auditable as a gate pass. Under the
framework a failed gate means no charter is opened and no research time is spent — this document is therefore the
*record of the gate decision*, not an authorisation to build.

---

## Header (drafted, for the record)

- **Signal name** — Funding stress (secured/unsecured funding-market functioning)
- **Assumption monitored** — **"funding markets function."** Ledger key
  {`intact` | `under_test` | `violated`}. **[recommended — Adam to confirm/override]** if the fold is accepted,
  this ledger key is **retained but owned by Phase 9**: the assumption stays visible in the ledger, the flag
  becomes its evidence, and no separate signal record is emitted.
- **Native clock / frequency** — daily, fast, **tail-only**. Distinct from every other signal in the set in that
  its intended duty cycle is near-zero: it is designed to read `intact` in ~97% of history.
- **Scope** — NARROW. A binary or three-level flag, not a continuous descriptor. Registered narrow deliberately.
- **Maturity tag** — DERIVED, unset. Given the data breaks registered in
  [§ Series construction](#series-construction) and [§ Data readiness](#data-readiness), **`research` is the
  ceiling any version of this signal can earn on free data. `production` is structurally unavailable**, because
  the out-of-hypothesis-sample requirement (§(d)) cannot be met: the Japan and Europe funding series carry the
  *same* benchmark-transition break as the US ones, so an international replication would test the splice, not
  the signal.
- **Investor question (production bar)** — *"Are funding markets currently functioning, or is there acute
  secured/unsecured funding stress right now?"* Clearly answerable in principle; the production bar fails on
  evidence, not on the question.
- **Charter/spec version** — v0.1-draft
- **Charter dated** — unfrozen

---

## Stage-0 Relevance Gate

Default = NO. Five questions, answered against `validation-standards.md` §Stage 0.

### G1 — What important investment question does this signal answer?

*"Are funding markets functioning right now, or is there acute secured/unsecured funding stress?"*

**PASS.** This is a real, first-order question about market plumbing, and it is not answered by any other
admitted signal directly.

### G2 — Why is that question important to long-term investors?

**PASS.** Funding seizure is the amplification mechanism of the worst realised tail events. In 2008 the
unsecured money market froze after the Reserve Primary Fund broke the buck (September 2008) and issuers could
not roll commercial paper; in March 2020 even Treasury and agency markets showed dealer-intermediation strain.
The distinguishing feature versus ordinary drawdowns is that funding stress converts a price decline into a
self-reinforcing spiral: falling prices raise haircuts, higher haircuts force deleveraging, deleveraging pushes
prices further down (Brunnermeier–Pedersen 2009). A long-horizon investor cares because it identifies the
episodes in which "wait it out" is being tested by forced sellers rather than by opinion.

### G3 — Does this provide information NOT already available from the existing signals?

**FAIL — outside tail episodes.** The kickoff states this plainly and it is the honest answer: in normal times
funding-stress measures are close to redundant with the volatility signal and with credit spreads. Three
independent reasons to expect that, none of which requires computing anything here:

1. **The orthogonality research already found it.** The `sensor-orthogonality-evidence` record concluded that
   raw stress series collapse ~85–94% onto a single common stress factor and *re-converge in crises*. Funding
   spreads were among those series. The residual verdict recorded there was "funding-flag tail-only."
2. **The composites say it themselves.** The OFR Financial Stress Index estimates a **single latent factor**
   across all 33 indicators and reports each category as that category's *contribution to the common factor*
   (Monin 2019). The funding category is, by construction, the part of funding that co-moves with credit,
   equity valuation, safe assets and volatility. So the standard published funding measure is *defined* as the
   shared component.
3. **The measure is contaminated with credit.** The classic funding spreads (TED, LIBOR–OIS, CP–bill) are
   unsecured bank/issuer rates minus a risk-free rate, so they price counterparty *credit* risk as well as
   funding *liquidity*. Taylor–Williams (2009) argued explicitly that the 2007–08 LIBOR–OIS widening was
   predominantly counterparty risk, not liquidity. That is Phase 6's territory.

The honest scope of unique information is therefore: **funding stress carries distinct information only in the
episodes where it decouples — 2008, September 2019, March 2020 — and possibly not even then, since the
decoupling has never been measured here against the volatility and credit signals as this repo constructs them.**

### G4 — Would REMOVING this signal make the observatory meaningfully less informative? (the sharp bar)

**FAIL.** Apply the framework's own litmus: *"if this signal disappeared tomorrow and the observatory were
essentially unchanged, it never belonged."* On ~97% of days the observatory is unchanged by construction — the
flag is designed to be off. On the remaining ~3%, the volatility signal is at an extreme percentile, the credit
signal is wide, and the tail signal is showing an inverted VIX term structure. The flag would be firing into a
room where every other instrument is already at its limit.

The counter-argument deserves a fair hearing: *the marginal information is not "is something wrong" but "which
mechanism is transmitting it"* — a drawdown with functioning funding markets is a genuinely different object
from one with a funding seizure, and that distinction is exactly the kind of resolution this observatory exists
to preserve. **That argument is correct, and it is why the recommendation is FOLD rather than DROP.** It is an
argument for the *mechanism* being represented somewhere in the ledger. It is not an argument for a separate
signal with its own charter, one-look, international replication and maturity tag — and Stage 0 is a test of the
latter.

### G5 — Strong theoretical/empirical prior BEFORE spending weeks?

**PASS.** The theory is strong and specific (Brunnermeier–Pedersen 2009; Adrian–Shin 2010; He–Krishnamurthy
2013; Gorton–Metrick 2012). The *empirical* prior is weaker than it looks, because the well-documented episodes
number two or three and each is observable only in a series that either no longer exists or did not yet exist
(see [§ Series construction](#series-construction)). "Strong prior" here means strong *mechanism*, thin
*measurable history*.

### Gate verdict

**G1 pass · G2 pass · G3 FAIL (outside tail episodes) · G4 FAIL · G5 pass (mechanism), thin (evidence).**

**FAILS the Stage-0 gate as a standalone signal.** The kickoff's CONDITIONAL PASS was recorded before the data
and series-construction facts below were checked; those facts make the conditional unrecoverable on free data.
Verdict: **do not open a standalone Phase 7 research programme. Relocate the mechanism to Phase 9.**

---

## The six charter questions

Answered so that Phase 9 inherits a specified object rather than a vague intention.

### 1. What question does the signal answer?

Whether short-term funding markets are currently clearing at or near their normal spread to the risk-free rate,
or whether an acute dislocation is present — and, if present, how it compares to the small set of historical
dislocations.

Deliberately **not** answered: whether funding stress is *building*, whether it will spread, or what it implies
for future returns. The signal is coincident to the point of being nearly contemporaneous with the event it
marks; treating it as an early warning is the primary way it would be misused. It has no lead. Phase 6's excess
bond premium is the leading credit-supply read; this is the *confirmation that the plumbing itself has broken*,
which is a different and later fact.

### 2. What market assumption does it monitor?

**"Funding markets function"** — that intermediaries can finance their balance sheets at close to the risk-free
rate against normal collateral, so that market prices reflect opinion rather than forced liquidation.

Draft ledger mapping (thresholds NOT pre-committed — see R6 and the open questions):

| reading | status | world |
|---|---|---|
| spread inside its normal band | `intact` | funding is available at customary terms |
| spread elevated but orderly | `under_test` | terms tightening; no seizure |
| spread at a historically extreme level | `violated` | acute dislocation; forced-deleveraging channel live |

**The thresholds are the whole signal, and there is not enough history to set them honestly.** That is registered
as reject condition R6, not smoothed over.

### 3. What mechanism supports it — why does it survive being known?

**Registered mechanism: risk-management channel via the funding-liquidity / market-liquidity spiral.** Not a
risk-premium channel and not a forecast.

**Funding liquidity vs market liquidity — the distinction the signal rests on.** Market liquidity is the ease of
trading an asset without moving its price. Funding liquidity is the ease with which the *traders* can finance
their inventories. Brunnermeier–Pedersen (2009) formalise the loop between them: when speculators' capital is
constrained, market liquidity falls; falling market liquidity raises volatility, which raises margins and
haircuts, which tightens funding further. The loop has two stable neighbourhoods — a normal one where the two
liquidities are near-independent, and a crisis one where they are mutually reinforcing. **That two-regime
structure is precisely why a narrow, mostly-off flag is the correct functional form**, and equally why it
carries almost no information in the normal neighbourhood.

Supporting lineage, all standard-literature terms:

- **Liquidity spiral / margin spiral** — Brunnermeier & Pedersen (2009), *RFS* 22(6), 2201–2238.
- **Procyclical leverage** — Adrian & Shin (2010), "Liquidity and Leverage," *JFI* 19(3), 418–437: dealer
  balance sheets expand and contract with measured risk, so a haircut shock is a balance-sheet shock.
- **Run on repo** — Gorton & Metrick (2012), *JFE* 104(3), 425–451: the 2007–08 crisis as a run on secured
  wholesale funding, visible in haircuts rather than in deposit withdrawals.
- **Intermediary asset pricing** — He & Krishnamurthy (2013), *AER* 103(2), 732–770: intermediary net worth as
  a state variable that prices risk; the funding measure is a noisy real-time observable of that state.
- **Financial accelerator** — Bernanke, Gertler & Gilchrist (1999): the general amplification frame.
- **Limits to arbitrage in funding markets** — Du, Tepper & Verdelhan (2018), *JF* 73(3), 915–957: persistent
  covered-interest-parity deviations as balance-sheet cost, i.e. funding constraints leave a price footprint
  even in the absence of default risk. *(Named because it is the cleanest conceptual measure and because it is
  infeasible on free data — see below.)*
- **Near-money premium** — Nagel (2016), *QJE* 131(4), 1927–1971: the T-bill/short-rate spread as the price of
  immediacy, the reason a bill leg is the natural risk-free comparator.
- **Reserve scarcity** — Copeland, Duffie & Yang, "Reserves Were Not So Ample After All" (NBER WP 29090, 2021);
  Anbil, Anderson & Senyuz, "What Happened in Money Markets in September 2019?" *FEDS Notes*, 27 Feb 2020. The
  September 2019 repo episode is the cleanest modern example of a pure funding dislocation with no credit event
  and no equity drawdown attached — which is what makes it the single most valuable observation for this signal,
  and it exists only in the SOFR-era data.

**Why it survives being known.** Two answers, and the second is a caveat that must not be lost:

1. *It is a measurement of a constraint, not a mispricing.* The spread is the price at which balance sheet is
   actually being rented under a binding regulatory and collateral constraint. Publishing the observation does
   not relax the constraint. Nobody can arbitrage away the fact that a dealer cannot finance inventory in
   September 2019 — that is why the observable persisted for years after Du–Tepper–Verdelhan documented it.
2. **The caveat — the observable is partly a measure of the backstop, not of the fragility.** Since the
   Standing Repo Facility was made permanent (July 2021), and given the FIMA repo facility and the 2020-vintage
   emergency facilities, a large class of funding dislocations is now capped by policy at a known rate. The
   spread can therefore stay narrow while underlying fragility is high, and a flag calibrated on pre-backstop
   history will systematically read `intact` in a post-backstop seizure. **This is a genuine partial failure of
   the mechanism gate as applied to the measurement**: the mechanism survives being known, but the *observable*
   has been deliberately suppressed by an actor who knows it. Registered as reject condition R4.

**Verdict on the mechanism gate (§(b)): PASS, with R4 attached.** The mechanism is written, structural, and
risk-management-channel. The gate is passed. The gate is not what fails here — Stage 0 is.

### 4. What evidence would validate it?

These are the bars a funding signal must clear **wherever it lives** — standalone or as a flag inside Phase 9.
Registering them here means the fold does not smuggle an unvalidated object into Phase 9.

**V1 — Causal and look-ahead-free.** The flag uses only data through *t*, including the publication lag of its
inputs (§(a)). Must pass `assert_causal(build, data)` under `scripts/causal.py`, and the build must be
registered under the guard so `tests/test_reproducibility.py` cannot pass by omission. Any expanding-window
standardisation must be genuinely expanding (`causal.expanding_percentile`), never full-sample.

**V2 — Point-in-time honesty.** Every input is either (a) an unrevised market price/transaction statistic, or
(b) reconstructed from vintages, or (c) explicitly declared not point-in-time with the consequence stated. A
revised composite used as if it were real-time is a disqualifying look-ahead, not a caveat.

**V3 — Series homogeneity across the benchmark transition.** The series used must be *one measurement* across
its declared span, or the span must be cut at the break and the pre- and post-break periods treated as separate
samples. A silent LIBOR→SOFR splice fails this outright. See [§ Series construction](#series-construction).

**V4 — Missingness is not endogenous.** Where an input is absent on some trading days, the absence must be shown
to be exogenous (holiday, publication calendar) rather than a function of the state being measured. An input
that is unpublished *because the market was too thin to price* is missing precisely when the signal should fire.
Test: report the missingness rate inside each declared stress window against the unconditional rate, and state
the imputation rule before the look. **Coverage figures already gathered are in
[§ Data readiness](#data-readiness) — this bar is already in trouble.**

**V5 — Episode identification.** The flag must fire on the pre-declared list of acknowledged funding
dislocations and must not fire on a pre-declared list of equity drawdowns with no funding component. Both lists
are declared **before** the look. Draft lists **[recommended — Adam to confirm/override]**:
- *Must fire:* Aug 2007 (ABCP/quant), Sep–Dec 2008 (post-Lehman/CP freeze), Sep 2019 (repo), Mar 2020 (dash for
  liquidity), Mar 2023 (regional-bank/discount-window episode — included as a partial, since it was largely
  contained).
- *Must not fire:* Aug 2011 (US downgrade), Aug 2015 (China devaluation), Feb 2018 (volatility complex),
  Q4 2018, Aug 2024 (yen-carry unwind).

**V6 — POWER PRE-CHECK, runs BEFORE any V5 or V7 result is interpreted.** Modelled on Phase 2's V4 and
registered for the same reason. Count the number of *independent* declared funding episodes contained in the
sample span of the series actually used. **If that count is fewer than four, the series is declared UNDERPOWERED
and its V5/V7 outcome is reported as "insufficient coverage" — never as support and never as refutation.**
Registered in advance precisely because the honest count is likely to be **two** (see
[§ Series construction](#series-construction)), and because an underpowered episode-matching exercise on n=2 is
the single most likely way this phase would produce a false positive.

**V7 — MARGINAL INFORMATION, leave-one-out (the decisive bar).** This is the test that Stage-0's G4 could only
argue about. Registered, not run:

> Condition on the volatility signal's descriptors (`vol_descriptors` level percentile + rarity) and on the
> credit signal's excess bond premium, both as this repo constructs them. **Does the funding flag identify any
> day, outside the declared tail episodes, on which it reads `violated`/`under_test` while volatility percentile
> is below its 90th and credit is inside its normal band?** Report the count of such days and the dates.
>
> Bar: **at least 20 such days, falling in at least two distinct episodes separated by more than a year.**
> Fewer than that and the flag adds no information the observatory does not already carry.

Two properties of this test are deliberate. It is a **counting test, not a correlation test** — a correlation
between funding stress and volatility is expected and is not the question; the question is whether funding ever
*decouples*. And its bar is stated as a number before the look, so "it decoupled a bit" cannot be argued after.

**V8 — Out-of-hypothesis-sample (Japan / Europe), §(d).** Identical construction on the Japanese and euro-area
funding spreads. **Registered as EXPECTED TO BE INFEASIBLE**, and the reason is structural rather than a matter
of effort: the euro-area equivalent (3M EURIBOR−EONIA) and the Japanese equivalent (3M JPY LIBOR−OIS) both hit
the *same* benchmark cessation — EONIA ceased January 2022 and was replaced by €STR; JPY LIBOR ceased December
2021 and was replaced by TONA/TORF. An international replication would therefore test the same splice twice.
**Consequence, registered before any run: without V8, `production` is unreachable and the maturity ceiling is
`research`.** This is not a to-do; it is a permanent property of the free data.

### 5. What would falsify it?

Each reject condition is paired to the bar that trips it.

- **R1 — look-ahead or vintage leak.** Any input found to be a revised series used as if it were real-time, or
  any full-sample standardisation. **Kill.** (Trips V1/V2.)
- **R2 — the series is a splice, not a measurement.** The chosen construction silently joins LIBOR-era and
  SOFR-era rates, so a level threshold means different things before and after the join. **Kill or cut the span
  at the break** and disclose. (Trips V3.)
- **R3 — endogenous missingness.** The input is systematically unpublished during the episodes the flag exists
  to mark. **Kill** — a flag that goes dark in the crisis is worse than no flag, because its silence reads as
  `intact`. (Trips V4.)
- **R4 — the observable is the backstop, not the fragility.** The measure is materially capped by a standing
  policy facility, so post-2021 readings are not comparable to pre-2021 readings and the flag would
  under-report a modern seizure. **Demote to a documented historical-context statistic**, not a live reading.
  (Trips V3/V5; flows from the mechanism caveat in Q3.)
- **R5 — false-positive/false-negative on the declared episodes.** The flag misses a "must fire" episode or
  fires in a "must not fire" window. **Kill or re-specify with the defect disclosed.** (Trips V5.)
- **R6 — thresholds cannot be set honestly.** The `under_test`/`violated` cut points cannot be pre-committed
  because the series has too few episodes to calibrate against, so any choice is a knob fitted to the two
  events everyone already knows about. This is the vol-signal lesson (`volatility-signal-reframe`): an
  arbitrary threshold on a continuous magnitude destroys graded information and manufactures confidence.
  **Kill the flag form**; report the continuous spread with its causal expanding percentile and no state, or
  fold. (Trips V6.)
- **R7 — REDUNDANCY (the registered fold/drop condition).** **If V7 finds fewer than 20 decoupled days in
  fewer than two distinct episodes — i.e. the flag fires only when volatility and credit are already at
  extremes — the signal is redundant confirmation. It does NOT stand alone. It is folded into Phase 9 as a
  conditioning annotation, or dropped.** Not a kill of the *mechanism*; a kill of the *separate signal*.
- **R8 — underpowered.** All candidate series fail V6's power pre-check. The phase closes as **INCONCLUSIVE —
  insufficient episode coverage**, not as support and not as refutation. Registered as a distinct outcome for
  the same reason Phase 2 registered R5.

### 6. What does it explicitly NOT claim?

The signal reports whether funding markets are currently clearing at customary terms, how that compares with the
handful of historical dislocations, and nothing else. It names the assumption "funding markets function" and
**STOPS**.

Explicit prohibitions — the forbidden vocabulary appears in this paragraph *only* in order to prohibit it. This
signal is **NOT** a crisis forecast and has no lead time; it is coincident and may lag the event it marks. It is
**NOT** a crash predictor, **NOT** a return forecast, and **NOT** a statement that a dislocation will spread. It
never implies or encodes any response to a `violated` reading: no buy, no sell, no risk-on / risk-off summary,
no allocation, no portfolio construction, no overweight or underweight, no position sizing, no risk budget, no
exposure change, no cash call, no instrument selection, and no composite safety score. What a funding seizure
means, and what if anything to do about it, is the human's judgment in a separate system. This repo supplies the
observation and its history, and stops there.

---

## Series construction

The three hazards named in the phase brief, worked through. This section is the substantive reason the
recommendation is FOLD.

### Hazard 1 — the LIBOR→SOFR splice

**The break is real, dated, and unavoidable.** USD LIBOR settings ceased (1W/2M in December 2021; the remaining
tenors in June 2023). FRED's `TEDRATE` (3M LIBOR − 3M T-bill) was discontinued after 2022-01-21, with FRED
stating that 3-Month LIBOR was removed from FRED as of 2022-01-31 and the calculated series will no longer be
updated. There is no free continuous LIBOR–OIS history spanning the transition.

Why this is not a cosmetic problem. LIBOR was a survey of **unsecured** interbank offer rates and embedded bank
credit risk; SOFR is a transaction-based **secured** overnight repo rate against Treasury collateral, with
essentially no credit component. A spread built on LIBOR and a spread built on SOFR do not measure the same
quantity: one widens on counterparty fear, the other on collateral and balance-sheet scarcity. Splicing them and
calling the join one series produces a level threshold that means different things on either side of 2022 — the
exact failure R2 names. Note that the two most instructive episodes fall on opposite sides: **2008 is observable
only in the LIBOR-era measure; September 2019 is observable only in the SOFR-era measure.**

**Registered handling — three options, one recommended.**

- **(a) Splice with a scale adjustment.** Rejected. Any adjustment is estimated on the overlap window
  (2018-04 → 2022-01), which contains March 2020 — so the adjustment would be fitted on the single stress
  episode the signal most needs to identify. That is result-driven specification (§(i)) and disqualifying.
- **(b) Register as a hard break and treat the eras as separate samples.** Acceptable. Each era gets its own
  causal expanding standardisation; no threshold and no percentile is ever computed across the join; the
  historical-context statement explicitly reports which era a comparison is drawn from. Cost: the *live* signal
  is the SOFR era only, which is 2018→present.
- **(c) Use only the post-transition era.** **[recommended — Adam to confirm/override]** if any funding signal
  is built at all. Honest, homogeneous, and PIT-clean — at the price of an eight-year sample containing two
  episodes, which is precisely what trips the V6 power pre-check and R8. Recommending (c) *and* registering
  that it fails V6 is not a contradiction: it is the finding.

**Note that the composites do not escape this — they perform the splice silently, on your behalf.** See below.

### Hazard 2 — composite contamination

The brief asks whether a clean, narrow, funding-specific measure is obtainable rather than a broad stress
composite. The three composites in play:

**OFR FSI funding sub-index** (the kickoff's preferred source). Verified against the published methodology
(Monin 2019, *Risks* 7(1), 25; OFR WP 17-04) and the current data file. Findings:

- The CSV at `financialresearch.gov/financial-stress-index/data/fsi.csv` carries columns
  `Date, OFR FSI, Credit, Equity valuation, Safe assets, Funding, Volatility, United States, Other advanced
  economies, Emerging markets`, starting **2000-01-03**. So the funding sub-index *is* separately published.
- **It is point-in-time in the strict sense, and the kickoff was right about that.** The paper states: *"Unlike
  some other FSIs, whose entire time series are re-estimated each time they are updated, the OFR FSI respects
  the arrow of time. The OFR FSI's value on a given day depends only on information available that day and,
  once estimated, its value does not change."* Standardisation is against each indicator's history *up until
  that time*. This is a genuinely well-built series and the best-behaved of the three on vintage.
- **But it is the wrong object, and for a decisive structural reason.** The index is estimated with a dynamic
  factor model with a **single latent factor** ("essentially corresponds to the first principal component").
  Each indicator's contribution is its loading on that common factor times its standardised value, and *"by
  summing contributions of indicators in each indicator category, we obtain the subtotals for the credit,
  equity valuation, funding, safe assets, and volatility indicator categories."* **The funding sub-index is
  therefore the funding indicators' projection onto the single common stress factor.** A funding indicator that
  *decouples* from the common factor receives a small loading and contributes little. The measure is
  structurally biased against exactly the decoupling that would make funding stress unique information. It is
  the sensible design for an aggregate stress index and the wrong one for this repo's question.
- **And it carries the same LIBOR splice, applied to all seven of its funding indicators at once.** As of
  31 December 2018 the funding category was: 2-Year EUR/USD cross-currency swap spread · 2-Year US swap
  spread · 2-Year USD/JPY cross-currency swap spread · 3-Month EURIBOR−EONIA · 3-Month Japanese LIBOR−OIS ·
  3-Month LIBOR−OIS · 3-Month TED spread. In June 2023 the OFR replaced seven indicators that were based on
  ceasing benchmark rates, with SOFR-, TIBOR- and TONAR-based replacements (OFR WP 23-07). **All seven funding
  indicators were benchmark-based; the funding category was entirely rebuilt.** The OFR also publishes an "FSI
  Revision History" and the index publishes with a two-business-day lag.

  Verdict: **the OFR funding sub-index does not solve the splice — it hides it.**

**NFCI (Chicago Fed).** Disqualified on vintage. The Chicago Fed states that the history of the NFCI can change
from week to week depending on incoming data, data revisions, and changes in the estimated loading given each
financial indicator, and that all data are subject to revision. The whole history is revised weekly. Using the current NFCI as if it were the
reading available in 2008 is a look-ahead, full stop (R1). ALFRED carries NFCI vintages, so a PIT reconstruction
is *possible*, but it is a substantial build for a signal that has already failed Stage 0. It is also a broad
composite of ~105 measures spanning risk, credit and leverage — contamination as well as vintage.

**STLFSI4 (St. Louis Fed).** Disqualified on both counts. It is an 18-series weekly composite that includes
volatility and credit-spread inputs directly — re-reading Phases 1.5 and 6 under a new name. And it has been
rebuilt four times: STLFSI → STLFSI2 → STLFSI3 → STLFSI4, with the LIBOR-based spreads replaced first by
90-day-average backward-looking SOFR (v3) and then by forward-looking term SOFR (v4), **with the entire history
back to December 1993 recomputed each time** (the Fed reports corr(v2, v3) = 0.99 over the full sample, which is
only meaningful because the whole history was restated). That is the LIBOR→SOFR splice applied retroactively to
thirty years of history, by a third party, invisibly.

**Conclusion on composites: none of the three is acceptable as this repo's funding measure.** NFCI and STLFSI4
fail on vintage *and* on contamination with signals already admitted. OFR passes vintage but fails on being a
projection onto the common factor — it measures the shared component when the entire value proposition is the
decoupled one. And all three splice LIBOR to SOFR without the user seeing it.

### Recommended narrow series, if a funding signal is built at all

If Adam overrides the fold recommendation, this is the construction to use — narrow, funding-specific,
transaction-based, uncontaminated by a stress composite, and PIT-clean:

1. **Primary — secured-funding dispersion: `SOFR99 − SOFR` (or `SOFR75 − SOFR25`), daily, 2018-04-03→present.**
   FRED publishes the SOFR distribution (`SOFR1`, `SOFR25`, `SOFR75`, `SOFR99`) alongside the volume-weighted
   median. The 99th-percentile-minus-median spread measures **how far the worst-financed borrower is paying
   above the median on the same collateral on the same day**. That is as close to a direct read on binding
   balance-sheet constraints as free data allows, and it is mechanistically the cleanest object in this
   document: it contains no credit leg (both sides are secured against Treasuries), no benchmark-survey
   component, and no cross-era splice. It captured September 2019 unambiguously — SOFR rose from 2.43% to 5.25%
   on 17 September 2019 with intraday prints reported near 10%, an episode with *no* credit event and *no*
   equity drawdown, which is exactly the decoupling this signal claims to detect.
2. **Secondary / cross-check — `SOFR − IORB`** (administered-rate spread; IORB from July 2021, EFFR from 2000-07
   in the current file). Reads the same constraint through a different lens: secured market rate versus the
   administered floor.
3. **Historical-context leg only, never the live reading — the CP−bill spread** already in
   `funding_daily.csv`, and, if long history is wanted for context, `DCPF3M` (3-month AA **financial** CP) in
   place of `DCPN3M` (nonfinancial). Financial CP is the intermediary funding rate and is mechanistically the
   right leg for this question; the current builder uses the nonfinancial series, which is thinner and less
   relevant. **Not the live reading** because of the missingness documented below.
4. **Named and excluded:** the conceptually cleanest measure in the literature — **cross-currency basis / CIP
   deviation** (Du–Tepper–Verdelhan 2018) — requires FX-swap and OIS quotes that are not free. Correctly
   dropped by the kickoff. Repo *haircuts*, the object Gorton–Metrick actually study, are likewise not freely
   available at daily frequency.

**The unavoidable arithmetic.** The recommended primary series begins 2018-04-03. It contains **two**
independent funding episodes (September 2019, March 2020) and one partial (March 2023). V6 requires four. **The
best available measure fails the power pre-check by construction, and no amount of care fixes it.** This is the
core finding of the phase.

---

## Data readiness

Verified against the actual files on 2026-08-06. Coverage only — no values, no statistics about behaviour.

### `data/processed/funding_weekly.csv`

| | |
|---|---|
| shape | 2900 rows × 2 cols; index spans 1971-01-08 → 2026-07-31 |
| index | **all Fridays**, uniform 7-day spacing (2899/2899 gaps = 7 days). Clean. |
| `nfci` | n=2900, 1971-01-08 → 2026-07-31, **no interior NaN** |
| `stlfsi` | n=1701, **1993-12-31** → 2026-07-31, no interior NaN |
| hygiene | index column is unnamed (`Unnamed: 0`), same as `credit_daily.csv` |

**Kickoff claim audited.** The kickoff says "`STLFSI4`, `NFCI`; 1971+". **Partly wrong**: only NFCI reaches 1971.
STLFSI4 begins 1993-12-31 — twenty-three fewer years, and it therefore contains neither the 1987 crash nor the
1990–91 banking stress. Both series are disqualified on the grounds in
[§ Series construction](#series-construction) regardless, but the file's advertised span should not be read as
the usable span.

**Publication-lag note for V1.** NFCI is released 08:30 ET Wednesday covering through the previous Friday; the
file is Friday-indexed. Any causal use must lag the Friday stamp by at least five calendar days, or it reads
data that did not exist. This is the standard weekly-macro alignment trap and it is easy to get wrong.

### `data/processed/funding_daily.csv`

| column | n | first | last | interior NaN |
|---|---|---|---|---|
| `cp3m` (DCPN3M) | 5292 | 1997-01-02 | 2026-08-04 | **2144** |
| `tbill3m` (DTB3) | 18138 | 1954-01-04 | 2026-08-04 | 35 |
| `sofr` | 2082 | 2018-04-03 | 2026-08-04 | 12 |
| `effr` | 6550 | 2000-07-03 | 2026-08-04 | 6 |
| `cp_bill_spread` | 5289 | 1997-01-02 | 2026-08-04 | **2147** |
| `sofr_effr` | 2082 | 2018-04-03 | 2026-08-04 | 12 |

File spans 1954-01-04 → 2026-08-04, 18173 rows, 6 columns (plus an unnamed index column).

**The CP−bill spread fails V4, and the numbers are not marginal.**

- **28.9%** of trading days are missing over the series' own span (1997→2026).
- Longest consecutive missing run: **55 trading days** (~11 weeks). Fifteen separate runs of ≥20 trading days;
  106 runs of ≥5.
- Annual non-null counts collapse repeatedly: 33 days in 2006, 64 in 2024, 64 so far in 2026 — against ~250
  trading days.
- **Coverage in the flagship episode is 63%.** Over 2007-07 → 2009-06: 318 of 502 trading days present.
- **Coverage in the September 2019 repo episode is 49%.** Over 2019-09 → 2019-12: 40 of 82 trading days present.
- Coverage in 2020-01 → 2020-06 is 94% — good, and the one episode where this series would work.

**The missingness is endogenous, which is the disqualifying part.** The Federal Reserve's commercial-paper
release publishes a rate only when trade data are sufficient to support the calculation; when issuance at a
given tier and maturity is too thin, the value is `n.a.`. So the days on which the 3-month AA nonfinancial CP
rate is unavailable are days on which that market did not trade enough to be priced. **A flag built on this
series is dark for up to eleven consecutive weeks, and it is dark for over a third of the global financial
crisis** — and its silence would be read as `intact`. That is R3, verbatim. Switching to `DCPF3M` (financial CP)
would likely improve coverage and is mechanistically better, but this is a change of construction and must be
verified, not assumed.

**`sofr_effr` is clean** — 2082 observations, 12 interior NaN, 2018-04-03 onward, and the interior gaps are
consistent with publication-calendar effects. It is the only daily column in the file fit for a live causal
reading, and it is eight years long.

**Kickoff claims audited.** "CP−bill (`DCPN3M` − `DTB3`, late-1990s+)" — start date correct (1997-01-02),
**but the 29% missingness and the 63% GFC coverage are not mentioned anywhere and are decisive**. "SOFR−EFFR
(2018+)" — correct. "No clean free LIBOR-OIS history; TED discontinued 2022" — **confirmed** (`TEDRATE` ends
2022-01-21). "Cross-currency basis infeasible free" — confirmed. "OFR FSI funding sub-index = preferred strict
PIT source" — **half right**: the PIT property is real and better than the kickoff claimed, but the sub-index is
a projection onto a single common stress factor and its seven funding indicators were entirely replaced in
June 2023, both of which the kickoff did not know.

### Point-in-time status, stated explicitly (§(a))

| input | vintage status |
|---|---|
| `SOFR` and its percentiles, `EFFR`, `IORB`, `DTB3`, `DCPN3M`/`DCPF3M` | **PIT-clean.** Published transaction statistics / market rates; not revised in the macro sense. The NY Fed can republish SOFR under a stated policy, but this is rare and same-cycle. |
| `NFCI` | **NOT PIT.** Entire history revised weekly, including the estimated indicator loadings. ALFRED vintages exist; a PIT reconstruction is possible but is a build in itself. |
| `STLFSI4` | **NOT PIT across versions.** History back to Dec 1993 recomputed at each of three version changes. |
| OFR FSI funding sub-index | **PIT within a version** (documented arrow-of-time property), **but discontinuous across the June 2023 indicator replacement.** |

---

## Cross-signal relationships

Template attribute 4. This is the heart of the phase, and every statement here is a *registered expectation to
be tested*, not a measured result. Nothing below has been computed.

### vs. Volatility (Phase 1.5, `production`)

**Expected relationship: high co-movement in stress, near-zero information in calm.** The mechanism is not
coincidence — Brunnermeier–Pedersen's spiral runs *through* volatility: higher measured volatility raises
margins and haircuts, which tightens funding, which forces sales, which raises volatility. The two are
causally linked in the crisis neighbourhood by construction of the world, not by construction of the
statistic.

**Consequence for admission.** The framework is explicit that statistical correlation with an existing signal is
a diagnostic and not a disqualifier when the mechanisms are distinct (§Discipline, "keep signals that are
statistically correlated but mechanistically distinct"). Funding stress *is* mechanistically distinct from
realised volatility — one is the price of balance sheet, the other is the amplitude of returns. **So the fold
recommendation does not rest on "it correlates with vol."** It rests on G4: the mechanism is distinct but the
*marginal readings* are almost entirely confined to episodes the observatory already flags three other ways.
That is the distinction between the mechanism gate (passed) and the relevance gate (failed).

**Registered test: V7.** Count decoupled days conditional on the volatility percentile being below its 90th.

### vs. Credit / excess bond premium (Phase 6, charter kicked off)

**This is the most serious overlap, and it is a measurement overlap rather than only a co-movement one.** The
classic funding spreads are unsecured rates minus a risk-free rate, so they contain a bank-credit component
directly — Taylor–Williams (2009) argued the 2007–08 LIBOR–OIS widening was predominantly counterparty risk
rather than liquidity, and that debate has never been settled cleanly. Phase 6's object is the *excess bond
premium* — the spread purged of expected default — which its kickoff describes as the thin, orthogonal,
**leading** residual reflecting "bond-investor risk appetite and intermediary balance-sheet capacity beyond
compensation for expected default."

Read that phrase carefully: **"intermediary balance-sheet capacity" is the same He–Krishnamurthy state variable
this signal claims as its own mechanism.** Phase 6 already claims the intermediary-constraint channel, measures
it with a longer and better-behaved series (1973→present, monthly), and claims a 1–2 year lead. Phase 7 would
measure the same underlying state variable with an eight-year series, coincidently, and with a credit
contamination Phase 6 has explicitly purged.

**Registered clarification of what would still be distinct:** the *secured* dispersion measure (`SOFR99 − SOFR`)
has no credit leg at all, so it is genuinely orthogonal to EBP in construction. That is the one construction
where the distinctness claim is clean. It is also the one with eight years of history.

**Registered test: V7 conditions on EBP jointly with volatility, not on volatility alone.** A version that
decouples from volatility but not from credit has not earned anything.

### vs. Tail / jump (Phase 9, charter kicked off)

**The complementary pair, and the reason FOLD is the recommendation rather than DROP.**

Phase 9 monitors *"the return distribution is its normal shape — tails aren't unusually priced"* from
**options-implied** data (CBOE SKEW, VIX term-structure slope) — the **risk-neutral, forward-looking** view of
tail risk. Funding stress is the **realised, money-market, contemporaneous** view of the mechanism that actually
produces left tails. They are the two halves of one question:

| | Phase 9 (tail) | funding flag |
|---|---|---|
| data | option prices | money-market transactions |
| horizon | forward-looking (30d risk-neutral) | contemporaneous |
| object | the *price* of tail risk | the *mechanism* of tail realisation |
| duty cycle | continuous reading | near-zero, episodic |

The genuinely valuable joint observation is the disagreement: **tail risk priced richly while funding is
functioning** is a different environment from **tail risk priced richly while funding is seizing** — the first is
fear, the second is mechanism. Preserving that distinction is exactly what D-03 (disagreement preserved) exists
for, and it is lost if the funding mechanism is simply dropped.

**The honest objection to folding, stated rather than glossed:** an options-implied signal and a money-market
funding flag are different instruments reading different markets, and bolting one onto the other risks a two-headed
signal with one charter — which is a mild version of the composite the architecture forbids. **The fold is
therefore specified narrowly** (next section) so that it cannot become a blend.

### vs. Stock-bond correlation (Phase 2), concentration (4), diversification (5), valuation (3)

No material relationship expected in either direction, and none claimed. Diversification/absorption is the one
worth a passing note — Kritzman et al.'s absorption ratio also spikes in funding crises, because everything
correlates when everyone is a forced seller — but that is a further argument that the crisis neighbourhood is
already densely instrumented, not an argument for adding another instrument to it.

---

## Recommendation

**FOLD INTO PHASE 9. Fallback: DROP.**

**Why not STAND ALONE.** Four independent reasons, each sufficient on its own:

1. **Stage 0 fails on its sharp bar.** G4's leave-one-out is not close. The kickoff conceded "everyday value
   ~zero" before any of the data problems below were known.
2. **The evidence base cannot be built on free data.** The only construction that is narrow, PIT-clean,
   credit-free and unspliced (`SOFR99 − SOFR`, or `SOFR − IORB`) begins in 2018 and contains two independent
   episodes. V6 requires four. Every longer alternative is either dead (TED/LIBOR-OIS, ends 2022-01-21), 29%
   missing with 63% coverage through the GFC and *endogenously* missing (CP−bill), or a revised/common-factor
   composite (NFCI, STLFSI4, OFR funding).
3. **`production` is structurally unreachable.** §(d) makes Japan/Europe out-of-hypothesis-sample confirmation
   mandatory before any SUPPORT claim. The euro-area and Japanese funding spreads carry the *same* benchmark
   cessation (EONIA → €STR, JPY LIBOR → TONA), so the international run would test the splice, not the signal.
   A signal that can never exceed `research` is a poor use of the scarce resource Stage 0 exists to protect.
4. **The mechanism is already claimed next door.** Phase 6's excess bond premium explicitly claims the
   intermediary-balance-sheet-capacity channel, with a 1973-onward series and a claimed lead. Phase 7 would
   re-measure that state variable coincidently with eight years of data.

**Why not DROP outright.** The mechanism is real and the distinction it preserves is genuinely informative: a
drawdown with functioning funding is a different environment from a drawdown with a funding seizure, and
September 2019 is a clean existence proof that funding can dislocate with no credit event and no equity
drawdown attached. Dropping it loses a documented mechanism the observatory otherwise has no instrument for.

**What FOLD means, specified so it cannot drift into a composite:**

- Phase 9's charter absorbs the funding flag as a **separately-reported binary annotation** on the tail
  signal's Level-0 record — a named boolean plus the underlying continuous spread and its causal expanding
  percentile beside it. It is **never averaged, blended, or scored** into the tail reading. This is the same
  discipline as D-02b: the label may never stand alone without its number.
- The assumption **"funding markets function"** stays a ledger key, owned by Phase 9. The ledger's coverage of
  the assumption is preserved; what disappears is the separate signal record, the separate maturity tag, and
  the separate research programme. **[recommended — Adam to confirm/override]**
- The flag is held to **V1–V4 and V6** above. V5/V7 become Phase 9's business. If Phase 9's own charter
  concludes that an options-implied instrument should not carry a money-market annotation — a legitimate
  conclusion — **the flag DROPS. It does not revert to standalone.** Registering the fallback now prevents the
  fold from becoming a way to keep a failed candidate alive.
- The material in this document, the coverage audit, and the `SOFR99 − SOFR` recommendation are the inheritance.
  Phase 9 does not re-derive them.

**What is NOT recommended:** building `scripts/funding_flag.py`, spending a look, wiring the OFR FSI download,
or reconstructing NFCI vintages from ALFRED. None of that should happen before Adam rules on the fold.

---

## Open questions for Adam

1. **The fold itself.** FOLD INTO PHASE 9 with DROP as fallback. **[recommended — Adam to confirm/override]**
   The competing view — that a mechanism this important deserves its own instrument regardless of duty cycle —
   is defensible; it would mean accepting a permanent `research` ceiling and a two-episode evidence base.
2. **The ledger key.** Retain "funding markets function" as a ledger key owned by Phase 9, rather than deleting
   it with the standalone signal. **[recommended — Adam to confirm/override]**
3. **If you override and want it standalone: the series.** `SOFR99 − SOFR` (secured-funding dispersion,
   2018-04→present) as primary, `SOFR − IORB` as cross-check, CP−bill demoted to historical context only, and
   `DCPF3M` (financial CP) substituted for `DCPN3M` in that context leg. **[recommended — Adam to
   confirm/override]**
4. **The splice.** Post-transition era only (option c), not a scale-adjusted splice (option a) and not a
   two-era construction (option b). **[recommended — Adam to confirm/override]** Option (a) is
   result-driven-specification-adjacent and should be off the table regardless.
5. **The episode lists** in V5 — both the "must fire" and the "must not fire" list are my drafts and must be
   fixed before any look. March 2023 in particular is a judgement call: a funding episode that was largely
   contained by the discount window and the BTFP, so it partly tests R4 (backstop vs fragility) rather than the
   signal. **[recommended — Adam to confirm/override]**
6. **The V7 bar.** 20 decoupled days across ≥2 episodes separated by >1 year. The number is mine and is
   deliberately modest; if you think a lower bar is defensible, set it *now*, before any look, or it is not a
   pre-registration. **[recommended — Adam to confirm/override]**
7. **Anything downstream of a fold is Phase 9's charter, not this one.** This document should be closed with a
   dated FOLD or DROP ruling and not reopened as a standalone charter later without a fresh Stage-0 pass.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/07-funding-signal/07-CHARTER-KICKOFF|07-CHARTER-KICKOFF]]

<!-- LINKS:END -->
