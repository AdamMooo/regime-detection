# Allocation Prereg — State-Conditional Covariance, Multi-Asset Allocation (Chapter 2)

Status: **FROZEN Rev 2.1 (2026-07-23).** Rev 1 written 2026-07-23, informed by the
descriptive atlas (`results/atlas.csv`); Rev 2 same day after the pre-freeze outside
audit; Rev 2.1 same day from synthetic-smoke findings (changes in §10 — all made
BEFORE any real-data allocation backtest was run; the smoke used synthetic panels
only, blind intact). The atlas informs the design; it does not constitute a look at
the confirmatory result.

## §1 Hypothesis

H2: conditioning the COVARIANCE structure of a long-only multi-asset portfolio on the
jump-model volatility state adds economic value over the identical allocator built on
unconditional covariance (B_match) AND over the identical allocator built on a reactive
EWMA covariance (B_react).

**Primary mechanism — state-conditional SCALE.** Stressed-state covariance is larger
(atlas: mkt vol ratio 1.75, bond 1.35, era-consistent), so the conditional arm de-risks
into stress and tracks the portfolio vol target better. This is the era-robust part of the
atlas structure and the moment family where Track-1 showed the conditional value lives.

**Secondary mechanism — the stock-bond correlation tilt — is NOT load-bearing.** Audit
correction (2026-07-23): the atlas's "30/30 LOEO-stable" corr deepening is robustness of
the POOLED estimate to single-episode drops, not a per-episode fact. Per-episode, stress
deepens stock-bond corr in only 11/23 episodes ≥15d; the 1990s stressed shift is +0.07
(bonds anti-hedge) and the 328-day 2022 inflation bear ran at stress corr +0.11. The vol
state cannot distinguish growth-scare stress (bonds hedge: 2008, 2020-03) from
inflation/rates stress (bonds anti-hedge: 1994, 2022) — consistent with the v1 stock-bond
finding that the macro/rates axis is a non-stationary co-trend. Named failure mode: a
corr-regime break (2000, 2022) where the expanding conditional estimate is stale and
wrong-signed; shrinkage halves the tilt but cannot fix its sign.

**Means are not used anywhere.** The allocator consumes second moments only.

Relation to prior nulls (the information gate): this HARVESTS the vol axis v1 proved is the
only real one — it does not claim information beyond it. v1 Chapter 3's operative lesson —
conditioning added nothing vs a matched vol-only/reactive estimator — is honored
structurally: B_react is a co-primary baseline, so "conditioning merely replicates reactive
estimation" is a pre-declared verdict (§7 F1b), not a post-hoc escape.

## §2 Object & universe (to freeze)

- Universe: market equity (French mkt TR), 10y Treasury (synthetic TR), gold (GC=F,
  2000-08-31+; weight 0 before era-2 begins, §2 covariance construction), cash (RF).
  Industries EXCLUDED (stressed correlations converge 0.83–0.92 — no reliable within-equity
  structure); factor legs EXCLUDED (long-short implementability; momentum's corr flip is
  design knowledge, not a position). Gold caveat: GC=F closes 1:30pm COMEX vs 4pm NYSE —
  non-synchronous closes bias measured gold correlations toward 0; contained by the gold
  cap; identical data in all arms.
- Allocator: **equal-risk-contribution (ERC)** long-only over the era's risky universe,
  cash as residual. Weight caps: equity ≤ 0.75, bond ≤ 0.75, gold ≤ 0.25. No leverage.
- **Vol target formula (pinned):** w = w_ERC · min(1, 0.08/σ̂_p), where
  σ̂_p = sqrt(w_ERC' Σ̂ w_ERC) uses the arm's own Σ̂; cash = 1 − Σw. Scale-down only.
  Known slack: the unlevered two-asset ERC runs ~6.9% ann vol, so the target rarely binds
  pre-2000; vol-tracking comparisons (§5, F2) are therefore evaluated post-activation.
- **ERC solver (pinned, pure numpy, deterministic — Rev 2.1):** log-barrier cyclical
  coordinate descent (Griveau-Billion–Richard–Roncalli 2013; per-coordinate closed
  form, every free asset's risk contribution equals the barrier multiplier exactly;
  the uncapped system is homogeneous of degree 2 so one solve rescales to the budget);
  caps by cap-and-redistribute (clip binding weights at caps, freeze them, re-solve
  the free set with the multiplier set by bisection to the residual budget). Tests
  must assert convergence and equal risk contributions among uncapped assets.
- **Covariance construction (pinned, identical across arms):** two eras.
  Era-1 (from 1963): {equity, bond}, expanding complete-case windows.
  Era-2 begins at the first date with ≥250 complete-case {equity, bond, gold} days
  (~mid-2001): {equity, bond, gold}, expanding complete-case windows from gold inception.
  NaN policy: days with any missing return in the era's universe are excluded from
  covariance updates; on such days the portfolio carries previous weights and the missing
  asset contributes 0 to daily P&L (bond-market-only holidays, scattered gold gaps).
- **Conditioning (pinned):** covariance estimated per state from expanding causal windows
  of state-labeled complete-case days. Activation per era and per state: ≥500 labeled days
  in that state (era-1 stressed clears 1993-12-31; era-2 ~2002-03 via the 2001-03 episode);
  before activation, unconditional. Shrunk toward the era's unconditional estimate with
  fixed weight 0.5 (pinned; no tuning).
- **Hard-state is PRIMARY (Rev 2):** at date t the conditional arm uses Σ̂_{s_t} (filtered
  causal state), shrunk 0.5 to unconditional. The GRADED variant (blend by P(stressed) from
  the filter evidence gap, logistic calibrated ON SYNTHETIC panels only) is a pre-declared
  secondary, contingent on its calibration constants being appended to this doc BEFORE the
  run; if not calibrated in time it is not run. This removes an uncalibrated component from
  the primary arm.
- States: the frozen chapter-1 label protocol, run causally (as in live_label.py).

## §3 Matched baselines & other arms (to freeze)

- **B_match (matched baseline 1): the IDENTICAL ERC allocator on the unconditional
  expanding covariance** — same era structure, NaN policy, caps, vol target, costs, delay.
  Isolates the regime increment vs a static-information allocator.
- **B_react (matched baseline 2, co-primary — Rev 2): the IDENTICAL ERC allocator on a
  reactive unconditional covariance** — EWMA, decay λ=0.97 daily (≈23d half-life),
  250d burn-in, same era structure/NaN policy/caps/target/costs/delay. The honest incumbent
  for anything timing-flavored (chapter-1 discipline; v1 chapter-3 lesson). If the state
  label only re-discovers what reactive estimation already knows, fee vs B_react shows it.
- Context arms (secondary): 60/40 (monthly rebalance), vol-targeted equity (chapter-1 VT),
  B&H equity.

## §4 Execution (identical across arms)

Next-close (delay=2), 10 bps one-way on Σ|Δw| across risky assets **excluding the cash
leg**, daily evaluation. **Rebalance (Rev 2): monthly (first trading day) PLUS an event
rebalance when the filtered hard state flips** (same delay=2) — chapter 1's mechanism was a
detection-lag race; a pure monthly grid adds up to +21d on top of the ~20d median detection
lag. Pre-declared sensitivities: pure-monthly and daily rebalancing. OOS scoring 1990+
(label availability), panel from 1963. **Primary fee window: full OOS 1990+** (includes
the pre-activation stretch where conditional ≡ B_match); from-activation window is a
pre-declared secondary.

## §5 Primary metric & support bar (to freeze)

At γ=10, annualized bps, 90% CI from the paired stationary bootstrap (mean block 126d,
B=2000, seed=0):

- **fee_A = fee(conditional ERC − B_match)** — full scored window (pre-activation the
  arms are identical, so the early stretch is pure dilution, never bias).
- **fee_B = fee(conditional ERC − B_react)** — FROM-ACTIVATION window (pre-activation
  cond ≡ B_match, so a full-window fee_B would measure match-vs-react — an
  expanding-vs-EWMA comparison unrelated to conditioning; smoke-run finding, Rev 2.1).
  Control distributions for fee_B use the same real-label activation window.

SUPPORT requires **fee_A > 0 with CI excluding 0, AND fee_B > 0 with CI excluding 0**, and
§6 controls clean. Secondaries: γ=1 fees; ΔMaxDD; ΔSharpe bootstrap CI; realized-vol
tracking error vs the 8% target per arm over the POST-ACTIVATION window (the target is
slack pre-2000); turnover per arm; **era-split diagnostics (pre-declared, not gates):**
fee_A and fee_B on pre/post-2000 subsamples and excluding the 2022 episode (the named
corr-regime failure mode).

## §6 Controls (pre-declared, run before the primary is looked at)

- C1 placebo states: 100 random persistent 2-state signals (transition rates matched to the
  real label) through the FULL conditional-ERC pipeline; fee_A and fee_B must each exceed
  the 95th percentile of their placebo distributions.
- C2 episode-shuffled states: real stressed episodes relocated in time (preserving count
  and durations, non-overlapping); **50 draws** (Rev 2: was 10 — no label refits in this
  pipeline, crude bands are avoidable); null band.
- C3 iid calibration: **20 simulated panels** (Rev 2: was 10; matched unconditional
  moments, no state structure); null band.

## §7 Falsifiers

- F1: fee_A ≤ 0 or CI includes 0 → conditional covariance adds no allocation value net of
  costs (chapter-2 null; the atlas structure is real but not economically harvestable at
  this cost/delay).
- **F1b (Rev 2): fee_A supported but fee_B ≤ 0 or CI includes 0 → conditioning replicates
  reactive estimation** — the v1-chapter-3 outcome on a new object; recorded as a null for
  the LABEL's incremental allocation value.
- F2 (risk stabilization, Rev 2.1): the conditional arm's vol-of-vol (std of rolling
  63d realized annualized vol) over the post-activation window exceeds B_match's →
  mechanism failure regardless of fee. (Replaces RMSE-vs-target: when the 8% target
  is slack both arms share the same shortfall and the RMSE comparison is noise —
  smoke-run finding. RMSE-vs-target is still reported as a diagnostic.)
- F3: turnover > 5× B_match → untradeable conditioning.

Verdict precedence: SUPPORT requires all of F1/F1b/F2/F3 clean AND controls clean;
otherwise F1 → NULL; else F1b → NULL (replicates reactive); else F2/F3 →
MECHANISM_FAIL; else controls dirty → NULL.

## §8 One look

One run, one look, frozen classification, results to RESEARCH-RECORD.md as chapter 2.
Runner will be `scripts/run_allocation.py` requiring `--confirm-frozen`.

## §9 Known limitations (pre-declared)

- Corr-regime breaks (1990s regime, 2022): the label is a vol-state, not a macro-state;
  the conditional corr tilt can be wrong-signed at breaks. Era-split diagnostics in §5.
- Gold non-synchronous close biases its measured correlations toward 0 (all arms equally).
- The 8% vol target is slack pre-2000 (unlevered two-asset ERC ~6.9%); F2 scoped
  post-activation.
- Flat 10 bps across assets is conservative for treasuries, roughly right for gold/equity.

## §10 Rev 2 changelog (2026-07-23 pre-freeze audit)

1. H2 reframed: scale/vol-tracking is the primary mechanism; the stock-bond corr tilt
   demoted to secondary and flagged era-fragile (per-episode: 11/23 deepen; 1990s +0.07;
   2022 stress corr +0.11). "30/30 reliably" wording corrected — LOEO is pooled-estimate
   robustness, not per-episode evidence.
2. B_react (EWMA λ=0.97 ERC) added as co-primary baseline; F1b partial verdict added
   (v1 chapter-3 lesson made structural).
3. Hard-state promoted to primary; graded P(stressed) variant demoted to a pre-declared
   secondary contingent on pre-run synthetic calibration (removes an uncalibrated component
   from the primary and unblocks the freeze).
4. Rebalancing: monthly + state-flip event rebalance (was pure monthly; detection-lag race).
5. Pinned: vol-target formula (scale-down only, no leverage); ERC solver + cap handling;
   two-era covariance construction; NaN policy; per-era/per-state 500-day activation;
   costs exclude the cash leg; primary fee window = full 1990+.
6. C2 10→50 draws, C3 10→20 panels.
7. §9 limitations and §5 era-split diagnostics added.

Rev 2.1 (same day, synthetic smoke findings — blind intact, smoke used synthetic
panels only):
8. fee_B scored from activation (full-window fee_B measures match-vs-react, not
   conditioning); fee_A unchanged (its pre-activation difference is exactly zero).
9. F2 redefined as vol-of-vol (risk stabilization); RMSE-vs-target demoted to
   diagnostic (noise-dominated when the target is slack).
10. Verdict precedence pinned (F1 → F1b → F2/F3); ERC solver pin upgraded to
    log-barrier cyclical coordinate descent (Griveau-Billion–Richard–Roncalli 2013)
    with cap-and-redistribute — the drafted naive fixed point provably fails to
    converge under strong negative correlations (caught by tests).

---
**FREEZE CHECKLIST (Adam):**
- [x] Rev 2 calls reviewed: hard-state primary, B_react co-primary + F1b, monthly+flip
      rebalance, EWMA λ=0.97, activation thresholds, C2/C3 counts
- [x] Graded secondary NOT run this chapter (calibration not built; per §2 it is
      simply not run — hard-state primary carries the chapter)
- [x] **FREEZE SIGN-OFF:** Adam, via session directive to run the backtest
      ("lets get going", after reviewing the Rev 2 audit amendments) — 2026-07-23.
      Synthetic smoke: CAPABILITY PASS (structured fee_a 7.0 vs unstructured 0.5;
      risk stabilization detected; controls clean on structure).

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
