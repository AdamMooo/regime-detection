# results/

**Frozen one-look evidence (chapter 1, 2026-07-23 — never overwrite):**
- `stage1.csv`, `stage1_run.log`, `oos_labels.csv`

Renamed by Adam 2026-07-23 (were `v2_stage1.csv`, `v2_stage1_run.log`, `v2_oos_labels.csv`);
the frozen prereg and RESEARCH-RECORD cite the old `v2_*` names — same files.

**Gates (living checks — rerunning as data updates is expected):**
- `construction_gate.csv` (was `v2_construction_gate.csv`) — `scripts/build_panel.py`
- `synthetic_validation.csv` + `_run.log` (were `v2_synthetic_validation.*`) —
  `scripts/synthetic_validation.py`

**Regenerable:**
- `report.html` — visual dashboard (`scripts/build_report.py`)
- `label_live.csv` / `live_label_meta.json` / `regime_card.json` — live instrument tail
  (`scripts/live_label.py` writes the first two; `scripts/regime_signal.py` reads all three and
  writes the card). `live_label_meta.json` carries the live SPY-splice health (gate
  pass/fail, correlation, agreement with the frozen chapter-1 labels) for the card's
  "is today's reading trustworthy" section.
- `sensor_validation.csv` — the instrument's historical track record vs ex-post bear dating
  (`scripts/validate_sensor.py`, scored against the *frozen* chapter-1 labels — a fixed fact,
  not part of the weekly refresh). Feeds the card's "skill" block: catches 15/18 bears at the
  15% dating (20d median lag), 9/11 at the 20% dating (56d lag) — a vol-state sensor, not a
  bear detector.

`backtest_*.csv` (chapter-1/2 battery output) no longer regenerable — the runner scripts were
removed 2026-07-27 (one-looks spent, both chapters closed); reproducible at git commit `51fbeff`.

v1-era result files (and the HDP pipeline) were removed 2026-07-23; recover at git tag
`v1-convergence` or in history.
