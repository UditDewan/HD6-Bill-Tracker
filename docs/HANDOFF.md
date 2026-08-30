# Handoff

Everything a person with no prior context needs to keep this site running.
Nothing here assumes you were on the team that built it.

## What this is, in one paragraph

A static website. Once a day a GitHub Action reads Rep. Cockley's member page
on ohiohouse.gov and the Ohio Legislature's public API, writes what it finds to
`data/snapshot.json`, commits it, turns it into HTML, checks every page for
accessibility problems, and publishes to GitHub Pages. There is no server, no
database, and **no API key**. The git history of `data/snapshot.json` is the
record of what changed and when, and the newsletter generator reads that
history.

## Run it on your own machine

```
pip install requests jinja2 pyyaml pytest
python -m pytest -q                 # the review gate must pass
python -m src.tracker.fetch         # ~30s cold, writes data/snapshot.json
python -m src.tracker.render        # writes site/
```

Then open `site/index.html`. Fetch caches everything in `.cache/` for 20 hours,
so a second run the same day makes no network calls and you can work offline.
Delete `.cache/` to force a fresh pull.

## Where the data comes from, and why

| What | Source |
|---|---|
| Which bills she is on, primary vs. cosponsor, current version | `ohiohouse.gov/members/christine-cockley/legislation` |
| Action history, committees, subject tags | `search-prod.lis.state.oh.us/api/v2/general_assembly_136/` |

**The member page is authoritative.** The original build plan called for
LegiScan. It was dropped for two reasons: it needs an API key that has to be
rotated and kept out of commits, and the Ohio API that would verify it returns
only the *As Introduced* version of every bill. Because cosponsors sign on
after introduction, that endpoint listed her on 76 bills as cosponsor on
2026-08-29 while her member page listed 154. Any source that is frozen at
introduction will undercount her cosponsorships. If you ever reintroduce
LegiScan, treat it as a cross-check, never as the roster.

## Add or correct a summary

```
python -m src.tracker.draft --todo      # the work queue, bills she leads first
python -m src.tracker.draft HB217       # the facts + a skeleton in content/drafts/
```

1. Open the bill page the tool prints. The **Analysis** tab there is the LSC
   analysis — that is the only source you may summarize from.
2. Write two to four sentences in `content/drafts/hb217.yaml`, following
   `docs/STYLE.md`.
3. A **different person** reads the analysis, checks every sentence against it,
   and fills in `reviewed_by` (their own name) and `reviewed_on` (the date).
4. That person moves the file and commits:
   `git mv content/drafts/hb217.yaml content/summaries/hb217.yaml`
5. The next build publishes it.

If `reviewed_by` or `reviewed_on` is missing or blank, the build fails — for
every page, not just that bill. That is deliberate. There is no override flag,
and adding one would defeat the only safeguard this project has. If you need a
bill published without a summary, leave the YAML in `content/drafts/`: the site
shows the official title, which is always accurate because it comes straight
from the Legislature.

## Force a rebuild

GitHub → the repository → **Actions** → **build** → **Run workflow**. Takes
about four minutes, most of it the accessibility check. Use this after
correcting a summary, or if the site looks stale.

## Correct a wrong bill status

Statuses are not edited by hand — they come from ohiohouse.gov and are
overwritten on every build, so a manual edit disappears the next morning. If a
status is wrong:

1. Check the bill on ohiohouse.gov. That site is authoritative; if it is wrong,
   the tracker will be wrong, and the fix has to happen there.
2. If the tracker disagrees with ohiohouse.gov, that is a bug here. Look at
   `normalize.to_bill` — status is the member page's "Current Version" column
   copied verbatim.
3. If it is urgent, move the bill's summary back to `content/drafts/` so the
   page shows title-only while the status is wrong, and email the office.

## If a data source changes

**Symptom: the build fails on "Fetch bills" with "Only N bills parsed".**
The member page changed shape. Everything that touches its HTML is
`parse_roster` in `src/tracker/fetch.py` — two regexes and about twenty lines,
with a saved copy of the real markup in `tests/fixtures/roster.html` to test
against. Fix the regex, update the fixture, run `pytest`.

That guard exists because the dangerous failure is not a crash — it is a parse
that quietly returns three bills and publishes a site claiming she has barely
worked on anything. **Never lower `MIN_BILLS` to make a build pass.**

**Symptom: the build fails with an HTTP error from search-prod.lis.state.oh.us.**
That API is undocumented and unkeyed. It rate-limits: the fetch is sequential
and backs off on 429 for that reason — do not add concurrency back. If the API
disappears entirely, the site still has bill numbers, titles, roles and
statuses from the member page; only the timeline and subject tags are lost.

The rest of the codebase reads only `data/snapshot.json`, so a change to either
source cannot break rendering.

## Repo access

The repository belongs to a GitHub organization, not to a student account, so
it survives people graduating. Add someone: GitHub → **Settings** → **Access**
→ **Add people**. Keep at least two owners, at least one of whom is not a
student.

_Fill in current access here when you take over:_

- Owners:
- Maintainers:
- Office contact:

## Generate the newsletter section

```
python -m src.tracker.newsletter --since 2026-08-01 --format text
python -m src.tracker.newsletter --since 2026-08-01 --format html
```

`--since` is any date; the generator finds the last committed snapshot before
it and reports what changed. `text` is for pasting into an email; `html` is a
fragment for a newsletter tool. Both are drafts — read them before sending.

It normally diffs against the committed snapshot from before `--since`. When
git history does not reach back that far — the first months after launch — it
reconstructs that date from each bill's own action history instead and says so
on stderr. So it works from day one; it just cannot see version relabels that
happened before the first commit.

## Before this goes live

Open items the build cannot do for itself:

- [ ] **Screen reader pass.** pa11y checks all 185 pages on every build and they
      pass clean, but automated tools miss things. Walk the index, one bill page
      and the About page with NVDA (Windows) or VoiceOver (macOS) once. Check
      that the skip link works, that each bill's number/title/status read in a
      sensible order, and that the filter box announces its result count.
- [ ] **Create the organization and transfer the repository**, then enable
      GitHub Pages (Settings → Pages → Source: GitHub Actions) and run the
      workflow once by hand.
- [ ] **Ask the office which newsletter tool they use** and whether they want
      `--format text` or `--format html`. Ship whichever; both already work.
- [ ] **Write summaries.** Start with the 29 bills she primary sponsors —
      `python -m src.tracker.draft --todo` prints them in order. Until then
      every bill correctly shows title-only.

## For the office: what breaks first if nobody maintains this

**Most likely, in order:**

1. **ohiohouse.gov changes its page layout.** The build fails loudly and stops
   publishing rather than publishing a partial list. The site freezes at its
   last good build. Someone has to fix about twenty lines of code.
2. **The 136th General Assembly ends (December 2026).** The site keeps showing
   136th GA bills forever until someone changes `GA` in
   `src/tracker/normalize.py` and the `API` URL in `src/tracker/fetch.py`.
   Nothing breaks loudly; it just quietly goes out of date.
3. **GitHub Actions disables the schedule.** GitHub turns off scheduled
   workflows in repositories with no activity for 60 days. The footer date
   stops moving. Anyone with access can restart it from the Actions tab.

**The single check to make:** look at the "Last updated" date in the footer of
the site. If it is more than a couple of days old, the automation stopped.

**Nothing here can publish a wrong summary on its own.** Summaries only change
when a person commits one, and the build refuses any that has not been
reviewed. Statuses and titles are copied verbatim from the Legislature's own
pages and are never rewritten. The worst realistic failure is a stale site, not
a false one.
