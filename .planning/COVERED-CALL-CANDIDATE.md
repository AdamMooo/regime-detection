# Candidate — Regime + Vol Conditioned Covered-Call Overwriting

**Status: DRAFT CANDIDATE. One-look NOT spent. This is a Layer-3 (economic/algo) REOPEN.**
Per `CLAUDE.md` + `NOTES.md`: Layer 3 is closed and this repo's identity is "detection +
paper + live feed, never an algo-backtest program again." Running this requires (1) Adam's
**explicit, conscious decision to reopen Layer 3**, (2) the standard **overnight cooling-off +
named/dated sign-off** (positive-claim run), and (3) a frozen prereg promoted out of "DRAFT."
Nothing here is committed to the roadmap until then.

Origin: Adam, 2026-07-28 — "run 2 models: the jump model for overall regime (bull/bear) and the
vol environment for whether it's favourable for covered-call writing."

---

## 1. Does it clear the gates that killed prior ideas?

- **Killed VRP axis?** No conflict. The repo killed *VRP/implied-vol as a **detection feature***
  ("does IV carry regime info beyond realized vol?" — no; everything collapses onto the vol axis,
  `NOTES.md:84`, `RESEARCH-RECORD.md:733`). This uses VRP as a **harvestable premium**, not a
  predictor. Different question. Clears the gate.
- **Information gate ("new use")?** Passes — covered-call overwriting is a new *use* and a new
  *instrument* (short-vol payoff), and sourced from CBOE buy-write indices it is also a new *data
  source*. Not a re-ask of a settled null.
- **The real hazard — "Ch1 in a costume."** Israelov–Nielsen (AQR, *Covered Calls Uncovered*,
  FAJ 2015) decompose a covered call into three exposures:
  1. **Passive equity** — most of the risk and return; compensated beta.
  2. **Short volatility (VRP)** — **< 10%** of risk, realized **Sharpe ≈ 1.0**; the *good* part.
  3. **Equity timing / reversal** — **~25%** of risk, ~no reward; **uncompensated** (from the
     call's time-varying delta).
  Because a naive buy-write is mostly component 1, conditioning it on the bull/bear regime is
  to first order *conditioning equity exposure on the regime* = **Chapter 1**, which is closed
  (exposure artifact; VT wins). Any version that is just "regime-time the BXM return stream"
  will almost certainly be **race #4** and lose to a vol-targeted equity twin.

## 2. The only framing that is NOT Ch1 rerun

AQR neutralizes the uncompensated equity-timing exposure (component 3) with a mechanical
**delta-hedge**, isolating the pure short-vol premium and improving Sharpe / lowering vol and
downside beta. This repo has no options-data / delta-hedge infrastructure.

**Hypothesis (the one worth a look):** the JM regime label is a cheap, **lag-tolerant substitute
for AQR's delta-hedge** — it manages the covered call's uncompensated equity-timing exposure
(don't overwrite / write further OTM in a bull regime, where the upside cap bites) without an
options desk. Economically: the **vol level governs *when* premiums are rich** (incumbent's turf);
the **regime governs *whether the upside cap is safe* (drift sign)** — the one axis a vol model is
structurally blind to. Lag-tolerant because getting called away in a bull is a slow, months-long
event, so a lagged "we're in a bull" label is still actionable.

**The load-bearing empirical precondition (test BEFORE spending the look):** does the JM label
carry **drift-sign** information beyond the contemporaneous vol level? The repo's own finding is
that the label is "a vol-state sensor, not a bear detector" (`NOTES.md:91`). If the label has no
drift-sign content beyond vol, this collapses to the vol axis and there is no reason to run it.
→ A **no-look descriptive check** (JM label vs BXM-minus-SPY relative performance, conditioned on
a vol bucket) should gate the decision to reopen at all.

## 3. Instrument & data

- **Primary substrate:** CBOE **BXM** (S&P 500 ATM buy-write, TR, daily from 1986-06-20) and
  **PUT** (put-write). Free (investing.com / barchart / Cboe DataShop). Condition entry/exit into
  the *published* return stream — no options modeling, no IV data required.
- **Sophisticated incumbent to beat:** CBOE **dynamic** buy-write family (CALRD/RUTD) — already
  time overwriting on 25-delta call IV (strikes nearer ATM when calm, further OTM as vol rises)
  and beat static BXM on Sharpe and drawdown. Our realized-vol-only arm must clear this bar too.
- Long-run BXM stats for context: ~8.4% ann. return, 10.7% vol, −35.8% max DD, vs S&P 500
  10.9% / 15.2% / −50.9% (Cboe factsheet, since 1986). Lower return, lower risk — the trade-off
  the regime signal is supposed to time.

## 4. Prereg structure (to be filled + frozen if reopened)

- **Arms:**
  - `A0` static BXM (unconditional overwrite) — the thing to add value over.
  - `A1` vol-only-conditioned overwrite (realized-vol bucket; the honest incumbent — mirrors CALRD logic).
  - `A2` **regime+vol-conditioned** overwrite (the hypothesis): write when NOT strong-bull AND vol favorable.
- **Mandatory exposure-matched controls (the C1 lesson):** a **vol-targeted equity** twin
  (Ch1's winner) and a matched static equity/BXM blend — because much of BXM is beta, an economic
  claim is uninterpretable without them. Random persistent placebos + surrogate/iid null bands.
- **Decision rule:** `A2` must beat BOTH `A1` and the VT twin on the utility-fee metric with a CI
  excluding 0 (paired stationary bootstrap), or the label adds nothing beyond vol → NULL, and it
  is race #4. Pre-commit the fee metric, delay (next-close, delay=2 headline), costs, one look.
- **Out-of-hypothesis-sample:** if the drift-sign precondition was found on the US panel, confirm
  on an international buy-write proxy before any SUPPORT.

## 5. Open design questions for Adam

1. Gate/switch vs graded (write-fraction / strike-distance as a function of regime × vol)?
2. Own the equity leg (buy-write = long SPY + short call, so downside is unhedged) or treat BXM as
   a black-box return stream? The former lets you add a vol-target on the equity leg (closer to
   Israelov's spirit); the latter is cleaner but less controllable.
3. Is this a personal-positioning tool (which the parked Ch3 exposure runner also serves) or a
   paper chapter (Race 5, "regime-conditioned overwriting loses to vol-conditioned overwriting")?
   The honest-null outcome is publishable either way and consistent with the negative-paper thesis.

## Citations

- Israelov & Nielsen, *Covered Calls Uncovered*, Financial Analysts Journal 71(6), 2015 —
  three-component decomposition; risk-managed (delta-hedged) covered call.
  https://images.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Covered-Calls-Uncovered.pdf
- Whaley, R., *Return and Risk of CBOE Buy Write Monthly Index*, J. Derivatives, 2002.
- Cboe BuyWrite Indices Methodology / BXM factsheet —
  https://cdn.cboe.com/api/global/us_indices/governance/Cboe_BuyWrite_Indices_Methodology.pdf
- Cboe, *How Dynamic Buy-Write Indices CALRD and RUTD May Help Manage Volatility* (IV-conditioned
  strike selection; beats static BXM) —
  https://www.cboe.com/insights/posts/how-dynamic-buy-write-indices-calrd-and-rutd-may-help-manage-russell-2000-index-volatility

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
