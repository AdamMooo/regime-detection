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

**2026-08-10 — the boundary this repo exports is now a real contract, the read is current, and credit's charter is
signed with its look staged.** 147 tests (was 42 on 2026-08-09).

**The observation contract shipped (plan §5).** `contracts/market-observation-v1.schema.json` + 18 conformance
vectors, every one run through **both** the JSON Schema and `signal_output_schema.py` with a required-identical
verdict. Consumers **vendor** a pinned copy by sha256 — no Python import, so drift is a red test in the consumer.
`rarity.basis` is a required enum, which resolves the cross-repo audit's **D2** at the interface, and
`full_sample` can never be `production`. `observations/<signal>/history.ndjson` holds the point-in-time history —
volatility **1190 records from 1927-07-30**, stock-bond **756 from 1963-12-31**. Deviated from plan §5.4's
one-file-per-`as_of` layout and disclosed why in `contracts/CHANGELOG.md`: that path **cannot express its own
correction model**, and daily granularity was **22× redundant** (25,938 `as_of` dates → 1,187 real
`available_at` vintages). **These records are reconstructions, not contemporaneous prints** — the data-derived
numbers are causal, the *specification* is today's, and the manifest says which via `provenance`.

**LIVE READ, as of 2026-06-30 (knowable 2026-07-15) — and for the first time the two axes disagree.**
Volatility **15.21% annualised, 69.7th percentile**, half-life 36.8d, falling. Stock-bond **+0.136, 52nd
percentile, `violated`, 52 months in** — against a historical median of **52** months for a major violated
episode (max 129), and falling hard (−0.333 over 12 months) toward the +0.10 band edge. In May both axes read
~52nd percentile and carried one piece of information between them; now volatility is elevated *while* the usual
shock absorber is not working. That is the "low-vol but fragile" case inverted, and no single axis gives it.

**EVERY signal has a vintage surface — found by refreshing the data.** The refresh to 2026-06-30 **restated 5
stock-bond and 2 volatility readings at `as_of` dates already published**, and the append-only log **refused to
overwrite them** on its first contact with live data. Magnitudes are 4th-decimal, so nothing quantitative moves,
but it **falsifies the credit charter's claim** that credit is "the first admitted signal with a vintage surface
at all (the others are built from returns)." Return data revises too. Note which control caught it:
`data/processed/MANIFEST.csv` **could not** — it records rows, span and sha256, so a within-span revision
arriving alongside an append presents as a plain append. Panel-level and reading-level provenance catch different
failures.

**Phase 6 (credit/EBP) — CHARTER FROZEN v1.0, signed 2026-08-09, build authorised, look UNSPENT.** PROCEED at a
`research` ceiling registered pre-look and **explicitly not reopenable on a strong result**; **R2 ⇒ DROP**, not
demotion; Bar B gates on the **minimum** Spearman and Bar C is **pooled**, both clarified before any value
existed. **19 archived EBP vintages harvested** (2022-08-18..2025-12-03) — V2's decisive-bar evidence base, which
did not exist in the repo, committed because Archive coverage is not guaranteed to persist. Two amendments cut
*against* the phase: **G4 is unopposed, not confirmed** (Phase 7 was dropped, so the registered leave-one-out can
never run — uniqueness is untested), and publication timing is **bounded from above** by captures, not verified.
`scripts/validate_credit.py` is scaffolded and self-tests 6/6 on synthetic data; the four statistics are Adam's
to write, and the script refuses to run without `--i-am-spending-the-one-look`.

**2026-08-07 — two signals now carry dated results sign-offs; the third's look is spent and its verdict is the
interesting one.**

**Phase 2 (stock-bond, PC2) CLOSED — signed off 2026-08-07, maturity `research`.** Cooling-off observed; V2–V5
verdict table in the charter's §RESULTS SIGN-OFF; R1–R5 none tripped. Evidence maturity is `M` rather than `H`
because the international sample begins 1990 and holds no inflation regime — the sign-flip cycle is untested
out-of-sample, and D-02c held even under a strong result. Level-0 record at `results/stockbond_level0.json`; live
read 2026-05-31 is **24m corr +0.15, 53rd percentile, `violated`, 51 months in**. The status and the rarity
disagree by design — the 1970s–80s were positive too, so **violated is not unprecedented**. Also added
`results/stockbond_monthly.csv`: the registered native clock had no committed artifact, which was a real gap.

**Phase 3 (valuation) — charter respecified to v1.1, signed, and its one-look spent the same day. Five of six bars
clear; V6, the pre-registered statistical bar, does not, so R9 is live and the disposition is Adam's.** The shape
is textbook and robust — log CAPE slope −0.0033 (1m) → −0.331 (5y) → **−0.610 (10y)**, R² rising to **0.257**,
~silent sub-1yr; it survives on **excess** returns, holds **stronger pre-1982** than inside the 1982–2021 rate
decline, and reproduces on P/D and cap/GDP (the latter using **no earnings at all**, which is what kills the
Siegel confound). **And none of that clears the null.** A bootstrap under no-predictability — 2000 block paths
preserving ρ = 0.9965 and corr(return innovation, regressor innovation) = **+0.96**, near-tautological because
CAPE's numerator *is* the price — gives **p = 0.07–0.26 at every horizon**. The 10y raw t = −23.7 is reproduced by
chance in ~10% of null paths, and Stambaugh removes **64–72%** of the raw one-month slope. With **~13 effective
independent 10-year observations in 145 years**, the data cannot separate the Campbell–Shiller mechanism from a
persistent-regressor artifact. That is the information content, not an analysis defect — and it is exactly what
R9 was written to detect.

Two things that made Phase 3 possible without paid data. **Free international valuation history:** no CAPE exists
for Japan or Europe, but French publishes the International Indices **twice**, with and without dividends, on the
same universe — so `R_with − R_without = D_t/P_{t−1}` exactly, giving market-level D/P for 6 regions, 1975–2025
(`scripts/build_intl_valuation.py`, 612 months; Asia Pacific bottoms 0.69% in 1989-03, Europe ex UK 1.63% in
1999-11). **And a named hole:** total-payout yield has no free history, so **R5 (payout confound) is registered
UNTESTABLE** — P/D was kept precisely because it is most exposed to it. **42 tests pass.**

**2026-08-06 (late) — the signal set is now CURATED: 9 scoped → 5 live.** Phase 2 stock-bond refactored onto the
shared spine, charter frozen + signed, and its **one-look spent: V2 hedge-behaviour is monotone in all three
regions** (US 28→44→56%, Japan 25→29→51%, Europe 27→32→48% of equity-down months where bonds also fell) — R1/R2
not tripped. Results sign-off pending cooling-off; maturity capped at `research` because the international sample
starts 1990 and contains no inflation regime (registered *before* the look). Then five research agents produced
five charter drafts and four build agents produced **four working signal constructions**: valuation (Shiller CAPE
1881+, 5-month earnings publication lag derived, not guessed), concentration (effective-N across the 25 French
size/BM buckets, 1926+), credit (EBP on an as-of index so the frame is indexed by when a reading was *readable*),
and tail (price of downside protection, 2000+ only). **Absorption and funding were DROPPED at the charter stage,
no look spent** — archived with why in `.planning/archive/dropped-signals/`. The jump-model program is archived to
`archive/jumpmodel-v2/` with its lessons written down, `results/regime_card.json` is a deliberate parked blank, and
the last boundary-audit exception is gone. **41 tests pass.**

**Two findings that outlive their phases.** (1) **Market data is not vintage-free** — Cboe's 2011 documentation
gives SKEW all-time low/high 101.09 / 146.88 where today's file gives 101.31 / 146.22 *on the same dates*, and the
all-time-low date itself moved. `assert_causal` cannot catch this; it guards the construction, not the data.
Mitigation: `python scripts/data_manifest.py --check` diffs every panel's sha256 against the committed manifest.
(2) **CI was never running the guards** — `tests.yml` installed a hand-picked subset and ran only the retired
program's suites, so the boundary audit, causal guard and reproducibility tests had never executed in CI. Fixed.

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

- **OPEN DECISION — R9 on the valuation signal.** The Phase 3 one-look is spent and five of six bars clear, but
  the pre-registered statistical bar does not. Two defensible readings are written into the charter's ONE-LOOK
  RESULTS section without one being chosen: **(1)** R9 trips, the forward-return claim fails, and valuation is
  demoted to a pure measurement — the shape volatility already took; **(2)** the evidence is weak-but-consistent
  across 20+ specifications, with the honest counter that those specifications share one price series. **The call
  is Adam's, after cooling-off. Do NOT rerun the bootstrap with another seed or block length to see whether p
  crosses 0.05** — seed 20260807 is fixed and the look is spent.
- **RESOLVED 2026-08-06, kept for the reasoning** — the retired jump-model estimator is no longer in the tree. It
  moved to `archive/jumpmodel-v2/` (and the internals gauge to `archive/internals-gauge/`), each with a README
  recording what was learned. The one real dependency, `build_panel.py`'s call to `jumpmodel.build_features`, was
  broken by moving that function to `causal.py` as `downside_features` and **verifying it bit-identical on the
  same input**, so `market_daily.csv` is unchanged and the signed-off vol numbers did not move.
- **Downstream leftover (other repo).** `portfolio-manager/src/regime.py` still contains a fetcher for the now-blank
  card, and `daily-report.yml` still passes `REGIME_REPO_PAT`. **Nothing imports either** — verified 2026-08-06.
  Dead weight in that repo, to be removed there; the PAT can be revoked once it is.
- **`.planning/ROADMAP.md` still lists Phase 8 (crowding)**, dropped 2026-08-05, and still shows Phase 9 (tail) as
  data-gated, which it no longer is. GSD-managed file, not hand-edited.
- French data publishes with a 1–2 month lag. The SPY-splice live tail that used to bridge it was deleted with the
  label pipeline, so signal reads now end at the French vintage (currently 2026-05-29). Any signal needing a
  to-today read must bring its own causal splice.
- **Resolved 2026-08-06, kept for the record:** the RF open item (volatility's provisional `production` tag) is
  closed by the literal Japan/Europe V5 run and the dated sign-off; `results/vol_descriptors.csv` is back in sync
  with its producer's columns; bare `pytest` works again via `pytest.ini`.
