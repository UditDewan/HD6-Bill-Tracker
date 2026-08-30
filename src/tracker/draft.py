"""Helper for the people writing summaries. Publishes nothing.

    python -m src.tracker.draft --todo      what still needs a summary
    python -m src.tracker.draft HB217       the facts, plus a draft skeleton

Drafts land in content/drafts/. Nothing reads that directory except a human.
To publish one, a *second* person checks it against the LSC analysis, fills in
reviewed_by and reviewed_on, and moves it to content/summaries/.
"""

import argparse
import sys
from pathlib import Path

from src.tracker import summaries
from src.tracker.normalize import read_snapshot, sort_key
from src.tracker.render import display

DRAFTS = Path("content/drafts")

SKELETON = """\
# Draft. Not published. See docs/STYLE.md before writing.
bill: {number}
summary: >
  TODO — two to four sentences, plain language, from the LSC analysis only.
  Say what the bill would do, not what it aims to achieve. Use "would".
source: "LSC Bill Analysis, {display}, 136th GA"
source_url: "{url}"
drafted_by: ""

# A DIFFERENT person checks this against the analysis, puts their own name and
# today's date below, and moves this file to content/summaries/{slug}.yaml.
# Until both fields are filled, the build refuses to publish it.
reviewed_by: ""
reviewed_on:
"""


def todo(bills: list[dict], reviewed: dict) -> list[dict]:
    """Bills with no reviewed summary, the ones she leads first."""
    pending = [b for b in bills if b["number"] not in reviewed]
    return sorted(pending, key=lambda b: (b["role"] != "primary", sort_key(b["number"])))


def show(bill: dict) -> str:
    lines = [
        f"{display(bill['number'])} — {bill['title']}",
        f"  Role       {'Primary sponsor' if bill['role'] == 'primary' else 'Cosponsor'}",
        f"  Version    {bill['status']}",
        f"  Committee  {bill['committee'] or '—'}",
        f"  Topics     {', '.join(bill['topics']) or '—'}",
        "",
        f"  Bill page (the Analysis tab has the LSC analysis):",
        f"    {bill['url']}",
        "",
        "  Recent activity:",
    ]
    lines += [f"    {h['date']}  {h['action']}" for h in bill["history"][-6:]]
    return "\n".join(lines)


def write_skeleton(bill: dict) -> Path:
    DRAFTS.mkdir(parents=True, exist_ok=True)
    path = DRAFTS / f"{bill['number'].lower()}.yaml"
    if not path.exists():
        path.write_text(
            SKELETON.format(
                number=bill["number"],
                display=display(bill["number"]),
                url=bill["url"],
                slug=bill["number"].lower(),
            ),
            encoding="utf-8",
        )
    return path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bill", nargs="?", help="bill number, e.g. HB217")
    p.add_argument("--todo", action="store_true", help="list bills needing a summary")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    bills = read_snapshot()
    reviewed = summaries.load_all()

    if args.todo or not args.bill:
        pending = todo(bills, reviewed)
        primary = [b for b in pending if b["role"] == "primary"]
        print(f"{len(pending)} of {len(bills)} bills have no reviewed summary "
              f"({len(primary)} of them primary sponsored).\n")
        print("Start with these — the bills she is leading:\n")
        for b in primary:
            print(f"  {display(b['number']):<9} {b['title']}")
        print(f"\n...then {len(pending) - len(primary)} cosponsored bills. "
              f"Run: python -m src.tracker.draft <BILL>")
        return

    key = summaries.key(args.bill)
    bill = next((b for b in bills if b["number"] == key), None)
    if bill is None:
        raise SystemExit(f"{args.bill} is not on her roster.")
    print(show(bill))
    if key in reviewed:
        print(f"\n  Already has a reviewed summary "
              f"(by {reviewed[key].reviewed_by} on {reviewed[key].reviewed_on}).")
        return
    print(f"\n  Draft skeleton: {write_skeleton(bill)}")


if __name__ == "__main__":
    main()
