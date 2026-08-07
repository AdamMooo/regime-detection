# Archived — market-internals (breadth / concentration) gauge

**Status: PARKED, unresolved. Archived 2026-08-06. Do not revive without reading the failure below.**

An attempt at a breadth / concentration fragility gauge, built 2026-08-01 against a frozen pre-registration
(`.planning/INTERNALS-BETA-DIAL-PREREG.md`, REV 2, frozen 2026-07-31). Infrastructure was complete —
`internals_gauge` (construction), `internals_h1` / `internals_h2` (the two hypotheses), `internals_controls`,
`internals_dial`, `run_internals_prereg` (orchestrator).

## Why it is parked

**The Europe placebo control was FAILING at the time work stopped.** A placebo that fires is not a detail: it
means the construction was picking up something that should not have been there, so no result from this gauge can
be trusted until that is explained. It was never explained.

It also depended on the retired jump-model evaluation code (`backtest.py`, `run_config.py`), now archived
alongside it under `archive/jumpmodel-v2/`.

## Relationship to the live roadmap

The question this asked — *is index performance broad, or dependent on a few names?* — is still live, as
**Phase 4 (Concentration)**. But Phase 4 warm-started a **different** construction: the French VW−EW leadership
spread from `data/processed/assets_daily.csv` (a true cap-HHI needs paywalled constituent data and must not be
faked with today's membership).

So this is not the Phase 4 implementation and should not be imported into it. If Phase 4's charter ends up
wanting a breadth measure, treat this as prior art with a known unexplained placebo failure — evidence about
what to check, not code to reuse.

Recover at git history.
