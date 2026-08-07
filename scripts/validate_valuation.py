"""Valuation signal — the registered one-look (charter V1-V6).

Charter: .planning/phases/03-valuation-signal/03-VALUATION-CHARTER.md (v1.1,
signed off 2026-08-07). ONE LOOK. Do not rerun to "refresh" — a second look is a
second look.

WHAT IS BEING ESTIMATED, and why the naive version of it is a trap
------------------------------------------------------------------
For horizon h (months) the predictive regression is

    y_t = a + b * x_t + e_{t+h},      y_t = sum_{j=1..h} log(1 + r_{t+j})

with x_t = log(CAPE_t) for the US and log(D/P_t) internationally. The
Campbell-Shiller (1988) identity says a high price relative to a smoothed
fundamental must be followed by LOW returns or HIGH dividend growth; b < 0 on
log CAPE (equivalently b > 0 on log D/P) is the risk-premium branch. The
signature of a SLOWLY mean-reverting discount rate is not any single b — it is
the PROFILE: |b| and R^2 rising with h, ~silent below a year.

Three separate things make the textbook standard error a lie here:

1. OVERLAP. Monthly observations of h-month forward returns share h-1 months of
   data, so e is MA(h-1) by construction. OLS SEs are far too small. Handled by
   Newey-West with lag h (the charter's registered method) AND by reporting the
   effective independent N = (T-h)/h, which is the number that actually governs.

2. STAMBAUGH (1999) BIAS. x is near-unit-root and its innovations correlate with
   return innovations, so

       E[b_hat - b] = (sigma_uv / sigma_v^2) * E[rho_hat - rho],
       E[rho_hat - rho] ~= -(1 + 3*rho)/T

   Both terms conspire to push b_hat AWAY from zero: the bias is
   anti-conservative — it manufactures the finding. Corrected in closed form at
   h = 1, where the formula is defined.

3. SPURIOUS LONG-HORIZON R^2. A persistent regressor against overlapping sums
   produces large R^2 with ZERO true predictability (Valkanov 2003;
   Boudoukh-Richardson-Whitelaw 2008).

All three are handled jointly by the BOOTSTRAP UNDER THE NULL (Nelson-Kim 1993):
fit x_{t+1} = c + rho*x_t + v_{t+1}, impose r_{t+1} = mu + u_{t+1} (no
predictability), BLOCK-resample the PAIRS (u, v) so the contemporaneous
correlation that drives the Stambaugh bias survives, rebuild synthetic paths,
re-run the same h-period regression, and read the observed statistic off that
null distribution. Registered as an addition that strengthens V6, disclosed here.

Run:  python scripts/validate_valuation.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import valuation
from valuation import CPI_PUBLICATION_LAG_M, EARNINGS_PUBLICATION_LAG_M

OUT = ROOT / "results" / "valuation_validation.txt"

HORIZONS_M = (1, 3, 12, 36, 60, 84, 120)
MIN_EFFECTIVE_N = 10          # charter V5a floor; below this a cell is "insufficient coverage"
N_BOOT = 2000
BLOCK_M = 12                  # block bootstrap block length, months
SEED = 20260807               # the charter's sign-off date; fixed so the look is reproducible

# Shiller's dividend comes from the same S&P quarterly aggregate as earnings, with
# the same monthly interpolation between endpoints, so it carries the same lag.
DIVIDEND_PUBLICATION_LAG_M = EARNINGS_PUBLICATION_LAG_M
# Z.1 Financial Accounts land ~2.5 months after quarter end; GDP earlier. One
# quarter is the first lag that uses only published figures for both legs.
CAPGDP_PUBLICATION_LAG_M = 3

INTL_REGIONS = ("europe_ex_uk", "europe", "uk", "scandinavia", "asia_pacific", "all")

lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    lines.append(s)


def rule(title: str) -> None:
    say("=" * 78)
    say(title)
    say("=" * 78)


# --------------------------------------------------------------------------
# data assembly
# --------------------------------------------------------------------------

def us_panel() -> pd.DataFrame:
    """US monthly frame: the three point-in-time valuation metrics and the three
    return objects (real total, excess over the short real rate, nominal)."""
    raw = valuation.load_panel()
    desc = valuation.build(raw)          # PIT CAPE, already causally guarded

    price, div, cpi = raw["price"], raw["dividend"], raw["cpi"]

    # monthly total return: Shiller's dividend is an ANNUALISED per-share rate, so
    # the month's cash is D/12
    tr = (price + div / 12.0) / price.shift(1) - 1.0
    infl = cpi / cpi.shift(1) - 1.0
    rf = (1.0 + raw["short_rate"]) ** (1.0 / 12.0) - 1.0

    out = pd.DataFrame({
        "cape": desc["cape"],
        # log D/P and log cap/GDP, both under their own publication lag
        "dp": np.log((div / price).shift(DIVIDEND_PUBLICATION_LAG_M)),
        "cap_gdp": np.log((raw["mktcap_nfc"] / raw["gdp"])
                          .shift(CAPGDP_PUBLICATION_LAG_M).ffill()),
        "r_real": np.log1p(tr) - np.log1p(infl),
        "r_excess": np.log1p(tr) - np.log1p(rf),
        "r_nominal": np.log1p(tr),
    })
    out["cape"] = np.log(out["cape"])
    return out.rename(columns={"cape": "log_cape"})


def intl_panel() -> pd.DataFrame:
    """International frame: log trailing D/P and log returns per region, local
    (primary — a market's own discount rate) and USD-real (secondary)."""
    m = pd.read_csv(ROOT / "data/processed/intl_valuation_monthly.csv",
                    parse_dates=["date"]).set_index("date")
    cpi = valuation.load_panel()["cpi"]
    us_infl = np.log1p(cpi / cpi.shift(1) - 1.0).reindex(m.index)

    out = {}
    for region in INTL_REGIONS:
        out[f"{region}__x_local"] = np.log(m[f"{region}_dp_local"])
        out[f"{region}__r_local"] = np.log1p(m[f"{region}_ret_local"])
        out[f"{region}__x_usd"] = np.log(m[f"{region}_dp_usd"])
        out[f"{region}__r_usd"] = np.log1p(m[f"{region}_ret_usd"]) - us_infl
    return pd.DataFrame(out)


def forward_sum(r: pd.Series, h: int) -> pd.Series:
    """y_t = sum of the NEXT h log returns. Deliberately forward-looking — it is
    the regressand. Nothing that feeds x_t may do this."""
    return r.shift(-1).rolling(h).sum().shift(-(h - 1))


# --------------------------------------------------------------------------
# the estimator + its three inference corrections
# --------------------------------------------------------------------------

def regress(x: pd.Series, y: pd.Series, h: int) -> dict | None:
    d = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if len(d) < 3 * h + 24:
        return None
    X = sm.add_constant(d["x"].values)
    ols = sm.OLS(d["y"].values, X).fit()
    nw = sm.OLS(d["y"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": h})
    return {
        "n": len(d), "eff_n": (len(d) - h) / h,
        "b": float(ols.params[1]), "r2": float(ols.rsquared),
        "t_ols": float(ols.tvalues[1]), "t_nw": float(nw.tvalues[1]),
        "_x": d["x"].values, "_y": d["y"].values,
    }


def stambaugh_correction(x: pd.Series, r1: pd.Series) -> dict:
    """Closed-form bias correction at h = 1, where the formula is defined.

        b_adj = b_hat - (sigma_uv / sigma_v^2) * (-(1 + 3*rho)/T)

    u = one-period return innovation, v = AR(1) innovation in the regressor.
    """
    d = pd.concat([x.rename("x"), r1.rename("r")], axis=1).dropna()
    xt, xl = d["x"].values[1:], d["x"].values[:-1]
    rt = d["r"].values[1:]
    T = len(xt)

    ar = sm.OLS(xt, sm.add_constant(xl)).fit()
    rho, v = float(ar.params[1]), ar.resid

    pred = sm.OLS(rt, sm.add_constant(xl)).fit()
    b_hat, u = float(pred.params[1]), pred.resid

    sigma_uv = float(np.cov(u, v)[0, 1])
    bias = (sigma_uv / float(np.var(v, ddof=1))) * (-(1.0 + 3.0 * rho) / T)
    return {"rho": rho, "b_hat": b_hat, "bias": bias, "b_adj": b_hat - bias,
            "corr_uv": float(np.corrcoef(u, v)[0, 1]), "T": T}


def bootstrap_null_p(x: pd.Series, r1: pd.Series, h: int, b_obs: float,
                     rng: np.random.Generator) -> float | None:
    """Nelson-Kim (1993). Simulate under NO predictability, preserving both the
    regressor's persistence and the (u, v) correlation that drives the Stambaugh
    bias, then ask how often the null reproduces a slope this extreme in the
    predicted direction."""
    d = pd.concat([x.rename("x"), r1.rename("r")], axis=1).dropna()
    if len(d) < 3 * h + 24:
        return None
    xv, rv = d["x"].values, d["r"].values
    T = len(xv)

    ar = sm.OLS(xv[1:], sm.add_constant(xv[:-1])).fit()
    c, rho, v = float(ar.params[0]), float(ar.params[1]), ar.resid
    mu, u = float(rv[1:].mean()), rv[1:] - rv[1:].mean()

    pairs = np.column_stack([u, v])
    n_pairs = len(pairs)
    n_blocks = int(np.ceil(T / BLOCK_M))
    hits = 0

    for _ in range(N_BOOT):
        starts = rng.integers(0, n_pairs - BLOCK_M, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + BLOCK_M) for s in starts])[:T]
        uu, vv = pairs[idx, 0], pairs[idx, 1]

        xs = np.empty(T)
        xs[0] = xv[0]
        for t in range(1, T):
            xs[t] = c + rho * xs[t - 1] + vv[t]
        rs = mu + uu

        ys = pd.Series(rs).shift(-1).rolling(h).sum().shift(-(h - 1)).values
        ok = ~np.isnan(ys)
        if ok.sum() < 24:
            continue
        fit = sm.OLS(ys[ok], sm.add_constant(xs[ok])).fit()
        b_sim = float(fit.params[1])
        if (b_sim <= b_obs) if b_obs < 0 else (b_sim >= b_obs):
            hits += 1

    return (hits + 1) / (N_BOOT + 1)


# --------------------------------------------------------------------------
# V5a — the power pre-check (runs FIRST, gates everything)
# --------------------------------------------------------------------------

def v5a_power(us: pd.DataFrame, intl: pd.DataFrame) -> dict[str, bool]:
    rule("[V5a] POWER PRE-CHECK (runs FIRST; gates every contrast below)")
    say(f"  bar: effective independent N = (T-h)/h must be >= {MIN_EFFECTIVE_N}, else the")
    say("       cell is INSUFFICIENT COVERAGE — not a weak finding, not refutation")
    say()
    say(f"  {'sample':16}{'months':>8}" + "".join(f"{h:>8}" for h in HORIZONS_M))
    powered = {}

    n_us = int(us[["log_cape", "r_real"]].dropna().shape[0])
    row = "".join(f"{(n_us - h) / h:>8.0f}" for h in HORIZONS_M)
    say(f"  {'US (CAPE)':16}{n_us:>8}{row}")
    powered["us"] = True

    for region in INTL_REGIONS:
        n = int(intl[[f"{region}__x_local", f"{region}__r_local"]].dropna().shape[0])
        row = "".join(f"{(n - h) / h:>8.0f}" for h in HORIZONS_M)
        say(f"  {region:16}{n:>8}{row}")
        powered[region] = (n - max(HORIZONS_M)) / max(HORIZONS_M) >= MIN_EFFECTIVE_N

    say()
    for name, ok in powered.items():
        if not ok:
            say(f"  ! {name}: 10y cell below the floor — the 120m column is NOT interpretable")
    say(f"  interpretable at 10y: {sorted(k for k, v in powered.items() if v)}")
    return powered


# --------------------------------------------------------------------------
# V1 / V2 / V6 — the US battery
# --------------------------------------------------------------------------

def horizon_table(x: pd.Series, r: pd.Series, label: str, rng, bootstrap: bool) -> dict:
    say(f"  {label}")
    say(f"    {'h (m)':>7}{'n':>7}{'eff N':>8}{'b':>10}{'R2':>8}"
        f"{'t OLS':>9}{'t NW':>9}{'boot p':>9}")
    res = {}
    for h in HORIZONS_M:
        out = regress(x, forward_sum(r, h), h)
        if out is None:
            say(f"    {h:>7}{'-':>7}{'-':>8}{'insufficient data':>36}")
            continue
        p = bootstrap_null_p(x, r, h, out["b"], rng) if bootstrap else None
        flag = "" if out["eff_n"] >= MIN_EFFECTIVE_N else "  <-- INSUFFICIENT COVERAGE"
        say(f"    {h:>7}{out['n']:>7}{out['eff_n']:>8.0f}{out['b']:>10.4f}{out['r2']:>8.3f}"
            f"{out['t_ols']:>9.2f}{out['t_nw']:>9.2f}"
            + (f"{p:>9.3f}" if p is not None else f"{'-':>9}") + flag)
        out["boot_p"] = p
        res[h] = out
    return res


def main() -> int:
    rng = np.random.default_rng(SEED)
    us, intl = us_panel(), intl_panel()

    rule("VALUATION — ONE-LOOK VALIDATION (charter v1.1, V1-V6)")
    say("assumption monitored: 'equities are priced for near-normal long-horizon returns'")
    say(f"clock: monthly | horizons (months): {list(HORIZONS_M)} | one look, spent")
    say()
    say("REGISTERED LIMITATIONS (all pre-look):")
    say("  - R5 (payout confound) is UNTESTABLE: no free net-buyback history exists.")
    say("  - The international leg is D/P not CAPE, Asia Pacific not Japan, and starts 1975.")
    say("  - V2 (excess returns) runs 1926+ (French RF start); V1/V3/V4 run 1881+.")
    say("  - Maturity ceiling is `research`. `production` is unavailable to this phase.")
    say(f"  - PIT lags: earnings {EARNINGS_PUBLICATION_LAG_M}m, dividends "
        f"{DIVIDEND_PUBLICATION_LAG_M}m, CPI {CPI_PUBLICATION_LAG_M}m, cap/GDP "
        f"{CAPGDP_PUBLICATION_LAG_M}m.")
    say()

    powered = v5a_power(us, intl)
    say()

    rule("[V1] HORIZON STRUCTURE — real total returns on log CAPE (US 1881-2026)")
    say("  bar: b < 0, with |b| and R2 RISING with horizon and ~silent sub-1yr.")
    say("  The PROFILE is the test; no single horizon is.")
    v1 = horizon_table(us["log_cape"], us["r_real"], "real total return", rng, bootstrap=True)
    say()

    rule("[V2] EXCESS RETURNS (PRIMARY DISCRIMINATOR) — over the short rate, US 1926-2026")
    say("  bar: the relationship survives on returns in excess of the short rate.")
    say("  Total real returns can fall as rates fall without any risk premium moving;")
    say("  excess returns are the clean risk-premium object. R1 trips here.")
    v2 = horizon_table(us["log_cape"], us["r_excess"], "excess over short rate", rng, bootstrap=True)
    say()

    rule("[V3] SUB-PERIOD STABILITY — including and EXCLUDING 1982-2021")
    say("  bar: the sign holds outside the secular rate-decline window. A relationship")
    say("  that exists only because of 1982-2021 is the rate regime, not reversion.")
    say(f"    {'sub-period':22}{'h (m)':>7}{'n':>7}{'eff N':>8}{'b':>10}{'R2':>8}{'t NW':>9}")
    periods = {
        "full 1881-2026": (None, None),
        "pre-1982": (None, "1981-12-31"),
        "1982-2021": ("1982-01-01", "2021-12-31"),
        "EXCL 1982-2021": ("excl", None),
    }
    v3 = {}
    for name, (a, b) in periods.items():
        for h in (60, 120):
            x, r = us["log_cape"], us["r_real"]
            if a == "excl":
                keep = (x.index < "1982-01-01") | (x.index > "2021-12-31")
                x = x[keep]
            else:
                x = x.loc[a:b]
            out = regress(x, forward_sum(r, h).reindex(x.index), h)
            if out is None:
                say(f"    {name:22}{h:>7}{'insufficient data':>32}")
                continue
            flag = "" if out["eff_n"] >= MIN_EFFECTIVE_N else "  <-- INSUFFICIENT COVERAGE"
            say(f"    {name:22}{h:>7}{out['n']:>7}{out['eff_n']:>8.0f}{out['b']:>10.4f}"
                f"{out['r2']:>8.3f}{out['t_nw']:>9.2f}{flag}")
            v3[(name, h)] = out
    say()

    rule("[V4] METRIC ROBUSTNESS — is the reading a CAPE artifact?")
    say("  bar: sign + horizon structure survive on the pre-committed panel, not CAPE alone.")
    say("  NOTE the registered hole: total-payout yield is UNAVAILABLE, so R5 (the payout")
    say("  confound) cannot be tested. P/D is kept precisely because it is the metric MOST")
    say("  exposed to that confound — the hole stays visible instead of hidden.")
    say()
    v4 = {}
    for metric, sign in (("log_cape", "-"), ("dp", "+"), ("cap_gdp", "-")):
        v4[metric] = horizon_table(us[metric], us["r_real"],
                                   f"{metric} (expect b {sign})", rng, bootstrap=False)
        say()

    rule("[V5] INTERNATIONAL OUT-OF-HYPOTHESIS SAMPLE — log D/P, 1975-2025")
    say("  bar: SIGN AND DIRECTION only (b > 0 on log D/P: cheap -> higher subsequent")
    say("  returns). Not a powered R2 claim. R8 trips ONLY on a sign reversal in a")
    say("  region the power pre-check declared interpretable.")
    say()
    v5 = {}
    for tag, what in (("local", "local currency, nominal (PRIMARY)"),
                      ("usd", "USD deflated by US CPI (secondary)")):
        say(f"  --- {what} ---")
        say(f"    {'region':16}" + "".join(f"{f'b@{h}m':>11}" for h in (12, 60, 120))
            + f"{'R2@120m':>10}{'eff N':>8}")
        for region in INTL_REGIONS:
            x = intl[f"{region}__x_{tag}"]
            r = intl[f"{region}__r_{tag}"]
            cells = {}
            for h in (12, 60, 120):
                cells[h] = regress(x, forward_sum(r, h), h)
            row = "".join(f"{cells[h]['b']:>11.4f}" if cells[h] else f"{'-':>11}"
                          for h in (12, 60, 120))
            last = cells[120]
            say(f"    {region:16}{row}"
                + (f"{last['r2']:>10.3f}{last['eff_n']:>8.0f}" if last else f"{'-':>10}{'-':>8}")
                + ("" if powered.get(region, False) else "  <-- INSUFFICIENT COVERAGE"))
            v5[(region, tag)] = cells
        say()

    rule("[V6] BIAS-AWARE INFERENCE — Stambaugh correction + the null distribution")
    say("  bar: predictability survives the persistent-regressor / overlapping-data")
    say("  corrections. Raw OLS long-horizon R2 is DESCRIPTIVE ONLY. R9 trips here.")
    say()
    for metric, robj, label in (("log_cape", "r_real", "log CAPE -> real return"),
                                ("log_cape", "r_excess", "log CAPE -> excess return")):
        s = stambaugh_correction(us[metric], us[robj])
        say(f"  {label}")
        say(f"    AR(1) persistence rho          {s['rho']:.4f}   (T = {s['T']} months)")
        say(f"    corr(return innov, x innov)    {s['corr_uv']:+.4f}")
        say(f"    b_hat (h = 1)                  {s['b_hat']:+.6f}")
        say(f"    Stambaugh bias                 {s['bias']:+.6f}")
        say(f"    b_adj = b_hat - bias           {s['b_adj']:+.6f}"
            f"   ({abs(s['bias'] / s['b_hat']) * 100:.1f}% of the raw slope)"
            if s["b_hat"] else "")
        say()
    say(f"  Bootstrap under the null: {N_BOOT} paths, block length {BLOCK_M}m, seed {SEED}.")
    say("  The 'boot p' column in V1/V2 is the share of no-predictability paths that")
    say("  reproduced a slope at least this extreme in the predicted direction.")
    say()

    rule("Read against the charter's V1-V6 bars and R1-R9 reject conditions.")
    say("Results sign-off is Adam's, dated, after overnight cooling-off.")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
