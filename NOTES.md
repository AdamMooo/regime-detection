# Regime-Detection — Session Notes

## Status
A **market-signal research system** (see CLAUDE.md HARD BOUNDARY — market data → independent signals →
historical context → regime relevance → STOP; never allocation/decisions). The equity-ownership / allocation
program was removed from this repo 2026-08-02 (recoverable in git history). Branch: main | Last updated: 2026-08-03

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
- `regime_read.build()` is the one documented exception (retired jump-model read path).
- **50 tests pass.**

**Phase-2 blocker found (no look spent):** `stockbond_corr.py:135` `build()` takes NO arguments — it loads its own
US panel, so it cannot feed `run_oos(build_region)`, which requires `build(r)`. It also re-implements
`realized_vol` / `expanding_z` locally instead of importing `causal.py` (D-20 drift). **Refactor onto the shared
spine is task 1 of Phase 2**, before the Japan/Europe run.

## NEXT ACTION

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

**Phase 2 is next** (stock-bond intl OOS) — un-gated, data pulled (`intl_bonds_monthly.csv`, JP 10y 1989+, DE Bund
1956+). Order: refactor `stockbond_corr.build()` onto `build(r)` + `causal.py` (see blocker above) → charter
(no `.planning/phases/02-*` directory exists yet — Phase 2 has neither charter nor kickoff) → run → one-look.

## Signal-research discipline (full text in CLAUDE.md)

Causal-only; mechanism-first (orthogonality is a diagnostic, not the gate); confound-check every context stat;
out-of-hypothesis-sample intl confirmation before SUPPORT; one look + prereg + cooling-off + dated sign-off for
any positive claim; NO single-word regime summary; present, never conclude or allocate.
