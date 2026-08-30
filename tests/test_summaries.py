"""The review gate. If these pass and the gate is broken, the tests are wrong."""

import pytest

from src.tracker.summaries import UnreviewedSummaryError, load, load_all

GOOD = """
bill: HB663
summary: Would create a commission to study artificial intelligence and report to the General Assembly.
source: "LSC Bill Analysis, H. B. No. 663, 136th GA"
source_url: "https://www.legislature.ohio.gov/legislation/136/hb663"
reviewed_by: "A. Reviewer"
reviewed_on: 2026-09-14
"""


def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_reviewed_summary_loads(tmp_path):
    s = load(write(tmp_path, "hb663.yaml", GOOD))
    assert s.bill == "HB663"
    assert s.reviewed_by == "A. Reviewer"


@pytest.mark.parametrize("field", ["reviewed_by", "reviewed_on"])
def test_missing_review_field_raises(tmp_path, field):
    text = "\n".join(l for l in GOOD.splitlines() if not l.startswith(field))
    with pytest.raises(UnreviewedSummaryError):
        load(write(tmp_path, "hb663.yaml", text))


@pytest.mark.parametrize("blank", ['reviewed_by: ""', "reviewed_on:"])
def test_blank_review_field_raises(tmp_path, blank):
    field = blank.split(":")[0]
    text = "\n".join(
        blank if l.startswith(field) else l for l in GOOD.splitlines()
    )
    with pytest.raises(UnreviewedSummaryError):
        load(write(tmp_path, "hb663.yaml", text))


def test_one_unreviewed_file_fails_the_whole_load(tmp_path):
    write(tmp_path, "hb663.yaml", GOOD)
    write(tmp_path, "hb247.yaml", GOOD.replace('reviewed_by: "A. Reviewer"', ""))
    with pytest.raises(UnreviewedSummaryError):
        load_all(tmp_path)


def test_shipped_summaries_are_all_reviewed():
    load_all()  # raises if anything in content/summaries/ is unreviewed


def test_drafts_directory_is_never_published():
    """content/drafts holds unreviewed work. Nothing may load it."""
    from pathlib import Path

    from src.tracker import render, summaries

    assert summaries.SUMMARY_DIR == Path("content/summaries")
    assert render.summaries.SUMMARY_DIR != Path("content/drafts")
    # Any draft skeleton that got moved without review would fail this.
    for path in Path("content/drafts").glob("*.yaml"):
        with pytest.raises(UnreviewedSummaryError):
            load(path)


def test_a_reviewed_draft_publishes_with_its_drafting_notes_intact(tmp_path):
    """Publishing is `git mv drafts/ summaries/`, and drafts carry drafted_by."""
    s = load(write(tmp_path, "hb663.yaml", GOOD + 'drafted_by: "D. Drafter"\n'))
    assert s.reviewed_by == "A. Reviewer"


def test_a_summary_missing_a_required_field_fails_the_build(tmp_path):
    text = "\n".join(l for l in GOOD.splitlines() if not l.startswith("source_url"))
    with pytest.raises(SystemExit):
        load(write(tmp_path, "hb663.yaml", text))


def test_two_files_cannot_claim_the_same_bill(tmp_path):
    write(tmp_path, "hb663.yaml", GOOD)
    write(tmp_path, "hb663-old.yaml", GOOD.replace("Would create", "Would also create"))
    with pytest.raises(SystemExit):
        load_all(tmp_path)
