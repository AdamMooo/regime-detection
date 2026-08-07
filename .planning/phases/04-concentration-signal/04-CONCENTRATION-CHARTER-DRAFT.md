# Research Charter — Concentration Signal (Phase 4)
# DRAFT — NOT FROZEN, NOT SIGNED
v0.2 · 2026-08-06 · **unsigned** · **no look spent** (coverage inspection only; long-form v0.1 in git history). Built 2026-08-06:
`build_concentration.py` · `concentration.py` · `tests/test_concentration.py` — **no bar below has run.**

**Verdict — PROCEED on a respecified measurement.** The assumption clears Stage 0; the kickoff's observable does not: a cap-weighted-
minus-equal-weighted spread measures a *rate*, its "equal-weighted" leg is a mean of cap-weighted *industry* returns (`build_assets.py`
keeps the value-weight block only), and the residue is ≈ −`smb`, a published risk-premium factor that fails §(b). **Spread-only ⇒ DROP.**

## Header
- **Signal** Concentration · **assumption** *"the index is not dependent on a few names"* · **clock monthly** · **maturity ceiling
  `research`** (capped by resolution · international coverage · restatement — see Data).
- **Monthly is forced and honest:** the firm-count and market-cap blocks are monthly in *every* region — v0.1's claim of a US **daily**
  read was wrong (verified in `25_Portfolios_5x5_CSV.zip`) — and buckets re-form only each June.
- **Investor question** — *"How much of the index's capital sits in its largest constituents, how unusual is that versus its own
  history, and which way is it moving?"*
- **Ledger status — recommend NONE:** `eff_n` has no mechanical boundary (unlike sign zero in stock-bond correlation), so banding it
  would re-introduce the knob the volatility reframe removed.

## Stage-0 gate — PASS for the level measure
A cap-weighted index is a claim on a *composition* that drifts silently; as capital concentrates, index variance shifts toward a few
firms' idiosyncratic outcomes — invisible to volatility (a top-heavy index can be calm) and in no admitted signal. **G4 decides:
removing the level leaves a permanent blind spot; removing the rate changes nothing, since `smb` is already on disk. PASS level / FAIL
rate.**

## Mechanism — PASS (risk-management channel, structural)
Index return is `Σ s_i r_i`; as the share vector concentrates, the diversifiable share of variance shrinks and the index inherits its
largest constituents' idiosyncratic variance — `eff_n = 1/Σ s_i²` is the standard summary. **It survives being known:** no forward-return
claim, so nothing to arbitrage. The **risk-premium reading is REFUSED** — that is what the rate descriptor is, the size premium's
post-Banz (1981) decay being the case in point. Refs — HHI (Herfindahl 1950 / Hirschman 1945) · Meucci (2009) effective number of bets ·
Campbell–Lettau–Malkiel–Xu (2001) variance decomposition · **Gabaix (2011)** granular origins. **Pre-registered limitation:**
concentration rises both from winner-take-most economics (Bessembinder 2018) and from a narrow re-rating of a crowded set; **no free
data separates them** ⇒ report level + rarity, never a direction of concern.

## Bars and rejects (one look, one frozen script; every number `[recommended — Adam to confirm/override]`)
- **V1 causal** — `assert_causal(build, panel)`; rarity expanding, never full-sample. **R1** leak ⇒ **kill**.
- **V2 reconstruction integrity** — `n_i·c_i` is a reconstruction, not a published total; share-weighted bucket returns must track the
  published cap-weighted market return, corr ≥ 0.95, mean abs monthly diff ≤ 25 bp. **R2** ⇒ **kill**.
- **V3 resolution — MAKE-OR-BREAK, reported FIRST.** `eff_n` IQR ≥ 10% of its median **and** its causal percentile flags ≥ 2 of three
  pre-named episodes (US 1998–2000, US 2020–24, Japan 1987–89, the last outside coverage). **R3** ⇒ close **NOT MEASURABLE** — expected
  and legitimate: the Mag-7 question is seven names *inside* one bucket.
- **V4 decoupling from volatility** (diagnostic, not the gate — §(b)) — ≥ 12 consecutive months with concentration rarity ≥ 0.80 while
  `vol_descriptors` rarity ≤ 0.50. **R4** ⇒ **demote to `research`**, redundancy declared; not a kill.
- **V5 out-of-hypothesis sample (Japan, Europe)** — identical monthly construction, V2 passing regionally, same order of variation; a
  region with < 2 distinct rarity>0.90 episodes is **UNDERPOWERED**, reported as insufficient coverage and never as weak support. **R5**
  all fail ⇒ **INCONCLUSIVE**, US-only. (`run_oos.py` needs a monthly loader.)
- **V6 restatement** — the vendor rebuilds history from its current database ("202606 CRSP"), so the series is restated, not archived;
  fresh-fetch drift ≤ 1 bp. **R6** ⇒ not a kill, but the point-in-time claim is *qualified*.

## What it explicitly does NOT claim (the boundary)
Reports `eff_n`, `top_share`, their rarity and direction, then **STOPS**. It does not predict returns, drawdowns or a market top; does
not call high concentration a bubble or low concentration safe; produces no threshold, state label, trigger or single score; and is
never a buy, sell, risk-on, risk-off, overweight or underweight statement, an allocation or exposure instruction, or a position-sizing
or risk-budget input. The decision is the human's, downstream.

## Data — verified 2026-08-06, coverage inspection only
`25_Portfolios_5x5_CSV.zip` (public Dartmouth, no key) carries **monthly** `Number of Firms in Portfolios` and `Average Market Cap`
blocks beside the returns: **1926-07..2026-06, 1200 months, 25 buckets, zero NaNs** (the block is "Average Market Cap", not "Average
Firm Size" as v0.1 said). `n_i × c_i` gives bucket capital mass — free, survivorship-clean, no membership list; Japan/Europe carry the
same blocks monthly from 1990-07, their *daily* files returns only. **The kickoff's "needs paywalled constituents" verdict is wrong for
a bucket-level measure**, right for a name-level one. **Out of reach:** name-level shares and any "largest *n* names" phrasing ·
concentration *inside* the top bucket (= R3, the most important limitation) · Japan's own 1987–89 peak (data starts 1990-07 — the twin
of Phase 2's missing 1970s inflation regime) · true vintages · free-float, buybacks, cross-holdings, multi-class shares. **Spec:**
`s_i = n_i c_i / Σ n_j c_j` over the 5×5 buckets, `eff_n = 1/Σ s_i²` with `top_share`; rarity = causal expanding percentile (min 120
months) + expanding z; direction = 12-month change in the percentile. Schema denies the `size`/`weight`/`score` segments ⇒ `eff_n`,
`top_share`, `eff_n_pctile`, `eff_n_z`. `[recommended: 5×5 primary, the 10 size deciles as V3's robustness check]`

## Cross-signal (registered pre-look)
Volatility measures amplitude, not how few sources produce it — present side by side, never merge. Stock-bond correlation ≈ zero
expected, but **the real-rate cycle is a confound to rule out, not assume**. **Phase 5 absorption ratio — HIGHEST OVERLAP RISK:** both
are Herfindahl-type measures, on capital vs eigenvalues, and a top-heavy capital vector inflates PC1 mechanically. **Binding
precondition: a written de-confliction before Phase 5's charter opens, or one of the two drops.**

## Open items — Adam to confirm or override
1. **PROCEED on the respecification, or DROP?** `[recommend PROCEED, level primary]`
2. **Drop the rate descriptor?** `[recommend DROP]` — duplicates `smb`, reads only as a risk premium, not built. If retained it needs
   its own bar: `|corr(smb)| ≥ 0.90` ⇒ drop.
3. **Authorise the fetch?** The kickoff scoped "no new fetch"; this is the same free library the existing builders use, and the
   alternative is measuring the wrong quantity. `[recommend YES]`
4. **V3 first · ledger status NONE · Phase-5 de-confliction binding · the numeric bars?** `[recommend yes to all]`
5. **If R3 fires** — close NOT MEASURABLE, paid constituent data recorded as a costed item, not a phase? `[recommend yes]`

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/04-concentration-signal/04-CHARTER-KICKOFF|04-CHARTER-KICKOFF]]

<!-- LINKS:END -->
