import json
from pathlib import Path

from src.tracker.newsletter import changes, reconstruct, render_html, render_text

OLD = json.loads(Path("tests/fixtures/snapshot.json").read_text("utf-8"))


def acted(number, action, date, chamber="house", **extra):
    """The same bill, one action later."""
    b = dict(next(x for x in OLD if x["number"] == number))
    b.update(
        last_action=action,
        last_action_date=date,
        status_date=date,
        history=b["history"] + [{"date": date, "chamber": chamber, "action": action}],
        **extra,
    )
    return b


def test_unchanged_bills_are_only_counted():
    groups, unchanged = changes(OLD, OLD)
    assert groups == {} and unchanged == 2


def test_passage_is_bucketed_by_the_chamber_that_acted():
    # A House bill that passes the Senate is not "Passed the House". The action's
    # own chamber decides, never the bill's number.
    groups, _ = changes(OLD, [acted("HB663", "Passed (Senate)", "2026-08-20", "senate")])
    assert list(groups) == ["Passed the Senate"]
    groups, _ = changes(OLD, [acted("HB663", "Passed (House)", "2026-08-20", "house")])
    assert list(groups) == ["Passed the House"]


def test_enrollment_reports_once_not_every_build():
    enrolled = acted("HB663", "Concurred in Senate amendments (House)", "2026-08-20",
                     status="As Enrolled")
    groups, _ = changes(OLD, [enrolled])
    assert list(groups) == ["Sent to the Governor"]
    # Already enrolled last time: report the action, not the enrollment again.
    later = acted("HB663", "Passed (House)", "2026-08-25", status="As Enrolled")
    groups, _ = changes([enrolled], [later])
    assert list(groups) == ["Passed the House"]


def test_cross_chamber_move_and_committee_steps():
    groups, _ = changes(OLD, [acted("HB663", "Introduced (Senate)", "2026-08-20", "senate")])
    assert list(groups) == ["Moved to the Senate"]
    groups, _ = changes(OLD, [acted("HB663", "Reported (House, Health Committee)", "2026-08-20")])
    assert list(groups) == ["Reported out of committee"]
    groups, _ = changes(OLD, [acted("HB663", "Refer to Committee (House, Health Committee)", "2026-08-20")])
    assert list(groups) == ["Referred to a committee"]


def test_groups_come_out_in_newsworthiness_order():
    new = [
        acted("HB247", "Refer to Committee (House, Housing Committee)", "2026-08-14"),
        acted("HB663", "Passed (House)", "2026-08-20"),
        {**OLD[0], "number": "HB900", "title": "A new bill"},
    ]
    groups, unchanged = changes(OLD, new)
    assert list(groups) == ["Passed the House", "Referred to a committee", "Newly introduced"]
    assert unchanged == 0


def test_text_output_is_prose_an_aide_can_paste():
    new = [acted("HB663", "Reported (House, Technology Committee)", "2026-08-14"), OLD[1]]
    groups, unchanged = changes(OLD, new)
    text = render_text("2026-08-01", groups, unchanged, {})
    assert text.startswith("Since August 1, one of Rep. Cockley's bills saw activity.")
    assert "HB 663 — Create the Artificial Intelligence Study Commission" in text
    assert "(August 14)" in text
    assert "1 bill had no change" in text  # HB247 unchanged


def test_html_output_escapes_and_fragments():
    new = [acted("HB663", "Reported <of> committee", "2026-08-14")]
    groups, unchanged = changes(OLD, new)
    html = render_html("2026-08-01", groups, unchanged, {})
    assert "&lt;of&gt;" in html
    assert "<html" not in html  # a fragment, not a document


def test_reconstruct_rewinds_history_to_a_past_date():
    bills = [
        {"number": "HB1", "chamber": "house", "status": "As Introduced",
         "last_action": "b", "last_action_date": "2026-08-20", "status_date": "2026-08-20",
         "history": [{"date": "2026-07-01", "chamber": "house", "action": "a"},
                     {"date": "2026-08-20", "chamber": "house", "action": "b"}]},
        {"number": "HB2", "chamber": "house", "status": "As Introduced",
         "last_action": "c", "last_action_date": "2026-08-05", "status_date": "2026-08-05",
         "history": [{"date": "2026-08-05", "chamber": "house", "action": "c"}]},
    ]
    past = reconstruct("2026-08-01", bills)
    # HB2 had no action before the cutoff, so it did not exist yet.
    assert [b["number"] for b in past] == ["HB1"]
    assert past[0]["last_action"] == "a" and past[0]["last_action_date"] == "2026-07-01"

    groups, unchanged = changes(past, bills)
    assert groups["Newly introduced"][0]["number"] == "HB2"
    assert unchanged == 0
