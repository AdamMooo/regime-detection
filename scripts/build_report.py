"""Generate results/report.html — self-contained visual report of the program's
one-look results (chapter 1: jump-model overlay; chapter 2: state-conditional ERC).

Reads: data/processed/market_daily.csv, results/oos_labels.csv, results/stage1.csv,
results/stage1_run.log (lambda path + LOTO parsed from the frozen one-look log), and —
when present — results/allocation_summary.csv / allocation_arms.csv /
allocation_controls.csv (the chapter-2 one-look artifacts).
Recomputes strategy paths with the exact frozen code (deterministic; not a new look).
Regenerate any time: .venv/Scripts/python scripts/build_report.py
"""

import ast
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from backtest import sharpe, sma_weights, vol_target_weights
from run_backtest import COST, DELAY, START, arm_returns, maxdd
from backtest import jm_weights


def build_data():
    panel = pd.read_csv(ROOT / "data" / "processed" / "market_daily.csv",
                        index_col=0, parse_dates=True).loc[START:]
    labels = pd.read_csv(ROOT / "results" / "oos_labels.csv", parse_dates=["date"])
    stats = pd.read_csv(ROOT / "results" / "stage1.csv").iloc[0]
    log = (ROOT / "results" / "stage1_run.log").read_text()

    lam_path = ast.literal_eval(re.search(r"lam_path=(\[[^\]]*\])", log).group(1))
    loto = ast.literal_eval(re.search(r"LOTO=(\{[^}]*\})", log).group(1))

    r = panel["mkt_ret"].to_numpy()
    rf = panel["rf"].to_numpy()
    idx = panel.index
    oos = idx.isin(labels["date"])
    s_o = labels["state"].to_numpy()
    idx_o = idx[oos]
    rf_o = rf[oos]

    w_jm_full = np.ones(len(r))
    w_jm_full[oos] = jm_weights(s_o)
    arms = {
        "JM": arm_returns(w_jm_full, r, rf, oos),
        "VT": arm_returns(vol_target_weights(r), r, rf, oos),
        "SMA200": arm_returns(sma_weights(r), r, rf, oos),
        "B&H": arm_returns(np.ones(len(r)), r, rf, oos, cost=0.0),
    }

    # weekly-thinned equity (log-scale chart) + drawdown
    keep = np.arange(len(idx_o)) % 5 == 0
    keep[-1] = True
    dates_w = [d.strftime("%Y-%m-%d") for d in idx_o[keep]]
    equity, drawdown = {}, {}
    for k, ret in arms.items():
        eq = np.cumprod(1.0 + ret)
        dd = eq / np.maximum.accumulate(eq) - 1.0
        equity[k] = [round(float(v), 4) for v in eq[keep]]
        drawdown[k] = [round(float(v) * 100, 2) for v in dd[keep]]

    # bear bands + episode table
    bands, episodes = [], []
    in_ep, start_i = False, 0
    calm_vol = float(np.std(arms["B&H"][s_o == 0]) * np.sqrt(252) * 100)
    for t in range(len(s_o) + 1):
        bear = t < len(s_o) and s_o[t] == 1
        if bear and not in_ep:
            in_ep, start_i = True, t
        elif not bear and in_ep:
            in_ep = False
            a, b = start_i, t - 1
            mkt = float(np.prod(1.0 + arms["B&H"][a:b + 1]) - 1.0)
            vol = float(np.std(arms["B&H"][a:b + 1]) * np.sqrt(252) * 100)
            episodes.append(dict(
                start=idx_o[a].strftime("%Y-%m-%d"), end=idx_o[b].strftime("%Y-%m-%d"),
                days=int(b - a + 1), mkt_ret=round(mkt * 100, 1), ann_vol=round(vol, 1)))
            bands.append([idx_o[a].strftime("%Y-%m-%d"), idx_o[b].strftime("%Y-%m-%d")])

    # per-arm summary + annual returns (table view / relief rule)
    arm_stats = {}
    for k, ret in arms.items():
        w_src = {"JM": w_jm_full, "VT": vol_target_weights(r),
                 "SMA200": sma_weights(r), "B&H": np.ones(len(r))}[k]
        w_exec = pd.Series(w_src).shift(DELAY).fillna(0).to_numpy()[oos]
        arm_stats[k] = dict(
            sharpe=round(sharpe(ret, rf_o), 3), maxdd=round(maxdd(ret) * 100, 1),
            ann_ret=round(float(np.mean(ret)) * 252 * 100, 2),
            avg_w=round(float(np.mean(w_exec)), 3),
            turnover_yr=round(float(np.abs(np.diff(w_exec)).sum() / len(ret) * 252), 2))
    years = sorted(set(d.year for d in idx_o))
    annual = []
    for y in years:
        m = idx_o.year == y
        row = {"year": int(y)}
        for k, ret in arms.items():
            row[k] = round((float(np.prod(1.0 + ret[m])) - 1.0) * 100, 1)
        annual.append(row)

    refit_years = list(range(idx_o[0].year, idx_o[0].year + len(lam_path)))

    live_state, live_since, live_date = None, None, None
    live_p = ROOT / "results" / "label_live.csv"
    if live_p.exists():
        lv = pd.read_csv(live_p, parse_dates=["date"])
        sl = lv["state"].to_numpy()
        sw = np.flatnonzero(sl[1:] != sl[:-1])
        live_state = "STRESSED" if sl[-1] == 1 else "CALM"
        live_since = str(lv["date"].iloc[sw[-1] + 1].date()) if len(sw) else str(lv["date"].iloc[0].date())
        live_date = str(lv["date"].iloc[-1].date())

    return dict(
        meta=dict(oos_start=str(idx_o[0].date()), oos_end=str(idx_o[-1].date()),
                  n=int(len(idx_o)), case=str(stats["case"]),
                  bear_frac=round(float((s_o == 1).mean()) * 100, 1),
                  switches_yr=round(float(stats["switches_yr"]), 2), calm_vol=round(calm_vol, 1),
                  delay=DELAY, cost=COST,
                  live_state=live_state, live_since=live_since, live_date=live_date),
        fees=dict(bh=round(float(stats["fee"]), 1), bh_lo=round(float(stats["ci_lo"]), 1),
                  bh_hi=round(float(stats["ci_hi"]), 1), vt=round(float(stats["fee_vt"]), 1),
                  vt_lo=round(float(stats["ci_vt_lo"]), 1), vt_hi=round(float(stats["ci_vt_hi"]), 1),
                  g1=round(float(stats["fee_g1"]), 1), sma=round(float(stats["fee_sma"]), 1),
                  mix=round(float(stats["fee_mix"]), 1), delay1=round(float(stats["fee_delay1"]), 1),
                  breakeven=round(float(stats["breakeven_bps"]), 1),
                  c1=round(float(stats["c1_bar"]), 1), c2=round(float(stats["c2_max"]), 1),
                  c3=round(float(stats["c3_max"]), 1),
                  c2_lo=41.4, c3_lo=178.7,
                  stab_p=float(stats["stab_start+2y"]), stab_m=float(stats["stab_start-2y"])),
        halves={"1990-2007": round(float(stats["half_1990_2007"]), 1),
                "2008-2026": round(float(stats["half_2008_2026"]), 1)},
        loto={k.replace("_", " "): v for k, v in loto.items()},
        dates=dates_w, equity=equity, drawdown=drawdown, bands=bands, episodes=episodes,
        arm_stats=arm_stats, annual=annual,
        lam=dict(years=refit_years, values=[float(v) for v in lam_path]),
    )


def build_alloc_data():
    p = ROOT / "results" / "allocation_summary.csv"
    if not p.exists():
        return None
    # keep_default_na: the verdict string "NULL" is on pandas' default NA list
    s = pd.read_csv(p, keep_default_na=False, na_values=[""]).iloc[0]
    arms = pd.read_csv(ROOT / "results" / "allocation_arms.csv", parse_dates=["date"])
    ctrl = pd.read_csv(ROOT / "results" / "allocation_controls.csv")

    keep = np.arange(len(arms)) % 5 == 0
    keep[-1] = True
    dates_w = arms["date"].dt.strftime("%Y-%m-%d")[keep].tolist()
    series_cols = {"Cond": "ret_cond", "B_match": "ret_match",
                   "B_react": "ret_react", "60/40": "ret_6040"}
    equity, drawdown = {}, {}
    for k, c in series_cols.items():
        eq = np.cumprod(1.0 + arms[c].to_numpy())
        dd = eq / np.maximum.accumulate(eq) - 1.0
        equity[k] = [round(float(v), 4) for v in eq[keep]]
        drawdown[k] = [round(float(v) * 100, 2) for v in dd[keep]]

    weights = {}
    for k, c in (("Equity", "w_cond_eq"), ("Bond", "w_cond_bd"),
                 ("Gold", "w_cond_au")):
        weights[k] = [round(float(v) * 100, 1) for v in arms[c].to_numpy()[keep]]
    cash = 1.0 - (arms["w_cond_eq"] + arms["w_cond_bd"] + arms["w_cond_au"])
    weights["Cash"] = [round(float(v) * 100, 1) for v in cash.to_numpy()[keep]]

    bands_ctl = {}
    for name, key in (("C1_placebo", "placebo"), ("C2_shuffle", "shuffle"),
                      ("C3_iid", "iid")):
        sub = ctrl[ctrl["control"] == name]
        bands_ctl[key] = dict(
            a_lo=round(float(sub["fee_a"].quantile(0.05)), 1),
            a_hi=round(float(sub["fee_a"].quantile(0.95)), 1),
            b_lo=round(float(sub["fee_b"].quantile(0.05)), 1),
            b_hi=round(float(sub["fee_b"].quantile(0.95)), 1), n=int(len(sub)))

    arm_stats = {}
    for nm, key in (("Cond", "cond"), ("B_match", "B_match"), ("B_react", "B_react"),
                    ("60/40", "60_40"), ("VT equity", "VT_eq"), ("B&H equity", "BH_eq")):
        arm_stats[nm] = dict(sharpe=round(float(s[f"{key}_sharpe"]), 3),
                             maxdd=round(float(s[f"{key}_maxdd"]) * 100, 1),
                             ann_ret=round(float(s[f"{key}_ann_ret"]) * 100, 2),
                             ann_vol=round(float(s[f"{key}_ann_vol"]) * 100, 2))

    years = sorted(set(arms["date"].dt.year))
    annual = []
    for y in years:
        m = arms["date"].dt.year == y
        row = {"year": int(y)}
        for k, c in series_cols.items():
            row[k] = round((float(np.prod(1.0 + arms.loc[m, c])) - 1.0) * 100, 1)
        annual.append(row)

    splits = {nm: [round(float(s[f"split_{key}_a"]), 1), round(float(s[f"split_{key}_b"]), 1)]
              for nm, key in (("1990–1999", "pre2000"), ("2000–2026", "post2000"),
                              ("excl. 2022 episode", "ex2022ep"),
                              ("from activation", "from_act"))}

    return dict(
        verdict=str(s["verdict"]), activation=str(s["activation"]),
        fees=dict(a=round(float(s["fee_a"]), 1), a_lo=round(float(s["ci_a_lo"]), 1),
                  a_hi=round(float(s["ci_a_hi"]), 1), b=round(float(s["fee_b"]), 1),
                  b_lo=round(float(s["ci_b_lo"]), 1), b_hi=round(float(s["ci_b_hi"]), 1),
                  a_g1=round(float(s["fee_a_g1"]), 1), b_g1=round(float(s["fee_b_g1"]), 1)),
        f=dict(f1=bool(s["f1"]), f1b=bool(s["f1b"]), f2=bool(s["f2"]), f3=bool(s["f3"]),
               clean=bool(s["controls_clean"])),
        volvol=dict(cond=round(float(s["volvol_cond"]) * 100, 2),
                    match=round(float(s["volvol_match"]) * 100, 2)),
        turnover=dict(cond=round(float(s["turnover_cond"]), 2),
                      match=round(float(s["turnover_match"]), 2),
                      react=round(float(s["turnover_react"]), 2)),
        dsr=[round(float(s["dsr_lo"]), 3), round(float(s["dsr_hi"]), 3)],
        dmaxdd=round(float(s["dmaxdd"]) * 100, 2),
        bands_ctl=bands_ctl, dates=dates_w, equity=equity, drawdown=drawdown,
        weights=weights, arm_stats=arm_stats, annual=annual, splits=splits)


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Regime Program — One-Look Results</title>
<style>
:root {
  color-scheme: light;
  --surface: #fcfcfb; --page: #f9f9f7;
  --ink: #0b0b0b; --ink2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100;
  --band: rgba(82,81,78,0.10); --neg: #d03b3b; --pos: #006300;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --surface: #1a1a19; --page: #0d0d0d;
    --ink: #ffffff; --ink2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
    --band: rgba(195,194,183,0.10); --neg: #e66767; --pos: #0ca30c;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
.wrap { max-width: 1080px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 24px; margin: 0 0 4px; }
h2 { font-size: 17px; margin: 40px 0 6px; }
.sub { color: var(--ink2); margin: 0 0 18px; }
.note { color: var(--ink2); font-size: 14px; max-width: 76ch; margin: 6px 0 12px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px; margin: 20px 0; }
.tile { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; }
.tile .v { font-size: 26px; font-weight: 650; letter-spacing: -0.01em; }
.tile .l { color: var(--ink2); font-size: 13px; margin-top: 2px; }
.tile .d { color: var(--muted); font-size: 12px; margin-top: 2px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px; margin: 10px 0; overflow-x: auto; }
svg { display: block; width: 100%; height: auto; }
svg text { font: 12px system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--muted);
  font-variant-numeric: tabular-nums; }
svg .dirlab { font-weight: 600; font-size: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 14px;
  font-variant-numeric: tabular-nums; }
th { text-align: left; color: var(--ink2); font-weight: 600; border-bottom: 1px solid var(--axis); }
th, td { padding: 6px 10px 6px 0; }
td { border-bottom: 1px solid var(--grid); }
td.num, th.num { text-align: right; }
.negv { color: var(--neg); } .posv { color: var(--pos); }
.tooltip { position: fixed; pointer-events: none; background: var(--surface);
  border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,.12);
  padding: 8px 10px; font-size: 13px; display: none; z-index: 10; min-width: 150px; }
.tooltip .tdate { color: var(--ink2); margin-bottom: 4px; }
.tooltip .row { display: flex; align-items: center; gap: 6px; }
.tooltip .key { width: 14px; height: 0; border-top: 3px solid; border-radius: 2px; }
.tooltip .val { font-weight: 650; font-variant-numeric: tabular-nums; }
.tooltip .nm { color: var(--ink2); }
.legend { display: flex; flex-wrap: wrap; gap: 14px; margin: 4px 0 8px; font-size: 13px;
  color: var(--ink2); align-items: center; }
.legend .key { width: 16px; height: 0; border-top: 3px solid; border-radius: 2px;
  display: inline-block; }
.legend .swatch { width: 14px; height: 14px; background: var(--band);
  border: 1px solid var(--grid); display: inline-block; border-radius: 3px; }
.legend span.item { display: inline-flex; gap: 6px; align-items: center; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); font-size: 14px; }
.footer { color: var(--muted); font-size: 13px; margin-top: 40px; border-top: 1px solid var(--grid);
  padding-top: 12px; }
</style>
</head>
<body>
<div class="wrap">
<h1>Regime Program — Living Results</h1>
<p class="sub" id="subtitle"></p>

<div class="tiles" id="tiles"></div>

<h2>Every claim, against its honest bar</h2>
<p class="note">One rule keeps this program honest: a claim counts only if it beats the best
<em>simple</em> alternative — not just buy-and-hold. Four claims tested under frozen
preregistration; the dot must sit right of zero with its whole whisker. None does.</p>
<div class="card"><div id="ladder"></div></div>

<h2>The sensor — the asset this program produced</h2>
<p class="note" id="sensornote"></p>
<div class="legend" id="eqlegend"></div>
<div class="card"><div id="equity"></div></div>
<details><summary>The 30 bear episodes it called</summary>
<p class="note" id="epnote"></p>
<div class="card"><table id="episodes"></table></div></details>
<details><summary>The speed/stability dial — &lambda; per refit</summary>
<p class="note">&lambda; = switch-resistance, re-chosen yearly by causal cross-validation.
Healthy: inside the grid, drifting faster in the modern era.</p>
<div class="card"><div id="lambda"></div></div></details>

<h1 id="ch1" style="font-size:20px;margin-top:44px">Chapter 1 — Trading the label · Case B</h1>
<p class="note"><strong>Plain English:</strong> the overlay's "beating the market" is just
holding less stock — random signals with the same average exposure score the same, and a cheap
vol-target rule beats it outright. Value = risk reduction, available cheaper elsewhere.</p>

<h2>The fee against its null bands</h2>
<p class="note">The fee = what a cautious investor (γ=10) would pay per year to switch. The dot
must clear the shaded bands (what fake signals score). It doesn't — and vs vol targeting it's
significantly negative.</p>
<div class="card"><div id="intervals"></div></div>

<details><summary>Drawdowns — where the overlay earns its keep (and VT matches it)</summary>
<p class="note">Max drawdown: JM &minus;27.5% vs buy-and-hold &minus;54.6% — but vol targeting
gets nearly identical protection.</p>
<div class="legend" id="ddlegend"></div>
<div class="card"><div id="drawdown"></div></div></details>

<details><summary>Robustness — era halves, leave-one-crisis-out</summary>
<p class="note">Positive in both halves and with any single crisis removed — an always-on
exposure effect, not one lucky call.</p>
<div class="card"><div id="robust"></div></div></details>

<details><summary>Strategy table + annual returns</summary>
<div class="card"><table id="arms"></table></div>
<div class="card"><table id="annual"></table></div></details>

<p class="footer" id="footer"></p>

<div id="ch2block" style="display:none">
<h1 id="ch2" style="font-size:20px;margin-top:44px">Chapter 2 — Feeding the label to an allocator · NULL</h1>
<p class="note"><strong>Plain English:</strong> telling the portfolio "we're in a storm" didn't
help — a simple estimator that just watches the last few weeks (EWMA) reacts faster and does
better. The cross-asset structure is real; being reactive already harvests it.</p>

<div class="tiles" id="ch2tiles"></div>

<h2>The map — risk taken vs return earned</h2>
<p class="note">Every arm is one dot. The dashed line is what cash or leverage does to the best
diversified arm — anything below it is beaten at equal risk. 60/40 and buy-and-hold earn more
only by taking more risk; per unit of risk they lose.</p>
<div class="card"><div id="ch2scatter"></div></div>

<h2>The two fees against their null bands</h2>
<p class="note">fee_A: does the label beat the same allocator on a slow "all history"
covariance? fee_B (the honest bar): does it beat a fast EWMA covariance? Shaded = what fake
labels score. fee_A sits inside the bands; fee_B is negative — the fast simple estimate wins.</p>
<div class="card"><div id="ch2intervals"></div></div>

<h2>What the conditional arm held</h2>
<p class="note">In stress the estimated risk rises, the 8% vol target binds, cash rises —
that's the whole mechanism, visible.</p>
<div class="legend" id="ch2wlegend"></div>
<div class="card"><div id="ch2weights"></div></div>

<details><summary>Equity curves of the arms + annual returns</summary>
<p class="note" id="ch2eqnote"></p>
<div class="legend" id="ch2eqlegend"></div>
<div class="card"><div id="ch2equity"></div></div>
<div class="card"><table id="ch2annual"></table></div></details>

<details><summary>Era splits + arm table</summary>
<p class="note">fee_A is ~0 in every era; fee_B: the EWMA wins big after 2000, and the 2022
inflation bear is the known worst case for bond-hedge assumptions.</p>
<div class="card"><table id="ch2splits"></table></div>
<div class="card"><table id="ch2arms"></table></div></details>

<p class="footer" id="ch2footer"></p>
</div>

<h2 style="margin-top:44px">What's next — the fork</h2>
<p class="note"><strong>1 · Write the paper (default).</strong> The 2024–25 jump-model
literature (Shu–Yu–Mulvey; Nystrup et al.) claims regime-aware allocation adds value — tested
against buy-and-hold-grade baselines. Two preregistered chapters here show the claims dissolve
against honest bars (exposure-matched placebos; reactive estimators). That negative result is
publishable and timely.</p>
<p class="note"><strong>2 · Chapter 3 only through the gate.</strong> Any new economic use must
name why it survives a lag race that VT and EWMA have now won twice. The one candidate with a
literature foothold: momentum at monthly cadence (Barroso–Santa-Clara vol-scaling is the strong
incumbent to beat; Cederburg et al. 2020 warn that even vol-scaling fails out-of-sample for
most factors — momentum is the exception).</p>
<p class="note"><strong>3 · Sensor track continues regardless.</strong> λ frontier, asymmetric
jump penalties, calibrated P(state) — instrument work, not allocation claims.</p>

<p class="footer" id="mainfooter"></p>
</div>
<div class="tooltip" id="tt"></div>
<script>
const DATA = __DATA__;
const CV = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const NS = "http://www.w3.org/2000/svg";
const el = (t, a) => { const e = document.createElementNS(NS, t);
  for (const k in a || {}) e.setAttribute(k, a[k]); return e; };
const div = (c, p) => { const e = document.createElement("div"); e.className = c || "";
  (p || document.body).appendChild(e); return e; };
const fmt = (v, d) => v.toLocaleString("en-US", {minimumFractionDigits: d ?? 0,
  maximumFractionDigits: d ?? 0});
const tt = document.getElementById("tt");
const SER = {"JM": "--s1", "VT": "--s2", "SMA200": "--s3", "B&H": "--s4"};

function showTT(x, y, html) { tt.style.display = "block"; tt.replaceChildren(...html);
  const r = tt.getBoundingClientRect();
  tt.style.left = Math.min(x + 14, innerWidth - r.width - 8) + "px";
  tt.style.top = Math.min(y + 14, innerHeight - r.height - 8) + "px"; }
function hideTT() { tt.style.display = "none"; }
function ttRows(dateStr, rows) {
  const out = [];
  const d = document.createElement("div"); d.className = "tdate"; d.textContent = dateStr;
  out.push(d);
  for (const r of rows) { const row = document.createElement("div"); row.className = "row";
    const k = document.createElement("span"); k.className = "key";
    k.style.borderTopColor = CV(r.colorVar); row.appendChild(k);
    const v = document.createElement("span"); v.className = "val"; v.textContent = r.value;
    row.appendChild(v);
    const n = document.createElement("span"); n.className = "nm"; n.textContent = r.name;
    row.appendChild(n); out.push(row); }
  return out; }

function lineChart(mount, cfg) {
  const W = 1040, H = cfg.height || 340, m = {t: 14, r: 92, b: 26, l: 52};
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": cfg.label || ""});
  mount.appendChild(svg);
  const dates = cfg.dates.map(d => new Date(d));
  const x0 = dates[0].getTime(), x1 = dates[dates.length - 1].getTime();
  const X = t => m.l + (t - x0) / (x1 - x0) * iw;
  let ymin = cfg.ymin, ymax = cfg.ymax;
  if (ymin == null) { ymin = Infinity; ymax = -Infinity;
    for (const s of cfg.series) for (const v of s.values) {
      if (v < ymin) ymin = v; if (v > ymax) ymax = v; } }
  const tf = cfg.logY ? Math.log10 : (v => v);
  const Y = v => m.t + ih - (tf(v) - tf(ymin)) / (tf(ymax) - tf(ymin)) * ih;
  // bear bands
  for (const [a, b] of (cfg.bands || [])) {
    const xa = X(new Date(a).getTime()), xb = X(new Date(b).getTime());
    svg.appendChild(el("rect", {x: xa, y: m.t, width: Math.max(xb - xa, 1.5), height: ih,
      fill: "var(--band)"})); }
  // y grid + ticks
  for (const v of cfg.yTicks) {
    const y = Y(v);
    svg.appendChild(el("line", {x1: m.l, x2: m.l + iw, y1: y, y2: y,
      stroke: "var(--grid)", "stroke-width": 1}));
    const t = el("text", {x: m.l - 8, y: y + 4, "text-anchor": "end"});
    t.textContent = cfg.yfmt(v); svg.appendChild(t); }
  // x ticks: years
  const yr0 = dates[0].getFullYear(), yr1 = dates[dates.length - 1].getFullYear();
  const step = (yr1 - yr0) > 12 ? 5 : 2;
  for (let y = Math.ceil(yr0 / step) * step; y <= yr1; y += step) {
    const xx = X(new Date(y + "-01-01").getTime());
    const t = el("text", {x: xx, y: H - 8, "text-anchor": "middle"});
    t.textContent = y; svg.appendChild(t); }
  svg.appendChild(el("line", {x1: m.l, x2: m.l + iw, y1: m.t + ih, y2: m.t + ih,
    stroke: "var(--axis)", "stroke-width": 1}));
  // series
  cfg.series.forEach(s => {
    let dstr = "";
    s.values.forEach((v, i) => {
      const px = X(dates[i].getTime()), py = Y(v);
      dstr += (i ? (cfg.stepped ? `H${px.toFixed(1)}V${py.toFixed(1)}` :
        `L${px.toFixed(1)} ${py.toFixed(1)}`) : `M${px.toFixed(1)} ${py.toFixed(1)}`); });
    svg.appendChild(el("path", {d: dstr, fill: "none", stroke: `var(${s.colorVar})`,
      "stroke-width": 2, "stroke-linejoin": "round"}));
    const last = s.values[s.values.length - 1];
    const lab = el("text", {x: m.l + iw + 6, y: Y(last) + 4, class: "dirlab",
      fill: `var(${s.colorVar})`});
    lab.textContent = s.name; lab.style.fill = `var(${s.colorVar})`; svg.appendChild(lab); });
  // crosshair + tooltip
  const cross = el("line", {y1: m.t, y2: m.t + ih, stroke: "var(--axis)",
    "stroke-width": 1, "stroke-dasharray": "3 3", visibility: "hidden"});
  svg.appendChild(cross);
  const hit = el("rect", {x: m.l, y: m.t, width: iw, height: ih, fill: "transparent"});
  svg.appendChild(hit);
  hit.addEventListener("pointermove", ev => {
    const box = svg.getBoundingClientRect();
    const frac = ((ev.clientX - box.left) / box.width * W - m.l) / iw;
    const t = x0 + Math.min(Math.max(frac, 0), 1) * (x1 - x0);
    let lo = 0, hi = dates.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1;
      (dates[mid].getTime() < t) ? lo = mid : hi = mid; }
    const i = (t - dates[lo].getTime() < dates[hi].getTime() - t) ? lo : hi;
    const px = X(dates[i].getTime());
    cross.setAttribute("x1", px); cross.setAttribute("x2", px);
    cross.setAttribute("visibility", "visible");
    showTT(ev.clientX, ev.clientY, ttRows(cfg.dates[i], cfg.series.map(s => ({
      colorVar: s.colorVar, name: s.name, value: cfg.yfmt(s.values[i]) })))); });
  hit.addEventListener("pointerleave", () => { hideTT();
    cross.setAttribute("visibility", "hidden"); });
}

function intervalChart(mount) {
  const F = DATA.fees;
  const W = 1040, H = 190, m = {l: 150, r: 30, t: 8, b: 30};
  const iw = W - m.l - m.r;
  const vmin = -600, vmax = 1250;
  const X = v => m.l + (v - vmin) / (vmax - vmin) * iw;
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Fee vs null bands"});
  mount.appendChild(svg);
  const bandY = m.t, bandH = H - m.t - m.b;
  // null bands
  const bands = [
    {a: F.c2_lo, b: F.c2, label: "surrogates"},
    {a: F.c3_lo, b: F.c3, label: "iid noise"}];
  bands.forEach((b, i) => {
    svg.appendChild(el("rect", {x: X(b.a), y: bandY, width: X(b.b) - X(b.a), height: bandH,
      fill: "var(--band)"}));
    const t = el("text", {x: X(b.b) - 4, y: bandY + 14 + i * 14, "text-anchor": "end"});
    t.textContent = `${b.label} band`; svg.appendChild(t); });
  // zero line
  svg.appendChild(el("line", {x1: X(0), x2: X(0), y1: bandY, y2: bandY + bandH,
    stroke: "var(--axis)", "stroke-width": 1}));
  // placebo 95th
  svg.appendChild(el("line", {x1: X(F.c1), x2: X(F.c1), y1: bandY, y2: bandY + bandH,
    stroke: "var(--muted)", "stroke-width": 1.5, "stroke-dasharray": "5 4"}));
  const pl = el("text", {x: X(F.c1) + 4, y: bandY + 12});
  pl.textContent = "placebo 95th"; svg.appendChild(pl);
  // axis ticks
  for (const v of [-500, 0, 500, 1000]) {
    const t = el("text", {x: X(v), y: H - 8, "text-anchor": "middle"});
    t.textContent = fmt(v); svg.appendChild(t); }
  const axl = el("text", {x: m.l + iw / 2, y: H - 8 + 0, "text-anchor": "middle"});
  // rows
  const rows = [
    {y: 66, name: "JM vs B&H", lo: F.bh_lo, hi: F.bh_hi, v: F.bh, colorVar: "--s1"},
    {y: 116, name: "JM vs VolTarget", lo: F.vt_lo, hi: F.vt_hi, v: F.vt, colorVar: "--s2"}];
  for (const r of rows) {
    const lab = el("text", {x: m.l - 10, y: r.y + 4, "text-anchor": "end", class: "dirlab"});
    lab.textContent = r.name; lab.style.fill = "var(--ink2)"; svg.appendChild(lab);
    svg.appendChild(el("line", {x1: X(r.lo), x2: X(r.hi), y1: r.y, y2: r.y,
      stroke: `var(${r.colorVar})`, "stroke-width": 2}));
    for (const e of [r.lo, r.hi])
      svg.appendChild(el("line", {x1: X(e), x2: X(e), y1: r.y - 5, y2: r.y + 5,
        stroke: `var(${r.colorVar})`, "stroke-width": 2}));
    svg.appendChild(el("circle", {cx: X(r.v), cy: r.y, r: 5, fill: `var(${r.colorVar})`,
      stroke: "var(--surface)", "stroke-width": 2}));
    const vl = el("text", {x: X(r.v), y: r.y - 12, "text-anchor": "middle", class: "dirlab"});
    vl.textContent = `${fmt(r.v)} bps`; vl.style.fill = `var(${r.colorVar})`;
    svg.appendChild(vl);
    const hitR = el("rect", {x: m.l, y: r.y - 18, width: iw, height: 36, fill: "transparent"});
    svg.appendChild(hitR);
    hitR.addEventListener("pointermove", ev => showTT(ev.clientX, ev.clientY,
      ttRows(r.name, [{colorVar: r.colorVar, name: "fee (90% CI)",
        value: `${fmt(r.v)} [${fmt(r.lo)}, ${fmt(r.hi)}]`}])));
    hitR.addEventListener("pointerleave", hideTT); }
  const cap = el("text", {x: m.l + iw / 2, y: H - 8, "text-anchor": "middle"});
}

function barChart(mount, items, colorVar) {
  const W = 1040, rowH = 26, m = {l: 170, r: 90, t: 6, b: 26};
  const H = m.t + m.b + items.length * rowH;
  const iw = W - m.l - m.r;
  const vmax = Math.max(...items.map(i => i.value)) * 1.08;
  const X = v => m.l + v / vmax * iw;
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img"});
  mount.appendChild(svg);
  svg.appendChild(el("line", {x1: m.l, x2: m.l, y1: m.t, y2: H - m.b,
    stroke: "var(--axis)", "stroke-width": 1}));
  items.forEach((it, i) => {
    const y = m.t + i * rowH + 4, h = rowH - 8;
    const lab = el("text", {x: m.l - 10, y: y + h / 2 + 4, "text-anchor": "end"});
    lab.textContent = it.label; svg.appendChild(lab);
    const w = Math.max(X(it.value) - m.l, 2);
    const p = el("path", {d: `M${m.l} ${y}h${w - 4}a4 4 0 0 1 4 4v${h - 8}a4 4 0 0 1 -4 4h${-(w - 4)}z`,
      fill: `var(${colorVar})`});
    svg.appendChild(p);
    const vl = el("text", {x: m.l + w + 8, y: y + h / 2 + 4, class: "dirlab"});
    vl.textContent = fmt(it.value); vl.style.fill = "var(--ink2)"; svg.appendChild(vl);
    const hit = el("rect", {x: m.l, y: y - 2, width: iw, height: h + 4, fill: "transparent"});
    svg.appendChild(hit);
    hit.addEventListener("pointermove", ev => { p.setAttribute("opacity", "0.8");
      showTT(ev.clientX, ev.clientY, ttRows(it.label,
        [{colorVar, name: "fee vs B&H (bps/yr)", value: fmt(it.value)}])); });
    hit.addEventListener("pointerleave", () => { p.setAttribute("opacity", "1"); hideTT(); }); });
}

function tile(parent, value, label, detail, cls) {
  const t = div("tile", parent);
  const v = div("v " + (cls || ""), t); v.textContent = value;
  const l = div("l", t); l.textContent = label;
  if (detail) { const d = div("d", t); d.textContent = detail; } }

function table(id, headers, rows, numFrom) {
  const tb = document.getElementById(id);
  const tr = document.createElement("tr");
  headers.forEach((h, i) => { const th = document.createElement("th");
    th.textContent = h; if (i >= numFrom) th.className = "num"; tr.appendChild(th); });
  tb.appendChild(tr);
  for (const row of rows) { const trr = document.createElement("tr");
    row.forEach((c, i) => { const td = document.createElement("td");
      td.textContent = c.text ?? c; if (i >= numFrom) td.className = "num";
      if (c.cls) td.className += " " + c.cls; trr.appendChild(td); });
    tb.appendChild(trr); } }

function ladderChart(mount, panels) {
  const W = 1040, rowH = 46, panelPad = 34;
  let H = 8;
  for (const p of panels) H += panelPad + p.rows.length * rowH + 20;
  const m = {l: 230, r: 190};
  const iw = W - m.l - m.r;
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Every claim vs its honest bar"});
  mount.appendChild(svg);
  let y = 8;
  for (const p of panels) {
    const title = el("text", {x: 0, y: y + 14, class: "dirlab"});
    title.textContent = p.title; title.style.fill = "var(--ink)"; svg.appendChild(title);
    y += panelPad;
    let vmin = 0, vmax = 0;
    for (const r of p.rows) { vmin = Math.min(vmin, r.lo); vmax = Math.max(vmax, r.hi); }
    const pad = (vmax - vmin) * 0.10 || 10;
    vmin -= pad; vmax += pad;
    const X = v => m.l + (v - vmin) / (vmax - vmin) * iw;
    const y0 = y, y1 = y + p.rows.length * rowH;
    svg.appendChild(el("line", {x1: X(0), x2: X(0), y1: y0 - 6, y2: y1,
      stroke: "var(--axis)", "stroke-width": 1}));
    const zl = el("text", {x: X(0), y: y1 + 14, "text-anchor": "middle"});
    zl.textContent = "0 bps/yr"; svg.appendChild(zl);
    for (const r of p.rows) {
      const cy = y + rowH / 2;
      const lab = el("text", {x: m.l - 10, y: cy + 4, "text-anchor": "end", class: "dirlab"});
      lab.textContent = r.name; lab.style.fill = "var(--ink2)"; svg.appendChild(lab);
      svg.appendChild(el("line", {x1: X(r.lo), x2: X(r.hi), y1: cy, y2: cy,
        stroke: `var(${r.colorVar})`, "stroke-width": 2}));
      for (const e of [r.lo, r.hi])
        svg.appendChild(el("line", {x1: X(e), x2: X(e), y1: cy - 5, y2: cy + 5,
          stroke: `var(${r.colorVar})`, "stroke-width": 2}));
      svg.appendChild(el("circle", {cx: X(r.v), cy, r: 5, fill: `var(${r.colorVar})`,
        stroke: "var(--surface)", "stroke-width": 2}));
      const vl = el("text", {x: X(r.v), y: cy - 11, "text-anchor": "middle", class: "dirlab"});
      vl.textContent = `${r.v > 0 ? "+" : ""}${fmt(r.v)}`;
      vl.style.fill = `var(${r.colorVar})`; svg.appendChild(vl);
      const tag = el("text", {x: W - m.r + 10, y: cy + 4});
      tag.textContent = r.tag; svg.appendChild(tag);
      const hit = el("rect", {x: m.l, y: cy - rowH / 2, width: iw, height: rowH,
        fill: "transparent"});
      svg.appendChild(hit);
      hit.addEventListener("pointermove", ev => showTT(ev.clientX, ev.clientY,
        ttRows(r.name, [{colorVar: r.colorVar, name: "fee, 90% CI (bps/yr)",
          value: `${fmt(r.v)} [${fmt(r.lo)}, ${fmt(r.hi)}]`}])));
      hit.addEventListener("pointerleave", hideTT);
      y += rowH; }
    y += 20; }
}

(function render() {
  const M = DATA.meta, F = DATA.fees, A = DATA.alloc;
  document.getElementById("subtitle").textContent =
    `Preregistered · causal · one look per claim · OOS ${M.oos_start} → ${M.oos_end} ` +
    `(${fmt(M.n)} trading days) · next-close execution, ${M.cost} bps costs`;
  const tiles = document.getElementById("tiles");
  if (M.live_state)
    tile(tiles, M.live_state, "sensor state, live", `since ${M.live_since} · as of ${M.live_date}`,
      M.live_state === "CALM" ? "posv" : "negv");
  tile(tiles, `${(F.stab_p * 100).toFixed(0)}%`, "sensor stability (±2y shifts)",
    "the program's real asset · incumbent 80.9%", "posv");
  tile(tiles, `Case ${M.case}`, "chapter 1 · trading the label",
    "exposure artifact — vol targeting beats it");
  if (A) tile(tiles, A.verdict.replace(/_/g, " "), "chapter 2 · conditioning covariance",
    "a plain EWMA estimate beats the label");
  tile(tiles, "reactive wins", "the program lesson so far",
    "daily-horizon lag races go to simple reactive estimators (VT, EWMA)");

  const panels = [{title: "Chapter 1 — overlay on equity (own scale)", rows: [
    {name: "JM − Buy&Hold", v: F.bh, lo: F.bh_lo, hi: F.bh_hi, colorVar: "--s1",
     tag: "inside all null bands"},
    {name: "JM − VolTarget · honest bar", v: F.vt, lo: F.vt_lo, hi: F.vt_hi,
     colorVar: "--s2", tag: "loses, significantly"}]}];
  if (A) panels.push({title: "Chapter 2 — conditional allocation (own scale)", rows: [
    {name: "Cond − B_match", v: A.fees.a, lo: A.fees.a_lo, hi: A.fees.a_hi,
     colorVar: "--s1", tag: "inside all null bands"},
    {name: "Cond − B_react · honest bar", v: A.fees.b, lo: A.fees.b_lo, hi: A.fees.b_hi,
     colorVar: "--s2", tag: "loses — EWMA wins"}]});
  ladderChart(document.getElementById("ladder"), panels);

  document.getElementById("sensornote").textContent =
    `A K=2 statistical jump model on daily downside features, run causally since 1990. ` +
    `Label stability ${(F.stab_p * 100).toFixed(1)}% under ±2y training shifts (incumbent ` +
    `80.9%), ${M.switches_yr} switches/yr, ${M.bear_frac}% of days stressed` +
    (M.live_state ? `; live today: ${M.live_state} since ${M.live_since}.` : `.`) +
    ` Shaded bands = its bear calls, drawn over the strategy equity curves.`;

  document.getElementById("mainfooter").textContent =
    `Living report — regenerate: scripts/build_report.py · frozen evidence: results/stage1.csv, ` +
    `oos_labels.csv, allocation_*.csv (+ run logs) · preregs in .planning/ (freeze precedes ` +
    `each run in git history) · tests 24/24 green.`;

  intervalChart(document.getElementById("intervals"));

  const eqSeries = ["JM", "VT", "SMA200", "B&H"].map(k => ({name: k, colorVar: SER[k],
    values: DATA.equity[k]}));
  for (const lid of ["eqlegend", "ddlegend"]) {
    const lg = document.getElementById(lid);
    for (const k of ["JM", "VT", "SMA200", "B&H"]) {
      const it = document.createElement("span"); it.className = "item";
      const key = document.createElement("span"); key.className = "key";
      key.style.borderTopColor = CV(SER[k]); it.appendChild(key);
      it.appendChild(document.createTextNode(k)); lg.appendChild(it); }
    const sw = document.createElement("span"); sw.className = "item";
    const s = document.createElement("span"); s.className = "swatch"; sw.appendChild(s);
    sw.appendChild(document.createTextNode("JM bear state")); lg.appendChild(sw); }
  lineChart(document.getElementById("equity"), {dates: DATA.dates, series: eqSeries,
    bands: DATA.bands, logY: true, ymin: 0.8, ymax: 55,
    yTicks: [1, 2, 5, 10, 20, 50], yfmt: v => "×" + fmt(v), label: "Equity curves"});

  lineChart(document.getElementById("drawdown"), {dates: DATA.dates,
    series: ["JM", "VT", "B&H"].map(k => ({name: k, colorVar: SER[k],
      values: DATA.drawdown[k]})),
    bands: DATA.bands, ymin: -60, ymax: 0, yTicks: [0, -10, -20, -30, -40, -50, -60],
    yfmt: v => fmt(v) + "%", label: "Drawdowns", height: 280});

  document.getElementById("epnote").textContent =
    `${DATA.episodes.length} bear calls covering ${M.bear_frac}% of days — all genuinely ` +
    `high-volatility stretches (calm-state vol is ${M.calm_vol}%). Real weather, no return edge.`;
  table("episodes", ["#", "Start", "End", "Days", "Market return", "Ann. vol in episode"],
    DATA.episodes.map((e, i) => [String(i + 1), e.start, e.end, fmt(e.days),
      {text: `${e.mkt_ret > 0 ? "+" : ""}${e.mkt_ret.toFixed(1)}%`,
       cls: e.mkt_ret < 0 ? "negv" : "posv"}, `${e.ann_vol.toFixed(1)}%`]), 3);

  lineChart(document.getElementById("lambda"), {dates: DATA.lam.years.map(y => y + "-01-01"),
    series: [{name: "λ", colorVar: "--s1", values: DATA.lam.values}], stepped: true,
    logY: true, ymin: 8, ymax: 1000, yTicks: [10, 25, 50, 100, 200, 400, 800],
    yfmt: v => fmt(v), label: "Selected lambda per refit", height: 220});

  const robust = [];
  for (const [k, v] of Object.entries(DATA.halves)) robust.push({label: "era " + k, value: v});
  for (const [k, v] of Object.entries(DATA.loto)) robust.push({label: "without " + k, value: v});
  barChart(document.getElementById("robust"), robust, "--s1");

  table("arms", ["Strategy", "Sharpe", "Max DD", "Ann. return", "Avg weight", "Turnover/yr"],
    Object.entries(DATA.arm_stats).map(([k, s]) => [k, s.sharpe.toFixed(3),
      {text: s.maxdd.toFixed(1) + "%", cls: "negv"}, s.ann_ret.toFixed(2) + "%",
      s.avg_w.toFixed(3), s.turnover_yr.toFixed(2)]), 1);

  table("annual", ["Year", "JM", "VT", "SMA200", "B&H"],
    DATA.annual.map(a => [String(a.year), ...["JM", "VT", "SMA200", "B&H"].map(k =>
      ({text: (a[k] > 0 ? "+" : "") + a[k].toFixed(1), cls: a[k] < 0 ? "negv" : ""}))]), 1);

  document.getElementById("footer").textContent =
    `Preregistered (.planning/V2-JUMPMODEL-PREREG.md Rev 2, frozen 2026-07-22) · ` +
    `K=2 weighted statistical jump model on downside-deviation/Sortino features · ` +
    `French daily market total return, trained from 1970 · annual refits, λ by 8y-validation ` +
    `Sharpe · causal DP-endpoint filter · run log: results/stage1_run.log (381 min) · ` +
    `secondary exhibits: fee γ=1 ${fmt(F.g1)}, vs SMA200 ${fmt(F.sma)}, vs matched static mix ` +
    `${fmt(F.mix)}, same-close sensitivity ${fmt(F.delay1)}, break-even cost ${fmt(F.breakeven)} bps.`;
})();

function mkLegend(id, entries, bandLabel) {
  const lg = document.getElementById(id);
  for (const e of entries) {
    const it = document.createElement("span"); it.className = "item";
    const key = document.createElement("span"); key.className = "key";
    key.style.borderTopColor = CV(e.colorVar); it.appendChild(key);
    it.appendChild(document.createTextNode(e.name)); lg.appendChild(it); }
  if (bandLabel) {
    const sw = document.createElement("span"); sw.className = "item";
    const s = document.createElement("span"); s.className = "swatch"; sw.appendChild(s);
    sw.appendChild(document.createTextNode(bandLabel)); lg.appendChild(sw); }
}

function scatterChart(mount, pts, refLine) {
  const W = 1040, H = 360, m = {t: 16, r: 40, b: 42, l: 56};
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const xmax = Math.max(...pts.map(p => p.x)) * 1.12;
  const ymax = Math.max(...pts.map(p => p.y)) * 1.18;
  const X = v => m.l + v / xmax * iw;
  const Y = v => m.t + ih - v / ymax * ih;
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Risk vs return by arm"});
  mount.appendChild(svg);
  for (let v = 0; v <= ymax; v += 2) {
    svg.appendChild(el("line", {x1: m.l, x2: m.l + iw, y1: Y(v), y2: Y(v),
      stroke: "var(--grid)", "stroke-width": 1}));
    const t = el("text", {x: m.l - 8, y: Y(v) + 4, "text-anchor": "end"});
    t.textContent = v + "%"; svg.appendChild(t); }
  for (let v = 0; v <= xmax; v += 2) {
    const t = el("text", {x: X(v), y: H - 20, "text-anchor": "middle"});
    t.textContent = v + "%"; svg.appendChild(t); }
  const xl = el("text", {x: m.l + iw / 2, y: H - 4, "text-anchor": "middle"});
  xl.textContent = "risk (annualized volatility)"; svg.appendChild(xl);
  svg.appendChild(el("line", {x1: m.l, x2: m.l + iw, y1: m.t + ih, y2: m.t + ih,
    stroke: "var(--axis)", "stroke-width": 1}));
  // leverage line through the reference arm: y = intercept + sharpe * x
  const yEnd = refLine.intercept + refLine.sharpe * xmax;
  svg.appendChild(el("line", {x1: X(0), y1: Y(Math.max(refLine.intercept, 0)),
    x2: yEnd > ymax ? X((ymax - refLine.intercept) / refLine.sharpe) : X(xmax),
    y2: yEnd > ymax ? Y(ymax) : Y(yEnd),
    stroke: `var(${refLine.colorVar})`, "stroke-width": 1.5,
    "stroke-dasharray": "6 5", opacity: 0.7}));
  const ll = el("text", {x: X(xmax * 0.55), y: Y(refLine.intercept + refLine.sharpe * xmax * 0.55) - 8,
    class: "dirlab"});
  ll.textContent = refLine.label; ll.style.fill = `var(${refLine.colorVar})`;
  svg.appendChild(ll);
  for (const p of pts) {
    svg.appendChild(el("circle", {cx: X(p.x), cy: Y(p.y), r: 6,
      fill: `var(${p.colorVar})`, stroke: "var(--surface)", "stroke-width": 2}));
    const t = el("text", {x: X(p.x) + 10, y: Y(p.y) + 4, class: "dirlab"});
    t.textContent = p.name; t.style.fill = "var(--ink2)"; svg.appendChild(t);
    const hit = el("rect", {x: X(p.x) - 12, y: Y(p.y) - 12, width: 24, height: 24,
      fill: "transparent"});
    svg.appendChild(hit);
    hit.addEventListener("pointermove", ev => showTT(ev.clientX, ev.clientY,
      ttRows(p.name, [
        {colorVar: p.colorVar, name: "return / vol", value: `${p.y.toFixed(1)}% / ${p.x.toFixed(1)}%`},
        {colorVar: p.colorVar, name: "Sharpe", value: p.sharpe.toFixed(2)},
        {colorVar: p.colorVar, name: "max drawdown", value: p.maxdd.toFixed(0) + "%"}])));
    hit.addEventListener("pointerleave", hideTT); }
}

function intervalChart2(mount, A) {
  const F = A.fees, B = A.bands_ctl;
  const rows = [
    {y: 64, name: "fee_A · Cond − B_match", v: F.a, lo: F.a_lo, hi: F.a_hi,
     shuffle: [B.shuffle.a_lo, B.shuffle.a_hi], iid: [B.iid.a_lo, B.iid.a_hi],
     placebo: B.placebo.a_hi, colorVar: "--s1"},
    {y: 140, name: "fee_B · Cond − B_react", v: F.b, lo: F.b_lo, hi: F.b_hi,
     shuffle: [B.shuffle.b_lo, B.shuffle.b_hi], iid: [B.iid.b_lo, B.iid.b_hi],
     placebo: B.placebo.b_hi, colorVar: "--s3"}];
  let vmin = 0, vmax = 0;
  for (const r of rows) for (const v of [r.v, r.lo, r.hi, ...r.shuffle, ...r.iid, r.placebo]) {
    if (v < vmin) vmin = v; if (v > vmax) vmax = v; }
  const pad = (vmax - vmin) * 0.12 || 10; vmin -= pad; vmax += pad;
  const W = 1040, H = 196, m = {l: 190, r: 30, t: 8, b: 30};
  const iw = W - m.l - m.r;
  const X = v => m.l + (v - vmin) / (vmax - vmin) * iw;
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Chapter-2 fees vs null bands"});
  mount.appendChild(svg);
  svg.appendChild(el("line", {x1: X(0), x2: X(0), y1: m.t, y2: H - m.b,
    stroke: "var(--axis)", "stroke-width": 1}));
  const rawStep = (vmax - vmin) / 5;
  const mag = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const step = [1, 2, 5, 10].map(s => s * mag).find(s => s >= rawStep) || 10 * mag;
  for (let v = Math.ceil(vmin / step) * step; v <= vmax; v += step) {
    const t = el("text", {x: X(v), y: H - 8, "text-anchor": "middle"});
    t.textContent = fmt(v); svg.appendChild(t); }
  for (const r of rows) {
    const lab = el("text", {x: m.l - 10, y: r.y + 4, "text-anchor": "end",
      class: "dirlab"});
    lab.textContent = r.name; lab.style.fill = "var(--ink2)"; svg.appendChild(lab);
    svg.appendChild(el("rect", {x: X(r.shuffle[0]), y: r.y - 20,
      width: Math.max(X(r.shuffle[1]) - X(r.shuffle[0]), 1.5), height: 40,
      fill: "var(--band)"}));
    svg.appendChild(el("rect", {x: X(r.iid[0]), y: r.y - 10,
      width: Math.max(X(r.iid[1]) - X(r.iid[0]), 1.5), height: 20,
      fill: "none", stroke: "var(--axis)", "stroke-dasharray": "2 2"}));
    svg.appendChild(el("line", {x1: X(r.placebo), x2: X(r.placebo), y1: r.y - 22,
      y2: r.y + 22, stroke: "var(--muted)", "stroke-width": 1.5,
      "stroke-dasharray": "5 4"}));
    svg.appendChild(el("line", {x1: X(r.lo), x2: X(r.hi), y1: r.y, y2: r.y,
      stroke: `var(${r.colorVar})`, "stroke-width": 2}));
    for (const e of [r.lo, r.hi])
      svg.appendChild(el("line", {x1: X(e), x2: X(e), y1: r.y - 5, y2: r.y + 5,
        stroke: `var(${r.colorVar})`, "stroke-width": 2}));
    svg.appendChild(el("circle", {cx: X(r.v), cy: r.y, r: 5,
      fill: `var(${r.colorVar})`, stroke: "var(--surface)", "stroke-width": 2}));
    const vl = el("text", {x: X(r.v), y: r.y - 26, "text-anchor": "middle",
      class: "dirlab"});
    vl.textContent = `${fmt(r.v)} bps`; vl.style.fill = `var(${r.colorVar})`;
    svg.appendChild(vl);
    const hitR = el("rect", {x: m.l, y: r.y - 24, width: iw, height: 48,
      fill: "transparent"});
    svg.appendChild(hitR);
    hitR.addEventListener("pointermove", ev => showTT(ev.clientX, ev.clientY,
      ttRows(r.name, [
        {colorVar: r.colorVar, name: "fee (90% CI)",
         value: `${fmt(r.v)} [${fmt(r.lo)}, ${fmt(r.hi)}]`},
        {colorVar: "--s4", name: "placebo 95th", value: fmt(r.placebo)},
        {colorVar: "--s4", name: "shuffle 5–95th",
         value: `[${fmt(r.shuffle[0])}, ${fmt(r.shuffle[1])}]`},
        {colorVar: "--s4", name: "iid 5–95th",
         value: `[${fmt(r.iid[0])}, ${fmt(r.iid[1])}]`}])));
    hitR.addEventListener("pointerleave", hideTT); }
}

(function renderAlloc() {
  const A = DATA.alloc;
  if (!A) return;
  document.getElementById("ch2block").style.display = "";
  const M = DATA.meta, F = A.fees;

  const tiles = document.getElementById("ch2tiles");
  tile(tiles, A.verdict.replace(/_/g, " "), "frozen verdict",
    `F1=${A.f.f1} F1b=${A.f.f1b} F2=${A.f.f2} F3=${A.f.f3} controls_clean=${A.f.clean}`);
  tile(tiles, `${F.a > 0 ? "+" : ""}${fmt(F.a)}`, "fee_A vs B_match (bps/yr, γ=10)",
    `90% CI [${fmt(F.a_lo)}, ${fmt(F.a_hi)}]`, F.a > 0 && F.a_lo > 0 ? "posv" : "");
  tile(tiles, `${F.b > 0 ? "+" : ""}${fmt(F.b)}`, "fee_B vs B_react (bps/yr, γ=10)",
    `90% CI [${fmt(F.b_lo)}, ${fmt(F.b_hi)}] · from activation`,
    F.b > 0 && F.b_lo > 0 ? "posv" : "");
  tile(tiles, `${A.volvol.cond.toFixed(2)} vs ${A.volvol.match.toFixed(2)}`,
    "vol-of-vol, cond vs B_match (pp)",
    A.volvol.cond < A.volvol.match ? "risk stabilization: holds" : "risk stabilization: FAILS",
    A.volvol.cond < A.volvol.match ? "posv" : "negv");
  tile(tiles, `${A.turnover.cond.toFixed(2)}×`, "turnover/yr (cond)",
    `B_match ${A.turnover.match.toFixed(2)} · B_react ${A.turnover.react.toFixed(2)} · bar 5× B_match`);

  const scatterColors = {"Cond": "--s1", "B_match": "--s2", "B_react": "--s3",
    "60/40": "--s4", "VT equity": "--s4", "B&H equity": "--s4"};
  const pts = Object.entries(A.arm_stats).map(([name, s]) => ({name,
    x: s.ann_vol, y: s.ann_ret, sharpe: s.sharpe, maxdd: s.maxdd,
    colorVar: scatterColors[name]}));
  const best = A.arm_stats["B_react"];
  scatterChart(document.getElementById("ch2scatter"), pts,
    {sharpe: best.sharpe, intercept: best.ann_ret - best.sharpe * best.ann_vol,
     colorVar: "--s3", label: "B_react + cash/leverage"});

  intervalChart2(document.getElementById("ch2intervals"), A);

  const armColors = {"Cond": "--s1", "B_match": "--s2", "B_react": "--s3", "60/40": "--s4"};
  document.getElementById("ch2eqnote").textContent =
    `Same caps, same 8% target, same costs — only the covariance estimate differs, and the ` +
    `three ERC lines barely separate: the label adds nothing here. Shaded = stressed states.`;
  mkLegend("ch2eqlegend", Object.entries(armColors).map(([name, colorVar]) =>
    ({name, colorVar})), "stressed state");
  const eqmax = Math.max(...Object.values(A.equity).flat());
  lineChart(document.getElementById("ch2equity"), {dates: A.dates,
    series: Object.entries(armColors).map(([k, cv]) => ({name: k, colorVar: cv,
      values: A.equity[k]})),
    bands: DATA.bands, logY: true, ymin: 0.8, ymax: eqmax * 1.15,
    yTicks: [1, 2, 5, 10, 20, 50].filter(v => v <= eqmax * 1.15),
    yfmt: v => "×" + fmt(v), label: "Chapter-2 equity curves"});

  const wColors = {"Equity": "--s1", "Bond": "--s2", "Gold": "--s4", "Cash": "--s3"};
  mkLegend("ch2wlegend", Object.entries(wColors).map(([name, colorVar]) =>
    ({name, colorVar})), "stressed state");
  lineChart(document.getElementById("ch2weights"), {dates: A.dates,
    series: Object.entries(wColors).map(([k, cv]) => ({name: k, colorVar: cv,
      values: A.weights[k]})),
    bands: DATA.bands, ymin: 0, ymax: 100, yTicks: [0, 25, 50, 75, 100],
    yfmt: v => fmt(v) + "%", label: "Conditional arm weights", height: 260});

  table("ch2splits", ["Window", "fee_A (bps/yr)", "fee_B (bps/yr)"],
    Object.entries(A.splits).map(([k, v]) => [k,
      {text: (v[0] > 0 ? "+" : "") + v[0].toFixed(1), cls: v[0] < 0 ? "negv" : "posv"},
      {text: (v[1] > 0 ? "+" : "") + v[1].toFixed(1), cls: v[1] < 0 ? "negv" : "posv"}]), 1);

  table("ch2arms", ["Arm", "Sharpe", "Max DD", "Ann. return", "Ann. vol"],
    Object.entries(A.arm_stats).map(([k, s]) => [k, s.sharpe.toFixed(3),
      {text: s.maxdd.toFixed(1) + "%", cls: "negv"}, s.ann_ret.toFixed(2) + "%",
      s.ann_vol.toFixed(2) + "%"]), 1);

  table("ch2annual", ["Year", "Cond", "B_match", "B_react", "60/40"],
    A.annual.map(a => [String(a.year), ...["Cond", "B_match", "B_react", "60/40"].map(k =>
      ({text: (a[k] > 0 ? "+" : "") + a[k].toFixed(1), cls: a[k] < 0 ? "negv" : ""}))]), 1);

  document.getElementById("ch2footer").textContent =
    `Preregistered (.planning/ALLOCATION-PREREG.md Rev 2.1, frozen 2026-07-23) · conditional ` +
    `ERC over equity/10y Treasury/gold/cash, covariance only, no return forecasts · scored ` +
    `${M.oos_start} → ${M.oos_end}, conditioning active ${A.activation} · hard-state expanding ` +
    `per-state cov (min 500 days, 0.5 shrink) · ERC by log-barrier CCD, caps 75/75/25, 8% vol ` +
    `target scale-down only · monthly + state-flip rebalance, next-close, 10 bps · baselines: ` +
    `identical ERC on unconditional expanding (B_match) and EWMA λ=0.97 (B_react) covariance · ` +
    `secondary fees γ=1: A ${fmt(F.a_g1)}, B ${fmt(F.b_g1)} · run log: results/allocation_run.log.`;
})();
</script>
</body>
</html>
"""


def main():
    data = build_data()
    data["alloc"] = build_alloc_data()
    html = HTML.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    out = ROOT / "results" / "report.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB) — "
          f"{len(data['dates'])} chart points, {len(data['episodes'])} episodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
