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

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
