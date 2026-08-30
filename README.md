# HD6 Bill Tracker

Every bill Ohio State Rep. Christine Cockley (House District 6) sponsors or
cosponsors, with current status and — once a second person has reviewed them —
plain-language summaries. A static site, rebuilt daily by GitHub Actions.
**Not an official website of the State of Ohio.**

183 items as of 2026-08-29: 29 primary sponsored, 154 cosponsored.

```
pip install requests jinja2 pyyaml pytest
python -m pytest -q                          # includes the review gate
python -m src.tracker.fetch                  # no API key needed
python -m src.tracker.render                 # -> site/
python -m src.tracker.draft --todo           # what still needs a summary
python -m src.tracker.newsletter --since 2026-08-01
```

Data comes from Rep. Cockley's [ohiohouse.gov member
page](https://ohiohouse.gov/members/christine-cockley/legislation) (the
authoritative roster) and the Ohio Legislature's SOLAR API (action history and
subject tags). Neither needs a key.

**No summary is published without a second person's review.** See
[docs/HANDOFF.md](docs/HANDOFF.md) to run and maintain it,
[docs/STYLE.md](docs/STYLE.md) to write a summary, and [docs/CONVENTIONS.md](docs/CONVENTIONS.md) for the
constraints this project does not bend.
