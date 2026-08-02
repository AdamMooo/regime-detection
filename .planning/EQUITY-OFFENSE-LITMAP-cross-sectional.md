# Literature Map — Cross-Sectional & Behavioral Sources of Long-Run Equity Outperformance

**Scope:** A landscape map of the major *schools of thought* on why some equities out-earn others in the cross-section, framed as **mechanisms** (the economic "why"), not products. Not a backtest, not a recommendation. Grounded in specific papers (cited inline). Built 2026-08-02.

**Reading key for each school:** (1) core claim; (2) mechanism type — *risk-based* / *behavioral* / *structural (limits-to-arbitrage)*; (3) durability under being known; (4) OOS + international + post-publication survival; (5) conditions under which it disappears; (6) what would falsify it; (7) agreement / disagreement / genuinely weak evidence; (8) key citations.

**The organizing tension of this entire field** (state it up front, it recurs in every school):
- A *risk premium* is compensation for bearing something painful. It **should survive publication** — knowing about it does not make you willing to hold the pain. (Value-as-risk, BAB-as-leverage-cost, quality-as-... something.)
- A *behavioral mispricing* is someone else's mistake. It **should decay once known and arbitraged** — *unless* limits to arbitrage keep smart money from correcting it. So a behavioral premium that persists is really a *limits-to-arbitrage* premium.
- A *data-mined* pattern was never real; it decays to zero OOS and has no mechanism at all.
The central empirical fight (Section 2) is over how much of the "factor zoo" is category 3 masquerading as 1 or 2.

---

## 0. CAPM / Market Beta — the null model everything is measured against

- **Core claim:** In the CAPM, the *only* priced risk is covariance with the market; expected excess return is linear in beta (the Security Market Line), and no characteristic should predict returns after controlling for beta.
- **Mechanism:** Risk-based, by construction — beta is the single systematic risk, everything else diversifies away.
- **Durable if known?** It is the *equilibrium* benchmark, not an anomaly; the question is whether it is *true*, and empirically it is not.
- **OOS / international / survival:** The SML is **empirically too flat** — high-beta stocks earn less than CAPM predicts, low-beta more. Documented since Black, Jensen & Scholes (1972) and Fama-MacBeth (1973); the flat line is one of the most robust facts in the field and holds internationally and across asset classes (it is the empirical foundation of BAB, Section 8).
- **Disappears if:** it never "worked" as a return predictor; as a *risk model* it fails whenever a non-beta characteristic prices the cross-section (which is constantly).
- **Falsified by:** any stable non-beta predictor with a t-stat surviving multiple-testing — i.e. the entire rest of this document.
- **Agree / disagree / weak:** Near-**universal agreement** that single-factor CAPM is empirically inadequate as a *pricing* model. Disagreement is entirely about *what replaces it* (multifactor risk vs. behavioral). Genuinely weak: whether beta is *completely* unpriced or just mispriced by leverage constraints — BAB says the latter.
- **Citations:** Sharpe (1964) *Capital Asset Prices*; Black, Jensen & Scholes (1972) *The Capital Asset Pricing Model: Some Empirical Tests*; Fama & MacBeth (1973) *Risk, Return, and Equilibrium*.

---

## 1. The Fama-French / q-theory multifactor "risk" tradition — the academic mainstream

- **Core claim:** A small number of characteristic-based factors (size, value, profitability, investment, + market) span the cross-section; these are compensation for systematic risks firms' fundamentals expose you to.
- **Mechanism:** Officially **risk-based**. FF3 (1993) added SMB + HML; FF5 (2015) added RMW (profitability) and CMA (investment). The rival **q-factor / Investment-CAPM** (Hou-Xue-Zhang 2015; Lu Zhang) derives investment + ROE factors from the *supply side* — firms' first-order condition on investment — a genuinely structural (not preference-based) risk story: firms that must invest heavily today have low expected returns because their marginal cost of capital is low.
- **Durable if known?** If truly risk premia, **yes** — you're paid to hold distress/low-growth-option exposure; knowing that doesn't remove the risk. This is the school's core defense.
- **OOS / international / survival:** FF factors replicate internationally (FF 1998, 2017 international five-factor tests). Notably, **in FF's own 2015/2018 work HML becomes *redundant*** — its average return is absorbed by RMW+CMA, i.e. value is "explained" by profitability/investment exposure. The q-model and FF6 fight to a near-draw in spanning tests (each side claims to subsume the other; q-camp claims q fully subsumes FF6).
- **Disappears if:** the "risks" turn out to be unpriced (no bad-times covariance) — the persistent complaint that no one has cleanly identified *what* macroeconomic bad state HML/RMW hedge against.
- **Falsified by:** factors that price the cross-section with **no** plausible risk interpretation *and* that decay post-publication (pointing to mispricing/mining instead).
- **Agree / disagree / weak:** Agreement that a *handful* of characteristics carry most cross-sectional variation. **Sharp disagreement** on (a) which factors (FF5 vs q vs Stambaugh-Yuan mispricing, Section 9) and (b) whether they are risk or mispricing. **Genuinely weak:** the risk *story* itself — the factors are reverse-engineered from returns, and the identification of the underlying state variable is the field's soft underbelly. HML's redundancy inside FF5 is a live embarrassment for "value is a distinct risk."
- **Citations:** Fama & French (1993) *Common Risk Factors...*; Fama & French (2015) *A Five-Factor Asset Pricing Model*; Fama & French (2018) *Choosing Factors*; Hou, Xue & Zhang (2015) *Digesting Anomalies: An Investment Approach*; Zhang (2017) *The Investment CAPM*.

---

## 2. The FACTOR ZOO & the replication / multiple-testing CRISIS — *the central methodological fact*

This is not a "school of return" — it is the meta-layer that discounts every claim below. Treat it as the prior.

- **Core claim:** Hundreds of published "factors" exist; most are the product of data mining and multiple testing, and a large fraction do not survive honest statistical hurdles or out-of-sample.
- **Mechanism:** N/A — this is about *whether the mechanisms below are real at all*.
- **The four load-bearing results:**
  - **Harvey, Liu & Zhu (2016), *"...and the Cross-Section of Expected Returns"* (RFS).** With 300+ published factors, the conventional t > 2.0 hurdle is wrong; accounting for multiple testing / publication bias, a new factor should clear **t ≈ 3.0** (and rising over time). Most published factors do not.
  - **Hou, Xue & Zhang (2020), *Replicating Anomalies* (RFS).** Replicating 452 anomalies with **NYSE breakpoints + value-weighting** (to kill the microcap distortion), **~65% fail even the t > 1.96 single-test hurdle**; **82%** fail the multiple-testing hurdle (t > 2.78). Survivors' magnitudes shrink. Their diagnosis: most of the zoo is a **microcap illusion**.
  - **McLean & Pontiff (2016), *Does Academic Research Destroy Stock Return Predictability?* (JF).** Reconstructing ~97 predictors: returns are **~26% lower out-of-sample** (upper bound on data mining) and **~58% lower post-publication** — implying **~32% pure "publication/arbitrage" decay** on top of mining. Decay is larger for predictors that are cheaper to arbitrage. This is the single cleanest evidence that *publication itself* erodes returns.
  - **Chen & Zimmermann (2022), *Open Source Cross-Sectional Asset Pricing* (Critical Finance Review), + Chen (2021).** The *contrarian* result: with transparent reconstruction, **~98% of clearly-significant original anomalies replicate** with t > 1.96; predictability persists OOS; t-stats are far above 2; predictors are weakly correlated. Their reading: **publication bias is NOT dominant** — the zoo is mostly *real but small and decaying*, not fake.
- **Where opinion lands:** The Hou-Xue-Zhang "most anomalies are microcap noise" camp and the Chen-Zimmermann "most anomalies are real but modest" camp **genuinely disagree**, and the disagreement is largely *methodological* — how you weight microcaps and whether you demand economic (not just statistical) significance. **What everyone agrees on:** raw t > 2 is not enough; microcap/equal-weight results are suspect; and *post-publication decay is real* (McLean-Pontiff is uncontested in direction, debated in magnitude).
- **Falsified by:** N/A — this *is* the falsification apparatus. The relevant question for every school below is: **does it clear the raised bar, survive OOS/international, and decay less than a pure-mining benchmark?**
- **Genuinely weak:** the *level* of the correct t-hurdle (3.0 is a modeling choice); how much decay is arbitrage vs. mining vs. regime; whether "economic significance after real costs" is even meetable at scale for most survivors.
- **Citations:** Harvey, Liu & Zhu (2016); Hou, Xue & Zhang (2020) *Replicating Anomalies*; McLean & Pontiff (2016); Chen & Zimmermann (2022) *Open Source Cross-Sectional Asset Pricing*; Chen (2021) *The Limits of Cross-Section...* / Chen & Zimmermann (2022) *Publication Bias in Asset Pricing Research*.

---

## 3. VALUE (HML) — the risk-vs-behavioral fault line, and the "is value dead" fight

- **Core claim:** Cheap stocks (high book/market, earnings/price, etc.) out-earn expensive ones over the long run.
- **Mechanism — two rival stories, both alive:**
  - **Risk (Fama-French; Zhang q-theory):** value firms are distressed / loaded with unproductive capital / bear more downside in bad states; the premium is compensation. Zhang's investment-CAPM gives value a *structural* (supply-side) reason: low-growth, high-book firms have already sunk capital and carry a higher required return.
  - **Behavioral (Lakonishok, Shleifer & Vishny 1994, *Contrarian Investment, Extrapolation, and Risk*):** investors **extrapolate** past growth too far, overpaying for glamour and underpricing value; the premium is *error correction*, and LSV show value stocks are **not** fundamentally riskier (they do fine in bad states / recessions).
- **Durable if known?** *If risk* → durable. *If behavioral* → durable only insofar as extrapolation is a hard-wired bias and arbitrage is limited (career risk, horizon). The 2007-2020 drawdown is exactly what "decays once crowded" would predict — hence the fight.
- **OOS / international / survival:** Historically robust internationally (FF 1998). But **value suffered a ~55% drawdown from 2007 to mid-2020** (HML), triggering the "**value is dead**" debate.
  - **AQR (Israel, Laursen & Richardson 2021, *Is (Systematic) Value Investing Dead?*):** no — the drawdown is a *revaluation* (value got cheaper relative to growth), not a disappearance of the premium; diversified multi-signal value still has an edge.
  - **Arnott, Harvey, Kalesnik & Linnainmaa (2021, *Reports of Value's Death May Be Greatly Exaggerated*, FAJ):** the entire drawdown is explained by (a) the book-value definition **missing intangibles** and (b) the **valuation spread widening** (value getting cheaper). Capitalize intangibles and value's death "may be greatly exaggerated"; a cheap starting spread even implies a *forward* tailwind.
- **Disappears if:** the intangibles-adjusted, spread-controlled premium *still* vanishes going forward; or if it were purely a book-measurement artifact that better accounting fully removes.
- **Falsified by:** value earning its premium *without* any bad-state covariance (kills risk story) AND *without* mean-reverting cheapness (kills behavioral story) — i.e., if it were just B/M mismeasurement.
- **Agree / disagree / weak:** **Agree:** a value effect existed and is *cheap* today; naive single-metric price-to-book value is impaired by intangibles. **Disagree:** risk vs. behavioral (unresolved for 30 years); whether the post-2007 stretch is death or drawdown. **Genuinely weak:** the risk-state identification (what recession does HML hedge?); whether intangible-adjusted value is robust OOS or a post-hoc fix fit to the drawdown.
- **Citations:** Fama & French (1992, 1993); Lakonishok, Shleifer & Vishny (1994); Israel, Laursen & Richardson (2021); Arnott, Harvey, Kalesnik & Linnainmaa (2021).

---

## 4. MOMENTUM — the anomaly that most embarrasses efficient markets

- **Core claim:** Recent winners (past ~12 months, **skipping the most recent month**) continue to out-earn recent losers over the next few months.
- **Mechanism:** Predominantly **behavioral**, with two families:
  - **Underreaction / gradual information diffusion (Hong & Stein 1999):** news diffuses slowly across "newswatchers"; prices drift toward fundamentals, and momentum traders ride the drift. Empirically supported by Hong, Lim & Stein (2000): momentum is stronger in low-analyst-coverage stocks (info diffuses slower), especially for bad news.
  - **Delayed overreaction / behavioral (Daniel-Hirshleifer-Subrahmanyam 1998):** overconfidence + biased self-attribution push prices *past* fundamentals before reversing.
  - No clean risk story survives; the effect is a challenge to *both* CAPM and FF (Carhart 1997 added UMD as a pragmatic 4th factor, explicitly *without* a risk claim).
- **Durable if known?** Uncomfortable case: it is **public, decades-old, and still (mostly) there** — which pure "behavioral decays when known" would not predict. The reconciliation is **limits to arbitrage + tail risk**: momentum is expensive to trade (high turnover) and periodically **crashes**, so arbitrageurs cannot costlessly remove it.
- **The crash tax (Daniel & Moskowitz 2016, *Momentum Crashes*):** momentum suffers rare, forecastable, severe crashes in "panic" states — after market declines, in high volatility, during rebounds (14 of 15 worst months followed 2-yr negative markets with a positive contemporaneous market). This is the *price of admission* that plausibly keeps the premium from being arbitraged away — a limits-to-arbitrage/risk hybrid.
- **The Japan exception:** momentum is famously **weak/absent in Japan** (Asness 2011). **Chui, Titman & Wei (2010, *Individualism and Momentum Around the World*)** tie momentum strength to Hofstede **individualism** (a proxy for overconfidence/self-attribution): low-individualism East Asian markets show little momentum — direct cross-cultural support for the *behavioral* mechanism. (Asness et al. note Japan value + momentum *together* still work — they're negatively correlated.)
- **Disappears if:** transaction costs rise enough to eat it; or crash risk is fully hedged and the premium then evaporates (would prove it was crash compensation).
- **Falsified by:** a clean risk factor fully explaining UMD with no residual alpha; or disappearance in a broad post-publication OOS sample without a cost/crash explanation.
- **Agree / disagree / weak:** **Agree:** momentum is real, large, global-on-average, and behavioral in origin; skip-a-month and crash risk are established. **Disagree:** underreaction vs. delayed-overreaction; how much crash risk "justifies" the premium. **Genuinely weak:** *net-of-cost* survival at scale (high turnover); why it persisted so long post-publication; the Japan case (individualism is one story among several).
- **Citations:** Jegadeesh & Titman (1993) *Returns to Buying Winners and Selling Losers*; Carhart (1997); Hong & Stein (1999); Daniel & Moskowitz (2016) *Momentum Crashes*; Chui, Titman & Wei (2010).

---

## 5. PROFITABILITY / QUALITY — "buy good companies," and the mechanism embarrassment

- **Core claim:** More profitable / higher-quality firms (profitable, growing, safe, high payout) out-earn junk — *even holding valuation constant* (Novy-Marx's "other side of value").
- **Mechanism — genuinely contested, and this is the school where the mechanism is *weakest*:**
  - **Risk / q-theory:** In FF5, RMW (robust-minus-weak profitability) and CMA are risk factors; the investment-CAPM rationalizes them — high profitability with low investment implies high discount rate. This is the cleanest theoretical leg quality has.
  - **Mispricing / free-lunch problem (Asness, Frazzini & Pedersen 2019, *Quality Minus Junk*):** high-quality stocks *should* command higher prices; the market only **partially** prices quality, so a QMJ long-short earns positive alpha in 23/24 countries. Crucially, **QMJ pays off *in* downturns** (negative market beta, high returns in crises) — which is the *opposite* of a risk premium. A factor that makes money when the world is scary is very hard to call "compensation for risk."
- **Durable if known?** This is the tension: if quality earns alpha *and* hedges crashes, it looks like a **partially-corrected mispricing / free lunch**, which "should" decay once known — yet it is a slow-moving, cheap-to-hold characteristic, so arbitrage is limited and it persists.
- **OOS / international / survival:** Gross profitability (Novy-Marx 2013) replicates broadly and was one of the *drivers* of FF adding RMW. QMJ is positive in 23/24 countries. Quality is among the **better-surviving** factors in the replication crisis.
- **Disappears if:** it is subsumed by a better-specified profitability/investment factor (much of "quality" is RMW+CMA re-labeled); or if the crisis-hedging property reverses.
- **Falsified by:** quality earning nothing after controlling for profitability+investment+value (i.e., no independent content) — a live possibility since "quality" is a *composite* whose definition varies by author.
- **Agree / disagree / weak:** **Agree:** profitability/quality predicts returns and improves other factors (especially rescuing size — Section 6). **Disagree:** risk vs. mispricing (the crisis-positive payoff makes risk hard to defend); whether "quality" is one thing or a grab-bag. **Genuinely weak — the weakest mechanism story in the whole map:** *why* a defensive, crisis-hedging, high-quality stock should be *underpriced* at all; and the definitional instability of "quality."
- **Citations:** Novy-Marx (2013) *The Other Side of Value: The Gross Profitability Premium*; Fama & French (2015); Asness, Frazzini & Pedersen (2019) *Quality Minus Junk*.

---

## 6. SIZE — the premium that mostly wasn't (until you control for junk)

- **Core claim:** Small-cap stocks out-earn large-caps (Banz 1981).
- **Mechanism:** Originally floated as risk (illiquidity, distress, limited diversification). In practice the *cleanest* modern story is a **conditioning artifact**: raw size is confounded by junk.
- **Durable if known?** The *raw* premium largely **decayed / was never robust** — weak record, concentrated in microcaps and January, fragile internationally, weakened after Banz. A textbook candidate for "published, then gone."
- **OOS / international / survival:** **Asness, Frazzini, Israel, Moskowitz & Pedersen (2018, *Size Matters, If You Control Your Junk*):** the size premium is weak *because small caps are disproportionately junk*; **control for quality (QMJ) and a stable, robust size premium re-emerges** — not concentrated in microcaps, consistent across seasons, present in 30 industries and 24 countries, and for non-price size measures. So size is best understood as **real but only visible net of a quality control**.
- **Disappears if:** you don't control for quality (then it's marginal); or if the "resurrection" is itself a product of the specific QMJ construction.
- **Falsified by:** quality-controlled size failing to replicate in fresh OOS data, or being an artifact of the hedge construction.
- **Agree / disagree / weak:** **Agree:** the *raw* standalone size premium is weak/decayed and microcap-driven — a poster child for the replication crisis. **Disagree:** whether the junk-controlled premium is a genuine independent effect or a byproduct of how you build the quality hedge. **Genuinely weak:** any *risk* mechanism for size that survives the quality control.
- **Citations:** Banz (1981) *The Relationship Between Return and Market Value of Common Stocks*; Fama & French (1992); Asness, Frazzini, Israel, Moskowitz & Pedersen (2018).

---

## 7. LOW-VOLATILITY / BETTING-AGAINST-BETA — the structural story with the best "survives being known" case

- **Core claim:** Low-beta / low-volatility stocks earn **higher risk-adjusted** returns than high-beta/high-vol stocks — the SML is too flat (Section 0), and low-risk wins.
- **Mechanism — two structural/behavioral legs, both about *why it isn't arbitraged*:**
  - **Leverage constraints (Frazzini & Pedersen 2014, *Betting Against Beta*):** investors who *want* more return but *can't use leverage* (many funds, individuals) instead **overweight high-beta stocks**, bidding them up (low future return) and leaving low-beta underpriced. BAB = leveraged-low-beta minus de-leveraged-high-beta; positive risk-adjusted returns in US equities, **20 international markets**, Treasuries, credit, and futures. The premium's size scales with the *tightness of funding constraints*.
  - **Benchmarking + lottery preferences (Baker, Bradley & Wurgler 2011, *Benchmarks as Limits to Arbitrage*):** (a) delegated managers are paid on **information ratio vs. a fixed benchmark without leverage**, which *discourages* them from arbitraging overpriced high-beta stocks (doing so raises tracking error); (b) investors have a **lottery preference** for volatile stocks. Both keep the anomaly alive.
- **Durable if known?** **Best-in-class durability argument in this document.** The mechanism is *structural* — leverage aversion and benchmark mandates are institutional facts that publication does not remove. Knowing about BAB doesn't give a pension fund permission to lever, so the constraint persists. This is exactly the "survives being known because it's a structural friction / risk-management fact" property.
- **OOS / international / survival:** Broad international and cross-asset replication (FP 2014). Among the more robust anomalies, though critics (Novy-Marx & Velikov) argue BAB's construction (beta-rank weighting, near-zero-cost leverage assumptions, microcaps) inflates it — net-of-cost and construction-robustness are the live debate.
- **Disappears if:** leverage becomes cheap and universally accessible (constraints relax), or benchmarking mandates vanish — then the bid for high-beta disappears and the SML steepens.
- **Falsified by:** the premium surviving in a world of relaxed leverage constraints (would kill the FP mechanism), or vanishing entirely under conservative construction/costs (would make it a construction artifact).
- **Agree / disagree / weak:** **Agree:** the flat/inverted risk-return line in equities is real and international; leverage-constraint + benchmarking mechanisms are theoretically clean and *durable*. **Disagree:** the *magnitude* after realistic implementation (Novy-Marx-Velikov critique of BAB construction). **Genuinely weak:** the exact split between leverage-constraint vs. lottery-preference vs. plain low-vol; and net-of-cost scalability.
- **Citations:** Black, Jensen & Scholes (1972); Frazzini & Pedersen (2014) *Betting Against Beta*; Baker, Bradley & Wurgler (2011) *Benchmarks as Limits to Arbitrage*; Ang, Hodrick, Xing & Zhang (2006) *The Cross-Section of Volatility and Expected Returns*.

---

## 8. BEHAVIORAL FINANCE & LIMITS TO ARBITRAGE — the framework, not a single factor

- **Core claim:** Prices deviate from value because (a) investors are systematically biased and (b) **arbitrage is limited**, so smart money cannot fully correct the deviation. Mispricing is the source, limits-to-arbitrage is why it persists.
- **Mechanism:** **Behavioral × structural.** The load-bearing idea is **Shleifer & Vishny (1997), *The Limits of Arbitrage*:** real arbitrageurs run others' money, face **capital withdrawals precisely when mispricing widens** (performance-based arbitrage), so they can't hold through pain — mispricings survive. This is *the* reason any behavioral premium can persist post-publication.
- **How it shows up in the cross-section:**
  - **Stambaugh & Yuan (2017), *Mispricing Factors*:** aggregate 11 anomalies into two clusters — **MGMT** (management/investment-style) and **PERF** (performance/profitability-style) — as explicit **mispricing factors**; a 4-factor model (market, size, MGMT, PERF) beats FF-style models on a wide anomaly set. The framing is openly *mispricing*, not risk.
  - **Sentiment (Baker & Wurgler 2006, *Investor Sentiment and the Cross-Section of Stock Returns*):** when sentiment is high, hard-to-value / hard-to-arbitrage stocks (small, young, volatile, unprofitable, distressed, extreme-growth) subsequently **underperform**; low sentiment → they outperform. Sentiment interacts with limits to arbitrage exactly as predicted.
  - **Short-leg concentration (Stambaugh, Yu & Yuan 2012):** anomalies live disproportionately in the **short leg** (overpriced, hard-to-short stocks) — consistent with short-sale constraints as the binding limit to arbitrage.
- **Durable if known?** **Persists only as long as the limits do.** This school explicitly *predicts* decay where arbitrage is easy (McLean-Pontiff's cheaper-to-arbitrage predictors decay more) and persistence where it is hard (short-sale-constrained short legs, sentiment-sensitive stocks). That conditional prediction is its strongest empirical calling card.
- **OOS / international / survival:** Sentiment effects and short-leg concentration replicate; mispricing factors are competitive OOS. But this school is *also* the one most exposed to the replication crisis (many "mispricings" are the zoo).
- **Disappears if:** arbitrage capital becomes deep, patient, and unconstrained (cheap shorting, permanent capital) — then mispricings close.
- **Falsified by:** mispricing being *unrelated* to arbitrage costs / sentiment / short constraints (if the "hard-to-arb" stocks showed *no* extra mispricing, the framework fails). To date the correlation holds up.
- **Agree / disagree / weak:** **Agree:** limits to arbitrage are real and are the correct lens for *why* mispricings persist; sentiment and short-leg effects are robust. **Disagree with the risk camp** over whether value/quality/momentum are risk or mispricing (unresolved). **Genuinely weak:** cleanly separating "behavioral mispricing" from "unmodeled risk" — both predict cross-sectional return spreads; distinguishing them requires the bad-state / sentiment / arbitrage-cost conditioning that is itself contested.
- **Citations:** Shleifer & Vishny (1997) *The Limits of Arbitrage*; Stambaugh, Yu & Yuan (2012) *The Short of It*; Stambaugh & Yuan (2017) *Mispricing Factors*; Baker & Wurgler (2006).

---

## 9. THE META-DEBATE — risk vs. behavioral vs. data-mining, and "which premia survive being known"

This is the synthesis the whole map is built to serve.

**The three-way contest:**
- **Risk-based (Fama-French, Zhang/q):** spreads are equilibrium compensation for systematic risk. *Prediction:* premia **persist** post-publication; should co-move with bad states. *Weakness:* the bad state is rarely identified; HML redundancy; quality pays off *in* crises (anti-risk).
- **Behavioral + limits-to-arbitrage (Shleifer, LSV, Baker-Wurgler, Stambaugh-Yuan):** spreads are mistakes that survive only where arbitrage is limited. *Prediction:* premia **decay where arbitrage is easy, persist where it's hard**; concentrate in short legs / hard-to-value / high-sentiment names. *Weakness:* hard to distinguish from unmodeled risk; exposed to the zoo.
- **Data-mining (Harvey-Liu-Zhu, Hou-Xue-Zhang):** much of the zoo is noise. *Prediction:* premia **decay toward zero OOS**, fail raised t-hurdles, are microcap-driven. *Counter (Chen-Zimmermann):* ~98% replicate; decay is real but partial, not total.

**The unifying test — "does it survive being KNOWN?" (directly relevant to the project's mechanism gate):**
- A **true risk premium** survives publication *because knowing about it doesn't make you willing to bear the risk* → BAB (leverage constraints are institutional and permanent), value-as-distress-risk *if* real.
- A **behavioral premium survives only if arbitrage stays limited** → momentum (turnover + crash risk), short-leg anomalies (short-sale constraints), sentiment-driven mispricing.
- A **data-mined pattern does not survive at all** → the ~26-58% McLean-Pontiff decay is the measured "being-known" tax; the fraction that goes to *zero* is the mining component.
- **Practical corollary the evidence supports:** the premia with the best "survives being known" case are the ones with a **structural friction** (BAB/leverage, benchmarking) or a **durable statistical/risk fact** (momentum crash risk, value revaluation) — *not* the ones justified only by "it's in the literature and it backtests." Novelty and in-sample fit are precisely what McLean-Pontiff and Harvey-Liu-Zhu show decays.

**Where the profession genuinely agrees:**
- CAPM is empirically inadequate; a few characteristics carry most cross-sectional variation.
- t > 2 is too weak; microcap/equal-weight results are suspect; **post-publication decay is real** (direction uncontested).
- Value, momentum, profitability/quality, and low-beta/BAB are the **"survivor" factors** most likely to be real (they clear the raised bars best and replicate internationally).
- Limits to arbitrage is the correct explanation for *why* any mispricing persists.

**Where it genuinely disagrees:**
- Risk vs. behavioral for *every* surviving factor (30+ years unresolved for value).
- How much of the zoo is real: Hou-Xue-Zhang (~65% fail) vs. Chen-Zimmermann (~98% replicate) — a live, methodology-driven split.
- FF5 vs. q vs. mispricing factors as *the* model.
- Whether value's 2007-2020 stretch is death or a (now-cheap) drawdown.

**Where evidence is genuinely WEAK (be honest about these):**
- **Mechanism identification for risk stories** — no one has cleanly named the bad state HML/RMW hedge. Quality's crisis-*positive* payoff actively contradicts a risk story.
- **Net-of-cost, at-scale survival** — most survivors shrink dramatically after realistic costs/turnover (momentum, BAB construction, microcaps).
- **Separating risk from mispricing empirically** — both predict return spreads; the discriminating tests (bad-state covariance, sentiment/arbitrage-cost conditioning) are contested.
- **The correct multiple-testing hurdle** — t = 3.0 is a defensible modeling choice, not a fact.

**Citations (synthesis):** Asness, Moskowitz & Pedersen (2013) *Value and Momentum Everywhere*; Harvey, Liu & Zhu (2016); Hou, Xue & Zhang (2020); McLean & Pontiff (2016); Chen & Zimmermann (2022); Shleifer & Vishny (1997).

---

## Appendix — one-line mechanism verdicts (skim table)

| School | Mechanism | Survives being known? | Strongest evidence | Weakest link |
|---|---|---|---|---|
| CAPM/beta | risk (single) | it's the null; fails as a model | flat SML is robust | doesn't predict returns |
| FF/q multifactor | risk (claimed) | yes *if* truly risk | international replication | unidentified risk state; HML redundant |
| Factor zoo/replication | (meta) | — | McLean-Pontiff decay; HXZ 65% fail | correct t-hurdle unknown; HXZ vs CZ split |
| Value | risk **or** behavioral | debated | long history; cheap now | no bad-state ID; intangibles fix is post-hoc |
| Momentum | behavioral (+ crash risk) | yes, via limits-to-arb + crashes | global-on-avg; Japan/individualism | net-of-cost; why it persisted |
| Quality/profitability | risk **or** mispricing | persists (slow-moving) | Novy-Marx, QMJ 23/24 countries | **crisis-positive payoff kills risk story** |
| Size | (weak) risk / conditioning | only net of junk | AFIMP quality-control resurrection | no standalone mechanism |
| Low-vol / BAB | **structural (leverage/benchmark)** | **best case — yes** | 20 markets, cross-asset; institutional friction | construction/cost critique |
| Behavioral / limits-to-arb | behavioral × structural | only while limits hold | sentiment, short-leg concentration | risk-vs-mispricing not separable |

*End of map.*
