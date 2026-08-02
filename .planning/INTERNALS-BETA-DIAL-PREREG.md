# Prereg — Market-Internals Fragility Gauge (Risk-Management Product) — REV 2, DRAFT

Status: **DRAFT 2026-07-31.** Design changes permitted until FREEZE. No result exists; blind intact.
Positive-claim-capable → requires (a) an overnight gap between FREEZE and the run, and (b) an
explicit named + dated sign-off (Adam) before the look. A conversational go-ahead does NOT
constitute sign-off (CLAUDE.md cooling-off rule).

Rev history: Rev 1 framed the deliverable as an automated beta dial judged on backtest drawdown
geometry vs vol-targeting. Rev 2 (Adam's direction, 2026-07-31) re-scopes the deliverable to a
**human-read fragility gauge** — because the dial-vs-VT framing is the same aggregate-backtest
horse race that nulled the prior three chapters, and it drowns a signal whose edge lives in ~5% of
days. The gauge is judged on **predictive validity for future drawdown** (does it carry info vol
doesn't) and on an **event study** (does it light up before real drawdowns and stay calm in healthy
markets), NOT primarily on whether an allocator beats a baseline. The dial survives only as a
secondary quantitative sanity check.

## §0 Objective (what this model is and is NOT)

This is a **risk-management gauge, not a return-prediction or alpha model, and not primarily an
automated allocator.** It does not forecast market direction. It estimates the **current level of
market fragility** from cross-sectional market internals and expresses it as a continuous score a
human reads to decide how much beta (SPY/QQQ) is prudent to hold. The hypothesis is that these
internals carry information about **future drawdown risk** that reactive volatility targeting does
not — specifically in the narrow-but-calm states where realized vol is low but leadership is
deteriorating. Success = predictive validity for drawdown at matched information, never excess return.

## §0.5 Mechanism gate (CLAUDE.md, added 2026-07-31) — why this survives being known

Category (b), risk management on a durable statistical fact. The mechanism is **structural, not
statistical curve-fit**: when fewer industries carry the index (low breadth, high leadership
concentration), the market has *fewer independent load-bearing points* — more of its level depends
on the continued performance of a shrinking set of names, so a shock to that set is not diversified
away. This is mechanical fragility, and it does not disappear when the gauge is published, because
(i) it is not a return forecast anyone can trade against, and (ii) fragility/vol clustering is one
of the most durable facts in finance. This is explicitly NOT selected on novelty or on a backtest —
it is selected on this mechanism. (Contrast: the three closed nulls were return-timing bets with no
un-arbitrageable mechanism — they fail this gate retroactively.)

## §1 Hypothesis

H1 (primary — incremental predictive validity): the fragility gauge `g(t)` carries information
about **future market drawdown** that realized volatility `σ̂(t)` does not. Operationally: in a
predictive regression of forward drawdown on σ̂ AND g(t), the g(t) coefficient is correctly signed
(more fragile → worse forward drawdown) and statistically significant *after* controlling for σ̂.

H2 (co-primary — event behaviour): the gauge **elevates ahead of large realized drawdowns** —
and, critically, elevates *earlier than σ̂ does* in the calm run-up — while staying low in broad,
healthy markets. This is the "when is beta less ideal to hold" question in its directly usable form.

H3 (secondary — sanity check only): when the gauge is mechanically turned into an exposure dial at
matched average exposure, it does not *worsen* drawdown geometry vs reactive vol-targeting. A
marginal or flat H3 does NOT sink H1/H2 — the deliverable is the gauge, not the allocator.

## §2 Data & era (frozen)

- Signal panel: `data/processed/industry48_daily.csv` (48 French industries, daily) +
  `data/processed/market_daily.csv` (mkt_ret, rf). Sample from first date with ≥90% industries
  present (~1930-07) to panel end. Drawdown target asset = the market factor (mkt_ret).
- OOS confirmation (hypothesis generated on US data → mandatory out-of-hypothesis confirmation,
  CLAUDE.md): `data/processed/{japan,europe}_assets_daily.csv`. Rebuild the SAME internals from
  their portfolio columns, apply the FROZEN gauge definition, repeat H1 (predictive regression) and
  H2 (event study). 1990+.

## §3 Gauge construction (frozen)

**Origin of the signal (frozen):** breadth and leadership concentration were selected **solely**
from the descriptive ceiling analysis (`scratchpad/internals_ceiling.py`, run 2026-07-31, NO LOOK)
on the basis of vol-orthogonality and the conditional forward-DD spread. They were **not** chosen
using any strategy performance, Sharpe, or predictive backtest — no strategy or predictive
regression had been run at selection time. Dispersion was demoted to a control by the same step.

All computed causally (rolling, no forward info), z-scored on an **expanding** window (no full-
sample z — leakage). Industry price proxy P = cumprod(1+ret).

- **breadth(t)** = fraction of industries with P > own 50d MA.
- **herf(t)** = Herfindahl of |20d industry cum-return| shares (leadership narrowness; higher =
  more concentrated = more fragile).
- **disp(t)** = cross-sectional stdev of daily industry returns, 20d mean. **CONTROL ONLY.**
- **Fragility gauge** `g(t) = z_expand(-breadth) + z_expand(herf)` (equal weight, frozen; higher =
  more fragile). No weight fitting — equal-weight is the frozen choice to avoid implicit timing.

## §4 The dial (secondary, frozen) & execution

Used only for H3. `w(t) = clip(1 - k·z_expand(g(t)), 0, 1)`, monotone decreasing in fragility.
`k` = the single scalar making the dial's **average portfolio exposure** (mean `w`) over the full
OOS equal the baseline's (mean `w_vt`), by a 1-D root solve on that single equality using ONLY the
two exposure paths — never any return/DD outcome. Once solved, `k` is fixed for every reported
result and both OOS panels. Execution: delay=2, costs 10 bps one-way on |Δw|, cash earns rf.
Baseline: reactive vol-targeting `w_vt(t)=clip(σ_target/σ̂(t),0,1)`, σ̂ = EWM vol hl=20, σ_target
frozen so mean `w_vt` is the exposure-match anchor.

## §5 Primary metrics & support bar (frozen, objective)

**H1 — incremental predictive validity (primary). TIGHTENED 2026-07-31 (Adam) — three holes closed.**
- Target: forward peak-to-trough max drawdown of a beta-1 hold over the next **H = 60 days** — the
  SINGLE pre-committed primary horizon (fragility is a slow-building condition; 60d chosen on that
  economic ground, NOT because it tested better — 60d was not measured in the ceiling; only 20d was).
  H = 20 is reported as a **sensitivity only, non-gating.** (Hole #1 closed: one horizon, not two.)
- Regression: `fwd_maxDD ~ β0 + β1·z(σ̂) + β2·z(g)` on **NON-OVERLAPPING 60d windows** (sample every
  60th day). This matches how the honest ceiling number was measured — overlapping windows inflate
  t-stats (ceiling: overlap t=−9.7 vs non-overlap t=−2.4; the non-overlap number is the truth).
  Overlapping-window HAC is reported as an over-optimistic sensitivity only. (Hole #2 closed.)
- **SUPPORT requires:** β2 correctly signed (more fragile → deeper drawdown, β2 < 0) AND
  |t(β2)| > 2.0 on the non-overlapping regression.
- **The US panel is NOT the verdict — it is the signal's origin and is contaminated by selection
  (breadth+herf were chosen from US descriptive work). US H1 is expected to pass by construction and
  is reported as such, NON-gating. The verdict is the OOS panels (§2 / §6 F4).** (Hole #3 closed.)

**H2 — event study (co-primary).**
- Episode set (objective, not narrative): the **5 largest** peak-to-trough drawdowns of the market
  factor in the OOS sample, identified mechanically by magnitude. (Expected to include the
  canonical narrow-leadership run-ups — 2000, 2007, 2020, 2022 — but selection is by drawdown size,
  not by name, to avoid cherry-picking.)
- Lead-time metric: for each episode, days between a signal first crossing its trailing 80th
  percentile and the drawdown onset (first day of the peak). Compare **gauge lead vs σ̂ lead**.
- **SUPPORT requires:** in ≥3 of 5 episodes the gauge crosses its threshold BEFORE σ̂ crosses its
  own (gauge elevates during the calm run-up), AND the gauge's median trailing level in the 60d
  before each onset exceeds its own full-sample median. Plus a specificity check: the gauge's
  false-alarm rate (threshold crossings NOT followed by a top-decile drawdown within H) is reported
  — a gauge that's always elevated is worthless even if it "predicts" every drawdown.

**H3 — dial sanity (secondary, non-gating).** At matched average exposure, dial max-DD ≤ baseline
max-DD (point estimate) with the paired stationary bootstrap 90% CI on the difference reported
(mean block 126d, B=2000, seed=0). Flat/marginal is acceptable; only a *significant worsening*
(CI entirely on the wrong side) is evidence against the gauge.

## §6 Falsifiers (frozen)

- F1: |t(β2)| ≤ 2.0 on the non-overlapping 60d regression, OR β2 wrong-signed → internals add no
  incremental drawdown information beyond vol. Primary null.
- F2: event study fails (gauge does not lead σ̂ in ≥3/5 episodes, or false-alarm rate so high the
  gauge is non-specific) → not usable as a human signal.
- F3: dispersion-in-the-gauge ablation shows disp drives β2 → signal is recycled vol, reject.
- F4 (THE VERDICT, tightened): SUPPORT requires H1 to pass on **BOTH** Japan AND Europe (the clean,
  selection-free tests), not just one. Passing only US (contaminated) or only one OOS panel → treat
  as a US/single-market artifact, do not ship. (Was: "fails on both → artifact"; strengthened to
  "must pass on both" per the multiple-comparisons tightening.)
- F5 (down-scoped, non-gating): the dial significantly *worsens* drawdown at matched exposure.

## §7 Controls (run BEFORE the primary is read)

- **Random-persistent placebo:** replace g(t) with a persistence-matched random signal (same
  autocorrelation, same threshold-crossing rate); it must FAIL H1 (|t(β2)| < 2) and H2. If the
  placebo "predicts" drawdowns, the test is broken — fix before reading the real gauge.
- **Dispersion ablation (F3):** re-run H1 with disp swapped into the composite; must NOT reproduce
  the real gauge's β2.
- **Vol-only benchmark regression:** report β1 and R² of the σ̂-only model, so the incremental
  contribution of g is visible, not just its significance.
- **Exposure-match verification (H3 only):** mean `w` of dial and baseline agree to within 1%
  relative before H3 is read.

## §8 Pre-mortem (frozen BEFORE the look — a null must teach)

Written now so a null is informative, not just another closed door. Most likely failure modes and
what each would mean:
1. **β2 significant but tiny R² gain** → internals carry *statistically* real but *economically*
   trivial drawdown info; gauge is a curiosity, not a product. Decision: do not ship; record.
2. **Gauge lags σ̂ in the event study** → internals deteriorate concurrently, not ahead; no
   run-up warning value (the thing Adam actually wants). Decision: reject the "early warning" claim.
3. **US-only (F4)** → same fate as dispersion-lag; a US microstructure artifact, not a market law.
4. **Placebo also "predicts"** → forward-DD is so autocorrelated with any persistent signal that
   the whole test design is too weak; redesign needed before any claim.
The pre-committed reading: SUPPORT only if H1 AND H2 pass, controls clean, and it survives ≥1 of
{Japan, Europe}. Anything less is recorded as a scoped negative, not squinted into a win.

## §9 One-look discipline

One look. On FREEZE + sign-off, run once, classify by §5/§6 verbatim, no re-decision of branches
after results exist. OOS panels, controls, and the pre-mortem reading are part of the single look.

---
SIGN-OFF (required before run): __________________  Date: __________
FREEZE timestamp: 2026-07-31 (design locked, REV 2 tightened). Run permitted no earlier than
2026-08-01 with Adam's explicit named sign-off on the line above. Blind intact at freeze.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
