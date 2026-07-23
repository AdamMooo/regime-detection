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

## The atlas — DONE (2026-07-23) — STRUCTURE REAL, ONE CLAIM CORRECTED BY AUDIT

`scripts/atlas.py` → `results/atlas.csv` (+ run log). Cross-ASSET conditional structure,
30/30 LOEO-stable at the pooled level: **bonds** corr −0.10→−0.30 in stressed states,
ret +4.4→+7.2%, vol ratio 1.35 vs mkt 1.75; **gold** uncorrelated both states (2000+ only);
**momentum factor** corr FLIPS +0.25→−0.52, premium evaporates (Daniel-Moskowitz crash
dynamic — anti-hedge, design knowledge not a position). **Industries: correlations converge
0.83–0.92 in stress — within-equity rotation is cosmetic** (Page diversification-failure).
Conclusion: conditional value lives in cross-asset SECOND MOMENTS only.

**Audit correction (2026-07-23, pre-freeze):** LOEO sign-stability is robustness of the
POOLED estimate to single-episode drops — NOT per-episode evidence. The stock-bond corr
deepening holds in only 11/23 episodes ≥15d: the 1990s stressed shift is +0.07 (bonds
anti-hedge) and the 2022 inflation bear ran at stress corr +0.11. The vol state can't
distinguish growth-scare from inflation/rates stress (v1 stock-bond lesson: macro/rates
axis is a non-stationary co-trend). The VOL-RATIO structure is era-consistent and survives;
the corr tilt is era-fragile → chapter-2 prereg reframed around scale, not corr.

## CHAPTER 2 — RUN AND CLOSED (2026-07-23): NULL

Prereg frozen at **Rev 2.1** (audit Rev 2 + synthetic-smoke Rev 2.1 fixes: fee_B scored
from activation, F2 = vol-of-vol, verdict precedence, CCD ERC solver; freeze commit
3c3c419 precedes the run). Runner `scripts/run_allocation.py` (--confirm-frozen; --smoke =
synthetic capability check, PASSED: structured fee_a 7.0 vs unstructured 0.5). One look:

- **fee_A(cond−B_match) = +2.8 bps [−3.2, +8.4]** — F1 fires; below placebo 95th (5.8).
- **fee_B(cond−B_react) = −29.1 [−66.8, +8.5]** — F1b fires: **plain EWMA λ=0.97
  covariance beats the state-conditioned estimate**; B_react is the best ERC arm outright
  (Sharpe 0.878 vs 0.826). Era split: +8.4 pre-2000, −37.7 post-2000.
- F2 CLEAR (vol-of-vol 2.11 vs 2.15pp): the mechanism exists — conditioning stabilizes
  risk vs static — it is just dominated by reactive estimation. v1 chapter-3 lesson
  replicated on a new object, preregistered this time.
- Chapter written: RESEARCH-RECORD.md (2026-07-23 latest section). Dashboard:
  `results/report.html` now has the chapter-2 section (equity curves, fee-vs-bands,
  conditional weights, era splits). Evidence: `results/allocation_*.{csv,log}` — frozen,
  do not overwrite.

## Next action — the fork (Adam's call)

The program lesson is now sharp: **the vol axis is real; every economic use tested is
dominated by a simple reactive estimator (VT for exposure, chapter 1; EWMA for covariance,
chapter 2). State-conditioning loses detection-lag races at daily horizons.** Options:

1. **Close the economic track** → write the methods/negative paper (the long-standing
   default; now with two preregistered chapters of ammunition + the instrument result).
2. **Chapter 3 only if a use is named where lag-tolerance is STRUCTURAL** (the gate from
   the information-gate discipline) — candidates would need horizon >> detection lag
   (e.g., monthly/quarterly decision cadences where EWMA's speed advantage dies), argued
   in a prereg BEFORE any data touch. **Named candidate (Adam, 2026-07-23): factor
   exposure conditioning** — the atlas's strongest conditional structure is momentum's
   stress behavior (corr flip +0.25→−0.52, premium evaporates; Daniel–Moskowitz crashes).
   Gate to clear in the prereg: the incumbent there is realized-vol scaling
   (Moreira–Muir 2017 vol-managed portfolios; Barroso–Santa-Clara 2015 momentum risk
   management) — the SAME reactive-estimator class that won chapters 1 and 2. A factor
   chapter must be monthly-cadence (where EWMA's speed edge compresses), long-short
   costs included, with the vol-scaled incumbent as the B_react-analog co-primary.
3. Instrument-track continuation regardless: λ frontier / asymmetric penalties (Track 2)
   are about the SENSOR, not allocation, and remain legitimate.

Also queued (not blocking): calibrated P(state) from the filter evidence gap (needed by the
graded variant — calibrate on SYNTHETIC panels pre-freeze); K=3 crash/rebound exploration
(entry-lag confound check); atlas pages in report.html; λ lag-vs-whipsaw frontier.
