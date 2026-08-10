# Cross-Repository Audit — Read-Only

Date: 2026-08-09 | Scope: §16 A–H of `SYSTEM ARCHITECTURE + RESEARCH CHARTER.md`
**Scope corrected 2026-08-09** — audits the **three internal repositories only**.
`vol-diagnostics` is an external, outward-facing research project and appears only in §2 as an
external research dependency, never as repository membership.

Status: **READ-ONLY. Nothing was modified, moved, deleted, or refactored in any repository.**

```
IN SCOPE (System Charter)          OUT OF SCOPE (external project)
  regime-detection      Market Intelligence      vol-diagnostics
  algo-trading-bot      Algo Trading             (options / vol / microstructure,
  portfolio-manager     Portfolio Management      public-facing, own governance)
```

---

## 0. Method, layout verification, and corrections

**Method.** Inspected actual source — import graphs, module docstrings, JSON artifacts, CI
workflows, git logs. Documentation was read *and cross-checked against code*, which is where
most findings came from.

**Layout on disk (verified).** Matches the corrected architecture:

```
C:\dev\
├── systematic-investing-research\
│   ├── regime-detection\
│   ├── algo-trading-bot\
│   ├── portfolio-manager\
│   └── SYSTEM ARCHITECTURE + RESEARCH CHARTER.md
└── vol-diagnostics\                    ← outside the private workspace
```

Three notes on the map as written in the brief:

1. `vol-diagnostics` was inside `systematic-investing-research\` at the start of this session
   and is now at `C:\dev\vol-diagnostics`. The physical boundary now matches the intended
   governance boundary. (An earlier draft of this audit described it as internal; that draft
   was written against the older layout.)
2. The three internal repos are at `C:\dev\systematic-investing-research\<repo>`, **not**
   `C:\dev\<repo>` as the brief's "CORRECT REPOSITORY MAP" section lists. The brief's own tree
   diagram is the accurate one.
3. The charter file is `SYSTEM ARCHITECTURE + RESEARCH CHARTER.md`, not `SYSTEM_CHARTER.md`.
4. `C:\dev\CLAUDE.md`'s repo/venv table still lists all four repos at their old `C:\dev\<repo>`
   paths and is now wrong for three of four rows. Flagged, not fixed — read-only phase.

**Repo liveness** (last commit):

| Repo | Last commit | Scheduled jobs |
|---|---|---|
| regime-detection | 2026-08-07 | none (`tests.yml` is `workflow_dispatch` only) |
| portfolio-manager | 2026-08-07 | daily brief 11:30 UTC Mon–Fri; weekly brief **disabled** |
| **algo-trading-bot** | **2026-07-27** | 3 crons in `trading.yml` (report + two trade windows) |

The algo repo has been quiet for 13 days while the others moved, and its last 12 commits are
all automated `chore: bot run`, not authored work. It is the only repo where scheduled capital
movement outlives active development.

---

## 1. `regime_card.json` — is it A (information transport) or B (decision contract)?

**Verdict: A — an information transport contract. Not a boundary violation. Currently inert on
both ends.**

**Producer.** `regime-detection/results/regime_card.json` is a deliberate blank:

```json
{ "status": "parked", "parked_since": "2026-08-06",
  "consumer_note": "No downstream code path currently reads this file. Do not repopulate
                    it with a single-label summary: a one-word regime summary destroys the
                    multi-signal vector this system exists to preserve." }
```

Parked because `results/detector_benchmark.csv` showed a plain causal volatility threshold with
hysteresis matching or beating the K=2 jump-model state label on precision, recall and BAC at
both bear datings, with shorter detection lag — and thresholding destroyed the graded
information in σ.

**Consumer.** `portfolio-manager/src/regime.py:16` `collect_regime_card()` exists and is
**imported by nothing**. No `from src.regime` / `import regime` appears anywhere in
portfolio-manager source; `scripts/daily_report.py` never calls it.

**Against your A/B test.** When populated, the card carried a CALM/STRESSED **vol state** — a
measured condition. It never contained `reduce_equity`, `portfolio_action`, a weight, or a
trade. So: case A.

More importantly, the replacement contract is stronger than the card ever was.
`regime-detection/scripts/signal_output_schema.py` is an **executable** boundary — a closed
allowlist of Level-0 fields plus a denylist that bans `weight, allocation, exposure, position,
sizing, order, trade, buy, sell, tilt, sleeve, overweight, underweight, recommendation, action,
score, rating, target`. `validate()` raises on any of them at any nesting depth. The shipped
`results/vol_level0.json` conforms. This is the single best artifact in the ecosystem and it is
code, not prose.

**One correction to the record.** `portfolio-manager/ARCHITECTURE.md:303` asserts the seam is
live — "`collect_regime_card()` → optional row in the daily brief ✓", with a check mark. That
claim is false against the current tree.

**On Unified Briefs.** Under the corrected architecture the question resolves cleanly: no
Unified Brief exists in code, and nothing about building one requires `vol-diagnostics` to join
the internal stack. The interface work is entirely internal — it is regime-detection's Level-0
record, extended and given a history (§F). Any vol-diagnostics contribution arrives later as a
*validated finding*, not as a repository dependency.

---

## 2. External research dependency — `vol-diagnostics`

Documented here as a relationship, not as membership. **Not audited, not modified.**

### Coupling: none in code, in either direction

| Direction | Code coupling | Evidence |
|---|---|---|
| internal → vol-diagnostics | **zero** | No import, no path reference, no data read in any of the three repos |
| vol-diagnostics → internal | **zero** | No import, no `C:\dev\...` path into the internal repos, no `regime_card.json` read |

`vol-diagnostics/app.py:290 _render_regime_cards()` is an unrelated per-ticker options card —
name collision with `regime_card.json` only.

### The real relationship: one-directional research provenance, in prose

`vol-diagnostics/research/risk-environment-conditioning.md:4` is explicit:

> "Cross-project provenance: the load-bearing lessons below were paid for in
> **regime-detection** and transfer directly. This note is the vol-diagnostics-specific
> synthesis. Keep the two in sync if either moves."

Four specific lessons flow **internal → external** there: the ~2–4 orthogonal-axis dimensionality
finding; the Stambaugh/Hodrick overlapping-observation correction to base-rate N; the killed
CALM/STRESSED label as the reason to ship payoff *shape* rather than a single state
(`:67`); and hedge-behavior-by-state replacing the confounded average-return-by-state
(`:84`).

Note the direction. Today the flow is **regime-detection → vol-diagnostics** (methodology
lessons travelling outward), which is the opposite of the eventual intended flow
(validated findings travelling inward). That is fine and probably healthy, but it means the
inward interface has never been exercised.

### Governance items worth flagging

- **`portfolio-manager/portfolio-sprint/`** is a career-portfolio initiative ("turn the three
  personal github.com/AdamMooo repos into presentable projects", deadline 2026-08-25) living
  inside the investment-portfolio governance repo. It contains candid assessments of
  **regime-detection**, **vol-diagnostics**, and **portfolio-manager**, explicitly "kept out of
  the repos" — while sitting inside one of them. It also groups the repos a *fourth* way
  (regime-detection + vol-diagnostics + portfolio-manager, no algo). Under the corrected
  architecture this is misplaced twice: private review material about a sibling internal repo,
  and about the external public project, inside the Portfolio Management system. It is also a
  naming collision — "portfolio" here means career portfolio, not investment portfolio.
- **The external project is clean of private content.** No IPS, no account data, no allocation
  rules, no Questrade references appear in `vol-diagnostics`. The constraint you stated is
  currently satisfied.

### Recommended posture

Keep them separate. If a vol-diagnostics finding should eventually inform Market Intelligence,
it enters as a **validated finding under regime-detection's own charter** — mechanism gate,
preregistration, cooling-off, dated sign-off — not as an import, a shared package, or a data
dependency. The public project's implementation must remain swappable to zero without the
internal stack noticing.

---

## A. Architecture map

### regime-detection — Market Intelligence

Not a Python package. Flat modules under `scripts/` importing each other directly
(`from causal import expanding_percentile`), so it must run with `scripts/` on the path.

```
data builders          build_{panel,assets,intl_panel,intl_bonds,credit,funding,tail,
(FRED · Ken French ·    concentration,valuation,trend_proxy,ohlc_panel}.py
 Fed EBP · yfinance)   → data/processed/*.csv + MANIFEST.csv (sha256 · shape · date-span)
        ↓
shared causal spine    causal.py — ewma_vol(λ=0.94) · realized_vol · expanding_percentile
                                 · expanding_z · downside_features · assert_causal
        ↓
per-signal build()     vol_descriptors · stockbond_corr · valuation · concentration
                       · credit_ebp · tail_skew
        ↓
one-look validation    validate_{vol,valuation,stockbond}.py → results/*_validation.txt
                       run_oos.py — generic Japan/Europe out-of-hypothesis-sample harness
        ↓
Level-0 record         vol_level0.py → results/vol_level0.json
                       ← schema-validated by signal_output_schema.py
```

Signals: **volatility** production, signed off 2026-08-06. **stock-bond correlation** built,
sign-off pending (Japan/Europe OOS owed). **valuation, concentration, credit EBP, tail skew**
— descriptors built, unsigned. Archived with written post-mortems: `archive/jumpmodel-v2/`,
`archive/internals-gauge/`, `archive/research-v1/`, plus two dropped signals (absorption,
funding).

7 test files, 26 claimed passing, including `test_boundary_audit.py`, which scans **import
lines** to prove no script reaches for an allocation system.

### algo-trading-bot — Algo Trading (two disjoint halves)

**Live spine (~45KB) — the actual bot:**

```
main.py ──▶ RiskManager (20% DD halt) ──▶ RegimeDetector ──▶ DataFetcher
        ──▶ EVRanker (12-1/6-1 momentum ÷ 63d vol) ──▶ equal-weight 1/N
        ──▶ AlpacaExecutor (sell-first, then buy) ──▶ outputs/bot_state.json
```

Universe: 8 ETFs (`config.py:63`). Cadence 21/14/7d by regime + immediate flip on regime
change. Sizing: pure 1/N; HIGH_VOL concentrates to top-4 by EV.

**Research mass (~300KB) — everything else:**

```
regime/           2-HMM gauge (VolHMM + BreadthHMM), entropy-weighted, 8 frozen artifacts
backtest/hmm/     12 modules, ~220KB — directional 3-state detector program:
                    features(oracle labels, 13 features) · model(causal decode + Hungarian)
                    · harness(Gupta et al. walk-forward) · detection_eval · oracle_audit
                    · lens_probe · state_discovery · subhmm_selection · deep_feature_search
                    · nightly_detector_backtest · detection_plots · detection_report
backtest/overlay/ 11 modules, ~55KB — two generations of signal→equity-curve research
backtest/regime_replay · regime_diagnostics · regime_vol_eval
scripts/daily_regime_report.py   33KB market-read email
```

`.holdout-quarantine/HOLDOUT.lock` — a genuinely good artifact: a sealed final holdout.

### portfolio-manager — Portfolio Management

```
Questrade (live truth) ─▶ config.py (holdings at import) ─▶ src/portfolio/_legacy.py
                                                         ─▶ src/instruments.py (classify)
                                                         ─▶ src/governance.py (compliance)
                                                         ─▶ scripts/daily_report.py (46KB)
src/data_provider.py   OpenBB + FRED + Finnhub + yfinance
src/market_sentiment.py  33.9KB — FRED macro snapshot + assess_market_regime()   ← see §D6
src/cache.py  holdings_watch.py  performance.py  mailer.py  news.py  regime.py(orphan)
```

`MANDATE.md` holds the IPS (US 55 / Cdn 15 / DevIntl 15 / EM 5 / Spec 5 / Crypto 5 / Cash 0,
with ranges). `ARCHITECTURE.md` is explicitly normative with five invariants. **The Policy
Object does not exist in code** — the self-declared missing core.

---

## B. Responsibility map

| Component | Actual responsibility | Correct repo? |
|---|---|---|
| **regime-detection** | | |
| `scripts/build_*.py` | 11 Infrastructure (data acquisition) | ✅ |
| `causal.py` + `assert_causal` | 11 Infrastructure (causality guarantee) | ✅ ecosystem asset |
| `vol_descriptors`, `stockbond_corr`, `valuation`, `concentration`, `credit_ebp`, `tail_skew` | 1 Market observation + 2 modeling | ✅ |
| `run_oos.py`, `validate_*.py` | 2 Market modeling (validation) | ✅ |
| `signal_output_schema.py` | 10 Reporting/interface (boundary enforcement) | ✅ **should become the shared contract** |
| `archive/*` | 12 Dead — with written post-mortems | ✅ correctly parked |
| **algo-trading-bot** | | |
| `main.py` allocation loop | 6 Trading strategy | ✅ |
| `execution/alpaca_executor.py` | 9 Execution | ✅ |
| `core/risk_manager.py` | 8 Risk/governance (drawdown halt) | ✅ |
| `strategy/ev_ranker.py` | 5 Signal research → 6 strategy | ✅ |
| `backtest/{data_loader,metrics}.py`, `overlay/{engine,splitter}` | 11 Infrastructure (backtest) | ✅ |
| `backtest/overlay/{signals,aggression,strategy,comparison,signal_factory,cross_asset_baseline}` | 5 Signal research | ✅ |
| `regime/` (2-HMM gauge) | **4 State estimation** | ❌ Market Intelligence |
| `backtest/hmm/` (12 modules) | **3 Dimension discovery + 4 state estimation** | ❌ Market Intelligence |
| `backtest/regime_{replay,diagnostics,vol_eval}.py` | **4 State estimation + validation** | ❌ Market Intelligence |
| `scripts/daily_regime_report.py` | **10 Reporting (market read)** | ❌ Market Intelligence |
| `docs/research_spine.md` | **7 Portfolio translation** (Cdn ETF crash-defense ladder) | ❌ Portfolio Mgmt |
| `.planning/spikes/{008,009,010}` | 12 Dead — import `strategy.vol_target`, deleted Phase 47 | ❌ non-runnable |
| **portfolio-manager** | | |
| `config.py`, `src/questrade.py`, `src/portfolio/_legacy.py` | 11 Infrastructure + portfolio state | ✅ |
| `src/instruments.py` | 7 Portfolio translation (exposure classification) | ✅ |
| `src/governance.py` | 8 Risk/governance | ✅ |
| `scripts/daily_report.py` | 10 Reporting | ✅ |
| `src/market_sentiment.py::{assess_market_regime, get_risk_summary, get_composite_macro_score, get_fear_greed_proxy}` | **2 Market modeling + 4 state estimation** | ❌ Market Intelligence |
| `src/regime.py` | 10 Interface — **orphaned, zero callers** | ⚠️ dead |
| `scripts/weekly_regime_brief.py` | 12 Blank template, workflow disabled | ⚠️ parked |
| `portfolio-sprint/` | 12 Career-portfolio initiative + cross-repo review material | ❌ not a PM concern (§2) |

**Summary.** The boundary holds almost perfectly in two repos and is broken in one direction
only: Market Intelligence machinery has accumulated inside `algo-trading-bot` (~300KB of ~380KB
non-test source) with a smaller pocket inside `portfolio-manager` (`market_sentiment.py`, 34KB
+ a 35KB test file). **Nothing flows the wrong way** — no Market Intelligence component
contains an allocation decision, and only `algo-trading-bot` places an order.

---

## C. Dependency map

**Code-level coupling between the three internal repos: zero.** No shared package, no
submodule, no vendored source, no common requirements, no imports.

The only cross-repo mechanism ever built:

```
regime-detection/results/regime_card.json
        │  (HTTP GET, GitHub contents API, PAT-authenticated)
        ▼
portfolio-manager/src/regime.py::collect_regime_card()   ← ORPHANED: no caller
```

Both ends inert (§1). **The three-repository ecosystem is currently three disconnected
systems.** `algo-trading-bot` has no connection to either sibling — not even a dead one.

Non-code dependencies that do exist:

| Kind | Detail |
|---|---|
| **Shared vocabulary, no shared definition** | "regime," "volatility," "percentile/rarity," "state" appear in all three repos meaning different things (§D). |
| **Manual/human workflow** | The human reads independent emails (algo regime report; PM daily brief; PM weekly, parked). Integration happens in Adam's head. |
| **Shared external data** | FRED (all three), yfinance (all three), each with its own client. |
| **Filesystem escape hatch** | None among the three. (The one instance in the ecosystem, `observation.py` writing to `C:\dev\_daily`, lives in the external project.) |
| **Documented-but-unbuilt** | `portfolio-manager/ARCHITECTURE.md:137-176` specifies the future "assumption ledger" and explicitly states the interface is DEFERRED with no `INTERFACE-CONTRACT.md`. Correct call; worth honouring. |
| **Cross-repo review material** | `portfolio-manager/portfolio-sprint/assessments/regime-detection.md` — private assessment of a sibling repo, stored in the PM repo (§2). |

---

## D. Duplication map

Classified as the brief asked — genuinely shared infrastructure vs accidental duplication vs
intentionally independent research implementations.

### D1. Volatility estimation — 4 implementations across 2 repos — **intentionally independent, leave alone**

| Where | Math | Purpose |
|---|---|---|
| `regime-detection/scripts/causal.py:21` | EWMA λ=0.94, burn-in-seeded, ×√252 | RiskMetrics level, causal-guarded |
| `regime-detection/scripts/causal.py:40` | rolling(21).std × √252 | lightly-smoothed input for half-life estimation |
| `algo-trading-bot/backtest/regime_vol_eval.py:41` | rolling std × √252, with a `forward=True` mode | forward-RV validation target |
| `algo-trading-bot/strategy/ev_ranker.py` | 63d std, **not** annualized | denominator of a momentum ratio |

Different estimators for different questions, each documented. **Do not consolidate** — it
would couple two repos to buy nothing.

### D2. "How unusual is this?" — 2 incompatible definitions — **the real problem**

| Where | Definition |
|---|---|
| `regime-detection/scripts/causal.py:50` | `expanding().rank(pct=True)` — expanding window, causal by construction, explicitly chosen so a full-sample rank cannot leak the future distribution into today's reading |
| `portfolio-manager/src/market_sentiment.py:222` | `percentileofscore` over a fetched history window |

Both are called "percentile." They answer different questions and are not comparable. Every
future interface transmits a `rarity` field — this is exactly that field. **The gap is a shared
definition (one page), not shared code.** (The external project adds a third variant — a fixed
2520-session trailing window — which is why the definition must travel *with* the number.)

### D3. Causal HMM posteriors — **accidental duplication, already drifted** (intra-algo)

`algo-trading-bot/regime/hmm_base.py:52` and `algo-trading-bot/backtest/hmm/model.py:191`. The
copy's own docstring says *"Verbatim copy of regime/hmm_base.py::causal_posteriors — do NOT add
a regime/ import."* It is **not verbatim**: the copy added zero-row renormalization
(`model.py:203-208`) the original lacks. The divergence is undocumented.

### D4. Backtest equity-curve builders — **accidental** (intra-algo)

`backtest/overlay/engine.py` docstring: *"Re-implemented from
backtest/hmm/harness.py::_build_equity_curve (lines 342-386)."* Two canonical leak-free
equity-curve builders in one repo, each claiming canonical status.

### D5. Data acquisition — **heavy intra-algo duplication; fine across repos**

Inside `algo-trading-bot` alone: FRED clients in `regime/data.py`, `backtest/hmm/harness.py`,
`scripts/refresh_discovery_snapshots.py`, `scripts/regenerate_hmm_fixtures.py`; yfinance in
those plus `backtest/data_loader.py`, `backtest/regime_replay.py`, `regime/ensemble.py`,
`scripts/download_etf_cache.py`, `backtest/hmm/features.py`.

`regime-detection` did this correctly — `build_intl_bonds.py:45 fred_series()` is imported by
`build_credit.py` and `build_funding.py`. One implementation, reused.

Cross-repo data duplication is **not** a problem: different universes, frequencies, vendors.

### D6. Regime/state detection — **3 independent systems inside 3 repos; only one is defensible today**

| Where | What | Status |
|---|---|---|
| regime-detection | continuous causal descriptors; **explicitly retired** the state label | production (vol) |
| algo-trading-bot | 2-HMM gauge (LOW/MED/HIGH_VOL) + a stalled 3-state directional detector program | gauge frozen; detector stalled |
| portfolio-manager | `assess_market_regime()` → "High Recession Risk / Late Cycle / Expansionary / Expansionary — Mixed Signals" | **dead in production, live code** |

The portfolio-manager instance deserves attention: `scripts/daily_report.py:179` states
*"Deliberately does NOT call assess_market_regime() or get_risk_summary()"* — so 34KB of
market-regime classification plus a 35KB test file sits in the governance repo, fully tested,
called by nothing but tests. It is precisely what `ARCHITECTURE.md:264` says must never live
there.

**This is the ecosystem's most consequential duplication**: three answers to "what state is the
market in," in three repos, with no shared definition and no shared evidence base — while the
repo that owns the question has published a benchmark rejecting the labelled-state framing
altogether.

### D7. Email/report builders — 3 independent (33KB + 46KB + mailers)

Different content, different infra, different repos. **Accidental but low value to unify.**

---

## E. Algo cleanup assessment

### KEEP — essential (~45KB, the real bot)

`main.py` · `config.py` · `core/risk_manager.py` · `data/fetcher.py` ·
`execution/alpaca_executor.py` · `strategy/ev_ranker.py` · `backtest/data_loader.py` ·
`backtest/metrics.py` · `backtest/overlay/{engine,splitter,baselines,strategy,aggression}.py` ·
`.holdout-quarantine/HOLDOUT.lock` · the corresponding tests.

**The charter's spine is missing a segment.** It specifies
`… ORDER → ALPACA → EXECUTION → RECONCILIATION → LOGGING`. Logging exists. **Reconciliation does
not.** `main.py::_execute_rotation` submits orders and returns (`main.py:372-388`) — it never
polls order status, never verifies fills, never checks realized position against target on the
next cycle. A partial fill, a rejected buy after a successful sell, or a stale quote leaves the
book silently off-target until the next cadence window. There is also no cost or slippage model
anywhere in the live path. This is the one gap that is *not* excess modelling complexity — it is
missing execution infrastructure, in the only repo that moves real money.

### SIMPLIFY — useful but overcomplicated

- **`backtest/overlay/` (11 modules)** holds two overlapping generations: the Phase 55–59
  "discovery loop" (`signals`, `aggression`, `strategy`, `comparison`, `report`) and the later
  Wave-A non-HMM pivot (`cross_asset_baseline`, `signal_factory`, `model_candidates`).
  `comparison.py` (18KB) implements a sweep whose real-data orchestration its own docstring
  defers to *"Plan 03 (wave 2)"* — never built. `report.py` writes `DISCOVERY_REPORT.md` for a
  Phase 59 that `.planning/STATE.md` records as "Not started." Two generations, neither
  finished.
- **`config.py`** carries two universes (8-ETF live + 15-ETF research), and
  `baselines.py:19 equal_weight_16etf_returns()` still bears a 16-ETF name while iterating the
  8-ETF list.
- **Documentation describes three mutually inconsistent architectures.** `CLAUDE.md` says a
  16-ETF universe; `config.py` has 8; the hub says 8. `STATE.md` references
  `backtest/discovery_loop/` and `backtest/repro_gupta/` — **neither directory exists**; the
  real code is `backtest/overlay/` and `backtest/hmm/`. Anyone orienting from the docs, human
  or agent, will be wrong about the codebase.

### REMOVE / DEPRECATE

- `.planning/spikes/{008,009,010}` — import `strategy.vol_target`, deleted in Phase 47.
  Non-runnable.
- `backtest/hmm/{detection_plots,detection_report,generate_fold1_posteriors}.py` — artifact
  emitters for Phase 50/51, a concluded milestone.
- `docs/research_spine.md` — specifies a Canadian ETF crash-defense engine (VFV.TO / QQC.TO /
  VDY.TO / VIU.TO / VEE.TO → CSAV.TO) with a 1.0 / 0.5 / 0.0 exposure ladder, hysteresis and
  re-entry gates. That is a **portfolio policy document** in the algo repo, duplicating
  `portfolio-manager/MANDATE.md`'s concern — and it is still cited by the hub as "current
  product direction."

### EXTRACT CONCEPTUALLY — Market Intelligence living in the trading repo

`regime/` (2-HMM gauge, 8 artifacts) · `backtest/hmm/` (~220KB, 12 modules) ·
`backtest/regime_{replay,diagnostics,vol_eval}.py` · `scripts/daily_regime_report.py` (33KB).

Roughly **300KB of ~380KB non-test source**. Every one answers "what state is the market in,"
not "can this be traded."

**But do not simply move it — and this is where I disagree with the obvious plan.**

`regime-detection` has *already run this experiment and closed it.* Its
`results/detector_benchmark.csv` head-to-head found a plain causal volatility threshold with
hysteresis matched or beat the K=2 jump-model state label on precision, recall and BAC at both
bear datings, with shorter detection lag — and thresholding destroyed σ's graded information.
Its `CLAUDE.md` now forbids single-label summaries outright. Relocating algo's HMM machinery
into regime-detection would import, into the repo that rejected labelled states, the largest
labelled-state codebase in the ecosystem.

Three defensible outcomes, in my order of preference:

1. **Close it with a written verdict and delete it.** The evidence already inside the algo repo
   points this way: MacroHMM removed as noise (+1.55% in-sample → +0.37% OOS); the gauge
   validated as an excellent vol *nowcaster* and explicitly not a forecaster; the directional
   program stalled mid-milestone since 2026-07-06.
2. **Re-ask the question inside regime-detection under its charter** — mechanism gate,
   preregistration, cooling-off, dated sign-off, Japan/Europe OOS. If the directional-state
   question is genuinely still open, that is where it earns an answer.
3. **Quarantine it in place with a dated stop condition.**

What is not defensible is leaving ~300KB of unlabelled market-modelling inventory in the repo
that submits orders, described by three documents that disagree with each other and with the
code.

---

## F. Interface proposal

**Do not invent a new contract — the right one exists in prototype.** Extend
`regime-detection/scripts/signal_output_schema.py` + the Level-0 record into the shared
interface. It already enforces information-vs-decision *in code*.

```
        regime-detection  (Market Intelligence)
                 │
                 ▼
        Level-0 records — one JSON per signal, per as-of date
        + MANIFEST (sha256 · date-span · spec_version)
                 │
     ┌───────────┴───────────┐
     ▼                       ▼
algo-trading-bot        portfolio-manager
may consume maturity ∈  may consume maturity = production only
{research, production}  for anything that changes behavior;
— it is a laboratory    research renders as prose context
     │
     └──▶ EVIDENCE records (never signals, never states) ──▶ research ledger

vol-diagnostics (external) ──▶ validated findings ──▶ re-tested under regime-detection's
                                                       charter before entering as a signal
```

### What crosses (information)

Existing validated Level-0 fields: `signal` · `assumption_monitored` · `clock` · `reading` ·
`rarity` · `trend` · `extreme_conditions` · `cross_signal_relationships` ·
`assessment{mechanism, measurement_validity, investment_usefulness, evidence_maturity}` ·
`maturity` · `spec_version`.

Two fields to add, both absent today and both necessary:

- **`available_at`** — when the reading could actually have been known, distinct from `as_of`.
  Without it, the charter's §6 question — *exactly what information was available at the
  decision timestamp?* — is unanswerable.
- **`rarity.basis`** made mandatory and enumerated: `expanding` | `trailing_fixed(N)` |
  `full_sample`. Fixes §D2 at the interface rather than in the code.

### What must not cross (decisions)

Already enforced by the `FORBIDDEN` denylist. Nothing to design.

### Consumption asymmetry — the charter's point, made executable

The algo repo *should* be allowed research-grade readings; a research-tier signal is a
legitimate hypothesis input for a laboratory. The portfolio repo should not — it may wire a
field into a **rule** only once that field is `production`-tagged, with research-grade fields
rendering as context. This is already written at `portfolio-manager/ARCHITECTURE.md:174` and
should become a clause of the versioned contract rather than a per-repo convention.

### Reverse flow: algo → Market Intelligence

Not a signal. An **evidence record**: `{hypothesis_id, test_design, fold_dates, n_variants,
result, decision, reason}`. It must never write back a state or a label — that is precisely the
circular-validation path §5 of the charter warns against.

### The prerequisite that blocks everything else

**Nothing in the ecosystem is point-in-time addressable.** `regime-detection/results/*.csv` are
overwritten in place. `algo-trading-bot`'s `regime_labels.parquet` is stale (ends 2026-06-16 per
its own `CLAUDE.md`). A consumer can ask *"what does Market Intelligence say now?"* but not
*"what did it say on 2024-03-15?"*

An interface that transmits only a current reading supports a report, not research. Algo cannot
backtest against Market Intelligence output; PM cannot evidence what it knew when. **This is the
interface's prerequisite, not a later refinement.**

---

## G. Research pipeline

### Current reality, per repo

**regime-detection — the most complete, and genuinely rigorous:**

```
research charter (6 preregistered questions, BEFORE any code)
  → build()  → assert_causal(build, data)     ← perturb-the-future property test
  → mechanism gate (a structural reason it survives being known)
  → confound check → Japan/Europe out-of-hypothesis-sample
  → ONE look, prereg + overnight cooling-off + explicit dated sign-off
  → Level-0 record + derived maturity tag
```

Enforced structurally, not by convention: `tests/test_reproducibility.py` fails on any new
module defining `build()` that is not registered under the causality guard — so the guard cannot
be skipped by omission. `RESEARCH-RECORD.md` (1120 lines) is the ledger, in narrative form, and
it visibly self-corrects (the 2026-07-30 entry retracts a "spanned, closed cheaply" verdict as
an over-claim and re-escalates the hypothesis).

**algo-trading-bot — real discipline, stalled pipeline.** `SWEEP_PREREG.md` locks fold
boundaries with an amendment log; `.holdout-quarantine/HOLDOUT.lock` seals a final holdout;
`comparison.py:248` implements Deflated Sharpe with an explicit warning about the
per-period-vs-annualized round trip. But `.planning/STATE.md` marks v9 `milestone_complete` with
4/5 phases and Phase 59 "Not started," and records uncommitted work diverging from saved state
since 2026-07-09. `.planning/spikes/MANIFEST.md` is **the best actual ledger in the ecosystem** —
a table with honest verdicts including `✗ INVALIDATED` and `⊘ NOT RUN — pre-determined by 003`.

**portfolio-manager — no research pipeline, by design.** Correct, and the repo defends it
(`ARCHITECTURE.md` "Do NOT rebuild").

### What does not exist

The chain `Observation → Hypothesis → Research → Evidence → Validated Signal → Algo Experiment →
Forward Validation → Portfolio Consideration` **has never been traversed end-to-end, and no
hypothesis has ever crossed a repository boundary.** There are two separate ledgers
(`RESEARCH-RECORD.md`, `spikes/MANIFEST.md`), no shared hypothesis ID space, and no
cross-references between them. Forward validation exists nowhere: no signal has a paper-traded
track record, and the one live system trades on a placeholder rule its own `CLAUDE.md` disowns
as *"provisional placeholder, NOT the intended architecture."*

Honest current state: **two parallel research pipelines of very different maturity, plus a
governance repo that correctly abstains — not one ecosystem pipeline.**

---

## H. Top three priorities

Ranked on the brief's criteria: scientific validity, duplication reduction, boundary clarity,
research reliability, clean connection, maintainability.

### 1. Make Market Intelligence output point-in-time queryable

*Criteria: scientific validity · research reliability · clean connection.*

Nothing downstream is possible without it. Algo cannot backtest against a signal that exists
only as "today's value"; PM cannot evidence what it knew when; the charter's §6 question is
currently unanswerable in all three repos.

The smallest defensible version is not new modelling: every signal's `build()` **already
produces the full history** (`results/vol_descriptors.csv` is 2.4MB of exactly this). What is
missing is an append-only, versioned record carrying `available_at` and a mandatory
`rarity.basis`. Low cost; unblocks the interface, the algo research loop, and the ledger at
once.

### 2. Resolve the algo repo's Market Intelligence mass — decide, do not relocate

*Criteria: duplication reduction · boundary clarity · maintainability.*

~300KB of state-estimation and dimension-discovery machinery sits in the repo that submits
orders. What makes this urgent rather than cosmetic: **regime-detection has already run the
head-to-head and retired the labelled-state approach.** Relocating the code would import a
rejected approach into the repo that rejected it.

Pick one outcome per component — close-with-verdict, re-ask under regime-detection's charter, or
quarantine with a dated stop condition — and write it down. Do the documentation reconciliation
in the same pass: `CLAUDE.md` (16 ETFs), `config.py` (8) and `STATE.md` (two non-existent
directories) cannot all stand.

This is also the only repo that went stale while the others moved, and the only one with live
crons. Unowned automation is the risk, not the code volume.

### 3. Close the false claims, then build the reconciliation the bot is missing

*Criteria: maintainability · integrity of the record.*

Two integrity items and one real gap:

- `portfolio-manager/ARCHITECTURE.md:303` asserts a wired regime seam, with a check mark, that
  does not exist; `src/regime.py` is orphaned and fetches a parked blank. Either wire it or
  delete both and correct the doc — the current state teaches a false architecture to every
  future reader, human or agent.
- `src/market_sentiment.py`'s regime classifiers (34KB + 35KB of tests) are the thing
  `ARCHITECTURE.md:264` forbids in that repo, kept alive by tests alone.
- **The live bot never verifies its fills.** `main.py` submits and returns. The charter's algo
  spine ends `EXECUTION → RECONCILIATION → LOGGING`; only logging exists. This is the one
  finding where a silent failure costs money rather than clarity.

### Explicitly NOT in the top three — and why

- **Consolidating volatility calculations.** The four implementations are intentionally
  independent and serve different questions. Unifying them couples two repos to buy nothing.
  The real gap is a shared *definition* of rarity — one page, folded into priority 1.
- **Building any interface to `vol-diagnostics`.** Under the corrected architecture this is not
  an ecosystem priority at all. The external project must remain removable to zero without the
  internal stack noticing; a validated finding can travel inward later through
  regime-detection's normal admission process (§2).
- **Building research-management infrastructure.** The charter says a table suffices, and
  `spikes/MANIFEST.md` proves it.
- **Relocating `portfolio-sprint/`.** Real misplacement (§2), trivial, not architectural.

---

## Research ledger — proposed starter

One file, `RESEARCH-LEDGER.md`, at the `systematic-investing-research\` root. Shared ID space
across the three internal repos (`MI-` / `ALGO-` / `PM-`) so a hypothesis can be referenced from
any of them. Seeded below from results the ecosystem **has already produced** — nothing
invented.

| ID | Hypothesis | Test | Result | Status | Reason |
|---|---|---|---|---|---|
| MI-001 | A K=2 jump-model state label reads volatility better than a plain causal threshold | Exposure-matched head-to-head, both bear datings (`results/detector_benchmark.csv`) | Threshold+hysteresis matched/beat on precision, recall, BAC; shorter lag | REJECTED 2026-08-04 | Thresholding destroys σ's graded information |
| MI-002 | Volatility descriptors (level · rarity · drift · GARCH half-life) are a usable production signal | Frozen one-look, `validate_vol.py` | Signed off, maturity `production` | VALIDATED 2026-08-06 | Mechanism pass; measurement / usefulness / maturity all H |
| MI-003 | Stock-bond correlation state describes whether bonds hedge equity drawdowns | Hedge-behavior-by-state, US 1962–2026 | Monotone through states (32% cushioned in negative-corr vs 57% fell-too in positive-corr) | VALIDATING | Japan/Europe OOS owed before SUPPORT |
| MI-004 | The JM regime is a priced cross-sectional factor | FF3 + BAB spanning, two FMP constructions | Constructions disagree (t = −1.30 vs t = −2.09) | AMBIGUOUS 2026-07-30 | Escalated to Step-4 prereg; earlier "spanned" verdict retracted as an over-claim |
| MI-005 | State-conditional covariance adds allocation value | Fee-equivalent vs reactive EWMA covariance | fee_A +2.8 inside all bands; reactive EWMA wins (fee_B −29.1) | REJECTED 2026-07-23 | Mechanism exists; reactive estimation harvests it better |
| MI-006 | Cross-asset defensive rotation timing adds value beyond exposure | Matched vol-target comparison | Null — matched VT matches/beats its drawdown protection | REJECTED 2026-07-26 | Exposure artifact; chapter 1 reconfirmed a 3rd time |
| MI-007 | Absorption ratio is an admissible diversification signal | Signal declaration + validation | Dropped | REJECTED | `archive/dropped-signals/05-ABSORPTION-DROPPED.md` |
| MI-008 | Funding stress is an admissible signal | Signal declaration + validation | Dropped | REJECTED | `archive/dropped-signals/07-FUNDING-DROPPED.md` |
| ALGO-001 | Regime-aware cross-sectional ML ranker produces tradable alpha | Backtest, then de-leak | IC 0.082 → 0.018; Sharpe 1.93 → −0.02 | REJECTED | Lookahead leak |
| ALGO-002 | The jump penalty λ yields a sticky, economically meaningful macro regime | Persistence sweep (spike 002) | Validated, narrowly scoped | VALIDATED (narrow) | Credit-crisis detector only; ~2 episodes / 21yr |
| ALGO-003 | The macro regime carries information volatility cannot see | Orthogonality / lead-lag at every λ (spike 003) | Regime lags vol at every λ; 100% overlap | REJECTED | Discretizing kills the lead |
| ALGO-004 | A damped macro overlay beats vol-target alone after costs | Decision gate (spike 004) | Not run | NOT RUN | Pre-determined by ALGO-003; verdict accepted 2026-06-12 |
| ALGO-005 | MacroHMM states track forward risk | OOS replacement test | +1.55% IS → +0.37% OOS; "Contraction" fwd-return ≈ "Expansion" | REJECTED 2026-06-16 | Window-dependent; removed entirely |
| ALGO-006 | The 2-HMM gauge detects volatility | Hermetic forward-RV eval (`regime_vol_eval.py`) | Monotonic LOW<MED<HIGH; AUC 0.77–0.81 | VALIDATED (as nowcaster) | Excellent nowcaster, **not** a forecaster |
| ALGO-007 | A paper-faithful 3-state directional detector beats oracle-label baselines | Two-fold walk-forward with locked gates | Incomplete | TESTING (stalled) | Milestone v9 Phase 59 never started; see priority 2 |
| PM-001 | MVO optimizer / recommender / rebalancer belongs in the governance engine | — | Retired | DEPRECATED 2026-08-02 | Security-selection paradigm abandoned; `ARCHITECTURE.md` "Do NOT rebuild" |

**Eight documented nulls across two repos is the strongest single indicator of research health
in this ecosystem.** The ledger's job is to keep them findable so none is rediscovered.

External-origin candidates enter the ledger only after re-testing under regime-detection's
charter. One exists today, recorded here as context, not as an internal result:

| Origin | Finding | Result | Note |
|---|---|---|---|
| vol-diagnostics | Timing covered-call writing off VRP level produces a forward-return edge | REJECTED, p = 0.74 (2026-07-27) | Prescriptive language was removed from that product as a result — not an internal signal |

---

## What this audit did not verify

- **No tests were run.** All pass counts (regime-detection 26, portfolio-manager 103–105,
  algo-trading-bot unstated) are as claimed in each repo's docs.
- **No pipeline, backtest, or report was executed.** No network calls, no credentialed access.
- **`.planning/` archives were sampled, not read exhaustively** — regime-detection's alone runs
  to dozens of prereg and phase documents.
- **Statistical claims were not re-derived.** Every result in the ledger is reported as the repos
  record it, not independently reproduced.
- **`archive/` trees were mapped but not audited** for content that should be revived.
- **`vol-diagnostics` was not audited.** It was inspected only far enough to characterize the
  external relationship in §2, and was not modified.
