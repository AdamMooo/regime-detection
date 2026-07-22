---
phase: roadmap
created: 2026-07-22
supersedes_question: reframes the yardstick again — from "state estimation quality" (REASSESSMENT-PLAN.md)
  to "trustworthy = calibrated latent-state inference." Keeps every prior negative; changes the goal.
status: SPINE — Phase 0 done + continuum confirmed + HMM estimator rejected (OOS); live fork = Stage-2 value vs methods paper
evidence: RESEARCH-RECORD.md (narrative), .planning/RESEARCH-AUDIT.md (technical), results/*.csv (E1/E2)
---

# Roadmap — Toward a Trustworthy Market-State Engine

## The reframe (why this doc exists)

The deliverable is **not** a trustworthy regime *label*. A latent state has no ground truth, so
"is the state correct?" is unanswerable in principle. The attainable, honest deliverable is:

> A **calibrated latent-state estimate** — one that is *honest about when it doesn't know* — with a
> confidence measure that is validated out of sample, plus a novelty flag for "this looks like nothing
> I've seen."

**Trust ≡ calibration, not accuracy.** A state is trustworthy *for a target observable T* iff its
confidence-qualified predictions of T are calibrated, OOS, under perturbation, and identifiable from the
data. Trust is therefore **purpose-relative** (a state can be trustworthy for vol and useless for
returns — and the evidence says exactly that) and **confidence-conditional** (a per-day, not global,
property). The output object is a reliability curve, never a scalar "trust score."

## Operating definition — the load-bearing properties

| Property | Test | Status (2026-07-22) |
|---|---|---|
| **Causal** | perturb-future / assert-past | ✓ done + mechanically tested |
| **Calibrated** | OOS reliability diagram: reported confidence vs forward-consistency | **untested — the gate** |
| **Invariant** | recoverable under window/seed/model perturbation (ARI) | E2: weak (ARI 0.04–0.33) |
| **Identifiable** | ≥ enough independent *episodes* per state for usable error bars | rare states structurally under-identified (~5–10 stress episodes total) |
| **Forward-consistent for T** | conditional prediction of T beats the trivial (VIX) benchmark OOS | vol: marginal; returns: none |

Separation / persistence / interpretability are instrumental, not load-bearing. E1 already showed the
temporal (Markov) structure earns its keep vs static clustering (raw dwell 44d vs 15–19d; better held-out
log-lik) — persistence is genuinely learned, not just hysteresis.

## Open premises being challenged (not assumed)

1. **Discreteness may be the enemy of trust.** K saturates at 8; "3 regimes" is a hand-cut on a
   continuous VIX axis; window sensitivity is a smooth gradient. The honest object may be a **continuous
   stress index with a credible interval** (or a changepoint framing), not K discrete states. Testing this
   is upstream of everything.
2. **The current model's specification fights calibration.** Mean-field SVI underestimates variance *by
   construction* (KL(q‖p) is mode-seeking); diagonal-Gaussian emissions cannot represent correlation
   environments; argmax + hysteresis discards the calibrated posterior. Keep the HMM *core*; be skeptical
   of these three choices. The *nonparametric HDP* framing is inert (K saturates) — demote it.
3. **The binding constraint may be data, not model.** No amount of Bayesian machinery manufactures
   information about a regime observed ~10 times. Respect this; don't promise trust the data can't support.

---

## Findings & status (2026-07-22 — Phase 0 done, and beyond)

The gate was run and the investigation went further than Phase 0. Results (scripts in `scripts/`, narrative
in `RESEARCH-RECORD.md` → "2026-07-22 — The Continuum Turn"):

- **Phase 0 (trust_gate):** cross-window agreement is a real confidence signal (η² rises with agreement),
  but the VIX-projected state ties the VIX null on forward vol. Prompted looking at the raw states.
- **Premise 1 RESOLVED — it's a continuum.** Raw states are ~2-D (stress + independent macro/curve axis),
  weakly-structured (silhouette 0.19, no natural K → explains K-saturation). Discrete labels were the
  artificial part; every prior beyond-VIX negative was on the VIX-projected label.
- **The continuous coordinate Z_t is stable** across windows (PC corr 0.92–0.97) — so E2's instability was
  largely the VIX-merge artifact — but ~2/3 is just a smoothed version of the features.
- **Phase-1 model question ANSWERED against the HMM:** the current HMM-based estimator is **rejected on OOS
  predictive grounds** vs simple continuous filters (EWMA/VAR carry ~2× its forward predictive corr). The
  environment should be represented by a **simple causal continuous filter**, not the discrete HMM.
- **Phase 2/3 (Stage-2 first cut):** the continuous coordinate adds no clear incremental OOS value over the
  raw features for conditioning cross-asset behavior yet (preliminary, low power).

**Where this leaves the spine:** the "fix the object" question (Phase 1) is largely settled — continuous,
simply-filtered, HMM demoted. The live fork is whether Stage-2 conditioning has any incremental value
(one rigorous pass) or whether the honest deliverable is the methods/negative paper.

## The spine (gated)

### Phase 0 — GATE: is the state calibratable at all? [cheap; reuses cached OOS labels]
**Goal.** Draw the OOS reliability diagram for the easiest target (forward realized vol, h=21), using the
confidence-qualified state (cross-window `agreement_frac`). Bin days by reported confidence; check that
high-confidence days are forward-consistent and low-confidence days are genuinely dispersed. Report against
a VIX-only benchmark.
**Go.** Curve is monotone in confidence and roughly on the 45° line → the state carries *calibrated*
information → proceed.
**No-go.** Uncalibrated even for vol → the trustworthy-state vision does not pan out; the honest output is
"a smoothed vol index ≈ a VIX transform," write it up as a rigorous negative + methods result, stop.
**Also here (cheap):** a first continuous-vs-discrete probe — does a continuous latent-stress estimate
calibrate better than the discretized label? (Premise 1.)

### Phase 1 — Fix the object [contingent on Phase 0 = go]
Stop discarding the calibrated posterior. Output `{distribution over states or continuous stress level,
validated confidence, novelty flag via marginal likelihood P(x_t|x_{1:t-1})}` — never an argmax'd label.
Decide the ontology (discrete vs continuous vs changepoint) on Phase 0 evidence. Address mean-field
overconfidence (use the cross-window ensemble as the calibrated object, or a better posterior).

### Phase 2 — Characterize the environment honestly [cheap, offline]
State-conditional distributions of vol, return, drawdown, **and correlations** (`Corr(X|S=k)` — the model
can't see this; compute it empirically). This decides whether it's *only* a vol ladder or a genuine
multivariate environment (the one place non-vol novelty could still live). All error bars must respect the
identifiability ceiling — report effective episode counts, not day counts.

### Phase 3 — Conditional asset behavior [contingent on Phases 0–2; the Stage-2 firewall applies]
`P(R_{i,t+h} | S_t=k)`, **always reported beside `P(R_{i,t+h} | VIX-tertile)`** so we never mistake
"conditioning on volatility" for a discovery. No asset returns feed back into state inference.

### Phase 4 — Decision support / risk-ops [contingent]
De-risking guardrails, state-scaled sizing, risk communication — restricted to high-trust days. Explicitly
not alpha timing; honest about turnover advantage and Sharpe-domination by RV30.

---

## Guardrails (carried from the audit + reassessment)
- **Firewall:** asset returns never train the state model (Phase 3+ only, as conditioning).
- **VIX benchmark travels downstream:** every conditional claim reported against a VIX-bucket null.
- **Calibration, not accuracy**, is the target; the output is a reliability curve.
- **Respect the data ceiling:** effective N = independent episodes; rare-state claims get wide bars or none.
- Causal timing everywhere; block resampling / permutation nulls for serially-correlated targets.

## Not doing
- Searching for alpha (settled: none).
- Defending the HDP / nonparametric framing (inert).
- Any expensive compute (K_max sweep, NUTS) before the Phase 0 gate.
- A heavy multi-phase build before we know the state is calibratable.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
