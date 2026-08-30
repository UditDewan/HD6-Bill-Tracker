"""The roster parser reads someone else's HTML, so it gets a real-markup test."""

from pathlib import Path

import pytest

from src.tracker.fetch import parse_roster

FIXTURE = Path("tests/fixtures/roster.html").read_text(encoding="utf-8")


def test_parses_roles_from_table_captions():
    rows = parse_roster(FIXTURE, minimum=8)
    assert len(rows) == 8
    by_number = {r["number"]: r for r in rows}
    assert by_number["hb32"]["role"] == "primary"
    assert by_number["hb3"]["role"] == "cosponsor"
    # Resolutions are separate tables and must keep their own roles.
    assert by_number["hr38"]["role"] == "primary"
    assert by_number["scr2"]["role"] == "cosponsor"


def test_version_and_title_are_verbatim():
    row = next(r for r in parse_roster(FIXTURE, minimum=8) if r["number"] == "hb32")
    assert row["version"] == "As Reported by the House Health Committee"
    assert row["title"] == "Designate Celebrating Disabilities Month"


def test_layout_change_fails_loudly_instead_of_dropping_bills():
    # The dangerous failure is a silent empty roster, which would publish a
    # site claiming she sponsors nothing.
    with pytest.raises(SystemExit):
        parse_roster("<html><body>redesigned</body></html>")
    with pytest.raises(SystemExit):
        parse_roster(FIXTURE)  # 8 rows, below the default minimum
