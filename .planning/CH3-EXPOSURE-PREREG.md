# Chapter 3 Prereg — State-Conditioned Continuous Exposure vs Volatility Targeting

**Status: DRAFT Rev 3 (2026-07-23) — NOT FROZEN. DO NOT RUN.**

Rev 3: **D2 RULED by Adam (2026-07-23): REGISTERED NULL** — chapter 3 is the clean
state-only test, VT vs VT + hard two-point state dial; M2 deferred to a screened
chapter-4 candidate (see `.planning/CH3-D2-MEMO.md`); no M2/K=3/sensor work may leak into
the one look. Conceptual hierarchy frozen: ch1 binary stress exposure fails; ch2 the
reactive-estimator class is the incumbent (VT for exposure, EWMA for covariance); ch3
does the hard state add decision value beyond VT; ch4 candidate: does episode duration.
Three Rev-3 refinements ACCEPTED by Adam (2026-07-23): (i) g_stress bounds [0, 2] (§4);
(ii) mandatory pre-freeze synthetic capability smoke — power AND size (§6b); (iii) F3
pinned to the hysteresis signature (§7). Remaining before run: build runner + smoke →
record smoke results here → Adam's named+dated sign-off (§9) → overnight cooling-off.

Rev 1: D1 (daily), D3 (w_max = 1.0) decided by Adam 2026-07-23; D2 preregistered as a
CONDITIONAL decision rule resolved by the K=3 probe (§5, §9) — the branch itself is frozen
before the probe result is seen, so neither outcome permits a post-hoc mechanism choice.
Calibration gate hardened per Adam: DGP-robustness grid (§6), margin input pinned as D_t/λ.

Rev 2: both gates RESOLVED (§10a) — calibration gate FAILED (pre-committed fallback: A3 =
hard label, two-point g; Adam concurred 2026-07-23); K=3 probe → D2 = M2 recommended
(stability PASSED 1.000/1.000; the phase-separation criterion was under-specified — prereg
defect recorded in §10a — resolution requires Adam's explicit ruling at sign-off).

Freeze is blocked on:
1. Adam's ruling on the D2 resolution (§10a) + freeze sign-off (§9).
2. Cooling-off: overnight gap between freeze and run + explicit named+dated sign-off
   (CLAUDE.md discipline, 2026-07-23). This experiment CAN produce a positive claim.

One look. After freeze, no changes to objective, state definition, exposure mapping, or
evaluation criteria. Scope explicitly EXCLUDES factor/asset selection (see §10).

## 1. Question

Does jump-state information improve the continuous exposure decision beyond volatility
targeting alone?

- H0: state information provides no incremental decision value beyond the frozen
  vol-targeting incumbent.
- H1: conditioning exposure on state (in addition to sigma-hat) improves risk-adjusted
  outcomes net of costs.

Operational scope of "beyond volatility management": beyond the specific frozen incumbent
w = sigma*/sigma-hat (EWMA, same estimator in every arm). The state label is computed from
the same daily return series as sigma-hat, so this is NOT an information-source claim — it is
a functional-form / decision-rule claim (information-gate compliance, v1 discipline). The
distinction detection != prediction != decision value is the organizing frame: chapter 1
established detection quality (stability 1.000); this chapter tests decision value ONLY.

## 2. Why this is not a re-ask of chapter 1

Chapter 1 tested the binary 0/100 overlay vs VT and closed it: fee(JM−VT) −255.8
[−477.5, −36.7]. The literature's remaining objection is "you used the label too coarsely."
This chapter tests the strongest graded use of the label. Registered in-house prior
(NOTES.md, 2026-07-23): the soft-exposure variant interpolates toward vol targeting —
i.e., expected NULL. A null closes the last escape hatch and completes the negative paper's
arc; a positive is subject to the confirmation regime in §8.

## 3. Arms (single-delta principle: adjacent arms differ by exactly one ingredient)

All arms: identical costs (10 bps one-way), identical execution (delay=2 next-close
headline; delay=1 sensitivity), identical sigma-hat estimator (EWMA std, halflife 20,
backtest.py spec), DAILY cadence (D1 decided; monthly appears only as a labeled robustness
secondary, never as a competing primary), same walk-forward protocol as chapter 1 (annual
refits, expanding window, frozen-per-refit parameters, causal filter only).

- A0 — Buy-and-hold.
- A1 — Static mix matched ex-post to A3's realized average exposure (diagnostic control,
  C1 idiom).
- A2 — Vol targeting (INCUMBENT/co-primary): w_t = min(w_max, sigma*/sigma-hat_t).
- A3 — State-conditioned exposure: w_t = min(w_max, (sigma*/sigma-hat_t) · g(z_t)), where
  z_t is the state input (calibrated p_t if §6 passes, else hard label) and g is the frozen
  modulation family (§4). A3 differs from A2 by exactly the g(z_t) factor.
- P — Placebo band: random persistent labels (episode-length-matched) fed through the
  IDENTICAL g and pipeline; 95th-percentile fee band.
- Surrogate + iid null bands as in chapter 1.

w_max = 1.0, long-only, 0 <= w_t <= 1 (D3 decided: the question is risk allocation, not
leverage; a leverage extension would be a separate later question). sigma* set so A2's
realized average exposure over the training era matches its chapter-1 configuration
(no retuning against the scoring era).

## 4. The exposure map g (family pinned per D2 branch; values fit causally per refit)

One family per D2 branch, fixed NOW so the probe outcome cannot influence family choice:
- none/null branch (OPERATIVE per D2 ruling + §6 gate failure): g(s) = {1, g_stress},
  hard label, g_stress the single free parameter. Rev-3 refinement ACCEPTED (Adam,
  2026-07-23): g_stress ∈ [0, 2], NOT [0, 1] — the anatomy says stress contains rebound phases,
  and Adam's own directive (2026-07-23) was to test the decision problem without assuming
  "de-risk" is the answer; a [0, 1] bound would presume the direction. w_max = 1.0 still
  caps the final weight, so g_stress > 1 binds exactly where VT is below full exposure —
  i.e., in stress, which is the point.
  (Superseded probability variant, recorded for the audit trail: g(p) = 1 − beta·p.)
- M2 branch: g(p, tau) = 1 − beta·p·h(tau), tau = trading days since stress entry
  (causally observable), h a FROZEN unit-scale shape taken from the training-era hazard
  curve per refit (no scoring-era data); beta remains the single free parameter.
- M3 branch: per-phase map g in {1, g_crash, g_rebound} (two free parameters), phase from
  the causal K=3 filter only.

Requirements common to all branches:
- Parameters chosen per refit on TRAINING data only, by the same 8y-validation criterion
  machinery as lambda (walkforward.py idiom), frozen before each scoring year. No global
  fit touching the scoring era. No family sweep: the branch's ONE family, preregistered.
- Degenerate checks pinned in advance: g ≡ 1 recovers A2 exactly (must be byte-identical);
  g = {1, 0} with binary label recovers the chapter-1 overlay shape.

## 5. Mechanism preregistration (name the channel or expect noise)

The claim "state helps beyond sigma-hat" requires a named channel, because the state is
return-derived. At most ONE channel is primary; others become sensitivity arms only.
D2 is preregistered as a conditional rule (Adam, 2026-07-23, set BEFORE the probe result):

    D2 = M3 if the K=3 probe passes the phase/stability gate;
         M2 if it fails;
         none/expected-null registered explicitly if M2 cannot be given a concrete
         falsifiable F3 signature at freeze time.

M1 is NOT selected (would demand a downside-vol incumbent arm and dilute the single-delta
design); it remains listed for the record:

- M1 — Conditional asymmetry: the state carries downside-shape information that total-vol
  sigma-hat misses. If chosen, a downside-vol-targeting arm (same form, downside deviation
  in the denominator) is MANDATORY as an additional reactive incumbent — otherwise a "win"
  may just be downside-vol targeting in disguise.
- M2 — Episode age / hazard: exit hazard is non-monotone in episode age (state anatomy,
  2026-07-23); age is causally observable in real time and is NOT encoded in sigma-hat.
  ANATOMY-BORN → out-of-hypothesis-sample confirmation binds (§8).
- M3 — Phase (K=3 crash/rebound): admissible ONLY if the running probe shows phase
  separation AND re-clears the K=2 stability bar (1.000 under ±2y shifts; bar: >= 0.95).
  Smoke-run evidence points the other way (severity split, identical crash/rebound
  distributions). ANATOMY-BORN → §8 binds.

If no channel can be defended at freeze time, the chapter runs as the completion exhibit
with the interpolation prior (§2) and the verdict wording pre-committed accordingly.

## 6. Calibration gate for P(state) — synthetic panels ONLY, pre-freeze

Purpose: distinguish detection from prediction. A probability input to g is admissible only
if it is a calibrated probability, established where truth is known.

- Calibrator input: the causal filter's evidence gap normalized by the deployed jump
  penalty, m_t = (V_t[calm] − V_t[stressed]) / λ. The λ-normalization is principled, not
  cosmetic: the filter's evidence accumulation clips at ±λ, so m_t is the dimensionless
  position of the evidence within the switch band and is comparable across refits whose
  λ and center geometry differ. m_t > 0 means the filter favors the stressed state.
- Estimator: Platt scaling p_t = sigmoid(a·m_t + b), fit by pooled logistic regression on
  the TRAIN seeds of the full DGP grid below. The pooled (a, b) is the single frozen map
  A3 may use; the real panel NEVER enters the fit (Adam, 2026-07-23: fitting the calibrator
  on the real panel would make the evaluation era part of the decision rule's training
  procedure — a one-look violation regardless of parameter count).
- DGP robustness grid (Adam's addition): acceptance must hold PER CELL across a grid
  varying state frequency, persistence, jump intensity/severity, and signal-to-noise —
  8 named cells (base, frequent, rare, choppy, long_dwell, weak_snr, strong_snr, asym_sev;
  exact parameters in scripts/calibration_gate.py), disjoint train/eval seeds per cell.
  A calibrator that shines on one DGP and breaks on plausible neighbors FAILS the gate.
- Acceptance criteria (evaluated per cell on held-out eval seeds):
  (a) reliability: calibration regression logit P(y=1 | p_hat) = alpha + beta·logit(p_hat)
      with slope beta in [0.8, 1.2] and |alpha| <= 0.1 for every cell;
  (b) Brier score beats BOTH the pooled-train climatological base rate and a
      sigma-hat-only logistic benchmark (log EWMA-vol, halflife 20 — the same estimator
      as the VT arm) fit the same pooled way, in every cell — if the margin cannot beat a
      vol-only probability, the state adds no probabilistic content and A3 uses the hard
      label;
  (c) stability: per-cell refits of (a, b) satisfy CV(a) <= 20% and range(b) <= 0.2
      across cells (b is near zero by construction, so a coefficient of variation on it
      is meaningless — range replaces it).
- If the gate FAILS: A3 takes the hard label, g reduces to the two-point family, and the
  prereg records the failure as an instrument finding (not a look).

## 6b. Capability smoke (Rev-3 requirement, ACCEPTED Adam 2026-07-23 — pre-freeze, synthetic only)

A null verdict is ambiguous between "the state adds nothing" and "the design cannot
detect anything" unless power is demonstrated where truth is known (program idiom:
chapter 2's --smoke, structured fee 7.0 vs unstructured 0.5). Before freeze:
- POWER: on synthetic 2-state panels with a PLANTED state-conditional Sharpe gap
  (state-dependent mu at fixed vol structure, magnitude in the range the anatomy
  suggests), the full A3 machinery (per-refit causal g_stress fitting included) must
  produce fee(A3−A2) > 0 and above the placebo band.
- SIZE: on matched panels with NO planted gap (returns differ by vol only, mu
  proportional), fee(A3−A2) must sit inside the placebo/iid bands (no false positive
  from the fitting machinery itself).
If POWER fails, the chapter is not run as-is (redesign or abandon — an underpowered
one-look is worse than none). Smoke results recorded here before the sign-off line.

## 7. Metrics, falsifiers, verdict

- PRIMARY: FKO performance fee, fee(A3 − A2), quadratic utility, gamma per chapter-1
  headline (gamma sensitivity reported), net of costs, delay=2, paired stationary
  bootstrap CI.
- F1 (NULL trigger): CI contains 0, OR fee(A3−A2) <= placebo-band 95th percentile, OR
  either surrogate/iid band contains it → verdict NULL. Precedence: F1 over everything.
- F2 (artifact trigger): if A3's realized average exposure differs from A2's by more than
  5pp, the exposure-rescaled comparison (A3 scaled to A2's mean exposure) becomes the
  headline — utility fees reward average exposure (C1 lesson).
- F3 (mechanism check — PINNED per D2 ruling to the hysteresis channel): the state dial's
  only claimed residual over sigma-hat is persistence-filtered downside hysteresis ("stay
  cautious through in-episode vol lulls" while VT re-levers into them). Signature frozen
  in advance: any positive fee(A3−A2) must concentrate on stressed days where sigma-hat
  is BELOW its trailing within-episode peak (the lull days). Fee > 0 with F3 absent →
  verdict AMBIGUOUS-NULL, not support. This is what makes a positive interpretable
  ("a clean reason to investigate why," Adam 2026-07-23).
- Secondaries: max drawdown, tail severity, turnover (switches/yr and traded volume),
  exposure distribution by state, era splits (pre/post-2000), LOTO over crisis episodes.

## 8. Confirmation regime for any positive

Any SUPPORT verdict additionally requires, before the claim is recorded as supported:
- Out-of-hypothesis-sample confirmation on the designated international panels
  (French/MSCI developed: Japan, Germany, UK) — same frozen design, no re-tuning. Binds
  with full force for M2/M3 (anatomy-born hypotheses).
- Cooling-off satisfied (overnight freeze→run gap; explicit named+dated sign-off recorded
  in this file's freeze banner).
- Comparative wording only: VT is a matched-race baseline, not a recommendation (rule 4).

## 9. Design decisions (recorded)

- D1 — Cadence: DAILY (Adam, 2026-07-23). Rationale: the chapter-1 problem is the timing
  of the state transition; monthly aggregation discards exactly the temporal resolution
  under test, and a daily null is the stronger null. Monthly = robustness secondary only.
- D2 — Mechanism: CONDITIONAL RULE preregistered before the probe result (§5): M3 if the
  K=3 phase/stability gate passes, M2 if it fails, explicit registered null if neither
  survives. No post-hoc mechanism selection under any outcome.
  **RULED (Adam, 2026-07-23): REGISTERED NULL** — deviation from the rule's letter
  (¬M3→M2) toward the more conservative branch, justified pre-freeze in
  `.planning/CH3-D2-MEMO.md` (M2's evidence is claim-3-level only; single-delta would
  break; external literature contests duration-dependence sign). M2 deferred to a
  screened chapter-4 candidate; "apparently underexplored" is the sanctioned wording.
- D3 — Exposure cap: w_max = 1.0, long-only (Adam, 2026-07-23). Risk allocation, not
  leverage; a leverage extension is a separate later question.
- Sign-off line (complete at freeze): FROZEN Rev __ by Adam Morris, date __, run no earlier
  than the following day.

## 10a. Branch resolutions (recorded 2026-07-23, pre-freeze — factual, no design changes)

- **Calibration gate (§6): FAILED** — all three criteria, all 8 DGP cells
  (`results/calibration_gate.csv`, `results/calibration_gate_run.log`). The margin loses to
  the log-EWMA-vol benchmark on Brier (2–4×) AND AUC in every cell; per-cell Platt slopes
  span −0.17..2.05 (CV 0.80). Pre-committed fallback fires: **A3 = hard label, two-point
  g = {1, g_stress}**. Adam concurred (2026-07-23): "state detection ≠ probability
  calibration — the filter's classification is robust, its internal evidence margin is not
  a portable confidence measure." No rescue attempts permitted.
- **K=3 probe (§5): stability PASSED** (agreement 1.000 at start+2y and start−2y, bar
  ≥0.95; `results/k3_exploration.csv`, run log). **Phase-separation criterion was
  UNDER-SPECIFIED in Rev 0/1 (prereg defect, recorded, not cured post hoc):** the probe
  shows crash/rebound days load differentially on the third state (71%/36% on state 2 vs
  57%/50% for an occupancy-matched EWMA-σ̂ threshold — more than a vol tier), BUT no K=3
  state is a phase: states are severity tiers (12.8/16.2/28.3% vol) and the rebound-heavy
  state is the majority state holding 58% of calm days. The M3 exposure family
  (g ∈ {1, g_crash, g_rebound}) presupposes phase-identifying states, which did not
  materialize → **D2 = M2 (episode age/hazard) RECOMMENDED; final resolution is Adam's
  explicit ruling at the freeze sign-off.** The phase-tilted severity finding is recorded
  as instrument knowledge (future sensor work), outside this chapter.

## 10. Out of scope (preregistered exclusions)

Factor selection, sector rotation, cross-asset menus, K=3 as an economic signal, any
"optimal allocation across regimes" framing. If the evidence points there, that is a NEW
prereg and a NEW look. This chapter answers one question: state + volatility > volatility
alone, or not.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
