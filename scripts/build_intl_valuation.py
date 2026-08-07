"""International valuation inputs — dividend yield by construction (Phase 3, V5).

The registered international out-of-hypothesis sample. No free CAPE exists for
Japan or Europe, so the charter's V5 was respecified 2026-08-07 onto the object
that IS free and exact:

French publishes the F-F International Indices twice — once WITH dividends and
once WITHOUT, same indices, same universe, same months. For any period,

    R_with - R_without = (P_t + D_t)/P_{t-1} - P_t/P_{t-1} = D_t / P_{t-1}

so the difference of the two published series IS the period's dividend yield on
lagged price. Cumulated over 12 months it is the trailing D/P — the canonical
Campbell-Shiller valuation object. Numerator, denominator and the forward-return
leg all come from one file on one universe, so they cannot drift apart across
sources.

LOCAL currency is the primary object (the mechanism is about a market's own
discount rate; USD returns add an FX channel the charter does not model). Dollar
returns are written alongside as the registered robustness lens.

Universe variant: the "All 4 Data Items Not Reqd" blocks — a firm need not have
all of BE/ME, E/P, CE/P and yield to enter the index. The broader universe, and
the one whose survivorship properties are least conditioned on data availability.

Writes data/processed/intl_valuation_monthly.csv (+ the annual VW-ratio block as
data/processed/intl_valuation_ratios_annual.csv, the secondary BE/ME cross-check)
Run:  python scripts/build_intl_valuation.py
"""

import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
WITH_DIV = "F-F_International_Indices.zip"
WOUT_DIV = "F-F_International_Indices_Wout_Div.zip"
UA = "Mozilla/5.0"

# index file -> the short region key used in the output columns
REGIONS = {
    "Ind_Eur_WOut_UK.Dat": "europe_ex_uk",
    "Ind_Eur_With_UK.Dat": "europe",
    "Ind_UK.Dat": "uk",
    "Ind_Scandanavia.Dat": "scandinavia",   # French's spelling of the filename
    "Ind_Asia_Pacific.Dat": "asia_pacific",
    "Ind_all.Dat": "all",
}

RATIO_COLUMNS = ["mkt", "beme_high", "beme_low", "ep_high", "ep_low",
                 "cep_high", "cep_low", "yld_high", "yld_low"]

MIN_YIELD_MEAN, MAX_YIELD_MEAN = 0.005, 0.08     # a plausible mean trailing D/P


def _download(name: str) -> bytes:
    resp = requests.get(BASE + name, timeout=180, headers={"User-Agent": UA})
    resp.raise_for_status()
    return resp.content


def _snapshot(name: str, payload: bytes) -> None:
    """The raw zip IS the vintage — French restates history, so the filename is
    not a dataset identifier (see the 2026-08-06 SKEW finding)."""
    path = ROOT / "data" / "raw" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _blocks(text: str) -> list[tuple[str, list[list]]]:
    """Split a .Dat into (header, rows). French stacks 10 blocks per file with a
    three-line header each; rows are recognised by a leading YYYYMM or YYYY."""
    out, header, rows = [], None, []
    for line in text.splitlines():
        parts = line.split()
        if parts and re.fullmatch(r"\d{4}(\d{2})?", parts[0]):
            rows.append([parts[0]] + [float(x) for x in parts[1:]])
            continue
        if rows:
            out.append((header, rows))
            rows = []
        if "Returns" in line or "Ratios" in line:
            header = line.strip()
    if rows:
        out.append((header, rows))
    return out


def _pick(blocks, want_monthly: bool, kind: str, required: bool):
    """kind: 'Dollar' | 'Local' | 'Ratios'."""
    for header, rows in blocks:
        if header is None or kind not in header:
            continue
        is_required = "Not Req" not in header
        if is_required != required:
            continue
        if (len(rows[0][0]) == 6) != want_monthly:
            continue
        return rows
    raise KeyError(f"block not found: monthly={want_monthly} kind={kind} required={required}")


def _series(rows, monthly: bool) -> pd.DataFrame:
    idx = pd.to_datetime([r[0] for r in rows], format="%Y%m" if monthly else "%Y")
    idx = idx + (pd.offsets.MonthEnd(0) if monthly else pd.offsets.YearEnd(0))
    return pd.DataFrame([r[1:] for r in rows], index=pd.DatetimeIndex(idx, name="date"))


def build_panels() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    raw_with, raw_wout = _download(WITH_DIV), _download(WOUT_DIV)
    _snapshot(WITH_DIV, raw_with)
    _snapshot(WOUT_DIV, raw_wout)
    zf_with, zf_wout = zipfile.ZipFile(io.BytesIO(raw_with)), zipfile.ZipFile(io.BytesIO(raw_wout))

    monthly, ratios, spans = {}, {}, {}
    for filename, region in REGIONS.items():
        b_with = _blocks(zf_with.read(filename).decode("latin-1"))
        b_wout = _blocks(zf_wout.read(filename).decode("latin-1"))

        for tag, kind in (("local", "Local"), ("usd", "Dollar")):
            w = _series(_pick(b_with, True, kind, required=False), True)[0] / 100.0
            o = _series(_pick(b_wout, True, kind, required=False), True)[0] / 100.0
            common = w.index.intersection(o.index)
            monthly[f"{region}_ret_{tag}"] = w.loc[common]
            # D_t / P_{t-1}, exact by construction
            monthly[f"{region}_dy_{tag}"] = (w.loc[common] - o.loc[common])

        r = _series(_pick(b_with, False, "Ratios", required=False), False)
        r.columns = RATIO_COLUMNS[:r.shape[1]]
        ratios[region] = r["mkt"]
        spans[region] = (common[0].date(), common[-1].date(), len(common))

    m = pd.DataFrame(monthly).sort_index()
    # trailing 12-month dividend yield: the D/P level the signal reads
    for region in REGIONS.values():
        for tag in ("local", "usd"):
            m[f"{region}_dp_{tag}"] = m[f"{region}_dy_{tag}"].rolling(12).sum()

    return m, pd.DataFrame(ratios).sort_index(), spans


def main() -> int:
    m, ratios, spans = build_panels()
    proc = ROOT / "data" / "processed"
    proc.mkdir(parents=True, exist_ok=True)
    m.to_csv(proc / "intl_valuation_monthly.csv")
    ratios.to_csv(proc / "intl_valuation_ratios_annual.csv")

    gate = []
    dp_local = [f"{r}_dp_local" for r in REGIONS.values()]
    dy_local = [f"{r}_dy_local" for r in REGIONS.values()]

    starts = {r: s[0] for r, s in spans.items()}
    ends = {r: s[1] for r, s in spans.items()}
    gate.append(("G1_span", len(set(starts.values())) == 1 and len(set(ends.values())) == 1,
                 f"{sorted(set(starts.values()))[0]} .. {sorted(set(ends.values()))[-1]} "
                 f"n={spans['europe'][2]} months x {len(REGIONS)} regions"))

    # a negative implied dividend would mean the two published series are not the
    # matched pair this construction assumes — the load-bearing integrity check
    neg = {c: int((m[c] < -1e-9).sum()) for c in dy_local}
    gate.append(("G2_no_negative_dividends", sum(neg.values()) == 0, f"negative months={neg}"))

    means = {c: float(m[c].mean()) for c in dp_local}
    ok = all(MIN_YIELD_MEAN < v < MAX_YIELD_MEAN for v in means.values())
    gate.append(("G3_yield_magnitude", ok,
                 " ".join(f"{c.split('_dp')[0]}={v:.2%}" for c, v in means.items())))

    # the two canonical out-of-US valuation extremes must be present and correctly
    # signed: Asia Pacific cheapest-priced-in 1989, Europe in 1999
    ap = m["asia_pacific_dp_local"].dropna()
    eu = m["europe_ex_uk_dp_local"].dropna()
    gate.append(("G4_known_extremes", ap.idxmin().year == 1989 and eu.idxmin().year in (1999, 2000),
                 f"asia_pacific min {ap.min():.2%} @ {ap.idxmin().date()} | "
                 f"europe_ex_uk min {eu.min():.2%} @ {eu.idxmin().date()}"))

    contiguous = m.index.equals(pd.date_range(m.index[0], m.index[-1], freq="ME"))
    gate.append(("G5_monthly_grid", contiguous and not m.index.has_duplicates,
                 f"contiguous={contiguous} dups={int(m.index.duplicated().sum())}"))

    gate.append(("G6_ratios_block", ratios.notna().all().all() and len(ratios) >= 45,
                 f"annual VW market BE/ME {ratios.index[0].year}-{ratios.index[-1].year}, "
                 f"n={len(ratios)}, regions={list(ratios.columns)}"))

    res = pd.DataFrame(gate, columns=["gate", "passed", "detail"])
    res.to_csv(ROOT / "results" / "intl_valuation_gate.csv", index=False)
    print(res.to_string(index=False))
    print(f"\nwrote {(proc / 'intl_valuation_monthly.csv').relative_to(ROOT)}  "
          f"rows={len(m)} cols={m.shape[1]}")
    print(f"wrote {(proc / 'intl_valuation_ratios_annual.csv').relative_to(ROOT)}  rows={len(ratios)}")
    print("CONSTRUCTION GATE:", "PASS" if res["passed"].all() else "FAIL")
    return 0 if res["passed"].all() else 1


if __name__ == "__main__":
    sys.exit(main())
