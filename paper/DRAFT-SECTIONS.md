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

*Next: intro draft against Shu–Yu–Mulvey's specific claims (OUTLINE next-action #4)
once the title framing is decided; figure exports (#3).*
