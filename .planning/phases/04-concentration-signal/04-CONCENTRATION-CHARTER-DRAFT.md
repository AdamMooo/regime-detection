# Research Charter — Concentration Signal (Phase 4)

# DRAFT — NOT FROZEN, NOT SIGNED

**Status: DRAFT.** This is not a Stage-1 freeze. No look has been spent: nothing below was informed by
computing the signal, its correlations, or any performance statistic. The only empirical work behind this
document is **data-coverage inspection** — file dates, row counts, column availability, missingness, and the
block structure of the Ken French source files — recorded in the Data Readiness section.

**Charter/spec version** — v0.1 (draft, unfrozen) · filled against framework template **v1.1**
(`.planning/framework/research-charter-template.md`).
**Drafted** — 2026-08-06. **Unsigned.**

---

## Summary recommendation (read this first)

**PROCEED — conditional on respecifying the measurement. DROP the kickoff's proxy as the primary observable.**

The *assumption* — "the index is not dependent on a few names" — clears Stage 0 and is genuinely uncovered by
the two built signals. The *measurement proposed in the kickoff brief* does not. Three specific defects, all
found by reading the actual data build, are documented in Data Readiness and summarised here:

1. **The proposed observable measures a rate, not a level.** A cap-weighted-minus-equal-weighted return spread
   is (approximately) the time-derivative of concentration, not concentration. The kickoff's own G2 argument —
   "index concentration was at multi-decade highs in a *low*-volatility regime" — is a **level** claim, which
   the proposed observable cannot make.
2. **The proposed equal-weighted leg is not equal-weighted across stocks.** `scripts/build_assets.py` keeps only
   the cap-weighted block of the French 10-industry file (explicit code comment at the `_ff_daily_table` de-dup
   line). The mean of ten cap-weighted industry returns is an equal-weighted-across-*industries* composite of
   cap-weighted returns. The resulting spread is as much a sector-rotation spread as a size spread.
3. **What remains overlaps a published return factor.** After removing the industry artifact, the spread is
   close to the negative of the size factor `smb`, which sits in the *same file* (`assets_daily.csv`). A signal
   that is a relabelled size factor has a **risk-premium** mechanism, and the size premium is the textbook case
   of a premium that decayed after publication (Banz 1981 → the post-1981 literature). That is precisely the
   mechanism class that fails "survives being known."

**But the kickoff's data verdict was too pessimistic and is wrong as stated.** It claims a true cap-based
concentration measure "needs historical index constituents — paywalled and survivorship-prone." Coverage
inspection (below) shows the Ken French library publishes, free, **a firm-count block and an average-firm-size
block alongside the return blocks** — US **daily** 1926-07-01..2026-06-30 and Japan/Europe
**monthly** 1990-07..2026-06. Firm count × average firm cap per bucket gives a **directly computable, causal,
survivorship-clean cap-mass distribution**, from which a Herfindahl / effective-N concentration *level* follows.
No paywall, no reconstituted-membership contamination.

**So the respecification is: measure the level from bucket cap masses (primary), keep the cap-weighted-minus-
equal-weighted spread only as an explicitly-renamed *leadership-narrowing rate* (secondary), and register a
make-or-break resolution test (V3) before anything else is interpreted.**

**If Adam rejects the respecification and insists on the kickoff's spread-only design, my recommendation flips
to DROP.** Spread-only, the signal is a size-factor return series with a risk-premium mechanism, and it fails
both the mechanism gate (§(b)) and the leave-one-out bar (§Stage 0 Q4).

---

## Header (draft)

- **Signal name** — Concentration (index cap-mass concentration + leadership-narrowing rate)
- **Assumption monitored** — **"the index is not dependent on a few names."**
- **Native clock / frequency** — **monthly.** Registered deliberately: the cap-mass distribution is only
  published monthly for Japan and Europe, and concentration is a structural quantity whose honest frequency is
  slow. A US daily read exists in the source and is retained as the domestic high-frequency view only, exactly
  as Phase 2 handled the daily/monthly split.
- **Maturity tag** — DERIVED, unset. Given the resolution and coverage limits registered in Data Readiness,
  **`research` is the ceiling this phase can earn.** `production` is not available and must not be claimed.
- **Investor question (the production bar)** — *"How much of the index's capital sits in its largest
  constituents right now, how unusual is that against its own history, and which way is it moving?"*
- **Boundary-vocabulary note (§(h) reviewed grep).** "Cap-weighted" and "equal-weighted" appear throughout as
  **index-construction descriptors of the observable**, never as decision quantities. The exact Ken French zip
  identifiers are deliberately **not** reproduced in this document because the vendor's filenames contain a token
  on the §(h) forbidden-vocabulary list; the identifiers already live in `scripts/build_assets.py` and
  `scripts/build_intl_panel.py`, which is where the builder will read them from.

---

## Stage-0 Relevance Gate (default = NO)

Re-answered against the **respecified** observable, not the kickoff's. Where the kickoff's answer does not
survive, that is stated.

- **G1 — what important investment question does this signal answer?**
  *How much of the index's capital is concentrated in its largest constituents, how unusual is that level
  against its own history, and is it rising or falling?* **PASS**, but only for the respecified level measure.
  The kickoff's G1 wording ("is leadership narrowing") is the *rate* question and is answered by the secondary
  descriptor, which is a weaker and more crowded question.

- **G2 — why is that question important to long-term investors?**
  A cap-weighted index is a claim on a *composition*, and the composition is not a constant. An investor who
  believes "the index is diversified" is relying on an arithmetic property that changes over decades without
  announcement. When cap mass concentrates, the index's return variance shifts from a broad average toward the
  idiosyncratic outcomes of a handful of firms, and single-firm events (a regulatory ruling, a product cycle, a
  fraud) become index events. This is invisible to a volatility reading — a top-heavy index can be calm.
  **PASS.** Note the honest correction to the kickoff: this argument is about a **level**, so it only supports
  the respecified measure.

- **G3 — information not already available from the existing signals?**
  **PASS, with one flag.** Volatility (production) measures the *amplitude* of index returns; stock-bond
  correlation (research) measures a cross-asset macro covariance. Neither carries any compositional fact about
  the index. Concentration is a within-equity, cross-sectional, capital-distribution quantity, which no admitted
  signal contains. *The flag:* Phase 5 (diversification / absorption ratio) is also a "concentration" measure —
  of *variance* in eigenvalue space rather than of *capital* in cap space. They are not obviously distinct. A
  de-confliction is registered as a required condition before Phase 5 opens (see Cross-signal relationships).

- **G4 — leave-one-out: would removing this signal make the observatory meaningfully less informative?**
  **PASS for the level measure. FAIL for the rate measure alone.** Removing a cap-mass concentration reading
  leaves the observatory unable to say anything about whether the index still is what the investor assumes it
  is — a permanent blind spot with no substitute in the set. Removing a cap-weighted-minus-equal-weighted return
  spread leaves the observatory essentially unchanged, because `smb` is already in the same data file and the
  spread carries a size-premium interpretation the repo explicitly refuses to make. Litmus applied honestly: the
  rate measure alone "never belonged"; the level measure does.

- **G5 — strong theoretical/empirical prior the relationship exists, before weeks of research?**
  **PASS, and it is a prior about arithmetic rather than about an effect.** The claim is not "concentration
  predicts X"; it is "a cap-weighted index's dependence on its largest constituents is a computable property
  that varies materially over time." That is arithmetically guaranteed to exist and is directly measurable.
  The theoretical support for why it *matters* (Gabaix 2011; Campbell–Lettau–Malkiel–Xu 2001; Meucci 2009) is
  cited in the Mechanism section. The kickoff's G5 citation of random-matrix theory (Laloux 1999) is about the
  **correlation matrix**, not cap concentration — it belongs to Phase 5, not here, and is not carried forward
  as this signal's prior.

**Gate verdict: PASS for the respecified level measure. The kickoff's spread-only scoping does NOT pass G4.**

---

## The six charter questions

### 1. What question does the signal answer?

Two descriptive questions about the current index, reported as continuous readings with rarity — no state, no
direction, no forecast:

1. **How top-heavy is the index right now?** The **effective number of independent capital buckets**
   (`effective_n = 1 / Σ s_i²`, where `s_i` is bucket *i*'s share of total index capital) and the **share of
   total capital in the largest size bucket**, plus each one's causal expanding percentile against its own
   history. This is the **level** descriptor and the primary reading.
2. **Is leadership narrowing or broadening?** The trailing cumulative **cap-weighted minus equal-weighted return
   spread**, computed on the *same* set of buckets so both legs share a universe. This is the **rate**
   descriptor. It is named a *leadership-narrowing rate*, never "concentration", so it cannot be misread as the
   level.

**What is NOT answered.** Not "is concentration too high" (there is no such threshold), not "is the market
fragile" (see the healthy-vs-fragile ambiguity in the Mechanism section), and not anything about future returns.

Maps to spec attribute 1.

### 2. What market assumption does it monitor?

**"The index is not dependent on a few names."**

**Ledger status — registered recommendation: NONE in v1.0.** Unlike stock-bond correlation, where sign zero is a
real mechanical boundary (bonds move *with* or *against* equity), there is no mechanical boundary anywhere in
`effective_n`. Any {intact | under-test | violated} banding would be a pure knob — the exact failure the
volatility reframe removed, and the one Phase 2's post-look disposition D-02b flagged when its `intact →
under_test` band failed to separate internationally. The honest output is **the number plus its rarity plus its
direction**, which *is* the answer to "is the assumption under strain," expressed without inventing a boundary.
`[recommended — Adam to confirm/override]`

### 3. What mechanism supports it — why does it survive being known?

**Registered mechanism: risk-management channel via the arithmetic of cap-weighted index construction.**

**The structural fact.** A cap-weighted index's return is `Σ s_i r_i` with `s_i` the capital shares. Decompose
the variance: as the share vector becomes concentrated, the diversifiable portion of index variance shrinks and
the index inherits the idiosyncratic variance of its largest constituents. In the limit, an index dominated by a
handful of names *is* those names. The effective number of independent bets — `1/Σ s_i²`, the reciprocal
Herfindahl — is the standard summary of exactly this. This is an identity about a composition at each instant,
not a claim about prices being wrong.

**Why it survives being known.** There is nothing to arbitrage. The signal makes **no forward-return claim**, so
public knowledge has no channel through which to compete it away. If every participant knew today's effective-N,
today's effective-N would still be today's effective-N — the arithmetic of a capital distribution is not a
mispricing. Note the contrast that makes this concrete: the *rate* descriptor, read as "large caps have been
beating small caps," is a **risk-premium** object and would be arbitrage-eligible; the size premium's decay after
Banz (1981) is the textbook case. That is why the risk-premium reading is refused (Q6) and the level descriptor
is the admitted one.

**Risk-premium channel vs risk-management channel — stated explicitly, as §(b) requires.**

| channel | claim it would make | status here |
|---|---|---|
| risk-premium | high concentration is compensated / predicts subsequent index returns | **REFUSED.** Contested, arbitrage-eligible, and a forecast claim this repo prohibits. Not registered, not tested, not claimed. |
| risk-management | the index's dependence on a few constituents is a measurable, time-varying compositional fact that changes what "owning the index" means | **ADMITTED.** This is the whole signal. |

**Standard-literature terms and actual references** (so the reading trail is real, not decorative):

- **Herfindahl–Hirschman index (HHI) / effective number of constituents.** Herfindahl (1950); Hirschman (1945).
  `effective_n = 1/HHI` is the industrial-organisation measure applied to index capital shares.
- **Effective number of bets / diversification measurement.** Meucci, A. (2009), "Managing Diversification,"
  *Risk* 22(5), 74–79. Choueifaty, Y. & Coignard, Y. (2008), "Toward Maximum Diversification,"
  *JPM* 35(1), 40–51 — cited for its *diversification-ratio* measurement construct only; its construction
  methodology is out of scope here and is not used. (Journal name given as its standard abbreviation: the full
  title contains a token on the §(h) forbidden-vocabulary list.)
- **Idiosyncratic vs systematic variance decomposition.** Campbell, J., Lettau, M., Malkiel, B. & Xu, Y. (2001),
  "Have Individual Stocks Become More Volatile? An Empirical Exploration of Idiosyncratic Risk," *Journal of
  Finance* 56(1), 1–43. The canonical market / industry / firm-level variance decomposition and the source of
  the "how many names does diversification actually require" arithmetic (see also Statman, M. (1987), *JFQA*).
- **Granular origins — the strongest theoretical support.** Gabaix, X. (2011), "The Granular Origins of Aggregate
  Fluctuations," *Econometrica* 79(3), 733–772. When the firm-size distribution has a fat tail, idiosyncratic
  firm-level shocks do **not** wash out in aggregate; they drive aggregate fluctuations. This is the formal
  statement of why a top-heavy cap distribution is a structural property of the aggregate, not a curiosity.
- **The healthy-side counter-argument (required reading, not a rebuttal to be dismissed).** Bessembinder, H.
  (2018), "Do Stocks Outperform Treasury Bills?", *Journal of Financial Economics* 129(3), 440–457 — lifetime
  wealth creation is extremely concentrated in a small number of firms. Concentration is partly the *expected
  outcome* of a skewed return-generating process, not evidence of anything being wrong.
- **Random-matrix theory** (Laloux, Cizeau, Bouchaud & Potters (1999), *PRL* 83, 1467; Plerou et al. (2002),
  *PRE* 65) — cited in the kickoff, but it concerns the **correlation matrix's** eigenvalue structure, which is
  Phase 5's object, not cap concentration. Recorded here only to note that it is *not* this signal's prior.

**The healthy-vs-fragile ambiguity — registered as a permanent limitation, not a defect to be solved.**
Concentration rises for at least two mechanistically opposite reasons: (a) genuine winner-take-most economics
(scale, network effects) — in which case the index is *correctly* representing the economy and Gabaix's
granularity is a real feature of it; and (b) a narrow re-rating of a crowded set — the fragility case. **The
measurement cannot distinguish them, and no free data can.** This is why the signal reports a level and a rarity
and STOPS, and why it must never be presented with a direction of concern. ROADMAP Phase-4 success criterion #3
requires this ambiguity be surfaced honestly; this paragraph is that commitment, registered before the look.

Gated by `validation-standards.md` §(b). **Mechanism gate: PASS** for the level descriptor (a written,
structural, arithmetic reason). **Mechanism gate: FAIL** for the rate descriptor read as a premium — which is
why it is admitted only as a descriptive rate and is subject to R5 below.

### 4. What evidence would validate it?

Validation is **measurement correctness + resolution adequacy + cross-regional replication** — never
forecastability. Each bar is paired with its reject condition in Q5. Bars run **once**, as a single frozen script.

- **V1 — the construction is causal and look-ahead-free.** `assert_causal(build, data)` passes
  (`scripts/causal.py`), registered under `tests/test_reproducibility.py` so it cannot be skipped by omission.
  Concretely: bucket cap shares at month *t* use only the counts and average firm caps published for month *t*;
  rarity uses `expanding_percentile`, never a full-sample rank; the rate descriptor uses trailing sums only.

- **V2 — construction integrity: the reconstructed cap mass reproduces the aggregate.** The bucket cap masses
  (`n_i × avg_cap_i`) are a *reconstruction*, not a published total. Registered check: the cap-share-weighted
  average of the bucket returns must track the published cap-weighted market return over the full overlap within
  a pre-committed tolerance of **corr ≥ 0.95 and mean absolute monthly difference ≤ 25 bp**
  `[recommended — Adam to confirm/override]`. If the reconstruction does not reproduce the aggregate, the cap
  distribution is wrong and nothing downstream is interpretable.

- **V3 — resolution adequacy. THE MAKE-OR-BREAK BAR, run and reported before any other interpretation.**
  The buckets are a coarse partition of the universe. If most of the variation in true concentration happens
  *inside* the largest bucket, then a bucket-level `effective_n` will be nearly flat and the signal cannot
  answer its own question. Registered test, pre-committed before the look:
  1. `effective_n` must have a full-history interquartile range of at least **10% of its own median**
     `[recommended — Adam to confirm/override]`; and
  2. its causal expanding percentile must exceed **0.90 during at least two of the three episodes independently
     known to have been concentration extremes** — US 1998–2000, US 2020–2024, Japan 1987–1989 (Japan is
     out of sample for coverage reasons; see Data Readiness, so in practice this is the two US episodes).

  Naming the episodes **in advance** is what makes this a pre-registration and not a post-hoc rationalisation.
  If V3 fails, the honest outcome is that free data cannot measure this signal's target and Phase 4 closes as
  **NOT MEASURABLE**, which is a legitimate and valuable result.

- **V4 — decoupling from volatility (orthogonality *diagnostic*, not the gate).** Per §(b), statistical
  correlation with an admitted signal never decides admission — mechanism does. Registered nonetheless because
  ROADMAP criterion #3 asks for it: there must exist extended periods (**≥ 12 consecutive months**,
  `[recommended — Adam to confirm/override]`) where the concentration rarity is ≥ 0.80 while the volatility
  rarity from `scripts/vol_descriptors.py` is ≤ 0.50. If concentration is elevated *only* when volatility is
  elevated, the signal is reading the PC1 axis in a new coordinate system and adds nothing.

- **V5 — the rate descriptor is not a relabelled size factor.** The leadership-narrowing rate is compared
  against `smb` in `data/processed/assets_daily.csv` over the common history. Pre-committed bar: if
  `|corr| ≥ 0.90` `[recommended — Adam to confirm/override]`, the rate descriptor is **dropped from the signal**
  as duplicative of a published factor already available to any reader, and the level descriptor stands alone.
  Registering this before the look prevents the rate descriptor being retained on the grounds that it "looks
  informative."

- **V6 — out-of-hypothesis-sample confirmation (Japan, Europe).** The identical monthly construction runs on
  Japan and Europe via the shared harness. Bar: the level descriptor is computable, the V2 reconstruction check
  passes in each region, and `effective_n` shows the same order of variation as the US (V3's IQR criterion holds
  regionally). *Construction note, disclosed in advance:* `scripts/run_oos.py` currently loads only a daily
  `mkt_ret` series per region; a monthly panel loader must be added. That is plumbing, registered here so the
  extension is not later mistaken for a protocol deviation.

- **V7 — coverage / power pre-check, run BEFORE any cross-region contrast is interpreted.** Borrowed
  deliberately from Phase 2's V4, which existed so an underpowered contrast could not be written up as either
  support or refutation. For each region, count months of coverage and the number of *distinct* episodes in
  which concentration rarity exceeds 0.90. **A region containing fewer than two distinct episodes is declared
  UNDERPOWERED and its result is reported as "insufficient coverage" — never as a weak or negative finding.**
  This is expected to bind: Japan's own concentration peak (1987–89) is **outside** the 1990-07 start of the
  international data, the exact structural parallel to Phase 2's missing 1970s inflation regime.

- **V8 — restatement / vintage check.** The French files are rebuilt from the vendor's *current* database
  (the US file header states "created using the 202606 CRSP database"; the Japan file states Bloomberg), so the
  published history is a restated series, not an archive of vintages. Registered check: compare the overlapping
  history of a fresh fetch against the already-stored `data/processed/assets_daily.csv` and
  `data/processed/industry10_daily.csv` (built 2026-07, sha256 recorded in `data/processed/MANIFEST.csv`) for
  material drift. Bar: max absolute daily return difference on the overlap ≤ 1 bp
  `[recommended — Adam to confirm/override]`. Material drift qualifies the point-in-time claim in the spec.

Maps to spec attribute 5.

### 5. What would falsify it?

Declared before any look. Each reject condition names the bar it trips.

- **R1 — look-ahead leak.** Any part of the construction found to use future data: a full-sample rank, a
  centred/forward filter, or a cap share attributed to a month before it was published. Fatal — the reading
  would be unusable live. **Kill.** (Trips V1.)

- **R2 — the cap reconstruction is wrong.** The bucket cap masses fail to reproduce the published cap-weighted
  index return within the pre-committed tolerance. The measured "capital distribution" would then not be the
  index's capital distribution. **Kill.** (Trips V2.)

- **R3 — insufficient resolution. The most likely rejection, and the one to expect.** `effective_n` is
  materially flat over history, or fails to flag the pre-named US concentration episodes. This is the honest
  failure mode of a bucket-level measure of a phenomenon that lives inside the largest bucket: the "Magnificent
  7" question is about seven names out of five hundred, and the partition available for free cannot see inside
  the top bucket. **Kill — Phase 4 closes as NOT MEASURABLE with free data**, with the paywalled constituent
  path recorded as a separate, costed decision for Adam. This is a legitimate outcome, not a failure of the
  phase. (Trips V3.)

- **R4 — the signal is the volatility axis in new clothes.** No sustained period exists in which concentration
  is rare while volatility is ordinary. **Demote, not kill** — mechanism governs admission (§(b)), but a signal
  that never decouples from an admitted signal fails the leave-one-out bar in practice and would be tagged
  `research` at best, with the redundancy declared in spec attribute 4. (Trips V4.)

- **R5 — the rate descriptor is a relabelled size factor.** Correlation with `smb` at or above the
  pre-committed bar. **Drop the rate descriptor**; the level descriptor is unaffected and continues. This is a
  partial rejection registered in advance precisely because the kickoff's design made this descriptor primary.
  (Trips V5.)

- **R6 — the point-in-time claim does not hold.** The vendor has materially restated the historical series
  between the stored 2026-07 build and the fresh fetch. **Not a kill:** the signal continues with the PIT claim
  explicitly qualified in spec attribute 8 ("no forward filtering; not a true vintage archive") and the maturity
  ceiling reaffirmed. Registered so the qualification is made honestly rather than discovered later.
  (Trips V8.)

- **R7 — international coverage is insufficient.** Every non-US region fails the V7 pre-check. **Not a kill:**
  the phase closes as **INCONCLUSIVE — insufficient international coverage**, the signal stays US-only at
  `research`, and no SUPPORT claim is made. Registered as a distinct outcome, following Phase 2's R5, so an
  underpowered international result cannot later be written up as either support or refutation. (Trips V6/V7.)

Maps to spec attribute 6, echoed as user-facing caveats in attribute 8.

### 6. What does it explicitly NOT claim?

The per-signal boundary. The signal reports the effective number of capital buckets, the largest bucket's share
of capital, each one's rarity against its own history, and the direction of the leadership-narrowing rate — and
**STOPS**. It implies no action.

Explicit prohibitions (this list is a boundary statement; the forbidden vocabulary appears here only in order to
prohibit it): the signal does **not** claim that concentration predicts index returns, drawdowns, or a market
top; does **not** claim high concentration is a bubble or that low concentration is safe — it cannot distinguish
winner-take-most economics from a crowded re-rating, and says so; does **not** produce a threshold, a state
label, a trigger, or a single concentration score; does **not** compare the index against any alternative index
construction as a preferred one; and is never a buy, sell, risk-on, risk-off, overweight, or underweight
statement, an allocation or exposure instruction, a position-sizing or risk-budget input, or any market-safety
number. The word "portfolio" and every capital-allocation concept are outside this repo entirely. What a
concentrated index means for anyone's decisions is the human's judgment, in a separate system.

Maps to spec attribute 8.

---

## Mechanism gate verdict (recorded separately, as §(b) requires)

**PASS**, for the level descriptor, on a written structural reason: cap-weighted index construction
arithmetically inherits its largest constituents' idiosyncratic variance, and this composition varies materially
over time. Public knowledge of a capital distribution does not change the capital distribution. Not admitted on
novelty, not admitted on a backtest, not admitted on literature citation alone.

The rate descriptor does **not** independently pass the gate on a risk-premium reading; it is admitted only as a
descriptive rate and is subject to R5.

---

## Data readiness

Verified 2026-08-06 against the actual files. **Coverage inspection only** — dates, row counts, columns, block
structure, missingness. No signal value was computed.

### What is already on disk

| file | rows | span | relevance |
|---|---|---|---|
| `data/processed/assets_daily.csv` | 26,190 | 1926-09-17 .. 2026-05-29 | `mkt_ret`, `smb`, and `ind_*` (10 industries). Zero NaNs in all ten industry columns and in `mkt_ret`/`smb` across the full span. |
| `data/processed/industry10_daily.csv` | 26,253 | 1926-07-01 .. 2026-05-29 | same 10 industries, zero NaNs |
| `data/processed/japan_assets_daily.csv` | 9,370 | 1990-07-02 .. 2026-05-29 | 25 size × book-to-market buckets `p0..p24`, zero NaNs |
| `data/processed/europe_assets_daily.csv` | 9,370 | 1990-07-02 .. 2026-05-29 | same shape |
| `data/processed/{japan,europe}_market_daily.csv` | 9,370 | 1990-07-02 .. 2026-05-29 | `mkt_ret`, the `run_oos` region schema |
| `data/processed/market_daily.csv` | 26,190 | 1926-09-17 .. 2026-05-29 | US `mkt_ret` |

Provenance (sha256 / shape / span) for all of the above is in `data/processed/MANIFEST.csv`.

### Finding 1 — the stored panels contain NO equal-weighted leg (contradicts the kickoff)

`scripts/build_assets.py`, in `_ff_daily_table`, ends with:

```
# daily files sometimes append a second (equal-weight) block with duplicate dates —
# keep the first (value-weight) block only
df = df[~df.index.duplicated(keep="first")]
```

`scripts/build_intl_panel.py` does the same and says so in its docstring. **Every return series on disk is
cap-weighted.** The kickoff's construction — "EW = mean of the 10 industry return series already in
`assets_daily.csv`" — therefore does not produce an equal-weighted-across-stocks index. It produces an
equal-weighted-across-*industries* composite of cap-weighted industry returns, whose difference from `mkt_ret`
mixes a size effect with a sector-composition effect in unknown proportion. `build_assets.py`'s own A1 gate calls
this out in a comment ("EW/VW difference is structural") without treating it as a signal.

### Finding 2 — a genuine cap-mass distribution IS available free (contradicts the kickoff's data verdict)

Block-structure inspection of the Ken French library:

| source | blocks present | span |
|---|---|---|
| US, daily 5×5 size × book-to-market | cap-weighted returns · equal-weighted returns · **Number of Firms** · **Average Firm Size** | 1926-07-01 .. 2026-06-30 |
| US, monthly size deciles (formed on market equity) | cap-weighted monthly · equal-weighted monthly · cap-weighted annual · equal-weighted annual · **Number of Firms** · **Average Firm Size** | 1926-07 .. 2026-06 |
| Japan, monthly 5×5 size × book-to-market | cap-weighted monthly · equal-weighted monthly · cap-weighted annual · equal-weighted annual · **Number of Firms** · **Average Firm Size** | 1990-07 .. 2026-06 |
| Europe, monthly 5×5 size × book-to-market | same six blocks | 1990-07 .. 2026-06 |
| Japan / Europe, **daily** 5×5 | cap-weighted returns · equal-weighted returns **only** — no firm counts, no average firm size | 1990-07-02 .. 2026-06-30 |

`Number of Firms` × `Average Firm Size` per bucket gives the bucket's total capital, hence the capital-share
vector, hence `effective_n = 1/Σ s_i²`. It is free, it is survivorship-clean (the vendor's universe includes
firms up to their delisting; buckets are re-formed each June from the universe available *then*), and it requires
no index-membership list. **The kickoff's claim that a cap-based concentration measure "needs historical index
constituents — paywalled" is wrong as stated** for a bucket-level measure; it remains true for a name-level one.

### Finding 3 — the frequency asymmetry decides the native clock

Firm counts and average firm caps are daily for the US but **monthly only** for Japan and Europe. Identical
cross-region construction therefore requires monthly. Registering monthly as the native clock is not a
concession — a capital distribution re-formed annually and reported monthly has no honest daily content.

### What CANNOT be tested with available data

1. **Name-level concentration.** No free source gives point-in-time index membership and per-name capital shares.
   Top-10 share, a true name-level Herfindahl, and anything phrased as "the largest *n* names" are **out of
   reach**. The bucket partition is the entire resolution available.
2. **Concentration inside the largest bucket** — which is where the phenomenon that motivated the phase actually
   lives. This is R3, the expected rejection, and it is the single most important limitation in this document.
3. **Japan's own concentration peak (1987–89).** International data starts 1990-07. This is the direct structural
   parallel to Phase 2's registered scope limitation (international panels begin 1990 and contain no 1970s
   inflation regime). Japan is arguably the most informative concentration episode in the historical record and
   it is outside the sample.
4. **True vintage reconstruction.** The vendor publishes one restated history rebuilt from its current database,
   not an archive of vintages. The construction is causal (no forward filtering, expanding-window rarity), but
   "point-in-time" here means "no look-ahead within the published series," not "the series a reader would have
   seen in 1998." V8/R6 handle this by qualification, not by pretence.
5. **Free-float adjustment, share repurchases, cross-holdings, and multi-class share structures** are not
   observable in the source and are not adjusted for. Japan's cross-holdings in particular make its measured
   capital distribution a known approximation.

### What this caps the maturity tag at

**`research` is the ceiling. `production` is not available to this phase and must not be claimed**, on three
independent grounds — resolution (item 2), international coverage (item 3), and the vintage qualification
(item 4). Any one of these alone would cap it. Registering the cap *before* the look is deliberate: a strong
result is exactly when the cap is most tempting to drop, which is why Phase 2 registered the same thing and held
it in its post-look disposition D-02c.

### Schema constraints the builder must respect

`scripts/signal_output_schema.py` rejects any key containing certain snake-case segments — among them `size`,
`weight`, and `score`. (The full denylist is in that module; it legitimately names the forbidden vocabulary as
data, which is the enforcement mechanism, and is not reproduced here.) So the natural names for these
descriptors are schema-invalid. Registered
field names that pass the allowlist: `effective_n`, `top_bucket_capital_share`, `leadership_spread_12m`,
`effective_n_percentile`. The vendor's `Average Firm Size` column must be renamed on ingest (e.g. `avg_firm_cap`).

### Build work implied

- A new builder, `scripts/build_concentration.py`, fetching the firm-count and average-firm-cap blocks for US /
  Japan / Europe and writing `data/processed/concentration_monthly.csv` (+ a US daily file), registered in
  `scripts/data_manifest.py`. **This is a new fetch, which the kickoff excluded** — see Open Questions.
- A monthly region loader in `scripts/run_oos.py` (V6's disclosed plumbing note).
- `scripts/concentration.py` exposing `build(panel)` on the shared causal spine, registered under
  `assert_causal` in `tests/test_reproducibility.py`.

---

## Cross-signal relationships

Maps to spec attribute 4. Registered as *expectations before the look*, so that a surprise is visible as a
surprise.

- **Volatility (Phase 1.5, `production`).** Mechanistically distinct: volatility measures the amplitude of index
  returns; concentration measures how few sources generate them. A top-heavy index can be calm, and a broad index
  can be violent. Registered expectation: weak unconditional relationship, with correlation *rising in crises*
  because nearly everything correlates in crises (the standing finding in the `sensor-orthogonality-evidence`
  memory: raw stress series collapse onto a single common stress factor and re-converge in crises). That is
  a diagnostic, not a gate. The two readings must be presented side by side and never merged: concentration is
  read *against* the volatility barometer, exactly as the volatility Level-0 record already anticipates
  ("the same valuation or concentration reading means something different in a high-volatility environment").

- **Stock-bond correlation (Phase 2, `research`).** Different space entirely — a cross-asset macro covariance
  versus a within-equity capital distribution. Registered expectation: **near-zero relationship.**
  **Registered confound, to be checked rather than assumed:** the real-rate cycle is a plausible *common* driver
  — a long period of low real rates re-rates long-duration mega-cap growth firms (raising measured concentration)
  and is also the regime in which the stock-bond correlation was negative. If a strong relationship appears
  between these two signals, the real-rate channel is the first explanation to rule out, and a claim of
  independence made without ruling it out would violate §(c).

- **Diversification / absorption ratio (Phase 5, not built) — HIGHEST OVERLAP RISK IN THE SET.** The absorption
  ratio is the concentration of *variance* in the eigenvalue structure of a correlation matrix; effective-N is
  the concentration of *capital* in the cap distribution. Both are Herfindahl-type measures, differing in which
  vector they are applied to. They may or may not be mechanistically distinct, and the two can move together for
  a purely mechanical reason: a top-heavy capital distribution makes the index's first principal component larger
  by construction. **Registered condition: before Phase 5's charter opens, a written de-confliction must show
  these are distinct mechanisms, or one of the two is dropped.** Flagging this now, against my own phase's
  interest, is the leave-one-out discipline applied honestly.

- **Crowding (Phase 8, not built).** ROADMAP criterion #2 requires concentration be kept distinct from crowding
  *by mechanism, not statistics*. The distinction registered here: concentration is a fact about **the index's
  composition** (how capital is distributed among firms); crowding is a fact about **who owns what, and at what
  price** (positioning and valuation of a common factor). A concentrated index whose largest firms are cheaply
  valued and widely dispersed in ownership is a different object from a crowded one. The two will likely be
  correlated in the 2020s sample; that is a coincidence of the era, not a merge condition.

- **Valuation (Phase 3, not built).** Complementary and independent by construction: valuation is a level of
  price relative to fundamentals; concentration is a distribution of capital. Joint readings (a concentrated
  *and* richly-valued index) are exactly the kind of multi-signal configuration the observatory exists to
  present — as a joint context in Phase 10, **never as a combined score** (D-09 / D-11).

---

## Pre-registered analysis specification (DRAFT — not frozen)

Frozen only when Adam signs. Lines marked `[recommended — Adam to confirm/override]` are my defaults.

- **Primary observable (level)** — capital-share Herfindahl over the French 5×5 size × book-to-market buckets:
  `s_i = n_i · c_i / Σ_j n_j c_j`, where `n_i` is the bucket's firm count and `c_i` its average firm capital;
  `effective_n = 1/Σ s_i²`. Reported alongside `top_bucket_capital_share`.
  `[recommended — Adam to confirm/override: 5×5 buckets vs the 10 size deciles. The 5×5 sort separates mega-cap
  growth from mega-cap value, which is the more informative partition for the current episode; the deciles give
  ten cap points instead of five. My recommendation is to compute BOTH and report the deciles as the V3
  resolution robustness check, since neither costs a separate look.]`
- **Secondary observable (rate)** — trailing 12-month cumulative cap-weighted-minus-equal-weighted return spread,
  both legs from the same bucket set. `[recommended — Adam to confirm/override: 12 months]`
- **Rarity** — causal expanding-window percentile (`causal.expanding_percentile`), minimum 120 months before a
  percentile is emitted; NaN during warm-up. `[recommended — Adam to confirm/override: 120 months]`
- **Direction** — change in `effective_n_percentile` over the trailing 12 months.
  `[recommended — Adam to confirm/override]`
- **Frequency** — monthly for everything cross-regional; the US daily read is a domestic view only and is not
  used for any cross-region claim.
- **Regions** — US (hypothesis sample), Japan and Europe (out-of-hypothesis sample), via `scripts/run_oos.py`
  after the monthly-loader extension.
- **Point-in-time** — bucket composition is fixed at each June formation and the counts/caps are as published for
  each month; no forward filtering. The restatement qualification (V8/R6) is carried in spec attribute 8
  regardless of the check's outcome.
- **One look.** V1–V8 run once, as a single frozen script writing to `results/concentration_validation.txt`.
  Any positive/SUPPORT claim requires overnight cooling-off and Adam's explicit dated sign-off of the *results*,
  separate from any sign-off of this charter.

---

## Open questions for Adam

1. **PROCEED on the respecification, or DROP?** `[recommended — Adam to confirm/override]` My recommendation is
   PROCEED with the cap-mass level descriptor as primary. If the kickoff's spread-only scoping is retained
   instead, my recommendation is **DROP the phase**: spread-only, the signal is a size-factor return series with
   a risk-premium mechanism, failing §(b) and Stage-0 Q4.

2. **Authorise the new data fetch?** `[recommended — Adam to confirm/override]` The kickoff scoped Phase 4 as
   "no new fetch." The respecification requires one small, free fetch from the *same* Ken French library that
   `scripts/build_assets.py` and `scripts/build_intl_panel.py` already use, to pick up the firm-count and
   average-firm-cap blocks the existing builders discard. My recommendation is to authorise it — the alternative
   is measuring the wrong quantity because the right one was not downloaded.

3. **Should V3 (resolution adequacy) be a gate that runs and reports FIRST, before any other bar is read?**
   `[recommended — Adam to confirm/override: yes.]` If the measure has no resolution, every other result is
   noise, and knowing that first prevents interpreting noise.

4. **Ledger status: none in v1.0?** `[recommended — Adam to confirm/override: none.]` There is no mechanical
   boundary in `effective_n`, unlike sign zero in stock-bond correlation. Any banding would be a knob of exactly
   the kind the volatility reframe removed and Phase 2's D-02b flagged. The reading plus rarity plus direction is
   the answer.

5. **The Phase 5 de-confliction — accept it as a binding precondition?** `[recommended — Adam to confirm/override:
   yes.]` Cap-Herfindahl and the absorption ratio are both Herfindahl-type concentration measures on different
   vectors and may be one idea counted twice. Binding the condition now, before Phase 5's charter, is cheaper
   than discovering it after both are built.

6. **The pre-committed numeric bars** — V2 tolerance (corr ≥ 0.95, MAD ≤ 25 bp), V3 IQR ≥ 10% of median and
   rarity > 0.90 in ≥ 2 of 3 named episodes, V4 ≥ 12 consecutive months of decoupling, V5 `|corr(smb)| ≥ 0.90`,
   V8 ≤ 1 bp restatement drift. `[recommended — Adam to confirm/override]` These are judgment calls made before
   seeing anything; they must be his before the freeze, because after the look they cannot be changed.

7. **If R3 fires (bucket resolution insufficient) — close as NOT MEASURABLE, or cost out paywalled constituent
   data as a separate decision?** `[recommended — Adam to confirm/override: close as NOT MEASURABLE and record
   the paid-data option as a costed item, not a phase.]` Buying constituent history is a purchasing decision with
   ongoing maintenance, in the same class as the Phase 2 deep-history question that was deliberately deferred.

---

## Charter-first status

**Clean.** No implementation exists for this signal: `scripts/` contains no concentration module, and no
concentration observable has been computed. Unlike Phases 1.5 and 2, which disclosed partial inversions of D-15,
Phase 4 is being registered fully before any construction.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/04-concentration-signal/04-CHARTER-KICKOFF|04-CHARTER-KICKOFF]]

<!-- LINKS:END -->
