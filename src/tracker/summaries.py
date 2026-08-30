"""Reviewed plain-language summaries.

This module is the review gate. Nothing else in the codebase is allowed to
read a summary file directly, and there is no flag that skips the check.
"""

from dataclasses import dataclass
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
    return Summary(**data)


def key(number: str) -> str:
    """Bill numbers are keyed as HB663 — uppercase, no spaces."""
    return number.upper().replace(" ", "")


def load_all(directory: Path = SUMMARY_DIR) -> dict[str, Summary]:
    """Every summary in the directory, keyed by bill number.

    Raises on the first unreviewed file, which is what fails the build.
    """
    out: dict[str, Summary] = {}
    for path in sorted(directory.glob("*.yaml")):
        s = load(path)
        out[key(s.bill)] = s
    return out
