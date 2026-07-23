# Regime-Detection — Session Notes

## Status
Architecture: v2 = statistical jump model program (v1 HDP-HMM sealed at `v1-convergence`)
Branch: main
Last updated: 2026-07-22 (night)

## Session 2026-07-22 (night) — V2 DIRECTION CHOSEN + Phases 0-1 executed; battery falsifies fee-vs-VT capability in silico

**Direction (Adam-driven reframe):** Adam rejected successor-question candidates derived from the
repo's own record and demanded outward grounding. A 3-agent methodology sweep (academic SOTA /
practitioner systems / data+stats standards) produced a 10-point gap list vs field practice — key
items: estimator was 2011-era (K-saturation + window sensitivity are DOCUMENTED HDP pathologies with
known remedies — Miller-Harrison 2013, Pohle et al. 2017; the 2020s standard is the statistical jump
model), NFCI carries real embedded lookahead (Chicago Fed refits its factor model full-sample weekly;
our 7d lag fixed availability only — Amburgey-McCracken 2023), features nonstandard (field uses
downside-dev/Sortino EWMs, log-VIX), training sample below field floor, home-rolled stats where
Clark-West/Giacomini-White/tail-weighted Amisano-Giacomini are standard, and the FKO economic-value
lens never run. Where we're AHEAD: causal discipline, matched baselines, prereg. Full plan:
`.planning/V2-JUMPMODEL-PLAN.md` (with execution status), gap sources cited there.

**V2 = build the field-standard instrument (K=2 weighted jump model, return-only features, 1926+
French data) under v1 discipline; test the field's own economic claims.** Adam approved autonomous
execution; Learning-Mode core-writing waived (precedent: tailhazard core).

**Phase 0 DONE, gate PASS** — `scripts/v2_build.py` → `data/processed/v2_daily.csv` (NOT committed;
regenerate via the script): French daily mkt TR + RF 1926-2026, 51 stress episodes, SPY cross-check
clean (corr 0.995 modern era; full-overlap 0.979 diagnosed as universe difference + 90s SPY noise).
French publishes ~1-2mo lagged → live instrument needs SPY-splice tail (Phase-4 item).

**Phase 1 DONE** — `scripts/v2_core.py` (weighted JM: coordinate descent, exact DP assignment with
k=2 fast path, sparse-JM-style feature weights, dd-quantile init; **causal filter = endpoint of the
forward DP value recursion** — greedy one-step rule was built first and FAILED the battery: it can
only switch on single-day evidence > lambda), `v2_eval.py` (FKO fee closed-form, VT/SMA/B&H baselines,
stationary bootstrap), `v2_pipeline.py` (shared walk-forward: annual refits, lambda from grid by
validation Sharpe, frozen params, byte-identical for synthetic and real runs), 20 passing tests incl.
causality invariants + DP-vs-brute-force + filter chaining equivalence.

**Phase 1 finding (the load-bearing one):** synthetic battery (`results/v2_synthetic_validation.csv`,
bars in-script) — B3 null-calibration PASS; B1/B2 capability FAIL. Oracle decomposition: perfect
regime knowledge beats vol targeting by +136..+1090 bps/yr, but lagging the oracle 10-21d erases
most/all of it, and causal filters intrinsically lag ~5-20d. The pipeline DOES beat B&H when regimes
exist (= the literature's actual claim, Shu/Mulvey 2024). **In-silico: VT subsumes persistent-regime
value at daily frequency up to detection lag** — v1's "vol absorbs everything" re-derived from first
principles, now with a mechanism (reaction-speed race, not information content).

**2026-07-23 ~5:50am — REAL RUN COMPLETE (381 min): CASE B, full deflation + an exceptional
instrument.** Primary fee(JM−B&H) +487.8 [−47.4, +1138.8] → F1; ALL THREE control bands contain or
exceed it (placebo 95th=541, surrogates [41,1080], iid [179,805]) and the exposure-matched constant
mix beats the overlay (−48.7) → the "beats B&H" claim is an exposure/utility artifact, not timing.
Deflation exhibit CONFIRMED significantly: fee(JM−VT) = −255.8 [−477.5, −36.7] — vol targeting
dominates, mechanism as predicted in silico. BUT: label stability 1.000/1.000 vs incumbent 0.809,
1.66 switches/yr, F2/F3 clear — the estimator-instability problem is solved by this architecture.
Chapter written: RESEARCH-RECORD.md top section. **NEXT: Phase 4 decision with Adam — swap the
Portfolio-Manager label source to the JM label (instrument decision, NOT an alpha claim). Open
design item: map 2 JM states onto the live 3-label LOW/MED/HIGH_VOL contract without breaking
downstream. Do NOT touch data/oos_regime_labels*.csv until that mapping is decided.**

**LATER SAME NIGHT (2026-07-22) — prereg FROZEN (Rev 2) + real run LAUNCHED.** Adam directed: final audit sweep,
then wire up the proper backtest, era focus 1990+. Second 2-agent sweep (backtest methodology +
adversarial code audit): NO critical findings; fixes applied pre-freeze — delay=2 next-close
execution headline (delay=1 was same-close; matches Shu/Mulvey's actual convention), rf footing in
C2/C3, 8y λ-validation window, moment-drop LOTO/era fees, full-panel baseline warmup. Prereg Rev 2:
primary = fee(JM−B&H) γ=10 (replication claim), deflation exhibit fee(JM−VT) expected ≤0; train
1970+, score ~1990→2026-05. Full audit trail: prereg §11. Stage-1 runner smoke-tested on synthetic
(correctly Case D on iid noise). **Real run launched ~2-3h; verdict + RESEARCH-RECORD chapter next.**

## Session 2026-07-22 (evening) — tail-hazard primary NULL; OU/Kalman correlation state NULL on both lenses

**Tail-hazard stage 1 (frozen prereg §8) — primary result is in and it is NULL.** OOS N=10049
(1986-08-28..2026-07-21), 352 events. dlogscore(D−C) = −0.00039, block-boot 90% CI [−0.00097, +0.00012],
P(>0)=0.11 — C (splines on leverage-aware set) beats D (+excitation) on point estimate; CI includes 0.
b: early-half mean −0.248 vs late-half −0.041 — whatever excitation existed is decaying toward zero in
the modern sample. LOTO: dropping dot-com makes D look *worse* (−0.00047) — no single-crisis rescue.
Full log: `results/tailhazard_stage1_run.log`. **Controls finished 21:09 — all clean and consistent:**
surrogates ≈0 (−0.00008), no-excitation simulation band [−0.00053, +0.00006] CONTAINS the primary,
VIX kill-check independently null (−0.00045, CI incl 0). **Formally CLOSED same night** —
RESEARCH-RECORD.md top section. Per the pre-declared stopping rule (§8.9/§9): null → program converged.

**Post-null exploration (Adam-directed): continuous latent correlation state, OU/Kalman.**
Direction: keep regime detection, drop HMMs, lens = "know the state we're in" (filtering quality),
NOT flip prediction. Built `scripts/corrfactor_stage1.py` (forecasting) and
`scripts/corrfactor_stage2_contemporaneous.py` (contemporaneous incremental info, stage1p architecture
reused byte-for-byte). Verdict: **NULL on both lenses, and diagnostically dead** — the MLE drives
observation noise → 0, Kalman gain → 1, so x_t ≡ raw z_t exactly (corr 1.000): the model itself says
there is no latent state distinct from the observable. EWMA(0.97) beats the Kalman on forecasting;
placebo noise coordinate matches it contemporaneously; partial corr given baseline CI includes 0.
Bonus finding: rolling-252d corr coordinate reproduces the absorption ratio's M1 blowup (2.23 vs 2.24) —
Chapter-3's GMV degradation is systematic to long-window correlation coordinates in this kernel
architecture. Full write-up: RESEARCH-RECORD.md top section; results in `results/corrfactor_stage2.csv`
+ `results/corrfactor_stage2_run.log`.

**Decisions (Adam, late session):** NO formal paper — RESEARCH-RECORD.md is the durable artifact.
Repo is KEPT and repositioned for a successor regime-detection question; v1 program sealed at tag
`v1-convergence`; converged-program research scripts archived (see `archive/`).

**Next action (the open question — everything else is done):** choose the new information source.
The v1 record constrains the choice: another representation of the same daily index-level features is
pre-refuted; a successor must tap NEW information (cross-sectional breadth, intraday, positioning/flows,
options surface, …). New thesis → then rewrite CLAUDE.md constraints + data layer around it.

## Session 2026-07-22 (direction decision) — "Continuous state + jumps" proposal evaluated → reduced to a tail-hazard MVE

Adam proposed reframing to a continuous-time latent state with jumps (dX = μdt + σdW + JdN),
explicitly not assuming the HMM survives. Full analysis: `.planning/CONTINUOUS-JUMP-STATE-DECISION.md`.
**Decision:** (1) literal latent jump-diffusion REJECTED — the continuous-state half was already run and
returned null (Z_t / EWMA-env: no incremental info; any filtered state is a function of the same
observables — representation cannot create information), and the jump half is unidentifiable at daily
frequency (jump vs heavy-tail vs fast-vol needs intraday/infill data — BNS bipower, Aït-Sahalia–Jacod).
(2) The one NEW, testable, gate-clearing component: **self-exciting tail-event intensity** (option D of
Adam's taxonomy) — after conditioning on the strongest vol model, do exceedances of z_t = r_t/σ̂_t still
cluster? Orthogonal to the vol axis BY CONSTRUCTION (standardized residuals). Also = the univariate
version of "tail dependence," one of the two untested objects named at Chapter-3 closure.
**APPROVED by Adam 2026-07-22, with revision:** ladder must contain an explicit leverage-aware rung
below the self-excitation comparison, and no freeze until event definition, vol model, threshold, and
ladder are causally specified. Done — §8 now pins: Layer-1 = GJR-GARCH(1,1)-t (leverage-aware),
expanding annual causal refits, 1950s initial window, events from 1960-01 (no full-sample fitting —
CR-04 bug class); events e_t = 1{z_t < −2.0}, fixed constant threshold; ladder
A → B_vol → B_lev (signed-return sums, RS⁻ share, down-day counts — absorbs leverage so b can't claim
it) → C (splines+ridge on B_lev set) → D (+H_t, β from fixed half-life grid {1,2,5,10,21,63}d); primary
OOS Δlog-score(D−C) with the full increment curve reported; prob clipping, uniform covariate set,
NFCI (1971+, 7d lag) and VIX-era kill-check as pre-declared variants. ~420–580 events, ~10 crisis
episodes, scoring starts ≈1986. If null → Chapter 4 of the methods/negative paper.
**FROZEN 2026-07-22** — Adam signed §8.9; also declared this the **FINAL preregistered experiment of the
current research program** (null → accept convergence, write the paper; Case A → genuinely new axis).
Recorded as a pre-declared stopping rule in the doc (§8 status + §9). Design changes now prohibited.

**Build session 1 DONE (2026-07-22):** `scripts/tailhazard_build.py` → `data/processed/tailhazard_daily.csv`
+ `results/tailhazard_{garch_params,construction_gate}.csv`. Construction gate CLEAN: 530 events @ c=2.0
(rate 3.16%, inside the frozen 2.5–3.5% band), 67/67 GJR refits converged, all 11 pre-named crisis
episodes contain events, per-decade counts even (56–94). Sanity highlight: top-|z| days mix raw crashes
(1987-10-19, z −9.5) with low-vol surprises (2007-02-27: −3.5% raw but z −7.5) — standardization doing
its job. venv note: `.venv` exists and has arch 8.0.0 / yfinance 1.2.0 (the dev-CLAUDE.md "not yet
created" row is stale).

**Build session 2 DONE (2026-07-22): full stage-1 battery scaffolded + smoke-tested.**
`scripts/tailhazard_stage1.py` (mirrors histext_stage1 idioms): ladder A/B_vol/B_lev/C(spline+ridge,
blocked-CV alpha)/D(+H_t, half-life grid), rolling-origin annual refits, 40% burn-in, per-day
log-scores clipped 1e-5, stationary block bootstrap (mean block 126d), LOTO over the 11 episodes,
increment curve D−A/D−B_vol/D−B_lev/D−C, per-refit b + chosen half-life (sign-stability falsifier),
Christoffersen screen, hazard-shape diagnostic, all 3 controls (positive-tail placebo, shifted-history
surrogate ×10, simulation calibration ×10), VIX-era kill-check. NFCI variant intentionally SKIPPED
(NFCI not in panel — session-3 item). **Every rung fits by penalized MLE over Adam's `bernoulli_nll`
with H from Adam's `excitation_state` — the battery cannot run until the core is written** (blind
preserved: no real-data result exists). Adam confirmed the causal convention H[t]→e[t+1] (leak
reasoning correct, incl. β distortion).

**Smoke-tested on SYNTHETIC panels only** (scratchpad-only reference core, never committed):
iid (b=0) → clean null (dLS −0.0002, CI incl 0, b sign-inconsistent, Christoffersen p=0.86);
strong excitation (b=1.2, went supercritical — 96% event rate, a branching-ratio object lesson) →
detected (dLS +0.056, P>0=1.00); moderate realistic (b=0.5, 3.5% rate, 95 OOS events) → detected
(dLS +0.0020, CI [+0.0002,+0.0038], b +0.72 sign-consistent), controls all ≤0. Real run has ~330 OOS
events ≈ 3.5× that power. Surrogate-control reading: PASS = not positive (strongly negative under
genuine excitation is expected — destroyed history actively hurts D).

**Core WRITTEN (2026-07-22, by Claude at Adam's direction — Learning-Mode arrangement waived):**
`excitation_state` (O(n) recursion) + `bernoulli_nll` (logit-space via logaddexp) in
`scripts/tailhazard_core.py`; all 5 property tests PASS. Pre-run verification checklist all green
(prereg frozen/unchanged, β grid, rungs, OOS, bootstrap/LOTO, H_t→e_{t+1}, no prior results).

**Real run LAUNCHED then ABORTED 2026-07-22 ~16:50 (Adam had to shut down).** ~12 min in, still inside
the primary OOS loop; stdout was block-buffered so NOTHING was observed and results write only at
completion → **no partial results exist, blind fully intact, relaunching is NOT a protocol violation**
(the one-look discipline applies to completed results, none were produced).

**Next action — relaunch when the machine can stay on ~2.5h (overnight is ideal):**
`.venv/Scripts/python scripts/tailhazard_stage1.py 2>&1 | Tee-Object -FilePath results/tailhazard_stage1_run.log`
(full battery, no --quick). Then the 12-part report incl. branching ratio
n ≈ b·p̄(1−p̄)·e^(−β)/(1−e^(−β)) and frozen case classification. Session 3 after verdict: NFCI variant,
RESEARCH-RECORD chapter. Nothing committed to git yet this arc.

## Session 2026-07-22 (latest) — Chapter 3 (Stage-1' covariance conditioning): NULL/negative, scoped closure

Frozen prereg `.planning/COVARIANCE-CONDITIONING-PREREG.md`; run `scripts/stage1p_covariance.py`
(`results/stage1p_covariance.csv`). New object (covariance matrix + eigenstructure), new lens (OOS
portfolio risk + covariance forecast loss, not predictive R²). 13-ETF universe 2007–2026, 206 monthly OOS
rebalances. PRIMARY test = T (vol+absorption ratio) vs **B_match** (matched similarity-weighted vol-only).

**Result: T fails, decisively negative.** M1 Var(GMV_T)/Var(GMV_Bmatch)=**2.24** [90% CI 1.00,4.33] —
T's min-var portfolio has 2.24× the variance (realized vol 1.98% vs 1.32%). M2: correlation-Frobenius
Δ=+0.004 [−0.020,+0.027] (FLAT — absorption adds nothing to the dependence-structure estimate); QLIK
Δ=−0.089 [−0.154,−0.019] (trivial ~1% average edge, contradicted by M1 → the exact coherence-grid case the
M2 metric was added to catch). Mechanism: AR is persistent/trending → similarity kernel concentrates weight
→ small effective sample → occasional degenerate covariances (0.5%) → GMV amplifies → variance blowup.
Controls: **placebo** (matched dim, uninformative coord) does NOT degrade (1.32%=B_match) → degradation is
AR-specific, not a kernel-dimension artifact; B_match vs EWMA ratio 0.95 → architecture is fine. Robust:
worse at all costs, all leave-one-crisis-out (2.24/2.31/2.53), risk-parity, hedge, diversification; T+
(adding macro/infl/credit) also worse (2.23).

**Scoped closure (frozen wording):** closes THIS covariance-conditioning approach / universe / features /
architecture — the pre-specified observable coordinates and estimator do NOT add incremental OOS covariance
or portfolio value beyond the matched vol-only baseline. Does NOT prove all non-vol structure exhausted.
Untested different objects remain: factor structure, tail dependence, nonlinear dependence, dynamic factor
loadings, liquidity/funding, other portfolio-specific dependence.

### Program status — three chapters, all null (genuine narrowing, not circling)
1. HMM/regime latent info → no robust incremental info. 2. Macro/rates → stock-bond corr → Case C
co-trend, no stable incremental prediction. 3. Covariance conditioning → this null. Broader question is now
"can observable structure improve systematic portfolio decisions beyond volatility?" — three
increasingly-well-designed nulls. **Decision point (do NOT auto-run a 4th experiment):** interpret whether
any remaining object (tail dependence / dynamic factor loadings the strongest candidates) is worth a
genuinely different design, or write the methods/negative paper documenting the three-chapter arc. Adam to choose.

**DIRECTION CHANGE (Adam, 2026-07-22):** pivot to a **Continuous-Time Latent Market State with Jumps**
(jump-diffusion / continuous-time latent state). Closes the discrete-HMM + macro-prediction +
covariance-conditioning arc; the three-chapter negative record stands and the methods/negative paper is the
documented fallback. The jump/tail framing targets the one object the reframe audit flagged as genuinely
untested. Next session: design + pre-register the jump-model experiment (object, baseline, metric,
falsification) before running — same discipline as the last three chapters. **This chat is closed.**

## Session 2026-07-22 (latest) — Stage-1 prereg FROZEN + Case-E construction gate PASSED

New, separate research line (does NOT reopen the HMM thesis): does the observable **macro/rates axis**
carry incremental, stable OOS information about **stock-bond correlation** beyond the strongest honest
volatility/stress baseline? Approved Option A (U.S.-only first stage).

**Pre-registration FROZEN:** `.planning/STOCKBOND-MACRO-PREREG.md` (2026-07-22) — hypothesis, primary
target (fwd 63d corr, SPX vs synthetic constant-maturity 10y par-bond TR), baseline ladder A→D (primary =
**D−C**, macro beyond a flexible spline+ridge stress model incl. RV21/RV63/NFCI/credit), macro axis
{slope, inflation}, primary metric ΔR²_OOS(D−C)>0 with block-bootstrap CI + leave-one-transition-out,
secondary sign-prediction test, 4-leg structural-break validation, Case A–E table, and a downstream
Stage 1→4 decision tree (trading strictly downstream; Stage 4 reachable only from Case A/scoped B).
Regime-count caveat is permanent (~2 independent U.S. transitions → any positive is provisional;
international pairs are the pre-named confirmation escalation). Do NOT alter hypothesis/thresholds by result.

**Case-E construction gate PASSED** (`scripts/histext_construction_gate.py`,
`results/histext_construction_gate.csv`): synthetic 10y par-bond TR reproduces the ETF-based stock-bond
correlation over 2002–2026 — corr(ρ_synth, ρ_IEF)=**0.985**, mean|Δρ|=**0.041** (frozen bar ≥0.90/≤0.10);
−dy corroborator identical (corr 1.000); the 2021→2022 sign flip is reproduced. Target is valid.

### Stage-1 RESULT (2026-07-22) — **Case C: historical co-trend / non-stationary**
Built `data/processed/histext_daily.csv` (1976-06→2026-07, ~12.1k complete-case days; 3 corr regimes /
2 major transitions: +pre-2000, −2000-2021, +2022; stress spans both signs; inflation 1976-82/1990/2008/
2021-23). Ran the frozen battery (`scripts/histext_build.py`, `scripts/histext_stage1.py`,
`results/histext_stage1.csv`).

**DECISIVE CONTEXT: all models have deeply negative OOS R²** (A −1.28, B −1.40, C −1.52, D −1.27) — they
predict forward corr *worse than the pooled mean*. So the frozen primary ΔR²(D−C)=**+0.253** is the gap
between two failing models — NOT "macro predicts correlation." 90% CI **[−0.017,+0.564] includes 0**
(support bar required exclude-0 → fails). **Two frozen falsifiers triggered:** (#4) detrending collapses
it +0.25→**−0.040** (co-trend); (#5) slope coef flips sign across regimes (−0.01/−0.09/+0.17) and
calibration fails (per-regime R²_D −1.29/−2.98/−0.28) → non-stationary. Per-regime ΔR²: R1 **−0.17**
(long positive era — fails there), R2 +0.42, R3 +0.87. Robust across maturities (2/5/10/30y +0.16..+0.23),
horizons (+0.16/+0.34), −dy corroborator (+0.25), alt vol proxies — but "robust between two failing
models" ≠ useful. **One on-mechanism positive:** stress alone predicts corr SIGN at AUC 0.497 (chance);
+macro → AUC 0.597 (ΔAUC +0.10) — consistent with vol=magnitude, macro=sign, but modest and plausibly
low-frequency era-identification (the thing detrending removes). Not enough for Case A.

**Verdict: Case C.** Macro/rates axis does NOT give stable incremental OOS info about the *level* of
stock-bond correlation beyond volatility; the increment is a non-stationary co-trend. HMM thesis stays
separate/dead. Per frozen §11 downstream tree, **Case C → STOP the portfolio bridge** (no Stage 2 on U.S.
data). No trading/allocation work.

### Next action (recommendation)
Default: **bank the negative + write the methods paper** (stable observable geometry; HMM adds nothing;
macro axis adds no stable incremental dependence info beyond a co-trend; unproven on-mechanism sign hint).
Only optional, clearly-provisional continuation: **international stock-bond pairs** (DE/JP/UK) — the one
way to get independent transitions and adjudicate whether the corr-SIGN signal is real vs one secular arc.
Pre-register it the same way; it is diagnosis, NOT a portfolio bridge. Awaiting Adam's choice.

## Session 2026-07-22 (later) — Belief Revision: the HMM coordinate is a compression, not a distinct latent state

Pre-registered OOS incremental-information test (`scripts/representation_information.py`,
`results/representation_information.csv`) — the direct test never previously run (prior negatives used
the VIX-projected discrete label; stage2 used an EWMA proxy, not the actual HMM `Z_t`).

**Result (Case A — no evidence):** `Z_loc` adds **no** incremental OOS information about forward SPY
realized vol beyond rich causal observables. Primary 21d ΔR² = −0.040 (perm p=0.53; boot 90% CI
[−0.41, +0.01]; phase-randomized negative control median −0.061 — `Z` ≈ its own surrogate). Broadly
negative across {5,21,63}d × {all, hiVIX, loVIX} + entropy; no Bonferroni cell passes; ΔR² → 0 as the
baseline is enriched (redundancy signature). Absolute: R²_X = 0.140 vs R²_{X+Z} = 0.100.

**Correction:** `Z_t` OOS cross-perturbation stability is only ≈0.42–0.60 (cross-seed/window/feature/
K_max) — far below the in-sample 0.92–0.97 the Continuum-Turn section reported. Even same-data seed noise
→ ≈0.45.

**Revised belief:** the HMM coordinate is a moderately-stable statistical *compression* of the
observables, not a distinct latent environment with incremental vol info. Durable writeup:
`RESEARCH-RECORD.md` → "Belief Revision". Scope: the negative is specific to volatility targets;
dependence/tail/factor properties untested.

### Next action (re-entry) — a GATE, not an experiment
Do NOT run another experiment unless it clears this gate: *why should `Z_t` (or the macro/curve axis)
carry information about `Y_t` orthogonal to the volatility axis?* Assessed 2026-07-22: the only principled
candidate is the **rates/inflation-regime family** (stock-bond corr sign; duration / value-growth
rotation), governed by PC2 (macro/curve), to which VIX is sign-blind. BUT (a) it is a *conditioning*
claim (macro axis beyond VIX), not the latent-distinctness claim that just failed, and (b) our 2016–2026
window contains ~one relevant macro-regime shift (2022) → severely underpowered / single-episode. Honest
default: the project has likely reached its strongest defensible conclusion — a stable statistical
geometry of observable vol/stress + macro conditions, with no independently-informative latent state.
Pursue the rates-regime question only via a longer sample (pre-2000, multi-regime) or as an explicit
descriptive-conditioning study with single-episode caveats — not as a rescue of the latent thesis.

## Session 2026-07-22 — The Continuum Turn: HMM estimator rejected on OOS prediction; env is a continuous 2-D coordinate

Big reframe + 6 reproducible experiments. Durable narrative: `RESEARCH-RECORD.md` → "2026-07-22 — The
Continuum Turn". Forward plan: `.planning/ROADMAP.md`. Arc:

- **Reframe** (ROADMAP.md): goal = a *trustworthy* state, defined as CALIBRATION (not accuracy),
  purpose-relative + confidence-conditional; two-stage (trusted state → conditional asset behavior).
- **Phase 0 gate** (`scripts/trust_gate.py`): cross-window agreement IS a real confidence signal (state
  η² rises 0.095→0.160 with agreement); but the VIX-projected state ties the VIX 15/25 null on forward-vol
  resolution (η² 0.078 vs 0.081). (RMSE-by-confidence was heteroskedasticity-confounded — use η².)
- **Raw-state fingerprint** (`scripts/raw_state_fingerprint.py`): the 8 raw states are **~2-D (PR 1.88),
  NOT a 1-D vol ladder** — PC1 (65%) stress = VIX+NFCI, PC2 (32%) macro = yield_slope, nearly orthogonal
  (cross-state corr 0.15). **Every prior "no beyond-VIX" negative was on the VIX-rank-merged label, which
  deletes PC2 by construction.**
- **Characterization** (`scripts/state_characterization.py`): it's a weakly-structured **CONTINUUM**, not
  discrete clusters (silhouette 0.19; GMM BIC never minimizes → explains K-saturation + E2 instability).
  Macro axis RECURS (corr w/ time 0.06, 92 crossings), not secular. No independent scale dim (cleanly 2-D).
- **Continuous-state diagnostic** (`scripts/continuous_state_diagnostic.py`): Z_t = E[μ_S|x] is STABLE
  across windows (PC corr 0.92–0.97; label ARI 0.60–0.81 — far above E2's 0.04–0.33, so most of E2's
  "instability" was the VIX-merge/label-switching artifact). Z_t is ~2/3 explained by a plain EWMA of the
  features (R²=0.68): trustworthy coordinate, mostly smoothed features + ~1/3 model-specific.
- **Filter horse-race** (`scripts/filter_horserace.py`) — DECISIVE: **the current HMM-based environment
  estimator is REJECTED on OOS predictive grounds vs simpler continuous filters.** Scale-invariant OOS corr
  predicting X_{t+h}: HMM 0.25–0.38 vs EWMA/VAR/persistence 0.51–0.73 (~half the info), every horizon, both
  regimes. Mechanism: discretizing a continuum discards within-state position (~half the predictive signal;
  corr(Z_t,X_{t+1})=0.38 < corr(X_t,X_{t+1})=0.71). SCOPE: this estimator on this evidence — NOT "HMMs wrong".
- **Stage 2 first cut** (`scripts/stage2_conditioning.py`): continuous env coordinate (stress=VIX+NFCI,
  macro=slope) adds **no reliable incremental OOS value over raw features** for conditioning cross-asset
  behavior (ΔR² mostly ≤0). Descriptive conditional structure exists (stress tertiles: TLT +1.1%→−0.6%,
  SPY +0.6%→+2.1% fwd-21d) but ~captured by raw features. Stock-bond (SPY–IEF) corr weakly tracks macro
  (+0.14; −0.21 inv → −0.04 steep). Basket cached: `data/processed/cross_asset.csv` (SPY IEF TLT HYG LQD
  GLD IWF IWD via yfinance).

**Net:** trustworthy object = a continuous, stable 2-D (stress, macro) coordinate ≈ the smoothed macro
features; the HMM adds no predictive value and is rejected as the estimator; the coordinate shows no clear
incremental conditioning value over raw features yet (first cut, low OOS power).

### Next action (re-entry)
1. If pursuing Stage 2: redo with block-bootstrap significance, a cleaner env spec, and focus the
   macro-axis → duration/style/stock-bond-corr hypotheses (the one place beyond-VIX structure could live),
   strictly benchmarked vs raw features.
2. If that also shows nothing incremental, write up the **methods/negative paper**: (a) the 2-D
   stress/macro geometry the VIX-projection hid; (b) markets = weakly-structured continuum, not discrete
   regimes (explains K-saturation); (c) HMM estimator rejected on OOS prediction vs simple filters;
   (d) cross-window agreement as honest confidence. Retires the discrete-HMM framing.

Nothing needs doing immediately. `paper.tex` untouched and now badly out of date.

## Session End 2026-07-21 — feature investigation done; headline thesis NOT supported

Full arc this session: research audit → reproducible significance test → feature diagnostics → reduced
feature search. **Verdict: the regimes are volatility regimes (overdetermined) — no beyond-VIX
information, and no tradeable alpha.** The vol ladder recovers even with zero vol inputs (no VIX, no
NFCI); every candidate feature (dispersion & participation breadth, slope, NFCI) collapses onto the vol
axis; K saturates at 8 in every fit. Robustness ⇒ already priced.

The durable take-away doc is **`RESEARCH-RECORD.md`** — see especially "Alpha Assessment & Where This
Leaves the Project" for the 4 options (pivot the paper to descriptive/methodological + honest negatives;
ship the tool as risk-ops only; treat alpha as a separate problem; or shelve). Nothing needs doing now.

New scripts (all reproducible): `scripts/significance_test.py`, `feature_ablation.py`,
`feature_discovery.py`, `feature_search.py`. `paper.tex` intentionally untouched pending the pivot decision.

---

## Experiment 1 DONE — significance test (surprising result)

`block_permutation_test()` implemented in `src/core/evaluation.py`; `scripts/significance_test.py` runs
end-to-end and is now the reproducible source for the ΔR² numbers (Finding 4 closed). **Result: 0/4 cells
significant under the block-permutation null** — return 5d p=0.20, return 21d p=0.16, vol 5d p=0.73, vol
21d p=0.50. The prior "regimes carry beyond-VIX volatility information" claim does **not** survive; vol
was demoted *hardest*. The bootstrap CIs all excluded 0 — the predicted mirage (ΔR²≥0 by construction).
Leading cause: **regime↔VIX collinearity** — the regime is a VIX-rank partition, so it can't add much
beyond VIX; permutation decorrelates it and inflates the null (observed ΔR² sits below the null median
for vol). This is quantitative proof of the audit's core concern: you can't test "beyond VIX" with a
label built from VIX. Full writeup + numbers: `RESEARCH-RECORD.md` → "Experiment 1 — Result".

Files: `scripts/significance_test.py` (new), `block_permutation_test()` in `evaluation.py` (new),
`results/significance_test.{txt,csv}` (generated). Check question answered: row-shuffle → smaller p →
overstates significance; block-permute is the honest choice.

**Next: Experiment 3** (raw 8-state fingerprints + VIX-ablation) — the only way to make the beyond-VIX
question answerable, since today's label is a function of VIX. Secondary: a conditional (VIX-stratified)
permutation as the "fair" version of this null.

## Research Audit (2026-07-21) — `RESEARCH-RECORD.md` (root)

Durable research record promoted to repo root (`RESEARCH-RECORD.md`); full technical evidence retained
at `.planning/RESEARCH-AUDIT.md`. Full read-only research reconstruction + statistical-validity audit.
No code changed. Verdict:
narrow thesis Partially Supported; headline thesis ("VIX-irrecoverable structure recovered by a
nonparametric model") Not Yet Established. Four findings not previously logged, ranked:

1. **[HIGH] Table 2 "posterior-mean transition matrix" is neither.** `run_paper_experiments.py:133-137`
   computes it as an empirical count on the hysteresis-smoothed, VIX-merged 3-state labels — not
   `params['trans_matrix']` (the real posterior matrix `get_transition_matrix()` extracts but is never
   used). High diagonals are partly inflated by hysteresis + the 8→3 merge, so "persistence is not
   imposed by the model" is backwards. Paper prose diagonals (0.989/0.986/0.974) are also stale vs the
   regenerated table (0.986/0.984/0.976).
2. **[HIGH] In-sample dwell comparison is confounded** — HDP labels get 3-day hysteresis; the
   VIX-threshold + parametric baselines it's compared against get none. Same class of bug already fixed
   for OOS (e6962df), but the inverse asymmetry is still baked into the paper's headline (66/61/41 vs
   8-17). Persistence advantage is real but its *magnitude* is inflated.
3. **[HIGH] The HDP's K-selection is inert.** `effective_K` = mean 8.0, std 0.0, mode 8 every run — it
   saturates K_max and keeps all 8 states; the 3 regimes are imposed by the VIX-rank tertile cut, not
   discovered. On current evidence the nonparametric complexity isn't demonstrably beating a fixed-K
   sticky HMM (and the one parametric baseline is degenerate: Moderate-Vol N=367, dwell=367 = one block).
4. **[HIGH] The significance test isn't reproducible.** `block_bootstrap_ci`/`regime_delta_r2` exist in
   `evaluation.py` but are called by no committed script — the ΔR² numbers (the project's best result)
   live only in prose. Fix: a ~30-line `scripts/significance_test.py`.

Top-3 next moves per the audit: (C2) write the significance-test script + permutation null; (C1) fix
the dwell/persistence comparison asymmetry + relabel Table 2; (R1) fingerprint the raw 8 states +
VIX-ablation — the experiment that actually decides the headline thesis. Also: `paper.tex:153` "features
lagged one day" is false (causality is from expanding-standardize + filtering, not a lag).

## Causality Deep-Review (2026-07-20/21) — Fixed and Committed (185ae8d)

Deep code review found 5 critical lookahead/correctness bugs (full detail: `.planning/DEEP-REVIEW.md`, untracked). All 5 are now fixed and verified against a clean pipeline run:

- **CR-01** NFCI weekly series was ffill'd on reference date, not release date — 7-day publication-lag shift added (`src/data/collect_macro.py`).
- **CR-02** `HDP_ALPHA`/`HDP_KAPPA` config constants were dead (kappa is Bayesian-learned, not fixed) — removed the dead constants/import.
- **CR-03** Parametric HMM baseline's `get_filtered_states()` used hmmlearn's smoothed (forward-backward) posterior despite claiming causal filtering — replaced with a manual forward-only pass (`src/baselines/parametric_hmm.py`).
- **CR-04** (headline bug) Table 4 vol-target backtest sized positions using full-training-sample realized vol per regime (lookahead). Fixed via `expanding_regime_vol()` in `src/core/inference.py` — causal, point-in-time per-regime vol.
- **CR-05** VIX-rank regime partition could silently drop "High-Vol" if HDP prunes to <3 active states — added `assert K_eff >= 3` stopgap in `run_paper_experiments.py`.

**Table 4 numbers changed after the CR-04 fix** (as expected — removing lookahead should reduce inflated performance):

| | Before (buggy) | After (fixed) |
|---|---|---|
| Vol-Target (HDP) Sharpe | 0.736 | 0.624 |
| Rebalances/yr | 3 | 13 |
| Max DD | — | -29.6% |

Table 1 dwell times also shifted (65.9 / 61.2 / 41.4 days vs previous 82/74/39) — attributable to the CR-01 NFCI feature fix changing what the HDP model learns, not a bug.

**Still open from the review (not yet done):**
- `data/processed/*.csv` and `models/*.pkl` are committed/regenerable and bloat git; `.gitignore` doesn't cover them.
- `requirements.txt` has dead deps (`arch`, `plotly`, `pandas_datareader`).

**2026-07-21 (later):** Added `tests/test_causality_invariants.py` — perturb-a-future-value / assert-nothing-before-it-changes checks for the 4 functions claiming causality (`expanding_standardize`, `expanding_regime_vol`, `get_filtered_states`, HDP `forward_backward_numpy`'s filtered output). Includes a negative control (smoothed output *does* change before t) proving the perturbation is large enough to matter. Verified the `expanding_regime_vol` test fails against the pre-fix buggy version (fold-before-compute) — the test has teeth, not just vacuously passing. Run with `pytest tests/ -v`.

**2026-07-21 merge:** `origin/main` had diverged with a same-day-earlier commit (`70849ae`, pushed from a different machine before this deep-review session) adding `scripts/run.py` (CLI wrapper for collect/features/train/signals/dashboard/regime/trust/analyze, with cached-artifact fallback) + `tests/test_cli_runner.py` + a README.md rewrite. Non-overlapping with the causality fixes — merged clean (`8dc349c`), both new tests pass. README staleness is now resolved.

## Walk-Forward OOS Validation — Implemented (2026-07-21, commit d4f4872)

`stage_walk_forward` was a no-op stub — the model had never actually been scored on anything after `TRAIN_END` (2023-12-31), meaning `scripts/run.py regime` was silently falling back to a live VIX-threshold guess (the null hypothesis this whole project argues against). Implemented properly: `src/core/walk_forward.py` refits the HDP-HMM quarterly (63 trading days, `config.WALK_FORWARD_REFIT_DAYS`) on an expanding window, forward-filters (never smooths) each new block, then folds it into the training window before the next refit. Run via `scripts/run.py walk_forward` or `--validate`; writes `data/oos_regime_labels.csv`.

**First real OOS run, 2024-01-02 → 2026-07-21 (11 folds):**
- **Today (2026-07-21) is genuinely Low-Vol at 99.99% posterior confidence** — the first real (non-VIX-threshold) live signal this project has ever produced.
- Mean confidence across all 635 OOS days: 96.5%; 26 days (4%) below 0.7 (real uncertainty on transition days, not degenerate always-100%-confident output).
- Distribution: Moderate-Vol 55.3%, Low-Vol 38.4%, High-Vol 6.3% — notably different mix than the in-sample training period (50/40/10).
- **Dwell times OOS (30.5 / 35.1 / 8.0 days) are much shorter than the in-sample claim (65.9 / 61.2 / 41.4 days)** — the "persistence advantage over VIX-threshold" story holds much less dramatically out-of-sample; High-Vol dwell (8.0 days) is right at the VIX-threshold baseline's range. Not yet root-caused: could be genuine 2024-2026 market character, or partial refit-boundary instability (fold-boundary check showed 7/10 boundaries label-stable, so not fully explained by that alone).
- **OOS vol-target(HDP) backtest Sharpe (1.062) slightly trails buy-and-hold (1.098)** over this period — the modest in-sample edge (0.624 vs 0.606) does not clearly replicate OOS. Both OOS Sharpes are much higher than in-sample simply because 2024-2026 was a strong bull run overall — only the HDP-vs-B&H *relative* comparison is meaningful here.

These are reported as-is, not smoothed over — exactly the kind of honest OOS grounding the paper needs. Next: investigate the dwell-time shrinkage (refit-artifact vs real) and whether the backtest edge is period-specific.

## Training-Window Sensitivity — Discovered and Addressed (2026-07-21, commit 8b06545)

Investigating the dwell-time shrinkage above turned up something bigger. Compared three training-window configurations for the same 635 OOS days (2024-01-02 → 2026-07-21): **expanding** (full history since 2015, the original design), **rolling 5-year** (1260 trading days), **rolling 3-year** (756 trading days).

**Pairwise agreement on the regime label:**
| | Expanding | Rolling 5y |
|---|---|---|
| Rolling 5y | 68.8% | — |
| Rolling 3y | 51.2% | 67.2% |

That's a **smooth gradient, not a threshold** — adjacent choices (5y vs 3y) disagree almost as much as the extremes (32.8% vs 31.2%/48.8%), which rules out "it's just about whether COVID is in the window." It's a pervasive sensitivity to training-window length, likely compounded by (a) genuine SVI estimation noise with less data per state, and (b) the coarse "sort states by mean VIX, chop into thirds by index" merge heuristic being brittle to small shifts in state ordering.

**The important part: even on days where BOTH configs independently reported >99% posterior confidence, they disagreed 22% of the time** (88/394 such days). A single model's `filt_prob_max` only measures uncertainty *within* one fixed training-window choice — it says nothing about uncertainty *about* that choice, which this shows is large. Today's own classification wasn't even unanimous: expanding and 5y both said Low-Vol (99.99%/99.8% confidence), but 3y said **Moderate-Vol at 98.8% confidence** — a different regime, stated with comparable certainty.

**Fix shipped:** `data/oos_regime_labels.csv` is now an ensemble of `config.WALK_FORWARD_WINDOW_DAYS = [expanding, 5y, 3y]` (see `ensemble_oos()` in `src/core/walk_forward.py`) — majority vote + `agreement_frac` as the real confidence measure, replacing any single window's overstated posterior. `scripts/run.py regime`/`trust` now report cross-window agreement (e.g. "Low-Vol, 2/3 windows agree, 67% confidence") instead of a single model's 99%+ number. Cost: `stage_walk_forward` now runs 3 window configs (~24 min total, up from ~8).

**Not yet done:** this same sensitivity almost certainly affects the in-sample paper Table 1/2/4 numbers too (only one training-window choice — full history — has ever been used there). Whether/how to report this as an explicit robustness section in the paper is still open. Raw per-config runs kept for reproducibility: `data/oos_regime_labels_rolling5y.csv`, `data/oos_regime_labels_rolling3y.csv`.

## Statistical Significance Test + Hysteresis Fix (2026-07-21, commit e6962df)

Pivoted the evaluation framework: stop asking "does vol-target backtest beat buy-and-hold" (never actually established — OOS Sharpe 1.062 vs B&H 1.098, HDP trails) and instead test whether the regime label carries statistically significant information at all, honestly, on the genuinely-OOS ensemble labels.

Added `block_bootstrap_ci()` + `regime_delta_r2()` to `src/core/evaluation.py` — resamples contiguous 21-day blocks (not individual rows) since daily vol/returns are serially correlated (VIX AC(1) ≈ 0.9); an i.i.d. bootstrap would understate sampling variability and make noise look significant.

**Result:**
- Forward 5-day return: ΔR² = 0.00077, 90% CI [0.0002, 0.0097] — significant but a tiny effect. Not a case for return-timing.
- Forward 21-day realized vol: ΔR² = 0.0124, 90% CI [0.0017, 0.0665] — significant, ~16x larger effect. **The regime label's real, provable signal is about future volatility, not direction** — consistent with the window-sensitivity finding above and with `algo-trading-bot`'s independent conclusion that HMMs ceiling out at classification, not timing.

Caveat: this CI tests whether the observed ΔR² is stable under block-resampling of the actual data, not a strict permutation test against an explicit null (regime randomly reshuffled relative to target). Same family of test as this project's pre-refactor `evaluation.py` used; a stricter permutation-null version is a possible future refinement.

**Separately, found and fixed a real comparability bug** (surfaced during the 2026-07-21 codebase mapping): in-sample regime labels get 3-day hysteresis smoothing via `get_labels_and_probs`' `hold_days=3` default (both `run_paper_experiments.py` and `stage_train_hmm` use it); `walk_forward_oos` computed OOS block labels via raw argmax with **zero** smoothing. So "OOS dwell times are half the in-sample claim" was never a fair comparison — turning off flicker-suppression mechanically shortens measured dwell regardless of any real persistence difference. Fixed: `_apply_hysteresis()` in `src/core/hdp_hmm.py` now accepts/returns chainable state (verified byte-identical to the original single-shot behavior via a split-and-chain equivalence test), so `walk_forward_oos` applies the same `hold_days=3` hysteresis across fold boundaries without resetting at every quarterly refit — in canonical regime-index space (0/1/2), since raw HDP state indices aren't comparable across independently-fit folds.

**Corrected 3-window ensemble regeneration completed** (all 33 folds, commit `8e2d637`): High-Vol dwell nearly doubled (8.0 → 15.0 days) once flicker-suppression was applied consistently — still well below the in-sample claim (41.4 days), but a fairer comparison now. Low-Vol/Moderate-Vol dwell (34.1/26.4 days) similarly closer to but still short of in-sample (65.9/61.2). Distribution and cross-window agreement (80.9% mean, 44.4% unanimous days) essentially unchanged from the pre-fix run — the hysteresis mismatch explains part of the dwell-time gap, not most of it. Today unchanged: Low-Vol, 2/3 windows agree (67%). The remaining in-sample-vs-OOS dwell gap is presumably the real market-character difference (2024-2026 calmer VIX) plus whatever residual the training-window sensitivity itself contributes — not further decomposed.

Also fixed a false comment in generated paper LaTeX (`run_paper_experiments.py`) claiming `merge_similar_states()` was used for K=3 regime merging — that function is dead code, never called; the actual method is the inline VIX-rank sort-and-partition-into-thirds two lines earlier. Regenerated paper outputs to confirm the fix was comment-only (all numbers unchanged).

## Two Regime-Labeling Schemes (2026-07-21) — Open Decision, Not a Bug

Codebase mapping surfaced that two different methods assign the 3 canonical regime names, and nothing checks they agree:
- `label_regimes_hdp()` (`src/core/hdp_hmm.py`) — absolute `VOL_BRACKETS` thresholds. Used by `stage_train_hmm`, the "production" pipeline path. Can correctly report "no High-Vol regime today" for a genuinely calm period — no rank ordering forced.
- `merge_states_to_regimes()` (`src/core/walk_forward.py`) — sorts active states by mean VIX, partitions into thirds. Used by `run_paper_experiments.py` and the walk-forward/ensemble path — i.e. everything the paper's headline numbers and `data/oos_regime_labels.csv` are built on. Always forces exactly 3 buckets (needed for the paper's Table 1/backtest structure).

These can disagree on the same data. Cross-referenced in both docstrings so nobody rediscovers this confused, but deliberately **not unified** under session-close time pressure — each has a real tradeoff, this is a decision for Adam, not an obvious fix.

## Paper Status — UPLOAD-READY

`paper_overleaf.zip` (206K) is ready to upload to Overleaf. Contains:
- `paper.tex` (root wrapper) + `paper/paper.tex` (full source, no TODOs)
- `paper/references.bib` (all entries fixed)
- `paper/figures/` — 4 publication-ready PDFs
- `results/paper_macros.tex` — preamble macros
- `results/paper_tables.tex` — Tables 1–5
- `results/paper_desc_stats.tex` — Table 0 (descriptive stats)

Overleaf: set main file to `paper.tex`, hit Compile.

## What's In The Paper

**Figures (4):**
1. `regime_timeline.pdf` — shaded regime bands + SPY cumulative return + VIX panel
2. `vol_violin.pdf` — realized-vol distributions HDP vs VIX-threshold
3. `transition_heatmap.pdf` — 3×3 posterior-mean transition matrix
4. `backtest_equity.pdf` — cumulative returns: B&H / RV30 / HDP (VIX-Thr removed)

**Tables (5):**
- Table 1: Descriptive statistics (4 features)
- Table 2: Within-regime characteristics (HDP vs VIX-Thr vs Param HMM)
- Table 3: HDP transition matrix
- Table 4: Information content regression (R² beyond VIX)
- Table 5: Volatility-targeting backtest (B&H / RV30 / HDP)

**Key results (superseded — see "Causality Deep-Review" section above for current numbers):**
- HDP: 8 raw states → 3 regimes, dwell times ~65 / 61 / 41 days
- VIX-threshold dwell: 8–17 days (persistence advantage still holds)
- Backtest Sharpe: HDP 0.624 vs B&H 0.606 vs RV30 0.766
- HDP uses 13 rebalances/yr vs RV30's 90 — lower turnover, but Sharpe no longer leads RV30 (was inflated by the CR-04 lookahead bug)

## Current Architecture (Clean)

- 4 features: spy_ret, vol_index, yield_slope, nfci (no PCA, no GARCH, no Student-t)
- HDP-HMM with Gaussian emissions, sticky transitions, K_max=8
- SVI (4000 steps, ~40s on CPU) for paper runs
- NUTS available but not yet run for final paper quality
- Dead code removed (data_download.py, fit_toy_hdp.py, parametric_hmm.py,
  threshold_regimes.py, src/experiments/, src/core/orchestrator.py,
  src/core/evaluation.py, src/pipeline/runner.py)

## Key Files

- `run_paper_experiments.py` — full pipeline: data → HDP → baselines → tables + CSVs
- `scripts/generate_figures.py` — reads regime_labels_train.csv, writes 4 PDFs (~2s)
- `src/config.py` — single source of truth for all params
- `src/core/hdp_hmm.py` — the model
- `src/data/collect_macro.py` — data collection (yfinance + FRED)
- `src/pipeline/stages.py` — collect + features stages
- `.env` — FRED_API_KEY (required, already set)

## Regenerate Everything

```bash
python run_paper_experiments.py        # ~40s — data + model + tables + CSVs
python scripts/generate_figures.py     # ~2s  — figures only (no retraining)
# then rebuild zip:
rm paper_overleaf.zip && zip paper_overleaf.zip paper.tex paper/paper.tex \
  paper/references.bib paper/figures/*.pdf \
  results/paper_macros.tex results/paper_tables.tex results/paper_desc_stats.tex
```

## Next Session — Updated Priority List (2026-07-21)

Superseded the old A/B split below — walk-forward OOS validation (was "B", highest value) is now done, and turned up more than expected. Priority order for next session:

1. **Decide on the two regime-labeling schemes** (see above) — unify, or keep the documented tradeoff permanently.
2. **Test training-window sensitivity on the in-sample paper numbers** — the OOS ensemble proved this matters; the paper's Table 1/2/4 have only ever used one window (full history).
3. Consider whether the remaining in-sample-vs-OOS dwell gap (now smaller post-hysteresis-fix but not closed) is worth further decomposing, or whether it's acceptable to report as-is.
4. Lower priority: update `CLAUDE.md`/`README.md` (still describe deleted modules, call walk-forward "a stub"), check/fix stale CI (`.github/workflows/tests.yml` references deleted files), hygiene batch (dead deps, `.gitignore` gaps, dead code removal — `merge_similar_states`, `HDPModelAdapter`).

Original A/B framing, still relevant for presentation-only work if wanted later:

**A) Better presentation (no model changes):**
- Replace Figure 4 equity curve with 3-panel bar chart (Sharpe / MaxDD / Rebalances)
- Add break-even cost analysis: at <0.25bps/trade HDP matches RV30 net of costs
- This makes the efficiency story visual without touching the model

**B) Strengthen the model/evaluation — DONE (2026-07-21):**
- ~~Walk-forward OOS validation~~ — shipped, then extended into the window-sensitivity ensemble and the significance-testing pivot above
- Bootstrap CIs — done, but on regime information content (ΔR²), not Sharpe specifically; could still add a Sharpe-specific CI
- NUTS full posterior (paper-quality uncertainty quantification) — still not done
- Adding features is lowest priority (uncertain payoff, requires re-running ablations)
