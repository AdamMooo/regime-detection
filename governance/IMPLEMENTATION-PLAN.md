# IMPLEMENTATION PLAN — Architecture Lock + Disposition

Date: 2026-08-09 | Baseline: `CROSS-REPO-AUDIT-2026-08-09.md` (accepted)
Revision: Algo reframed as the **monetization layer** (2026-08-09)
Status: **SUBSTANTIALLY EXECUTED as of 2026-08-10.** ~~PLAN ONLY. No repository has been modified.
Nothing below has been executed.~~ Steps **0a · 0b · 1 · 9 · 3 · 4 · 5 · 2** are DONE. Step 6 is
complete except one row that the charter reserves for a human; Step 7 is de facto satisfied by the
first real evidence record. **Every step of the original plan has now been executed or is blocked
only on a human decision.**

**The execution log below is the authority on what is true of the tree — the section bodies describe
what was *planned*, and where execution diverged the divergence is annotated in place.** Amendments
recorded 2026-08-10: the §3.3 preamble (every `ARCHIVE` became `DELETE`), D-2, two §12 lines, and
five divergences in §6 — one of which (the buying-power gate) is a **design error, not a deviation**.

**Decisions D-1, D-2, D-3 are RESOLVED and locked (2026-08-09) — see §11.**
Live trading is to be **suspended**; the gauge is archived and **not replaced by an
equal-weight fallback**; the daily regime email is **archived, not deleted**.

Review this document before any code change. §12 lists what will not be touched.

---

## Execution log

| Step | Action | Status | Detail |
|---|---|---|---|
| **0a** | Pause scheduled trading | ✅ **DONE** 2026-08-09 | `algo-trading-bot` `4810fb7f`, pushed to `origin/main`. All three crons commented; `workflow_dispatch` and both jobs unchanged. **The bot no longer trades on a schedule.** ~~Resume = uncomment three lines.~~ **Amended 2026-08-10:** Step 1 then deleted the morning-report cron along with its script, so `trading.yml` now carries **two** commented crons (14:00 and 19:30 UTC). Resume = uncomment two lines. |
| **0b** | Documentation corrections (§10) | ✅ **DONE** 2026-08-09 | algo `b1f3fa3e` (4 files) · PM `db5cdf7` (5 files) · vault `C:\dev\CLAUDE.md` (paths + stack diagram). Docs-only; no code touched. **Surfaced a new finding — see `ALGO-009` below.** |
| **1** | Algo strip-down (§3.3) | ✅ **DONE** 2026-08-09 | `9f6e4a28` — 102 files, **−15,382 lines**. **DELETED not archived** (Adam: "we want gone not fixed"); recoverable at `b1f3fa3e`. Tests 204 → **52 passing**. Bot dry-run verified: exits without trading. Ledger written first, so the findings outlived the code. **Scope of the override, verified against the tree 2026-08-10 — see the §3.3 preamble:** no `archive/` directory was ever created; `outputs/models/` is gone entirely (8 frozen `.joblib` artifacts **and** `FROZEN.md`), as are `scripts/daily_regime_report.py` and its cron. This overrides **D-2** and the `outputs/models/*.joblib` line in **§12**, both of which still read as written. |
| **9** | Research ledger (§9) | ✅ **DONE** 2026-08-09 | `RESEARCH-LEDGER.md` — **pulled forward from Step 6**: deleting the code made it the only thing preserving ALGO-001…009. 16 seeded findings, 9 of them nulls |
| **3** | MI history + contract v1 (§5) | ▶ **NEXT** | **reordered 2026-08-09 (Adam): regime-detection is the first stop after the strip-down.** The bot now has nothing to consume; MI producing point-in-time records is what makes validated inputs possible |
| **4** | Algo reconciliation (§6) | ✅ **DONE** 2026-08-10 | `b83e0a6e` `0e35e037` `aad8bac5` `42ba1df4` + 3 doc/label commits. Tests 67 → **135**, all offline. Both §6.1 defects fixed: `last_rebalance` advances only on `CLEAN`, and `rebalancing_in_progress` is gone — a ledger with submissions but no reconciliation now resolves to `HALT`, one with no submissions to `CARRY_FORWARD`, which is exactly the distinction the single boolean could not express. **Five spec divergences amended in §6.** Precondition for the bot trading again is satisfied; the remaining blockers are the strategy call contract and the admission gate |
| **5** | Consumer vendoring + checksum tests | ✅ **DONE** 2026-08-10 | Both consumers pinned. algo `d84b9960`, PM `c30e1f2`; all three repos hash to `49257038…b219bcf`. **`core.autocrlf=true` is set in Git-for-Windows' *system* config, so it is invisible to `--global` and will very likely be true on the new machine too** — a CRLF rewrite on checkout would present the same commit as contract drift. Each repo carries a `.gitattributes` pinning `eol=lf`; verified by simulating a fresh `autocrlf=true` clone of all three (pins hold, 0 CR bytes) |
| **2** | PM disposition (§4) | ✅ **DONE** 2026-08-10 | `d8acd0d` `fec34a0` `b22f5ab` `c30e1f2` `d52d9ac` + `e1086e9`. −381 lines of market-state machinery from `market_sentiment.py` (all five confirmed zero call sites) and −365 from its tests; `src/regime.py` deleted; **8** false `regime_card.json` claims corrected (§10 listed five; three more were found while verifying); `portfolio-sprint/` relocated to `C:\dev\portfolio-sprint\`. Tests 151 → **131**, net −20 by design. The daily brief keeps sending. **`REGIME_REPO_PAT` is now read by no code and can be revoked** |
| 6 | Research ledger seeding (§9) | ◐ **MOSTLY DONE** 2026-08-10 | Seeded at Step 9; brought current today (`272acda` `ee7c581`): MI-003 → `VALIDATED` with its OOS numbers, **MI-009** valuation and **MI-010** credit added, MI-004 expanded plus a new `### Open questions` section. **Blocked on a human, by charter design:** the `ALGO-008` row still reads `IDEA` and its draft cites `owner_verdict`, which §8 of the prereg reserves for Adam |
| 7 | Evidence record schema (§8) | ◐ **DE FACTO DONE** | `evidence/ALGO-008-2026-08-10.json` was emitted 2026-08-10 carrying `hypothesis_id`, `n_variants: 3`, fold dates, result and decision — ahead of this step's place in the order. What remains is formalising the shape as a schema rather than a convention |

**Revised order:** `0a ✅ → 0b ✅ → 1 → 3 → 4 → 5 → 2 → 6 → 7`

### Findings surfaced during execution

| ID | Finding | Impact |
|---|---|---|
| **ALGO-009** | **The frozen 2-HMM gauge has been fed out-of-distribution features since 2026-07-21.** Artifacts frozen 2026-06-16 against the 16-ETF universe; `493cba43` (2026-07-21) cut `ETF_UNIVERSE` to 8; `regime/data.py:191-192` computes `pct_above_{50,200}ma` from `ETF_UNIVERSE`, and `pct_above_200ma` is BreadthHMM's primary relabeling anchor. | Every regime label from 2026-07-21 onward is suspect, including those the live bot traded on through 2026-07-27. **Not fixed — reinforces D-1.** Retraining would violate `FROZEN.md`'s do-not-retrain rule and would re-home market-state modelling in the wrong repo. Recorded in `FROZEN.md`; goes into the ledger at Step 6. |

---

## 1. Locked architecture

```
                    MARKET DATA
                         │
                         ▼
        ┌────────────────────────────────┐
        │  MARKET INTELLIGENCE           │   UNDERSTANDING
        │  regime-detection              │   "What is happening, how unusual,
        │  Observe · Measure · Model     │    how has it behaved historically?"
        └───────────────┬────────────────┘
                        │  INFORMATION
                        │  (Level-0 observation records, versioned, point-in-time)
             ┌──────────┴──────────┐
             ▼                     ▼
   ┌───────────────────┐  ┌──────────────────────┐
   │  ALGO TRADING     │  │ PORTFOLIO MANAGEMENT │
   │  algo-trading-bot │  │ portfolio-manager    │
   │  MONETIZATION     │  │  GOVERNANCE          │
   │                   │  │                      │
   │ "Can this under-  │  │ "Given policy and    │
   │  standing be      │  │  constraints, what   │
   │  turned into      │  │  portfolio behavior  │
   │  returns after    │  │  is permitted?"      │
   │  costs and OOS?"  │  │                      │
   └─────────┬─────────┘  └──────────────────────┘
             │  EVIDENCE (never a state, never a signal)
             ▼
      RESEARCH LEDGER
```

**Three roles, three questions, no overlap:**

```
regime-detection  =  UNDERSTANDING
algo-trading-bot  =  MONETIZATION
portfolio-manager =  GOVERNANCE
```

**Three internal repositories. No fourth.** `vol-diagnostics` is an outward-facing research
project outside the workspace (`C:\dev\vol-diagnostics`), referenced in this plan only where it
prevents repeating work already paid for. **No step creates a code dependency on it in either
direction.**

### Epistemic invariants (must survive every step below)

| Invariant | Enforcement mechanism |
|---|---|
| A Market Intelligence output is not a trading instruction | Closed allowlist + denylist in the contract (§5); `additionalProperties: false` throughout |
| An Algo signal is not a portfolio allocation | Algo emits Evidence records only; PM never reads Algo output (§7) |
| A Portfolio decision is not a market-state label | PM disposition removes its regime classifiers (§4) |
| **Understanding is not monetization** | Algo owns no market-state model; every MI input must independently clear the Algo admission gate (§3.1, §7) |
| No implicit conversion between layers | Only `maturity` is behavior-bearing, and it is enumerated (§5.3) |

---

## 2. Repository responsibilities

### regime-detection — Market Intelligence · UNDERSTANDING

**Answers:** *What is happening in the market, how unusual is it, and how has this environment
behaved historically?*

**Owns:** market measurement · dimensional structure · **all market-state modelling** ·
signal-validation methodology (charter → prereg → causal guard → mechanism gate → OOS →
cooling-off → dated sign-off) · the observation contract and its schema · the point-in-time
observation history.

**This is the only repository permitted to model market state.** If a market-state question is
worth answering, it is answered here or it is not answered.

**Must not own:** any allocation, exposure, order, or trading concept. Already enforced
executably by `scripts/signal_output_schema.py` and `tests/test_boundary_audit.py`.

**Important constraint — this repo is not a destination for orphaned models.** Its admission
process is the point of it. Code arriving from elsewhere without a mechanism gate, a
preregistration, a causal guard, and an out-of-hypothesis-sample confirmation does not become
Market Intelligence by being moved. **A question can be re-homed here; unfinished code cannot.**

### algo-trading-bot — Algo Trading · MONETIZATION

**Answers:** *Given something we believe we understand about the market, can that understanding
be turned into a systematic, testable, executable source of returns?*

Not *"how do we build models that understand the market?"* — that is upstream.

Six questions, and nothing else:

1. Can this understanding actually be monetized?
2. What is the precise trading rule?
3. Does it survive honest testing — costs, constraints, out-of-sample?
4. How is the position constructed?
5. How is it executed safely?
6. What actually happened versus what we intended?

**Owns:** monetization hypotheses · the backtest harness and its honesty machinery · position
construction · risk controls · order generation · Alpaca execution · fill reconciliation ·
operational state and logging · Evidence records.

**Must not own:** HMMs, regime models, state estimation, market-state machinery, feature
discovery, or any modelling stack whose output is a description of the market. **The repo takes
validated inputs; it does not manufacture understanding.**

**Admission gate (§3.1):** an MI observation reaching this repo is a *candidate*, not a signal.
Monetization must be proven independently, after costs, implementation constraints, and OOS.
Most candidates will fail. That is the expected outcome, not a defect.

Structural rule: production execution code imports nothing from research modules. The
dependency runs research → frozen artifacts → production, never production → research.

### portfolio-manager — Portfolio Management · GOVERNANCE

**Answers:** *Given my policy, constraints, utility, and available information, what portfolio
behavior is permitted?*

**Owns:** the mandate/IPS · sleeve definitions and ranges · holdings state · exposure
classification · drift and compliance · concentration limits · governance reporting.

**Must not own:** market prediction, regime classification, security selection, optimization,
trade generation. Already normative in its `ARCHITECTURE.md`; §4 closes the gap between that
statement and the code.

---

## 3. Algo disposition

### 3.1 The question was inverted

The previous revision asked *"which of the existing models do we keep in Algo?"* — which
assumes the models belong there and argues about degree. **Replaced with:**

> **What does a clean monetization engine require, and what existing code supports that?**

Everything that does not support it is removed from the bot — archived as research history, or
re-homed upstream **as a question, not as code**.

### 3.2 What a monetization engine requires

| Required capability | Why it is required | Existing code that supports it |
|---|---|---|
| **Hypothesis interface** | A monetization hypothesis must be stated before it is tested: what understanding, what rule, what horizon, what would falsify it | `backtest/overlay/signals.py::SignalAdapter` ABC — a causal fit/transform contract. **The abstraction is right; its one concrete implementation is not** (see 3.3) |
| **Backtest harness** | Leak-free equity curves, fold isolation, uniform costs | `backtest/overlay/engine.py` (shift(1) fill, 10bps, one definition), `overlay/splitter.py` (folds locked by a dated prereg with an amendment log), `backtest/metrics.py`, `backtest/data_loader.py` |
| **Honesty machinery** | K combinations on one OOS window will produce a winner by chance | `overlay/comparison.py` — Deflated Sharpe + winner criterion, with an explicit warning about the per-period-vs-annualized round trip. `.holdout-quarantine/HOLDOUT.lock` — a sealed final holdout |
| **Baselines** | A strategy must beat the honest alternative, not just cash | `overlay/baselines.py` (buy-and-hold + equal-weight), `overlay/cross_asset_baseline.py` |
| **Signal generation from candidates** | Turning an observation into candidate rules, evaluated independently before combination | `overlay/signal_factory.py` |
| **Position construction** | Signal → target weights, one definition shared by backtest and live | `overlay/strategy.py` + `overlay/aggression.py` ABCs; the live 1/N logic is currently inline in `main.py` |
| **Risk controls** | Pre-trade gates and a kill switch | `core/risk_manager.py` (drawdown halt) + the new gates in §6 |
| **Execution** | Order submission | `execution/alpaca_executor.py`, `data/fetcher.py` |
| **Reconciliation** | What happened vs what was intended | **Does not exist** — §6 |
| **Operational state + logging** | Crash recovery, audit trail | `outputs/bot_state.json`, `logs/`, + the cycle ledger in §6 |
| **Evidence** | The output of a monetization test | **Does not exist** — §8 |

That is the whole engine. Note what is absent: no feature engineering, no state estimation, no
model selection, no market description of any kind.

### 3.3 Disposition table

Dispositions: **KEEP** (core monetization engine) · **SIMPLIFY** (core, but carrying upstream
coupling to sever) · **ARCHIVE** (research history, inert, with a written post-mortem) ·
**DELETE** (dead or belongs to another system) · **RE-HOME AS QUESTION** (the code is archived;
the open question moves upstream as a new charter, not as a transfer).

> **AMENDED 2026-08-10 — read this before the table.** The `ARCHIVE` column below records what was
> *planned*. Step 1 executed **every `ARCHIVE` row as `DELETE`** on Adam's instruction ("we want gone
> not fixed"). Verified against the tree 2026-08-10: **no `archive/` directory exists** in
> `algo-trading-bot`, and neither do `archive/regime-gauge-v7/`, `archive/directional-hmm-v9/`,
> `outputs/models/` (its 8 `.joblib` artifacts and `FROZEN.md`), or `scripts/daily_regime_report.py`.
> Everything is recoverable from git at `b1f3fa3e`. **Nothing was lost — but no archive destination
> named in this table exists on disk, so do not send anyone looking for one.** The table is kept
> unedited because it is the record of the decision; this note is the record of the override. One
> consequence worth naming: the gauge's **do-not-retrain rule died with `FROZEN.md`** and now survives
> only in `.planning/phases/**` and `docs/ARCHITECTURE-AUDIT.md`. The artifacts are gone too, so
> nothing can be retrained by accident — but if they are ever restored from `b1f3fa3e`, the rule must
> be restored with them.

| Component | Question it answers | Serves monetization? | Evidence on record | Disposition | Destination |
|---|---|---|---|---|---|
| `regime/` (2-HMM gauge, 8 frozen artifacts) | "What volatility state is the market in?" | **No — understanding** | Validated as a vol *nowcaster* (fwd RV monotonic LOW<MED<HIGH, AUC 0.77–0.81); explicitly not a forecaster. `FROZEN.md`: do not retrain. Live use is cadence + top-N, which `CLAUDE.md` calls *"provisional placeholder, NOT the intended architecture."* | **ARCHIVE** | `archive/regime-gauge-v7/` + post-mortem. Gated on D-1. |
| `backtest/hmm/` (12 modules, ~220KB) | "Which feature spaces form stable latent states? Can a 3-state directional detector beat oracle baselines?" | **No — understanding** | Phase 59 **never started**; milestone marked complete at 4/5; uncommitted divergence since 2026-07-09. **No verdict was ever reached.** Upstream, `detector_benchmark.csv` retired the labelled-state framing outright. | **ARCHIVE** + **RE-HOME AS QUESTION** | Code → `archive/directional-hmm-v9/`. Question → ledger `ALGO-007`, restated as an MI question. Re-opened only if regime-detection judges it open, under a fresh charter. **The code does not move.** |
| `backtest/regime_replay.py` | "What would the gauge have said historically?" | **No** | Produces `regime_labels.parquet`, stale since 2026-06-16. Sole consumer is `VolGaugeSignal`. | **ARCHIVE** | `archive/regime-gauge-v7/` |
| `backtest/regime_diagnostics.py` | "Are the labels well-formed?" | **No** | Helper for `regime_vol_eval.py` only. | **ARCHIVE** | `archive/regime-gauge-v7/` |
| `backtest/regime_vol_eval.py` | "Does the gauge detect volatility?" | **No — but it is the evidence** | The artifact that produced `ALGO-006`. Hermetic. Its result is why the gauge can be archived confidently rather than deleted blindly. | **ARCHIVE** (as evidence) | `archive/regime-gauge-v7/`; result transcribed to the ledger first |
| `scripts/daily_regime_report.py` (33KB) | "What is the market doing this morning?" | **No — an understanding report** | `CLAUDE.md`: *"This report IS the gauge's purpose — it is not a trading dependency."* | **ARCHIVE** (D-2 resolved) | `archive/regime-gauge-v7/`; its cron in `trading.yml` is disabled with the rest. Function belongs to MI's presentation layer when that exists. |
| `docs/research_spine.md` | "How should a Canadian ETF portfolio de-risk in a crash?" | **No — governance** | VFV.TO/QQC.TO/VDY.TO → CSAV.TO with a 1.0/0.5/0.0 exposure ladder. Duplicates `MANDATE.md`'s concern. Still cited by the hub as "current product direction." | **DELETE from Algo** | If wanted, it enters via `MANDATE.md`'s policy-change process |
| `backtest/overlay/signals.py` | "How does an input become a causal (state, score) series?" | **Yes — the hypothesis interface** | `SignalAdapter` ABC is a clean causality contract. Its concrete `VolGaugeSignal` wraps the archived gauge. | **SIMPLIFY** — keep the ABC, drop `VolGaugeSignal` | ABC stays; concrete class goes with the gauge |
| `backtest/overlay/comparison.py` (18KB) | "Which combo wins, and is the win real?" | **Yes — honesty machinery** | DSR + winner criterion correctly implemented with a documented annualization trap. But hard-codes an HMM-era `SIGNALS` list and defers its orchestration to a "wave 2" that was never built. | **SIMPLIFY** — keep the statistics, sever the HMM coupling, drop the unbuilt sweep scaffolding | stays |
| `backtest/overlay/{engine,splitter,baselines,strategy,aggression}.py` | harness · folds · baselines · construction | **Yes — core** | `engine.py` is the one leak-free equity-curve definition; folds locked by dated prereg. | **KEEP** | stays |
| `backtest/overlay/signal_factory.py` | "Generate candidate rules and evaluate each independently before combining" | **Yes — this is monetization research** | Leak-safe fold discipline; combines only survivors. | **KEEP** | stays |
| `backtest/overlay/cross_asset_baseline.py` | "What does an honest cross-asset momentum+risk baseline earn?" | **Yes — baseline** | One-bar execution lag, proportional turnover costs. | **KEEP** | stays |
| `backtest/overlay/model_candidates.py` + `scripts/research/rank_model_candidates.py` | "Which model family should we pick?" | **No** | A weighted scoring matrix (objective_fit 0.40 / robustness 0.30 / complexity 0.15 / deployability 0.15). Model-family preference is not evidence; the backtest is. | **DELETE** | — |
| `backtest/{data_loader,metrics}.py` | price cache · Sharpe/Sortino/drawdown | **Yes — infrastructure** | — | **KEEP** | stays |
| `main.py`, `config.py`, `core/risk_manager.py`, `data/fetcher.py`, `execution/alpaca_executor.py` | the execution spine | **Yes — core** | — | **KEEP** | stays |
| `strategy/ev_ranker.py` | "Does 12-1/6-1 risk-adjusted momentum rank this universe?" | **Yes — but it is a candidate, not a validated strategy** | A momentum rule, not a market model, so it is monetization logic and correctly located. But it has **no ledger entry and never cleared the admission gate** — it is live today only as residue of the deleted rotation system. | **KEEP as a candidate**, unwired from the live path | stays in `strategy/`; enters the ledger as `ALGO-008` and reaches production only via §3.6 |
| `main.py` equal-weight allocation logic (`main.py:208-222`) | "How is the position constructed?" | **No — it is a benchmark, not a strategy** | 1/N across the universe plus HIGH_VOL top-N. Never validated; inherited from the dead rotation system. Its correct role already exists upstream: `overlay/baselines.py::equal_weight_*_returns` is the honest baseline a strategy must beat. | **DELETE from the live path** (D-1) | Equal-weight survives **only as a backtest baseline**, never as live behavior |
| `strategy/regime_detector.py` | thin wrapper over `RegimeEnsemble` | **No** | Exists only to hand the gauge to `main.py`. | **DELETE** (D-1) | — |
| `scripts/{download_regime_features,refresh_discovery_snapshots,regenerate_hmm_fixtures}.py` | feature/fixture plumbing for the HMM stack | **No** | Serve the archived modelling only. | **ARCHIVE** | with their stacks |
| `.planning/spikes/008-validation-run` | "Does the shipped vol-target signal validate?" | history | `validate_voltarget.py:25` imports `strategy.vol_target`, **deleted in Phase 47** — verified absent. Non-runnable. | **ARCHIVE** (README + plot) | `.py` is dead |
| `.planning/spikes/009-credit-spread-tilt` | "Does a credit-spread tilt add value?" | history | Same broken import (`credit_tilt.py:23`). Non-runnable. | **ARCHIVE** (README + plot) | — |
| `.planning/spikes/010-diversified-base-voltarget` | "Does a diversified base improve vol-targeting?" | history | **Self-contained and still runnable** — imports only spike-local `loader`. Distinct from 008/009. | **ARCHIVE** (intact) | remains runnable |

### 3.4 Net effect

The bot goes from ~380KB of non-test source to roughly **80–90KB**: a hypothesis interface, a
backtest harness with real honesty machinery, position construction, risk controls, execution,
reconciliation, state, and evidence. Approximately **300KB of market-understanding machinery
leaves the monetization layer.**

Nothing is rebuilt in a nicer form inside the bot. The modelling is removed, and the bot is
rebuilt around *validated understanding produced upstream* rather than continually reinventing
understanding itself.

### 3.5 D-1 RESOLVED — the strategy slot is emptied, not refilled

`regime/` cannot be archived while `main.py` imports it. The live path uses the regime label for
exactly two things:

1. **Rebalance cadence** — `{LOW:21, MED:14, HIGH:7}` days + immediate rebalance on flip
   (`main.py:130-146`).
2. **HIGH_VOL concentration** — top-4 by EV instead of the full 8 (`main.py:208-215`).

Both are explicitly disowned by the repo's own `CLAUDE.md` as placeholder.

**An earlier draft of this plan proposed replacing them with a fixed-cadence equal-weight
rotator. That is rejected.** Equal-weight 1/N plus momentum top-N is not a validated strategy —
it is residue from the rotation system deleted in Phase 37, and it has no ledger entry, no
out-of-sample test, and no cost analysis. Keeping it as the default would preserve exactly the
thing this cleanup exists to remove: **an unvalidated rule running live because it happens to
already be there.**

Equal-weight has a correct role, and it is not this one:

```
BEFORE   equal-weight = what the bot does          (an unvalidated default)
AFTER    equal-weight = what a strategy must beat  (the honest baseline, overlay/baselines.py)
```

**Resolution: the live path retains the execution spine and empties the strategy slot.**

```
KEPT (warm, tested, ready)          REMOVED FROM LIVE
  risk checks                          regime gauge input
  order construction                   regime-conditional cadence
  Alpaca submission                    HIGH_VOL top-N concentration
  fill reconciliation  (§6, new)       equal-weight 1/N allocation
  operational state + logging          EVRanker wiring (kept as a candidate)
```

**Consequence, stated plainly: the bot has no validated strategy today, and after this step it
will not trade.** That is the honest description of its actual state, not a regression. It has
been trading an unvalidated rule; suspending that is the correct action, not a loss of
capability.

The bot resumes trading when — and only when — some hypothesis clears the admission gate in
§3.6 and reaches `VALIDATED` in the ledger. `Strategy` becomes a genuine slot with nothing
plugged into it, which is what a monetization engine with no validated monetization looks like.

### 3.6 The admission gate

An MI observation arriving at the bot is a **candidate**, never a signal. It becomes a
production trading input only by traversing:

```
MI observation (production maturity)
   → monetization hypothesis stated, with a falsification condition
   → in-sample rule construction
   → out-of-sample test on an untouched fold
   → cost / turnover / capacity / implementation test
   → multiple-testing correction (DSR against the number of variants tried)
   → Evidence record → ledger entry reaching VALIDATED
   → only then: production path
```

**Most candidates will fail here.** A `production`-maturity MI signal that fails monetization is
a completely normal outcome and does not reflect on the signal — it means the understanding is
real and not exploitable, which the charter explicitly treats as a valid result.

---

## 4. Portfolio disposition table

| Component | Governance function? | Assessment | Disposition |
|---|---|---|---|
| `src/market_sentiment.py` — `get_indicator_snapshot()` + private helpers | **Yes** — the FRED macro-context block of the daily brief | The only live surface. Verified: **1 call site** outside tests (`daily_report.py:193`); `fetch_series_data` called only from inside the class. | **KEEP** |
| `src/market_sentiment.py` — `assess_market_regime()`, `get_risk_summary()`, `get_composite_macro_score()`, `get_fear_greed_proxy()`, `get_yield_curve_data()` | **No** — market-state classification and composite scoring | **Zero call sites outside tests**, verified individually. `daily_report.py:179` states the omission is deliberate. `ARCHITECTURE.md:264` names an in-repo regime detector as a thing that must not exist here. Emits labels like "High Recession Risk / Late Cycle / Expansionary". | **DELETE** (with their tests) |
| `src/regime.py` (`collect_regime_card()`) | **No** — orphaned interface | Imported by nothing; fetches a deliberate parked blank. | **DELETE** — the real interface is §5 and will not resemble it |
| `scripts/weekly_regime_brief.py` + its workflow | **Deferred** — future assumption-ledger email | Blank template; schedule disabled 2026-08-04; docstring accurately records why. | **KEEP as parked** — correct future home for MI context. Revisit at ≥2 production MI signals. |
| `portfolio-sprint/` (hub + 3 assessments) | **No** — career/publication material | A career-portfolio initiative (deadline 2026-08-25) inside the investment-portfolio repo, holding private assessments of **regime-detection** and **vol-diagnostics** explicitly "kept out of the repos" while inside one. Naming collision: "portfolio" here means career portfolio. | **MOVE out of the repo** to the vault (e.g. `C:\dev\_planning\portfolio-sprint\`). Live dated work — not deleted. |

**Net effect:** PM loses ~34KB of market modelling plus ~35KB of its tests, one dead interface,
and review material about two other projects. Its answer to *"what will the market do?"*
becomes: **it doesn't ask.**

---

## 5. Market Intelligence interface design

### 5.1 Form — a versioned, language-neutral contract

A **JSON Schema (draft 2020-12) document plus a conformance test-vector set**. Not a Python
module; `signal_output_schema.py` does not become a cross-repository import.

```
regime-detection/contracts/
    market-observation-v1.schema.json     ← canonical, producer-owned, versioned
    vectors/valid/*.json                  ← must validate
    vectors/invalid/*.json                ← must be rejected, each naming the rule it violates
    CHANGELOG.md
```

**Distribution: vendoring with a checksum test.** Each consumer keeps a pinned copy at
`contracts/market-observation-v1.schema.json` plus a test asserting its sha256 matches the
claimed version. No import, no submodule, no runtime network call. Drift becomes a red test.

Deliberate duplication made safe by a checksum — chosen because a shared package would couple
three release cycles, which is what the architecture exists to prevent.

`signal_output_schema.py` remains regime-detection's internal producer-side validator, and
gains one job: a test asserting it and the JSON Schema accept and reject the same vectors.

### 5.2 Record shape

```jsonc
{
  "spec_version": "1.0",
  "signal": "volatility",
  "as_of":        "2026-05-29",            // the date the reading describes
  "available_at": "2026-05-30T09:15:00Z",  // when it could actually have been known
  "clock": "daily",
  "assumption_monitored": "…",             // or an explicit "N/A because…"
  "reading":   { "value": 0.1203, "units": "annualised_volatility", "estimator": "…" },
  "rarity":    { "level_percentile": 0.5187, "basis": "expanding", "window": null },
  "trend":     { "level_percentile_change_10_sessions": -0.0812, "direction": "falling" },
  "extreme_conditions": { … },
  "cross_signal_relationships": [ "…" ],
  "assessment": { "mechanism": "pass", "measurement_validity": "H",
                  "investment_usefulness": "H", "evidence_maturity": "H" },
  "maturity": "production"
}
```

**`as_of` vs `available_at`** — `as_of` is the observation date; `available_at` is the wall-clock
instant the value was computable given data vintage, publication lag, and revision policy. A
backtest filters on `available_at`. For revised series (most macro), `available_at` is
first-print availability, never the revision date. **Both required; neither inferable from the
other.**

**`rarity.basis`** — required enum:

| basis | meaning | `window` |
|---|---|---|
| `expanding` | rank against the signal's own history to date | must be `null` |
| `trailing_fixed` | rank within a fixed trailing window | required, integer sessions |
| `full_sample` | rank against the whole sample — **leaks; research-only** | `null`; forces `maturity` ≠ `production` |

Resolves the audit's D2 finding at the interface: the number travels with the definition that
makes it comparable.

### 5.3 What the contract rejects

Denylist carried verbatim: `weight · allocation · exposure · position · sizing · order · trade ·
buy · sell · tilt · overweight · underweight · recommendation · action` (plus `target_weight,
position_size, entry, exit, stop, stop_loss, cash_call, signal_action, risk_score, score,
rating, target`).

**A denylist alone is not the enforcement** — a producer could rename `allocation` to
`alpha_hint` and pass. Three structural rules close that:

1. **Closed allowlist at every level** — `additionalProperties: false` throughout. A renamed
   decision field is rejected for being *unknown*, not *forbidden*.
2. **Every numeric leaf carries `units`** — removing the natural shape a smuggled weight takes.
3. **Only `maturity` is behavior-bearing, and it is enumerated.** Consumers may not derive
   behavior from any other field's name. A contract clause, enforced in review.

### 5.4 The prerequisite: point-in-time history

```
regime-detection/observations/<signal>/<as_of>.json    one record per observation date
regime-detection/observations/<signal>/MANIFEST.csv    as_of · available_at · sha256 · spec_version
```

Append-only, never rewritten. A correction is a **new record with a later `available_at`** and a
`supersedes` pointer — so "what did we believe on date X, as of time T?" stays answerable.

**Not new modelling.** Every signal's `build()` already returns the full history —
`results/vol_descriptors.csv` is 2.4MB of exactly this. The work is serialization plus the two
timestamp fields.

---

## 6. Reconciliation design

~~**Design only. Not implemented.**~~ **IMPLEMENTED 2026-08-10** — `execution/reconciliation.py`
(broker-agnostic: imports neither `alpaca-py` nor `config`), `alpaca_executor.py` gained the three
lookup methods, `main.py` sequences phases and holds no reconciliation logic. Tests 67 → **135**,
verified offline by monkeypatching `socket.socket` to raise. Both §6.1 defects fixed. The bot still
cannot trade: `ACTIVE_STRATEGY = None` (asserted by a test) and `trading.yml` is byte-identical.

> **AMENDED 2026-08-10 — five places this design did not survive contact with the code.**
>
> 1. **The buying-power gate in §6.5 is provably non-binding, and this is a real error in the design
>    above.** The bot sizes targets off `min(sleeve, buying_power)`, so `sum(buys) ≤ effective_bp` —
>    the very figure the gate compares against. It can never fire. It is retained as a documented
>    tripwire, **not as a protection**; do not later "simplify" it away *or* start trusting it. The
>    condition that actually binds, and that the old code did protect, is now explicit: a failed sell
>    blocks the buys it was funding, with a recorded reason instead of the previous silent skip.
>    Making the gate meaningful requires changing the sizing base, which changes trading behavior —
>    deliberately out of scope.
> 2. **That gate also had to move phases.** §6.5 lists buying-power under RISK CHECK, but it is only
>    evaluable *after* sells are submitted. It lives in `submit_cycle` and still writes into
>    `risk_checks`, so the ledger shape is unchanged.
> 3. **§6.4's `cause` enum is short two values.** §6.5's prose requires `EXPLAINED` to cover "blocked
>    check, or open order"; the enum has neither. Added `open_order`, and non-BP blocks now carry the
>    gate's own name (`stale_quote`, `max_order_frac`, …). `insufficient_bp` stays reserved for the
>    gate in (1).
> 4. **`done_for_day` is absent from §6.4's `broker_status` set.** Mapped to `open` / `terminal: false`
>    rather than inventing a label or implying finality — consistent with "absence of fill information
>    is not evidence of a fill."
> 5. **`CARRY_FORWARD`'s "force a rebalance regardless of cadence" has no cadence left to override.**
>    Regime-conditional cadence was deleted with the gauge on 2026-08-09 (D-1), so `last_rebalance` is
>    the only cadence state. `CARRY_FORWARD` sets a `force_rebalance` flag and withholds the
>    `last_rebalance` advance; **any future cadence rule must consult that flag** or it will silently
>    re-introduce the §6.1 defect.
>
> One behavior chosen, not derived: `MAX_ORDER_NOTIONAL_FRAC = 0.35` can deadlock the liquidation of an
> inherited position larger than 35% of the portfolio — blocked every cycle, `EXPLAINED`, carried
> forward until a human acts. Fail-closed on purpose, recorded as a Known Issue.

### 6.1 The gap, precisely

`main.py::_execute_rotation` computes deltas, submits sells, submits buys, writes
`bot_state.json`, returns. It never polls order status, never reads back fills, never compares
realized position to target.

Two concrete defects, both visible in current code:

- **`main.py:364-369`** — if any sell fails, buys are skipped but `last_rebalance` is still set
  to `now()`. The cadence clock advances on a rotation that did not happen, so the book can sit
  half-rotated for a full window.
- **`_save_state(rebalancing_in_progress=True)` (`main.py:344`)** is the only crash-recovery
  mechanism and is a single boolean — it cannot distinguish "crashed before submitting" from
  "submitted, unknown fills."

### 6.2 Lifecycle

```
INTENT ─▶ RISK CHECK ─▶ SUBMISSION ─▶ BROKER RESPONSE ─▶ FILL STATUS
                                                              │
                                                              ▼
   LOG ◀── ACTUAL POSITION ◀── DISCREPANCY HANDLING ◀── RECONCILIATION
                                       │
                                       └─▶ NEXT-CYCLE RECOVERY
```

### 6.3 Identity and idempotency

Deterministic `client_order_id` per intent:

```
{cycle_id}:{ticker}:{side}          e.g.  20260810-1400:SPY:buy
cycle_id = {UTC date}-{cron slot}   the two trade windows are 1400 and 1930 UTC
```

**Idempotency comes from the broker, not local locking.** Alpaca rejects a duplicate
`client_order_id`, so re-running a cycle after a crash cannot double-submit. This replaces the
`rebalancing_in_progress` boolean with a mechanism correct even if the process dies between
submit and write.

*Implementation note:* exact alpaca-py call names for order lookup and status must be verified
against the pinned version at implementation time. The design depends only on
submit-with-client-id, get-order, and list-orders existing.

### 6.4 The cycle ledger

Append-only JSON per cycle at `outputs/cycles/{cycle_id}.json`:

```jsonc
{
  "cycle_id": "20260810-1400",
  "started_at": "…", "mode": "paper|live|dry_run",
  "inputs":  { "portfolio_value": …, "buying_power": …, "ignored_notional": … },
  "targets": { "SPY": { "target_weight": 0.125, "target_notional": … }, … },

  "intents": [ { "client_order_id": …, "ticker": …, "side": "buy|sell",
                 "intended_notional": …, "intended_qty": …,
                 "ref_price": …, "ref_price_as_of": … } ],

  "risk_checks": [ { "check": "drawdown_halt|max_order_frac|stale_quote|buying_power|
                               universe_membership|max_orders_per_cycle",
                     "client_order_id": …, "verdict": "pass|BLOCKED", "reason": … } ],

  "submissions": [ { "client_order_id": …, "broker_order_id": …,
                     "submitted_qty": …, "accepted": true, "error": null, "at": … } ],

  "fills": [ { "client_order_id": …, "filled_qty": …, "filled_avg_price": …,
               "rejected_qty": …, "broker_status": "filled|partially_filled|canceled|
                                                    rejected|expired|open",
               "terminal": true, "at": … } ],

  "reconciliation": {
      "as_of": …,
      "per_ticker": [ { "ticker": …, "target_notional": …, "actual_notional": …,
                        "discrepancy": …, "class": "OK|EXPLAINED|UNEXPLAINED",
                        "cause": "partial_fill|rejected|insufficient_bp|
                                  below_min_trade|none" } ],
      "verdict": "CLEAN|CARRY_FORWARD|HALT"
  }
}
```

Every field you listed has a home: expected → `intended_qty`; submitted → `submitted_qty`;
filled → `filled_qty`; rejected → `rejected_qty`; broker status → `broker_status`; actual vs
target → `reconciliation.per_ticker`; discrepancy handling → `class` + `cause`; failure logging
→ `error` plus `risk_checks` (a blocked intent is recorded, never silently dropped).

### 6.5 Phase rules

**INTENT** — pure function of (targets, current positions, prices). No broker calls. Fully
unit-testable offline. This seam is what makes the production path testable without network.

**RISK CHECK** — every intent passes all gates or is recorded `BLOCKED` with a reason: drawdown
halt (exists); max single-order notional as a fraction of portfolio value (new); stale-quote
guard on `ref_price_as_of` (new); buying-power sufficiency (partial); universe membership
(exists as the ignore-list); max orders per cycle (new circuit breaker).

**SUBMISSION** — one submission per intent, carrying its `client_order_id`. **No retry inside a
cycle.** A failed submission is recorded and left for next-cycle recovery; blind retry is how
duplicate exposure happens.

**FILL STATUS** — poll to terminal state with a bounded wait. DAY orders may legitimately remain
`open` at cycle end; recorded as `terminal: false`, never assumed filled. **Absence of fill
information is not evidence of a fill.**

**RECONCILIATION** — fetch actual positions, compare to targets, classify:

| Class | Condition | Response |
|---|---|---|
| `OK` | \|discrepancy\| < `_MIN_TRADE_FRAC` × buying_power | none |
| `EXPLAINED` | traces to a recorded partial fill, rejection, blocked check, or open order | carry forward with cause |
| `UNEXPLAINED` | a position no intent created, or a quantity mismatch with no fill record | **HALT** |

**NEXT-CYCLE RECOVERY** — next cycle reads the previous verdict first:

- `CLEAN` → normal cadence.
- `CARRY_FORWARD` → force a rebalance regardless of cadence, and do **not** advance
  `last_rebalance` for the incomplete cycle (fixes the `main.py:364-369` defect).
- `HALT` → refuse to trade; require an explicit human acknowledgement file. Same fail-closed
  posture as the existing corrupt-state handling.

**LOG** — one structured JSON line per phase transition alongside the existing human log. The
cycle ledger is the audit record; the log is the narrative.

### 6.6 Placement

New module `execution/reconciliation.py`; `execution/alpaca_executor.py` gains order-status and
order-lookup methods. `main.py` orchestrates phases and contains no reconciliation logic.
**Production execution imports nothing from `backtest/`.**

---

## 7. Consumer rules

### Algo — the monetization laboratory

May consume `maturity ∈ {research, production}`. A research-grade observation is a legitimate
hypothesis input for a laboratory.

**Two ladders, deliberately separate — this is the understanding/monetization split made
operational:**

```
MI maturity    research ──▶ production        "does this measurement earn its place?"
Algo status    IDEA ─▶ TESTING ─▶ PROMISING ─▶ VALIDATING ─▶ VALIDATED
                                               "can it be monetized after costs?"
```

A `production` MI signal is **not** a validated trading signal. A `research` MI signal **may**
become one. Independent, because they answer different questions.

Rules:

1. Every experiment records the `spec_version`, `as_of`, `available_at` and `maturity` of each
   observation consumed, in its Evidence record.
2. A research-grade input caps the experiment at `PROMISING` until its MI source reaches
   `production` — a trading rule cannot be validated on a measurement not yet trusted.
3. Backtests filter on `available_at`, never `as_of`.
4. Only a ledger entry at `VALIDATED` enters the production path, and it enters as a named
   strategy component, never as a raw MI field.

### Portfolio Management — the governed system

May **display** research-grade information as prose context.

Anything that changes portfolio behavior requires `maturity: production` **and** passes the
three-part litmus already at `ARCHITECTURE.md:174`: realized not anticipated; feeds a response
the mandate pre-committed independent of the signal; non-directional.

PM never consumes Algo output. Evidence flows to the ledger; the human reads it. **A backtest
Sharpe ratio is not an input to portfolio governance.**

---

## 8. Evidence flows backward

```
regime-detection ──▶ observation records ──▶ algo experiment ──▶ Evidence ──▶ RESEARCH-LEDGER.md
                                                                      │
                                                     (read by a human; never auto-consumed)
```

Evidence record at `algo-trading-bot/evidence/{hypothesis_id}-{date}.json`:

```jsonc
{
  "hypothesis_id": "ALGO-008",
  "test_design": "…",
  "fold_dates":  { "train": ["2010-01-01","2015-12-31"], "test": ["2016-01-01","2020-12-31"] },
  "n_variants": 37,
  "inputs_consumed": [ { "signal": "volatility", "spec_version": "1.0",
                         "maturity_at_time": "production" } ],
  "result": "…",
  "decision": "VALIDATED|PROMISING|REJECTED|NOT_RUN",
  "reason": "…"
}
```

**It is not** `new_regime`, `new_signal`, or `new_market_state`. Nothing in regime-detection
reads this directory. The only path from evidence back into Market Intelligence is a **human
opening a new research charter** under regime-detection's own process.

That human step is the circular-validation break. Automating it recreates exactly the loop the
charter's §5 warns against.

`n_variants` is mandatory — it is the multiple-testing record. 37 variants and one winner is a
different claim from 1 variant and one winner.

---

## 9. Research ledger design

`RESEARCH-LEDGER.md` at the workspace root. Markdown table. No database.

**Columns:** `ID · Hypothesis · Test · Result · Status · Reason · Evidence · Date`

**Status vocabulary** (charter §12): `IDEA · TESTING · PROMISING · VALIDATING · VALIDATED ·
REJECTED · DEPRECATED · REDUNDANT`.

**ID space:** `MI-*` · `ALGO-*` · `PM-*`. Externally-originated findings sit in a separate
table, marked external, and carry no internal ID until re-tested under regime-detection's
charter.

**Seed:** the 16 findings already documented in the audit, transcribed exactly. **No new
findings invented.** Eight are documented nulls — the ledger's whole value. A future agent
proposing "let's try a macro regime overlay" must hit `ALGO-003` (regime lags vol at every λ,
100% overlap) before writing code.

**Two entries are created by this plan**, recording the §3 dispositions so the archiving is
discoverable: the `regime/` gauge archive and the directional-HMM archive, each citing its
evidence and noting that the *question*, not the code, is what may move upstream.

**Caveat:** the workspace root is not a git repository, so a root-level ledger is versioned by
the Obsidian vault only. Options — (a) accept vault-only history, or (b) keep the canonical copy
in `regime-detection/` and mirror to root. **Recommend (a):** the ledger is a human-read index
whose entries cite evidence that *is* in git, and (b) reintroduces the cross-repo ownership
question the architecture avoids.

---

## 10. Documentation correction list

**No edits performed.** Every row verified against code.

| Document | Incorrect claim | Actual implementation | Required correction |
|---|---|---|---|
| `C:\dev\CLAUDE.md` | Repo table lists all four repos at `C:\dev\<repo>` | Three internal repos at `C:\dev\systematic-investing-research\<repo>`; `vol-diagnostics` at `C:\dev\vol-diagnostics` | Update all four paths; record that three form the charter-governed stack and `vol-diagnostics` is separate |
| `algo-trading-bot/CLAUDE.md` | "A **single** 16-ETF universe" + the 16 tickers | `config.py:63` defines **8**: SPY QQQ IWM XLE XLU TLT SHY XLRE | Correct to 8 and the actual tickers |
| `algo-trading-bot/CLAUDE.md` | Concentration narrative assumes the 16-name basket | `MOMENTUM_TOP_N = {"HIGH_VOL": 4}` out of 8 | Correct |
| `algo-trading-bot/CLAUDE.md` | Frames the repo as "Regime-aware ETF trading bot" with the gauge as a first-class component | Under the locked architecture the repo is the **monetization layer** and owns no market-state model | Rewrite the framing section around the six monetization questions (§2) |
| `algo-trading-bot/.planning/STATE.md` | References `backtest/discovery_loop/` and `backtest/repro_gupta/model.py` | **Neither directory exists.** Real code is `backtest/overlay/` and `backtest/hmm/` | Correct both paths, or mark the v9 plan superseded |
| `algo-trading-bot/.planning/STATE.md` | `status: milestone_complete`, `percent: 100` | 4/5 phases; Phase 59 "Not started"; uncommitted divergence since 2026-07-09 | Set status to reflect the incomplete milestone |
| `algo-trading-bot/algo-trading-bot.md` (hub) | "Status: ready_to_plan" | `STATE.md` says `milestone_complete` | Reconcile; regenerate the hub block |
| `algo-trading-bot/algo-trading-bot.md` (hub) | Cites `docs/research_spine.md` as "current product direction" | That document is a Canadian ETF portfolio crash-defense ladder — governance, not monetization | Remove the citation (doc is DELETE per §3) |
| `algo-trading-bot/outputs/models/FROZEN.md` | "Spikes kept: `backtest/risk_appetite_spike.py`, `backtest/risk_appetite_causal_spike.py`" | **Both absent** — verified | Remove the claim or restore from git history |
| `portfolio-manager/ARCHITECTURE.md:303` | "`collect_regime_card()` → optional row in the daily brief; degrades to `None`. ✓" | Imported by nothing; never called; fetches a parked blank | Remove the claim and the check mark; state no regime seam is wired |
| `portfolio-manager/ARCHITECTURE.md:47-50` | "The seam is `regime_card.json`, consumed one-directional and read-only" | No consumer exists | Reword as the *intended* future seam (§5), explicitly not yet built |
| `portfolio-manager/portfolio-manager.md:28` | "`regime_card.json` consumed read-only, degrades to None" | Not consumed | Correct |
| `portfolio-manager/README.md:29` | "regime-detection's regime_card.json ──optional sensor, read-only──▶" | Not consumed | Correct the diagram |
| `portfolio-manager/NOTES.md:198` | "`src/regime.py` fetches regime-detection's `regime_card.json`" | True of the function, misleading about the system | Add "(orphaned — no caller)" |
| `regime-detection/CLAUDE.md` | "`results/regime_card.json` is a deliberate parked blank until Phase 10" | **Accurate** | — (confirm the Phase-10 reference survives §5) |

Not verified, therefore not listed as errors: all test-count claims (regime-detection 26,
portfolio-manager 103–105). Confirm by running the suites before citing them.

---

## 11. Migration order and dependencies

```
Step 0  Documentation corrections (§10)                       no deps
           │
           ├──────────────────────────────┬──────────────────────────┐
           ▼                              ▼                          ▼
Step 1  Algo strip-down (§3.3)    Step 2  PM disposition (§4)   Step 3  MI history +
        archive / delete                  delete / move                 contract v1 (§5)
           │                              │                          │
           ▼                              │                          ▼
Step 4  Algo reconciliation (§6)          │                  Step 5  Consumer vendoring
        ★ money-touching                  │                          + checksum tests
           │                              │                          │
           └──────────────┬───────────────┴──────────────────────────┘
                          ▼
Step 6  Research ledger seeding (§9)
                          │
                          ▼
Step 7  Evidence record schema + first emission (§8)
```

| Step | Depends on | Why |
|---|---|---|
| 0 | — | Docs describe three architectures for one repo; any later step read through them starts wrong. Zero risk. |
| 1 | 0 | Archiving while `STATE.md` points at non-existent directories guarantees confusion. Gated on D-1. **Now a strip-down, not a reorganization** — the `overlay/` dispositions fold in here rather than deferring, because §3.3 judged them all against one criterion. |
| 2 | 0 | Independent of 1 — different repo, no shared code. Parallelizable. |
| 3 | 0 | Producer-side only. Independent of 1 and 2. |
| 4 | 1 | Both touch `main.py`; wrong order means editing the same file twice with a behavior change between. **Deliberately independent of 3 and 5** — the money-touching fix must not be gated on interface work. |
| 5 | 3 | Cannot vendor a schema that does not exist. |
| 6 | 1, 2 | The ledger records the dispositions, so it is seeded after the verdicts are real. |
| 7 | 3, 5, 6 | An evidence record cites `spec_version` and a `hypothesis_id`; both must exist first. |

### Decisions — RESOLVED and locked 2026-08-09

- **D-1 — Does the live bot lose its regime input? → YES, and it is not replaced.** Archiving
  `regime/` drops regime-conditional cadence and HIGH_VOL concentration. The proposed
  equal-weight fallback is **rejected**: it is an unvalidated rule inherited from a deleted
  system, and preserving it would defeat the cleanup. Equal-weight survives only as a backtest
  baseline. **The strategy slot is emptied; the bot does not trade until something clears the
  admission gate.** (§3.5)
- **D-2 — Does the daily regime report email stop? → ARCHIVE, not delete.** The email stops when
  its cron is disabled in Step 0, but `scripts/daily_regime_report.py` moves to
  `archive/regime-gauge-v7/` intact and is recoverable if MI's presentation layer takes longer
  than expected.
  **⚠ OVERRIDDEN IN EXECUTION, 2026-08-09 (recorded 2026-08-10).** Step 1 deleted the script and its
  cron rather than archiving them, under the blanket "gone not fixed" instruction. D-2's *intent* —
  that the capability be recoverable, not destroyed — still holds and is still satisfied, but by **git
  (`b1f3fa3e`) instead of by an on-disk archive**. Restoring it is a `git show` away, not a file move.
- **D-3 — Sequencing risk on the live bot. → PAUSE `trading.yml` now.** All three crons
  (morning report + two trade windows) are disabled **in Step 0**, before any code changes. This
  is now the first action in the plan.

### What D-1 and D-3 change about the ordering

Pausing the crons in Step 0 removes the live-trading risk that previously constrained the
sequence. Two consequences:

1. **Steps 1 and 4 are no longer racing an unattended live system.** They can proceed at a
   normal pace with the bot cold.
2. **Reconciliation (Step 4) changes character.** It is no longer an urgent fix to a live
   money-moving path — it becomes a **precondition for ever turning the bot back on.** No
   validated strategy may go live until the reconciliation spine exists, because a strategy
   that cannot verify its own fills cannot produce trustworthy evidence about itself.

Revised first action:

```
Step 0a  Disable all three crons in algo-trading-bot/.github/workflows/trading.yml
Step 0b  Documentation corrections (§10)
```

Step 0a is the only change to a workflow file anywhere in this plan, and it is a pause, not a
deletion — the file and its schedule lines are retained, commented, with a dated reason.

---

## 12. Files that will NOT be touched

### Entire repositories

- **`C:\dev\vol-diagnostics`** — every file. Not audited, not modified, not referenced by any
  code this plan produces.

### regime-detection

- `results/{stage1.csv, stage1_run.log, oos_labels.csv, construction_gate.csv,
  sensor_validation.*, synthetic_validation.*}` — frozen one-look evidence.
- `results/{vol_validation.txt, valuation_validation.txt, stockbond_validation.txt}` — frozen
  one-look outputs.
- `archive/**` — `research-v1/`, `jumpmodel-v2/`, `internals-gauge/`, `dropped-signals/`.
- `data/processed/**` and `MANIFEST.csv` — provenance-tracked panels.
- `.planning/framework/**` — the frozen v1.0 signal framework.
- `scripts/causal.py` — the shared causal spine and `assert_causal`.
- `results/regime_card.json` — stays parked. Not repopulated, not deleted, not reused as the
  new interface.
- **No code arrives here from `algo-trading-bot`.** Only a question may be re-homed, and only
  through a new research charter.

### algo-trading-bot

- `.holdout-quarantine/**` — ~~`HOLDOUT.lock` stays sealed.~~ **Corrected 2026-08-10: the lock has
  read `status: UNSEALED, touched: true` since 2026-06-18 (`3b4fdca1`) over `2020-01-01 → present`.**
  It was already unsealed when this plan was written; the plan was wrong, not the lock. The rule that
  actually applies: **leave it exactly as it reads and never re-seal it to tidy the record.** The
  operative consequence is that no historical window is clean, so the only virgin data is prospective.
- ~~`outputs/models/*.joblib` — the 8 frozen artifacts, archived with their code, never
  retrained.~~ **Moot 2026-08-10: `outputs/models/` no longer exists** — the artifacts and `FROZEN.md`
  were deleted in Step 1 under the "gone not fixed" override, recoverable at `b1f3fa3e`. See the §3.3
  preamble. Nothing here to protect, and nothing that can be retrained by accident.
- `logs/**` and `outputs/bot_state.json` — live operational state.
- `docs/ARCHITECTURE-AUDIT.md`, `docs/PRE-REGISTRATION.md`, `docs/AUDIT-2026-07-05.md` — the
  written record of why the rotation strategy failed honest testing.
- `backtest/data/*.parquet` — the price cache.
- `.planning/spikes/**` READMEs and result plots — research history, archived intact.

### portfolio-manager

- `MANDATE.md` — the IPS. Policy changes only through its own governance process.
- `src/questrade.py` and the token-handling guards — hard-won CI/local single-use-token
  protections.
- `src/{governance,instruments,cache,mailer,holdings_watch,performance,data_provider}.py` and
  `src/portfolio/_legacy.py` — the governance spine.
- `scripts/daily_report.py` — except removal of dead `market_sentiment` references surfacing in
  Step 2. **The live daily brief keeps sending throughout.**
- `src/market_sentiment.py::get_indicator_snapshot()` and its private helpers.

### Everywhere

- No `.git` history rewriting. Every deletion is recoverable from git.
- No changes to any `.github/workflows/**` except **`algo-trading-bot/trading.yml`**, whose
  three cron lines are commented out in Step 0a with a dated reason (D-3). The file, its jobs,
  and its `workflow_dispatch` trigger are retained so the bot can be run manually and resumed
  by uncommenting. `portfolio-manager/daily-report.yml` keeps sending throughout.
- No dependency-manager migrations. `requirements.txt` stays.

---

## Success criterion

```
Observe → Measure → Validate → Experiment → Evidence → Govern
```

- **regime-detection understands.** It is the only repository that models market state, and it
  admits new modelling only through its charter.
- **algo-trading-bot monetizes.** It owns no market model. It takes validated understanding and
  proves — or fails to prove — that the understanding contains an exploitable relationship
  after costs, constraints, and out-of-sample testing. Most candidates fail, and that is the
  expected outcome.
- **portfolio-manager governs.** It never asks what the market will do.

Each repository can be cloned, read, and tested alone. None imports another. Information
crosses as versioned, point-in-time observation records; evidence flows back as records a human
reads. **There is no step where an observation silently becomes a trading decision.**
