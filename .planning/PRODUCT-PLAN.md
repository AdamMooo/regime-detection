# Product Plan — Holdable Momentum-Based Strategy + Regime Communication Layer

## ORIENTATION (2026-08-01) — read this first, everything else is detail

**The purpose, one sentence:** run an aggressive, momentum/factor-driven equity book almost all the
time, and have one trustworthy trigger to step OUT into safety when equities are genuinely done for
— not to predict, not to time entries/exits finely, just to react correctly when it's real.

**PROVEN, usable today, don't re-litigate:**
- **Equity selection engine:** 48-industry momentum sleeve (`momentum_breadth.py`) — 12-1 skip-month,
  inverse-vol weighted, buffered. OOS-robust (8/10 decades, Europe confirms, Japan weak-as-literature-
  predicts). This is what decides WHICH equities, all the time you're in.
- **Cost/tax reality:** survives realistic costs up to 100bps (Sharpe 0.69-0.81). Tax drag in a
  non-registered account (~4.5 pts/yr) is bigger than any cost/turnover tuning could ever recover —
  **run this inside RRSP/TFSA if at all possible, biggest lever available, zero research needed.**
- **The de-risk trigger is a BINARY SWITCH, not a smooth dial** — this matches how you actually trade
  (100% equity, out to safety only when it's real). Vol-targeting (smooth, continuous) and the JM
  (laggy, not even the best detector) are NOT the right tool for this job. A vol-threshold+hysteresis
  binary switch, tested honestly (causal, properly lagged — an earlier version of this had a real
  lookahead bug, caught and fixed same session), trades some Sharpe/return (0.53 vs 0.61 raw) for
  roughly half the max drawdown (-23% vs -51%) and flips 2008 positive. Directionally right, NOT yet
  fully proven — only tested on 2 crisis windows (2008, 2022) in a 20-year sample; needs the full
  history (back to 1970s/1930s in `market_daily.csv`) before it's trustworthy.
- **When "out," hold a small STATIC blend (gold+trend+bonds), don't try to actively pick the best
  defensive asset** — timing that was tested (Path-B) and lost to just holding the static blend always.

**TESTED AND KILLED — do not revive without genuinely new information:**
- Dynamic/regime-timed allocation (min-var/trend-gating) — loses to static (`dynamic_allocation.py`).
- The trend-signal "confidence dead-zone" refinement — looked good on gold alone in Oct 2008, worse
  across the whole trend universe on every metric when tested honestly (`build_trend_proxy_deadzone.py`).
- Dispersion-lag (the -40d lead) — US-only artifact, did NOT generalize to Japan/Europe. Dead.
- JM as a timing/allocation signal, or as the best detector — 5 closed nulls; a dumb vol-threshold+
  hysteresis rule beats it on precision/recall/lag (`detector_benchmark.csv`). JM's only remaining
  claimed value (stable label = easier for a human to trust) is a real hypothesis but UNTESTED —
  don't oversell it; it costs nothing to leave running as color commentary, but isn't proven to add value.

**GENUINELY OPEN, not yet decided:**
- Gold+trend sizing as a permanent diversifier — real, evidenced, correlation-checked as genuinely
  distinct (not double-counting the sleeve), but not proven at any specific size; needs rescaling to
  your real 80-90% equity target (tested at 60/40 and 85/15 placeholders so far, both showed WORSE
  risk-adjusted returns than expected at 85/15 specifically — a real, still-unresolved tension worth
  another look with a properly-scaled base).
- The binary-switch trigger — promising, needs full-history validation before trusting it.
- Fragility gauge (breadth/concentration early-warning) — infrastructure built, no look taken, needs
  your sign-off on a calm day, not mid-session.



Created 2026-07-30. Goal: **A (make money) + B (advisor-holdable) as ONE product.** Grounded in the
2026-07-30 deep-research deliverable (RESEARCH-RECORD), not in-repo backtests. Every phase is
build/characterization (NO look spent) until Phase 5 makes an OOS economic claim — at which point the
standing discipline kicks in (prereg + overnight cooling-off + explicit dated sign-off).

## The thesis (why this shape)

The edge is **cross-sectional momentum** (the one real return-adder we found: industry momentum beat
EW 0.67→0.76, decade-robust, low overfit). Its blocking problem is the **crash** (−72% DD → fails B).
The research verdict: **do NOT fix standalone momentum** (vol-scaling is a long-short-WML tool; it
failed on our long-only coarse tilt because our crash is beta+sector-concentration, a different animal).
Instead: **change the signal (residual momentum) + diversify the crash away (value, negatively
correlated) + add breadth + implement with cost discipline.** Regime work = the client comms layer, not
a trade signal.

## Phases (each with a GATE that must pass to proceed, and a KILL criterion)

**Phase 1 — Residual momentum signal.** Rank industries on 12-1 momentum of the RESIDUALS from a rolling
36m FF3 regression (vol-standardized), not raw returns. Strips the factor betas that cause the crash
(Blitz-Huij-Martens). Compare raw vs residual momentum on Sharpe AND the 2000-09 crash decade + max DD.
- GATE: residual momentum reduces the crash-decade loss and/or max DD vs raw, without killing the edge.
- KILL: if residual momentum is no better than raw on the drawdown → the "2× Sharpe" doesn't transfer to
  industries (research flagged this is untested on 10-48 names); fall back to leaning on Phase 2+3.

**Phase 2 — Value sleeve → value+momentum blend.** Add an industry value signal (book-to-market if
available from French industry chars; else long-term-reversal proxy, 60-13m past return). Blend 50/50
with (residual) momentum. Value is long exactly when momentum crashes (AMP 2013) → structural offset.
- GATE: the blend's 2000-09 decade and max DD become materially holdable (target: DD shallower than a
  static diversified equity portfolio, not −72%).
- KILL: if value adds nothing to holdability → reconsider whether an equity-only product is viable at all.

**Phase 3 — Breadth: 10 → 30/48 industries.** Rebuild the panel at finer granularity (Ken French 30/48
industry portfolios, `build_assets.py` pattern). More independent bets → less sector-concentration crash.
- GATE: finer universe reduces DD / improves stability vs 10.
- KILL: none (pure improvement; if it doesn't help, stay at the coarser, cheaper universe).

**Phase 4 — Implementation harness (make it net-of-cost real).** Skip-month (mandatory —
Grundy-Martin), asymmetric BUFFERING / no-trade bands (enter top-X%, hold until out of top-Y% — AQR's
key turnover tool), monthly rebalance, explicit turnover + cost + short-term-tax drag accounting.
- GATE: the edge survives net of realistic costs + turnover (validate OUR turnover; don't trust AQR's
  self-interested 23bps/yr — treat as best-case).
- KILL: if the premium dies net of honest costs/taxes → not a deployable product; document and stop.

**Phase 5 — OOS / walk-forward validation + the ECONOMIC CLAIM gate.** Walk-forward the whole blend
(all params causal / a-priori). THIS is where a positive claim could arise → prereg + overnight
cooling-off + explicit dated sign-off + (since signals born on US industries) international confirmation
BEFORE the one look.

**Phase 6 — Regime communication layer (B).** Wrap the strategy with the regime read
(turbulence×trend + stable JM label) that EXPLAINS the current posture to a client ("blend is defensive
because we're in regime Y") — the holdability/behavior-gap value. Ships into portfolio-manager.

## Discipline (non-negotiable)
- Phases 1-4 are characterization/engineering (no look). Phase 5 is the one look, fully gated.
- No parameter grid-search for best Sharpe (overfit refused); use a-priori standard params (12-1, 36m,
  skip-month, 50/50) and report sensitivity, not optima.
- Every claim comparative + cost/turnover-honest; kill criteria are real, not decorative.

## ARCHITECTURE CORRECTION (2026-07-30, after Phases 1-2)

Two instructive negatives reshaped the plan:
- **Phase 1 (residual momentum): NET NEGATIVE on 10 industries.** Tamed the 2000-09 crash (WML −0.15→+0.35)
  but hurt every other era; full-sample Sharpe 0.78→0.73, DD −52.6→−56.6. Residual momentum is
  breadth-hungry (a single-stock result) — doesn't transfer to 10 names. Needs Phase 3 breadth first.
- **Phase 2 (value+mom blend): NO crash offset — corr(mom,value)=+0.96.** The negative value-momentum
  correlation is a LONG-SHORT (WML vs HML) property; LONG-ONLY tilts are ~95% market beta, so the blend
  is still ~market and DD stayed ~55%. **A long-only equity product's drawdown IS the market's drawdown;
  you can't fix it with equity factors.**

**Corrected architecture — the drawdown fix lives at the ASSET-ALLOCATION layer, not the factor layer:**
> Momentum-tilted equity SLEEVE (the modest alpha, 0.78 vs 0.70) INSIDE a diversified vol-targeted
> multi-asset allocation (the holdability — `risk_engine.py` already cut DD −58%→−8/−28%) + regime
> read as the client comms layer. This is what target-risk/balanced funds actually are.

Revised sequence: (A1) assemble sleeve-inside-allocation, measure end-to-end DD+return [NEXT];
(A2) breadth 30/48 to improve the sleeve + revisit residual momentum with enough names; (A3)
implementation harness (skip-month, buffering, costs); (A4) OOS + prereg gate; (A5) comms layer.

## Status
- [x] Phase 1 residual momentum — DONE, net negative on 10 industries (breadth-hungry); revisit after breadth
- [x] Phase 2 value blend — DONE, +0.96 corr in long-only; drawdown is market-beta → fix at allocation layer
- [x] A1 assembled sleeve-in-allocation — beat JM 0.92 vs 0.50 (compare_vs_jm.py); dynamic allocation
      tested + REJECTED (min-var/trend-gating lose to static — dynamic_allocation.py) → allocation STATIC
- [x] A2 breadth — 48-industry buffered momentum beats 10 (Sharpe 0.74→0.81, DD −73→−51; momentum_breadth.py);
      residual momentum breadth-hungry, parked; confidence=consistency helps as MILD tilt (conviction_momentum.py)
- [~] A3 implementation harness — buffering + skip-month DONE in momentum_breadth; costs/tax/turnover realism TODO
- [x] **A4 OOS/walk-forward + international confirmation — DONE 2026-07-31 (validate_product.py).** Sleeve
      edge OOS-robust in time (8/10 decades, incl. 2010s/2020s); Europe strong (+0.15), Japan weak-as-
      literature-predicts (+0.07); allocation = DD/holdability not Sharpe. Characterization, no look spent.
- [x] **A5 regime communication layer (B) → portfolio-manager — CONFIRMED SHIPPED 2026-08-01.**
      Docs had gone stale; audit found it's fully live: `regime_card.json` (health/skill/gauge/history
      all populated) fetched PAT-authed by portfolio-manager's `src/regime.py`, rendered in
      `daily_report.py` (one-liner) and `weekly_regime_brief.py` (full deep-dive incl. skill/history),
      both verified via real GH Actions runs since 2026-07-29 (portfolio-manager's own NOTES.md).
      One by-design caveat, not a gap: the PAT has an expiry; on lapse both regime sections
      silently self-omit rather than failing loud.

Revised improvement sequence AFTER A4 passes: (2) multi-factor value+quality COMPOSITE rank (not tilt-blend
— +0.96 corr trap); (3) diversify allocation w/ trend+gold (honest 2022 stock-bond-together fix, as a
diversifier not a timer); (4) mild confidence tilt + buffering; (5) ship comms; (6) single-stock graduation
(delisting-aware data — survivorship is THE risk there; French data is clean, stocks are not).

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
