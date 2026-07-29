# V2 Plan — Statistical Jump Model Under V1 Discipline (DRAFT)

> **STALE FRAMING (banner added 2026-07-26).** This doc predates key rulings and its mission
> framing is superseded: the "HDP-HMM ensemble incumbent" and the "Portfolio-Manager consumes
> the label" goal were both RETIRED 2026-07-23 (nothing consumed the label; PM integration was
> notes-only). The live forward roadmap is `PROGRAM.md` (three-layer program; detection + paper,
> not trading). Retained here only for the Phase-4 track descriptions that NOTES still references.
> Cites pre-rename `v2_*` filenames (mapping in `results/README.md`).

Status: Phases 0-1 EXECUTED 2026-07-22 (see "Execution status" at bottom). Phase 2 freeze
BLOCKED on a design decision (see prereg banner). Created: 2026-07-22. Origin: outward-facing
methodology sweep (3-agent survey of academic SOTA, practitioner systems, data/stats standards)
after v1 convergence.

## The v2 question

Do the positive claims of the statistical jump model literature — persistent, low-turnover
regime signals that reduce drawdowns / improve risk-adjusted returns **net of costs**
(Shu, Yu & Mulvey 2024, J. Asset Management; Nystrup/Kolm/Lindström 2020-21) — survive
causally-clean, preregistered evaluation? And does the resulting label beat our incumbent
HDP-HMM 3-window ensemble as the practical instrument Portfolio-Manager consumes?

This is NOT a reopening of v1 ("information beyond vol") — it changes the success criterion
to the field's (economic value, tails, turnover), the estimator to the field's current
standard, and fixes the data/feature defects the sweep identified.

## Why this direction (the four standouts)

1. **Return-only features kill the vintage-lookahead problem class entirely.** Field-standard
   feature set = EWM downside deviation (10d halflife) + Sortino ratios (20d, 60d halflives),
   all derived from the return series itself. No NFCI (current-vintage lookahead), no VIX
   level (mean-drift in expanding z-score). Biggest craft fix for least effort.
2. **K=2 + explicit jump penalty λ directly targets v1's two documented pathologies.**
   K-saturation (Miller-Harrison DP inconsistency — fix K a priori) and training-window label
   instability (jump penalty + robust coordinate-descent fitting are the literature's remedy
   for exactly this).
3. **The economic lens is the exhibit v1 never ran.** Fleming-Kirby-Ostdiek performance fee
   (quadratic utility, bps/yr, net of costs); KPT 2012 loss-avoidance framing. Statistical
   and economic value are known to diverge — regime value concentrates in a few episodes.
4. **Replication-as-construction-gate.** Shu/Mulvey 2024 publish concrete results (US/DE/JP,
   1990–2023, 10bps costs, 1-day delay). First milestone = reproduce their pipeline shape,
   not hunt a fresh null. A reference implementation exists (`jumpmodels`, PyPI).

## Phases

### Phase 0 — Data foundation (the Adam-flagged underinvestment)
- Primary series: daily US equity total return, multi-decade. Candidate: Ken French daily
  market factor (Mkt-RF + RF), 1926+, free, survivorship-clean — cross-checked against SPY
  on the 1993+ overlap. Document adjustment conventions; quality gate before anything else.
- Deliverable: `data/processed/` panel + a construction-gate script with pass bars
  (coverage, overlap agreement, no gaps), same idiom as tailhazard_build.
- Explicitly out: NFCI (unless later variant uses ALFRED real-time, 2011+ only), raw VIX.

### Phase 1 — Instrument build + synthetic validation (blind preserved)
- Core algorithm: jump model fit = minimize Σ_t ||x_t − μ_{s_t}||² + λ·#{state switches},
  alternating (i) per-state means given sequence (k-means step) and (ii) state sequence given
  means (dynamic-programming shortest path). λ=0 → k-means; λ→∞ → one regime.
  Candidate: Adam writes the ~100-line core (Learning-Mode arrangement), harness/tests generated.
  Fallback: `jumpmodels` package with our own causality-invariant tests wrapped around it.
- Online/causal inference variant for OOS use (Nystrup/Kolm/Lindström 2020 greedy online
  classification) — filtered, frozen-parameter, never smoothed.
- Validate on simulated data with known regimes FIRST (field norm): balanced accuracy,
  persistence recovery, λ-sensitivity map. Property tests + causality-invariant tests.
- λ selection protocol: causal time-series CV, criterion pre-specified at Phase 2 (validation
  Sharpe with delay per Shu/Mulvey, vs information-criterion alternative — decide before freeze;
  note the field's own risk: λ-by-validation-Sharpe can overfit the criterion).

### Phase 2 — PREREG FREEZE (gate: no real-data result may exist yet)
To pin before any real run:
- Object: K=2 jump-model regime label on return-derived features, expanding walk-forward,
  ≥12y initial training, scoring era with ≥5 independent vol cycles (1990+ if French data).
- Baselines: (a) buy-and-hold, (b) **vol-targeting** (the v1-informed brutal baseline — EWMA,
  fixed target), (c) 200-day SMA rule, (d) incumbent HDP 3-window ensemble label.
- Primary metric: FKO performance fee Δ vs vol-targeting, net 10bps one-way, 1-day trade
  delay, with block-bootstrap CI. Secondary: max drawdown / tail severity, turnover (shifts/yr),
  label-stability metric (cross-window agreement with variance-sort relabeling), tail-weighted
  Amisano-Giacomini log-score where a forecasting claim is made.
- Falsifiers + stopping rule, incl. what counts as a practical win for the instrument swap
  (e.g., fee ≈ 0 vs vol-target but ≥5× lower turnover and higher label stability may still
  justify replacing the ensemble — decide and freeze the wording).
- Statistical machinery: Clark-West where nested, Giacomini-White for rolling comparisons,
  SPA/MCS if multiple specs are compared. Block bootstrap lives INSIDE these, not as raw CI.

### Phase 3 — Run + verdict
- Full battery, LOTO over crisis episodes, controls (placebo feature, shuffled-block surrogate),
  12-part report idiom from tailhazard. One look, frozen case classification.

### Phase 4 — Instrument decision
- If v2 label wins on the frozen practical criteria: swap Portfolio-Manager's label source,
  preserving the LOW_VOL/MED_VOL/HIGH_VOL mapping and `oos_regime_labels*.csv` contract.
- If not: incumbent stays; result goes to RESEARCH-RECORD.md either way.

## Honest priors / risks
- Man AHL's vol-targeting result implies the economic edge vs baseline (b) may be small —
  the fee-vs-vol-target primary could well be null. The turnover/stability margin is the
  more likely practical win; the prereg must decide up front how much that counts.
- Shu/Mulvey's positive results select λ by validation Sharpe — our rigor may deflate them.
  That deflation, cleanly demonstrated, is itself a publishable-quality finding and fits
  RESEARCH-RECORD.md as the v2 chapter regardless of sign.
- French daily market return is a factor-portfolio return, not an investable ETF — fine for
  research; the instrument swap decision should sanity-check on SPY-era data.

## Effort estimate
Phase 0: 1 session. Phase 1: 1–2 sessions. Phase 2: 1 session. Phase 3: 1 run + 1 session.
Phase 4: <1 session. Total ≈ 5–6 sessions.

## Execution status (2026-07-22, autonomous session)

- **Phase 0 DONE — gate PASS** (`scripts/v2_build.py`, `results/v2_construction_gate.csv`):
  French daily market TR 1926-09..2026-05 (26,190 days, 51 stress episodes, all 10 crisis
  windows covered), SPY cross-check corr 0.995 on 2010+ / 0.979 full overlap (universe
  difference diagnosed, gate recalibrated with reasons in-script). Two real source properties
  found: French publishes ~1-2 months lagged (RESEARCH panel fine; live instrument needs an
  SPY-splice tail — Phase-4 item), and sub-0.98 90s overlap corr is SPY tracking noise +
  2000/2008 total-market-vs-S&P divergence, not bad prints.
- **Phase 1 DONE — with a load-bearing finding** (`scripts/v2_core.py`, `v2_eval.py`,
  `v2_pipeline.py`, `v2_synthetic_validation.py`; 20 tests in `tests/test_v2_{core,eval}.py`).
  Two design iterations forced by the battery: (1) greedy online classification replaced by the
  causal DP-endpoint filter (greedy can only switch on single-day evidence > lambda — froze at
  fit-scale lambda); (2) plain L2 jump model upgraded to the weighted (lightweight sparse-JM)
  variant + downside-dev-quantile init (noisy Sortino dims dilute the informative axis —
  balanced-split local optimum). Battery verdict: B3 (iid null calibration) PASS;
  B1/B2 (capability) FAIL — and the oracle/lag decomposition shows why: perfect detection
  beats VT by +136..+1090 bps, but at 10-21d lag most/all of that is gone, and any causal
  filter lags ~5-20d. **In-silico conclusion: vol targeting subsumes persistent-regime value
  at daily frequency up to detection lag; the JM does beat B&H when regimes exist (replicating
  the literature's actual claim).** This is the v1 arc's "vol absorbs everything" reproduced
  from first principles in simulation.
- **Phase 2 FROZEN 2026-07-22 (Rev 2)** per Adam's direction (1990+ focus, "wire it up properly"):
  primary = fee(JM−B&H) replication claim; deflation exhibit fee(JM−VT) expected ≤0. Pre-freeze:
  second sweep (backtest-methodology survey + adversarial code audit) — verdict "no CRITICAL,
  causal architecture holds"; fixes applied: **delay=2 next-close execution headline** (our delay=1
  was same-close; Shu/Mulvey's "one-day delay" = shift-2), rf footing in C2/C3 controls, 8y
  λ-validation window (was 4y), LOTO/era fees by moment-drop on precomputed returns (no stitched
  seams), full-panel baseline warmup, fit objective resync. Full audit trail in prereg §11.
  Era: train 1970+, score ~1990→2026-05.
- **Phase 3 COMPLETE 2026-07-23 (381 min): CASE B.** Primary fee(JM−B&H) +487.8 [−47.4, +1138.8],
  F1 fires, controls not clean — all three null bands contain the primary; exposure-matched mix
  beats the overlay. Deflation exhibit significant: fee(JM−VT) −255.8 [−477.5, −36.7]. Label
  instrument exceptional: stability 1.000 vs incumbent 0.809, 1.66 switches/yr. Full chapter:
  RESEARCH-RECORD.md (2026-07-23 section).
- **Phase 4 DIRECTION SET (Adam, 2026-07-23): instrument-first.** Accept the speed loss to VT
  (proven ceiling); win on stability + correctness, then dabble with speed deliberately.
  Ordered tracks:
  1. **Instrument hardening / correctness** — benchmark the label vs ex-post bull/bear datings
     (Pagan-Sossounov, Lunde-Timmermann; field norm), characterize the two states, solve the
     live tail (French lags 1-2mo → SPY-splice), decide the 2-state → LOW/MED/HIGH_VOL mapping.
  2. **Speed, quantified** — map the lag-vs-whipsaw frontier across λ; try asymmetric jump
     penalties (fast into bear, slow out); pay for speed only with measured stability.
  3. ~~Downstream wiring (Portfolio-Manager)~~ — dissolved 2026-07-23: nothing ever consumed
     the v1 label (integration was an idea in notes only; verified by grep + Adam). HDP retired.
     Future integrations designed fresh against the jump-model label.
  4. **Candidate Phase-5 research question (Adam, 2026-07-23): state-conditional asset menu.**
     Given the trusted label, model what to HOLD within each state (duration, credit, gold,
     defensive-vs-cyclical sectors) — the lag-tolerant use (episodes 60-200d vs ~8d detection
     lag). Framing: disciplined conditional playbook evaluated on portfolio outcomes, NOT
     "information beyond vol" (settled null in v1). Mandatory: exposure-matched placebo
     controls (the C1 lesson); soft-exposure variant from the filter's evidence gap is the
     companion Track-2 idea (hypothesis: it interpolates toward vol targeting). Data: French
     daily industry portfolios (1926+, same validated source) + v1's synthetic long-history
     bond TR. Prereg before any real-data result, as always.

## Sources (key)
- Bemporad, Breschi, Piga & Boyd, "Fitting Jump Models," Automatica 2018.
- Nystrup, Lindström & Madsen, ESWA 2020 (jump-penalized HMM); Nystrup, Kolm & Lindström,
  ESWA 2021 (sparse JM), JFDS 2020 (online classification).
- Shu, Yu & Mulvey, "Downside risk reduction using regime-switching signals: a statistical
  jump model approach," J. Asset Management 2024 (arXiv:2402.05272).
- Fleming, Kirby & Ostdiek, "The Economic Value of Volatility Timing," JF 2001.
- Kritzman, Page & Turkington, "Regime Shifts," FAJ 2012.
- Bulla, "Hidden Markov models with t components," QF 2011 (heavy-tail control check).
- Pohle et al. 2017 (state-count selection); Miller & Harrison 2013 (DP K inconsistency).
- Amisano & Giacomini JBES 2007; Clark & West 2007; Corsi 2009 (HAR-RV).
- `jumpmodels` (PyPI) — reference implementation.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
