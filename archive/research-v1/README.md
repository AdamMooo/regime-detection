# Archive — v1 Research Program (converged)

One-shot research code from the converged v1 program (five null results), sealed at git tag
`v1-convergence`. The narrative lives in `RESEARCH-RECORD.md` at the repo root; the numeric
outputs live in `results/` at the repo root.

Import paths (e.g. `from src.config import ...`, `sys.path` tricks relative to `scripts/`)
are intentionally left as-is, so these files will NOT run from this location. To reproduce
any result, check out the tag:

    git checkout v1-convergence

Contents:
- `scripts/` — standalone experiment scripts (histext, tailhazard, corrfactor, stock-bond,
  covariance conditioning, feature search/ablation, stability/significance diagnostics,
  paper figure generation)
- `tests/` — tests that exclusively covered archived code
- `run_paper_experiments.py` — paper table/label generator (in-sample)
- `paper/`, `paper_overleaf.zip` — the paper draft and its figures

The live regime-label tool chain (`scripts/run.py`, `src/pipeline/`, `src/core/`,
`src/baselines/`, `src/data/`) was not moved and keeps running from the repo root.
