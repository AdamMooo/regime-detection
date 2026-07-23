# Regime-Detection — Session Notes

## Status
Program: statistical jump model (chapter 1 CLOSED — Case B); instrument-first roadmap
Branch: main
Last updated: 2026-07-23

*Full v1 session history (five nulls → convergence) and the v2 build log live in git
(this file pre-cleanup, commit b6e4b5f and earlier) and in `RESEARCH-RECORD.md` (the durable
narrative, newest-first). This file now tracks only the living program.*

## Current state (2026-07-23, post-cleanup)

**Chapter 1 verdict (frozen prereg Rev 2, one look, 381-min run): Case B.**
- fee(JM−B&H) +487.8 bps/yr [−47.4, +1138.8] — inside ALL THREE null bands (placebo 95th 541.3,
  surrogates [41,1080], iid [179,805]); exposure-matched 71/29 static mix beats the overlay
  (−48.7); γ=1 fee −314 → the "beats B&H" claim is an exposure/utility artifact, not timing.
- fee(JM−VT) **−255.8 [−477.5, −36.7]** — vol targeting dominates significantly; mechanism =
  detection-lag race (proven in silico first: even the ORACLE loses at 10–21d lag).
- The label as an instrument: stability **1.000** under ±2y train-window shifts (incumbent
  ensemble 0.809), 1.66 switches/yr, λ off grid edges, 30 bear episodes all real high-vol
  environments. Estimator instability: solved.
- Chapter written: `RESEARCH-RECORD.md` (2026-07-23 section). Visual dashboard:
  `results/report.html` (regenerate: `.venv/Scripts/python scripts/build_report.py`).

**Repo cleaned + renamed (2026-07-23):** v2_* working code renamed to functional names
(jumpmodel / walkforward / backtest / build_panel / run_backtest / synthetic_validation /
build_report; data → `market_daily.csv`); ~40 v1-era result/data/planning files deleted
(recoverable at tag `v1-convergence`); CI workflow rewritten (was referencing deleted files);
CLAUDE.md rewritten for the new era. Frozen evidence later renamed by Adam to drop v2_ prefixes
(stage1.csv / stage1_run.log / oos_labels.csv — mapping in `results/README.md`); frozen DOCS
still cite the old names. Forward program doc: `.planning/PROGRAM.md` (regime-aware allocation,
graded tilts, never 0/100 — goal set 2026-07-23).

## Roadmap (`.planning/V2-JUMPMODEL-PLAN.md`, Phase-4 tracks)

1. **Track 1 — prove the sensor (NEXT):** benchmark the 30 bear calls vs ex-post bull/bear
   datings (Pagan–Sossounov / Lunde–Timmermann); characterize the two states; build the
   SPY-splice live tail (French publishes 1–2mo lagged) so the label runs to today.
2. **Track 2 — the dial:** λ lag-vs-whipsaw frontier; asymmetric jump penalties (fast into
   bear, slow out); soft-exposure variant from the filter's evidence gap (hypothesis: it
   interpolates toward vol targeting).
3. **Phase 5 candidate — state-conditional asset menu:** what to HOLD per state (duration,
   credit, gold, French daily industry portfolios 1926+) — the lag-tolerant use. Framed as a
   conditional playbook on portfolio outcomes, NOT "info beyond vol" (settled v1 null).
   Exposure-matched controls mandatory. Prereg before running.
4. ~~Portfolio-Manager label swap~~ — DISSOLVED 2026-07-23: grep of portfolio-manager confirmed
   (and Adam confirmed) nothing ever consumed the v1 label; the integration was only an idea in
   notes. **HDP pipeline fully retired same day** (src/, run.py, models/, label CSVs, cached
   inputs, v1 deps — all deleted; recoverable in git history). Any future downstream integration
   is designed fresh against the jump-model label.

## Track 1 — DONE (2026-07-23)

- **Ex-post benchmark** (`scripts/validate_sensor.py`, `results/sensor_validation.csv`): the
  sensor is a VOLATILITY-STATE detector, not a bear-market detector — catches 15/18 LT-15%
  bears (median lag 20d from ex-post peak), precision ~0.32 (also flags vol-without-bear),
  misses fast crashes entirely (1998 LTCM, 2018 Q4 — sub-threshold at deployed λ; documented
  spec limitation; asymmetric-λ is the Track-2 knob for it).
- **Characterization (the headline):** stressed state has HIGHER ann. mean (14.1% vs 11.6%)
  at 2× vol (25% vs 14.3%) — crashes AND rebounds share the state (partly a mechanical
  entry-lag tilt toward rebound days). Sharpe 0.56 vs 0.81 → risk-adjusted logic alone cuts
  stressed exposure to ~40% of calm with NO directional bet. **Conditional value lives in
  second moments** → atlas focuses there. Confidence upgrades queued: calibrated P(state)
  from the filter evidence gap; K=3 crash/rebound split as atlas-phase exploration (must
  re-clear K=2's stability bar; watch the entry-lag confound).
- **Live label operational** (`scripts/live_label.py`, `results/label_live.csv`): SPY splice
  gate PASS (corr 0.9957), label runs to TODAY; 1.0000 agreement with frozen labels on all
  9120 overlap days. Current state: CALM since 2026-04-23.

## Panel expansion — DONE (2026-07-23)

`scripts/build_assets.py` → `data/processed/assets_daily.csv` (regenerable, gitignored),
gates PASS (`results/assets_gate.csv`): 10 FF industries + SMB/HML/MOM (complete-case 1963+),
synthetic 10y bond TR (IEF corr 0.962, ann vol 7.1% — fixed a duration bug that had doubled
vol: half-year periods vs years), gold via GC=F (2000+, GLD corr 0.888, non-synchronous
closes documented; FRED London-fix series unavailable).

## Next action

**The atlas** (program step 3): per-state conditional stats (ann ret / vol / Sharpe /
corr-with-market) for every asset, industry, and factor, with leave-one-episode-out
stability counts (the confidence meter) + block-bootstrap CIs → new pages in
`results/report.html`. Descriptive, in-sample, labeled as such; informs (never gates) the
step-4 allocation prereg. Confidence upgrades alongside: calibrated P(state) from the filter
evidence gap; K=3 crash/rebound split exploration (entry-lag confound check included).
