from src.tracker.normalize import to_bill

ENTRY = {
    "number": "hb217",
    "role": "primary",
    "title": "Enact the FIND Act",
    "version": "As Passed by the House",
    "subjects": ["State and Local Government"],
    "actions": [
        {"occurred": "2026-03-26T10:00:00-04:00", "chamber": "Senate",
         "description": "Introduced", "cmte_name": ""},
        {"occurred": "2026-03-25T16:00:00-04:00", "chamber": "House",
         "description": "Passed", "cmte_name": None},
        {"occurred": "2026-04-15T09:00:00-04:00", "chamber": "Senate",
         "description": "Refer to Committee", "cmte_name": "General Government"},
    ],
}


def test_history_is_chronological_and_names_the_chamber():
    b = to_bill(ENTRY, {})
    assert [h["date"] for h in b.history] == ["2026-03-25", "2026-03-26", "2026-04-15"]
    # Without the chamber, "Passed" then "Introduced" reads as an error.
    assert b.history[0]["action"] == "Passed (House)"
    assert b.history[1]["action"] == "Introduced (Senate)"
    assert b.history[2]["action"] == "Refer to Committee (Senate, General Government Committee)"


def test_last_action_and_committee_come_from_the_most_recent_activity():
    b = to_bill(ENTRY, {})
    assert b.last_action_date == "2026-04-15"
    assert b.status_date == "2026-04-15"
    assert b.committee == "General Government"


def test_identity_fields():
    b = to_bill(ENTRY, {})
    assert b.number == "HB217"
    assert b.chamber == "house"
    assert b.status == "As Passed by the House"  # verbatim from ohiohouse.gov
    assert b.url == "https://www.legislature.ohio.gov/legislation/136/hb217"
    assert to_bill({**ENTRY, "number": "sb100"}, {}).chamber == "senate"


def test_hand_tags_override_the_legislatures_subjects():
    assert to_bill(ENTRY, {}).topics == ["State and Local Government"]
    assert to_bill(ENTRY, {"HB217": ["housing"]}).topics == ["housing"]


def test_bill_with_no_actions_does_not_crash():
    b = to_bill({**ENTRY, "actions": []}, {})
    assert b.history == [] and b.last_action == "" and b.committee is None


def test_bills_sort_numerically_not_lexically():
    from src.tracker.normalize import sort_key

    numbers = ["HB217", "HB32", "SB6", "HB9"]
    assert sorted(numbers, key=sort_key) == ["HB9", "HB32", "HB217", "SB6"]
