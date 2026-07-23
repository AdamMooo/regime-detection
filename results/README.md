# results/

**Frozen evidence (never overwrite/rename — cited by RESEARCH-RECORD.md and the frozen prereg):**
- `v2_stage1.csv`, `v2_stage1_run.log`, `v2_oos_labels.csv` — chapter-1 one-look run (2026-07-23)
- `v2_construction_gate.csv`, `v2_synthetic_validation.csv`, `v2_synthetic_validation_run.log` —
  Phase 0/1 gates (pre-freeze)

**Regenerable:**
- `report.html` — visual dashboard (`scripts/build_report.py`)
- `construction_gate.csv`, `backtest_*.csv`, `synthetic_validation.csv` — written by future runs
  of the renamed pipeline (no collision with frozen names)

**Live-tool artifact (do not delete):** `regime_labels_train.csv` — read by `scripts/run.py`.

v1-era result files were removed 2026-07-23; recover them at git tag `v1-convergence`.
