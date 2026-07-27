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
Direction: **instrument-first** (see `.planning/V2-JUMPMODEL-PLAN.md` Phase-4 tracks).

The v1 program (HDP-HMM + four successor formulations, five preregistered nulls) is CONVERGED
and sealed at git tag `v1-convergence`; narrative in `RESEARCH-RECORD.md` (newest-first).

## File Map (living code, `scripts/`)

Core pipeline:
- `jumpmodel.py` — estimator core: features (dd10/sortino20/sortino60), DP state assignment
  (k=2/k=3 fast paths), weighted fit, causal DP-endpoint filter (+ value-path/margin export)
- `walkforward.py` — shared walk-forward pipeline (annual refits, λ by 8y-validation Sharpe;
  optional evidence-margin output); used byte-identically by synthetic and real runs
- `backtest.py` — strategy construction (delay/costs), VT/SMA/B&H baselines, FKO fee,
  paired stationary bootstrap
- `build_panel.py` / `build_assets.py` — French daily panel + SPY cross-check + gates
  → `data/processed/market_daily.csv`, `assets_daily.csv`
- `run_backtest.py` / `run_allocation.py` + `allocation.py` — the chapter-1/2 preregistered
  batteries (one-looks SPENT) → frozen `results/` evidence
- `synthetic_validation.py` — capability battery on simulated panels (known truth)
- `live_label.py` — SPY-splice live tail; label to today
- `build_report.py` — regenerates `results/report.html` (living program report)

Gates & probes (living checks; rerunnable):
- `calibration_gate.py` — P(state) Platt gate on 8-cell synthetic DGP grid (FAILED
  2026-07-23 → probability layer KILLED; script kept as the finding's reproduction path)
- `explore_k3.py` — K=3 probe (severity ladder, stability 1.000; K=3 dev PARKED)
- `validate_sensor.py` — label vs ex-post bear datings (lag/precision stats, monitor C7)

Descriptive anatomy (no look; hypothesis-generating, contaminated for prereg purposes):
- `atlas.py`, `state_anatomy.py`, `episode_anatomy.py`

Path-B descriptive probes + data tools (2026-07-26; the cross-asset ALGO candidate is CLOSED
NULL — the portfolio-backtest scripts `rotation_gonogo/sweep/deflate.py` were REMOVED from the
tree, reproducible in git at commit `d022c09`; the null is documented in RESEARCH-RECORD). These
kept for NON-algo use — regime/asset characterization and reusable data:
- `rotation_precondition.py` — do per-asset JM regimes diverge cross-sectionally? (mixed ~76% of
  days) → `results/rotation_precondition*.csv`
- `hedge_anatomy.py` — behavioral fingerprint of 20 assets vs equity-stress (descriptive market
  characterization) → `results/hedge_fingerprint.csv` (panel `data/processed/hedge_etf_daily.csv`)
- `build_trend_proxy.py` — TSMOM (Moskowitz–Ooi–Pedersen) trend proxy tool, GATED vs DBMF/KMLM
  (corr 0.69) → `data/processed/trend_proxy_daily.csv`, `results/trend_proxy_gate.csv`

Tests: `tests/test_jumpmodel.py`, `tests/test_backtest.py`. venv: `.venv` (numpy/pandas stack;
requirements.txt is the slim jump-model set — the v1 JAX/NumPyro stack was retired 2026-07-23).

## Frozen vs Archived

**The HDP-HMM pipeline is GONE (retired 2026-07-23, Adam's direction).** Its label was never
consumed by anything — the Portfolio-Manager integration was only ever an idea in notes
(verified by grep of that repo, 2026-07-23). The jump-model label
(`results/oos_labels.csv` frozen; `results/backtest_labels.csv` from future runs) is the
repo's label artifact; any downstream integration is a future project designed fresh.

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
- Rerun `run_backtest.py` casually — the one-look is spent.
- Build production execution logic here (Algo-Trading-Bot's job).

## Session Close

Update NOTES.md (state + next action) → commit → push.
