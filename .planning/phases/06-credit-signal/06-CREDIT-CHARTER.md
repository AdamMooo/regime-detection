# Research Charter — Credit / Excess Bond Premium (Phase 6)

# v1.0 — FROZEN. CHARTER SIGNED OFF BY ADAM 2026-08-09.

**The pre-registration below is now BINDING.** Every V bar, R condition, threshold and construction
choice is frozen as written and is not re-tunable after a value has been seen. **No look spent as of
this signature:** framework reading, data-coverage inspection and vintage research only — no value
computed, no hypothesis tested, no statistic anywhere below. Signing freezes the pre-registration
only; it is **not** a positive claim, so no cooling-off applies to *this* signature. The one-look and
its **separate dated RESULTS sign-off** come after, and that one does require cooling-off. Template
v1.1, held to `validation-standards.md` v1.1. (Long-form rationale and the v0.1/v0.2 drafts: git
history of this file.)

## CHARTER SIGN-OFF — Adam, dated 2026-08-09

All four open items ruled. Dispositions, in the charter's own numbering:

| # | Item | Ruling |
|---|---|---|
| 1 | PROCEED or drop | **PROCEED, maturity capped at `research`.** The cap is registered *before* the look and is not reopenable on a strong V2 — the option to "revisit the ceiling if V2 comes back strong" was offered and **rejected**, because a strong V2 is precisely when dropping the cap becomes tempting. |
| 2 | R2 consequence | **DROP, not demotion.** Two of V2's three bars failing kills the signal. Thresholds frozen: **A** RMS revision ÷ full-sample σ ≤ 0.25 · **B** Spearman(vintage, today) ≥ 0.95 · **C** settled months agreeing within ±1 decile ≥ 0.90, **C decisive**. Settled portion = months ≥ 12m before a vintage's last observation. Rationale accepted as drafted: untrustworthy history kills both "how unusual" and "what did comparable environments look like", which is two thirds of the product and fails G4. *Demote-to-live-reading-only was rejected* — it would emit a level with no rarity, the first exception to D-02b in the repo. |
| 3 | Numeric defaults | **All accepted as drafted.** Publication lag = **end of *t*+1** (`PUBLICATION_LAG_MONTHS = 2` on a month-start index) · ledger bands **0.80 / 0.95 on the causal expanding percentile**, never the raw level, because the EBP is a residual whose units are not independently interpretable · **R4** diagnostic threshold \|Spearman\| ≥ 0.90 vs the monthly volatility reading · **120-month burn-in** (NaN before) with a **trailing-60m** fraction-higher second lens. |
| 4 | Vintage archive | **YES to both, and the harvest is DONE** — see the harvest record below. The home-made "PIT EBP" **stays rejected**. |

**Build is authorised.** Next step is the single frozen one-look script (V1–V6 → `results/credit_validation.txt`), then overnight cooling-off, then a separate dated results sign-off.

## Harvest record (2026-08-09, no look spent)

`scripts/harvest_ebp_vintages.py` → **19 distinct vintages, 2022-08-18 .. 2025-12-03**, in
`data/vintages/ebp/` with a checksum manifest regenerated from disk each run. **No cross-vintage
statistic was computed** — revision magnitude, rank correlation and decile agreement *are* V2 bars
A/B/C, and there is no way to unspend a look.

Three things the harvest established, none of them a look:

1. **Schema is identical across all 19** (`date, gz_spread, ebp, est_prob`), confirming this charter's
   claim.
2. **Correction to this charter's V2 wording.** The Data-limits section said publication timing was
   "verified from captures". It is **bounded from above** by captures, not verified: a capture date
   is when the Archive *crawled*, and the Fed may have published days earlier. Across all 19 the data
   arrived **earlier** than the end-of-*t*+1 rule allows, so the registered lag is demonstrably
   **conservative** — but the captures cannot show it is tight, and V2 must not treat capture dates
   as publication dates.
3. **One vintage carries a vendor defect** (2025-06-12: a trailing bare `,,,` row, recorded as
   `dateless_rows=1`). It matters for the one-look because **`build_credit.py:41` calls
   `pd.to_datetime` with no `errors=` guard**, so such a row becomes a NaT-indexed all-NaN row
   *without raising*. The live `credit_monthly.csv` is clean (642 rows, zero NaT) — the guard is
   absent, not satisfied. **The one-look script must reject or explicitly handle dateless rows in
   every vintage it reads.**

## V2 AGGREGATION CLARIFIED — Adam, 2026-08-09, BEFORE any value was computed

The frozen text gave each bar's threshold but not how to aggregate it across the 19 vintages. Both
gaps were closed **before the one-look script existed and before any statistic was computed** — the
same clarification made *after* seeing values would be specification search, so the ordering is the
whole point and is recorded deliberately.

- **Bar B — gate on the MINIMUM Spearman across vintages.** The bar exists to catch *any* vintage
  whose ordering broke; a median would let one catastrophic restatement hide behind eighteen good
  ones. The usual objection to a minimum — most noise-sensitive statistic, one odd vintage fails the
  whole bar — is already answered by **R2 requiring two of three bars to fail**, so a strict single
  bar is safe. Report min, median and the full per-vintage table; gate on min.
- **Bar C — POOLED across all settled (vintage, month) pairs.** The literal reading of "share of
  settled months". It weights each vintage by how much settled history it carries, so later vintages
  count for more, which is the right weighting because more months compared is more evidence.
  **Accepted knowingly: the 2025 vintages will dominate this statistic.**

**Registered expectation about WHERE revisions will fall (a prior, not a bar, recorded pre-look).**
Since the EBP is an OLS residual, the revision has the closed form
`r_v(t) = EBP_v(t) − EBP_today(t) = x_t'(β̂_today − β̂_v)` — proportional to the regressor vector at
`t`. So revisions should concentrate in months with **extreme regressors**, which are the crisis
months this signal exists to describe. Consequence for interpretation: *"revisions are small on
average"* and *"revisions are small where it matters"* are **different claims**, and bar A measures
only the first. If A passes while the largest revisions sit on 2008 and 2020, that is a real finding
and must be reported, not smoothed. No threshold is attached — this is a lens for reading the
result, registered in advance so it cannot be invented afterwards.

**Known gap: the 2026-03-23 capture is not harvested** — the Archive began refusing connections
after ~20 requests, so it is a rate-limit casualty, not an absent capture. Re-run the script to pick
it up. V2 may run on 19 or 20 vintages; the count actually used must be stated in the results.

## Header + Stage-0 gate (PASS, on the EBP residual — NOT on raw spreads)

- **Signal** Credit (excess bond premium) · **clock** monthly, forced by the data · **charter-first status** clean (`build_credit.py` pulls inputs only; no construction preceded this draft).
- **Assumption monitored** — *"credit conditions are benign: the compensation demanded for bearing corporate credit risk beyond expected default is not unusual."* Ledger status {intact | under-test | violated} is an observation, never an instruction, and is never emitted without `reading` + `rarity` beside it (D-02b).
- **Investor question** — *right now, is the corporate-bond market demanding unusual compensation for credit risk beyond expected default, how unusual is that versus history, and what did comparable environments look like?* Plus one honesty field most published uses omit: **how provisional is today's number** (revision band, V2b).
- **Maturity** — DERIVED but **capped at `research`** by two limits registered *before* the look (vintage surface; unmet international bar). `production` is unavailable however the results read.
- **G1/G2** — the price of bearing US corporate credit risk above expected default is the cleanest public read on the risk-bearing capacity of the intermediary sector, the marginal supplier of capital to risky claims; not observable from equity-return dynamics.
- **G3** — raw spreads share the large majority of their variation with the equity-volatility axis (`sensor-orthogonality-evidence`) and are REJECTED as the reading; only the residual is admitted, raw spreads surviving as a data-integrity companion (V5).
- **G4** — nothing else in the set reads credit-risk pricing. Registered caveat: the margin against **Phase 7 (funding stress)** is genuinely uncertain — both rest on intermediary balance sheets. Claimed distinction: short-dated money-market frictions (daily) vs the price of long-dated credit risk (monthly). Re-run leave-one-out across the pair once both exist; neither is pre-designated the survivor.
  - **AMENDED 2026-08-09 (pre-signature, no look).** **Phase 7 was DROPPED 2026-08-06**, so the leave-one-out adjudication registered above **can never run**. Consequence, stated plainly rather than allowed to lapse into a pass: **G4 is now UNOPPOSED, not confirmed.** The one candidate that might have shown this signal to be redundant no longer exists, and its absence is not evidence of distinctness. Anyone later reading a favourable V4 as proof of orthogonality must read this line first — combined with the V4 caveat below (the EBP regresses out a Merton distance-to-default, itself a function of equity volatility, so part of any measured orthogonality is manufactured by construction), the honest position is that this signal's uniqueness is **untested**, not established.
- **G5** — strong prior: Gilchrist–Zakrajšek (2012 *AER*); Favara–Gilchrist–Lewis–Zakrajšek (FEDS Notes 2016); He–Krishnamurthy (2013); Adrian–Etula–Muir (2014); He–Kelly–Manela (2017). Published monthly by the Board.

## Mechanism — why it survives being known

GZ (2012) regress bond-level spreads on a Merton (1974) distance-to-default plus bond characteristics; **the residual is the EBP** — the part of the price of corporate credit that expected losses do not explain. In intermediary asset pricing (He–Krishnamurthy 2013; Adrian–Etula–Muir 2014; He–Kelly–Manela 2017) the marginal bondholder is a levered intermediary whose effective risk aversion is a function of balance-sheet capacity; when capacity contracts, required compensation rises with expected default unchanged (Brunnermeier–Pedersen 2009 for the amplification). **It survives being known because it is a risk premium, not a mispricing:** earning it means supplying the scarce thing — risk-bearing capacity — exactly when supplying it is most punishing. Knowing the number relaxes no one's balance sheet.

**Competing interpretation, on the record:** López-Salido–Stein–Zakrajšek (2017) and Greenwood–Hanson (2013) read credit-market sentiment partly as over-optimism with predictable reversal — a mispricing, which would *not* obviously survive being known. The gate is passed on the risk-premium reading, and it matters less than it would elsewhere because this signal makes no forecast claim: a measurement of the current price of credit risk is valid under either. **The documented ~1–2yr EBP lead over real activity is admitted as ex-ante prior only — never tested, never asserted here.**

## Validation bars (V) / reject conditions (R)

Per the 2026-08-06 objective restatement, reproducing a known relationship point-in-time, causally and honestly **is** the pass condition. Falsification targets the measurement; the signal makes no forward claim so it cannot fail to predict.

| V | bar | R → consequence |
|---|---|---|
| V1 | causal construction + publication lag; `assert_causal(build, panel)` passes under the shared guard. **It tests the CODE and structurally cannot detect vintage leak, which lives in the DATA — that is V2's job** | R1 any look-ahead (full-sample rank, a reading dated before its lag allowed) → fatal, unusable live |
| V2 | **vintage-instability diagnostic — the decisive bar.** ~24 Internet Archive vintages (2022-08→2026-03); settled portion = months ≥12m before a vintage's last obs, so the channel-3 refit effect dominates. **A** RMS revision ÷ full-sample σ ≤ 0.25 · **B** Spearman(vintage, today) ≥ 0.95 · **C** share of settled months agreeing within ±1 decile of the causal expanding percentile ≥ 0.90 (**C is the one that matters** — the output is a rarity, and levels can restate while ordering survives). All pass → V2 passes with the vintage caveat attached; one fails → passes with a permanently disclosed defect; two fail → R2 | R2 **DROP recommendation, not a caveat** — untrustworthy history kills "how unusual" and "what did comparable environments look like", two thirds of the product, failing G4 |
| V2b | live revision band on the newest 1–3 months, **published as part of the reading** — a presentation requirement, not pass/fail, so a provisional number is never shown as settled | — |
| V3 | rarity calibration non-degenerate; burn-in NaN rather than a percentile of a handful of points; the two lenses do not contradict misleadingly | R3 rarity misleads → fix or demote |
| V4 | distinctness from the volatility axis — **DIAGNOSTIC, not a gate** (§(b): mechanism governs, statistics diagnose); crisis co-movement is expected and disclosed. **Caveat that must travel with any favourable result: the EBP regresses out a Merton DD, itself a function of equity volatility, so part of any measured orthogonality is manufactured by construction, not discovered in the market** | R4 \|Spearman\| ≥ 0.90 vs the monthly volatility reading → demote; the mechanism gate is failing in practice |
| V5 | PIT-clean companion check: `gz_spread` tracks unrevised Baa−10y (1986+) and Moody's Baa−Aaa (1919+) at major credit episodes. Plumbing verification only; the companion is **not** the signal | R5 no tracking → broken/mis-parsed input → fix or halt (a data failure, not a finding) |
| V6 | sub-period stability 1973–1998 vs 1999–2026, registered as a **degraded substitute** for the international bar (a temporal split would not have caught the sector-dispersion artifact that Japan and Europe killed) | R6 qualitative divergence → disclose and demote; a real structural change in the corporate bond market is not a measurement defect, and separating the two needs a second look |
| V7 | out-of-hypothesis-sample Japan/Europe — **UNMET BY CONSTRUCTION** (below), recorded as a documented failure under §(d) | R7 evidence maturity cannot score `H`; maturity capped at `research`. Registered now because a strong US result is exactly when it gets tempting to drop |

**Ledger bands**, pre-committed on the *causal expanding percentile* (the raw EBP is a model residual whose units are not independently interpretable): ≤0.80 `intact` · 0.80–0.95 `under_test` · >0.95 `violated`.

## What it explicitly does NOT claim (per-signal boundary)

It reports the level, its rarity against its own history, the descriptive character of comparable environments and a revision band, names the assumption, and **STOPS**. The forbidden vocabulary appears here **only to prohibit it**: this signal does NOT forecast recessions, credit events, defaults, drawdowns or returns at any horizon; is NOT a timing signal, trigger or switch; never enters a composite or a single market-safety number; and never states or implies a **portfolio**, **allocation**, **exposure**, **weight**, **tilt**, **sleeve**, **position sizing**, **risk budget**, **overweight**, **underweight**, **cash call**, **buy**, **sell** or **risk-on / risk-off** conclusion. A `violated` status observes that the price of bearing credit risk is historically unusual — nothing more. What follows from it is the human's judgment, in a separate system.

## Vintage / point-in-time — the phase's defining constraint

The first admitted signal with a vintage surface at all (the others are built from returns). The Board states that **"the entire history of the EBP may revise each month"** (FEDS Notes 2016-10-06). Three channels: balance-sheet restatement and bond-panel composition (both "modest, concentrated in recent months" per the Board), plus the one the Board does not name and that matters most — **full-sample re-estimation of the predicted-spread regression**: the EBP is a residual, so a monthly refit moves *every* historical value, and the number printed today for March 2008 embeds coefficients estimated through 2026.

**Achievable:** release timing (verified from captures — month *t* publishes during *t*+1; **registered rule: unavailable until the end of *t*+1**, enforced in `build()`); forward vintage capture from now at zero cost; and *measuring* restatement on the 2022-08→2026-03 archive. **Not achievable:** no ALFRED vintages (the EBP is a FEDS-Notes CSV, not a FRED series — zero search matches), and no pre-2022 PIT reconstruction without paid bond-level and balance-sheet data. **Registered consequence: whatever V2 returns, the pre-2022-08 history remains final-revision data** — bounded contamination is still contamination, hence the `research` cap. Path to `production`, both outside this phase: accumulate ~a decade of forward vintages, or buy the inputs and refit expanding. **REJECTED alternative:** a home-made "PIT EBP" regressing free Baa−10y on causally-available default proxies — the only free proxies are volatility-derived, so the residual would be *mechanically* orthogonalised against the volatility signal, manufacturing the very independence V4 exists to test, and it would not be the literature's EBP, forfeiting the G5 prior. Precedent this section is written against: Orphanides (2001); Croushore–Stark (2001); Diebold–Rudebusch (1991).

**International bar unmet, with evidence:** the EBP is US-only; regional replications are one-off academic exercises, not maintained series (euro area Gilchrist–Mojon *EJ* 2018; Canada BoC SAN 2018-4; Japan BoJ working papers); self-construction abroad needs the same paywalled inputs plus, in Japan, a thin bank-intermediated bond panel; and even a degraded raw-spread substitute is blocked by the same FRED/ICE licence truncation.

## Data limits — verified against the files, 2026-08-06

- **`credit_monthly.csv` is clean:** 642 rows, 1973-01-01→2026-06-01 month-start, cols `date, gz_spread, ebp, est_prob`, **zero** missing, no gaps, sample start stable across every archived vintage checked. `est_prob` is **excluded entirely** — an explicit recession forecast has no place in this repo.
- **`credit_daily.csv`: the kickoff's "OAS proxies 1986+" is WRONG for two of three columns.** Per-column spans (MANIFEST): `baa_10y` 1986-01-02+ (10,147 obs), `ig_oas`/`hy_oas` **2023-08-07+ only** — FRED serves a rolling ~3-year window of ICE BofA data under licence. So V5's long-history unrevised companion is `baa_10y` plus Moody's monthly `BAA`/`AAA` (1919+); the OAS columns are a 3-year contemporary cross-check, never history.
- Vintage archive: **HARVESTED 2026-08-09 — 19 distinct vintages, 2022-08-18 .. 2025-12-03**, schema-identical (verified, all 19), irregular cadence, committed to `data/vintages/ebp/` with per-file sha256. The pre-look estimate of "~24 usable captures" resolved to 22 successful captures carrying 20 distinct contents, of which 19 are on disk. See the Harvest record at the top of this charter, including the correction that capture dates bound publication **from above only**.

## Construction spec (FROZEN 2026-08-09) + open items — ALL FOUR RESOLVED, see the sign-off table above

`scripts/credit_ebp.py::build(panel)` on the shared causal spine; input `credit_monthly.csv` col `ebp`; publication lag enforced in code; rarity = `causal.expanding_percentile`, 120-month burn-in (NaN before) with a trailing-60m fraction-higher second lens; `causal.expanding_z` companion; **vintage stamped in code** (sha256 of source + build date → `results/credit_vintage.json`) so any later result ties to the vintage it used; one look = V1–V6 in a single frozen script → `results/credit_validation.txt`; Level-0 output schema-validated, `clock = monthly`.

1. **PROCEED?** *Recommend PROCEED.* The best available outcome is a US-only `research`-tagged instrument; the caps are the honest result, not a failure, and a causal, lagged, vintage-documented reading of a series almost universally used at final revision is exactly this repo's work.
2. **V2 thresholds** A ≤0.25 / B ≥0.95 / C ≥0.90, 12-month settled portion, two-of-three fires R2. **R2 consequence = DROP** rather than demotion to a live-reading-only signal (*recommend DROP*).
3. **Publication lag** = end of *t*+1 (*recommend confirm* — conservative vs the ~5–7 weeks verified in the captures). **Bands on the percentile** 0.80 / 0.95 rather than the raw level. **R4 threshold** \|Spearman\| ≥ 0.90. **120-month burn-in / 60-month second lens.**
4. **Start the forward vintage archive now** on every `build_credit.py` run, independent of this phase's outcome, and **harvest the ~24 Internet Archive vintages** as V2's evidence base (*recommend YES to both* — zero cost, and Archive coverage is not guaranteed to persist). **The home-made "PIT EBP" stays rejected.**

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/06-credit-signal/06-CHARTER-KICKOFF|06-CHARTER-KICKOFF]]

<!-- LINKS:END -->
