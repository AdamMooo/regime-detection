# Claude Context — Regime-Detection

**Read NOTES.md first** — current state and next action.

## System context — one of three independent repositories

**This repo stands alone.** It clones, installs and tests by itself. There is no shared parent
directory, no relative path out of this repo, and no code dependency on the other two in either
direction. Clone the three wherever you like, in any layout.

| Repo | Role | Its question |
|---|---|---|
| **regime-detection** ← you are here | MARKET INTELLIGENCE · UNDERSTANDING | *What is happening in the market, how unusual is it, how has this environment behaved?* |
| [algo-trading-bot](https://github.com/AdamMooo/algo-trading-bot) | MONETIZATION | *Can that understanding be turned into returns after costs and out-of-sample?* |
| [portfolio-manager](https://github.com/AdamMooo/portfolio-manager) | GOVERNANCE | *Given my policy and constraints, what portfolio behavior is permitted?* |

Shared governance documents live in **this repo**, under `governance/` — the
[charter](governance/SYSTEM%20ARCHITECTURE%20%2B%20RESEARCH%20CHARTER.md),
[implementation plan](governance/IMPLEMENTATION-PLAN.md),
[research ledger](governance/RESEARCH-LEDGER.md) and
[migration runbook](governance/MIGRATION.md). They are stored here because this is the repo
guaranteed to be present — **storage, not ownership.** This repo does not own the ledger's
`ALGO-*` or `PM-*` rows, and **no code here reads the ledger.**

### What crosses this repo's boundary

**Out (this repo produces):** versioned, point-in-time observation records — `contracts/` holds
the schema, `observations/<signal>/<as_of>.json` the history. Both `as_of` and `available_at` are
mandatory; consumers filter on `available_at`. `maturity` is the only behavior-bearing field.

**In: nothing.** This repo consumes no output from the other two. The only path from their
evidence back to here is **a human opening a new research charter** under this repo's own
process — never an automated read. Automating it would create the circular validation the
charter's §5 forbids.

**Never:** an allocation, exposure, position, order, trade, tilt or recommendation — enforced
executably by `scripts/signal_output_schema.py` and `tests/test_boundary_audit.py`. Code arriving
from another repo without a mechanism gate, preregistration, causal guard and out-of-sample
confirmation does not become Market Intelligence by being moved. **A question can be re-homed
here; unfinished code cannot.**

## HARD BOUNDARY — a market-UNDERSTANDING layer only (Adam, non-negotiable, corrected repeatedly)

This repo **finds, validates, and presents independent market signals + their historical context**, and STOPS:
`market data → independent signals → historical context → regime relevance → STOP.`
It does **NOT** decide, recommend, or imply any investment action — no allocation, exposure changes, cash calls,
ETF selection, sleeves, tilts, or "risk-on/risk-off" one-word summaries (a single label DESTROYS the
information; preserve the full multi-signal complexity — a market can be low-vol but fragile, cheap but
illiquid). It must **not know or reference any capital-allocation or implementation detail** (weights / sleeves /
tilt budgets / deployment) — only which ABSTRACT MARKET assumptions to monitor ("bonds hedge equity drawdowns",
"the index is diversified", "factor premia aren't crowded"). Investment decisions live in a SEPARATE system +
the human. Value = fewer blind spots for the human's judgment, never prediction or decisions. **The word
"portfolio" and every allocation/implementation concept stay OUT of this repo — zero references.**

**One documented exception, and only one: VENDOR IDENTIFIERS.** Ken French's filenames and block headers
literally contain the word (`25_Portfolios_5x5_CSV.zip`, `Number of Firms in Portfolios`,
`{Region}_25_Portfolios_ME_BE-ME_daily_CSV.zip`). You cannot fetch or parse the data without writing them.
These are **source identifiers, never concepts** — the same class as `signal_output_schema.py` naming forbidden
words as denylist data. This is why `tests/test_boundary_audit.py::test_no_script_imports_allocation_system`
scans **import lines**, not all text: the rule that matters is that no code here reaches for a decision system,
not that a vendor's spelling is scrubbed. Do not "fix" these strings; do not treat them as licence to use the
concept.

## What This Project Is

A **market-signal research system.** Each signal is an independent research module answering: *what is happening ·
how unusual is it · how has this environment behaved historically · which market assumption does it relate to* —
then STOP. The intelligence is in the quality of each individual signal, not in combining them into one score.
Governing design: **`.planning/REGIME-SENSOR-ARCHITECTURE.md`** (signal set, per-signal spec, validation
standards, maturity model, the assumption-ledger output — organized so the human connects the dots).

**The signal set** (each monitors one abstract market assumption): volatility/risk-off (shipped), stock-bond
correlation (shipped), valuation, concentration, credit (EBP), tail. **Absorption · funding · crowding were
DROPPED at the charter stage** (`.planning/archive/dropped-signals/`) — the gate working, not attrition.
Orthogonality evidence in the `sensor-orthogonality-evidence` memory.

**History note:** the equity-ownership / allocation program (constitution, offense/defense studies, factor,
momentum) was REMOVED from this repo 2026-08-02 — a separate concern; recoverable in git history if needed.

## File Map

**Shared signal infra (built ONCE, D-20 — every signal reuses it):**
- `causal.py` — causal primitives (`ewma_vol`, `realized_vol`, `expanding_percentile`) + **`assert_causal`**, the
  perturb-the-future look-ahead guard every signal's `build()` must pass before its one-look.
- `run_oos.py` — generic Japan/Europe out-of-hypothesis-sample harness over any `build_region(returns)`.
  `load_region` (daily) · `load_region_monthly` (month-end, compounded) — pass the latter as `loader=` for a
  signal on the monthly clock.
- `signal_output_schema.py` — executable HARD BOUNDARY (closed Level-0 allowlist + denylist + `validate()`).
- `data_manifest.py` → `data/processed/MANIFEST.csv` — sha256/shape/date-span provenance for every panel.

**Volatility signal (Phase 1.5, COMPLETE — signed off 2026-08-06, maturity `production`):**
- `vol_descriptors.py` (measurement spine: level · rarity · drift · GARCH half-life) · `vol_read.py`
  (presentation) · `validate_vol.py` (the frozen one-look → `results/vol_validation.txt`) · `vol_level0.py`
  (emits + schema-validates `results/vol_level0.json`).

**Stock-bond correlation signal (Phase 2, COMPLETE — signed off 2026-08-07, maturity `research`):**
- `stockbond_corr.py` — `build(panel)` / `build_monthly(panel)` over a region-agnostic `(eq, bond)` schema, on the
  shared spine · `validate_stockbond.py` (the frozen one-look → `results/stockbond_validation.txt`) ·
  `stockbond_level0.py` (emits + schema-validates `results/stockbond_level0.json`).

**Presentation layer, THE PRODUCT (Phase 10, plan 10-02 — the informativeness map):**
- `informativeness_map.py` → `results/informativeness_map.{json,html}`. **This is the output object;
  the assumption ledger is a SECTION inside it.** Every axis is a first-class row whether or not it
  carries a status, because the `{intact|under_test|violated}` vocabulary is only honest for a quantity
  with a mechanical boundary and **exactly one here has one** (correlation sign) — volatility,
  concentration and tail each refused a status in their own charters, and those refusals stand.
- **Two independent dimensions per axis, never merged, no one-word axis summary.** `standing` = what
  the axis says about the world now (its declared status, plus the tail mass beyond the reading,
  `min(p, 1-p)`, against the tail **the axis itself declares** in `extreme_conditions.threshold_percentile`
  — this module owns no threshold, same discipline as `status_of`). `novelty` = whether the reading
  changed (the trend descriptor its signed charter registered, how long its status has held, how long
  since it was last inside its tail; **bands nothing**). `persistence` is context for BOTH and never a
  rank: "52 months in, median 52, longest 129" makes today's print unsurprising **and** says the
  situation still is not holding. Nothing is sequenced, grouped or styled by either dimension —
  alphabetical only — so an axis with extreme standing and zero novelty stays as prominent as any other.
- **Concentration renders as a CANDIDATE**, in its own list and its own dashed-border section: charter
  UNSIGNED, no validation bar run, `maturity: null`, reading **recomputed** by `concentration.build()`
  because no `observations/concentration/` log exists, and **excluded from `--known-at` replay** for the
  same reason. It carries `promotion_requires` naming what Adam must rule. `EMITTERS` is untouched, so a
  candidate cannot reach the admitted set.
- Causal by construction: every percentile was ranked expanding-only at its own date, every summary is
  taken over the log **as filtered to `known_at`**, and a past map is not revised by later data.
  `build()` is under `assert_causal`. **No forward-looking statistic anywhere** — the tail charter's
  registered constraint is carried verbatim and enforced by a forward-looking-key test over both
  artifacts.

**Presentation layer (Phase 10, plan 10-01 — Level 0 + Level 1 only):**
- `assumption_ledger.py` — reads the **current view** of each admitted signal's
  `observations/<signal>/history.ndjson` (never the `results/*.csv` spines, never a recomputation) and
  renders Level 0 (the state vector) + Level 1 (the ledger) to `results/assumption_ledger.{json,html}`.
  Assumption text, status and its `derivation` are carried **verbatim** from the record: this module owns
  **no thresholds**, and a monitor signal with no declared `{intact|under_test|violated}` mapping RAISES
  rather than getting one invented for it. A signal whose `assumption_monitored` opens `N/A because ...`
  (the contract's own discriminator) is carried as a **reading with no status** — volatility, by charter.
  Artifacts carry no wall-clock stamp, so a test can assert they still equal a fresh build.
- **Level 2 is NOT built.** The seam is `assumption_ledger.level2_context()` — joint rarity + analogues
  attach there and nowhere else. No distance is computed anywhere in this repo.
- `mailer.py` (stdlib `smtplib`/`email`; **reimplemented**, not imported from another repo) + `send_ledger.py`
  (**`--dry-run` is the default and works offline with no credentials**; `--send` logs and skips when
  `LEDGER_EMAIL_ADDRESS` / `LEDGER_EMAIL_APP_PASSWORD` are absent, so a missing secret never fails a run).
- `.github/workflows/assumption-ledger.yml` — `schedule:` **commented out with a dated reason**,
  `workflow_dispatch` retained. Adam enables the schedule.

**Data builders:** `build_panel.py` (US market TR + the construction gate) · `build_assets.py` (multi-asset incl.
bond10/gold) · `build_intl_panel.py` (Japan/Europe equity) · `build_intl_bonds.py` (JGB/Bund monthly) ·
`build_credit.py` · `build_tail.py` · `build_ohlc_panel.py` (Parkinson inputs) ·
`build_trend_proxy.py`.

**`contracts/` — the versioned observation schema (what crosses the boundary OUT):**
- `market-observation-v1.schema.json` + `CHANGELOG.md` + `vectors/{valid,invalid}` (21 conformance vectors, each
  invalid one naming the rule it breaks). Consumers **vendor** a pinned copy with a sha256 assertion — no Python
  import, so drift shows up as a red test in the consumer. `tests/test_contract_conformance.py` runs every vector
  through BOTH the JSON Schema and `signal_output_schema.py` and requires the same verdict.
- `.gitattributes` pins `contracts/** observations/** text eol=lf` and `data/vintages/** -text`; without it the
  same commit hashes differently per platform and the vendoring mechanism breaks silently.

**`observations/<signal>/history.ndjson` — append-only point-in-time history (`scripts/observation_history.py`):**
- One NDJSON log per signal on the **`available_at` vintage grid** (not the `as_of` grid — 22× redundant, and an
  `<as_of>.json` path cannot hold a correction). Lines are canonical JSON, so `sha256(line)` is the hash
  `MANIFEST.csv` records and the hash `supersedes` cites. Same key + different content is **refused**.
- Correction path: `corrections_for()` appends a NEW record with `available_at = now` and `supersedes` = the
  superseded sha256; **`current_view()` (latest `available_at` per `as_of`) is the consumer's query.** Records
  append in the order knowledge arrived, so **the newest LINE is not the current belief.**
- Records are RECONSTRUCTIONS, not contemporaneous prints (`MANIFEST.csv` carries `provenance` per row), and the
  *specification* is not point-in-time — a 1930 row carries a maturity derived from a 2026 sign-off.
- Live: volatility 1190 records, stock-bond 756. Valuation deliberately absent while R9 is open.

**ARCHIVED 2026-08-06 — `scripts/` now holds ONLY data builders + the signal spine.** The retired jump-model
program (`jumpmodel`, `walkforward`, `backtest`, `run_config`, `synthetic_validation`, `validate_sensor`,
`benchmark_detector` + its tests) moved to **`archive/jumpmodel-v2/`**, and the market-internals gauge
(`internals_*`, `run_internals_prereg`) to **`archive/internals-gauge/`**. Each has a README recording what was
learned and why it is parked — **read those before reviving anything.** Nothing in `scripts/` imports them.
`live_label.py` / `regime_signal.py` were DELETED (not archived — nothing consumed them);
`results/regime_card.json` **stays a deliberate parked blank.** Phase 10 did NOT repopulate it: the assumption
ledger has its own name and path (`results/assumption_ledger.{json,html}`), and
`tests/test_boundary_audit.py::test_regime_card_stays_a_parked_blank` now fails if the card grows a reading.
Never repopulate it with a single-label summary — one word destroys the multi-signal vector.

Tests: `tests/{test_boundary_audit,test_causal,test_reproducibility,test_contract_conformance,test_observation_history,
test_assumption_ledger,test_informativeness_map,test_concentration,test_credit_ebp,test_tail_skew,test_valuation,
test_run_oos}.py` — **215 passing** (2026-08-10), run with bare `pytest` (`pytest.ini` scopes collection to
`tests/`, excluding `archive/`). venv: `.venv`. The boundary audit scans **both** presentation artifacts' prose
and HTML, not only field names, with the vendor-identifier exception stripped first (`_VENDOR_IDENTIFIER_RE`) so
an honest Ken French citation cannot fail the audit — plus three closed key sets per artifact as **literals in
the test**, a **forward-looking-key ban** over both artifacts, and a no-negative-`.shift()` check on both
presentation modules.

## Discipline (signal research — non-negotiable)

- **Find → Validate → Present → STOP.** Each signal declares its 8-attribute spec (research question ·
  mechanism · data · metric · validation · failure modes · historical-context output · maturity) before it runs.
- **Causal only** — trailing/forward filtering, no look-ahead, point-in-time data (macro series get revised).
  **`assert_causal(build, data)` must pass before the one-look** — `tests/test_reproducibility.py` fails on any
  new module defining `build()` that is not registered under the guard, so it cannot be skipped by omission.
- **Validate honestly** — mechanism first; statistical orthogonality is a *diagnostic*, not the gate (keep
  signals that are statistically correlated but mechanistically distinct); confound-check every context stat;
  **out-of-hypothesis-sample confirmation on Japan/Europe** before any SUPPORT.
- **Mechanism gate** — a signal needs a structural reason it survives being known.
- **One look, prereg + overnight cooling-off + explicit dated sign-off** for any positive/SUPPORT claim (never
  inferred from a conversational go-ahead).
- **No single-word regime summary.** Preserve the full vector. Present, never conclude, never allocate.

## Frozen evidence (never overwrite)

`results/{stage1.csv, stage1_run.log, oos_labels.csv, construction_gate.csv, sensor_validation.*,
synthetic_validation.*}` — the chapter-1 one-look artifacts + living gates (`results/README.md` maps them).
`archive/research-v1/` is inert (reproduce v1 at git tag `v1-convergence`).

## Session Close

Update NOTES.md (state + next action) → commit → push.
