# Risk-State Monitor — Validation Specification (Layer 2: risk characterization)

Status: SPEC v1, 2026-07-23. Freezes the monitor's claim list and validation criteria
BEFORE any gate computation or UI work (prereg-lite: the claim list may grow only by
spec revision, never by adding a display first). Requested by Adam 2026-07-23.

Hierarchy (frozen): Layer 1 Measurement (largely established) → Layer 2 Risk
characterization (THIS SPEC) → Layer 3 Decision value (chapter 3, separate, frozen).
Measurement validity ≠ decision value. The monitor may have risk-characterization
value > 0 with incremental trading value = 0; that is not a failure.

## Governance

- Every displayed statement carries exactly one badge, assigned MECHANICALLY from gate
  output: **[OOS]** (out-of-sample validated), **[DESC]** (descriptive only, labeled as
  such with n), or **UNSUPPORTED** (never rendered).
- Gate runner: `scripts/monitor_gate.py` (to build) → `results/monitor_gate.csv`.
  Living check, rerunnable (construction-gate idiom, not a one-look).
- All tests in this spec are reported in full — no selective display of passing cells.
- Headline disclosure, always rendered first, own box:
  **"This is a nowcast, not an early-warning system"** (claim C7 quantifies it).

## Inference rules (apply to every claim)

- Evaluation sample: frozen OOS labels 1990-03..present (~9,120 days, 30 episodes).
- Distributional tests use NON-OVERLAPPING forward windows; where overlap is
  unavoidable, HAC/stationary-block-bootstrap inference. Path-dependent claims
  (drawdowns) use the EPISODE as the unit (n≈30 — power stated, not hidden).
- All conditional quantities the monitor displays must be computable causally at
  display time (expanding-window estimates; the fan shown "as of t" uses only episodes
  completed before t).
- Era-splits (pre/post-2008) reported for every [OOS] claim.

## Claims

### C0 — Data vintage and liveness
- Display: label date, splice freshness, French-lag status.
- Validation: existing construction + splice gates (corr 0.9957; agreement 1.0000 on
  9,120 overlap days), rerun on refresh. **Status: [OOS] (already established).**

### C1 — Current state, stability, persistence
- Display: current state, days in state, switch rate; "this label does not whipsaw."
- Validation, existing: ±2y train-shift agreement 1.000 (twice re-confirmed at K=3,
  2026-07-23); live-vs-frozen agreement 1.0000; 1.66 switches/yr.
- Validation, NEW (quantifies the "persistence + categorical framing" value honestly —
  replaces the retracted "denoising" wording): flip-rate race vs an occupancy-matched
  EWMA-σ̂ threshold monitor — same fraction of days flagged, compare state-change
  counts and mean run lengths. If the label does not flip materially less than the
  matched vol threshold, the categorical-framing claim is demoted to [DESC].
- **Status: [OOS] for stability; flip-rate test TO RUN.**

### C2 — Conditional forward volatility
- Display: forward 21d vol fan (median, IQR, 5-95%) conditional on state.
- Sub-claim (a) SEPARATION: stressed vs calm forward realized-vol distributions differ.
  Test: two-sample comparison on non-overlapping 21d windows, block-aware.
- Sub-claim (b) CALIBRATION of the displayed fan: causal expanding-window conditional
  quantiles; PIT uniformity (Diebold-Gunther-Tay; Rossi-Sekhposyan specification test)
  and interval-hit conditional coverage (Christoffersen 1998) per state.
- NOTE: benchmark comparison intentionally NOT here — a fan can be true and calibrated
  without beating anything; incremental value is C6's question, kept separate.
- **Status: TO RUN (anatomy versions are pooled in-sample → currently [DESC]).**

### C3 — Tail / drawdown risk
- Display: conditional daily VaR/ES (5%, 1%) per state; per-episode max-drawdown
  distribution.
- Validation, daily tails: VaR hit tests per state — Kupiec unconditional coverage +
  Christoffersen independence — on causal expanding-window quantiles.
- Validation, drawdowns: episode-level only (n≈30). Pre-commitment: this will very
  likely carry [DESC] with explicit n and CI — the monitor displays it as history with
  uncertainty, never as a validated forecast. Power is stated on the face of the panel.
- **Status: daily tails TO RUN; episode drawdowns expected [DESC] permanently.**

### C4 — Episode age
- Display now permitted: τ itself and episode start date (facts, causal) — [OOS] as
  facts. Age-conditional VOL/hazard displays: [DESC] only, labeled.
- Age-conditional forward-RETURN statements: **UNSUPPORTED — not rendered.** The
  existing age bins were chosen by inspecting the full forward-return curve
  (contaminated; see CH3-D2-MEMO §3). Upgrade path to [OOS]: bins pre-pinned from
  theory or first-half data only, validated on the untouched second half — this
  coincides with the chapter-4 screens; the monitor must not front-run them.
- **Status: facts [OOS]; risk-by-age [DESC]; returns-by-age UNSUPPORTED.**

### C5 — Historical analogs
- Display: nearest prior episodes by time-t-observable features ONLY (entry σ̂ path,
  current age, drawdown depth so far, trailing jump count); their subsequent histories
  shown as history, explicitly not as a forecast.
- Validation: leak check on the similarity features (all causal at display time) — the
  procedure is auditable, the content is inherently descriptive.
- **Status: [DESC] permanently, unless a scored analog-forecast procedure is separately
  validated (out of scope for v1).**

### C6 — Incremental information beyond an EWMA-vol chart (the load-bearing claim)
- Question: where, exactly, does state conditioning improve conditional DISTRIBUTION
  forecasts over σ̂ alone? The monitor does not need to win on point forecasts to be
  useful, but every "adds information" statement must cite this gate.
- Design: benchmark forecaster = conditional density scaled by EWMA σ̂ (location-scale
  t, causal); augmented forecaster = same + state (and state×σ̂). Compare OOS by:
  CRPS (calibration+sharpness; log score is not distance-sensitive), quantile-weighted
  CRPS for tail regions (Gneiting-Ranjan), Amisano-Giacomini weighted log-score as the
  region-focused likelihood test, Giacomini-White conditional predictive ability for
  inference. Horizons: 5d, 21d, 63d. Also: statement-revision frequency (C1 flip-rate)
  as the stability dimension of "adds information."
- Registered priors (honest, from v1 + calibration gate): center/point ≈ no gain;
  plausible gains confined to tail quantiles, longer horizons, and statement stability.
  External context both ways: regime-GARCH literature reports vol-forecast gains in
  some settings (Marcucci et al.) — this is a fair fight, not a foregone null.
- Display rule: wherever the augmented forecaster does NOT beat the benchmark, the
  monitor's corresponding panel shows the σ̂-based number or carries an explicit
  "no incremental information vs vol chart" annotation. Quantified, not hand-waved.
- **Status: TO RUN.**

### C7 — The lag disclosure (nowcast, not early warning)
- Display: median detection lag from ex-post peak (20d), episodes missed entirely
  (1998 LTCM, 2018 Q4), precision vs ex-post bear datings (~0.32), hit rate (15/18
  LT-15% bears).
- Validation: already established — `scripts/validate_sensor.py`,
  `results/sensor_validation.csv` (2026-07-23). Rerunnable.
- **Status: [OOS] (already established). Rendered prominently, not in a footnote.**

## Current scoreboard

| Claim | Status now | Gate work needed |
|---|---|---|
| C0 vintage | [OOS] | rerun on refresh |
| C1 stability | [OOS]; framing test TO RUN | flip-rate race |
| C2 vol fan | [DESC] → target [OOS] | separation + PIT/coverage |
| C3 tails | TO RUN / drawdowns [DESC] | VaR hit tests |
| C4 age | facts [OOS]; risk [DESC]; returns UNSUPPORTED | ch4 screens (external to monitor) |
| C5 analogs | [DESC] permanent | leak audit only |
| C6 incremental | TO RUN | CRPS/QW-CRPS/AG/GW battery |
| C7 lag | [OOS] | none |

## Build order (frozen)

1. `scripts/monitor_gate.py` implementing C1-flip, C2, C3-daily, C6 → gate CSV.
2. Badges assigned from gate output; spec updated with results (status column only).
3. ONLY THEN the presentation surface (report.html page or standalone), rendering
   nothing without a badge.

## Key methodology sources (verified 2026-07-23)

Christoffersen 1998 (interval/conditional coverage); Diebold-Gunther-Tay 1998 (PIT);
Kupiec 1995 (unconditional coverage); Amisano-Giacomini 2007 JBES (weighted LR);
Giacomini-White 2006 Econometrica (CPA); Gneiting-Ranjan 2011 (threshold/quantile-
weighted scoring); Rossi-Sekhposyan 2019 (conditional predictive density specification);
Marcucci 2005 (regime-switching GARCH forecast comparisons — external precedent that
C6 can go either way).

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
