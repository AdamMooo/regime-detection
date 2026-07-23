# Regime Program — Goal & Roadmap

Last updated: 2026-07-23. Forward-looking program doc. Chapter-1 receipts:
`V2-JUMPMODEL-PREREG.md` (frozen) + `V2-JUMPMODEL-PLAN.md` (execution history) +
`RESEARCH-RECORD.md` 2026-07-23 section.

## Goal (Adam, 2026-07-23)

**Regime-aware allocation.** Learn the state-conditional behavior of asset classes and factors
(a regime-switching factor model), and allocate GRADEDLY across them — tilts, never 0/100 cash.
Speed is explicitly de-prioritized: chapter 1 proved regime *timing* loses the reaction race to
vol targeting even with a perfect detector; the program now lives exclusively in lag-tolerant
uses (episodes 60–200d vs ~8d detection lag).

## Design rules (carried from chapter 1, non-negotiable)

1. **Matched baseline:** the primary comparison is always [conditional allocator] vs the
   IDENTICAL allocator with conditioning removed — isolates regime awareness from
   diversification/exposure.
2. **Exposure-matched controls mandatory:** placebo persistent states (matched durations),
   shuffled states, matched static mixes. "Bonds in 2008" is the fee-vs-B&H trap in new clothes.
3. **Graded by evidence, floors on weights:** allocation blends state portfolios by a pinned
   mapping of the filter's value gap (continuous "how bear"); asset floors keep it a tilt.
   (Absorbs the old Track-2 soft-exposure idea — it is the allocation mechanism.)
4. **Shrinkage toward unconditional moments:** ~30 bear episodes → per-state estimates are
   noisy; the state tilts estimates, never replaces them (James–Stein logic).
5. Everything else from CLAUDE.md discipline: prereg/one-look, causal-only, next-close
   execution, costs identical across arms, honest baselines (incl. vol-target and TSMOM-class
   rules where relevant).

## Roadmap

1. **Prove the sensor** (NEXT): benchmark bear calls vs ex-post datings (Pagan–Sossounov,
   Lunde–Timmermann); characterize the two states; SPY-splice live tail (French lags 1–2mo).
   The λ lag-vs-whipsaw frontier + asymmetric penalties live here as sensor diagnostics.
2. **Expand the panel** (`build_panel.py` extensions + gates): French 10-industry daily
   portfolios + SMB/HML/MOM (1926+); synthetic long-history 10y bond TR (v1 recipe; key-free
   FRED yield endpoint); gold (1968+); cash = RF.
3. **The state-conditional atlas** (the learning deliverable, descriptive, in-sample, labeled
   as such): per-state ann. return / vol / Sharpe / correlations for every asset class and
   factor, block-bootstrap CIs, 60+ years. New pages in `results/report.html`. This is where
   conditional factor premia (Robeco FAJ 2023; KPT FAJ 2012 lineage) do or don't show up in
   OUR states — and it informs, but does not gate, the prereg.
4. **Prereg'd allocation test** (confirmatory, one look): graded conditional allocator vs
   matched unconditional allocator; primary = FKO fee (γ=10; γ=1 secondary), net 10 bps,
   delay=2; full control battery per design rules; frozen before any OOS result.

## Status

- Chapter 1 (timing claim): CLOSED, Case B — deflation + exceptional instrument.
- HDP/v1 machinery: fully retired 2026-07-23 (no consumer existed; git history has it).
- Steps 1–2 are buildable now; step 4 freezes only after 1–3 exist.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
