---
type: research-record
project: regime-detection
created: 2026-07-21
last_updated: 2026-07-22
status: interim — belief revised (2026-07-22): HMM coordinate is a moderately-stable compression of observables; no incremental OOS vol info beyond raw features
detailed_audit: .planning/RESEARCH-AUDIT.md (full 25-section research audit — retained as evidence)
code_review: .planning/DEEP-REVIEW.md (code-level causality review, 5 fixed bugs)
---

# Research Record — Regime-Detection HDP-HMM

Durable, root-level narrative of what this project believes and why. This is the file to read to
understand the current state of knowledge. It captures the 2026-07-21 research audit as the current
baseline. **No research code, model, state count, truncation level, backtest, or paper has been changed
to create this record — it is documentation only.**

Detailed technical evidence is retained in two `.planning/` files: `RESEARCH-AUDIT.md` (the full
25-section research audit — regime fingerprints, per-feature data audit, look-ahead matrix, repository
map) and `DEEP-REVIEW.md` (the code-level causality review, 5 fixed bugs). This record is the durable
**narrative** and current status; those files are the **evidence**. Where a table here is summarized,
the full version is in `RESEARCH-AUDIT.md`. Nothing from the audit has been discarded.

---

## 2026-07-22 (latest) — Chapter 3 (covariance conditioning): NULL/negative, scoped closure

Frozen, pre-registered reframe (`.planning/COVARIANCE-CONDITIONING-PREREG.md`): new object (covariance
matrix + eigenstructure), new lens (OOS portfolio risk + covariance forecast loss, not predictive R²). Test
whether an observable NON-volatility coordinate (absorption ratio primary) improves covariance estimation
beyond a MATCHED volatility-only similarity-weighted estimator (`B_match`). 13-ETF universe 2007–2026, 206
monthly OOS rebalances (`scripts/stage1p_covariance.py`).

**Verdict: NULL, indeed negative.** Primary M1 Var(GMV_T)/Var(GMV_Bmatch)=2.24 [CI 1.00,4.33] — T's
minimum-variance portfolio has 2.24× the realized variance (1.98% vs 1.32%). M2: correlation-Frobenius flat
(Δ=+0.004, CI incl 0 — absorption adds nothing to the dependence-structure estimate); QLIK a trivial ~1%
edge (Δ=−0.089) that is contradicted by the portfolio outcome. A dimensionality-matched placebo does not
degrade (isolates the harm to the AR coordinate, not the kernel dimension); similarity architecture ≈ EWMA;
negative across costs, leave-one-crisis-out, risk-parity, hedge, diversification, and T+ (macro/credit
added). Mechanism: the persistent/trending absorption ratio concentrates the similarity kernel → small
effective sample → occasionally degenerate covariances → GMV amplifies into variance blowups. The
GMV-blowup is partly architecture-sensitive, but the flat correlation-Frobenius means there is no
dependence-structure signal to recover.

**Scoped closure:** closes THIS covariance-conditioning approach / universe / features / architecture — the
pre-specified coordinates and estimator do not add incremental OOS covariance or portfolio value beyond the
matched vol-only baseline. Does NOT establish that all useful non-vol structure is exhausted; untested
objects remain (factor structure, tail dependence, nonlinear dependence, dynamic factor loadings,
liquidity/funding, other portfolio-specific dependence). Program status: three chapters (HMM latent info;
macro→stock-bond-corr Case C; covariance conditioning), all null — genuine narrowing of where useful
structure beyond volatility could live.

## 2026-07-22 (latest) — Stage-1 result: macro/rates axis is a non-stationary co-trend (Case C)

Pre-registered, frozen test (`.planning/STOCKBOND-MACRO-PREREG.md`) of a *separate* hypothesis (does NOT
reopen the HMM): does the observable macro/rates axis carry stable, incremental OOS information about
stock-bond correlation beyond a strong volatility/stress baseline? Built a ~50y dataset
(`data/processed/histext_daily.csv`, 1976→2026; 3 correlation regimes / 2 major transitions; synthetic
constant-maturity par-bond TRs validated against IEF/TLT, gate corr 0.985) and ran the full frozen battery
(`scripts/histext_build.py`, `scripts/histext_stage1.py`).

**Verdict: Case C — historical co-trend / non-stationary.** Decisive context: all models have deeply
negative OOS R² (A −1.28 … D −1.27) — they predict forward correlation worse than the pooled mean, so the
frozen primary ΔR²(D−C)=+0.253 is a gap between two *failing* models, not evidence macro predicts
correlation. Its 90% CI [−0.017, +0.564] includes 0 (support bar = exclude-0, fails). Two frozen
falsifiers triggered: (#4) detrending collapses it to −0.040 (the increment is the secular
disinflation→reflation trend); (#5) the standardized macro effect flips sign across regimes
(−0.01/−0.09/+0.17) and calibration is badly non-stationary (per-regime R²_D −1.29/−2.98/−0.28).
Per-regime ΔR² is negative in the long pre-2000 positive era (−0.17), positive in R2/R3. Robust across
maturities/horizons and the −dy corroborator — but robustness between two failing models is not
usefulness. One genuinely on-mechanism positive: volatility alone predicts the correlation *sign* at
chance (AUC 0.497) while +macro reaches AUC 0.597 — consistent with vol=magnitude, macro=sign, but modest
and plausibly low-frequency era-identification (what detrending removes); insufficient for Case A.

**Net:** the macro/rates axis does NOT provide stable incremental OOS information about the *level* of
stock-bond correlation beyond volatility on U.S. data. Per the frozen downstream tree, Case C stops the
portfolio bridge (no Stage 2 on U.S. data). Only legitimate continuation: international stock-bond pairs
(independent transitions) to adjudicate the corr-*sign* hint — as pre-registered diagnosis, not a
portfolio path. Default recommendation: bank the negative and write the methods paper. HMM thesis remains
separate and dead; this does not revive it.

## 2026-07-22 (later) — Belief Revision: the HMM coordinate is a compression, not a distinct latent state

Formal belief revision following a pre-registered out-of-sample test
(`scripts/representation_information.py`, `results/representation_information.csv`). This is the current
headline; the "Continuum Turn" object below is superseded where they conflict.

**Prior belief.** The continuous HMM coordinate `Z_t = E[μ_S | x_{1:t}]` appeared highly stable across
training windows (in-sample cross-window corr 0.92–0.97) and potentially represented a latent market
environment distinct from the raw observables.

**New evidence.**
- *Stability (genuine OOS perturbation tests, 2024→present):* cross-seed 0.42 / 0.50, cross-window
  (exp~5y / exp~3y) 0.52 / 0.44, feature-subset (drop `spy_ret`) 0.60, K_max 8→12 0.54 — mean ≈0.5,
  **substantially below the in-sample 0.92–0.97.** Even pure SVI seed noise (same data, same window)
  drops Z-agreement to ≈0.45. Partly range-restriction on a calm validation window, partly genuine
  estimation fragility; either way `Z` is not the seed/window-invariant coordinate it was filed as.
- *Incremental information (pre-registered; HMM frozen on discovery ≤2023-12-31, forward-filtered):*
  `Y ~ X_rich` vs `Y ~ X_rich + Z` for forward SPY realized vol. Primary (21d, baseline X+EWMA21):
  R²_naive −0.031, R²_X **+0.140**, R²_{X+Z} +0.100, **ΔR² = −0.040** (block-perm p=0.53; bootstrap 90%
  CI [−0.41, +0.01]; phase-randomized negative control median −0.061 — `Z` is indistinguishable from its
  own spectral surrogate). **Broadly negative across {5,21,63}d × {all, hiVIX, loVIX} + entropy; no cell
  passes Bonferroni.** The increment shrinks toward 0 as the observable baseline is enriched (A_raw
  −0.052 → C_ewma5/21/63 −0.017) — the signature of a redundant compression.

**Revised belief.** The HMM coordinate is best regarded as a **moderately-stable statistical
compression / reparameterization of the observable feature space**, *not* — on current evidence — a
distinct latent environment carrying incremental volatility information. This retires the implicit hope
in the Continuum-Turn framing that `Z_t` was a trustworthy object beyond the observables.

**Remaining uncertainty (scope of the negative).** The result is specific to **volatility-related
outcomes**. It does not establish whether the representation (more precisely, the macro/curve axis)
carries incremental information about **dependence structure, tail co-movement, factor exposures,
breadth, or liquidity** — untested, and worth testing ONLY given a stated theoretical reason for
orthogonality to the volatility axis (not "something has to work").

**Gate for any further experiment.** Before testing a new target class, answer: *why should `Z_t` (or the
macro axis) contain information about `Y_t` that the volatility axis cannot already explain?* Assessed
2026-07-22: only the **rates/inflation-regime family** (stock-bond correlation sign; duration /
value-growth rotation) has a principled orthogonality argument (governed by PC2, to which VIX is
sign-blind) — but (a) it is a *conditioning* claim (macro axis beyond VIX), not the latent-distinctness
claim that just failed, and (b) in this 2016–2026 sample the relevant macro-regime shift is essentially a
single episode (2022), so it is severely underpowered. Honest default: the project has likely reached its
strongest defensible conclusion. See `NOTES.md`.

---

## 2026-07-22 — The Continuum Turn (reframe + 6 experiments)

A reframe (durable plan in `.planning/ROADMAP.md`) shifted the yardstick to **trustworthy state
inference**, defined as *calibration* (not accuracy), purpose-relative and confidence-conditional, feeding
a two-stage architecture (trusted state → conditional asset behavior). Six reproducible experiments
followed (`scripts/{trust_gate,raw_state_fingerprint,state_characterization,continuous_state_diagnostic,
filter_horserace,stage2_conditioning}.py`).

1. **The states are ~2-D, not a 1-D vol ladder** (`raw_state_fingerprint.py`). Participation ratio 1.88;
   PC1 (65%) = stress (VIX+NFCI), PC2 (32%) = macro/yield-curve (slope), nearly orthogonal (cross-state
   corr 0.15). Critically, **every prior "no beyond-VIX information" negative (permutation test, feature
   search, Phase-0 gate) was computed on the VIX-rank-merged label, which deletes PC2 by construction** —
   those negatives test "a VIX-sort of the states vs VIX" (near-tautological), not the raw structure. The
   beyond-VIX question was re-opened, not answered, for the raw representation.

2. **The latent structure is a weakly-structured CONTINUUM, not discrete regimes**
   (`state_characterization.py`). Silhouette 0.19; GMM BIC never minimizes (no natural K) — this *explains*
   the long-standing K-saturation and much of the E2 label instability (gridding a continuum → wobbling
   boundaries). The macro axis *recurs* (corr with time 0.06, 92 median crossings), not secular. No
   independent within-state scale dimension (scale tracks stress, corr 0.78) — cleanly ~2-D.

3. **The continuous coordinate Z_t = E[μ_S | x_{1:t}] is stable; the label instability was largely an
   artifact** (`continuous_state_diagnostic.py`). Across training windows Z_t's 2-D coordinate correlates
   0.92–0.97 (label ARI 0.60–0.81 in-sample [but Z_t's OOS cross-perturbation stability is only ≈0.42–0.60 — corrected 2026-07-22; see Belief Revision above] — far above E2's OOS 0.04–0.33, most of which was the VIX-merge
   + label-switching on the projected label). Z_t is label-switching-invariant (a physical location), so it
   needs no merge to compare. BUT ~2/3 of Z_t is reproducible by a plain EWMA of the features (R²=0.68): a
   trustworthy continuous coordinate that is mostly smoothed observables + a ~1/3 model-specific component.
   The 2-D coordinate *system* reproduces (macro axis sub-degree principal angle); only the 3-year window is
   underpowered (PR 1.26).

4. **The current HMM-based environment estimator is REJECTED on OOS predictive grounds relative to simpler
   continuous alternatives** (`filter_horserace.py`) — the decisive result. HMM frozen on train, forward-
   filtered through 2024–26: Z_t predicts the near-future environment far worse than a plain EWMA, VAR(1),
   or persistence. Scale-invariant OOS forecast correlation with X_{t+h}: HMM 0.25–0.38 vs 0.51–0.73 for
   the simple filters, every horizon, both VIX regimes; RMSE skill@21 −6% (HMM) vs +18–22% (simple).
   Mechanism: discretizing a continuum discards within-state position (~half the predictive info;
   corr(Z_t,X_{t+1})=0.38 < corr(X_t,X_{t+1})=0.71 — Z_t is a worse summary of *now* than today's raw
   features). Scope, precise: **this estimator, on this OOS evidence — NOT a claim about HMMs as a class.**
   Reconciles E1: its "persistence" is real but is predictively-costly lag; stability (result 3) ≠
   predictive reliability.

5. **Stage 2, first cut** (`stage2_conditioning.py`). Env represented continuously (EWMA of features;
   stress=VIX+NFCI, macro=slope), conditioning a cross-asset basket (SPY, IEF, TLT, HYG, LQD, GLD, IWF, IWD;
   cached `data/processed/cross_asset.csv`): the coordinate adds **no reliable incremental OOS value over
   raw contemporaneous features** (ΔR² mostly ≤0; a few tiny positives — SPY/IWF forward vol). Descriptive
   conditional structure exists (across stress tertiles TLT +1.1%→−0.6%, SPY +0.6%→+2.1% fwd-21d) but is
   ~captured by the raw features. Stock-bond (SPY–IEF) corr weakly tracks the macro axis (+0.14; −0.21 inv
   → −0.04 steep). Preliminary, low OOS power.

**Net position.** Trustworthy object = a continuous, stable 2-D (stress, macro) coordinate ≈ the smoothed
macro features; the HMM adds no predictive value over simple filters and is rejected as the estimator; the
coordinate shows no clear incremental conditioning value over raw features. The strongest honest
contribution on current evidence is *methodological*: the 2-D geometry the VIX-projection hid, the
continuum finding (explains K-saturation), the OOS rejection of the HMM estimator vs simple filters, and
cross-window agreement as an honest confidence measure.

**Open decision (next session):** (a) one rigorous Stage-2 pass — block-bootstrap significance, cleaner env
spec, macro-axis → duration/style/stock-bond-corr hypotheses, strictly benchmarked vs raw features — or
(b) accept the methods/negative framing and write it up. `paper.tex` untouched and now badly out of date.

---

## Purpose (unchanged)

Two goals: (1) an academic paper on latent market regimes; (2) regime labels for Portfolio-Manager.
Core thesis as originally stated: *"markets have latent states not directly observable from any single
indicator — a Bayesian HDP-HMM can recover them."* Null hypothesis: *"regimes are just VIX thresholds."*

---

## Thesis Status (current, evidence-based)

### Narrow Thesis — **Partially Supported**

> The project provides partial evidence for persistent, causally detectable volatility states that
> contain modest information about future volatility beyond VIX, while remaining uncertain about their
> broader economic interpretation and trading utility.

### Headline Thesis — **Not Supported (tested 2026-07-21)**

> The stronger claim — that latent volatility states are *not recoverable from VIX alone* — was tested
> directly via a reduced feature-combination search (VIX-removal, plus a config with zero implied-vol
> inputs) and is **not supported**. The regimes are volatility regimes: the vol ladder is recoverable
> even from purely non-vol features (momentum, yield slope, participation breadth), and every candidate
> feature collapses onto the vol axis at the state level. Not because VIX is uniquely powerful, but
> because the vol-regime structure is pervasive and redundant across the feature universe.

Not overstated: this was tested over a *reduced but reasonable* feature set; an exotic feature could in
principle carve a non-vol axis, but the pattern (everything collapses to vol) is strong and the a priori
case for the remaining untested candidates is weak. See "Feature Set — Diagnostics & Discovery".

### Full verdict table

| Claim | Status |
|---|---|
| Pipeline is causal / no-lookahead | **Validated** |
| Regime labels are training-window-sensitive; agreement is the honest confidence | **Validated** |
| Regime carries return/*volatility* info **beyond VIX** | **Not demonstrated** (Exp 1, 2026-07-21: 0/4 cells significant under a block-permutation null, p=0.16–0.73; vol demoted hardest. Confounded by regime↔VIX collinearity — see Experiment 1 Result below) |
| Regimes are persistent (sticky) states | **Partially Validated** (model κ is learned & real; reported Table 2 persistence is inflated by hysteresis + merge) |
| Regimes are "not recoverable from VIX alone" (headline) | **Not Supported** (tested 2026-07-21: vol ladder recovers even with zero vol inputs; every feature collapses onto the vol axis — regimes are vol regimes) |
| HDP nonparametric structure justified over a simpler HMM | **Open — Unsupported on current evidence** (K saturates; no fair fixed-K baseline) |
| Volatility-targeting backtest edge | **Not valid for OOS claims** (does not replicate OOS) |
| Tradeable alpha / signal | **None** (no return info; vol info dominated by VIX; robustness ⇒ already priced — see Alpha Assessment) |
| Persistence-*advantage magnitude* (66/61/41 vs 8–17 days) | **Partially Invalid** (confounded by asymmetric smoothing) |

### Experiment 1 — Result (2026-07-21): the "beyond-VIX" claim does not survive as stated

`scripts/significance_test.py` now regenerates the ΔR² statistics (Finding 4 resolved). Reproducible
numbers on the OOS ensemble labels; targets = cumulative forward return / annualized forward realized
vol (the new committed definition — differs from the old single-day-ahead prose numbers):

| Target | Horizon | ΔR² | Boot 90% CI | Perm p |
|---|---|---|---|---|
| return | 5d | 0.017 | [0.002, 0.060] | 0.20 |
| return | 21d | 0.061 | [0.013, 0.152] | 0.16 |
| realized vol | 5d | 0.004 | [0.001, 0.027] | 0.73 |
| realized vol | 21d | 0.020 | [0.002, 0.077] | 0.50 |

**Under the block-permutation null, none of the four cells is significant** (Bonferroni α=0.025; none
clears even an uncorrected 0.10). The block-bootstrap CIs all exclude 0 — exactly the predicted mirage:
ΔR² ≥ 0 by construction, so the CI excluding 0 is near-automatic and is *not* a test. **The permutation
test overturns the prior prose claim that "regimes carry significant volatility information beyond VIX."**

Surprise, recorded honestly: **volatility was demoted *hardest*** (p = 0.50–0.73), the opposite of the
pre-run expectation. Leading explanation — **regime↔VIX collinearity**: the regime is *defined by* VIX
rank, so its dummies are near-collinear with VIX and add little *beyond* VIX; permutation decorrelates
the label from VIX, so permuted (null) dummies pick up *more* spurious beyond-VIX variance than the real
ones. Signature: observed ΔR² sits *below* the null median for vol (p > 0.5). VIX is already a strong
forward-vol predictor, leaving almost no beyond-VIX headroom for a VIX-derived regime to fill.

Interpretation: this is **not** "regimes are uninformative" — it is quantitative proof of the audit's
core concern. **You cannot test "information beyond VIX" using a label that is itself a function of VIX.**
The beyond-VIX question is only answerable once the regime is decoupled from VIX — which is exactly
**Experiment 3** (raw 8-state fingerprints + VIX-ablation). Secondary refinement: a *conditional*
(VIX-stratified) permutation that preserves regime↔VIX while breaking regime↔target — the "fair" null.

---

## The Four High-Priority Findings

These are recorded as **known methodological issues requiring correction**. None has been fixed —
this record deliberately precedes any research-code change.

### Finding 1 — Transition Matrix Mislabeling  *(HIGH)*

The paper describes Table 2 as the **posterior-mean transition matrix**. The implementation
(`run_paper_experiments.py:133–137`) actually computes an **empirical transition-frequency matrix** from
the **hysteresis-smoothed, VIX-merged** 3-state labels. The model's own posterior transition matrix is
available via `get_transition_matrix()` (`src/core/hdp_hmm.py`) but is **not used** for the reported
table.

Implications:
- Persistence may be **overstated**.
- The 3-day hysteresis contributes **mechanically** to the reported persistence (flicker suppression
  raises self-transition frequency by construction).
- The VIX-based 8→3 merge can **absorb within-tertile state switches** into the diagonal.
- The reported matrix **does not represent the model's posterior transition parameters**.
- (Minor) The paper prose hardcodes diagonals "0.989 / 0.986 / 0.974" which do not match the
  regenerated table "0.986 / 0.984 / 0.976" — stale numbers.

Status: known methodological issue requiring correction. **Not fixed.**

### Finding 2 — Confounded Dwell Comparison  *(HIGH)*

- HDP labels use `hold_days=3` (hysteresis smoothing).
- VIX-threshold baseline uses **no smoothing**.
- Parametric-HMM baseline uses **no smoothing**.

The reported dwell comparison (HDP 66/61/41 days vs VIX-threshold 8–17 days) is therefore **not
symmetric**. Distinguish:

```
Observed dwell advantage
   vs
Dwell advantage inflated by asymmetric smoothing
```

The underlying advantage may still be real (κ is genuinely learned and sticky), but its **reported
magnitude is currently confounded**. This is the *same class of bug* the team already fixed for the OOS
labels (commit e6962df); the inverse asymmetry remains baked into the in-sample paper headline.

Status: known methodological issue requiring correction. **Not fixed.**

### Finding 3 — HDP Data-Driven K Is Currently Inert  *(HIGH)*

```
effective_K:  mean = 8   std = 0   mode = 8   (every observed run)
```

The HDP consistently **saturates the truncation level** (K_max = 8) and `prune_states` keeps all 8
states. The reduction from 8 states to 3 regimes is performed by a **hand-coded VIX-rank tertile
partition** (`merge_states_to_regimes`), not by the model.

Research implication (recorded explicitly):

> The claimed advantage of the HDP-HMM as a nonparametric model that learns the appropriate number of
> latent states has **not yet been demonstrated**.

The current fixed-K parametric-HMM comparison is **not a sufficient test**, because the existing
parametric result appears degenerate:

```
Param HMM "Moderate-Vol":  N = 367   dwell = 367   (a single contiguous 367-day block)
```

— consistent with a bad EM local optimum despite 10 restarts. Therefore:

> The question of whether the HDP-HMM's additional complexity is justified **remains unanswered.**

Status: known open research question. **Not changed.** (Model, K, and truncation untouched.)

### Finding 4 — Best Result Is Not Currently Reproducible  *(HIGH)*

`block_bootstrap_ci` and `regime_delta_r2` exist in `src/core/evaluation.py` but are **called by no
committed script** (grep-confirmed). The reported significance numbers therefore cannot be regenerated
from the executable experiment pipeline:

```
ΔR² volatility (fwd 21d) = 0.0124   90% CI [0.0017, 0.0665]
ΔR² returns    (fwd  5d) = 0.00077  90% CI [0.0002, 0.0097]
```

These numbers are **preserved** (not removed) and marked:

```
Reported in existing research record (NOTES.md, hub, this file)
Not currently reproducible from the executable experiment pipeline
Requires implementation of the significance-test experiment (see Experiment 1)
```

Status: **RESOLVED 2026-07-21** — `scripts/significance_test.py` + `block_permutation_test()` now
regenerate the numbers on every run. The reproducible result *overturned* the prose claim (see
"Experiment 1 — Result" above): under a proper block-permutation null, none of the four ΔR² cells is
significant. Reproducibility gap closed; the substantive claim it was protecting did not survive.

---

## Causal Integrity — a Genuine Strength  *(Validated)*

Recorded explicitly so it is not lost among the issues above:

- The system has been **mechanically tested for no-lookahead** — `tests/test_causality_invariants.py`
  perturbs a future value and asserts nothing at or before that index changes, for all four functions
  claiming causality (`expanding_standardize`, `expanding_regime_vol`, `get_filtered_states`, the HDP
  forward pass), with a negative control proving the perturbation is large enough to matter.
- Causal integrity is a **genuine strength** of this project.
- The model uses **expanding-window standardization** (past data only) and **forward filtering**
  (P(z_t | x_{1:t}), never the smoothed P(z_t | x_{1:T})) for all published labels.
- **Paper discrepancy (documentation issue):** `paper.tex:153` states the four features are "lagged one
  day to ensure causal inference." This is **inaccurate** — the features are contemporaneous, and
  causality comes from expanding standardization + forward filtering, not a one-day lag. To be corrected
  in the paper **later** (see "Paper — Do Not Modify Yet").

---

## Strongest Current Findings (current evidence)

### Finding A — Causal Integrity  *(Validated)*
The regime-detection pipeline is genuinely causal and mechanically tested for look-ahead.

### Finding B — Training-Window Sensitivity  *(Validated — treat as a research finding, not a nuisance)*
Cross-window agreement is approximately **51%–69%**. There is meaningful disagreement across training
windows even when individual regime assignments report **>99% confidence** (they disagreed 22% of the
time on such days). Live example preserved:

```
Today (2026-07-21): Low-Vol at only 2/3 agreement.
The 3-year rolling window currently classifies the state as Moderate-Vol.
```

The research question is therefore not simply *"Is the model confident?"* but *"How sensitive is the
regime classification to the historical training window?"* — a distinction the project's honest
`agreement_frac` confidence measure now captures, and which the paper does not yet emphasize.

### Finding C — Regime → Future Volatility Information  *(Downgraded 2026-07-21 → Not Demonstrated)*
Experiment 1 (block-permutation null) does **not** support beyond-VIX volatility information: 0/4 cells
significant, vol demoted hardest (p = 0.50–0.73). The prior "modest beyond-VIX vol info" claim does not
survive. Caveat: the test is confounded because the regime is VIX-derived (see "Experiment 1 — Result");
the beyond-VIX question needs a VIX-decoupled label (Experiment 3) to be answerable at all.

### Finding D — No Meaningful Return Prediction Yet  *(Validated as a negative result)*
Current evidence does **not** support meaningful return prediction. The model must not be described as a
return-predictive regime detector.

---

## Feature Set — Diagnostics & Discovery (2026-07-21)

Tools built (reusable): `scripts/feature_ablation.py` (refit on any subset + fingerprint),
`scripts/feature_discovery.py` (candidate: collinearity gate → fit → new-axis check).

**(1) The current 4 features are NOT collinear.** VIF 1.05–1.69, ~3.24 effective independent axes of 4,
condition number 4.7. Multicollinearity / redundancy is *not* the problem — a hypothesis both Adam and
the auditor bet on and the data rejected. Pairwise: VIX↔NFCI 0.45, slope↔NFCI −0.48, everything else
near 0. (So the earlier "NFCI is just VIX" claim was overstated — NFCI is mostly independent.)

**(2) Dropping `spy_ret` is safe.** Refit on {VIX, slope, NFCI}: vol ladder essentially unchanged
(11/17/36% realized vol vs 11/18/39%). Raw daily return was contributing ~noise (AR1 = −0.13 vs
+0.96–0.998 for the others) — its low correlation was the *bad* kind (independent because uninformative).
But label agreement with the 4-feature baseline was only **64.5%** — removing a near-useless feature
still reshuffled ~35% of daily labels, the same fragility band as the training-window sensitivity.
Recommendation: swap `spy_ret` → 63-day momentum (a slow trend axis), don't just drop.

**(3) Breadth (sector-return dispersion) FAILS the new-axis test — key methodological result.** Ran a
discovery fit on {momentum, VIX, slope, breadth} where breadth = daily cross-sectional std of the 9
full-history SPDR sectors. Breadth *passed* the collinearity gate (VIF 1.51, daily corr with VIX only
0.58) — but the **new-axis check killed it**: at the state level, corr(state-mean VIX, state-mean
breadth) = **+0.99**. Sorted by VIX, breadth rises monotonically (0.0052 → 0.0145). Cross-sectional
dispersion is mechanically a volatility proxy; it re-orders the states on vol exactly like slope/NFCI
did, adding no independent structure.

**Lesson (now the standard for feature screening): low VIF is necessary but NOT sufficient. A feature
earns inclusion only if it survives the new-axis check** — does it carve states VIX can't tell apart?
Daily pairwise correlation (0.58) understated the redundancy; the regime structure only cares about the
systematic component, which was 99% vol-aligned. `momentum` looks more independent (VIF 1.37; goes
*negative* only in the two highest-vol states — a genuine drawdown signal), so the swap is defensible.

**Emerging hypothesis (not yet confirmed):** the HDP regimes may be *intrinsically* volatility regimes —
every vol-adjacent feature tried (realized vol, dispersion, and even slope/NFCI) collapses onto the VIX
ordering at the state level, because diagonal-Gaussian state separation is dominated by the vol scale.
Genuinely non-vol candidates still untested: **participation breadth** (% of names > 200-DMA /
advance-decline — can decouple from vol in narrow low-VIX rallies, unlike dispersion), **vol term
structure** (VIX/VIX3M), and the **variance risk premium**. If none carves a new axis, the honest thesis
is "regimes are volatility regimes" and the defensible value is persistence/stability + honest
uncertainty — not beyond-VIX information. K still saturates at 8 in every fit (Finding 3 holds).

**(4) Reduced feature-combination search — the hypothesis is now CONFIRMED (2026-07-21).** Tested 5
principled configs (adding *participation* breadth = % of 9 SPDR sectors above their 200-DMA):

| config | K | RV Low→High (%) | spread | VIX Low→High | agree vs base | P new-axis ρ |
|---|---|---|---|---|---|---|
| M,V,S,N (swap-baseline) | 8 | 10.5 → 31.9 | 3.03 | 13.4 → 26.9 | 65% | — |
| M,S,N,P (no VIX) | 8 | 12.6 → 33.9 | 2.70 | 14.5 → 28.7 | 60% | −0.92 |
| **M,S,P (no VIX / no NFCI)** | 8 | 11.7 → 31.3 | 2.69 | 13.5 → 27.6 | 59% | −0.95 |
| M,V,S,P (P instead of N) | 8 | 11.4 → 37.7 | 3.32 | 14.2 → 31.8 | 77% | −0.90 |
| V,N (vol/credit only) | 8 | 10.1 → 30.3 | 3.01 | 13.7 → 25.6 | 75% | — |

**Every config recovers the same vol ladder — including `{momentum, yield_slope, participation}` with
ZERO implied-vol inputs** (no VIX, no NFCI): it still separates 11.7% → 31.3% realized vol and 13.5 → 27.6
mean VIX. Participation breadth also fails the new-axis check (ρ = −0.90 to −0.95 with realized vol). So
the volatility-regime structure is **redundantly encoded across macro, trend, credit, and breadth** — you
cannot remove it; strip the vol features and it reappears from the rest. K saturates at 8 in all five.
**Verdict: the regimes are volatility regimes, overdetermined.** No feature in this universe carves a
non-vol axis; the remaining untested candidates (VIX term structure, VRP) are vol-derived and very
unlikely to differ — the pattern is now the finding, and further feature-hunting has low expected value.

Mild silver lining worth keeping: the vol regime is recoverable from purely non-vol macro/trend/breadth
features — i.e. it is *macro-economically grounded*, not merely a VIX artifact. But that cuts *against*
the headline thesis (the regime is recoverable from many things, VIX among them), not for it. Tool:
`scripts/feature_search.py`.

---

## Revised Research Direction

The research is evolving based on evidence; the objective is **not** to preserve the original thesis but
to identify the strongest thesis the evidence supports.

```
Original Thesis
  ↓
Causal Integrity
  ↓
Out-of-Sample Testing
  ↓
Training-Window Sensitivity
  ↓
Recognition of Hysteresis Confounding
  ↓
Recognition of Transition-Matrix Mislabeling
  ↓
Recognition That HDP K Is Not Actually Being Learned
  ↓
Shift Toward Formal Significance Testing
  ↓
VIX-Ablation / Raw-State Analysis
  ↓
Reassessment of the Nonparametric Thesis
```

---

## Top Three Next Experiments  *(recorded; NOT implemented in this step)*

### Experiment 1 — Reproducible Significance Testing
Implement `scripts/significance_test.py` and integrate `block_bootstrap_ci` + `regime_delta_r2` into the
executable pipeline.
**Goal:** determine whether the incremental volatility information beyond VIX is statistically
significant under an appropriate null and a bootstrap/permutation framework. (Directly resolves
Finding 4.)

### Experiment 2 — Symmetric Persistence Comparison
Correct the comparison so HDP, VIX-threshold, and parametric-HMM states are evaluated under **comparable
smoothing assumptions.** Separately report, without conflating:
1. raw state persistence
2. smoothed state persistence
3. model-implied transition matrix (`get_transition_matrix()`)
4. empirical transition matrix
(Resolves Findings 1 & 2.)

### Experiment 3 — Raw 8-State Fingerprinting and VIX Ablation  *(key test of the original thesis)*
Investigate the raw HDP-HMM states **before** VIX-based merging: state fingerprints, transition
behavior, persistence, predictive characteristics. Then perform a **VIX-ablation** (refit without VIX in
the feature set; compare).
**Purpose:** directly test the headline thesis — *does the HDP-HMM discover latent information that
cannot be recovered from VIX alone?* This is the decisive experiment for the original thesis and for
Finding 3 (is the nonparametric structure discovering anything a VIX ladder can't).

---

## Deferred Future Experiment — K_max Sweep / Fixed-K Ladder  *(recorded; NOT implemented)*

Run a **K_max sweep** and a **fixed-K model ladder** (e.g. K ∈ {2,3,4,6} sticky HMM vs HDP at several
K_max) to determine whether:
- the HDP genuinely benefits from nonparametric state discovery;
- the truncation level is binding (if K_eff tracks K_max, K is not being selected);
- the model would behave differently under larger K_max;
- a fixed-K HMM can capture the same structure;
- the HDP-HMM's complexity is justified.

The existing degenerate parametric baseline (Finding 3) must be repaired (better init / more restarts /
report restart-stability) for this comparison to be fair.

---

## Reconstructed Research History (timeline)

| Date | Commits | What happened | Classification |
|---|---|---|---|
| 2026-05-05 → 05-11 | f14a9d7 … 04a3c31 | Kitchen-sink era: 23 features, PCA, GARCH; codebase map generated | Historical |
| 2026-05-10 | d6b0f14 … 58d89ce | The Strip-Down: rewritten to 4 features, no PCA; absolute vol brackets added | Defines current core |
| 2026-05-24 | 4fe1733 … 21278c4 | Paper era: experiment runner + LaTeX + backtest skeleton | Core (paper) |
| 2026-05-26 | 0bdca4e … 1a324d9 | Figures, descriptive stats, manuscript finalized | Core (paper) |
| 2026-07-18 | 6920c7f … 70849ae | CLI wrapper + README rewrite (second machine) | Core (tooling) |
| 2026-07-20/21 | 185ae8d | Causality deep-review: 5 lookahead/correctness bugs fixed | Core (correctness) |
| 2026-07-21 | 8dc349c, 94cefd8 | Branch merge + causality-invariant test suite | Core (validation) |
| 2026-07-21 | d4f4872, 5955673 | Walk-forward OOS implemented (was a no-op stub) | Core (current direction) |
| 2026-07-21 | 8b06545 … 9936a0a | Training-window sensitivity discovered → 3-window ensemble | Core (current direction) |
| 2026-07-21 | e6962df … 0126d32 | Significance-test pivot + hysteresis mismatch fixed (OOS) | Current frontier |
| 2026-07-21 | (this record) | Read-only research audit + documentation finalization | Current |

The project has been **self-correcting in the honest direction** — each step made the claims smaller and
truer. The external paper (`paper.tex`, "upload-ready") is a snapshot from *before* the last four steps
and has intentionally **not** been updated (see below).

---

## Research Decision Log

```
Date: 2026-07-21
Question: Is the reported regime persistence (Table 2, dwell 66/61/41) a real learned property?
Method: Traced run_paper_experiments.py:133–137 + get_labels_and_probs hysteresis.
Result: Table 2 is an empirical count on smoothed, VIX-merged labels — not the model's posterior matrix;
        dwell compares smoothed HDP vs raw baselines.
Interpretation: Persistence is real in the model (κ learned) but the reported magnitude is inflated by
        post-processing; the advantage-vs-baseline comparison is unfair.
Decision: Record as HIGH (Findings 1 & 2). Do not fix yet. Fix via Experiment 2.
Confidence: High.
```
```
Date: 2026-07-21
Question: Is the HDP's data-driven K actually doing work?
Method: effective_K output (results/run_log.txt) + prune_states + merge path.
Result: effective_K = mean 8.0, std 0.0, mode 8 every run; all 8 kept; 3 regimes imposed by VIX-rank cut.
Interpretation: K is not inferred — it saturates the truncation; nonparametric benefit is inert here.
Decision: Record "HDP justified?" as Open/Unsupported (Finding 3). Do not change model. Test via K_max
        sweep + fixed-K ladder.
Confidence: High (single-run; a K_max sweep would make it airtight).
```
```
Date: 2026-07-21
Question: Is the volatility-information significance result reproducible?
Method: grep for callers of block_bootstrap_ci / regime_delta_r2.
Result: Defined in evaluation.py; called by nothing. Numbers exist only in prose.
Interpretation: The best result is orphaned.
Decision: Record as HIGH (Finding 4). Preserve numbers; mark not-reproducible. Fix via Experiment 1.
Confidence: High.
```
```
Date: 2026-07-21
Question: Are the published regimes "not recoverable from VIX alone"?
Method: Traced merge_states_to_regimes (sorts states by mean VIX) + reviewed fingerprints.
Result: Final regimes are literally a VIX-rank partition; no VIX-independent structure isolated; raw
        8-state emissions never characterized.
Interpretation: Headline thesis neither supported nor refuted — untested; labeling method works against it.
Decision: Record headline thesis as Not Yet Established / Open. Test via Experiment 3 (raw-state +
        VIX-ablation). Do not implement yet.
Confidence: High that it's untested; open on the underlying truth.
```

---

## Open Questions

1. Do VIX-independent latent states exist? (Experiment 3.)
2. Does data-driven K ever activate, or always saturate K_max? (K_max sweep.)
3. Does a fixed-K sticky HMM match the HDP on fit / stability / vol-ΔR²? (Fixed-K ladder.)
4. Is the vol-ΔR² robust to a strict permutation null and multiple-testing correction? (Experiment 1.)
5. How much of the in-sample→OOS dwell gap is real market calm vs window sensitivity vs residual method?
6. Which of the two labeling schemes is "the" scheme? (Open decision — deliberately unresolved.)
7. Is the regime drawdown-predictive (P(maxDD_{t:t+h} | S_t))? (Untested.)

---

## Paper — Do Not Modify Yet

`paper.tex` is intentionally **not** being updated. It should be revised only after:
1. the significance-test experiment (Experiment 1) is implemented;
2. the persistence comparison (Experiment 2) is corrected;
3. the raw-state / VIX-ablation experiment (Experiment 3) is completed.

The paper should ultimately reflect the **final evidence**, not this interim audit. Documentation issues
to carry into that eventual revision: the "features lagged one day" sentence (paper.tex:153) and the
stale transition-matrix diagonals in prose (paper.tex:313).

---

## Alpha Assessment & Where This Leaves the Project (2026-07-21)

**Tradeable alpha: none.** (a) No return-direction info (permutation test; every regime had positive
mean return in-sample). (b) No vol-forecasting edge beyond VIX (permutation test; dominated by trivial
realized-vol models). (c) No variance-risk-premium timing edge — the regime is laggy/persistent, wrong
for timing acute vol spikes. (d) "Regime-as-filter" ≈ a free VIX threshold; the HMM adds nothing.
**Deep reason: robustness and alpha are opposites** — a signal recoverable from a dozen public features
and ≈ VIX is, by definition, already priced. The very robustness that makes it a good *descriptive* tool
is the tell that it carries no edge.

**Where the two goals land:**
- *Academic paper:* the "beyond-VIX / nonparametric-discovery" thesis is not supported. The defensible
  paper is descriptive + methodological: (i) market regimes are robustly volatility regimes — recoverable
  even with zero vol inputs, so macro-grounded, not a VIX artifact; (ii) regime assignment is materially
  training-window-sensitive (51–69% agreement even at >99% confidence) — cross-window agreement is the
  honest confidence measure; (iii) honest negatives — K saturates the truncation (nonparametric machinery
  inert) and there is no beyond-VIX information. A clean, publishable methodological/negative result.
- *Practical tool (Portfolio-Manager):* value is risk-ops, NOT signal — a cheap, low-turnover (13 vs 90
  rebalances/yr), persistent, interpretable volatility-regime label for de-risking guardrails and risk
  communication. Explicitly not a trading signal; dominated on Sharpe by RV30, wins only on turnover/cost.

**Options for next session (Adam to choose — nothing needs doing now):**
1. **Pivot the paper** to the descriptive/methodological + honest-negative framing above (rewrite thesis,
   fix Table 2, drop the backtest-edge claim). Most of the evidence already exists.
2. **Ship the tool, drop the paper** — keep the regime label as a documented risk-ops utility, stop.
3. **New problem for alpha** — accept alpha isn't in index-level vol regimes; it would need a different
   problem (cross-sectional, microstructure, alternative data) — a separate project, not this one.
4. **Shelve** as a rigorous null result; this record stands as the durable account.

---

## Cross-references

- `NOTES.md` — session-to-session state (read first); carries the four findings + audit pointer.
- `.planning/DEEP-REVIEW.md` — code-level causality review (5 fixed bugs) — technical evidence layer.
- `regime-detection.md` — project hub (thesis-status buckets).
- `CLAUDE.md` — architecture, hard constraints, downstream label mapping.
