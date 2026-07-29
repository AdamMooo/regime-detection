# Factor-Model Direction — Gap Analysis (pre-work, NO look, NO prereg)

Created 2026-07-29. Status: **the honest prerequisite before any factor prereg or look.** This
maps professional cross-sectional factor construction (cited) against what this repo actually has,
ranked by what matters. Nothing here spends a look or makes a claim. Companion: RESEARCH-RECORD
2026-07-29 (the pivot), memory [[factor-model-pivot]].

---

## 0. The reframe (why we're here)

Ch1, Ch2, Path-B, and the dispersion feature all tested *single-time-series market timing* and all
lost to a reactive baseline (vol-targeting / EWMA). **That is the literature's own verdict, not our
failure:**

- **Asness (2016), "The Siren Song of Factor Timing"** — factor timing is "highly analogous to
  timing the stock market… difficult and should be done in very small doses, if at all"; the
  incentive to *sell* timing is exactly why it's oversold.
- **Asness, Chandra, Ilmanen & Israel (2017), "Contrarian Factor Timing Is Deceptively Difficult"**
  — valuation-spread timing "works" mostly because it's a **disguised perpetual value bet**; hedge
  out the induced value exposure and the standalone timing benefit is small and unreliable. → This
  is our Chapter-1 Case B ("exposure artifact") in someone else's words.
- **Kim, Tse & Wald (2016)** — even in TSMOM, much of the apparent alpha is the **vol-scaling**, not
  the momentum signal (monthly alpha 1.27% → 0.41% without scaling).

**The load-bearing distinction for our whole program:**
> Vol targeting = *scaling the size of a bet you already hold* — legitimate, survives OOS.
> Factor timing = *changing which bet you hold based on a forecast* — fragile, usually doesn't.

So the JM regime label's ONLY defensible role is **risk-scaling** (Stage 4), never factor-exposure
timing. The *alpha* has to come from the **cross-section** (Stages 1–3), which is the thing this
repo has never built. "Jump Model + Factor Model" = a cross-sectional alpha model (the new work) +
the JM as a risk-side scaler (its honest job).

---

## 1. What we actually have (inventory, 2026-07-29)

- **Factor OUTPUTS, not INPUTS.** Everything in `data/` is Ken French *pre-aggregated*:
  `smb`, `hml`, `mom` (returns of already-formed long/short portfolios), 10 US industry portfolios,
  25 Japan/Europe size×BE-ME portfolios. These are the *finished product* of a cross-sectional
  sort, not the raw cross-section.
- **Zero single-stock data. Zero point-in-time fundamentals. No investable universe.**
- Kept tools: `build_assets.py` (US factors+industries), `build_intl_panel.py` (int'l size/value),
  `build_trend_proxy.py` (momentum), the JM estimator + walk-forward + vol-target library.

This single fact drives the whole gap: **most of professional factor craft operates on a
cross-section of individual securities we do not have.**

---

## 2. The gap, ranked by how much it matters

Severity: 🔴 blocks a real factor model · 🟡 real gap, workable · 🟢 already have it / minor.

| # | Professional standard (cited) | What we have | Gap |
|---|---|---|---|
| 1 | **Cross-section of individual securities** to rank & long/short (Stages 1–3 all assume it) | Pre-formed French portfolios only | 🔴 the fork (§3) |
| 2 | **Point-in-time fundamentals**, lagged to announcement date; as-filed not restated (S&P PIT; FF June-*t* convention) | None (no fundamentals at all) | 🔴 needed for any characteristic signal |
| 3 | **Alpha model ⟂ risk model as separate objects** (Grinold-Kahn; Barra) — blended-score-then-equal-weight is *the* amateur tell | We've only ever built single blended timing signals; no separation | 🔴 the discipline gap that killed attribution in Ch1–3 |
| 4 | **Multiple-testing hurdle**: t>3 (Harvey-Liu-Zhu), ~26%/58% OOS/post-pub decay (McLean-Pontiff), ~65–82% of anomalies fail (Hou-Xue-Zhang) | Our prereg/one-look discipline is strong on *this* already | 🟢 we're ahead here — keep it |
| 5 | **Cross-sectional standardize + winsorize per date; industry-neutralize** (Barra; Asness QMJ) | N/A yet (no cross-section to standardize) | 🟡 straightforward once #1 exists |
| 6 | **Ledoit-Wolf shrinkage / factor-structure covariance** (never raw sample cov when p≈n) | Ch2 used EWMA cov (reactive); no shrinkage/factor-risk model | 🟡 known technique, not built |
| 7 | **Constrained MVO w/ costs, turnover penalty, no-trade bands** (Grinold-Kahn; AQR trading-cost work); FF sorts are "illustrative, not investable" | Ch1–3 used simple weight rules; costs modeled but no optimizer | 🟡 build only if we go investable |
| 8 | **Regime/vol → RISK-SCALING only, not exposure timing** (Asness 2016/2017; Kritzman-Li turbulence; MOP 2012) | We kept trying to use it for timing (closed 3×) | 🟢 now understood — this is the JM's honest role |
| 9 | **Eval: Fama-MacBeth, GRS joint test, IC/IR, deflated Sharpe, PIT universe/survivorship** (FM 1973; GRS 1989; Bailey-LdP; Hou-Xue-Zhang) | We have deflated-Sharpe (stage1 `dsr_*`) + prereg; no FM/GRS/IC machinery | 🟡 partially there; add FM/GRS/IC |

**The "5-10 little things" you bet your leg on, concretely:** #2 PIT lag, #3 alpha/risk separation,
#5 per-date z-score + winsorize + industry-neutralize, #6 covariance shrinkage, #7 costs/turnover
inside construction, #9 Fama-MacBeth + GRS + IC + PIT universe. We already do #4 (multiple-testing
discipline) and now understand #8 (regime = risk-scaling). The one that reframes everything is #1.

---

## 3. The strategic fork (this is the real decision)

Because we have portfolios not stocks (#1), "build a factor model" splits into two very different
programs:

**Path A — portfolio-level cross-section (buildable TODAY, no new data).**
Run rigorous asset-pricing tests on French's portfolio *grids* (US 25 size/BE-ME, industries,
int'l): Fama-MacBeth cross-sectional regressions, GRS joint alpha tests, factor-spanning ("is HML
subsumed by quality?"), IC analysis. This is how academic factor research is actually *tested*, it's
genuinely new territory for this repo, and it needs zero new data. **Limit:** answers "do these
premia exist / is one factor spanned by another / does regime-scaling improve a factor's
risk-adjusted return" — NOT "pick individual stocks."

**Path B — real stock-selection alpha model (the full professional thing).**
Needs single-stock prices + PIT fundamentals + an investable universe (CRSP/Compustat, or a free
proxy — SimFin / yfinance on a curated liquid universe with delisting handling). Then #2, #5, #6,
#7 all become live. This is "rank names, long/short the spread." **Much heavier data lift**, and
the data-quality bar (survivorship, PIT) is exactly where amateur factor models die (#9).

---

## 3b. Path A — progress (started 2026-07-29)

**Chosen: Path A first (Adam).** Built and validated the portfolio-level test bench:
- `build_factor_test_panel.py` → `data/processed/factor_test_monthly.csv` — French 25 size/BE-ME
  value-weight portfolios + FF3 factors, monthly, 1926-07..2026-05 (1199 months), gates pass
  (incl. a raw value-premium integrity check, V5−V1 = +0.47%/mo).
- `factor_tests.py` — `grs_test` (Gibbons-Ross-Shanken), `fama_macbeth`, `factor_spanning`.
  7 tests incl. a simulation-based GRS null-size check (catches a wrong scaling constant).
- **Machinery validated on real data (descriptive, no look):** GRS rejects both CAPM and FF3 on
  the 25 portfolios (p~1e-7 — the known FF result); HML priced (FM t=3.5) and not spanned by
  Mkt+SMB; SMB weak (t=1.0). Known caveat surfaced: FM market premium is unidentified on these
  low-beta-dispersion test assets (intercept absorbs it) — GRS is the clean headline; add
  beta-dispersed test assets (e.g. beta-sorted or industry portfolios) before leaning on FM premia.

**Next on Path A:** (a) add beta-dispersed test assets to fix FM identification; (b) the real
question this bench exists for — does the JM regime label, used as a *risk-scaler* (not a timer),
improve a factor's risk-adjusted return? — which needs a prereg + cooling-off + sign-off before any
look, since it could produce a positive claim.

## 4. Recommendation & next step (still NO look)

1. **Pick the fork (Path A vs B)** — a real decision for Adam. Path A is honest, fast, and uses our
   strengths (discipline + clean French data); Path B is the "real thing" but is a data-engineering
   project first. A sane sequence: **do Path A first** (it's a legitimate research program on its
   own and de-risks whether we even want B), keep B as the graduation.
2. Whichever fork: the **JM label enters only as a risk-scaler** (Stage 4/#8), never as an
   exposure-timing signal — pre-commit that so we don't relaunder a closed null.
3. Then, and only then, a prereg with the Stage-5 gates (Fama-MacBeth/GRS/IC, deflated Sharpe,
   PIT-clean universe) + overnight cooling-off + explicit dated sign-off before any look.

---

## 5. Regime-as-a-FACTOR — researched test design (2026-07-29)

Adam's idea: is the JM regime an **input to the factor model** — i.e. is regime a priced
*cross-sectional* risk factor (do assets whose returns covary with regime shifts earn a premium),
NOT regime-timing. This is the right, higher bar. Deep-research synthesis (cited below):

**The honest prior (what the literature predicts): most likely SPANNED.** Our label is a nonlinear
transform of the market's own downside-vol features, so a portfolio sorted on "regime-beta" loads
on exactly the high-β / high-IVOL cross-sectional dimension that **betting-against-beta (BAB,
Frazzini-Pedersen 2014)** and the low-vol anomaly (Baker-Bradley-Wurgler 2011) already harvest.
Expected outcome: regime-factor α ≈ 0 once BAB is controlled → redundant. This is the v1
"everything collapses onto the vol axis" finding, in cross-sectional form.

**Real precedents (the idea is not crazy):**
- **Ang, Hodrick, Xing & Zhang (2006)** — build **FVIX**, a max-correlation portfolio mimicking
  VIX *innovations*; aggregate-vol-risk is priced at ~−1%/mo. Sign is NEGATIVE (a vol-hedging asset
  is expensive) — theoretically correct via ICAPM. **A positive regime premium would be a red
  flag** (timing artifact), not a win.
- **Ang, Chen & Xing (2006)** downside-beta β⁻ priced ~6%/yr and NOT subsumed by β/size/value/mom —
  the closest surviving precedent; **Lettau-Maggiori-Weber (2014)** DR-CAPM prices across asset classes.

**The two narrow doors where it could survive spanning:**
1. **Jump / tail risk distinct from diffusive vol** — if the *jump* model captures discontinuous
   crash-onset risk (regime switches concentrated at jumps, not gradual vol drift), it may be
   orthogonal to BAB (a diffusive-β story). Benchmark: **Kelly-Jiang (2014)** tail risk priced
   beyond vol; **Bollerslev-Todorov (2011)** jump/tail-fear component of the variance premium.
2. **Downside-conditional covariance beyond symmetric β** (the AC(X)/LMW result) — narrower than it
   looks, since that premium may itself be BAB in disguise.

**The cleanest test for our exact data (FF 25 + FF3 monthly + JM label):**
1. **Build a regime FACTOR return (FMP).** Use the label *innovation* Δs (a factor must be a
   return, and the ICAPM-priced object is the state *innovation*, not the level). Two ways for
   robustness: (a) **beta-sort spread** — trailing-window β of each test portfolio to Δs, monthly
   long-short; (b) **max-correlation mimicking portfolio** — project Δs on base-asset excess returns
   (Breeden-Gibbons-Litzenberger; Lamont 2001 economic tracking, OOS-validated). Call it `REG`.
2. **Spanning regression** `REG = α + b·Mkt + s·SMB + h·HML + βa·BAB (+ low-vol) + ε`. Decision:
   α significant at the **Harvey-Liu-Zhu t>3** bar (Newey-West) ⇒ not spanned. **Must include BAB**
   or the result is a false positive re-discovering the low-vol anomaly.
3. **Max-squared-Sharpe confirmation (Barillas-Shanken 2017/2018):** the correct model-comparison
   criterion — REG helps iff Sh²(FF3+BAB+REG) − Sh²(FF3+BAB) > 0; use **BKRS (2020)** standard
   errors (the Sharpe-difference sampling error is large — don't eyeball it).
4. **GRS** of FF3 vs FF3+REG on the 25 (+ industry + size-mom) portfolios — does REG shrink the
   joint intercepts? The 25 FF portfolios ALONE are weak test assets (Lewellen-Nagel-Shanken 2010) —
   add beta-dispersed assets so a spurious factor can't hide in the FF3 structure.
5. **Sign/economics:** the price of REG-risk must be NEGATIVE (hedging); positive ⇒ timing artifact.

**Top 3 pitfalls that would invalidate the test:**
1. **Look-ahead in FMP betas/weights** — estimate on a strictly PRIOR window (our causal discipline);
   full-sample betas manufacture an in-sample spread that dies OOS.
2. **Not controlling for BAB/low-vol** — the single most likely false positive; α must survive AFTER BAB.
3. **Timing-vs-pricing confusion (the Case-B trap)** + weak test assets + no multiple-testing bar —
   impose t>3, BKRS SEs, and a broader test-asset set; require the α to show up UNCONDITIONALLY
   (Lewellen-Nagel 2006: conditional-only stories that vanish unconditionally aren't priced factors).

**Discipline:** this test CAN produce a SUPPORT claim → cooling-off + explicit dated sign-off before
any look; and since the label was born on the US panel, any surviving α confirms on the
French/MSCI international panels (we already have Japan/Europe) before being called real.

## 6. Tomorrow's plan (concrete, ordered)

All of step 1–3 below are NO-look data/plumbing; the look is gated at step 4.
1. **Data:** fetch AQR's monthly **BAB** factor (+ a low-vol factor if available); produce a
   **monthly JM regime series** (state + continuous stress score) aligned to the panel from the
   existing daily label / `oos_labels`. New builder `build_regime_factor_inputs.py` + gate.
2. **FMP:** add `regime_factor(...)` to `factor_tests.py` (or a new `regime_factor.py`) — both the
   beta-sort spread and the max-correlation mimicking portfolio, betas on a trailing window (causal).
   Tests: recovers a known planted factor; no-lookahead check.
3. **Descriptive spanning (NO look, characterization):** run the spanning regression of REG on
   FF3+BAB and the Barillas-Shanken Sh² check. If α is insignificant / spanned → **CLOSED, cheaply**,
   documented as "regime is the vol/BAB axis in the cross-section." (This is the expected outcome and
   it's a clean result either way.)
4. **Only if step 3 shows an unspanned α:** freeze a prereg (spanning + Sh² + GRS + sign + intl
   confirmation), overnight cooling-off, explicit dated sign-off, THEN the one look.

---

## Key citations (full list in the RESEARCH-RECORD entry / research transcript)

- Asness (2016) *Siren Song of Factor Timing*, JPM — aqr.com/Insights/Research/Journal-Article/The-Siren-Song-of-Factor-Timing
- Asness, Chandra, Ilmanen & Israel (2017) *Contrarian Factor Timing Is Deceptively Difficult*, JPM
- Harvey, Liu & Zhu (2016) *…and the Cross-Section of Expected Returns*, RFS (t>3 hurdle)
- McLean & Pontiff (2016) *Does Academic Research Destroy Return Predictability?* JF
- Hou, Xue & Zhang (2020) *Replicating Anomalies*, RFS (NYSE breakpoints + value-weight)
- Ledoit & Wolf (2004) *Honey, I Shrunk the Sample Covariance Matrix*, JPM
- Grinold & Kahn (2000) *Active Portfolio Management* (alpha⟂risk, Fundamental Law, transfer coef.)
- Fama & MacBeth (1973); Gibbons, Ross & Shanken (1989) — the cross-sectional test workhorses
- Bailey & López de Prado (2014) *Deflated Sharpe Ratio*, JPM
- MSCI/Barra E3 Handbook (exposure standardization, factor-risk structure)

Regime-as-a-factor (§5):
- Ang, Hodrick, Xing & Zhang (2006) *The Cross-Section of Volatility and Expected Returns*, JF — FVIX, aggregate-vol priced ~−1%/mo
- Ang, Chen & Xing (2006) *Downside Risk*, RFS (β⁻ priced ~6%/yr, not subsumed); Lettau-Maggiori-Weber (2014) DR-CAPM, JFE
- Frazzini & Pedersen (2014) *Betting Against Beta*, JFE; Baker-Bradley-Wurgler (2011) low-vol anomaly, FAJ — the spanning threat
- Breeden-Gibbons-Litzenberger (1989); Lamont (2001) *Economic Tracking Portfolios* — factor-mimicking-portfolio construction
- Barillas & Shanken (2017 *Which Alpha?*, 2018 *Comparing Asset Pricing Models*), Barillas-Kan-Robotti-Shanken (2020) — max-squared-Sharpe model comparison + correct SEs
- Lewellen & Nagel (2006) *Conditional CAPM Does Not Explain Anomalies*, JFE; Lewellen-Nagel-Shanken (2010) *Skeptical Appraisal of Asset Pricing Tests*, JFE (weak-test-asset critique)
- Kelly & Jiang (2014) *Tail Risk and Asset Prices*, RFS; Bollerslev & Todorov (2011) *Tails, Fears, and Risk Premia*, JF — the jump/tail door

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
