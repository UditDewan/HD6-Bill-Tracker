"""Jinja templates -> static HTML in site/.

Loading summaries raises UnreviewedSummaryError on any file missing review
metadata, so an unreviewed summary fails the build rather than publishing.
"""

import re
import shutil
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.tracker import summaries
from src.tracker.normalize import SNAPSHOT, read_snapshot, sort_key

OUT = Path("site")
TEMPLATES = Path("templates")
STATIC = Path("static")
UNTAGGED = "Other"


def display(number: str) -> str:
    """HB663 -> HB 813."""
    return re.sub(r"^([A-Z]+)(\d+)$", r"\1 \2", number)


def _view(bill: dict, reviewed: dict[str, summaries.Summary]) -> dict:
    s = reviewed.get(bill["number"])
    return {
        **bill,
        "display": display(bill["number"]),
        "slug": bill["number"].lower(),
        "summary": s,
    }


def group_by_topic(bills: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for b in bills:
        for topic in b["topics"] or [UNTAGGED]:
            groups.setdefault(topic, []).append(b)
    for bills_in_topic in groups.values():
        bills_in_topic.sort(key=lambda b: sort_key(b["number"]))
    # Untagged bills group last; every other topic alphabetically.
    return dict(sorted(groups.items(), key=lambda kv: (kv[0] == UNTAGGED, kv[0])))


def render(
    snapshot: Path = SNAPSHOT,
    out: Path = OUT,
    summary_dir: Path = summaries.SUMMARY_DIR,
) -> None:
    reviewed = summaries.load_all(summary_dir)
    bills = [_view(b, reviewed) for b in read_snapshot(snapshot)]
    env = Environment(
        loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape()
    )
    ctx = {
        "built": date.today().isoformat(),
        "bills": bills,
        "primary_count": sum(1 for b in bills if b["role"] == "primary"),
    }

    out.mkdir(parents=True, exist_ok=True)
    (out / "bills").mkdir(exist_ok=True)
    shutil.copytree(STATIC, out / "static", dirs_exist_ok=True)

    (out / "index.html").write_text(
        env.get_template("index.html").render(
            base="", groups=group_by_topic(bills), **ctx
        ),
        encoding="utf-8",
    )
    (out / "about.html").write_text(
        env.get_template("about.html").render(base="", **ctx), encoding="utf-8"
    )
    tpl = env.get_template("bill.html")
    for b in bills:
        (out / "bills" / f"{b['slug']}.html").write_text(
            tpl.render(base="../", bill=b, **ctx), encoding="utf-8"
        )


if __name__ == "__main__":
    render()
    print(f"rendered {len(list(OUT.rglob('*.html')))} pages to {OUT}/")
