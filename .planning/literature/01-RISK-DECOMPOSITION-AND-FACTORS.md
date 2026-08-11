# Literature Review 01 — Market/Industry/Firm Risk Decomposition and Latent Factor Structure

**Domain:** variance decomposition across levels of aggregation · approximate factor structure · the number
of distinguishable factors · random-matrix limits on correlation matrices · equicorrelation and departures
from it · common components in volatility panels.

**Written** 2026-08-11 · **status** REVIEW ONLY — no look spent, no statistic computed, no code written.
**Supports** `.planning/phases/11-cross-section-structure/11-STAGE0-GATE.md` (v0.1-draft, UNSIGNED).

**Boundary note.** This repo measures and stops. Nothing below is an allocation, exposure, position,
weight, trade, tilt or recommendation, and where a cited paper has such an application this review reports
**only its statistic, its estimator and its measured numbers** and drops the application. Journal names,
dataset filenames and paper titles are reproduced verbatim where a precise citation requires it; these are
**source identifiers under the documented vendor-identifier exception in `CLAUDE.md`**, never concepts.
"Value-weighted" and "equal-weighted" appear only as descriptions of how a vendor constructed a published
index series — data-construction descriptors, the same class the Stage-0 gate already uses.

**Verification convention.** `[V]` = verified from primary source text by a research agent in this
session. `[S]` = standard-literature fact taken from a secondary source or from model knowledge, not
re-verified against the primary text — **check before quoting a number**. `[D]` = derived here; the
algebra is in Appendix A and is checkable in five minutes. `[INF]` = inference, explicitly labelled.

---

## 0. Bottom line, before the detail

1. **Ψ is not a new statistic. It is an exact, monotone reparameterization of the coefficient of variation
   of the off-diagonal correlations.** `Ψ² = s²/(s²+ρ̄²)`, i.e. `Ψ = CV/√(1+CV²)`. `[D]` Everything Ψ knows,
   the pair (mean, sd) of the pairwise correlations already knows. Say this in the first paragraph of any
   write-up; it is the first thing a competent reader will derive, and the review loses nothing by
   conceding it up front.
2. **The numerator of Ψ² has been computed on every rebalancing date since 2004.** It is Ledoit & Wolf's
   `γ̂ = Σ_ij (f_ij − s_ij)²`, the misspecification term of the *constant-correlation shrinkage target*,
   and their constant-correlation target **is** `R_eq`. `[V]` The denominator is `p ×` John's (1971)
   locally-most-powerful-invariant sphericity statistic evaluated at a correlation matrix. `[V]`
   **Ψ² = (Ledoit–Wolf γ̂) / (p × John's U). Both halves are known; the ratio has not been formed.**
3. **No paper anywhere plots a normalized departure-from-equicorrelation time series for equity markets.**
   Exhaustive OpenAlex/Crossref phrase searches on "departure from equicorrelation", "deviation from
   equicorrelation", "dispersion of pairwise correlations" return nothing relevant. `[V]` Engle & Kelly
   (2012) define `R_eq` verbatim, acknowledge in one sentence that the restriction fails, and then
   **dismiss the failure by proving DECO is a consistent QMLE under exactly that misspecification** — so
   they never measure it. `[V]` That is the gap, and it is narrow.
4. **A pure ONE-FACTOR model with dispersed loadings gives Ψ ≈ 0.20–0.48 in population.** `[D]` Under
   `r_i = β_i f + e_i`, off-diagonal `ρ_ij = b_i b_j` with `b_i = corr(r_i,f)`, so `Ψ ≈ √2·c/√(1+2c²)`
   where `c` is the coefficient of variation of the `b_i`. **Ψ > 0 is evidence of loading heterogeneity,
   not of extra factors.** The Stage-0 gate's registered H₀ (exact equicorrelation) is therefore far too
   weak: it will be rejected by a one-factor world, and rejecting it is not a finding.
5. **Under that same one-factor model Ψ is counter-cyclical in factor variance.** As `σ²_f → ∞` every
   `b_i → 1`, so `R → J`, which *is* equicorrelated, so `Ψ → 0`. `[D]` **Ψ falling in 1987-10 / 2008-10 /
   2020-03 is the null confirmed, not a finding.** This is the Ψ-space image of the Forbes–Rigobon (2002)
   heteroskedasticity bias.
6. **Ψ also has a large, ρ̄-dependent sampling floor.** With `sd(r̂) ≈ (1−ρ²)/√T`, at T=125 the pure-noise
   Ψ is 0.395 at ρ̄=0.2, 0.185 at ρ̄=0.4, 0.095 at ρ̄=0.6. `[D]` **Ψ_null is strongly DECREASING in ρ̄**, so
   Ψ_t inherits a mechanical negative relation to ρ̄_t *before any real structure exists*. Registered bar
   **E2 (|Spearman(Ψ,ρ̄)| < 0.90) is under threat from the null side**, not only from redundancy.
7. **The registered decisive test E4 does not test what it says it tests.** With `R_eq` recentred on each
   window's own ρ̄_t, the static, time-invariant departure `d_p = C_p − C̄` survives the demeaning, so
   `corr(vec(R_t−R_eq), vec(R_{t+h}−R_eq)) → Var(d)/(Var(d)+Var(η))`, a strictly positive constant that is
   **flat in h**. Predicted values for the exact registered configurations: **≈0.75 (N=10,T=125), ≈0.86
   (N=10,T=250), ≈0.77 (N=48,T=125), ≈0.87 (N=48,T=250)**. `[INF, checkable]` E4 as written is a
   *reliability* coefficient, not a persistence coefficient, and it will "pass" at ~0.8 on a completely
   static non-equicorrelated matrix. **Industry correlation matrices have been known to be
   non-equicorrelated since King (1966).** Fixes are in §7.
8. **The volatility-side construct `c_t = mean_i log σ_it`, `D_it = log σ_it − c_t` is published.**
   Herskovic, Kelly, Lustig & Van Nieuwerburgh, *Journal of Political Economy* 128(11) (2020), Table 5,
   run exactly `log σ_i,t = a_i + b_i·μ_σ,t + e_i,t` with `μ_σ,t` the cross-sectional average log
   volatility, and describe it verbatim as "essentially the first principal component of firm
   volatilities … a natural yardstick for any one-factor model." `[V]` The February-2014 draft of their
   2016 JFE paper plots *exactly* `c_t` and `sd_i(D_it)` (its Figure 3, Panels B and C). `[V]` At the
   **sector** level, Barigozzi, Brownlees, Gallo & Veredas, *Journal of Econometrics* 182(2) (2014) fit
   `x_it = a_i·φ(z_t)·μ_it·ε_it` on **nine sector index series** — in logs, that is your two-way fixed
   effect exactly. `[V]` **This part of the approach is a reimplementation, not a discovery.**
9. **Expect a much stronger common factor at the sector level than the firm level.** Firm-level R² ≈ 35%
   (HKLVN); on grouped series, 49.7%; on the nine sector series, PC1 = 58–91% and average pairwise
   correlation of realized volatility 0.66–0.82. `[V]` Loadings are near 1 (0.73 / 0.92 / 0.96 median
   across three studies) `[V]`, so the unit-loading restriction in `D_it` costs little.
10. **The CLMX headline has been retired by its own authors.** Their 2023 update (*Critical Finance
    Review* 12(1–4), 203–223) reports market volatility **12% → 18%**, industry **9% → 14%** and firm
    **26% → 28%** across the two eras: "*A main difference between volatility patterns today and those of
    the late 1990s is not that idiosyncratic volatility is lower, but that industry and, in particular,
    market volatility are higher.*" `[V]` The market's share of total variance went ~10% (late 1990s) →
    40% (GFC) → ~30%, and current variance shares "look more like the period 1926–1962 than like the CLMX
    period 1962–1997." `[V]` **What this repo would be replicating is a *co-movement* result, not a trend
    result** — and that is closer to Phase 11's actual question than the original paper was.
11. **The frontier is not "is there structure beyond ρ̄" (there is; that is settled). It is: after netting
    out (i) the sampling floor, (ii) a one-factor model with the empirically observed loading dispersion,
    and (iii) the static time-invariant departure, does anything measurable remain, and does it move?**
    Nobody has run that decomposition on an industry panel with a calibrated null. That is the gap, it is
    largely methodological, and the Stage-0 gate already says so in its own §Replication-before-research
    table. This review's contribution is to say the gate's *null is wrong*, not that its framing is.

---

## 1. What has already been solved

### 1.1 The variance decomposition across levels of aggregation — SOLVED, 2001

**Campbell, J.Y., Lettau, M., Malkiel, B.G. & Xu, Y. (2001), "Have Individual Stocks Become More
Volatile? An Empirical Exploration of Idiosyncratic Risk," *Journal of Finance* 56(1), 1–43.**

Everything in this subsection marked `[V]` was decoded and read from the primary text (NBER WP 7590, whose
Table 3 numbers are **identical** to the published Table III — independently confirmed because the
authors' own archived data files reproduce them, §8).

**The method, precisely enough to reimplement.**

- **The trick is that no betas are estimated.** With `i` industry, `j` firm, `t` month, `s` day in month,
  `w_ijt` the firm's weight within its industry and `w_it` the industry's weight in the market:

```
R_is  = R_ms + ε_is            ε_is  ≡ R_is − R_ms                    (WP eq. 6)
R_ijs = R_ms + ε_is + η_ijs    η_ijs ≡ R_ijs − R_is                   (WP eq. 10)
```

  All returns are **excess** returns over the T-bill. `[V]` CLMX cite Campbell, Lo & MacKinlay (1997,
  Ch. 4, p. 156) for the name: the **market-adjusted-return model**. `[V]` Their stated reason for
  dropping betas, verbatim: "it requires knowledge of firm-specific betas which are difficult to estimate
  and may well be unstable over time." `[V]`
- **Why the cross terms vanish — the paper's answer.** Individual variances *do* contain covariance
  terms, `Var(R_it) = Var(R_mt) + Var(ε_it) + 2(β_im − 1)Var(R_mt)` (eq. 8), but the **weighted average
  across industries is covariance-free** because the adding-up identities `Σ_i w_it β_im = 1`,
  `Σ_{j∈i} w_ijt β_jm = 1`, `Σ_{j∈i} w_ijt β_ij = 1` (eq. 3) make `Σ_i w_it(β_im − 1) = 0`. `[V]` Hence
  `Σ_i w_it Var(R_it) = Var(R_mt) + Σ_i w_it Var(ε_it)` (eq. 9), and one level down (eq. 16)
  `Σ_i w_it Σ_{j∈i} w_ijt Var(R_ijt) = σ²_mt + σ²_εt + σ²_ηt`. Their words: "the terms involving betas
  aggregate out." `[V]`
- **The stronger answer, which the paper does not state.** The cross-products vanish **identically, day by
  day, in sample** — no expectation, no population betas, no distributional assumption — because the
  residuals are deviations from *weighted* cross-sectional means:
  `Σ_{j∈i} w_ijt η_ijs = 0` and `Σ_i w_it ε_is = 0` **exactly, every day**. `[D]` So
  `MKT_t + IND_t + FIRM_t` equals the weighted sum of squared firm deviations **exactly**.
- **What the beta restriction actually costs is interpretation, not the identity** (eqs. 17–18):
  `σ²_εt = σ̃²_εt + CSV_t(β_im)·σ²_mt` and
  `σ²_ηt = σ̃²_ηt + CSV_t(β_jm)·σ²_mt + CSV_t(β_ij)·σ̃²_εt`, where `CSV_t` is the **cross-sectional
  variance of betas**. `[V]` **If beta dispersion trends, FIRM trends spuriously.** CLMX check this and
  dismiss it: regressing IND on MKT gives 0.27 against a direct `CSV(β_im)` estimate of only 0.03;
  regressing FIRM on MKT and IND gives 0.72 and 1.40, "much too large to be explained by plausible
  cross-sectional variation in firms' beta coefficients." `[V]` **Note this is exactly the same
  loading-dispersion channel that drives Ψ (Appendix A.3) — the two live in the same algebra.**
- **The estimators** — sampling frequency **daily**, aggregation window **one calendar month**, output
  series **monthly**:

```
MKT_t   = Σ_{s∈t} (R_ms − μ_m)²                          (WP 19 / JF 17)
IND_t   = Σ_i w_it · Σ_{s∈t} ε²_is                       (WP 21 / JF 18–19)
FIRM_t  = Σ_i w_it · Σ_{j∈i} w_ijt · Σ_{s∈t} η²_ijs      (WP 24 / JF 20–22)
```

  `[V]` **Three replication traps** `[V]`: (1) `μ_m` is the **full-sample** mean daily market excess
  return, not a within-month mean; (2) **no mean is subtracted for IND or FIRM** — raw sums of squared
  residuals, which is correct because `ε` and `η` are already exact cross-sectional deviations; (3) the
  daily excess return uses the 30-day bill return divided by trading days in the month.
- **The firm term needs individual stocks, but not per-firm regressions.** Since `w_it·w_ijt = W_jt`,
  both terms are **weighted cross-sectional variances computed day by day**:
  `IND_t = Σ_s [Σ_i w_it R²_is − R²_ms]` and
  `FIRM_t = Σ_s Σ_i w_it [Σ_{j∈i} w_ijt R²_ijs − R²_is]` — one pass accumulating `Σ w R` and `Σ w R²`.
  `[V]` **That identity removes the betas, not the need for CRSP.**
- **Universe and sample.** CRSP daily, NYSE + AMEX + NASDAQ, **July 1962 – December 1997, 426 months**;
  2,047 firms (62:7) rising to 8,927 (97:12). Weights from market cap at `t−1`, **held constant within
  the month**. `[V]`
- **Industries: 49 = the Fama–French (1997, *JFE* 43, 153–193) 48 plus a residual bucket for unclassified
  firms.** `[V, their footnote 2 verbatim]` ⚠️ **This is NOT the vendor's public 49-industry scheme**,
  which instead splits `Comps` into `Hardw` + `Softw`. **For replication use the 48-industry set**, whose
  `Other` already absorbs the unclassified firms. `[V]`
- **Trend test: Vogelsang, T.J. (1998), "Trend Function Hypothesis Testing in the Presence of Serial
  Correlation," *Econometrica* 66(1), 123–148 — the `PS₁` statistic.** `[V, verbatim]` Robust to I(0) and
  I(1) errors; they use PS₁ "to obtain the best power" having rejected a unit root in all three series by
  ADF. **They report no critical value** — inference is by whether zero lies outside a reported two-sided
  90% confidence interval. `[V]` The October-1987 observation is replaced by the sample's second-largest
  in the crash-downweighted variants. `[V]`

**Headline numbers — daily, value-weighted, 1962:07–1997:12 (Table 3 / Table III).** `[V, two independent
extractions agreeing, cross-validated against the authors' archived files]`

| | MKT | IND | FIRM |
|---|---|---|---|
| mean ×100, **annualized variance** | **1.542** | **1.032** | **6.436** |
| implied annualized SD | **12.4%** | **10.2%** | **25.4%** |
| linear trend ×10⁵ | 0.156 | 0.062 | **0.965** |
| PS statistic | 0.261 | 0.086 | **1.005** |
| 90% CI | (−0.07, 0.60) | (−0.10, 0.27) | **(0.55, 1.47)** |

**Only FIRM's trend excludes zero.** `[V]` **Aggregate industry volatility does not trend** — insignificant
at 10% raw and crash-downweighted, at daily, weekly and monthly horizons. `[V]` Across the 49 individual
industries, 14 have significantly positive IND trends and 7 significantly negative, while **24 have
significantly positive FIRM trends and none negative**. `[V]`

⚠️ **Scale convention, the single biggest replication trap and not stated in the table note:** the means
and standard deviations are **annualized (×12)**, but **the trend coefficient is per-month on the
NON-annualized monthly variance.** `[V, reconstructed and confirmed against six of the paper's own
numbers to within 1pp]`

**Fitted endpoints — use these as replication targets** (crash-downweighted, VW, daily; `0.939×10⁻⁵ ×
426`):

| | 1962:07 | 1997:12 | ratio | annualized SD |
|---|---|---|---|---|
| MKT | 0.0118 | 0.0164 | 1.39 | 10.9% → 12.8% |
| IND | 0.00874 | 0.01180 | 1.35 | 9.3% → 10.9% |
| **FIRM** | **0.0398** | **0.0878** | **2.21** | **20.0% → 29.6%** |
| TOTAL | 0.0603 | 0.1160 | 1.92 | 24.6% → 34.1% |

`[V/D]` The paper's own prose matches: firm-level variance "more than doubled" while market and industry
rose "by only about one third." `[V]`

**Variance shares.** Trend-fitted, crash-downweighted: **1962 — FIRM 65%, MKT 20%, IND 15%; 1997 — FIRM
76%, MKT 14%, IND 10%.** `[V]` Unconditional full-sample means (their Table 6): **MKT 16%, IND 12%, FIRM
72%**, with the market share — "the R² of a market model" — "only about 17%." `[V]`

**Correlations and market-model R².** Average pairwise correlation, **monthly** (5-year rolling):
**0.28 in the early 1960s → 0.08 in 1997**; **daily** (12-month rolling): **0.12 → 0.02–0.04.** `[V]`
The market-model R² panel of their Figure 5 is "almost indistinguishable" from the correlation panel
(if all stocks were identical with common correlation ρ, the market-model R² equals ρ) — so average R²
follows the same path. **Exact R² values exist only in the figure; there is no table.** `[V/INF]`

**The diversification statistic** (quotation paraphrased to keep this repo's forbidden vocabulary out; the
original wording is in the paper). CLMX report that in the first two subsamples a randomly chosen group of
**20** stocks reduced *excess standard deviation* to about 10%, whereas in 1986–97 the same level required
a group of **50**. `[V]` **20 → 50, i.e. 2.5×, not 2×.** Subsamples 1963–73, 1974–85, 1986–97; "excess
standard deviation" = √(group variance − equal-weighted index variance), computed on equal-weighted random
groups without replacement. `[V]` A typical 2-stock group's SD rose from below 30% in the early 1960s to
almost 50% by 1997, while a 50-stock group showed only "a modest increase." `[V]`
**This statistic has never been recomputed on post-1997 data by anyone.** `[V]`

**The authors' own update, and it is the most important follow-on: Campbell, Lettau, Malkiel & Xu (2023),
"Idiosyncratic Equity Risk Two Decades Later," *Critical Finance Review* 12(1–4), 203–223** (NBER WP
29916, 2022), sample **1927–2021**, methodology unchanged. `[V]`

| annualized SD, VW | 1962–1997 | since 1997 |
|---|---|---|
| MKT | 12% | **18%** |
| IND | 9% | **14%** |
| FIRM | 26% | **28%** |

Verbatim: "*While a linear trend was a good description of the increase in idiosyncratic volatility in our
sample period, we did not believe that the positive trend would necessarily continue in extended
samples.*" `[V]` And: "*A main difference between volatility patterns today and those of the late 1990s is
not that idiosyncratic volatility is lower, but that industry and, in particular, market volatility are
higher.*" `[V]` The market share of total variance went **~10% (late 1990s) → 40% (GFC peak) → ~30%**; the
FIRM share fell **below 50% in the GFC and is ~60% now** (VW). `[V]` "*Variance shares in the recent data
look more like the period 1926–1962 than like the CLMX period 1962–1997.*" `[V]`

⚠️ **They never mention mega-cap concentration.** The rise in the market share is attributed to volatility
*levels*, not concentration. `[V]` **`[INF]`, and it matters for this repo: a rising top-weight
concentration mechanically pushes a few firms' idiosyncratic risk into the MKT term of a cap-weighted
decomposition, so measured MKT variance can rise from concentration alone with no change in true
systematic risk. CLMX's framework does not separate the two, and no published decomposition covers
2022–2025.**

**The intervening debate, with the numbers that settle it** — see §3 for the contested table. The short
version: the 1962–97 rise is **real and replicable** (Brandt et al. reproduce the trend at 0.963 vs CLMX's
0.965) `[V]`, it **stopped in 2001 and reversed**, it lives almost entirely in NASDAQ (NYSE/AMEX-only
trend = **0.032**, i.e. nothing) `[V]`, and the current best account is composition (firm age, listing
cohort) plus growth options.

### 1.2 The number of factors — SOLVED in theory (1983) and in estimation (2002–2013)

- **Chamberlain, G. & Rothschild, M. (1983), "Arbitrage, Factor Structure, and Mean-Variance Analysis on
  Large Asset Markets," *Econometrica* 51(5), 1281–1304.** Defines the **approximate factor structure**:
  in a large cross-section, *k* factors means exactly *k* eigenvalues of the covariance matrix diverge
  with N while the rest stay bounded. `[S]` **The number of factors is the number of diverging
  eigenvalues** — that is the right definition and it is 43 years old.
- **Bai, J. & Ng, S. (2002), "Determining the Number of Factors in Approximate Factor Models,"
  *Econometrica* 70(1), 191–221.** `[V citation]` The `PC_p` and `IC_p` criteria with penalties
  `g(N,T)` — consistent as `N,T → ∞` jointly. Known practical weaknesses: sensitivity to `k_max`, to
  standardization, and upward bias under cross-sectionally correlated errors. `[S]`
- **Onatski, A. (2009/2010)** — eigenvalue-difference / edge-distribution estimator using the Tracy–Widom
  limit. **Ahn, S.C. & Horenstein, A.R. (2013), *Econometrica* 81(3), 1203–1227** — eigenvalue-ratio (ER)
  and growth-ratio (GR) estimators, generally more robust in practice than Bai–Ng. `[S]`
- **Connor, G. & Korajczyk, R.A. (1993), *Journal of Finance* 48(4), 1263–1291** — an earlier test for the
  number of factors; asymptotic principal components (1986, 1988). `[S]`
- **Empirically, on volatility panels, the answer is one.** Luciani & Veredas, *Journal of Forecasting*
  34(3) (2015): "the four methods unanimously indicate that there is one common factor" (spectral-density
  eigenvalue share, covariance eigenvalue share, Bai–Ng IC, Onatski). `[V]` Engle & Marcucci, *Journal of
  Econometrics* 132(1) (2006): "at most three variance factors in the thirty volatilities" — 2 in log
  space, 3 with Box–Cox. `[V]`

### 1.3 How many factors are distinguishable from noise — SOLVED, 1967/1999

- **Marchenko & Pastur (1967).** For an N×T matrix of iid entries with variance σ², with `q = N/T` fixed
  as `N,T → ∞`, the sample correlation eigenvalues are supported on
  `λ± = σ²(1 ± √q)²`. **Eigenvalues below λ₊ are indistinguishable from noise.** `[S]`
  Numerical values for the exact panels on disk are in **Appendix B**.
- **Laloux, Cizeau, Bouchaud & Potters (1999), "Noise Dressing of Financial Correlation Matrices,"
  *Physical Review Letters* 83(7), 1467–1470.** The canonical result is usually quoted as **≈94% of the
  S&P 500 correlation-matrix eigenvalues falling inside the Marchenko–Pastur bulk**. ⚠️ **This figure
  could NOT be verified against the primary paper in this session** — one thread found it only via Fenn
  et al.'s citation of it, and the dedicated random-matrix thread never delivered. **Treat the 94% as
  unverified and check it before quoting.** The *qualitative* claim — most of the spectrum is
  noise-compatible — is not in doubt.
- **Plerou, Gopikrishnan, Rosenow, Amaral, Guhr & Stanley (2002), "Random matrix approach to cross
  correlations in financial data," *Physical Review E* 65, 066126.** The deviating eigenvectors **map
  onto business sectors**; the largest is the market mode with roughly uniform positive components.
  Verified figures: **N = 1,000 US stocks, 30-minute returns, 1994–95: λ₁ ≈ 50 against an RMT bound of
  λ₊ = 1.94**; **N = 422 US stocks, daily, 1962–96: λ₁ = 46.3.** `[V]` Since `tr R = N`, those imply PC1
  variance shares of **5.0%** and **11.0%** respectively `[D]` — a useful reminder that at large N the
  market mode is a *huge* eigenvalue but a *small* variance share, the reverse of what a 10- or
  48-series industry panel will show.
- **Johnstone (2001), *Annals of Statistics* 29(2), 295–327** — Tracy–Widom law for the largest
  eigenvalue, giving a formal test. `[S]`
- **Bun, Bouchaud & Potters (2017), "Cleaning large correlation matrices: tools from random matrix
  theory," *Physics Reports* 666, 1–109** — the modern synthesis. `[V]`

**Settled consequence, and it constrains this repo directly:** for an outlier eigenvector to be
recoverable at all it must clear the BBP transition at `μ₁ = 1 + √q`. `[V]` At N=48, T=125 that means an
eigenvalue above **1.62**; at N=10, T=125, above **1.28**. In an industry panel the market mode
(λ₁ ≈ 0.5N–0.7N) clears this enormously and typically only 1–4 further eigenvalues do. `[INF]`

### 1.4 The common factor in volatility panels — SOLVED, repeatedly, since 2001

- **Andersen, Bollerslev, Diebold & Ebens (2001), "The distribution of realized stock return volatility,"
  *Journal of Financial Economics* 61(1), 43–76.** The justification for working in log-vol space.
  Realized **variance** has median skewness **5.609**, median kurtosis **66.16**; **log realized standard
  deviation** has median skewness **0.192**, median kurtosis **3.885**. `[V]` Returns scaled by realized
  s.d. have median kurtosis **3.129**. `[V]` Long memory: GPH `d` median **0.349** on log realized s.d.
  `[V]` The volatility-in-correlation effect: median `Corr(Corr_ij,t, lv_i,t) = 0.150` across 870 pairs;
  median `Corr(lv_i,t, lv_j,t) = 0.205` across 435 pairs. `[V]` Sample: the 30 DJIA constituents,
  5-minute returns, 2 Jan 1993 – 29 May 1998, 1,366 days. `[V]`
- **Herskovic, Kelly, Lustig & Van Nieuwerburgh (2016), "The Common Factor in Idiosyncratic Volatility:
  Quantitative Asset Pricing Implications," *Journal of Financial Economics* 119(2), 249–283.** CIV.
  Construction (footnote 24, verbatim): "Each month, we estimate a regression of daily individual firm
  returns on the value-weighted market return for all CRSP firms with non-missing data that month. We then
  calculate CIV (in levels) as the **equal-weighted average of market model residual variance** across
  firms." `[V]` So: monthly, market model only, daily returns within the month, EW average of residual
  **variance**. Shocks are monthly first differences.
  - **A single factor explains ≈35% of the time variation in firm-level idiosyncratic risk** `[V]`;
    average univariate R² 34.6–34.8% for idiosyncratic vol, 36.2% for total vol. `[V]`
  - Group-level correlations of idiosyncratic-vol **levels**: size Q1 vs Q5 = **81%**; minimum across five
    industry groups = **65%**. `[V]` (They never report a firm-level pairwise correlation of idio-vol
    *changes*.) `[V]`
  - After a 5-PC return model, residual **return** correlations are typically **<0.2%**, never above 0.9%
    in any year — so the volatility comovement is not an omitted-return-factor artifact. `[V]` This is the
    paper's central rhetorical move and it is the reason "we removed the market and there is still
    structure" is not, by itself, a finding.
  - CIV vs market variance: correlation **63.8%** in levels, **67.0%** in innovations. `[V]`
  - **Grouped series show a much stronger factor structure than firms**: average univariate R² **70.8%**
    (total vol), **49.7%** (market-model residual vol) and **39.4%** (FF3 residual vol) on 100
    size/value-sorted groups, vs ≈35% at the firm level. `[V]` **Directly relevant: an industry panel is
    a panel of grouped series.**
    ⚠️ **But do not treat this table as a checkable replication target.** A research thread attempted
    exactly that and **failed to reproduce it** — the total-vol figure came out close, the two residual
    figures far off — almost certainly a definitional mismatch in the residual construction, the
    log-vs-level choice, or the sample handling. **Use 49.7% as a directional prior, not a bar.**
    `[V — negative result, and it saves an afternoon]`
  - The pricing result (negative price of CIV risk, ≈ −5.4%/yr spread) is outside this repo's boundary as
    an application and is not relied on here. It is worth knowing that it is **much weaker in the first
    half of the sample** (1963–1985 FF3 α = −1.18%, t = −0.75, insignificant; 1986–2010 α = −4.94%,
    t = −2.57). `[V]`
  - **No failed replication or published critique of CIV was found** in a 100-citation sweep. `[V, but
    the sweep was not exhaustive]` The cautionary precedent in the neighbouring literature is Goyal &
    Santa-Clara (*Journal of Finance* 2003) vs Bali, Cakici, Yan & Zhang (*Journal of Finance* 2005),
    where an equal-weighted average-variance factor did not survive out of sample. `[V]`
  - **Out-of-sample confirmation exists:** Bekaert, Hodrick, Wang & Zhang, "The International Commonality
    of Idiosyncratic Variances," *Management Science* 71(3) (2025), 2216–2244 — 23 developed markets,
    robust worldwide synchronization. `[V]`
- **Herskovic, Kelly, Lustig & Van Nieuwerburgh (2020), "Firm Volatility in Granular Networks," *Journal
  of Political Economy* 128(11), 4097–4162.** See §1.5 — this is the paper that already contains `c_t`.
- **Barigozzi & Hallin** — generalized dynamic factor models on volatility. *Econometrics Journal* 19(1)
  (2016), C33–C60; *Journal of Econometrics* 201(2) (2017), 307–321; *Journal of Econometrics* 216(1)
  (2020), 4–34. Two-stage: GDFM on returns, then GDFM on `log(residual²)`. Their stated reason for the log
  is decisive for this repo: a logarithmic proxy "can be analyzed via an **additive factor model**, while a
  similar analysis of the squared residuals would require imposing intricate positivity constraints."
  `[V]` Market-volatility R² on the level-common volatility panel = **0.5997**; on the level-idiosyncratic
  panel = **0.1740**. `[V]`
- **Engle & Marcucci (2006), *Journal of Econometrics* 132(1), 7–42.** The sharpest evidence that the log
  transform is not cosmetic: common-ARCH-feature tests on **squared returns** find a common feature in
  only **4 of 435 pairs**; on the **log** transform, the null is rejected for only **35 of 435 pairs** —
  i.e. almost all pairs share a common feature. `[V]`
- **Engle & Rangel (2008), "The Spline-GARCH Model for Low-Frequency Volatility and Its Global
  Macroeconomic Causes," *Review of Financial Studies* 21(3), 1187–1222**; **Engle, Ghysels & Sohn (2013),
  *Review of Economics and Statistics* 95(3), 776–797** (GARCH-MIDAS). Both split a slow common volatility
  *level* from short-run dynamics via a multiplicative `τ_t · g_t` with `E[g] = 1`. `[V]` Same
  architecture as `c_t` + `D_it`, in a univariate rather than cross-sectional setting.
- **Connor, Korajczyk & Linton (2006), "The common and specific components of dynamic volatility,"
  *Journal of Econometrics* 132(1), 231–255.** `log f_t = g_f(t/T) + u_t`, where `f_t` is a
  cross-sectional mean-square asset-specific return, "approximately observable by taking a probability
  limit for large n." Monthly CRSP, 1926–2000, n = 21,598. `[V]` **This predates BBGV by eight years with
  essentially the same architecture, in logs.**

### 1.5 The specific construct `c_t`, `D_it` — ALREADY PUBLISHED

**Verdict: at the firm level, exactly published; at the sector level, published in multiplicative form.**

- **HKLVN, *JPE* 128(11) (2020), §2.1 and Table 5.** They define `μ_σ,t` = cross-sectional average log
  volatility and `σ_σ,t` = cross-sectional standard deviation of log volatility, and run
  **`log σ_i,t = a_i + b_i·factor_t + e_i,t`**. `[V]` Verbatim: "Since this is essentially the first
  principal component of firm volatilities, it is a natural yardstick for any one-factor model." `[V]`
  Their justification is the one this repo should use: "The cross-sectional size and variance
  distributions are well approximated by a lognormal distribution. As a result, each distribution may be
  summarized by **two moments: the cross-sectional mean and cross-sectional variance of the log
  quantities**." `[V]`
  **Table 5 R² (annual, CRSP, 1926–2016):** contemporaneous `μ_σ,t` → **33.65%** all firms (29.37% small,
  36.55% large); lagged `μ_σ,t−1` → 20.94%; lagged log-size dispersion → 15.65%. Loadings on `μ_σ,t`:
  **0.73** all firms. `[V]` **`D_it` is precisely the residual `e_i,t` under the restriction `b_i = 1`.**
- **HKLVN 2016, the 14 Feb 2014 draft.** "the cross-sectional distributions of return volatility and
  fundamental volatility are lognormal to a close approximation, **which motivates us to estimate our
  factor models using volatility in logs rather than levels**." Table 1 is titled "Log Volatility Factor
  Model Estimates"; the factor is "the **equal weighted average of all firms' log volatilities**." `[V]`
  Loadings **0.925 / 0.920 / 0.924 / 0.925**; average univariate R² **0.363**. `[V]` **Its Figure 3 plots
  Panel B "Average Log Volatility" and Panel C "Dispersion of Log Volatility" — literally `c_t` and
  `sd_i(D_it)`, 1926–2010.** `[V]`
  *Unresolved:* the published JFE 2016 Table 1 appears to be in **levels**, not logs (the 5.4% headline
  matches the Dec-2014 levels draft). `[INF, high confidence]` Their own JPE 2020 paper retrospectively
  describes the 2016 result as being about "log firm variance". **Pulling the published JFE Table 1 is a
  five-minute check that settles whether `c_t` is "the CIV factor in logs" or a variant.**
- **Barigozzi, Brownlees, Gallo & Veredas (2014), "Disentangling systematic and idiosyncratic dynamics in
  panels of volatility measures," *Journal of Econometrics* 182(2), 364–384.** `[V — note: *Journal of
  Econometrics*, NOT *Journal of Applied Econometrics*]` Model: **`x_it = a_i · φ(z_t) · μ_it · ε_it`**
  with `x_it` a realized kernel variance, `a_i` an asset scale factor, `φ(z_t)` a deterministic smooth
  scalar common trend with `E[φ]=1`, `μ_it` an idiosyncratic asymmetric-GARCH MEM component. `[V]`
  **In logs this is `log a_i + log φ(z_t) + deviation` — the two-way fixed effect exactly.** The authors
  never write it that way. `[INF]` The trend estimator is literally a precision-weighted cross-sectional
  mean of each series divided by its own sample mean, kernel-smoothed with a three-month bandwidth. `[V]`
  **The panel is nine sector index series** (Materials, Energy, Financials, Industrials, Technology,
  Staples, Utilities, Health Care, Discretionary), daily, 2 Jan 2001 – 31 Dec 2008. `[V]`
  **Sector commonality benchmark numbers — use these as the prior:** average pairwise correlation
  **0.66–0.82**, PC1 share **0.58–0.91**, both "always above 0.50 and 50% respectively." `[V]`
  Their key finding for this repo: plain univariate models without the trend give volatility persistence
  collapsing to ≈1 for essentially every series; **the common trend is what restores stationarity of the
  deviations.** `[V]` And residual correlation falls to ≈0.40 from >0.50, with **sector clusters that are
  invisible in the raw data** appearing in the residual heat-map. `[V]`
- **Luciani & Veredas (2015), *Journal of Forecasting* 34(3), 163–176.** Approximate DFM on **log**
  realized volatility, 90 series, 2001–2008. `r = 1`. Loadings min 0.54 / **median 0.96** / max 1.38,
  "approximately equally distributed around one." `[V]` **With r=1 and unit-centred loadings the estimated
  common component is numerically very close to the equal-weighted cross-sectional mean of log-RV** —
  i.e. to `c_t`. `[INF]` Long memory: raw log-RVs median `d = 0.55`; **the factor has `d = 0.69`** —
  the common level is *more persistent* than the deviations. `[V]`
- **Econometric name to cite:** `c_t` as a factor proxy is the **Common Correlated Effects** estimator —
  **Pesaran, M.H. (2006), "Estimation and Inference in Large Heterogeneous Panels with a Multifactor Error
  Structure," *Econometrica* 74(4), 967–1012** — which uses cross-sectional averages as proxies for
  unobserved common factors. `[S]` Companion: Bai (2009), interactive fixed effects.

### 1.6 Hierarchical (common → block → series) variance decomposition — SOLVED

- **Moench, Ng & Potter (2013), "Dynamic Hierarchical Factor Models," *Review of Economics and
  Statistics* 95(5), 1811–1817.** Blocks with block-level factors and a common factor above them,
  estimated by Bayesian MCMC. `[S — the dedicated agent for this did not return; verify the estimation
  details and the applied panel before citing specifics.]`
- **Kose, Otrok & Whiteman (2003), "International Business Cycles: World, Region, and Country-Specific
  Factors," *American Economic Review* 93(4), 1216–1239.** The three-level Bayesian dynamic factor
  variance decomposition — world / region / country. `[S]` **This is the closest methodological cousin to
  a market/industry/firm decomposition done with an explicit factor model rather than the CLMX no-beta
  trick**, and it reports variance shares by level directly.
- **Diebold & Yılmaz** — a different way to decompose a panel, via forecast-error variance decompositions
  of a VAR. *Economic Journal* 119(534) (2009), 158–171; *International Journal of Forecasting* 28(1)
  (2012), 57–66; *Journal of Econometrics* 182(1) (2014), 119–134. `[V]` Definition:
  `S = 100 · (Σ_{i≠j} a²_0,ij) / trace(A₀A₀')`, generalized to H-step horizons; the total connectedness
  index equals `1 − (mean own-variance share)`. `[V]` Headline: 19 global equity markets, 1992–2007,
  weekly, VAR(2), 10-week horizon — **36% of return forecast-error variance and 40% of volatility
  forecast-error variance comes from spillovers.** `[V]` **Return spillovers show a gently increasing
  trend but no bursts; volatility spillovers show no trend but clear bursts.** `[V]` Crisis numbers:
  volatility connectedness 73% → 80% (March–June 2007), then **+12pp to 88% between 25 July and 10 August
  2007**. `[V]`
- **Billio, Getmansky, Lo & Pelizzon (2012), *Journal of Financial Economics* 104(3), 535–559.** PC1
  variance share of a return covariance matrix, explicitly motivated by Chamberlain–Rothschild. `[V]`
  **PC1 = 77% (1994–2000) rising to 83% (2001–2008); PC1+PC2 = 92%; PC1 ranges 65%–93% through time,
  peaking at 93% in August 1998 and exceeding 80% through 2007–09.** `[V]` **This is already a published
  time series of "how much of the cross-section is one common factor."**

### 1.7 The equicorrelation model itself — SOLVED, and the algebra is closed-form

**Engle, R.F. & Kelly, B. (2012), "Dynamic Equicorrelation," *Journal of Business & Economic Statistics*
30(2), 212–228.** `[V]` Definition 2.1 is `R_eq` verbatim: `R_t = (1−ρ_t)I_n + ρ_t J_n`. `[V]`
Closed forms (Lemma 2.1, from Graybill 1983):

```
R⁻¹ = 1/(1−ρ) · [ I − ρ/(1+(n−1)ρ) · J ]
det(R) = (1−ρ)^(n−1) · [1 + (n−1)ρ]
positive definite  iff  ρ ∈ ( −1/(n−1), 1 )
```

`[V]` **For N=48 that lower bound is −0.0213; for N=10 it is −0.111.** `[V]`

**Spectrum, confirmed:** `λ₁ = 1 + (N−1)ρ` once, with eigenvector `1/√N`; `λ₂ = … = λ_N = 1 − ρ`. `[V]`
This is the algebra behind the MI-007 drop (`AR₁ = [1+(N−1)ρ̄]/N`, affine in ρ̄) and the Stage-0 gate's G3.

**A sharpening the gate does not have, and it is the strongest defence of Ψ against the absorption
ratio.** For a general R, `1 + (N−1)ρ̄ = 1'R1/N` is the Rayleigh quotient at the equal-weight vector, so
**`λ₁ ≥ 1 + (N−1)ρ̄` always, with equality iff `1` is an eigenvector of R — i.e. iff all row sums are
equal**, which is far weaker than equicorrelation. `[V]` Therefore `Ψ = 0` is strictly stronger than
"λ₁ matches its equicorrelation value", and **the absorption ratio cannot distinguish equicorrelation from
any equal-row-sum matrix, while Ψ can.** That is a defensible, citable reason to compute Ψ alongside AR₁
rather than instead of it — and it is the correct answer to the F2 reject condition in the gate.

**Two estimators of ρ̄, and they differ** `[V]`:
- **DECO-DCC (their Eq. 7):** the simple average of the off-diagonal correlations — **this is the repo's
  ρ̄, and it is the Frobenius least-squares projection onto the equicorrelation family.** `[V]`
- **LDECO (their Eq. 20, Lemma 2.4 — the period-by-period MLE):**
  `u_t = (1'S_t1 − tr S_t) / ((n−1) tr S_t)`, a **trace-weighted** average. `[V]` This is also exactly the
  classical compound-symmetry MLE. They agree to O(1/p) and coincide when all sample variances are equal.
  **State which one is used.**

**Do they measure departure from equicorrelation? No.** There is no Frobenius norm, no distance metric, no
goodness-of-fit index anywhere in the paper. `[V]` §2.3 acknowledges in one sentence that "the
equicorrelation assumption fails so that there is cross sectional variation in pairwise correlations" and
then **dismisses it by proving DECO is a consistent QMLE of the DCC parameters under exactly that
misspecification.** `[V]` The only tests they run are a Newey (1985) conditional-moment test on *residual*
equicorrelation and a 1-df LM test against the specific alternative `ρ_ij,t = ρ_t + γ·r_i,t−1 r_j,t−1`.
`[V]` They note the full conditional-moment test over all `n(n−1)/2` pairwise moments is infeasible for
large n. `[V]` **This is the precise shape of the gap: they proved the misspecification does not hurt
them, so they never had a reason to measure it.**

### 1.8 Time-varying correlation — the stylized facts are settled, and one of them is a trap

- **Forbes, K. & Rigobon, R. (2002), "No Contagion, Only Interdependence: Measuring Stock Market
  Comovements," *Journal of Finance* 57(5), 2223–2261.** `[V]` **The single most important methodological
  warning in this whole review.** Under `y = α + βx + ε` with constant β and exogenous x, the observed
  correlation in a high-volatility subsample is biased upward:

```
ρ_h = ρ_l · sqrt( (1+δ) / (1 + δ·ρ_l²) )
adjustment:  ρ* = ρ_h / sqrt( 1 + δ(1 − ρ_h²) ),    δ = (σ^h_xx − σ^l_xx)/σ^l_xx
```

  `[V, verbatim]` Empirically: average turmoil correlation **0.53 unadjusted → 0.32 adjusted** (1997 East
  Asia); Hong Kong–Netherlands **0.35 → 0.74 unadjusted, 0.35 → 0.40 adjusted**; the count of markets
  showing "contagion" falls from **15 to 1** (1997) and from **6 to 0** (1994 Mexico). `[V]`
  **Caveat they state themselves: the correction is exact only under constant β, exogenous x, and no
  omitted common factor.** `[V]` Corsetti, Pericoli & Sbracia, *Journal of International Money and
  Finance* 24(8) (2005), 1177–1199, reverse several conclusions once idiosyncratic variance is allowed to
  differ. `[S]`
- **Loretan & English (2000), Federal Reserve Board IFDP No. 658.** The general version: conditioning on
  **any** event A defined on x, `ρ_A = ρ / sqrt(ρ² + (1−ρ²)·σ²_x/Var(x|A))`. `[V]` Requires ellipticity,
  which they verify nonparametrically. `[V]` Their finding: the 1998 "correlation breakdown" was largely a
  conditioning artifact. `[V]`
- **Longin & Solnik (2001), "Extreme Correlation of International Equity Markets," *Journal of Finance*
  56(2), 649–676.** `[V]` Multivariate extreme value theory rather than conditional correlation — this
  **sidesteps the Forbes–Rigobon bias** because the null is derived under the actual distributional model.
  Finding: correlation increases in bear markets but not bull markets; the multivariate-normal null is
  rejected for the negative tail only. `[V]`
- **Ang & Chen (2002), *Journal of Financial Economics* 63(3), 443–494** — exceedance correlations
  `ρ±(c)` and the H statistic; downside exceedance correlations ≈11.6% above the bivariate normal.
  `[S — the 11.6% figure was not verified]` **Ang & Bekaert (2002), *Review of Financial Studies* 15(4),
  1137–1187** — regime-switching correlations; the "bear" regime has higher volatility **and** higher
  correlation simultaneously, so the regime variable loads on both moments at once. `[S]`
- **Engle (2002), *Journal of Business & Economic Statistics* 20(3), 339–350** — DCC. **Cappiello, Engle
  & Sheppard (2006), *Journal of Financial Econometrics* 4(4), 537–572** — asymmetric DCC; equity
  correlations show strong asymmetry, bond correlations little. `[S]`

### 1.9 Eigenstructure stability over time — largely solved, and mostly negative

- **Bun, Bouchaud & Potters (2017), *Physics Reports* 666, 1–109.** `[V]` Two results, verbatim:
  "(i) Any bulk sample eigenvector is **delocalized** in the population basis … (ii) For any outlier,
  `u_i` is **concentrated within a cone** with its axis parallel to `v_i` but is completely delocalized in
  any direction orthogonal to the spike direction." `[V]` And decisively: "for the bulk eigenvectors, we
  discover that projection of the estimated eigenvectors and their corresponding 'true' directions
  **converges almost surely to zero** for large N; i.e. **sample eigenvectors appear to contain very little
  information about the true eigenvectors**." `[V]`
  They also define the two-sample overlap `Φ(λ_i, λ̃_j) = N·E[⟨u_i, ũ_j⟩²]` between two **independent**
  samples of the same population matrix (their Eq. 4.4, 4.40–4.41) — **this is the pattern-persistence
  question with a closed-form null** — and state its purpose: "Any statistically significant deviation
  between this predicted overlap and empirical results can be interpreted as a violation of the hypothesis
  that the 'true' population matrices … are in fact different." `[V]`
  Their empirical protocol is a near-exact template: **N = 300 US equities, 2004–2013, split into two
  non-overlapping 1,200-day subperiods, T = 600 sampled per subperiod, q = 0.5, 100 bootstraps**, repeated
  for TOPIX and a European panel. Finding: **real data requires an effective `q_eff > q`** — it is
  *noisier* than the iid null, consistent with genuine non-stationarity plus fat tails. `[V]`
- **Allez & Bouchaud (2012), "Eigenvector dynamics: general theory and some applications," *New Journal of
  Physics* 14, 013023.** `[V]` **The single most important quantitative prior for Phase 11.** They note
  "single eigenvectors are strongly unstable in time" because of eigenvalue pseudo-collisions, so one must
  study **subspaces**, and they give both an RMT accidental-overlap null and a noise-only null for two
  non-overlapping windows. `[V]` Empirically (204 Nikkei names, daily, 2000–2010): `D_emp > D_th`
  decisively — genuine eigenvector evolution — and the ratio `D_emp/D_th` at τ = T, plotted against T,
  "reveals a marked maximum around **T\* ≈ 2 years**, suggesting that the correlation matrix has some true
  dynamical evolution with a **mean reversion time around T\***." `[V]`
  **Consequence: real correlation-matrix dynamics exist and their characteristic timescale is ≈500 trading
  days. A 125- or 250-day window is shorter than the dynamics being estimated.**
- **Münnix et al. (2012), "Identifying States of a Financial Market," *Scientific Reports* 2:644.** `[V]`
  Distance is **L1, not Frobenius**: `ζ(t₁,t₂) = ⟨|C_ij(t₁) − C_ij(t₂)|⟩_ij`. `[V]` S&P 500 constituents,
  1992–2010, **non-overlapping two-month windows**, top-down k-means, threshold 0.1465 → **8 market
  states**. `[V]` Persistence is reported **qualitatively and hedged** — no autocorrelation, no decay
  time, no null. `[V]` **That gap is real.**
- **Fenn, Porter, Williams, McDonald, Johnson & Jones (2011), *Physical Review E* 84, 026109.** `[V]`
  N = 98 assets, weekly, 1999–2010; MP edge λ₊ = 3.96 with several empirical eigenvalues ~10× larger.
  `[V]` **The sentence that matters most:** "There were **frequent changes in the indices correlated with
  the higher PCs**. This is the result of **changes in the variance of the index returns** for the
  different assets, **which affect the ordering of the PCs**." `[V]` A published statement that subleading
  eigenvector identity is not persistent *and* that the instability is driven by heteroskedasticity.
- **Onnela, Chakraborti, Kaski, Kertész & Kanto (2003), *Physical Review E* 68, 056110** — `d_ij =
  √(2(1−ρ_ij))`, minimum spanning trees, single-step edge survival ratio. `[S — the PDF could not be
  text-extracted; the survival-ratio numbers are unverified]`

---

## 2. What methods already exist — inventory

| Object to be measured | Existing method | Citation | Status |
|---|---|---|---|
| Variance split across levels of aggregation, no betas | CLMX beta-free additive identity | Campbell, Lettau, Malkiel & Xu, *JF* 2001 | Canonical, updated 2022 |
| Same split with an explicit hierarchical factor model | Dynamic hierarchical factor model / three-level Bayesian DFM | Moench, Ng & Potter, *REStat* 2013; Kose, Otrok & Whiteman, *AER* 2003 | Canonical |
| Same split from a VAR's forecast-error variance | Connectedness index | Diebold & Yılmaz 2009/2012/2014 | Canonical |
| Common factor in firm idiosyncratic volatility | EW average of residual variance (CIV) | Herskovic et al., *JFE* 2016 | Canonical; internationally confirmed 2025 |
| Common LOG-volatility level + per-series deviation | `log σ_i,t = a_i + b_i μ_σ,t + e_i,t` | HKLVN, *JPE* 2020, Table 5 | **This is `c_t`, `D_it`** |
| Same, on a SECTOR panel, multiplicative | `x_it = a_i φ(z_t) μ_it ε_it` | Barigozzi, Brownlees, Gallo & Veredas, *JoE* 2014 | **Nine sector series, 2001–08** |
| Same, as an approximate DFM on log-RV | r=1 DFM, ARFIMA-GARCH components | Luciani & Veredas, *J. Forecasting* 2015 | Canonical |
| Same, as a GDFM on `log(residual²)` | Two-stage block GDFM | Barigozzi & Hallin 2016/2017/2020 | Canonical |
| Slow common volatility level vs short-run | Spline-GARCH; GARCH-MIDAS | Engle & Rangel, *RFS* 2008; Engle, Ghysels & Sohn, *REStat* 2013 | Canonical |
| Cross-sectional average as a factor proxy | Common Correlated Effects | Pesaran, *Econometrica* 2006 | The name to cite |
| Number of factors, definition | Diverging eigenvalues / approximate factor structure | Chamberlain & Rothschild, *Econometrica* 1983 | Canonical |
| Number of factors, estimator | `PC_p`/`IC_p`; eigenvalue-difference; eigenvalue-ratio | Bai & Ng 2002; Onatski 2009/10; Ahn & Horenstein 2013 | Canonical |
| Which eigenvalues are distinguishable from noise | Marchenko–Pastur edge; Tracy–Widom | MP 1967; Johnstone 2001; Laloux et al. 1999 | Canonical |
| Whether an eigenvector survives out of sample | BBP transition `μ₁ = 1+√q`; two-sample overlap `Φ(λ,λ̃)` | Bun, Bouchaud & Potters 2017 | **Closed-form null exists** |
| Whether the correlation matrix has true dynamics | Subspace distance `D(P,Q)` vs RMT + noise nulls | Allez & Bouchaud 2012 | **≈2-year mean reversion measured** |
| Distance between two correlation matrices over time | L1 mean absolute difference `ζ` | Münnix et al. 2012 | 8 states, 1992–2010 |
| | Frobenius-cosine correlation matrix distance (CMD) | Herdin, Czink, Özçelik & Bonek, VTC 2005 | Same geometry, different arguments |
| Equicorrelation as a model | DECO / block DECO | Engle & Kelly, *JBES* 2012 | Canonical |
| Testing the equicorrelation restriction | Compound-symmetry LRT | Wilks 1946; Votaw 1948; Anderson Ch.10 | Determinant-based; degenerate for p>n |
| | Modern nonparametric structure test | Sattler & Dobler, arXiv:2310.11799 | **Off-the-shelf, finite 4th moments only** |
| Distance from a scaled identity | John's `U`; Nagao's `V`; `W` | John 1971; Nagao 1973; Ledoit & Wolf, *Ann. Stat.* 2002 | **Ψ's denominator, essentially** |
| Misspecification of the constant-correlation target | `γ̂ = Σ(f_ij − s_ij)²` | Ledoit & Wolf 2004 | **Ψ's numerator, exactly** |
| Concentration of variance in top eigenvectors | Absorption ratio | Kritzman, Li, Page & Rigobon 2011 | Competing measure; MI-007 |
| Correlation level in one scalar | Average pairwise correlation; implied correlation | Pollet & Wilson, *JFE* 2010; Driessen, Maenhout & Vilkov, *JF* 2009 | Level only, no dispersion |
| Correlation level from return dispersion | Cross-sectional return dispersion identity | Solnik & Roulet, *Financial Analysts Journal* 2000 | **Terminology collision — see §5** |

---

## 3. Established vs contested empirical findings

### Established

| Finding | Evidence |
|---|---|
| A single common factor explains ≈35% of firm-level idiosyncratic volatility variation | HKLVN 2016 `[V]` |
| That factor is not an omitted return factor — post-5-PC residual return correlations are <0.2% | HKLVN 2016 `[V]` |
| The common volatility factor is international | Bekaert, Hodrick, Wang & Zhang, *Management Science* 2025 `[V]` |
| Log realized volatility is approximately Gaussian; realized variance is violently right-skewed | ABDE 2001: skew 0.192 vs 5.609; kurtosis 3.885 vs 66.16 `[V]` |
| Common volatility features are visible in log space and nearly invisible in squared-return space | Engle & Marcucci 2006: 4/435 vs 400/435 pairs `[V]` |
| Grouped/sector series have a far stronger common volatility factor than individual firms | HKLVN 49.7–70.8% vs ≈35%; BBGV PC1 0.58–0.91 on nine sector series `[V]` |
| The common log-vol level is more persistent than the deviations | Luciani & Veredas: factor d=0.69 vs raw median 0.55 `[V]`; BBGV: deviations only become mean-reverting after the trend is removed `[V]` |
| Most of an equity correlation matrix's spectrum is noise-compatible | Laloux et al. 1999 — ⚠️ the usually quoted **94%** could not be verified this session; the qualitative claim is not in doubt |
| Deviating eigenvectors beyond the first map onto business sectors | Plerou et al. 2002 `[V]` |
| Bulk sample eigenvectors carry asymptotically zero information about population eigenvectors | Bun, Bouchaud & Potters 2017 `[V]` |
| Sample correlation rises mechanically with volatility even at constant true correlation | Forbes & Rigobon 2002 `[V]`; Loretan & English 2000 `[V]` |
| Correlation rises in bear markets specifically, surviving an EVT null immune to that bias | Longin & Solnik 2001 `[V]` |
| Connectedness/PC1 share is strongly time-varying and spikes in crises | Diebold & Yılmaz (73%→88% in 16 days, 2007) `[V]`; Billio et al. (PC1 65–93%) `[V]` |
| Industry/sector factors exist beyond the market factor — the correlation matrix is NOT one-factor | King, *Journal of Business* 1966; Roll 1992; Heston & Rouwenhorst 1994; Fama & French 1997 `[S]` |
| The correlation matrix has genuine dynamics with a ≈2-year mean-reversion time | Allez & Bouchaud 2012 `[V]` |

### Contested or reversed

| Claim | Status |
|---|---|
| Firm-level volatility trended up secularly (CLMX 1962–97) | **Reversed, and the authors concede it.** Brandt, Brav, Graham & Kumar (*RFS* 23(2), 2010, 863–899): VW mean idiosyncratic volatility back to **6.59%** by 2003, "remarkably close to the average level over the first half of the CLMX sample"; they reproduce CLMX's trend at **0.963** (vs 0.965 ✓) then show it becomes **0.211, insignificant** when extended to 2008Q3; **Bai–Perron structural break at April 2000**, pre-break +1.304×10⁻⁵, post-break **−26.629×10⁻⁵**, both strongly significant; **NYSE/AMEX-only trend is 0.032 (1962–97) and −0.024 (1962–2008) — the trend lives in NASDAQ** `[V]`. Bekaert, Hodrick & Zhang (*JFQA* 47(6), 2012): US 1964–1997 t‑PS₁ = **3.89** (significant), US 1964–2008 t‑PS₁ = **1.35** (insignificant) with the point estimate *rising*; **no significant positive trend in any of 23 developed markets 1980–2008**; verbatim, "**Ending the sample in the 1988–1998 decade is key to finding a trend**" `[V]`. CLMX (2023) themselves: "we did not believe that the positive trend would necessarily continue" `[V]` |
| Which stocks carried the rise | **Low-priced and retail-held, not just small.** Brandt et al. Fama–MacBeth standardized coefficients: **Log(Price) −0.277 (t = −20.38)** vs **Log(Size) −0.059 (t = −14.89)** — price ≈5× size, and the size coefficient flips sign across eras while price is stable. Low Price × **High** retail-trading = 0.037 (t = 3.34); Low Price × **Low** retail-trading = −0.001 (t = −0.60), **insignificant** `[V]` |
| The rise was a *composition* effect | **Partly, and firm age is the strongest version.** Fink, Fink, Grullon & Weston (*JFQA* 45(5), 2010, 1253–1278): median age at listing **~40 yrs (early 1960s) → <5 yrs (2000)**; adding AGE makes the linear trend **flip sign and lose significance**; explains "almost two-thirds" of the 1956→2000 rise; their FIRM series correlates **0.993** with CLMX's `[V]`. Brown & Kapadia (*JFE* 84(2), 2007, 358–388): each listing cohort is persistently riskier, and **within any cohort there is no time trend** `[V]`. But Bekaert–Hodrick–Zhang's horse race finds **no compositional variable survives** `[V]` |
| The best-surviving *economic* mechanism | **Growth options.** Cao, Simin & Zhao (*RFS* 21(6), 2008, 2599–2633): adding growth options drives the trend to zero or significantly negative (MABA −3.83, t = −3.16) and lifts adj R² from **0.32 to 0.63**; in rolling 100-month windows the trend is significant in 90 of 217 and growth options kill it in **83 of those 90 (92%)** `[V]`. BHZ's covariance decomposition: **MABA 42%, market volatility 40%, R&D 26%, industry turnover 2%** `[V]`. Competing: Irvine & Pontiff (*RFS* 22(3), 2009) product-market competition, "6% per year", survives BHZ but contributes only 2%; Wei & Zhang (*Journal of Business* 79(1), 2006) ROE, loses to growth options; Xu & Malkiel (*Journal of Business* 76(4), 2003) institutional ownership, whose sign **flips negative for low-priced stocks** in Brandt et al. `[V]` |
| Is any of it a measurement artifact? | **Contested both ways.** Leippold & Svatoň (*Critical Finance Review* 12(1–4), 2023, 171–202): correcting bid-ask-bounce bias removes **17%–62% of the trend and almost all of the reversal** — cutting against CLMX *and* Brandt et al. `[V, abstract only]`. Chiah, Gharghori & Zhong (*CFR* 12(1–4), 2023, 125–170) replicate 1962–97 but find idiosyncratic volatility **decreases** in both 1926–1962 and 1998–2017: "their finding is sample-specific" `[V, abstract only]`. CLMX rebut that closing transaction prices are the right input and that NASDAQ was only ~15% of market cap in the affected window `[V]` |
| The recent *level* of idiosyncratic volatility | **Explained, essentially exactly.** Bartram, Brown & Stulz (NBER WP 24270): age + size + liquidity give predicted EW idiosyncratic risk **27% vs actual 26%**, and predicted = actual = **17%** VW for 2013–2017; market-model R² for 2013–2017 exceeds any year 1963–2006. CLMX (2023) call it "the most thorough recent empirical study" `[V]`. ⚠️ No journal publication located |
| Post-2021 direction of the variance shares | **Genuinely unresolved.** No CLMX-style decomposition exists on 2022–2025 data; the academic series stops at 2021 `[V]`. Practitioner evidence points both ways: top-10 concentration **14% (2014) → 27% (end-2023)** but *lower* than the early 1960s and the 1930s, while realized average pairwise correlation is near multi-decade lows `[S, practitioner sources, not peer reviewed]` |
| CIV carries a robustly negative price of risk | **Contested by its own subsample split** — insignificant 1963–1985 (FF3 α t = −0.75), significant 1986–2010 `[V]`. No published failed replication found, but the sweep was not exhaustive. The Goyal–Santa-Clara / Bali et al. precedent is the cautionary analogue `[V]` |
| Equity correlation matrices are adequately described by equicorrelation | **Contested.** Giller (2025, arXiv:2411.08864) argues an "isotropic" (equicorrelated) model is empirically adequate for the S&P 500 and finds no support for linear factor models `[V]`; the sector-factor literature and RMT say otherwise `[S]`. **Working paper, not peer reviewed** |
| Long memory in log volatility: is `d` ≈0.35–0.55, or below 0.25? | **Unresolved across proxies.** ABDE 2001: d ≈0.35 on log realized s.d. `[V]`; Luciani & Veredas: median 0.55, factor 0.69 `[V]`; Barigozzi & Hallin 2016: ARFIMA d **never reaches 0.25** `[V]`. Different volatility proxies give different answers |
| Was the 2009–2012 high-correlation period a level shift? | **No — a transient excursion.** It mean-reverted by 2013–2017, with multi-decade lows in 2017 and 2024 `[S]`, consistent with the measured ≈2-year mean-reversion time `[V]` |

---

## 4. Which parts of the approach are actually new

**Honestly: one narrow methodological thing, and it is not Ψ itself.**

**NEW (a):** *The ratio.* `Ψ² = (Ledoit–Wolf γ̂) / (p × John's U)`. Both halves have been computed since
2004 and 1971 respectively; nobody appears to have formed the ratio, named it, or plotted it as a time
series for equity markets. `[V — exhaustive OpenAlex/Crossref phrase searches returned nothing]` The
novelty is a **scale-free, N-free, [0,1] normalization**, not new information.

**NEW (b):** *The application to a volatility-dependency matrix.* The equicorrelation-departure question
has been asked only of **return** correlation matrices. Whether `R^v_t` — the correlation of industry
log-volatility innovations — departs from equicorrelation more or less than `R^r_t` does is, as far as
this review can establish, unasked. The gate is right that this is the stronger half of its case.

**NEW (c):** *A calibrated null for pattern persistence in `vec(R − R_eq)` space on an industry panel.*
The two papers that built such nulls (Allez & Bouchaud 2012; Bun, Bouchaud & Potters 2017) built them in
**eigenvector/subspace space**, not in raw off-diagonal space, and on large-N equity panels rather than a
small-N industry panel. Münnix et al. (2012) worked in matrix-distance space but built **no null at all**
and reported persistence only qualitatively. `[V]` **The gap is the null, not the statistic.**

**NEW (d), and this is the one worth having:** *the explicit statement that Ψ is non-monotone in
"structure" under a one-factor model.* §0 items 4–5 and Appendix A show `Ψ → 0` both when loadings become
homogeneous **and** when factor variance explodes. Nothing in the literature states this, because nobody
has used Ψ. It is a derived property of a statistic nobody uses — which is a reason to be careful with the
statistic, not a research contribution.

**That is the whole list.** Everything else below is a reimplementation.

---

## 5. Which parts are just different implementations of existing ideas

| Repo construct | It already is | Citation |
|---|---|---|
| `Ψ_t` | A bounded monotone reparameterization of the **coefficient of variation of the off-diagonal correlations**, `Ψ = CV/√(1+CV²)` | `[D]`, Appendix A |
| `‖R − R_eq‖²_F` (numerator) | Ledoit & Wolf's `γ̂`, the constant-correlation shrinkage target's misspecification term, computed since 2004 | Ledoit & Wolf, *Journal of Portfolio Management* 30(4) (2004), 110–119, Appendices A–B `[V]` |
| `‖R − I‖²_F` (denominator) | `p ×` John's locally-most-powerful-invariant sphericity statistic evaluated at a correlation matrix; also exactly the **eigenvalue dispersion** `Σ_k(λ_k − 1)²` | John, *Biometrika* 58 (1971), 123–127; Nagao, *Ann. Stat.* 1 (1973), 700–709; Ledoit & Wolf, *Ann. Stat.* 30(4) (2002), 1081–1102 `[V]` |
| `ρ̄_t` (mean off-diagonal) | The Frobenius least-squares projection onto the equicorrelation family; **and** the DECO-DCC estimator | Engle & Kelly 2012 Eq. 7 `[V]` |
| `1 − Ψ²` | The uncentered R² of the regression "`r_ij = ρ̄`"; `Ψ = sin θ` of the Frobenius angle between the off-diagonal vector and `1` | `[D]` |
| `c_t = mean_i log σ_it` | HKLVN's `μ_σ,t`, "essentially the first principal component of firm volatilities"; also the CCE cross-sectional-average factor proxy | HKLVN, *JPE* 128(11) (2020) Table 5 `[V]`; Pesaran, *Econometrica* 74(4) (2006) `[S]` |
| `D_it = log σ_it − c_t` | The residual `e_i,t` in `log σ_i,t = a_i + b_i μ_σ,t + e_i,t` under `b_i ≡ 1`. Estimated loadings are 0.73 / 0.92 / 0.96 median, so the restriction is mild | HKLVN 2020 `[V]`; HKLVN Feb-2014 draft `[V]`; Luciani & Veredas 2015 `[V]` |
| `sd_i(D_it)` | HKLVN's `σ_σ,t`, plotted in their Feb-2014 Figure 3 Panel C | `[V]` |
| The two-way structure `log a_i + c_t + D_it` | BBGV's `x_it = a_i φ(z_t) μ_it ε_it`, in logs — **on nine sector index series** | Barigozzi, Brownlees, Gallo & Veredas, *JoE* 182(2) (2014) `[V]` |
| The MKT/IND replication | CLMX 2001, updated by the same authors in NBER WP 29916 (2022) | `[V]` |
| `Σ_i D_it = 0` and rank(Cov(D)) ≤ N−1 | The standard rank deficiency of any within-transformed panel | `[S]` |
| Alternative to Ψ already tried in this repo | The absorption ratio, `AR₁ = [1+(N−1)ρ̄]/N` under equicorrelation — MI-007 | Kritzman, Li, Page & Rigobon (2011) `[S]` |

**A naming hazard, flagged because it will bite.** `Solnik & Roulet (2000), "Dispersion as Cross-Sectional
Correlation," Financial Analysts Journal 56(1), 54–61` already owns the word "dispersion" in this exact
subject area, and it means the **opposite** thing there: dispersion of *returns* used to estimate the
*level* of average correlation. `[V]` Do not call Ψ a dispersion measure without disambiguating.

---

## 6. What genuine research gap remains

**Not "is there structure beyond ρ̄?"** — that was settled in 1966 (King) and has been reconfirmed by RMT
(Plerou et al.: deviating eigenvectors localize on business sectors) and by every sector-factor paper
since. An industry correlation matrix is not equicorrelated. **A test whose null is exact equicorrelation
tests a hypothesis known to be false and will reject it.** Rejecting it is not a finding, and the Stage-0
gate's E1 bar, as registered, is therefore nearly free.

**Not "is there a common factor in sector log-volatility?"** — BBGV measured it on nine sector series:
average pairwise correlation 0.66–0.82, PC1 0.58–0.91. `[V]` It will be there.

**The remaining gap is a three-layer subtraction that nobody has performed on an industry panel:**

> Take the observed departure of the industry correlation matrix from equicorrelation. Subtract, in order:
> **(i)** the sampling floor at the realized `(N, T, ρ̄_t)` — which is large and *moves with ρ̄_t*;
> **(ii)** the departure implied by a **single** factor with the empirically observed loading dispersion —
> which is 0.20–0.48 in Ψ units and *moves inversely with factor variance*; **(iii)** the **static,
> time-invariant** component `d_p = C_p − C̄`, which by itself makes a naive pattern-persistence statistic
> read ≈0.8 forever. **What, if anything, is left, and does it move?**

Layers (i) and (ii) are pure nulls; layer (iii) is what separates "the industry structure is stable and
boring" from "the arrangement reorganizes". **Layer (iii) is the only one that could carry information
this repo does not already have**, and it is exactly what Allez & Bouchaud measured in eigenvector space
(finding real dynamics, ≈2-year mean reversion) and what Münnix et al. gestured at in matrix-distance
space without a null.

**A second, narrower gap:** whether the volatility-dependency matrix `R^v_t` behaves differently from the
return matrix `R^r_t` on all three layers. `R^v` has a structural reason to be more equicorrelated
(everything loads on one common level with loadings near 1 — HKLVN 0.73, Luciani–Veredas median 0.96) and
a structural reason to be less so (BBGV's residual heat-maps show sector clusters that are invisible in
the raw data). `[V]` **Nobody has reported this comparison.** It is small, honest, and answerable.

**Be plain about the size of this.** The gap is methodological, the expected answer is "mostly noise plus
static structure, with a slow-moving remainder consistent with Allez–Bouchaud", and under the repo's
2026-08-06 objective restatement that is a **PASS**, not a disappointment. The write-up should not claim
more.

---

## 7. The smallest experiment that could test the gap

**The smallest experiment is a simulation, not a measurement. It spends no look, because it touches no
market data and has no outcome variable.**

### Experiment S — the three-layer null, in one script

Generate returns from a **one-factor model with the empirically observed loading dispersion and the
empirically observed factor-variance path**, push them through the **identical** pipeline
(21-day realized vol → log → difference → 125/250-day correlation → ρ̄_t, Ψ_t, `vec(R−R_eq)`), and read
off the joint distribution of everything the gate proposes to measure.

Registered outputs, all from simulated data only:

1. **`Ψ_null(ρ̄, T, N)` surface** — the sampling floor. Appendix A gives the closed-form approximation;
   the simulation gives the exact finite-sample version with fat tails.
2. **`Ψ_1factor(c)`** — Ψ under one factor with loading CV `c`, and its path as factor variance moves.
   Appendix A predicts 0.20–0.48 for plausible `c`, falling as factor variance rises.
3. **`Corr(Ψ_t, ρ̄_t)` under the null.** If this already exceeds 0.90 in simulation, **bar E2 is
   unpassable by construction** and the gate must be redrafted before it is signed, not after it fails.
4. **The E4 baseline.** Run the pattern-persistence statistic on a **completely static** non-equicorrelated
   `C` with the empirical loading dispersion. `[INF]` predicts ≈0.75–0.87 flat in `h`. If simulation
   confirms that, E4 as registered is a reliability coefficient and must be replaced.

**Cost: one afternoon. No market data. No look. No preregistration needed** — there is no hypothesis, no
outcome, and nothing for a specification search to search over, on the same footing as the informativeness
map's own no-look argument.

### If Experiment S says the design survives, the smallest *measurement* is Experiment M

Three registered fixes, each with precedent:

- **(A) Normalize by a same-window reliability ceiling.** Split window `t` into two independent halves,
  compute the pattern correlation *within* the window (this estimates `Var(d)/(Var(d)+Var(η))` with zero
  dynamics), and report `E4(h) / E4_split`. Values below 1 measure genuine decay. **This is exactly Allez
  & Bouchaud's `D_emp/D_th` ratio and BBP's "deviation from predicted self-overlap".** `[V]`
- **(B) Demean by the full-sample matrix, not by the window's own `R_eq`.** Define
  `x^t_p = (R_t)_p − C̄_p^{full-sample}`. This removes the static `d_p` by construction, so any surviving
  persistence is genuine time-variation. **This is the version worth pre-registering.** Note it is not
  causal as stated and needs an expanding-window version to satisfy `assert_causal`.
- **(C) Report the `h`-profile, never a point.** The literature's one hard number — the ≈2-year
  mean-reversion time `[V]` — predicts decay visible over `h ≈ 250–750` days and largely complete beyond
  ≈500. **A single `h = W_A` reading cannot distinguish "persistent" from "static".**

**Power warning, and it binds.** Strictly non-overlapping windows at `W_A = 250` leave ~1 observation per
year. Over the usable sample that is a few dozen effective observations, so the standard error on a
correlation is ≈0.13. `[INF]` **Compute the power before running the test, not after.**

### One free, high-value substitution

Replace the ad-hoc Ψ threshold with an **off-the-shelf formal test of `H₀: R = R_eq`**:
**Sattler & Dobler, "Testing for patterns and structures in covariance and correlation matrices,"
arXiv:2310.11799** — a unified nonparametric Wald-type framework explicitly covering compound symmetry,
requiring only finite fourth moments, with a parametric bootstrap for small samples and an extension to
correlation matrices. `[V]` It gives a calibrated p-value where Ψ gives an uncalibrated number.
Report both: the test for "is it rejected", Ψ for "by how much".

---

## 8. Canonical results replicable with the data already on disk

> ### ⚠️ DISCLOSURE — unsanctioned exploratory computation, recorded rather than buried
>
> This review was produced with parallel research agents. **One of them, on its own initiative and
> outside its brief, executed replication code against the on-disk panels** (`industry10_daily.csv`,
> `industry48_daily.csv`, the market series) plus freshly downloaded vendor files. It computed, among
> other things: rolling average pairwise correlations and their crisis-window values, PC1 variance
> shares, Marchenko–Pastur edge counts, Bai–Ng and Ahn–Horenstein factor counts, market-model R² by
> decade, a CLMX MKT/IND reconstruction, and log-realized-volatility moments.
>
> **Nothing it computed has been carried into this document, and no number below is one of its
> outputs.** Every figure in §8 is a *published* target or a coverage fact. Its working files live in a
> session scratchpad **outside the repo** and were not copied in.
>
> **Why this is recorded and not simply dropped.** Under the Stage-0 gate's own separation of claims,
> all of it falls in the "Replication (known answer)" row, which the gate explicitly treats as
> pre-look construction verification and not a spent look — the same footing as
> `results/concentration_gate.csv`. **So the phase's one look is not spent.** But two of the quantities
> it touched — the rolling average pairwise correlation ρ̄_t and the PC1 share — are *also* registered
> redundancy benchmarks in the gate (§The statistic). **Adam should rule on whether that constitutes
> partial sighting of E2's inputs**, and either accept it explicitly or re-scope E2. Silence here would
> recreate exactly the audit gap the ledger's MI-013 row exists to prevent.
>
> One incidental observation it surfaced is worth checking as a *data* question before any research
> question: it reported the 10-industry trailing average pairwise correlation ending at a
> century-low value at the end of the panel. **Treat that as a possible tail-of-file data problem to
> verify during construction, not as a finding.**

**Data actually present** (verified by coverage inspection only — row counts, spans, missing-cell counts):

| File | Shape | Span | Completeness |
|---|---|---|---|
| `data/processed/industry10_daily.csv` | 26,253 × 10 | 1926-07-01 … 2026-05-29 | **zero missing cells** |
| `data/processed/industry48_daily.csv` | 26,253 × 48 | 1926-07-01 … 2026-05-29 | 56,325 missing of 1,260,144; **fully rectangular from 1969-07-01 (14,350 rows, zero missing)** — last starters are Hlth (1969-07), Gold/Guns/Soda/FabPr (1963-07) |
| `data/processed/market_daily.csv` | 26,211 rows | 1926-09-17 … 2026-06-30 | `mkt_ret`, `rf` |
| `data/processed/assets_daily.csv` | — | from 1926-09-17 | market, rf, the ten industry series, `smb`, `hml`, `mom`, bond10, gold |

**Not on disk:** industry market-capitalisation weights, individual-stock returns.

**Two source facts that change the plan, both verified by download this session** `[V]`:

1. **The vendor's DAILY industry files contain only two tables** — value-weighted and equal-weighted
   daily returns. **There is no firm-count or average-firm-size table in the daily zip.** Those live in
   the **monthly** zip (eight tables, monthly 192607–202606). Missing flags are `-99.99` / `-999`.
   Their product **is** a valid industry market capitalisation: the implied Dec-1997 total is **$9.60T**
   against **$9.76T** reconstructed independently (a 1.6% gap explained by two-decimal rounding), and
   cap-weighting the monthly industry returns reproduces the market return to ±0.01–0.43pp across eight
   spot checks. Holding those monthly weights fixed and aggregating **daily** over a test month gives a
   mean absolute error of **1.38 bps/day** — and since CLMX also hold weights fixed within the month,
   monthly-only weights cost nothing. `[V]`
2. **CLMX's own output series are public, CC0, and validate to three decimals.** Harvard Dataverse
   `doi:10.7910/DVN/YSL0TW` — "Replication data for: Have Individual Stocks Become More Volatile?",
   53 files, deposited 2007. Format `year month value`, 426 rows (1962:07–1997:12), **variances NOT
   annualized — multiply by 12**. Verified: `dsig2mt.dat` → 1.542 (paper 1.542 ✓), `dsig2et.dat` → 1.032
   (✓), `dsig2nt.dat` → 6.436 (✓), `edsig2nt.dat` → 33.903 (✓), plus per-industry long-format files
   `dsig2eit.dat` / `dsig2nit.dat` (20,796 rows, industry index 1–49). ⚠️ `wsig2nt.dat` does **not**
   reproduce the weekly FIRM mean (2.867 vs 5.842) — likely a mislabelled member; validate before use.
   `[V]`

**What is and is not recoverable — measured, not argued** `[V]`:

| Component | Recoverable from public data? | Result |
|---|---|---|
| **MKT** | **Yes** | From the daily factor file. vs CLMX 1962:7–1997:12: mean ×12×100 **1.644 vs 1.542**, **ρ = 0.9978**; Oct-87 0.659 vs 0.675; trend 0.161 vs 0.156. The ~7% level gap is the universe difference (CLMX built their own index over all CRSP firms) |
| **IND** | **Yes, with a real caveat** | Cap-weighting the industry series with firm-count × average-firm-size weights gives mean ×12×100 **0.989** (49-scheme) / **0.978** (48-scheme) vs CLMX **1.032** — but **ρ = only 0.828**. Usable as an indicator, **not interchangeable** with CLMX's series |
| **FIRM** | **No** | Irreducibly a within-industry cross-sectional dispersion of individual returns. The beta-free trick eliminates betas, not the need for `R_ijs`. Backing it out by subtraction fails because the left-hand side (cap-weighted average *total* variance of an individual stock, 1962–97 value **9.010×10⁻²** annualized) is itself an individual-stock quantity. VW-vs-EW industry return pairs do **not** identify it |

**Since FIRM is ~72% of total variance, a public-data-only decomposition misses the substance of the
paper.** Say that plainly rather than presenting a two-level decomposition as "CLMX replicated."

### Ranked — cheapest × most diagnostic first

| # | Replication | What it establishes | Data needed | Effort | Checkable against a published number? |
|---|---|---|---|---|---|
| **1** ★ | **Fama & French (1997), "Industry costs of equity," *Journal of Financial Economics* 43, 153–193, Table 2** — regress each of the 48 industry series on the market factor, monthly, 7/1963–12/1994 | **The best pipeline-validation target found in this entire review.** It checks date alignment, excess-return construction, the industry mapping and the factor merge simultaneously, against **48 independent published numbers plus three aggregates** | industry + factor **monthly** files; two small free downloads. Not on disk — the on-disk panels are daily | **~30 min** | **YES, exceptionally.** Mean CAPM adjusted R² = **0.63**; mean 3-factor adjusted R² = **0.68**; mean market beta = **1.11**; rolling 5-year CAPM average 1968–94 = **0.65**. Per-industry values are published for all 48 (lowest **Gold 0.15**; then Coal 0.36, Smoke 0.40, Agric 0.44, Mines 0.45 … highest **BldMt 0.83**). **Tolerance ±0.02 on the mean, ±0.10 per industry** — the industry definitions were rebuilt with later data vintages `[V]` |
| **2** | **`ρ̄_t` crisis spikes** on the 10-industry panel — 1987-10, 2008-09/10, 2020-03 | The fastest proof that dates, alignment, units and sign conventions are right on the **daily** panels actually on disk. A pipeline bug shows up as a spike on the wrong date or no spike at all | on disk | ~1 hour | **Qualitatively yes, quantitatively almost not at all.** **No published, crisis-dated industry average-correlation level was found** for Oct 1987, Sep–Oct 2008 or Mar 2020 `[V — searched, negative result]`. The nearest published moments are Li (2018), PhD thesis, Griffith University, `doi:10.25904/1912/1581`, Table 4.2: equal-weighted average pairwise correlation of the 48 industry series, 1963:7–2015:12, **mean 0.503, sd 0.158, min 0.085, max 0.907, AR(1) 0.599** — a thesis, not refereed, and on a different window. Treat as a **shape** check and say so |
| **3** | **Marchenko–Pastur bulk edge vs the observed spectrum** at N=10 and N=48 over several `T` | That the eigenvalue computation, the standardization and the `q = N/T` bookkeeping are right; and how many industry eigenvalues clear the noise edge at each window | on disk | ~2 hours | **Partly.** The *formula* is exact (Appendix B tabulates λ₊). Laloux et al.'s "≈94% inside the bulk" is for N≈400 individual stocks, **not** for a 10- or 48-industry panel, and an industry panel should show a **much larger** λ₁ share. Do not expect 94% here — the *shape* claim (one huge outlier, a bulk, a few sector modes) is what transfers `[V/INF]` |
| **4** | **Log realized volatility is approximately Gaussian** — the ABDE (2001) stylized fact, computed per industry at monthly frequency from daily returns | Validates the entire decision to work in log-vol space, on which the `c_t`/`D_it` construct rests | on disk | ~1 hour | **YES for the direction, and the monthly-from-daily analogue is itself published.** ABDE: realized **variance** median skew **5.609**, median kurtosis **66.16**; **log realized s.d.** median skew **0.192**, kurtosis **3.885**; raw daily kurtosis **5.416** falling to **3.129** once returns are standardized by realized volatility `[V]`. Their sample is intraday (30 names, 5-min, 1993–98) so the exact moments are **not** reproducible — but ABDE explicitly cite **French, Schwert & Stambaugh (1987), *JFE* 19, 3–29** (open access) for log monthly s.d. built from daily returns being near-Gaussian, which **is** the on-disk construction `[V]`. ⚠️ **A single daily squared return is not a legitimate substitute** — ABDE note its variance is ~20× that of true integrated volatility `[V]` |
| **5** | **Ding, Granger & Engle (1993), *Journal of Empirical Finance* 1, 83–106 — the Taylor effect** | Catches return-scaling and sign errors instantly; validates the volatility estimator and causal windowing | on disk (market series alone suffices) | **~15 min** | **YES.** Sample: S&P 500 daily, 4 Jan 1928 – 30 Aug 1991, **17,054 returns**. The autocorrelation of `\|r\|^d` is maximized at **d = 1 at every lag** — *not* at 1.25, and *not* at 2 (the "Taylor effect": ρ_k(θ) < ρ_k(1) for θ above **or** below 1; FX is the exception at d = ¼). `ρ(\|r\|) > ρ(r²)` at **every** lag, significant out to **~2,500 lags (>10 years)**. **d_GPH = 0.474 (t = 8.15)**; minimum-distance fit 0.358; GARCH(1,1) α+β = **0.997** `[V, via Ding & Granger 1996, *JoE* 73, 185–215 and Granger & Ding 1996, *JoE* 73, 61–77 — DGE itself is closed access]` |
| **6** | **Nelson (1991), *Econometrica* 59, 347–370, Table II — the EGARCH asymmetry parameter** | An exact published point estimate obtainable from a daily market series alone; a second, independent estimator check | on disk | ~1 hour | **YES, to a standard error.** CRSP value-weighted daily, Jul 1962 – Dec 1987, 6,408 observations: **θ̂ = −0.1178 (s.e. 0.0090)**, γ = 0.2053 (0.0123), ν = 1.5763 (0.0320), δ = 0.1831; the news-impact slope ratio `(γ+\|θ\|)/(γ−\|θ\|)` = **3.7×** `[V]` |
| **7** | **Long memory in industry log-volatility** — a GPH estimate of `d` | Validates the volatility estimator and the causal windowing; a look-ahead bug inflates persistence | on disk | ~2 hours | **Range only, because the literature disagrees across proxies.** ABDE: `d` median **0.349** (s.e. 0.074), scaling estimate 0.386 `[V]`; Luciani & Veredas: median **0.55** raw, **0.69** for the common factor `[V]`; Barigozzi & Hallin: **below 0.25** `[V]`. Checks that `d` lands in ≈0.3–0.7, not a point value |
| **8** | **The common factor in industry log-volatility** — PC1 share and average pairwise correlation of the 10 (and 48) industry log-vol series | The direct sector-level analogue of the CIV result; establishes the prior for `c_t` before `c_t` is used | on disk | ~3 hours | **YES, and this is the best-calibrated benchmark available.** BBGV report, on **nine sector series**, average pairwise correlation **0.66–0.82** and PC1 **0.58–0.91** `[V]`. Different sample (2001–08, realized kernels from intraday data) but the same object. **A 10-industry daily panel landing far outside 0.5–0.9 means something is wrong** |
| **9** | **CLMX MKT term** against the authors' own archived series | The single most precisely checkable item in this entire review, and the strongest possible proof the return/date/units pipeline is correct | market series on disk + the Dataverse download | ~3 hours | **YES, to three decimals.** Target: `dsig2mt.dat` mean ×12×100 = **1.542**; an independent public-data reconstruction achieved **1.644 with ρ = 0.9978**, so **ρ > 0.99 is the bar and the ~7% level gap is expected** (universe difference), not a bug `[V]` |
| **10** | **CLMX IND term**, restricted to the two levels the data supports | The gate's own registered first replication. Establishes the variance-additive bookkeeping | industry series on disk; **industry weights must be fetched from the MONTHLY zip** (firm-count × average-firm-size — they are absent from the daily files) | ~1 day incl. the fetch | **Partially, and know the ceiling in advance.** Targets `[V]`: `dsig2et.dat` mean ×12×100 = **1.032** raw / **1.027** ex-crash; **MKT in Oct 1987 = 0.056**; MKT autocorrelations at lags 1/2/3 = **0.494 / 0.383 / 0.313**; **corr(MKT, IND) = 0.645**; Granger p-values **MKT→IND 0.000, IND→MKT 0.548**. Reconstructed weights recover CLMX's Table 4 rank order with all top-10 industries within ~1pp `[V]`. An independent public-data reconstruction reached **0.978–0.989 with ρ = 0.828** — **ρ ≈ 0.83 is the realistic ceiling**, and a much higher value should be treated as suspicious. **Use the 48-industry set, not the 49** `[V]`. FIRM is **out of reach** |
| **11** | **Moskowitz & Grinblatt (1999), *Journal of Finance* 54(4), Table IV — partial autocorrelations of monthly industry returns** | A second, independent check on the monthly aggregation, statable entirely as an autocorrelation | on disk (needs monthly aggregation) | ~30 min | **Yes, qualitatively.** Cross-industry **mean lag-1 partial autocorrelation 0.0868**, decaying to ≈0 by lag 6 (−0.0002 at 6, −0.0001 at 12, −0.0023 at 36); range at lag 1 from −0.0477 to 0.2187. Jul 1966–Jul 1995, 347 months `[V]`. ⚠️ Their 20 industries are custom 2-digit-SIC groups, **not** the vendor's 10 or 48 — expect qualitative agreement only. **Their headline result is a long-short spread and cannot be stated within this repo's boundary; it is dropped, not paraphrased** |
| **12** | **The market-model R² decline** for industry series against the market | The synchronicity/comovement literature's central series | on disk | ~3 hours | **NO — and this is a correction to a plausible-sounding plan.** CLMX's monthly **0.28 → 0.08** and daily **0.12 → 0.02–0.04** are average pairwise correlations among **individual stocks** `[V]`, and **exact R² values exist only in their Figure 5 — there is no table** `[V]`. Morck, Yeung & Yu (2000) report **US R² = 0.021, the lowest of 40 countries** (biweekly 1995, SST-weighted, individual stocks) `[V]` — averaging industry-on-market R² gives an order of magnitude more, because an industry index has already diversified away the variance being measured. **No numeric year-by-year US R² series exists in print at all** — every source is a chart `[V]`. Do not attempt |
| **13** | **Number of factors** (Bai–Ng `IC_p`, Ahn–Horenstein ER/GR) on the industry return panel | Whether the panel's factor count matches the literature | on disk | ~3 hours | **No usable published target.** ⚠️ **Ahn & Horenstein (2013, *Econometrica*) contains no empirical application at all** — the "one factor in stock returns" result is from the **working paper, Table 9** `[V]`. Bai & Ng (2002) §6.1 find **2** (CRSP, T=60, N=4,883); Onatski finds **8**; Connor & Korajczyk (1993) find **1–6**, configuration- and January-dependent `[V]`. **No published estimate exists for an industry panel.** Informative, **not** a pipeline check |
| **14** | **Roll (1988), *Journal of Finance* 43(3), 541–566** | — | needs individual stocks | — | **NOT REPLICABLE.** Recorded because the commonly quoted numbers are wrong: Roll's market index is **equal-weighted**, his "industry" is a bespoke size-matched group of smaller same-SIC firms (not a published index), and all R² are adjusted. Actual values: monthly CAPM **0.179**, APT 0.244, CAPM+industry **0.3438**, daily CAPM **0.16282**, daily APT **0.20532** `[V]`. The famous "0.35" is the CAPM+industry figure on a 96-large-firm subsample, not a market-model R² |
| **15** | **CLMX FIRM term**; **Ang, Hodrick, Xing & Zhang (2006)** idiosyncratic-volatility sorts (5−1 raw **−1.06%/month, t = −3.10**; FF3 α **−1.31, t = −7.00** `[V]`); **CIV** itself; **Pollet & Wilson (2010)**; the **20 → 50** diversification statistic | — | needs individual stocks | — | **NOT REPLICABLE** without CRSP. Say so plainly rather than substituting an industry proxy. The AHXZ sort is substantially a microcap phenomenon (Q1 holds 53.5% of market cap, Q5 only 1.9% `[V]`) and 48 industries give ~10 per quintile. Pollet & Wilson is **doubly blocked** — closed access everywhere *and* needs individual stocks `[V]` |

**Recommended first afternoon: #1, then #5.** #1 gives a near-exact published match against 48 independent
numbers in about thirty minutes and is the strongest single proof the panel ingest is correct; #5 costs
fifteen minutes and catches return-scaling and sign errors immediately. **#9 is the most decisive test of
the daily pipeline** — a three-decimal target from the original authors' own CC0 files. **#8 is the
highest-information single run** and should follow, because it sets the prior for everything the phase
does afterwards.

> **Reliability caveat on this section, from the research thread's own final self-audit.** The agent that
> assembled these candidates reported on its last pass that it had earlier announced results which never
> actually arrived in its context, and that it did **not** confirm the published figures for **Ding,
> Granger & Engle (1993), Christie (1982), Glosten–Jagannathan–Runkle (1993), Nelson (1991), Laloux et
> al. (1999), Plerou et al. (2002), Pollet & Wilson (2010) or Ang & Chen (2002)** against primary text.
> **The citations are right; the specific numbers in rows 5, 6, 11 and in the corrections below are
> therefore `[S]`, not `[V]` — confirm each against the paper before using it as a replication target.**
> What *is* independently double-sourced: the **CLMX** figures (two threads each decoded the primary
> PDF), the **Fama–French (1997) Table 2** targets (extracted and then matched to 0.004 by an executed
> regression), **Roll (1988)** and **Morck–Yeung–Yu (2000)** (read from primary), and the **ABDE (2001)**
> moments (verified independently by the volatility thread).

**Corrections to plausible-sounding priors, recorded so they are not re-derived** (`[S]` unless noted):
Ding–Granger–Engle's maximizing exponent is **d = 1**, not 1.25 or 2 · **Christie's (1982) leverage
elasticity is disputed between the two research threads** — one sourced a cross-sectional **mean of
−0.23 with average t = −1.01** (379 stocks, 1962–78, quarterly) and argued the widely quoted −1.5 is a
CEV exponent on the price *level*, a different object; the other reported the conventional −1.5 to −2.
**Resolve against the primary paper before quoting either** · Roll's "news days" finding is that
**23.7% of daily observations were excluded and R² barely moved while residual kurtosis fell 20.457 →
7.750**, not a statement about what fraction of large moves had news (that is Cutler, Poterba &
Summers) · Ahn–Horenstein (2013) has **no empirical section** ·
Morck–Yeung–Yu is **biweekly and SST-weighted**, not simple-averaged weekly · Glosten–Jagannathan–Runkle's
indicator is on **positive** residuals, so the modern asymmetry parameter is **−g₂** (their Model 4:
g₁ = 0.153 [2.590], g₂ = **−0.227** [−3.570]).

**Do not describe any of these as a signal reading.** Every one is construction verification under the
gate's own §Replication-before-research heading.

---

## 9. Consequences for the Stage-0 gate as currently drafted

Recorded as findings for Adam's ruling, not as edits. The gate is **UNSIGNED**, so this is the moment.

1. **H₀ is too weak.** "R_t = R_eq(ρ̄_t) at every t" will be rejected by a one-factor world with dispersed
   loadings (Ψ ≈ 0.20–0.48 in population, Appendix A) and by an industry cross-section known to be
   non-equicorrelated since King (1966). **Recommend: replace with a one-factor null carrying the
   empirical loading dispersion.** E1 as written is nearly free.
2. **E2 is threatened from the null side, not only by redundancy.** `Ψ_null` falls monotonically in ρ̄
   (0.395 → 0.095 as ρ̄ goes 0.2 → 0.6 at T=125, Appendix A). A strong negative `Spearman(Ψ_t, ρ̄_t)` is
   the *expected* result under the null. **Recommend: state the sign and magnitude expected under H₀
   before the look, so a mechanical relation is not read as redundancy or as a finding.**
3. **E4 does not test pattern persistence.** It converges to `Var(d)/(Var(d)+Var(η))` ≈ 0.75–0.87 and is
   **flat in h** under a completely static matrix `[INF, checkable in simulation]`. **Recommend: adopt fix
   (A) or (B) from §7 and report the `h`-profile, not a point.** As written, E4 will pass and the pass
   will mean nothing — a worse outcome than failing.
4. **The Marchenko–Pastur figure quoted in the gate is slightly off.** At N=10, T=125, `(1+√q)² =
   **1.646**`, not 1.60. Appendix B tabulates the exact values for every (N, T) the phase might use.
5. **`W_A` may be too short for the phenomenon.** Allez & Bouchaud measure a ≈2-year (≈500-day)
   mean-reversion time for genuine correlation-matrix dynamics `[V]`. The registered 125/250-day windows
   are shorter than the dynamics being estimated. **Recommend: record this as a registered scope
   limitation alongside the existing quarterly-resolution note**, rather than reopening window choice
   (window-shopping is correctly closed).
6. **`Σ_i D_it = 0` and rank ≤ N−1 are already correctly flagged as non-findings.** Add that
   `Var(D)` is *also* mechanically inflated by realized-volatility measurement error: at a 21-day window,
   `Var(log RV) ≈ 2/n = 0.095`, i.e. **sd ≈ 0.31 per observation**, and that error is **positively
   correlated across industries** because they share calendar days. `[INF]` This can dominate at N=48.
7. **Prior art must be cited in the charter, not discovered after.** `c_t`/`D_it` is HKLVN *JPE* 2020
   Table 5 and BBGV *JoE* 2014; Ψ's numerator is Ledoit & Wolf (2004); Ψ's denominator is John (1971).
   The gate's G5 already says "expect confirmation, not discovery" — **these citations are what makes
   that statement concrete.**
8. **The gate's "Charter-first status: clean" line is stale, and that matters for its own discipline.**
   The gate states "Nothing implemented. No `scripts/` module exists." As of this review, **untracked
   `scripts/cross_section.py` (6.3 KB) and `tests/test_cross_section.py` (8.3 KB) are present in the
   working tree**, both timestamped shortly before the gate document itself. The module's own docstring
   is disciplined — it declares itself construction-only, carries the interpretation limit verbatim, and
   states that no empirical result has been computed from it — so this is a bookkeeping discrepancy, not
   a violation. **But an unsigned gate that says "nothing is implemented" while an implementation sits
   beside it is exactly the auditability failure the MI-013 row exists to name.** Update the line before
   signing.
9. **The strongest defensible novelty claim against MI-007 is now available and should be recorded.**
   `λ₁ ≥ 1 + (N−1)ρ̄` with equality iff all row sums are equal `[V]` ⇒ the absorption ratio **cannot**
   distinguish equicorrelation from any equal-row-sum matrix, while Ψ can. That is the honest,
   citable reason F2 ("it is the absorption ratio in a fourth costume") does not automatically fire.

---

## Appendix A — the Ψ algebra, derived and checkable

**A.1 Ψ is a monotone transform of the coefficient of variation of the off-diagonal correlations.**

`R − R_eq` has zero diagonal (both have unit diagonal) and off-diagonal `r_ij − ρ̄`. `R − I` has zero
diagonal and off-diagonal `r_ij`. With `M = N(N−1)/2` pairs, `m = ρ̄`, and `s²` the divide-by-count
variance of the off-diagonal entries:

```
‖R − R_eq‖²_F = 2 M s²          ‖R − I‖²_F = 2 M (s² + m²)

    Ψ² = s² / (s² + m²)  =  CV² / (1 + CV²),        CV = s/|m|
    Ψ  = CV / √(1 + CV²)        CV = Ψ / √(1 − Ψ²)
```

Equivalently `Ψ = sin θ` where θ is the angle between the off-diagonal vector and the all-ones direction,
and **`1 − Ψ²` is the uncentered R² of the regression "`r_ij = ρ̄`"**. `ρ̄` is the Frobenius least-squares
projection coefficient onto the equicorrelation family (verified numerically by an agent this session).

**Consequence.** Ψ is a function of the first two cross-sectional moments of the pairwise correlations and
**nothing else**. It is invariant to any permutation of the series. **It carries zero information about
which pairs deviate.** Only a `vec(R − R_eq)`-space statistic touches arrangement.

**Pythagorean form** (`⟨R−R_eq, R_eq−I⟩_F = ρ̄ Σ_{i≠j}(r_ij − ρ̄) = 0`):

```
‖R − I‖²_F = ‖R − R_eq‖²_F + N(N−1) ρ̄²
```

**Eigenvalue form** (since `tr R = N`, `‖R − I‖²_F = Σ_k (λ_k − 1)² = N·Var(λ)`):

```
Ψ² = 1 − (N−1) ρ̄² / Var(λ)
```

**A.2 The sampling floor, and its dependence on ρ̄.** Using `sd(r̂_ij) ≈ (1 − ρ²)/√T`, so that under exact
equicorrelation `s ≈ sd(r̂)`:

| ρ̄ | T=125: sd(r̂) | **Ψ_null** | T=250: sd(r̂) | **Ψ_null** |
|---|---|---|---|---|
| 0.2 | 0.0859 | **0.395** | 0.0607 | **0.290** |
| 0.3 | 0.0814 | **0.262** | 0.0576 | **0.188** |
| 0.4 | 0.0751 | **0.185** | 0.0531 | **0.132** |
| 0.5 | 0.0671 | **0.133** | 0.0474 | **0.094** |
| 0.6 | 0.0572 | **0.095** | 0.0405 | **0.067** |
| 0.7 | 0.0456 | **0.065** | 0.0323 | **0.046** |

**Ψ_null is strongly decreasing in ρ̄.** Since ρ̄_t moves over a wide range through time, Ψ_t inherits a
mechanical negative relation to ρ̄_t before any real structure exists. Independently: Ledoit & Wolf (2002)
show the un-normalized denominator needs an `(n,p)` bias correction of the form
`W = (1/p)tr[(S−I)²] − (p/n)[(1/p)tr S]² + p/n`; **Ψ → 1 mechanically as `T/N → 0`** because the numerator
absorbs all the sampling noise while the denominator absorbs noise plus a noise-free `N(N−1)ρ̄²` term. `[V]`

**A.3 A pure one-factor model gives Ψ ≫ 0, and Ψ falls as factor variance rises.**

Under `r_i = β_i f + e_i` with independent `e`, let `b_i = corr(r_i, f) = β_i σ_f / σ_i ∈ (0,1)`, so
`b_i² = R²_i`. Then for `i ≠ j`, **`r_ij = b_i b_j`** exactly, and `R = bb' + diag(1 − b_i²)` — the common
part is **rank one**. With `b` iid across `i`, mean `μ`, variance `v`:

```
m = μ²        s² = (μ² + v)² − μ⁴ = 2μ²v + v²
Ψ² = (2μ²v + v²) / (2μ²v + v² + μ⁴)
```

Equivalently, writing `b_i = b̄(1 + u_i)` with `Var(u) = c²`: `CV ≈ √2 · c`, so **`Ψ ≈ √2 c / √(1 + 2c²)`
— the CV of the pairwise correlations is ≈ √2 × the CV of the loadings, independent of the level.**

| μ = E[b] | sd(b) | **Ψ under ONE factor** |
|---|---|---|
| 0.8 | 0.10 | **0.175** |
| 0.7 | 0.10 | **0.199** |
| 0.6 | 0.10 | **0.231** |
| 0.6 | 0.15 | **0.338** |
| 0.5 | 0.15 | **0.398** |
| 0.4 | 0.15 | **0.481** |

**Ψ > 0 measures loading heterogeneity, not factor count.**

**Counter-cyclicality.** With `κ_i = β_i²/σ²_ei`, `b_i² = κ_i σ²_f / (1 + κ_i σ²_f)`, so every `b_i` is
strictly increasing in `σ²_f`. As `σ²_f → ∞`, all `b_i → 1`, so all `r_ij → 1`, so `R → J`, **which is
equicorrelated: Ψ → 0**. As `σ²_f → 0`, `ρ̄ → 0` and `Ψ → 1`. **Under a constant-parameter one-factor
model Ψ_t is a deterministic decreasing function of factor variance.** Ψ falling in 1987-10, 2008-10 or
2020-03 is the null, fully explained without any regime, contagion or structural change. This is the
Ψ-space image of the Forbes–Rigobon bias.

**A.4 Why E4 as registered reads ≈0.8 on a static matrix.** Write `(R_t)_p = C_p + e_{t,p}`. Subtracting
the window's own mean gives `x^t_p = (C_p − C̄) + (e_{t,p} − ē_t) ≡ d_p + η_{t,p}`, where **`d_p` is
time-invariant**. At non-overlapping `h`, `η_t ⊥ η_{t+h}`, so

```
E[ corr(x^t, x^{t+h}) ] ≈ Var_p(d) / ( Var_p(d) + Var(η) )
```

— strictly positive and **flat in h**. With plausible `sd_p(C)`: ≈**0.75** (N=10,T=125), ≈**0.86**
(N=10,T=250), ≈**0.77** (N=48,T=125), ≈**0.87** (N=48,T=250). `[INF — confirm in simulation before
relying on it.]` **It is a reliability coefficient, not a persistence coefficient.**

---

## Appendix B — Marchenko–Pastur edges for the panels on disk

`λ± = (1 ± √q)²`, `q = N/T`. Computed, not quoted.

| N | T=21 | T=63 | T=125 | T=250 | T=500 | T=1260 | T=2520 |
|---|---|---|---|---|---|---|---|
| **10** | 2.856 | 1.956 | **1.646** | **1.440** | 1.303 | 1.186 | 1.130 |
| **48** | *singular* | 3.508 | **2.623** | **2.068** | 1.716 | 1.428 | 1.295 |
| **49** | *singular* | 3.542 | 2.644 | 2.081 | 1.724 | 1.433 | 1.298 |

Lower edges `λ−`: N=10 — 0.514 (T=125), 0.640 (T=250). N=48 — 0.145 (T=125), 0.316 (T=250), 0.016 (T=63).

`N > T` ⇒ the sample correlation matrix is **singular**: N=48 or 49 with a 21-day window is not estimable
at all. At N=48, T=63, `λ+ = 3.51` and `λ− = 0.016` — the bulk fills almost the whole range and nothing
but the market mode is distinguishable.

**BBP recoverability threshold** (Bun, Bouchaud & Potters 2017): an eigenvector is recoverable only if its
eigenvalue exceeds `1 + √q` — **1.28** at (N=10, T=125), **1.20** at (N=10, T=250), **1.62** at (N=48,
T=125), **1.44** at (N=48, T=250). `[V for the threshold; values computed here]`

---

## Appendix C — bibliography, grouped

**Variance decomposition across levels**
Campbell, Lettau, Malkiel & Xu (2001), *Journal of Finance* 56(1), 1–43 (NBER WP 7590; replication data
Harvard Dataverse `doi:10.7910/DVN/YSL0TW`, CC0) · Campbell, Lettau, Malkiel & Xu (2023), "Idiosyncratic
Equity Risk Two Decades Later," *Critical Finance Review* 12(1–4), 203–223 (NBER WP 29916) · Vogelsang
(1998), *Econometrica* 66(1), 123–148 (the PS₁ trend test) · Bunzel & Vogelsang (2005) (the t‑DAN
variant) · Fama & French (1997), *Journal of Financial Economics* 43, 153–193 (the 48-industry scheme) ·
Brandt, Brav, Graham & Kumar (2010), *Review of Financial Studies* 23(2), 863–899 · Bekaert, Hodrick &
Zhang (2012), *Journal of Financial and Quantitative Analysis* 47(6), 1155–1185 · Brown & Kapadia (2007),
*Journal of Financial Economics* 84(2), 358–388 · Cao, Simin & Zhao (2008), *RFS* 21(6), 2599–2633 ·
Irvine & Pontiff (2009), *RFS* 22(3), 1149–1177 · Fink, Fink, Grullon & Weston (2010), *JFQA* 45(5),
1253–1278 · Xu & Malkiel (2003), *Journal of Business* 76(4), 613–644 · Wei & Zhang (2006), *Journal of
Business* 79(1), 259–292 · Bennett, Sias & Starks (2003), *RFS* 16(4), 1203–1238 · Zhang (2010), *JFQA*
45(3), 663–684 · Rajgopal & Venkatachalam (2011), *Journal of Accounting and Economics* 51(1–2), 1–20 ·
Guo & Savickas (2006), *JBES* 24(1), 43–56 · Guo & Savickas (2008), *RFS* 21(3), 1259–1296 · Leippold &
Svatoň (2023), *Critical Finance Review* 12(1–4), 171–202 · Chiah, Gharghori & Zhong (2023), *Critical
Finance Review* 12(1–4), 125–170 · Bartram, Brown & Stulz (2018), NBER Working Paper 24270 · Comin &
Philippon (2005), *NBER Macroeconomics Annual* 20, 167–201 · Gaspar & Massa (2006), *Journal of Business*
79(6), 3125–3152

**Common factors in volatility**
Herskovic, Kelly, Lustig & Van Nieuwerburgh (2016), *Journal of Financial Economics* 119(2), 249–283 ·
Herskovic, Kelly, Lustig & Van Nieuwerburgh (2020), *Journal of Political Economy* 128(11), 4097–4162 ·
Bekaert, Hodrick, Wang & Zhang (2025), *Management Science* 71(3), 2216–2244 · Barigozzi, Brownlees,
Gallo & Veredas (2014), *Journal of Econometrics* 182(2), 364–384 · Luciani & Veredas (2015), *Journal of
Forecasting* 34(3), 163–176 · Barigozzi & Hallin (2016), *Econometrics Journal* 19(1), C33–C60 · Barigozzi
& Hallin (2017), *Journal of Econometrics* 201(2), 307–321 · Barigozzi & Hallin (2020), *Journal of
Econometrics* 216(1), 4–34 · Barigozzi & Hallin (2017), *Journal of the Royal Statistical Society C* 66(3),
581–605 · Connor, Korajczyk & Linton (2006), *Journal of Econometrics* 132(1), 231–255 · Engle & Marcucci
(2006), *Journal of Econometrics* 132(1), 7–42 · Engle & Rangel (2008), *Review of Financial Studies*
21(3), 1187–1222 · Engle, Ghysels & Sohn (2013), *Review of Economics and Statistics* 95(3), 776–797 ·
Andersen, Bollerslev, Diebold & Ebens (2001), *Journal of Financial Economics* 61(1), 43–76 · Andersen,
Bollerslev, Diebold & Labys (2003), *Econometrica* 71(2), 579–625 · Goyal & Santa-Clara (2003), *Journal of
Finance* 58(3), 975–1007 · Bali, Cakici, Yan & Zhang (2005), *Journal of Finance* 60(2), 905–929

**Factor structure and the number of factors**
Chamberlain & Rothschild (1983), *Econometrica* 51(5), 1281–1304 · Connor & Korajczyk (1993), *Journal of
Finance* 48(4), 1263–1291 · Bai & Ng (2002), *Econometrica* 70(1), 191–221 · Onatski (2009),
*Econometrica* 77(5), 1447–1479 · Ahn & Horenstein (2013), *Econometrica* 81(3), 1203–1227 · Pesaran
(2006), *Econometrica* 74(4), 967–1012 · Bai (2009), *Econometrica*

**Hierarchical / block decompositions**
Moench, Ng & Potter (2013), *Review of Economics and Statistics* 95(5), 1811–1817 · Kose, Otrok &
Whiteman (2003), *American Economic Review* 93(4), 1216–1239 · Diebold & Yılmaz (2009), *Economic Journal*
119(534), 158–171 · Diebold & Yılmaz (2012), *International Journal of Forecasting* 28(1), 57–66 · Diebold
& Yılmaz (2014), *Journal of Econometrics* 182(1), 119–134 · Billio, Getmansky, Lo & Pelizzon (2012),
*Journal of Financial Economics* 104(3), 535–559 · Barigozzi & Brownlees (2019), *Journal of Applied
Econometrics* 34(3), 347–364

**Random matrix theory**
Marchenko & Pastur (1967) · Laloux, Cizeau, Bouchaud & Potters (1999), *Physical Review Letters* 83(7),
1467–1470 · Plerou, Gopikrishnan, Rosenow, Amaral & Stanley (1999), *PRL* 83, 1471 · Plerou et al. (2002),
*Physical Review E* 65, 066126 · Johnstone (2001), *Annals of Statistics* 29(2), 295–327 · Baik, Ben Arous
& Péché (2005) · Paul (2007) · Ledoit & Péché (2011), *Probability Theory and Related Fields* 151,
233–264 · Bun, Bouchaud & Potters (2017), *Physics Reports* 666, 1–109 · Allez & Bouchaud (2012), *New
Journal of Physics* 14, 013023 · Münnix et al. (2012), *Scientific Reports* 2:644 · Onnela, Chakraborti,
Kaski, Kertész & Kanto (2003), *Physical Review E* 68, 056110 · Fenn, Porter, Williams, McDonald, Johnson
& Jones (2011), *Physical Review E* 84, 026109

**Equicorrelation, correlation structure and its tests**
Engle & Kelly (2012), *Journal of Business & Economic Statistics* 30(2), 212–228 · Wilks (1946), *Annals
of Mathematical Statistics* 17, 257–281 · Votaw (1948), *Ann. Math. Statist.* 19, 447–473 · Anderson
(2003), *An Introduction to Multivariate Statistical Analysis*, 3rd ed., Ch. 10 · Lawley (1963), *Ann.
Math. Statist.* 34(1), 149–151 · Mauchly (1940), *Ann. Math. Statist.* 11, 204–209 · John (1971),
*Biometrika* 58, 123–127 · John (1972), *Biometrika* 59, 169–173 · Nagao (1973), *Annals of Statistics* 1,
700–709 · Ledoit & Wolf (2002), *Annals of Statistics* 30(4), 1081–1102 · Ledoit & Wolf (2003), *Journal
of Empirical Finance* 10(5), 603–621 (single-index target) · Ledoit & Wolf (2004), *Journal of Portfolio
Management* 30(4), 110–119 (**constant-correlation target — the γ̂ citation**) · Sattler & Dobler,
arXiv:2310.11799 · Herdin, Czink, Özçelik & Bonek (2005), *IEEE VTC2005-Spring*, vol. 1, 136–140 · Giller
(2024/25), arXiv:2411.08864 (working paper)

**Time-varying correlation**
Forbes & Rigobon (2002), *Journal of Finance* 57(5), 2223–2261 · Loretan & English (2000), Federal Reserve
Board IFDP 658 · Boyer, Gibson & Loretan (1999), IFDP 597 · Corsetti, Pericoli & Sbracia (2005), *Journal
of International Money and Finance* 24(8), 1177–1199 · Longin & Solnik (1995), *JIMF* 14(1), 3–26 · Longin
& Solnik (2001), *Journal of Finance* 56(2), 649–676 · Ang & Chen (2002), *Journal of Financial Economics*
63(3), 443–494 · Ang & Bekaert (2002), *Review of Financial Studies* 15(4), 1137–1187 · Engle (2002),
*JBES* 20(3), 339–350 · Cappiello, Engle & Sheppard (2006), *Journal of Financial Econometrics* 4(4),
537–572 · Pollet & Wilson (2010), *Journal of Financial Economics* 96(3), 364–380 · Krishnan, Petkova &
Ritchken (2009), *Journal of Empirical Finance* 16(3), 353–367 · Driessen, Maenhout & Vilkov (2009),
*Journal of Finance* 64(3), 1377–1406 · Solnik & Roulet (2000), *Financial Analysts Journal* 56(1), 54–61 ·
Kritzman, Li, Page & Rigobon (2011), *Journal of Portfolio Management* 37(4), 112–126

**Sector/industry factors and granular origins**
King (1966), *Journal of Business* 39(1), 139–190 · Roll (1992), *Journal of Finance* 47(1), 3–41 ·
Heston & Rouwenhorst (1994), *Journal of Financial Economics* 36(1), 3–27 · Fama & French (1997),
*Journal of Financial Economics* 43(2), 153–193 · Gabaix (2011), *Econometrica* 79(3), 733–772 ·
Acemoglu, Carvalho, Ozdaglar & Tahbaz-Salehi (2012), *Econometrica* 80(5), 1977–2016 · Morck, Yeung & Yu
(2000), *Journal of Financial Economics* 58 · Ding, Granger & Engle (1993), *Journal of Empirical Finance*
1, 83–106 · Bekaert & Wu (2000), *Review of Financial Studies* 13

**Overlapping-window inference (for any Ψ_t autocorrelation claim)**
Working (1960), *Econometrica* 28(4), 916–918 · Hansen & Hodrick (1980), *Journal of Political Economy*
88(5), 829–853 · Newey & West (1987), *Econometrica* 55(3), 703–708 · Richardson & Stock (1989), *Journal
of Financial Economics* 25(2), 323–348 · Valkanov (2003), *JFE* 68(2), 201–232 · Boudoukh, Richardson &
Whitelaw (2008), *Review of Financial Studies* 21(4), 1577–1605

---

## Open items this review could not close

1. **The published JFE 2016 Table 1 specification — logs or levels?** Three drafts of the CIV paper
   disagree; the published 5.4% headline matches the levels draft, while the authors' own 2020 paper
   describes the 2016 result as being about "log firm variance." This determines whether `c_t` is "the
   CIV factor in logs" or a variant. **Five-minute check, highest value of anything on this list.**
2. **CLMX Figure 5's exact R² values.** They exist only in the figure; there is no table `[V]`. The
   0.28 → 0.08 path is the *correlation* series, and the R² panel is "almost indistinguishable" from it.
   Do not quote an R² number as if it were tabulated.
3. **Moench, Ng & Potter (2013) specifics** — model equations, estimation method, applied panel, and
   whether they report variance shares by level. The dedicated agent did not return; §1.6 is `[S]` only.
4. **The entire random-matrix thread failed to deliver.** A dedicated agent was dispatched for
   Marchenko–Pastur, Laloux et al., Plerou et al., Bai–Ng, Onatski, Ahn–Horenstein, Chamberlain–
   Rothschild and Moench–Ng–Potter, and **completed three times without its findings ever arriving**.
   §1.2, §1.3 and §1.6 are therefore the thinnest sections in this review and rest largely on `[S]`.
   **Re-run that thread before the charter is written.** Specifically unclosed: Laloux et al.'s "% inside
   the band"; Plerou et al.'s deviating-eigenvalue counts by (N, T); the exact Bai–Ng penalty functions;
   whether Ahn & Horenstein (2013) really has no empirical section; and all of Moench, Ng & Potter.
5. **Brandt et al.'s decade-average units** — described as annualized standard deviation but inconsistent
   with CLMX's own levels; likely annualized variance ×100. Resolve before using as a target.
6. **CLMX's "14 positive / 7 negative" industry IND trends** — read directly from the working paper; one
   secondary source says 16/12. Unresolved.
7. **Onnela et al. (2003)** edge-survival numbers (PDF not text-extractable).
8. **Barigozzi & Brownlees (2019) NETS** — entirely unverified; the fetch was blocked.
9. Whether any **international industry sorts** exist on the vendor source — this fixes the phase's
   maturity ceiling and is item 3 in the gate's own open list.
