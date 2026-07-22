---
phase: research-audit
audited: 2026-07-21
depth: deep
scope: full-repository research reconstruction + statistical-validity audit
auditor: Claude (Opus 4.8) — senior-quant / research-SWE review
status: thesis PARTIALLY SUPPORTED (see §19)
do_not_modify: this audit changed no source code (read-only phase)
---

# Research Audit — Regime-Detection HDP-HMM

> **Note (2026-07-21):** The durable research narrative now lives at the repository root in
> `RESEARCH-RECORD.md`. This file is retained unchanged as the detailed technical evidence behind that
> record (full 25-section audit, tables, repository map). Read `RESEARCH-RECORD.md` first.

**One-line verdict:** The repository is a genuine, mostly-clean regime-*discovery* system whose
causal plumbing is now sound, but whose **published thesis (persistence + backtest edge) runs
ahead of its own evidence**, whose **HDP nonparametric machinery is not demonstrably earning its
complexity**, and whose **single most defensible result (regimes predict future volatility) is not
reproducible from any committed script**.

---

## Executive Summary

This project has two heads: a paper ("markets have latent states not recoverable from VIX alone")
and a practical tool (regime labels for Portfolio-Manager). Over ~2.5 months (May–July 2026) it went
from a PCA/GARCH kitchen-sink to a stripped 4-feature sticky HDP-HMM, then through a hard causality
clean-up, then to walk-forward OOS validation, then to a self-correcting sequence of findings
(training-window sensitivity → hysteresis mismatch → a pivot away from backtest-Sharpe toward a
volatility-information significance test).

The most important thing to understand: **the paper (`paper.tex`, "upload-ready") is a snapshot from
before the project's most rigorous work.** Its three headline contributions are, in light of the
later evidence:

1. **Persistence advantage (dwell 66/61/41 vs 8–17 days)** — *partly a measurement artifact.* HDP
   labels are hysteresis-smoothed (3-day hold); the VIX-threshold and parametric-HMM baselines it is
   compared against are not. This is the *same class of bug* the team already found and fixed for the
   OOS labels — but the inverse asymmetry is still baked into the paper's in-sample headline.
2. **Backtest Sharpe edge (0.624 vs 0.606)** — *does not replicate OOS* (the project's own walk-forward
   found HDP 1.062 vs B&H 1.098 — HDP trails). The paper reports it in-sample without this caveat.
3. **3.6× volatility spread across 3 "discovered" regimes** — *the 3 regimes are not discovered by the
   HDP.* The nonparametric model pins at K=8 every run; the 3 regimes are imposed by sorting those 8
   states on **VIX** and cutting into thirds. The published regimes are, definitionally, a VIX
   partition — which sits awkwardly against the thesis that the structure is "not recoverable from VIX."

What *is* defensible, and is the strongest honest thesis: **the regime label carries a small but
statistically significant amount of information about future realized volatility (ΔR² ≈ 0.012, 90% CI
excludes zero under a block bootstrap), and almost none about future return direction (ΔR² ≈ 0.0008).**
That is a real, publishable, narrower claim — but its supporting numbers currently exist only in prose.

Causal integrity is now good (5 lookahead bugs fixed + a causality-invariant test suite). The audit
found **no new look-ahead bug in the code**, but several **framing/measurement issues** that matter
more for a paper than a trading system. Detail below.

---

## 1. What This Repository Actually Is

A **research + thesis environment**, not a production trading system, despite the "practical tool"
framing. Concretely:

- A single-author academic-paper pipeline (`run_paper_experiments.py` → LaTeX tables/macros →
  `paper/paper.tex`) that fits one sticky HDP-HMM on 2016–2023 and generates Tables 1–5 + 4 figures.
- A causal, walk-forward OOS harness (`src/core/walk_forward.py`) that refits quarterly on an expanding
  window and produces `data/oos_regime_labels.csv` — a 3-window ensemble with a cross-window
  agreement fraction as its honest confidence measure.
- A small CLI (`scripts/run.py`) meant to surface "what regime are we in today" for downstream use.
- ~12 source files, 2 test files, 6 archived codebase-map docs (`.planning/codebase/`, stale), one prior
  deep code review (`.planning/DEEP-REVIEW.md`), rich session logs in `NOTES.md`.

It is small, legible, and — after the July causality work — internally honest with itself in `NOTES.md`.
The gap is between that honest internal record and the *external-facing paper*, which has not been
updated to match.

---

## 2. Original Research Thesis

From `CLAUDE.md` and the earliest paper framing:

- **Research question:** Can a Bayesian nonparametric model recover more stable, economically coherent
  market regimes from a small macro-financial feature set than a VIX threshold can?
- **Thesis:** *"Markets have latent states not directly observable from any single indicator — a
  Bayesian HDP-HMM can recover them."*
- **Null hypothesis (the thing to beat):** *"Regimes are just VIX thresholds."*
- **Why HMM:** regimes = persistent hidden states with state-dependent emissions; Hamilton (1989)
  regime-switching is the canonical frame.
- **Why HDP-HMM:** so the number of regimes K is *learned from data* rather than fixed, avoiding the
  fragmentation/aggregation failure mode of misspecified fixed-K HMMs (Dacco & Satchell 1999).
- **Why sticky (Fox 2011):** encode the prior that real regimes persist (κ self-transition boost),
  countering the HDP-HMM's known tendency to create rapidly-switching redundant states.
- **What was expected:** ~3 economically interpretable regimes (Low/Moderate/High vol), persistent,
  separable in realized-vol space, and carrying information VIX alone does not.

**Explicitly stated hypotheses:** persistence advantage over VIX thresholds; distinct within-regime
vol; information content beyond VIX; practical volatility-targeting utility.

**Implicitly assumed hypotheses** (never separately tested):
- That the 3 canonical regimes are *discovered* rather than *imposed* by the VIX-rank merge. (They are
  imposed — see §5, §16.)
- That K is genuinely inferred. (It saturates the truncation — see §15.)
- That the SVI posterior mean is an adequate stand-in for "the Bayesian posterior." (Mean-field, single
  point used — see §5.)
- That in-sample regime characteristics transfer OOS. (Partly false — see §13.)

---

## 3. Reconstructed Research History

Timeline from git (`git log`, dates are commit dates):

| Date | Commits | What happened | Branch status |
|---|---|---|---|
| 2026-05-05 → 05-11 | f14a9d7 … 04a3c31 | **Kitchen-sink era.** 23 computed features, PCA, GARCH references; `gsd-map-codebase` produced the 7-doc `.planning/codebase/` map. | HISTORICAL |
| 2026-05-10 | d6b0f14, 9c28005, 9f6a0d6, 58d89ce | **The Strip-Down.** Pipeline rewritten to 4 features, no PCA; rank-based naming replaced by absolute vol brackets (58d89ce — note: later *partly reverted* in practice, see §5). | Defines current core |
| 2026-05-24 | 4fe1733 … 21278c4 | **Paper era begins.** Aligned to 4-feature architecture; paper experiment runner + LaTeX + backtest Table 4 skeleton. | CORE |
| 2026-05-26 | 0bdca4e … 1a324d9 | Figures, descriptive stats, manuscript finalized; VIX-Thr removed from backtest fig; Overleaf compile fixed. | CORE (paper) |
| 2026-06-06 | b80e812 | `paper.tex` removed from repo (moved to Overleaf) — *later restored*; `paper_overleaf.zip` is the shipping artifact. | — |
| 2026-07-18 | 6920c7f, 0f38678, 70849ae | CLI wrapper (`scripts/run.py`) + README rewrite, pushed from a second machine. | CORE (tooling) |
| 2026-07-20 → 07-21 | 185ae8d | **Causality deep-review.** 5 critical lookahead/correctness bugs fixed (`.planning/DEEP-REVIEW.md`). Table 4 Sharpe 0.736→0.624 (removing lookahead). | CORE (correctness) |
| 2026-07-21 | 8dc349c, 94cefd8 | Merge of the two branches; **causality-invariant test suite** added (perturb-future / assert-past-unchanged). | CORE (validation) |
| 2026-07-21 | d4f4872, 5955673 | **Walk-forward OOS implemented** (was a no-op stub). First real live signal produced. Dwell + backtest edge shrink vs in-sample. | CORE (current direction) |
| 2026-07-21 | 8b06545, 22868bc, 9936a0a | **Training-window sensitivity discovered** (51–69% agreement across window lengths, even at >99% individual confidence) → single-window replaced by 3-window ensemble. | CORE (current direction) |
| 2026-07-21 | e6962df, fa20c37, ccf89ee, 8e2d637, 0126d32 | **Evaluation pivot:** block-bootstrap significance test (ΔR²) replaces "beat buy-and-hold"; **hysteresis mismatch** between in-sample (smoothed) and OOS (raw) labels found + fixed; OOS ensemble regenerated. | CURRENT FRONTIER |

Reconstructed intellectual arc:

```
Thesis: HDP-HMM recovers VIX-independent latent regimes
  → Built kitchen-sink (PCA/GARCH), rejected as un-defensible → stripped to 4 features
  → Fit one in-sample HDP-HMM, wrote paper (persistence + backtest edge + 3.6× vol spread)
  → Audited causality: found+fixed 5 lookahead bugs; backtest edge shrinks (0.736→0.624)
  → Built walk-forward OOS: backtest edge does NOT replicate (1.062 vs 1.098); dwell shrinks
  → Asked "why does dwell shrink?" → found training-window sensitivity (bigger problem)
  → Built 3-window ensemble; found part of the dwell gap was a hysteresis measurement mismatch
  → Pivoted the whole evaluation: not "does it trade well" but "does the label carry real info"
  → Answer: significant volatility info (ΔR²≈0.012), negligible return info (ΔR²≈0.0008)
```

The project has been **self-correcting in the honest direction** (each step made the claims smaller and
truer). The paper simply hasn't caught up to the last four steps.

---

## 4. Current Research Thesis (as the code+notes actually support it)

> *Equity markets exhibit persistent latent volatility states that a sticky HMM can detect causally and
> out-of-sample. Knowing the current state carries a small, statistically significant amount of
> information about **future realized volatility**, and essentially none about future return direction.
> The state assignment is, however, materially sensitive to the training-window length — more than any
> single model's posterior confidence reveals — so the honest confidence measure is cross-window
> agreement, not filtered posterior probability.*

This is narrower and more defensible than the paper's thesis. See §17–19.

---

## 5. What the HDP-HMM Actually Does (Model + Mathematics)

### 5.1 Generative model (`src/core/hdp_hmm.py:hdp_hmm_model`)

Truncated sticky HDP-HMM, Gaussian emissions, K_max = 8:

- **Global weights (GEM / stick-breaking):**
  α_dp ~ Gamma(0.5, 2.0); v_k ~ Beta(1, α_dp) for k=1..K_max−1; β = stick_breaking(v).
  β is the shared "menu" of state popularities.
- **Sticky transitions:** κ ~ Gamma(2.0, 0.2) (prior mean 10); α_trans ~ Gamma(1.0, 1.0);
  π_k ~ Dirichlet(α_trans·β + κ·e_k). The κ·e_k term adds mass to the diagonal → self-persistence.
  **κ is a learned latent, not a fixed hyperparameter** (the dead `HDP_KAPPA=10` constant was removed in
  CR-02). This is correct and matches paper.tex:289.
- **Emissions (diagonal Gaussian):** μ_k ~ Normal(0, 3) per dim; σ_k ~ HalfCauchy(2) per dim;
  x_t | z_t=k ~ N(μ_k, diag(σ_k²)). Diagonal covariance = features assumed conditionally independent
  given the state (a real modeling assumption — yield-slope/NFCI co-movement within a state is not
  modeled).
- **Likelihood:** discrete states are **marginalized analytically** via the forward algorithm in
  `lax.scan` (Rao-Blackwellized — states are never sampled). This is the right, numerically stable
  choice. `numpyro.factor('log_likelihood', total_ll)`.

So the model *is* estimating P(z_t | z_{t-1}) (sticky Dirichlet rows) and P(x_t | z_t) (Gaussian) — a
standard HMM, wrapped in an HDP prior over the transition rows. Nothing more exotic.

### 5.2 Inference (what is *actually* run for the paper)

- **SVI, AutoNormal guide, 4000 steps, lr 0.005** (`_fit_svi`). AutoNormal = **mean-field Gaussian in
  unconstrained space** — it factorizes across all latents and ignores posterior correlations (e.g.
  among the Dirichlet transition rows, among stick-breaking v's). It is a *unimodal* approximation.
- **NUTS exists (`_fit_nuts`) but has never been run for the paper** (NOTES + config confirm SVI-only).
- Convergence: a crude ELBO-plateau check (rel. change of last-200 vs prior-200 mean < 5%). Reported
  converged, final ELBO ≈ 6382.

### 5.3 From posterior to labels (the critical, under-appreciated path)

1. `posterior_mean_params()` takes the **mean over SVI draws** of β, trans_matrix, locs, scale_diag.
   *This is safe only because AutoNormal is unimodal* — there is no label-switching within one SVI fit.
   **⚠ If NUTS is ever used (as planned), naive `.mean(axis=0)` over multi-chain samples will average
   across permuted state labels and produce garbage.** See §12/§25.
2. `forward_backward_numpy()` runs a plug-in forward-backward on those *point-estimate* params. It
   returns both **filtered** P(z_t | x_{1:t}) (causal) and **smoothed** P(z_t | x_{1:T}) (non-causal).
3. **Labels use the *filtered* posterior argmax** (`get_labels_and_probs` → `filt_active.argmax`). Good —
   the historical labels are causal (P(z_t | x_{1:t})), not smoothed. This is the correct choice and is
   explicitly tested (`test_causality_invariants.py`).
4. `_apply_hysteresis(hold_days=3)` suppresses <3-day flicker.
5. **State→regime mapping — two different, unreconciled methods:**
   - `label_regimes_hdp()` (absolute VOL_BRACKETS): each state named by its own realized vol; *can*
     legitimately report "no High-Vol regime today." Used by `stage_train_hmm` (the "production" path).
   - `merge_states_to_regimes()` (VIX-rank thirds): sort active states by mean VIX, `min(int(i·3/K),2)`.
     **Always yields exactly 3 non-empty buckets including High-Vol, by construction.** Used by
     `run_paper_experiments.py` and the entire walk-forward/ensemble/paper path.

**What the model believes a "state" is:** a region of the 4-D standardized feature space with a
characteristic Gaussian mean/spread, that the system tends to stay in. Nothing in the model privileges
"volatility" — the *naming* as vol regimes is entirely a post-hoc projection onto VIX rank (or vol
brackets). This is the crux of §16.

---

## 6. Data and Feature Audit

Source: `src/data/collect_macro.py`. Daily, 2015-01 → 2026-07 (train ≤ 2023-12-31, N=1991 after warmup).

| Feature | Source | Freq | Transform | Timing at decision | Descriptive/Predictive | Notes |
|---|---|---|---|---|---|---|
| `spy_ret` | yfinance ^GSPC | daily | log return | contemporaneous (x_t = day-t return) | Descriptive | Also the eventual prediction target family → mild circularity if used to "predict" returns |
| `vol_index` (VIX) | yfinance ^VIX | daily | level | contemporaneous | Descriptive of implied vol; mildly predictive of realized vol | The very variable the null hypothesis uses AND the merge sorts on |
| `yield_slope` | FRED T10Y2Y | daily | level (10y−2y) | contemporaneous, real-time series | Predictive-ish (slow macro cycle) | Fine |
| `nfci` | FRED NFCI | weekly→ffill | level | **+7-day publication-lag shift then ffill** | Predictive-ish (financial stress) | CR-01 fix is an *approximation* of true ALFRED vintage release dates |

- **Standardization:** `expanding_standardize` — cumulative mean/std using only [0..t], first 252 rows
  NaN'd. Causal, correct, and tested. Computed once over the full series then sliced (safe because it is
  causal by construction).
- **Stationarity:** spy_ret ~ stationary; VIX/NFCI/slope are persistent, near-unit-root levels. The
  Gaussian emission on *levels* (after expanding z-score) is a modeling simplification; regimes will
  partly track slow drifts in these levels.
- **⚠ Paper inaccuracy:** `paper.tex:153` states the four features are "all lagged one day to ensure
  causal inference." **They are not lagged** — they are contemporaneous, and causality comes from
  expanding standardization + forward filtering (P(z_t | x_{1:t}) legitimately uses x_t). The sentence
  is false as written and should be corrected to describe the actual causal mechanism.

**Verdict:** features are primarily **descriptive** of the current environment. VIX and NFCI have weak
predictive content for *future volatility*; none has meaningful predictive content for *future return
direction* (consistent with Table 3 and the OOS significance test).

---

## 7. Look-Ahead and Leakage Audit

The heavy lifting was done in `.planning/DEEP-REVIEW.md` (5 criticals, all fixed + tested). I
re-verified the current state and looked for anything new.

| Issue | Location | Severity | Status |
|---|---|---|---|
| NFCI reference-date vs release-date ffill | collect_macro.py | ~~Critical~~ | **Fixed** (CR-01, 7-day shift; approximation) |
| Parametric-HMM baseline used smoothed posteriors | parametric_hmm.py | ~~Critical~~ | **Fixed** (CR-03, manual forward-only) |
| Table-4 backtest sized on full-sample per-regime vol | inference.py/runner | ~~Critical~~ | **Fixed** (CR-04, `expanding_regime_vol`, tested) |
| VIX-rank partition could drop High-Vol if K<3 | runner | ~~Critical~~ | Stopgap `assert K_eff>=3` |
| Historical labels use filtered (not smoothed) posterior | hdp_hmm.py | — | **No issue** — correct + tested |
| `.bfill()` on RV30 warmup | runner:250,282 | **Low** | WR-01 still open; ~30/1991 rows; RV30 is a baseline |
| In-sample fit → in-sample Tables 1/4 | runner | **Low (disclosed)** | Paper says "all backtests in-sample"; not leakage, but in-sample optimism |
| VIX-rank merge uses full-sample mean VIX per state | runner | **Low (in-sample only)** | Fine for in-sample tables; walk-forward redoes it per fold |
| Averaging SVI draws of locs/trans | hdp_hmm.py | **No issue now / Medium if NUTS** | Safe for unimodal SVI; will break under NUTS label-switching |

**New finding:** none of *code* look-ahead. The remaining exposure is **in-sample optimism** in the
paper tables (the model is fit on the whole 2016–2023 window and then characterized on that same
window), which the paper discloses but which the walk-forward OOS numbers should now supersede in the
narrative. **Rating: No new Critical/High leakage. Causal integrity is genuinely good.**

---

## 8. Regime Discovery Methodology (traced end-to-end)

```
yfinance/FRED → collect_macro (NFCI lag-shift, ffill, align to SPX days)
  → expanding_standardize (causal z-score, 252-row warmup)
  → SVI fit of sticky HDP-HMM (K_max=8, 4000 steps)  [full training sample OR per-fold window]
  → posterior_mean_params (mean over SVI draws — unimodal-safe)
  → forward_backward_numpy → FILTERED P(z_t|x_{1:t})  [causal]
  → prune_states (β>0.08 AND >max(1%,10) days; fallback top-3) → K_eff (=8 every observed run)
  → argmax → _apply_hysteresis(hold_days=3)
  → merge_states_to_regimes: sort 8 states by mean VIX, cut into thirds → {Low,Mod,High}
```

- **State at t depends on x_{1:t} only** for the published labels (filtered). ✔
- The **smoothed** P(z_t | x_{1:T}) is computed and returned but *not* used for labels (only, correctly,
  as a negative control in the causality test). ✔
- **The regime definition is not the model's** — it is the VIX-rank tertile cut applied *after* the
  model. This is the single most important methodological fact in the repo (see §16).

---

## 9. Regime Fingerprints (in-sample, from `results/paper_results.txt`)

Anti-bias exercise: strip the names and describe what the numbers say.

| "Regime" (VIX-rank tertile of 8 states) | N (%) | Ann. Ret | Ann. Vol | Sharpe | Avg VIX | Dwell* |
|---|---|---|---|---|---|---|
| Bucket 0 ("Low-Vol") | 988 (49.6%) | +8.95% | **10.97%** | +0.82 | 14.2 | 65.9 |
| Bucket 1 ("Moderate-Vol") | 796 (40.0%) | +11.41% | **18.01%** | +0.63 | 21.3 | 61.2 |
| Bucket 2 ("High-Vol") | 207 (10.4%) | +22.61% | **39.37%** | +0.57 | 31.2 | 41.4 |

\* dwell measured on **hysteresis-smoothed** labels — see §11/§12.

**What an unbiased reader would call these:** three points on a **volatility ladder** (11% / 18% / 39%
realized vol; 14 / 21 / 31 avg VIX). They are essentially *ordered by volatility and by VIX
simultaneously* — which is unsurprising, because they were **constructed by sorting on VIX.** The
positive mean return even in "High-Vol" (+22.6% ann.) reflects the filtered-label timing capturing
rebound days inside stress periods, not a distinct return regime.

Crucially: the fingerprints do **not** reveal a dimension VIX misses. If the thesis were fully carried,
we would expect at least one state that is (say) *calm VIX but tight financial conditions* or *low VIX
but inverted curve* — a state the VIX ladder cannot see. **That analysis has never been done on the raw
8 states** (the object that could actually support the thesis). See §16 and §25 (Experiment 1).

---

## 10. Statistical Regime Validation

- **What exists:** `regime_stats` (within-regime mean/vol/Sharpe/dwell), and the honest
  `block_bootstrap_ci` + `regime_delta_r2` (21-day block bootstrap of the ΔR² of regime dummies beyond
  VIX). Block bootstrap is the *correct* choice given VIX AC(1)≈0.9 — an i.i.d. bootstrap would
  understate variance and manufacture significance.
- **What has been tested (per NOTES, on the OOS ensemble labels):**
  - Forward 5-day return: ΔR² = 0.00077, 90% CI [0.0002, 0.0097] — significant but *tiny*.
  - Forward 21-day realized vol: ΔR² = 0.0124, 90% CI [0.0017, 0.0665] — significant, ~16× larger.
- **⚠ Reproducibility gap (HIGH):** `block_bootstrap_ci`/`regime_delta_r2` are **called by no committed
  script** (grep-confirmed: only referenced in docstrings + NOTES/hub/CONCERNS). The project's most
  defensible result is not regenerable. Fix is trivial (a ~30-line `scripts/significance_test.py`) and
  is the highest-value small change in this audit (§21, §25).
- **What is missing:** proper multiple-testing awareness (two horizons × two targets tested), and a
  *strict permutation null* (shuffle regime relative to target) as opposed to a block-resample of the
  observed data. NOTES already flags the latter honestly. ANOVA/Kruskal-Wallis across regimes on
  realized vol would be a cheap, standard addition for the paper.
- **Statistical vs economic significance:** ΔR²=0.012 for vol is statistically significant and
  economically *modest* — it is a real signal, not a tradeable edge on its own. The correct framing is
  "the label is an informative volatility state indicator," not "the label predicts vol well."

---

## 11. Regime Persistence

- Reported transition matrix (`results/transition_matrix.csv`, Table 2): diagonals **0.986 / 0.984 /
  0.976** ⇒ implied expected durations 1/(1−p) ≈ 70 / 61 / 42 days.
- **⚠ HIGH — Table 2 is mislabeled and its persistence is partly manufactured:**
  - The paper caption calls it the "posterior-mean transition matrix" and the prose (paper.tex:288–289)
    says persistence "is not imposed by the model: it emerges … via the learned κ." **But
    `run_paper_experiments.py:133–137` computes Table 2 as an *empirical transition-frequency count on
    the merged, hysteresis-smoothed 3-state labels* — not `params['trans_matrix']`** (the actual
    posterior-mean model matrix; `get_transition_matrix()` exists precisely for this but is never used
    for Table 2).
  - Consequences: (a) the 3-day hysteresis mechanically inflates the diagonal (flicker suppression =
    higher self-transition frequency by construction); (b) collapsing 8 states→3 by VIX absorbs all
    within-tertile state switches into the diagonal. So a meaningful fraction of the reported
    "stickiness" is **post-processing, not learned κ.** The model *is* sticky, but Table 2 does not
    measure that.
  - Minor add-on: the prose hardcodes diagonals "0.989, 0.986, 0.974" which don't match the regenerated
    table (0.986/0.984/0.976) — stale numbers in prose.
- **The honest persistence statement** requires reporting the model's own posterior κ / `get_transition_
  matrix()` diagonals on the *raw* (unsmoothed) filtered labels, and applying identical smoothing to all
  baselines before any dwell comparison.

---

## 12. Regime Stability

- **Across posterior draws (within one fit):** `hdp_stability_check` measures label agreement across SVI
  draws — a within-fit robustness check. Fine, but weak (unimodal guide ⇒ high agreement is nearly
  guaranteed).
- **Across training-window length (the important axis):** the project's own headline finding —
  expanding vs 5y vs 3y windows agree on the label only **51–69%** of the time, and **disagree 22% even
  on days where both windows individually report >99% posterior confidence.** This is *structural
  instability*, not mere label-switching: the same date is genuinely assigned different vol regimes
  depending on how much history the model saw. Today (2026-07-21) is a live example — Low-Vol at only
  2/3 agreement (the 3-year window says Moderate-Vol).
- **Label-switching vs structural instability:** the ensemble's cross-window disagreement is *canonical-
  space* (Low/Mod/High), so it is genuine structural instability, not index permutation. Good that the
  team caught this.
- **⚠ NUTS caveat (Medium, pre-emptive):** the planned NUTS run will introduce cross-chain label
  switching; `posterior_mean_params`'s naive averaging will silently corrupt. Must relabel before
  averaging, or decode per-draw then align.

**Verdict:** the discovered regimes are **persistent within a fit but not stable across reasonable
training-window choices.** This is the most scientifically interesting (and most under-reported in the
paper) property of the system.

---

## 13. Out-of-Sample Validation

`walk_forward_oos` (expanding, refit every 63 days, forward-filter only, hysteresis threaded across fold
boundaries in canonical space) + `ensemble_oos` (3 windows, majority vote + agreement_frac). 635 OOS
days, 2024-01-02 → 2026-07-21.

- **Distribution OOS:** Moderate 55% / Low 38% / High 6% — a different mix than in-sample (50/40/10).
- **Dwell OOS (post-hysteresis-fix):** ~34 / 26 / 15 days — much shorter than in-sample (66/61/41). The
  hysteresis fix roughly doubled High-Vol dwell (8→15) but did not close the gap. Residual gap is
  attributed (not decomposed) to genuine 2024–26 calm + window sensitivity.
- **Backtest OOS:** HDP vol-target Sharpe 1.062 vs B&H 1.098 — **HDP trails.** The in-sample edge (0.624
  vs 0.606) does not replicate. (Both high because 2024–26 was a bull run; only the relative comparison
  is meaningful.)
- **The one thing that survives OOS:** the volatility-information ΔR² significance result (§10),
  computed on these genuinely-OOS ensemble labels.

**Verdict:** OOS validation exists and is honest. It *falsifies* the paper's backtest-edge and
undercuts the magnitude of the persistence claim, while *confirming* a narrow volatility-information
claim.

---

## 14. Predictive Information

Per the requested conditional-distribution framing P(r_{t+h}|S_t=k), P(σ_{t+h}|S_t=k):

- **Return direction (r_{t+h}):** negligible. In-sample Table 3 ΔR² = +0.0000 at h=5; OOS ΔR² = 0.00077.
  The regime is **not return-predictive.**
- **Future realized volatility (σ_{t+h}):** small but significant. OOS ΔR² = 0.0124 at h=21 (beyond
  VIX). The regime is **weakly volatility-predictive** — and, importantly, adds a little *beyond VIX*.
- **Drawdown / P(r<0):** not yet evaluated (Experiment 3, §25).

**Classification:** the regime is **descriptive + weakly risk(vol)-predictive**, and **not
return-predictive.** This is exactly what the literature expects and what a sister project
(algo-trading-bot) independently concluded ("HMMs ceiling out at classification, not timing").

---

## 15. HDP-HMM vs Simpler Models

- **The parametric K=3 HMM baseline is present but degenerate**, so the current comparison is unfair *to
  the baseline*: its "Moderate-Vol" state has N=367 and dwell=367.0 — i.e. it fired as a **single
  contiguous 367-day block** (a collapsed/absorbing state from a bad EM local optimum, despite 10
  restarts). Table 1's Param-HMM column therefore cannot support "HDP beats fixed-K HMM."
- **No K=2 / K=4 sticky comparison exists.** The audit brief's core question (does HDP structure beat
  simpler HMMs on fit / stability / OOS reproducibility) is **not currently answered by the repo.**
- **Decisive observation:** `effective_K` reports **mean 8.0, std 0.0, mode 8** — the HDP uses **all 8
  truncation states on every run** and `prune_states` keeps all 8. The nonparametric prior is **not
  selecting K** here; it is saturating the truncation ceiling, and the real K-reduction to 3 is done by
  the hand-coded VIX-rank tertile cut. Raising K_max would very likely just yield more raw states.

**Implication:** on the current evidence, the HDP's defining benefit (data-driven K) is **inert.** A
fixed-K sticky Gaussian HMM (K=3 or K=8) fed the same 4 features and the same VIX-rank collapse would
almost certainly reproduce the same three vol regimes.

---

## 16. Is the HDP Component Justified?

**On current evidence: not demonstrably.** Reasoning:

1. K is not being inferred (saturates at K_max — §15).
2. The published regimes are defined by a VIX-rank cut *after* the model, not by the HDP (§5, §8).
3. The only surviving quantitative claim (vol ΔR²) is a property of *having vol-ordered state labels*,
   not of the *nonparametric* machinery specifically — a fixed-K HMM would plausibly match it.
4. The extra complexity has real costs already biting: SVI mean-field approximation, ~8-min-per-window
   refits (×3 windows = ~24 min), training-window instability, and the label-switching landmine for the
   planned NUTS run.

**This does not mean "delete the HDP."** It means the HDP's value is currently *asserted, not
demonstrated*, and the paper's framing ("the HDP prior allows K to be inferred from the data") is not
supported by the runs (K is pinned). Two honest paths (see §17, §20):
- **(A) Demonstrate the value:** run the K=2/3/4/6 sticky-HMM ladder and an HDP with higher K_max, and
  show — on held-out log-likelihood, OOS label stability, and vol-ΔR² — that the HDP's flexibility earns
  its complexity. If it does, the thesis strengthens materially.
- **(B) Right-size the model:** if a fixed-K sticky HMM matches, the defensible paper becomes "a *sticky
  HMM* detects persistent vol states with cross-window-honest confidence" — dropping the nonparametric
  claim entirely. Less novel, more true.

---

## 17. What Has Actually Been Proven

Ranked by strength of evidence:

1. **Causal integrity of the pipeline** — the standardization, per-regime vol, filtering, and parametric
   baseline are genuinely no-lookahead, and this is *mechanically tested* (perturb-future / assert-past-
   unchanged, with a negative control). Strong.
2. **Regime assignment is training-window-sensitive** — 51–69% cross-window agreement, disagreement even
   at >99% individual confidence. Strong, quantified, honestly reported.
3. **The regime label carries significant *volatility* information beyond VIX (ΔR²≈0.012, block-
   bootstrap CI excludes 0), and negligible *return* information (≈0.0008)** — computed on genuinely-OOS
   ensemble labels. Moderately strong (weakened only by the reproducibility gap and permutation-null
   caveat).
4. **The states form a clean realized-vol ladder (11/18/39%)** — true, but partly circular given VIX-
   rank construction (§9).

---

## 18. What Has NOT Been Proven

1. **That regimes are "not recoverable from VIX alone"** — the published regimes are *defined by VIX
   rank*; no analysis isolates VIX-independent structure (would need the raw-8-state fingerprints and/or
   an ablation dropping VIX from the feature set).
2. **That the HDP (nonparametric K) beats a fixed-K sticky HMM** — no fair comparison exists; the one
   baseline is degenerate; K is not actually inferred (§15).
3. **The persistence *advantage* magnitude** — confounded by hysteresis-smoothed-vs-raw label
   comparison and by the merge absorbing within-tertile switches (§11).
4. **Any out-of-sample economic/backtest benefit** — OOS HDP trails buy-and-hold (§13).
5. **Full-posterior uncertainty quantification** — SVI mean-field point estimate only; NUTS never run;
   no uncertainty bands actually reported despite the framing (§5).
6. **That the live signal is reliable** — today's own label is 2/3 agreement (§13).

---

## 19. Thesis Assessment

| Claim | Verdict |
|---|---|
| Pipeline is causal / no-lookahead | **Supported** |
| Regime labels are training-window-sensitive; agreement is the honest confidence | **Supported** |
| Regime carries significant *volatility* info beyond VIX, negligible *return* info | **Partially Supported** (real, but not reproducibly scripted; needs permutation null + multiple-testing) |
| Regimes are persistent (sticky) states | **Partially Supported** (model κ is learned+real; but reported Table 2 persistence is inflated by hysteresis+merge) |
| Regimes are "not recoverable from VIX alone" (the headline thesis) | **Inconclusive / Not Yet Tested** (final regimes are literally a VIX-rank partition; VIX-independent structure never isolated) |
| HDP nonparametric structure is justified over a simpler HMM | **Unsupported on current evidence** (K saturates; no fair baseline) |
| Volatility-targeting backtest edge (paper Table 4/5) | **Invalid for OOS claims / in-sample-only** (does not replicate OOS) |
| Paper's persistence-*advantage magnitude* (66/61/41 vs 8–17) | **Partially Invalid Due to Methodological Issue** (smoothed-vs-raw comparison) |

**Overall: the *narrow* thesis (persistent, causally-detectable vol states with modest vol-information
content, honestly uncertain) is Partially Supported. The *headline* thesis (VIX-irrecoverable latent
structure recovered by a nonparametric model) is Not Yet Established** — mostly because the experiments
that would establish it (raw-state fingerprinting, VIX-ablation, fixed-K comparison) have not been run,
and the labeling method actively works against it.

---

## 20. Recommended Research Architecture

Adopt the audit's intended progression explicitly, and **stop treating `paper.tex` as done**:

```
Discover (raw K-state HDP) → Validate (stability, OOS, significance)
  → Interpret (raw-state fingerprints, VIX-ablation) → Predictive info (vol, drawdown)
  → Model justification (HDP vs fixed-K ladder) → THEN policy/backtest → THEN OOS policy
```

- Separate **two deliverables** cleanly: (i) a *methods/validation* paper built on the OOS ensemble +
  significance test + window-sensitivity (this is the honest, novel-enough contribution); (ii) the
  in-sample descriptive tables as *illustration*, clearly flagged in-sample.
- Make **cross-window agreement**, not filtered posterior, the headline confidence object — it is the
  project's most original empirical finding.
- Demote the backtest to "illustrative, in-sample, does not replicate OOS" or cut it.

---

## 21. Recommended Code Changes

**Explicitly deferred (audit is read-only): none applied.** Prioritized for Adam's decision:

### Critical (do before any external submission)
- **C1. Fix the dwell/persistence comparison asymmetry.** Apply identical hysteresis (or none) to HDP,
  VIX-threshold, and parametric-HMM labels before comparing dwell times; and report the model's *own*
  posterior transition matrix (`get_transition_matrix`) separately from any empirical smoothed-label
  matrix. Relabel Table 2 accurately. (Addresses §11, §18.3.)
- **C2. Add `scripts/significance_test.py`** that calls `regime_delta_r2` + `block_bootstrap_ci` on
  `data/oos_regime_labels.csv` and writes the ΔR² CIs to `results/`. Makes the project's best result
  reproducible. (Addresses §10 reproducibility gap.)
- **C3. Correct the paper's false "features lagged one day" sentence** (paper.tex:153) and the stale
  hardcoded transition diagonals (paper.tex:313). (Addresses §6, §11.)

### Research improvements (change what we believe)
- **R1. Raw-state fingerprints + VIX-ablation** (Experiment 1, §25) — the experiment that could actually
  support or kill the headline thesis.
- **R2. Fixed-K sticky-HMM ladder (K=2..6) vs HDP** on held-out log-likelihood, OOS stability, vol-ΔR²
  (Experiment 2). Fix the degenerate parametric baseline (better init / more restarts / report the
  restart-stability).
- **R3. Permutation-null version of the significance test** + multiple-testing correction across the
  {return,vol}×{5d,21d} grid.

### Optional / defer
- NUTS run **only after** adding a label-relabeling step to `posterior_mean_params` (else it silently
  corrupts). Uncertainty bands on dwell/vol-separation would then be real.
- Housekeeping already tracked in NOTES: untrack regenerable `data/processed/*.csv` + `models/*.pkl`;
  drop dead deps (`arch`, `plotly`, `pandas_datareader`); delete dead code (`merge_similar_states`,
  `HDPModelAdapter`); fix stale CI (`.github/workflows/tests.yml`) and README ("walk-forward is a stub").
- Decide the two-labeling-scheme question (§5.3) — recommend: use `label_regimes_hdp` (absolute
  brackets) as the honest primary and report the VIX-rank version only where a fixed 3-bucket structure
  is structurally required, with a test asserting where they agree.

---

## 22. Research Documentation Added

- **This file** (`.planning/RESEARCH-AUDIT.md`) — the permanent research record + decision log
  (§23), genre-matched to `DEEP-REVIEW.md`.
- `NOTES.md` "Next Session" list updated to surface the four new critical/high findings (transition-
  matrix mislabel, dwell hysteresis asymmetry, HDP K-saturation, orphaned significance test) so they are
  not re-lost. **No source code modified.**

---

## 23. Research Decision Log

```
Date: 2026-07-21
Question: Is the reported regime persistence (Table 2 diagonals, dwell 66/61/41) a real learned property?
Hypothesis: High diagonals reflect the learned κ stickiness.
Method: Traced run_paper_experiments.py:133–137 and get_labels_and_probs hysteresis.
Result: Table 2 is an empirical count on hysteresis-smoothed, VIX-merged labels — not the model's
        posterior transition matrix. Dwell compares smoothed HDP vs raw baselines.
Interpretation: Persistence is real in the model (κ learned) but the *reported magnitude* is inflated
        by post-processing; the advantage-vs-baseline comparison is unfair.
Decision: Flag as HIGH; recommend C1 (symmetric smoothing + report posterior matrix separately).
Confidence: High.
Next Experiment: Recompute dwell with identical smoothing across all label sets; report get_transition_matrix diagonals.
```
```
Date: 2026-07-21
Question: Is the HDP's data-driven K actually doing work?
Hypothesis: The HDP infers K≈3 from the data.
Method: Read effective_K output (results/run_log.txt) + prune_states + merge path.
Result: effective_K = mean 8.0, std 0.0, mode 8 every run; all 8 states kept; 3 regimes imposed by
        VIX-rank tertile cut.
Interpretation: K is not inferred — it saturates the truncation. Nonparametric benefit is inert here.
Decision: Rate "HDP justified" as Unsupported on current evidence; recommend R2 (fixed-K ladder).
Confidence: High (single-run evidence; a K_max sweep would make it airtight).
Next Experiment: Vary K_max ∈ {5,8,12,20}; if K_eff tracks K_max, K is truly not selected.
```
```
Date: 2026-07-21
Question: Is the volatility-information significance result reproducible?
Hypothesis: A committed script regenerates ΔR² and its CI.
Method: grep for block_bootstrap_ci / regime_delta_r2 callers.
Result: Defined in evaluation.py; called by nothing. Numbers exist only in NOTES/hub prose.
Interpretation: The best result is orphaned.
Decision: HIGH; recommend C2 (scripts/significance_test.py).
Confidence: High.
Next Experiment: Write the script; also add a permutation null + multiple-testing correction.
```
```
Date: 2026-07-21
Question: Are the published regimes "not recoverable from VIX alone"?
Hypothesis: The regimes encode structure beyond VIX.
Method: Traced merge_states_to_regimes (sorts states by mean VIX) + reviewed fingerprints.
Result: Final regimes are literally a VIX-rank partition; no VIX-independent structure isolated; raw
        8-state emissions never characterized.
Interpretation: The headline thesis is neither supported nor refuted — it is untested, and the
        labeling method works against it.
Decision: Rate headline thesis Inconclusive; recommend R1 (raw-state fingerprints + VIX-ablation).
Confidence: High that it's untested; open on the underlying truth.
Next Experiment: Fingerprint raw 8 states in 4-D feature space; refit dropping VIX; compare.
```

---

## 24. Open Questions

1. Do VIX-independent latent states exist? (Raw-state fingerprints / VIX-ablation — untested.)
2. Does data-driven K ever activate, or does it always saturate K_max? (K_max sweep — untested.)
3. Does a fixed-K sticky HMM match the HDP on fit/stability/vol-ΔR²? (Ladder — untested.)
4. Is the vol-ΔR² robust to a strict permutation null and multiple-testing correction? (Untested.)
5. How much of the in-sample→OOS dwell gap is real market calm vs window sensitivity vs residual
   method? (Partially decomposed; not closed.)
6. Which labeling scheme is "the" scheme? (Open decision, deliberately unresolved.)
7. Is the regime drawdown-predictive (P(maxDD_{t:t+h} | S_t))? (Untested — Experiment 3.)

---

## 25. Next Experiments (prioritized: importance × info-gain ÷ effort)

1. **Significance test script + permutation null (C2, R3).** *Importance: high. Info-gain: high
   (makes the best claim reproducible & rigorous). Effort: ~1–2 h.* Highest ROI in the repo.
2. **Fix the persistence/dwell comparison (C1).** *High / high / ~2–3 h.* Directly repairs a paper
   contribution that is currently invalid.
3. **Raw-8-state fingerprints + VIX-ablation (R1).** *High / very high (this is the thesis) / ~half day.*
   The experiment that decides whether the headline thesis lives.
4. **K_max sweep {5,8,12,20}.** *Medium-high / high (settles whether HDP K-selection works) / ~2 h of
   compute.*
5. **Fixed-K sticky-HMM ladder vs HDP (R2), with the parametric baseline fixed.** *High / high / ~half
   day.* Answers "is the complexity justified."
6. **Drawdown / P(r<0) conditional distributions by regime (Experiment 3).** *Medium / medium / ~2 h.*
   Rounds out the risk-predictive story.
7. **NUTS run — only after adding label-relabeling to `posterior_mean_params`.** *Medium / medium
   (real uncertainty bands) / ~overnight compute + ~2 h code.* Defer until 1–5 land.

---

## Final Principle (restated for this repo)

The project already internalized "discover → validate → interpret → test predictive info → policy →
optimize." Its honest internal record (`NOTES.md`) is well ahead of its external paper. The single most
valuable move is **not new modeling** — it is bringing the paper's claims down to what the OOS +
significance work already supports, making that work reproducible, and running the three experiments
(R1, R2, K-sweep) that would let the *nonparametric* thesis stand on evidence instead of assertion.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
