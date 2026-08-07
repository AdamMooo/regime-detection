# Research Charter — Stock-Bond Correlation Signal (Phase 2)

**Stage-1 pre-registration.** Frozen before the out-of-hypothesis-sample look. Nothing below may be revised
after the Japan/Germany run; deviations caught during construction are disclosed in-line and dated
(`validation-standards.md` §(e), §(g)).

---

## Header

- **Signal name** — Stock-bond correlation (the inflation / real-rate axis, PC2)
- **Assumption monitored** — **"bonds hedge equity drawdowns."** This signal DOES carry a ledger status
  {intact | under-test | violated} — unlike volatility, which is a context axis. The status is an observation
  about the market, never an instruction.
- **Native clock / frequency** — **monthly.** Registered deliberately: the 2026-08-02 US construction found the
  daily 126d calendar-mean read HID the 2022 flip, and the international bond series exist only monthly. Monthly
  is both the honest frequency of a slow nominal-real covariance and the only one available out-of-sample.
- **Maturity tag** — DERIVED, not to be hand-set. Given the scope limitation registered in Q4, **`research` is
  the ceiling this phase can earn**; `production` is not available and must not be claimed.
- **Investor question** — *"Right now, are bonds behaving as a hedge against equity drawdowns, how unusual is
  that versus history, and how long have similar environments lasted?"*
- **Charter/spec version** — v1.0
- **Charter dated** — 2026-08-06. **SIGNED OFF by Adam 2026-08-06**, both `[recommended]` analysis-spec lines
  confirmed (24-month primary correlation window; equity-down = monthly equity return < 0). Build/run authorised.
  This signs the *pre-registration* only — a Stage-1 freeze, not a positive claim, so no cooling-off applies here.
  Any SUPPORT claim arising from the run still requires one look + overnight cooling-off + a separate dated
  sign-off of the *results*.

**Charter-first status.** Partially inverted and disclosed: the US signal was built 2026-08-02 before this
charter existed. The **international OOS run — the subject of this charter — has NOT been run**, and no
international data has been inspected beyond date coverage and column availability (documented in Q4). The US
construction is treated as the hypothesis-generating sample; Japan/Germany is the out-of-hypothesis sample.

---

## Stage-0 Relevance Gate (PASSED)

1. **Does it monitor an assumption that matters?** Yes — "bonds hedge equity drawdowns" is one of the few
   load-bearing assumptions in a multi-asset world, and it demonstrably failed in 2022.
2. **Is it mechanistically distinct from what exists?** Yes — PC2 (inflation/real-rate), distinct from the vol
   axis (PC1). Statistically it partially overlaps vol; the mechanism gate, not the correlation, governs.
3. **Is it measurable causally and point-in-time?** Yes — built from asset returns only, no macro vintage surface.
4. **Marginal information (leave-one-out)?** Yes — the orthogonality research identified it as the single most
   defensible second axis after volatility (`sensor-orthogonality-evidence`).
5. **Can it be maintained?** Yes — returns-only, three regions, no paywalled inputs.

---

## The six charter questions

### 1. What question does the signal answer?

Whether equities and bonds are currently moving together or apart, how unusual that is against the signal's own
history, and how long comparable environments have persisted. It reports the **realized** correlation state. It
does not forecast when the sign will flip.

### 2. What market assumption does it monitor?

**"Bonds hedge equity drawdowns."** Ledger mapping, registered before the look:

| correlation | status | world |
|---|---|---|
| corr < −0.10 | `intact` | demand-shock: equities fall, yields fall, bonds rally |
| \|corr\| ≤ 0.10 | `under_test` | ambiguous transition band |
| corr > +0.10 | `violated` | supply/inflation: bonds and equities fall together |

The ±0.10 neutral band was pre-committed 2026-08-02 before looking and is **not** re-tunable in this phase.

### 3. What mechanism supports it — why does it survive being known?

The stock-bond correlation is the observable proxy for the **nominal-real covariance** — whether the dominant
macro shock is to demand/growth or to supply/inflation. Under demand shocks, growth and inflation move together,
so falling equities coincide with falling yields and bonds rally. Under supply/inflation shocks, they move
oppositely and both assets fall.

**Why it survives being known:** it is not an arbitrage. The correlation is a property of the prevailing
macro-shock composition, set by the monetary regime and inflation dynamics, not by a mispricing anyone can trade
away. Knowing today's correlation regime does not change which shocks the economy is experiencing. This is a
**risk-management** channel, not a risk-premium one: the signal tells you the current joint distribution's shape,
which is true regardless of how many people observe it. (Standard-literature terms: nominal-real covariance;
Campbell–Sunderam–Viceira on bonds' changing risk; Baele–Bekaert–Inghelbrecht on flight-to-quality.)

### 4. What evidence would validate it?

**V1 — Sign correspondence (US, hypothesis sample; already observed 2026-08-02).** Mean correlation positive in
1970s–80s, negative 2000–2021, positive from 2022. Recorded as hypothesis-generating, NOT evidence.

**V2 — Hedge behaviour by state (the on-mechanism read).** Conditional on state, on **equity-down months**, do
bonds cushion or fall too? Registered as the primary validation metric because — unlike average returns by state
— it is not confounded by the secular rate cycle (a confound found and documented 2026-08-02). Bar: the fraction
of equity-down months on which bonds also fell must be **monotone increasing** across `intact → under_test →
violated`.

**V3 — Out-of-hypothesis-sample replication (Japan, Germany).** Identical construction, monthly, via the shared
`run_oos` harness on `build(panel)`. Pairings registered: **Japan equity × JGB 10y**, **Europe equity × German
Bund 10y**. Bar: V2's monotonicity holds in each adequately-powered region.

> **REGISTERED SCOPE LIMITATION (Adam's ruling, 2026-08-06 — before the look).** International equity panels
> begin **1990-07**; the JGB series begins 1989. **The international sample therefore does not contain the
> 1970s–80s inflation regime.** Phase 2 can test the 2022 flip and the by-state hedge behaviour on 1990–2026
> only — it **cannot** test the full sign-flip cycle out-of-sample. This is registered as a known constraint of
> the evidence, not a finding, and it is why `production` is unavailable to this phase. Free deeper history does
> not exist (yfinance reaches only 1985/1987 and is price-only, mismatching the bond total-return leg; MSCI and
> Global Financial Data are paywalled). Revisiting requires purchased data, which is a separate decision.

**V4 — Power pre-check (registered, runs BEFORE any by-state contrast is interpreted).** For each region, count
months in each state. **If any state has fewer than 24 months in a region, that region is declared UNDERPOWERED
for the by-state contrast and its result is reported as "insufficient coverage", not as a weak or negative
finding.** Registered in advance precisely so an underpowered noisy contrast cannot be read as either support or
refutation after the fact.

**V5 — Window robustness.** The state read must not depend on the window: the 63d/126d/252d daily panel (US) and
a 12m/24m/36m monthly panel (all regions) must agree on the sign in the same periods.

### 5. What would falsify it?

- **R1 (primary).** V2 monotonicity fails in the US — the `violated` state does not correspond to bonds cushioning
  less on equity-down months. The signal would then not be measuring the hedge property it claims. **Kill.**
- **R2.** V2 monotonicity fails in every adequately-powered international region. The US result would be a
  US-specific artifact. **Kill** (as the sector-dispersion lead candidate was killed on exactly this bar).
- **R3.** The state is an artifact of the window: sign disagreement across 12m/24m/36m in the same periods.
  **Kill or re-specify** with the defect disclosed.
- **R4.** The signal turns out to be a relabelling of the volatility axis — it carries no information about hedge
  behaviour once volatility is conditioned on. **Demote**; the mechanism gate would be failing in practice.
- **R5.** All regions fail V4's power pre-check. Not a kill: the phase closes as **INCONCLUSIVE — insufficient
  international coverage**, and the signal stays US-only at `research`. Registering this as a distinct outcome
  prevents an underpowered result being written up as either support or refutation.

### 6. What does it explicitly NOT claim?

This signal reports a measured correlation state, its historical rarity, and how long comparable episodes lasted.
It names the assumption "bonds hedge equity drawdowns" and STOPS.

It does **not** predict when the correlation will flip, does not claim the flip is forecastable, and does not
imply, recommend, or encode any response to a `violated` reading. What a violated hedge assumption means, and
what if anything to do about it, is the human's judgment in a separate system. No instrument selection, no
exposure change, no sizing, no timing — none of these concepts exist in this repo.

---

## Post-look dispositions (2026-08-06) — decided by Claude, ratified by Adam

Three judgment calls arising from the one-look. Recorded here so the reasoning is attributable, and because
ratifying a recommendation is not the same act as signing off the results.

- **D-02a — V5 window softness: ACCEPT, no re-specification.** Sign agreement with the 24m primary is 74–85% at
  12m and 85–91% at 36m. A 12-month correlation is estimated from 12 observations and *should* be noisier; the
  registered primary is 24m and the state is stable at 24m and above. R3 is not tripped. The caveat stays on the
  record rather than being smoothed away, and the neutral-band concentration check remains a **registered
  follow-up** — not run, because it would be a second look.
- **D-02b — the state: CONTINUOUS-FIRST. The label may never stand alone.** *(Amended 2026-08-06 after Adam
  challenged whether this re-imports the state thing we killed. He was right to push; the original wording was too
  comfortable with the label.)*

  The distinction that holds: for volatility, CALM/STRESSED was an **arbitrary threshold on a continuous
  magnitude** — nothing mechanical happens at 18% annualized — and the benchmark proved a continuous read beat it.
  Here, **sign zero is a real mechanical boundary**: corr < 0 means bonds move *against* equity (the hedge
  operates), corr > 0 means they move *with* it. That is a property of the world, not a knob.

  **But the ±0.10 neutral band IS a knob**, and the one-look showed exactly the predicted symptom — in Japan and
  Europe `intact → under_test` barely separates (25→29%, 27→32%) while nearly all discrimination sits at
  `violated`. So the vol lesson applies, just not by collapsing to two states (that would be *more* thresholding):

  **The reading is the continuous correlation plus its rarity. The ledger status is a DERIVED label and must never
  be emitted, presented, or stored without the underlying number beside it.** Same shape as the volatility signal,
  where level and percentile lead and any banding is presentation only. The three states stay — an ambiguous
  transition zone honestly labelled as ambiguous is information, not noise — but they are a view of the number,
  never a replacement for it. To be enforced in the Level-0 record: no `state` field without `corr` and its rarity.
- **D-02c — maturity ceiling `research`: STANDS.** V2 replicating in all three regions does not change the sample:
  the international panels begin 1990 and contain no inflation regime. A strong result is precisely when this cap
  is most tempting to drop, which is why it was registered before the look.

**Results sign-off remains PENDING** — overnight cooling-off, then Adam's dated sign-off. These dispositions are
not that sign-off.

## Pre-registered analysis specification

Frozen before the look. Lines marked **[recommended — Adam to confirm/override]** are my defaults, not yet his.

- **Construction** — `stockbond_corr.build(panel)` on the shared causal spine (`causal.py`), region-agnostic
  two-column schema `(eq, bond)`. Already refactored and guarded by `assert_causal` (2026-08-06, no look spent).
- **Frequency** — monthly for all cross-region comparison; the US daily read is retained as the domestic
  high-frequency view only.
- **Monthly correlation window** — **24 months** primary, 12m/36m robustness. [recommended — Adam to
  confirm/override]
- **Equity-down definition for V2** — monthly equity return < 0. [recommended — Adam to confirm/override]
- **Neutral band** — ±0.10, pre-committed 2026-08-02, not re-tunable.
- **Point-in-time** — returns only; no macro vintage surface. Bond total returns are constructed from yields,
  so the construction method is fixed before the run and disclosed.
- **One look.** V2–V5 run once, as a single frozen script writing to `results/`. Positive claims require
  overnight cooling-off and Adam's explicit dated sign-off.

**Open before the run:** the two [recommended] lines above, and Adam's dated sign-off of this charter.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
