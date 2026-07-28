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


def build_card():
    dates, states = load_labels()
    card = current_state(dates, states)
    p_stay = stay_probability(states, card["state_code"])
    dwell = dwell_samples(states, card["state_code"])
    gauge = persistence_gauge(p_stay, dwell, card["days_in_state"])
    card["p_stay"] = round(p_stay, 4)
    card["gauge"] = gauge
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
