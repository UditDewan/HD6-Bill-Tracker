"""Reviewed plain-language summaries.

This module is the review gate. Nothing else in the codebase is allowed to
read a summary file directly, and there is no flag that skips the check.
"""

from dataclasses import dataclass, fields
from datetime import date
from pathlib import Path

import yaml

SUMMARY_DIR = Path("content/summaries")


class UnreviewedSummaryError(Exception):
    """A summary lacks review metadata. It must never reach a rendered page."""


@dataclass(frozen=True)
class Summary:
    bill: str
    summary: str
    source: str
    source_url: str
    reviewed_by: str
    reviewed_on: date


def load(path: Path) -> Summary:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not data.get("reviewed_by") or not data.get("reviewed_on"):
        raise UnreviewedSummaryError(f"{path} lacks review metadata")
    known = {f.name for f in fields(Summary)}
    missing = sorted(known - data.keys())
    if missing:
        raise SystemExit(f"{path} is missing: {', '.join(missing)}")
    # Extra keys are ignored on purpose: a draft is published by moving the
    # file, and the draft skeleton carries drafted_by with it.
    return Summary(**{k: data[k] for k in known})


def key(number: str) -> str:
    """Bill numbers are keyed as HB663 — uppercase, no spaces."""
    return number.upper().replace(" ", "")


def load_all(directory: Path = SUMMARY_DIR) -> dict[str, Summary]:
    """Every summary in the directory, keyed by bill number.

    Raises on the first unreviewed file, which is what fails the build.
    """
    out: dict[str, Summary] = {}
    seen: dict[str, Path] = {}
    for path in sorted(directory.glob("*.yaml")):
        s = load(path)
        k = key(s.bill)
        if k in seen:  # otherwise one reviewed summary silently replaces another
            raise SystemExit(f"{path} and {seen[k]} both claim {k}")
        seen[k] = path
        out[k] = s
    return out
