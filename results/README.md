# results/

What is in here, what produced it, and what may be overwritten. Last reconciled against the directory listing
2026-08-06.

---

## WHAT HAS ACTUALLY PASSED — read this first

Only **two** signals have spent a one-look. Everything else in this directory is either a construction output
with no claim attached, a living gate, or retired-program evidence. Built ≠ validated.

### Volatility — PASSED, SIGNED OFF 2026-08-06, maturity `production`

Evidence: `vol_validation.txt` · record: `vol_level0.json` · descriptors: `vol_descriptors.csv`

| bar | result |
|---|---|
| V5 international replication | **PASS** — GARCH α≈0.09 / β≈0.89 in US, Japan AND Europe; rolling half-life median 42 / 17 / 40d |
| V2 robustness | **PASS** — corr(λ0.94, λ0.97)=0.975; close-to-close vs Parkinson 0.91–0.95 all regions. Caveat: exact 5-band bucket agrees 78% of days |
| V3 persistence | **PASS** — GARCH identifiable everywhere, IGARCH guard fires correctly |
| V4 rarity | **PASS** — expanding percentile ~uniform (mean 0.48), corr(level, pctile)=0.735 |

Live read: **12.0% annualised vol, 51.9th percentile, 34.8d shock half-life** (as of 2026-05-29).
**Claims a measurement, NOT forecastability.** α+β≈0.99 means volatility forecasts volatility — nothing about
returns or direction.

### Stock-bond correlation — PASSED ITS BARS, RESULTS SIGN-OFF PENDING

Evidence: `stockbond_validation.txt` · descriptors: `stockbond_corr.csv`, `stockbond_context.csv`

V2, the primary on-mechanism metric — share of **equity-down months on which bonds also fell**, by state:

| region | intact | under_test | violated | |
|---|---|---|---|---|
| US | 28% | 44% | 56% | monotone |
| Japan | 25% | 29% | 51% | monotone |
| Europe | 27% | 32% | 48% | monotone |

V4 power pre-check: all three regions POWERED. R1/R2 not tripped. V5 window robustness is the soft spot —
sign agreement 74–85% at 12m, 85–91% at 36m; stable at 24m and above, noisy below.
**Maturity capped at `research`** — the international sample starts 1990 and contains no inflation regime, so
this does not test the sign-flip cycle out-of-sample. Registered before the look, not after.

### Built but NOT validated — no look spent, no claim

`valuation_descriptors.csv` · `concentration_descriptors.csv` · `credit_descriptors.csv` · `tail_skew.csv`

These are construction outputs only. Their charters are unsigned and their one-looks unspent. The numbers in
them are readings, **not evidence of anything**.

---

## Frozen one-look evidence — NEVER overwrite

- `stage1.csv`, `stage1_run.log`, `oos_labels.csv` — the chapter-1 one-look (2026-07-23). Renamed by Adam
  2026-07-23 (were `v2_stage1.csv`, `v2_stage1_run.log`, `v2_oos_labels.csv`); the frozen prereg and
  `RESEARCH-RECORD.md` cite the old `v2_*` names — same files. The runners were removed 2026-07-27; reproducible
  at git commit `51fbeff`.
- `vol_validation.txt` — the volatility signal's one-look (charter V2–V5, `scripts/validate_vol.py`, run
  2026-08-05). GARCH persistence replicates on Japan/Europe (α≈0.09, β≈0.89 in all three), level is robust to the
  EWMA λ and to a range-based estimator, rarity percentile is well-behaved. **Results signed off by Adam, dated
  2026-08-06** (`.planning/phases/01.5-volatility-signal/1.5-VOLATILITY-CHARTER.md` §RESULTS SIGN-OFF): V2–V5 pass,
  no reject condition tripped, maturity derived = `production`, the RF open item closed by a literal Japan/Europe
  run. Do not rerun to "refresh" — a second look is a second look.

## Gates — living checks, rerunning as data updates is expected

| File | Produced by |
|---|---|
| `construction_gate.csv` (was `v2_construction_gate.csv`) | `scripts/build_panel.py` |
| `assets_gate.csv` | `scripts/build_assets.py` |
| `intl_panel_gate.csv` | `scripts/build_intl_panel.py` |
| `ohlc_gate.csv` | `scripts/build_ohlc_panel.py` |
| `trend_proxy_gate.csv` | `scripts/build_trend_proxy.py` |
| `synthetic_validation.csv` + `_run.log` (were `v2_synthetic_validation.*`) | `archive/jumpmodel-v2/scripts/synthetic_validation.py` |
| `sensor_validation.csv` + `_run.log` | `archive/jumpmodel-v2/scripts/validate_sensor.py` |

`sensor_validation.*` scores the jump-model label against ex-post Lunde–Timmermann bear datings using the *frozen*
chapter-1 labels — a fixed fact, not part of any refresh. `CLAUDE.md` lists both `sensor_validation.*` and
`synthetic_validation.*` under "never overwrite": rerun them only to reproduce, and never hand-edit.

## Current signal outputs — regenerable

- `vol_descriptors.csv` + `vol_descriptors.png` — `scripts/vol_descriptors.py`:
  `date,mkt_ret,vol_annual,vol_pctile,half_life,half_life_pctile`. The committed CSV drifted out of sync with its
  own producer once (missing the two `half_life` columns, 2026-08-04 → fixed 2026-08-06);
  `tests/test_reproducibility.py` now fails if that recurs.
- `vol_level0.json` — `scripts/vol_level0.py`: the volatility signal's Level-0 historical-context record
  (reading · rarity · trend · extreme conditions · cross-signal relationships · assessment · maturity), generated
  from the descriptor artifact and passed through `signal_output_schema.validate()`. Regenerable, but it encodes a
  signed-off measurement claim — regenerate it from the committed descriptors, never hand-edit.
- `vol_read.png` — `scripts/vol_read.py`, the human-facing volatility read (level/percentile · drift · rarity ·
  durability).
- `stockbond_corr.csv` — `scripts/stockbond_corr.py`: causal trailing equity/10y-bond correlation at 63/126/252
  days plus the derived assumption state (`intact` / `under_test` / `violated`).
- `stockbond_context.csv` — same script: historical behaviour by state (annualised return, vol, Sharpe for equity /
  bond10 / gold). Descriptive context only.
- `stockbond_validation.txt` — `scripts/validate_stockbond.py`, the Phase-2 one-look (charter V2–V5, run
  2026-08-06). **One look, spent.** Do not rerun to refresh.

## Constructions built 2026-08-06 — NO look spent, NO claim attached

Charters unsigned, one-looks unspent. These are readings, not evidence.

- `valuation_descriptors.csv` — `scripts/valuation.py` (built by `build_valuation.py`). Shiller CAPE 1881-06 →
  2026-08, 1743 rows: `real_price, real_earn_10y, cape, cape_pctile, cape_z`. **Point-in-time**: a 5-month
  earnings publication lag is applied (S&P aggregate quarterlies land ~3mo after quarter end, and Shiller
  interpolates monthly between endpoints). Removes the *publication* look-ahead, **not** the *revision*
  look-ahead — the source is a single current vintage.
- `concentration_descriptors.csv` + `concentration_gate.csv` — `scripts/concentration.py` /
  `build_concentration.py`. Effective-N across the 25 French size/BM buckets, monthly 1926-07 → 2026-06, 1200
  rows: `eff_n, top_share, eff_n_pctile, eff_n_z`. Free firm-count × average-market-cap blocks, so no constituent
  list is needed — but 25 buckets cannot resolve individual names inside the top bucket, which is the registered
  make-or-break limitation.
- `credit_descriptors.csv` + `credit_vintage.json` — `scripts/credit_ebp.py`. Fed EBP 1973 → 2026, 642 rows.
  Indexed by **as-of date** (when a reading was readable), not by what it describes: a 2-month publication lag is
  applied. The vintage JSON stamps the source sha256 because the EBP is a regression residual refit monthly on the
  full sample, so every historical value can move.
- `tail_skew.csv` + `tail_vintage.json` — `scripts/tail_skew.py`. CBOE SKEW as the **price of downside
  protection** (not a crash probability), 2000-01 → 2026-08, 6671 rows. Restricted to 2000+ because the BKM
  strike-grid error is confounded with the index level and would manufacture a trend in the rarity descriptor.
  The vintage JSON exists because **Cboe silently revised this history** — see `--check` below.

## Provenance

`data/processed/MANIFEST.csv` records sha256, shape, index span and **per-column** spans for every panel.
Run `python scripts/data_manifest.py --check` after any data refresh: it diffs current hashes against the
committed manifest. A change is not a failure — it is a prompt to confirm the refresh was yours and not a vendor
restating history underneath a frozen result.

## Retired-program artifacts — regenerable, jump-model era

The volatility signal was reframed off the K=2 state label on 2026-08-04. These files belong to that retired
program and are kept because they are the evidence for the reframe, or because a downstream consumer still reads
them.

- `detector_benchmark.csv` — `archive/jumpmodel-v2/scripts/benchmark_detector.py`. The exposure-matched head-to-head that ended the
  state label: a plain causal vol threshold (with hysteresis) matches or beats the jump model on precision, recall
  and BAC at both the LT15 and LT20 bear datings, and detects with shorter median lag.
- `regime_card.json` — **PARKED PLACEHOLDER, deliberately blank since 2026-08-06.** It has no producer: the
  generator (`live_label.py` → `regime_signal.py`) and its weekly GitHub Action were deleted. Serving a retired
  reading is worse than serving nothing. It stays blank until the multi-signal observatory can fill it (Phase 10),
  and must never be repopulated with a single-label summary — one word destroys the multi-signal vector. Blanking
  it also resolved the last boundary-audit exception (`gauge.position`).

## Removed

- **2026-08-06 cleanup** — `regime_panel.csv`, `regime_read_latest.json` (producers `regime_panel.py` /
  `regime_read.py` deleted with them: retired jump-model read paths, superseded by `vol_descriptors.py` +
  `vol_read.py`), and `explore_dispersion_intl_{japan,europe}.csv` (the orphaned record of the CLOSED
  sector-dispersion lead candidate — the US −40d lead did not generalize: Japan +154d, Europe +94d). All
  recoverable in git history; the closure itself is recorded in `RESEARCH-RECORD.md` and the memory index.
- `report.html` + `scripts/build_report.py` — deleted 2026-08-06. The report rendered the retired chapter-1/2
  framing; the current human-facing read is `vol_read.py` and the Level-0 records.
- `backtest_*.csv` (chapter-1/2 battery output) — no longer regenerable; the runners were removed 2026-07-27
  (one-looks spent, both chapters closed). Reproducible at git commit `51fbeff`.
- v1-era result files (and the HDP pipeline) were removed 2026-07-23; recover at git tag `v1-convergence`.
