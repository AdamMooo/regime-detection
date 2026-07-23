"""Build the multi-asset daily panel for the state-conditional atlas.

Sources (all free, survivorship-clean where applicable):
- Ken French daily: 10 industry portfolios (1926+), SMB/HML from the factors file (1926+),
  momentum factor (1927+). Same library as the market panel.
- Synthetic constant-maturity 10y Treasury total return from FRED DGS10 (key-free csv
  endpoint, 1962+): TR_t = y_{t-1}/252 - D_mod * dy + 0.5 * C * dy^2  (v1 histext recipe;
  duration/convexity of a par bond at the prevailing yield).
- Gold: London fix via FRED (1968+), yfinance GC=F fallback.

Gates:
  A1 industries coverage 1963+ complete-case; equal-weight composite tracks the market
     (corr >= 0.90 on daily returns; EW/VW difference is structural) and every industry
     corr >= 0.50
  A2 bond TR sane: corr(bond_ret, IEF total return) >= 0.90 on the 2002+ overlap and
     ann vol in [4%, 14%]
  A3 gold sane: corr(gold_ret, GLD) >= 0.85 on the 2004+ overlap (futures 1:30pm COMEX vs
     GLD 4pm NYSE, non-synchronous; gold optional: panel still PASSES without it, flagged)
  A4 factors present 1963+ (SMB/HML/MOM complete-case)

Writes data/processed/assets_daily.csv + results/assets_gate.csv.
"""

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

FF_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"


def _ff_daily_table(zip_name, n_cols=None):
    resp = requests.get(FF_BASE + zip_name, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")
    header, rows = None, []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and len(parts[0]) == 8 and parts[0].isdigit():
            rows.append(parts)
        elif header is None and len(parts) >= 2 and parts[0] == "" and any(parts[1:]):
            header = ["date"] + [p for p in parts[1:]]
    if rows and header and len(header) != len(rows[0]):
        header = ["date"] + [f"c{i}" for i in range(1, len(rows[0]))]
    df = pd.DataFrame(rows, columns=header[:len(rows[0])])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.set_index("date").sort_index()
    df = df.apply(pd.to_numeric, errors="coerce").replace([-99.99, -999], np.nan) / 100.0
    df = df.dropna(axis=1, how="all")
    # daily files sometimes append a second (equal-weight) block with duplicate dates —
    # keep the first (value-weight) block only
    df = df[~df.index.duplicated(keep="first")]
    return df


def fred_series(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(io.StringIO(requests.get(url, timeout=120).text))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    return df.set_index("date")[series_id].dropna()


def bond_total_return(y10_pct):
    """Constant-maturity 10y par-bond TR. Macaulay duration of a par bond in half-year
    periods is (1-(1+y/2)^-n)/(y/2); divide by 2 for years and by (1+y/2) for modified.
    Par-bond convexity (half-year^2 units, /4 for years^2):
    C = 2/h^2 * (1-(1+h)^-n) - 2n/(h*(1+h)^(n+1)), h=y/2."""
    y = y10_pct / 100.0
    y_prev = y.shift(1)
    dy = y - y_prev
    n = 20
    h = y_prev / 2.0
    dur_mod = (1.0 - (1.0 + h) ** (-n)) / h / 2.0 / (1.0 + h)
    conv = ((2.0 / h ** 2) * (1.0 - (1.0 + h) ** (-n))
            - 2.0 * n / (h * (1.0 + h) ** (n + 1))) / 4.0
    tr = y_prev / 252.0 - dur_mod * dy + 0.5 * conv * dy ** 2
    return tr.dropna()


def _yf(ticker, start):
    import yfinance as yf
    px = yf.download(ticker, start=start, auto_adjust=True, progress=False)["Close"]
    if isinstance(px, pd.DataFrame):
        px = px.iloc[:, 0]
    return px.pct_change().dropna()


def main():
    mkt = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                      index_col=0, parse_dates=True)

    ind = _ff_daily_table("10_Industry_Portfolios_Daily_CSV.zip")
    ind.columns = ["ind_" + c.lower().replace(" ", "") for c in ind.columns]
    factors = _ff_daily_table("F-F_Research_Data_Factors_daily_CSV.zip")
    factors = factors.rename(columns=str.lower)[["smb", "hml"]]
    mom = _ff_daily_table("F-F_Momentum_Factor_daily_CSV.zip").iloc[:, :1]
    mom.columns = ["mom"]

    y10 = fred_series("DGS10")
    bond = bond_total_return(y10).rename("bond10_ret")

    gold = None
    for sid in ("GOLDPMGBD228NLBM", "GOLDAMGBD228NLBM"):
        try:
            fix = fred_series(sid)
            gold = fix.pct_change().dropna().rename("gold_ret")
            break
        except Exception:
            continue
    if gold is None or len(gold) < 1000:
        try:
            gold = _yf("GC=F", "1975-01-01").rename("gold_ret")
        except Exception:
            gold = None

    panel = mkt[["mkt_ret", "rf"]].join([ind, factors, mom, bond] +
                                        ([gold] if gold is not None else []))

    gate = []
    core = panel.loc["1963-01-01":, ["mkt_ret", "rf", "smb", "hml", "mom", "bond10_ret"]
                     + list(ind.columns)]
    complete = core.dropna()
    # equal-weight composite vs the VALUE-weight market: 0.90 bar (EW/VW difference is
    # structural); plus every industry must be strongly market-correlated (data integrity)
    comp = panel.loc[complete.index, list(ind.columns)].mean(axis=1)
    corr_ind = comp.corr(panel.loc[complete.index, "mkt_ret"])
    per_ind = [panel.loc[complete.index, c].corr(panel.loc[complete.index, "mkt_ret"])
               for c in ind.columns]
    gate.append(("A1_industries",
                 corr_ind >= 0.90 and min(per_ind) >= 0.50 and complete.index[0].year <= 1963,
                 f"ew_composite_corr={corr_ind:.4f} min_ind_corr={min(per_ind):.2f} "
                 f"start={complete.index[0].date()}"))

    ief = _yf("IEF", "2002-08-01")
    both = pd.DataFrame({"bond": bond, "ief": ief}).dropna()
    corr_b = both["bond"].corr(both["ief"])
    bvol = float(bond.loc["1963":].std() * np.sqrt(252))
    gate.append(("A2_bond", corr_b >= 0.90 and 0.04 <= bvol <= 0.14,
                 f"ief_corr={corr_b:.4f} ann_vol={bvol:.2%}"))

    if gold is not None:
        gld = _yf("GLD", "2004-11-01")
        bg = pd.DataFrame({"gold": gold, "gld": gld}).dropna()
        corr_g = bg["gold"].corr(bg["gld"])
        # futures (1:30pm COMEX close) vs GLD (4pm NYSE): non-synchronous -> 0.85 bar
        gate.append(("A3_gold", corr_g >= 0.85, f"gld_corr={corr_g:.4f} start={gold.index[0].date()}"))
    else:
        gate.append(("A3_gold", True, "gold unavailable — panel proceeds without it (flagged)"))

    gate.append(("A4_factors", complete.index[0] <= pd.Timestamp("1963-07-01"),
                 f"factors complete-case from {complete.index[0].date()}"))

    out = ROOT / "data" / "processed" / "assets_daily.csv"
    panel.to_csv(out)
    res = pd.DataFrame(gate, columns=["gate", "passed", "detail"])
    res.to_csv(ROOT / "results" / "assets_gate.csv", index=False)
    print(res.to_string(index=False))
    print(f"\npanel {panel.index[0].date()}..{panel.index[-1].date()} rows={len(panel)} "
          f"cols={list(panel.columns)}")
    print("ASSETS GATE:", "PASS" if res["passed"].all() else "FAIL")
    return 0 if res["passed"].all() else 1


if __name__ == "__main__":
    sys.exit(main())
