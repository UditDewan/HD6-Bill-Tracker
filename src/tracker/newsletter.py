"""Monthly newsletter section, diffed out of snapshot.json's git history.

    python -m src.tracker.newsletter --since 2026-08-01 --format text
    python -m src.tracker.newsletter --since 2026-08-01 --format html

When git history does not reach back to --since, the state on that date is
reconstructed from each bill's own action dates instead, so this works before
any snapshots have accumulated.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from src.tracker import summaries
from src.tracker.normalize import SNAPSHOT, read_snapshot
from src.tracker.render import display

# Buckets, most newsworthy first. Derived from the action vocabulary the Ohio
# LIS actually uses — as of 2026-08-29 that is: Refer to Committee, Introduced,
# Reported, Passed, Adopted, Concurred in <chamber> amendments, Offered,
# Re-referred. Signing by the Governor does not appear in the actions feed at
# all, which is why enrollment is inferred from the version label instead.
ENROLLED = "Sent to the Governor"
NEW = "Newly introduced"
OTHER = "Other activity"
ORDER = [
    "Signed into law",
    ENROLLED,
    "Passed the House",
    "Passed the Senate",
    "Agreed to the other chamber's amendments",
    "Moved to the Senate",
    "Moved to the House",
    "Reported out of committee",
    "Referred to a committee",
    NEW,
    OTHER,
]
WORDS = ["none", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def _bucket(new: dict, old: dict) -> str:
    """What happened to this bill, from its newest action and version label."""
    action = (new.get("last_action") or "").lower()
    where = ((new.get("history") or [{}])[-1].get("chamber") or "").lower()
    origin = new.get("chamber", "")

    if re.search(r"signed by (the )?governor|filed with the secretary of state", action):
        return "Signed into law"
    if new.get("status") == "As Enrolled" and old.get("status") != "As Enrolled":
        return ENROLLED
    if action.startswith(("passed", "adopted", "informally passed")):
        return "Passed the Senate" if (where or origin) == "senate" else "Passed the House"
    if action.startswith("concurred"):
        return "Agreed to the other chamber's amendments"
    if action.startswith("introduced") and where and where != origin:
        return "Moved to the Senate" if where == "senate" else "Moved to the House"
    if action.startswith("reported"):
        return "Reported out of committee"
    if action.startswith(("refer to committee", "re-referred", "introduced and referred")):
        return "Referred to a committee"
    return OTHER


def changes(old: list[dict], new: list[dict]) -> tuple[dict[str, list[dict]], int]:
    """Group changed bills by what happened; also return the unchanged count."""
    before = {b["number"]: b for b in old}
    groups: dict[str, list[dict]] = {}
    unchanged = 0
    for b in new:
        was = before.get(b["number"])
        if was is None:
            groups.setdefault(NEW, []).append(b)
        elif (b["status"], b["last_action"], b["last_action_date"]) == (
            was["status"],
            was["last_action"],
            was["last_action_date"],
        ):
            unchanged += 1
        else:
            groups.setdefault(_bucket(b, was), []).append(b)
    return {g: groups[g] for g in ORDER if g in groups}, unchanged


def _pretty(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{d:%B} {d.day}"


def _entry(bill: dict, reviewed: dict) -> tuple[str, str]:
    s = reviewed.get(bill["number"])
    blurb = s.summary.strip() if s else bill["title"]
    action = f"{bill['last_action']} ({_pretty(bill['last_action_date'])})."
    return f"{display(bill['number'])} — {blurb}", action


def _unchanged(n: int) -> str:
    return f"{n} bill{'' if n == 1 else 's'} had no change this period."


def render_text(since: str, groups: dict, unchanged: int, reviewed: dict) -> str:
    moved = sum(len(v) for v in groups.values())
    lines = [
        f"Since {_pretty(since)}, {WORDS[moved] if moved < 10 else moved} of "
        f"Rep. Cockley's bills saw activity.",
        "",
    ]
    for group, bills in groups.items():
        lines.append(f"{group}")
        lines.append("")
        for b in bills:
            head, action = _entry(b, reviewed)
            lines += [head, f"  Latest action: {action}", ""]
    if unchanged:
        lines.append(_unchanged(unchanged))
    return "\n".join(lines)


def render_html(since: str, groups: dict, unchanged: int, reviewed: dict) -> str:
    from markupsafe import escape  # ships with Jinja2

    moved = sum(len(v) for v in groups.values())
    out = [
        f"<p>Since {escape(_pretty(since))}, "
        f"{WORDS[moved] if moved < 10 else moved} of Rep. Cockley's bills saw "
        f"activity.</p>"
    ]
    for group, bills in groups.items():
        out.append(f"<h3>{escape(group)}</h3>")
        for b in bills:
            head, action = _entry(b, reviewed)
            out.append(
                f"<p><strong>{escape(head)}</strong><br>"
                f"Latest action: {escape(action)}</p>"
            )
    if unchanged:
        out.append(f"<p>{_unchanged(unchanged)}</p>")
    return "\n".join(out)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def reconstruct(since: str, bills: list[dict]) -> list[dict]:
    """Rebuild the snapshot as of `since` from each bill's own action history.

    For the first months after launch there is no committed snapshot to diff
    against. Every action carries its date, so the past is recoverable: drop
    the actions that had not happened yet. Version labels cannot be rewound, so
    a bill whose only change was a relabel will not appear — actions are what
    the newsletter reports anyway.
    """
    out = []
    for b in bills:
        past = [h for h in b["history"] if h["date"] < since]
        if not past:
            continue  # not introduced yet, so it reads as newly introduced
        out.append(
            {
                **b,
                "history": past,
                "last_action": past[-1]["action"],
                "last_action_date": past[-1]["date"],
                "status_date": past[-1]["date"],
            }
        )
    return out


def snapshot_at(since: str, path: Path = SNAPSHOT) -> list[dict]:
    """The committed snapshot as of the last commit before `since`.

    Falls back to reconstructing it from action history when git does not
    reach that far back, and says so on stderr.
    """
    rev = _git("rev-list", "-1", f"--before={since}", "HEAD", "--", path.as_posix()).strip()
    if rev:
        return json.loads(_git("show", f"{rev}:{path.as_posix()}"))
    print(
        f"No commit of {path.as_posix()} before {since}; reconstructing that "
        f"date from action history instead.",
        file=sys.stderr,
    )
    return reconstruct(since, read_snapshot(path))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--since", required=True, help="ISO date, e.g. 2026-08-01")
    p.add_argument("--format", choices=["text", "html"], default="text")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252

    groups, unchanged = changes(snapshot_at(args.since), read_snapshot())
    reviewed = summaries.load_all()
    render = render_text if args.format == "text" else render_html
    print(render(args.since, groups, unchanged, reviewed))


if __name__ == "__main__":
    main()
