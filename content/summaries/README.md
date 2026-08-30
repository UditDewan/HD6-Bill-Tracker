# Reviewed summaries

One YAML file per bill, named for the bill number in lowercase: `hb32.yaml`.

A file in this directory is published. There is no draft state and no override
flag: `summaries.load_all()` raises `UnreviewedSummaryError` on any file
missing `reviewed_by` or `reviewed_on`, and that fails the build for every
page, not just the one bill. Keep drafts outside this directory until they are
reviewed.

Copy `_template.yaml.example` to start one. Writing rules are in
`docs/STYLE.md`; the review requirement is in `docs/HANDOFF.md`.
