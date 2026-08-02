# Claude Context — Regime-Detection

**Read NOTES.md first** — current state and next action.

## What This Project Is

**ACTIVE DIRECTION (2026-08-02) — PORTFOLIO CONSTITUTION / equity-ownership optimization.** The live frontier
is a decades-holdable systematic equity portfolio, framed as *equity-ownership optimization* (not asset
allocation): maximize long-term geometric wealth from owning the equity risk premium; diversifiers are a war
chest that preserves compounding capacity and funds countercyclical redeployment into cheap equity. The
DEFENSE study (structural risk drivers → failure-mode spanning → international replication → equity-drawdown
decomposition) is COMPLETE; the OFFENSE study (mechanisms that create equity compounding → exposures →
implementations) is underway, literature-map-first. See `.planning/PORTFOLIO-CONSTITUTION.md`,
`.planning/EQUITY-ENGINE-OFFENSE.md`, `.planning/PORTFOLIO-TEST-PREREG.md`, NOTES.md. All no-look; 0 looks spent.

The **live jump-model instrument** (below) continues in parallel as the shipped tool (`regime_card.json` →
portfolio-manager). Prior directions — factor-model pivot (2026-07-29), momentum product (2026-07-30),
internals fragility gauge (2026-08-01, prereg frozen) — are PARKED; see the File Map and NOTES.md.

### Prior context (2026-07-23)

A regime-detection research program built on the **K=2 weighted statistical jump model**
(Bemporad/Boyd 2018; Nystrup et al. 2020-21; Shu/Yu/Mulvey 2024) over Ken French daily market
data (1926+), run under strict prereg/causal discipline. Chapter 1 (frozen prereg, one look,
2026-07-23) returned **Case B**: the literature's "regime switching beats buy-and-hold" claim is
an exposure artifact under risk-averse utility (all null bands contain it); vol targeting beats
the overlay significantly (fee −256 bps, CI excl. 0); **but the label itself is an exceptional
instrument** — 100.0% stability under ±2y training-window shifts vs the v1 ensemble's 80.9%.

**PIVOT (2026-07-29): cross-sectional factor model.** Three closed Layer-3 nulls (Ch1, Ch2,
Path-B) all tested *single-time-series market timing* and all lost to a reactive baseline
(vol-targeting/EWMA) — the textbook result (Asness 2016, factor/market timing is a trap; risk
management is the edge). The mistake was the sport, not the execution. New direction: build an
actual **cross-sectional factor model** (rank names by a characteristic, harvest the long/short
spread) — a genuinely new information source, not a re-ask of a settled market-timing null, which
is the one condition the standing Layer-3-closed rule permits. Next step is a literature-grounded
gap analysis of professional factor construction BEFORE any prereg or look. See RESEARCH-RECORD
2026-07-29 entry. (Prior direction "instrument-first" — the live JM label feeding portfolio-manager
— continues in parallel as the shipped tool.)

The v1 program (HDP-HMM + four successor formulations, five preregistered nulls) is CONVERGED
and sealed at git tag `v1-convergence`; narrative in `RESEARCH-RECORD.md` (newest-first).

## File Map (living code, `scripts/` — 48 modules, refreshed 2026-08-02)

Status tags: **LIVE** shipped/consumed · **ACTIVE** current direction · **PARKED** shelved (may revive) ·
**QA** characterization only. (Closed-null/dead-probe code was removed 2026-07-29 — `calibration_gate`,
`explore_k3`, `build_credit`, `build_dispersion*`, `rotation_precondition`, `hedge_anatomy`, `run_exposure`,
the anatomy trio — all in RESEARCH-RECORD, recoverable in git history.)

**Jump-model instrument — LIVE (the shipped tool):**
- `jumpmodel.py` — JM estimator core (dd10/sortino20/sortino60 features, k=2/k=3 DP assignment, causal filter)
- `walkforward.py` — shared walk-forward pipeline (annual refits, λ by validation Sharpe); synthetic + real
- `backtest.py` — evaluation machinery: strategy construction, VT/SMA/B&H baselines, FKO fee, bootstrap
- `run_config.py` — frozen chapter-1 protocol constants + arm helpers (`arm_returns`, `maxdd`)
- `build_panel.py` / `build_assets.py` — US market TR panel + JM features / multi-asset panel → `market_daily.csv`, `assets_daily.csv`
- `build_intl_panel.py` — Japan/Europe daily panels (1990+) → `{japan,europe}_*_daily.csv`
- `build_trend_proxy.py` — TSMOM trend/managed-futures proxy → `trend_proxy_daily.csv`
- `synthetic_validation.py` — capability battery on synthetic panels (blind preserved)
- `validate_sensor.py` — label vs ex-post bear datings (descriptive)
- `live_label.py` — SPY-splice live tail → `label_live.csv`
- `regime_signal.py` — **LIVE:** emits `results/regime_card.json` (consumed by portfolio-manager emails)
- `build_report.py` — regenerates `results/report.html`

**Human-facing regime read / detector QA (2026-07-30):**
- `benchmark_detector.py` — JM detector skill vs a dumb vol-threshold baseline
- `regime_read.py` — synthesized human read (turbulence×trend quadrant + severity + analogs)
- `regime_panel.py` — regime panel (consensus-count; superseded by PC1 critique) · `build_ohlc_panel.py` — range-vol probe (not pursued)

**Factor-model pivot — PARKED (regime-as-a-factor is an open Step-4):**
- `build_factor_test_panel.py` · `factor_tests.py` — 25 size/BE-ME + FF3 panel; GRS + Fama-MacBeth + spanning
- `build_bab.py` — AQR Betting-Against-Beta factor
- `build_regime_factor_inputs.py` → `regime_factor.py` → `explore_regime_spanning.py` — regime-as-a-factor steps 1-3
- `oracle_exposure.py` · `risk_engine.py` · `strategy_combo.py` · `compare_vs_jm.py` — exposure/allocation diagnostics + JM head-to-head

**Momentum product — PARKED (PRODUCT-PLAN; A4 OOS-validated 2026-07-30):**
- `cross_sectional_momentum.py` — industry cross-sectional momentum (the return-adder)
- `momentum_breadth.py` — 48 vs 10 industries + buffering · `residual_momentum.py` / `value_momentum_blend.py` — crash fixes
- `conviction_momentum.py` — confidence tilt (concentration KILLED) · `dynamic_allocation.py` — reactive-cov allocation (KILLED)
- `allocation_with_diversifiers.py` — gold+trend leg on static allocation · `build_trend_proxy_deadzone.py` — trend confidence-dead-zone variant
- `validate_product.py` — Phase A4 OOS validation · `sleeve_cost_tax_analysis.py` — cost+Canadian-tax gate · `overlap_check.py` — overlap characterization

**Internals fragility gauge — PARKED (2026-08-01, prereg frozen; Europe placebo control FAILING):**
- `internals_gauge.py` — breadth/herf/dispersion/g construction (US/JP/EU) · `internals_h1.py` / `internals_h2.py` — predictive validity / event study
- `internals_controls.py` — S7 placebo (MUST pass first) · `internals_dial.py` — H3 dial (secondary) · `run_internals_prereg.py` — sign-off-gated orchestrator

**Portfolio constitution — ACTIVE (2026-08-02, equity-ownership optimization; DEFENSE study, all NO-look):**
- `drawdown_budget.py` — the −30% drawdown-budget payoff table
- `economic_driver_study.py` — structural sleeve study (drawdown episodes, conditional corr, driver PCA, failure-mode coverage, cost-of-insurance ledger, spanning)
- `intl_replication.py` — international replication break-test (Japan/Europe bond-hedge × inflation)
- `equity_decomposition.py` — Campbell-Shiller equity-drawdown decomposition (cash-flow vs multiple/risk-premium)
- *(OFFENSE study = literature map first, no scripts yet — see `.planning/EQUITY-ENGINE-OFFENSE.md`)*

Tests: `tests/{test_jumpmodel,test_backtest,test_factor_tests,test_regime_factor,test_regime_signal}.py`.
venv: `.venv` (numpy/pandas; `requirements.txt` = slim jump-model set).

## Frozen vs Archived

**The HDP-HMM pipeline is GONE (retired 2026-07-23, Adam's direction).** Its label was never
consumed by anything — the Portfolio-Manager integration was only ever an idea in notes
(verified by grep of that repo, 2026-07-23). The jump-model label (`results/oos_labels.csv`
frozen; `results/label_live.csv` the live tail from `live_label.py`) is the repo's label
artifact. Downstream integration is now underway for real: `scripts/regime_signal.py` emits
`results/regime_card.json` for consumption by portfolio-manager (weekly positioning email —
see NOTES.md).

**Frozen evidence (never overwrite):** `RESEARCH-RECORD.md` sealed sections;
`.planning/archive/V2-JUMPMODEL-PREREG.md` (+ all earlier frozen preregs, archived 2026-07-29
into `.planning/archive/` — closed-chapter record, out of the working view); the chapter-1 one-look
artifacts `results/stage1.csv`, `results/stage1_run.log`, `results/oos_labels.csv`
(renamed by Adam 2026-07-23 from the `v2_*` names the frozen docs cite — see
`results/README.md` for the mapping). Gates (`construction_gate.csv`,
`synthetic_validation.*`) are living checks and may be rerun; future backtests write
`results/backtest_*` and cannot clobber stage1 evidence.

**Archived:** `archive/research-v1/` (inert; reproduce v1 via tag `v1-convergence`). Deleted
v1 result files are recoverable at that tag.

## Discipline (non-negotiable, extended by the v2 audits)

- **Prereg before running; one look; frozen classification.** `run_backtest.py` requires
  `--confirm-frozen`. Chapter 1's look is SPENT — rerunning it is a new experiment and needs a
  new/updated prereg.
- **Causal only:** forward filtering, frozen-per-refit parameters, expanding windows, no
  smoothed probabilities, causality-invariant tests for new estimators.
- **Exposure-matched controls are mandatory for any economic claim** (the C1 lesson: utility
  fees reward average exposure; random persistent placebos + surrogate/iid null bands + a
  matched static mix, or the result is uninterpretable).
- **Execution timing:** next-close (delay=2) is the honest headline; same-close (delay=1) is
  sensitivity only.
- **Honest baselines:** vol targeting is the bar for anything timing-flavored; B&H and SMA200
  as context; costs and delay identical across arms.
- **Information gate (v1 lesson):** a new representation of the same daily index features
  cannot create information; new claims need a new information source or a new *use* (e.g.,
  lag-tolerant conditional allocation), never a re-ask of a settled null.
- **Cooling-off (added 2026-07-23):** any experiment that could produce a SUPPORT/positive
  claim requires an overnight gap between freeze and run, and an EXPLICIT named+dated
  sign-off — never inferred from a conversational go-ahead. (Chapter 2 compressed this;
  harmless for a null, disqualifying for a positive.)
- **Out-of-hypothesis-sample confirmation (added 2026-07-23):** any hypothesis generated by
  descriptive work on the US panel (the atlas, the state anatomy) is contaminated by
  selection — prereg alone does not cure hypothesis-hunting on the answer sheet. Before any
  SUPPORT is claimed for such a hypothesis, it must confirm on data that did not generate
  it (designated set: French/MSCI developed-market daily panels — Japan, Germany, UK).
- **Mechanism gate (added 2026-07-31, Adam's direction — the meta-lesson of the closed nulls):**
  before ANY signal/strategy is preregistered, write down its structural reason to keep working
  *after it is widely known* — either (a) a risk premium someone is structurally paid to bear, or
  (b) a risk-management mechanism exploiting a durable statistical fact (vol/fragility clustering).
  "It's in the recent literature," "it's novel," or "it backtests well" are NOT mechanisms and are
  disqualifying as the *sole* justification. Proven-and-public return alpha is a contradiction —
  if it were proven and known it would be arbitraged away; only risk premia and risk management
  survive being known. The three closed nulls (jump model, dispersion-lag, macro-timing) all fail
  this gate retroactively — each was selected on academic novelty, not mechanism. Refuse
  novelty-chasing at the *proposal* stage, not after another spent look.

## Do Not

- Edit sealed RESEARCH-RECORD sections, frozen preregs, `archive/research-v1/`, or the frozen
  v2_* evidence files.
- Rebuild the chapter-1/2 battery runners to "just rerun something" — those one-looks are spent
  and the scripts are gone (reproducible at commit `51fbeff`); a new backtest needs a new prereg.
- Build production execution logic here (Algo-Trading-Bot's job) — the portfolio-manager
  integration is a read-only `regime_card.json` export, not a trading system.

## Session Close

Update NOTES.md (state + next action) → commit → push.
