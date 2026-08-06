---
type: hub
project: regime-detection
---
# Regime Detection

A **market-signal observatory**: `market data → independent validated signals → historical context → regime
relevance → STOP`. Each signal is a standalone research module measuring one market mechanism, saying how unusual
the current reading is against its own long history, and naming the abstract market assumption it bears on — then
stopping. No forecast, no score, no decision (see [[regime-detection/CLAUDE|CLAUDE.md]] HARD BOUNDARY). The
intelligence is the quality of each individual signal, never a combination of them.

Governing docs: [[_planning/regime-detection/REGIME-SENSOR-ARCHITECTURE|REGIME-SENSOR-ARCHITECTURE.md]] (system
design, incl. the 2026-08-06 objective restatement) and `.planning/framework/` (frozen v1.0 2026-08-03, now v1.1
after the Stage-0 gate amendment — the spec every signal declares against).

## Status

**2026-08-06 — volatility signal COMPLETE (first signal through the full DoD).** Adam's dated results sign-off
landed (`.planning/phases/01.5-volatility-signal/1.5-VOLATILITY-CHARTER.md` §RESULTS SIGN-OFF): V2–V5 pass, no
reject condition tripped, **maturity derived = `production`**, and the **RF open item is CLOSED** — the
out-of-hypothesis-sample evidence is now a literal Japan/Europe run, not an appeal to the universal vol-clustering
stylized fact. Scope is deliberately narrow: a *measurement* claim, never forecastability. Level-0 record emitted
and schema-validated (`scripts/vol_level0.py` → `results/vol_level0.json`). Reproducibility hardening the same
day, each test written against a failure that actually happened: `requirements.txt` completed (arch / statsmodels /
scikit-learn / matplotlib), `tests/test_reproducibility.py` added, `causal.assert_causal` added to the DoD
(a signal's `build` must pass it before its one-look), `scripts/data_manifest.py` → `data/processed/MANIFEST.csv`
for data provenance, and `pytest.ini` so bare `pytest` works (50 pass).

**2026-08-06 — objective restated; measurement system ≠ prediction system.** Recorded in the architecture doc: the
signals are *expected* to be mostly known relationships (Engle, Campbell–Shiller, Kritzman, Gilchrist–Zakrajšek) —
reproducing them point-in-time, causally, cross-regionally is the pass condition of an instrument, not a thin
result. The edge hypothesis is explicitly **not** "signal X predicts the market" but "multiple validated
measurements of different mechanisms describe market state more completely than any single indicator." Prohibited
by name: market-timing labels · predictive models without economic justification · weights optimized on historical
returns · composite scores built to maximize backtests. No backtesting engine enters the repo. Sequencing
consequence: build the remaining signals out first — the joint-configuration question is deferred to Phase 10 and
must not be pre-empted signal by signal. Same day: the stale root docs (`README.md`, this hub, `results/README.md`)
rewritten to match reality.

**2026-08-05 — volatility one-look run and passed + 5 signals warm-started.** Vol charter signed off, then the
frozen one-look ran (`scripts/validate_vol.py` → `results/vol_validation.txt`): V2–V5 all pass — GARCH structure
remarkably consistent across US/Japan/Europe (α≈0.09, β≈0.89), level robust to λ and to a range-based estimator,
rarity percentile well-behaved. Rolling-only locked (rolling ≈ expanding, DM t=0.65; expanding fails the D-19
leave-one-out as a live reading). Shared infra built once (D-20): `scripts/causal.py` (causal primitives),
`scripts/run_oos.py` (generic Japan/Europe harness). Persistence estimator **deviates** from the registered AR(1)
to GARCH(1,1)-t — disclosed: AR(1) on rolling realized vol manufactures autocorrelation from return overlap, so its
half-life just tracked the smoothing window. Separately, triage warm-started 5 signals (concentration ·
absorption · credit/EBP · funding · tail) with kickoff briefs + pulled data, and **dropped crowding (Phase 8)** —
proxy-only, and it risks re-reading the vol axis.

**2026-08-04 — volatility reframed from a STATE to continuous DESCRIPTORS (Phase 1.5 inserted).** The K=2
jump-model label loses to a plain causal vol threshold with hysteresis on every skill axis
(`results/detector_benchmark.csv`) and the thresholding step throws away σ's graded information. Vol is now
`scripts/vol_descriptors.py` (measurement spine) + `scripts/vol_read.py` (presentation): level/percentile · drift ·
rarity · durability. "Barometer, not switch."

**2026-08-03 — Phase 1 framework FROZEN v1.0 (signed off).** `.planning/framework/` holds the 8-attribute signal
spec, the validation standards, the charter template, and the unified admission model (D-17: a binary mechanism
prerequisite gate + three non-compensatory axes — measurement validity · investment usefulness · evidence
maturity — with the maturity tag *derived*, never asserted; composite scalars forbidden). Enforcement is live in
code, not prose (D-18): `scripts/signal_output_schema.py` + `tests/test_boundary_audit.py`, which on day one caught
a real boundary leak every manual grep had missed. System framing locked as **factor observatory /
decision-support layer**; module = **signal** (canonical). Valuation charter frozen the same day (Phase 3,
sign-off pending, no data look spent).

**2026-08-02 — PIVOT to the market-signal system.** The equity-ownership program (a separate concern) was removed
from this repo; recoverable in git history. Ten-phase roadmap set up, every phase's DoD identical: Find → Validate
→ Present → STOP. Stock-bond correlation signal built and US-validated 1962–2026 (`scripts/stockbond_corr.py`) —
the hedge-behaviour-by-state metric confirms the mechanism; average-return-by-state is confounded by the rate cycle
and was rejected as the metric.

**History — v1 and v2 (both closed, worth remembering).** *v1* (sticky HDP-HMM plus four successor formulations)
converged through five preregistered nulls and is sealed at git tag `v1-convergence`. *v2* (the K=2 statistical
jump model on Ken French daily data 1926+) ran three chapters through 2026-07: **chapter 1 closed 2026-07-23** —
"regime switching beats buy-and-hold" is an exposure artifact (fee inside every null band) and vol targeting
dominates the overlay; **chapter 2 closed the same day as a registered NULL** — state-conditional covariance adds
nothing over its unconditional twin and loses to a plain EWMA twin; the **probability layer was KILLED** on a
calibration gate (the filter's evidence margin loses to plain EWMA vol on Brier *and* AUC in all 8 synthetic DGP
cells); **chapter 3's one-look was deliberately never spent**. Two further directions closed the same way: the
sector-dispersion lead did not generalize (Japan +154d, Europe +94d) and the cross-asset defensive-rotation probe
returned NULL. Program lesson, reconfirmed three times: *reactive estimators win daily-horizon lag races* — which
is exactly why this repo now measures rather than decides. Durable narrative:
[[regime-detection/RESEARCH-RECORD|RESEARCH-RECORD.md]].

## Next

Volatility is done. Take the next signal kickoff → full charter → build → one-look → dated sign-off. All are warm:

- **Phase 2 — stock-bond correlation intl OOS.** Closest to done; un-gated since 2026-08-05
  (`scripts/build_intl_bonds.py` → `intl_bonds_monthly.csv`, JP 10y 1989+, Bund 1956+, monthly = the signal's
  honest frequency). Recommended first. Order: refactor `stockbond_corr.build()` onto `build(r)` + `causal.py`
  (it currently takes no arguments and loads its own US panel, so it cannot feed `run_oos` — and it re-implements
  primitives instead of importing them, D-20 drift) → charter (no `.planning/phases/02-*` directory exists yet)
  → run → one-look.
- **Phase 3 — valuation.** Charter frozen 2026-08-03, sign-off pending; the first fully-new signal.
- **Phases 4 / 5 / 6 / 7 / 9** — warm-started with kickoff briefs and data; each needs its charter expanded first
  (D-15, charter before implementation).

No auto-advance. Every signal gets its own one-look and its own dated sign-off.

## Memory

- **Operations:** [[regime-detection/CLAUDE|CLAUDE.md]] (boundary, file map, discipline)
- **Notes:** [[regime-detection/NOTES|NOTES.md]] (session state, read first)
- **Research narrative:** [[regime-detection/RESEARCH-RECORD|RESEARCH-RECORD.md]] (newest-first)
- **Public orientation:** [[regime-detection/README|README.md]] (what the repo is, signal status, quickstart)

## Known Issues

- **`scripts/build_report.py` renders the retired v2 program.** It does *not* crash on the deleted
  chapter-2 CSVs — `build_alloc_data()` guards with `if not p.exists(): return None` (`build_report.py:145`) and
  `main()` runs clean; the earlier "will crash if run as-is" note was wrong. The real problem is content: the
  report is still chapter-1/2 framing built on the jump-model label. It needs refocusing on signals, or retiring.
- **Retired jump-model code still in the tree.** `live_label.py` → `regime_signal.py` still generates
  `results/regime_card.json` for a downstream consumer, and `jumpmodel.py` / `walkforward.py` / `backtest.py` /
  `regime_read.py` / `regime_panel.py` remain. Retirement is deliberate-but-unscheduled; the downstream contract
  has to be handled first.
- **`gauge.position` → `gauge.dwell_rank` rename outstanding.** A boundary leak in `results/regime_card.json`,
  carried as the single documented exception in `tests/test_boundary_audit.py`. Needs a coordinated rename with the
  consumer repo, then the exception is removed. End-of-project cleanup.
- **`scripts/stockbond_corr.py` is off the shared spine.** `build()` takes no arguments (loads its own US panel),
  so it cannot feed `run_oos(build_region)`, and it re-implements `realized_vol` / `expanding_z` locally instead of
  importing `causal.py` (D-20 drift). Blocks the Phase-2 Japan/Germany run; fix first, no look spent.
- **`.planning/ROADMAP.md` still lists Phase 8 (crowding)**, dropped 2026-08-05, and still shows Phase 9 (tail) as
  data-gated, which it no longer is. GSD-managed file, not hand-edited.
- French data publishes with a 1–2 month lag — handled by the SPY-splice live tail (`scripts/live_label.py`, gate
  PASS corr 0.9957, 1.0000 agreement on overlap); the splice must be refreshed when displaying a current reading.
- **Resolved 2026-08-06, kept for the record:** the RF open item (volatility's provisional `production` tag) is
  closed by the literal Japan/Europe V5 run and the dated sign-off; `results/vol_descriptors.csv` is back in sync
  with its producer's columns; bare `pytest` works again via `pytest.ini`.
