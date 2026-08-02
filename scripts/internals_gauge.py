"""Fragility gauge construction — frozen per INTERNALS-BETA-DIAL-PREREG.md REV 2, S3.

Generic over any industry/portfolio-return panel (US 48 French industries, or the
Japan/Europe 25-portfolio OOS panels) — same frozen formula, different input columns.
All causal: breadth/herf/disp use only trailing data; z-scoring uses an expanding
window through t (no full-sample z, no forward info).
"""

import numpy as np
import pandas as pd


def z_expand(x, min_periods=252):
    mean = x.expanding(min_periods=min_periods).mean()
    std = x.expanding(min_periods=min_periods).std()
    return (x - mean) / std.replace(0.0, np.nan)


def breadth(ind_ret, window=50):
    """Fraction of industries with price > own trailing window MA."""
    valid = ind_ret.notna()
    p = (1.0 + ind_ret.fillna(0.0)).cumprod()
    p = p.where(valid)
    ma = p.rolling(window, min_periods=window).mean()
    above = (p > ma) & valid
    denom = valid.sum(axis=1).where(valid.sum(axis=1) > 0)
    return above.sum(axis=1) / denom


def herf(ind_ret, window=20):
    """Herfindahl of |20d cumulative industry return| shares (leadership concentration)."""
    logp = np.log1p(ind_ret.fillna(0.0))
    cum = np.expm1(logp.rolling(window, min_periods=window).sum())
    cum = cum.where(ind_ret.notna())
    abscum = cum.abs()
    total = abscum.sum(axis=1)
    shares = abscum.div(total.where(total > 0), axis=0)
    return (shares ** 2).sum(axis=1)


def dispersion(ind_ret, window=20):
    """Cross-sectional stdev of daily industry returns, 20d mean. CONTROL ONLY (S3)."""
    cs_std = ind_ret.std(axis=1, skipna=True)
    return cs_std.rolling(window, min_periods=window).mean()


def build_internals(ind_ret, breadth_window=50, herf_window=20, disp_window=20,
                     min_industry_frac=0.90):
    """Return DataFrame with breadth, herf, disp, g — trimmed to first date with
    >= min_industry_frac industries present (S2, frozen)."""
    valid_frac = ind_ret.notna().sum(axis=1) / ind_ret.shape[1]
    start = valid_frac[valid_frac >= min_industry_frac].index.min()

    b = breadth(ind_ret, breadth_window)
    h = herf(ind_ret, herf_window)
    d = dispersion(ind_ret, disp_window)

    out = pd.DataFrame({"breadth": b, "herf": h, "disp": d})
    out = out.loc[out.index >= start]

    g = z_expand(-out["breadth"]) + z_expand(out["herf"])
    out["g"] = g
    return out.dropna()


def sigma_hat(mkt_ret, halflife=20):
    """EWM realized vol, annualized — same convention as backtest.vol_target_weights."""
    return mkt_ret.ewm(halflife=halflife).std() * np.sqrt(252)
