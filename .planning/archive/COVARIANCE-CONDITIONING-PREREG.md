---
title: Pre-registration — Stage-1' Covariance conditioning (non-volatility structure vs a matched volatility-only estimator)
status: FROZEN 2026-07-22 — do not edit features, estimator, primary metric, or thresholds after this date
chapter: 3 of the broader program (1 HMM/regime; 2 macro/rates prediction of stock-bond corr; 3 covariance conditioning)
approved_by: Adam, 2026-07-22
depends_on: RESEARCH-RECORD.md (HMM belief revision + macro Case-C); reframe audit 2026-07-22
---

# Stage-1' — Does an observable NON-volatility coordinate improve OOS covariance estimation and portfolio risk beyond a MATCHED volatility-only estimator?

Broader program question (reframed): **"Can observable market structure improve systematic portfolio
decision-making beyond what can be captured by volatility alone?"** This is chapter 3, a new object
(covariance matrix + eigenstructure) and a new lens (OOS portfolio consequence + covariance forecast
loss, NOT predictive R² on a scalar). This does NOT reopen the HMM (dead) or the macro-prediction (Case C).

## 1. Hypothesis
H1: conditioning the cross-asset covariance estimate on an observable coordinate beyond volatility —
market eigenstructure/absorption ratio primary — yields better OOS portfolio outcomes and lower covariance
forecast loss than a MATCHED volatility-only conditional estimator. H0: it does not. Estimation/conditioning
value, not prediction.

## 2. Object & lens
Object: forward covariance matrix and its topology (eigenvalue concentration). Lens: OOS portfolio
consequence (realized risk, hedge effectiveness, diversification, cost-adjusted) + direct covariance
forecast loss (QLIK/Stein + correlation-Frobenius). Not predictive R².

## 3. Universe (frozen)
Primary: ~14 liquid ETFs, daily auto-adjusted TR, common history ~2007-04+:
SPY, IWD, IWF, IWM, IEF, TLT, SHY, LQD, HYG, GLD, DBC, VNQ, EFA. Robustness: long-history FF-industry
daily portfolios + synthetic Treasury/credit/gold (1976+). Covariance is re-estimated and consumed DAILY
=> large effective-N (unlike chapter-2's ~2 transitions).

## 4. Estimator ladder (frozen). All Ledoit-Wolf-style shrinkage to a constant-correlation target,
identical recency kernel, identical bandwidth (h=1.0 std units); ONLY the state vector differs across
B_match/B_placebo/T.
- B0  unconditional LW-shrunk sample cov (rolling 252d).  [context]
- B1  EWMA/RiskMetrics cov (lambda=0.94).                  [context: industry vol clock]
- B_match  similarity-weighted, state = [volatility descriptor only].   << THE MATCHED BASELINE
- B_placebo similarity-weighted, state = [vol, phase-randomized surrogate coordinate].  [negative control:
            dimensionality/persistence-matched, uninformative -> isolates "extra kernel dim" artifact]
- T   similarity-weighted, state = [vol, absorption ratio].  << TREATMENT (primary: +1 non-vol coord)
- T+  similarity-weighted, state = [vol, absorption, slope, infl, credit].  [secondary]

PRIMARY INCREMENTAL TEST: T vs B_match (NOT T vs EWMA). B_match vs B1 reported as architecture context only.

## 5. Conditioning coordinates (frozen, limited)
Vol descriptor: trailing 63d realized vol of the equal-weight universe (scalar market-stress state).
Non-vol PRIMARY: absorption ratio = top-3 eigenvalue share of the trailing 252d correlation matrix.
Non-vol SECONDARY (T+ only): macro slope + CPI-YoY inflation + credit(Baa-Aaa), from histext_daily.csv.
All causal (trailing), standardized by expanding z-score. No orthogonalization needed: T-vs-B_match
isolates the incremental coordinate by construction.

## 6. Portfolio construction (covariance consumers, as-of-t weights)
Long-only global minimum-variance (GMV) [PRIMARY consumer]; risk parity; long-short GMV; 1/N reference;
minimum-variance equity-bond hedge (SPY hedged by IEF+TLT). Monthly (21d) rebalance primary; weekly robustness.

## 7. Transaction costs (frozen)
c = 3 bps x one-way turnover per rebalance PRIMARY; sensitivity {0,5,10}. Report gross and net.

## 8. OOS procedure
Rolling causal; ~2y burn-in; estimate on trailing data, hold to next rebalance, record realized returns.
Conditioners lagged/trailing. No refit lookahead.

## 9. Metrics (frozen) — two axes, reported jointly
M1 portfolio consequence (closure-determining): Var(GMV_T)/Var(GMV_Bmatch), net 3bps, stationary
   block-bootstrap CI (mean block ~63d). Support: ratio<1, CI excludes 1.
M2 covariance forecast loss (estimation quality): vs forward-21d realized covariance -- QLIK/Stein loss
   (full cov, GMV-decision-aligned) + Frobenius on the correlation matrix (isolates dependence structure).
   T vs B_match loss difference, block-bootstrap CI. Support: lower loss, CI excludes 0.
Coherence grid: (M1 better & M2 better)=genuine; (M1 better, M2 not)=portfolio-behavior artifact;
   (M2 better, M1 not)=estimation gain without portfolio value; (neither)=null.

## 10. Support & closure (frozen)
Support: T beats B_match on BOTH M1 and M2, surviving robustness (GMV+risk-parity; monthly+weekly;
costs {0,5,10}; hedge effectiveness; diversification ratio; leave-one-crisis-out 2008/2020/2022), AND T
beats the dimensionality-matched B_placebo comparably (coordinate is informative, not just an extra dim).

CLOSURE (scoped, per Adam 2026-07-22): "A null result closes this specific covariance-conditioning
approach and establishes that the pre-specified observable coordinates and estimator architecture do not
provide incremental OOS covariance or portfolio value beyond the matched volatility-only baseline. It does
NOT establish that all useful non-volatility market structure has been exhausted." Untested fundamentally
different objects remain: factor structure, tail dependence, nonlinear dependence, dynamic factor
loadings, liquidity/funding relationships, other portfolio-specific dependence structures.

Discipline on a null: interpret the failure and decide whether it points to a genuinely different research
question. Do NOT add features and search until something works.

## 11. Downstream (only if support)
Only then: is the realized-risk/hedge improvement economically meaningful net of costs, and tradeable vs a
strong baseline (60/40, risk-parity, vol-target)? Not part of this test.

## 12. Honest prior
~15-25% on support. The matched baseline is a high, correct bar: T must show the non-vol coordinate itself
adds covariance-structure info beyond a vol-conditioned version of the SAME estimator. A null is a clean,
scoped closure of this chapter, not the whole program.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
