"""Orchestrator for INTERNALS-BETA-DIAL-PREREG.md REV 2 — the fragility-gauge one-look.

Gating: S7 controls always run (they must run BEFORE the primary is read, and are
NOT the look). H1/H2/H3 on any panel require --confirm-frozen AND a parsed, dated,
named sign-off line in the prereg file (S9: no conversational go-ahead counts).
This script only checks the sign-off line is present and non-blank — it is not a
substitute for actually reading and freezing the prereg; it exists so the primary
result cannot be produced by accident.

Usage:
    python run_internals_prereg.py --controls-only              # always allowed
    python run_internals_prereg.py --confirm-frozen              # full run, all panels
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / ".planning" / "INTERNALS-BETA-DIAL-PREREG.md"
PANELS = ["us", "japan", "europe"]


def check_signoff():
    text = PREREG.read_text(encoding="utf-8")
    m = re.search(r"^SIGN-OFF \(required before run\):\s*(\S.*?)\s+Date:\s*(\S+)\s*$",
                  text, re.MULTILINE)
    if not m or not m.group(1) or not m.group(2):
        return None
    name, date = m.group(1).strip(), m.group(2).strip()
    if name.startswith("_") or date.startswith("_"):
        return None
    return name, date


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm-frozen", action="store_true",
                     help="Run H1/H2/H3 (the actual look). Requires a filled sign-off line.")
    ap.add_argument("--controls-only", action="store_true",
                     help="Run only S7 controls (placebo/ablation) — always permitted.")
    args = ap.parse_args()

    if not args.confirm_frozen and not args.controls_only:
        print("Specify --controls-only or --confirm-frozen.")
        sys.exit(1)

    import internals_controls

    print("Running S7 controls (must pass before the primary is read)...")
    for p in PANELS:
        out = internals_controls.run(p)
        internals_controls.report(p, out)

    if args.controls_only:
        return

    signoff = check_signoff()
    if signoff is None:
        print("\nBLOCKED: no filled sign-off line found in "
              f"{PREREG.relative_to(ROOT)}. Per CLAUDE.md cooling-off rule, a "
              "conversational go-ahead does not count — Adam must edit the SIGN-OFF "
              "line in the prereg file itself (name + date), on a day separate from "
              "FREEZE, before this can run.")
        sys.exit(2)
    name, date = signoff
    print(f"\nSign-off found: {name} ({date}). Proceeding with the one look.")

    import internals_h1
    import internals_h2
    import internals_dial

    for p in PANELS:
        res, _ = internals_h1.run(p)
        internals_h1.report(p, res)
        res2, _, extra2 = internals_h2.run(p)
        internals_h2.report(p, res2, extra2)
        res3 = internals_dial.run(p)
        internals_dial.report(p, res3)


if __name__ == "__main__":
    main()
