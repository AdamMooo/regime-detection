# Research Charter (DRAFT) — Diversification / Absorption Signal (Phase 5)

**DRAFT — NOT FROZEN, NOT SIGNED.** No look has been spent. No PCA has been run, no absorption ratio
computed, no statistic about whether the signal works or leads has been produced. Everything below is a
*registered intention*. Data inspection was limited to coverage: dates, row counts, column names,
missingness, file vintages.

**Recommended verdict up front: DROP.** The Stage-0 gate passes on mechanism and (narrowly) on unique
information, but fails on **live readability** — see §Stage-0 G3′ and §6 Data readiness. The whole charter
is written out anyway so that (a) the reasoning is auditable, and (b) if Adam overrides the recommendation
or sources a lower-latency cross-section, the protocol is ready to freeze without re-deriving it.

**Charter v0.1-draft** — filled against framework template **v1.1** (`research-charter-template.md`).

---

## Header (draft)

- **Signal name** — Diversification / correlation compression (absorption ratio)
- **Assumption monitored** — *"diversification within the equity cross-section is intact — returns are not
  compressed onto a small number of common factors."*
- **Native clock / frequency** — slow (a 500-day trailing covariance; the reading moves on a multi-week scale).
  **Publication clock: ~2 months behind, see §6.**
- **Maturity tag** — DERIVED, unset. Ceiling registered in advance: **`research`. `production` is not
  available to this phase** on the current data (matched cross-region panel starts 1990-07, is a different
  cross-sectional object from the source paper's, and arrives ~2 months stale).
- **Investor question** — *"Is the market's cross-section compressing onto fewer common factors, how unusual
  is that compression versus its own history, and does it register before the volatility barometer moves?"*
- **Charter/spec version** — v0.1 (DRAFT)
- **Charter dated** — drafted 2026-08-06. **NOT signed. NOT frozen.**

**Charter-first status: clean.** Nothing has been implemented. There is no `scripts/absorption.py`, no
US matched panel, and no result artifact. This is a genuine pre-registration.

---

## Stage-0 Relevance Gate (default = NO)

- **G1 — what important investment question does this signal answer?**
  Whether the diversification an investor believes they have across the equity cross-section is real right
  now, or whether returns have compressed onto a few common factors so that idiosyncratic differences no
  longer separate outcomes. **PASS.**

- **G2 — why is that question important to long-term investors?**
  Because diversification is assumed, not measured. A tightly-coupled cross-section propagates shocks
  further and faster (Kritzman, Li, Page & Rigobon 2011), so the same nominal breadth carries different
  fragility at different times. The failure mode is silent: compression can build while realized volatility
  is still low. **PASS.**

- **G3 — information NOT already available from the existing signals?**
  **PARTIAL, and thin — this is the gate's weak point.** On an equity-only cross-section the absorption
  ratio is close to a monotone restatement of average pairwise correlation. Under exact equicorrelation ρ
  across N standardized series, the leading eigenvalue is λ₁ = 1 + (N−1)ρ and the total is N, so
  AR₁ = [1 + (N−1)ρ] / N — **affine in ρ̄**. And ρ̄ is a *component* of index volatility:
  σ²_index ≈ σ̄² [ ρ̄ + (1−ρ̄)/N ]. The admitted volatility signal already measures the left-hand side.
  So the genuinely non-redundant content is only: (i) the *shape* of the eigenvalue spectrum beyond PC1
  (concentration across K components, not one scalar ρ̄), and (ii) **timing** — whether compression
  registers before magnitude does. Adam's 2026-08-05 scoping ruling (**NARROW keep, lead-only**) is the
  correct reading of this and is carried into the charter as the admission bar, not softened.

- **G3′ — [ADDED, and it is the reason for the DROP recommendation] can the unique information be READ?**
  **FAIL.** The unique content is a lead of roughly one month (the source paper's claim). The only data
  source that gives a *matched* cross-section for the US, Japan and Europe publishes with a **~2-month
  lag** (§6, evidenced from three independent builder runs in late July 2026 all terminating 2026-05-29).
  A ~20–40 day lead read from data that is ~40–60 days stale is **cancelled before it can be observed**.
  Even a fully successful validation yields a historical measurement finding, not a live observatory
  reading. Under D-19 (default NO; the scarce resource is research time and the investor's attention),
  a signal that cannot reach the observatory on a full pass should not consume the research time.

- **G4 — leave-one-out: would removing this signal make the observatory meaningfully less informative?**
  **Only if the lead is real AND readable.** If the lead fails, what remains is a second reading of the
  correlation component of the volatility axis — a duplicate, which D-19 rejects explicitly. If the lead
  holds but arrives stale, what remains is a historical description with no live content. **FAIL as
  currently sourced; conditional PASS if a low-latency matched cross-section is obtained.**

- **G5 — strong theoretical/empirical prior the relationship exists?**
  **Moderate.** Kritzman, Li, Page & Rigobon (2011) is real, cited, and mechanistically motivated; the
  eigenvalue-concentration object is standard (Laloux, Cizeau, Bouchaud & Potters 1999 on the spectrum of
  financial correlation matrices; Bai & Ng 2002 on how many factors are actually there). But the *lead*
  claim rests on an in-sample, US-only, small-event-count event study, and the prior for a US-only lead
  generalizing is **materially lowered by this repo's own precedent**: the sector-dispersion lead was
  −40d in the US and reversed sign out-of-sample (Japan +154d, Europe +94d), and was closed 2026-07-29.
  This candidate is the same *shape* of claim on a closely related object.

### Gate verdict

**CONDITIONAL PASS on mechanism and (narrow) uniqueness · FAIL on readability (G3′/G4) ⇒ recommended
DROP.** If Adam overrides, the correct form of the override is *"proceed for the historical measurement
finding, accepting that `production` is unreachable"* — not *"proceed and we'll figure out latency later."*
The rest of this document is the protocol for that override.

---

## The six charter questions

### 1. What question does the signal answer?

What fraction of the cross-sectional variance of the market's constituent return series is absorbed by the
leading K principal components of their trailing covariance, how unusual that fraction is against its own
history, and whether it is rising or falling. It is a **structural** reading (how concentrated is the
covariance spectrum), not a magnitude reading (how large is the variance).

It answers **nothing about returns.** It does not say what compression implies, how long it will last, or
what follows it.

### 2. What market assumption does it monitor?

**"Diversification within the equity cross-section is intact."** Ledger mapping, registered before the look
and subject to the **D-02b continuous-first rule** established in Phase 2:

> The reading is the **continuous absorption ratio plus its rarity**. Any {intact | under_test | violated}
> label is a DERIVED view of that number and **may never be emitted, presented, or stored without the
> number beside it.** No `state` field without `ar` and its expanding percentile.

Banding is deliberately left to the presentation layer and is **not** registered here as a threshold with
mechanical meaning — unlike stock-bond correlation, where sign zero is a real mechanical boundary, the
absorption ratio has **no privileged level**. It is bounded in [K/N, 1] and its informative content is
entirely relative to its own history. Registering a level threshold would be exactly the arbitrary-knob
error the volatility reframe removed.

### 3. What mechanism supports it — why does it survive being known?

**Registered mechanism: risk-management channel via covariance-spectrum concentration.**

*The structural claim.* When a larger share of cross-sectional variance loads on few common factors, the
system has fewer independent channels through which a shock can be absorbed. The same shock therefore
propagates to more of the cross-section, and the diversification that the breadth of the cross-section
appears to provide is not there. This is the tight-coupling argument of Kritzman, Li, Page & Rigobon
(2011) — standard-literature terms: *absorption ratio*, *systemic risk measure*, *eigenvalue concentration
of the return covariance matrix*, *approximate factor model*.

*Why it survives being known.* It is not a mispricing and not a premium. It is a measured property of the
current covariance matrix. Knowing that the cross-section is tightly coupled today does not untie it —
the coupling is produced by common sensitivity to shared shocks (macro, liquidity, factor crowding), not by
anyone's ignorance of the measurement. Nothing is arbitraged away by publishing the number. This is a
**risk-management** channel; there is **no risk-premium claim** here and none is made.

*Where the mechanism is weaker than it looks — stated honestly.* The same tight-coupling mechanism is
partly what the volatility signal already measures (see G3: ρ̄ is a component of σ_index). So the mechanism
gate, which usually carries the admission burden, **cannot carry it alone here** — a mechanism shared with
an admitted signal does not establish marginal information. The burden shifts almost entirely onto the
**temporal** claim: does the structural reading move *before* the magnitude reading. That is why the
lead-only scoping is right, and why its failure must be a kill rather than a demotion.

*Prior art on the estimator, not the claim:* the number-of-components choice is the known weak point
(Bai & Ng 2002; Marchenko–Pastur / random-matrix bounds separating signal from sampling noise in
correlation spectra, Laloux et al. 1999). This is registered as an estimator-robustness axis (V2), not
as something to be tuned after seeing results.

### 4. What evidence would validate it?

Registered as an **ordered, non-compensatory** sequence. V3 is a *necessary screen* that can kill the
signal cheaply before the lead is examined; V4–V6 are the decisive bars. **A pass on any later bar cannot
rescue a failure on an earlier one, and no bar can be traded off against another.**

- **V1 — causal / look-ahead-free construction.** `absorption.build(panel)` passes
  `causal.assert_causal` (`scripts/causal.py:99`) on each region's panel: every reading at or before an
  arbitrary cut is bit-identical when all data after the cut is replaced with noise. Registered under
  `tests/test_causal.py` and added to `CAUSALLY_GUARDED` in `tests/test_reproducibility.py:118` so it
  cannot be skipped by omission. Built from return series only ⇒ **no macro vintage surface** (§(a));
  the publication-lag hazard is separate and is a *latency* issue, not a look-ahead issue (§6).

- **V2 — estimator robustness (the knob check).** The qualitative reading (level percentile, direction,
  and the rarity of the current compression) must not flip across the registered grid:
  window W ∈ {250, 500, 750} trading days × components K ∈ {3, 5, 7} × matrix ∈ {covariance, correlation}.
  The whole grid is computed and reported **in the single look**; the primary cell (W=500, K=5,
  covariance) is named in advance below. This mirrors the volatility signal's V2, which caught a real
  estimator artifact before a claim was made.

- **V3 — dissociation from volatility (NECESSARY SCREEN, runs before the lead test).** The absorption
  reading must be numerically separable from the volatility reading in every region:
  (a) |corr(AR level, EWMA vol level)| < 0.90 **and** |corr(AR percentile, vol percentile)| < 0.90; and
  (b) the **low-volatility / high-absorption quadrant must be materially populated** — at least **5%** of
  valid days in each region with vol percentile < 0.50 and AR percentile > 0.75.
  *[recommended — Adam to confirm/override the 0.90 and 5% thresholds]*
  (b) is the load-bearing half: it is the operational form of "a market can be calm and fragile," which is
  the only reason this signal is being considered. If the quadrant is empty, absorption is a relabelling
  of volatility and the phase ends here.

- **V4 — the lead exists (US, hypothesis sample).** Definitions frozen below in §Lead-test specification.
  Bars, all three required: median lead **L_AR ≥ 10 trading days**; **coverage ≥ 0.50** of qualifying
  turbulence onsets are preceded by a ΔAR trigger inside the 126-day pre-window; and the observed median
  L_AR exceeds the **95th percentile of a circular-block-bootstrap null** (block 63d, B = 2000, fixed
  seed) built by resampling the ΔAR series against the *fixed* onset dates. The bootstrap preserves the
  trigger frequency, so it automatically controls for "it triggers all the time."

- **V5 — the lead is INCREMENTAL to volatility (the confound bar).** The identical event/lead statistic is
  computed for a **volatility control**: the same standardized-shift transform applied to EWMA volatility
  instead of AR. Registered bar: **ΔL = median(L_AR) − median(L_vol) > 0**, with ΔL above the 95th
  percentile of a paired bootstrap null, **and** AR coverage ≥ vol coverage. This is the confound-check
  required by §(c) and it is the single most important bar in the document: without it, "AR leads
  turbulence" is satisfied by any transform of volatility that is smoother than the event definition.

- **V6 — out-of-hypothesis-sample generalization (the dispersion bar).** Identical construction, identical
  panel object, identical statistic on **Japan and Europe** via the shared harness. Required in **both**
  adequately-powered regions: median L_AR > 0 (correct sign); coverage ≥ 0.50; median L_AR within
  **[⅓×, 3×]** of the US median (an order-of-magnitude band, registered ex ante); and ΔL > 0 (V5's
  incremental bar must also hold out-of-sample). *[recommended — Adam to confirm/override the [⅓×, 3×]
  band]*

- **V7 — power pre-check (runs BEFORE any lead statistic is interpreted).** Count qualifying turbulence
  onsets per region on the common window. **A region with fewer than 8 qualifying onsets is declared
  UNDERPOWERED and its result is reported as "insufficient coverage" — never as support and never as
  refutation.** Registered in advance for the same reason Phase 2 registered one: a noisy lead estimate
  from 4 events must not become either a claim or a kill after the fact.
  *[recommended — Adam to confirm/override the minimum of 8]*

- **V8 — reconstitution artifact check.** The constituent series are re-sorted annually at end-June. If AR
  discontinuities cluster in the late-June / early-July window beyond chance, the reading is partly an
  artifact of the data construction rather than of the market. Reported alongside V2.

### 5. What would falsify it?

Each reject condition names the bar it trips. **R2, R3 and R4 are kills, not demotions** — there is
deliberately no path by which a failed lead leaves behind "well, it still describes something." What it
would still describe is average correlation, which the volatility signal already contains.

- **R1 — look-ahead leak.** `assert_causal` fails, or any construction step is found to use a full-sample
  mean, a full-sample standardization, or a non-trailing normalizer. Fatal. (Trips V1.)

- **R2 — not dissociable from volatility. KILL.** Either correlation bound in V3(a) is breached, or the
  low-vol/high-AR quadrant in V3(b) is essentially empty. The signal would be a second reading of the
  volatility axis and D-19 rejects duplicates. (Trips V3.) *The lead test is not run in this case — the
  phase closes here.*

- **R3 — the lead is not incremental to volatility. KILL.** ΔL ≤ 0, or ΔL inside the bootstrap null, or
  AR coverage < vol coverage, in the US. "AR leads turbulence" would then be true only in the sense that
  any smoothed volatility transform leads turbulence. (Trips V5.)

- **R4 — the lead does not generalize. KILL. THE DISPERSION BAR — non-negotiable, no reinterpretation.**
  If the median lead **reverses sign (L_AR ≤ 0) in either Japan or Europe** while that region is
  adequately powered, the signal is closed as a US artifact **on the day the result is read**, exactly as
  the sector-dispersion lead was closed on 2026-07-29 (US −40d, Japan +154d, Europe +94d). No follow-up
  specification, no window search, no "the international cross-section is different so the test was
  unfair" — the panel-mismatch objection is *pre-empted* by the matched-panel prerequisite in §6, which
  is precisely why that prerequisite is mandatory before the look rather than optional.
  A lead that is positive in both regions but **outside the [⅓×, 3×] band** is likewise a failure of V6
  and is recorded as **KILL**, not as partial support. (Trips V6.)

- **R5 — estimator artifact.** The qualitative reading flips across the V2 grid — in particular, if the
  lead exists on the **covariance** matrix but vanishes on the **correlation** matrix, the effect is
  driven by variance *scale* rather than covariance *structure*, i.e. it is volatility again. **KILL** in
  that specific case; re-specify with disclosure in the milder cases. (Trips V2.)

- **R6 — underpowered everywhere.** Fewer than the registered minimum of qualifying onsets in every
  region. The phase closes as **NOT ADMITTED — INCONCLUSIVE**, which under the Stage-0 default (NO) means
  the signal does **not** enter the observatory. The difference between INCONCLUSIVE and KILL is only
  whether purchased or re-sourced data could revive it; it is **not** a softer form of pass. (Trips V7.)

- **R7 — construction artifact.** AR jumps cluster at the annual reconstitution date. Re-specify with
  disclosure, or drop the affected robustness cell. (Trips V8.)

- **R8 — latency makes the reading unobservable.** *(Standing, not a test outcome.)* Independent of every
  result above: if the measured lead is shorter than the data's publication lag, the signal cannot be
  read live and cannot reach `production` regardless of how well V1–V8 go. This is known **before** the
  look (§6) and is the basis of the DROP recommendation; it is registered here so that a strong result
  cannot later be used to quietly drop the caveat.

### 6. What does it explicitly NOT claim?

This signal reports a measured absorption ratio, its standardized shift, its rarity against its own
history, and — if and only if the registered bars pass — the historically observed temporal ordering
between compression and turbulence onsets. It names the assumption *"diversification within the equity
cross-section is intact"* and **STOPS**.

It does **not** forecast returns, drawdowns, or crashes; a temporal-precedence description of past
episodes is not a forecast and must never be presented as one. It does not claim compression *causes*
turbulence. It does not say how long compression will persist, or what follows it. It carries no
portfolio, allocation, or exposure concept; no weight, sleeve, tilt, cash, position sizing, or risk
budget; no overweight or underweight; no buy or sell; no risk-on / risk-off summary; and no composite or
single-number market-safety score. Those concepts do not exist in this repo, and this signal introduces
none of them. What a compressed cross-section means, and what if anything to do about it, is the human's
judgment in a separate system.

---

## The causal PCA specification (registered — this is where look-ahead leaks live)

PCA is a *fitting* procedure. A single full-sample eigendecomposition would push the future covariance
into every historical reading and produce a beautiful, worthless signal. The following is frozen.

**Panel.** For each region, a matrix R of N = 25 daily constituent return series (the French 5×5 size ×
book-to-market sorts; see §6 for the matched-panel prerequisite). Constituent series only — the market
aggregate is **not** included in the panel (including it would put the common factor in twice).

**Rolling covariance, trailing only.** At each date t:

1. Take the trailing W = 500 trading days of returns, rows t−W+1 … t inclusive. Nothing after t is
   touched, ever.
2. De-mean **within that window** (the window mean, never a full-sample or expanding mean).
3. Σ̂_t = the W×W-sample covariance of the de-meaned block (25×25). For the correlation variant,
   standardize each column by **its own trailing-window** standard deviation — never a full-sample σ.
4. Eigendecompose with `numpy.linalg.eigh` (symmetric solver; deterministic given the input), sort
   eigenvalues **descending** explicitly (`eigh` returns ascending).
5. AR_t(K) = Σ_{k=1..K} λ_k / Σ_{k=1..N} λ_k, with **K = 5 = N/5** (the source paper's convention:
   10 of 51 series). Primary cell: **W = 500, K = 5, covariance matrix.**

**Refit cadence: every trading day.** A 25×25 decomposition on 500 rows over ~9,000 dates is trivially
cheap, so there is no computational excuse for a coarser refit — and a coarse refit would introduce a
stale-reading artifact that is hard to distinguish from a lead. Registered as **daily refit, full
re-decomposition, no incremental/online update** (an online eigen-update carries state across the cut and
would complicate the `assert_causal` proof for no benefit).

**Eigenvector sign and ordering stability across refits.** Two known instabilities, and why neither
touches the registered reading:

- **Sign.** For any eigenvector v, −v is an equally valid eigenvector, and solvers flip signs arbitrarily
  between refits. **AR is a function of the eigenvalue spectrum only** (a ratio of sums of λ), so it is
  exactly invariant to eigenvector sign. No sign anchoring is required for the v1.0 reading.
- **Ordering.** When λ_k ≈ λ_{k+1}, their order can swap between adjacent refits. AR(K) is a **sum** over
  the top K, so a swap *within* the top K, or *within* the tail, leaves AR unchanged; only a swap across
  the K/K+1 boundary matters, and there the two eigenvalues are near-equal by construction, so the effect
  on AR is second-order. Registered as a documented property, and covered empirically by the K ∈ {3,5,7}
  robustness axis.
- **Consequence, registered:** **v1.0 emits no eigenvector composition** — no loadings, no "which factor
  is dominant." The moment composition is reported (a plausible v-next), sign anchoring becomes mandatory
  (fix the sign so that the sum of the loadings is positive) and near-degenerate ordering must be handled
  explicitly. Registering the restriction now prevents that being discovered after a claim exists.

**The standardized shift ΔAR** (the source paper's leading-indicator transform), all components trailing:

> ΔAR_t = [ MA₁₅(AR)_t − MA₂₅₂(AR)_t ] / sd₂₅₂(AR)_t

15-day short mean, 252-day long mean, denominator = the standard deviation of AR over the same trailing
252 days. Trigger threshold **ΔAR ≥ +1.0** (the source paper's one-standard-deviation shift). Every one of
these is a trailing window; a full-sample sd here would be the classic leak.

**Rarity.** `causal.expanding_percentile` on AR and on ΔAR — expanding, not full-sample rank.

**How `assert_causal` is satisfied.** `absorption.build(panel: pd.DataFrame) -> pd.DataFrame` takes the
region's 25-column return frame and returns `[ar, ar_pctile, delta_ar, delta_ar_pctile]`. The guard
(`causal.py:99`) replaces every row after a cut with N(0, 5σ) noise per column and requires every output
row at or before the cut to be **bit-identical**. The four constructions that would fail it, and are
therefore forbidden by name in this charter: (i) full-sample or expanding de-meaning inside the covariance
step; (ii) full-sample standardization in the correlation variant; (iii) a centred/two-sided moving
average in ΔAR; (iv) a full-sample sd in the ΔAR denominator. The burn-in — W + 252 days before ΔAR is
defined — is emitted as NaN, never back-filled.

**Registration.** Add `absorption` to `CAUSALLY_GUARDED` (`tests/test_reproducibility.py:118`) with a case
in `tests/test_causal.py`; the reproducibility test fails on any new `build()` that is not registered, so
this cannot be skipped by omission.

## Lead-test specification (frozen definitions — no post-hoc dating)

**Turbulence onsets (the evaluation events).** Per region, from that region's own market return series
(`*_market_daily.csv`), never from the panel used for the PCA:

- τ_t = trailing 21-day realized volatility (`causal.realized_vol`).
- q_t = `causal.expanding_percentile(τ)`.
- An **onset** at t if q_t ≥ 0.90 and q_s < 0.90 for all s ∈ [t−126, t−1] (a 126-day refractory period, so
  one long episode is one event).

Onsets are **ex-post evaluation labels**, used only to evaluate the signal; they never enter the AR
construction, so their use is not a look-ahead violation. The definition is frozen here, before the look.

**Why volatility onsets and not drawdowns.** The registered claim is a *sensor-timing* claim — does the
structural instrument register a change before the magnitude instrument does — not a claim about losses.
Dating events on drawdowns would make the target a return outcome and would drift toward the prediction
goal three closed nulls already killed in this repo. A drawdown-dated replication (peak-to-trough ≥ 15%)
of the source paper's own event definition **is reported for fidelity but is explicitly NOT a bar: a
positive drawdown-lead result cannot rescue a failed V4/V5/V6.**

**Lead statistic.** For onset t*: the trigger date a* = the **first** date in [t*−126, t*] with
ΔAR ≥ +1.0. Lead L_i = t* − a* in trading days. If no trigger occurs in the pre-window the episode is
**unsignalled** — recorded, counted against coverage, and never silently dropped. Per region report:
median L over signalled episodes, coverage = signalled / total onsets, and the count of triggers not
followed by an onset within 126 days (false-alarm count, descriptive).

**Volatility control (V5).** Identical transform and identical trigger rule applied to
`causal.ewma_vol(λ=0.94)` in place of AR, evaluated against the same onsets.

**One look.** V1–V8 run once, as a single frozen script writing to `results/`. No re-run to a preferred
answer. Any positive claim requires overnight cooling-off and Adam's separate dated sign-off of the
*results*.

---

## Data readiness — verified against actual files

Verified from `data/processed/MANIFEST.csv` and by loading the panels for shape, span and missingness
only. **No PCA, no absorption ratio, no lead statistic.**

| panel | rows | columns | span | missingness |
|---|---|---|---|---|
| `japan_assets_daily.csv` | 9,370 | 25 (`p0`…`p24`) | 1990-07-02 → 2026-05-29 | **none** |
| `europe_assets_daily.csv` | 9,370 | 25 (`p0`…`p24`) | 1990-07-02 → 2026-05-29 | **none** |
| `industry10_daily.csv` (US) | 26,253 | 10 | 1926-07-01 → 2026-05-29 | none |
| `industry48_daily.csv` (US) | 26,253 | 48 | 1926-07-01 → 2026-05-29 | structural: 4 series missing 10,420 rows, `Hlth` 11,903; **complete cases only from 1969-07-01** (14,350 rows) |
| `assets_daily.csv` (US multi-asset) | 26,190 | 17 | 1926-09-17 → 2026-05-29 | `bond10_ret` 10,146, `gold_ret` 19,736 NaN; **complete cases only from 2000-08-31** (6,408 rows) |
| `*_market_daily.csv` (event dating) | US 26,190 / JP 9,370 / EU 9,370 | `mkt_ret` | as above | none |

### Finding 1 — there is NO matched US cross-section. This is the dispersion trap, and it is a hard prerequisite.

The international panels are 25 size × book-to-market sorts. The US panels are 10- or 48-industry sorts.
**Running the US read on industries and the international read on size/BM sorts would repeat the exact
error that made the dispersion-lead failure ambiguous** — the memory records the cause explicitly: the US
feature dispersed across industry series, the international proxy across size/BM series, "a related but
different cross-sectional object." A generalization failure under object mismatch is uninterpretable, and
a success would be luck.

**Registered prerequisite, mandatory before the look and before the charter can be frozen:** build
`data/processed/us_assets_daily.csv` — the US 5×5 size × book-to-market daily sorts, from the French
library file whose name follows the same convention as the Japan/Europe zips already hard-coded at
`scripts/build_intl_panel.py:63`, i.e. `25_[…]_5x5_Daily_CSV.zip` (the elided token is one the HARD
BOUNDARY bans, hence the elision; resolve it from the library index at build time). Same builder shape,
same gates I1–I4, plus a new gate asserting the three regions carry the **same 25 sorts in the same
column order**. This is a data build with no economic claim and spends no look. Confirmed available:
the US 5×5 daily file exists in the French library and the international daily files are the two already
in use.

**Consequence:** the cross-region comparison window is **1990-07-02 → 2026-05-29** for all three regions,
minus the W=500 + 252 burn-in, i.e. an effective start around **mid-1993**. The US's 60 extra years of
industry history may be reported as a *domestic descriptive* read only and is **not** evidence for any
registered bar — the bars are evaluated on the common window so the US is not advantaged by sample length.

**Confirmed unavailable:** the French library publishes **no international industry sorts at any
frequency**. The source paper's own object (51 US industry series) therefore **cannot** be replicated
out-of-sample. The matched object we can build (25 size × book-to-market sorts) is a *different and
weaker* absorption object than the paper's: the 5×5 sorts are all long-equity and share a dominant common
factor by construction, so the spectrum is compressed toward a saturated AR with less room to vary than a
51-industry cross-section. **This is a registered measurement-validity limitation, declared before the
look**, and it caps measurement validity at **M** at best.

### Finding 2 — publication latency (~2 months) cancels the claimed lead. This is the DROP argument.

All three region panels terminate **2026-05-29**. Three independent builder runs on three different dates
in late July 2026 (`market_daily.csv` 07-22, `europe/japan_*` 07-29, `industry*` 07-30 — file mtimes)
each terminated at that same date, so the ~2-month gap is the **source's** publication lag, not a stale
local copy. The volatility signal has a low-latency escape (the OHLC panels run to 2026-07-29/30); **for a
cross-section there is no such substitute in this repo.**

The claimed lead is ~1 month. The data arrives ~2 months late. **The lead is negative by the time it can
be read.** Nothing in the validation protocol can fix this, which is why it is registered as R8 (a
standing condition, not a test outcome) and why `production` is unavailable regardless of results.

### What cannot be tested, and what that caps maturity at

1. **Any pre-1990 international behaviour** — no international cross-section exists before 1990-07. The
   1987 crash, the 1970s inflation regime, and the 1990 Japan unwind are outside the common window.
2. **The source paper's own object out-of-sample** — no international industry sorts exist (Finding 1).
3. **Live readability** — cannot be tested, and is known to fail (Finding 2).
4. **Event count** — the common window is ~33 years per region; the number of qualifying turbulence
   onsets is the binding constraint on the lead estimate, which is why V7's power pre-check runs first.

**Registered maturity ceiling for this phase: `research`. `production` is not available and must not be
claimed**, on three independent grounds (object mismatch with the source; 1990-start common window;
publication latency). Registered before the look for the same reason Phase 2 registered its ceiling: a
strong result is exactly when the cap is most tempting to drop.

### Vintage hazards

- **No macro vintage surface** — the construction is return series only (§(a)).
- The constituent series are **re-sorted annually at end-June**; composition changes are a construction
  discontinuity, checked by V8.
- The source occasionally **restates history** (methodology and format changes; a CRSP source-file format
  change is noted in the library for data from January 2025). Mitigation: `data/processed/MANIFEST.csv`
  already records sha256 + span for every panel, so any restatement is detectable as a hash change rather
  than silently changing a past reading. Any re-fetch after a frozen result must be recorded as a
  disclosed deviation.

---

## Cross-signal relationships (spec attribute 4)

**The mechanism gate governs, not the correlation** — a signal that is statistically correlated with an
admitted one is kept if it is mechanistically distinct (§Discipline). The unusual thing about this
candidate is that the mechanism is *partly shared*, which is why the correlation argument cannot be waved
away here.

- **Volatility (Phase 1.5, `production`) — the overlap that matters.**
  *How they differ, precisely:* volatility measures the **magnitude** of variance (σ, a scale); absorption
  measures the **concentration of the covariance spectrum** (a ratio of eigenvalues, scale-free on the
  correlation matrix). In principle these are independent: a cross-section can compress at low variance,
  or stay diffuse at high variance.
  *How they overlap, precisely:* under equicorrelation AR₁ is affine in ρ̄, and ρ̄ is a component of index
  variance via σ²_index ≈ σ̄²[ρ̄ + (1−ρ̄)/N]. Both rise in crises for the same underlying reason. On an
  equity-only cross-section the overlap is therefore close to definitional, not incidental.
  *How they will be told apart — registered, not argued:*
  1. **V3(b), the low-vol/high-AR quadrant** — a direct, falsifiable count of days where the two readings
     disagree in the direction the signal claims to matter (calm but compressed). If that quadrant is
     empty, they are the same instrument and the phase ends.
  2. **V5, the volatility control** — the lead must beat the *same transform applied to volatility*. This
     converts "is it different from vol" from a hand-wave into a paired, bootstrapped comparison.
  3. **V2's covariance-vs-correlation cell** — if the effect exists only on the covariance matrix, it is
     a variance-scale effect, i.e. volatility wearing a different name (R5).
  The correlation coefficient between AR and σ is reported as a *diagnostic* and is **not** the gate.

- **Concentration / breadth (planned) — second-highest overlap risk.** Both describe "the market is
  driven by less than it appears," but through different objects: breadth/concentration measures how few
  *names* drive the index level, absorption measures how few *factors* drive the covariance. They can
  diverge (a broad cross-section can still be one-factor). Registered as a known relationship to be
  re-examined when that signal exists; if both are admitted, their joint behaviour is a Phase-10 question,
  **not** something to pre-empt here.

- **Stock-bond correlation (Phase 2, `research`).** Different object entirely: cross-asset-class, two
  assets, monthly, the inflation/real-rate axis. Absorption here is strictly within-equity. Expect
  co-movement in crises, no construction overlap.

- **Tail, credit (EBP), funding, crowding (planned).** Distinct mechanisms and distinct data. Crowding is
  the one to watch: factor crowding is a plausible *cause* of eigenvalue concentration, so if both are
  ever admitted, the causal ordering between them is a real question — again a Phase-10 question.

- **The joint configuration is deliberately NOT analysed here** (architecture doc, 2026-08-06 sequencing
  ruling). Each signal is built to the same standard first; what the joint reading *means* is Phase 10.

---

## Level-0 output shape (draft — validated against `signal_output_schema.py`)

`reading` = {`ar`, `delta_ar`, `n_components`, `n_assets`, `window`} · `rarity` = expanding percentile of
`ar` and of `delta_ar` · `trend` = drift of the `ar` percentile · `assumption_monitored` = the
diversification assumption · `cross_signal_relationships` = the volatility overlap statement above.

**Implementation warning, registered:** the closed schema's denylist matches on snake-case *segments*
(`signal_output_schema.py:43`), and **`size` is a forbidden segment** — while the panel is literally a
size × book-to-market sort. Field names must therefore avoid `size` entirely (`n_assets`, `me_bm_panel`,
not `panel_size` or `size_bm`). Also forbidden as segments: `score`, `position`, `weight`, `target`.
Naming the trap now avoids discovering it in a failing boundary-audit test after the artifacts exist.

---

## Pre-registered analysis specification (summary)

| item | registered value |
|---|---|
| panel | 25 size × book-to-market daily sorts, US / Japan / Europe, **matched object mandatory** |
| common window | 1990-07-02 → 2026-05-29; effective start ≈ mid-1993 after burn-in |
| covariance window W | **500** trading days (primary); {250, 750} robustness |
| components K | **5** = N/5 (primary); {3, 7} robustness |
| matrix | **covariance** (primary, source fidelity); **correlation** (mechanism-purity check) |
| refit | every trading day, full re-decomposition, trailing window only |
| ΔAR | [MA₁₅ − MA₂₅₂] / sd₂₅₂, all trailing; trigger at **+1.0σ** |
| rarity | `causal.expanding_percentile` |
| events | 21-day realized-vol expanding-percentile ≥ 0.90 crossing, 126-day refractory |
| pre-window | 126 trading days |
| null | circular block bootstrap, block 63d, B = 2000, fixed seed |
| control | same shift transform on `ewma_vol(λ=0.94)` |
| power floor | ≥ 8 onsets/region *[recommended]* |
| harness | shared `run_oos`, extended with a panel loader (`REGION_ASSET_PANELS` + `load_region_panel`) — an extension of shared infra, **not** a per-signal pipeline (D-20) |
| guard | `assert_causal` on `absorption.build`, registered in `CAUSALLY_GUARDED` |
| looks | **one** |

---

## Open questions for Adam

1. **The verdict itself.** I recommend **DROP**, on Finding 2: the only unique content is a ~1-month lead,
   and the only matched cross-region source publishes ~2 months late, so the lead is unreadable live even
   if every bar passes. Overriding this is legitimate — but the honest form of the override is *"proceed
   for the historical measurement finding, `production` unreachable,"* not *"proceed and solve latency
   later."* **[recommended — Adam to confirm/override]**

2. **Scope tension: lead-only vs the 2026-08-06 objective restatement.** Your 2026-08-05 ruling scoped
   this NARROW / lead-only. The architecture doc's objective restatement (2026-08-06, one day later)
   names absorption (Kritzman et al. 2011) among the known relationships whose *point-in-time, causal,
   cross-regional reproduction is the pass condition* — which would be a measurement-only bar, no lead
   required. **I have kept lead-only**, because a measurement-only absorption reading on an equity
   cross-section is ≈ average pairwise correlation, which the volatility signal already contains, and
   would fail D-19's leave-one-out test. But the two rulings do point different ways and you should settle
   it explicitly. **[recommended — keep lead-only; Adam to confirm/override]**

3. **Matched-panel prerequisite.** The kickoff said "no new fetch." I am registering a mandatory new
   build (US 5×5 daily) because without it the generalization test is uninterpretable — the exact defect
   that made the dispersion failure ambiguous. Confirm the fetch is authorised. **[recommended — Adam to
   confirm/override]**

4. **The V3 dissociation thresholds** (|corr| < 0.90; ≥ 5% of days in the low-vol/high-AR quadrant) and
   the **V6 generalization band** ([⅓×, 3×] of the US lead) and the **V7 power floor** (8 onsets/region).
   These are the four numbers that decide the outcome and they are my defaults, not yours. They must be
   fixed before the look or the whole freeze is theatre. **[recommended — Adam to confirm/override each]**

5. **Whether the drawdown-dated replication is run at all.** I have it as reported-but-not-a-bar for
   source fidelity. It is also the one output most easily misread as a crash forecast. Cutting it entirely
   is defensible. **[recommended — keep, clearly labelled non-decisive; Adam to confirm/override]**

---

**Status: DRAFT. Not frozen, not signed, no look spent.** Freezing requires: the four numbers in Q4
fixed, the matched-panel build completed and gated, and Adam's dated sign-off of this charter — which
authorises the build only, never a result.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/05-diversification-signal/05-CHARTER-KICKOFF|05-CHARTER-KICKOFF]]

<!-- LINKS:END -->
