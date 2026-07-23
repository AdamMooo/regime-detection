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

- `jumpmodel.py` — estimator core: features (dd10/sortino20/sortino60), DP state assignment
  (k=2 fast path), weighted fit, causal DP-endpoint filter
- `walkforward.py` — shared walk-forward pipeline (annual refits, λ by 8y-validation Sharpe);
  used byte-identically by synthetic and real runs
- `backtest.py` — strategy construction (delay/costs), VT/SMA/B&H baselines, FKO fee,
  paired stationary bootstrap
- `build_panel.py` — French daily panel + SPY cross-check + construction gate
  → `data/processed/market_daily.csv`
- `run_backtest.py` — full preregistered battery (controls → primary → falsifiers →
  secondaries) → `results/backtest_*.csv`
- `synthetic_validation.py` — capability battery on simulated panels (known truth)
- `build_report.py` — regenerates `results/report.html` (visual results dashboard)
- `run.py` — the v1 live-label CLI (still the production path; see below)

Tests: `tests/test_jumpmodel.py`, `tests/test_backtest.py` (CI), plus
`test_causality_invariants.py`, `test_cli_runner.py` (local, guard the live tool).
venv: `.venv` (numpy/pandas for the jump-model stack; JAX 0.9.1/NumPyro 0.20.0 for v1 src/).

## Live vs Frozen vs Archived

**Live (do not break):** the practical vol-regime ensemble label — `data/oos_regime_labels*.csv`
(3-window HDP ensemble, consumed by Portfolio-Manager; mapping Low→`LOW_VOL`, Moderate→`MED_VOL`,
High→`HIGH_VOL`) and the `src/` + `scripts/run.py` pipeline + cached artifacts
(`data/processed/spx_data.csv`, `features_train/test.csv`, `train/test.csv`,
`models/hdp_checkpoint.pkl`, `results/regime_labels_train.csv`) that produce it. This stays the
production label until the Phase-4 swap is designed and Adam approves it.

**Frozen evidence (never overwrite, never rename):** `RESEARCH-RECORD.md` sealed sections;
`.planning/V2-JUMPMODEL-PREREG.md` (+ all earlier frozen preregs); the chapter-1 one-look
artifacts `results/v2_stage1{.csv,_run.log}`, `results/v2_oos_labels.csv`,
`results/v2_construction_gate.csv`, `results/v2_synthetic_validation*`. Future runs write
`results/backtest_*` / `results/construction_gate.csv` — clean names, no collisions.

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

## Do Not

- Break the live label contract or delete its cached inputs (list above).
- Edit sealed RESEARCH-RECORD sections, frozen preregs, `archive/research-v1/`, or the frozen
  v2_* evidence files.
- Rerun `run_backtest.py` casually — the one-look is spent.
- Build production execution logic here (Algo-Trading-Bot's job).

## Session Close

Update NOTES.md (state + next action) → commit → push.
