---
date: "2026-04-25 16:30"
promoted: false
---

HDP micro-states end-to-end: currently the HDP-HMM discovers 7 meaningful states naturally (Crisis-Vol, Elevated-Vol, Low-Vol, Low-Vol-B, Moderate-Vol x3) but the in-sample naming path collapses them to 3 via rank-based labeling. The K=3 enforcement in config was a workaround for the old classic HMM (hmmlearn) where K=4 had overlapping states — it does NOT apply to the HDP-HMM which has its own pruning/merging. Fix would be: use VOL_BRACKETS absolute naming consistently on the HDP path everywhere (signals, dashboard, GARCH fitting, regime_results.csv) instead of rank-based naming. Pros: captures genuine market granularity the model already found, finer-grained risk signals, richer transition matrix. Cons: more regimes = noisier signals for trading, downstream consumers (algo-trading-bot, portfolio-manager) need to handle variable K, more GARCH fits per run (already parallelized). Discuss before implementing — touches MacroRegimeDetector API which is a hard cross-project constraint.
