# 03 — Economic Relevance and Asset-Pricing Status of Cross-Sectional Structure Measures

**Literature review · DRAFT v0.1 · dated 2026-08-11**
Companion to `01-*` and `02-DEPENDENCY-AND-NETWORKS.md`. Where 02 asks *can we measure cross-sectional
structure honestly*, this document asks the next question: **once measured, is the object economically
meaningful — is it a compensated state variable, or merely a statistic that exists?**

> **Boundary note.** This is a measurement-and-pricing-literature review. It contains no allocation,
> exposure, position, sizing, trading or recommendation concept, and no reviewed result is reported as an
> actionable claim. Journal names and vendor filenames (*Journal of Portfolio Management*, *Financial
> Markets and Portfolio Management*, `48_Industry_Portfolios_Daily_CSV.zip`, and the estimator terms
> "value-weighted" / "equal-weighted") appear only as **source identifiers**, the documented exception in
> `CLAUDE.md`. Where a cited paper's own contribution is a decision rule or an implementable strategy,
> that part is deliberately not reported; only its measurement content is.
>
> **A pricing test is used here as evidence about *measurement validity*** — does a measure track a state
> variable that market participants demonstrably price — **never as a return claim.** See §5.4 for why
> this distinction has a governance consequence for this repo.

> **Verification key** (same convention as 02):
> **[V]** verified against a source fetched during this review · **[M]** from trained memory, plausible and
> standard, **not** re-verified — check before relying on it in a signed charter · **[U]** could not verify,
> despite trying · **[INF]** my inference or derivation, not anyone's published claim.
>
> This review was run as a six-way fan-out of delegated research agents, each fetching primary sources.
> **[V] therefore means "a source was fetched and read during this review", not "I personally read the
> printed journal page."** Several agents hit paywalls, 403s and unparseable PDFs; every such case is
> marked **[U]** and named, rather than filled with a plausible number. Sections §3.3, §4 and §9 are where
> the distinction matters most.

---

## 0. Executive answer, before the detail

**1. The economic-relevance question has been asked repeatedly and answered ambiguously nearly every
time.** Almost every positive pricing result for a cross-sectional structure measure is *in-sample,
single-sample, US-only, and never re-tested out of sample by anyone*. Across six independent search
streams covering CIV, idiosyncratic volatility, network centrality, connectedness, systemic risk and
correlation risk, the agents found **not one** case of a structure measure whose price of risk has been
independently re-estimated on a genuine holdout and confirmed. That absence is itself the headline
finding.

**2. The strongest published results in this entire family are NULLS and REDUNDANCY PROOFS, not positive
pricing results.** In descending order of strength:
- Benoit, Colletaz, Hurlin & Pérignon derive CoVaR/MES/SRISK in a common framework and show they are
  **transformations of standard market-risk measures (e.g. beta)**; empirically, systemic-risk rankings
  "mirror rankings obtained by sorting firms on market risk or liabilities", and **"one-factor linear
  models explain most of the variability of the systemic risk estimates"** [V, verbatim abstract]. §3.3-N1.
- Bali, Cakici, Yan & Zhang (2005, *JF* 60(2)) and Wei & Zhang (2005, *JBF* 29(3)) independently refute
  Goyal & Santa-Clara (2003, *JF* 58(3)): average stock variance does not forecast market returns; the
  result was an equal-weighting × small-cap/NASDAQ × pre-2001-sample artifact [V]. §3.3-N2.
- Löffler & Raupach (2018, *JFQA* 53(1):269–298): there exist **non-exotic cases in which a bank becoming
  riskier — in systematic risk, idiosyncratic risk, size or contagiousness — *lowers* its measured
  systemic-risk contribution** [V]. A measure that moves the wrong way is not a measure. §3.3-N3.
- Idier, Lamé & Mésonnier (2014, *JBF* 47:134–146): across 68 large US banks, **the Tier-1 solvency ratio
  predicts crisis-period equity losses better than MES does** [V]. §3.3-N4.
- Guo, Kassa & Ferguson (2014, *JFQA*): Fu's (2009, *JFE* 91(1)) positive conditional-IVOL/return relation
  is a **look-ahead-bias artifact of full-sample EGARCH estimation**; reconstructed with information
  through *t−1* only, the relation disappears [V]. §3.3-N5.

**3. The algebraic redundancy result this repo already holds is TRUE, ELEMENTARY, and NOT IN PRINT AS A
CRITIQUE.** Six independent search formulations found no published paper stating
AR₁ = [1 + (N−1)ρ̄]/N as a formal redundancy critique of the absorption ratio [U — searched exhaustively,
several exact-phrase queries returned literal zero results, which is a stronger negative than a vague
miss]. **Do not write it up as a discovery.** The algebra is standard in the equicorrelation/DECO
literature (Engle & Kelly 2012, *JBES* 30(2):212–228) [V] and follows as a special case of the
random-matrix "market mode" result (Laloux et al. 1999, *PRL* 83:1467; Plerou et al. 2002, *PRE* 65:066126)
[M]. Its value to this repo is as an **admission gate**, not as a contribution. §4.

**4. The correct general form of that result is stronger than the equicorrelation special case, and it
identifies exactly what is non-redundant.** By the Rayleigh quotient with the equal-weight vector,
**AR₁ ≥ ρ̄ + (1−ρ̄)/N for *any* correlation matrix**, with equality iff the equal-weight vector is the
leading eigenvector. The non-negative gap is precisely the loading-heterogeneity term. §4.2 [INF].
And under equicorrelation with equal variances, **AR₁ equals Var(equal-weight index) / average constituent
variance, exactly** — which is also the CBOE-style implied-correlation formula and the object Engle & Kelly
derive [V for the E&K identity; INF for the AR₁ equality]. So *absorption ratio, average pairwise
correlation, implied correlation, and the index-variance-to-constituent-variance ratio are one scalar in
that limit.* This unification is what makes the redundancy critique bite. §4.3.

**5. CIV (Herskovic, Kelly, Lustig & Van Nieuwerburgh 2016, *JFE* 119(2):249–283) is a strong in-sample
result with three specific weaknesses** [V]: (a) the headline spread **moved from 6.4%/yr in the 2014 NBER
draft to 5.4%/yr in the published abstract**; (b) test assets are individual-stock sorted groups, and
Gempesaw, Kassa & Zykaj (2022, *European Financial Management* 28(3):693–721) report **"the IVOL puzzle
disappears when using well-diversified [sorted groups] as test assets"**; (c) **no out-of-sample or
international replication of the CIV-beta pricing test exists** [U — searched, none found]. Yin, Shu & Su
(2019, *IJFE* 24(1):370–390) find the CIV-return relation **flips sign by horizon** in Chinese data. §3.2.

**6. "Firm Volatility in Granular Networks" is a MEASUREMENT paper, not a pricing paper.** Herskovic,
Kelly, Lustig & Van Nieuwerburgh (2020, *JPE* 128(11):4097–4162) — note the authorship changed from the
3-author 2013 NBER WP 19466 — explains *why a common factor in idiosyncratic volatility exists*
(size-dependent customer-supplier network formation). It runs **no cross-sectional risk-premium test** [V].
Citing it as evidence that network structure is priced is a misreading. §3.4.

**7. Network centrality pricing is thinner than its citation count suggests.** The paper most often cited
for "centrality is priced in equities" — **Ahern, "Network Centrality and the Cross Section of Stock
Returns" (SSRN 2197370, Dec 2013) — appears never to have been published in a refereed journal**, despite
a decade of heavy citation [V for the working-paper status; U at ~high-but-not-certain confidence for
"never published"]. The peer-reviewed results that do exist (Herskovic 2018 *JF* 73(4); Richmond 2019 *JF*
74(3); Gofman, Segal & Wu 2020 *RFS* 33(12); Branger et al. 2021 *Review of Finance* 25(3)) are **all
in-sample**, with no holdout test reported in any of them [V]. §3.2.

**8. Diebold–Yilmaz connectedness has never been shown to be priced, and has never been shown to forecast
anything out of sample.** It is a rolling-window *description* of estimated interdependence, evaluated
in-sample against crises already contained in the estimation window. The "forecast-based" in the 2012 title
refers to the *forecast-error* variance decomposition used to build it, not to predictive validation — a
common and consequential misreading [V]. §3.4.

**9. The "correlation risk premium" and the "index variance risk premium" may be one fact wearing two
names.** Driessen, Maenhout & Vilkov's (2009, *JF* 64(3):1377–1406) own decomposition makes index variance
risk premium ≡ weighted sum of individual variance risk premia + correlation risk premium; since they
show individual variance risk premia are indistinguishable from zero (null not rejected for 98 of 127
stocks), **the correlation risk premium is definitionally what the index variance risk premium is**, not a
second independent premium [V]. Cosemans (2010/11, SSRN, unpublished) reaches the same conclusion from the
predictive-regression side. And DMV's own frictions check collapses the result: **bid-ask spreads roughly
halve the premium and the alpha t-statistic falls from 1.96 to 0.77** [V]. §3.3-N6.

**10. The genuine gap is not "is X priced." It is "how much of X is one scalar, asked systematically and
pre-registered."** Nobody has taken a battery of cross-sectional structure measures, computed them on one
panel, and reported the share of each that is spanned by {average correlation, aggregate volatility}, with
a pre-registered kill threshold. Nor does anyone run the **matched-transform volatility control** — the
same standardized-shift transform applied to volatility instead of the structure measure. §7.

**11. Where the frontier actually is: multiple-testing and replication, not new measures.** Harvey, Liu &
Zhu (2016, *RFS* 29(1):5–68) put the honest threshold for a *new* priced factor at |t| > 3.0 [M]; Hou, Xue
& Zhang (2020, *RFS* 33(5):2019–2133) report that a large majority of 452 published anomalies fail even
|t| > 1.96 under value-weighting and NYSE breakpoints [M]. Under that regime, **almost none of the
structure-measure pricing results reviewed here would clear the bar today.** §10.

---

## 1. Q1 — What has already been solved?

*Framed as: what would a competent referee say is no longer an open question?*

**1.1 That aggregate volatility risk carries a NEGATIVE price of risk.** Settled directionally, with
independent corroboration by a methodologically distinct estimator. Ang, Hodrick, Xing & Zhang (2006, *JF*
61(1):259–299) estimate roughly **−1%/yr** on a VIX-innovation-mimicking factor [V for the sign and rough
magnitude; U for the exact table coefficient — every PDF host returned unparseable output to the agent].
Cremers, Halling & Weinbaum (2015, *JF* 70(2):577–614), using option-based factor-mimicking series
orthogonalized against each other, separate jump from volatility risk and find both negatively priced:
a two-standard-deviation increase in volatility-risk loading is associated with **2.7–2.9% p.a.** lower
expected return, and in jump-risk loading **3.5–5.1% p.a.** [V]. Chang, Christoffersen & Jacobs (2013,
*JFE* 107(1):46–68) find a risk-neutral-skewness price of risk of **−6.00% to −8.40% annually** [V].

**The theory behind the sign is the single most transferable idea in this literature, and it should be
taught not assumed.** Under Merton's (1973) ICAPM as developed by Campbell (1993, 1996) [M], state
variables that forecast *future investment opportunities* are priced. An increase in aggregate volatility
is bad news for a long-horizon agent: it signals a worse future opportunity set. An asset whose return is
*high* exactly when volatility jumps therefore pays off in the bad state — it is a **hedge**. Agents accept
a *lower* expected return to hold that payoff profile, so the cross-sectional regression of average returns
on the volatility-innovation loading has a **negative slope**. This is why "negative λ" is the *signature*
of a hedge, and why finding a *positive* λ on a volatility-like factor should be treated as evidence the
factor is not measuring what its name says. **Standard-literature terms:** ICAPM, intertemporal hedging
demand, price of risk (λ), factor-mimicking series, two-pass Fama–MacBeth.

> *"What would happen if…"* — if you estimated λ on an innovation series and got a **positive** and
> significant λ, what are the three most likely causes, in order? (My ranking: the innovation series is
> sign-flipped relative to the state variable; the "innovation" is contaminated by the contemporaneous
> return of the test assets themselves; or the state variable is procyclical, not countercyclical, and the
> hedge story does not apply.)

**1.2 That idiosyncratic volatility has a strong common factor.** Settled by at least four independent
constructions. Connor, Korajczyk & Linton (2006, *Journal of Econometrics* 132(1):231–255) estimate a
dynamic approximate factor model with a common component in asset-specific variance [V]. Herskovic et al.
(2016) report a first principal component explaining **~35–36%** of the idiosyncratic-volatility panel,
essentially invariant to whether returns are purged by CAPM, FF3 or a 5-PC statistical model (34.6%,
34.8%), with **81–84%** average pairwise correlation of idiosyncratic volatility across size groups and a
minimum of 65% across industry groups [V]. Duarte, Kamara, Siegel & Sun (SSRN 1905731) independently find
~1/3 [V, working paper; U on journal placement]. Bekaert, Wang & Zhang (*Management Science*, CEPR DP
18230) find **"strong global commonality in country idiosyncratic return variances across 23 developed
markets, which is stronger than international return commonality"** [V].

The decisive detail: Herskovic et al. show this comovement is in *second* moments while average pairwise
correlation of the residual *returns* themselves is **< 0.2–0.9%** — which rules out "you just omitted a
common return factor" as the explanation [V].

**1.3 That the equity correlation matrix is dominated by one large eigenvalue, and that this eigenvalue
tracks average correlation.** Settled. The random-matrix result (Laloux, Cizeau, Bouchaud & Potters 1999,
*PRL* 83:1467; Plerou et al. 1999 *PRL* 83:1471, 2002 *PRE* 65:066126) [M] is that the bulk of the spectrum
is indistinguishable from Marchenko–Pastur noise, with a single anomalously large "market mode."
Zheng, Podobnik, Feng & Li (2012, *Scientific Reports* 2:888) state in print that **"previous work has
shown that the first PC is closely related to the average correlation"**, citing Billio, Getmansky, Lo &
Pelizzon (2010, NBER WP 16223) [V]. Reigneron, Allez & Bouchaud (2011, *Physica A* 390(17):3026–3035) show
the dominant eigenvalue and average correlation move together, while the *uniformity of the eigenvector*
does separate work [V]. §4 makes the algebra exact.

**1.4 That the Goyal–Santa-Clara average-variance predictability result does not hold.** Settled, and it is
the cleanest documented null in the family. See §3.3-N2.

**1.5 That systemic-risk measures are largely restatements of standard risk measures.** Settled
analytically and empirically by Benoit, Colletaz, Hurlin & Pérignon; extended to a general copula setting
by Leeuwenkamp (arXiv:2206.02582, 2022/23), who shows **CoVaR, ΔCoVaR, CoES, ΔCoES and MES can all be
written as univariate VaR/ES evaluated at copula-determined quantiles** [V, preprint — weight accordingly].
See §3.3-N1.

**1.6 That published cross-sectional predictability decays after publication.** Settled. McLean & Pontiff
(2016, *JF*) over 97 predictors: **26% lower out-of-sample, 58% lower post-publication**, implying ~32
percentage points attributable to publication [V]. Any new priced-factor claim must be evaluated against
this base rate, not against zero.

---

## 2. Q2 — What methods already exist?

The methods are mature and none of them needs inventing. The table separates **what is measured** from
**how economic relevance is tested**, because conflating the two is the field's most common error.

### 2.1 Measurement constructions

| Object | Canonical construction | Source |
|---|---|---|
| Common idiosyncratic volatility (CIV) | Equal-weighted cross-sectional mean of firm-level residual variance from a within-period market-model regression; monthly *changes*, **orthogonalized against market-variance changes** | Herskovic et al. 2016 [V] |
| Aggregate volatility innovation | Daily ΔVIX (ΔVXO pre-1990); or a factor-mimicking series projected onto base assets (FVIX) | AHXZ 2006 [V]; Barinov [V] |
| Idiosyncratic volatility (firm) | SD of daily residuals from FF3 within a month | AHXZ 2006 [V] |
| Conditional idiosyncratic volatility | EGARCH(p,q) forecast — **contaminated by look-ahead unless refit strictly through t−1** | Fu 2009 [V]; Guo, Kassa & Ferguson 2014 [V] |
| Average pairwise correlation ρ̄ | Mean off-diagonal of a trailing correlation matrix | Pollet & Wilson 2010 *JFE* 96(3):364–380 [V] |
| Dynamic equicorrelation (DECO) | Single time-varying scalar ρ_t restricted equal across all pairs; QMLE-consistent even when the DGP is DCC | Engle & Kelly 2012 [V] |
| Absorption ratio AR_K | Share of total variance in the top K eigenvalues of a trailing covariance matrix; K ≈ N/5; "standardized shift" = [MA₁₅ − MA₂₅₂]/sd₂₅₂ | Kritzman, Li, Page & Rigobon 2011, *JPM* 37(4):112–126 [V] |
| PCA systemic risk | Fraction of variance in the top components of a return panel | Billio et al. 2012, *JFE* 104(3):535–559 [V] |
| Granger-causality network density | Fraction of significant pairwise Granger links; in/out-degree; eigenvector centrality | Billio et al. 2012 [V] |
| Connectedness index | Generalized (order-invariant) forecast-error variance decomposition of a VAR, read as a weighted directed network | Diebold & Yilmaz 2009 *EJ* 119; 2012 *IJF* 28(1); 2014 *J.Econometrics* 182 [V] |
| ΔCoVaR | VaR of the system conditional on institution *i* at its own VaR, minus the same at *i*'s median state | Adrian & Brunnermeier 2016, *AER* 106(7):1705–1741 [V] |
| MES / SES | Expected equity loss of *i* conditional on the market's own tail; SES adds leverage | Acharya, Pedersen, Philippon & Richardson 2017, *RFS* 30(1):2–47 [V] |
| SRISK | Expected capital shortfall conditional on a severe market decline; function of size, leverage, LRMES | Brownlees & Engle 2017, *RFS* 30(1):48–79 [V] |
| Cross-sectional variance (CSV) | Cross-sectional variance of individual returns as a **model-free** estimator of aggregate idiosyncratic volatility | Garcia, Mantilla-Garcia & Martellini 2014, *JFQA* 49(5-6):1133–1165 [V] |
| CSSD / CSAD | Cross-sectional SD / absolute deviation of returns from the market return; herding read off the *nonlinearity* in market return | Christie & Huang 1995 *FAJ* 51(4):31–37; Chang, Cheng & Khorana 2000 *JBF* 24(10):1651–1679 [V] |
| Implied correlation | (σ²_index − Σwⱼ²σⱼ²) / (Σ_{i≠j} wᵢwⱼσᵢσⱼ) — **a deterministic transform of index and constituent implied volatilities, not an independent observable** | Engle & Kelly 2012 [V] |
| Integration R² | R² from regressing a country's return on globally PCA-extracted factors — proposed *against* raw correlation | Pukthuanthong & Roll 2009, *JFE* 94(2):214–232 [V] |

### 2.2 Economic-relevance test designs

1. **Two-pass Fama–MacBeth with Shanken (1992) errors-in-variables correction.** Estimate loadings on
   innovations in the structure measure, then regress average returns on loadings across test assets.
   Reported quantity: the price of risk λ, its sign, and its t-statistic. Krishnan, Petkova & Ritchken
   (2009 — **published in *Journal of Empirical Finance* 16(3):353–367, not *Journal of Financial
   Markets*; correct this citation wherever it appears**) is the canonical template using return data only
   [V].
2. **Sorted-group spread tests.** Sort assets on the estimated loading; report the return spread between
   extreme groups and its alpha against a factor model. Herskovic et al. 2016; Herskovic 2018; AHXZ 2006.
3. **Double sorts as a confound control.** Herskovic et al. sort on CIV-beta within market-variance-beta,
   size, idiosyncratic-variance and liquidity-beta quintiles [V]. This is the discipline analogue of the
   repo's V5 "incremental to volatility" bar.
4. **Factor-mimicking projection.** Project the non-traded innovation onto a set of base assets to obtain a
   traded series with an interpretable mean. AHXZ's FVIX; Barinov's purged FVIX.
5. **Predictive regressions with out-of-sample evaluation.** In-sample slope + R², then Welch & Goyal
   (2008, *RFS* 21(4):1455–1508)-style out-of-sample R² against the prevailing-mean benchmark, with
   Clark & West (2007, *J.Econometrics* 138(1):291–311) MSPE-adjusted inference for nested models [M].
   **This step is the one the structure-measure literature almost never performs.**
6. **Event-window "validation."** Regress crisis-realized outcomes on pre-crisis measure values (APP&R
   2017; Brownlees & Engle 2017). Structurally a **single-episode retrospective fit**, and treating it as
   an out-of-sample test is the central methodological complaint against the systemic-risk literature [V].
7. **Cross-measure horse races and rank correlations.** Benoit et al.; Nucera, Schwaab, Koopman & Lucas
   (2016, *Journal of Empirical Finance* 38(A):461–475 — **not *JBF***, correct this citation) pool
   rankings by PCA precisely because individual rankings are contaminated by estimation uncertainty [V].
8. **Quantile / growth-at-risk evaluation.** Test whether the measure predicts the *lower tail* of future
   macro outcomes rather than the mean. Giglio, Kelly & Pruitt (2016, *JFE* 119(3):457–471) [M];
   Adrian, Boyarchenko & Giannone (2019, *AER* 109(4):1263–1289) [M]. See §3.3-N8 for the backtest null.

---

## 3. Q3 — What empirical findings are established, and which contested?

### 3.1 Established (replicated, or mechanism-anchored, or both)

| Finding | Confidence |
|---|---|
| Aggregate volatility risk is negatively priced (the hedge-asset signature) | High — corroborated by an independent option-based estimator (Cremers-Halling-Weinbaum) [V] |
| Idiosyncratic volatility has a strong common factor (~1/3 of panel variance) | High — four independent constructions [V] |
| The high-IVOL / low-return pattern exists and is international | High — AHXZ 2009 *JFE* 91(1): **−1.31%/month** spread after world market, size and value controls across 23 developed markets, individually significant in each G7 country [V] |
| The IVOL pattern **replicates out of sample post-2000, attenuated** | High — Detzel, Duarte, Kamara, Siegel & Sun (2023, *Critical Finance Review* 12(1-4):9–56): the spread "decreases but remains significant out of sample"; aggregate-volatility-risk pricing survives except for NASDAQ names [V] |
| The correlation matrix has a dominant market mode tracking average correlation | High [M/V] |
| A single equicorrelation scalar captures the dominant common movement of a large correlation matrix well enough to be useful, and is QMLE-consistent under DCC misspecification | High — Engle & Kelly 2012 [V] |
| Systemic-risk measures are monotone/copula transformations of standard risk measures | High — Benoit et al. [V]; Leeuwenkamp [V, preprint] |
| Credit growth has genuine long-horizon, cross-country early-warning content | High — Schularick & Taylor 2012, *AER* 102(2):1029–1061; Borio–Drehmann credit-to-GDP gap [V] |
| Published predictability decays post-publication | High — McLean & Pontiff 2016 [V] |

### 3.2 Contested

| Claim | Why contested |
|---|---|
| **CIV is priced with λ < 0** | Headline spread **6.4%/yr (2014 NBER draft) → 5.4%/yr (2016 *JFE* abstract)** [V]; test assets are individual-stock sorted groups and the effect **disappears on well-diversified sorted groups** (Gempesaw, Kassa & Zykaj 2022) [V]; **sign flips by horizon in Chinese data** (Yin, Shu & Su 2019: negative < 4 months, positive 4–16 months, negative again long-horizon) [V]; **no out-of-sample or international replication of the CIV-beta test exists** [U] |
| **The IVOL puzzle is a risk story** | Stambaugh, Yu & Yuan (2015, *JF* 70(5):1903–1948) give a mispricing account: negative among overpriced names, positive among underpriced, net negative because overpricing dominates [V]. Hou & Loh (2016, *JFE* 121(1):167–194): individual candidate explanations each explain **< 10%** (coskewness ≈1.9%, analyst-dispersion ≈5.3%); **combined, all existing explanations account for 29–54% at the individual-stock level and 78–84% at the sorted-group level** [V] |
| **The IVOL result is robust to estimation choices** | Bali & Cakici (2008, *JFQA* 43(1):29–58): **no robustly significant relation** across data frequency × weighting × breakpoints × screens, and **no effect at all under equal weighting** [V]. Huang, Liu, Rhee & Zhang (2010, *RFS* 23(1):147–168): with daily-estimated IVOL, the relation **disappears once short-term reversal is controlled**; with monthly-estimated IVOL a **positive** relation survives [V]. Han & Lesmond (2011, *RFS* 24(5):1590–1629): a closed-form microstructure bias from zero returns and bid-ask bounce; correcting it eliminates the predictive ability, and the effect weakens after the 1997 tick change and 2001 decimalization [V] |
| **Network centrality is priced in equities** | The most-cited source (Ahern 2013) **appears never to have been published** [V/U]. Peer-reviewed results — Herskovic 2018 *JF* 73(4):1785–1818 (sparsity-beta spread **+4.6%/yr**, concentration-beta **−3.2%/yr**); Richmond 2019 *JF* 74(3):1315–1361 (central countries have *lower* currency risk premia — note the **opposite sign convention** to the equity papers); Gofman, Segal & Wu 2020 *RFS* 33(12):5856–5905 — are **all in-sample with no holdout reported** [V] |
| **Correlation risk is a separately priced factor** | See §3.3-N6. KPR's return-based factor is the strongest evidence *for* separability (λ = **−0.7726/month, t = −2.93** baseline; **−0.5067, t = −2.18** with Pastor-Stambaugh liquidity; test assets the 25 size×value sorts; 1963–2003) [V], and **has never been re-tested out of sample by anyone** [U] |
| **Adrian–Brunnermeier's forward-CoVaR predicted the crisis** | Secondary sources render the headline claim as both "more than one-third" and "more than half" of realized crisis covariances predicted from 2006:Q4 information; the agent could not reconcile them against the *AER* text [U]. The design is an ex-ante-characteristics fit, not a holdout forecast |
| **The absorption ratio leads drawdowns** | Kritzman et al.'s own claim — **all of the worst 1% monthly US equity drawdowns 1998–2010 were preceded by a standardized AR shift > 1** [V, secondary-sourced quote; U on the primary table]. No independent replication located; no matched-transform volatility control run [U] |

### 3.3 THE DOCUMENTED NULLS — the most valuable rows in this review

These are ranked by how directly they bear on this repo's programme.

**N1 — Systemic-risk measures are one factor wearing many names. [V, verbatim abstract]**
Benoit, Colletaz, Hurlin & Pérignon, "A Theoretical and Empirical Comparison of Systemic Risk Measures"
(HAL halshs-00746272 / SSRN 1973950; **journal placement unconfirmed — treat as a working paper** [U]):
> *"We derive several popular systemic risk measures in a common framework and show that they can be
> expressed as transformations of market risk measures (e.g. beta)… (1) different systemic risk measures
> identify different SIFIs and (2) firm rankings based on systemic risk estimates mirror rankings obtained
> by sorting firms on market risk or liabilities. One-factor linear models explain most of the variability
> of the systemic risk estimates, which indicates that systemic risk measures fall short in capturing the
> multiple facets of systemic risk."*
Separately corroborated: *"the empirical CoVaR of a firm is strongly correlated with its VaR, indicating
that CoVaR brings limited added value over and above VaR to forecast systemic risk"* [V].
**Not verified:** the exact proposition numbering, the distributional assumption the monotonicity rests on
(linear factor model / joint normality / general elliptical — the agent could not confirm which; my guess
of "linear factor model" is [INF]), the rank-correlation coefficients, and the one-factor R². Every PDF
host served a bot-wall or unparseable binary. **Pull this paper by hand before citing a number from it.**

**N2 — Average stock variance does not forecast market returns. [V]**
Goyal & Santa-Clara (2003, *JF* 58(3):975–1007) claimed a positive relation between average (largely
idiosyncratic) stock variance and next-month market return. Bali, Cakici, Yan & Zhang (2005, *JF*
60(2):905–929) refute it on three independent grounds: **extending the sample through 2001–2003 removes
it**; it is an artifact of the **equal-weighted** average-variance measure and is far weaker or
insignificant value-weighted; and it is **concentrated in small-cap and NASDAQ names**. Wei & Zhang (2005,
*JBF* 29(3):603–621) reach the same conclusion independently and contemporaneously. This is the template
failure mode for every cross-sectional-dispersion predictability claim: *an equal-weighted cross-sectional
moment overweights the smallest, least liquid, most microstructure-contaminated series, and that is where
the "predictability" lives.*

**N3 — Systemic-risk measures can move the wrong way. [V]**
Löffler & Raupach (2018, *JFQA* 53(1):269–298) identify **"non-exotic cases in which a change in a bank's
systematic risk, idiosyncratic risk, size, or contagiousness increases the risk of the system but lowers
the measured systemic risk contribution of the bank."** Also: a change in one bank's risk structure can
raise its **competitors'** measured contributions more than its own; and under contagion, CoVaR and MES
give **conflicting signals** on infectious versus infected institutions. **Not verified:** the exact
algebraic counterexample [U].

**N4 — MES loses to a balance-sheet ratio out of sample. [V]**
Idier, Lamé & Mésonnier (2014, *JBF* 47:134–146), 68 large US banks, 2007–09 as the test window:
**"standard balance-sheet metrics like the Tier 1 solvency ratio are better able than the MES to predict
equity losses conditional on a true crisis."** Magnitude unverified [U].

**N5 — A headline positive result was manufactured by look-ahead in the estimator. [V]**
Fu (2009, *JFE* 91(1):24–37) reported a significantly *positive* conditional-IVOL/return relation using
EGARCH forecasts. Guo, Kassa & Ferguson (2014, *JFQA*) show standard EGARCH estimation fits parameters on
the **full sample including month t's own return**, so month t leaks into the month-t "forecast."
Reconstructed with information through **t−1 only, the significant relation disappears.** This is the
single most instructive null in this review for a repo whose central control is `assert_causal`: *the
look-ahead was not in the data alignment, it was in the parameter estimation.* A `.shift()` audit would
not have caught it.

**N6 — "Correlation risk premium" and "index variance risk premium" may be one object. [V]**
Driessen, Maenhout & Vilkov (2009, *JF* 64(3):1377–1406), OptionMetrics 1996–2003, S&P100 and its
constituents. Their own decomposition: index variance = Σwᵢ²σᵢ² + Σ_{i≠j}wᵢwⱼσᵢσⱼρᵢⱼ, so the index
variance risk premium is *exactly* a weighted sum of individual variance risk premia plus the correlation
risk premium. Empirically the individual leg is zero: **realized 41.44% vs implied 38.97% (t = 3.2) — the
wrong sign for a premium; the null of zero is not rejected for 98 of 127 stocks**; a common
individual-variance factor prices at +0.077/month, **t = 1.74, insignificant**. The correlation risk
premium is therefore *definitionally* the residual that the index variance risk premium already was.
Cosemans (SSRN, unpublished) independently finds the market variance risk premium's predictive power for
the equity premium is **"completely driven by"** the correlation risk premium [V].
And the pricing result does not survive frictions on the authors' own numbers: **raw 10.37%/month, CAPM
alpha 10.59% (t = 1.96) → with bid-ask spreads, 5.3% and alpha 5.5% (t = 0.77, insignificant)**; Sharpe
falls from 0.73 to 0.41, exactly the unlevered equity Sharpe [V]. DMV themselves concede the result "may
also be consistent with a hypothesis of index-option mispricing."

**N7 — Implied correlation is not an independent observable. [V]**
Engle & Kelly (2012) derive ρ = (σ²_basket − Σwⱼ²σⱼ²) / (Σ_{i≠j}wᵢwⱼσᵢσⱼ) explicitly. CBOE-style implied
correlation is a **deterministic transform of index implied volatility and constituent implied
volatilities** — two things already measured. Whether a deterministic nonlinear transform of two priced
variables can itself carry a *separate* premium (rather than being spanned by them) is unresolved in print
[INF]. **This critique applies squarely to the options-based correlation literature and NOT to
return-based constructions like KPR's**, which never touch the identity.

**N8 — Financial-conditions information adds little out of sample for growth-at-risk. [M — verify before
relying on]** Brownlees & Souza (2021, *Journal of Monetary Economics* 118:312–330), "Backtesting global
growth-at-risk," report that GARCH-type models using GDP alone perform as well as or better than quantile
regressions augmented with financial-conditions indices, out of sample. This is the closest thing in print
to a direct out-of-sample null on the whole "financial stress measures forecast bad macro outcomes"
programme, and it partially offsets Giglio, Kelly & Pruitt (2016) [M] and Adrian, Boyarchenko & Giannone
(2019) [M]. **Flagged [M] because no agent verified it; it is important enough to check by hand.**

**N9 — No market-based systemic-importance measure is valid across crises. [V]**
Zhang, Vallascas, Keasey & Cai (2015, *Journal of Money, Credit and Banking* 47(7):1403–1442) test four
market-based measures across three crises: **for 2007–08 only ΔCoVaR consistently adds predictive power to
conventional early-warning models, and even that addition is small; the result does not hold for the
1997–98 Asian crisis.** Conclusion: it is problematic to identify any single market-based measure that
remains valid across crises with different characteristics.

**N10 — Systemic-risk rankings are not statistically identifiable. [V]**
Danielsson, James, Valenzuela & Zer (2016, *JMCB* 48(4):795–812), "Can we prove a bank guilty of creating
systemic risk? A minority report": **"estimation error alone prevents the reliable identification of the
most systemically risky banks,"** and "it will be a considerable challenge to develop a riskometer that is
sound and reliable enough to provide an adequate foundation for macroprudential policy." Companion result
(2016, *Journal of Financial Stability* 23:79–91): **model disagreement across risk models is small in
calm periods and rises sharply in distress** — largest exactly when the measure is needed. Quantitative
ranking-instability statistics unverified [U].

**N11 — The IVOL puzzle vanishes on diversified test assets. [V]**
Gempesaw, Kassa & Zykaj (2022, *European Financial Management* 28(3):693–721): if IVOL proxied for a
missing systematic factor, diversification into sorted groups should *preserve* it, since factor loadings
do not average away. **"The IVOL puzzle disappears when using well-diversified [sorted groups] as test
assets."** Direct challenge to reading the IVOL/CIV literature as evidence of a single missing systematic
factor — and **directly relevant to this repo, because Ken French sorted groups are exactly such
well-diversified test assets** (§9).

### 3.4 Widely asserted, NOT established

- **"Connectedness predicts crises."** Diebold–Yilmaz indices have never been shown to have out-of-sample
  forecasting content; the primary papers make no such claim and run no such test [V]. One comparative
  study puts the DY total-connectedness lead time at **~2.0 days** versus ~9.7 days for entropy-based
  alternatives, and reports DY **failing to detect 3 of 4** crisis events in a crypto application
  [U on author/venue — surfaced only through a secondary summary; do not cite without tracing].
- **"Billio et al. predicted the crisis."** The measures rise around 2007–09 *within the estimation
  window that contains 2007–09*. That is in-sample description. The authors' own language ("seem to
  contain predictive power", "may serve as early warning indicators") outruns the design [V].
- **"Granger-causality network density measures transmission."** Bilateral Granger tests that do not
  condition on the rest of the system "may find misleading spurious causality edges and tend to
  overestimate linkages"; the field's own migration to generalized-FEVD methods is the tacit admission
  [V]. *No paper named "Baek & Chen" attacking Billio et al. could be located* — do not cite it [U].
- **"Granular networks show network location is priced."** Herskovic, Kelly, Lustig & Van Nieuwerburgh
  (2020, *JPE* 128(11):4097–4162) run no pricing test. It explains the *level and comovement* of
  idiosyncratic volatility via size-dependent customer-supplier network formation. Herskovic et al. (2016)
  cite it precisely that way in their own literature review [V].
- **"Composite financial-stress indices are leading indicators."** The OFR Financial Stress Index and the
  ECB CISS are, by their own construction descriptions, weighted averages of *current* market variables'
  deviation from historical norms — coincident gauges. No study demonstrating validated leading value was
  located [U — the agent flagged this as the weakest-sourced part of its memo; treat as an open search].
- **"Credit growth beats market-based measures out of sample."** Almost certainly true, but **no paper runs
  the credit-to-GDP gap against CoVaR/MES/SRISK in one horse race.** The claim rests on comparing two
  separate literatures' self-reported performance [INF, flagged by the agent]. That absence is itself a
  gap worth recording.

---

## 4. Interlude — the redundancy algebra, stated correctly

This section exists because it is the repo's own asset (`.planning/archive/dropped-signals/05-ABSORPTION-DROPPED.md`,
G3) and because the literature review changes how it should be framed.

### 4.1 The equicorrelation special case (already in the repo)

Let C be an N×N correlation matrix under exact equicorrelation ρ: C = (1−ρ)I + ρ**11**ᵀ. Then
- eigenvalue **1 + (N−1)ρ**, once, with eigenvector **1**/√N;
- eigenvalue **1 − ρ**, with multiplicity N−1;
- trace = N.

So **AR₁ = [1 + (N−1)ρ] / N = ρ + (1−ρ)/N** — affine in ρ with slope (N−1)/N → 1. For N = 48, AR₁ and ρ̄
differ by at most 1/48 ≈ 0.021 across the whole range. *They are the same number.*

### 4.2 The general case, which is the defensible form [INF]

Do not restrict to equicorrelation. For **any** correlation matrix C, the Rayleigh quotient at the
equal-weight vector gives
λ₁ = max_x (xᵀCx)/(xᵀx) ≥ (**1**ᵀC**1**)/N = [N + N(N−1)ρ̄]/N = 1 + (N−1)ρ̄,
where ρ̄ is the average off-diagonal correlation. Therefore

> **AR₁ ≥ ρ̄ + (1−ρ̄)/N for every correlation matrix, with equality iff the equal-weight vector is the
> leading eigenvector.**

This is stronger and more useful than the equicorrelation statement, because it converts the redundancy
claim into a **measurable decomposition**:

> **H_t ≡ AR₁,t − [ρ̄_t + (1−ρ̄_t)/N] ≥ 0**

H_t is exactly the part of the leading eigenvalue share that average correlation cannot account for — the
**loading-heterogeneity term**, i.e. how far the market mode has rotated away from uniformity. Reigneron,
Allez & Bouchaud (2011) show empirically that this *uniformity of the market mode* does separate work from
the eigenvalue magnitude [V], which is the published result closest to H_t, though they do not define it.

**Consequence for any absorption-type charter:** the admissible non-redundant object is **H_t, not AR₁**.
A signal built on AR₁ is a signal built on ρ̄ plus a rounding error. This is a sharper admission gate than
the one the dropped Phase-5 charter registered (which set a |corr| < 0.90 threshold against volatility);
H_t is the residual by construction, so no threshold is needed to define it.

**Caution [INF]:** H_t inherits the pathology that 02 §6.4 identified for Ψ — a statistic defined as a
residual from a ρ̄-benchmark has built-in mechanical dependence on ρ̄, and any redundancy bar of the form
"|Spearman(H, ρ̄)| < c ⇒ else DROP" would be testing algebra, not science. The correct bar is whether H
carries **incremental information**, not whether it is **uncorrelated**.

### 4.3 The unification that makes the critique bite [INF, with [V] components]

Take equal weights and equal variances σ̄² across N series with common correlation ρ. Then the variance of
the equal-weight aggregate is

Var(r̄) = (1/N²)[Nσ̄² + N(N−1)σ̄²ρ] = σ̄² · [1 + (N−1)ρ]/N = **σ̄² · AR₁**

so **AR₁ = Var(equal-weight aggregate) / (average constituent variance), exactly.** But that ratio is
*also* the object Engle & Kelly derive as implied correlation [V], and it is *also* the CBOE-style
implied-correlation formula [V], and it is *also* what Pollet & Wilson's average-correlation predictor is
proxying for [V — their stated motivation is precisely that aggregate risk shows up as average pairwise
correlation rather than as index variance]. In this limit:

> **absorption ratio ≡ average pairwise correlation ≡ implied correlation ≡ index-variance-to-average-
> constituent-variance ratio ≡ (inverse squared) diversification ratio.** One scalar, five names.

The five differ only through (i) loading heterogeneity — the H_t term of §4.2 — (ii) variance heterogeneity
across constituents, and (iii) the risk-neutral-versus-physical wedge in the option-based versions. Those
three residuals are the entire non-redundant content of the family.

### 4.4 Is this in print as a critique? No. [U, high confidence]

Six distinct query formulations across two search engines plus targeted publisher fetches found **no paper
stating the equicorrelation identity as a formal redundancy critique of the absorption ratio.** Several
exact-phrase queries returned literal zero results. What exists instead:
- **Kritzman et al. themselves pre-empt the comparison**: *"We make a similar argument that the absorption
  ratio is a better measure of systemic [risk] than average correlation, but our main focus is to
  demonstrate that the absorption ratio is a reliable indicator of market fragility"* [V, quoted from a
  State Street republication of the *JPM* paper]. The authors treat it as a claim requiring defence — and
  the agent could not extract *why* they believe AR is superior [U].
- **Qualitative acknowledgment in econophysics**: Zheng et al. (2012) citing Billio et al. (2010) [V].
- **The mathematical machinery**: the RMT market-mode literature [M], from which the identity follows as a
  special case, applied by nobody as a critique of AR.
- **Pukthuanthong & Roll (2009)** argue the *opposite direction* — that raw correlation is the misleading
  measure because it conflates factor loading, factor volatility and idiosyncratic variance, and a
  multi-factor R² is better [V]. Worth taking seriously: it is the strongest published argument that
  correlation and eigenvalue-share measures are **not** equivalent outside restrictive special cases.

**Verdict for this repo: the identity is a correct, elementary admission gate and a legitimate reason to
have dropped the absorption signal. It is NOT a publishable critique and must not be written up as one.**
Recording it as a ledger null — *"absorption ratio closed as algebraically redundant with average
correlation; identity elementary, not novel"* — is the honest treatment.

---

## 5. Q4 — Which parts of this approach are actually new?

Brutally: **very little, and none of the measurement.** Four candidates, ranked by how much survives
scrutiny.

### 5.1 Genuinely thin in the literature, and worth doing

**(a) The matched-transform control.** The Phase-5 draft charter's **V5** bar — apply the *identical*
standardized-shift transform to volatility and require the structure measure to beat it, with a paired
bootstrap null — is, as far as six search streams could establish, **not run anywhere in the published
absorption/connectedness/systemic-risk literature** [U]. Kritzman et al. do not run it; Billio et al. do
not; Diebold–Yilmaz do not. Herskovic et al.'s double sort on market-variance beta is the closest
published analogue [V], and it is in the *pricing* literature, not the *early-warning* literature. This is
a real, narrow contribution: **it is the difference between "AR leads turbulence" and "any smooth
transform of volatility leads turbulence."**

**(b) A systematic spanning audit with a pre-registered kill threshold.** Nobody has computed a battery of
structure measures on one panel and reported, for each, the R² of a regression on {ρ̄, log σ}. The pieces
exist (Benoit et al. for systemic-risk measures; Nucera et al. for cross-measure PCA; Zheng et al.'s
qualitative remark) but the audit as a designed exercise does not [U]. §8.

**(c) Century-length, causal, expanding-percentile structure series with an out-of-hypothesis-sample
confirmation.** Kritzman et al. use ~1987–2010; Billio et al. use hedge-fund/financial-sector monthly
returns; the DY papers use post-1990 windows. A 1926–2026 US series on 48 industry sorts, with a
1990–2026 matched Japan/Europe confirmation, is **longer than anything published in this family** and the
generalization test is one almost nobody runs. Note the honest discount: this is *more data applied to a
known object*, which is a robustness contribution, not a discovery.

**(d) An out-of-sample test of Krishnan–Petkova–Ritchken's return-based correlation factor.** The agent
found **no replication, extension or out-of-sample test of KPR's factor of either sign** [U]. And — this is
the important part — **KPR's entire construction requires nothing beyond free data** (§9.1). A 1926–2026 US
re-estimation plus a 1990–2026 Japan/Europe out-of-hypothesis-sample test would be, as far as this review
can establish, the first out-of-sample evidence on that factor.

### 5.2 New only relative to this repo, not to the field

- Point-in-time, expanding-percentile rarity framing of a structure measure. Standard practice dressed in
  house discipline.
- The `assert_causal` perturb-the-future guard. Excellent practice; not a research contribution.
  **N5 (Guo–Kassa–Ferguson) is the warning that it is not sufficient**: the look-ahead in Fu (2009) lived
  in the *parameter estimation*, not the data alignment, and would survive a shift-audit. Any GARCH/EGARCH
  or PCA fitting step needs a *refit-through-t−1* discipline on top of the guard.

### 5.3 Not new, and should not be claimed

- The absorption ratio, and the observation that it is near-redundant with ρ̄ (§4.4).
- Any statement that dependency rises in stress (02 §1.1 already settles this).
- The observation that connectedness measures are descriptive. The primary papers never claimed otherwise;
  the overclaim is downstream.

### 5.4 A governance consequence, flagged explicitly

The dropped Phase-5 charter registered its mechanism as **risk-management** and stated: *"there is no
risk-premium claim here and none is made."* An economic-relevance test in the Fama–MacBeth sense is a
**risk-premium claim**, and therefore a *different registered mechanism* — a new charter, not an extension
of the old one.

There is also a boundary subtlety worth naming: a priced-factor result invites the question this repo must
never answer. The safe and honest framing, and the one used throughout this document, is:

> A pricing test is evidence about **measurement validity** — whether the measured object corresponds to a
> state variable that market participants demonstrably price — and about the **mechanism gate**, because a
> genuine risk premium survives being known while a mispricing does not. It is never a return claim, and
> the price of risk λ is reported as a property of the measure, not as anything to act on.

---

## 6. Q5 — Which parts are just different implementations of existing ideas?

| The construction | What it already is |
|---|---|
| Absorption ratio AR₁ | Average pairwise correlation, affinely (§4). Also: Billio et al.'s PC1 share; the RMT market mode; the DECO scalar; implied correlation; the index/constituent variance ratio |
| AR_K for K > 1 | A coarse read of the eigenvalue spectrum. Its non-redundant content over AR₁ is the **shape** of the spectrum, which the RMT literature characterizes far more precisely via Marchenko–Pastur deviations [M] |
| Standardized shift ΔAR | A z-scored moving-average crossover. Structurally identical to a momentum/trend filter on any series; carries no information about *what* series it is applied to — which is exactly why the matched-transform control (§5.1a) is mandatory |
| DY connectedness index | A nonlinear but **deterministic** transform of the estimated VAR coefficients and residual covariance — themselves functions of the sample second-moment structure. Not an independent data source [INF; the agent found no paper running this horse race, and it should be run before the claim is made] |
| Granger-network density | A thresholded read of the same second-moment structure, with a known spurious-edge problem under common shocks [V] |
| MES | A conditional-tail restatement of beta [V] |
| ΔCoVaR | A conditional-tail restatement of the firm's own VaR and its tail dependence with the system [V] |
| SRISK | A leverage-weighted MES; dominated by size and leverage, which is why its "predictions" name the largest, most levered institutions [V/INF] |
| CSV (Garcia et al.) | Cross-sectional variance — the same object as Goyal–Santa-Clara's average variance, model-free rather than residual-based. Inherits the equal-weighting hazard that killed GSC (N2) unless explicitly weighted otherwise [INF] |
| CSSD / CSAD herding | Cross-sectional dispersion, mechanically driven by market volatility and by the cross-sectional distribution of betas. Christie & Huang's own result — dispersion **rises** in extreme moves — is the tell [V]. **A clean citation for the specific "beta-dispersion artifact" framing could not be located** [U]; Bohl, Branger & Trede (*JBF*) exists but its title suggests the opposite direction of critique, and the agent could not read it |
| Implied correlation | Index implied vol and constituent implied vol, rearranged (N7) [V] |
| CIV | The equal-weighted average of firm residual variances. A 2021 *International Review of Financial Analysis* 76 study reports the de-noised average idiosyncratic **covariance** correlates **0.63 (China) / 0.81 (US)** with CIV [V] — high but not one, so CIV and average idiosyncratic correlation are empirically distinguishable, not a strict transform. **Nobody has decomposed CIV's time variation into its variance-share versus correlation-share** [U] — a small, clean open question |

---

## 7. Q6 — What genuine research gap remains?

**Gap 1 (strongest) — the spanning question, asked systematically and pre-registered.**
The literature has produced ~20 named cross-sectional structure measures and evaluated them one at a time,
each against its own crisis narrative. Benoit et al. did the audit *for systemic-risk measures only* and
found one factor explains most of the variation [V]. **Nobody has done it for the correlation/eigenvalue/
connectedness/dispersion family.** The question is not "does AR work" but:

> Given {ρ̄, AR₁, AR_K, H (§4.2), DY connectedness, CSV, cross-sectional dispersion, Granger density}
> computed on one panel over one window, what fraction of each is spanned by {ρ̄, log σ_mkt}, and does any
> residual carry incremental information about anything?

This is a documented-null generator: every possible outcome is publishable-to-the-ledger. High R² closes
axes cheaply. Low R² identifies the one measure worth a charter.

**Gap 2 — the matched-transform control, everywhere.** The early-warning literature compares a structure
measure to *nothing*, or to a crisis chronology. It essentially never compares it to **the same transform
applied to volatility**. Until that control is run, every "X leads turbulence" result in this family is
uninterpretable. (Herskovic et al.'s double sort on market-variance beta shows the pricing literature knows
how to do this; the early-warning literature does not do it.)

**Gap 3 — out-of-sample evidence on the return-based correlation factor.** KPR (2009, *JEF* 16(3)) reports
λ = −0.7726/month (t = −2.93), robust across five specifications, on 1963–2003 US data, and **no one has
re-estimated it since** [U]. It is free-data-replicable (§9.1). Under the modern threshold (Harvey–Liu–Zhu
|t| > 3.0 [M]), the original result **does not clear the bar** — a fact worth stating plainly.

**Gap 4 — the credit-versus-market-structure horse race.** No paper runs the credit-to-GDP gap against
CoVaR/MES/SRISK/connectedness in a single out-of-sample early-warning evaluation [V, flagged by the
agent]. The prior from two separate literatures is that credit wins decisively. Partially feasible on free
data (§9.2).

**Gap 5 — decomposing CIV into variance-share and correlation-share.** Small, clean, and unclaimed [U].
**Not feasible on free data** (§9.3) — record it and stop.

### What is NOT a gap, and must not be claimed as one

- The equicorrelation identity (§4.4).
- "Dependency rises in stress."
- "Systemic-risk measures are correlated with volatility" — Benoit et al. established it more generally
  and more rigorously.
- A new named structure measure. The field has too many already, and the marginal one has a prior
  probability of survival that the replication literature puts near zero (§10).

---

## 8. Q7 — The smallest experiment that could test the gap

**The spanning audit. One script, one panel, one look, no new data, no new fetch.**

**In one sentence.** On the US 48-industry daily panel already on disk (1926-07-01 → 2026-05-29), compute
every structure measure the repo might ever want on a common trailing window, regress each on
{ρ̄, log σ_mkt}, and report the R² — with a pre-registered threshold above which the axis is closed.

**Construction (all trailing, all causal, one refit rule).**
1. Common window W = 500 trading days, daily refit, complete-cases only from 1969-07-01 (the panel's
   structural-missingness boundary already recorded in the Phase-5 charter).
2. Compute per date t: ρ̄_t (mean off-diagonal of the trailing correlation matrix); AR₁_t and AR₅_t;
   H_t = AR₁_t − [ρ̄_t + (1−ρ̄_t)/N]; σ_mkt,t (EWMA, λ = 0.94); CSV_t (cross-sectional variance of the 48
   series' returns); cross-sectional dispersion of the trailing betas.
3. **Spanning regressions**, on levels and on first differences separately (they answer different
   questions — levels are dominated by a common trend, differences by shared innovations):
   M_t = a + b·ρ̄_t + c·log σ_mkt,t + e_t. Report R², and the partial R² of each regressor.
4. **Pre-registered kill:** R² > 0.95 on the levels regression ⇒ the measure is closed as a
   reparameterization, recorded as a ledger null, no further work. **This threshold must be fixed before
   the script runs.**
5. For any measure surviving step 4, one incremental test only: does e_t add anything to a forecast of
   next-month realized market volatility beyond {ρ̄, log σ}, evaluated by **out-of-sample R² against the
   prevailing-mean benchmark with Clark–West MSPE-adjusted inference** [M]? Not in-sample R². Not a
   t-statistic on an in-sample slope.

**Why this is the smallest such experiment.**
- No new data build. No new fetch. No cross-region panel prerequisite (that is only needed for a
  *generalization* claim, and this experiment makes none).
- No event definition, so no turbulence-onset dating, no refractory period, no power pre-check — the four
  places the Phase-5 charter had to register defaults it was uncomfortable with.
- No pricing test, so no test-asset choice, no Shanken correction, no factor-mimicking projection.
- Every outcome is informative. High R² closes axes and generates ledger nulls — which this repo values
  above positive results. Low R² for exactly one measure tells you which charter to write next.
- It answers the question that *precedes* every other question in this document. Running a pricing test or
  a lead test on a measure that turns out to be ρ̄ in disguise is wasted work.

**Registered scope limits, to write into any charter that adopts this.**
- 48 industry sorts are **already-diversified aggregates**, not firms. The spectrum is compressed relative
  to a firm-level cross-section, which biases AR₁ *upward* and biases the spanning R² *upward* too. A high
  R² on this panel is therefore **weaker evidence of redundancy than it looks** — state this before the
  look, not after.
- N = 48 makes the AR₁/ρ̄ gap at most ~0.021 by §4.1. On a panel this small the affine identity is close to
  exact by construction. The experiment measures how far the *empirical* matrix departs from
  equicorrelation, which is the honest question, but it cannot be advertised as a general-N result.
- Rolling-window overlap: consecutive 500-day windows share 99.8% of their data. Every reported R² is on
  a series whose effective sample size is a small fraction of its length. Do not attach a t-statistic to
  the spanning regression without a block bootstrap. (02 §5 covers this at length.)

---

## 9. Which economic-relevance tests are POSSIBLE on free data

Free sources assumed: **Ken French Data Library** (daily industry and characteristic sorts, US from
1926-07-01; Japan / Europe / Asia-Pacific-ex-Japan / North America from 1990-07-01) and **FRED**. Vendor
filenames below are source identifiers.

### 9.1 Fully possible — no missing data

| Test | How | Notes |
|---|---|---|
| **The negative-price-of-risk sign test on a return-based structure factor** | Build correlation innovations among a small set of sorted groups, extract PC1, orthogonalize against market-variance innovations and macro controls, estimate λ by two-pass Fama–MacBeth on a *disjoint* set of sorted groups | **This is exactly KPR's design and it uses nothing but free data.** They used 5 size×value groups to build correlations and the 25 size×value sorts as test assets. Use disjoint sets — e.g. build from `48_Industry_Portfolios_Daily_CSV.zip`, test on the 25 ME×BE-ME sorts — to avoid the circularity KPR's overlapping design has |
| **Out-of-hypothesis-sample confirmation of that λ** | Identical construction on Japan / Europe / Asia-Pac-ex-Japan, 1990-07 → present | Nobody has done this for KPR (§7 Gap 3). The repo's `run_oos.py` harness already exists |
| **The spanning audit of §8** | US 48-industry daily, 1926–2026 | Zero new data |
| **AR / ρ̄ / H / CSV / dispersion, causally, over a century** | Already-built panels | |
| **Diebold–Yilmaz connectedness on industry realized volatilities, and whether it is spanned by ρ̄** | GFEVD of a VAR on 10- or 48-industry daily realized volatility | Fully feasible; and the "is DY just the correlation matrix rearranged" horse race (§6) has, as far as this review found, never been run [U] |
| **A time-series predictability test with honest out-of-sample evaluation** | Structure measure → next-period market excess return or realized volatility; OOS R² vs prevailing mean, Clark–West | The market series is in the French library. **This is the test the dispersion literature mostly skipped, which is why N2 happened** |
| **Replicating the Goyal–Santa-Clara / Bali-Cakici-Yan-Zhang dispute** | Equal- vs value-weighted average variance across sorted groups, pre- and post-2001 | A cheap, high-value calibration exercise: it reproduces a *known null* and validates the pipeline against a documented failure. Strongly recommended before any new claim |
| **The variance risk premium** | FRED `VIXCLS` (daily from 1990-01-02) and `VXOCLS` (1986–2021, discontinued) minus realized variance of the French market series | Gives a 1990–2026 VRP without any option data. Bollerslev–Tauchen–Zhou's in-sample result (>15% of quarterly return variation, 1990–2005) is replicable; **its out-of-sample status is unresolved in the literature** [U, flagged by the agent] and is testable here |
| **Credit / macro state-variable controls** | FRED: `BAA`/`AAA` monthly from 1919, `BAA10Y` daily from 1986, `NFCI` weekly from 1971, `DGS10` from 1962, `USREC`, `INDPRO`, `UNRATE`, `CPIAUCSL`; the Gilchrist–Zakrajšek excess bond premium is published free by the Fed and the repo already builds it | Sufficient for the macro control sets used in KPR and in most Fama–MacBeth specifications |

### 9.2 Possible but materially compromised — declare the compromise before the look

- **An IVOL-style cross-sectional test.** Ken French publishes sorts on **variance** and on **residual
  variance** (10 groups, and 25 ME × variance / ME × residual-variance sorts), daily from 1963-07 [M —
  verify the exact files before relying on this]. That permits a *coarse* AHXZ-style test. **But** the
  residual variance is computed by the vendor, at the vendor's frequency, with the vendor's factor model
  and the vendor's rebalancing — you cannot vary the estimation choices that Bali & Cakici (2008) showed
  the entire result depends on. **A pass on this data is not evidence the IVOL effect is robust; a failure
  is not evidence it is absent.** Declare this before the look.
- **An Ahern-style industry-centrality test.** BEA input-output tables are free, so industry-level
  eigenvector centrality is buildable and can be matched to French industry sorts. **But** this is a third
  source outside {French, FRED}, the industry concordance is a research project in itself, and the target
  paper was apparently never refereed (§3.2). Low priority.
- **A credit-versus-structure early-warning horse race (§7 Gap 4), partially.** FRED gives credit
  aggregates and the BIS gives credit-to-GDP gaps free; the market-structure side is fully available. What
  is missing is the *institution-level* systemic-risk measures (CoVaR/MES/SRISK), so the race would be
  "credit growth vs market-structure measures", not "credit growth vs CoVaR". Worth saying out loud that
  this is a *different* race from the one the literature is missing.

### 9.3 NOT possible — record as gaps, do not silently attempt

| Test | What is missing | Consequence |
|---|---|---|
| **Replicating CIV (Herskovic et al. 2016)** | Individual stock returns (CRSP). CIV is the average of *firm-level* residual variances | **The residual of a 48-industry or 25-sorted-group series is not firm-idiosyncratic volatility.** Computing a "CIV" from French sorted groups produces a different object with the same name. Do not do it. This is the single most likely silent error available here |
| **Any individual-stock cross-sectional pricing test** | CRSP/Compustat | No Fama–MacBeth on firms; no firm-level loading sorts; no replication of the Hou–Loh decomposition or the Stambaugh–Yu–Yuan arbitrage-asymmetry split |
| **Correlation risk premium (DMV 2009)** | Option prices on the index *and* its constituents (OptionMetrics) | The entire options-based correlation literature is closed. Implied correlation, dispersion-construction returns, individual variance risk premia: all unavailable |
| **Risk-neutral skewness / higher-moment pricing (Chang et al. 2013)** | Option surfaces | Closed |
| **Granular-network / customer-supplier tests (Herskovic et al. 2020)** | Firm-level customer-supplier links (FactSet Revere, Compustat segment files) | Closed |
| **CoVaR / MES / SRISK replication or critique** | Bank-level equity panels plus balance-sheet leverage at usable frequency | Closed on {French, FRED}. Note that the *critiques* (N1, N3, N4) are the valuable part and they are already established — there is nothing here worth reproducing |
| **Crowding / holdings-based structure** | 13F holdings, short interest, fund flows | Closed |
| **Belief dispersion (Buraschi–Trojani–Vedolin channel)** | Analyst forecasts (I/B/E/S) | Closed |
| **Post-publication decay of a specific anomaly** | The anomaly's own firm-level construction | Closed |
| **Any test whose object is 51 US industry series** (Kritzman et al.'s own panel) | French publishes **no international industry sorts at any frequency** | Already recorded in the Phase-5 charter: the source paper's own object cannot be confirmed out of hypothesis sample. The matched cross-region object is the 25 sorts, which is weaker (all long-equity, one dominant factor by construction) |

**One structural caution that applies to everything in §9.1.** Ken French sorted groups are
*well-diversified aggregates*, and N11 (Gempesaw, Kassa & Zykaj 2022) reports that the IVOL puzzle
**disappears** on exactly such test assets [V]. So a null result on French test assets is genuinely
ambiguous: it may mean the effect is absent, or it may mean the test assets averaged it away. **Register
this before the look for any pricing test run here.** It does not weaken a *positive* result, and it does
not weaken the spanning audit of §8 at all — which is another reason the spanning audit is the right first
experiment.

---

## 10. Where the frontier actually is

If the goal is a contribution rather than a confirmation, the frontier in this literature is **not** a new
structure measure. It has moved in three directions, and two of them are closed to this repo on data
grounds.

**(a) Multiple-testing and replication — OPEN to this repo, and the most relevant.** Harvey, Liu & Zhu
(2016, *RFS* 29(1):5–68) argue the appropriate threshold for a *newly proposed* factor, after accounting
for the hundreds already tested, is **|t| > 3.0** [M]. Hou, Xue & Zhang (2020, *RFS* 33(5):2019–2133)
replicate 452 anomalies and find a large majority insignificant at |t| > 1.96 under value-weighting with
NYSE breakpoints, with the failure rate rising sharply at |t| > 2.78 [M — the exact percentages should be
checked before citation]. Chen & Zimmermann's *Open Source Cross-Sectional Asset Pricing* is the
countervailing evidence: across 161 characteristics clearly significant in their original papers, **98%
reproduce at |t| > 1.96**, with a reproduced-on-original t-slope of **0.88** and R² **82%** [V] — i.e. the
*published* results mostly reproduce; the dispute is about how many were ever worth publishing.
**Consequence: KPR's t = −2.93 and Herskovic et al.'s CIV t-statistics do not clear the Harvey–Liu–Zhu
bar.** This is not a marginal caveat; it is the modern standard, and it is available for free.

**(b) Conditional factor models that absorb ad-hoc structure factors — CLOSED (needs firm data).**
Kelly, Pruitt & Su (2019, *JFE* 134(3):501–524) IPCA and Gu, Kelly & Xiu (2020, *RFS* 33(5):2223–2273)
[M] estimate latent factors with characteristic-driven loadings. The relevant implication: a proposed
structure factor now has to show incremental pricing content **over a conditional latent-factor model**,
not over FF3. Detzel et al. (2023) already show the Stambaugh–Yuan 4-factor and Barillas–Shanken 6-factor
models **resolve the IVOL anomaly out of sample** where older models do not [V]. Ad-hoc structure factors
are being absorbed.

**(c) Micro-data networks — CLOSED (needs proprietary link data).** The live work is firm-level
customer-supplier, input-output, and bank-interlinkage networks (Herskovic et al. 2020; Gofman, Segal & Wu
2020; the Acemoglu et al. 2012 *Econometrica* / 2015 *AER* theoretical line) [V]. Return-only network
estimation, which is what {French, FRED} permits, is the *older* and weaker branch, and the field's own
methodological migration — Granger networks → generalized FEVD → dynamic factor models — is a record of it
not working well.

**Honest conclusion.** For a repo constrained to {French, FRED}, the frontier is **(a)**: apply modern
multiple-testing and out-of-sample discipline to structure measures that were never subjected to it, and
publish the nulls. That is a real contribution, it is exactly what this repo's ledger is designed to hold,
and it is where the §8 experiment lands.

---

## 11. Candidate ledger rows arising from this review

Offered as drafts for a human to rule on; nothing is entered by this document.

| Proposed row | Type | Basis |
|---|---|---|
| Absorption ratio closed as algebraically redundant with average correlation on an equity cross-section (AR₁ = ρ̄ + (1−ρ̄)/N under equicorrelation; AR₁ ≥ that bound in general). Identity elementary; **not** a novel critique | **NULL, in-repo, already effected** | §4; `05-ABSORPTION-DROPPED.md` G3 |
| No published out-of-sample or international replication of the CIV-beta pricing test exists (Herskovic et al. 2016) | **Gap, external** | §3.2 [U] |
| No published out-of-sample test of the return-based correlation factor exists (KPR 2009) — and it is free-data-replicable | **Gap, external, actionable** | §7 Gap 3, §9.1 [U] |
| Diebold–Yilmaz connectedness has no published out-of-sample forecasting or pricing evidence; it is a coincident descriptor | **NULL, external** | §3.4 [V] |
| Systemic-risk measures are transformations of standard risk measures; one factor explains most of their variation | **NULL, external** | N1 [V] |
| Systemic-risk measures can respond perversely to a genuine increase in risk | **NULL, external** | N3 [V] |
| MES is beaten out of sample by the Tier-1 ratio | **NULL, external** | N4 [V] |
| Average stock variance does not forecast market returns (GSC refuted) | **NULL, external, replicable here** | N2 [V], §9.1 |
| The index variance risk premium and the correlation risk premium are plausibly one object; the DMV pricing result loses significance under transaction costs (t: 1.96 → 0.77) | **NULL, external** | N6 [V] |
| Ahern (2013), the most-cited source for equity centrality pricing, appears never to have been refereed | **Provenance caution** | §3.2 [V/U] |
| KPR (t = 2.93) and CIV do not clear the Harvey–Liu–Zhu |t| > 3.0 bar | **Standard-of-evidence note** | §10 [M] |
| A firm-level CIV cannot be constructed from vendor sorted groups; attempting it produces a different object with the same name | **Data gap, hazard flagged** | §9.3 |

---

## 12. Bibliography

Entries carry the same verification marks. **[U] entries are named so they can be traced, not so they can
be cited.**

**Common idiosyncratic volatility and granular networks**
- Herskovic, B., Kelly, B., Lustig, H. & Van Nieuwerburgh, S. (2016). "The common factor in idiosyncratic
  volatility: Quantitative asset pricing implications." *Journal of Financial Economics* 119(2):249–283;
  NBER WP 20076. [V]
- Herskovic, B., Kelly, B., Lustig, H. & Van Nieuwerburgh, S. (2020). "Firm volatility in granular
  networks." *Journal of Political Economy* 128(11):4097–4162; NBER WP 19466 (3-author 2013 draft). [V]
- Duarte, J., Kamara, A., Siegel, S. & Sun, C. "The systematic risk of idiosyncratic volatility."
  SSRN 1905731. [V, working paper; U on journal placement]
- Connor, G., Korajczyk, R. & Linton, O. (2006). "The common and specific components of dynamic
  volatility." *Journal of Econometrics* 132(1):231–255. [V]
- Bekaert, G., Hodrick, R. & Zhang, X. (2012). "Aggregate idiosyncratic volatility." *JFQA*
  47(6):1155–1185. [V]
- Bekaert, G., Wang, X. & Zhang, X. "The international commonality of idiosyncratic variances."
  *Management Science*; CEPR DP 18230. [V]
- Campbell, J., Lettau, M., Malkiel, B. & Xu, Y. (2001). "Have individual stocks become more volatile?"
  *Journal of Finance* 56(1):1–43. [M]
- Brandt, M., Brav, A., Graham, J. & Kumar, A. (2010). "The idiosyncratic volatility puzzle: Time trend or
  speculative episodes?" *RFS* 23(2):863–899. [V]
- Yin, Shu & Su (2019). *International Journal of Finance & Economics* 24(1):370–390. [V]
- "Expected stock returns, common idiosyncratic volatility and average idiosyncratic correlation" (2021).
  *International Review of Financial Analysis* 76. [V]
- Kalniņa, I. & Tewou, K. "Cross-sectional dependence in idiosyncratic volatility." Working paper. [U]

**Idiosyncratic and aggregate volatility pricing**
- Ang, A., Hodrick, R., Xing, Y. & Zhang, X. (2006). "The cross-section of volatility and expected
  returns." *Journal of Finance* 61(1):259–299. [V for sign; U for exact table figures]
- Ang, A., Hodrick, R., Xing, Y. & Zhang, X. (2009). "High idiosyncratic volatility and low returns:
  International and further U.S. evidence." *JFE* 91(1):1–23. [V]
- Bali, T. & Cakici, N. (2008). "Idiosyncratic volatility and the cross section of expected returns."
  *JFQA* 43(1):29–58. [V]
- Han, Y. & Lesmond, D. (2011). "Liquidity biases and the pricing of cross-sectional idiosyncratic
  volatility." *RFS* 24(5):1590–1629. [V]
- Fu, F. (2009). "Idiosyncratic risk and the cross-section of expected stock returns." *JFE* 91(1):24–37.
  [V]
- Guo, H., Kassa, H. & Ferguson, M. (2014). "On the relation between EGARCH idiosyncratic volatility and
  expected stock returns." *JFQA*. [V]
- Huang, W., Liu, Q., Rhee, S.G. & Zhang, L. (2010). "Return reversals, idiosyncratic risk, and expected
  returns." *RFS* 23(1):147–168. [V]
- Stambaugh, R., Yu, J. & Yuan, Y. (2015). "Arbitrage asymmetry and the idiosyncratic volatility puzzle."
  *Journal of Finance* 70(5):1903–1948. [V]
- Hou, K. & Loh, R. (2016). "Have we solved the idiosyncratic volatility puzzle?" *JFE* 121(1):167–194.
  [V]
- Detzel, A., Duarte, J., Kamara, A., Siegel, S. & Sun, C. (2023). "The cross-section of volatility and
  expected returns: Then and now." *Critical Finance Review* 12(1-4):9–56. [V]
- Gempesaw, D., Kassa, H. & Zykaj, B. (2022). *European Financial Management* 28(3):693–721. [V]
- Cremers, M., Halling, M. & Weinbaum, D. (2015). "Aggregate jump and volatility risk in the cross-section
  of stock returns." *Journal of Finance* 70(2):577–614. [V]
- Chang, B.Y., Christoffersen, P. & Jacobs, K. (2013). "Market skewness risk and the cross section of
  stock returns." *JFE* 107(1):46–68. [V]
- Barinov, A. FVIX programme (multiple papers). [V] — and a Berkeley CDAR working paper (Anderson, 2012)
  and a companion "In search of a statistically valid volatility risk factor" that appear to challenge
  FVIX's statistical validity directly, **neither of which could be retrieved** [U].
- Carr, P. & Wu, L. (2009). "Variance risk premiums." *RFS* 22(3):1311–1341. [V]
- Bollerslev, T., Tauchen, G. & Zhou, H. (2009). "Expected stock returns and variance risk premia." *RFS*
  22(11):4463–4492. [V]
- Bekaert, G. & Hoerova, M. (2014). "The VIX, the variance premium and stock market volatility."
  *Journal of Econometrics* 183(2):181–192. [V]

**Correlation risk**
- Driessen, J., Maenhout, P. & Vilkov, G. (2009). "The price of correlation risk: Evidence from equity
  options." *Journal of Finance* 64(3):1377–1406. [V]
- Krishnan, C.N.V., Petkova, R. & Ritchken, P. (2009). "Correlation risk." ***Journal of Empirical
  Finance*** 16(3):353–367. **Note the corrected venue.** [V]
- Buraschi, A., Kosowski, R. & Trojani, F. (2014). "When there is no place to hide: Correlation risk and
  the cross-section of hedge fund returns." *RFS* 27(2):581–616. [V]
- Buraschi, A., Trojani, F. & Vedolin, A. (2014). "When uncertainty blows in the orchard: Comovement and
  equilibrium volatility risk premia." *Journal of Finance* 69(1):101–137. [V]
- Mueller, P., Stathopoulos, A. & Vedolin, A. (2017). "International correlation risk." *JFE*
  126(2):270–299. [V]
- Faria, G., Kosowski, R. & Wang, T. (2022). "The correlation risk premium: International evidence."
  *Journal of Banking & Finance* 136. [V, abstract only; U on magnitudes]
- Cosemans, M. "Long and short run correlation risk in stock returns." SSRN 1569563 / 1787576. [V,
  unpublished]
- Engle, R. & Kelly, B. (2012). "Dynamic equicorrelation." *Journal of Business & Economic Statistics*
  30(2):212–228. [V]
- Pollet, J. & Wilson, M. (2010). "Average correlation and stock market returns." *JFE* 96(3):364–380.
  [V; U on the exact in-sample coefficient and on any out-of-sample test]
- Oh, J.-M. (2024). "Predicting stock market returns with average correlation and average variance:
  Decomposition approach." *Finance Research Letters*, DOI 10.1016/j.frl.2024.105343. [U]

**Networks, centrality, connectedness**
- Diebold, F.X. & Yilmaz, K. (2009). *Economic Journal* 119:158–171; (2012) *IJF* 28(1):57–66; (2014)
  *Journal of Econometrics* 182:119–134; (2015) *Financial and Macroeconomic Connectedness*, OUP. [V]
- Billio, M., Getmansky, M., Lo, A. & Pelizzon, L. (2012). "Econometric measures of connectedness and
  systemic risk in the finance and insurance sectors." *JFE* 104(3):535–559. [V]
- Ahern, K. (2013). "Network centrality and the cross section of stock returns." SSRN 2197370. **Working
  paper; apparently never refereed.** [V/U]
- Herskovic, B. (2018). "Networks in production: Asset pricing implications." *Journal of Finance*
  73(4):1785–1818. [V]
- Richmond, R. (2019). "Trade network centrality and currency risk premia." *Journal of Finance*
  74(3):1315–1361. [V]
- Gofman, M., Segal, G. & Wu, Y. (2020). "Production networks and stock returns: The role of vertical
  creative destruction." *RFS* 33(12):5856–5905. [V]
- Branger, N., Konermann, P., Meinerding, C. & Schlag, C. (2021). "Equilibrium asset pricing in directed
  networks." *Review of Finance* 25(3):777–818. [V]
- Buraschi, A. & Porchia, P. "Dynamic networks and asset pricing." SSRN 2024483. [V; U on venue]
- Acemoglu, D., Carvalho, V., Ozdaglar, A. & Tahbaz-Salehi, A. (2012). "The network origins of aggregate
  fluctuations." *Econometrica* 80(5):1977–2016. [V]
- Acemoglu, D., Ozdaglar, A. & Tahbaz-Salehi, A. (2015). "Systemic risk and stability in financial
  networks." *AER* 105(2):564–608. [V]
- Cohen, L. & Frazzini, A. (2008). "Economic links and predictable returns." *Journal of Finance*
  63(4):1977–2011. [V] — framed by the authors as **information diffusion**, not a risk premium.
- Menzly, L. & Ozbas, O. (2010). "Market segmentation and cross-predictability of returns." *Journal of
  Finance* 65(4):1555–1580. [V] — the effect **declines with analyst coverage and institutional
  ownership**, the authors' own evidence against a risk interpretation.

**Systemic-risk measurement and its critiques**
- Adrian, T. & Brunnermeier, M. (2016). "CoVaR." *American Economic Review* 106(7):1705–1741; FRBNY Staff
  Report 348; NBER WP 17454. [V; U on the exact "one-third vs one-half" crisis-prediction figure]
- Acharya, V., Pedersen, L., Philippon, T. & Richardson, M. (2017). "Measuring systemic risk." *RFS*
  30(1):2–47. [V]
- Brownlees, C. & Engle, R. (2017). "SRISK: A conditional capital shortfall measure of systemic risk."
  *RFS* 30(1):48–79. [V]
- Benoit, S., Colletaz, G., Hurlin, C. & Pérignon, C. "A theoretical and empirical comparison of systemic
  risk measures." HAL halshs-00746272 / SSRN 1973950. [V abstract; U on the propositions and numbers]
- Benoit, S., Colliard, J.-E., Hurlin, C. & Pérignon, C. (2017). "Where the risks lie: A survey on systemic
  risk." *Review of Finance* 21(1):109–152. [V]
- Danielsson, J., James, K., Valenzuela, M. & Zer, I. (2016). "Can we prove a bank guilty of creating
  systemic risk? A minority report." *JMCB* 48(4):795–812. [V]
- Danielsson, J., James, K., Valenzuela, M. & Zer, I. (2016). "Model risk of risk models." *Journal of
  Financial Stability* 23:79–91. [V]
- Löffler, G. & Raupach, P. (2018). "Pitfalls in the use of systemic risk measures." *JFQA*
  53(1):269–298. [V]
- Idier, J., Lamé, G. & Mésonnier, J.-S. (2014). "How useful is the marginal expected shortfall for the
  measurement of systemic exposure? A practical assessment." *JBF* 47:134–146. [V]
- Guntay, L. & Kupiec, P. "Taking the risk out of systemic risk measurement." FDIC/AEI working paper. [V
  on framing; U on empirical results]
- Nucera, F., Schwaab, B., Koopman, S.J. & Lucas, A. (2016). "The information in systemic risk rankings."
  ***Journal of Empirical Finance*** 38(A):461–475. **Note the corrected venue.** [V]
- Zhang, Q., Vallascas, F., Keasey, K. & Cai, C. (2015). *JMCB* 47(7):1403–1442. [V]
- Leeuwenkamp, "Making heads or tails of systemic risk measures." arXiv:2206.02582. [V, preprint]
- Giglio, S., Kelly, B. & Pruitt, S. (2016). "Systemic risk and the macroeconomy: An empirical
  evaluation." *JFE* 119(3):457–471. [M]
- Adrian, T., Boyarchenko, N. & Giannone, D. (2019). "Vulnerable growth." *AER* 109(4):1263–1289. [M]
- Brownlees, C. & Souza, A. (2021). "Backtesting global growth-at-risk." *Journal of Monetary Economics*
  118:312–330. [M — **verify; this is a high-value null**]
- Schularick, M. & Taylor, A. (2012). "Credit booms gone bust: Monetary policy, leverage cycles, and
  financial crises, 1870–2008." *AER* 102(2):1029–1061. [V]
- Borio, C. & Drehmann, M. — BIS credit-to-GDP gap and debt-service-ratio early-warning programme. [V]

**Dispersion, absorption, spectra**
- Goyal, A. & Santa-Clara, P. (2003). "Idiosyncratic risk matters!" *Journal of Finance* 58(3):975–1007.
  [V]
- Bali, T., Cakici, N., Yan, X. & Zhang, Z. (2005). "Does idiosyncratic risk really matter?" *Journal of
  Finance* 60(2):905–929. [V]
- Wei, S.X. & Zhang, C. (2005). "Idiosyncratic risk does not matter." *JBF* 29(3):603–621. [V]
- Garcia, R., Mantilla-Garcia, D. & Martellini, L. (2014). "A model-free measure of aggregate idiosyncratic
  volatility and the prediction of market returns." *JFQA* 49(5-6):1133–1165. [V; U on sample and
  out-of-sample R²]
- Stivers, C. (2003). "Firm-level return dispersion and the future volatility of aggregate stock market
  returns." ***Journal of Financial Markets***. **Note the corrected venue** (not *Journal of Empirical
  Finance*). US 1927–1995. [V]
- Connolly, R. & Stivers, C. (2003). *Journal of Finance* 58(4):1521–1556. [V]
- Stivers, C. & Sun, L. (2010). *JFQA* 45(4):987–1014. [V]
- Angelidis, T., Sakkas, A. & Tessaromatis, N. (2015). "Stock market dispersion, the business cycle and
  expected factor returns." *JBF* 59:265–279. **The one dispersion result reported as surviving
  out-of-sample, and it is G7-wide rather than US-only.** [V]
- Jiang, X. (2010). "Return dispersion and expected returns." *Financial Markets and Portfolio Management*
  24(2):107–135. [V]
- Christie, W. & Huang, R. (1995). "Following the pied piper: Do individual returns herd around the
  market?" *Financial Analysts Journal* 51(4):31–37. [V]
- Chang, E., Cheng, J. & Khorana, A. (2000). *JBF* 24(10):1651–1679. [V]
- Bohl, M., Branger, N. & Trede, M. "The case for herding is stronger than you think." *JBF*. [U —
  paywalled; the title suggests a **different** direction of critique than the beta-dispersion-artifact
  argument, so do not cite it for that argument]
- Kritzman, M., Li, Y., Page, S. & Rigobon, R. (2011). "Principal components as a measure of systemic
  risk." *Journal of Portfolio Management* 37(4):112–126. [V, largely via secondary sources; U on the
  primary tables]
- Laloux, L., Cizeau, P., Bouchaud, J.-P. & Potters, M. (1999). *Physical Review Letters* 83(7):1467. [M]
- Plerou, V., Gopikrishnan, P., Rosenow, B., Amaral, L.A.N. & Stanley, H.E. (1999). *PRL* 83:1471;
  Plerou et al. (2002). *Physical Review E* 65:066126. [M]
- Reigneron, P.-A., Allez, R. & Bouchaud, J.-P. (2011). "Principal regression analysis and the index
  leverage effect." *Physica A* 390(17):3026–3035. [V]
- Zheng, Z., Podobnik, B., Feng, L. & Li, B. (2012). "Changes in cross-correlations as an indicator for
  systemic risk." *Scientific Reports* 2:888. [V]
- Pukthuanthong, K. & Roll, R. (2009). "Global market integration: An alternative measure and its
  application." *JFE* 94(2):214–232. [V]

**Standards of evidence**
- Harvey, C., Liu, Y. & Zhu, H. (2016). "…and the cross-section of expected returns." *RFS* 29(1):5–68.
  [M]
- Hou, K., Xue, C. & Zhang, L. (2020). "Replicating anomalies." *RFS* 33(5):2019–2133. [M]
- Chen, A. & Zimmermann, T. "Open source cross-sectional asset pricing." *Critical Finance Review*. [V]
- McLean, R.D. & Pontiff, J. (2016). "Does academic research destroy stock return predictability?"
  *Journal of Finance* 71(1):5–32. [V]
- Welch, I. & Goyal, A. (2008). *RFS* 21(4):1455–1508. [M]
- Clark, T. & West, K. (2007). *Journal of Econometrics* 138(1):291–311. [M]
- Campbell, J. & Thompson, S. (2008). *RFS* 21(4):1509–1531. [M]
- Kelly, B., Pruitt, S. & Su, Y. (2019). "Characteristics are covariances: A unified model of risk and
  return." *JFE* 134(3):501–524. [M]
- Gu, S., Kelly, B. & Xiu, D. (2020). "Empirical asset pricing via machine learning." *RFS*
  33(5):2223–2273. [M]
- Shanken, J. (1992). "On the estimation of beta-pricing models." *RFS* 5(1):1–33. [M]

---

*End of draft v0.1. Sections 3.3 (the nulls), 4 (the algebra), 8 (the experiment) and 9.3 (what free data
cannot do) are the load-bearing content; everything else is context. Nothing in this document constitutes a
result, a look, or a claim — no data was touched and no experiment was run.*
