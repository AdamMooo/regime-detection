---
title: Pre-registration — Macro/Rates vs Volatility as a distinct market-environment dimension (stock-bond correlation)
status: FROZEN 2026-07-22 — do not edit hypothesis, targets, baselines, or thresholds after this date
stage: 1 of 4 (distinct-information diagnostic; U.S.-only first stage)
depends_on: RESEARCH-RECORD.md "Belief Revision" (HMM latent-info thesis stays weakened; NOT reopened here)
approved_by: Adam, 2026-07-22
---

# Pre-registration — Stage 1: does the macro/rates axis carry incremental OOS information about stock-bond correlation beyond volatility?

**This is a frozen pre-registration.** The hypothesis, primary target, baseline ladder, macro
specification, primary metric, thresholds, and falsification/decision rules below are fixed as of
2026-07-22 and will not be altered based on results. Any post-hoc analysis is labeled exploratory.

**Scope discipline.** (1) Trading/portfolio relevance is strictly DOWNSTREAM of the evidence (see §11),
never assumed. (2) The HMM latent-information thesis remains weakened (RESEARCH-RECORD "Belief Revision")
and is NOT reopened — this test is built directly from observable features. If the observable macro axis
is where the information lives, we accept that rather than rescue the HMM.

---

## 1. Hypothesis (falsifiable form)

Financial markets carry at least two empirically separable state dimensions: a **volatility/stress**
dimension (magnitude of aggregate risk) and a **macro/rates** dimension (growth-vs-inflation character of
the environment, via term structure + inflation state). **H1:** conditional on the volatility/stress
state, the macro/rates state contains **incremental, stable, out-of-sample information about the level
and/or sign of future stock-bond correlation.** **H0:** it does not (no incremental OOS information beyond
a strong stress baseline). Claim is **associational, not causal** (no instrument; both axes driven by
unmodeled latent macro forces). The stronger reading "macro governs the sign, volatility the magnitude" is
NOT assumed — it is a secondary structural question (§6, §7 Layer B).

Two layers, kept distinct:
- **Layer A (predictive):** does macro improve OOS prediction of future stock-bond correlation beyond a
  strong volatility baseline?
- **Layer B (mechanistic interpretation):** IF A holds, are direction/magnitude *consistent with* the
  growth/inflation mechanism? Layer B is a consistency check on an interpretation; the predictive test
  cannot prove mechanism.

## 2. Primary target and exact construction

`rho^{SPX,10y}_{t,t+h}` = Pearson correlation of daily log returns over the forward window `(t, t+h]`,
`h = 63` trading days. Assets: S&P 500 total return vs a **10-year constant-maturity par-bond total
return** (NOT IEF/TLT — ETFs start 2002 and their duration drifts).

**Bond TR construction (exact par-bond repricing, not duration linearization — 1980s had ~15% yields):**
each day hold a 10y par bond with coupon `c = y_{t-1}` (semiannual), priced at 100; reprice at `y_t`:
`P_t = c/2·[1-(1+y_t/2)^{-2T}]/(y_t/2) + 100·(1+y_t/2)^{-2T}` with `T=10`;
`TR_t = (P_t-100)/100 + y_{t-1}/252`; roll to a fresh par bond daily.

**Construction-validity gate (Case E), pre-registered:** over the ETF overlap the synthetic-TR rolling
correlation series must reproduce the ETF-based series — require `corr(rho_synth, rho_IEF) >= 0.90` AND
`mean|rho_synth - rho_IEF| <= 0.10`. Fail => Case E.

**Construction-free corroborator (pre-declared, must agree):** correlation of S&P returns with `-dy_10`
(negative daily 10y yield change); needs no TR construction, spans 1962+. Since daily bond return
`≈ -D·dy + smooth carry`, this captures the same sign object. If the TR gate fails, `-dy` becomes primary
with stated caveats.

One primary (SPX-10y TR, h=63). Replication: 2y/5y/30y maturities; h in {21,126}; `-dy` corroborator;
IEF/TLT over the modern overlap.

## 3. Volatility/stress baseline ladder

Stress inputs (causal, historically available): **{RV21, RV63, NFCI, credit spread (Baa-Aaa)}**. RV =
annualized trailing realized vol of S&P log returns (21d, 63d). **NFCI is placed on the stress axis** (it
is a financial-conditions/stress index) — this enriches the control AND keeps the macro axis clean.
Credit spread: daily from ~1986, monthly (1919+) causally ffilled earlier, or restricted to a post-1986
robustness. Stress representation chosen by its OWN OOS fit for the target BEFORE macro is introduced.

Ladder (nested models for the target):
- **A** stress, linear.
- **B** stress + nonlinear terms (squares, log RV).
- **C** stress, flexible smooth: **natural cubic splines (df=4 per input) + ridge** (alpha by blocked CV
  on the training portion); shallow gradient boosting (max_depth=2, OOS-tuned) as robustness. C = the
  strongest honest observable baseline.
- **D** C + macro axis.

**Primary comparison is D - C** (macro must beat the strongest honest volatility model, not a linear straw
man). FWL is used ONLY as a linear diagnostic decomposition; it does NOT define orthogonality under the
nonlinear C. The operational claim is: macro provides incremental predictive information conditional on a
sufficiently rich volatility control.

## 4. Macro specification

Macro/rates axis (primary, parsimonious): **{10Y-2Y slope, inflation state = trailing 12m CPI change}**.
Levels; causal standardization (expanding z-score); publication-lag/vintage alignment (ALFRED for
CPI/NFCI). Robustness slope: 10Y-3M.

**"Beat simple variables" rule:** decompose the macro increment across slope-alone, inflation-alone,
slope+inflation. If one variable explains it all, classify as a single-variable macro effect, NOT a
two-dimensional "macro axis."

## 5. Primary OOS test

Rolling-origin / expanding-window OOS, annual re-fit, first ~40% of sample as burn-in, accumulating
genuinely-OOS forecasts across all regimes. **Primary metric: continuous incremental OOS R^2 of D over C,
dR2_OOS(D-C).**

- **Primary criterion: dR2_OOS(D-C) > 0**, credibility decided by inference + stability (NOT a fixed
  effect-size gate; the earlier 0.03 is dropped):
  - stationary/block bootstrap CI (mean block ~2h = 126d) excluding 0; HAC(lag>=h) cross-check;
    non-overlapping-window version reported.
  - **leave-one-transition-out (LOTO):** increment must not collapse when any single sign-transition is
    removed.
- dR2 reported continuously; ALSO translated to forecast-RMSE reduction and sign-classification
  improvement (§6) as practical secondary descriptors, not pass/fail gates.

## 6. Secondary sign-prediction test

Target `I(rho_{t,t+h} > 0)`. Compare `P(rho>0 | C)` vs `P(rho>0 | C + macro)` (regularized logistic;
shallow classifier as robustness), OOS rolling-origin. Metrics: OOS AUC, log-loss, Brier improvement, with
LOTO. Directly tests the central economic intuition (does macro help call the SIGN). Primary remains the
continuous rho; sign is secondary and is where Layer B interpretation is examined (does macro raise
P(rho>0) specifically in inflation/inverted-curve states?).

## 7. Transition / structural-break validation

Coefficient constancy alone is insufficient. Stability requires ALL four legs:
1. **Predictive transfer** across transitions (LOTO OOS).
2. **Coefficient stability** (rolling betas; Bai-Perron/Chow as one input only).
3. **Effect-direction stability** — sign of the STANDARDIZED macro effect consistent across regimes
   (scale-invariant; immune to predictor-variance shifts).
4. **Calibration stability** — predicted correlations well-calibrated to realized per regime.

Distinguishes: (world 1) stable relationship surviving transitions; (world 2) structurally changing
(direction/calibration shifts); (world 3) spurious co-trend (fails after detrending / fails at turning
points but "works" on slow drift).

## 8. Falsification criteria (fixed)

No evidence for orthogonal macro information if ANY:
- dR2_OOS(D-C) <= 0;
- increment collapses under LOTO (single-transition-driven);
- vanishes under an alternative vol proxy (RV-blend vs GARCH vs, over overlap, VIX);
- explained by a time trend (dies under detrending / turning-point test) — world 3;
- effect-direction or calibration unstable across regimes with no coherent mechanism — world 2;
- incoherent across maturities (10y vs 2y/30y inconsistent with a duration story);
- construction gate (Case E) fails AND `-dy` corroborator is null.

Support = dR2_OOS(D-C) > 0, CI excludes 0, survives LOTO, survives alt vol proxies + detrending, coherent
direction/calibration across regimes, coherent across maturities, `-dy` corroborator agrees. Achievable
but not trivial. ALWAYS labeled provisional (see §10 regime-count caveat) — never "replicated".

## 9. Minimum historical data

**Essential:** S&P 500 daily total return (~1980+); 10y yield (DGS10 / ^TNX, 1962+) and 2y (DGS2, 1976+)
-> synthetic 10y par-bond TR + slope; NFCI (1971+, vintage); RV (from S&P returns); VIX (1990+, overlap
check only); 3M T-bill (excess-return robustness). **Useful:** CPI (vintage) for inflation state + trend
control; DGS5/DGS30/DGS3MO; Moody's Baa/Aaa; IEF/TLT (Case-E validation). **Unnecessary:** HDP-HMM /
Z_HMM (not reopened); rest of ETF basket; intraday/options; pre-1990 VIX reconstruction. All free
(FRED + Yahoo). Real work = TR construction + validation + vintage handling, not data volume.

## 10. Stage-1 result classification (Case A-E) and regime-count caveat

| Case | Outcome | Interpretation |
|---|---|---|
| A | macro adds stable OOS info beyond flexible C, survives LOTO, improves continuous and/or sign | distinct macro/rates dependence dimension — **provisional (small regime-N)** |
| B | macro adds info in some regimes not globally | regime-conditional association, not universal |
| C | macro improves in-sample, fails OOS across transitions | historical co-trend / non-stationary |
| D | macro adds nothing beyond C | no orthogonal information in this target |
| E | synthetic bond TR fails validation AND `-dy` corroborator null | stop — invalid target |

**Regime-count caveat (permanent).** U.S. history offers ~2-3 historically distinct stock-bond
correlation transitions, but these are NOT independent replications — one secular macro arc; effective
independent regime realizations ~2. Not fixable with more U.S. data; only international pairs (DE/JP/UK)
add independent transitions. Hence LOTO (not "replication") throughout, and any Case-A result is stamped
provisional, with international pairs the pre-named confirmation escalation. Realistic expectation: Cases
B/C/D/E are more likely than a clean A; each is a legitimate, publishable result; distinguishing which is
true is the contribution.

## 11. Downstream staged decision tree (trading strictly downstream)

Chain: observable state -> distinct information -> stable OOS association -> cross-asset behavior ->
portfolio/risk implication -> (only then) trading rule -> OOS economic evaluation. Four gated stages;
**nothing past Stage 1 is built or parameterized now.**

- **Stage 1 (this prereg):** distinct-information diagnostic -> Case A-E.
- **Stage 2 — cross-asset behavior** (entry: Case A, or Case B scoped). Descriptive, no trading. Pre-declared
  panel of what the macro state may organize beyond volatility: equity-bond corr level/sign, bond
  diversification benefit, duration attractiveness, value-vs-growth, cross-asset hedging effectiveness,
  risk-budget dispersion. Each tested D-C-style, LOTO, provisional.
- **Stage 3 — portfolio/risk implication** (entry: a Stage-2 relationship stable OOS + economically
  coherent). Does conditioning a RISK CHARACTERIZATION on the macro state change ex-ante portfolio
  risk/diversification OOS vs a strong static + vol-only baseline? Risk understanding, not P&L.
- **Stage 4 — trading/allocation rule** (entry: Stages 2-3 both hold). One pre-registered simple rule, OOS
  economic evaluation vs a strong baseline (60/40, risk-parity, vol-targeting), net of costs. Provisional
  pending international confirmation before any capital.

Gating: reach Stage 4 ONLY from Case A (or scoped B), and ONLY after Stages 2-3 independently hold.
Case C/D -> stop the portfolio bridge (bank negative / methods paper). Case E -> stop before any economic
claim.

## 12. Frozen operational choices (resolved at approval)

- Horizon h = 63 primary; replication 21, 126.
- RV windows: 21 and 63.
- Level-C control: natural cubic spline df=4 per stress input + ridge (blocked-CV alpha); shallow GBM
  (depth 2) robustness.
- Case-E tolerances: corr(rho_synth, rho_IEF) >= 0.90 AND mean|drho| <= 0.10 over the overlap.
- Rolling-origin: first ~40% burn-in, annual refit; bootstrap mean block ~126d.
- Standardization: expanding causal z-score.
- Multiple testing: ONE primary (dR2_OOS(D-C), SPX-10y, h=63, continuous). Sign test is the one
  pre-declared secondary. All else replication/robustness.
- International pairs: NOT in Stage 1 (U.S.-only, as approved); pre-named Stage-2/confirmation escalation.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
