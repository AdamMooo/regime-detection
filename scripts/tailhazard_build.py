"""Tail-hazard MVE — Layer 1 build (FROZEN prereg: .planning/CONTINUOUS-JUMP-STATE-DECISION.md §8).

Causal GJR-GARCH(1,1)-t on ^GSPC daily log returns with expanding annual refits:
parameters fit on data through year-end Y filter sigma_{t|t-1} for days in year Y+1
(recursion run over the full history under year-Y params — no future data enters any
sigma_hat; full-sample fitting would leak the future through the parameters, CR-04 class).
Events e_t = 1{z_t < -2.0} from 1960-01. Covariates are all trailing (info <= t).

Outputs:
  data/processed/tailhazard_daily.csv       — per-day panel (sigma, z, events, covariates)
  results/tailhazard_garch_params.csv       — per refit-year GJR params (reproducibility)
  results/tailhazard_construction_gate.csv  — construction sanity report

Run: .venv/Scripts/python scripts/tailhazard_build.py
"""

import warnings

import numpy as np
import pandas as pd
import yfinance as yf
from arch import arch_model

START = "1950-01-01"
FIRST_EVENT_YEAR = 1960  # frozen: 1950-59 is the initial estimation window
C_PRIMARY = 2.0          # frozen threshold
C_ROBUST = 2.5

OUT_PANEL = "data/processed/tailhazard_daily.csv"
OUT_PARAMS = "results/tailhazard_garch_params.csv"
OUT_GATE = "results/tailhazard_construction_gate.csv"

# episodes for the construction check (must each contain >= 1 primary event)
EPISODES = {
    "1962 (Kennedy slide)": ("1962-04-01", "1962-12-31"),
    "1974 (oil/bear)": ("1974-01-01", "1974-12-31"),
    "1987 (Black Monday)": ("1987-10-01", "1987-12-31"),
    "1998 (LTCM/Russia)": ("1998-08-01", "1998-10-31"),
    "2000-02 (dot-com)": ("2000-03-01", "2002-12-31"),
    "2008-09 (GFC)": ("2008-09-01", "2009-03-31"),
    "2011 (US downgrade)": ("2011-08-01", "2011-10-31"),
    "2015 (China deval)": ("2015-08-01", "2015-09-30"),
    "2018 (Volmageddon/Q4)": ("2018-02-01", "2018-12-31"),
    "2020 (COVID)": ("2020-02-15", "2020-04-30"),
    "2022 (inflation bear)": ("2022-01-01", "2022-12-31"),
}


def fetch_returns():
    px = yf.download("^GSPC", start=START, progress=False, auto_adjust=True)
    close = px["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    ret = 100.0 * np.log(close / close.shift(1))  # percent log returns
    return ret.dropna()


def filter_gjr(r, mu, omega, alpha, gamma, beta):
    """sigma2[t] = conditional variance of day t given info <= t-1, under fixed params.

    Initialized at the params-implied unconditional variance; with a decade-plus of
    burn-in before any sigma is consumed, initialization is immaterial.
    """
    eps = r - mu
    n = len(r)
    s2 = np.empty(n)
    denom = 1.0 - alpha - 0.5 * gamma - beta
    s2[0] = omega / denom if denom > 1e-6 else np.var(eps)
    for t in range(1, n):
        e = eps[t - 1]
        s2[t] = omega + (alpha + gamma * (e < 0)) * e * e + beta * s2[t - 1]
    return s2, eps


def causal_sigma(ret):
    """Expanding annual refits: params through year-end Y apply to days in year Y+1."""
    r = ret.values
    years = ret.index.year
    sigma = np.full(len(ret), np.nan)
    eps_out = np.full(len(ret), np.nan)
    rows = []
    last_year = int(years.max())
    for Y in range(FIRST_EVENT_YEAR - 1, last_year):
        train = ret[ret.index <= f"{Y}-12-31"]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            am = arch_model(train, mean="Constant", vol="GARCH", p=1, o=1, q=1, dist="t")
            res = am.fit(disp="off")
        p = res.params
        mu, omega = p["mu"], p["omega"]
        alpha, gamma, beta = p["alpha[1]"], p["gamma[1]"], p["beta[1]"]
        nu = p["nu"]
        s2, eps = filter_gjr(r, mu, omega, alpha, gamma, beta)
        mask = years == Y + 1
        sigma[mask] = np.sqrt(s2[mask])
        eps_out[mask] = eps[mask]
        rows.append({"fit_through": Y, "applied_year": Y + 1, "n_train": len(train),
                     "mu": mu, "omega": omega, "alpha": alpha, "gamma": gamma,
                     "beta": beta, "nu": nu, "converged": res.convergence_flag == 0})
    return sigma, eps_out, pd.DataFrame(rows)


def build_covariates(ret):
    """All trailing / inclusive of t — information <= t (predictors for t+1)."""
    r = ret
    r_neg = (-r).clip(lower=0.0)
    r2 = r ** 2
    rv21 = np.sqrt(r2.rolling(21).mean())
    rv63 = np.sqrt(r2.rolling(63).mean())
    rs_neg21 = (r2 * (r < 0)).rolling(21).sum()
    return pd.DataFrame({
        "ret": r,
        "log_rv21": np.log(rv21),
        "log_rv63": np.log(rv63),
        "r_neg_1d": r_neg,
        "r_neg_5d": r_neg.rolling(5).sum(),
        "r_neg_21d": r_neg.rolling(21).sum(),
        "rs_share_21d": rs_neg21 / r2.rolling(21).sum(),
        "down_days_21d": (r < 0).rolling(21).sum(),
    })


def main():
    ret = fetch_returns()
    print(f"^GSPC daily log returns: {len(ret)} days, {ret.index[0].date()} -> {ret.index[-1].date()}")

    sigma, eps, params = causal_sigma(ret)
    print(f"GJR refits: {len(params)} ({int(params['converged'].sum())} converged)")

    panel = build_covariates(ret)
    panel["sigma"] = sigma
    panel["log_sigma"] = np.log(sigma)
    panel["z"] = eps / sigma
    panel["event"] = (panel["z"] < -C_PRIMARY).astype(float).where(panel["z"].notna())
    panel["event_c25"] = (panel["z"] < -C_ROBUST).astype(float).where(panel["z"].notna())
    panel["event_2s"] = (panel["z"].abs() > C_PRIMARY).astype(float).where(panel["z"].notna())

    vix = yf.download("^VIX", start="1990-01-01", progress=False, auto_adjust=True)["Close"]
    if isinstance(vix, pd.DataFrame):
        vix = vix.iloc[:, 0]
    panel["vix"] = vix.reindex(panel.index)

    panel.to_csv(OUT_PANEL, index_label="date")
    params.to_csv(OUT_PARAMS, index=False)

    # ---- construction sanity (report-only; hypothesis-relevant statistics deliberately
    # deferred to the stage script — nothing here touches clustering or prediction) ----
    el = panel[panel["z"].notna()]
    n, n_ev = len(el), int(el["event"].sum())
    rate = 100 * n_ev / n
    checks = [
        ("event_eligible_days", n, ""),
        ("first_event_day", str(el.index[0].date()), "expect 1960-01"),
        ("n_events_c2.0", n_ev, "expect ~420-580"),
        ("event_rate_pct", round(rate, 2), "expect 2.5-3.5 (t-innovations)"),
        ("n_events_c2.5", int(el["event_c25"].sum()), ""),
        ("n_events_two_sided", int(el["event_2s"].sum()), ""),
        ("nan_sigma_in_eligible", int(el["sigma"].isna().sum()), "must be 0"),
        ("min_sigma", round(float(el["sigma"].min()), 4), "must be > 0"),
    ]
    for decade in range(1960, 2030, 10):
        d = el[(el.index.year >= decade) & (el.index.year < decade + 10)]
        if len(d):
            checks.append((f"events_{decade}s", int(d["event"].sum()), ""))
    missed = []
    for name, (a, b) in EPISODES.items():
        hit = int(el.loc[a:b, "event"].sum())
        checks.append((f"episode: {name}", hit, ">=1"))
        if hit == 0:
            missed.append(name)
    checks.append(("episodes_missed", len(missed), "expect 0" + (f" — MISSED: {missed}" if missed else "")))

    worst = el.nsmallest(10, "z")[["z", "ret", "sigma"]]
    gate = pd.DataFrame(checks, columns=["check", "value", "expectation"])
    gate.to_csv(OUT_GATE, index=False)
    print("\n" + gate.to_string(index=False))
    print("\nTop-10 most negative z days:")
    print(worst.to_string())


if __name__ == "__main__":
    main()
