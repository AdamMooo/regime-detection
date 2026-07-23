# Claude Context — Regime-Detection

**Read NOTES.md first** — it has the current state and next action.

## State of the Project (2026-07-22)

The v1 research program is **CONVERGED and sealed** at git tag `v1-convergence`. Five
preregistered/pre-specified formulations of "markets have latent structure beyond volatility" —
discrete HDP-HMM states, macro/rates axis, covariance/eigenstructure conditioning, self-exciting
tail hazard, continuous OU/Kalman correlation factor — all returned null, all causally clean.
**`RESEARCH-RECORD.md` is the durable artifact** (no academic paper — Adam's decision, 2026-07-22).

The repo is being repositioned for a successor regime-detection question. **The successor question is
not yet chosen** — that's the single open item. See NOTES.md and the hub's Next section.

## What Is Live vs Archived

**Live (do not break):**
- The practical vol-regime ensemble label — `data/oos_regime_labels*.csv`, 3-window ensemble with
  agreement fraction, consumed by Portfolio-Manager. Label mapping that must survive any change:
  Low-Vol → `LOW_VOL`, Moderate-Vol → `MED_VOL`, High-Vol → `HIGH_VOL`.
- `src/` pipeline, data collectors (yfinance + FRED; key in `.env` as `FRED_API_KEY`), evaluation/
  bootstrap utilities, causal-inference helpers (`expanding_standardize`, forward-pass filtering),
  the causality-invariant test suite.
- `.venv` exists (JAX 0.9.1 / NumPyro 0.20.0 pinned; also arch 8.0.0, yfinance 1.2.0).

**Archived (`archive/research-v1/` — inert, sealed):** the one-shot chapter experiment scripts, paper
scaffolding, and research baselines. Import paths left as-is intentionally; to reproduce v1 results,
check out the `v1-convergence` tag. Never edit archived code in place.

## Discipline That Carries Forward (non-negotiable, learned the hard way)

- **The information gate:** any proposed formulation must name the NEW information source it taps —
  not a new representation of the same daily index-level features. A filtered/transformed state is a
  function of the same observables; representation cannot create information (demonstrated literally:
  the v1 Kalman MLE collapsed its "latent" state onto the raw observable).
- **Prereg before running:** object, matched baseline, primary metric, falsifier, and stopping rule
  frozen before any real-data result exists.
- **Causal inference only:** expanding-window standardization, forward-pass filtering, no full-sample
  fitting, no refit lookahead. New estimators get causality-invariant tests.
- **Honest baselines:** never benchmark a smoother/filter against raw persistence — fixed EWMA is the
  minimum; matched same-architecture baselines for conditioning claims; placebo/surrogate controls for
  extra-dimension artifacts.
- **Evaluation lens is part of the prereg** — don't re-ask a settled question under a new lens without
  acknowledging which prior null already covers it.

## Do Not

- Reopen any v1 formulation (HMM variants, vol-conditioned covariance kernels, daily-frequency
  self-excitation, OU/Kalman states on index-level series) without a genuinely new information source.
- Edit `RESEARCH-RECORD.md`'s sealed sections, the frozen preregs in `.planning/`, or anything under
  `archive/research-v1/`.
- Build production execution logic here (that's Algo-Trading-Bot's job).

## Session Close Checklist

- Update NOTES.md with progress + next action
- Commit and push to GitHub
