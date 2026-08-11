# Conditional Admission — proposed amendment to `signal-output-spec.md`

**Proposed spec version: v2.0 (BREAKING).** Two v1.0 rules are **removed**, not extended, which is why
this is a major bump rather than the additive v1.1 that added the Stage-0 gate.

**STATUS: DRAFT — NOT SIGNED, NOT FROZEN.** Nothing here is in force. `signal-output-spec.md` v1.1
governs until Adam signs this. Written 2026-08-11. No look spent, no empirical claim made.

---

## Why this exists

The v1.0 admission model evaluates each axis **alone**: does it answer an important question, and does
it add *unique* information beyond the already-admitted set. Redundancy with an admitted axis is grounds
for rejection.

The hypothesis now under investigation is that market information lives in the **conditional structure**
— how validated measurements move together, and how unusual their joint configuration is.

**These are incompatible, and not by a matter of degree.** An admission gate that screens on marginal
uniqueness will systematically remove exactly the interaction terms the conditional hypothesis says are
the point. Marginal redundancy does not imply conditional redundancy — XOR is the standing
counterexample: each input is marginally independent of the output, both together determine it.

The rejections that rested on marginal redundancy are therefore **unadjudicated under this criterion,
not overturned by it.** This amendment changes the rule; it re-opens no specific row.

---

## 1. The target problem, faced first

Conditional mutual information `I(X_i ; Y | X_-i)` requires a target `Y`. Three candidates, and two are
disqualified by the repo's own boundary:

| Candidate `Y` | Verdict |
|---|---|
| a future return | **Forbidden.** Makes this a prediction system. |
| a future value of another axis | **Forbidden.** Still a forecast, of a measurement instead of a price. |
| none | **Correct.** The object is the joint distribution itself. |

With no target, "conditional usefulness" is not information *about* anything. It is **whether the joint
distribution factorizes.** The relevant quantity is interaction information (co-information):

```
II(X_i ; X_j ; X_k) = I(X_i ; X_j | X_k) − I(X_i ; X_j)
```

Negative = redundancy. **Positive = synergy** — the case this amendment exists to permit.

> **Definition — conditional usefulness.** An axis is conditionally useful if the joint distribution of
> the admitted set is not reproducible by a model that omits it, judged against the registered null in
> §2 rather than against zero.

**Mandatory warning, carried from `MI-014`.** Total dependence rises mechanically when any correlated
variable is added, so an incremental-dependence statistic is positive almost automatically. That is the
Ψ trap in new clothing. §2 is the only thing standing between this criterion and admitting everything.

## 2. The registered null

**H₀: the joint is a Gaussian copula with the empirical marginals.**

By Sklar's theorem this separates the two things cleanly — each axis keeps its own distribution exactly,
and **only the dependence structure is under test.** Rejecting H₀ is a claim that the axes exhibit
dependence beyond linear/second-order: state-dependent coupling, tail dependence, asymmetric comovement.
That is what "conditional structure" has to mean if it means anything measurable.

Ladder, in increasing strength — **N1 is the registered bar**:

| Null | Grants | Rejecting it claims |
|---|---|---|
| **N1** Gaussian copula, empirical margins | all dependence is linear | dependence is state-dependent or tail-asymmetric |
| N2 single common factor + independent idiosyncratic | one driver | more than one axis of joint variation |
| N3 conditional independence given a K-dim latent | K drivers | irreducibly pairwise structure |

Null distributions come from **simulation at the actual sample size and autocorrelation**. No asymptotic
p-values — conditional-dependence estimators are positively biased exactly where data is thinnest.

## 3. The sample-size wall — a hard scope limit, registered in advance

The stock-bond axis uses a **registered 24-month window**. Consecutive monthly readings share 23 of 24
months. Over 63 years that is roughly **31 effective independent observations.**

A 4-dimensional dependence structure is not estimable from ~31 points.

> **Registered consequence: PAIRWISE INTERACTIONS ONLY.** Triples and higher are ruled out *in advance*
> on this data, rather than attempted and quietly abandoned. Admitting a triple requires new evidence
> that the effective sample supports it.

Second limit, equally binding: **crisis-conditional structure rests on n ≈ 4 events** (1987, 2000–02,
2008, 2020). Any claim of the form "the structure changes under stress" carries four observations. This
is the same shape as `MI-009`'s ~13 effective independent 10-year observations — which was sufficient to
strip a signal of its forward-return claim.

**Multiple testing:** with `n` axes there are `C(n,2)` pairs — 15 at n=6, tractable under FDR **only
because the pairs-only restriction is registered before looking.** Searching subsets is not.

## 4. Stability requirements for an interaction

| Requirement | Rationale |
|---|---|
| **Mechanism, written, binary** | The interaction space is combinatorially larger than the axis space; mechanism is the only thing constraining the search. **More necessary here than under v1.0, not less.** |
| **Sign stability across DISJOINT sub-periods** | Overlapping windows do not count |
| **Conditioning-set robustness** | An interaction visible given {A,B} but absent given {A,B,C} is not real. Tested against the **full** admitted set, never a convenient subset — the conditional analogue of cherry-picking controls |
| **Out-of-hypothesis-sample where it exists** | Available for volatility and stock-bond; **impossible** for tail (no international risk-neutral skew index at any tier); infeasible for credit. **This asymmetry is registered here rather than discovered later**: the OOS bar constrains which interactions can ever be admitted, unequally |

## 5. `CONDITIONAL` — a set-level status

v1.0 emits a per-axis tag in {production, research, rejected}. That is a property of the axis **alone**
and structurally cannot express "weak by itself, load-bearing with X."

**Admission becomes a property of a SET, not of an axis.** The record splits:

- **Axis-level (unchanged):** mechanism pass/fail · measurement validity · causal/PIT compliance. These
  genuinely are properties of the axis alone.
- **Set-level (new):** conditional contribution given the *named* rest.

New status **`CONDITIONAL`** — admitted only as part of a named set, never standing alone, with the set
recorded in the row.

> **Anti-loophole clause, load-bearing: if the set changes, the admission is VOID and must be
> re-evaluated.** Without this, `CONDITIONAL` becomes a way to admit anything by pairing it with
> something else.

## 6. Disposition of every v1.0 rule

**SURVIVES UNCHANGED**

- **The binary mechanism prerequisite gate.** The strongest part of v1.0 and more load-bearing here.
- **Causal / point-in-time discipline** — `assert_causal`, `available_at`. Orthogonal to this question.
- **Measurement validity** as a graded axis.
- **Preregistration · one look · cooling-off · dated sign-off.** The interaction space is where multiple
  testing bites hardest; these get stricter in practice, not looser.
- **The HARD BOUNDARY.** Level 2 output is a state description — *"these assumptions are in this
  configuration, and it is this unusual historically"* — never a direction, never an instruction.

**MODIFIED**

- *Investment usefulness* — "unique information" currently means **marginal** uniqueness. Becomes
  **conditional contribution given the admitted set.**
- *Evidence maturity* — assessed for the **interaction**, not only the axis. The OOS component becomes
  set-dependent per §4.

**REMOVED — these are why this is v2.0**

1. **Rejection on marginal redundancy alone.** The `Rejected / redundant` list in
   `REGIME-SENSOR-ARCHITECTURE.md` was built on it. Those rows become **unadjudicated**, not admitted.
2. **The non-compensatory rule** ("a high score on one axis never offsets a low one"). Under a
   conditional criterion, low *marginal* usefulness is precisely what conditional contribution is meant
   to offset. The rule forbids the thing the hypothesis requires. **Note what this costs:** v1.0's
   non-compensatory structure was a real guard against a strong axis carrying a weak one. §4's stability
   requirements and §5's void-on-set-change clause are what replace it, and they are less proven.

## 7. The research sequence this criterion serves

```
STEP 1  CRITERION       methodology — this document
STEP 2  EXISTENCE       does the joint distribution reject H₀?
STEP 3  MEANING         do those configurations correspond to observable market conditions?
STEP 4  TRADEABILITY    algo-trading-bot only, via the §3.6 admission gate
```

> **Contamination guard on Step 3, registered now.** "Does the joint state *correspond to* sector
> dispersion" is one word from "does it *predict* sector dispersion." The moment it is lead-lag it is a
> forecast and inherits the full apparatus — persistent regressors, overlapping windows, effective
> sample size, Stambaugh. **Step 3 is CONTEMPORANEOUS description unless a separate charter explicitly
> authorises a forecast claim.** This is the exact slide that cost `MI-009` its forward-return claim.

## 8. First test — of the criterion, not of an axis

**Dispersion**, `D_t = σ̄_t²(1 − ρ̄_t)`.

Chosen because its marginal redundancy is an **exact algebraic identity** and it is computable from data
already on disk with no new fetch. That makes it the hardest available case in both directions:

- **No conditional content found** ⇒ the criterion has teeth and has not degenerated into "admit
  everything." That is the falsification the amendment needs.
- **Conditional content found** ⇒ existence proof in the hardest case available.

Either outcome is informative, which is the property a first experiment should have.

**This is a test of the criterion. Dispersion is not thereby a candidate axis, and passing does not admit
it.**

---

## Open items before signing

1. Whether `CONDITIONAL` belongs in the observation contract's `maturity` enum, or stays purely a
   ledger/framework concept. The contract is semver'd, vendored and sha256-pinned in two consumers — a
   change there is a three-repo operation and should not be made casually.
2. Whether removing the non-compensatory rule needs a compensating guard beyond §4 and §5.
3. Adam's dated sign-off. Until then `signal-output-spec.md` v1.1 governs.
