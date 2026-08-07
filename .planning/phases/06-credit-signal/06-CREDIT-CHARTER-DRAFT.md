# Research Charter — Credit / Excess Bond Premium Signal (Phase 6)

# DRAFT — NOT FROZEN, NOT SIGNED

**Status: DRAFT.** Nothing here is pre-registered yet. This document becomes a Stage-1 freeze only when Adam
signs and dates it. No look has been spent: the work behind this draft is (a) reading the governing framework,
(b) inspecting data **coverage** — dates, row counts, missingness, columns, series metadata — and (c) researching
data-vintage availability. **No value of the signal has been computed, no hypothesis tested, and no statistic
about whether the signal works appears anywhere below.**

Filled against framework template **v1.1** (`research-charter-template.md`), held to `validation-standards.md` v1.1.

---

## Executive summary (read before the detail)

- **Stage-0 verdict: PROCEED**, with two limitations registered *before* the look, not discovered after.
- **The vintage problem is partially solvable, and it caps this signal at maturity `research`.** The Fed states
  that "the entire history of the EBP may revise each month." No ALFRED vintage archive exists (EBP is not a FRED
  series). A usable but sparse vintage archive **does** exist — ~24 Internet Archive captures of the Board's CSV,
  2022-08-18 to 2026-03-23, each a complete 1973-onward history. That is enough to **measure** restatement
  magnitude and to present the live reading with an honest revision band. It is **not** enough to reconstruct a
  point-in-time series before 2022-08.
- **International replication is not feasible on free data**, and is registered up front as a documented unmet
  bar rather than a later surprise.
- Consequently the phase's honest deliverable is a **US-only, `research`-tagged measurement instrument** with a
  named path to `production` that this phase cannot walk.

---

## Stage-0 Relevance Gate (default = NO)

The gate is cheap pre-research triage. Answers carried forward from `06-CHARTER-KICKOFF.md` (2026-08-05),
sharpened here and with one framing corrected.

- **G1 — what important investment question does this signal answer?**
  *What is the current price of bearing US corporate credit risk over and above the compensation warranted by
  expected default, how unusual is that price versus its own history, and which historical environments looked
  like this one?* Plainly: is the corporate-credit market currently demanding unusual compensation for reasons
  other than expected losses.

- **G2 — why is that question important to long-term investors?**
  The excess bond premium is the cleanest available public read on the **effective risk-bearing capacity of the
  financial intermediary sector** — the marginal supplier of capital to risky claims. When that capacity is
  scarce, the price of every risky claim is set by a more constrained marginal investor, and credit supply to
  the real economy contracts. That is a first-order description of the environment a long-horizon investor is
  operating in, and it is not observable from equity-return dynamics.
  **Framing correction vs. the kickoff:** the kickoff justified G2 by the EBP's documented ~1–2 year lead over
  subsequent market and real-activity deterioration. That lead (López-Salido–Stein–Zakrajšek 2017) is admitted
  here **only as ex-ante prior (G5)**, never as a claim this signal makes or tests. This repo is a measurement
  system; see Q6.

- **G3 — information not already available from the existing signals?**
  Yes, and specifically the **residual only**. Raw credit spreads share the large majority of their variation
  with the equity-volatility axis (`sensor-orthogonality-evidence`) and would be redundant with the shipped
  volatility signal. The EBP — the spread purged of the modelled expected-default component — is the thin part
  that is *about intermediary risk-bearing capacity rather than about realized instability*. Raw spreads are
  therefore **not** the signal and are carried only as a data-integrity companion (V5).

- **G4 — leave-one-out: would removing this signal make the observatory meaningfully less informative?**
  Yes. Without it the observatory has no read on credit-market risk pricing at all — the assumption "credit
  conditions are benign; the price of bearing corporate credit risk is not unusually elevated" would be
  unmonitored, and neither the volatility axis nor the stock-bond correlation axis speaks to it.
  **Caveat registered now:** the leave-one-out margin against **Phase 7 (funding stress)** is genuinely
  uncertain, because both rest on intermediary balance-sheet mechanisms. See *Cross-signal relationships*.

- **G5 — strong theoretical/empirical prior before weeks of research?**
  Strong. Gilchrist & Zakrajšek (2012, *AER*); Favara–Gilchrist–Lewis–Zakrajšek (FEDS Notes 2016, and the monthly
  update series); López-Salido–Stein–Zakrajšek (2017, *QJE*); the intermediary-asset-pricing literature
  (He–Krishnamurthy 2013; Adrian–Etula–Muir 2014; He–Kelly–Manela 2017). The measure is maintained and published
  monthly by the Federal Reserve Board.

**Gate verdict: PASS** — on the EBP residual, not on raw spreads.

---

## Header

- **Signal name** — Credit (excess bond premium)
- **Assumption monitored** — **"credit conditions are benign — the compensation demanded for bearing corporate
  credit risk beyond expected default is not unusual."** This signal carries a ledger status
  {intact | under-test | violated}. The status is an observation about the market and never an instruction.
- **Native clock / frequency** — **monthly.** Forced by the data: the EBP is published monthly, dated to
  month-start, with a publication lag. Monthly is also the honest frequency of a slow intermediary-capacity
  quantity.
- **Maturity tag** — DERIVED, not hand-set. **Given the vintage limitation and the unmet international bar
  registered below, `research` is the ceiling this phase can earn.** `production` is not available and must not
  be claimed, however the results read.
- **Investor question (production bar)** — *"Right now, is the corporate-bond market demanding unusual
  compensation for bearing credit risk beyond expected default, how unusual is that versus history, and what did
  comparable environments look like?"* Clearly answerable — but the production bar also requires evidence
  maturity this phase cannot reach.
- **Charter/spec version** — v0.1 (DRAFT; becomes v1.0 on sign-off)
- **Charter dated** — **UNDATED / UNSIGNED.**

**Charter-first status.** Clean. `scripts/build_credit.py` pulls inputs only; **no `build()` exists, nothing has
been computed, no look spent.** This is the first phase in the repo to reach its charter with no prior
construction to disclose.

---

## The six charter questions

### 1. What question does the signal answer?

Three descriptive questions about the current environment, in the shape the shipped volatility signal uses
(reading → rarity → historical context), then STOP:

1. **What is the level?** — the current excess bond premium in percentage points, as published, read under a
   registered publication-lag rule so that the value is one a reader could actually have had on the date it is
   attributed to.
2. **How unusual is it?** — a **causal expanding-window percentile** against the signal's own history, plus the
   trailing-5-year fraction of months that ran higher. Reported with the vintage caveat attached (see the
   VINTAGE section — the pre-2022 history is final-revision data).
3. **What did comparable environments look like?** — descriptive historical context for months in the same
   rarity band: how long such environments persisted, and what the other admitted signals were reading at the
   same time. **Descriptive co-occurrence only, never a forward statement.**

Plus one honesty field that most published uses of this series omit:

4. **How provisional is today's reading?** — an explicit **revision band** on the most recent months, estimated
   from the archived vintages (V2b). The EBP's newest values are the ones most subject to restatement; a reader
   is entitled to know that the latest point may move.

### 2. What market assumption does it monitor?

**"Credit conditions are benign — the compensation demanded for bearing corporate credit risk beyond expected
default is not unusual."**

Ledger mapping, to be pre-committed **before** the look and not re-tunable afterwards. The bands are defined on
the **causal expanding percentile**, not on a raw level, because the EBP's raw scale is a model residual whose
units are not independently interpretable:

| expanding percentile of EBP | status | reading |
|---|---|---|
| ≤ 0.80 | `intact` | compensation demanded is within its historical norm |
| 0.80 – 0.95 | `under_test` | elevated relative to history |
| > 0.95 | `violated` | historically unusual compensation demanded |

**Continuous-first (D-02b applies).** The percentile and the level are the reading; the status is a **derived
label that may never be emitted, presented, or stored without the underlying number and its rarity beside it.**
Enforced in the Level-0 record: no status without `reading` and `rarity`.

[recommended — Adam to confirm/override] the 0.80 / 0.95 cut points, and the choice of percentile rather than a
raw level for the banding.

### 3. What mechanism supports it — why does it survive being known?

**Registered mechanism: risk-premium channel via intermediary risk-bearing capacity. Secondarily, a
risk-management channel (the EBP conditions how the other readings should be interpreted).**

**The decomposition.** Gilchrist & Zakrajšek (2012) build a credit-spread index from secondary-market prices of
senior unsecured bonds of a large panel of US non-financial firms, then regress bond-level spreads on a
firm-level measure of expected default — a Merton (1974) distance-to-default — plus bond characteristics. The
fitted part is the compensation warranted by expected default; **the residual, averaged across the panel, is the
excess bond premium.** It is, by construction, the part of the price of corporate credit that expected losses do
not explain.

**Why that residual is economically meaningful.** In intermediary asset pricing (He–Krishnamurthy 2013;
Adrian–Etula–Muir 2014; He–Kelly–Manela 2017), the marginal investor in corporate bonds is a levered financial
intermediary, not a representative household. The effective risk aversion of that marginal investor is a
function of its net worth and balance-sheet capacity. When capacity contracts, the required compensation for
bearing credit risk rises even with expected default unchanged, and credit supply to firms tightens
(Brunnermeier–Pedersen 2009 for the funding-liquidity spiral that amplifies this). The EBP is a price-based
observable of exactly that state variable.

**Why it survives being known.** It is a risk premium, not a mispricing. To earn the elevated compensation an
investor must **supply the scarce thing — risk-bearing capacity — precisely when supplying it is most painful
and most likely to be punished.** That is a genuine risk, borne in the states where it hurts, and public
knowledge of the premium's existence does not remove the constraint that creates it. Nothing about knowing the
number relaxes intermediary balance sheets. This is the same structural argument that makes the equity risk
premium survive being known.

**The competing interpretation, registered honestly.** López-Salido–Stein–Zakrajšek (2017) and
Greenwood–Hanson (2013) read elevated/compressed credit-market sentiment partly as **over-optimism followed by
predictable reversal** — a behavioural mispricing story. A mispricing does *not* obviously survive being known.
Two points:
- The mechanism gate here is passed on the **risk-premium / intermediary-capacity** reading, not on the
  sentiment reading. If only the sentiment reading were true, the gate would be weaker.
- It matters less than it would elsewhere, because **this signal makes no forecast claim.** A measurement of the
  current price of credit risk remains a valid measurement under either interpretation; only a *forecasting*
  claim would be exposed to being arbitraged away. See Q6.

Gated by `validation-standards.md` §(b) — passed, with the competing-interpretation caveat on the record.

### 4. What evidence would validate it?

Validation here is **measurement correctness and measurement trustworthiness**, not forecastability — per the
2026-08-06 objective restatement, reproducing a known relationship point-in-time, causally, and honestly *is*
the pass condition. Each bar is paired with a reject condition in Q5.

- **V1 — causal construction + release-lag discipline.** `build()` uses only data through *t*: expanding-window
  percentile (never a full-sample rank), trailing-window context, and a **registered publication-lag rule** —
  the value dated month *t* is treated as unavailable until the **end of month *t*+1**. `assert_causal(build,
  data)` passes and the module is registered under the guard in `tests/test_reproducibility.py`.
  **Stated explicitly:** `assert_causal` tests the *code* for look-ahead. It **cannot** detect vintage leak,
  because that leak is in the data. V2 is the bar that addresses it.
- **V2 — vintage-instability diagnostic (the decisive bar for this signal).** Using the archived vintages
  (2022-08 → 2026-03), quantify how much the *settled* history restates. Definitions and thresholds are
  pre-committed in the VINTAGE section below. Passing means the historical-context statistics can be trusted;
  failing means they cannot, and R2 fires.
- **V2b — live-reading revision band.** Measure how much the most recently published 1–3 months move between
  consecutive vintages, and **publish that band as part of the reading.** Not a pass/fail bar — a presentation
  requirement. Its purpose is that a reader is never shown a provisional number as if it were settled.
- **V3 — rarity calibration is well-behaved.** The causal expanding percentile is non-degenerate and not
  dominated by the early sample; the two rarity lenses (expanding-history percentile and trailing-5-year
  fraction-higher) do not contradict each other in a way that would mislead. Burn-in is reported as NaN, not as
  a percentile of a handful of observations.
- **V4 — distinctness from the volatility axis (DIAGNOSTIC, not a gate).** Report the co-movement between the
  monthly EBP reading and the monthly-aggregated volatility reading, over the common sample and separately
  within crisis and non-crisis months. **Registered interpretation rule, fixed before the look:** high
  co-movement is **disclosed, not disqualifying** — §(b) says the mechanism governs and statistics diagnose.
  Only near-identity trips R4.
  **Registered caveat:** the EBP's construction regresses out a Merton distance-to-default, which is itself a
  function of equity volatility. **Any measured orthogonality to the volatility signal is therefore partly by
  construction, not purely an economic fact.** This must be stated in the signal's limitations, not quietly
  enjoyed as a favourable result.
- **V5 — PIT-clean companion cross-check (data integrity).** The GZ credit-spread index (`gz_spread`, the
  pre-residual leg) is checked against the **unrevised, market-priced** Moody's Baa−10y series (`baa_10y`,
  1986-01-02 onward, daily, with ALFRED vintages available from 2014 as independent proof of non-revision), and
  against Moody's Baa−Aaa monthly (FRED `BAA`/`AAA`, 1919 onward). Bar: the two track each other at the level of
  major credit episodes. This is **plumbing verification** — it confirms the pulled file is the series it claims
  to be and that restatement has not distorted the raw leg beyond recognition. It is not a hypothesis test and
  the companion is **not** the signal (raw spreads were rejected at G3 as redundant).
- **V6 — sub-period stability.** The descriptive properties (rarity calibration, band occupancy, persistence of
  environments) behave sensibly in **1973–1998** and **1999–2026** separately. Registered as a *degraded
  substitute* for the international bar, and explicitly labelled as such — a temporal split does not catch
  region-specific artifacts, which is precisely how the sector-dispersion lead survived until Japan and Europe
  killed it.
- **V7 — out-of-hypothesis-sample (Japan / Europe).** **Registered as UNMET BY CONSTRUCTION.** Evidence and
  consequence in the *Out-of-hypothesis-sample plan* section. Recorded as a documented failure per §(d), not
  quietly omitted.

### 5. What would falsify it?

Declared before any look. Falsification targets the **measurement and its trustworthiness**, never a missed
forecast — this signal makes no forward claim, so it cannot fail to predict.

- **R1 — look-ahead in the code.** Any descriptor found to use data beyond *t*: full-sample rank, a percentile
  computed over the whole history, or a reading attributed to a date before its publication lag allowed. Fatal;
  the reading would be unusable live. (Trips V1.)
- **R2 — vintage instability above the registered threshold.** The settled portion of the history restates by
  more than the pre-committed bound. **Consequence, registered now so it cannot be softened later: the
  historical-context and rarity outputs are not trustworthy, and since "how unusual is it / what did comparable
  environments look like" is most of this signal's content, a bare uncontextualised level fails the G4
  leave-one-out bar. R2 firing is a DROP recommendation, not a caveat.** (Trips V2.)
- **R3 — rarity read misleads.** The expanding percentile is degenerate or unstable, or the two rarity lenses
  contradict each other in a way that would mislead rather than inform a reader. (Trips V3.)
- **R4 — the signal is a relabelling of the volatility axis.** Near-identity with the monthly volatility reading
  (|Spearman| ≥ 0.90 over the common sample) — the residual would be carrying no distinct information despite the
  mechanism story. **Demote**, and record that the mechanism gate is failing in practice.
  [recommended — Adam to confirm/override] the 0.90 threshold.
- **R5 — the pulled series is not what it claims.** The `gz_spread` leg does not track the unrevised Baa−10y /
  Baa−Aaa companions at major credit episodes, indicating a broken or mis-parsed input. **Fix or halt** — this is
  a data-integrity failure, not a finding about the market. (Trips V5.)
- **R6 — sub-period instability.** The descriptive properties differ qualitatively between 1973–1998 and
  1999–2026 in a way that indicates the construction is period-specific. **Disclose and demote**; not an
  automatic kill, because a genuine structural change in the corporate bond market (the growth of the HY market,
  the post-1999 issuance regime) is a real feature of the world rather than a measurement defect — and
  distinguishing the two would require a second look, which is not available.
- **R7 — no international confirmation.** Already known to be unmet (V7). Registered consequence: evidence
  maturity cannot be scored `H`; maturity cannot exceed `research`. **This is a cap that is registered before
  the look precisely because a strong US result is exactly when it becomes tempting to drop it** (the same
  reasoning that produced D-02c in Phase 2).

### 6. What does it explicitly NOT claim?

This signal reports the current excess bond premium, its rarity against its own history, the descriptive
character of comparable historical environments, and an honest revision band on the newest values. It names the
assumption *"credit conditions are benign"* and **STOPS**.

Explicit prohibitions — this paragraph is the per-signal boundary statement, and the forbidden vocabulary
appears here **only in order to prohibit it**: this signal does **NOT** forecast recessions, credit events,
defaults, drawdowns, or returns at any horizon; it does **NOT** claim the documented 1–2 year lead of the EBP
over real activity, which is admitted as ex-ante prior only and is never tested or asserted here; it is **NOT** a
timing signal, trigger, or switch; it is **NOT** a single market-safety number and never enters a composite; and
it never states or implies a **portfolio**, **allocation**, **exposure**, **weight**, **tilt**, **sleeve**,
**position sizing**, **risk budget**, **overweight**, **underweight**, **cash call**, **buy**, **sell**, or
**risk-on / risk-off** conclusion. A `violated` ledger status is an observation that the price of bearing credit
risk is historically unusual — nothing more. What that means, and what if anything follows from it, is the
human's judgment in a separate system.

---

## VINTAGE / POINT-IN-TIME — the central issue of this charter

Every signal admitted to this repo so far was built from asset returns and had **no vintage surface at all**;
each said so explicitly per §(a). **This one has a vintage surface, and it is the reason this phase needs
careful pre-registration.**

### What is restated, and by what mechanism

The Federal Reserve Board states it plainly in *Updating the Recession Risk and the Excess Bond Premium* (FEDS
Notes, 2016-10-06):

> "Going forward, users of the EBP data should take note that **the entire history of the EBP may revise each
> month.**"

Three distinct restatement channels, of which the Board names two:

1. **Balance-sheet revision and intra-quarter interpolation.** Firms restate historical balance-sheet data.
   Because the EBP is published monthly but balance-sheet inputs arrive quarterly, the Board holds balance-sheet
   data constant while updating bond and equity prices, then revises once the quarter's data lands. Effect:
   concentrated in recent months.
2. **Bond-panel composition.** Bonds retire, refinance, or are newly issued, changing the panel and the
   bond-to-firm matching. The Board says these revisions "tend to be modest and concentrated in the most-recent
   months."
3. **Full-sample re-estimation of the predicted-spread regression** — *not named in the Board's revision
   discussion, and the one that matters most here.* The EBP is a **regression residual**. If the coefficients of
   the predicted-spread regression are refit over the full sample each month, then the residual at *every*
   historical date changes whenever new observations arrive. **This is why the Board's warning is about the
   entire history rather than just recent months, and it is a genuine in-sample-fit look-ahead: the EBP printed
   today for March 2008 embeds coefficients estimated using data through 2026.**

Channel 3 is the one an `assert_causal` guard is structurally incapable of catching. The code is causal; the
data is not.

### What point-in-time discipline IS achievable here

- **Release timing: fully achievable.** Empirically verified from archived captures — the 2026-03-23 capture
  ends at 2026-02-01; the 2025-03-08 capture ends at 2025-02-01; the 2022-08-18 capture ends at 2022-07-01. Month
  *t* is published during month *t*+1. **Registered rule: the value dated month *t* is treated as unavailable
  until the end of month *t*+1.** Conservative, verified, and enforceable in `build()`.
- **Forward-going vintage capture: fully achievable, starting now, at zero cost.** `build_credit.py` already
  fetches the CSV; writing each fetch to `data/vintages/ebp/<fetch-date>.csv` creates a genuine point-in-time
  archive from 2026-08 onward. This is the only path to a strictly-PIT EBP history, and it takes about ten years
  to become useful. **It should be started regardless of what this phase concludes.**
- **Measuring the restatement: achievable, on a 2022-08 → 2026-03 window.** See below.

### What is NOT achievable

- **ALFRED vintages do not exist for this series.** Verified: a FRED `series/search` for "excess bond premium"
  returns **zero** matches. The EBP is a Board FEDS-Notes CSV, not a FRED series, so it is outside the ALFRED
  vintage archive entirely. There is no vintage API for it.
- **A monthly point-in-time EBP series before 2022-08 cannot be reconstructed from free data.** Independent
  reconstruction requires bond-level secondary-market prices (Mergent FISD / ICE), quarterly firm balance sheets
  (Compustat), and equity data for the Merton distance-to-default — all paywalled. Purchasing them is a separate
  decision, out of scope for this phase.

### What IS obtainable — the Internet Archive vintage set

Verified via the Wayback CDX API against
`https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv`:

- **~24 distinct successful (HTTP 200, unique-digest) captures**, earliest **2022-08-18**, latest **2026-03-23**;
  55 CDX rows total including redirects and duplicates.
- Capture cadence is **irregular** — roughly every one to three months, with gaps (e.g. none between 2022-10 and
  2023-02, none between 2025-07 and 2025-12).
- **Each capture is a complete history**, schema-identical to today's file (`date,gz_spread,ebp,est_prob`), and
  each starts at **1973-01-01** — the sample start has been stable across all captures.
- Six captures were fetched and their headers/row counts verified during this draft. Row counts increment
  consistently with elapsed months (596 → 639 lines from 2022-08 to 2026-03 vs 643 today).

This is **not** a point-in-time series. It is a set of ~24 snapshots of a restated series, which is exactly what
is needed to answer the question *how badly does it restate?*

### V2 — the pre-committed vintage-instability test

Run inside the single frozen one-look script. Let `E_now(t)` be today's published value for month *t*, and
`E_v(t)` the value in archived vintage *v*.

Define the **settled portion** of vintage *v* as all months *t* at least **12 months** before *v*'s last
observation — deliberately excluding the recent months the Board says carry most of channel-1 and channel-2
revision, so that what is measured is predominantly the channel-3 full-sample-refit effect.

Three statistics, over the settled portion, pooled across vintages:

| # | statistic | pass bar |
|---|---|---|
| **A** | RMS revision `E_now(t) − E_v(t)`, divided by the full-sample standard deviation of EBP | **≤ 0.25** |
| **B** | Spearman rank correlation between `E_v(·)` and `E_now(·)` over the settled portion | **≥ 0.95** |
| **C** | share of settled months whose **decile** of the causal expanding percentile agrees within ±1 decile | **≥ 0.90** |

**Decision rule, fixed before the look:** all three pass → V2 passes, historical context is presented with the
vintage caveat attached. Exactly one fails → V2 passes **with a disclosed defect** carried permanently in the
signal's limitations. Two or more fail → **R2 fires → DROP recommendation** (see R2).

Statistic **C** is the one that actually matters for the product, because the output is a **rarity percentile**,
not a raw level. A series can restate materially in levels while leaving the ordering — and therefore the "how
unusual is this" answer — intact. Registering all three, with C treated as equally decisive, prevents choosing
the flattering one afterwards.

[recommended — Adam to confirm/override] all three thresholds, the 12-month settled-portion definition, and the
two-of-three decision rule.

### Registered consequence

**Whatever V2 returns, the pre-2022-08 history remains final-revision data.** Restatement that is *small* is
still restatement, and a small measured revision does not convert the historical series into a point-in-time
one — it only establishes that the contamination is bounded.

Therefore, registered before the look and not revisable after it:

- **Maturity is capped at `research`.** `production` requires point-in-time discipline under §(a), which this
  signal cannot satisfy for the bulk of its sample.
- **Every presented historical-context statistic carries the vintage caveat**, in the output itself and not only
  in documentation.
- **The named path to `production`** — for the record, so the cap is a fact rather than a mood: either (i)
  accumulate roughly a decade of forward vintages from the archive started in this phase, or (ii) purchase
  bond-level and balance-sheet data and reconstruct the EBP with expanding-window estimation. Both are separate
  decisions outside this phase.

### One alternative considered and REJECTED

**Building a home-made "point-in-time EBP"** by regressing a free, unrevised spread (Baa−10y) on causally
available default proxies with an expanding-window fit. Rejected for two reasons: (i) the only free default
proxies available at that frequency are volatility-derived, so the residual would be **mechanically
orthogonalised against the volatility signal** — a circularity that would manufacture the very independence V4
is supposed to test; and (ii) it would be an invented indicator, not the literature's EBP, and would forfeit the
G5 prior that justified opening this charter at all. Recorded here so it is not re-proposed later as a clever
fix. [recommended — Adam to confirm/override]

---

## Data readiness — verified against the actual files

Checked against `data/processed/MANIFEST.csv` and the files themselves on 2026-08-06.

**`credit_monthly.csv` — the signal input. Clean.**

| property | verified value |
|---|---|
| rows | 642 observations (643 lines incl. header) |
| span | 1973-01-01 → 2026-06-01, month-start dated |
| columns | `date`, `gz_spread`, `ebp`, `est_prob` |
| missing values | **zero**, in every column |
| gaps | none — consecutive date steps are 28/29/30/31 days only |
| sample start | stable at 1973-01 across every archived vintage checked |
| sha256 | `7daa29a7…5c15f87` (MANIFEST) |

**`credit_daily.csv` — the companion proxies. The kickoff's coverage claim is WRONG.**

The kickoff records "OAS proxies 1986+". That is true of the file's **index**, not of its columns:

| column | first valid | last | n | interior NaN |
|---|---|---|---|---|
| `baa_10y` | **1986-01-02** | 2026-08-04 | 10,147 | 39 (max gap 5 days, 2001-12-26 — holidays/no-quote days) |
| `ig_oas` | **2023-08-07** | 2026-08-04 | 785 | 1 |
| `hy_oas` | **2023-08-07** | 2026-08-04 | 786 | 0 |

**Cause, verified from FRED series metadata:** every ICE BofA series checked reports
`observation_start = 2023-08-07` — `BAMLC0A0CM`, `BAMLH0A0HYM2`, `BAMLC0A4CBBB`, `BAMLH0A0HYM2EY`,
`BAMLHE00EHYIOAS` (euro HY), `BAMLEMHBHYCRPIOAS` (EM). FRED serves only a **rolling ~3-year window** of ICE BofA
index data, governed by its licence with ICE Data. The full history has not been "lost" in the pull; it is not
available from FRED at all.

**Consequences, registered:**
- The **long-history, unrevised companion for V5 is `baa_10y` (1986+)**, supplemented by Moody's monthly
  `BAA`/`AAA` (FRED, 1919-01 onward) for the pre-1986 era. The ICE BofA OAS columns are usable only as a
  three-year contemporary cross-check and must not be described as historical coverage.
- `AAA10Y` (1983-01-03+) is available as a second daily companion if an investment-grade-only leg is wanted.
- **MANIFEST caveat worth naming:** the manifest's `first`/`last` columns record the index span, not per-column
  first-valid dates. For a wide file with ragged column starts this is misleading, and it is what propagated the
  "1986+" error into the kickoff. Not fixed here (out of scope — this phase writes one file), but flagged.

**Vintage archive readiness:** ~24 usable Internet Archive captures, 2022-08-18 → 2026-03-23, schema-identical,
irregular cadence, complete histories. Not yet harvested into the repo — see Open Questions.

---

## Cross-signal relationships

Declared per template attribute 4, for interpretation only. **No composite is formed, ever.** Disagreement
between signals is preserved (D-03).

- **vs Volatility (Phase 1.5, `production`, daily).** The most important relationship and the most likely source
  of a false sense of independence. Raw credit spreads share the large majority of their variation with the
  equity-volatility axis; that is exactly why G3 rejected raw spreads. The EBP residual is claimed to be
  distinct on **mechanism** — intermediary risk-bearing capacity versus realized instability of returns — and on
  **clock** (monthly and slow versus daily and fast). Expected honestly: **strong co-movement in crises.** Under
  §(b) that is disclosed and does not disqualify; V4 measures it and only near-identity trips R4.
  **The caveat that must travel with any favourable V4 result:** the EBP is constructed by regressing out a
  Merton distance-to-default, which is a function of equity volatility. Part of any measured orthogonality is
  therefore **manufactured by the construction**, not discovered in the market.

- **vs Stock-bond correlation (Phase 2, `research`, monthly).** Mechanistically distinct: Phase 2 measures the
  nominal-real covariance (which macro shock dominates); Phase 6 measures the price of bearing corporate credit
  risk. Same clock, different objects. A plausible shared driver exists — a large inflation shock can move both
  — and if the readings co-move it should be attributed to that, not treated as confirmation of either.

- **vs Funding stress (Phase 7, not yet chartered).** **The highest redundancy risk in the whole signal set, and
  it is named here rather than discovered later.** Both rest on intermediary balance-sheet mechanisms. The
  claimed distinction: funding stress measures **short-dated money-market frictions** (CP−bill, SOFR−EFFR) at a
  daily-to-weekly clock; the EBP measures the **price of long-dated corporate credit risk** at a monthly clock —
  the cost of *funding the intermediary* versus the price *the intermediary charges for bearing credit risk*.
  Related but not the same quantity, and they decouple: money markets can be calm while corporate credit
  repriced, and the reverse.
  **Registered:** once both exist, the G4 leave-one-out test must be re-run **across the pair**, and if they
  prove to be the same measurement, D-19 requires dropping one. Neither phase may assume it is the survivor.

- **vs Tail (Phase 9) and Crowding (Phase 8).** Both are crisis-sensitive and will co-move with the EBP in
  stress. Assessed when they are chartered; no claim made here.

- **Joint interpretation is deferred to Phase 10** per the 2026-08-06 sequencing ruling and is not pre-empted
  here.

---

## Out-of-hypothesis-sample plan

The standing bar (§(d)) is Japan / Europe replication before any SUPPORT claim. **This charter registers, before
the look, that the standard bar cannot be met for this signal**, with the evidence for that conclusion — rather
than discovering it after a favourable US result.

**Why an international EBP is not obtainable on free data:**

1. **The EBP is a US-only published series.** It exists as a Board FEDS-Notes CSV for the United States. It is
   not on FRED (verified: zero search matches), and there is no international counterpart published by any
   central bank on a maintained monthly basis that this research could find.
2. **Regional EBP replications exist only as one-off academic exercises, not maintained series.** Euro area:
   Gilchrist & Mojon, *"Credit Risk in the Euro Area"*, **Economic Journal** 128(608), 2018, 118–158 — bond-level
   credit-risk indicators for Germany, France, Italy and Spain from 1999, including an excess-premium residual;
   published as a research dataset accompanying a paper, not as an updated public series. Canada: Bank of Canada
   Staff Analytical Note 2018-4 constructs a Canadian EBP. Japan: the GZ decomposition has been applied to
   Japanese corporate bonds in Bank of Japan working papers. **None of these is a downloadable, maintained,
   monthly series a live signal could read.**
3. **Self-construction abroad is harder than in the US**, requiring national bond-level secondary-market price
   panels plus point-in-time balance sheets — paywalled everywhere, and in Japan additionally constrained by a
   small, bank-intermediated corporate bond market whose panel would be thin.
4. **Even a degraded raw-spread substitute is blocked on FRED**, because the euro-area ICE BofA OAS series carry
   the same 2023-08-07 licence truncation as the US ones.

**Registered substitutes — declared as DEGRADED, not as the standard bar:**

- **OOS-1 (temporal split, V6).** 1973–1998 versus 1999–2026. Tests whether the descriptive properties are
  period-specific. **Explicitly weaker than a regional split**: the sector-dispersion lead passed every US test
  and was killed only by Japan (+154d) and Europe (+94d). A temporal split would not have caught it.
- **OOS-2 (conditional, optional).** If a free, long-history euro-area corporate-spread series is obtainable
  from the ECB Data Portal, use it to check the **measurement plumbing** — rarity calibration and crisis
  behaviour of the construction — while stating clearly that this tests the plumbing on a raw spread and **does
  not test the EBP residual hypothesis out of sample.** Not yet verified as available; must not become a
  substitute claim of international confirmation.

**Registered consequence:** V7 is recorded as a **documented unmet bar** under §(d). Evidence maturity cannot be
scored `H`. Maturity is capped at `research`, reinforcing the same cap the vintage limitation already imposes —
two independent reasons, both registered before the look.

---

## Pre-registered analysis specification (to be frozen on sign-off)

- **Construction** — a new `scripts/credit_ebp.py` exposing `build(panel)` on the shared causal spine
  (`causal.py`), registered under the `assert_causal` guard in `tests/test_reproducibility.py` before the look.
- **Input** — `data/processed/credit_monthly.csv`, column `ebp`. `gz_spread` is carried as a V5 diagnostic only
  and is never presented as the reading. `est_prob` (the model-implied recession probability) is **excluded
  entirely** — it is an explicit forecast output and has no place in this repo.
- **Publication lag** — month *t* unavailable until end of month *t*+1. Enforced in `build()`, verified by V1.
- **Rarity** — `causal.expanding_percentile` with a **120-month (10-year) burn-in**, reported NaN before that;
  second lens = trailing-60-month fraction of months higher. [recommended — Adam to confirm/override]
- **Ledger bands** — expanding percentile ≤0.80 / 0.80–0.95 / >0.95, pre-committed, not re-tunable within the
  phase. The status is never emitted without `reading` and `rarity` beside it (D-02b).
- **Vintage harvest** — the ~24 Internet Archive captures fetched once into `data/vintages/ebp/`, with capture
  timestamps preserved in filenames, sha256-recorded in the manifest. Forward captures written on every
  `build_credit.py` run from this phase onward.
- **One look** — V1–V6 plus the V2 vintage diagnostic run **once**, as a single frozen script writing to
  `results/credit_validation.txt`. Positive claims require overnight cooling-off and Adam's explicit dated
  sign-off of the *results*, separate from sign-off of this charter.
- **Level-0 output** — schema-validated against `signal_output_schema.py`. Fields used, all inside the closed
  allowlist: `signal`, `assumption_monitored`, `reading` (level + revision band), `rarity`, `trend`,
  `extreme_conditions`, `cross_signal_relationships`, `clock` = `monthly`, `assessment`, `maturity`,
  `spec_version`.

---

## Open questions for Adam

1. **Proceed at all?** The signal arrives with two independent maturity caps — the vintage limitation and the
   unmet international bar — so the best outcome available is a US-only `research`-tagged instrument.
   *[recommended — Adam to confirm/override] **PROCEED.** The mechanism is strong and mechanistically distinct,
   the data is free and already pulled, and building a causal, publication-lagged, vintage-documented reading of
   a series that is almost universally used at final revision is precisely the kind of measurement work this
   repo exists to do. The caps are the honest result, not a failure.*
2. **V2 thresholds** — statistic A ≤ 0.25, B ≥ 0.95, C ≥ 0.90, 12-month settled portion, two-of-three failures
   fire R2. *[recommended — Adam to confirm/override]*
3. **R2 consequence = DROP** rather than demotion to a live-reading-only signal.
   *[recommended — Adam to confirm/override] **DROP.** A reading with no trustworthy history answers "what is
   it" but not "how unusual is it" or "what did comparable environments look like" — two thirds of the product —
   and fails the G4 leave-one-out bar.*
4. **Publication-lag rule** — month *t* unavailable until end of month *t*+1.
   *[recommended — Adam to confirm/override] confirm; it is conservative relative to the ~5–7 week lag verified
   in the archived captures.*
5. **Start the forward vintage archive now**, on every `build_credit.py` run, independent of this phase's
   outcome. *[recommended — Adam to confirm/override] **YES** — it costs nothing, and it is the only path to a
   strictly point-in-time EBP that does not require purchased data.*
6. **Harvest the ~24 Internet Archive vintages into the repo** as the evidence base for V2.
   *[recommended — Adam to confirm/override] **YES** — they are the entire empirical basis for the decisive bar,
   and Internet Archive coverage is not guaranteed to persist.*
7. **Ledger bands on the percentile (0.80 / 0.95) rather than on the raw level.**
   *[recommended — Adam to confirm/override] percentile — the EBP's raw units are a model residual and are not
   independently interpretable.*
8. **R4 near-identity threshold** |Spearman| ≥ 0.90 versus the monthly volatility reading.
   *[recommended — Adam to confirm/override]*
9. **The rejected home-made "PIT EBP" alternative** — confirm it stays rejected, for the circularity reason
   given, so it is not revived later as a shortcut. *[recommended — Adam to confirm/override]*
10. **Phase 6 / Phase 7 redundancy.** Confirm that the cross-pair leave-one-out test is deferred to when both
    exist, and that neither phase is pre-designated the survivor.
    *[recommended — Adam to confirm/override]*
11. **`est_prob` excluded entirely** from anything this repo reads or presents, being an explicit recession
    forecast. *[recommended — Adam to confirm/override]*

---

## References

- Gilchrist, S. & Zakrajšek, E. (2012). "Credit Spreads and Business Cycle Fluctuations." *American Economic
  Review* 102(4), 1692–1720.
- Favara, G., Gilchrist, S., Lewis, K. F. & Zakrajšek, E. (2016). "Recession Risk and the Excess Bond Premium."
  *FEDS Notes*, 2016-04-08; and "Updating the Recession Risk and the Excess Bond Premium," *FEDS Notes*,
  2016-10-06 (the source of the revision statement quoted above).
- López-Salido, D., Stein, J. C. & Zakrajšek, E. (2017). "Credit-Market Sentiment and the Business Cycle."
  *Quarterly Journal of Economics* 132(3), 1373–1426.
- Greenwood, R. & Hanson, S. G. (2013). "Issuer Quality and Corporate Bond Returns." *Review of Financial
  Studies* 26(6), 1483–1525.
- He, Z. & Krishnamurthy, A. (2013). "Intermediary Asset Pricing." *American Economic Review* 103(2), 732–770.
- Adrian, T., Etula, E. & Muir, T. (2014). "Financial Intermediaries and the Cross-Section of Asset Returns."
  *Journal of Finance* 69(6), 2557–2596.
- He, Z., Kelly, B. & Manela, A. (2017). "Intermediary Asset Pricing: New Evidence from Many Asset Classes."
  *Journal of Financial Economics* 126(1), 1–35.
- Brunnermeier, M. K. & Pedersen, L. H. (2009). "Market Liquidity and Funding Liquidity." *Review of Financial
  Studies* 22(6), 2201–2238.
- Merton, R. C. (1974). "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates." *Journal of
  Finance* 29(2), 449–470.
- Gilchrist, S. & Mojon, B. (2018). "Credit Risk in the Euro Area." *Economic Journal* 128(608), 118–158.
- Gilchrist, S., Wei, B., Yue, V. Z. & Zakrajšek, E. (2021/2025). "The Term Structure of the Excess Bond
  Premium: Measures and Implications." Federal Reserve Bank of Atlanta *Policy Hub*.
- Bank of Canada (2018). "Is the Excess Bond Premium a Leading Indicator of Canadian Economic Activity?" Staff
  Analytical Note 2018-4.
- Orphanides, A. (2001). "Monetary Policy Rules Based on Real-Time Data." *American Economic Review* 91(4),
  964–985. — the canonical demonstration that final-revision data misleads about what was knowable at the time.
- Croushore, D. & Stark, T. (2001). "A Real-Time Data Set for Macroeconomists." *Journal of Econometrics* 105(1),
  111–130. — the standard-literature framing of vintages / real-time data.
- Diebold, F. X. & Rudebusch, G. D. (1991). "Forecasting Output with the Composite Leading Index: A Real-Time
  Analysis." *Journal of the American Statistical Association* 86(415), 603–610. — an indicator whose apparent
  performance collapsed once evaluated on real-time vintages. The precedent this charter is written against.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/06-credit-signal/06-CHARTER-KICKOFF|06-CHARTER-KICKOFF]]

<!-- LINKS:END -->
