# Claude Context — Regime-Detection

**Read NOTES.md first** — current state and next action.

## What This Project Is (2026-07-23)

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

## File Map (living code, `scripts/`)

**Tree cleaned 2026-07-29 (Adam's direction): all closed-null / dead-probe code removed** —
`calibration_gate`, `explore_k3`, `build_credit`+`explore_credit_feature`,
`build_dispersion`+`explore_dispersion_feature`+`explore_dispersion_intl`,
`rotation_precondition`, `hedge_anatomy`, `run_exposure`, and the descriptive anatomy trio
(`atlas`/`state_anatomy`/`episode_anatomy`). Each closure is recorded in RESEARCH-RECORD
(2026-07-29 entry); all recoverable in git history. Repo is now: **the living instrument + the
factor-model pivot** (see What This Project Is).

Core pipeline:
- `jumpmodel.py` — estimator core: features (dd10/sortino20/sortino60), DP state assignment
  (k=2/k=3 fast paths), weighted fit, causal DP-endpoint filter (+ value-path/margin export)
- `walkforward.py` — shared walk-forward pipeline (annual refits, λ by 8y-validation Sharpe;
  optional evidence-margin output); used byte-identically by synthetic and real runs
- `backtest.py` — strategy construction (delay/costs), VT/SMA/B&H baselines, FKO fee,
  paired stationary bootstrap
- `build_panel.py` / `build_assets.py` — French US daily market panel + SPY cross-check +
  multi-asset panel (industries, SMB/HML/MOM) → `data/processed/market_daily.csv`, `assets_daily.csv`
- `build_intl_panel.py` — French International daily panels (Japan, Europe: market factor + 25
  size/BE-ME portfolios, 1990+) → `data/processed/{japan,europe}_{market,assets}_daily.csv`.
  Built 2026-07-29 for the dispersion int'l confirmation; **kept as factor-portfolio data for the pivot.**
- `build_trend_proxy.py` — TSMOM (Moskowitz–Ooi–Pedersen) trend proxy, GATED vs DBMF/KMLM
  (corr 0.69) → `data/processed/trend_proxy_daily.csv`. **Kept — momentum is a factor.**
- `run_config.py` — shared frozen-protocol constants (START/DELAY/LAMBDA_GRID/REFIT/…) + arm-return
  helpers (`arm_returns`, `maxdd`), imported by build_report/live_label. The chapter-1/2 battery
  runners (`run_backtest.py`, `run_allocation.py`, `allocation.py`) were removed 2026-07-27
  (one-looks SPENT, reproducible at `51fbeff`).
- `synthetic_validation.py` — capability battery on simulated panels (known truth)
- `validate_sensor.py` — label vs ex-post bear datings (lag/precision stats, monitor C7)
- `live_label.py` — SPY-splice live tail; label to today
- `regime_signal.py` — emits `results/regime_card.json` (LIVE, consumed by portfolio-manager)
- `build_report.py` — regenerates `results/report.html` (living program report)

Tests: `tests/test_jumpmodel.py`, `tests/test_backtest.py` (18 passing).
venv: `.venv` (numpy/pandas stack;
requirements.txt is the slim jump-model set — the v1 JAX/NumPyro stack was retired 2026-07-23).

## Frozen vs Archived

**The HDP-HMM pipeline is GONE (retired 2026-07-23, Adam's direction).** Its label was never
consumed by anything — the Portfolio-Manager integration was only ever an idea in notes
(verified by grep of that repo, 2026-07-23). The jump-model label (`results/oos_labels.csv`
frozen; `results/label_live.csv` the live tail from `live_label.py`) is the repo's label
artifact. Downstream integration is now underway for real: `scripts/regime_signal.py` emits
`results/regime_card.json` for consumption by portfolio-manager (weekly positioning email —
see NOTES.md).

**Frozen evidence (never overwrite):** `RESEARCH-RECORD.md` sealed sections;
`.planning/V2-JUMPMODEL-PREREG.md` (+ all earlier frozen preregs); the chapter-1 one-look
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

## Do Not

- Edit sealed RESEARCH-RECORD sections, frozen preregs, `archive/research-v1/`, or the frozen
  v2_* evidence files.
- Rebuild the chapter-1/2 battery runners to "just rerun something" — those one-looks are spent
  and the scripts are gone (reproducible at commit `51fbeff`); a new backtest needs a new prereg.
- Build production execution logic here (Algo-Trading-Bot's job) — the portfolio-manager
  integration is a read-only `regime_card.json` export, not a trading system.

## Session Close

Update NOTES.md (state + next action) → commit → push.
