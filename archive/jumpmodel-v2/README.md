# Archived — the v2 statistical jump-model program (2026-07-23 → 2026-08-06)

**Status: PARKED as history. Not imported by anything. Do not revive without re-reading this page.**

This was the repo's second program: a K=2 weighted statistical jump model (Bemporad et al. 2018; Nystrup et al.
2020–21; Shu/Yu/Mulvey 2024) fit to Ken French daily market data (1926+) under strict preregistration and causal
discipline. It produced a market risk-state label — CALM / STRESSED — that was validated hard, shipped live, and
then retired.

It is kept because the *result* is worth more than the code, and because the way it died is the reason the
current observatory is designed the way it is.

## What was learned (the part that matters)

**1. Measurement validity ≠ decision value.** The label was an exceptional *instrument*: 100.0% stability under
±2y training-window shifts (vs 80.9% for the retired v1 HMM ensemble), 15/18 −15% bears caught at 20d median lag.
Every economic use tested was still dominated by something simpler. Being a good measurement does not make
something useful.

**2. Causal filters lag the regime by 5–20 days, and at a daily horizon that lag erases the edge.** This one
mechanism unified three separate closed nulls — chapter 1 (regime overlay vs buy-and-hold: the apparent win was
an exposure artifact; vol targeting dominated the overlay by −256bps, CI excluding 0), chapter 2 (state-conditional
covariance: +2.8bps vs its unconditional twin, inside every band, and −29bps against a plain EWMA-covariance twin),
and the cross-asset rotation probe. **Reactive estimators win daily-horizon lag races.**

**3. The threshold was the defect, not the model.** `results/detector_benchmark.csv` — the exposure-matched
head-to-head that ended the program — showed a plain causal volatility threshold with hysteresis matching or
beating the jump model on precision, recall and BAC at *both* bear datings, with shorter detection lag. Worse,
thresholding a continuous quantity piles all the classification error at the boundary and throws away the graded
information in σ. **This is the single most important lesson in the repo: the volatility signal was reframed from
a STATE to continuous DESCRIPTORS (2026-08-04) because of it, and "no single-word regime summary" became a
standing rule.**

**4. A confidence margin is not a portable confidence measure.** The filter's evidence margin lost to plain EWMA
volatility on Brier *and* AUC across all 8 synthetic DGP cells. Killed.

## Why it is archived rather than deleted

Adam's call, 2026-08-06: keep the jump model as history and as something we learned, but get it out of the signal
path so it cannot confuse the observatory later. It is parked as its own thing.

The frozen evidence it produced stays in `results/` and is still cited by the live docs — `stage1.csv`,
`oos_labels.csv`, `stage1_run.log` (the chapter-1 one-look), `sensor_validation.csv`, `synthetic_validation.csv`,
`construction_gate.csv`, and `detector_benchmark.csv`. The pre-registrations that governed the runs are in
`.planning/archive/`. Those are the evidence the nulls were called honestly and in advance; they are not to be
deleted.

## What is in here

- `scripts/jumpmodel.py` — the estimator: exact DP state assignment (k=2/k=3 fast paths, verified against brute
  force), sparse feature-weighted fit, causal DP-endpoint filter (never smoothed).
- `scripts/walkforward.py` — expanding walk-forward, annual refits, λ selected causally by 8y-validation Sharpe.
  Imported byte-identically by both the synthetic battery and the real runner so the two could not drift.
- `scripts/backtest.py` — strategy construction, VT/SMA200/B&H baselines, FKO utility fee, paired stationary
  bootstrap (Politis–Romano).
- `scripts/run_config.py` — frozen protocol constants.
- `scripts/synthetic_validation.py` — capability battery on simulated panels with known truth, incl. oracle and
  oracle-lag ceilings.
- `scripts/validate_sensor.py` — label vs ex-post bear datings.
- `scripts/benchmark_detector.py` — the head-to-head that ended the program.
- `tests/` — the estimator and backtest suites, including the mechanical proof that perturbing a future value
  cannot change any past state. That idea survived: it is now `causal.assert_causal`, applied to every live signal.

## What was NOT archived, and why

`build_features` (EWM downside deviation + EWM Sortino) was lifted into `scripts/causal.py` as
`downside_features` on 2026-08-06. It is a generic causal return descriptor, not jump-model machinery, and
`build_panel.py`'s construction gate (G4 crisis coverage, G5 episode count) keys off `dd10`. The move was verified
bit-identical, so `data/processed/market_daily.csv` is unchanged across it.

The live label pipeline (`live_label.py`, `regime_signal.py`, the weekly GitHub Action) was **deleted**, not
archived, on 2026-08-06 — nothing consumed it. `results/regime_card.json` is now a deliberate parked blank.

Recover any of this at git history, or reproduce v1 at tag `v1-convergence`.
