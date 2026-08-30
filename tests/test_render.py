from pathlib import Path

import pytest

from src.tracker.render import group_by_topic, render
from src.tracker.summaries import UnreviewedSummaryError

FIXTURE = Path("tests/fixtures/snapshot.json")
REVIEWED = """
bill: HB663
summary: Would create a commission to study artificial intelligence and report to the General Assembly.
source: "LSC Bill Analysis, H. B. No. 663, 136th GA"
source_url: "https://www.legislature.ohio.gov/legislation/136/hb663"
reviewed_by: "A. Reviewer"
reviewed_on: 2026-09-14
"""


def build(tmp_path, summary_text=None):
    sdir = tmp_path / "summaries"
    sdir.mkdir()
    if summary_text:
        (sdir / "hb663.yaml").write_text(summary_text, encoding="utf-8")
    out = tmp_path / "site"
    render(snapshot=FIXTURE, out=out, summary_dir=sdir)
    return out


def test_reviewed_summary_publishes(tmp_path):
    page = (build(tmp_path, REVIEWED) / "bills" / "hb663.html").read_text("utf-8")
    assert "commission to study artificial intelligence" in page
    assert "A. Reviewer" in page


def test_bill_without_summary_shows_title_only(tmp_path):
    out = build(tmp_path, REVIEWED)
    page = (out / "bills" / "hb247.html").read_text("utf-8")
    assert "Revise dog law, including dangerous and vicious dogs" in page
    assert "No plain-language summary has been reviewed" in page


def test_unreviewed_summary_fails_the_build(tmp_path):
    with pytest.raises(UnreviewedSummaryError):
        build(tmp_path, REVIEWED.replace('reviewed_by: "A. Reviewer"', ""))


def test_index_lists_every_bill_and_disclaims_officialness(tmp_path):
    index = (build(tmp_path, REVIEWED) / "index.html").read_text("utf-8")
    assert "HB 663" in index and "HB 247" in index
    assert "not an official website" in index


def test_untagged_bills_group_last():
    groups = group_by_topic(
        [{"number": "A", "topics": []}, {"number": "B", "topics": ["health"]}]
    )
    assert list(groups) == ["health", "Other"]
