"""Render the assumption ledger and (optionally) email it.

DRY RUN IS THE DEFAULT and works fully offline with no credentials: it builds the ledger
from the committed observation logs, writes both artifacts, and prints the text read.
`--send` attempts delivery and, when the secret is absent, logs and skips rather than
failing - so this is safe to run anywhere, including CI without secrets.

Run:  python scripts/send_ledger.py            # dry run
      python scripts/send_ledger.py --send     # attempt delivery
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mailer
from assumption_ledger import (
    HTML_OUT,
    JSON_OUT,
    build_ledger,
    render_html,
    render_text,
    write_artifacts,
)


def subject_for(ledger: dict) -> str:
    """Dates only. A subject line is the most tempting place in the whole system to put
    a one-word verdict, so it carries none."""
    dates = sorted({
        ev["as_of"]
        for entry in ledger["level1_assumption_ledger"]
        for ev in entry["evidence"]
    })
    span = dates[-1] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}"
    return f"Assumption ledger - observations as of {span}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--send", action="store_true",
        help="attempt delivery; without credentials in the environment it logs and skips",
    )
    ap.add_argument("--known-at", default=None, help="point-in-time replay (available_at <= this)")
    ap.add_argument("--json-out", type=Path, default=JSON_OUT)
    ap.add_argument("--html-out", type=Path, default=HTML_OUT)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    ledger = build_ledger(args.known_at)
    json_out, html_out = write_artifacts(ledger, args.json_out, args.html_out)

    print(render_text(ledger))
    print(f"\nsubject:  {subject_for(ledger)}")
    print(f"wrote     {json_out}")
    print(f"wrote     {html_out}")

    if not args.send:
        print("\ndry run - nothing sent. Re-run with --send to attempt delivery.")
        return 0

    sent = mailer.send_html(subject_for(ledger), render_html(ledger))
    print("sent" if sent else "not sent - see the log line above")
    return 0


if __name__ == "__main__":
    sys.exit(main())
