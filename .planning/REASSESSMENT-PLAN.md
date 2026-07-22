---
phase: reassessment
created: 2026-07-21
depth: deep
scope: reframe the research question from "beyond-VIX / alpha" to "latent-state estimation quality"
status: PLAN — no research code, model, or narrative changed to create this file
supersedes_question: not the findings in RESEARCH-RECORD.md, only the yardstick they are judged against
---

# Reassessment Plan — What Is the HDP-HMM Actually Good At?

The prior audit (`RESEARCH-RECORD.md`, `.planning/RESEARCH-AUDIT.md`) judged the model against a
**beyond-VIX / alpha** yardstick and it failed: no beyond-VIX information (permutation null, 0/4 cells),
no tradeable edge, K saturates, regimes are overdetermined volatility regimes. This plan **keeps every one
of those negatives** and changes only the *question*: an HMM is a latent-state estimator, not an
alpha engine. Judge it as one. All ground-truth numbers below were read from the repo on 2026-07-21, not
from the audit's prose.

---

## Part 1 — Initial Model Assessment (the 14 questions)

1. **What is estimated?** Joint posterior over HMM parameters — sticky-Dirichlet transition rows
   `π_k ~ Dir(α_trans·β + κ·e_k)`, diagonal-Gaussian emissions `μ_k, σ_k`, stick-breaking global weights
   `β`, concentrations `α_dp, α_trans, κ` — with discrete states analytically marginalized
   (Rao-Blackwellized forward algorithm, `hdp_hmm.py:116-130`). Published "labels" are a *plug-in filtered
   posterior* `P(z_t|x_{1:t})` on the SVI posterior-**mean** parameters, argmax'd.
2. **Observed variables?** 4 daily, contemporaneous, expanding-standardized features: `spy_ret`,
   `vol_index` (VIX), `yield_slope` (T10Y2Y), `nfci`. In-sample 2016-01-13→2023-12-29 (N=1991); OOS
   2024-01-02→2026-07-21 (N=635).
3. **What is the latent state?** A region of 4-D standardized feature space with a characteristic
   diagonal-Gaussian mean/scale that the system persists in. Nothing privileges volatility — **diagonal
   emissions mean no within-state cross-feature covariance is modeled at all**; "vol regime" is a post-hoc
   projection.
4. **Why HMM?** Regimes = persistent hidden states with state-dependent emissions (Hamilton 1989). Unlike
   static clustering, transitions are modeled explicitly.
5. **Why HDP-HMM vs fixed-K?** *Intent:* K learned from data (Teh 2006 HDP; Fox 2011 sticky HDP-HMM).
   *Reality:* inert — `effective_K` = mean 8.0 / std 0.0 / mode 8, and `K_max`=8. Saturated.
6. **How inferred?** SVI (AutoNormal mean-field, 4000 steps, lr 0.005) → `posterior_mean_params` → numpy
   forward-backward. NUTS coded, never run. Labels = filtered argmax + 3-day hysteresis.
7. **How labelled?** Two unreconciled schemes: (a) **VIX-rank tertile cut** (`walk_forward.py:27-53` /
   `run_paper_experiments.py:127`) — sort active states by mean VIX, chop into thirds, *always* 3 buckets;
   used by the paper + OOS + ensemble (everything headline). (b) **absolute vol brackets**
   (`hdp_hmm.py:498`) — used by the production stage path; *can* report "no High-Vol today." Both post-hoc.
8. **Causal?** Yes — expanding standardization + forward filtering, mechanically tested (perturb-future /
   assert-past-unchanged, negative control). Genuine strength.
9. **Filtering / smoothing / Viterbi / posterior?** Filtered `P(z_t|x_{1:t})` argmax for *all* published
   labels. Smoothed `P(z_t|x_{1:T})` is computed but used only as a negative control in the causality
   test. No Viterbi.
10. **Evidence states are meaningful?** Clean monotone realized-vol ladder (11.0 / 18.0 / 39.4%), monotone
    VIX (14.2 / 21.3 / 31.2), high within-fit posterior confidence, high self-transition (diag
    0.986/0.984/0.976). Meaningful **along the vol axis**.
11. **Evidence they're unstable?** Cross-training-window agreement 51–69% (in canonical 3-regime space);
    22% disagreement even at >99% within-model confidence; OOS ensemble mean agreement 0.809, only 282/635
    (44%) unanimous; today's live label 2/3.
12. **Evidence they're primarily vol states?** Every feature config — including `{momentum, slope,
    participation}` with **zero implied-vol inputs** — recovers the same vol ladder; every candidate
    feature collapses onto the vol axis at the state level (new-axis ρ ≈ ±0.90–0.99); and the regimes are
    *literally defined by* VIX rank.
13. **Robust prior conclusions (keep):** causal integrity; training-window sensitivity is real; **no
    beyond-VIX information (now confirmed by the committed permutation null — 0/4 cells, vol demoted
    hardest p=0.50/0.73)**; K saturation / HDP inert; no alpha; the vol-ladder separation itself.
14. **Conclusions to reconsider:**
    - The **yardstick**. "No beyond-VIX info" is decisive *only* if the model's job is to beat VIX. As a
      state estimator it is the wrong test.
    - The **stability verdict**. 51–69% is measured *through the brittle VIX-tertile cut*, never
      label-aligned, never resolution-decomposed. Could be "stable coarse / unstable fine."
    - **Persistence**. Never compared against a *static-clustering* baseline under symmetric processing, so
      "does the Markov structure add persistence?" is genuinely untested.
    - RESEARCH-RECORD "Finding C" (beyond-VIX vol info) is now **falsified** by the committed permutation
      test, not merely "downgraded."

---

## Part 2 — Reframed Hierarchy: what the evidence already says (§19 of the brief)

| Step | Question | Status from existing evidence |
|---|---|---|
| 1 | Meaningful latent structure exists? | **Yes, weakly** — along the vol axis (established) |
| 2 | HDP-HMM recovers it? | **Yes** — the vol ladder (established) |
| 3 | Is it stable? | **Unknown / contested** — measured unstable at 3-regime resolution, but never label-aligned or resolution-decomposed. **GAP** |
| 4 | Genuinely temporal (vs static)? | **UNTESTED** — no GMM baseline exists. **The decisive gap** |
| 5 | Does the HDP component add value? | **No on current evidence** (K inert); K_max sweep would make it airtight. **GAP (confirmatory)** |
| 6 | Better than simple vol states? | **Not on information** (established). Reframe: is it a better *representation* (persistence, less whipsaw)? Partly visible, not cleanly tested |
| 7 | Condition future behavior? | Beyond VIX: **no** (permutation). At all: trivially yes (≈VIX). Drawdown / tail / transitions: **untested** |

**Working hypothesis for the strongest defensible contribution:** the sticky HMM is valuable as a
*temporal smoother / state estimator* — it turns a noisy per-day vol clustering into a persistent,
low-turnover, causally-filtered state path — **not** as an information-discovery device. That is Outcome B/C
in the brief. It is currently *asserted* (dwell 66/61/41 vs VIX-threshold 8–17) but not *demonstrated*,
because the only persistence comparison is (i) against VIX-threshold not static clustering, and (ii)
confounded by asymmetric hysteresis. E1+E3 below decide it.

---

## Part 3 — The Research Plan

### Experiments (reframed)

- **E1 — Static vs temporal (GMM baseline). [decisive, cheap, offline]**
  Fit `GaussianMixture(diag)` at K=8 and K=3 on the same 4 standardized features, in-sample and per-fold
  OOS. Compare to the HDP-HMM under **identical** post-processing (same VIX-rank merge; hysteresis ON for
  both and OFF for both) on: mean dwell, regime-changes/yr (whipsaw), within-regime vol ladder, and
  held-out log-likelihood. Isolates how much persistence is the *transition model* vs post-processing.
  *This is the core test of the reframe: does modeling `P(S_t|S_{t-1})` buy a better state path than
  clustering observations independently?* Literature: mixture-vs-HMM; the transition matrix as a temporal
  prior/regularizer on the state sequence.

- **E2 — Stability decomposition (label-aligned + multi-resolution). [cheap; reuses existing files]**
  Reuse the 3 committed per-window OOS label files. (a) Re-measure cross-window agreement with optimal
  label alignment (Hungarian) and report **Adjusted Rand Index** (permutation-invariant). (b) Decompose by
  resolution: 2-regime (calm/stressed) vs 3-regime agreement. (c) [moderate] raw-state agreement across
  windows after alignment. *Is the 51–69% genuine structural instability, or a tertile-cut discretization
  artifact? Is a coarse partition stable?* Literature: ARI (Hubert & Arabie 1985), Hungarian assignment.

- **E3 — Symmetric persistence + honest transition matrix. [cheap] (fixes Findings 1 & 2)**
  Identical smoothing across HDP / GMM / VIX-threshold / fixed-K HMM before any dwell comparison. Report
  the model's **own posterior transition matrix** (`get_transition_matrix`, currently imported-but-unused)
  separately from the empirical smoothed-label matrix. Separates learned κ-stickiness from post-processing.

- **E4 — State-conditional dependence structure. [cheap, offline]**
  Empirically compute `Corr(X | S=k)` among the 4 features per state (the model can't — diagonal
  emissions). *Do the states differ as multivariate **environments** (e.g. a `spy_ret`↔`yield_slope`
  flight-to-quality sign flip in stress), or only in vol scale?* If correlations move, that is genuine
  Outcome-C structure a univariate vol comparison misses. (Sector/breadth version needs network — defer.)

- **E5 — Transitions as a first-class object. [cheap–moderate]**
  Entry/exit asymmetry; transitional vs stable days; does a "just-transitioned" flag or time-since-entry
  condition forward realized vol / drawdown differently than the static state label?

- **E6 — Conditional future risk, NOT beyond-VIX. [moderate]**
  `P(maxDD_{t:t+h} | S_t)` and forward tail (min return, vol-of-vol) by state, multiple horizons, causal
  timing, reported **side by side with a VIX-only benchmark and the permutation null** — so we cleanly
  separate "the state conditions future risk" (likely yes) from "beyond VIX" (likely no).

- **E7 — HDP value: K_max sweep + fixed-K ladder. [expensive: hours of compute]**
  `K_max ∈ {5,8,12,20}` — if `K_eff` tracks `K_max`, data-driven K is confirmed inert. Fixed-K sticky HMM
  ladder K∈{2,3,4,6}, with the degenerate parametric baseline repaired (causal standardizer, more
  restarts, report restart-stability). Compare held-out log-lik, OOS stability, vol ladder.

### (1) Reusable as-is
`scripts/significance_test.py` + `block_bootstrap_ci` / `block_permutation_test` / `regime_delta_r2` (the
honest-null machinery); `walk_forward_oos` / `ensemble_oos`; `regime_stats` / `vol_target_backtest`;
`feature_ablation.fingerprint` (refit-on-arbitrary-subset); the 3 cached per-window OOS label files (E2a/b
need no recompute); cached 4-feature matrices (E1, E4 fully offline). Causal forward-only hmmlearn HMM
(`parametric_hmm.py`) is a usable fixed-K baseline for E7.

### (2) Needs correction
- Stability measured only through the tertile cut, never label-aligned → **E2**.
- Dwell comparison asymmetric smoothing → **E3** (Finding 2).
- Table 2 empirical-count mislabeled "posterior mean"; `get_transition_matrix` unused → **E3** (Finding 1).
- Degenerate parametric HMM baseline (Moderate dwell=367=N) → **E7** repair.
- Two labeling schemes unreconciled → a decision, not an experiment (recommend: absolute brackets as the
  honest primary; rank-thirds only where a fixed 3-bucket structure is structurally required).

### (3) Missing (genuinely new)
GMM static baseline (**E1** — the big one); state-conditional covariance/correlation (**E4**);
transitions-as-object (**E5**); conditional forward-risk incl. drawdown/tail (**E6**); K_max sweep +
fixed-K ladder (**E7**); resolution-decomposed + ARI stability (**E2**).

### (4) Answer first
**E1 + E2 (a,b).** Both cheap and offline; together they decide whether *any* positive contribution
survives the reframe:
- If E1 shows HMM persistence ≈ GMM under symmetric processing **and** E2 shows even coarse regimes are
  unstable → **Outcome A/B**: "sophisticated re-description of the vol axis with no temporal edge" — write
  the honest null and stop.
- If E1 shows the HMM meaningfully out-persists the GMM **and** E2 shows a coarse calm/stressed partition
  is stable → **Outcome C**: a real "persistent, stable, causal vol-state estimator" contribution —
  proceed to E3–E6, then E7.

### (5) Evidence that would change the overall conclusion
- HMM dwell/whipsaw ≈ GMM under identical processing → temporal machinery adds nothing → collapses the
  last positive claim toward Outcome A/B.
- Coarse 2-regime cross-window ARI high (≳0.8) → rescues a stable calm/stressed-regime claim (Outcome C).
- `K_eff` tracks `K_max` in the sweep → nonparametric claim dead (drop HDP framing, right-size to sticky
  fixed-K HMM).
- `Corr(X|S=k)` moves materially across states (e.g. equity/rates correlation flips) → genuine
  multivariate-environment finding → strengthens Outcome C beyond "just vol."
- Forward drawdown/tail conditioned on state significant vs a VIX-only benchmark under permutation →
  partial rescue of conditioning value.
- Model's own posterior transition diagonals high on *raw* (unsmoothed) labels → persistence is genuinely
  learned, not a hysteresis artifact → supports the persistence claim honestly.

---

## Guardrails (unchanged)
Causal timing everywhere; discovery/validation separated; block resampling for serially-correlated
targets; permutation null (not just bootstrap CI) for `ΔR²`-type statistics; multiple-testing awareness;
`paper.tex` and the `RESEARCH-RECORD.md` narrative untouched until the experiments land.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
