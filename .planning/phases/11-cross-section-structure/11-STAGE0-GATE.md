# Stage-0 Gate — Cross-Sectional Dependency Structure (Phase 11)

> # OUTCOME — PARKED 2026-08-11, PRE-LOOK, ON ALGEBRA
>
> **The one look was never spent. The design was killed by a literature review and a derivation, before
> any statistic was computed on real data.** Adam's ruling, same day the gate was written.
>
> **Read this block before the body. Everything below it is the record of what was *registered*, kept
> unedited so the reasoning is auditable — but the design it registers does not survive.**
>
> ### Why Ψ fails, in one line
>
> ```
> Ψ² = s² / (s² + ρ̄²)      s = standard deviation of the off-diagonal correlations
> ```
>
> Ψ is a bounded monotone transform of the **coefficient of variation of the off-diagonal
> correlations** — a function of exactly two moments. It is therefore **permutation-invariant**:
> shuffle *which* pairs are coupled and Ψ does not move. **The entire relational content the phase
> existed to measure is absent from the statistic.** Ψ is the *norm* of the interesting object
> (`R_t − R_eq`); taking that norm discards everything that made the object interesting.
>
> ### Three further findings, any one of which is disqualifying
>
> 1. **Prior art.** Ψ's numerator is exactly **Ledoit & Wolf's γ̂** (2004, *JPM* 30(4)) — the
>    misspecification term of the constant-correlation shrinkage target, computed on every rebalancing
>    date since 2004. Its denominator is `p ×` **John's (1971) sphericity statistic**. Their δ̂ is
>    additionally a *sampling-error-normalised* version of the same quantity, which is what this gate's
>    bootstrap null was going to supply by hand.
> 2. **`c_t` is published.** `c_t = mean_i log σ_it` is **Herskovic, Kelly, Lustig & Van Nieuwerburgh,
>    *JPE* 128(11) (2020), Table 5** — same estimator, described there as "essentially the first
>    principal component." At sector level, Barigozzi, Brownlees, Gallo & Veredas (*JoE* 182(2), 2014).
> 3. **The registered bars do not work.** **E4 is not decisive** — with `R_eq` recentred each window it
>    converges to a reliability coefficient ≈0.75–0.87, flat in h, **on a completely static matrix**, so
>    it passes trivially. And **the expected direction was backwards**: a one-factor model with dispersed
>    loadings gives Ψ ≈ 0.20–0.48, Ψ measures *loading heterogeneity rather than factor count*, and
>    Ψ → 0 as factor variance rises — so **Ψ falling in 1987/2008/2020 is the null being confirmed**, not
>    a finding. Ψ's sampling floor also moves strongly *inverse* to ρ̄ (0.395 at ρ̄=0.2 vs 0.095 at
>    ρ̄=0.6, T=125), threatening **E2 from the null side**.
>
> ### What survives, and is NOT parked
>
> - **The research objective.** The architecture Adam stated: `validated axes → joint state → joint
>   rarity / geometry → economic consequences → trading hypothesis`. This is Phase 10 **Level 2**, whose
>   seam (`assumption_ledger.level2_context()`) is registered and unbuilt. It is gated on having admitted
>   axes, not on this phase.
> - **The audit framing.** The literature review's strongest finding is a *plausible unclosed gap*
>   (**UNOPPOSED, not confirmed** — the MI-010 G4 standard): the Forbes–Rigobón (2002) /
>   Boyer–Gibson–Loretan (1999) conditioning bias has never been carried over to network estimators, even
>   though MST length, graphical-lasso edge counts and connectedness indices are all deterministic
>   functions of the same biased ρ̂. Onnela et al. (2003) report ρ(ρ̄, tree length) = **−0.98** and read
>   the redundancy as *validation of the method*.
> - **The sector/industry universe**, as the place to test whether joint market states have
>   cross-sectional consequences — not as the place to manufacture another aggregate.
>
> ### The rule this phase paid for
>
> **Do not replace Ψ with another clever scalar.** A sophisticated-looking statistic reduced to a
> permutation-invariant function of two moments. The lesson is to *preserve relational information*
> rather than manufacture a new aggregate. Any successor must be **pair-resolved** — the residual matrix
> `R_t − R_eq` itself, not a norm of it.
>
> ### Corrections to the body below
>
> - **The Marchenko–Pastur edge is wrong.** §Registered construction states 1.60 at N=10, W_A=125. The
>   correct value is **1.646**: q = 0.08, (1+√0.08)² = 1.283² = 1.646.
> - **"Nothing implemented. No `scripts/` module exists" is false.** `scripts/cross_section.py` and
>   `tests/test_cross_section.py` were written 2026-08-11, after this gate. 254 tests pass. The four
>   statistics are implemented; **none has been run against repo data.**
> - **Disclosure — unsanctioned computation.** Research subagents were instructed not to run
>   experiments; two did. Against `industry10_daily.csv`, `industry48_daily.csv` and the market series
>   they computed rolling average pairwise correlations and crisis-window values, PC1 variance shares,
>   Marchenko–Pastur edge counts, Bai–Ng and Ahn–Horenstein factor counts, market-model R² by decade, a
>   CLMX reconstruction, log-realized-volatility moments, and a Fama–French (1997) Table 2 replication
>   (obtained 0.626 against a published 0.63). No output was carried into any repo file. Most of it is
>   known-answer replication, which this gate treats as pre-look construction verification — **but ρ̄_t
>   has no published target on this panel, so computing it is a genuine first sighting of a registered
>   E2 benchmark.** Recorded rather than relied upon, on the MI-013 standard. Moot for this phase, which
>   is parked; it must be carried forward if E2 is ever reused.
> - **One data-integrity item to verify, unrelated to any research question:** the 10-industry trailing
>   average pairwise correlation was reported ending at a century-low value at the end of the panel.
>   Treat as a possible tail-of-file defect, not a finding.

**DRAFT — NOT SIGNED, AND NOW SUPERSEDED BY THE OUTCOME BLOCK ABOVE.** No look was spent. Everything
below is a *registered intention* that did not survive review. Data inspection at the time of writing was
coverage only: row counts, column spans, date ranges from `data/processed/MANIFEST.csv`.

**Dated** 2026-08-11 · **version** v0.1-draft · filled against `research-charter-template.md` v1.1.

---

## What this phase is, and what it is not

**It is not a new signal.** It is a **construction/redundancy gate** on a proposed *class* of signal —
the cross-sectional dependency structure of the equity market. Its output is `PROCEED-TO-CHARTER` or
`DROP`, not a reading, not a status, not a maturity tag.

**It therefore does not spend a one-look**, on the same footing as
`results/concentration_gate.csv` (C1–C5), which this repo already treats as pre-look construction
verification. The gate's pass/fail criteria are registered below, before the data is touched. If the
gate passes, a full charter with its own registered one-look is written for the experiment that
follows. If it fails, the class is dropped and a ledger row records why.

**Rationale for the gate existing at all.** Four separate proposals in this repo have turned out to be
mechanically implied by a simpler quantity already admitted (see the standing lesson below). This gate
tests that redundancy *before* a program is built on top of it, rather than after.

---

## Header

- **Candidate class** — cross-sectional dependency structure of the equity market
- **Assumption monitored** — *(none yet — a gate does not monitor an assumption)*
- **Native clock** — see §Temporal resolution. Quarterly, not daily.
- **Maturity ceiling, registered pre-look** — **`research`, permanently.** The repo's recorded finding
  (`.planning/archive/dropped-signals/05-ABSORPTION-DROPPED.md`) is that no international industry
  sorts are published on this source, so `run_oos.py` cannot serve this class at all. Same position as
  Phase 9 (tail). **Verify this claim against the source before signing** — it determines the ceiling.
- **Research question** — *Does the cross-section of industry return and volatility series contain
  dependency structure that a single scalar (average pairwise correlation) cannot express?*
- **Charter-first status** — clean. Nothing implemented. No `scripts/` module exists.

---

## Stage-0 Relevance Gate (default = NO)

**G1 — what important question does this class answer?**
Whether the market's risk configuration is *relational* — a property of how components are arranged —
or merely a set of component-level readings. Every axis in the current observatory measures a property
of a component (volatility level, correlation sign, valuation ratio, credit residual). None measures
the arrangement. **PASS.**

**G2 — why is that important?**
The failure mode of a component-level observatory is silent: every axis can read unremarkably while the
cross-section reorganizes. If that reorganization carries information, an observatory built only from
scalars cannot see it by construction. **PASS.**

**G3 — information NOT already available from existing signals?**
**This is the gate's weak point and the reason the phase exists.** Under exact equicorrelation ρ across
N standardized series, λ₁ = 1+(N−1)ρ and λ₂…λ_N = 1−ρ — the *entire spectrum*, and therefore every
network summary derived from it, is a function of one scalar. MI-007 was dropped on the adjacent
finding that AR₁ = [1+(N−1)ρ̄]/N is affine in ρ̄. So the non-redundant content of any dependency
statistic is exactly the **departure of the correlation matrix from the one-parameter equicorrelation
family**, and nothing else. **CONDITIONAL — this gate tests G3 directly rather than asserting it.**

**Important distinction, and the strongest part of the case:** the equicorrelation algebra applies to
the *return* correlation matrix. It says nothing about the **volatility-dependency** matrix
(correlation of industry log-volatility innovations), which is a different object with an open
redundancy question. Both are tested; they are reported separately and never pooled.

**G3′ — can the unique information be READ live?**
**FAIL, and registered as such now rather than discovered later.** The 10-industry panel ends
2026-05-29 against a 2026-08-11 wall clock — a **74-day publication lag**, the same lag that killed
MI-007 on this gate. **Consequence, registered:** this phase is chartered as a *measurement* question,
for which G3′ does not bind. Its path to becoming a live observatory axis is blocked by that lag
unless a lower-latency cross-section is sourced. **No result from this phase may be presented as a live
reading**, and a future agent proposing to promote it must clear G3′ first.

**G4 — leave-one-out: would the observatory be meaningfully less informative without it?**
Undetermined — that is the gate's output, not its input.

**G5 — strong theoretical/empirical prior?**
**Moderate to strong, and partly against novelty.** Campbell, Lettau, Malkiel & Xu (2001) establish an
industry-level volatility component. Herskovic, Kelly, Lustig & Van Nieuwerburgh (2016) establish a
common factor in idiosyncratic volatility. Barigozzi & Brownlees (2019) estimate volatility-dependency
networks directly. Billio, Getmansky, Lo & Pelizzon (2012) and Diebold & Yılmaz (2014) establish
directed, time-varying connectedness that rises in crises. **Expect confirmation, not discovery** —
which under the 2026-08-06 objective restatement is the pass condition, not a failure.

---

## Registered construction

**Universe: N = 10** (`data/processed/industry10_daily.csv`, 26,253 rows, 1926-07-01..2026-05-29, ten
complete columns, no ragged starts).

**Justification, and it is measurement validity only:** at N=10, T=125 the ratio q = N/T = 0.08 keeps
the correlation matrix well conditioned (Marchenko–Pastur bulk edge (1+√q)² = 1.60); at N=48 the window
needed for a stable estimate (~2 years) exceeds the timescale of the phenomenon. 45 undirected pairs
versus 1,128 controls the multiple-testing burden. The 48-industry panel additionally has ragged starts
(Soda from 1963) and thin early industries whose "industry volatility" is a handful of firms.

> **D-10 note, recorded rather than omitted.** A downstream-implementation rationale for N=10 was
> raised on 2026-08-11 and **excluded as out of boundary**. The choice rests on conditioning,
> multiplicity and measurement validity alone. Recording the exclusion makes it auditable.

**Transformations** (all trailing-only, all registered under `assert_causal` before any statistic):

| Object | Definition |
|---|---|
| σ_{i,t} | trailing realized volatility, window W_σ, via the existing `causal` primitives (D-20 — reuse, do not reimplement) |
| x_{i,t} | log σ_{i,t} |
| c_t | (1/N) Σ_i x_{i,t} — **equal-weighted**, not index volatility, which contains ρ̄ by the variance identity |
| D_{i,t} | x_{i,t} − c_t. **Σ_i D_{i,t} = 0 by construction**; Cov(D) has rank ≤ N−1 and that deficiency is not a finding |
| R^r_t | correlation of daily returns over W_A |
| R^v_t | correlation of **Δx_{i,t}** over W_A — differences, not levels (log realized vol is near-unit-root persistent; correlating levels manufactures correlation from shared trends) |

**To verify and register before use:** value- vs equal-weighted panel, percent vs decimal units, total
vs excess returns.

---

## The statistic

**Structural residual share**, the fraction of off-diagonal structure a single scalar cannot express:

```
Ψ_t = ‖R_t − R_eq(ρ̄_t)‖_F / ‖R_t − I‖_F        R_eq(ρ̄) = (1−ρ̄)·I + ρ̄·11′
```

Chosen because it is orthogonal to the redundancy hazard **by construction**. Computed on both R^r_t
and R^v_t, reported separately.

Also computed, as redundancy benchmarks only: ρ̄_t (mean off-diagonal) and c_t.

**Nothing else.** No graphical lasso, no VAR, no thresholded adjacency, no eigenvalue counting beyond
the MP diagnostic. Every one of those introduces a tuning parameter, and a tuning parameter is a
density knob.

---

## Temporal resolution — registered, not chosen after the fact

**W_σ = 21, W_A = 125 primary; W_A = 250 as a second lens.** Two windows, both fixed here, before the
look. (Two-lens pattern follows Phase 6's registered 120m + trailing-60m construction.)

A flat rolling window's response to a step change is a linear ramp: 50% at W/2, 100% at W. With the
volatility nesting, total memory is W_A + W_σ − 1 = 145 days, half-response ≈ 73 days.

> **Registered scope limitation.** This estimator resolves dependency structure on a **quarterly**
> timescale. A topology shift resolving in under ~6 weeks is **not observable** here, and any such
> claim would be an artifact of plotting a smoothed quantity daily. R_t is not a daily network and
> must never be presented as one.

**Overlap, registered for any future propagation work:** a W_σ-day rolling window induces an
**MA(W_σ−1)** structure in Δx. Any propagation test at lag k < W_σ is contaminated by construction. At
W_σ = 21, one-day propagation is untestable on this data.

**Window-shopping is closed.** Re-running the gate on a different W_A after a failure is spec-searching
on the answer sheet. The windows above are the windows.

---

## Null model

**H₀: R_t = R_eq(ρ̄_t) at every t** — the correlation matrix is at all times a member of the
one-parameter family, with ρ̄_t free to move as it empirically moves, volatilities following their
actual empirical paths, innovations t-distributed with empirically matched degrees of freedom.

Deliberately generous: it grants everything except cross-sectional heterogeneity in the structure.

Implementation: parametric bootstrap, W_A observations per date drawn from R_eq(ρ̄_t) scaled by the
empirical volatility path.

**Why mandatory.** At N=10, W_A=125 sampling error alone gives off-diagonal correlations a standard
error of roughly (1−ρ²)/√W_A ≈ 0.08, so **Ψ_t is strictly positive under H₀**. Without the bootstrap
there is no way to distinguish structure from 1/√T. Fat tails plus time-varying volatility also mean
effective sample size falls in stress, so Ψ_t drifts upward in crises *under the null* — using the
actual volatility path is what catches that.

---

## Pass criteria — all four required, registered conjunctively

| | Bar |
|---|---|
| **E1 magnitude** | Ψ_t exceeds the H₀ 95th percentile over a substantial fraction of the sample, assessed as a whole-sample summary under block bootstrap — never pointwise across autocorrelated dates |
| **E2 non-redundancy** | \|Spearman(Ψ_t, ρ̄_t)\| < 0.90 **and** \|Spearman(Ψ_t, c_t)\| < 0.90, **and** nonparametric R² of Ψ_t on (ρ̄_t, c_t) jointly < 0.90. Threshold carried from Phase 6's registered R4 bar — not a new knob |
| **E3 persistence** | ACF(Ψ_t) materially exceeds what H₀ generates |
| **E4 pattern persistence — DECISIVE** | corr( vec(R_t − R_eq), vec(R_{t+h} − R_eq) ) at **non-overlapping h = W_A** is well above its H₀ distribution |

**E4 is make-or-break, and is pre-called as the most likely failure.** E1–E3 can all pass on a
departure whose *pattern* reshuffles between windows — that is a magnitude finding, not a relational
one. A real dependency structure must be recognizable from one independent window to the next. If which
pairs deviate is white noise across windows, there is no map to draw and every downstream experiment
estimates noise.

**Dimensionality is NOT a bar.** "We found k > 1 dimensions" is guaranteed by sampling noise and is not
evidence. Only E4 discriminates.

---

## Reject conditions — registered consequence is DROP

- **F1** — Ψ_t inside the H₀ band. No structure beyond equicorrelation.
- **F2** — Ψ_t significant but E2 fails. It is the absorption ratio in a fourth costume; **MI-007
  repeating**, which is exactly what the ledger exists to prevent.
- **F3** — E4 at chance. Departures are estimation noise.

**Any of F1/F2/F3 ⇒ DROP the class.** Not demote, not "try N=48", not "try another window". Follows
Phase 6's precedent where R2 firing was registered as DROP and the revisit-later option was explicitly
offered and rejected.

A DROP here is a legitimate output and gets a dropped-signal memo plus a ledger row, on the standard of
MI-007/MI-008 — **not** the three-line disposition that MI-013 records as a process failure.

---

## Replication before research

Run first, because it has a known answer and validates the pipeline for the price of an afternoon:

1. **Campbell, Lettau, Malkiel & Xu (2001)** market/industry variance decomposition, restricted to the
   two levels this data supports. If a known result cannot be reproduced, the construction is broken.
2. **Sanity:** ρ̄_t should spike in 1987-10, 2008-09/10, 2020-03.

Separation of claims, to be maintained in the write-up:

| Category | Content |
|---|---|
| Replication (known answer) | CLMX decomposition · ρ̄_t crisis spikes |
| Methodological validation (no market claim) | H₀ sampling distribution of Ψ_t · estimator resolution measured against simulated step changes · MP bulk edge · MA(W_σ−1) overlap structure · rank deficiency of Cov(D) |
| Genuinely new | Whether the departure from equicorrelation in **R^v_t** is larger than sampling noise, not a transform of ρ̄_t/c_t, and pattern-persistent |

The new part is **narrow and largely methodological**. Say so in the write-up.

---

## Boundary

- Industry names are vendor identifiers, covered by the documented exception in `CLAUDE.md`.
- **"Sector rotation" and equivalents may not be used as configuration labels** — an allocation
  concept. Label configurations by their measured statistics only.
- The `EMITTERS` set is untouched by this phase. A gate produces no observation record.

---

## Relationship to MI-007 — this is materially a reopening

MI-007 (absorption) was dropped 2026-08-09 on G3′, not on the science. This phase asks a related
question with G3′ registered as non-binding *because the output is a measurement, not a live reading*.

**Required before signing:** a ledger row — either a new `MI-014` cross-referencing MI-007, or an
explicit amendment to MI-007 — recording the reopening and the reason G3′ does not bind. Silence
recreates the rediscovery hazard the ledger exists to prevent.

---

## Standing lesson this phase institutionalizes

Proposed for `RESEARCH-LEDGER.md` as a cross-cutting section (the existing "Standing lessons" block
sits under the ALGO table and is scoped to regime/state proposals; this class spans MI and ALGO rows):

> **Construction-implied structure.** If a proposed structural measure can be mechanically generated by
> a simpler quantity already admitted, it is not a new dimension until that redundancy is tested and
> rejected. Instances: **ALGO-003** (a regime fitted on an asset's own returns rediscovers volatility) ·
> **MI-007** (AR₁ = [1+(N−1)ρ̄]/N, affine in ρ̄ under equicorrelation) · **MI-010 G4** (the EBP regresses
> out a distance-to-default that is itself a function of equity volatility, so measured orthogonality is
> partly manufactured) · **the sector-volatility residual proposal, 2026-08-11** (apparent residual
> structure shown to carry the coupling channel). **The test precedes the build, not the write-up.**

---

## Open items before this gate is signed

1. **Construction gate vs spent look** — recommended as a gate (§What this phase is). Adam's ruling.
2. **Ledger row** for the MI-007 reopening — new `MI-014` or an amendment. Adam's call.
3. **Verify** no international industry sorts exist on the source, since it fixes the maturity ceiling.
4. **Verify** the panel's weighting, units and total-vs-excess basis.
5. Capacity: migration hard stop **2026-08-25**.
