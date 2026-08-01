"""Regime signal: read the live label (results/label_live.csv, produced by live_label.py)
and emit results/regime_card.json — a small, stable data contract consumed by
portfolio-manager (daily Market Brief one-liner + weekly positioning email; 2026-07-27
decision — vol-diagnostics stays a separate showcase project, not a consumer here).

Instrument operation, not research: this only derives descriptive persistence stats from an
already-produced causal label. It does not re-run the backtest or touch frozen evidence.

Run after live_label.py:  python scripts/regime_signal.py
"""

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_labels():
    df = pd.read_csv(ROOT / "results" / "label_live.csv", parse_dates=["date"])
    return df["date"], df["state"].astype(int)


def current_state(dates, states):
    s = states.to_numpy()
    switches = np.flatnonzero(s[1:] != s[:-1])
    last_switch = dates.iloc[switches[-1] + 1] if switches.size else dates.iloc[0]
    as_of = dates.iloc[-1]
    return {
        "state": "STRESSED" if s[-1] == 1 else "CALM",
        "state_code": int(s[-1]),
        "as_of": as_of.date().isoformat(),
        "last_switch": last_switch.date().isoformat(),
        "days_in_state": int((as_of - last_switch).days),
    }


def stay_probability(states, state_code):
    trans = pd.crosstab(states.shift(), states, normalize="index")
    if state_code not in trans.index:
        # state_code has never had a day-after to transition from (e.g. it just
        # started today for the first time in the label's history) — no completed
        # transition to estimate a stay probability from.
        return 1.0
    return float(trans.loc[state_code, state_code])


def dwell_samples(states, state_code):
    runs = states.groupby((states != states.shift()).cumsum()).agg(["first", "size"])
    return runs[runs["first"] == state_code]["size"].to_numpy()


def persistence_gauge(p_stay, dwell_days, days_in_state):
    """Turn the current state's stay-probability and its historical dwell-length samples
    into the persistence gauge. Return a dict with these keys:
        markov_expected_dwell : float   # mean regime length implied by p_stay
        markov_half_life       : float   # days until 50% chance the regime has ended
        empirical_median       : float   # median historical dwell for this state
        empirical_n            : int     # number of historical episodes
        position               : str     # where days_in_state sits vs history
    """
    if p_stay >= 1.0:
        markov_expected_dwell = markov_half_life = float("inf")
    else:
        markov_expected_dwell = 1.0 / (1.0 - p_stay)
        markov_half_life = float(np.log(0.5) / np.log(p_stay))

    # dwell_days' last entry is the still-open run this card is reporting on (same
    # episode as days_in_state) — drop it so "position" ranks the current run against
    # completed history only, not against itself. Also trading-day counts (dwell_days)
    # vs calendar-day counts (days_in_state) are different units; rank the current run
    # in its own (trading-day) unit rather than mixing the two.
    historical = dwell_days[:-1] if len(dwell_days) > 1 else dwell_days[:0]
    current_run_td = dwell_days[-1] if len(dwell_days) else 0
    empirical_n = int(len(historical))

    if empirical_n:
        empirical_median = float(np.median(historical))
        pctile = int(round(float((historical <= current_run_td).mean() * 100)))
        suffix = "th" if 11 <= pctile % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(pctile % 10, "th")
        position = f"{pctile}{suffix} percentile of {empirical_n} completed episodes (currently {days_in_state}d in)"
    else:
        empirical_median = None
        position = f"no completed historical episodes yet (currently {days_in_state}d in)"

    return {
        "markov_expected_dwell": round(markov_expected_dwell, 1),
        "markov_half_life": round(markov_half_life, 1),
        "empirical_median": round(empirical_median, 1) if empirical_median is not None else None,
        "empirical_n": empirical_n,
        "position": position,
    }


def health_block():
    """Splice-gate health for TODAY's specific reading (from live_label.py's most recent
    run) — the earliest warning if the live SPY splice has drifted from the French panel
    it's spliced onto. None if live_label.py hasn't been run since this field was added.
    """
    meta_path = ROOT / "results" / "live_label_meta.json"
    if not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text())
    return {
        "splice_corr": meta.get("splice_corr"),
        "splice_gate_pass": meta.get("splice_gate_pass"),
        "agreement_with_frozen": meta.get("agreement_with_frozen"),
    }


def skill_block():
    """The instrument's historical track record vs ex-post bear dating (validate_sensor.py,
    scored against the frozen chapter-1 OOS labels — a fixed fact, not rerun per card).
    Companion to the stability/persistence numbers above: pairs every "how persistent" claim
    with a "how often has it actually been right" one.
    """
    path = ROOT / "results" / "sensor_validation.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path).set_index("variant")
    if "LT15" not in df.index or "LT20" not in df.index:
        return None
    lt15, lt20 = df.loc["LT15"], df.loc["LT20"]
    return {
        "source": "validate_sensor.py vs Lunde-Timmermann ex-post bear dating, frozen chapter-1 OOS",
        "lt15_detected": int(lt15["detected"]), "lt15_episodes": int(lt15["episodes"]),
        "lt15_median_lag_days": int(lt15["median_lag_days"]),
        "lt20_detected": int(lt20["detected"]), "lt20_episodes": int(lt20["episodes"]),
        "lt20_median_lag_days": int(lt20["median_lag_days"]),
        "caveat": ("Vol-state sensor, not a bear detector: catches most drawdowns with a "
                   "multi-week lag; historically misses fast crashes (e.g. 1998, 2018 Q4)."),
    }


def history_block(dates, states, months=24):
    """Monthly state (last trading day of each month) for the trailing `months` — a compact
    timeline so the current dwell has visual scale, not just a percentile number."""
    monthly = pd.Series(states.to_numpy(), index=dates).resample("ME").last()
    tail = monthly.iloc[-months:]
    return [{"period": d.strftime("%Y-%m"), "state": int(v)} for d, v in tail.items()]


def build_card():
    dates, states = load_labels()
    card = current_state(dates, states)
    p_stay = stay_probability(states, card["state_code"])
    dwell = dwell_samples(states, card["state_code"])
    gauge = persistence_gauge(p_stay, dwell, card["days_in_state"])
    card["p_stay"] = round(p_stay, 4)
    card["gauge"] = gauge
    card["health"] = health_block()
    card["skill"] = skill_block()
    card["history"] = history_block(dates, states)
    card["generated"] = date.today().isoformat()
    return card


def main():
    card = build_card()
    out = ROOT / "results" / "regime_card.json"
    out.write_text(json.dumps(card, indent=2))
    print(json.dumps(card, indent=2))
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
