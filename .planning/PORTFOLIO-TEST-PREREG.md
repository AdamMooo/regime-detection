# PORTFOLIO-TEST-PREREG — Driver-Balanced Equity-Ownership Efficiency Test

**Status: DRAFT — NOT FROZEN, NOT RUN.** This is a POSITIVE-claim experiment. One-look discipline applies:
review → freeze → overnight cooling-off → explicit dated sign-off → single run → frozen classification.
Weights, metrics, and decision rules cannot be re-decided after results exist.

**Last updated:** 2026-08-02 (draft for Adam's review)

---

## Thesis being tested (the north star, from PORTFOLIO-CONSTITUTION.md)

This is an **equity-ownership optimization problem, not an asset-allocation problem.** The objective is to
maximize lifetime compounded wealth through ownership of equity risk. Alternative sleeves are justified ONLY
if they improve the ability to MAINTAIN, REBALANCE, or INCREASE equity exposure through adverse regimes —
they are structural tools that protect the compounding engine, never return substitutes.

The question: **"can we own the same economic engine with fewer interruptions to compounding — AND with a
war chest we can deploy aggressively into it after it's been crushed?"**

**The offensive core (Adam, 2026-08-02):** the diversifiers are a WAR CHEST. Their entire purpose is to hold
value through a drawdown so we can convert them into equity *when equity is cheap and others are forced out*.
This is why the failure-mode study mattered — not for comfort, but as a **deploy-capability guarantee**: in
every regime that crushes equity, at least one sleeve must survive to fund the buy. (Inflationary bear →
bonds are dead powder, so gold/trend/cash must carry it; deflationary bear → bonds are the powder.) The
mechanism is durable-when-known: forced/panic selling at bottoms is structural, and the disciplined deployer
is paid to provide that liquidity.

## Hypotheses

- **H1 (frictionless):** a static driver-balanced book captures equity-*like* frictionless CAGR (within a
  pre-committed tolerance of 100% equity — see Open Item D) while materially improving **equity participation**
  (up-capture stays high, down-capture falls) and reducing compounding interruptions (maxDD, underwater time).
- **H2 (behavioral/capital-constrained):** once a realistic investor's inability to hold 100% equity through
  the deepest drawdowns is modeled, the driver-balanced book delivers **superior realized compounding** vs.
  100% equity and 60/40.
- **H3 (the offensive core — countercyclical deployment):** a driver-balanced book WITH a pre-committed
  drawdown-triggered deployment ladder — converting the war chest into equity as equity gets cheaper —
  **beats both static 100% equity and the static driver-balanced book** on long-run compounding, because it
  systematically buys the engine cheap using powder engineered to survive the specific crashing regime. This
  is where the structural alpha should be largest.
- **Null:** no candidate beats the benchmarks on the pre-specified efficiency metrics after costs and
  complexity; OR any apparent improvement comes only from sacrificing CAGR to lower volatility → **reject**
  (that is explicitly not the objective). For H3 specifically: the deployment ladder must beat a *naive
  fixed-schedule rebalance* — if the tranche timing adds nothing beyond mechanical rebalancing, drop it.

## Benchmarks

- **100% equity** — the CAGR bar and the participation reference (up/down capture measured against it).
- **60/40 equity/bond** — naive diversification, the thing structural diversification must beat.

## Candidate ladder (nested — each rung must MARGINALLY improve the geometric / behavioral-adjusted outcome
after costs, or it is rejected per the complexity test)

| # | Book | Tests |
|---|---|---|
| 0 | 100% equity | the engine, unprotected |
| 1 | 60/40 equity/bond | naive diversification |
| 2 | Driver core: equity + bonds + cash | deflationary axis + rebalancing dry powder |
| 3 | + modest inflation cover (trend and/or gold, humble weight) | the thin inflation/real-rate axis |
| 4 | Full driver-balanced set | complete spanning set |
| 5 | **Equity-maximized within budget** | highest equity weight the diversifiers permit while respecting the −30% budget — the "own MORE of the engine" variant |

Rung 5 is the sharpest expression of the thesis: does diversification let us run *higher* equity exposure
within the feasibility boundary, capturing more of the engine rather than less?

| 6 | **Rung 4 + countercyclical DEPLOYMENT ladder** | the offensive core — war chest converts to equity as it gets cheaper |

## Central mechanism: the countercyclical deployment ladder (rung 6 — the H3 test)

Pre-committed, mechanical, triggered by *realized* equity drawdown (backward-looking, not a forecast — this
is what keeps it inside the bright line). Proposed schedule — **Open Item E, confirm before freeze:**

- **base state:** rung-4 weights (the peacetime war chest)
- **equity DD > −20%:** deploy 1/3 of the diversifier sleeves into equity
- **equity DD > −30%:** deploy 2/3
- **equity DD > −40%:** all in (~100% equity)
- **recovery (new equity high / DD closes):** rebuild the war chest back to base weights over a pre-set glide

Two things this makes explicit and testable: (1) tranching means we never exhaust powder early and are
*progressively* all-in as it cheapens; (2) the deployment is only as good as the powder that survived — so
rung 6's result is the real payoff of the whole failure-mode / spanning study. **Discipline check:** this is
the one rule that changes total equity exposure. It is defensible as *contrarian rebalancing to realized
price* (buy more as it falls), NOT regime forecasting — but it must be confirmed as inside the constitution's
bright line before freeze (Open Item E), and it must beat a naive fixed-schedule rebalance to earn its keep.

## Weights — FIXED, pre-committed, NOT optimized (an optimizer overfits the studied history)

Proposed structural starting weights (annual rebalance) — **Open Item A, confirm before freeze:**
- Rung 2: equity 80 / bond 15 / cash 5
- Rung 4: equity 70 / bond 15 / cash 5 / trend 5 / gold 5
- Rung 5: equity 85 / bond 7 / cash 3 / trend 3 / gold 2 (or whatever keeps maxDD ≤ budget)

## Data

- US monthly: equity (French mkt TR), bond10 (synthetic 10y TR), gold (post-1971), cash (rf), trend
  (TSMOM proxy 2005+), commod (BCOM 1991+). Long-history rungs use what's available; multi-sleeve rungs run
  on the common sample and are flagged for length.
- International (Japan, Europe) as **out-of-sample robustness**, not primary.

## Metrics (pre-specified)

**PRIMARY**
1. **Equity participation:** up-capture and down-capture vs 100% equity (monthly; and restricted to the large
   drawdown episodes). The headline efficiency read.
2. **Frictionless geometric CAGR** vs 100% equity and 60/40.
3. **Behavioral-adjusted CAGR:** an identical capitulation rule applied to every book — **Open Item B** —
   proposed: *move fully to cash if drawdown breaches −35% for ≥3 months; re-enter after +20% off the low.*
   Realized compounding under this rule is the H2 metric.

**SECONDARY**
4. MaxDD and recovery time (months underwater) — compounding damage.
5. Budget-breach count/severity — feasibility against the −30% boundary.
6. Rebalancing premium — compounding benefit from deploying dry powder into beaten-down equity.
7. Costs: ETF expense ratios + rebalance turnover cost, applied identically to all books.

## Decision rules (pre-committed — no post-hoc reinterpretation)

- A rung is KEPT only if it improves the primary geometric / behavioral-adjusted metric after costs vs. the
  simpler rung below it. Ties go to the simpler book (complexity test).
- **REJECT any book whose only improvement is lower volatility at the cost of CAGR.**
- Inflation-cover sizing (trend/gold) stays modest per the thin-evidence humility; its marginal contribution
  is tested for robustness, not assumed.
- A US-only result that fails the Japan/Europe robustness check is downgraded, not headlined.

## One-look discipline

Freeze this document → overnight gap between freeze and run → explicit dated sign-off (`<name>, <date>: run`)
→ a single run → frozen classification. Reproducibility: the run script and its output are archived; weights
and metrics above are the contract.

## Open items to confirm before freezing

- **A. Weights** — the fixed structural set above (esp. equity-dominant sizing and the rung-5 max-equity book).
- **B. Capitulation rule** — the −35%/3-month / +20%-reentry parameters (the crux of H2).
- **C. Candidate ladder** — the rungs, especially whether to keep both trend and gold separable at rung 3.
- **D. "Equity-like" tolerance** — how close frictionless CAGR must sit to 100% equity to count as H1 success.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
