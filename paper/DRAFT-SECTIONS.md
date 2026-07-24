# Draft manuscript sections — v0 (2026-07-23, for Adam's edit)

Framing-invariant sections drafted first (identical under the negative-first or
system-first title — see OUTLINE.md REFRAME OPTION). Numbers from frozen artifacts:
stage1.csv, allocation_summary.csv, calibration_gate.csv, sensor_validation.csv.

---

## §2. Discipline

Every economic claim in this paper was evaluated exactly once, against criteria frozen
before any real-data result existed. We preregister each experiment in a versioned
document (objects, arms, primary metric, falsifiers, and verdict wording), freeze it in
the project's public git history, and only then run: the freeze commit provably precedes
the one-look run in the commit graph. Results cannot be re-run, re-classified, or
re-worded after the look; where a design defect is discovered post hoc — it happened
once, a qualitatively-specified gate criterion — it is recorded as a defect rather than
resolved silently. Two further rules harden the protocol beyond common practice. First,
a cooling-off requirement: any experiment that could produce a positive claim requires
an overnight gap between freeze and run, and an explicit signed authorization — never a
conversational go-ahead. Second, an out-of-hypothesis-sample rule: hypotheses generated
by descriptive work on the U.S. panel are treated as contaminated by selection, and no
supportive verdict may be claimed for them until they confirm on data that did not
generate them (designated developed-market panels, held untouched).

The estimation architecture is causal end to end. Features are derived from the return
series alone — exponentially weighted downside deviation (10-day half-life) and Sortino
ratios (20- and 60-day half-lives) — eliminating the vintage-lookahead problem class
that macro conditioning series import. The jump model is refit annually on an expanding
window; within each scoring year every parameter is frozen, including the jump penalty
λ, which is re-chosen each refit by causal validation on the trailing eight years of
the training window only. Out-of-sample states come from a forward dynamic-programming
filter — the endpoint of the value recursion, never the backtracked (smoothed) path —
so the state at time t depends only on data through t. Execution is next-close
(signals trade with a two-day shift; same-close is reported as sensitivity only), with
10 bps one-way costs identical across every arm.

Inference is comparative and exposure-honest. The primary metric is the Fleming–
Kirby–Ostdiek quadratic-utility performance fee (γ=10 headline, γ=1 sensitivity) with
paired stationary-bootstrap confidence intervals (mean block 126 days). Because utility
fees mechanically reward average exposure, every conditional arm faces three null
distributions computed before the primary: random persistent signals with matched
transition rates (exposure-matched placebos), timing-destroyed surrogates, and iid
pipelines — plus a static mix matched to the strategy's realized average exposure. And
because "beats buy-and-hold" is not evidence of skill, every experiment carries a
reactive incumbent as co-primary: volatility targeting for exposure decisions, EWMA
estimation for covariance decisions. A claim counts only if it clears the best simple
alternative; arms adjacent in the design differ by exactly one ingredient, so any gap
is attributable.

## §6. Mechanism — the detection-lag race

The results are unified by a single mechanism, demonstrated in simulation before any
real-data run: regime value at daily horizons is an information-timing claim, and
recognition lag is the binding constraint. On synthetic two-state panels with known
regimes, an oracle that switches exposure at the true regime boundaries beats
volatility targeting by +136 to +1,090 bps per year of utility fee — persistent-regime
information is genuinely valuable when it is instantaneous. Delaying the same oracle's
signal by 10–21 trading days erases most to all of that edge. Any causal detector of
persistent states must accumulate evidence before switching — our filter's median
recognition lag is on the order of 5–20 days by construction, and its empirical median
detection lag from ex-post market peaks is 20 days — so a causal regime signal lives
precisely in the regime where even perfect information loses. The reactive incumbent
has no recognition step to lose: volatility targeting responds to squared returns
within days, without ever naming the regime. It harvests the same persistent-volatility
structure the regime model detects, but pays no lag toll.

The race generalizes beyond exposure timing, which is what makes it a mechanism rather
than an anecdote. Conditioning a multi-asset covariance estimate on the state loses to
a plain EWMA covariance of the same data (−29 bps; the EWMA arm is the best-performing
arm outright). Even the model's own confidence measure loses the race: mapped through
a calibration layer on synthetic panels where the true states are volatility states,
the filter's evidence margin is dominated by a plain EWMA volatility estimate as a
state-probability signal in eight of eight data-generating environments, on both
discrimination and calibration. The pattern is uniform: the state machine knows where
it is with exceptional reliability, but everything it knows about *magnitude* — how
much risk, how confident, how to size — arrives later and coarser than a reactive
estimator computing the same quantity directly. Regime detection survives as
measurement; regime conditioning fails as decision machinery wherever a reactive
estimator can compute the decision-relevant quantity without waiting for a label.

---

## §1. Introduction (system-first, v0 — 2026-07-24)

A recurring claim in the applied regime-switching literature is that identifying the
market's latent state and trading on it improves investor outcomes. Recent work built on
statistical jump models — Nystrup, Lindström & Madsen (2020), Nystrup, Kolm & Lindström
(2021), Shu, Yu & Mulvey (2024), and the jump-model-with-MPC extension (2025) — reports
that regime-aware allocations beat buy-and-hold and raise risk-adjusted returns. The claim
is attractive because the estimator is attractive: jump models produce stable, interpretable
state sequences from a handful of return-based features, without the fragility that made
hidden Markov regime models hard to deploy out of sample. [TODO: quote Shu–Yu–Mulvey's exact
headline improvement and their benchmark — buy-and-hold or 60/40 — so the deflation is
against their stated numbers.]

We take the estimator seriously as a measurement device and separate two questions the
literature tends to fuse. First: does the instrument *measure* the market's risk state
reliably — is the label a stable, reproducible, live-computable quantity? Second: does
*conditioning a decision* on that label add value over a simple estimator that never names
the regime? Our central finding is that these questions have opposite answers, and that the
reported economic value lives in the gap between them.

On the first question the instrument is exceptional. A K=2 jump model on return-only
downside features produces a label that is 100.0% stable under ±2-year perturbations of the
training window — where an HMM ensemble on the same data agrees with itself only 80.9% of
the time — switches a modest 1.66 times per year, and reproduces to 1.0000 agreement on a
9,120-day out-of-sample overlap when carried to the present through a live data splice. As a
market-state sensor it is genuine: it flags 15 of 18 ex-post bear markets. This is a
measurement instrument worth having, and Section 3 validates it as such.

On the second question every use we tested is dominated by a reactive estimator computing
the decision-relevant quantity directly. We evaluate three uses under strict preregistered,
one-look discipline (Section 2): trading the label as an exposure signal (Section 4),
conditioning a multi-asset covariance estimate on it (Section 5), and mapping the filter's
own evidence margin to a state probability (Section 6). The exposure strategy's apparent
+488 bps/yr utility fee over buy-and-hold sits inside every exposure-matched null band and
loses a significant −256 bps/yr to volatility targeting; covariance conditioning adds a
band-interior +2.8 bps/yr and loses −29 bps/yr to a plain EWMA covariance; and the evidence
margin is beaten by an EWMA-volatility probability in all eight synthetic environments. A
single mechanism, demonstrated in simulation before any real-data run, unifies the three
(Section 7): regime value at daily horizons is an information-*timing* claim, and a causal
detector's recognition lag lands it exactly where even a perfectly-informed oracle loses to
an estimator that pays no recognition toll.

Our contribution is therefore both constructive and deflationary. We deliver a regime
instrument validated to an unusual standard — perturbation stability, live operation, and a
claim-by-claim ledger of what is out-of-sample-validated versus merely descriptive
(Section 8, the monitor). And we show, with exposure-matched nulls and reactive co-primary
baselines that the source literature omits, that its decision value at daily horizons is an
artifact of comparison choices. The instrument-versus-strategy distinction — usually a
footnote — is the paper's thesis: measurement validity is not decision value, and honest
baselines separate them.

## §3. The instrument (Layer 1 — measurement validity) (v0 — 2026-07-24)

The estimator is a two-state weighted statistical jump model (Bemporad et al. 2018; Nystrup
et al. 2020) fit to three return-only features — exponentially weighted downside deviation
(10-day half-life) and Sortino ratios at 20- and 60-day half-lives — with a jump penalty λ
that enforces state persistence. We evaluate it first purely as a measurement device, before
any economic use, on three properties a deployable instrument must have: stability under
reasonable estimation choices, agreement with an external ground truth, and live
computability.

**Stability.** The property that motivated the whole program is reproducibility of the label
under training-window perturbation. Shifting the training start by ±2 years — a first-order
analyst choice that leaves competing estimators disagreeing about the state on a fifth of all
days — changes the jump-model label on 0.0% of out-of-sample days: 1.000/1.000 agreement at
both the −2y and +2y shifts. An HMM ensemble on the identical data and features achieves only
0.809. The label switches 1.66 times per year and partitions the 1990–2026 out-of-sample
period into 30 episodes, each a genuine high-volatility environment (calm-state annualized
volatility ≈14%, stressed-state ≈25%); λ selects to the interior of its search grid rather
than an edge. Estimation instability — the practical reason HMM regime labels are hard to
trust in production — is, for this estimator on this data, solved.

**External agreement, and an honest boundary.** Validated against ex-post bear-market
datings, the label catches 15 of 18 declines of −15% or more, at a median recognition lag of
20 trading days from the ex-post peak. It is, precisely, a *volatility-state* detector rather
than a *bear-market* detector: it fires on high-volatility environments whether or not a
sustained decline follows (hence a moderate precision against directional bear datings), and
it misses fast crashes that resolve before its persistence-seeking filter can accumulate
evidence — 1998 (LTCM) and 2018-Q4 are sub-threshold at the deployed λ. We state this as the
instrument's boundary of use rather than a defect to be tuned away: the 20-day lag and the
fast-crash misses are exactly the constraints the mechanism section shows are binding for any
causal detector, and they define what the monitor (Section 8) can and cannot claim.

**Live computability.** The instrument runs to the present. Ken French publishes with a
one-to-two-month lag, so the live tail is spliced from an SPY proxy; the splice passes its
gate at 0.9957 return correlation, and the composite label agrees with the frozen research
label on 1.0000 of the 9,120-day overlap. There is no vintage-lookahead: the filter's state
at time t uses only data through t, and the live label at t is the same object the frozen
backtest would have produced.

These three properties make the label a measurement instrument worth building on. The
remaining sections ask what happens when a decision is conditioned on it — and find, uniformly,
that the measurement's quality does not transfer to decision value.

---

*Next: figure exports as standalone SVG/PNG (OUTLINE #5); exact-numbers appendix (#1); fill
the two [TODO] quotes in §1 from Shu–Yu–Mulvey. Section-number map under the system-first
spine: §1 intro, §2 discipline, §3 instrument, §4–6 the three races, §7 mechanism (the block
labeled "§6" above), §8 monitor.*
