---
type: hub
project: regime-detection
---
# Regime Detection

Bayesian HDP-HMM market regime detection. Two goals: (1) an academic paper proving markets have latent states not recoverable from VIX alone, (2) regime labels consumed downstream by Portfolio-Manager. See [[regime-detection/CLAUDE|CLAUDE.md]] for architecture, hard constraints, and downstream label mapping.

## Status

**2026-07-22 (latest) — three-chapter negative arc concluded; DIRECTION CHANGE.** After the Continuum
Turn, the project ran three increasingly-well-designed, pre-registered tests of "is there useful observable
structure beyond volatility/stress?" — all null (see `RESEARCH-RECORD.md` newest-first, `NOTES.md`):
(1) **HMM/latent state** — belief-revised to a moderately-stable *compression* of observables, no
incremental OOS info; (2) **macro/rates → stock-bond correlation** (frozen prereg
`.planning/STOCKBOND-MACRO-PREREG.md`, ~50y data) — **Case C**, non-stationary co-trend; (3) **covariance
conditioning** (frozen prereg `.planning/COVARIANCE-CONDITIONING-PREREG.md`, matched vol-only baseline) —
**null/negative** (GMV variance 2.24× worse, dependence-structure estimate flat). Cumulative read:
volatility/stress absorbs whatever the candidate dimensions were meant to add. The documented fallback
deliverable is a **methods/negative paper** covering the arc. **New direction (Adam, 2026-07-22): pivot to
a Continuous-Time Latent Market State with Jumps** (jump-diffusion / continuous-time latent state) — targets
the jump/tail object left untested by the audit. Next session begins that experiment.

---

**2026-07-22 (The Continuum Turn):** Major reframe + 6 reproducible experiments — see `RESEARCH-RECORD.md`
→ "2026-07-22 — The Continuum Turn", `NOTES.md`, and `.planning/ROADMAP.md`. Key results: the raw states
are **~2-D** (stress + an independent yield-curve axis), not a 1-D vol ladder — and every prior "no
beyond-VIX" negative was measured on the VIX-projected label that deletes the 2nd axis; the latent
structure is a **weakly-structured continuum** (explains K-saturation); the continuous coordinate Z_t is
stable across windows (so E2's instability was largely the VIX-merge artifact) but ~2/3 just smoothed
features; and **the current HMM-based environment estimator is rejected on OOS predictive grounds vs
simpler continuous filters** (EWMA/VAR carry ~2× its forward predictive correlation). Stage-2 first cut:
the continuous coordinate shows no clear incremental conditioning value over the raw features yet.

Post-audit (2026-07-21). A read-only research audit reassessed the thesis against the evidence — see
**`RESEARCH-RECORD.md`** (root, durable narrative) and `.planning/RESEARCH-AUDIT.md` (full technical
evidence). The paper (`paper.tex`) is **not** upload-ready as a final claim: it is a snapshot from before
the OOS + significance work and overstates persistence and backtest edge. It is deliberately left
unchanged until three experiments land (see Next).

### Thesis status (evidence-based)

- **Validated:** causal integrity (mechanically tested no-lookahead); training-window sensitivity is
  real (51–69% cross-window agreement, disagreement even at >99% individual confidence).
- **Partially validated:** regime → *future-volatility* information beyond VIX (real but not yet
  reproducible from a committed script); regime persistence (model κ is real, but reported Table 2
  persistence is inflated by hysteresis + the VIX-merge).
- **Not yet established (not refuted):** the headline thesis that latent states are "not recoverable
  from VIX alone" — the published regimes are *defined by* a VIX-rank partition; VIX-independent
  structure has never been isolated. Requires a VIX-ablation + raw-state analysis.
- **Open research question:** is the HDP's nonparametric complexity justified? K saturates the
  truncation (effective_K = 8 every run), so data-driven K is currently inert, and the one fixed-K
  baseline is degenerate.
- **Negative result:** no meaningful *return*-direction prediction.

A deep causality review (2026-07-20/21) previously found and fixed 5 lookahead/correctness bugs
(185ae8d); post-fix in-sample numbers were HDP dwell ~66/61/41 days, backtest Sharpe 0.624 vs 0.606
(B&H) vs 0.766 (RV30) — but these are in-sample and the backtest edge does **not** replicate OOS
(HDP 1.062 vs B&H 1.098). Treat them as illustrative, not as established claims.

Not GSD-managed in the usual sense — `.planning/` holds a codebase snapshot and a planning doc, not `STATE.md`/`ROADMAP.md`.

Walk-forward OOS validation shipped 2026-07-21 (`scripts/run.py walk_forward`) — the model now produces a genuine live regime signal instead of falling back to a VIX-threshold guess. Same-day follow-up found regime assignment is meaningfully sensitive to training-window length (down to 51% agreement between configs on the same days), so the signal is now a 3-window ensemble reporting cross-window agreement (e.g. "Low-Vol, 2/3 windows agree") rather than one model's overstated posterior confidence. See NOTES.md "Training-Window Sensitivity."

A same-day follow-up pivoted the evaluation framework: instead of asking "does vol-targeting beat buy-and-hold" (never actually established), a block-bootstrap significance test now asks "does the regime label carry real information, honestly tested" on the genuinely-OOS ensemble labels. Answer: forward-return information content is statistically significant but tiny (ΔR²=0.00077); forward-*volatility* information content is significant and ~16x larger (ΔR²=0.0124). The defensible claim is that regimes predict future volatility, not direction. Also found and fixed a real bug: in-sample dwell times were smoothed with 3-day hysteresis while OOS labels used raw argmax — part of the earlier "OOS dwell times are half in-sample" finding was just this mismatch. Corrected re-run (commit `8e2d637`): High-Vol dwell nearly doubled (8.0→15.0 days), still below the in-sample claim (41.4 days) but fairer. Today unchanged: Low-Vol, 2/3 windows agree.

## Next

**Direction change (2026-07-22): experiment with a Continuous-Time Latent Market State with Jumps.** The
discrete-HMM / predictive-regime / covariance-conditioning arc is concluded (three nulls; see Status).
The new line is a continuous-time latent-state model with a jump component (jump-diffusion), which also
addresses the strongest untested object from the reframe audit (tail/jump behavior). Not yet designed;
apply the same discipline used throughout — pre-register object, baseline, metric, and falsification
before running. The **methods/negative paper** documenting the three-chapter arc remains the standing
fallback deliverable if the new line does not land.

(Superseded: the earlier three deferred experiments — significance-test wiring was since shipped
`scripts/significance_test.py`; the raw-state/VIX-ablation and persistence questions were overtaken by the
belief revision and the reframe. See `RESEARCH-RECORD.md` for the full chronology.)

## Memory

- **Operations:** [[regime-detection/CLAUDE|CLAUDE.md]] (architecture, hard constraints, downstream label mapping)
- **Notes:** [[regime-detection/NOTES|NOTES.md]] (session-to-session state, read first)
- **Public docs:** [[regime-detection/README|README]]

## Known Issues

Four methodological findings from the 2026-07-21 audit (detail + implications in `RESEARCH-RECORD.md`;
**none fixed yet, by decision**):

- **[HIGH] Transition-matrix mislabeling** — paper's Table 2 is an empirical count on hysteresis-smoothed,
  VIX-merged labels, not the model's posterior matrix (`get_transition_matrix()` exists but is unused).
  Reported persistence is partly a post-processing artifact.
- **[HIGH] Confounded dwell comparison** — HDP labels are hysteresis-smoothed; the VIX-threshold and
  parametric baselines are not. The 66/61/41-vs-8–17 advantage is real in part but its magnitude is
  inflated by asymmetric smoothing.
- **[HIGH] HDP data-driven K is inert** — effective_K = mean 8.0 / std 0.0 / mode 8 every run (saturates
  truncation); the 3 regimes are imposed by a VIX-rank cut, not learned. The nonparametric complexity is
  not yet shown to beat a fixed-K HMM (and the one parametric baseline is degenerate: N=367, dwell=367).
- **[HIGH] Best result not reproducible** — `block_bootstrap_ci`/`regime_delta_r2` are called by no
  committed script; the ΔR² numbers (vol 0.0124, return 0.00077) live only in prose. Preserved but marked
  not-reproducible until `scripts/significance_test.py` exists.
- Documentation: `paper.tex:153` "features lagged one day" is inaccurate (causality is from
  expanding-standardize + forward filtering); paper prose transition diagonals are stale vs the table.

- **Regime assignment is sensitive to training-window length** (2026-07-21) — expanding vs. rolling-5y vs. rolling-3y windows agree on the label only 51-69% of the time, even when each individually reports >99% confidence. `data/oos_regime_labels.csv` is now a 3-window ensemble (majority vote + agreement_frac) rather than one overconfident number, but the in-sample paper Table 1/2/4 numbers still use only the original single (full-history) window — this sensitivity almost certainly applies there too, not yet addressed.
- **Two regime-labeling schemes coexist with no test enforcing agreement**: `label_regimes_hdp()` (absolute VOL_BRACKETS, used by `stage_train_hmm`) vs. `merge_states_to_regimes()` (VIX-rank thirds, used by the paper/walk-forward path). Each has a real tradeoff; cross-referenced in both docstrings but not unified — open decision.
- `data/processed/*.csv` / `models/*.pkl` are committed/regenerable (git bloat); `requirements.txt` has dead deps (`arch`, `plotly`, `pandas_datareader`) — cheap cleanup, not done.
- `CLAUDE.md`/`README.md` still describe deleted modules (`orchestrator.py`, old `evaluation.py`) and call walk-forward "a stub" — stale, not yet updated.
- `.github/workflows/tests.yml` references test/analysis files deleted in the May 2026 refactor — CI may be silently broken or not testing what it claims to.
