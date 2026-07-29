---
title: Research decision — continuous-time latent state with jumps
status: FROZEN 2026-07-22 — §8 prereg frozen per Adam's §8.9 sign-off; do not edit hypothesis, event definition, threshold, vol model, or ladder after this date; declared the FINAL preregistered experiment of the current research program
depends_on: RESEARCH-RECORD.md (Belief Revision; Continuum Turn; Chapters 1–3), .planning/COVARIANCE-CONDITIONING-PREREG.md, .planning/STOCKBOND-MACRO-PREREG.md
approved_by: Adam, 2026-07-22 (direction + leverage rung; §8.9 freeze sign-off same day)
---

# Research decision: continuous latent state with jumps

## 0. The decision, up front

1. **Reject the proposal in its literal form** — fitting a latent jump-diffusion
   $dX_t = \mu(X_t)dt + \sigma(X_t)dW_t + J_t dN_t$ to the daily feature panel — for two
   independent reasons:
   - **(a) The continuous-state half has already been run and returned null.** The Continuum
     Turn established descriptively that the latent object *is* a continuous 2-D coordinate
     (PR 1.88, silhouette 0.19, GMM BIC never minimizes). The continuous coordinate was then
     tested as an information source — `representation_information.py` (Z_t: 21d ΔR² = −0.040,
     p = 0.53) and `stage2_conditioning.py` (EWMA env coordinate: ΔR² ≤ 0) — and added nothing
     beyond raw observables for vol targets. "Go continuous" alone is a fourth null waiting to
     happen.
   - **(b) The jump half is not identifiable at daily frequency.** Separating genuine
     discontinuities from heavy-tailed diffusion or fast/rough volatility requires infill
     (intraday) asymptotics (§2). On daily data, "jump" is a semantic choice, not an empirical
     finding.
2. **Accept the one component that is new and testable**: option D of the taxonomy —
   a **state/history-dependent tail-event intensity** — reduced to its honest daily-frequency
   content:
   > *After conditioning on the strongest honest volatility model, do extreme-move arrivals
   > still cluster, and are they predictable from event history?*
   This clears the standing orthogonality gate **by construction**: events are defined on
   vol-standardized residuals, so any signal is orthogonal to the vol axis by design.
3. **Recommended model**: a discrete-time self-exciting hazard model (Hawkes-GLM /
   autoregressive conditional hazard) for tail-event arrival, benchmarked against a
   vol-calibrated hazard ladder. Not a latent SDE, not Bates SVJ, not a neural SDE (§3, §5).
4. **MVE** (§8 — direction approved 2026-07-22; freeze pending §8.9): S&P daily 1950→2026
   (events from 1960), ~420–580 left-tail events across ~10 distinct crisis episodes — an
   order of magnitude better replication count than Chapter 2's ~2 stock-bond transitions.
   ~2–3 sessions of work, all data already available. Per Adam's revision, the hazard ladder
   contains an explicit leverage-aware rung (B_lev) below the self-excitation comparison.
5. **If the MVE fails**, the negative closes the continuous-time/jump reframing at daily
   frequency and becomes Chapter 4 of the methods/negative paper — strengthening the
   three-chapter arc, not padding it.

---

## 1. Conceptual diagnosis — what the HMM actually failed at

### 1.1 The measurability argument (why representation cannot create information)

Any filtered latent state is a function of the observables:
$\hat{Z}_t = E[Z_t \mid Y_{1:t}] = f_\theta(Y_{1:t})$.
It is measurable with respect to the observation filtration $\mathcal{F}_t^Y$. Comparing
`Y ~ X_rich + Ẑ` against `Y ~ X_rich` therefore never tests "does latent information exist" —
it tests **whether the filter is better feature engineering of the past than the baseline
features already are**. A filter can win only through its inductive bias (imposing dynamics
that regularize better than raw features in finite samples), never by accessing information
the observables don't carry.

This is the single most important lens on the whole program, and it applies with full force
to the new proposal: a latent jump-diffusion filtered on the same daily panel produces
$\hat{X}_t = g_\theta(Y_{1:t})$ — a different compression of the same filtration. Swapping
HMM → SDE changes the smoother, not the information set.

### 1.2 Adjudicating the five candidate explanations against the record

| Candidate explanation | Verdict | Evidence |
|---|---|---|
| 1. Latent structure carries no incremental info | **Supported, for vol-level targets** | ΔR² → 0 as baseline enriched (redundancy signature); phase-randomized surrogate indistinguishable from Z |
| 2. Wrong features | **Mostly rejected** | Feature search: every candidate collapses onto the vol axis; vol ladder recovers with zero vol inputs (overdetermined) |
| 3. Discrete representation inappropriate | **Supported — but already diagnosed AND repaired** | Continuum finding; filter horserace (discretization discards ~half the predictive signal) |
| 4. HMM compresses continuous info into artificial states | **Supported — same evidence as 3** | corr(Z_t, X_{t+1}) = 0.38 < corr(X_t, X_{t+1}) = 0.71 |
| 5. Structure lives in a different mathematical object | **The only live branch** | Untested objects named at Chapter-3 closure: tail dependence / tail dynamics, dynamic factor loadings |

The critical subtlety: explanations 3–4 are *true* but **already priced into the nulls**.
The continuous repair was built (Z_t, then the EWMA env coordinate) and still added nothing
for vol targets. So the discreteness critique explains why the HMM was a *bad estimator*
(losing half the signal to gridding), not why there was *nothing incremental to find*. The
failure was informational, not representational.

**Consequence for the new proposal:** its continuous-evolution half is correct but exhausted;
its only untested content is the **jump/intensity mechanism**, and only against a target
*off the vol-level axis* — tail-event arrival, not conditional variance.

### 1.3 Where the intuition survives

The narrative "gradual drift → rising fragility → jump → new state" contains one claim no
prior experiment touched: that **crash arrival has its own dynamics beyond the volatility
level** — that fragility is a second axis, partially decoupled from σ_t. That claim is
testable on daily data (§2.3) and is portfolio-relevant through a channel (tail sizing,
drawdown control) distinct from the saturated vol-forecasting channel. It also happens to be
the univariate version of "tail dependence," one of the two strongest untested objects named
at the Chapter-3 closure — the recommendation converges from two independent directions.

---

## 2. Jumps at daily frequency — the identification problem

### 2.1 What "jump" means mathematically

For a semimartingale price process, quadratic variation decomposes as
$$[X]_t = \underbrace{\int_0^t \sigma_s^2\, ds}_{\text{continuous}} + \underbrace{\sum_{s \le t} (\Delta X_s)^2}_{\text{jumps}}.$$
The entire modern jump-detection literature identifies the two terms by sampling *within*
the day: realized variance $RV = \sum r_i^2$ estimates the total, **bipower variation**
$BV = \frac{\pi}{2}\sum |r_i||r_{i-1}|$ estimates the continuous part only (a jump enters one
$|r_i|$ but is multiplied by a normal-sized neighbor, so its contribution vanishes as
$\Delta \to 0$), and $JV = \max(RV - BV, 0)$ estimates the jump part. Standard-literature
names: Barndorff-Nielsen–Shephard test (2004/2006), Aït-Sahalia–Jacod power-variation test
(2009), Lee–Mykland local test (2008). All are **infill asymptotics** — they need intraday
data.

### 2.2 Why daily data cannot answer the literal question

At Δ = 1 day, the following are observationally near-equivalent on realistic sample sizes:
a compound-Poisson jump component; a heavy-tailed (Student-t / Lévy) diffusion; volatility
that moves abruptly but continuously (rough volatility — Gatheral–Jaisson–Rosenbaum 2018 —
makes vol paths jump-like at coarse sampling); and vol clustering with occasional 4σ draws.
Aït-Sahalia (2004) shows likelihood can in principle disentangle jumps from diffusion, but
practical power at daily frequency is very weak; SVJ models estimated on daily returns
(Eraker–Johannes–Polson 2003) recover jump intensities of a handful per year with wide
posteriors, and jump intensity trades off against vol-of-vol almost one-for-one.
This is also the direct answer to "high volatility vs genuine jump behavior": **on daily
data alone, the distinction is not identifiable, and any model that claims to make it is
asserting, not testing.**

### 2.3 The honest reduction — what *is* testable daily

Condition returns on the strongest causal vol model: $z_t = r_t / \hat{\sigma}_{t|t-1}$.

- **World SV-complete:** if the vol model captures all dynamics, $z_t$ is i.i.d. (possibly
  heavy-tailed). Tail exceedances of $z_t$ arrive as independent Bernoulli events. Nothing
  beyond vol exists at this frequency; "jumps" are repackaged vol.
- **World jump-intensity:** if crash arrival has its own dynamics, exceedances cluster and
  are predictable from event history *even after vol conditioning*.

This dichotomy is exactly the empirical content of option D, and it has standard-literature
handles: the **hit-sequence independence / conditional-coverage tests** of Christoffersen
(1998) from VaR backtesting; **self-exciting (Hawkes) point processes** (Hawkes 1971; Ogata
MLE 1978; in finance Aït-Sahalia–Cacho-Diaz–Laeven 2015, mutually exciting jumps as
contagion); **autoregressive conditional hazard** (Hamilton–Jordà 2002). Known priors, both
directions: weak vol models (plain GARCH-normal) notoriously leave clustered exceedances;
strong ones (asymmetric, t-innovations, HAR with semivariance — Patton–Sheppard 2015) absorb
much of it; ACL 2015 still finds significant self-excitation in daily index returns. The
question is genuinely open at the strongest-baseline rung — an honest coin-flip, which is
what a good experiment looks like.

### 2.4 Jumps in the *state* vs jumps in *prices* (the C/D conflation)

The proposal's SDE puts the jump in the latent state $X_t$ (option C). But a jump in an
unobserved state, absent a price discontinuity, is observationally just a *fast continuous
move* of the environment — and the record already shows environment transitions are fast.
At daily sampling, option C is unidentifiable against rapid drift. Option D relocates the
discontinuity to where it is observable (returns) and puts the *continuity* where the
evidence supports it (the slowly-evolving intensity/fragility coordinate). D is the only
member of the taxonomy that is simultaneously new, identifiable, and on-mechanism.

---

## 3. Model landscape

The 15 requested families, grouped by what their latent object is and what they could add
*given the three existing nulls*. "New vs record" asks: does this family test anything the
Chapters 1–3 nulls and the Continuum Turn have not already tested?

| # | Family | State object | Jumps | Daily-freq identifiable? | New vs record | Verdict |
|---|---|---|---|---|---|---|
| 1–3 | Linear/nonlinear state space, Kalman & extensions | $X_t \in \mathbb{R}^d$, Gaussian | none | yes (easy) | **No** — a Kalman smoother of the same features is the EWMA/VAR rung of the filter horserace, already the *winner* there and already null in Stage 2 | baseline machinery, not a hypothesis |
| 4 | Stochastic volatility (latent log-vol OU/AR) | 1-D continuous | none | yes (particle MCMC / Kim-Shephard-Chib) | **No** — the latent SV state ≈ the vol axis; VIX/RV already proxy it; record shows that axis is saturated | use as *baseline component only* |
| 5 | Jump-diffusion (Merton/Kou) | observed price; params static | compound Poisson, constant λ | **weak** (λ ↔ tail-thickness confounded) | No dynamics — constant λ is "heavy tails," not a state | reject |
| 6 | Lévy processes (VG, CGMY) | none (i.i.d. increments) | infinite-activity | tail shape yes; jump-vs-diffusion no | **No** — stateless by construction; cannot carry conditioning information | reject for this question |
| 7 | Markov-modulated jump-diffusion | $(S_t, X_t)$ mixed | state-dep. λ | poor (many weakly-identified params) | Reintroduces the discrete $S_t$ just rejected; = option E | reject unless D finds bimodal intensity |
| 8 | SV with jumps (Bates, SVCJ, affine AJD) | (vol, jump intensity) | Poisson, often λ ∝ σ² | **poor on daily returns alone** (EJP 2003: wide posteriors; λ↔vol-of-vol tradeoff); good only with options panels | Partially — but identification needs options data (a Stage-2 data expansion, not an MVE) | defer; revisit with options data |
| 9 | **Hawkes / self-exciting point process** | intensity λ_t (observable-driven) | events are the object | **yes** — few params, events observable, MLE tractable | **Yes** — event-history memory is a function class no rung of any prior baseline could express | **recommended core** (§5) |
| 10–12 | Dynamic factor models, TVP models, DFM+state-space | loadings/factors drift | none | yes | Partially — "dynamic factor loadings" is the *other* untested Chapter-3 object; but it's a covariance-object question, distinct from this proposal | park as the named alternative direction |
| 13 | Latent continuous-state models (generic) | $X_t \in \mathbb{R}^d$ | optional | depends | **No** — this is exactly Z_t / the EWMA env coordinate; run, null | closed |
| 14 | Neural SDEs / latent SDEs / neural jump SDEs | high-dim latent | learned | **no** at n ≈ 15k daily obs; thousands of params; no interpretable falsifier | Nothing testable it adds; maximal overfitting surface; in-sample likelihood would be the only "evidence" | reject firmly |
| 15 | Manifold / diffusion maps | deterministic re-embedding | n/a | n/a | **No** — a re-embedding of observables is definitionally information-free; useful only as visualization of the known 2-D continuum | descriptive tool only |

Notes on the two families closest to being chosen:

- **GAS / score-driven models with dynamic tail parameter** (Creal–Koopman–Lucas; Harvey's
  DCS; e.g. a t-distribution with time-varying ν_t) model the same object — time-varying
  conditional tail — as a *smooth* process rather than an *event-driven* one. This is the
  natural continuous rival to Hawkes and enters the design as a rival specification (§6.4),
  so that a positive result can say *which kind* of tail dynamics exists.
- **CAViaR / dynamic quantiles** (Engle–Manganelli 2004) are the quantile-regression cousin;
  kept as a robustness lens, not primary, because the hazard formulation maps directly onto
  the falsifiable clustering question.

---

## 4. Adjudicating the A–E taxonomy

| Option | Statement | Verdict on current evidence |
|---|---|---|
| A. Continuous latent state | $X_t \in \mathbb{R}^d$ evolves continuously | **Descriptively established** (the continuum finding) and **informationally null** for vol targets — already run |
| B. Discrete regimes | $S_t \in \{1..K\}$ | **Rejected** — silhouette 0.19, BIC never minimizes, K saturates, estimator rejected OOS |
| C. Continuous state with jumps in the state | $dX = \mu dt + \sigma dW + J dN$ | **Unidentifiable at Δ = 1d** vs fast continuous moves; also informationally bounded by the same filtration argument |
| D. Continuous state controlling jump intensity | $\lambda_t = f(X_t, \text{history})$, jumps in *returns* | **The only new, identifiable, on-mechanism claim** — recommended |
| E. Mixed discrete-continuous | $(S_t, X_t)$ | Reintroduces the rejected discrete component; over-parameterized; only revisit if D finds strongly bimodal λ |

---

## 5. Recommended model and mathematical formulation

Deliberately **two-layer and observable-driven** — no latent-state filtering problem is
created, because the record shows latent filtering on this panel destroys rather than adds
information. The "continuous latent fragility state" of the hypothesis is *represented* by
the intensity λ_t, which is a deterministic recursive function of observables (like a GARCH
conditional variance: a latent-in-name, observable-in-practice state).

**Layer 1 — volatility (the null hypothesis, made as strong as possible).**
$$r_t = \hat{\sigma}_{t|t-1} z_t, \qquad \hat{\sigma}_{t|t-1} = \text{strongest causal vol model (ladder, §8.3)}$$

**Layer 2 — tail-event process.** Events: $e_t = \mathbf{1}\{z_t < -c\}$ (left tail primary).
Discrete-time self-exciting hazard (Hawkes-GLM / autoregressive conditional hazard):
$$P(e_{t+1} = 1 \mid \mathcal{F}_t) = \Lambda\!\big(a + b\, H_t + \gamma' X_t\big),
\qquad H_t = e^{-\beta} H_{t-1} + \alpha\, e_t,$$
with $\Lambda$ the logistic link, $H_t$ the exponentially-decaying **excitation state**
(the discrete-time Hawkes kernel $\sum_{t_i \le t} \alpha e^{-\beta (t - t_i)}$ written as a
one-line recursion), and $X_t$ the vol/stress covariates (RV, VIX where available, NFCI,
asymmetry terms) whose job is to absorb any vol-dependent miscalibration of Layer 1.

- **Latent state:** none estimated; the fragility coordinate is $H_t$ (observable-driven).
- **Observation process:** daily S&P log returns; events derived from standardized residuals.
- **Jump intensity:** $\lambda_t = \Lambda(a + bH_t + \gamma'X_t)$ — the object of interest.
- **Jump-size distribution:** deferred to Stage 2 (marked process); the MVE tests arrival only.
- **Parameterization:** $(a, b, \alpha, \beta, \gamma)$ — with α absorbable into b, effectively
  **4 + dim(γ) parameters** for ~450 events. Identification is comfortable.
- **Estimation:** Bernoulli MLE (a logistic regression with one recursively-generated
  regressor; β profiled over a small grid or estimated by BFGS). Continuous-time Ogata MLE
  as a robustness check. No MCMC, no particle filter, no simulation-based inference.
- **The key quantity:** $b$ (does event history move the hazard?) and the **branching ratio**
  $n = \alpha/\beta$ in the continuous-time version — the expected number of child events per
  event; $n \to 1$ is criticality/endogeneity, $n = 0$ is the SV-complete world.

**What this expresses that the HMM structurally could not:** an HMM's crisis state has a
geometric dwell — a *memoryless*, constant hazard of exit, and entry hazard independent of
event history given the state. Hawkes hazard *spikes at each event and decays* — aftershock
dynamics (the Omori-law/ETAS analogy from seismology). These imply different, measurably
distinct hazard shapes following an event (§6.2).

**Why not the sophisticated alternatives:** Bates/SVCJ needs an options panel to identify λ
separately from vol-of-vol; a latent SDE filter re-runs the compression experiment that just
failed; neural SDEs put ~10³–10⁴ parameters against ~450 informative events with in-sample
likelihood as the only fit signal — the exact overfitting geometry this project's discipline
exists to prevent.

---

## 6. Empirical identification strategy — distinguishing the hypotheses

1. **vs volatility-only (the real null):** the entire design is the D−C comparison of §8 —
   excitation must add OOS forecast value *after* vol covariates absorb miscalibration.
   Orthogonality to the vol axis is by construction (standardized residuals), satisfying the
   standing gate.
2. **vs an HMM:** fit a 2-state HMM to the same event series as a rival D′. Discriminating
   statistic: the empirical hazard profile $h(\tau)$ = P(event at lag τ after an event) —
   HMM implies a flat-then-step (memoryless within state) profile; Hawkes implies smooth
   exponential decay from an elevated peak. Also compare OOS log-scores directly.
3. **vs SV misspecification — above all the leverage effect (the most likely false
   positive):** a large down move raises tomorrow's volatility (asymmetry/leverage) and hence
   tomorrow's tail probability *through the vol channel*; event-history excitation would
   inherit that pattern and misreport it as b > 0. Controlled twice: parametrically at the
   standardization stage (Layer 1 is GJR-asymmetric) and non-parametrically by the dedicated
   leverage rung B_lev (§8.3). If apparent self-excitation shrinks toward zero across
   A → B_vol → B_lev → C, it was vol/leverage misspecification wearing a jump costume —
   the same redundancy-signature diagnostic that correctly diagnosed Z_t.
4. **vs smooth tail drift:** rival D″ = GAS-t with dynamic ν_t (score-driven tail thickness,
   no event mechanism). If D″ ≈ D, tail dynamics exist but are smooth, not self-exciting —
   a different (still interesting) conclusion.
5. **vs luck/artifact — controls:** (i) placebo events from *positive* tail at same
   unconditional rate (crash-specific mechanisms shouldn't fire on up-moves symmetrically —
   partial excitation expected, must be weaker); (ii) surrogate control: time-shuffle event
   history within blocks (destroys causal ordering, preserves clustering rate) — b must die;
   (iii) simulation check: fit Layer 1, simulate i.i.d.-z data of matched length, verify the
   pipeline finds b ≈ 0 (false-positive calibration).

---

## 7. Falsification criteria (what kills the direction)

Declare **no evidence for tail-event dynamics beyond volatility** if ANY of:

- The hit sequence from the strongest vol baseline (rung C) already passes independence
  testing (Christoffersen-type) in-sample — nothing left to model;
- OOS Δlog-score(D−C) ≤ 0, or its block-bootstrap CI includes 0;
- The increment collapses under leave-one-crisis-out (single-episode artifact);
- The increment shrinks monotonically toward 0 across the rungs A → B_vol → B_lev → C
  (redundancy signature — leverage or vol miscalibration, not excitation);
- $b$ (or branching ratio) is unstable in sign across the 1950–1990 / 1990–2026 halves;
- The surrogate/simulation controls fire (pipeline manufactures excitation from i.i.d. data).

Declare support only if: Δlog-score(D−C) > 0 with CI excluding 0, survives LOTO across ≥
8 crisis episodes, survives the full baseline ladder including the VIX-era kill-check, and
the hazard-shape diagnostic favors decay over memoryless. As always: support is stamped
provisional; the pre-named escalation is international indices (independent crash histories).

---

## 8. Pre-registration — Minimum Viable Experiment (FROZEN 2026-07-22)

**Status (2026-07-22, frozen).** Adam approved the experiment, required (i) an explicit
leverage-aware volatility rung below the self-excitation comparison and (ii) full causal
specification of the event definition, volatility model, threshold, and ladder — both
incorporated — and then **signed the §8.9 checklist. This pre-registration is FROZEN**:
hypothesis, thresholds, event definition, and ladder do not change; all post-hoc analysis
is labeled exploratory. **Program-level commitment (Adam, 2026-07-22): this is the FINAL
preregistered experiment of the current research program.** A null result is accepted as
the convergence of the evidence — write the methods/negative paper, no further conditioning
experiments. A Case-A result is a genuinely new axis that the HMM and covariance analyses
were not designed to detect — proceed per §8.8.

**Hypothesis (falsifiable form).** H1: conditional on the strongest honest causal volatility
model — *including its leverage/asymmetry channel* — left-tail event arrival in S&P daily
returns is self-exciting: event history carries incremental, stable OOS information about
near-term tail-event probability. H0: standardized returns' tail exceedances are serially
independent given the vol/leverage information set (SV-complete world).

**8.1 Layer-1 volatility model (event-defining; pinned, causal, leverage-aware).**
- **Primary: GJR-GARCH(1,1) with Student-t innovations** — leverage-aware by construction
  (the asymmetry term lets negative returns raise conditional vol more than positive ones),
  so the leverage effect is absorbed at the standardization stage before any hazard modeling.
- **Causal estimation protocol:** parameters re-estimated each year-end on all data through
  that date (expanding window); $\hat\sigma_{t|t-1}$ for days in year Y+1 is produced by
  running the GARCH recursion causally under the year-Y parameters. Initial estimation window
  1950-01→1959-12; the event series therefore begins **1960-01**. No full-sample parameter
  fitting anywhere — fitting once on all data and standardizing in-sample would leak the
  future through the parameters (the same class of bug as CR-04).
- **Pre-declared alternative event-vol models (robustness — full pipeline re-run):** HAR-RV
  with signed semivariance (Patton–Sheppard; leverage-aware through $RS^-$), and RiskMetrics
  EWMA (λ = 0.94; no estimation, trivially causal). A Case-A result must not be specific to
  the GJR event definition.
- **The event series is fixed by the primary Layer-1 model.** The hazard ladder varies the
  *information set*, never the events — otherwise rung comparisons would be scoring different
  targets.

**8.2 Events and threshold (pinned).** $z_t = r_t/\hat\sigma_{t|t-1}$;
$e_t = \mathbf{1}\{z_t < -2.0\}$ with the threshold a **fixed constant** — causal by
definition (no estimated quantile, no calibration to a target rate, nothing fit to data).
Robustness: c = 2.5. Two-sided $|z_t| > 2.0$ is the one pre-declared secondary. Under
t-innovations expect P(z < −2) ≈ 2.5–3.5% → roughly **420–580 events** on ~16,700
event-eligible days (1960→2026), across 10+ distinct crisis episodes (1962, 1974, 1987, 1998,
2000–02, 2008–09, 2011, 2015, 2018, 2020, 2022, …) — the replication-count weakness of
Chapters 2–3 does not apply here.

**8.3 Hazard ladder (pinned; every rung predicts $e_{t+1}$ from information ≤ t, all on the
same fixed event series).**
- **A — constant hazard:** expanding-window empirical event rate.
- **B_vol — symmetric vol/stress:** logistic hazard on
  $\{\log\hat\sigma_{t|t-1},\ \log RV21_t,\ \log RV63_t\}$. Absorbs *level*-dependent
  miscalibration of Layer 1 ("the GARCH is miscalibrated when vol is high").
- **B_lev — leverage-aware rung (required by Adam, 2026-07-22):** B_vol +
  $\{r_t^-,\ \textstyle\sum_{5d} r^-,\ \sum_{21d} r^-,\ RS^-_{21}/RV_{21},\ \text{down-day count}_{21}\}$
  — signed-return magnitudes, negative-semivariance share, down-day frequency. Absorbs the
  leverage effect non-parametrically: a large down day raises tomorrow's vol and hence
  tomorrow's tail probability *through the vol channel*, a pattern event-history excitation
  would otherwise inherit and misreport as b > 0. Leverage is thus controlled twice —
  parametrically in Layer 1 (GJR asymmetry) and non-parametrically here.
- **C — flexible:** natural cubic splines (df = 4 per input) + ridge (alpha by blocked CV on
  the training portion only) over the **B_lev covariate set** — the strongest honest
  vol/leverage-driven hazard.
- **D — C + excitation:** adds $H_t = e^{-\beta}H_{t-1} + e_t$ ($H_0 = 0$; α absorbed into
  b); β selected on training data only, from the pre-declared half-life grid
  {1, 2, 5, 10, 21, 63} days.
- **Primary comparison: D − C.** The full increment curve D−A, D−B_vol, D−B_lev, D−C is also
  reported: the increment must *survive to the last rung*; monotone shrinkage toward 0 is the
  redundancy signature (leverage/vol miscalibration, not excitation).
- Note: if Layer 1 were perfectly specified, A ≈ B_vol ≈ B_lev ≈ C by construction; the rungs
  exist so that D−C cannot be won by any vol- or leverage-dependent miscalibration of Layer 1.

**8.4 Primary metric and OOS protocol (causal).** OOS mean Δ log-score (D − C) for the
1-day-ahead event probability. Rolling-origin with burn-in = first 40% of the event-eligible
sample (scoring starts ≈ 1986, so 1987, 1998, 2000–02, 2008–09, 2011, 2015, 2018, 2020, 2022
are all OOS); **annual refit of everything** (Layer 1, all hazard rungs, ridge alphas, β) on
data through each refit date; predicted probabilities clipped to $[10^{-5}, 1-10^{-5}]$
(log-score stability, pre-declared); all rungs scored on identical evaluation days.
Inference: stationary block bootstrap CI (mean block ~126d) excluding 0, plus
leave-one-crisis-out. Secondaries: Brier; cumulative event probability at h ∈ {5, 21};
hazard-shape diagnostic (§6.2).

**8.5 Sample and covariate availability (pre-declared).** Primary: ^GSPC daily
1950-01→2026-07 (events from 1960-01; yfinance, already in-pipeline). The primary covariate
set is **uniform over the whole sample** (σ̂, RV, leverage terms — all return-derived; no
series that starts mid-sample). Two pre-declared enrichment variants, reported separately and
never swapped in post hoc: (i) **NFCI-added** (1971+, with the 7-day publication lag per the
CR-01 convention); (ii) **VIX-era kill-check** (1990→2026, prior-day VIX close added to
B_vol/B_lev/C): the D−C increment must independently hold there — if it lives only where
implied vol is unobservable, it is proxying implied-vol information, not excitation.

**8.6 Controls.** Positive-tail placebo; block-shuffled event-history surrogate; i.i.d.
simulation false-positive calibration (§6.5). One primary, one pre-declared secondary
(two-sided events); all else robustness.

**8.7 Case table.**

| Case | Outcome | Interpretation |
|---|---|---|
| A | D−C > 0, CI excludes 0, survives LOTO + full rung curve + VIX-era kill-check + controls | tail-arrival dynamics beyond vol/leverage exist — provisional; proceed to Stage 2 |
| B | increment exists only in some eras/episodes | episode-conditional; diagnose, do not proceed |
| C | in-sample clustering exists but OOS increment ≤ 0, or dies across A → B_vol → B_lev → C | leverage/vol miscalibration, not excitation — close |
| D | rung-C hit sequence already independent in-sample | SV-complete world at daily frequency — close, bank the negative |
| E | controls fire (surrogate/simulation false positives) | pipeline invalid — fix before any claim |

**8.8 Downstream decision tree (strictly gated, nothing built now).**
Stage 2 (entry: Case A): marked process (jump-size distribution), asymmetry (left vs right
excitation), cross-asset mutual excitation (does an SPX event raise credit/rates tail hazard —
the ACL 2015 contagion object), and the D″ GAS-ν rival to classify smooth-vs-event-driven.
Stage 3: risk characterization — does λ_t change ex-ante *tail* risk assessment OOS vs
vol-only (CVaR calibration, drawdown-probability calibration — note this addresses the
record's open question #7, P(maxDD), untested). Stage 4: one pre-registered rule (tail-hazard
de-risking overlay vs vol-targeting baseline), net of costs, provisional. Honest expectation
even under Case A: excitation half-lives are days, so the natural consumer is **daily
risk-ops/de-risking** — consistent with where the record already located this project's
practical value — not monthly allocation.

**8.9 Freeze checklist — the four blocking items, now pinned.**

| # | Item | Pinned specification | Sign-off |
|---|---|---|---|
| 1 | Event definition | $e_t = \mathbf{1}\{z_t < -2.0\}$ on GJR-GARCH(1,1)-t standardized residuals; events from 1960-01; fixed across all rungs and never redefined by the ladder | ✓ 2026-07-22 |
| 2 | Volatility model | GJR-GARCH(1,1)-t, expanding annual causal refits, 1950-01→1959-12 initial window; HAR-RS⁻ and EWMA(0.94) as event-definition robustness | ✓ 2026-07-22 |
| 3 | Threshold | fixed constant c = 2.0 (causal by definition); c = 2.5 robustness; two-sided the one secondary | ✓ 2026-07-22 |
| 4 | Ladder | A → B_vol → B_lev (leverage rung) → C (splines+ridge on B_lev set) → D (+ $H_t$, β from fixed half-life grid); primary D−C; full increment curve reported | ✓ 2026-07-22 |

Sign-off: **Adam, 2026-07-22** → status **FROZEN**. Thereafter no changes to hypothesis,
thresholds, event definition, or ladder; deviations require a logged amendment before
results are seen.

**8.10 Effort estimate.** Layer-1 causal GJR harness + event construction ~1 session; hazard
ladder + OOS harness (reusing the rolling-origin/bootstrap machinery from
`histext_stage1.py` / `stage1p_covariance.py`) ~1 session; controls + writeup ~1 session. No
new data infrastructure; no options, no intraday.

---

## 9. Roadmap and what each outcome means

**Pre-declared stopping rule (Adam, 2026-07-22):** this MVE is the final preregistered
experiment of the current program — Case C/D ends the program at the methods/negative
paper; there is no fifth experiment.

- **Case A →** Stage 2 as in §8.7. The only place "genuine jumps" ever become *identifiable*
  (rather than inferred) is with new data: intraday realized measures (RV/BV/JV) or the
  options surface (risk-neutral jump tail — Bollerslev–Todorov 2011 found the left jump-tail
  premium is distinct from the variance premium). Those are pre-named *data expansions*
  contingent on Case A — never a rescue move after a null.
- **Case C/D →** the continuous-time/jump reframing adds nothing beyond volatility dynamics
  at daily frequency. This is a *strong, clean* fourth chapter for the methods/negative
  paper: discrete regimes rejected (Ch. 1), continuous compression rejected
  (Belief Revision), macro conditioning rejected (Ch. 2), covariance conditioning rejected
  (Ch. 3), and now tail-arrival dynamics rejected — the observable vol/stress axis
  exhausts daily-frequency index structure across every representation tried. That is a
  publishable, coherent thesis, arguably stronger than any single positive result would
  have been.
- **What would make the *model* (not just the test) useful:** a Case-A λ_t that (i) is
  stable across seeds/windows (the Z_t lesson: check perturbation stability *before*
  believing it), (ii) improves OOS tail-probability calibration, and (iii) changes a
  risk decision (Stage 3) relative to vol-targeting. Fit statistics are never evidence.

## 10. Reading list (standard-literature anchors)

- Jumps vs diffusion, identification: Barndorff-Nielsen & Shephard (2004, 2006); Aït-Sahalia
  & Jacod (2009); Lee & Mykland (2008); Aït-Sahalia (2004); Andersen, Bollerslev & Diebold
  (2007, "Roughing it up" — jump component adds little to vol forecasts); Patton & Sheppard
  (2015, signed jumps); Gatheral, Jaisson & Rosenbaum (2018, rough vol as jump-mimic).
- Self-excitation: Hawkes (1971); Ogata (1978, 1981); Hamilton & Jordà (2002, ACH);
  Aït-Sahalia, Cacho-Diaz & Laeven (2015, JFE — mutually exciting jumps/contagion).
- Hit-sequence testing: Christoffersen (1998, conditional coverage/independence).
- Tail dynamics, smooth rivals: Hansen (1994, autoregressive conditional density);
  Creal, Koopman & Lucas (2013, GAS); Engle & Manganelli (2004, CAViaR); Kelly & Jiang
  (2014, RFS — tail risk measure with pricing power).
- Jump risk premia (Stage-2+ data expansion): Bollerslev & Todorov (2011, JF); Eraker,
  Johannes & Polson (2003); Duffie, Pan & Singleton (2000); Bates (1996); Pan (2002).

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
