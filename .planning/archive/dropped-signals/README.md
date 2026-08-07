# Dropped signals — killed at the charter stage, before any look was spent

These signals were researched to a full pre-registration and then **not built**. That is the Stage-0 gate
working as designed (D-19: the default answer to a proposed signal is NO, and the scarce resource is research
time and the investor's attention, not code).

Kept rather than deleted so the same idea does not get re-proposed in six months from reasoning alone — the
recurring failure this repo has already been bitten by.

**Nothing here was validated. No look was spent on either. These are decisions, not results.**

## 05 — Diversification / Absorption ratio — DROPPED 2026-08-06

Absorption ratio (Kritzman, Li, Page & Rigobon 2011): share of cross-sectional variance on the leading
principal components.

**Killed on readability, not on mechanism.** Its only unique content over volatility is a ~1-month lead, and
the matched cross-region panel publishes ~2 months late — verified at a **69-day lag** across all three
French-derived panels in `data/processed/MANIFEST.csv`. A one-month lead arriving two months late is
unreadable live no matter how well it validates.

Two structural findings behind it: there is **no matched US cross-section** (US panels are industry sorts,
international are 25 size/BM — the same object mismatch that made the earlier sector-dispersion lead failure
uninterpretable), and **French publishes no international industry sorts at any frequency**, so the source
paper's own 51-industry object cannot be replicated out-of-sample.

**If revived:** the honest form is "a descriptive US-only measurement finding, `production` unreachable" —
never "solve the latency later." The one piece worth keeping regardless is its V3b test: the
low-volatility / high-absorption quadrant ("calm but fragile") must be materially populated, which is the
falsifiable form of the whole pitch. Under equicorrelation the overlap with volatility is near-definitional,
not incidental.

## 07 — Funding stress — DROPPED 2026-08-06

Funding-liquidity / market-liquidity spiral (Brunnermeier & Pedersen 2009). Mechanism is real and distinct.

**Killed on measurability.** The only construction that is narrow, point-in-time-clean, credit-free and
unspliced (`SOFR99 − SOFR`) begins in 2018 and contains two episodes — it can never clear its own validation
bars. The LIBOR→SOFR transition is a hard break, not a splice: 2008 is observable only pre-break and
September 2019 only post-break, and any scale adjustment would be fitted on the 2018–22 overlap, which
contains March 2020 — the single episode the signal most needs to identify.

**The finding worth remembering:** `cp3m` is 28.8% missing since 1997, with **63% coverage through the GFC**
and **45% through the September 2019 repo episode**, longest gap 55 trading days. The missingness is
**endogenous** — the Fed publishes a CP rate only when trade data are sufficient — so the series goes dark
precisely when the market is too stressed to price, and its silence would read as `intact`. A stress flag that
goes quiet during stress.

All three composites were rejected: NFCI revises its entire history weekly including the estimated indicator
loadings; STLFSI4 embeds volatility and credit-spread inputs directly; and the OFR funding sub-index reports
each category's *contribution to a single common factor*, so an indicator that decouples gets a small loading —
structurally biased against exactly the decoupling that would be its unique information.

**Not folded into Phase 9 (tail), despite Phase 7 proposing it.** Phase 9's counter-argument won: impaired
funding reduces dealers' capacity to supply protection, *raising its price* — so funding is a candidate
**cause** of the tail signal's moves. Folding a cause into the price it moves destroys the ability to observe
them disagreeing, and creates a two-mechanism module.

## 08 — Crowding — DROPPED 2026-08-05

Dropped earlier, before this batch: proxy-only construction, real positioning data infeasible solo, and it
risks re-reading the volatility axis.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
