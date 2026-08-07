# Claude Context — Regime-Detection

**Read NOTES.md first** — current state and next action.

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

## What This Project Is

A **market-signal research system.** Each signal is an independent research module answering: *what is happening ·
how unusual is it · how has this environment behaved historically · which market assumption does it relate to* —
then STOP. The intelligence is in the quality of each individual signal, not in combining them into one score.
Governing design: **`.planning/REGIME-SENSOR-ARCHITECTURE.md`** (signal set, per-signal spec, validation
standards, maturity model, the assumption-ledger output — organized so the human connects the dots).

**The signal set** (each monitors one abstract market assumption): volatility/risk-off (shipped), stock-bond
correlation (built), valuation, concentration, diversification/correlation (absorption ratio), credit (EBP),
funding stress, crowding, tail. Orthogonality evidence in the `sensor-orthogonality-evidence` memory.

**History note:** the equity-ownership / allocation program (constitution, offense/defense studies, factor,
momentum) was REMOVED from this repo 2026-08-02 — a separate concern; recoverable in git history if needed.

## File Map (scripts/)

**Shared signal infra (built ONCE, D-20 — every signal reuses it):**
- `causal.py` — causal primitives (`ewma_vol`, `realized_vol`, `expanding_percentile`) + **`assert_causal`**, the
  perturb-the-future look-ahead guard every signal's `build()` must pass before its one-look.
- `run_oos.py` — generic Japan/Europe out-of-hypothesis-sample harness over any `build_region(returns)`.
- `signal_output_schema.py` — executable HARD BOUNDARY (closed Level-0 allowlist + denylist + `validate()`).
- `data_manifest.py` → `data/processed/MANIFEST.csv` — sha256/shape/date-span provenance for every panel.

**Volatility signal (Phase 1.5, COMPLETE — signed off 2026-08-06, maturity `production`):**
- `vol_descriptors.py` (measurement spine: level · rarity · drift · GARCH half-life) · `vol_read.py`
  (presentation) · `validate_vol.py` (the frozen one-look → `results/vol_validation.txt`) · `vol_level0.py`
  (emits + schema-validates `results/vol_level0.json`).

**Stock-bond correlation signal (Phase 2, charter frozen 2026-08-06, sign-off pending):**
- `stockbond_corr.py` — `build(panel)` over a region-agnostic `(eq, bond)` schema, on the shared spine.

**Data builders:** `build_panel.py` (US market TR + the construction gate) · `build_assets.py` (multi-asset incl.
bond10/gold) · `build_intl_panel.py` (Japan/Europe equity) · `build_intl_bonds.py` (JGB/Bund monthly) ·
`build_credit.py` · `build_funding.py` · `build_tail.py` · `build_ohlc_panel.py` (Parkinson inputs) ·
`build_trend_proxy.py`.

**ARCHIVED 2026-08-06 — `scripts/` now holds ONLY data builders + the signal spine.** The retired jump-model
program (`jumpmodel`, `walkforward`, `backtest`, `run_config`, `synthetic_validation`, `validate_sensor`,
`benchmark_detector` + its tests) moved to **`archive/jumpmodel-v2/`**, and the market-internals gauge
(`internals_*`, `run_internals_prereg`) to **`archive/internals-gauge/`**. Each has a README recording what was
learned and why it is parked — **read those before reviving anything.** Nothing in `scripts/` imports them.
`live_label.py` / `regime_signal.py` were DELETED (not archived — nothing consumed them);
`results/regime_card.json` is a deliberate parked blank until Phase 10. Never repopulate it with a single-label
summary — one word destroys the multi-signal vector.

Tests: `tests/{test_boundary_audit,test_causal,test_reproducibility}.py` — **26 passing**, run with bare `pytest`
(`pytest.ini` scopes collection to `tests/`, excluding `archive/`). venv: `.venv`.

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
