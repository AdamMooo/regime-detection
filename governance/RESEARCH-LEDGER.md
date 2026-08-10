# RESEARCH LEDGER

Every hypothesis tested across the three internal repositories, and what happened to it.

**Purpose:** prevent rediscovering the same idea six months later because nobody remembers why
it failed. **Read this before proposing a new signal, model, or strategy.** Eight of the
entries below are documented nulls — that is the point of the file.

Created 2026-08-09, seeded from `CROSS-REPO-AUDIT-2026-08-09.md`. No findings invented; every
row is transcribed from evidence already recorded in the repos.

**ID space:** `MI-*` regime-detection · `ALGO-*` algo-trading-bot · `PM-*` portfolio-manager.
**Status:** `IDEA · TESTING · PROMISING · VALIDATING · VALIDATED · REJECTED · DEPRECATED · REDUNDANT`

> **Location is not ownership.** This file lives in `regime-detection/governance/` for one
> reason only: the workspace root is not a git repository, so a root-level ledger had no
> version history and no way to survive a machine migration (decided 2026-08-09, superseding
> `IMPLEMENTATION-PLAN.md` §9's "accept vault-only history"). **regime-detection does not own
> the `ALGO-*` or `PM-*` entries.** Each repository owns its own rows; this is a shared index
> that happens to be stored in the one repo guaranteed to be present. Do not infer any
> architectural relationship from the path, and do not let regime-detection code read this file.

> **Note on deleted code.** Several `ALGO-*` entries reference code deleted from the working
> tree on 2026-08-09 (the market-understanding strip-down). The code is recoverable from git
> history at commit `b1f3fa3e~1`. **The findings below are the durable artifact — not the
> implementations.** That is why they are written out in full here.

---

## Market Intelligence — `regime-detection`

| ID | Hypothesis | Test | Result | Status | Reason | Date |
|---|---|---|---|---|---|---|
| MI-001 | A K=2 jump-model state label reads volatility better than a plain causal threshold | Exposure-matched head-to-head at both bear datings (`results/detector_benchmark.csv`) | Threshold + hysteresis matched or beat it on precision, recall and BAC, with shorter detection lag | **REJECTED** | Thresholding destroys the graded information in σ. `results/regime_card.json` parked as a consequence | 2026-08-04 |
| MI-002 | Volatility descriptors (level · rarity · drift · GARCH half-life) are a usable production signal | Frozen one-look, `scripts/validate_vol.py` → `results/vol_validation.txt` | Signed off; maturity `production` | **VALIDATED** | Mechanism pass; measurement validity / investment usefulness / evidence maturity all H | 2026-08-06 |
| MI-003 | Stock-bond correlation state describes whether bonds hedge equity drawdowns | Frozen one-look, `scripts/validate_stockbond.py` → `results/stockbond_validation.txt`: hedge-behaviour-by-state on the registered monthly clock, US **and** the Japan/Europe out-of-hypothesis sample | **The OOS run was made.** V4 power pre-check cleared all three regions (≥24 months in every state). Fraction of equity-down months on which bonds ALSO fell, intact→under_test→violated: **US 28→44→56% · Japan 25→29→51% · Europe 27→32→48% — monotone in all three.** R1–R5 none tripped | **VALIDATED** | Phase 2 closed; results signed off 2026-08-07 at maturity **`research`**, not `production`: evidence maturity is `M` because both international panels start 1990-07, so the OOS sample contains **no 1970s–80s inflation regime** and the sign-flip cycle itself is untested abroad. Two honest caveats recorded: in Japan/Europe nearly all discrimination sits at `violated` rather than grading a smooth ladder, and V5 window-robustness is stable at 24m+ but noisy at 12m. Average-return-by-state was **confounded by the rate cycle** — hedge behaviour is the honest metric | 2026-08-07 |
| MI-004 | The jump-model regime is a priced cross-sectional factor | REG on FF 25 size/BE-ME, spanning-regressed on FF3 and FF3+BAB, Newey-West(6); two factor-mimicking constructions | Constructions **disagree**: beta-sort α t=−1.30 (not significant), mimicking-portfolio α t=−2.09 (significant at \|t\|>2), **both with the negative/hedge sign** | **TESTING** (ambiguous — see Open questions below) | The one live question here with real upside. Escalated to a Step-4 preregistered confirmatory test **that has never been run, and nothing on the roadmap runs it.** An earlier "spanned, closed cheaply" verdict was **retracted** as an over-claim. Full record: `RESEARCH-RECORD.md` §2026-07-30 | 2026-07-30 |
| MI-005 | State-conditional covariance adds allocation value | Fee-equivalent comparison vs a reactive EWMA covariance | fee_A +2.8 inside all bands; reactive EWMA beats it outright (fee_B −29.1) | **REJECTED** | The risk-stabilization mechanism exists (F2 clear), but reactive estimation harvests it better | 2026-07-23 |
| MI-006 | Cross-asset defensive rotation timing adds value beyond exposure | Matched vol-target comparison | Null — timing adds no return or Sharpe beyond exposure; a matched vol-target matches or beats its drawdown protection | **REJECTED** | Exposure artifact. Chapter 1 reconfirmed for the third time | 2026-07-26 |
| MI-007 | The absorption ratio is an admissible diversification signal | Signal declaration + data-feasibility scout; no look spent | Dropped at the charter stage | **REJECTED** | `.planning/archive/dropped-signals/05-ABSORPTION-DROPPED.md` | 2026-08-09 |
| MI-008 | Funding stress is an admissible signal | Signal declaration + data-feasibility scout; no look spent | Dropped at the charter stage | **REJECTED** | `.planning/archive/dropped-signals/07-FUNDING-DROPPED.md`. `scripts/build_funding.py` and both funding panels **deleted 2026-08-10** (recoverable in git history) | 2026-08-09 |
| MI-009 | Valuation carries information about future long-horizon EXCESS equity returns, consistent with the Campbell–Shiller discount-rate mechanism | Frozen one-look, `scripts/validate_valuation.py` → `results/valuation_validation.txt` (V1–V6, charter v1.1 signed 2026-08-07). Bars registered before the look; **the look IS spent** | **Five of six bars clear; V6, the statistical bar, does NOT.** Shape and sign hold (log-CAPE slope −0.0033 at 1m → −0.610 at 10y, R² 0.001 → 0.257, silent sub-1yr), survive on *excess* returns, are **stronger pre-1982** than in 1982–2021, and reproduce on P/D and cap/GDP (which uses no earnings, so R6/Siegel does not trip). But the block bootstrap under the no-predictability null gives **p = 0.07–0.26 at every horizon, both return objects**; ρ = 0.9965 and corr(return innovation, regressor innovation) = **+0.96**; Stambaugh removes 64–72% of the raw one-month slope | **VALIDATING** | **R9 is live and the disposition is Adam's, not yet made** — the decision needs zero further build work. With ~13 effective independent 10-year observations in 145 years the data cannot separate the mechanism from a persistent-regressor artifact. Two defensible readings are written into the charter (demote to a pure measurement with no forward-return claim, vs weak-but-consistent across 20+ specifications that share one price series). **Do NOT rerun the bootstrap with another seed or block length.** R5 (payout confound) is a registered **UNTESTABLE** reject condition — no free net-buyback history. No `observations/valuation/` log exists while R9 is open, deliberately | 2026-08-07 |
| MI-010 | The Gilchrist–Zakrajšek excess bond premium is an admissible credit signal — and its history is stable enough across vintages to support a rarity reading | **Not run.** Charter v1.0 FROZEN and SIGNED 2026-08-09 (`.planning/phases/06-credit-signal/06-CREDIT-CHARTER.md`, commit `29e7c3d`); build authorised; `scripts/validate_credit.py` scaffolded (self-tests pass, refuses to run without `--i-am-spending-the-one-look`); V2's evidence base harvested — **20 distinct vintages 2022-08-18..2026-03-23** in `data/vintages/ebp/` (the 20th recovered 2026-08-10 after the first run was rate-limited by the Archive). **The one look is UNSPENT: no cross-vintage statistic has been computed** | **No result exists** | **IDEA** (charter signed, look unspent) | Registered pre-look, and **not reopenable**: maturity capped at **`research`** · **R2 firing ⇒ DROP, not demotion** (A: RMS revision ÷ σ ≤ 0.25 · B: Spearman ≥ 0.95 · **C: settled-month decile agreement ≥ 0.90, decisive**; two of three failing kills the signal). The EBP is a **regression residual refit monthly on the full sample**, so today's March-2008 value embeds coefficients fitted through 2026, and there are no ALFRED vintages — which is why V2 is the decisive bar. **G4 (uniqueness) is UNOPPOSED, not confirmed**: the registered leave-one-out was against MI-008, which was dropped, so that adjudication can never run; and the EBP regresses out a Merton distance-to-default that is itself a function of equity vol, so part of any measured orthogonality against MI-002 is **manufactured by construction** | 2026-08-09 |

| MI-011 | Effective-N of the index's capital distribution (`eff_n = 1/Σsᵢ²` over the 25 ME×BE/ME buckets) is an admissible concentration signal | **Not run.** Charter is **v0.2 DRAFT, UNSIGNED** (`.planning/phases/04-concentration-signal/04-CONCENTRATION-CHARTER-DRAFT.md`); V1–V6 registered in the draft and **none has been run**; no look spent, no results sign-off, no derived maturity. Construction only: `scripts/build_concentration.py` + `scripts/concentration.py`, `results/concentration_gate.csv` C1–C5 all `True` (1200 months 1926-07..2026-06, blocks agree 25/25, `eff_n` ∈ [2.064, 10.627], Σs−1 = 4.4e-16, zero gaps), panel in `MANIFEST.csv`, `build()` under `assert_causal` | **No result exists.** Live descriptive read only, rendered as a CANDIDATE axis in `results/informativeness_map.json`: `eff_n` 2.5372, `top_share` 0.6100, **1.8th percentile** of its own causal expanding history as of 2026-06-30 | **IDEA** (built + construction-gated, charter unsigned, no bar run) | Registered in the draft, pre-look: maturity ceiling **`research`** (resolution · coverage · restatement) · **ledger status NONE** — "`eff_n` has no mechanical boundary (unlike sign zero in stock-bond correlation); banding it re-introduces the knob the volatility reframe removed" · **V3 (resolution) is MAKE-OR-BREAK and its own charter expects it to fire**: "R3 ⇒ close NOT MEASURABLE — expected: the Mag-7 question is seven names *inside* one bucket." Out of reach at bucket level: name-level shares, concentration *inside* the top bucket, Japan's 1987–89 peak (data starts 1990-07), true vintages. **No `observations/concentration/` log exists**, so the rendered reading is a recomputation from the committed panel, not a point-in-time record — admissible for a candidate, not for an admitted axis. Five open items await Adam's ruling before sign-off | 2026-08-10 |
| MI-012 | Risk-neutral index skew measures the price of downside protection, and that price is an admissible tail signal distinct from volatility | **Not run.** Charter is **v0.2 DRAFT, UNSIGNED** (`.planning/phases/09-tail-signal/09-TAIL-CHARTER-DRAFT.md`); V1–V8 registered, **none run**; no look spent. Construction only: `scripts/build_tail.py` → `tail_daily.csv`, `scripts/tail_skew.py` → `results/tail_skew.csv` + `results/tail_vintage.json` (sha-stamped source vintage) | **No result exists** | **IDEA** (built, charter unsigned, **the reframe itself is UNACCEPTED**) | **The reframe is the open decision, not a detail:** the monitored assumption moves from "the return distribution is its normal shape" (physical, unmeasurable from this data) to **"downside protection is priced normally"** (risk-neutral). DROP is registered as defensible. **Its own registered prior is that R4 likely fires:** "given Kozhan et al., R4 firing is likely, not a surprise" — skew and VIX are two nonlinear functions of one state vector. Also registered pre-look: **ledger status NONE** (index skew has been persistently negative since 1987, so any threshold is an arbitrary percentile knob) · maturity capped at **`research` permanently** — international replication is **impossible, not unattempted** (no risk-neutral skew index exists for JP/EU at any tier), so `run_oos.py` cannot serve this signal at all · the published SKEW history **has already been silently revised** (Cboe 2011 docs: all-time low/high 101.09/146.88; today's file 101.31/146.22 on the same dates) and a further recalculation is announced without an effective date · the absorption confound registered for V7 can now only be *disclosed*, never tested, because MI-007 was dropped. Nine `[recommended]` items await Adam's ruling | 2026-08-10 |
| MI-013 | Crowded positioning is an admissible signal (consensus + leverage → fire-sale externality, Stein 2009) | **Never tested. No charter was written and no Stage-0 record exists** — the only record is three lines in `.planning/archive/dropped-signals/README.md:59-62`, unlike MI-007/MI-008 which each have a full dropped-signal memo | **No result exists** | **REJECTED** (dropped 2026-08-05) | Drop rationale, **verbatim and complete**: *"Dropped earlier, before this batch: proxy-only construction, real positioning data infeasible solo, and it risks re-reading the volatility axis."* **Two problems with that record, recorded here rather than resolved.** (1) "real positioning data infeasible solo" objects to a form the architecture had **already scoped out**: `REGIME-SENSOR-ARCHITECTURE.md:368` states the sensor is "Buildable ONLY as return-based comomentum (Lou-Polk) = *factor*-crowding, narrow; general form needs proprietary/stale data" — so the general form was never the candidate, and its infeasibility is not an argument against the scoped one. (2) "risks re-reading the volatility axis" was **never tested** — no orthogonality diagnostic, no leave-one-out, nothing; it is a prior, and the same file's standing lesson is that "a prior is not the test". The architecture also names concentration and crowding as *the clean proof of the mechanistic gate* — they overlap yet fail through different mechanisms (Aug-2007 quant quake was crowded, not concentrated, zero index-vol at onset), which is an argument for distinctness that the drop record does not engage. **This row does not reopen the drop.** It makes the drop visible and its reasoning auditable; reopening it means a Stage-0 gate and a charter under this repo's own process | 2026-08-05 |

### Open questions

Six `MI-*` rows are not finished. Two are waiting on a decision, one on a test nobody has
scheduled, and three (MI-011/MI-012/MI-013) are signals that were invisible in this file until
2026-08-10 — the exact rediscovery hazard it exists to prevent.

**MI-004 — is the regime innovation a priced hedge? The only open row with genuine upside, and it is
invisible on every plan.** Read as a table row it looks stalled; read on the evidence it is a live
result that was never confirmed or killed.

- **What was actually found.** Two factor-mimicking constructions of the regime innovation Δs, both
  with strictly-prior (causal) betas, spanning-regressed on FF3 and FF3+BAB with Newey–West(6):
  beta-sort α t = **−1.30**, Lamont/BGL mimicking-portfolio α t = **−2.09**. Under the correct
  \|t\|>2 spanning bar the mimicking construction **clears**, and both premia carry the
  **negative** sign — the Ang–Hodrick–Xing–Zhang FVIX signature of a priced hedge you overpay for,
  which is what a downside-vol regime factor structurally is. A marginally significant *negative* α
  on a hedge candidate is arguably supporting evidence, not a kill.
- **Why it is ambiguous rather than positive.** The two constructions disagree, and a candidate
  resting on one of two is a reason for caution on its own. The earlier "SPANNED by FF3+BAB, closed
  cheaply" verdict was **retracted the same day** as an over-claim built on four errors: Harvey–Liu–Zhu
  t>3 applied to a *spanning* alpha (a \|t\|>2 question), "zero α" conflated with "negative α", ΔSh²
  eyeballed with no BKRS standard error, and BAB treated as the controlling axis when a downside-vol
  factor sits nearer the volatility/IVOL axis. The build was sound; the verdict was not.
- **What would settle it, and why it has not run.** A preregistered confirmatory test was specified:
  fixed control set FF3+BAB+IVOL/BAC, fixed \|t\|>2 bar, BKRS/GRS inference, a **required** negative
  sign, international confirmation → overnight cooling-off → dated sign-off → **one look**. **No look
  has been spent.** Adding the IVOL control and re-reading the α without that preregistration is
  spec-searching on the answer sheet, which is why it cannot be done casually — and it is the reason
  the row has sat untouched since 2026-07-30.
- **Nothing on the roadmap resolves this.** Every open phase is a *market-understanding signal*
  (concentration, credit, tail, then the Phase-10 presentation layer). MI-004 is a **cross-sectional
  asset-pricing** question about whether a state innovation is priced — a different object, with no
  phase, no charter and no owner. It will stay open until someone opens one.
- **Do not close it by pointing at a neighbouring row.** MI-001 retired the K=2 label as a *reading of
  volatility*; it says nothing about whether the label's innovation is priced in the cross-section.
  The standing lesson that a regime fitted on an asset's own returns rediscovers volatility
  (ALGO-003) is a real prior against MI-004 — but a prior is not the test.
- **Where the evidence lives.** `RESEARCH-RECORD.md` §2026-07-30 (numbers, the correction block, and
  the Step-4 specification). The machinery — `build_regime_factor_inputs.py`, `build_bab.py`,
  `regime_factor.py`, `explore_regime_spanning.py` and `results/regime_spanning.csv` — was deleted
  from the working tree by `3d51161` (2026-08-02, the allocation-program removal) and is recoverable
  at `3d51161~1`. As with the `ALGO-*` rows, the finding is the durable artifact, not the code.

**MI-009 — valuation's R9 disposition.** The look is spent and the result is on file; what is missing
is Adam's dated ruling between the two readings written into the charter. **Zero build work.** Do not
rerun the bootstrap.

**MI-010 — credit's one look.** Charter signed, build authorised, evidence base harvested, scaffolding
in place; the four statistics in `scripts/validate_credit.py` are unwritten and the look is unspent.

**MI-011 / MI-012 / MI-013 — three signals that had no row here at all until 2026-08-10.** Two are
live and half-built, one is dropped, and none of them was visible in the file whose stated purpose is
preventing rediscovery. Nothing about their state changed when the rows were added; only the record
did.

- **MI-011 concentration** — the closest of the three to a decision: built, construction-gated,
  charter unsigned, five open items, no bar run. Its own V3 is pre-called against it. Under the
  informativeness reframe (`scripts/informativeness_map.py`) V3 is arguably the *right question*
  rather than a gate — the axis can be informative about bucket-level capital concentration while
  being blind to concentration inside the top bucket — but that is a ruling for the owner, and until
  it is made the axis renders as a **candidate**, never as an admitted signal.
- **MI-012 tail** — the open decision is the reframe itself (physical distribution shape → the price
  of protection), not a numeric bar, and DROP is registered as defensible. Its own prior is that R4
  fires.
- **MI-013 crowding** — dropped without a charter or a Stage-0 record, on two reasons that do not
  hold up as written (one objects to a form the architecture had already scoped out; the other was
  never tested). **Recorded, not reopened.**

---

## Algo Trading — `algo-trading-bot`

| ID | Hypothesis | Test | Result | Status | Reason | Date |
|---|---|---|---|---|---|---|
| ALGO-001 | A regime-aware cross-sectional ML ranker produces tradable alpha | Backtest, then de-leaked | IC 0.082 → 0.018; Sharpe 1.93 → **−0.02** | **REJECTED** | Lookahead leak. The entire apparent edge was the leak | — |
| ALGO-002 | The jump penalty λ yields a sticky, economically meaningful macro regime | Persistence sweep (spike 002) | Validated, but narrowly | **VALIDATED** (narrow) | It is a **credit-crisis detector**: nailed the GFC, caught COVID late, missed 2022. ~2 episodes in 21 years — the GFC dominates the sample | 2026-06-12 |
| ALGO-003 | The macro regime carries information volatility cannot see | Orthogonality / lead-lag at every λ (spike 003) | Regime **lags** vol at every λ; 100% overlap | **REJECTED** | Discretizing kills the lead. **Fitting a regime on an asset's own returns just rediscovers vol** | 2026-06-12 |
| ALGO-004 | A damped macro overlay beats vol-target-alone after costs | Decision gate (spike 004) | Never run | **REJECTED** (not run) | Pre-determined by ALGO-003: the overlay acts only on already-de-risked days, so it cannot improve risk-adjusted return. Verdict accepted rather than spending the test | 2026-06-12 |
| ALGO-005 | MacroHMM states track forward risk | Out-of-sample replacement test | Window-dependent (transmat diagonal ~0.999 → locks into its start state); "Contraction" fwd-63d +3.0% ≈ "Expansion" +3.2%; a market-priced risk-appetite replacement went +1.55% in-sample → **+0.37% OOS** | **REJECTED** | States do not order forward returns. Model + 4 artifacts deleted | 2026-06-16 |
| ALGO-006 | The 2-HMM gauge detects volatility | Hermetic forward-RV eval (`backtest/regime_vol_eval.py`) | Forward RV monotonic LOW < MED < HIGH; HIGH/LOW ratio 2.2× / 1.9× / 1.6× at 5/21/63d; AUC 0.77–0.81 | **VALIDATED** as a *nowcaster* | An excellent volatility **nowcaster**, explicitly **not a forecaster**. Never demonstrated to be monetizable — it was never put through a monetization test | 2026-06-16 |
| ALGO-007 | A paper-faithful 3-state directional detector (Gupta et al. 2025) beats oracle-label baselines | Two-fold walk-forward with locked Fold-1 gates and one-shot Fold-2 confirmation | **Never completed.** Milestone v9 marked complete at 4/5 phases; Phase 59 never started; working tree diverged 2026-07-09 | **DEPRECATED** | No verdict was ever reached. Deleted from the Algo repo 2026-08-09 as market *understanding*, which the monetization layer does not own. **If the question is still open it belongs in `regime-detection` under a fresh charter — but note MI-001 already retired the labelled-state framing on published evidence** | 2026-08-09 |
| ALGO-008 | 12-1 / 6-1 risk-adjusted momentum ranks an 8-ETF universe well enough to monetize | — | **Never tested** | **IDEA** | `strategy/ev_ranker.py` ran in the live path for months without ever clearing an admission gate — no OOS test, no cost analysis, no ledger entry. Unwired from live 2026-08-09; retained as a candidate | 2026-08-09 |
| ALGO-009 | *(defect, not a hypothesis)* The frozen 2-HMM gauge was fed valid features | Discovered during the Step-0b documentation audit | Artifacts frozen **2026-06-16** against the 16-ETF universe; `493cba43` (**2026-07-21**) cut `ETF_UNIVERSE` to 8; `regime/data.py:191-192` computed `pct_above_{50,200}ma` from `ETF_UNIVERSE`, and `pct_above_200ma` was BreadthHMM's **primary relabeling anchor** | **REJECTED** (invalidated) | The scaler and label map stayed frozen to a 16-name distribution while the input became an 8-name one. **Every regime label from 2026-07-21 onward is suspect, including those the live bot traded on through 2026-07-27.** Same failure class as the 2026-06-16 live feature-degradation bug, in a new form. Not fixed — the gauge was deleted instead | 2026-08-09 |

### Standing lessons for anyone proposing a regime/state idea here

1. **A regime fitted on an asset's own returns rediscovers volatility** (ALGO-003). If the
   proposal cannot state what it sees that vol cannot, it is redundant before it is written.
2. **Discretizing a continuous state destroys information** (MI-001, ALGO-003). A threshold has
   to earn its place against the continuous reading plus hysteresis, and so far it never has.
3. **State detection quality is not monetization** (ALGO-006). The gauge is a genuinely good
   volatility nowcaster and was still never shown to make money.
4. **Frozen artifacts silently rot when their inputs move** (ALGO-009). Any frozen model needs
   a test pinning the distribution of its inputs, not just its own checksums.
5. **Market-state modelling does not belong in the Algo repo at all.** That is the architectural
   conclusion these five entries add up to.

---

## Portfolio Management — `portfolio-manager`

| ID | Hypothesis | Test | Result | Status | Reason | Date |
|---|---|---|---|---|---|---|
| PM-001 | An MVO optimizer / recommender / rebalancer belongs in the governance engine | — | Retired | **DEPRECATED** | The security-selection paradigm was abandoned. `ARCHITECTURE.md` "Do NOT rebuild" — Quarter-Kelly sizing, the ~70-name TSX universe, the factor library, the in-repo regime detector | 2026-08-02 |

---

## External-origin findings

Recorded as context only. A finding from outside the internal stack carries **no internal ID**
and is not a signal here until re-tested under `regime-detection`'s charter (mechanism gate,
preregistration, cooling-off, dated sign-off).

| Origin | Finding | Result | Note |
|---|---|---|---|
| `vol-diagnostics` | Timing covered-call writing off the VRP level produces a forward-return edge | **REJECTED**, p = 0.74 | The prescriptive language was removed from that product as a result (`engine/report/card_model.py:474-481`). Not an internal signal | 2026-07-27 |

---

## How to add an entry

Append a row. Keep it to one line per hypothesis; put detail in the repo that owns it.

A hypothesis reaching **VALIDATED** in the `ALGO-*` table is the **only** path into the live
trading path — and it enters as a named strategy component, never as a raw Market Intelligence
field. See `IMPLEMENTATION-PLAN.md` §3.6 (admission gate) and §7 (consumer rules).

`REJECTED` and `DEPRECATED` rows are never deleted. They are the most valuable rows here.
