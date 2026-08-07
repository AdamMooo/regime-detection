# Tail Signal — Research Charter

**DRAFT — NOT FROZEN, NOT SIGNED.**

Drafted 2026-08-06 against framework template **v1.1** (`research-charter-template.md`). No look has been spent:
the only data contact was coverage inspection (dates, row counts, missingness, columns) recorded in §Data
readiness. **Nothing in this document reports how the signal behaves, what it correlates with, or whether it
works.** Those are registered below as tests.

Freezing this charter requires Adam's dated sign-off, which is a separate act from any later sign-off of results
(`validation-standards.md` §(e)).

---

## Headline: this charter REFRAMES the signal, and the reframe is load-bearing

The warm-start kickoff (`09-CHARTER-KICKOFF.md`) registered the monitored assumption as *"the return distribution
is its normal shape — tails aren't unusually priced."* Those are two different claims joined by a dash, and the
data can only measure the second one.

**CBOE SKEW is a price, not a probability.** It is computed from the risk-neutral density implied by SPX option
prices. The risk-neutral density is the physical density reweighted by the pricing kernel, `q(x) = p(x)·m(x)/E^P[m]`,
and a cross-section of option prices identifies only the product — never the split. Bollerslev & Todorov (2011,
*JF*) measure both sides and find the risk-neutral left-tail jump intensity exceeds the physical one by **two to
three orders of magnitude** (their Table 1: jumps < −10%, Q intensity 0.5640 vs P intensity 0.0017, and the P
estimates are not statistically distinguishable from zero). More decisively for this signal: **the left/right
asymmetry that skew measures exists only under Q** — the physical tails are close to symmetric and their
left/right difference is statistically insignificant.

Therefore the signal cannot monitor "the distribution is its normal shape." It monitors **"downside protection is
priced normally."** That is a narrower claim, it is honestly measurable, and — critically — it is a claim about a
*market price of risk*, which is a mechanism family the observatory currently has no sensor for at all.

**If Adam rejects the reframe and requires the original physical-shape assumption, the correct outcome is DROP,**
because no free data in scope can measure it (the realized-jump / bipower route that could is excluded as
data-gated, and physical tail estimation on daily returns is a different measurement object — see §RN-vs-P).

---

## Stage-0 Relevance Gate — RE-RUN (default = NO)

The kickoff recorded a PASS. It is re-run here because the reframe changes what G1 and G3 are answering, and
because one kickoff citation does not support the claim it was attached to.

- **G1 — important investment question.** *How expensive is protection against a large decline in the broad
  equity market right now, relative to at-the-money, and how unusual is that price versus its own history?*
  (Kickoff G1 asked whether "the shape of the return distribution is abnormal" — a physical question this data
  cannot answer. Replaced.)

- **G2 — why it matters to long-term investors.** It is the market's own quoted price for bearing large-decline
  risk. Every other admitted signal reads what the market *did* (realized volatility, realized correlation,
  realized prices); this reads what participants currently *charge* to absorb a left-tail event. When that price
  is at a historical extreme, the market is expressing something about large-decline risk that no realized
  measure contains — and the long-horizon investor who wants to know whether the environment is unusual should
  know whether protection is unusually dear or unusually cheap.

- **G3 — information not already available from the existing signals.** Yes, on two independent axes:
  1. **Measure.** Every admitted signal (volatility, stock-bond correlation) is a **physical (P)** measure built
     from realized returns. This is a **risk-neutral (Q)** measure — a price. The observatory has zero coverage
     of the market price of risk.
  2. **Moment.** Volatility measures the *width* of the distribution (second moment). This measures its
     *asymmetry* (third moment) — the price of out-of-the-money downside protection **relative to**
     at-the-money, which is by construction a shape statistic normalized by width.

  Direct evidence the Q left tail is not spanned by volatility: Andersen, Fusari & Todorov (2017, *JF*) find "a
  sharp separation between the dynamics of the actual jump risk and its pricing," and that the risk-neutral
  left-jump tail moves in ways inconsistent with affine models in which jump intensity is proportional to
  volatility (Bates, Pan). Bollerslev & Todorov (2011) state it plainly: "the risk premium for tail events cannot
  solely be explained by the level of the volatility." Bollerslev, Todorov & Xu (2015, *JFE*) open with the point
  that "on average, only a small fraction of the VIX is arguably attributable to market fears" — i.e. the level
  and the tail-price component are separable objects.

  **Kickoff correction.** G3 in the kickoff cited "Kelly-Jiang 2014 ≈5.4%/yr" as evidence for this signal. Kelly
  & Jiang (2014, *RFS*) is a **physical** cross-sectional tail measure — a Hill power-law estimator on the pooled
  cross-section of daily firm returns — and its 5.4% is a tail-*beta* return spread. It is a different
  measurement object on a different probability measure and it does **not** support an options-implied signal.
  Kelly & Jiang report their measure correlates 30–33% with option-implied skewness and kurtosis, which is itself
  consistent with the two objects being largely distinct. Citation retired from this signal's justification.

- **G4 — leave-one-out.** Removing this signal leaves the observatory with no reading of what the market charges
  for large-decline risk, and no risk-neutral sensor of any kind. The environments this distinguishes — calm with
  cheap protection versus calm with historically expensive protection — are not separable by any admitted signal.
  Meaningful loss ⇒ keep. **Contingent on V4:** if the reading turns out to be statistically spanned by the
  volatility level with no decoupling episodes and no interpretable residual, this answer inverts and the signal
  is dropped (R4).

- **G5 — strong ex-ante prior. Split verdict, and the split is the point.**
  - **Prior on the OBJECT: strong.** The priced left tail is one of the most robustly documented features in
    derivatives pricing: Rubinstein (1994, *JF*) "crash-o-phobia" — the persistent post-1987 negative skew in
    index implied volatility; Bakshi, Kapadia & Madan (2003, *RFS*) on the model-free risk-neutral moments and
    why index densities are far more negatively skewed than individual-stock densities; Bates (2008, *JEDC*)
    *The Market for Crash Risk*; Bollerslev & Todorov (2011). The prior is not that it *predicts* — this charter
    tests no prediction. It is that **the object exists, is separately priced, and has its own time variation.**
  - **Prior on the INSTRUMENT (the CBOE SKEW index specifically): weak, and the literature is unflattering.**
    Cao, Ruan & Zhang (2020) find SKEW "very noisy" and not containing "much important information";
    Bevilacqua & Tunaru (2021) find only the put-only variant carries signal while the aggregate inherits an
    over-optimistic bias from the call side; Kozhan, Neuberger & Schneider (2013) find skew risk tightly related
    to variance risk with an insignificant premium once variance is hedged out. Add the instrument defects found
    in §Data readiness: a confirmed silent revision of the published history, an announced-but-unscheduled full
    recalculation that may change the index's definition, and strike-grid measurement error confounded with the
    index level.

  **This split is the honest state of the evidence: sound mechanism, poor instrument.** The framework handles
  exactly this case — the mechanism gate is binary and passes, while measurement validity is a separate,
  non-compensatory axis that grades **L**. A strong mechanism does not buy off a weak instrument, and this
  charter does not let it try.

**GATE VERDICT: PASS — CONDITIONAL, at reduced confidence versus the kickoff's unqualified PASS.** Conditional on
(a) the reframed assumption being accepted; (b) the V4 redundancy bar, which is a kill condition and which
Kozhan et al. (2013) give a real prior of firing; and (c) the V8 start-date restriction surviving with enough
history left to support an honest rarity read.

**DROP remains a defensible call and Adam should make it deliberately rather than by default.** The case for DROP:
the signal can never reach `production` (the international bar is unmeetable, not merely unmet), the instrument
is contested in peer review, and Stage-0's stated scarce resource is research time. The case for PROCEED: the
mechanism is real and the observatory has no other risk-neutral sensor, the data is free, and a documented null
from a properly pre-registered R4 is itself a legitimate output of a measurement framework. My recommendation is
**PROCEED at reduced priority** — see §Open questions item 9.

---

## Header

- **Signal name** — Tail (the priced asymmetry of the risk-neutral density)
- **Assumption monitored** — **"downside protection is priced normally."** *(Reframed. The kickoff's "the return
  distribution is its normal shape" is a physical claim this data cannot measure — see §RN-vs-P.)*
- **Native clock / frequency** — daily (fast). Same clock as volatility; the two are read side by side.
- **Ledger status** — **NONE. Registered deliberately: this signal emits a reading plus its rarity and no
  {intact | under-test | violated} label.** Volatility carries no status because it is a context axis;
  stock-bond correlation carries one because **sign zero is a real mechanical boundary** (bonds move against
  equity, or with it). Here there is no such boundary: the index risk-neutral density has been persistently
  negatively skewed since 1987, so the sign is uninformative and *any* status threshold would be an arbitrary
  percentile knob — precisely the failure the volatility reframe removed. The assumption is named; the evidence
  for it is the continuous price and its historical rarity. `[recommended — Adam to confirm/override]`
- **Maturity tag** — DERIVED, not hand-set. **Registered ceiling: `research`.** `production` is not available to
  this phase and must not be claimed, on four independent grounds established before the look: (i) international
  out-of-hypothesis-sample replication is **impossible, not merely difficult** — no risk-neutral-skewness index
  exists for Japan or Europe at any tier (V6, and §Data readiness finding 11); (ii) the input is a vendor-computed
  index that cannot be independently reconstructed from free data (V1); (iii) the pre-2011 history is a
  retrospective backfill, not a point-in-time-available series (V2); (iv) Cboe changed the SKEW methodology on
  2025-07-17 and indicated the history would be **recalculated**, so the series is itself a moving object
  (§Data readiness finding 6). Registering the cap now, per the Phase 2 precedent, so a strong result cannot
  tempt it away afterwards.
- **Investor question (production bar)** — *"How expensive is protection against a large equity decline right
  now, relative to at-the-money, and how unusual is that price versus its own history?"* Clearly answerable from
  the data; note that clearing the *question* bar does not lift the maturity ceiling above, which rests on
  evidence and measurement grounds.
- **Charter/spec version** — v0.1 (DRAFT)
- **Charter dated** — drafted 2026-08-06. **NOT FROZEN. NOT SIGNED.**

**Charter-first status: CLEAN.** No implementation exists. `scripts/build_tail.py` is a data builder only; no
`build()` construction, no descriptors, no look.

---

## The six charter questions

### 1. What question does the signal answer?

*How expensive is protection against a large decline in the broad equity market right now, relative to
at-the-money protection, and how unusual is that price versus its own history?*

The signal reports the **asymmetry of the 30-day risk-neutral density of the S&P 500** — how much more the market
charges for out-of-the-money downside than the symmetric-density benchmark implies — as a continuous reading plus
its causal historical rarity. Following the volatility signal's shape, there is **no state and no label**:

1. **How asymmetric?** The risk-neutral skewness of the 30-day SPX log return.
2. **How unusual?** Causal expanding-window percentile against the signal's own history to date, plus a
   trailing-252-day rarity lens.
3. **Which way?** Short-horizon drift of that percentile.
4. **At an extreme?** Whether the reading sits at or beyond a historical extreme, and which side.

It answers nothing about *when* a decline will occur, or *whether* one is more likely. See Q6 and §RN-vs-P.

### 2. What market assumption does it monitor?

**"Downside protection is priced normally."** The assumption is named and the evidence is the continuous reading
plus its rarity. No status label is emitted (see Header).

What a violation of this assumption *means* — whether historically dear protection reflects information, crowding
into protection, constrained dealer capacity to supply it, or simple fear — is **not resolvable from this signal
and is not claimed**. The signal reports the price and its rarity, names the assumption, and STOPS.

### 3. What mechanism supports it — why does it survive being known?

**Registered mechanism: risk-premium channel — the jump/tail risk premium, plus an intermediary supply channel.**

**The structural reason.** Insuring a large index decline is a risk that cannot be diversified away and cannot be
hedged by trading the index alone (a jump cannot be replicated by continuous trading). Someone must bear it, and
they must be compensated. The compensation is large and has its own time variation: Bollerslev & Todorov (2011)
attribute a median **5.2%** of the equity risk premium to fears of rare events — roughly two-thirds of the
prototypical post-war equity premium — and **~60%** of the variance risk premium to the left tail alone. Carr &
Wu (2009, *RFS*) establish the variance risk premium as a separately priced factor unexplained by CAPM or
Fama-French. Bates (2008) models the market for crash risk as an equilibrium between heterogeneously
crash-averse agents; Gârleanu, Pedersen & Poteshman-style demand-based pricing adds the supply side — dealers
with finite balance-sheet capacity charge more for protection when their capacity to warehouse it is impaired.

**Why it survives being known.** It is a **price of risk, not a mispricing**. There is no arbitrage: the premium
compensates a real, undiversifiable, unhedgeable risk of jumps. Publishing "downside protection is currently
at the 95th percentile of expensiveness" does not make anyone willing to supply it more cheaply — if anything the
knowledge is already in the price, since the price *is* the signal. The measurement reports a traded quantity;
knowing it changes nothing about the fact. This is the same structure as the credit signal's excess bond premium
(the credit market's price of risk) and the opposite of a predictive edge claim, which this charter does not make.

**Distinctness from volatility (the mechanism gate's real work here).** Volatility measures the *width* of the
realized, physical distribution. This measures the *asymmetry* of the *priced, risk-neutral* one. Two
independent separations — moment order and probability measure. The literature supports the separation directly:
AFT (2017) find the risk-neutral left-jump tail's dynamics are sharply separated from actual jump risk and
inconsistent with jump intensity being proportional to volatility; BT (2011) find the tail premium is not
explained by the level of volatility; BTX (2015) find that subtracting the left-jump variation from the variance
risk premium halves its explanatory content while adding VIX² to the left-jump measure "hardly increases" it.

**COUNTER-EVIDENCE, registered before the look because it cuts against the signal.** The distinctness argument is
contested in peer review and the charter must say so:

- **Kozhan, Neuberger & Schneider (2013, *RFS* 26(9), 2174–2203)** find that "skew risk is tightly related to
  variance risk," and that once variance risk is hedged out, **the remaining skew premium is insignificant**.
  This is the single most damaging citation for G3/G4 and it is a direct prior that V4's residual will be thin.
- **Scale dependence is structural, not incidental.** Risk-neutral skewness is the third cumulant normalized by
  total variance to the 3/2 power. SKEW and VIX are therefore **two nonlinear functions of one underlying state
  vector**, not two independent readings — which is why the empirical relationship between them is unstable in
  sign: reported at **−0.23 in levels** (Bevilacqua & Tunaru 2021, *Journal of Financial Stability* 53, 100816)
  yet positive in daily changes (Liu & Faff 2017). Cboe's own FAQ describes the two as "uncorrelated," which both
  results contradict. *(These are literature values, cited here as priors that shape the test design. No
  correlation has been computed in this repo.)*

**How this is reconciled — and the limit of the reconciliation.** Kozhan et al. test whether skew risk earns a
premium *after hedging variance* — an investability question. This repo asks whether the priced asymmetry is a
distinct *measurement*, which is a different and lower bar: a quantity can be a distinct, honestly-measured
feature of the environment without being separately harvestable. That distinction is real, and it is also
exactly the kind of reasoning that can be used to wave away inconvenient evidence. So it is not accepted here as
a defence; it is registered as the reason V4 is designed around the **residual** rather than a correlation
threshold, and R4 is written so that a thin, unstable residual **kills the signal**.

**The mechanism gate is passed on the reframed claim, and only on it** — and provisionally, subject to V4. Under
the original physical-shape claim the gate would fail outright, because no mechanism connects an option price to
a physical crash frequency without an untestable pricing-kernel restriction (§RN-vs-P). This is registered here
so the distinction cannot be blurred later.

### 4. What evidence would validate it?

Because this is a **measurement** claim, not a forecastability claim, validation follows the volatility charter's
shape: measurement correctness plus replication, with falsification aimed at the measurement being an artifact.
**No forward-return statistic is computed anywhere in this phase.** V1–V7 are stated in §Validation bars below,
each paired with its reject condition.

The out-of-hypothesis-sample bar (`validation-standards.md` §(d)) is V6, and its likely outcome — a documented
failure for lack of free international option-implied data — is registered in advance as the reason for the
`research` maturity ceiling, not discovered after the look.

### 5. What would falsify it?

R1–R8 in §Validation bars, each paired to the test it trips. The decisive one is **R4: redundancy with
volatility**, which is a kill condition, not a caveat. There is deliberately no "tail failed to predict a
drawdown" reject condition — the signal never claims to predict one.

### 6. What does it explicitly NOT claim?

The signal reports the current price of downside protection relative to at-the-money, its historical rarity, its
direction of travel, and whether it sits at an extreme — and **STOPS**.

Explicit prohibitions (this list is a boundary statement; the forbidden vocabulary appears here only in order to
prohibit it):

- It is **NOT a crash predictor and NOT a crash-probability estimate.** It does not state, imply, or permit the
  inference that a large decline is more or less likely. This is the single most important prohibition attached
  to this signal, and §RN-vs-P is the reason.
- It is **NOT a forecast** of returns, of volatility, or of when protection will cheapen or dearen.
- It is **NOT a state, regime label, switch, trigger, or timing signal**, and emits no
  {intact | under-test | violated} status.
- It never states or implies a buy or sell, a risk-on or risk-off reading, an allocation, exposure, weight, tilt,
  sleeve, cash call, position sizing, risk budget, or any recommendation to obtain or forgo downside protection.
  Whether to act on an unusual price for protection is the human's judgment in a separate system; this repo does
  not know that system exists.
- It is **NOT a composite** and is never combined with the volatility reading into a single number. The two are
  presented side by side precisely because their disagreement (calm market, expensive protection) is the
  information.

---

## RISK-NEUTRAL VS PHYSICAL — what this signal measures, and what it therefore cannot claim

This section governs the whole charter. It is the identification problem, and it is not a caveat to be softened.

### The problem

Option prices are state prices, not probabilities. For any horizon,

> `q(x) = p(x) · m(x) / E^P[m]`

where `p` is the physical density, `q` the risk-neutral density, and `m` the pricing kernel (marginal-utility
weighting). A cross-section of option strikes identifies `q`. It does **not** identify how `q` splits into `p`
and `m` — the pricing kernel is identified only as the ratio `q/p`, so recovering either requires an independent
estimate of the other (Aït-Sahalia & Lo 2000, *J. Econometrics*; Jackwerth 2000, *RFS*; Rosenberg & Engle 2002,
*JFE*; Bliss & Panigirtzoglou 2004, *JF*).

### How large is the wedge, specifically for the tail

Not a rounding error — orders of magnitude. Bollerslev & Todorov (2011, *JF*), estimating Q intensities from SPX
options and P intensities from 5-minute futures with EVT extrapolation:

| 30-day jump | Q intensity | P intensity | ratio |
|---|---|---|---|
| < −7.5% | 0.9888 | 0.0036 | ~275× |
| < −10% | 0.5640 | 0.0017 | ~332× |
| < −20% | 0.0862 | 0.0002 | ~430× |

The P estimates are statistically indistinguishable from zero; the Q estimates are highly significant. The
authors rule out a Peso-problem explanation, because the P side is estimated from frequent medium-sized jumps
plus extrapolation rather than from the handful of realized disasters.

**And the asymmetry — the thing skew measures — is a Q phenomenon only.** BT (2011) find the risk-neutral
intensity for jumps < −20% exceeds that for jumps > +20% by more than 12×, while the corresponding physical
asymmetry is statistically insignificant. The skew of the physical distribution is close to symmetric at these
horizons. **What SKEW measures does not have a physical counterpart of comparable magnitude.**

### Is the *variation* premium or probability?

There is **no published clean variance decomposition** of the form "X% of the variation in an option-implied tail
measure is premium." Anyone quoting one is paraphrasing. The literature converges from four directions and the
answer is "predominantly premium":

- **Level:** essentially all premium (the table above).
- **Asymmetry:** a Q object; the P asymmetry is insignificant.
- **Variation, derived:** Bollerslev, Todorov & Xu (2015, *JFE*) show that under approximately symmetric physical
  tails — which BT (2011) support empirically — the left-minus-right jump premium reduces to the observable
  risk-neutral left-jump variation itself, "conveniently avoid[ing] any tail estimation under P." In plain terms:
  **the observable Q left-tail series is, to a first approximation, the premium series.** This is the strongest
  available citation for the point, and it rests on a stated assumption.
- **Variation, from Q dynamics:** AFT (2017) find the priced negative-jump tail varies in ways "unmatched by
  actual variation in negative market jumps under the statistical measure," and read this as time-varying risk
  aversion toward tail risk. Todorov (2010, *RFS*) finds willingness to pay for jump protection rises sharply
  immediately after a jump, beyond what the change in jump activity warrants — a time-varying price of risk, not
  a time-varying quantity of risk.

### Can the physical density be recovered?

**No, and this is not an open engineering problem we could solve later.** Ross (2015, *JF*) claims recovery of P
from Q, but requires a finite-state time-homogeneous Markov chain, the full state-price *transition matrix* (not
a strike cross-section), and **transition independence** — which Ross concedes is necessary "to allow us to
separately determine the kernel and the natural probability distribution." Borovička, Hansen & Scheinkman (2016,
*JF*) show transition independence is equivalent to assuming away the martingale (permanent-risk) component of
the SDF; when it is present — and empirically it is large — Ross's procedure recovers a long-term eigen-measure,
not investors' measure, and treating it as P "may severely bias inference about risk premia [and] investors'
aversion to risk." Jackwerth & Menner (2020, *JFE*) find recovered densities from SPX options are incompatible
with subsequent returns and fail to beat naive benchmarks. Jensen, Lando & Pedersen (2019, *JFE*) generalize the
setting but trade one identifying restriction for another. Backus, Chernov & Martin (2011, *JF*) find that
inverting options into consumption disasters gives probabilities irreconcilable with macro data — itself evidence
the object is not a probability.

### The resolution — what this signal measures

> **The signal measures the current PRICE of one month of downside protection on the broad US equity index,
> relative to at-the-money, expressed as the asymmetry of the risk-neutral density. It is a price, not a
> probability.**

This claim requires no auxiliary assumption, because it is a statement about traded quantities. Everything beyond
it — "the market thinks a crash is X% likely," "crash risk is elevated" — requires an untestable pricing-kernel
restriction and is prohibited by Q6.

**What is therefore forbidden in every output, presentation, and downstream reference:**

- any translation of the reading into a probability, likelihood, odds, or expected frequency of a decline;
- the words "crash risk is high/low" without the qualifier that this is the *price of protection against* one;
- any claim that a historically extreme reading means a decline is more likely — the literature's own reading is
  the reverse-causal one, that the price rises because compensation demanded rises;
- any comparison of the reading to realized outcomes framed as accuracy, hit rate, or calibration.

**The comparison for what a defensible option-implied claim looks like:** Martin (2017, *QJE*) derives a lower
*bound* on the equity premium from risk-neutral variance under one economically motivated assumption. A bound on
a price of risk, not a point estimate of a probability. That is the ceiling of what this data supports.

**Is a price still worth measuring?** Yes, and this is the affirmative case, not a consolation. The price of
downside protection is the market's own quoted compensation for bearing large-decline risk. It is observable,
final, high-frequency, and — per G3 — the only risk-neutral quantity in the observatory. A market where
protection is at its most expensive in a decade is a *different environment* from one where it is at its
cheapest, and no realized measure distinguishes them. That is a measurement worth having. It is simply not a
forecast, and this charter is constructed so it can never be read as one.

---

## Validation bars and reject conditions

Each V is paired with the R it trips. All of V1–V8 run **once**, in a single frozen script, after this charter is
signed. Deviations are disclosed with a dated note, never silently edited.

**V1 — Definitional fidelity. Largely PRE-CONFIRMED from the vendor documentation (2026-08-06), not deferred to
the look.** `SKEW = 100 − 10·S`, where `S` is the risk-neutral skewness of the 30-day SPX log return; **higher
SKEW = more negative risk-neutral skewness**. The **Bakshi–Kapadia–Madan (2003, *RFS* 16(1), 101–143)** lineage
is an **explicit Cboe citation** (white-paper footnote 2), not an inference of ours. The signal therefore reports
`S_t = (100 − SKEW_t)/10` (negative = priced left asymmetry), **not** the vendor's 100-scale, because the
100-scale inverts the sign and reliably misleads a reader into thinking "up = safer." What remains for the run is
narrow: confirm the transform is a deterministic re-expression with no fitting, and confirm nothing in the file
violates the bounds the mapping implies.
> **R1 — the object is not what we claim.** The published methodology does not support the mapping, or the index
> ceases to be the BKM third-moment object. **NOTE: R1 has a known future trigger** — the announced
> reconstitution (finding 7) proposes replacing the BKM measure with a **25-delta put/call ratio or
> differential**, which is a *different object*. If that lands, V1 fails by construction and the signal must be
> re-chartered, not patched. **Re-specify or drop**, disclosed.

**V2 — Causality, look-ahead, and point-in-time availability.** `assert_causal(build, tail_frame)` must pass
before the one-look (`causal.py`; enforced structurally by `tests/test_reproducibility.py`). All rarity is
causal expanding-window (`causal.expanding_percentile`), never a full-sample rank. Two further point-in-time
defects are registered because both are easy to miss and neither is ordinary revision: (a) **the pre-2011 SKEW
history is a retrospective backfill** that no live reader could have seen — not point-in-time-*available* even
though its option-price inputs were never revised; (b) **the published series is subject to recalculation** by
the vendor (§Data readiness finding 6), so the run must execute against a **frozen, date-stamped vintage**, never
a live re-fetch. Registered dual read: the full history and the live-publication era only, reported side by side.
> **R2 — leak or unusable history.** `assert_causal` fails; **or** the qualitative reading differs materially
> between the full-history and live-era rarity bases in a way that would mislead a reader. **Kill, or truncate
> the usable history to the live era with the loss disclosed.**

**V3 — Methodology homogeneity across the documented rebasings.** The break dates are registered in §Data
readiness before the look. The distribution of `S_t` (level and dispersion) must not exhibit a break at those
dates large enough that an expanding percentile is comparing two different instruments.
> **R3 — methodology break.** A material distributional break at a documented methodology-change date.
> **Truncate the usable history to the homogeneous segment** and re-derive the rarity base, disclosing the lost
> history. If the homogeneous segment is too short to support a rarity read, **drop**.

**V4 — REDUNDANCY WITH THE VOLATILITY SIGNAL (the decisive bar).**

> **Design note, disclosed.** An earlier draft of this charter made the primary redundancy trigger a correlation
> threshold (|ρ| ≥ 0.80). That design was **wrong and is retracted before the look.** The literature reports
> corr(SKEW, VIX) at about **−0.23 in levels** (Bevilacqua & Tunaru 2021), so an 0.80 trigger could essentially
> never fire — a reject condition that cannot fire is not a reject condition, and pre-registering one would have
> been unfalsifiable theatre. Worse, a *low* correlation would have been read as evidence of distinctness when
> Kozhan et al. (2013) show the entanglement is **conditional and nonlinear**, not linear-contemporaneous, and
> the scale-dependence argument (third cumulant over variance^{3/2}) predicts exactly that. The redesign below
> makes the **residual** the primary test, which is what Kozhan et al. actually did.

  - **(a) PRIMARY — the vol-conditioned residual.** A **causal expanding-window** regression of `S_t` on the
    volatility signal's contemporaneous level, specified to admit the known nonlinearity (level and log level; no
    search over specifications after seeing results — the two-term form is fixed here). Report the residual and
    assess whether it is **stable, economically interpretable, and non-negligible** relative to the raw series.
    House precedent: the credit signal *keeps the EBP residual and drops the raw spread*; the architecture doc
    already rejects "VIX/VRP as a separate axis (collapses onto vol)." The residual is registered **now**, not
    invented afterwards.
  - **(b) Decoupling episodes.** Identify and characterize periods where the two readings' rarity percentiles
    diverge materially, and state whether they form an **interpretable class** (a describable kind of
    environment) or are unstructured noise. This is the leave-one-out test made empirical.
  - **(c) Descriptive diagnostic, NO threshold attached.** Rank correlation between the tail reading and the
    volatility level percentile, reported in **both levels and daily changes** (the literature's sign conflict
    lives in that gap), full sample and by sub-period. Reported for the record and to characterize the
    relationship. Per house rule, statistical correlation is a diagnostic and never the gate — and here it is
    explicitly *not* wired to any reject condition, because it cannot bear that weight.

> **R4 — the signal carries no information the volatility axis does not. KILL.** Fires when **(a) the
> vol-conditioned residual is not stable and interpretable** — thin, unstable, or indistinguishable from
> estimation noise, which is the outcome Kozhan et al. (2013) predict — **AND (b) the decoupling episodes do not
> form an interpretable class.** Either condition failing to hold means the signal is kept, with the overlap
> documented. If the residual survives but the raw level does not, **the residual becomes the presented reading
> and the raw level is demoted to a diagnostic**, exactly as EBP demoted raw spreads.
>
> **Registered prior, so the outcome cannot be spun either way:** given Kozhan et al., R4 firing is a *likely*
> outcome, not a surprise. A null here is a clean, publishable result for a measurement framework and is to be
> recorded as such — not softened, and not rescued by a specification search.

**V5 — Sub-period replication (the registered substitute for international OOS).** The descriptive properties —
rarity calibration approximately uniform, persistence of the same order of magnitude, sign of the asymmetry
stable — must hold in the backfill era and the live-publication era separately, split at the registered date.
This is explicitly **weaker** than the Japan/Europe bar and does not substitute for it in the maturity
assessment; it caps evidence maturity, it does not lift it.
> **R5 — the property is an artifact of the backfill.** The descriptive properties hold in the backfill era but
> not the live era. That would mean the signal is a property of the vendor's retrospective algorithm, not of the
> market. **Kill.**

**V6 — Out-of-hypothesis-sample: RESOLVED IN ADVANCE AS A DOCUMENTED FAILURE** (`validation-standards.md` §(d)).
The availability question was researched *before* this charter rather than discovered after the look. The finding
is definitive and is recorded in §Data readiness: **no risk-neutral-skewness index exists for Japan or Europe at
any tier, free or paid-published.** There is nothing to replicate on. Two structural consequences worth recording:

  - The shared `run_oos` harness (`scripts/run_oos.py`) operates on regional *return* panels and **cannot serve
    this signal at all** — an options-implied measure has no returns-based analogue. This is the first signal in
    the set for which the shared OOS spine does not apply.
  - The only free path to an international risk-neutral skew is to begin harvesting the JPX daily settlement
    chain (which does carry per-strike settlement prices and implied volatilities, sufficient for a BKM
    calculation) **prospectively** — no archive exists, so it can never produce historical replication. Out of
    scope for this phase; noted so it is not rediscovered.

> **R6 — NOT A KILL; a registered, pre-committed cap.** The international bar cannot be met. Record the
> documented failure per §(d), set **evidence maturity = L**, and hold the maturity tag at **`research`**
> permanently unless purchased data is later obtained — a separate decision outside this phase. Registering this
> before the look is the whole point: a strong US result must not be able to argue the cap away.

**V7 — Confound-check on every historical-context statistic** (`validation-standards.md` §(c)). Any statement of
the form "environments with similarly-priced protection looked like X" must rule out the volatility confound by
conditioning on the volatility reading, and must state the conditioning explicitly.
> **R7 — unconfounded statement unavailable.** A context statistic that cannot be separated from the volatility
> confound **is not reported at all**. Not a kill for the signal; a kill for that statistic.

**V8 — The rarity descriptor is not an artifact of improving measurement precision.** This bar exists because of
§Data readiness finding 9: the strike-grid error in the BKM third moment shrinks monotonically as the index level
rises, so measurement precision is **confounded with calendar time**. The expanding-window rarity read — the core
of what this signal reports — would inherit a manufactured trend from that alone. Registered test: the
distributional properties of `S_t` (dispersion above all, since discretization error inflates variance) must not
show a monotone decline across the sample that tracks the index level rather than any market event; and the
rarity read must be materially unchanged between the full sample and the restricted start date.
> **R8 — the rarity read is a measurement artifact.** The dispersion of `S_t` declines monotonically with the
> index level, and the rarity percentile shifts materially when the start date is restricted. **Not a kill for
> the signal — a kill for the long sample.** Truncate to the measurement-grade era (recommended 2000-01, with
> 2011 as the conservative alternative), re-derive the rarity base on the restricted sample, and disclose the
> lost history. If no start date leaves enough history to support an honest rarity read, **drop**.

**Registered design constraint, not a bar:** no forward-return, forward-drawdown, hit-rate, lead/lag, or
predictive statistic of any kind is computed in this phase. Not as a headline, not as a robustness check, not in
a scratch script. The signal makes no forward claim, so there is nothing for such a statistic to validate, and
computing one is how a measurement system drifts into a prediction system.

---

## Data readiness — verified against the actual file

Verified 2026-08-06 by coverage inspection only (`data/processed/tail_daily.csv`, and `data/processed/MANIFEST.csv`).

**Coverage as observed:**

| column | first | last | non-null rows |
|---|---|---|---|
| `skew` | 1990-01-02 | 2026-08-04 | 9198 |
| `vix` | 1990-01-02 | 2026-08-04 | 9243 |
| `vix3m` | **2009-09-18** | 2026-08-05 | 4245 |
| `vix9d` | **2011-01-04** | 2026-08-05 | 3919 |
| `term_slope` | **2009-09-18** | 2026-08-04 | 4244 |

File span 1990-01-02 … 2026-08-05, 9248 rows. MANIFEST entry present with sha256 and matching shape.

**Findings that change the charter:**

1. **`term_slope` has no pre-2009 history at all, and cannot be given one.** It begins **2009-09-18** in our file
   — after the Global Financial Crisis, and with no dot-com, no 1998, no 1987 aftermath. Cboe's own first-value
   dates confirm this is not a download artifact: **VIX9D 2011-01, VIX3M 2009-09, VIX6M 2008-01**. (VIX itself
   shows 1990-01 but was launched 2003-09-22 in its current model-free form, so 1990–2003 is *also* backfill.)
   Seventeen years containing one genuine stress episode (2020). The kickoff presented SKEW and the term slope as
   co-equal inputs; they are not remotely comparable in evidential weight.

   **Additional construction constraint: the curve is not a homogeneous universe.** The contract sets differ
   along the maturity axis — VIX9D and VIX use end-of-week SPXW options, VIX3M uses end-of-month SPXW, and VIX6M
   uses AM-settled SPX only. A 9D/30D/3M slope therefore compares indices built from **different option
   universes**, so part of any measured slope is a contract-set artifact rather than a term-structure signal.
   Registered here rather than discovered later.

2. **`term_slope` is a volatility object, not a tail object, and the architecture doc has already rejected it.**
   `VIX3M/VIX − 1` is the term structure of the *risk-neutral variance* — the **same moment at two horizons**. It
   contains no asymmetry information whatsoever. It is a statement about the expected path of the second moment,
   which is exactly what the volatility signal's persistence/half-life descriptor already addresses, and
   `REGIME-SENSOR-ARCHITECTURE.md` lists "**VIX/VRP as a separate axis (collapses onto vol)**" among the
   sensors rejected for mechanism-duplication. Carrying it inside the tail signal would import the duplication
   hazard directly into the one signal whose whole justification is being distinct from volatility.
   > **Recommendation: REMOVE `term_slope` from this signal.** The tail signal's object is the asymmetry of the
   > risk-neutral density: **SKEW only**. The VIX term structure, if it is wanted anywhere, is a candidate
   > v-next descriptor for the *volatility* signal (where its mechanism actually sits), and would need its own
   > relevance-gate answer there given the 2009 start. `[recommended — Adam to confirm/override]`

   **The uncomfortable observation, recorded rather than buried.** The international-availability research
   (finding 11) turned up an inversion worth stating plainly: a **volatility term-structure** signal *could* be
   replicated out-of-hypothesis-sample today — STOXX publishes the full VSTOXX sub-index family free back to
   1999-01-04 (`V6I1` 1M through `V6I8` 24M, plus fixed-maturity `VSTX60/90/180/360`). A **risk-neutral-skewness**
   signal cannot be replicated anywhere. So the component that is internationally validatable is precisely the one
   that duplicates volatility, and the component that carries the distinct mechanism is precisely the one that
   cannot clear the OOS bar. That is an honest tension in this phase and it is not resolvable by choosing the
   easier component — doing so would trade the mechanism gate for a data convenience, which is the D-10 failure
   mode ("no signal designed around a desired conclusion"). The recommendation stands: keep the mechanism, accept
   the maturity cap.

3. **A real hole in the SKEW backfill: 2000-09-20 … 2000-09-29**, seven consecutive trading days missing, in the
   middle of the dot-com unwind. Twelve of the 50 total `skew` NaNs are pre-2011; this gap is seven of them.
   Registered as a known discontinuity, to be left as NaN and never interpolated.

4. **Calendar-alignment defect between the CBOE files.** 49 rows carry a `vix` value on dates where `skew` is
   absent, and spot-checking shows these are **US market holidays** (2022-06-20 Juneteenth, 2023-01-16 MLK,
   2024-07-04, 2024-11-28 Thanksgiving, 2025-01-09) on which the VIX history file prints a value that differs
   from both the preceding and following session. The union index in `tail_daily.csv` therefore contains rows
   that are not trading days, which is why 2022–2025 show 256–259 rows per year against a ~252-day calendar.
   Registered fix, before the look: **reindex to the SKEW trading calendar** (or an explicit NYSE calendar) and
   drop non-session rows. This is data hygiene, not a finding.

5. **Point-in-time status is two-tiered, and the distinction matters.** Individual option prices are never
   revised, so unlike the credit and funding signals there is no input-vintage reconstruction problem. But
   **SKEW was launched in 2011 and its 1990–2011 history is a retrospective backfill** — computed later, under a
   methodology that did not exist at the time, from an option universe a contemporaneous reader could not have
   processed. A backfilled value is not point-in-time-*available* even when its inputs are unrevised. This is a
   distinct defect from revision and is easy to miss. Registered as V2's dual read, and as one of the three
   grounds for the `research` ceiling.

6. **THE PUBLISHED HISTORY HAS ALREADY BEEN SILENTLY REVISED — CONFIRMED, and this is the most serious finding
   in this charter.** Cboe's 2011 SKEW white paper / FAQ published an all-time low of **101.09 (1991-03-21)** and
   an all-time high of **146.88 (1998-10-16)**. Today's `SKEW_History.csv` gives **101.31** and **146.22** on the
   *same dates*. The dates align; the values do not. Differences of 0.22 and 0.66 index points are far beyond
   rounding. The revision date is unestablished and the cause is unattributable from public documents.

   **This falsifies the assumption — mine and the kickoff's — that an options-implied series is vintage-free.**
   It is a restatement hazard of exactly the kind Phase 6 registered for the EBP, and it must be given the same
   seriousness. Two consequences:
   - **`assert_causal` cannot detect this.** The guard perturbs the *input* and checks the *construction*; here
     the leak is in the data itself, silently, between downloads. Passing the causal guard would give false
     comfort. Registered explicitly so nobody later reads a green test as covering this.
   - Any result computed from a given download is reproducible only against that download.

   > **Registered requirement, before any look: freeze a vintage-stamped local copy.** `data/processed/` acquires
   > a dated, sha256-recorded snapshot; the MANIFEST already carries the hash, and what is missing is the
   > **acquisition date** as a first-class field for this file. The one-look runs against the frozen vintage,
   > never a live re-fetch. Any later re-fetch is a **new vintage**, compared against the frozen one and disclosed,
   > never silently substituted. Forward vintage capture costs nothing and should start immediately.
   > `[recommended — Adam to confirm/override]`

7. **A further, larger recalculation is announced but not yet effective.** Cboe opened a consultation on
   **2025-05-20** proposing to replace the BKM-based measure with a 25-delta put/call ratio or differential, and
   on **2025-07-17** determined that modifications are appropriate — **without naming a replacement and without
   an effective date as of 2026-08-06**. The consultation states the index history **"would be recalculated."**
   So a full historical restatement is scheduled-in-principle and unscheduled-in-fact, and it may change the
   index's *definition*, not just its values — a 25-delta put/call differential is a different object from a BKM
   third moment, and V1's definitional-fidelity claim would not survive it. Registered as a known expiry date on
   this entire signal.

8. **Methodology break dates registered for V3.** **(a) 1990-01-02** — start of the retrospective backfill;
   **(b) the 2011 launch / first live publication** — the backfill-to-live boundary, which is also the V5
   sub-period split; **(c) 2014-10-06** — the addition of SPX Weeklys to the VIX-family constant-maturity
   interpolation. On the available evidence the Weeklys change was applied to **VIX but NOT to SKEW**, which is
   itself worth confirming, and there is a cheap registered test: measure the Weeklys effect on VIX against
   VIXMO (the monthly-only variant), then look for a matching break in SKEW at the same date. Absence of a
   matching break is evidence SKEW was left on the monthly expiry set. The V3 procedure is registered
   independently of which dates land: **test at the documented dates, and truncate rather than patch.**

9. **MEASUREMENT ERROR IS CONFOUNDED WITH THE INDEX LEVEL — it trends downward across the sample, and it
   directly attacks the rarity descriptor.** Aschakulporn & Zhang (2022, *Review of Derivatives Research* 25(3),
   233–281) establish that a risk-neutral *skewness* estimate with absolute error below 1e-3 requires strikes
   spanning ≥ ¾F to 4/3F with a step no coarser than **0.1% of the forward**. Because SPX strike intervals are
   quoted in dollars while the requirement is proportional, the constraint mechanically eases as the index rises:

   | date | SPX level | $5 strike step as % of forward | requirement (≤0.1%) |
   |---|---|---|---|
   | 1990-01 | ~350 | 1.43% | violated ~14× |
   | mid-1990s | ~600 | 0.83% | violated ~8× |
   | today | ~6000 | 0.083% | satisfied |

   Deep-OTM listings were also far sparser early, so the *coverage* condition fails independently of the step
   condition — and a third moment weights deep out-of-the-money strikes most heavily, which is precisely where
   the early chain is thinnest. *(The table assumes a uniform $5 interval; actual SPX intervals have narrowed
   near-the-money over time, which if anything strengthens the monotone-improvement point rather than weakening
   it.)*

   **Why this is worse than ordinary noise:** the error is not stationary, it **shrinks monotonically with the
   index level**, so it will manufacture a spurious trend in any long-sample percentile or rarity statistic. The
   expanding-window rarity descriptor — the core of what this signal reports — is directly exposed. An early
   sample that is biased in a *drifting* direction makes "how unusual is today versus history" partly an artifact
   of how coarse the 1990s strike grid was.

   > **Registered as a start-date restriction, not a footnote.** Pre-2000 SKEW is not treated as
   > measurement-grade. Recommended usable start: **2000-01**, with the live-publication era (2011) as the
   > conservative alternative that V5 will inform. Note the 2000-09 seven-day gap (finding 3) sits immediately at
   > the recommended boundary. `[recommended — Adam to confirm/override]`

   Root citation: **Jiang & Tian (2005, *RFS* 18(4), 1305–1342)** made the same truncation/discretization
   argument for model-free implied *variance*, and showed the errors grow with negative skewness and sparse
   listings — exactly the state SKEW is built to measure.

10. **Known critiques of SKEW's informativeness — registered as declared failure modes.**
    - **Cao, Ruan & Zhang (2020, *Journal of Futures Markets* 40(6), 945–973):** "the SKEW is very noisy and does
      not contain much important information."
    - **Bevilacqua & Tunaru (2021, *Journal of Financial Stability* 53, 100816):** only the **put-only** variant
      (SKEW−) carries signal; the aggregate index inherits an "over-optimistic bias" from the call side. The
      put-only construction would be the principled fix and it is **not available to us** — it requires raw
      strike-level SPX option data, which is paywalled. Registered as a known, unfixable limitation of the
      instrument rather than a v-next task.
    - **Not cited, deliberately:** the widely-circulated claim that "critics found SKEW cannot predict tail risk"
      has no traceable primary source, and Zhen & Zhang's "A Theory of the CBOE SKEW" is an unpublished working
      paper and is not cited as peer-reviewed evidence. Recorded so neither gets laundered into this charter
      later.

11. **International: no risk-neutral-skewness index exists for Japan or Europe. Definitive.** Researched
   2026-08-06:
   - **Japan.** Nikkei Inc. publishes the **Nikkei 225 VI** (VIX-family, calculation commenced 2010-11-19,
     back-calculated to 1989-06-12), but the free daily download is a rolling ~3.5-year window (2023-01-04
     onward) and the full history is not free. The complete Nikkei index catalogue contains exactly two
     volatility members — the VI and its futures index — and **no skew index**. No short/long-dated pair, so no
     term-slope analogue either. JPX's daily settlement file *does* carry per-strike settlement prices and
     implied volatilities (sufficient to compute BKM moments), but only for the current day — prior dates 404,
     so no historical backfill is constructible.
   - **Europe.** STOXX publishes the full VSTOXX family free back to 1999-01-04 (`V6I1`=1M … `V6I8`=24M, the
     fixed-maturity `VSTX60/90/180/360`, and V-VSTOXX vol-of-vol), but the May 2026 STOXX Strategy Index Guide
     contains **zero occurrences of "skew"** and there is no tail-risk index. Eurex's monthly VSTOXX commentary
     mentions a "skew" number, but it is editorial text describing a 95%-put vs 105%-call implied-vol spread —
     no ticker, no methodology document, no series. Strike-level Eurex chains require a signed Deutsche Börse
     agreement.
   - **Not substitutable.** VSTOXX term slope and V-VSTOXX are built from a **symmetric** variance-swap
     construction; they are convexity-adjacent, not risk-neutral skewness, and must not be presented as a skew
     proxy. `SX5EVBT` (EURO STOXX 50 Volatility-Balanced) is a strategy index, not a moment measure, and is
     doubly excluded — it also carries implementation content this repo does not touch.
   - **Consequence:** V6 is a pre-registered documented failure and the `research` ceiling is locked. See V6/R6.

**Declared starting point, measurement-validity axis.** `signal-output-spec.md` §1.1 anchors a signal needing
"options / high-frequency" data at **M or L**, and `REGIME-SENSOR-ARCHITECTURE.md`'s first-pass scorecard already
records Tail at **L (needs options/HF)**. The anchor's stated reason — "revised or not-yet-available data" —
turns out to apply after all, though not for the reason the anchor names: finding 6 means the *published history
is subject to recalculation*, and finding 9 means the early history carries materially larger estimator error.
Combined with the fact that the index is vendor-computed and not independently reconstructible from free data, I
now read the honest starting point as **L**, not M.
`[recommended — Adam to confirm/override]` *(An earlier draft of this charter argued for M on the grounds that
SKEW is free, final and never revised. Finding 6 falsified that premise; the change is recorded rather than
silently corrected.)*

---

## Cross-signal relationships (template attribute 4 / Q4.3)

Registered before the look as expectations to be characterized, not as findings.

- **Volatility (Phase 1.5, `production`) — the critical relationship.** Both are fast, both rise in stress, and
  they will co-move. The registered mechanistic distinction is two-fold: **moment** (asymmetry vs width) and
  **measure** (risk-neutral price vs physical realization). The relationship is tested at V4 with a kill
  condition, and the presentation rule is that the two readings are **always shown side by side and never
  combined** — the environment "calm, with protection at a decade-high price" is a distinct configuration that
  only survives if both numbers are preserved.

- **Funding stress (Phase 7) — related, and the reason NOT to fold them together.** There is a genuine
  mechanistic link running one way: **impaired intermediary funding reduces dealers' capacity to supply downside
  protection, which raises its price.** Funding stress is a plausible *cause* of moves in this signal. That is
  precisely the argument for keeping them separate: folding a candidate cause into the price it moves destroys
  the ability to observe them disagreeing, and creates a two-mechanism module in a framework whose gate is
  one-mechanism-per-signal (D-07). They also share no data (money-market spreads vs SPX option prices), no
  measure (physical quantity vs risk-neutral price), and no clock behaviour (funding is silent outside crises
  by its own kickoff's admission; this signal reads every day). **Recommendation: do NOT fold Phase 7 into this
  signal** — see §Open questions.

- **Credit / EBP (Phase 6).** The closest cousin: EBP is the *credit* market's price of risk after purging
  expected default; this is the *options* market's price of downside protection. Same conceptual family (a
  compensation-for-risk residual), different markets, different clocks (EBP slow and leading; this fast and
  coincident). Expect co-movement in stress; the interesting reading is divergence. Also the direct methodological
  precedent for V4's residual remedy.

- **Diversification / absorption (Phase 5) — a non-obvious confound worth registering now.** Index risk-neutral
  skew is not a pure fear measure: Bakshi, Kapadia & Madan (2003) show index densities are far more negatively
  skewed than individual-stock densities, and that the gap is driven by **systematic risk** — index skew embeds
  implied *correlation*. A rise in the priced index asymmetry can therefore reflect a rise in expected
  co-movement rather than a rise in the price of tail protection per se. That is the same object the absorption
  ratio measures on the physical side. Registered as a characterization task and a confound for V7.

- **Concentration (Phase 4).** Related through the same composition channel: index skew depends on the index's
  own structure, so a more concentrated index mechanically changes the relationship between constituent skews
  and index skew. Expected to be second-order relative to the correlation channel; registered for completeness.

- **Stock-bond correlation (Phase 2), valuation (Phase 3), crowding (Phase 8).** No mechanism links them
  directly; no relationship registered beyond common stress co-movement.

The **joint** reading across signals is deliberately deferred to Phase 10 per the architecture doc's sequencing
ruling, and nothing in this phase pre-empts it.

---

## Pre-registered analysis specification (to be frozen at sign-off)

- **Construction** — a new `scripts/tail_skew.py` exposing `build(frame)` on the shared causal spine, registered
  in `tests/test_reproducibility.py::CAUSALLY_GUARDED` and passing `assert_causal` before the one-look.
- **Data vintage** — the run executes against a **frozen, date-stamped snapshot** of `SKEW_History.csv`, captured
  and hashed before the look, with the acquisition date recorded in the MANIFEST. Never a live re-fetch. Required
  by §Data readiness finding 6 (confirmed silent revision).
- **Sample start** — **2000-01** recommended, not 1990, per V8 / finding 9. The 1990s strike grid violates the
  BKM third-moment discretization requirement by roughly an order of magnitude and the error is confounded with
  the index level. `[recommended — Adam to confirm/override]`
- **Primary object** — `S_t = (100 − SKEW_t)/10`, the risk-neutral skewness. Reported in its native sign.
- **Rarity** — `causal.expanding_percentile(S)`, plus a trailing-252-session fraction-more-negative lens, mirroring
  the volatility signal's two-lens rarity. No full-sample rank anywhere.
- **Trend** — change in the rarity percentile over the trailing 10 sessions, matching the volatility signal's
  drift window so the two are read on the same scale. `[recommended — Adam to confirm/override]`
- **Extreme flag** — at or beyond the 95th percentile of priced left-asymmetry, matching the volatility signal's
  extreme convention.
- **Calendar** — reindex to the SKEW trading calendar; drop the non-session rows identified in §Data readiness;
  never interpolate the 2000-09 gap.
- **Redundancy test** — V4(a) is the primary: a causal expanding-window regression of `S_t` on the volatility
  level and its log, with the two-term specification **fixed here** so no specification search can follow the
  results. The correlation diagnostic V4(c) carries no threshold and no reject condition.
- **Contingent descriptor** — the vol-conditioned residual of V4(a), promoted to the presented reading **only** if
  the raw level proves vol-spanned but the residual survives. Registered now, pre-committed.
- **`term_slope`** — excluded, per §Data readiness recommendation 2, pending Adam's ruling.
- **One look.** V1–V8 run once as a single frozen script writing to `results/`. Overnight cooling-off, then a
  separate dated sign-off of the results.
- **Level-0 record** — schema-validated against `scripts/signal_output_schema.py`; no status field, per Header.

---

## Open questions for Adam

1. **The reframe itself — the decisive one.** The monitored assumption moves from *"the return distribution is
   its normal shape"* (physical, unmeasurable from this data) to *"downside protection is priced normally"*
   (risk-neutral, measurable). Everything in this charter follows from that. If you want the original physical
   claim, **the honest outcome is DROP this phase**, because the realized-jump route that could measure it is
   excluded as data-gated. `[recommended — Adam to confirm/override: accept the reframe]`

2. **`term_slope`: remove from this signal?** It has no pre-2009 history, carries no asymmetry information, and
   the architecture doc already rejects VIX-family objects as a separate axis. `[recommended — Adam to
   confirm/override: remove; offer to the volatility signal as a v-next candidate, or drop entirely]`

3. **No ledger status.** Registering that this signal emits a reading plus rarity and **no**
   {intact | under-test | violated} label, because there is no mechanical boundary here as there is at
   correlation-sign-zero — only arbitrary percentile knobs, which is the failure the volatility reframe removed.
   `[recommended — Adam to confirm/override: no status]`

4. **Maturity ceiling `research`, registered before the look**, on the four grounds in the Header — note that
   ground (i) is now known to be *impossible*, not merely unattempted: no risk-neutral-skewness index exists for
   Japan or Europe at any tier. Phase 2 precedent.
   `[recommended — Adam to confirm/override: confirm the cap]`

4b. **Vintage freeze — a new requirement, and the assumption it falsifies matters beyond this phase.** The
   published SKEW history **has already been silently revised** (Cboe's own 2011 documentation gives 101.09 and
   146.88 as the all-time low/high; today's file gives 101.31 and 146.22 on the same dates), and a further full
   recalculation is announced-but-unscheduled. The one-look must run against a **date-stamped frozen snapshot**,
   and the MANIFEST needs an acquisition-date field. Note the general lesson: **`assert_causal` cannot catch
   this** — it guards the construction, not the data — so this is a hole in the repo's current reproducibility
   machinery, not just a quirk of this signal. Worth a look at whether any other vendor-sourced panel needs the
   same treatment. `[recommended — Adam to confirm/override: freeze the vintage before the look]`

5. **Phase 7 (funding) does NOT fold into this signal.** Related mechanism, opposite direction (funding stress is
   a candidate *cause* of the price of protection), but different data, different measure, different clock —
   and folding a cause into a price destroys the ability to see them disagree. Phase 7 should stand or fall on
   its own relevance gate. `[recommended — Adam to confirm/override: do not fold]`

6. **V4 was redesigned mid-draft and the retraction is disclosed, not smoothed over.** My first design made the
   redundancy trigger a correlation threshold (|ρ| ≥ 0.80). That was wrong: the literature puts corr(SKEW, VIX)
   near **−0.23 in levels**, so the trigger could never have fired — an unfalsifiable reject condition. The
   redesigned V4 makes the **vol-conditioned residual** the primary test (which is what Kozhan et al. actually
   ran) and attaches **no threshold to the correlation at all**. Flagging it because you should see that the
   first version would have quietly guaranteed a pass.
   `[recommended — Adam to confirm/override: accept the redesigned V4/R4]`

6b. **The V8 sample-start restriction: 2000-01, not 1990.** This throws away a decade of history including the
   1990s and costs the signal its longest rarity base. The reason is that the discretization error in the early
   BKM estimate is confounded with the index level, so the long sample would manufacture a trend in exactly the
   descriptor the observatory reports. The conservative alternative is 2011 (live-publication era only).
   `[recommended — Adam to confirm/override: 2000-01]`

7. **Measurement-validity starting point: L**, matching the framework anchor and the architecture doc's
   first-pass scorecard — but for different reasons than the anchor states (vendor-computation, the backfill, the
   2025 recalculation, and the strike-grid estimator error in the early history). An earlier draft argued for M;
   finding 6 falsified its premise. `[recommended — Adam to confirm/override]`

8. **Trend window of 10 sessions**, chosen to match the volatility signal so the two readings share a scale.
   `[recommended — Adam to confirm/override]`

9. **PROCEED or DROP — the fork, stated as a fork.** This signal can never reach `production`: the international
   bar is unmeetable, not merely unmet. The instrument is contested in peer review (noisy — Cao et al.; call-side
   biased — Bevilacqua & Tunaru; entangled with variance — Kozhan et al.), its published history has been
   silently revised once and is scheduled for another recalculation that may change its definition, and its early
   sample must be discarded for measurement-error reasons. Stage-0's stated scarce resource is research time.

   **Case for DROP:** a permanently-`research` signal built on a contested vendor index, with a real prior that
   R4 fires, is a legitimate thing to decline before spending the time. Declining is cheap now and expensive
   later.
   **Case for PROCEED:** the mechanism is sound and distinct, it is the observatory's only risk-neutral sensor,
   the data is free, and the framework explicitly renders `research` signals as human context — which is exactly
   what this is. A documented null from a properly pre-registered R4 is a legitimate output, not a wasted phase.

   `[recommended — Adam to confirm/override: **PROCEED at reduced priority** — build it after the remaining
   signals, tagged `research`, with the measurement caveats carried on every presentation of the reading, and
   with R4/R8 genuinely binding. If phase capacity is tight, this is the first phase to cut.]`

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/09-tail-signal/09-CHARTER-KICKOFF|09-CHARTER-KICKOFF]]

<!-- LINKS:END -->
