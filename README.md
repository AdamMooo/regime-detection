# Regime Detection

**A market-signal observatory.** `market data → independent validated signals → historical context → regime relevance → STOP.`

Each signal is a standalone research module that measures one market mechanism, states how unusual the current
reading is against its own long history, and names the abstract market assumption the reading bears on. The system
stops there. The intelligence is in the quality of each individual signal, never in combining them into a score.

## The boundary (read this before anything else)

**This is a measurement layer, not a trading or decision system.** It does not decide, recommend, or imply any
investment action — no exposure changes, cash calls, instrument selection, tilts, or one-word "risk-on/risk-off"
summaries. A single label destroys the information: a market can be low-vol but fragile, cheap but illiquid, so the
full multi-signal vector is preserved and presented. The code knows nothing about capital deployment or
implementation; it knows only which *abstract market assumptions* to monitor ("bonds hedge equity drawdowns", "the
index is genuinely diversified", "funding markets function"). Decisions live downstream — a separate system and a
human. Full statement: `CLAUDE.md` (HARD BOUNDARY) and `.planning/PROJECT.md`.

Prohibited by name (`.planning/REGIME-SENSOR-ARCHITECTURE.md` §"Objective restatement", 2026-08-06): market-timing
labels · predictive models without economic justification · weights optimized on historical returns · composite
scores designed to maximize backtests. No backtesting engine (vectorbt / backtrader / zipline / bt) enters this
repo — a fast sweep-over-returns affordance is exactly what pulls a project toward "optimize until it forecasts."

The boundary is enforced in code, not by convention — see `scripts/signal_output_schema.py` and
`tests/test_boundary_audit.py` below.

## What is actually being claimed

The individual signals are *expected* to be mostly known relationships: volatility clustering (Engle 1982),
valuation → long-horizon returns (Campbell–Shiller 1988), absorption (Kritzman et al. 2011), the excess bond
premium (Gilchrist–Zakrajšek 2012). Reproducing them is the pass condition of a measurement instrument, not a thin
result. What is uncommon is doing it **point-in-time, causally, out-of-hypothesis-sample, across regions, for
several mechanisms at once** — the published versions are typically in-sample, US-only, and single-signal.

The edge hypothesis is **not** "signal X predicts the market." It is: *multiple validated measurements of different
market mechanisms give a more complete assessment of market state than any single indicator.* Whether the joint
configuration of the sensor set says anything is a question deliberately deferred until the set exists (Phase 10);
it is not to be pre-empted signal by signal.

## Signal set and status

Nine signals were scoped; crowding was dropped 2026-08-05 (proxy-only construction, real positioning data
infeasible solo, and it risks re-reading the volatility axis). Status as of **2026-08-06**:

| # | Signal | Assumption / question it monitors | Status |
|---|---|---|---|
| 1.5 | **Volatility** | how large is uncertainty, how unusual, how durable (a context axis, not an assumption monitor) | **Complete.** Charter signed off 2026-08-05; one-look run 2026-08-05 (`results/vol_validation.txt`), V2–V5 pass, no reject condition tripped; results signed off dated 2026-08-06. Maturity derived = `production`. Level-0 record at `results/vol_level0.json`. |
| 2 | **Stock-bond correlation** | "bonds hedge equity drawdowns" | Built and US-validated 1962–2026; refactored onto the shared spine 2026-08-06 (`build(panel)`, region-agnostic). **Charter frozen 2026-08-06, sign-off pending; the Japan/Germany run has NOT been made.** Registered limitation: the international panels start 1990-07, so the out-of-sample period does not contain the 1970s–80s inflation regime — `research` is this phase's maturity ceiling. |
| 3 | **Valuation** | "equities are priced for normal forward returns" | Charter frozen 2026-08-03 (`.planning/phases/03-valuation-signal/03-VALUATION-CHARTER.md`), sign-off pending, no data look spent. |
| 4 | **Concentration** | "the index is not dependent on a few names" | Warm start only: kickoff brief + data (French VW−EW leadership spread from `assets_daily.csv`; true cap-HHI needs paywalled constituents). |
| 5 | **Diversification / absorption** | "diversification is intact" | Warm start only: absorption ratio via PCA of the `assets_daily.csv` panel. Scoped narrow — the lead is the whole justification. |
| 6 | **Credit (EBP)** | "credit conditions are benign" | Warm start only: `scripts/build_credit.py` → `credit_monthly.csv` (Fed EBP 1973+, restated monthly = PIT caveat), `credit_daily.csv` (OAS proxies 1986+). |
| 7 | **Funding stress** | "funding markets function" | Warm start only, narrow binary flag: `scripts/build_funding.py` → `funding_weekly.csv` (STLFSI4/NFCI), `funding_daily.csv` (CP−bill, SOFR−EFFR). LIBOR→SOFR splice hazard noted. |
| 8 | ~~Crowding~~ | — | **DROPPED 2026-08-05.** (`.planning/ROADMAP.md` still lists it; not yet reconciled.) |
| 9 | **Tail** | "the distribution is its normal shape" | Warm start only: `scripts/build_tail.py` → `tail_daily.csv` (CBOE SKEW 1990+ and VIX term slope). SKEW methodology-rebasing caveat. |
| 10 | Presentation / assumption ledger | — | Not started. Organizes validated signals into lenses; no score, no summary, no decision. |

"Warm start" means a Stage-0 gate + kickoff brief (`.planning/phases/NN-*/NN-CHARTER-KICKOFF.md`) and the data
pulled — **not** a charter, not a build, not a validated signal.

## Shared infrastructure

The Definition of Done is identical for every signal, so its machinery is built once (D-20) rather than once per
signal:

- **`scripts/causal.py`** — the causal primitives every signal imports: `ewma_vol` (RiskMetrics/IGARCH),
  `realized_vol`, `expanding_percentile`, `expanding_z`, `downside_features`, plus `assert_causal`, the
  perturb-the-future check a signal's `build` must pass before its one-look. Every function here uses data through
  `t` only; if a function needs the future it does not belong in this module.
- **`scripts/run_oos.py`** — the generic out-of-hypothesis-sample harness. Given any signal's
  `build_region(returns) -> DataFrame`, it runs the identical construction over US / Japan / Europe panels (all
  share a `date,mkt_ret` schema). It runs the construction and asserts nothing; interpretation stays with the
  caller's one-look.
- **`scripts/signal_output_schema.py`** — the executable boundary: a closed Level-0 field allowlist plus a
  forbidden-vocabulary denylist and `validate()`. A Level-0 record may contain only the enumerated fields.
- **`tests/test_boundary_audit.py`** — asserts no decision-shaped or composite-scalar field is ever emitted. On the
  day it was written it caught a real leak that every prose "reviewed grep" had missed. It now carries **no
  exceptions**: the one deferred entry (`gauge.position`) was resolved 2026-08-06 by retiring the card's generator
  rather than renaming the field — the leak came from the retired state, so deleting the state deleted the leak.
- **`tests/test_causal.py`** — the look-ahead guard: it perturbs future values and demands past values do not move,
  and includes a test proving the guard itself catches a deliberately leaky function.
- **`tests/test_reproducibility.py`** — every test in it exists because the corresponding failure actually
  happened here: imports missing from `requirements.txt`, a committed result artifact whose columns disagreed with
  the code that produces it, `assert_causal` existing but nothing forcing a signal to use it.
- **`scripts/data_manifest.py`** → `data/processed/MANIFEST.csv` — sha256, shape and date span of every processed
  panel, so a result can be tied to the bytes it was computed from. French restates, FRED revises, SKEW gets
  rebased, yfinance back-adjusts; a filename is not a dataset identifier. It is a record, not a lock — regenerate
  and commit it alongside any data refresh.

`pytest` → **26 passed** (`pytest.ini` scopes collection to `tests/`).

## Research discipline

- **Charter first (D-15).** Every signal pre-registers six questions — mechanism, measurement, validation bars
  (V1…), reject conditions (R1…), and the boundary prohibition — *before* any implementation.
  Templates: `.planning/framework/research-charter-template.md`, `.planning/framework/signal-spec-template.md`.
- **Stage-0 relevance gate.** Five questions, default NO, leave-one-out marginal-information test. No charter is
  opened for a candidate that fails it. The observatory is a curated set, not an indicator library.
- **Mechanism gate.** A signal needs a written structural reason it survives being known. Novelty or a good
  backtest is disqualifying as the sole basis.
- **Causal / point-in-time only.** Trailing or forward filtering, expanding or trailing windows, no look-ahead;
  macro series get revised, so vintage matters.
- **Out-of-hypothesis-sample confirmation on Japan/Europe** before any SUPPORT claim, or a documented failure.
- **One look, plus overnight cooling-off and an explicit dated sign-off** for any positive claim. Never inferred
  from a conversational go-ahead.
- **Honest reporting.** Statistical orthogonality is a diagnostic, not the gate (signals that correlate but are
  mechanistically distinct are kept); every historical-context statistic gets a confound check; the maturity tag is
  *derived* from the admission model, never asserted.

Governing docs: `.planning/framework/` (frozen v1.0 2026-08-03, currently v1.1 after the Stage-0 gate amendment —
the spec every signal declares against) and
`.planning/REGIME-SENSOR-ARCHITECTURE.md` (the system design). Where they differ, the framework governs.

## Repo layout

All code is flat in `scripts/` (there is no `src/` package).

**Shared spine:** `causal.py` · `run_oos.py` · `signal_output_schema.py`

**Signal modules**
- `vol_descriptors.py` — the volatility measurement spine: EWMA level, expanding-percentile rarity, and
  GARCH(1,1)-t shock persistence (half-life = ln0.5 / ln(α+β), trailing ~5y window, NaN when α+β ≥ 1).
- `vol_read.py` — presentation of the volatility signal (level/percentile · drift · rarity · durability) + figure.
- `validate_vol.py` — the volatility one-look (charter V2–V5) → `results/vol_validation.txt`.
- `vol_level0.py` — emits the volatility signal's Level-0 historical-context record
  (`results/vol_level0.json`), generated from the committed descriptor artifact and passed through
  `signal_output_schema.validate()` so the boundary is enforced by the allowlist rather than by care.
- `stockbond_corr.py` — causal trailing equity/10y-bond correlation, its sign read as the state of the
  bonds-hedge-equities assumption → `results/stockbond_corr.csv`, `results/stockbond_context.csv`.
**Provenance** — `data_manifest.py` → `data/processed/MANIFEST.csv`

**Data builders** — `build_panel.py` (Ken French daily US market TR 1926+, SPY cross-check) · `build_assets.py`
(multi-asset incl. 10y bond and gold) · `build_intl_panel.py` (Japan/Europe equity panels) ·
`build_intl_bonds.py` (JGB / Bund monthly 10y TR) · `build_credit.py` · `build_funding.py` · `build_tail.py` ·
`build_ohlc_panel.py` (range-based estimator inputs) · `build_trend_proxy.py`.

**Archived, not in the signal path** (2026-08-06) — `scripts/` now contains only data builders and the signal
spine. The retired K=2 jump-model program moved to **`archive/jumpmodel-v2/`** and the market-internals gauge to
**`archive/internals-gauge/`**. Each carries a README recording *what was learned* and why it is parked; read
those before reviving anything.

The jump model is worth knowing about even though it is retired, because the current design is a reaction to how
it failed: the label was an excellent *instrument* (100.0% stability under ±2y window shifts) that lost every
economic use to something simpler, because causal filters lag the regime by 5–20 days. And
`results/detector_benchmark.csv` showed a plain causal vol threshold with hysteresis matching or beating it on
precision, recall and BAC at both bear datings with shorter lag — **thresholding a continuous quantity piles the
error at the boundary and discards the graded information in σ.** That is why the volatility signal is now
continuous descriptors, and why "no single-word regime summary" is a standing rule here.

Its live pipeline (`live_label.py`, `regime_signal.py`, the weekly GitHub Action) was **deleted** rather than
archived — nothing consumed it. `results/regime_card.json` is now a deliberate **parked placeholder**: serving a
retired reading is worse than serving nothing. It stays blank until the observatory can fill it (Phase 10).

The one piece kept out of the archive is `build_features` (EWM downside deviation + Sortino), lifted into
`causal.py` as `downside_features` because it is a generic causal return descriptor and `build_panel.py`'s
construction gate keys off `dd10`. The move was verified bit-identical, so `market_daily.csv` is unchanged.

## Quickstart

Python 3.13 (`runtime.txt`).

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

```bash
pytest                            # 50 tests — causal guard, boundary audit, reproducibility, estimator core
python scripts/vol_descriptors.py # rebuild the volatility measurement spine + figure
python scripts/vol_read.py        # the human-facing volatility read
python scripts/vol_level0.py      # emit + schema-validate the volatility Level-0 record
python scripts/stockbond_corr.py  # stock-bond correlation signal + its historical context
python scripts/data_manifest.py   # refresh the processed-data provenance manifest
```

Rebuilding data from source needs network but **no credentials**. `build_panel.py` uses the public Dartmouth
French files + yfinance; `build_assets.py`, `build_credit.py` and `build_funding.py` use FRED's key-free
`fredgraph.csv` endpoint; `build_tail.py` pulls CBOE index history directly. `build_intl_bonds.py` is the only
script that will *use* a `FRED_API_KEY` if one is present in `.env`, and it falls back to the key-free endpoint
when it is not.

`results/` ships with the current artifacts, so a fresh clone can read every number offline —
see `results/README.md` for what is frozen and what is regenerable.

## History

Two programs were retired out of this repo; both are recoverable in git history and neither is being revived.

- **v1** — a sticky HDP-HMM plus four successor formulations, five preregistered nulls. Converged, sealed at git
  tag `v1-convergence`; code inert in `archive/research-v1/`.
- **v2** — the K=2 statistical jump-model program (chapters 1–3). Chapter 1 closed 2026-07-23: "switching beats
  buy-and-hold" was an exposure artifact. Chapter 2 closed the same day as a registered null. The probability layer
  was killed on a calibration gate. The one-look for chapter 3 was deliberately never spent. The chapter-1/2
  evidence stays frozen in `results/`; the runners were removed 2026-07-27.
- The **equity-ownership program** (a separate concern entirely) was removed from this repo 2026-08-02.

The durable newest-first narrative is `RESEARCH-RECORD.md`. Current session state is `NOTES.md`.
