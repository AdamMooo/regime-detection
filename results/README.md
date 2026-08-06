# results/

What is in here, what produced it, and what may be overwritten. Last reconciled against the directory listing
2026-08-06.

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
| `synthetic_validation.csv` + `_run.log` (were `v2_synthetic_validation.*`) | `scripts/synthetic_validation.py` |
| `sensor_validation.csv` + `_run.log` | `scripts/validate_sensor.py` |

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

## Retired-program artifacts — regenerable, jump-model era

The volatility signal was reframed off the K=2 state label on 2026-08-04. These files belong to that retired
program and are kept because they are the evidence for the reframe, or because a downstream consumer still reads
them.

- `detector_benchmark.csv` — `scripts/benchmark_detector.py`. The exposure-matched head-to-head that ended the
  state label: a plain causal vol threshold (with hysteresis) matches or beats the jump model on precision, recall
  and BAC at both the LT15 and LT20 bear datings, and detects with shorter median lag.
- `label_live.csv` + `live_label_meta.json` — `scripts/live_label.py` (SPY-splice live tail; the meta file carries
  the splice health: gate pass/fail, correlation, agreement with the frozen chapter-1 labels).
- `regime_card.json` — `scripts/regime_signal.py`, the data contract consumed by a separate downstream repo. It
  contains the one documented deferred boundary exception, `gauge.position` (rename to `dwell_rank` needs
  coordinating with the consumer); see `tests/test_boundary_audit.py`.
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
