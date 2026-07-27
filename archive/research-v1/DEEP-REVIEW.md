---
phase: deep-review
reviewed: 2026-07-20T00:00:00Z
depth: deep
files_reviewed: 9
files_reviewed_list:
  - src/config.py
  - src/core/hdp_hmm.py
  - src/core/inference.py
  - src/data/collect_macro.py
  - src/pipeline/stages.py
  - src/baselines/threshold_rules.py
  - src/baselines/parametric_hmm.py
  - run_paper_experiments.py
  - scripts/generate_figures.py
findings:
  critical: 5
  warning: 7
  info: 3
  total: 15
status: issues_found
---

# Phase: Deep Code Review — regime-detection

**Reviewed:** 2026-07-20
**Depth:** deep
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Cross-file trace of the causal-inference claim, the sticky HDP-HMM math, config consumption, and the paper-generation pipeline. The core `expanding_standardize()` (inference.py) and the model's own forward algorithm (`hdp_hmm_model` + `forward_backward_numpy`, both in hdp_hmm.py) are mathematically sound and genuinely causal — no lookahead was found in the standardization or in the state-filtering math itself. However, five issues were found that either (a) reintroduce lookahead outside the core model, or (b) silently produce mathematically/scientifically wrong output that could corrupt the paper's tables without raising any error. Two of these five directly touch the project's "causal inference only" hard constraint (NFCI merge, parametric-HMM baseline), one is a config-consumption defect requested for review (HDP_ALPHA/HDP_KAPPA silently ignored), one is a lookahead bug in the Table 4 backtest, and one is a partition-math bug that can silently erase the "High-Vol" regime from the paper's tables. Several further maintainability/documentation issues are listed as Warnings and Info.

## Critical Issues

### CR-01: NFCI weekly series reindexed onto daily index with no publication-lag adjustment (lookahead into causal features)

**File:** `src/data/collect_macro.py:64-78`
**Issue:** NFCI is published weekly by the Chicago Fed with a multi-day lag between the reference (observation) date and the actual release date. The code does:
```python
raw_nfci = fred.get_series(FRED_NFCI_SERIES, observation_start=START_DATE, observation_end=END_DATE)
...
nfci_daily = raw_nfci.reindex(idx, method='ffill')
```
`fred.get_series()` returns values indexed by the *reference* date (e.g. the Friday the observation describes), not the date it was actually released. `reindex(..., method='ffill')` immediately forward-fills that value onto the following Monday/Tuesday/etc., meaning the daily feature matrix "knows" the week's NFCI value several days before it was actually published. This directly contradicts the project's hard constraint of "Causal inference only... essential for live trading" (CLAUDE.md) and the explicit "no lookahead" claim repeated throughout the codebase (`expanding_standardize` docstring, `get_filtered_states` docstring, etc.) — the leak happens one step upstream of those causal transformations, in the raw feature construction itself, so no downstream causal-only code can undo it.
**Fix:** Shift the FRED series forward by its actual publication lag before reindexing, e.g.:
```python
raw_nfci = fred.get_series(FRED_NFCI_SERIES, observation_start=START_DATE, observation_end=END_DATE)
raw_nfci.index = raw_nfci.index + pd.Timedelta(days=7)  # or query FRED's realtime_start/vintage date via fred.get_series_all_releases()
nfci_daily = raw_nfci.reindex(idx, method='ffill')
```
Better: use `fredapi`'s realtime/vintage endpoints (`Fred.get_series_all_releases`) to align on actual release date rather than reference date.

### CR-02: `HDP_ALPHA` and `HDP_KAPPA` config values are imported but never used — the "sticky" hyperparameters documented in config.py do not control the model

**File:** `src/core/hdp_hmm.py:37, 76-91`; `src/config.py:38-39`
**Issue:** `config.py` defines and documents:
```python
HDP_ALPHA  = 1.0
HDP_KAPPA  = 10.0   # stickiness — markets are persistent
```
`hdp_hmm.py` imports both names (`from src.config import (..., HDP_ALPHA, HDP_KAPPA, ...)`) but never references either symbol anywhere else in the 802-line file (verified by grep — the import line is the only occurrence). Instead, the model treats `kappa` and `alpha_trans` as **fully learned latent variables** with hardcoded hyperpriors:
```python
kappa = numpyro.sample('kappa', dist.Gamma(2.0, 0.2))       # prior mean = 10, but freely inferred
alpha_trans = numpyro.sample('alpha_trans', dist.Gamma(1.0, 1.0))
```
`Gamma(2.0, 0.2)` happens to have prior mean 10 (coincidentally matching `HDP_KAPPA`), but this is a prior, not a fixed value — the posterior kappa is free to move substantially (prior std ≈ 7). Anyone editing `HDP_KAPPA`/`HDP_ALPHA` in config.py expecting to change model stickiness gets a silent no-op, and any paper text that cites "we fix kappa=10 for sticky transitions" (as the config comment implies) would be describing the model incorrectly.
**Fix:** Either use the config constants as fixed hyperparameters (e.g. `numpyro.deterministic('kappa', HDP_KAPPA)` or use them as the Gamma hyperprior params instead of the hardcoded `2.0, 0.2`/`1.0, 1.0`), or remove the unused imports from `hdp_hmm.py` and update the config.py comment to clarify these describe prior means only, not fixed values.

### CR-03: Parametric HMM baseline's `get_filtered_states()` returns smoothed (forward-backward) posteriors, not causal filtered posteriors — contradicts its own docstring and the "causal only" hard constraint

**File:** `src/baselines/parametric_hmm.py:45-51`
**Issue:**
```python
def get_filtered_states(model: GaussianHMM, X: np.ndarray) -> tuple:
    """Forward-pass filtered states only (causal, no lookahead)."""
    _, posteriors = model.score_samples(X)
    ...
```
`hmmlearn.GaussianHMM.score_samples()` (verified against the installed hmmlearn 0.3.3 source, `BaseHMM._score_log`) runs **both** a forward pass (`_hmmc.forward_log`) and a backward pass (`_hmmc.backward_log`), then returns `_compute_posteriors_log(fwdlattice, bwdlattice)` — the standard forward-backward **smoothed** posterior P(s_t | x_1..T), which uses future observations. This is the opposite of what the docstring claims. Because these labels feed directly into Table 1 (regime characteristics) and Table 3 (information-content regression) for the "Param HMM" column via `run_paper_experiments.py`, those two tables' "Param HMM" comparison numbers are computed on a baseline that has silently seen the future, undermining the fairness of the causal-vs-baseline comparison the paper is built around.
**Fix:** Implement true forward-only filtering manually (hmmlearn does not expose this directly):
```python
def get_filtered_states(model, X):
    framelogprob = model._compute_log_likelihood(X)
    logprob, fwdlattice = model._do_forward_pass(framelogprob)  # hmmlearn internal, forward only
    posteriors = np.exp(fwdlattice - logsumexp(fwdlattice, axis=1, keepdims=True))
    return np.argmax(posteriors, axis=1), posteriors
```
or clearly relabel the function/docstring as "smoothed, non-causal — baseline reference only" if the intent is genuinely to give the parametric baseline the (unfair) benefit of hindsight.

### CR-04: Table 4 volatility-targeting backtest sizes positions using full-sample per-regime realized vol — lookahead bias inflates HDP-HMM backtest results

**File:** `run_paper_experiments.py:128-129, 325-336`
**Issue:**
```python
hdp_vols = {k: float(np.std(spy_train[hdp_labels == k]) * np.sqrt(252) * 100)
            for k in range(3) if (hdp_labels == k).sum() > 0}
...
regime_vol_map = {k: hdp_vols.get(k, 15.0) for k in range(3)}
hdp_vol_series = np.array([regime_vol_map[l] for l in hdp_labels])
```
`hdp_vols` is computed once from the **entire** training sample's realized volatility per regime, then broadcast back onto every day assigned to that regime — including days at the very start of the sample. When `vol_target_backtest()` sizes a position on day 1 of a "High-Vol" regime, it is using volatility information realized on the last day of that regime's occurrences, months or years later. This is a textbook lookahead bug and directly inflates (or at minimum mischaracterizes) the Sharpe/MaxDD numbers reported for "Vol-Target (HDP)" in Table 4 — the one table most likely to be cited as evidence of "practical value" of the regime signal. The identical bug pattern also affects `thresh_vol_map` (lines 331-336), used for `cum_vix_thr` (exported to CSV, currently unused in Table 4 itself but silently available for future figures/analysis with the same defect baked in).
**Fix:** Use a strictly point-in-time vol estimate — e.g. an expanding or rolling realized-vol estimate computed only from data up to (and lagged one day before) the current row, the same discipline already correctly applied to the `RV30` strategy:
```python
# expanding per-regime vol using only data seen so far
hdp_vol_series = np.zeros(T)
running_sq = {k: [] for k in range(3)}
for t in range(T):
    k = hdp_labels[t]
    hdp_vol_series[t] = (np.std(running_sq[k]) * np.sqrt(252) * 100) if len(running_sq[k]) > 20 else 15.0
    running_sq[k].append(spy_arr[t])
```

### CR-05: Regime-count partition math silently drops the "High-Vol" label whenever the HDP model prunes to fewer than 3 effective states

**File:** `run_paper_experiments.py:104-119`
**Issue:** The comment claims:
```python
# Sort all discovered states ascending by mean VIX, partition into thirds.
# This always produces exactly 3 non-empty groups regardless of K.
...
state_to_regime = {s: min(int(i * 3 / K_eff), 2) for i, s in enumerate(sorted_by_vix)}
```
This claim is false for `K_eff` (the number of active/pruned HDP states, from `hdp_hmm.py:prune_states`) less than 3. Trace: for `K_eff=2`, `i=0 → min(0,2)=0`, `i=1 → min(int(1*3/2),2)=min(1,2)=1` — group index 2 ("High-Vol") is *never* assigned, regardless of how volatile that state's mean VIX actually is. For `K_eff=1`, only group 0 ("Low-Vol") is ever populated, even if the single discovered state has extremely high realized vol. This is not a rare corner case: `prune_states()` in `hdp_hmm.py` (lines 367-387) explicitly allows exactly 2 active states to pass through without triggering its own `len(active) < 2` fallback (`if len(active) < 2: ...`), so `K_eff == 2` is a directly reachable path with default config (`kappa=10` sticky prior tends to collapse states). When this happens, Tables 1-4 of the paper will silently mislabel a genuinely high-volatility state as "Moderate-Vol" (assigned by count-position, not by its actual realized vol), with no error or warning surfaced anywhere in the pipeline.
**Fix:** Partition by actual vol level (reuse `VOL_BRACKETS` / the same absolute-vol-bracket logic already implemented correctly in `hdp_hmm.py:label_regimes_hdp()`) instead of by sorted index position, or explicitly assert/warn when `K_eff < 3`:
```python
assert K_eff >= 3, f"HDP pruned to only {K_eff} active states — cannot map to 3 canonical regimes; rerun or lower prune_states threshold"
```

## Warnings

### WR-01: `.bfill()` on the RV30 vol estimate reintroduces the lookahead the `.shift(1)` was meant to prevent

**File:** `run_paper_experiments.py:322, 357`
**Issue:**
```python
# Strategy 2: Vol-target using 30-day realized vol (lagged 1 day to avoid lookahead)
rv30 = pd.Series(spy_arr).rolling(30).std().shift(1).bfill().values * np.sqrt(252) * 100
```
The `.bfill()` call backward-fills the first ~30 NaN rows using the first *future* valid rolling-std value, directly contradicting the inline comment on the same line ("to avoid lookahead"). Small in magnitude (≈30 rows out of ~2000), but it is a real, easily-avoided leak in one of the two supplementary backtest baselines.
**Fix:** Leave the warmup rows as NaN/excluded from the backtest, or forward-fill with a fixed placeholder (e.g. `target_vol_pct`) instead of `.bfill()`.

### WR-02: `FIGURE_DIR` / `RESULTS_DIR` config values are defined but never consumed

**File:** `src/config.py:65-66`; `scripts/generate_figures.py:86`; `run_paper_experiments.py:21` (and throughout, e.g. hardcoded `'results/...'` paths)
**Issue:** `config.py` defines `FIGURE_DIR = 'figures'` and `RESULTS_DIR = 'results'`, but neither is imported anywhere. `run_paper_experiments.py` hardcodes `'results'` as a literal string at every call site (`os.makedirs('results', ...)`, `open('results/run_log.txt', 'w')`, etc.), and `scripts/generate_figures.py` computes its own independent output path (`os.path.join(os.path.dirname(__file__), '..', 'paper', 'figures')`) that doesn't even match the string `'figures'` in config.py (writes to `paper/figures/`, not `figures/`). Changing either config constant has zero effect anywhere.
**Fix:** Import and use `RESULTS_DIR`/`FIGURE_DIR` from `src.config` in both files, or delete the unused constants from config.py if the paths are intentionally meant to stay independent.

### WR-03: Auto-generated LaTeX appendix falsely claims `merge_similar_states()` was used for regime merging

**File:** `run_paper_experiments.py:535`; `src/core/hdp_hmm.py:435-476`
**Issue:** The generated appendix text writes:
```python
tex(f"% Merged to K=3 for tables using merge_similar_states()")
```
but the actual merging logic used earlier in the same script (lines 104-119) is the ad-hoc "sort states by mean VIX, partition into thirds" scheme (see CR-05) — `merge_similar_states()` (defined in `hdp_hmm.py`) is never called anywhere in the codebase (confirmed via grep — dead function). This bakes a false methodology description directly into paper-facing generated text.
**Fix:** Either call `merge_similar_states()` for real, or correct the appendix comment to describe the VIX-rank partition actually used.

### WR-04: `label_regimes_hdp()` docstring example vol bracket doesn't match the actual `VOL_BRACKETS` config

**File:** `src/core/hdp_hmm.py:484-488`; `src/config.py:51-55`
**Issue:** Docstring says: `"A state with 13% realized vol is named 'Moderate-Vol' (if 10-18% is that bracket)..."` but the actual configured brackets are `(0,14,'Low-Vol'), (14,22,'Moderate-Vol'), (22,200,'High-Vol')` — the "10-18%" example bracket doesn't exist in the config. Minor but confusing when cross-referencing docs against behavior.
**Fix:** Update the docstring example to match `config.VOL_BRACKETS` (e.g. "a state with 15% realized vol is named 'Moderate-Vol' since 14 ≤ 15 < 22").

### WR-05: Figure 1 regime-shading loop can drop the shading for the final trading day if the regime changes on the last observation

**File:** `scripts/generate_figures.py:133-144`
**Issue:**
```python
for i in range(1, len(dates)):
    if hdp_regime[i] != prev_regime or i == len(dates) - 1:
        end_idx = i if hdp_regime[i] != prev_regime else i + 1
        ax_top.axvspan(dates[start_idx], dates[min(end_idx, len(dates) - 1)], ...)
        start_idx   = i
        prev_regime = hdp_regime[i]
```
If the regime changes exactly on the final iteration (`i == len(dates)-1` and `hdp_regime[i] != prev_regime`), the span for the *previous* segment is drawn correctly, `start_idx` is advanced to the last index, but the loop then terminates — so the single-day final segment (`start_idx=i` to `i`) is never drawn. Cosmetic only, affects at most the last day's shading in the paper figure.
**Fix:** After the loop, add a final `axvspan` call for any un-flushed trailing segment.

### WR-06: Hardcoded figure title date range will silently go stale if config dates change

**File:** `scripts/generate_figures.py:156`
**Issue:** `ax_top.set_title('HDP-HMM Regime Timeline (January 2016–December 2023)', ...)` is a hardcoded literal, while the same file already derives `dates[0]`/`dates[-1]` dynamically elsewhere (e.g. `ax_top.set_xlim(dates[0], dates[-1])`). If `START_DATE`, `TRAIN_END`, or the warmup period change, this title becomes silently incorrect — a reproducibility risk for a paper figure caption.
**Fix:** `f'HDP-HMM Regime Timeline ({dates[0].strftime("%B %Y")}–{dates[-1].strftime("%B %Y")})'`

### WR-07: Duplicate computation of `bh_cum` and `rv30`/`rv_sizes` in `run_paper_experiments.py`

**File:** `run_paper_experiments.py:315-323, 355-365`
**Issue:** `bh_cum`, `rv30`, and the RV30 sizing/backtest are computed once for the printed backtest summary (~line 315-323) and recomputed independently for the CSV export block (~line 355-365). If one copy is edited (e.g. to fix WR-01) without the other, the printed log and the exported CSV/figures will silently diverge.
**Fix:** Compute once, reuse both places.

## Info

### IN-01: `expanding_standardize()` silently overrides near-zero std with 1.0, masking degenerate features

**File:** `src/core/inference.py:42`
**Issue:** `cum_std[cum_std < 1e-8] = 1.0` silently replaces a near-zero cumulative std with 1.0 (to avoid division by zero) with no warning/log — if a feature is genuinely constant during warmup, this is invisible to the user.
**Fix:** Log a warning (e.g. via `warnings.warn`) when this clamp triggers, noting which column/row.

### IN-02: Dead code — `merge_similar_states()` and `HDPModelAdapter` are defined but never used anywhere in the reviewed files or the rest of the repo

**File:** `src/core/hdp_hmm.py:435-476, 762-802`
**Issue:** Neither `merge_similar_states()` nor `HDPModelAdapter` is referenced by any of the 9 reviewed files (or found elsewhere via repo-wide grep). `HDPModelAdapter.score()` is additionally a stub that always returns `0.0`.
**Fix:** Either wire these into the pipeline (per CLAUDE.md preference for small diffs / no speculative code, deleting is likely the right call) or remove them if truly unused.

### IN-03: Redundant `.dropna()` defensive calls create silent length-alignment risk between `param_states` and other label arrays

**File:** `run_paper_experiments.py:158, 55`
**Issue:** `X_raw_train = df_raw[[...]].reindex(feat_train.index).dropna().values` applies a defensive `.dropna()` after reindexing onto an index that should already be NaN-free (it's derived from the same upstream `spx_data.csv`). If this ever silently drops rows (e.g. due to upstream data staleness), `param_states` would end up a different length than `hdp_labels`/`thresh_labels`, and `pd.DataFrame({...})` construction in `labels_df` (line 367) would raise a length-mismatch error rather than fail silently — so the failure mode is a crash, not corruption, but it's worth confirming this dropna is actually a no-op in the current pipeline rather than relying on it implicitly.
**Fix:** Assert `len(X_raw_train) == len(feat_train)` right after the reindex/dropna to make the invariant explicit and fail fast with a clear message.

---

_Reviewed: 2026-07-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
