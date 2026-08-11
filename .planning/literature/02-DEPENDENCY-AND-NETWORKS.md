# 02 — Cross-Sectional Dependency Structure, Financial Networks, Dynamic Connectedness

**Literature review · DRAFT v0.1 · dated 2026-08-11**
Scope: the published state of the art against which Phase 11
(`.planning/phases/11-cross-section-structure/11-STAGE0-GATE.md`) must justify its existence.

> **Boundary note.** This document is a measurement-literature review. It contains no allocation,
> exposure, position, sizing, trading or recommendation concept, and none of the reviewed results is
> reported as an actionable claim. Journal names and vendor filenames (e.g. *Journal of Portfolio
> Management*, `10_Industry_Portfolios_Daily_CSV.zip`, "value-weighted") appear only as **source
> identifiers**, the documented exception in `CLAUDE.md`. Where a cited paper's own contribution is a
> decision rule, that part is deliberately not reported.

> **Verification key.** Every factual claim carries one of:
> **[V]** verified against a source fetched during this review ·
> **[M]** from trained memory, plausible and standard, **not** re-verified — treat as a citation to
> check before it is relied on in a signed charter ·
> **[U]** could not verify · **[INF]** my inference/derivation, not anyone's published claim ·
> **[SIM]** a small synthetic simulation run during this review on generated data — **not a published
> result and not a citation.** No repo data was touched and no look was spent; treat every [SIM] result
> as a hypothesis to replicate before it is relied on.
> Section 4 and Section 9 are the two places where the distinction matters most.

---

## 0. Executive answer, before the detail

1. **Almost everything in the Phase-11 construction already exists in print**, in a more general form.
   The residual-from-equicorrelation idea is the complement of Engle & Kelly's DECO restriction [V];
   volatility-dependency networks were estimated directly by Barigozzi & Brownlees [V]; the
   "structure beyond one scalar" question is the whole content of the absorption-ratio and
   random-matrix literatures. **Expect confirmation, not discovery** — which the gate itself already
   says, correctly.

2. **The one thing that is genuinely thin in the literature is exactly the thing the gate is built
   around**: a *null-calibrated* statement of how much apparent structural change is free. The
   near-universal practice is to plot an estimated network statistic through time and narrate its
   crisis behaviour, with no sampling distribution attached. See §4.

3. **The critique the caller asked about — that crisis "densification" may be an estimator artifact —
   is NOT published. Its three ingredients are, separately, and nobody has joined them.**
   - the **theory** is proved: Basu & Michailidis (2015, *Annals of Statistics* 43(4):1535–1567) show the
     valid LASSO penalty for a sparse VAR scales **linearly with the innovation noise level**,
     λ_n ≳ c₀·2π[M(f_X) + M(f_ε)]·√(log p / n) [V]. Hold λ fixed while volatility rises and you are
     running a penalty below the level the theory requires. They never point this at the empirical
     claim;
   - the **confession** is in print: Hautsch, Schaumburg & Schienle (2014, *IJF* 30(3):781–794) attribute
     the volatility of their estimated network to "the hard thresholding with which other companies'
     loss exceedances are measured and thus appear and disappear as potential candidates for network
     links over time", and leave the fix "for future work" [V]. Two paragraphs, not a study;
   - the **confound result** is published: Krampe & Margaritella (2024/25, arXiv:2402.02482) find crisis
     connectedness spikes are driven by the **common component**, not by the idiosyncratic/bilateral
     network [V];
   - the **ancestor** is settled science one dimension down: Forbes & Rigobon (2002); Boyer, Gibson &
     Loretan (1999) [M].

   **No paper holds a true network fixed, drives it with the empirical volatility path, and reports how
   much densification a standard estimator invents.** In particular, Billio et al. (2012) calibrate their
   Monte Carlo null **once**, from a constant-variance IID-normal DGP, and compare **every** rolling
   window against it [V] — a design that is structurally incapable of detecting the artifact it would need
   to rule out. §4 states this precisely; §9 turns it into a one-panel experiment.

4. **Temporal resolution is systematically glossed over.** The dominant practice plots a 100–250-day
   rolling-window statistic at daily frequency, where consecutive points share ≥99% of their data. The
   ramp response and the induced autocorrelation are essentially never reported. §5. The Phase-11 gate
   is, on this specific point, **more honest than the published literature it is drawing on** — that is
   a real, if narrow, contribution.

5. **A specific technical finding against the current gate text** (§6.4, [INF], derived from
   `scripts/cross_section.py`): Ψ is algebraically a monotone transform of the *coefficient of
   variation* of the off-diagonal correlations, Ψ = CV/√(1+CV²) with CV = sd(ρ_ij)/ρ̄. It therefore
   carries a **built-in negative mechanical dependence on ρ̄** — under the gate's own null, Ψ falls as
   ρ̄ rises. The E2 bar (|Spearman(Ψ, ρ̄)| < 0.90 ⇒ else DROP) is consequently **testing algebra, not
   redundancy**, and can fire for a reason that has nothing to do with the science. This should be
   fixed before signing.

6. **`scripts/cross_section.py` exists** (142 lines, four statistics + plumbing) while the gate document
   states "Nothing implemented. No `scripts/` module exists." That sentence is stale and should be
   corrected before signature; nothing in the module computes an empirical result, so the charter-first
   discipline is intact in substance.

---

## 1. What has already been solved?

Framed as: *what would a competent referee say is no longer an open question?*

**1.1 That cross-sectional dependency in equity returns is time-varying, and rises in stress.**
Settled beyond dispute, by every method that has been pointed at it: multivariate GARCH/DCC (Engle
2002, *JBES* 20(3):339–350) [M]; extreme-value correlation (Longin & Solnik 2001, *Journal of Finance*
56(2):649–676) [M]; asymmetric correlation (Ang & Chen 2002, *JFE* 63(3):443–494) [M]; correlation
network topology (Onnela et al. 2003, *Physical Review E* 68:056110) [M]; variance-decomposition
connectedness (Diebold & Yılmaz 2009, 2012, 2014) [M/V]; Granger-network density (Billio, Getmansky, Lo
& Pelizzon 2012, *JFE* 104(3):535–559) [V]. Any Phase-11 result showing "dependency rises in 1987/2008/2020"
is a **pipeline check**, not a finding, and must be reported as such.

**1.2 That the equity correlation matrix is dominated by one large eigenvalue.**
Settled. Laloux, Cizeau, Bouchaud & Potters (1999, *Physical Review Letters* 83(7):1467–1470) and Plerou,
Gopikrishnan, Rosenow, Amaral, Guhr & Stanley (2002, *Physical Review E* 65:066126) [M] establish that
the bulk of the eigenvalue spectrum of a large equity correlation matrix is statistically
indistinguishable from Marchenko–Pastur noise, with a small number of deviating eigenvalues led by a
dominant market mode. The repo's own MI-007 disposition rests on the algebraic corollary.

**1.3 That the first eigenvalue is close to an affine function of average pairwise correlation.**
Solved *analytically* and recorded in this repo already
(`.planning/archive/dropped-signals/05-ABSORPTION-DROPPED.md`, G3): under exact equicorrelation ρ across
N standardised series, λ₁ = 1 + (N−1)ρ and λ₂..λ_N = 1 − ρ, so AR₁ = [1+(N−1)ρ]/N is affine in ρ̄ [V,
in-repo]. I could not find a paper that states this as an explicit critique of the absorption ratio [U]
— the algebra is elementary and appears in the equicorrelation/DECO literature (Engle & Kelly 2012, *JBES*
30(2):212–228, DOI 10.1080/07350015.2011.652048) [V] rather than as a named criticism. **Inference [INF]:**
this is a rediscovery of standard algebra, not a novel critique, and should not be written up as one.

**1.4 That volatility itself has a strong common cross-sectional factor.**
Settled. Campbell, Lettau, Malkiel & Xu (2001, *Journal of Finance* 56(1):1–43) decompose return variance
into market, industry and firm levels [M]; Herskovic, Kelly, Lustig & Van Nieuwerburgh (2016, *JFE*
119(2):249–283) establish a dominant common factor in *idiosyncratic* volatility (the CIV factor) [M];
Barigozzi, Brownlees, Gallo & Veredas (2014, *Journal of Applied Econometrics*) disentangle systematic and
idiosyncratic dynamics in panels of volatility measures [M]. **This matters directly for Phase 11:** the
gate's argument that R^v (the volatility-dependency matrix) is "a different object with an open redundancy
question" is weaker than the gate implies. The common-factor-in-volatility result *is* the c_t channel,
and the gate already removes c_t by construction — so the open question is narrower than "is there
structure in volatility dependency" (there is, established) and is really "does the residual after
removing c_t carry a persistent pattern". §6.

**1.5 That measured comovement is biased upward when it is measured on high-volatility samples.**
Solved, rigorously, in the bivariate case. Forbes & Rigobon (2002, *Journal of Finance* 57(5):2223–2261)
[M]: if the source market's variance rises by a proportion δ with the underlying linear relationship
unchanged, the measured correlation rises, and the unbiased quantity is
ρ* = ρ / √(1 + δ(1 − ρ²)) [M — verify the exact algebraic form before using]. Their conclusion: almost all
of the apparent "contagion" in the 1997 Asian, 1994 Mexican and 1987 US episodes disappears after the
adjustment; there is "no contagion, only interdependence". Boyer, Gibson & Loretan (1999, Federal Reserve
IFDP 597) and Loretan & English (2000) [M] show the sharper version: conditioning on a high-volatility
sub-sample raises the measured correlation **even under a constant bivariate normal DGP** — a pure
selection artifact. Corsetti, Pericoli & Sbracia (2005, *Journal of International Money and Finance*
24(8):1177–1199) [M] push back that Forbes–Rigobon implicitly assumes no rise in idiosyncratic variance
and, relaxing it, recover "some contagion, some interdependence".

**This is the intellectual ancestor of the crux question in §4, and it is the single most important set
of citations in this document.** The bivariate problem was recognised, formalised, and largely settled by
2002. The *multivariate graph-estimator* version of the same problem was, as far as I can establish, never
done.

**1.6 That the number of "real" factors is a hard, sample-size-dependent question.**
Solved in the sense of having a mature literature: Bai & Ng (2002, *Econometrica* 70(1):191–221) information
criteria [M]; Onatski (2010, *REStat*) edge distribution [M]; Ahn & Horenstein (2013, *Econometrica*)
eigenvalue ratio [M]. The relevant lesson for Phase 11 is negative and the gate already states it:
**"we found k > 1 dimensions" is not evidence**, because the estimated count is a function of N/T.

---

## 2. What methods already exist?

A taxonomy, because Phase 11's proposed statistic sits inside it rather than beside it.

| Family | Canonical reference | What it estimates | Tuning knobs (= density knobs) |
|---|---|---|---|
| **Marginal correlation** | any | ρ̄_t, ρ_ij,t | window W |
| **Spectral / absorption** | Kritzman, Li, Page & Rigobon (2011, *JPM* 37(4):112–126) [V] | share of variance in top n eigenvectors | W (500d), n (=N/5) |
| **Random-matrix filtering** | Laloux et al. (1999); Plerou et al. (2002) [M] | eigenvalues outside the MP bulk | q = N/T, clipping rule |
| **MST / PMFG topology** | Mantegna (1999, *EPJ B* 11:193–197); Tumminello et al. (2005, *PNAS* 102:10421) [M] | a filtered graph from d_ij = √(2(1−ρ_ij)) | filtration rule, W |
| **Partial correlation / precision** | Friedman, Hastie & Tibshirani (2008, *Biostatistics* 9(3):432–441) glasso [M]; Meinshausen & Bühlmann (2006, *AoS* 34(3):1436–1462) [M] | conditional independence graph | penalty λ, W |
| **Sparse VAR + sparse precision, jointly** | **Barigozzi & Brownlees (2019, *Journal of Applied Econometrics* 34(3):347–364), "NETS"** [M] | contemporaneous partial-correlation network **and** long-run/Granger network, on volatility | two λ's, selection criterion, W |
| **Variance-decomposition connectedness** | Diebold & Yılmaz (2009 *EJ* 119(534):158–171; 2012 *IJF* 28(1):57–66; 2014 *J. Econometrics* 182(1):119–134) [V] | pairwise shares of H-step FEV attributable to each shock | W, VAR lag p, horizon H, identification (Cholesky vs generalized), **normalisation scheme (row / column / scalar)** |
| **Regularised high-dimensional connectedness** | Demirer, Diebold, Liu & Yılmaz (2018, *JAE* 33(1):1–15) [V] | same, N ≈ 150 | + elastic-net penalty λ (**re-selected by 10-fold CV in each rolling window** — see §4) |
| **Granger-causality networks** | Billio, Getmansky, Lo & Pelizzon (2012, *JFE* 104(3):535–559) [V] | directed adjacency from pairwise Granger tests | W (36 months), significance level α (**5%, uncorrected**), lag order (BIC) |
| **Factor-first networks** | Barigozzi & Hallin (2017, *JRSS-C* 66(3):581–605) [V]; Krampe & Margaritella (2024/25) [V] | network on the **idiosyncratic** component only, after a factor model | number of factors + all the penalty knobs |
| **Tail/quantile networks** | Hautsch, Schaumburg & Schienle (2015, *Review of Finance* 19(2):685–738) [M]; Corsi, Lillo, Pirino & Trapin (2018, *Journal of Financial Stability*) [M] | tail-risk directed links | quantile level, LASSO penalty, W |
| **Point-process contagion** | Aït-Sahalia, Cacho-Díaz & Laeven (2015, *JFE* 117(3):585–606) [M] | mutually exciting jump intensities | jump threshold, decay parameterisation |
| **Equicorrelation restriction** | Engle & Kelly (2012, *JBES* 30(2):212–228) [V] | one scalar ρ_t (DECO) or block-scalars (Block-DECO) | block structure, GARCH spec |
| **Frequency-domain connectedness** | Baruník & Křehlík (2018, *Journal of Financial Econometrics* 16(2):271–296) [M; arXiv:1507.01729 verified [V]] | connectedness split by frequency band | band cut-points + all D-Y knobs |
| **TVP-VAR connectedness** | Antonakakis, Chatziantoniou & Gabauer (2020, *JRFM* 13(4):84) [M] | D-Y measures without a rolling window | forgetting factors κ₁, κ₂ — *the window knob in disguise* |

**Two observations that matter for Phase 11.**

**(a) Every method in the table has at least one tuning knob that directly controls the estimated
density or the estimated structure.** The Phase-11 gate's decision to admit *no* threshold, *no* penalty
and *no* eigenvalue count — Ψ is a continuous, knob-free functional of R_t given (W_σ, W_A) — is a real
methodological choice and is the strongest single design decision in the document. Ψ has exactly two
knobs (the two windows) and both are registered before the look. **[INF]** I am not aware of a published
network-structure statistic with fewer free parameters.

**(b) Barigozzi & Brownlees (2019) is the closest published baseline and Phase 11 must cite it as such.**
NETS estimates, jointly and by LASSO-type penalisation, (i) a sparse VAR autoregressive matrix — the
"long-run"/Granger network — and (ii) a sparse concentration matrix of the innovations — the
contemporaneous partial-correlation network; the empirical application is to a panel of US stock
*realized volatilities* [M — verify panel size, sample period and whether they use log-RV levels or
differences; this determines whether their object is the same as R^v]. If their application is on
**levels** of log realized volatility, Phase 11's decision to correlate **Δx** rather than x is a genuine
methodological improvement with a stateable reason (near-unit-root persistence manufactures correlation
from shared trends), and should be written up as such. If they already difference, Phase 11 is a
re-implementation. **This is the single highest-value citation check in this document.**

---

## 3. What empirical findings are established, and which are contested?

### 3.1 Established (high confidence, replicated, mechanism-plausible)

| Finding | Source | Status |
|---|---|---|
| Average pairwise equity correlation spikes in 1987-10, 2008-09/10, 2020-03 | ubiquitous | **Established.** Qualitative only — no canonical number to match, because every paper uses a different universe. |
| The correlation matrix has one dominant eigenvalue; the rest of the spectrum is close to MP noise | Laloux et al. (1999); Plerou et al. (2002) [M] | **Established** for large-N individual-stock panels. **Not** established for N=10 industries, where q = N/T is tiny and the bulk is narrow. |
| Firm-level idiosyncratic volatility has a strong common factor | Herskovic et al. (2016) [M] | **Established.** |
| Return variance decomposes into market/industry/firm components with the firm component largest | Campbell, Lettau, Malkiel & Xu (2001) [M] | **Established**; magnitudes precise in the paper, but see §10 for why exact replication on this repo's data is not possible. |
| Measured bivariate correlation rises mechanically with the conditioning variance | Forbes & Rigobon (2002); Boyer, Gibson & Loretan (1999) [M] | **Established, and formalised.** |
| Estimated network/connectedness measures rise in crises | Billio et al. (2012) [V]; Diebold & Yılmaz (2014) [M]; Onnela et al. (2003) [M] | **Established as a measurement fact.** Its *interpretation* is contested — §4. |
| Volatility connectedness/spillovers rise in crises across asset classes | Diebold & Yılmaz (2012, 2014) and a very large follow-on literature [M] | **Established as a measurement fact**, with the same interpretive caveat. |

### 3.2 Contested or weakly supported

| Claim | Why contested |
|---|---|
| **"Network topology changes in crises" (as distinct from "correlations rise")** | MST tree length is a *deterministic decreasing function* of the correlations entering it [INF, elementary]. Onnela et al.'s (2003) crash-time tree shrinkage is therefore guaranteed by ρ̄ rising, and is only a topology finding if it survives a control for ρ̄. I could not find a paper in the MST literature that imposes that control [U]. Partial-correlation-based variants (Kenett et al. 2010, *PLoS ONE* 5(12):e15032) [M] are a partial answer because partial correlations are not monotone in ρ̄, but they introduce an inversion step whose noise properties in stress are not characterised. |
| **The absorption ratio as an early-warning measure** | Kritzman, Li, Page & Rigobon (2011) [V] report it as an early warning. Giglio, Kelly & Pruitt (2016, *JFE* 119(3):457–471) evaluate a large set of systemic-risk measures for out-of-sample predictive content and reach a far more sceptical conclusion, with an explicit multiple-testing correction across measures [M — get their exact verdict on the absorption ratio before citing it either way]. **Treat the early-warning claim as contested.** |
| **Systemic-risk measures as informative beyond volatility and beta** | Benoit, Colletaz, Hurlin & Pérignon show several popular systemic-risk measures can be written as transformations of ordinary market-risk quantities (beta, VaR), and that a one-factor linear model explains most of the cross-sectional variability of the estimates [V, from abstract]. Löffler & Raupach (2018, *JFQA* 53(1):269–298) [V] construct non-exotic cases where a bank's contribution to system risk rises while its *measured* contribution falls, and show a higher idiosyncratic risk can *lower* measured CoVaR once N > 3. **Directly analogous to MI-007's construction-implied-structure lesson**, and worth adding to the ledger's standing-lesson block as an external precedent. |
| **Whether crisis connectedness reflects bilateral links or a common factor** | Krampe & Margaritella (2024, arXiv:2402.02482, rev. 2025) [V]: using a factor model with sparse-VAR idiosyncratic components on daily volatilities of 90+ global banks (2003–2013, 2014–2023), system-wide connectedness "spikes during global crises, primarily driven by common component shocks and their short term effects", while in normal times it is "largely influenced by idiosyncratic shocks and medium-term dynamics." **This is the strongest published statement that crisis connectedness spikes are a common-factor phenomenon rather than a bilateral-network phenomenon.** It is not the same as the estimator-artifact critique (§4) but it is adjacent and must be cited. |
| **Whether apparent densification is real at all** | §4. |

### 3.3 What is *not* established and is often asserted

**[INF]** Three claims recur in the applied connectedness literature without support proportional to
their confidence:
- that a rolling connectedness index has *timing* content at daily or weekly resolution (§5 makes this
  mechanically impossible for W ≥ 100);
- that changes in the *ranking* of nodes (net transmitters/receivers) are stable enough to interpret —
  I found no paper reporting a sampling distribution for the net-directional ranking [U];
- that a densification episode is distinguishable from a variance-scaling episode.

---

## 4. THE CRUX — is crisis "densification" an artifact of estimator sensitivity?

The question, restated precisely so the answer can be graded:

> Every estimator producing "networks densify in crises" is threshold- or penalty-based: a
> Granger-causality test at α = 5%; a graphical-LASSO penalty λ; a correlation threshold; an MST
> edge-selection rule; an eigenvalue cut. In high-volatility periods the cross-sectional signal-to-noise
> ratio changes — common-factor variance rises relative to idiosyncratic variance, fat tails reduce the
> *effective* sample size, and the sampling distribution of every pairwise statistic shifts. **A constant
> true network can therefore appear to densify purely because the estimator crosses its threshold more
> often.** Does the published literature address this, and do the headline results survive?

### (a) Does the critique exist in print?

**No — not as a stated critique, not as a test, not as a caveat in any headline paper.** Its ingredients
exist separately, and nobody has assembled them. Ordered by how close each gets:

**1. The theory is proved, and never pointed at the empirical claim.**
Basu & Michailidis (2015, *Annals of Statistics* 43(4):1535–1567), "Regularized estimation in sparse
high-dimensional time series models" [V] establish, for a sparse VAR estimated by ℓ₁-penalised least
squares, that the **valid penalty scales linearly with the noise level**:

```
λ_n  ≳  c₀ · 2π · [ M(f_X,1) + M(f_ε) ] · √( log p / n )        (their Prop. 3.2 / 3.3)
```

where M(f_ε) = ess sup Λ_max(f_ε(θ)) is the spectral-density upper bound of the innovations, and the
VAR-specific deviation bound (their Prop. 4.3) carries
Q(β*, Σ_ε) = c₀[Λ_max(Σ_ε) + Λ_max(Σ_ε)/μ_min(A) + Λ_max(Σ_ε)μ_max(A)/μ_min(A)] — again linear in
Λ_max(Σ_ε). Their own gloss: the estimates have smaller error bounds "when the spectrum is less spiky."

**[INF] The corollary is immediate and, as far as I can establish, unwritten: hold λ fixed across rolling
windows while innovation volatility rises, and you are running a penalty *below* the level the theory
requires, in a regime where the deviation bound has grown. More coefficients survive. Density rises. The
true transition matrix never moved.** Basu & Michailidis never mention crisis densification. The same
logic runs through the graphical-model sample-complexity results (Ravikumar, Wainwright, Raskutti & Yu
2011, *EJS* 5:935–980; Meinshausen & Bühlmann 2006) [M], whose recovery guarantees are stated in terms of
the minimum edge signal *relative to noise*.

**2. The confession is in print, as a two-paragraph aside.**
Hautsch, Schaumburg & Schienle (2014, *International Journal of Forecasting* 30(3):781–794), "Forecasting
systemic impact in financial networks" [V], §4.2 — the single most on-point passage found in the entire
finance literature:

> "Note that the high variation of pointwise predicted systemic risk betas is **neither an artefact of the
> LASSO-procedure for network selection nor an indication of problems in selecting the penalization
> constant** in practice. Plots of estimated individual VaRs rather reveal a major part of the volatile
> behavior stemming from **the hard thresholding with which other companies' loss exceedances are measured
> and thus appear and disappear as potential candidates for network links over time.** We leave it for
> future work to determine appropriate smoothed versions of exceedances. In our study we remain
> conservative towards the type II error in detecting network links…"

Read carefully, this **denies** the penalty is the culprit and **concedes** the mechanically identical
phenomenon one layer upstream: a firm enters the regressor set only when it breaches a loss-exceedance
threshold, so when volatility rises more exceedances fire, more candidate links become available, and the
estimated network changes with no change in the underlying structure. They also state, §3, that "higher
significance levels generally result in larger systemic risk networks" — i.e. they know network size is a
tuning choice. **This is a known-defect note in a forecasting paper, not a study, and nobody appears to
have followed it up.**

**3. The confound result is published and strong, but is a different claim.**
Krampe & Margaritella (2024/2025, arXiv:2402.02482), "Decomposing global bank network connectedness: What
is common, idiosyncratic and when?" [V] estimate an approximate factor model with sparse-VAR idiosyncratic
components on Demirer et al.'s own 2003–2014 bank panel plus a fresh 2014–2023 panel (90+ banks, daily
volatilities), with bootstrap confidence bands. Finding: **"SWC spikes during global crises, primarily
driven by common component shocks and their short term effects. Conversely, in normal times, SWC is
largely influenced by idiosyncratic shocks and medium-term dynamics."** They name Billio et al. (2012) and
Demirer et al. (2018) explicitly as papers imposing "direct sparsity" on the VAR coefficient matrix, argue
that sparsity "is a non-testable assumption" and is only reasonable after controlling for common
variation, and add the signal-to-noise point directly: "controlling for common factors in a first step
tends to reduce collinearity among idiosyncratics, which is well known to **render LASSO variable
selection arbitrary**."
**This says the crisis edges are real but attributable to a common driver — a misattribution critique. The
crux question is whether the edges exist at all.** The antecedent is Barigozzi & Hallin (2017, *JRSS-C*
66(3):581–605) [V], who estimate the volatility network on the **idiosyncratic** component of a generalized
dynamic factor model on the S&P 100 precisely so that shared market factors do not manufacture edges.

**4. The multiplicity/size critique exists, but blames the wrong mechanism.**
Mazzarisi, Zaoli, Campajola & Lillo (2020, *Journal of Economic Dynamics and Control* 121:104022), "Tail
Granger causalities and where to find them: extreme risk spillovers vs spurious linkages" [V] show that the
standard tail-Granger test (Hong, Liu & Wang 2009, *J. Econometrics* 150(2):271–287) **over-rejects at the
5% level**, with the false-positive rate **increasing in the autocorrelation of the series**, and that
pairwise designs manufacture links via omitted third nodes. They name Billio et al. (2012) as an instance
that "will capture the network of causal relations, **but also spurious effects**", and — unlike Billio et
al. — they apply **Benjamini–Hochberg FDR** across all N(N−1) tests. **But the drivers they identify are
autocorrelation and omitted variables, not heteroskedasticity or volatility.** The modern fix in the same
direction is Uematsu & Yamagata (2025, *JASA*, DOI 10.1080/01621459.2025.2450836), FDR-controlled network
Granger causality via debiased LASSO and bootstrap [V].

**5. The bivariate ancestor — settled science, never lifted to graphs.**
Forbes & Rigobon (2002, *Journal of Finance* 57(5):2223–2261) and Boyer, Gibson & Loretan (1999, Fed IFDP
597) [M]. Diebold & Yılmaz (2009) cite Forbes & Rigobon as a debate they are explicitly **"sidestepping"**
[V]. **Nobody appears to have carried the heteroskedasticity-bias correction across to any network
estimator** [V — the D-Y-focused search returned nothing].

**6. The "is the change even significant?" question — asked once, recently, narrowly.**
Greenwood-Nimmo, M., Kočenda, E. & Nguyen, V.H. (2024), "Detecting statistically significant changes in
connectedness: A bootstrap-based technique", *Economic Modelling* 140:106843 [V — citation verified via
Crossref; **[U] on content**, the abstract is not exposed by Crossref or Semantic Scholar and the publisher
page 403s]. The reported premise is that D-Y spillover-index increases are routinely attributed to events
while "formal statistical evidence is limited". **This is the closest published thing to "is the increase
real?" and it must be read before Phase 11 claims novelty on inference-for-connectedness.** It tests
significance of *changes in the index*; it does not ask whether the estimator's threshold is
volatility-dependent.

**7. The right statistical machinery, absent from finance.**
Newman (2018, *Nature Physics* 14:542–545) and Peixoto (2018, *Physical Review X* 8:041011) [M] model edge
existence as uncertain and the measurement process explicitly; Squartini & Garlaschelli's maximum-entropy
network nulls [M] are the canonical null machinery. **[INF]** The finance-network and
network-inference-statistics literatures barely cite each other.

### (b) Who made it and what did they conclude?

| Who | What they concluded | Distance from the crux |
|---|---|---|
| Basu & Michailidis (2015) [V] | Valid LASSO penalty for a sparse VAR scales **linearly with innovation volatility**. | **The mechanism, proved.** Never applied to the empirical claim. |
| Hautsch, Schaumburg & Schienle (2014) [V] | Network-link turnover comes from **hard thresholding of loss exceedances**, not the penalty; smoothing left to future work. | **Closest explicit statement in finance.** An aside, not a study. |
| Krampe & Margaritella (2024/25) [V] | Crisis connectedness spikes are **common-component-driven**; direct VAR sparsity is misspecified under a factor structure. | Misattribution critique, not an artifact critique. Adjacent and essential to cite. |
| Barigozzi & Hallin (2017) [V] | Estimate the volatility network on the **idiosyncratic** component only. | A *design* that pre-empts one channel, without diagnosing it. |
| Mazzarisi, Zaoli, Campajola & Lillo (2020) [V] | Tail-Granger tests **over-reject**, worse with higher autocorrelation; pairwise designs create spurious links; FDR needed. | Right conclusion, wrong driver (autocorrelation, not volatility). |
| Greenwood-Nimmo, Kočenda & Nguyen (2024) [V cite / U content] | Bootstrap test for whether changes in connectedness are significant. | Nearest published attempt at inference for the index. **Read before claiming novelty.** |
| Forbes & Rigobon (2002); Boyer, Gibson & Loretan (1999) [M] | Volatility-conditioned correlation rises under a **constant** DGP; apparent contagion largely vanishes after correction. | Exactly the right logic, one dimension, 24 years ago. |
| Corsetti, Pericoli & Sbracia (2005) [M] | The Forbes–Rigobon correction is itself model-dependent; some contagion survives. | Cautionary precedent for §9. |
| Benoit, Colletaz, Hurlin & Pérignon [V]; Löffler & Raupach (2018) [V] | Systemic-risk measures are largely transformations of market risk and can move opposite to the truth. | Same *kind* of finding, different measure family. |
| Sheng & Montgomery (2024, *International Review of Financial Analysis*, "Does high volatility increase connectedness? A study of Asian equity markets") [V title/venue; **[U] findings**] | Asks the question in the title. | **Verify design and conclusion before citing either way.** |

### (c) What null models or simulation designs guard against it?

**One published design gets close, and it is the one that fails in an instructive way.**

**Billio et al.'s (2012) Monte Carlo — the design that cannot detect the thing it would need to rule out**
[V, from the NBER WP 16223 text, Appendix A.3 and §6.1]:
- They apply **no per-link multiplicity correction at all** — no Bonferroni, no Holm, no FDR. Every network
  diagram and every connection count is at raw, uncorrected 5%, with HAC-adjusted p-values and (per the
  appendix) a GARCH(1,1) pre-filter of returns.
- Instead they run a **single aggregate Monte Carlo on density**: simulate 100 series from
  y_i = α_i + β_i·S&P500 + σ_i ε_i with ε ~ IID N(0,1), 36 monthly observations, 500 replications, and
  record the fraction of the 9,900 possible directed links significant at 5%. The null density
  distribution is **"centered at 0.052"** with **"the area between 0.049 and 0.055 [capturing] 90% of the
  simulations"**, so "if we observe more than 5.5% of significant relationships in the real data, our
  results are unlikely to be the result of type I error."
- **The fatal design feature: the null is calibrated ONCE, on the full sample, with CONSTANT σ_i and IID
  normal innovations, and then compared against EVERY rolling window.** There are no volatility dynamics in
  the simulated series, no window-specific calibration, no re-simulation per window. **The experiment is
  structurally incapable of detecting whether the null density itself rises with market volatility.** They
  never raise the possibility.

Other nulls in circulation, and what each does not cover:
- **Marchenko–Pastur** (Laloux et al. 1999; Plerou et al. 2002) [M] — a real null for the eigenvalue
  spectrum, but homoskedastic and Gaussian; silent on whether an estimator invents edges under stress.
- **Bootstrap confidence bands** — Krampe & Margaritella [V] and Greenwood-Nimmo et al. (2024) [V cite] do
  this; most of the applied literature does not.
- **CV-selected penalty per window** — Demirer, Diebold, Liu & Yılmaz (2018, *JAE* 33(1):1–15) select the
  elastic-net λ by **10-fold cross-validation, re-run in every 150-day rolling window** [V]. **[INF] This is
  the strongest incidental defence against the artifact anywhere in the literature**, because a
  CV-selected λ partially self-normalises to the window's own noise level, unlike Billio's fixed α or a
  fixed threshold. It is nowhere presented as such — they present it as a fitting choice. **Any Phase-11
  work touching penalised estimators should adopt per-window penalty selection and say why.**
- **Maximum-entropy network nulls** and **Bayesian measurement-error models** [M] — the right tools, unused
  here.
- **The Forbes–Rigobon adjustment** — a correction, not a null, and defined only pairwise.

**What is missing is the obvious design:** simulate from a DGP with a **fixed** true dependency structure
and the **empirical, time-varying volatility path**, run the estimator, and report how much of the observed
crisis move the null reproduces. **[INF, stated as the central claim of this review: I found no published
instance of this design applied to any financial network estimator.]** The Phase-11 gate's registered H₀
(bootstrap from R_eq(ρ̄_t) scaled by the empirical volatility path) is *precisely this design*, restricted
to one statistic. That is the gate's real, if narrow, contribution — and it is worth generalising (§9).

### (d) Do the headline results survive?

**Not tested — and two of them look fragile on their own published numbers.**

**Billio et al. (2012).** Their Table 5 densities and link counts [V]:

| 36-month window | Density | Connections |
|---|---|---|
| Jan 1994 – Dec 1996 | 6% | 583 |
| Jan 1996 – Dec 1998 (LTCM) | 9% | 856 |
| Jan 1999 – Dec 2001 | **5%** | 520 |
| Jan 2002 – Dec 2004 | 6% | 611 |
| Jan 2006 – Dec 2008 (GFC) | **13%** | 1,244 |

Two arithmetic observations that follow from their **own** null calibration and that they do not draw
[computed by the reviewing agent from the paper's numbers, **[INF]** as to the interpretation]:
- **Three of the five windows sit at or below their own noise floor.** Their null mean density is 0.052 and
  the 95th percentile is 0.055. Observed: 6%, 9%, **5% (below the null mean)**, 6%, 13%. **The entire "rise
  in connectedness" narrative rests on two crisis windows.**
- **Expected false links under their own null: 9,900 × 0.052 ≈ 515.** So ~88% of the 583 links in
  1994–96 and ~41% of the 1,244 links in 2006–08 are expected type-I errors. Every published network
  *diagram* in the paper is majority-noise by their own calibration, yet individual edges (the
  Banks→Hedge Funds hub, named institutions) are interpreted as if individually validated. **They control
  the aggregate and interpret the edges.**

**Verdict on Billio et al.: the aggregate density result clears their null in two crisis windows, and the
question of whether the null floor itself moves in those windows has never been asked.** That is the
single cheapest high-value experiment in this whole area (§9).

**Diebold & Yılmaz (2014).** The TCI is a ratio of off-diagonal to total forecast-error variance, so it is
**exactly scale-invariant in the volatility level** — a genuine defence against the crudest artifact.
Two things are not defended:
- **[SIM]** Holding the VAR coefficient matrix Φ *exactly fixed* and varying only the equicorrelation ρ of
  the innovation covariance (N=6, H=12) moved the TCI 28.8% → 39.6% → 57.6% → 70.7% → 78.6% → 81.3% for
  ρ = 0, 0.2, 0.4, 0.6, 0.8, 0.9; scaling the *volatility level* ×1 to ×50 at fixed correlation left the
  TCI at 48.88% to machine precision. **The TCI is a contemporaneous-correlation measure far more than a
  lag-structure measure.** A crisis TCI spike is therefore substantially a restatement of rising average
  correlation, not evidence of a changed directed network. *(Unpublished simulation run during this
  review — replicate before relying on it.)*
- **[SIM]** Small-sample bias. With a known DGP matched to D&Y (2014)'s own setup (N=13, VAR(3), H=12,
  ρ=0.3, OLS), the estimated TCI was **67.4% at W=100** against a true population TCI of **56.9%**,
  decaying monotonically: 64.1% (150), 61.9% (200), 59.9% (300), 58.5% (500), 57.8% (1000), 57.3% (3000).
  **At D&Y's own window the TCI carries roughly a +10 percentage-point upward bias**, because 13 equations
  × 40 parameters are fitted on 100 observations. **[INF] Since fat tails reduce the effective sample size
  in stress, this bias is itself state-dependent — a direct volatility→densification channel for the D-Y
  index.** *(Unpublished simulation — replicate before relying on it.)*
- The authors themselves knew something was here: D&Y (2014) footnote 10 raises Bayesian estimation to
  "reduce the probability of **spuriously-inflated connectedness measurements for large N**" [V], and §5.2
  attributes their high 78.3% partly to the fact that "both industry-wide and macroeconomic shocks affect
  each one of these stocks" — a common-factor reading of their own headline number, offered without
  adjustment [V].

**Aït-Sahalia, Cacho-Díaz & Laeven (2015)** [V] is a third instructive case. Their estimated model has
**constant σ** (they state the stochastic-volatility extension is "theoretically identified" but that "this
identification can be tenuous in practice"), and they concede outright: "**the jump part of our model
partially captures what was traditionally (with continuous return dynamics) modeled as (instantaneous)
volatility**." So volatility clustering has nowhere to go except into the self-excitation parameter β_ii.
Their estimates imply λ_∞/λ₁ = 0.40/4.63 ≈ **8.6% exogenous**, i.e. ~91% of US jumps endogenously
triggered, with a branching-ratio spectral radius ≈ 0.91 [computed by the reviewing agent from their Table
5, [INF]]. **[INF] That is squarely in the contested near-critical "reflexivity" range that the
Hardiman–Bouchaud critique of Filimonov–Sornette attributes to non-stationary baseline intensity being
absorbed into the excitation kernel** — the same failure mode, in a different estimator family. Their
cross-excitation result is also strictly asymmetric and pairwise: β₂₁ (US→foreign) is significant for UK
(13.1), EU (8.2) and Emerging Asia (8.6), while β₁₂ (foreign→US) is **never significantly different from
zero** at daily frequency.

**MST tree-length shrinkage (Onnela et al. 2003)** [M]: **[INF]** does not survive as a *topology* claim
without a ρ̄ control, because tree length is a deterministic decreasing function of the correlations
entering it. It survives fine as a *correlation-level* claim, which is not what it is usually cited for.

**Bottom line for the caller's question.** The critique is real; its bivariate ancestor was settled in
2002; the theory that makes it inevitable was proved in 2015 in a different literature; one paper confesses
the mechanism in an aside; one paper shows the crisis signal is a common factor rather than a network; and
**nobody has run the experiment.** The headline "networks densify in crises" results have **not** been
tested against a constant-network, volatility-matched null. **Phase 11 should say exactly that — and should
not claim to have discovered the critique, because the pieces are all in print.**

---

## 5. Temporal resolution of rolling-window network estimators

### 5.1 The mechanics, which are not in dispute

For a flat (rectangular) rolling window of length W applied to a quantity that undergoes a step change at
time τ:
- the estimate is a **linear ramp** from the old level to the new one, reaching 50% at τ + W/2 and 100%
  at τ + W;
- the effective **centre of mass** of the estimate stamped at t is t − (W−1)/2, i.e. the plotted series
  is **delayed by roughly W/2**;
- consecutive estimates share (W−1)/W of their data, so the induced autocorrelation at lag k is
  approximately 1 − k/W **by construction**, independent of anything in the data;
- nesting a volatility window W_σ inside a correlation window W_A gives total memory W_A + W_σ − 1 and
  half-response ≈ (W_A + W_σ − 1)/2.

All of this is elementary [INF, but standard]. Phase 11 derives it correctly: W_A = 125, W_σ = 21 ⇒ memory
145 days, half-response ≈ 73 days, and the gate registers that structure resolving in under ~6 weeks is
**not observable**.

### 5.2 The actual window/lag/horizon choices in the canonical papers [V]

Verified against the source texts (D&Y 2009 and 2012 read in working-paper form — NBER WP 13811 and Koç
ERF WP 1001; D&Y 2014 read in the published *J. Econometrics* PDF):

| | **D&Y 2009** *EJ* 119(534):158–171 | **D&Y 2012** *IJF* 28(1):57–66 | **D&Y 2014** *J.Econometrics* 182(1):119–134 |
|---|---|---|---|
| Identification | **Cholesky** | Generalized (KPPS) | Generalized, Cholesky as robustness |
| VAR lag | 2 (SIC) | 4 | 3 |
| Horizon H | **10 weeks** | 10 days | 12 days |
| Rolling window | **200 weeks** | 200 days | **100 days** |
| N | 19 equity markets | 4 asset classes | 13 US financial firms |
| Frequency | **weekly** | daily | daily |
| Volatility measure | Garman–Klass weekly range | Parkinson daily range | 5-min **realized** vol, in logs |
| Full-sample index | 36% (returns) / 40% (vol) | **12.6%** | **78.3%** |

**Three corrections to widely repeated claims** [V]:
1. **D&Y (2009) is weekly, with a 200-*week* window** — the "200-day window" often attributed to it is
   wrong.
2. **D&Y (2014) contains no LASSO.** The LASSO/elastic-net VAR for large N is **Demirer, Diebold, Liu &
   Yılmaz (2018, *JAE* 33(1):1–15)** — 150 global banks, 2003–2014, 150-day rolling window, H = 10, penalty
   by 10-fold CV per equation per window.
3. **D&Y (2014) did not abandon Cholesky**: "Our own preferences run toward Cholesky and related
   identifications."

**What sensitivity analysis actually exists** [V]:
- **Identification** is the best-covered dimension. D&Y (2009) §6 Fig. 4 tries 18 rotated plus 50 random
  orderings ("Throughout, the spillover range is small"). D&Y (2014) §5.3.4 Fig. 5 runs a fully crossed
  design — W ∈ {75, 100, 125} × H ∈ {6, 12, 18} × 100 random Cholesky orderings with a [10%, 90%] band —
  and reports three findings: the generalized TCI is always **above** the Cholesky band (Cholesky is a
  lower bound); the ordering band is "quite narrow"; and **the generalized–Cholesky gap widens as W
  increases and narrows as H shortens.** Klößner & Wagner (2014, *JAE* 29(1):172–179) [V, abstract level]
  give an algorithm for the **exact** min and max over all N! orderings rather than sampling.
- **Lag and horizon:** D&Y (2012) fn. 6 + Appendix Figs A1/A2 vary VAR order 2–6 and H 4–10 days and
  conclude the index is "not sensitive". D&Y (2014) §3.2 goes further and denies H-robustness is even
  desirable: "there is no reason why connectedness should be 'robust' to H", since H → ∞ approaches the
  unconditional decomposition. Varying H is phenomenology, not a robustness check.
- **Window length:** D&Y (2009) contrast 75 vs 200 weeks; D&Y (2014) 75/100/125 days. Both report only
  qualitative verdicts — shorter is "more wiggly", longer is "smoother". **No paper found publishes a table
  of TCI level against window length** [V, negative result]. Given the [SIM] small-sample bias in §4(d)
  (+10.5pp at W=100 falling to +0.4pp at W=3000), **comparisons across window lengths are comparisons of
  different biases**, and the D&Y (2014) observation that W=75 and W=125 "move in accordance" is a
  statement about *shape*, entirely consistent with systematically different *levels*.
- **Normalisation:** Caloia, Cipollini & Muzzioli (2019, *Energy Economics*, DOI 10.1016/j.eneco.2019.104536)
  [V] run the one serious Monte Carlo in this family — 5 variables, T=500, 1000 replications, VAR(2) and
  restricted VAR(22), crossed with low/high comovement, H ∈ {2, 10}. Row normalisation (i.e. D&Y) produced
  **354 net-spillover sign errors out of 5,000 at H=2** (column normalisation: 2,525), and **corrupted the
  net-spillover ranking in >850/1000 replications at H=2 and >950/1000 at H=10**. Scalar normalisations
  (spectral radius, max row sum) preserve sign and ranking exactly. Crucially: **"In both normalization
  schemes, the number of errors increases with the degree of comovement."** Replicating D&Y (2012)'s own
  application, they find no sign errors but a genuine **ranking reversal** between row and max-row-sum
  normalisation.
- **Lanne & Nyberg (2016, *OBES* 78(4):595–603)** [V] is frequently cited as a correction to D&Y. It is
  not. They never cite D&Y, and **for a linear VAR their redefined GFEVD is algebraically identical to the
  D&Y row-normalised KPPS GFEVD** (verified numerically by the reviewing agent on a random 4-variable VAR:
  max |DY − LN| = 1.1e-16). Their genuine contribution is the extension to **nonlinear** models. Switching
  to Lanne–Nyberg changes nothing for a linear-VAR TCI; **the live alternative is Caloia et al.'s scalar
  normalisation.**

### 5.3 Is temporal resolution discussed honestly?

**Largely, no.** [INF, from reading practice across the field, with two verified exceptions]

- The dominant presentation is a **daily-frequency plot of a 100–250-day rolling-window statistic**,
  narrated as if turning points were dated events. **D&Y (2014) themselves do this** [V]: "on the last day
  of February 2007, the total connectedness measure jumped by more than 17 points, the biggest increase on
  a single day" — a 100-day trailing window read as a daily quantity. The ramp is never flagged.
- The autocorrelation induced by overlap is essentially **never reported**, and inference is routinely
  performed pointwise across overlapping dates, which is invalid. The Phase-11 gate's E1 bar explicitly
  forbids this ("assessed as a whole-sample summary under block bootstrap — never pointwise across
  autocorrelated dates") — **more careful than the literature it draws on.**
- **TVP-VAR connectedness** (Antonakakis, Chatziantoniou & Gabauer 2020, *JRFM* 13(4):84) [V] is the one
  paper that addresses detection lag directly, and it is worth quoting: "**TVP-VAR values immediately
  adjust to underlying events, while rolling-window-based estimates either overreact (given an inadequate
  window size) or smooth out the effect (given a large window size)**"; and "despite how the 100-month
  rolling-windows VAR is as persistent as its TVP counterpart, **it does not appear to adjust to changes as
  quickly as the TVP-VAR model**." They back this with a **Monte Carlo under a known DGP with a deliberate
  structural break** — VAR(1), 10,000 replications, T=400, window sizes 50–300, coefficient matrix
  switching from [[.6,.3],[.3,.6]] to [[.9,0],[0,.9]] — and report mean-absolute-deviation differences
  (rolling minus TVP) of 0.033/0.040/0.032/0.028 under the break and 0.025/0.016/0.012/0.027 under a single
  outlier, all p < 0.01. **[INF]** But the metric is *parameter* deviation, not **days-to-detection of the
  TCI**; and the TVP-VAR's forgetting factors κ₁, κ₂ are the window knob renamed, with the implied
  half-life rarely reported. **No paper found publishes a detection-lag figure in days for any connectedness
  index** [V, negative result].
- **Frequency-domain connectedness** (Baruník & Křehlík 2018, *Journal of Financial Econometrics*
  16(2):271–296) [M/V] is the most honest treatment of timescale in this family, and their argument against
  using H as a timescale knob is a clean counterexample [V]: two bivariate AR systems with coefficients of
  **opposite sign but equal magnitude** — the positive one generates low-frequency connectedness rising in
  H; the anti-persistent one generates **identical connectedness at every H**, sourced entirely from high
  frequencies. "Hence, simply assessing connectedness at different horizons… is not sufficient." Their fix
  is a spectral decomposition of the GFEVD onto frequency bands (they use a 300-day moving window; R package
  `frequencyConnectedness`). **But this decomposes the dynamics of the modelled process, not the resolution
  of the estimator** — different things, and sometimes conflated.

### 5.3 What is properly known — the change-point literature

Detection lag is a solved *statistical* problem in an adjacent field that the finance-network literature
under-cites:

- Aue, Hörmann, Horváth & Reimherr (2009, *Annals of Statistics* 37(6B):4046–4087), "Break detection in the
  covariance structure of multivariate time series models" [M] — CUSUM-type detection on the vectorised
  outer products, with asymptotics for detection.
- Wied, Krämer & Dehling (2012, *Econometric Theory* 28(3):570–589) [M] — testing for a change in
  correlation at an unknown point via an extended functional delta method. Galeano & Wied (2014,
  *Computational Statistics & Data Analysis*) [M] extend to multiple change points.
- Barigozzi, Cho & Fryzlewicz (2018, *Journal of Econometrics* 206(1):187–225), "Simultaneous multiple
  change-point and factor analysis for high-dimensional time series" [M]; Cho & Fryzlewicz (2015, *JRSS-B*
  77(2):475–507) sparsified binary segmentation [M].

**[INF] The relevant lesson:** these methods achieve far better temporal resolution than a rolling window
because they use *all* the data on both sides of a candidate break rather than a fixed lookback. A rolling
window is the *worst* estimator for detecting a change point and the *most common* one in this literature.
If Phase 11 ever wants genuine timing content — which G3′ says it cannot have anyway, given the 74-day
publication lag — the change-point family is the right tool, not a shorter window.

**[INF] An honest scope statement, which Phase 11 already has and the literature mostly lacks:** a
rolling-window dependency estimator is a *quarterly-resolution instrument plotted daily*. It cannot date
an event, and the apparent smoothness of its path is an artifact of overlap, not evidence of a smoothly
evolving market.

---

## 6. Which parts of the Phase-11 approach are actually new?

Graded harshly. "New" means: I could not find it in print, and it is not a trivial restatement.

### 6.1 Genuinely new, narrow

1. **Ψ as the registered statistic — a knob-free, normalised distance from the equicorrelation family,
   applied to a rolling correlation matrix and calibrated against a bootstrap null that uses the
   *empirical volatility path*.** [INF] The *components* all exist (the equicorrelation family: Engle &
   Kelly 2012 [V]; Frobenius distance to a structured target: the shrinkage-target literature, Ledoit &
   Wolf 2003/2004 [M], where the equicorrelation matrix is a *standard shrinkage target*); the
   *combination as a pre-registered redundancy test with a volatility-path-matched null* is, as far as I
   can establish, not published. **This is a small, real, methodological novelty and should be described
   at exactly that size.**

   Note the direct precedent that must be cited: **the equicorrelation matrix is one of the canonical
   shrinkage targets in Ledoit & Wolf's constant-correlation estimator** [M]. Ψ is, up to normalisation,
   the *shrinkage residual* against that target. Anyone who has implemented constant-correlation shrinkage
   has computed the numerator of Ψ. Phase 11's contribution is turning it into a *test*, not inventing it.

2. **E4 — pattern persistence at non-overlapping horizon h = W_A.** [INF] This is the right test and I did
   not find it in the network literature, which typically reports "edge survival ratios" (Onnela et al.)
   [M] on *overlapping* windows, where persistence is guaranteed by data overlap. Requiring
   non-overlapping windows is a genuine tightening. **This is the strongest single design element in the
   gate.**

3. **The volatility-dependency object R^v built on Δ log σ with c_t removed, tested for redundancy against
   ρ̄ and c_t before anything is built on it.** Whether this is new depends entirely on the Barigozzi &
   Brownlees (2019) check flagged in §2(b). **[U] until verified.**

### 6.2 New only relative to this repo, not to the field

- The claim that the cross-section carries "relational" information a component-level observatory cannot
  see (G1/G2). This is the founding premise of the entire systemic-risk-network literature since 2010.
  It is well-argued in the gate but it is not new and should not be presented as motivation-by-novelty.

### 6.3 Not new, and the gate already says so

The gate's own "Replication before research" table is accurate and honest: CLMX decomposition and ρ̄
crisis spikes are replication; the H₀ sampling distribution, resolution measurement, MP bulk edge, the
MA(W_σ−1) overlap structure and the rank deficiency of Cov(D) are methodological validation with no market
claim. **No changes recommended to that table** other than adding the NETS check and the Ledoit–Wolf
shrinkage-target precedent.

### 6.4 A technical problem with the registered E2 bar — [INF], recommend fixing before signature

From `scripts/cross_section.py` the identity Ψ² = 1 − N(N−1)ρ̄²/‖R−I‖²_F is asserted. Writing
m = N(N−1), S² = (1/m)Σ_{i≠j}(ρ_ij − ρ̄)² (the off-diagonal variance) and noting
‖R−I‖²_F = m(S² + ρ̄²), this reduces exactly to

```
Ψ² = S² / (S² + ρ̄²)        ⇔        Ψ = CV / √(1 + CV²),      CV = S / |ρ̄|
```

**Ψ is a monotone transform of the coefficient of variation of the off-diagonal correlations.** Three
consequences:

1. **Ψ is not scale-free in ρ̄ — it is inversely related to it.** If the dispersion of pairwise
   correlations stays constant while ρ̄ rises (the classic crisis pattern), **Ψ falls mechanically.**
2. **Under the gate's own H₀** (true equicorrelation ρ, window T), sampling gives S ≈ (1 − ρ²)/√T and
   ρ̄̂ ≈ ρ, so CV ≈ (1 − ρ²)/(ρ√T). At W_A = 125: ρ = 0.3 ⇒ CV ≈ 0.27 ⇒ Ψ ≈ 0.26; ρ = 0.6 ⇒ CV ≈ 0.095
   ⇒ Ψ ≈ 0.095. **The null band for Ψ moves by a factor of ~2.7 across a plausible range of ρ̄.** The
   gate is right that the bootstrap must use the empirical ρ̄_t path — this quantifies *how right*.
3. **Therefore E2 is mis-specified as written.** E2 requires |Spearman(Ψ_t, ρ̄_t)| < 0.90 or the class is
   DROPPED under F2 ("the absorption ratio in a fourth costume"). But a strong *negative* Spearman between
   Ψ and ρ̄ is what H₀ predicts — it is the algebra of the normalisation, not evidence that Ψ is a restatement
   of ρ̄. **Recommended amendment: run E2 on the H₀-standardised statistic** (Ψ_t's empirical p-value or
   z-score against its bootstrap distribution *at the same ρ̄_t and T*), not on raw Ψ_t. Otherwise F2 can
   fire on a mathematical identity and the class is dropped for the wrong reason.

**[INF] Also worth reconsidering: the gate's pre-call that E4 is the most likely failure.** For the
*return* correlation matrix R^r that pre-call is probably wrong. Industry correlations have obvious,
economically persistent heterogeneity (utilities and telecoms cluster; energy does not), so E4 on R^r
should pass easily. Rough power calculation: with N = 10 there are 45 unique pairs; under H₀ the
cross-window correlation of two 45-vectors of noise has sd ≈ 1/√45 ≈ 0.15, and the expected cross-window
correlation is Var(Δ)/(Var(Δ) + s_e²) where s_e ≈ (1−ρ²)/√W_A ≈ 0.08. A true pairwise-correlation
dispersion of only 0.08 already delivers an expected E4 statistic of ~0.5. **The binding bar is E2, not
E4**, and E2 is the one that is mis-specified. For R^v the pre-call may well be right.

---

## 7. Which parts are just different implementations of existing ideas?

Stated bluntly, because this is the most useful thing this review can say.

| Phase-11 element | Existing idea it re-implements | Citation |
|---|---|---|
| "Dependency structure is more than one scalar" | The entire absorption-ratio / RMT / factor-count programme | Kritzman et al. (2011) [V]; Laloux et al. (1999); Plerou et al. (2002); Bai & Ng (2002) [M] |
| ‖R − R_eq(ρ̄)‖_F, the numerator of Ψ | The residual against the **constant-correlation shrinkage target** | Ledoit & Wolf (2003, *Journal of Empirical Finance*; 2004, *JMVA*) [M] |
| R_eq as the null family | DECO / Block-DECO — the same restriction, imposed rather than tested | Engle & Kelly (2012) [V] |
| ρ̄_t as the least-squares projection onto the equicorrelation family | Standard; the off-diagonal mean is the constant-correlation estimator | Elton & Gruber (1973) [M]; Ledoit & Wolf [M] |
| Correlating **volatility innovations** across the cross-section | NETS' contemporaneous network on realized volatilities | Barigozzi & Brownlees (2019) [M] |
| Removing a cross-sectional common volatility factor c_t before looking at residual structure | CIV / common-factor-in-idiosyncratic-volatility; systematic-vs-idiosyncratic panel decomposition | Herskovic et al. (2016); Barigozzi, Brownlees, Gallo & Veredas (2014) [M] |
| A market/industry variance decomposition as the pipeline check | CLMX exactly | Campbell, Lettau, Malkiel & Xu (2001) [M] |
| A rolling-window structural statistic plotted through time with crisis annotations | The universal template of this literature | everyone |
| The registered scope limit "quarterly resolution, not daily" | The mechanics are standard; the *honesty* is not | §5 |

**The uncomfortable summary:** Phase 11 is a *well-disciplined re-implementation* of a well-populated
research area, with two small genuine additions (the null-calibrated Ψ, and E4 at non-overlapping
horizons) and one large procedural addition (pre-registration of the reject conditions, which the source
literature essentially never does). **The gate's own write-up already says the new part is "narrow and
largely methodological". That assessment is correct and should not be softened.**

---

## 8. What genuine research gap remains?

Ranked by how defensible each is under a hostile referee.

### Gap 1 (strongest, and the one the caller identified) — *how much apparent structural change is free?*

**No published work holds a true dependency structure fixed, drives it with the empirical volatility path,
and reports how much "densification" each standard estimator invents.** [INF; §4(c)]. The bivariate version
of the question was settled in 2002 (Forbes & Rigobon) and never lifted to graphs. The nearest published
neighbours are:
- Krampe & Margaritella (2024/25) [V] — decomposes crisis connectedness into common vs idiosyncratic, but
  does not ask whether the edges are estimation noise;
- Benoit et al. [V] and Löffler & Raupach (2018) [V] — show measure-vs-thing failures for a different
  measure family;
- Ravikumar et al. (2011) [M] — supplies the theory implying the effect must exist, without ever pointing
  it at the empirical claim.

**Why this is a real gap and not a manufactured one:** it is a *measurement-validity* question about the
most-cited empirical claim in the field, it is answerable with data already on disk, and a negative answer
("most of the observed densification is free") would be a genuinely uncomfortable result for a large
literature. It also sits exactly inside this repo's mandate: it is a statement about what a measurement
can and cannot support, and it contains no market claim at all.

### Gap 2 (narrower, and the one Phase 11 actually registered) — *is there persistent, non-redundant structure in industry volatility dependency after removing the common volatility factor?*

Legitimate but small, and **conditional on the Barigozzi & Brownlees (2019) check** (§2b). If NETS already
estimates a contemporaneous network on differenced log realized volatility, Gap 2 shrinks to "the same
question on industries rather than stocks, with a cleaner null" — worth an afternoon, not a programme.

### Gap 3 (open, low priority here) — *the sampling distribution of network-topology summaries.*

No paper found reporting a sampling distribution for net-directional-connectedness rankings, MST tree
length, or graph density under a stated null [U]. This is a general methodological gap, but it is a
statistics paper, not a market-measurement result, and it is outside what this repo exists to do.

### What is NOT a gap, and should not be claimed as one

- "Nobody has measured cross-sectional dependency in industries." False — heavily measured.
- "Nobody knows dependency rises in crises." False — §1.1.
- "The absorption ratio is redundant with ρ̄." Not a gap; it is elementary algebra already recorded in
  this repo (MI-007) and implicit in the equicorrelation literature.
- "Rolling windows are slow." Not a gap; it is arithmetic. The gap is that people *plot as if it were not
  true*, which is a practice criticism, not a research question.

---

## 9. The smallest experiment that could test the gap

Designed against **Gap 1**, because it is the one with real upside, it needs no new data, and it produces
a result that is useful whether it comes out positive or negative.

### 9.1 The experiment in one sentence

Simulate a market whose **true dependency structure never changes** but whose **volatility path is the
one that actually happened**, run the standard "networks densify in crises" estimators on it, and report
how much of the historically observed crisis move each estimator reproduces **under a structure that by
construction did not move**.

### 9.2 Construction

**Data:** `data/processed/industry10_daily.csv` only (N = 10, complete 1926-07-01..2026-05-29). No new
data. A robustness pass on `industry48_daily.csv` complete cases (1969-07-01 onward) if the first pass is
informative.

**DGP (the null world):**
1. Standardise each industry return series by its own trailing volatility ⇒ z_{i,t}.
2. Estimate **one** full-sample correlation matrix R\* from z. This is the *fixed true network* — it never
   changes for the rest of the experiment.
3. Draw ε_t ~ t_ν with ν matched to the empirical tail index, correlated by R\* (Cholesky of R\*).
4. Rescale: r̃_{i,t} = σ̂_{i,t} · ε_{i,t}, where σ̂_{i,t} is **each industry's actual estimated trailing
   volatility path from the real data**. So the simulated market has the real 1929, 1987, 2008 and 2020
   volatility, real fat tails, real cross-sectional volatility heterogeneity — and a constant correlation
   matrix.
5. Repeat B times (B = 200–500 is ample).

**The estimator panel** — the point is breadth across *knob types*, not depth:

| Estimator | Knob under test |
|---|---|
| ρ̄_t, rolling W = 125 | none (the baseline; should be flat by construction — a correctness check on the DGP) |
| Ψ_t (`cross_section.structural_residual_share`) | none |
| Absorption ratio, n = N/5, W = 500 | eigenvalue cut |
| Correlation-threshold graph density at fixed τ | threshold |
| Graphical-LASSO edge count at **fixed λ**, and at **λ chosen by EBIC each window** | penalty, and penalty-selection rule |
| MST normalised tree length | edge-selection rule |
| Pairwise Granger edge count at α = 5%, W = 36 months | test size |
| (optional, expensive) D-Y total connectedness, W = 125, VAR(2), H = 12 | window/lag/horizon/identification |

**The readout, per estimator:**
- `crisis_move_null` = mean (crisis-window value − calm-window value) across the B null simulations;
- `crisis_move_real` = the same contrast computed on the actual data;
- **artifact share** = `crisis_move_null / crisis_move_real`.

Crisis and calm windows are **fixed in advance** by date (1929-10, 1987-10, 2008-09/10, 2020-03 vs a
registered set of calm periods) so there is no selection on the answer.

### 9.3 Pre-registered interpretation

| Outcome | Reading |
|---|---|
| Artifact share ≈ 0 for all estimators | The critique is wrong. Crisis densification is real. Publishable as a *negative* result and it strengthens the whole literature. |
| Artifact share small for ρ̄ and Ψ, large for the threshold/penalty estimators | The critique is right and **specifically about threshold crossing**. Directly vindicates Phase 11's knob-free design choice. |
| Artifact share ≈ 1 for most estimators | The headline literature result is largely an estimator artifact. Large finding; would require unusually careful confirmation before being asserted. |
| ρ̄ moves in the null | **Bug.** The DGP has a constant correlation matrix; if ρ̄ moves, the standardisation or the volatility path is leaking. Stop and fix. |

### 9.4 Why this is the *smallest* such experiment

- Zero new data; one panel already on disk with a recorded sha256 in `MANIFEST.csv`.
- No look is spent: this is a **methodological validation with no market claim**, in exactly the category
  the gate's own separation-of-claims table defines. It produces no reading, no status, no maturity tag,
  and nothing that could be presented as a live signal.
- It uses machinery that already exists (`causal.realized_vol`, `cross_section.py`) plus a Cholesky draw.
- It answers a question that is *upstream* of the Phase-11 gate: if the artifact share for Ψ is large, the
  gate's E1 bar needs the volatility-path bootstrap it already registered; if it is small, the gate's null
  can be simplified.
- Its result is informative regardless of sign, which is the property the repo's charter discipline asks
  for.

### 9.5 Registered scope limits (write these into any charter that adopts it)

- **This is not a market claim.** It measures estimators, not markets.
- **A constant-R\* null is a null, not a model of the world.** Failing to reject it does not mean the true
  network is constant; it means the data cannot distinguish. Corsetti, Pericoli & Sbracia (2005) [M] is the
  cautionary precedent — the Forbes–Rigobon correction was itself model-dependent.
- **Do not extend the estimator panel after seeing results.** The eight estimators above are the panel.
- **The crisis/calm window dates are registered before the run** and are not revisable.

---

## 10. What is replicable with the data on disk

**Data available:** `data/processed/industry10_daily.csv` (10 columns, complete, 26,253 rows,
1926-07-01..2026-05-29, sha256 in `MANIFEST.csv`) and `industry48_daily.csv` (48 columns, same rows, but
ragged: Soda/FabPr/Guns/Gold from 1963-07-01, Rubbr 1930-07, Paper 1929-07, PerSv 1927-07, **Hlth
1969-07-01**; the repo's own absorption memo records **complete cases only from 1969-07-01, 14,350 rows**).
Values are decimal simple returns.

**Three provenance caveats that bear on every row below.**
1. **No live builder exists in-repo for either industry panel.** `scripts/build_assets.py` builds a
   *different* file and, for its own Ken French daily tables, keeps the **first block** of the daily file
   (the value-weighted block) and divides by 100. **[INF]** The industry panels were almost certainly built
   the same way, but this is **unverified** — gate open item #4 (value- vs equal-weighted, percent vs
   decimal, total vs excess) is still genuinely open, and the check is a five-minute rebuild.
2. **Ken French publishes no international industry sorts.** **[V — verified today directly against the
   data library page]**: the industry portfolio datasets (5/10/12/17/30/38/48/49) are US-only; the
   international sections (Developed, Developed ex US, Europe, Japan, Asia Pacific ex Japan, North America,
   Emerging) contain factor and size/value sorts, **no industry sort**. This confirms the gate's registered
   maturity ceiling of `research` — `run_oos.py` cannot serve this class. **Gate open item #3 is now
   closed in favour of the gate's assumption.**
3. **Returns only.** No prices, no high/low ranges, no market values, no firm counts, no volumes, no
   options. This eliminates several otherwise-obvious replications.

### Ranked: cheapest and most diagnostic first

**DO NOT RUN ANY OF THESE. This is a ranking, not an instruction.**

---

**#1 — ρ̄_t rolling mean off-diagonal correlation, with crisis annotation.**
- *Establishes:* the pipeline computes correlations correctly and reproduces the universal stylised fact.
- *Data:* industry10 alone. *Effort:* ~1 hour.
- *Published answer precise enough to check?* **No — qualitative only.** Every paper uses a different
  universe, so there is no number to match. Its value is as a **construction gate**, on the footing of
  `results/concentration_gate.csv`, not as a finding.
- *Diagnostic value:* **Highest per unit effort.** If this does not spike in 1987-10, 2008-09/10 and
  2020-03, everything downstream is wrong.

---

**#2 — Absorption ratio and its empirical relationship to ρ̄_t.**
- *Establishes:* whether MI-007's algebraic drop rationale (AR₁ affine in ρ̄ under equicorrelation)
  survives contact with real, non-equicorrelated data — i.e. what the actual R² of AR on ρ̄ is.
- *Data:* industry10 (n = N/5 = 2) and industry48 complete cases from 1969 (n ≈ 10, closest to Kritzman
  et al.'s 51-series universe). W = 500 days per the source. *Effort:* ~2 hours.
- *Published answer precise enough to check?* **Partially.** Kritzman, Li, Page & Rigobon (2011, *JPM*
  37(4):112–126, DOI 10.3905/jpm.2011.37.4.112) [V] is a real, citable, precisely-specified construction
  (fraction of total variance in the top n eigenvectors) — but their empirical claims are on a different
  universe and a much shorter span, so **their headline numbers are not matchable**; the construction is.
- *Diagnostic value:* **Very high for this repo specifically**, because it converts MI-007's algebra into
  evidence and produces a number (AR-vs-ρ̄ R²) the ledger currently asserts rather than measures.
- *Boundary note:* report the AR series and its relation to ρ̄. Do not reproduce the source paper's
  conditional-outcome tables — those are decision content and are out of this repo's scope.

---

**#3 — Marchenko–Pastur bulk-edge diagnostic through time.**
- *Establishes:* how much apparent eigenstructure is free at this N and T, and whether the count of
  deviating eigenvalues is stable. Feeds directly into §9.
- *Data:* industry48 complete cases (q = 48/500 ≈ 0.096, bulk edge (1+√q)² ≈ 1.71) and industry10
  (q = 10/125 = 0.08, edge ≈ 1.60). *Effort:* ~1 hour.
- *Published answer precise enough to check?* **No.** Laloux et al. (1999) and Plerou et al. (2002) used
  ~400–1000 individual stocks at q ≈ 0.4–1.0. Their bulk edge is completely different, so the *numbers*
  are not comparable; only the *qualitative* pattern (one dominant mode, most of the spectrum inside the
  bulk) transfers. **[INF]** With N = 10 the MP asymptotics are marginal at best and should be treated as
  a heuristic, not a null.
- *Diagnostic value:* **High**, low effort, and it is a required input to any honest statement about how
  much structure is real.

---

**#4 — MST normalised tree length, with an explicit ρ̄ control.**
- *Establishes:* the Onnela et al. (2003) crash-shrinkage stylised fact **and**, more usefully, a direct
  demonstration that tree length is a monotone decreasing function of ρ̄ — i.e. that the canonical
  "topology changes in crises" result is largely a restatement of "correlations rise".
- *Data:* industry48 complete cases (47 MST edges; N = 10 gives only 9 edges and is too small for a
  meaningful tree). *Effort:* ~3 hours.
- *Published answer precise enough to check?* **No.** Onnela et al. used 116/477 NYSE stocks, 1980–1999,
  with a 1000-day window; the numbers do not transfer. The claim being checked is qualitative.
- *Diagnostic value:* **Moderate as replication, high as an artifact demonstration.** This is the cheapest
  concrete illustration of the §4 crux, and it can be reported as a purely methodological result with no
  market claim.

---

**#5 — CLMX-style market/industry variance decomposition (restricted).**
- *Establishes:* that the pipeline reproduces a published, precisely-numbered decomposition — the gate's
  own "Replication before research" item #1.
- *Data:* industry10 or industry48. *Effort:* medium (~half a day).
- *Published answer precise enough to check?* **In principle yes — in practice, no, and this is important
  for the gate.** Campbell, Lettau, Malkiel & Xu (2001, *JF* 56(1):1–43) publish annualised variance
  levels for market, industry and firm components [M — read the table directly; I could not verify the
  figures during this review]. But: **(i)** the firm-level component is unreachable without CRSP
  firm-level data; **(ii)** CLMX build the industry component using *market-value shares* of each
  industry, and the daily Ken French industry files on disk contain **no firm counts and no average firm
  size** — those appear only in the *monthly* industry files, which are **not on disk**. An equal-share
  construction is computable but **will not match CLMX's published numbers**, so the "known answer"
  property that justifies running it first is weakened. **Recommendation: either fetch the monthly
  industry files to recover market-value shares, or downgrade this from "replication with a known answer"
  to "construction check with no external benchmark", and say so in the gate.**

---

**#6 — Pairwise Granger edge count (Billio et al. method, industry data).**
- *Establishes:* nothing by way of replication — Billio, Getmansky, Lo & Pelizzon (2012) [V] used monthly
  returns of individual hedge funds, banks, brokers and insurers, not industries. This is a **new estimate
  with an existing method**.
- *Data:* industry10/48, monthly-aggregated or daily. *Effort:* low–moderate.
- *Published answer precise enough to check?* **No** — different universe, different frequency,
  different object.
- *Diagnostic value:* **High, but only as an input to the §9 experiment**, where it is the canonical
  threshold-based estimator whose artifact share is the whole point. As a standalone result it would be a
  fourth costume of the same question and MI-007 says not to.

---

**#7 — Diebold–Yılmaz total connectedness on industry returns.**
- *Establishes:* a US-industry-level TCI series. **[U]** I did not find a published US-industry-level D-Y
  series to check against — D&Y (2014) used ~13 US financial institutions with range-based volatilities;
  Demirer, Diebold, Liu & Yılmaz (2018, *Journal of Applied Econometrics*) used ~96 global banks [M].
- *Data:* industry10 returns. The **volatility** version of D-Y needs daily high/low ranges (Garman-Klass
  / Parkinson), which exist on disk only for index-level OHLC (`ohlc_spy.csv`, `ohlc_nikkei.csv`,
  `ohlc_stoxx.csv`), **not per industry**. So only the return-based version is possible.
- *Effort:* **High** (VAR + generalized FEVD + rolling + lag/horizon choices).
- *Diagnostic value:* **Low relative to cost, and it re-introduces exactly the four tuning knobs the gate
  deliberately excluded.** Recommend against, except as one row of the §9 estimator panel if capacity
  allows.

---

**#8 — Graphical-LASSO edge count through time.**
- Same status as #6: a new estimate with an existing method, no published industry-level benchmark, and
  valuable **only** inside the §9 design where the penalty is the knob under test.

---

### Not replicable on this data — state plainly and stop

| Result | Why not |
|---|---|
| Herskovic et al. (2016) CIV | Needs firm-level idiosyncratic volatilities. An industry-level analogue is a different object with no published benchmark. |
| CLMX firm-level component | Needs CRSP firm-level returns. |
| Laloux/Plerou RMT numbers | Needs ~400–1000 individual stocks; q is not comparable. |
| Billio et al. (2012) as a *replication* | Needs individual financial-institution returns. |
| Aït-Sahalia, Cacho-Díaz & Laeven (2015) Hawkes contagion | Needs high-frequency or at minimum individual-asset jump identification; industry aggregates smooth away the jumps the model is about. |
| Any international out-of-hypothesis-sample confirmation | **No international industry sorts exist** [V]. This is why the maturity ceiling is `research`. |
| Hautsch, Schaumburg & Schienle tail networks | Needs firm-level data and balance-sheet controls. |
| Moskowitz & Grinblatt (1999) industry momentum | *Computable* on this panel, but it is a return-predictability result. **Out of this repo's boundary — do not run it here.** Listed only so a future agent does not propose it as an easy win. |

---

## 11. Recommendations to the gate document (no files changed)

1. **Correct the stale sentence.** "Charter-first status — clean. Nothing implemented. No `scripts/`
   module exists." is false: `scripts/cross_section.py` exists (142 lines). No empirical result has been
   computed from it, so the substance of charter-first discipline holds, but the sentence must be fixed
   before signature.
2. **Fix E2** (§6.4). Assess non-redundancy on the H₀-standardised Ψ, not raw Ψ, or F2 can fire on an
   algebraic identity.
3. **Reconsider the E4 pre-call** (§6.4). For R^r, E4 will likely pass easily; the binding bar is E2.
4. **Add the missing citations** to the gate's G5 prior: Engle & Kelly (2012) DECO as the *imposed* version
   of the null Ψ tests; Ledoit & Wolf constant-correlation shrinkage as the precedent for the Ψ numerator;
   Forbes & Rigobon (2002) and Boyer, Gibson & Loretan (1999) as the ancestors of the null design;
   Krampe & Margaritella (2024/25) as the strongest published statement that crisis connectedness is
   common-factor-driven.
5. **Resolve the NETS check** (§2b) before signing — it determines whether §6.1(3) is a contribution or a
   duplicate.
6. **Gate open item #3 is closed** [V]: no international industry sorts exist on the source; the `research`
   ceiling stands.
7. **Gate open item #4 remains open**, and is now sharper: there is **no builder script in-repo** for
   either industry panel, so weighting/units/basis are unverified. `MANIFEST.csv` records sha256, shape
   and date spans, not provenance for these two rows.
8. **Consider whether §9 (the artifact experiment) should precede the Phase-11 gate rather than follow
   it.** It is methodological validation with no market claim, it is cheaper than the gate, and its
   result changes how the gate's own E1 bar should be read.

---

## 12. Bibliography

Marked as in the body. Entries flagged **[M]** should be verified before being cited in a signed charter.

**Connectedness / variance decomposition**
- Diebold, F.X. & Yılmaz, K. (2009). "Measuring financial asset return and volatility spillovers, with
  application to global equity markets." *Economic Journal* 119(534):158–171. [M]
- Diebold, F.X. & Yılmaz, K. (2012). "Better to give than to receive: Predictive directional measurement
  of volatility spillovers." *International Journal of Forecasting* 28(1):57–66. [M]
- Diebold, F.X. & Yılmaz, K. (2014). "On the network topology of variance decompositions: Measuring the
  connectedness of financial firms." *Journal of Econometrics* 182(1):119–134. [M]
- Demirer, M., Diebold, F.X., Liu, L. & Yılmaz, K. (2018). "Estimating global bank network connectedness."
  *Journal of Applied Econometrics* 33(1):1–15. [M]
- Baruník, J. & Křehlík, T. (2018). "Measuring the frequency dynamics of financial connectedness and
  systemic risk." *Journal of Financial Econometrics* 16(2):271–296. [M] (arXiv:1507.01729 [V])
- Antonakakis, N., Chatziantoniou, I. & Gabauer, D. (2020). "Refined measures of dynamic connectedness
  based on time-varying parameter vector autoregressions." *Journal of Risk and Financial Management*
  13(4):84. [M]
- Krampe, J. & Margaritella, L. (2024/2025). "Decomposing global bank network connectedness: What is
  common, idiosyncratic and when?" arXiv:2402.02482. [V]

**Granger / sparse networks**
- Billio, M., Getmansky, M., Lo, A.W. & Pelizzon, L. (2012). "Econometric measures of connectedness and
  systemic risk in the finance and insurance sectors." *Journal of Financial Economics* 104(3):535–559. [V]
- Barigozzi, M. & Brownlees, C. (2019). "NETS: Network estimation for time series." *Journal of Applied
  Econometrics* 34(3):347–364. [M]
- Hautsch, N., Schaumburg, J. & Schienle, M. (2015). "Financial network systemic risk contributions."
  *Review of Finance* 19(2):685–738. [M]
- Corsi, F., Lillo, F., Pirino, D. & Trapin, L. (2018). "Measuring the propagation of financial distress
  with Granger-causality tail risk networks." *Journal of Financial Stability* 38:18–36. [M]
- Friedman, J., Hastie, T. & Tibshirani, R. (2008). "Sparse inverse covariance estimation with the
  graphical lasso." *Biostatistics* 9(3):432–441. [M]
- Meinshausen, N. & Bühlmann, P. (2006). "High-dimensional graphs and variable selection with the lasso."
  *Annals of Statistics* 34(3):1436–1462. [M]
- Ravikumar, P., Wainwright, M.J., Raskutti, G. & Yu, B. (2011). "High-dimensional covariance estimation by
  minimizing ℓ1-penalized log-determinant divergence." *Electronic Journal of Statistics* 5:935–980. [M]
- Basu, S. & Michailidis, G. (2015). "Regularized estimation in sparse high-dimensional time series
  models." *Annals of Statistics* 43(4):1535–1567. [M]

**Spectral / topology**
- Kritzman, M., Li, Y., Page, S. & Rigobon, R. (2011). "Principal components as a measure of systemic
  risk." *Journal of Portfolio Management* 37(4):112–126. DOI 10.3905/jpm.2011.37.4.112. [V]
- Laloux, L., Cizeau, P., Bouchaud, J.-P. & Potters, M. (1999). "Noise dressing of financial correlation
  matrices." *Physical Review Letters* 83(7):1467–1470. [M]
- Plerou, V., Gopikrishnan, P., Rosenow, B., Amaral, L.A.N., Guhr, T. & Stanley, H.E. (2002). "Random
  matrix approach to cross correlations in financial data." *Physical Review E* 65:066126. [M]
- Mantegna, R.N. (1999). "Hierarchical structure in financial markets." *European Physical Journal B*
  11:193–197. [M]
- Onnela, J.-P., Chakraborti, A., Kaski, K., Kertész, J. & Kanto, A. (2003). "Dynamics of market
  correlations: Taxonomy and portfolio analysis." *Physical Review E* 68:056110. [M]
- Tumminello, M., Aste, T., Di Matteo, T. & Mantegna, R.N. (2005). "A tool for filtering information in
  complex systems." *PNAS* 102(30):10421–10426. [M]
- Kenett, D.Y., Tumminello, M., Madi, A., Gur-Gershgoren, G., Mantegna, R.N. & Ben-Jacob, E. (2010).
  "Dominating clasp of the financial sector revealed by partial correlation analysis of the stock market."
  *PLoS ONE* 5(12):e15032. [M]

**Correlation bias / contagion econometrics — the ancestors of §4**
- Forbes, K.J. & Rigobon, R. (2002). "No contagion, only interdependence: Measuring stock market
  comovement." *Journal of Finance* 57(5):2223–2261. [M]
- Boyer, B.H., Gibson, M.S. & Loretan, M. (1999). "Pitfalls in tests for changes in correlations." Federal
  Reserve International Finance Discussion Paper 597. [M]
- Loretan, M. & English, W.B. (2000). "Evaluating correlation breakdowns during periods of market
  volatility." BIS/Federal Reserve. [M]
- Corsetti, G., Pericoli, M. & Sbracia, M. (2005). "Some contagion, some interdependence: More pitfalls in
  tests of financial contagion." *Journal of International Money and Finance* 24(8):1177–1199. [M]
- Rigobon, R. (2003). "Identification through heteroskedasticity." *Review of Economics and Statistics*
  85(4):777–792. [M]
- Longin, F. & Solnik, B. (2001). "Extreme correlation of international equity markets." *Journal of
  Finance* 56(2):649–676. [M]
- Ang, A. & Chen, J. (2002). "Asymmetric correlations of equity portfolios." *Journal of Financial
  Economics* 63(3):443–494. [M]

**Correlation modelling / equicorrelation**
- Engle, R.F. (2002). "Dynamic conditional correlation." *Journal of Business & Economic Statistics*
  20(3):339–350. [M]
- Engle, R.F. & Kelly, B. (2012). "Dynamic equicorrelation." *Journal of Business & Economic Statistics*
  30(2):212–228. DOI 10.1080/07350015.2011.652048. [V]
- Aielli, G.P. (2013). "Dynamic conditional correlation: On properties and estimation." *Journal of
  Business & Economic Statistics* 31(3):282–299. [M]
- Caporin, M. & McAleer, M. (2013). "Ten things you should know about the dynamic conditional correlation
  representation." *Journal of Economic Surveys* 27(4):736–751. [M]
- Ledoit, O. & Wolf, M. (2003). "Improved estimation of the covariance matrix of stock returns with an
  application to portfolio selection." *Journal of Empirical Finance* 10(5):603–621. [M] *(cited for the
  constant-correlation shrinkage target only)*

**Volatility cross-section**
- Campbell, J.Y., Lettau, M., Malkiel, B.G. & Xu, Y. (2001). "Have individual stocks become more volatile?
  An empirical exploration of idiosyncratic risk." *Journal of Finance* 56(1):1–43. [M]
- Herskovic, B., Kelly, B., Lustig, H. & Van Nieuwerburgh, S. (2016). "The common factor in idiosyncratic
  volatility: Quantitative asset pricing implications." *Journal of Financial Economics* 119(2):249–283. [M]
- Barigozzi, M., Brownlees, C., Gallo, G.M. & Veredas, D. (2014). "Disentangling systematic and
  idiosyncratic dynamics in panels of volatility measures." *Journal of Econometrics* 182(2):364–384. [M]

**Systemic-risk measure critiques**
- Giglio, S., Kelly, B. & Pruitt, S. (2016). "Systemic risk and the macroeconomy: An empirical evaluation."
  *Journal of Financial Economics* 119(3):457–471. [M]
- Löffler, G. & Raupach, P. (2018). "Pitfalls in the use of systemic risk measures." *Journal of Financial
  and Quantitative Analysis* 53(1):269–298. [V]
- Benoit, S., Colletaz, G., Hurlin, C. & Pérignon, C. "A theoretical and empirical comparison of systemic
  risk measures." HEC Paris Research Paper FIN-2014-1030 / SSRN 1973950. [V]
- Benoît, S., Colliard, J.-E., Hurlin, C. & Pérignon, C. (2017). "Where the risks lie: A survey on systemic
  risk." *Review of Finance* 21(1):109–152. [V]
- Bisias, D., Flood, M., Lo, A.W. & Valavanis, S. (2012). "A survey of systemic risk analytics." Office of
  Financial Research Working Paper 0001. [M]

**Change-point / temporal resolution**
- Aue, A., Hörmann, S., Horváth, L. & Reimherr, M. (2009). "Break detection in the covariance structure of
  multivariate time series models." *Annals of Statistics* 37(6B):4046–4087. [M]
- Wied, D., Krämer, W. & Dehling, H. (2012). "Testing for a change in correlation at an unknown point in
  time using an extended functional delta method." *Econometric Theory* 28(3):570–589. [M]
- Barigozzi, M., Cho, H. & Fryzlewicz, P. (2018). "Simultaneous multiple change-point and factor analysis
  for high-dimensional time series." *Journal of Econometrics* 206(1):187–225. [M]
- Cho, H. & Fryzlewicz, P. (2015). "Multiple-change-point detection for high dimensional time series via
  sparsified binary segmentation." *JRSS-B* 77(2):475–507. [M]

**Noisy network inference (statistics/physics, absent from finance)**
- Newman, M.E.J. (2018). "Network structure from rich but noisy data." *Nature Physics* 14:542–545. [M]
- Peixoto, T.P. (2018). "Reconstructing networks with unknown and heterogeneous errors." *Physical Review X*
  8:041011. [M]

**Contagion as a point process**
- Aït-Sahalia, Y., Cacho-Díaz, J. & Laeven, R.J.A. (2015). "Modeling financial contagion using mutually
  exciting jump processes." *Journal of Financial Economics* 117(3):585–606. [M]

**Factor count**
- Bai, J. & Ng, S. (2002). "Determining the number of factors in approximate factor models." *Econometrica*
  70(1):191–221. [M]

---

*End of draft v0.1. Sections 4, 6.4 and 9 are the load-bearing content; everything else is context.*
