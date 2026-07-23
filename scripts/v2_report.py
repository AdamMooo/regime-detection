"""Generate results/v2_report.html — self-contained visual report of the v2 Stage-1 backtest.

Reads: data/processed/v2_daily.csv, results/v2_oos_labels.csv, results/v2_stage1.csv,
results/v2_stage1_run.log (lambda path + LOTO parsed from the frozen one-look log).
Recomputes strategy paths with the exact stage-1 code (deterministic; not a new look).
Regenerate any time: .venv/Scripts/python scripts/v2_report.py
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

from v2_eval import sharpe, sma_weights, vol_target_weights
from v2_stage1 import COST, DELAY, START, arm_returns, maxdd
from v2_eval import jm_weights


def build_data():
    panel = pd.read_csv(ROOT / "data" / "processed" / "v2_daily.csv",
                        index_col=0, parse_dates=True).loc[START:]
    labels = pd.read_csv(ROOT / "results" / "v2_oos_labels.csv", parse_dates=["date"])
    stats = pd.read_csv(ROOT / "results" / "v2_stage1.csv").iloc[0]
    log = (ROOT / "results" / "v2_stage1_run.log").read_text()

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

    return dict(
        meta=dict(oos_start=str(idx_o[0].date()), oos_end=str(idx_o[-1].date()),
                  n=int(len(idx_o)), case=str(stats["case"]),
                  bear_frac=round(float((s_o == 1).mean()) * 100, 1),
                  switches_yr=round(float(stats["switches_yr"]), 2), calm_vol=round(calm_vol, 1),
                  delay=DELAY, cost=COST),
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


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V2 Jump-Model Backtest — Results</title>
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
<h1>V2 Jump-Model Backtest — One-Look Results</h1>
<p class="sub" id="subtitle"></p>

<div class="tiles" id="tiles"></div>

<h2>The verdict in one picture — the fee against its null bands</h2>
<p class="note">The FKO fee (γ=10) measures what a risk-averse investor would pay to hold the
strategy instead of the benchmark. The jump-model overlay earns a big fee vs buy-and-hold — but
so do random persistent signals with the same average exposure (placebo), timing-destroyed
surrogates, and pure iid-noise pipelines. The point sits inside every null band, and vs vol
targeting the fee is significantly negative. The fee is exposure, not timing.</p>
<div class="card"><div id="intervals"></div></div>

<h2>Equity curves, 1990&ndash;2026 (log scale)</h2>
<p class="note">Shaded bands are the model's OOS bear states, called causally. The overlay
(JM) sidesteps the big drawdowns — but vol targeting rides the same information with less lag,
and buy-and-hold's terminal wealth is higher: the overlay's value is risk reduction, priced by
the fee, not extra return.</p>
<div class="legend" id="eqlegend"></div>
<div class="card"><div id="equity"></div></div>
<details><summary>Table view — annual returns by strategy (%)</summary>
<div class="card"><table id="annual"></table></div></details>

<h2>Drawdowns</h2>
<p class="note">Where the overlay earns its fee: max drawdown &minus;27.5% vs buy-and-hold's
&minus;54.6%. Note how closely vol targeting tracks the same protection.</p>
<div class="legend" id="ddlegend"></div>
<div class="card"><div id="drawdown"></div></div>

<h2>What the model is doing — bear episodes it called</h2>
<p class="note" id="epnote"></p>
<div class="card"><table id="episodes"></table></div>

<h2>The speed/stability dial — selected &lambda; per refit</h2>
<p class="note">&lambda; is the jump penalty: the switch cost the causal cross-validation chose
each year (grid 10&ndash;800, log scale). It stays off the grid edges (falsifier F2 clear) and
drifts lower in the modern era — the data asking for a slightly faster dial.</p>
<div class="card"><div id="lambda"></div></div>

<h2>Robustness — fee vs B&amp;H by era and with each crisis removed</h2>
<p class="note">The fee is positive in both era halves and under every leave-one-crisis-out —
consistent with an exposure effect that is always present, rather than skill concentrated in
one lucky episode.</p>
<div class="card"><div id="robust"></div></div>

<h2>Strategy comparison</h2>
<div class="card"><table id="arms"></table></div>

<p class="footer" id="footer"></p>
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

(function render() {
  const M = DATA.meta, F = DATA.fees;
  document.getElementById("subtitle").textContent =
    `OOS ${M.oos_start} → ${M.oos_end} · ${fmt(M.n)} trading days · next-close execution ` +
    `(delay ${M.delay}d) · ${M.cost} bps one-way costs · frozen prereg, one look · Case ${M.case}`;
  const tiles = document.getElementById("tiles");
  tile(tiles, `Case ${M.case}`, "frozen verdict", "fee>0 but CI includes 0; controls not clean");
  tile(tiles, `+${fmt(F.bh)}`, "fee vs B&H (bps/yr, γ=10)", `90% CI [${fmt(F.bh_lo)}, ${fmt(F.bh_hi)}] — inside all null bands`);
  tile(tiles, `${fmt(F.vt)}`, "fee vs VolTarget (bps/yr)", `90% CI [${fmt(F.vt_lo)}, ${fmt(F.vt_hi)}] — significantly negative`, "negv");
  tile(tiles, `${(F.stab_p * 100).toFixed(1)}%`, "label stability (±2y window)", "incumbent ensemble: 80.9%", "posv");
  tile(tiles, `${M.switches_yr}`, "regime switches / year", "falsifier bar: 12");
  tile(tiles, `${M.bear_frac}%`, "of OOS days in bear state", `${DATA.episodes.length} episodes`);

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
    `The model spent ${M.bear_frac}% of days in its bear state across ` +
    `${DATA.episodes.length} episodes. Within-episode annualized volatility runs far above ` +
    `the calm-state ${M.calm_vol}% — the states are real volatility environments; ` +
    `what they are not is a tradable return edge.`;
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
    `Sharpe · causal DP-endpoint filter · run log: results/v2_stage1_run.log (381 min) · ` +
    `secondary exhibits: fee γ=1 ${fmt(F.g1)}, vs SMA200 ${fmt(F.sma)}, vs matched static mix ` +
    `${fmt(F.mix)}, same-close sensitivity ${fmt(F.delay1)}, break-even cost ${fmt(F.breakeven)} bps.`;
})();
</script>
</body>
</html>
"""


def main():
    data = build_data()
    html = HTML.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    out = ROOT / "results" / "v2_report.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB) — "
          f"{len(data['dates'])} chart points, {len(data['episodes'])} episodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
