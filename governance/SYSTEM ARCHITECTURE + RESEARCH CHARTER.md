# SYSTEM ARCHITECTURE + RESEARCH CHARTER

## READ THIS BEFORE MODIFYING ANY REPOSITORY

This workspace contains three separate repositories that together form a systematic investment research ecosystem:

1. **Market Intelligence / Modeling**
2. **Portfolio Management**
3. **Algo Trading**

These repositories are intentionally separate.

Your job is not to collapse them into one system.

Your job is to make them **composable, scientifically rigorous, and clear about their respective responsibilities.**

The overarching objective is to move from:

\[
\text{Market Data}
\rightarrow
\text{Information}
\rightarrow
\text{Research}
\rightarrow
\text{Validated Signal}
\rightarrow
\text{Trading}
\rightarrow
\text{Portfolio Interpretation}
\]

without allowing any layer to silently assume the responsibilities of another.

---

# 0. THE MOST IMPORTANT PRINCIPLE

## DO NOT SEARCH FOR A MAGIC MARKET MODEL.

Do not assume that:

- one HMM explains the market
- one factor explains returns
- one PCA explains market behavior
- one macro model predicts equities
- one ML model can predict the market
- one composite score should summarize everything

The market may be multidimensional.

It may have persistent structure.

It may have conditional relationships.

It may also be substantially unpredictable.

**The architecture must be capable of discovering either outcome.**

If the evidence says there is no stable predictive structure in a particular dimension, that is a valid and valuable result.

Do not force predictive power into existence.

---

# 1. EPISTEMIC SEPARATION

Every component and research result must be classified into one of four categories:

### OBSERVATION

What is measured?

Example:

> Volatility is elevated relative to its historical distribution.

### HYPOTHESIS

What might this imply?

Example:

> Elevated volatility may correspond to different future return distributions.

### EVIDENCE

What does the data actually support?

Example:

> Conditional downside risk is historically higher under this state, but mean returns are not reliably different.

### ACTION

What should a trading or portfolio system actually do?

Example:

> Reduce equity exposure by 3%.

These categories must not be silently collapsed.

In particular:

\[
\boxed{\text{Observation} \neq \text{Prediction} \neq \text{Action}}
\]

A model identifying a state does not automatically create a trading signal.

A trading signal does not automatically justify portfolio action.

---

# 2. REPOSITORY 1: MARKET INTELLIGENCE

## PURPOSE

The Market Intelligence repository is the **market observatory**.

Its primary job is:

> **Measure and characterize the structure of markets.**

It should preserve the multidimensional nature of the market.

---

## 2.1 Measurements

It may measure:

- volatility
- breadth
- trend
- momentum
- correlation
- dispersion
- liquidity
- rates
- credit
- macro variables
- factor behavior
- cross-sectional relationships
- relative performance
- other empirically useful market dimensions

Do not assume any one of these is predictive.

---

## 2.2 Dimensional structure

Investigate whether many observed variables can be represented by a smaller number of stable dimensions.

Potential methods include:

- PCA
- rolling PCA
- factor models
- clustering
- latent-state models
- HMMs
- other appropriate statistical methods

But every method must answer a research question.

Do not use sophisticated models merely because they are available.

For example:

> Does PCA reveal a stable low-dimensional representation of market behavior?

is a legitimate question.

> PCA exists, therefore we need a PCA trading strategy.

is not.

---

## 2.3 Principal components

Principal components are **descriptive statistical objects first**.

Do not automatically interpret:

\[
PC_1
\]

as:

> "market risk"

or:

\[
PC_2
\]

as:

> "bull/bear"

unless the evidence supports that interpretation.

Track:

- loadings
- explained variance
- stability
- rolling behavior
- economic interpretation
- relationship to known variables
- sensitivity to sample period

Ask:

> Does this component represent a stable phenomenon or merely a sample-specific mathematical direction?

---

## 2.4 State / regime models

HMMs and similar models should primarily answer:

> **What state does the observed market appear to be in?**

They should not automatically answer:

> **What trade should we make?**

Avoid forcing the market into:

\[
\{\text{Bull},\text{Neutral},\text{Bear}\}
\]

if a multidimensional representation contains more information.

A useful output may instead be:

```text
Volatility state: elevated
Breadth state: deteriorating
Trend state: persistent
Dispersion: high
Liquidity: normal
Confidence: moderate
Persistence: 18 days
```

Preserve this information.

---

# 3. REPOSITORY 2: ALGO TRADING

## PURPOSE

The Algo repository is the **systematic trading laboratory**.

Its question is:

> **Can market information be converted into a robust, executable trading strategy?**

It is intentionally more experimental and aggressive than Portfolio Management.

It is allowed to investigate:

- tactical strategies
- momentum
- mean reversion
- factor rotation
- volatility strategies
- cross-sectional strategies
- market-state strategies
- combinations of dimensions
- short strategies
- high-turnover strategies
- other systematic ideas

But every strategy is a **hypothesis**, not a truth.

---

# 3.1 MAJOR CLEANUP REQUIRED

The existing Algo repository has accumulated substantial modeling/research complexity.

Perform a serious audit.

Remove, simplify, or relocate components whose primary purpose is:

> understanding market structure

if they belong in Market Intelligence instead.

Do not preserve obsolete complexity just because it exists.

The Algo repository should ultimately be centered around:

```text
INPUT
→ STRATEGY
→ POSITION LOGIC
→ BACKTEST
→ RISK
→ ORDER
→ ALPACA
→ EXECUTION
→ RECONCILIATION
→ LOGGING
```

The Algo repository should not become another Market Intelligence repository.

---

# 3.2 Strategy research

A strategy should explicitly define:

### Hypothesis

What relationship are we testing?

### Input

What market information is used?

### Rule

How does that information become a trading decision?

### Position sizing

How large is the position?

### Holding period

How long is the signal expected to persist?

### Costs

What transaction costs, spread, slippage, and market impact are assumed?

### Validation

What constitutes success or failure?

---

# 3.3 Research hierarchy

Every strategy should pass through:

```text
IDEA
 ↓
HYPOTHESIS
 ↓
PRE-REGISTERED TEST DESIGN
 ↓
IN-SAMPLE DEVELOPMENT
 ↓
OUT-OF-SAMPLE TEST
 ↓
ROBUSTNESS TESTING
 ↓
COST / EXECUTION TEST
 ↓
FORWARD / PAPER TEST
 ↓
LIVE EXPERIMENT
```

Do not optimize repeatedly against the same out-of-sample period.

If the test period is used to modify the model, it is no longer genuinely out-of-sample.

---

# 3.4 Multiple testing

The system must explicitly account for the fact that many hypotheses will be tested.

If 1,000 ideas are tested, some will look excellent by chance.

Track:

- number of hypotheses tested
- parameter searches
- model variants
- rejected strategies
- data periods tested
- assets tested
- selection criteria

Do not present the best backtest without its research context.

---

# 3.5 Strategy failure is a valid result

A strategy should be allowed to conclude:

> REJECTED

because:

- effect too small
- unstable
- redundant
- no mechanism
- fails out of sample
- fails after costs
- excessive turnover
- parameter-sensitive
- regime-dependent without sufficient robustness
- insufficient economic significance

Do not rescue failed strategies simply because they are interesting.

---

# 4. REPOSITORY 3: PORTFOLIO MANAGEMENT

## PURPOSE

Portfolio Management represents the **actual investor's utility and constraints**.

It is not a market prediction system.

It is not the Algo Trading laboratory.

Its question is:

> **Given available market information and validated evidence, what portfolio exposure is appropriate for this investor?**

---

# 4.1 Inputs

Potential inputs include:

- Market Intelligence outputs
- validated Algo findings
- strategic allocation
- IPS ranges
- risk constraints
- liquidity
- investment horizon
- contribution capacity
- speculative budget
- concentration limits
- personal utility
- behavioral constraints

---

# 4.2 Portfolio action

Portfolio Management may translate market information into:

- no action
- monitoring
- small tilt
- larger tilt within policy
- rebalance
- reduction of exposure
- increase of exposure

But the action must remain bounded by governance.

---

# 4.3 CRITICAL DISTINCTION

The Portfolio Manager is intentionally more risk-constrained than the Algo Trading laboratory.

This is not a contradiction.

The Algo asks:

> **Can this strategy make money?**

The Portfolio Manager asks:

> **Does this risk deserve a place in my financial life?**

These are different objective functions.

---

# 5. INFORMATION FLOW BETWEEN SYSTEMS

The repositories should remain separate but communicate through explicit, versioned interfaces.

Conceptually:

```text
MARKET INTELLIGENCE
        │
        ├──────────────→ ALGO TRADING
        │
        │                "Can this information
        │                 be traded?"
        │
        └──────────────→ PORTFOLIO MANAGEMENT
                         "How much should this
                          matter to the portfolio?"
```

Validated Algo findings may eventually feed back into Market Intelligence as evidence about which dimensions appear to contain tradable information.

This feedback must not cause circular validation.

---

# 6. DO NOT LET THE SYSTEM LEARN FROM THE FUTURE

This is non-negotiable.

Audit for:

- look-ahead bias
- survivorship bias
- data leakage
- timestamp errors
- future constituent knowledge
- future parameter knowledge
- revised macro data
- overlapping labels
- improper train/test splitting
- accidental use of future information through preprocessing

Every research result should be capable of answering:

> **Exactly what information was available at the decision timestamp?**

---

# 7. SIGNAL ADMISSION

A candidate signal should not become part of the system merely because it backtests well.

Evaluate:

### Mechanism

Why might the relationship exist?

### Measurement

Can we reliably measure it?

### Incremental information

Does it add information beyond existing signals?

### Stability

Does it persist?

### Robustness

Does it survive reasonable methodological changes?

### Out-of-sample performance

Does it generalize?

### Economic significance

Is the effect large enough to matter?

### Implementation

Can it actually be traded?

### Cost

Does it survive realistic execution?

### Capacity

Would the strategy remain viable at realistic size?

### Redundancy

Is it merely another representation of an existing signal?

---

# 8. MARKET INTELLIGENCE SHOULD NOT BECOME A TRADING ENGINE

The Market Intelligence system should be allowed to conclude:

> "We do not know."

It should also be allowed to say:

> "This dimension appears informative about risk but not returns."

or:

> "This state appears descriptive but not tradable."

That is valuable information.

---

# 9. ALGO TRADING SHOULD NOT BECOME A PORTFOLIO MANAGER

The Algo system can discover:

> "This strategy has historically produced a 1.2 Sharpe ratio."

That does not imply:

> "Put 30% of the user's portfolio into it."

Portfolio Management decides whether and how the result should be used.

---

# 10. PORTFOLIO MANAGEMENT SHOULD NOT BECOME A PREDICTIVE MODEL

Portfolio Management does not need to know whether the market will rise tomorrow.

Its job is to construct an appropriate portfolio given uncertainty.

It should be robust to being wrong.

---

# 11. THE SYSTEM SHOULD BE ABLE TO DISAGREE WITH ITSELF

A healthy architecture can produce:

```text
Market Intelligence:
    Conditions are deteriorating.

Algo:
    No statistically robust trading opportunity found.

Portfolio:
    Maintain strategic allocation,
    perhaps with a modest tilt.
```

That is not failure.

It is exactly what separation of responsibilities allows.

---

# 12. RESEARCH LEDGER

Create or maintain a central research ledger containing:

```text
Hypothesis
Date proposed
Data used
Variables
Test design
Variants tested
Results
Out-of-sample result
Costs
Decision
Reason for rejection/acceptance
Current status
```

Possible statuses:

```text
IDEA
TESTING
PROMISING
VALIDATING
VALIDATED
REJECTED
DEPRECATED
REDUNDANT
```

The purpose is to prevent:

> rediscovering the same idea six months later because nobody remembers why it failed.

---

# 13. RESEARCH DISCIPLINE

When proposing a new model, feature, signal, or architecture change, first answer:

1. What question does this answer?
2. Which repository owns that question?
3. Why can't an existing component answer it?
4. What evidence would falsify the hypothesis?
5. What information is available at decision time?
6. How will it be validated?
7. What would cause us to reject it?
8. Does it duplicate existing information?
9. What is the smallest experiment capable of answering the question?

If these questions cannot be answered, **do not immediately build the feature.**

---

# 14. AGENT BEHAVIOR

You are not being asked to blindly implement my ideas.

You are expected to **challenge them.**

If an architectural assumption is wrong, explain why.

If a model is redundant, say so.

If a proposed signal is likely overfit, say so.

If the correct answer is:

> "We don't have enough evidence."

say that.

Do not manufacture sophistication.

Do not add machine learning because it sounds advanced.

Do not add another regime model because the current model is inconvenient.

Do not optimize for backtest performance at the expense of research validity.

Do not assume that more complexity means more predictive power.

---

# 15. BEFORE MAKING CHANGES

For any substantial task:

### STEP 1
Inspect the relevant repository.

### STEP 2
Map the current architecture.

### STEP 3
Identify what already works.

### STEP 4
Identify duplication and dead complexity.

### STEP 5
Explain the proposed change.

### STEP 6
State what will NOT be changed.

### STEP 7
Implement the smallest defensible change.

### STEP 8
Run relevant tests.

### STEP 9
Report what changed and what evidence supports it.

Do not rewrite large sections of the system without first establishing why the rewrite is necessary.

---

# 16. CURRENT PRIORITY

The immediate objective is **NOT** to build a new trading strategy.

The immediate objective is to understand the existing three repositories and establish the correct boundaries between them.

Perform a cross-repository audit.

Produce:

## A. Architecture map

What currently exists?

## B. Responsibility map

Which repository should own each component?

## C. Dependency map

How do the repositories currently interact?

## D. Duplication map

Where are the same concepts implemented multiple times?

## E. Algo cleanup plan

Which modeling components should be removed, simplified, or separated from the execution/trading infrastructure?

## F. Interface proposal

What information should Market Intelligence expose to Algo and Portfolio Management?

## G. Research pipeline

How should ideas move from hypothesis → validation → trading → portfolio consideration?

## H. Top three priorities

Identify the three highest-value changes required to move the ecosystem toward this architecture.

Do not begin by implementing all of them.

---

# 17. DEFINITION OF SUCCESS

The final system should have this conceptual structure:

```text
                    MARKET DATA
                         │
                         ▼
              ┌─────────────────────┐
              │ MARKET INTELLIGENCE │
              │                     │
              │ Measure             │
              │ Discover structure  │
              │ Estimate states     │
              │ Preserve dimensions │
              └──────────┬──────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
     ┌──────────────────┐   ┌──────────────────┐
     │  ALGO TRADING    │   │ PORTFOLIO MGMT   │
     │                  │   │                  │
     │ Experiment       │   │ Interpret        │
     │ Test             │   │ Constrain        │
     │ Validate         │   │ Allocate         │
     │ Execute          │   │ Govern           │
     └──────────────────┘   └──────────────────┘
              │                     │
              └──────────┬──────────┘
                         ▼
                RESEARCH FEEDBACK
```

The ultimate objective is not:

> **Build the world's best market predictor.**

It is:

> **Build a system that continuously discovers, tests, rejects, validates, and selectively exploits information about markets while keeping market intelligence, trading experimentation, and personal portfolio governance conceptually separate.**

If the research eventually discovers that only a few dimensions are useful, the system should become simpler.

If it discovers that no particular dimension is reliably tradable, the system should say so.

If it discovers a genuinely robust strategy, the system should make it possible to test and eventually deploy it.

**The architecture must allow all three outcomes.**