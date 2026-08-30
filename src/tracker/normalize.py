"""Ohio Legislature payloads -> our schema -> data/snapshot.json."""

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

SNAPSHOT = Path("data/snapshot.json")
TOPICS = Path("content/topics.yaml")
GA = 136


@dataclass
class Bill:
    number: str  # "HB663"
    title: str  # official short title, verbatim
    role: str  # "primary" | "cosponsor"
    status: str  # current version label, verbatim from ohiohouse.gov
    status_date: str  # date of the action that produced the current version
    committee: str | None
    chamber: str  # "house" | "senate"
    last_action: str
    last_action_date: str
    url: str  # Ohio LIS canonical URL
    topics: list[str] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)  # for the detail timeline


def sort_key(number: str) -> tuple[str, int]:
    """HB32 sorts before HB217, which string ordering gets backwards."""
    m = re.match(r"([A-Za-z]+)0*(\d+)", number)
    return (m.group(1).upper(), int(m.group(2))) if m else (number.upper(), 0)


def topic_overrides() -> dict[str, list[str]]:
    """Hand-maintained tags that win over the Legislature's subject tags."""
    if not TOPICS.exists():
        return {}
    data = yaml.safe_load(TOPICS.read_text(encoding="utf-8")) or {}
    return {k.upper().replace(" ", ""): v for k, v in data.items()}


def _action_text(a: dict) -> str:
    """Verbatim action, qualified by chamber and committee.

    The chamber matters: a House bill that passes the House is then
    "Introduced" in the Senate, which reads as a mistake without it.
    """
    text = (a.get("description") or a.get("action") or "").strip()
    committee = (a.get("cmte_name") or "").strip()
    where = ", ".join(
        p for p in [(a.get("chamber") or "").strip(), f"{committee} Committee" if committee else ""] if p
    )
    return f"{text} ({where})" if where else text


def to_bill(entry: dict, overrides: dict[str, list[str]] | None = None) -> Bill:
    overrides = topic_overrides() if overrides is None else overrides
    number = entry["number"].upper()
    acts = sorted(entry.get("actions") or [], key=lambda a: a["occurred"])
    history = [
        {
            "date": a["occurred"][:10],
            "chamber": (a.get("chamber") or "").lower(),
            "action": _action_text(a),
        }
        for a in acts
    ]
    last = history[-1] if history else {"date": "", "action": "", "chamber": ""}
    committee = next(
        (a["cmte_name"] for a in reversed(acts) if (a.get("cmte_name") or "").strip()),
        None,
    )
    return Bill(
        number=number,
        title=entry["title"],
        role=entry["role"],
        status=entry["version"],
        status_date=last["date"],
        committee=committee,
        chamber="senate" if number.startswith("S") else "house",
        last_action=last["action"],
        last_action_date=last["date"],
        url=f"https://www.legislature.ohio.gov/legislation/{GA}/{number.lower()}",
        topics=overrides.get(number) or entry.get("subjects") or [],
        history=history,
    )


def write_snapshot(entries: list[dict], path: Path = SNAPSHOT) -> list[Bill]:
    overrides = topic_overrides()
    bills = sorted(
        (to_bill(e, overrides) for e in entries),
        key=lambda b: (b.chamber, sort_key(b.number)),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(b) for b in bills], indent=2) + "\n", encoding="utf-8"
    )
    return bills


def read_snapshot(path: Path = SNAPSHOT) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"{path} does not exist. Run: python -m src.tracker.fetch")
    return json.loads(path.read_text(encoding="utf-8"))
