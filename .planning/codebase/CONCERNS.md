# Codebase Concerns

**Analysis Date:** 2026-07-21

## Tech Debt

**Two incompatible regime-labeling methodologies coexist for the same HDP-HMM states:**
- Issue: The "merge K raw HDP states into 3 canonical regimes" step is implemented two different ways in two different code paths, and nothing enforces they agree. (1) Rank-based: sort active states by mean VIX, partition into equal thirds by count-position — inlined in `run_paper_experiments.py:110-127` (the paper's Tables 1/2/3/4) and duplicated as `merge_states_to_regimes()` in `src/core/walk_forward.py:26-44` (the walk-forward OOS path, `data/oos_regime_labels.csv`). (2) Absolute-bracket: `label_regimes_hdp()` in `src/core/hdp_hmm.py:479-531`, which maps each state's own realized vol into `config.VOL_BRACKETS` regardless of rank — used only by `stage_train_hmm` (`src/pipeline/stages.py:107`), which is the path `scripts/run.py train` calls and the one that produces `data/regime_results.csv`, the artifact CLAUDE.md identifies as consumed by downstream Algo-Trading-Bot/Portfolio-Manager.
- Files: `run_paper_experiments.py:104-130`, `src/core/walk_forward.py:26-44`, `src/core/hdp_hmm.py:479-531`, `src/pipeline/stages.py:81-134`
- Impact: The same underlying HDP fit can be labeled differently depending on which entry point produced the regime column — the paper's regime story and the "live" pipeline's regime output are not guaranteed to agree, and no test or assertion checks this.
- Fix approach: Pick one merge methodology and route every consumer through the same shared function (delete the other, don't maintain two).

**Duplicated partition logic risks silent divergence:**
- Issue: The rank-based thirds partition (see above) exists as inline code in `run_paper_experiments.py` and again as a full function `merge_states_to_regimes()` in `src/core/walk_forward.py` — not shared, not called from a common module.
- Files: `run_paper_experiments.py:110-127`, `src/core/walk_forward.py:26-44`
- Impact: A future edit to one copy (e.g. changing the `min(int(i*3/K_eff),2)` edge-case handling) will not propagate to the other.
- Fix approach: Extract to one function in `src/core/hdp_hmm.py` or `src/core/evaluation.py`, import it in both call sites.

**Dead code in `src/core/hdp_hmm.py`:**
- Issue: `merge_similar_states()` (lines 435-476) and `HDPModelAdapter` (lines 762-802) are defined but never called anywhere in the repo (confirmed via repo-wide grep). `HDPModelAdapter.score()` is additionally a stub that always returns `0.0`.
- Files: `src/core/hdp_hmm.py:435-476, 762-802`
- Impact: ~110 lines of unused, unmaintained surface area; the `.score()` stub would silently return a meaningless value if the adapter were ever wired up without noticing.
- Fix approach: Delete both unless there's a concrete near-term plan to use them (per project's own "no speculative code" preference).

**Stale comment baked into paper-facing generated LaTeX:**
- Issue: `run_paper_experiments.py:460` writes `% Merged to K=3 for tables using merge_similar_states()` into `results/paper_results.txt` and `results/paper_tables.tex`, but `merge_similar_states()` is never called (see Dead Code above) — the actual method used two lines earlier in the same script is the inline VIX-rank thirds partition.
- Files: `run_paper_experiments.py:460`, `results/paper_tables.tex:88`, `results/paper_results.txt:96`
- Impact: A false methodology description is committed to the repo in paper-facing generated text; if pasted into the appendix as-is it misrepresents the actual regime-merging method used.
- Fix approach: Rewrite the comment to describe the VIX-rank partition actually used, or call `merge_similar_states()` for real.

**Dead dependencies in `requirements.txt`:**
- Issue: `arch`, `plotly`, and `pandas_datareader` are pinned in `requirements.txt` but not imported anywhere in `src/`, `scripts/`, `run_paper_experiments.py`, or `tests/` (confirmed via repo-wide grep for `import arch`, `import plotly`, `pandas_datareader`).
- Files: `requirements.txt:9,15,20`
- Impact: Unnecessary install surface, slightly larger attack surface / longer `pip install`, and confuses anyone auditing what the model actually depends on.
- Fix approach: Remove the three lines; `pip install -r requirements.txt` and existing tests should be unaffected.

**Regenerable/log artifacts committed without `.gitignore` coverage:**
- Issue: `.gitignore` only excludes `figures/dashboard.html` and `figures/feature_analysis.html`. Everything else regenerable is tracked: `data/processed/*.csv` (spx_data, train/test, features*), `data/oos_regime_labels*.csv`, `models/hdp_checkpoint.pkl`, `results/*.csv`/`*.txt`, `paper_overleaf.zip`, and three log files (`logs/cron_run.log`, `logs/pipeline.log`, `logs/pipeline_run.log`).
- Files: `.gitignore`, `data/processed/`, `models/hdp_checkpoint.pkl`, `logs/`, `results/`
- Impact: ~2.1MB currently tracked across these paths (not large yet, but every retrain or pipeline run diffs binary/CSV blobs into git history, and log files in particular grow unbounded with no reason to be version-controlled at all).
- Fix approach: Add `data/processed/`, `data/oos_regime_labels*.csv`, `models/*.pkl`, `logs/`, and `results/*.csv` to `.gitignore`; decide separately whether `results/*.tex` (paper-facing, small, meaningfully diffable) should stay tracked.

**Orphaned artifacts from a deleted pre-refactor architecture:**
- Issue: `reports/fragmentation_report.txt` and `reports/fragmentation_diagnostic.log` reference a "ROLLING_PCA_252d" experiment and OOS regime "fragmentation" investigation — PCA was removed entirely from the current architecture (CLAUDE.md: "Do Not: Add rolling PCA... Change the 4-feature set without re-running the paper's ablation"). No code in the current tree produces these files. `logs/cron_run.log` similarly references a cron job with no corresponding script anywhere in the repo; its last entry (`2026-04-27T01:42:41Z`) shows `exit code: 1` (a failed run), predating the current stripped architecture.
- Files: `reports/fragmentation_report.txt`, `reports/fragmentation_diagnostic.log`, `logs/cron_run.log`
- Impact: Dead artifacts committed to the repo that no longer correspond to any runnable code path; misleading if discovered during an audit (looks like an active experiment or scheduled job when neither exists).
- Fix approach: Delete; nothing in the current pipeline regenerates or reads them.

**CI workflow completely disconnected from the current codebase:**
- Issue: `.github/workflows/tests.yml` runs `pytest tests/test_causality.py`, `tests/test_bot_integration.py`, `tests/test_incremental_collection.py`, `tests/test_pca_caching.py`, `tests/test_dashboard_refactor.py` — none of these files exist (only `tests/test_causality_invariants.py` and `tests/test_cli_runner.py` do). It also validates `analyze_feature_importance.py`, `analyze_regime_characterization.py`, `analyze_signal_quality.py` as importable at repo root — none of these files exist either.
- Files: `.github/workflows/tests.yml`
- Impact: The workflow would fail immediately (`ERROR: file not found`) if triggered. Its `push`/`pull_request` triggers are commented out (`workflow_dispatch` only), which is likely why this has gone unnoticed — it silently never runs automatically.
- Fix approach: Rewrite to `pytest tests/ -v` (matches what actually exists) and delete the `analyze_*.py` validation step, or delete the workflow file entirely until CI is actually wanted.

**`CLAUDE.md` architecture section is stale (confirmed against the actual tree):**
- Issue: The root `CLAUDE.md`'s "Architecture (Stripped — Paper-First)" diagram lists `src/core/evaluation.py` as `"evaluate() + block bootstrap CIs"` and `src/core/orchestrator.py` as `"walk_forward() stub (not yet implemented)"`, and also lists `src/experiments/thesis_experiments.py` and `src/pipeline/runner.py`. None of `orchestrator.py`, `src/experiments/`, or `src/pipeline/runner.py` exist in the current tree (deleted in the May 2026 refactor per `NOTES.md`). `evaluation.py` does exist but has no `evaluate()` function — it has `regime_stats()`, `vol_target_backtest()`, `regime_delta_r2()`, `block_bootstrap_ci()` (a different, newer, differently-scoped file added 2026-07-21, coincidentally reusing the old filename). Walk-forward is no longer a stub — it's fully implemented in `src/core/walk_forward.py` (commit `d4f4872`).
- Files: `CLAUDE.md` (Architecture section)
- Impact: Anyone using CLAUDE.md to navigate the codebase will look for files that don't exist and miss the file that actually has the functionality described.
- Fix approach: Update the Architecture diagram to list `src/core/walk_forward.py` and describe `evaluation.py`'s actual current contents.

**`README.md` "data freshness" note is stale:**
- Issue: README states "The `--validate` flag is accepted for compatibility, but the walk-forward validation stage is still a stub in this checkout." This was true when README was rewritten (commit `70849ae`/merge `8dc349c`), but `stage_walk_forward` was fully implemented afterward (commit `d4f4872`) and README was not updated to match.
- Files: `README.md:70`
- Impact: Understates what `--validate` currently does (a real, ~24-minute walk-forward ensemble across 3 training-window configs, not a no-op).
- Fix approach: Update the line to describe the current ensemble walk-forward behavior; also update README's "Project structure" section, which omits `src/core/walk_forward.py`, `src/core/evaluation.py`, and `src/baselines/`.

**Unimplemented `block_bootstrap_ci()` (uncommitted, in progress):**
- Issue: `src/core/evaluation.py`'s `block_bootstrap_ci()` contains a literal `raise NotImplementedError(...)` inside its resample loop (the block-index-construction step is left as a scaffolded exercise per the inline TODO comment — consistent with intentional "guide me through writing it myself" work-in-progress, not an accidental bug).
- Files: `src/core/evaluation.py:156-168` (uncommitted working-tree change as of 2026-07-21 — `git status` shows this file modified, not yet staged/committed)
- Impact: Calling `block_bootstrap_ci()` in its current state raises immediately. Not currently a live problem since nothing in the committed pipeline calls it yet, but it will block whatever change is planned to wire it in (bootstrap CIs on Sharpe / `regime_delta_r2`, per NOTES.md "Next Session" options).
- Fix approach: Finish the block-resampling loop before any code path calls this function.

**RV30 backtest still bfills its warmup window despite an "avoid lookahead" comment (DEEP-REVIEW WR-01, unresolved):**
- Issue: `rv30 = pd.Series(spy_arr).rolling(30).std().shift(1).bfill().values * ...` appears twice (`run_paper_experiments.py:250, 282`). `.bfill()` backward-fills the ~30 NaN warmup rows using the first *future* valid rolling-std value — directly contradicting the inline comment on the same line.
- Files: `run_paper_experiments.py:250, 282`
- Impact: A small (~30/2000 rows), real lookahead leak in one of the two supplementary backtest baselines (RV30), inconsistent with the project's causal-only hard constraint.
- Fix approach: Leave warmup rows as NaN/excluded from the backtest, or forward-fill with a fixed placeholder (`target_vol_pct`) instead of `.bfill()`.

**Duplicate `bh_cum`/`rv30` computation (DEEP-REVIEW WR-07, unresolved):**
- Issue: `bh_cum`, `rv30`, and the RV30 sizing/backtest are computed once for the printed backtest summary (~`run_paper_experiments.py:240-251`) and recomputed independently for the CSV export block (~`run_paper_experiments.py:280-290`).
- Files: `run_paper_experiments.py:240-251, 280-290`
- Impact: If one copy is edited (e.g. to fix the WR-01 `.bfill()` issue above) without the other, the printed log and the exported CSV/figures will silently diverge.
- Fix approach: Compute once, reuse both places.

**`FIGURE_DIR`/`RESULTS_DIR` config inconsistency (DEEP-REVIEW WR-02, unresolved):**
- Issue: `config.FIGURE_DIR = 'figures'` is used by `scripts/run.py` (dashboard/analyze commands write to `figures/dashboard.html`, `figures/feature_analysis.html`), but `scripts/generate_figures.py` (the script that produces the actual paper PDFs) computes its own independent, hardcoded output path `paper/figures/` — a different directory entirely, not derived from config. `config.RESULTS_DIR = 'results'` is defined but never imported/used anywhere (verified via grep); `run_paper_experiments.py` hardcodes the `'results'` string literal at every call site instead.
- Files: `src/config.py:73-76`, `scripts/generate_figures.py:86`, `scripts/run.py:25,94`, `run_paper_experiments.py:26,28` (and throughout)
- Impact: Two different "figures" output locations exist in the repo (`figures/` vs `paper/figures/`) depending on which script ran; changing `RESULTS_DIR` in config has zero effect anywhere.
- Fix approach: Either import and use `FIGURE_DIR`/`RESULTS_DIR` consistently from `src.config` in both scripts, or delete `RESULTS_DIR` and rename `FIGURE_DIR`'s role to be explicit about which figures directory it controls.

**Paper figure generation has two remaining cosmetic defects (DEEP-REVIEW WR-05/WR-06, unresolved):**
- Issue: `scripts/generate_figures.py`'s regime-shading loop (lines 135-143) can drop the final trading day's shading if the regime changes exactly on the last observation (the trailing segment is never flushed after the loop). Figure 1's title (`line 156`) hardcodes `'HDP-HMM Regime Timeline (January 2016–December 2023)'` as a literal, while `dates[0]`/`dates[-1]` are already computed dynamically elsewhere in the same file.
- Files: `scripts/generate_figures.py:135-144, 156`
- Impact: Cosmetic only (affects at most the last day's shading, and the title would silently mismatch actual data range if `START_DATE`/`TRAIN_END` ever change) — but both are paper-figure correctness/reproducibility risks.
- Fix approach: Add a final `axvspan` call after the loop for any un-flushed trailing segment; derive the title from `dates[0]`/`dates[-1]` (`f'HDP-HMM Regime Timeline ({dates[0].strftime("%B %Y")}–{dates[-1].strftime("%B %Y")})'`).

## Known Bugs

No open bugs beyond the tech-debt items above. The five critical causality/correctness bugs found by the 2026-07-20/21 deep code review (NFCI publication-lag lookahead, dead `HDP_ALPHA`/`HDP_KAPPA` config constants, non-causal parametric-HMM baseline, Table 4 vol-target lookahead, and the `K_eff<3` "High-Vol" silent-drop partition bug) were all fixed and verified in commit `185ae8d` (2026-07-21) — see `.planning/DEEP-REVIEW.md` (untracked) for full original detail and `NOTES.md` for the post-fix Table 4 number changes.

## Security Considerations

**Secrets handling:**
- Risk: `FRED_API_KEY` is required for data collection.
- Files: `src/data/collect_macro.py:28-35` (reads via `os.getenv('FRED_API_KEY')`), `.env` (present, gitignored, not read as part of this audit)
- Current mitigation: `.env` is excluded via `.gitignore`; `_get_fred_api()` raises a clear error rather than silently proceeding if the key is missing or left as the placeholder value.
- Recommendations: None needed — this is already handled correctly for a single-developer research pipeline with no deployed/shared credential surface.

**Private/internal API usage:**
- Risk: `src/baselines/parametric_hmm.py` imports `hmmlearn`'s private `_hmmc` module directly (`from hmmlearn import _hmmc`) to get a true forward-only pass (the public API only exposes forward-backward smoothing).
- Files: `src/baselines/parametric_hmm.py:14, 57`
- Current mitigation: `hmmlearn==0.3.3` is exactly pinned in `requirements.txt`, so this can't silently break via a dependency bump.
- Recommendations: None urgent given the pin, but note in a comment that any future `hmmlearn` version bump must re-verify `_hmmc.forward_log`'s signature hasn't changed.

## Performance Bottlenecks

**Pure-Python forward-backward pass:**
- Problem: `forward_backward_numpy()` (`src/core/hdp_hmm.py:296-349`) runs the forward and backward recursions as nested Python `for` loops over `T` (trading days) × `K` (truncated states), despite the rest of the model (`hdp_hmm_model`, SVI/NUTS fitting) being JAX-jitted and vectorized.
- Files: `src/core/hdp_hmm.py:296-349`
- Cause: Post-processing/decoding step was written in plain numpy for simplicity, not `jax.lax.scan`-based like the training model.
- Improvement path: This function is called once per `get_labels_and_probs()` invocation and once per walk-forward fold (11 folds × 3 window configs = 33 calls in the current OOS run, plus 10 more per `hdp_stability_check()` call) — likely the largest non-SVI CPU cost in the pipeline. Rewriting with `jax.lax.scan` (mirroring the training model's own forward pass) would remove the Python-loop overhead.

**Walk-forward ensemble cost:**
- Problem: `stage_walk_forward` now runs 3 full training-window configs sequentially, each refitting the HDP-HMM via SVI from scratch every 63-day fold — NOTES.md reports ~24 minutes total (up from ~8 minutes for a single window).
- Files: `src/core/walk_forward.py:47-136`, `src/pipeline/stages.py:175-214`
- Cause: No warm-starting — each fold's SVI guide is reinitialized from scratch (`AutoNormal` default init) rather than reusing the previous fold's posterior as an initialization.
- Improvement path: Warm-start each fold's SVI from the prior fold's posterior-mean params if fold-to-fold runtime becomes a bottleneck as the OOS history grows (expanding-window folds get more expensive over time by design).

## Fragile Areas

**Regime labels are sensitive to training-window length — and only the OOS path corrects for it:**
- Files: `src/core/walk_forward.py`, `src/config.py:48-53`, `run_paper_experiments.py`
- Why fragile: A 2026-07-21 investigation (documented in `NOTES.md` "Training-Window Sensitivity") found that expanding-window and 3-year-rolling-window configs disagree on the regime label for the same OOS day 48.8% of the time (51.2% agreement) across 635 days — a smooth gradient with window length, not a COVID-inclusion threshold effect. Critically, **even on days where both configs independently reported >99% posterior confidence, they disagreed 22% of the time** (88/394 such days) — a single model's `filt_prob_max` measures confidence *within* one window choice, not uncertainty *about* the window choice itself.
- Safe modification: The walk-forward/live OOS signal (`data/oos_regime_labels.csv`) now mitigates this via `ensemble_oos()` (majority vote across `[expanding, 5y, 3y]` + `agreement_frac` as the honest confidence measure). The **in-sample paper numbers do not** — `run_paper_experiments.py` (Tables 1, 2, 4) uses only the single full-history "expanding" window with no robustness check. NOTES.md flags this explicitly as not yet done; treat any Table 1/2/4 percentage or Sharpe number as conditional on that one window choice until an ensemble/robustness pass is added to the paper pipeline too.
- Test coverage: None — there is no test asserting cross-window agreement stays above any threshold, nor a regression test that would catch the ensemble silently degrading to near-random agreement.

**Hysteresis is applied in-sample but not in the walk-forward OOS path — a likely uncounted contributor to the OOS dwell-time shrinkage NOTES.md flags as unexplained:**
- Files: `src/core/hdp_hmm.py:390-407, 410-432` (`get_labels_and_probs`/`_apply_hysteresis`), `src/core/walk_forward.py:112-120`
- Why fragile: `get_labels_and_probs()` defaults to `hold_days=3` (a 3-day hysteresis filter that suppresses single-day regime flicker) and is called with this default in both `run_paper_experiments.py:103` and `stage_train_hmm` (`src/pipeline/stages.py:101`) — i.e. every in-sample regime label benefits from hysteresis smoothing. The walk-forward OOS path never calls `get_labels_and_probs()` for its output labels at all: `block_labels_raw = block_filtered.argmax(axis=1)` (`src/core/walk_forward.py:118`) is a raw, un-smoothed argmax — no hysteresis. (It does call `get_labels_and_probs(obs_train, params, hold_days=1)` once per fold, but only to rank training-window states by VIX for the merge step, not to produce the final OOS labels.)
- Impact: NOTES.md observes OOS dwell times (30.5/35.1/8.0 days) are much shorter than in-sample (65.9/61.2/41.4 days) and calls this "not yet root-caused... could be genuine market character or partial refit-boundary instability." The hysteresis asymmetry above is a third, purely mechanical candidate explanation that isn't yet mentioned in that investigation: removing the smoothing filter that in-sample labels get would mechanically shorten measured dwell times regardless of any real change in market behavior.
- Safe modification: If the dwell-time investigation continues, re-run the OOS path with the same `hold_days=3` hysteresis applied to `block_filtered.argmax(axis=1)` before comparing dwell times in-sample vs OOS, to isolate this effect from genuine 2024-2026 market character.
- Test coverage: None directly — the causality-invariant tests confirm `forward_backward_numpy`'s *filtered* output is causal, but nothing tests `_apply_hysteresis()`'s behavior or asserts hysteresis is applied consistently (or intentionally not) across the in-sample vs OOS paths.

**State→regime merge heuristic is index-position-based, not vol-level-based:**
- Files: `run_paper_experiments.py:110-127`, `src/core/walk_forward.py:26-44`
- Why fragile: "Sort `K_eff` active states by mean VIX, partition into equal thirds by count-position" (`min(int(i*3/K_eff), 2)`) assigns regime names by *rank position*, not by actual vol level — a state's "High-Vol" label depends on how many other states exist and where it ranks among them, not on its own realized volatility. Both code paths now guard the degenerate `K_eff < 3` case with an assert/raise (from the CR-05 fix), but the rank-based approach itself is unchanged and still differs conceptually from the absolute-bracket approach (`label_regimes_hdp()`/`VOL_BRACKETS`) used by the production training path.
- Safe modification: Any change to `prune_states()`'s active-state count or threshold (`src/core/hdp_hmm.py:367-387`) can silently shift which states get which regime name in the rank-based paths, with no test to catch a mislabeling.
- Test coverage: None — no test exercises the merge/partition logic itself (only the underlying causal filtering functions are tested).

## Performance Bottlenecks
(see above)

## Scaling Limits

**Walk-forward retrain cost grows with OOS history:**
- Current capacity: 11 quarterly folds × 3 window configs currently run in ~24 minutes total (per NOTES.md), on ~635 OOS days since 2024-01-02.
- Limit: Each new quarter adds another fold; the "expanding" window config's training set (and therefore its SVI fit cost) grows every fold by design, so per-fold cost is not constant — the walk-forward run gets slower over calendar time even with `refit_every` fixed.
- Scaling path: Warm-starting SVI from the prior fold's posterior (see Performance Bottlenecks) would flatten this; alternatively, cap the expanding window's max lookback (turning it into a bounded rolling window) if retrain time becomes prohibitive.

## Dependencies at Risk

**JAX/NumPyro exact pin is a project-wide single point of fragility (intentional, but worth naming):**
- Risk: `jax==0.9.1` / `jaxlib==0.9.1` / `numpyro==0.20.0` are pinned exactly, per the project's own stated reasoning in `requirements.txt`: "Breaking changes in JAX/NumPyro silently corrupt regime assignments." This is a deliberate choice (also stated as a CLAUDE.md hard constraint), not an oversight — flagged here only because it means the entire model is frozen to one JAX/NumPyro pairing with no tested upgrade path.
- Impact: Any future need to upgrade JAX (e.g. for a newer Python version, or a security patch) requires re-verifying the full HDP-HMM output against a reference run before trusting new regime labels.
- Migration plan: None needed proactively; when an upgrade is eventually required, re-run `run_paper_experiments.py` before/after and diff `results/regime_labels_train.csv` to confirm no silent behavior change.

**`hmmlearn._hmmc` private API usage:**
- Risk: `src/baselines/parametric_hmm.py:14` imports `hmmlearn`'s internal `_hmmc` Cython module directly to implement a true causal forward pass, since hmmlearn's public API doesn't expose forward-only decoding.
- Impact: A version bump of `hmmlearn` (currently pinned to `0.3.3`) could change or remove `_hmmc.forward_log`'s signature with no deprecation warning, silently breaking or corrupting the parametric-HMM baseline used in paper Tables 1 and 3.
- Migration plan: Re-verify `_hmmc.forward_log`'s signature against the installed `hmmlearn` source any time the pin is bumped (this is exactly the kind of check the now-fixed CR-03 bug in this same function required originally).

## Missing Critical Features

**No robustness/sensitivity reporting for the in-sample paper's single training-window choice:**
- Problem: The training-window sensitivity finding (see Fragile Areas) applies in principle to every in-sample number in `run_paper_experiments.py`'s Tables 1, 2, and 4 — all computed using only the full-history "expanding" window — but no ensemble, robustness check, or caveat currently exists for the paper path. NOTES.md explicitly flags this as open ("this same sensitivity almost certainly affects the in-sample paper Table 1/2/4 numbers too... still open").
- Blocks: Any claim in the paper about dwell times, Sharpe, or transition-matrix persistence being "the" HDP-HMM's behavior, rather than one training-window choice's behavior.

**No test asserting the two regime-merge code paths produce compatible output:**
- Problem: Given the rank-based vs absolute-bracket labeling inconsistency (see Tech Debt), nothing currently checks whether `run_paper_experiments.py`'s in-sample labels and `stage_train_hmm`'s production labels agree on the same historical data.
- Blocks: Confidence that `data/regime_results.csv` (the artifact meant for downstream Bot/Portfolio-Manager consumption) tells the same story as the paper.

## Test Coverage Gaps

**`src/core/evaluation.py` is entirely untested:**
- What's not tested: `regime_stats()`, `vol_target_backtest()`, `regime_delta_r2()` have no unit tests. `block_bootstrap_ci()` is currently an unfinished stub (see Tech Debt) that would fail any test written against it today.
- Files: `src/core/evaluation.py`
- Risk: These functions feed every number in paper Tables 1-4; a silent regression (e.g. an off-by-one in the dwell-time spell-counting loop, `regime_stats():36-50`) would not be caught by any existing test.
- Priority: Medium — high-value target given these functions directly produce cited paper statistics, but low complexity/risk of subtle bugs relative to the causal-inference code already covered.

**Walk-forward OOS causality is tested only at the component level, not end-to-end:**
- What's not tested: `src/core/walk_forward.py`'s `walk_forward_oos()` and `ensemble_oos()` have no dedicated test. The existing causality-invariant tests (`tests/test_causality_invariants.py`) cover the underlying `forward_backward_numpy` filtered output and `expanding_standardize`/`expanding_regime_vol`, but nothing exercises the fold-loop itself (e.g. that `window_days` slicing, `obs_window` construction, and the per-fold state-to-regime mapping together preserve the "no lookahead across fold boundaries" property the module's own docstring claims).
- Files: `src/core/walk_forward.py:47-136`
- Risk: A bug introduced in the fold-loop plumbing (e.g. an off-by-one in `train_idx`/`block_index` slicing) would not trip any existing causality test, since those only check the primitives the fold loop calls, not the loop's own composition of them.
- Priority: High — this is the code path that produces the "genuinely out-of-sample" claim the project's live signal depends on.

**No test for `_apply_hysteresis()` or the in-sample/OOS hysteresis asymmetry:**
- What's not tested: `src/core/hdp_hmm.py:410-432` has no direct test (correctness of the hold-days streak logic, or that it's a backward-looking/causal transform).
- Files: `src/core/hdp_hmm.py:410-432`
- Risk: Given the hysteresis asymmetry documented above (in-sample smoothed, OOS raw), a test here would also surface that inconsistency mechanically rather than requiring manual code reading to notice.
- Priority: Medium.

**`src/baselines/threshold_rules.py` (the paper's null-hypothesis baseline) is untested:**
- What's not tested: `apply_threshold_rules()`'s `np.select` boundary conditions (e.g. exactly at `THRESH_VOL_LOW=15` or `THRESH_VOL_HIGH=25`) have no unit test.
- Files: `src/baselines/threshold_rules.py`
- Risk: Low complexity, low risk, but this is literally the paper's null hypothesis — worth a trivial boundary-value test given how central it is to the paper's argument.
- Priority: Low.

**No integration test for `run_paper_experiments.py` or the full `scripts/run.py` pipeline:**
- What's not tested: `tests/test_cli_runner.py` only checks `scripts/run.py --help` exits 0 and that `classify_regime_from_vix()`'s VIX-threshold boundaries are correct — it does not exercise `run_collect`/`run_features`/`run_train`/`run_signals` end-to-end, nor `run_paper_experiments.py` at all.
- Files: `run_paper_experiments.py`, `scripts/run.py`
- Risk: A break in the collect → features → train_hmm → signals → walk_forward stage chain (e.g. a column-name mismatch after a refactor) would only be caught by manually running the pipeline, not by CI or `pytest tests/`.
- Priority: Medium — full end-to-end runs are slow (minutes, due to SVI), so a full integration test is a real tradeoff, but even a smoke test on a tiny synthetic dataset would catch plumbing breaks cheaply.

---

*Concerns audit: 2026-07-21*

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
