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
- `label_live.csv` / `regime_card.json` — live instrument tail (`scripts/live_label.py` /
  `scripts/regime_signal.py`)

`backtest_*.csv` (chapter-1/2 battery output) no longer regenerable — the runner scripts were
removed 2026-07-27 (one-looks spent, both chapters closed); reproducible at git commit `51fbeff`.

v1-era result files (and the HDP pipeline) were removed 2026-07-23; recover at git tag
`v1-convergence` or in history.
