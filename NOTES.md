# Regime-Detection — Session Notes

## Status
A **market-signal research system** (see CLAUDE.md HARD BOUNDARY — market data → independent signals →
historical context → regime relevance → STOP; never allocation/decisions). The equity-ownership / allocation
program was removed from this repo 2026-08-02 (recoverable in git history). Branch: main | Last updated: 2026-08-09

## Current direction — independent market-signal modules (find → validate → present → STOP)

Governing design: **`.planning/REGIME-SENSOR-ARCHITECTURE.md`**. Each signal is its own research module with 8
attributes (research question · economic mechanism · data · metric · validation · failure modes ·
historical-context output · maturity). The intelligence is the quality of each individual signal; the
presentation layer only organizes validated signals into multiple lenses — never a score, never a decision.

**Built / shipped:**
- **Volatility / risk-off** — REFRAMED 2026-08-04 from the jump-model STATE to continuous DESCRIPTORS
  (`scripts/vol_descriptors.py` measurement spine + `scripts/vol_read.py` presentation). The K=2 jump label loses
  to a continuous vol+hysteresis read on every skill axis (`results/detector_benchmark.csv`) and the threshold
  destroys σ's graded info. Now Phase 1.5 (INSERTED, executes next); still owes the full DoD (charter · Stage-0 ·
  Japan/Europe OOS · sign-off). Old jump-model card/`regime_signal.py` still generates but is being retired.
- **Stock-bond correlation** (inflation/real-rate) — `scripts/stockbond_corr.py`, built this session. Validated
  on US 1962-2026: sign matches known regimes; hedge-behavior-by-state confirms the signal (on equity-down days
  bonds cushioned 32% of the time in the "intact"/negative-corr regime vs fell-too 57% in the "violated"/
  positive-corr regime — monotone through the states). Design lessons: monthly-anchored regime read (daily
  126d calendar-mean hid the 2022 flip); avg-return-by-state is CONFOUNDED by the rate cycle (use the
  hedge-behavior metric). Still TODO: OOS confirmation on Japan/Europe (needs JGB/Bund series).

**To build (one GSD phase each): valuation · concentration · diversification/correlation (absorption) · credit
(EBP) · funding stress · crowding · tail (data-gated).** Then the presentation layer (assumption ledger + joint
rarity + historical analogues).

## PHASE 1 COMPLETE (2026-08-03) — framework FROZEN v1.0 (signed off; see below)

**Phase 1 (Signal Framework) built + verified 7/7.** The shared spec every future signal declares against now
lives under **`.planning/framework/`**:
- `signal-spec-template.md` — semver 8-attribute template (D-04 order: Definition · Mechanism · Measurement ·
  Historical Context · Validation · Assumptions · Confidence · Limitations), question-form, forced "N/A because…".
- `validation-standards.md` — causal/PIT · mechanism gate · confound-check · Japan/Europe OOS · one-look+prereg+
  cooling-off+dated sign-off · TRIPOD completeness checklist · HARD BOUNDARY reviewed-grep audit · D-10 (no
  signal designed around a desired conclusion) · D-12 (optimize for integrity/reproducibility, not prediction).
- `research-charter-template.md` — D-15 six-question pre-registration required BEFORE any future signal is built.
- `signal-output-spec.md` — **unified signal-admission model** (2026-08-03, D-17, REPLACES the four-dimension
  confidence model): a **binary mechanism prerequisite gate** (pass/rejected) + **three graded non-compensatory
  axes** — measurement validity · investment usefulness (important question + unique information, static
  per-signal) · evidence maturity; the **maturity tag is DERIVED** {mechanism pass + 3 axes + sign-off +
  investor-question}, implementation-maturity dimension DROPPED. Assessment = "earned its place," never
  predictive. Descriptive maturity (production NOT "better" than research); Level 0 measurement · Level 1
  historical context · Level 2 regime relevance, STOP at Level 2; composite-scalar forbidden, kept distinct from
  the Phase-10 joint-rarity (Mahalanobis) lens. Level-0 closed `assessment{}` field set + boundary enforced in
  code next pass (schema allowlist + boundary-audit test + repo-structure rule — D-18, architecture not docs).
- `examples/{volatility,stock-bond-corr}-signal-declaration.md` — the two built signals retro-fit the template
  cleanly (fast/production + slow/research shapes).
- `SIGNOFF-CHECKLIST.md` — **everything unsigned; nothing frozen to v1.0.**
- `.planning/REGIME-SENSOR-ARCHITECTURE.md` now cross-links `.planning/framework/` as the governing spec (D-16).

**Observatory-framing refinement (2026-08-03, Adam-directed):** system-level name = **factor observatory /
decision-support layer**; module stays **signal** (canonical); **market-state factor** = informal synonym,
DISTINCT from an equity-return/priced-risk factor and from the killed regime-as-a-factor. Added to the
framework: each signal declares its **investment question** (template Q1.3) + its **cross-signal relationships**
(Q4.3), and Level-0 output gains **trend · extreme_conditions · cross_signal_relationships** — so the set is an
observatory, not disconnected readings. Pipeline (investment view): Market data → signal states → historical
context → *investor interpretation* → *investment decision*; the CODE stops after historical context (Level 2).
Glossary + framing live in `.planning/REGIME-SENSOR-ARCHITECTURE.md` §observatory framing.

Config note: `auto_advance` + `use_worktrees` disabled (sequential docs workflow). ROADMAP SC#3 + architecture
doc still say "three confidence dimensions" — superseded to FOUR (recorded in the new spec, not silently edited);
patch those two frozen docs to "four" once the framework is signed off.

## FRAMEWORK FROZEN v1.0 (2026-08-03) — Phase 1 CLOSED

Adam signed off the framework 2026-08-03 (`.planning/framework/SIGNOFF-CHECKLIST.md`). Dispositions: **A1**
(three-axis anchors) ACCEPTED · **A2** (maturity-derivation rule, structure) ACCEPTED · **A3** (forbid composite
scalar) ACCEPTED · **ADM** (unified admission model, D-17) CONFIRMED · **ENF** (code enforcement is architecture,
D-18) CONFIRMED · **OBS** (observatory framing) CONFIRMED. D-06 swap RESOLVED (superseded by ADM). All framework
docs bumped to v1.0; ROADMAP SC#3 + architecture stale "three confidence dims" text patched to the admission model.

**Enforcement is LIVE (code, not docs):** `scripts/signal_output_schema.py` (closed Level-0 allowlist + denylist +
`validate()`) and `tests/test_boundary_audit.py` (34 passed). On day one it caught a real HARD-BOUNDARY leak that
every prose "reviewed grep" had missed — vindicating D-18.

**Two open/tracked items (do NOT lose):**
- **RF (OPEN, cooling-off):** the shipped volatility signal's `production` tag rests on frozen-US OOS + the
  universal vol-persistence stylized fact, NOT a literal Japan/Europe run. Tag carried PROVISIONALLY. Decide the
  universal-stylized-fact clause vs a literal panel run when volatility is formally admitted (or at Phase 2).
- **`gauge.position` → `gauge.dwell_rank` rename (deferred cleanup):** boundary leak in `results/regime_card.json`
  (produced by `scripts/regime_signal.py`), a downstream contract. Carried as a single documented exception in
  `tests/test_boundary_audit.py` (`KNOWN_DEFERRED_EXCEPTIONS`). Coordinated rename (this repo + downstream repo) +
  remove the exception = end-of-project cleanup.

## VALUATION CHARTER FROZEN (2026-08-03) — Phase 3 pre-registration written, sign-off pending

`.planning/phases/03-valuation-signal/03-VALUATION-CHARTER.md` written this session (worked Q3/Q4/Q5 with Adam,
no data look). Registered: **mechanism = risk-premium-primary** via the Campbell–Shiller discount-rate identity
(behavioral = non-load-bearing amplifier; survives-being-known argued from the un-arbitrageability of a low risk
premium; horizon structure = the mechanism's signature). **Validation bar (V1–V6):** horizon-conditional shape ·
excess returns · sub-period incl./excl. 1982–2021 · metric-robustness panel · Japan/Europe OOS · bias-aware
inference. **Reject conditions (R1–R9)**, each paired to the test it trips — R1 (Adam's primary) = *no evidence
valuation carries useful info about future EXCESS returns consistent with the mechanism* (a growth-forecast
finding is a category change → separate signal, NOT a bury). **Analysis spec frozen:** CAPE-primary + cap/GDP +
P/D + total-payout-yield panel (anti-metric-shopping) · excess over short real risk-free · three-test rate-regime
battery (excess + sub-period + intl OOS) · Stambaugh/Hodrick + effective-N inference · point-in-time
reconstruction. Boundary self-audit clean (forbidden vocab only in the Q6 prohibition).

**Two open items before research/build starts:**
- The three defaulted analysis choices (metric / excess benchmark / rate battery) are registered as *recommended,
  not yet Adam's* — Adam reviews the "Pre-registered analysis specification" block and overrides any line.
- **Dated sign-off pending.** Signing the charter = Stage-1 freeze of the pre-registration only (NOT a positive
  claim, so no cooling-off needed). Research/build begins after sign-off. Emphasis (Adam): get this right — the
  signal must come out **clear and definable**, not a fuzzy composite.

## VOLATILITY CHARTER FROZEN (2026-08-05) — Phase 1.5 pre-registration written, sign-off pending

`.planning/phases/01.5-volatility-signal/1.5-VOLATILITY-CHARTER.md` written this session (Stage-0 gate + 6 charter
questions + analysis spec; boundary grep clean — hits only in the Q6 prohibition). Two framing decisions locked
with Adam (2026-08-05): **(1) validation shape = measurement correctness + international replication** (vol is
DESCRIPTIVE, not predictive — mechanism = vol clustering, trivial/universal; no forecastability claim, so Q5
falsification targets the MEASUREMENT being an artifact, never a missed forecast). **(2) ledger key = N/A, vol is
a CONTEXT axis (PC1 barometer), not an assumption-monitor** — no {intact/under-test/violated} status, deliberately,
to avoid re-importing a state. V1–V5 / R1–R5 registered; V5 (Japan/Europe replication) is the run that **closes the
RF open item**. Charter-first inversion disclosed: level/pct/drift/rarity built during the 2026-08-04 reframe
before the charter; the 4th descriptor (**shock persistence / half-life**) is NOT built and is registered here.

**Two open items before build starts (mirror the valuation charter):**
- Analysis-spec lines marked **[recommended — Adam to confirm/override]**: the estimator-robustness panel (λ=0.97 +
  range-based Parkinson/Garman–Klass) and the persistence estimator (AR(1) on log realized vol → half-life =
  ln2/(−ln φ), in trading days). Adam reviews + overrides any line.
- **Dated sign-off pending.** Signing = Stage-1 freeze of the pre-registration only (not a positive claim → no
  cooling-off needed). Build begins after sign-off.

## TASK 1.5-01 COMPLETE (2026-08-05) — charter signed off + infra + persistence descriptor

Charter **signed off by Adam 2026-08-05** (both [recommended] analysis-spec lines confirmed); build authorised.
Built + tested (34 pass):
- `scripts/causal.py` — shared causal primitives (D-20, built ONCE): `ewma_vol`, `realized_vol`,
  `expanding_percentile`. Reused by the harness + every later signal.
- `scripts/run_oos.py` — generic OOS harness (D-20): `load_region` + `run_oos(build_region, regions)`; region-
  agnostic, all panels share `date,mkt_ret`. Drives any signal's `build(r)` over US/Japan/Europe.
- `scripts/vol_descriptors.py` — refactored onto `causal`; `build(r)` accepts any region's returns;
  `shock_half_life(r)` = **GARCH(1,1)-t persistence** (half-life = ln0.5/ln(α+β)), trailing ~5yr window refit
  quarterly, NaN when α+β≥1. Wired into `build` + `vol_read` as the 4th reading.
- `scripts/vol_read.py` — now renders all four questions (level·pctile / drift / rarity / **durability**).

**Persistence estimator = GARCH (DEVIATION from the AR(1) originally registered — disclosed in the charter,
2026-08-05, Adam-directed "do this right").** The AR(1)-on-realized-vol was caught in construction as a V2
estimator artifact: fitting AR(1) to a rolling-window realized-vol series manufactures autocorrelation from the
shared-return overlap (φ→(m−1)/m), so its half-life just tracked the smoothing window. GARCH models latent
conditional variance directly (no artifact); α+β is the canonical persistence. Trailing (not expanding) window
because a century fit mixes regimes → near-IGARCH inflation (Lamoureux–Lastrapes). **US finding:** persistence
strong everywhere (α+β≥0.92) but half-life is REGIME-CONDITIONAL — ~9d (last 3yr) → ~123d (last 10yr) → undefined
(1930–50, α+β=1); latest live read ~35d. **v-next registered:** component/spline-GARCH (Engle–Rangel) to split
short-run persistence from baseline drift (version A = trailing-window GARCH = v1.0).

**Sanity is INFORMAL, construction-time — NOT the frozen one-look.** See the one-look note below before 1.5-02.

## TASK 1.5-02 — VALIDATION ONE-LOOK DONE (2026-08-05), PASSES; sign-off + cooling-off pending

Ran `scripts/validate_vol.py` (frozen one-look) → `results/vol_validation.txt`. Rolling-only LOCKED (horse race
= rolling≈expanding, DM t=0.65; expanding fails D-19 leave-one-out as a live reading). Descriptor finalized:
`half_life_pctile` (rarity of durability from its own history) added. Honest read vs charter bars:
- **V5 OOS replication (closes RF):** GARCH structure REMARKABLY consistent — α≈0.09, β≈0.89 in US/Japan/Europe;
  rolling half-life median 42/17/40d (same order of magnitude). Clustering is universal, not a US artifact. PASS.
- **V2 robustness:** corr(λ0.94,λ0.97)=0.975 (soft caveat: exact 5-band bucket agrees 78% — adjacent drift, not
  flips); close-to-close vs Parkinson corr 0.91–0.95 all regions. PASS (stable, not identical).
- **V3 persistence:** GARCH identifiable all regions, IGARCH guard works. PASS.
- **V4 rarity:** expanding pctile uniform/monotone. PASS.

## PHASE 1.5 CLOSED — vol RESULTS SIGNED OFF by Adam 2026-08-06

Cooling-off observed (one-look 2026-08-05 → sign-off 2026-08-06), explicit and dated. Recorded in
`.planning/phases/01.5-volatility-signal/1.5-VOLATILITY-CHARTER.md` §RESULTS SIGN-OFF with the V2–V5 verdict
table; R1–R5 none tripped.
- **RF open item CLOSED** — the OOS evidence is now a literal Japan/Europe run, not an appeal to the universal
  stylized fact. The provisional clause is retired.
- **Maturity DERIVED = `production`** (mechanism `pass` · measurement validity `H` · investment usefulness `H` ·
  evidence maturity `H`).
- **Level-0 record emitted** — `results/vol_level0.json` via `scripts/vol_level0.py`, generated from the artifact
  and passed through `signal_output_schema.validate()` (boundary enforced by allowlist, not by care).
- Claim scope is deliberately narrow: a MEASUREMENT claim, not forecastability. α+β≈0.99 means vol forecasts vol.

**Bug caught while emitting the record:** the committed `results/vol_descriptors.csv` predated the half-life
descriptor (only `mkt_ret, vol_annual, vol_pctile`) — a result artifact that silently disagreed with the code
that claims to produce it. Regenerated; live read = **34.8d half-life, 12.0% vol, 51.9th pctile, as of 2026-05-29**
(French publishes 1–2mo lagged). Now guarded by a test.

## WARM-START — remaining signals prepped (2026-08-05)

Triage (orthogonality evidence + a data-source scout): **5 signals warm-started, crowding (Phase 8) DROPPED**
(proxy-only, real positioning data infeasible solo, risks re-reading the vol axis — the curse-of-dimensionality
waste). Each warm-started signal has a `NN-CHARTER-KICKOFF.md` (Stage-0 gate + header + mechanism + data plan +
scope) under `.planning/phases/`, and its data pulled to `data/processed/`:
- **04 Concentration** (FULL, proxy-scoped): French VW−EW leadership spread from `assets_daily.csv` (true
  cap-HHI needs paywalled constituents — do NOT fake with today's membership). No new fetch.
- **05 Diversification/absorption** (NARROW, lead-only): absorption ratio = PCA of `assets_daily.csv` panel; the
  LEAD is the whole justification — kill if it fails to generalize (dispersion-lead bar). No new fetch.
- **06 Credit/EBP** (FULL, residual only): `scripts/build_credit.py` → `credit_monthly.csv` (Fed EBP 1973+,
  restated monthly = PIT caveat) + `credit_daily.csv` (OAS proxies 1986+).
- **07 Funding** (NARROW binary flag, fold-into-Tail candidate): `scripts/build_funding.py` →
  `funding_weekly.csv` (STLFSI4/NFCI) + `funding_daily.csv` (CP−bill, SOFR−EFFR). LIBOR→SOFR splice hazard;
  OFR FSI funding sub-index = preferred PIT source, wire later.
- **09 Tail** (FULL, options-implied): `scripts/build_tail.py` → `tail_daily.csv` (CBOE SKEW 1990+ + VIX term
  slope). NO LONGER data-gated (realized-jump/bipower is the gated part, excluded). SKEW methodology-rebasing caveat.

Each is a WARM START, not a charter: next step per signal = expand the kickoff into a full charter (V/R
conditions worked with Adam) → build → one-look → dated sign-off. Boundary grep clean on all 5.

## OBJECTIVE RESTATED + INFRA HARDENED (2026-08-06)

**Adam restated the objective** (recorded durably in `.planning/REGIME-SENSOR-ARCHITECTURE.md` §"Objective
restatement", near the top): this is a **measurement system, not a prediction system**. The signals are EXPECTED
to be mostly known relationships (Engle 1982, Campbell–Shiller 1988, Kritzman 2011, Gilchrist–Zakrajšek 2012) —
that is the pass condition, not a failure. The research value is the point-in-time / causal / OOS / cross-regional
framework plus the **joint configuration** of orthogonal mechanisms. Edge hypothesis = *multiple validated
measurements beat any single indicator*, NOT "signal X predicts." Prohibited by name: timing labels · predictive
models without economic justification · weights optimized on historical returns · composites that maximize
backtests. Sequencing: **build all the sensors first**, defer the joint analysis to Phase 10 (can't know until
they exist). "Risk budgeting" was flagged back to Adam as the human's downstream question — stays out of the repo.

**Three real defects found + fixed (they were breaking reproducibility, the repo's whole selling point):**
- `requirements.txt` was missing `arch`, `matplotlib`, `scipy`, `statsmodels`, `scikit-learn` — all imported
  (`vol_descriptors.py:62`, `:113`) but unlisted. **A fresh clone could not run the vol signal.** Fixed + the
  no-backtest-engine decision recorded inline.
- Bare `pytest` was broken: it collected `archive/research-v1/scripts/significance_test.py` (matches `*_test.py`,
  imports a deleted `src` package). The "34 passed" figure came from `pytest tests/`. Fixed with a 3-line
  `pytest.ini` (`testpaths=tests`, `norecursedirs=archive scratchpad .venv`).
- **No look-ahead test covered the new spine.** The only causality tests (`test_jumpmodel.py:93`,
  `test_backtest.py:26`) guard the RETIRED jump-model program; `causal.py` / `vol_descriptors.py` had none.

**`assert_causal()` added to `scripts/causal.py` (D-20, the shared guard).** Property test: perturb the input
strictly after `cut`, assert every reading at ≤ `cut` is bit-identical; raises naming the first offending
column/date. Accepts a Series or a DataFrame (multi-input signals — credit/funding/tail). `tests/test_causal.py`
applies it to `ewma_vol`, `realized_vol`, `expanding_percentile`, `shock_half_life` (GARCH refit loop),
`vol_descriptors.build`, and `stockbond_corr` — **plus two deliberately-leaky functions (full-sample rank,
centered rolling window) that the guard MUST reject**, so the test cannot silently become a no-op. **42 pass.**
Every future signal's `build()` goes through this before its one-look.

**Tooling decision (recorded in `requirements.txt` + the architecture doc): NO backtesting engine** (vectorbt /
backtrader / zipline / bt). This repo emits measurements, not strategies; a sweep-over-returns affordance is the
exact thing that pulls a project toward "optimize until it forecasts." Permitted instead: `arch` (already used),
`statsmodels` (HAC/Newey–West — the valuation charter's registered inference), `scikit-learn` (PCA for absorption).

**REPRODUCIBILITY HARDENING (2026-08-06, Adam-directed: "reproducibility guaranteed and not leaking — that's the
whole purpose of this funnel").** Every test below exists because that exact failure ALREADY happened here:
- `scripts/data_manifest.py` → `data/processed/MANIFEST.csv`: sha256 + rows + columns + date span of all 19
  processed panels. French restates, FRED revises, SKEW gets rebased, yfinance back-adjusts — a filename is not
  a dataset identifier. The manifest is a RECORD, not a lock: refresh data → regenerate → commit, so the diff
  shows which panels moved.
- `tests/test_reproducibility.py` (6 tests): **(1)** every third-party import across `scripts/` is declared in
  `requirements.txt` (would have caught the missing `arch`); **(2)** `results/vol_descriptors.csv` carries the
  columns its producer emits (would have caught the stale artifact); **(3)** the Level-0 record is schema-valid;
  **(4)** every processed panel is in the manifest; **(5)** **every module defining `build()` is under
  `assert_causal` or explicitly excepted** — a new signal CANNOT skip the look-ahead guard by omission (D-18
  structural enforcement, same pattern as the boundary audit); **(6)** the guard registry names no dead modules.
- The registry test earned its keep immediately: it flagged `data_manifest.build()`, so that was renamed
  `build_manifest()` — `build()` in `scripts/` now unambiguously means "a signal construction."
- `CAUSAL_GUARD_EXCEPTIONS` is **empty** — the correct state; an entry there is a debt, not a design.

**DEAD-CODE PURGE (2026-08-06).** Deleted: `scripts/{build_report,regime_read,regime_panel}.py`,
`results/{regime_panel.csv, regime_read_latest.json, explore_dispersion_intl_japan.csv,
explore_dispersion_intl_europe.csv}`, `.planning/MONITOR-VALIDATION-SPEC.md` (spec for a monitor whose runner was
never built, on the retired K=2 label), `.planning/archive/V2-JUMPMODEL-PLAN.md` (a build plan, not a
pre-registration). **KEPT deliberately:** all six `.planning/archive/*-PREREG.md` + `CH3-D2-MEMO` — frozen
pre-registrations are the evidence the nulls were called honestly and in advance; stale-looking is what a
scientific record looks like.

**CARD BLANKED + LIVE CHAIN DELETED (2026-08-06, Adam-directed: "if we've proven the new thinking is better, make
it BLANK for now until we can actually combine all the signals into the regime card").** Verified first, in the
downstream repo: **nothing in `portfolio-manager` imports `src/regime.py` or calls `collect_regime_card()`**, and
its weekly-regime-brief cron was disabled 2026-08-04. The card was orphaned on BOTH ends — the "live contract"
was live only in the sense that a cron kept regenerating something nobody read.
- **`results/regime_card.json` is now a deliberate parked placeholder** (status/reason/replaced_by), not deleted:
  it stays blank until the observatory can fill it (Phase 10). **Never repopulate it with a single-label summary.**
- Deleted: `scripts/{live_label,regime_signal}.py`, `tests/test_regime_signal.py`,
  `results/{label_live.csv, label_live_run.log, live_label_meta.json}`,
  `.github/workflows/weekly-regime-card.yml`.
- **Last boundary-audit exception RESOLVED** — `gauge.position` was a leak from the retired state, so deleting the
  state deleted the leak (better than the planned `dwell_rank` rename + downstream coordination).
  `KNOWN_DEFERRED_EXCEPTIONS` is now empty. Both exception registries in this repo are empty.
- Consequence: the SPY-splice to-today bridge is gone; signal reads now end at the French vintage (2026-05-29).
  The new stack never used the splice. Any signal needing a to-today read brings its own causal splice.
- Downstream leftover (**other repo, not touched**): `portfolio-manager/src/regime.py` + the `REGIME_REPO_PAT` env
  in `daily-report.yml` are now dead weight there. Remove them in that repo; the PAT can then be revoked.

## JUMP MODEL ARCHIVED (2026-08-06) — `scripts/` is now signal-only

Adam: *"keep the jump model as history and parked as its own thing, something we learned, but remove it from any
of the signals."* Done.
- **`archive/jumpmodel-v2/`** — `jumpmodel`, `walkforward`, `backtest`, `run_config`, `synthetic_validation`,
  `validate_sensor`, `benchmark_detector` + `tests/{test_jumpmodel,test_backtest}.py`. **README records what was
  learned** (measurement validity ≠ decision value · causal filters lag 5–20d and that erases the daily-horizon
  edge · thresholding a continuous quantity piles error at the boundary and discards σ's graded info — the reason
  vol became continuous descriptors and "no single-word summary" is a standing rule · the evidence margin is not a
  portable confidence measure).
- **`archive/internals-gauge/`** — the `internals_*` set + `run_internals_prereg`. README records the **failing
  Europe placebo control** as the reason it is parked, and warns Phase 4 not to import it (Phase 4 warm-started a
  different construction).
- **`scripts/` now holds ONLY data builders + the signal spine** (verified: no live script imports anything
  archived). **26 tests pass.**

**The one decoupling that mattered:** `build_panel.py` used `jumpmodel.build_features` for its construction gate
(G4/G5 key off `dd10`). That function is a generic causal return descriptor, not jump-model machinery, so it moved
to `causal.py` as **`downside_features`** — **verified bit-identical to the original on the same input**, so
`market_daily.csv` is unchanged and the signed-off vol numbers do not move. This is what the "byte-identical
check" below was for; it is now DONE.

**Superseded — the caution below is resolved.** Kept for the reasoning only:

**WHERE I STOPPED, AND WHY (do not "finish the cleanup" casually).** The retired estimator —
`jumpmodel/walkforward/backtest/run_config`, `synthetic_validation/validate_sensor/benchmark_detector`, and the
`internals_*` set — is still in the tree, held up by ONE dependency: **`build_panel.py:34,88` calls
`jumpmodel.build_features`** when writing `market_daily.csv`, then truncates `.iloc[63:]` for feature burn-in.
Removing the feature join changes the panel's START DATE by 63 rows → shifts the expanding-percentile baseline →
**moves vol numbers that were signed off today.** Sequence to finish it properly:
1. Drop the feature join from `build_panel.py` but KEEP the `.iloc[63:]` offset (as a documented legacy constant).
2. Regenerate and assert `mkt_ret` is byte-identical to the committed panel — a diff of zero rows and zero values.
3. Only then delete the estimator + its tests; decide `internals_*` separately (it has a frozen prereg and a
   FAILING Europe placebo, and Phase 4 warm-started a different approach).

**CI GAP FOUND + FIXED — this one mattered.** `.github/workflows/tests.yml` installed only `numpy pandas pytest`
and ran only `test_jumpmodel.py` + `test_backtest.py` — the two suites for the RETIRED program. **The boundary
audit, the causal guard and the reproducibility tests never ran in CI.** Now: `pip install -r requirements.txt`
+ bare `pytest -q` (whole suite), and it runs on PRs too. Never narrow it to named files again.

- **49 tests pass** (was 50; the boundary audit had a per-JSON case for the deleted `regime_read_latest.json`).

**Phase-2 blocker found (no look spent):** `stockbond_corr.py:135` `build()` takes NO arguments — it loads its own
US panel, so it cannot feed `run_oos(build_region)`, which requires `build(r)`. It also re-implements
`realized_vol` / `expanding_z` locally instead of importing `causal.py` (D-20 drift). **Refactor onto the shared
spine is task 1 of Phase 2**, before the Japan/Europe run.

## FIVE CHARTER DRAFTS DELIVERED (2026-08-06) — parallel research agents, no look spent

Five agents ran the research + draft-charter stage for Phases 4/5/6/7/9 in parallel. Charter sign-offs, one-looks
and results sign-offs were deliberately NOT delegated — agents finalizing their own pre-registrations would make
the charter paperwork. Every draft is marked DRAFT — NOT FROZEN, NOT SIGNED. Boundary greps clean.

| Phase | Verdict | The deciding fact |
|---|---|---|
| **4 Concentration** | PROCEED **if respecified** | Kickoff's data verdict was WRONG — French publishes firm-count + avg-market-cap blocks free (verified, from 1926-08), so effective-N `1/Σsᵢ²` is buildable with no constituent list. VW−EW is the *derivative* of concentration; the phase's motivating claim is about the LEVEL. Spread-only ⇒ **DROP** (relabelled size factor). |
| **5 Absorption** | **DROP** | Only unique content is a ~1-month lead; the matched cross-region panel publishes ~2 months late (verified: 69-day lag in our own manifest) ⇒ unreadable live. Also no matched US cross-section exists and French publishes no international industry sorts. |
| **6 Credit (EBP)** | PROCEED, `research` ceiling | EBP is a **regression residual** refit monthly on the full sample ⇒ today's March-2008 value embeds coefficients fitted through 2026. No ALFRED vintages. Intl replication NOT feasible. |
| **7 Funding** | **DROP** (see conflict below) | Only PIT-clean, credit-free, unspliced series (SOFR99−SOFR) starts 2018. `cp3m` is 28.8% missing since 1997 with **endogenous** missingness — the Fed publishes only when trade data suffice, so it goes dark exactly when funding seizes and its silence reads as `intact`. All three composites rejected. |
| **9 Tail** | PROCEED, conditional, reduced priority | Measures **the PRICE of downside protection, not the probability of a crash** (Bollerslev–Todorov: the left/right asymmetry exists only under Q). Intl replication IMPOSSIBLE — no risk-neutral skew index for JP/EU at any tier. First signal `run_oos` cannot serve. |

**CONFLICT RESOLVED:** Phase 7 recommended folding itself into Phase 9; **Phase 9 refused, and is right.** Impaired
funding reduces dealers' capacity to supply protection, *raising its price* — funding is a candidate **cause** of
the tail signal's moves. Folding a cause into the price it moves destroys the ability to observe them disagreeing.
So funding is DROP, not fold, unless Adam wants it standalone-limited.

**REPO-WIDE FINDING — market data is NOT vintage-free.** Cboe's 2011 documentation gives SKEW all-time low/high
**101.09 / 146.88**; today's file gives **101.31 / 146.22** on the SAME dates. Silently revised, date and cause
unestablished. We had assumed only macro series had a revision surface. **`assert_causal` cannot catch this — it
guards the construction, not the data.** Mitigation shipped: `python scripts/data_manifest.py --check` recomputes
every panel's sha256 and diffs against the committed manifest (changed rows, moved spans, moved per-column spans).
A command, not a test — a test would fail on every legitimate refresh. Currently clean across 19 panels.
Related: a further SKEW recalculation is **announced but unscheduled** (Cboe determination 2025-07-17, no effective
date), so forward vintage capture should start now.

**Also caught: a defect in `data_manifest.py` from earlier the same day** — `first`/`last` recorded only the INDEX
span, so ragged-start wide panels read as though every column spanned the full range. That is exactly how the
false "OAS proxies 1986+" claim formed (`ig_oas`/`hy_oas` actually start **2023-08-07**; FRED serves a rolling
~3yr window of ICE BofA series). Manifest now records per-column first/last valid dates.

**THE OBSERVATORY SHRINKS, and that is the gate working (D-19 quality over quantity).** Plausible final set is
**5 signals, not 9**: volatility · stock-bond · valuation · concentration (respecified) · credit. Tail is
conditional on Adam accepting the price-of-protection reframe; absorption, funding and crowding are out.

**Decisions waiting on Adam:** (1) Phase 4 respecify-or-drop · (2) Phase 5 drop vs US-only descriptive ·
(3) Phase 7 drop vs standalone-limited · (4) Phase 9 reframe-and-proceed vs drop · (5) each charter's dated
sign-off before its build. Nine `[recommended]` items are marked inside the Phase 9 draft alone.

## NEXT ACTION (rewritten 2026-08-09)

**Adam's ruling 2026-08-09: keep the three dropped signals dropped (absorption · funding · crowding); take the
three half-built ones — concentration (4) · credit (6) · tail (9) — through to looks.** Each is further along than
"halfway": a complete draft charter *and* a committed working construction. What is missing is identical in all
three — **Adam's rulings on the `[recommended]` lines → dated charter sign-off → one frozen validation script →
one-look → cooling-off → dated results sign-off.**

**Read this before spending effort: two of the three pre-registered their own likely failure.**
- **Phase 4 V3 (resolution), decisive** — charter says R3 firing is *expected*: "the Mag-7 question is seven names
  *inside* one bucket." The 25 ME×BE/ME buckets may be blind to the very phenomenon that motivates the signal.
- **Phase 9 V4 (redundancy with vol), decisive** — "Registered prior: given Kozhan et al., R4 firing is likely,
  not a surprise." Skew and VIX are two nonlinear functions of one state vector.
- **Phase 6 V2 (vintage instability), decisive** — the only one whose odds are not pre-called against it.

So honest expected yield is **1–2 signals, not 3**; final observatory is realistically **3–4**, not the 5–6 in the
hub. Each failure would be a registered NULL, which is a legitimate output — but it is not more signals.

**Recommended order: credit → concentration → tail.** Credit has the best odds and its evidence base is already
harvested; concentration is cheapest (needs a monthly loader for `run_oos`, V5); tail's own charter names it "first
phase to cut if capacity is tight."

**Three consequences of the drops that were nowhere recorded until now:**
1. **Concentration was unblocked for free.** Its charter set a *binding precondition* — "a written de-confliction
   before Phase 5's charter opens, or one of the two drops." Absorption dropped ⇒ satisfied, no work.
2. **Credit's G4 is now unopposed, not confirmed.** It registered "the margin against Phase 7 is genuinely
   uncertain… re-run leave-one-out across the pair once both exist; neither is pre-designated the survivor."
   Funding dropped ⇒ that adjudication never happens, so the uniqueness claim is **untested**.
3. **Tail lost a confound test.** It registered absorption as "a real confound… registered for V7" (index skew
   embeds implied correlation, BKM 2003). Phase 5 dropped ⇒ that confound can only be *disclosed*, never tested.
   A cost of the drop, not a benefit.

**Still open and unrelated to the above: valuation's R9 disposition** — a decision with zero build work, blocking a
signal whose look is already spent. Both readings are written into the charter; do **NOT** rerun the bootstrap with
another seed or block length.

**Dropped-signal dead weight still in the tree** (Adam said drop them, not yet done): `scripts/build_funding.py` +
`data/processed/funding_{daily,weekly}.csv` (nothing imports them — only a comment in `test_causal.py:57` mentions
funding), and `.planning/ROADMAP.md` still lists Phase 7 and Phase 8 as open unchecked phases with Phase 9
declaring "Depends on: Phase 8". ROADMAP is GSD-managed, not hand-edited.

## NEXT ACTION (superseded — kept for the sequencing rationale)

**▶ After vol's dated sign-off:** pick the next signal to take from kickoff → full charter → build. All are warm:
- **Phase 2 (stock-bond intl OOS)** — un-gated (correction 2026-08-05): `scripts/build_intl_bonds.py` →
  `intl_bonds_monthly.csv` (JP 10y 1989+, DE Bund 1956+, monthly = the signal's honest frequency). Pair with
  monthly-resampled equity, run causal corr + hedge-behavior-by-state on JP+DE. Closest to done (US signal built).
- **Phase 3 valuation** (charter frozen 2026-08-03, sign-off pending) — first fully-new signal.
- **Phases 4/5/6/7/9** — warm-started (above); expand kickoff → charter first (D-15).
Recommend Phase 2 first (most built), then valuation. No auto-advance; each signal gets its own one-look + sign-off.

Vol validation PASSES; per Adam "if it passes move to the next signal" — but honor vol's dated sign-off +
cooling-off first. `scratchpad/garch_horserace.py` holds the rolling-vs-expanding evidence.

**Start building the layers (the signals).** Every signal MUST begin with a research charter (D-15, the six
pre-registration questions) BEFORE any implementation — the framework's own admission discipline. Then it runs
through: charter → research/build → validation (mechanism gate · confound · Japan/Europe OOS) → admission review
(3 non-compensatory axes + "why in front of an investor?") → cooling-off + dated sign-off → production.
New in the DoD (2026-08-06): **`assert_causal(build, data)` must pass before the one-look.**

## PHASE 2 IN PROGRESS (2026-08-06) — refactor DONE, charter FROZEN, sign-off pending

**Refactor done (no look spent).** `stockbond_corr.build(panel)` is now region-agnostic over a two-column
`(eq, bond)` schema and sits on `causal.py`; `expanding_z` promoted to a shared primitive; the local
`realized_vol` dropped in favour of the vol signal's own `ewma_vol` (so the orthogonality diagnostic compares
against the real signal — its value moves slightly; it is a diagnostic, no reject condition rests on it).
Guarded through the REAL `build()` in `test_causal.py`, plus a test that it cannot silently reach for the US
panel behind the caller's back. `results/stockbond_corr.csv` regenerated to match its producer.

**Charter frozen:** `.planning/phases/02-stockbond-signal/02-STOCKBOND-CHARTER.md` (v1.0, dated 2026-08-06,
boundary grep clean). **Sign-off pending — the OOS run does NOT start until Adam signs.**

**THE REGISTERED SCOPE LIMITATION (Adam's ruling 2026-08-06, before any look — do not lose this).** Both
international equity panels start **1990-07**; JGB starts 1989. **The OOS sample does not contain the 1970s–80s
inflation regime**, which is the era that makes the sign-flip mechanism interesting. Phase 2 can therefore test
the 2022 flip + by-state hedge behaviour on 1990–2026 ONLY. Consequence: **`production` is unavailable to this
phase; `research` is the ceiling.** Free deeper history does not exist — yfinance reaches only 1985 (Nikkei) /
1987 (DAX) and is price-only, mismatching the bond total-return leg; MSCI and Global Financial Data are paywalled.
Revisiting means buying data — a separate decision.

**Two registered guards against reading noise as a result:** V4 is a **power pre-check** that runs BEFORE any
by-state contrast is interpreted (a region with <24 months in any state → "insufficient coverage", not a weak
finding); R5 makes **INCONCLUSIVE** a distinct registered outcome. Primary metric is hedge-behaviour-by-state,
NOT average returns by state — the latter is confounded by the secular rate cycle (found 2026-08-02).

**Charter SIGNED OFF by Adam 2026-08-06** (both `[recommended]` lines confirmed: 24-month primary window;
equity-down = monthly return < 0). Stage-1 freeze only — not a positive claim, so no cooling-off applied.

## TASK 02 — ONE-LOOK SPENT 2026-08-06 → `results/stockbond_validation.txt`

`scripts/validate_stockbond.py`. Infra added first and causally guarded BEFORE the look: `build_monthly` +
`load_region_monthly` (monthly is the registered native clock — intl bond series are monthly, and the daily 126d
calendar mean hid the 2022 flip).

- **V4 power pre-check (ran FIRST, gates everything): ALL THREE REGIONS POWERED.** The underpowered risk did not
  materialize — Japan 242/69/95, Europe 160/119/129, US 246/123/381 months per state; every state clears the
  24-month bar. Japan/Europe spans start 1992-06 (24m burn-in off the 1990-07 panels).
- **V2 (PRIMARY, on-mechanism) — MONOTONE IN ALL THREE.** Fraction of equity-down months on which bonds ALSO fell:
  **US 28→44→56% · Japan 25→29→51% · Europe 27→32→48%** across intact→under_test→violated. **R1 and R2 not
  tripped.** *Honest wrinkle:* in Japan/Europe the intact→under_test step is small; nearly all discrimination sits
  at `violated`. The signal separates violated-vs-not more than it grades a smooth three-way ladder.
- **V5 window robustness — the soft spot, NOT a clean pass.** Sign agreement vs the 24m primary: 85/79/74% at 12m,
  91/88/85% at 36m; corr(12m,36m) 0.62–0.75. Stable at 24m and above, noisy below.
  **REGISTERED FOLLOW-UP (deliberately NOT run — it would be a second look):** test whether the 12m disagreement
  concentrates inside the neutral band, where ambiguity is already flagged. Register it before running it.
- **V3:** levels look like the same object across regions (means +0.09/−0.11/−0.02, ranges ≈ −0.8..+0.7). All
  three read **violated** as of 2026-05 (US +0.15, Japan +0.31, Europe +0.12).

## PHASE 2 CLOSED — stock-bond RESULTS SIGNED OFF by Adam 2026-08-07

Cooling-off observed (one-look 2026-08-06 → sign-off 2026-08-07), explicit and dated. Recorded in
`.planning/phases/02-stockbond-signal/02-STOCKBOND-CHARTER.md` §RESULTS SIGN-OFF with the V2–V5 verdict table;
R1–R5 none tripped.
- **Maturity DERIVED = `research`** — mechanism `pass` · measurement validity `H` · investment usefulness `H` ·
  **evidence maturity `M`**. The `M` is the registered scope limitation doing its job: the intl sample begins
  1990 and contains no inflation regime, so the sign-flip cycle is untested OOS. D-02c held under a strong V2.
- **Level-0 record emitted** — `results/stockbond_level0.json` via `scripts/stockbond_level0.py`, generated from
  `results/stockbond_monthly.csv` and schema-validated.
- **New artifact `results/stockbond_monthly.csv`** — the registered native clock was monthly but nothing committed
  was monthly; `stockbond_corr.py:main()` now writes it. Disclosed post-look addition: `build_monthly` gained
  `level_pctile` so the record can satisfy D-02b (no state without the number AND its rarity). No bar reads it.
- **Live read (2026-05-31):** 24m corr **+0.15**, **53rd percentile**, status **`violated`**, **51 months in**
  (since 2022-03). Status and rarity disagree by design — violated ≠ unprecedented, because the 1970s–80s were
  positive too. That disagreement is information; do not smooth it.
- `test_level0_records_are_schema_valid` now **globs** `results/*_level0.json` — a future signal cannot skip the
  boundary check by not being named in the test. **42 pass.**

## PHASE 3 (VALUATION) — CHARTER v1.1 SIGNED 2026-08-07, ONE-LOOK SPENT SAME DAY, RESULTS SIGN-OFF PENDING

**Charter respecified to v1.1 before signing** (two registered bars were not runnable; both checked against the
real sources, not assumed):
- **V5** — no free CAPE exists for Japan or Europe. French publishes the International Indices **twice**, with and
  without dividends, on the same universe, so `R_with − R_without = D_t/P_{t−1}` **exactly**; 12-month cumulation
  gives the canonical Campbell–Shiller D/P. `scripts/build_intl_valuation.py` → `intl_valuation_monthly.csv`,
  **612 months × 6 regions, 1975-01..2025-12**, local + USD. Six gates pass, incl. the two that matter: zero
  negative implied dividends, and both canonical out-of-US extremes present and correctly signed (Asia Pacific
  bottoms **0.69% in 1989-03**, the Japanese bubble; Europe ex UK **1.63% in 1999-11**, TMT).
- **V4** — total-payout yield DROPPED (no free net-buyback history). Panel = CAPE + P/D + **cap/GDP** (FRED
  NCBEILQ027S / GDP, added to `build_valuation.py`, G7 passes: 0.32 at the 1982 trough, 2.29 in 2025-12).
  **R5 (payout confound) recorded as an UNTESTABLE reject condition** — a named hole, not a silent one.

**ONE-LOOK RESULT (`results/valuation_validation.txt`): five of six bars clear; V6, the statistical bar, does not.**
- **V1/V2/V3/V4 clear on shape and sign.** log CAPE slope −0.0033 (1m) → −0.331 (5y) → **−0.610 (10y)**, R² 0.001
  → 0.140 → **0.257**, ~silent sub-1yr. Survives on **excess** returns (so it is not just the rate level — R4
  safe). **Stronger pre-1982 (β@60m −0.522) than in 1982–2021**, so it is not a creature of the rate decline.
  Reproduces on **P/D and cap/GDP**, and cap/GDP uses **no earnings at all**, so R6/Siegel does not trip.
- **V5 clears, heavily qualified.** The power pre-check earned its keep: at 10y every region has **eff N 3–4 ⇒
  INSUFFICIENT COVERAGE**, and the R² 0.36–0.79 sitting there is exactly the trap. At the only interpretable
  horizon (12m, eff N 49) the primary local specification is **correctly signed in all six regions**; the
  secondary USD-real specification **reverses in Scandinavia**, disclosed.
- **V6 FAILS. Bootstrap under the no-predictability null: p = 0.07–0.26 at EVERY horizon, both return objects.**
  ρ = 0.9965 and corr(return innovation, regressor innovation) = **+0.96** — near-tautological, since CAPE's
  numerator IS the price. The 10y cell's raw t = −23.7 / NW t = −4.93 looks overwhelming; that R² is reproduced
  by chance in ~10% of null paths. **Stambaugh removes 64–72% of the raw one-month slope.**
- **R9 is live.** With **~13 effective independent 10-year observations in 145 years**, the data cannot separate
  the Campbell–Shiller mechanism from a persistent-regressor artifact. Not an analysis defect — the actual
  information content, and exactly what R9 was written to detect. **Reading the t-stat as the answer is the error
  the charter existed to prevent.**

**Disposition is Adam's, after cooling-off. Two defensible readings are laid out in the charter's ONE-LOOK RESULTS
section** — (1) R9 trips, demote to a pure measurement with no forward-return claim (the shape volatility took), or
(2) weak-but-consistent across 20+ specifications, with the honest counter that those specifications share one
price series. **Do NOT rerun the bootstrap with another seed or block length to see if p crosses 0.05.**

## STEP 3 DONE (2026-08-09) — the observation contract + point-in-time history

Plan §5 shipped in four commits (`9f1153a`, `b745e25`, `0ccc951`, `e70b399`). **143 tests pass** (was 42).

- **`contracts/market-observation-v1.schema.json`** + `CHANGELOG.md` + 18 vectors (6 valid / 12 invalid, each
  invalid one naming the rule it breaks). Consumers **vendor** a pinned copy with a sha256 assertion — no Python
  import, so drift is a red test in the consumer. `tests/test_contract_conformance.py` runs every vector through
  BOTH the JSON Schema and `signal_output_schema.py` and requires the same verdict: two implementations of one
  rule set is only safe if something proves they agree.
- **`scripts/data_vintage.py`** — per-source `available_at` policy with a stated CONSERVATISM RULE (over-state the
  lag; getting it wrong optimistically is a look-ahead bug that shows up as better performance, never as an error).
- **`rarity.basis`** is now a required enum (`expanding` / `trailing_fixed` / `full_sample`), which resolves the
  cross-repo audit's **D2** at the interface. `full_sample` can never be `production`, enforced in both validators.
- **`observations/<signal>/history.ndjson`** — volatility **1187 records 1927-07-30..2026-05-29**, stock-bond
  **750 records 1963-12-31..2026-05-31**. Valuation deliberately absent while R9 is open.

**DEVIATION from plan §5.4, disclosed in `contracts/CHANGELOG.md` (2 reasons, both found while implementing it):**
(1) `<as_of>.json` **cannot express its own correction model** — §5.4 says a correction is "a new record with a
later `available_at`", but a path keyed on `as_of` holds exactly one record, so the first correction either
overwrites (killing the append-only guarantee stated in the same paragraph) or has nowhere to go. (2) Daily
granularity is **22× redundant**: 25,938 `as_of` dates resolve to **1,187 distinct `available_at` vintages**
because French publishes monthly, and vintage-mates are indistinguishable under the only legitimate filter.
So: one NDJSON log per signal on the **vintage grid**, lines in canonical JSON so `sha256(line)` equals both the
`MANIFEST.csv` hash and the hash `supersedes` cites. Same key + different content is **refused** — that refusal is
the guarantee the log exists for.

**These records are RECONSTRUCTIONS, not contemporaneous prints** (`provenance` column, `reconstructed`|`live`).
Data-derived numbers are causal — one code path, `build_record(df.loc[:as_of])`, and a test asserts reading +
rarity equal the committed descriptor at **every** `as_of`, which carries `assert_causal`'s guarantee through the
slice. The **specification is not** point-in-time: a 1930 record carries a maturity derived from a 2026-08-06
sign-off. Unavoidable, but it must be stated or a consumer reads `maturity: production` on a 1930 row and believes
it was earned then.

**Three live defects the work exposed** (none were hypothetical):
- `trend.level_percentile_change` was **NaN during burn-in** → serialized as bare `NaN`, invalid strict JSON no
  non-Python consumer can parse, while `direction` said `"flat"`, asserting flatness the data does not support.
  Both now `null`; `canonical_bytes` uses `allow_nan=False` so it fails loudly.
- `stockbond_level0` dropped on `corr` alone, so a record could be emitted mid-rarity-burn-in with
  `level_pctile` NaN — where every comparison in `_band()` is False and it **silently returned "very high"**.
- **`core.autocrlf` broke byte integrity.** No `.gitattributes` existed, so the SAME commit presented different
  sha256s on Windows vs Linux — which silently breaks the **vendoring mechanism plan §5.1 rests on**: every
  consumer would report contract drift that never happened. Now `contracts/** observations/** text eol=lf`.

## PHASE 6 (CREDIT) — V2's EVIDENCE BASE HARVESTED 2026-08-09 (no look spent)

`scripts/harvest_ebp_vintages.py` → **19 distinct EBP vintages, 2022-08-18..2025-12-03**, in
`data/vintages/ebp/` + a manifest regenerated from disk each run. V2 is the phase's decisive bar and had **no
evidence base in the repo**; the EBP is a residual refit monthly on the full sample (the Board: "the entire
history of the EBP may revise each month"), there are **no ALFRED vintages**, and Archive coverage is not
guaranteed to persist — so this was the one item with an irreversible cost to waiting.

**NO cross-vintage comparison was computed, deliberately** — revision magnitude, rank correlation and decile
agreement ARE V2 bars A/B/C, and V2 runs once, after sign-off, from a frozen script. The script fetches bytes and
records structural coverage only. There is no way to unspend a look.

**Findings from coverage inspection:**
- **git had already corrupted one piece of evidence.** The Fed served the 2025-06-12 capture with CRLF, and
  `autocrlf` normalized it into the blob: disk 39,244 bytes / 631 CRLF vs blob 38,613 / 0. Its sha256 attested to
  **git's edit, not the Fed's bytes**. Fixed with `data/vintages/** -text` — deliberately stronger than `eol=lf`,
  because these are a third party's originals and *any* normalization is a rewrite. **Never reformat evidence.**
  Caught only because the manifest records checksums and something compared them.
- Same capture ships a trailing bare `,,,` row (recorded as `dateless_rows=1`). It matters: **`build_credit.py:41`
  calls `pd.to_datetime` with no `errors=` guard**, so such a row becomes a NaT-indexed all-NaN row *without
  raising*. The live `credit_monthly.csv` is clean (642 rows, zero NaT) — the guard is absent, not satisfied.
- Schema **is** identical across all 19 (`date, gz_spread, ebp, est_prob`), confirming the charter.
- **Still missing: the 2026-03-23 capture** — a rate-limit casualty (the Archive began refusing connections after
  ~20 requests), not an absent capture. Re-run the script to pick it up.

**Methodological point for V2, not yet in the charter:** a capture date bounds publication from **above only** —
the Fed may have published days before the Archive crawled. So captures can prove the registered end-of-*t*+1 lag
is *conservative* (it is, in all 19) but cannot prove it is tight.

## PHASE 6 (CREDIT) — CHARTER FROZEN v1.0, SIGNED 2026-08-09 (`29e7c3d`). Build authorised.

Renamed off `-DRAFT` to match the signed-charter convention. All four open items ruled:
**PROCEED at a `research` ceiling** (registered pre-look, explicitly **not** reopenable on a strong V2 — the
"revisit the ceiling later" option was offered and rejected) · **R2 ⇒ DROP, not demotion**
(A ≤ 0.25 · B ≥ 0.95 · **C ≥ 0.90 decisive**; settled = months ≥ 12m before a vintage's last obs;
demote-to-live-reading-only rejected because it emits a level with no rarity, the first D-02b exception) ·
**numerics as drafted** (lag end-of-*t*+1 · bands 0.80/0.95 on the **percentile**, not the raw level · R4
\|Spearman\| ≥ 0.90 · 120m burn-in + trailing-60m second lens) · **vintage archive YES, done**.

**Three amendments recorded pre-signature, all no-look:**
- **G4 is UNOPPOSED, not confirmed.** The charter registered a leave-one-out against Phase 7 with neither
  pre-designated the survivor; **Phase 7 was dropped 2026-08-06**, so that adjudication can never run, and its
  absence is not evidence of distinctness. With the standing V4 caveat (the EBP regresses out a Merton DD, itself
  a function of equity vol, so part of any measured orthogonality is **manufactured by construction**), this
  signal's uniqueness is **untested**, not established. Do not read a favourable V4 as proof.
- **V2 wording corrected:** publication timing is **bounded from above** by captures, not "verified from" them.
  A capture date is when the Archive *crawled*. All 19 show data arriving earlier than end-of-*t*+1 allows, so
  the lag is demonstrably conservative but cannot be shown tight. **V2 must not treat capture dates as
  publication dates.**
- **The one-look script MUST handle dateless rows** — `build_credit.py:41` calls `pd.to_datetime` with no
  `errors=` guard, and one vintage ships a trailing bare `,,,` line, so it becomes a NaT-indexed all-NaN row
  without raising. The live panel is clean; the guard is absent, not satisfied.

**▶ NEXT: `scripts/validate_credit.py`, the single frozen one-look (V1–V6 → `results/credit_validation.txt`).**
Then overnight cooling-off, then a **separate dated results sign-off**. Two specification gaps must be closed
BEFORE it runs (legitimate as clarifications now, specification search if resolved after seeing values):
1. **Bar B aggregation across the 19 vintages is unspecified** — min (strictest), median, or pooled?
2. **Bar C is "share of settled months"** — pooled across all vintages, or per-vintage then aggregated?

## DATA REFRESHED + CORRECTION PATH BUILT (2026-08-10) — `d85e51d`, `ff22be0`. **147 tests.**

The read was 10 weeks stale. Refreshed the French panel → **2026-06-30**; gates G1–G5 and A1–A4 all PASS.

**LIVE READ (as of 2026-06-30, knowable 2026-07-15) — the two axes disagree for the first time:**
- **Volatility 15.21% annualised, 69.7th percentile** (was 12.03% / 51.9th), half-life 36.8d, **falling**
  (−0.059 over 10 sessions — June held a spike that was resolving by month-end).
- **Stock-bond +0.136, 52nd percentile, `violated`, 52 months in** (since 2022-03-31) — and the historical
  median for a major violated episode is **also 52 months**, max 129. Falling hard (−0.333 over 12 months)
  toward the +0.10 band edge.
- Read together: **volatility elevated while the usual shock absorber is not working.** In May both axes sat at
  ~52nd percentile and carried one piece of information between them. This is the "low-vol but fragile" case
  inverted, and neither axis alone produces it.

**THE APPEND-ONLY GUARD EARNED ITS KEEP ON FIRST CONTACT.** The refresh **restated 5 stock-bond and 2 volatility
readings at `as_of` dates already published**; the writer refused to overwrite. 4th-decimal magnitudes (0.1494 →
0.1492), so nothing quantitative moves — but it **falsifies the credit charter's claim** that credit is "the first
admitted signal with a vintage surface at all." **Every signal here has one**; credit's is the only one where the
mechanism (monthly full-sample refit of a residual) makes it first-order rather than rounding. Amended
struck-through in the charter — a signed pre-registration that quietly changes its factual claims is not one.

**Which control caught it matters.** `data/processed/MANIFEST.csv` **could not isolate it** — it records rows,
span and sha256, so a within-span value revision arriving *alongside* an append presents as a plain append. The
observation log located it per reading. **Panel-level and reading-level provenance catch different failures.**

**NEW — the correction path**, specified in the contract but never implemented (the writer could *detect* a needed
correction and refuse, but not *emit* one):
- `corrections_for()` appends a NEW record with `available_at = now` (the moment of rediscovery — using the
  original instant would both collide and backdate knowledge) and `supersedes` = the superseded sha256.
- `current_view()` = latest `available_at` per `as_of`. **This is the consumer's query**, and the reason
  superseded rows are kept rather than edited.
- Records append in `available_at` order, so the log reads in the order knowledge arrived. **Consequence: the
  newest LINE is no longer the current belief** — a correction found today lands after a routine record for a
  later `as_of` published weeks ago. Two tests encoded that false invariant and moved to `current_view`.
- **Two bugs, both caught by running it twice.** (1) Not idempotent: it compared each rebuilt record against the
  **original** row, which keeps its old content by design and so never stops differing — every run re-emitted the
  same corrections with a fresh timestamp. Now compares against `current_view` on a payload hash excluding
  `available_at`/`supersedes`. (2) `append()` was still handed the superseded originals, so it kept refusing.
  Verified: second run appends **0 new, 0 corrections**.

**▶ NEXT (unchanged): the four credit statistics in `scripts/validate_credit.py`.** Adam writes
`revisions`/`bar_a`/`bar_b`/`bar_c`; scaffolding self-tests 6/6; script refuses to run without
`--i-am-spending-the-one-look`. **The trap:** compute `causal_deciles` on the FULL vintage series *then* subset to
`settled_index(v)` — reversed, every reading is ranked against a shorter, later-starting history, and it looks
entirely plausible.

**Also queued:** write up **MI-004** (jump-model regime as a priced cross-sectional factor — `TESTING (ambiguous)`,
two constructions disagree, the Step-4 confirmatory test was never run; the only open ledger row with real upside
and nothing on the roadmap resolves it) · bring the ledger current (**MI-003 still says `VALIDATING`** with the
Japan/Europe OOS "owed" — it ran, Phase 2 closed 2026-08-07 at `research`; **valuation and credit have no rows**)
· this file's own CLAUDE.md claims "42 passing" and "sign-off pending" for stock-bond, and never mentions
`contracts/` or `observations/`.

## Signal-research discipline (full text in CLAUDE.md)

Causal-only; mechanism-first (orthogonality is a diagnostic, not the gate); confound-check every context stat;
out-of-hypothesis-sample intl confirmation before SUPPORT; one look + prereg + cooling-off + dated sign-off for
any positive claim; NO single-word regime summary; present, never conclude or allocate.
