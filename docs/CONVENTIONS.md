# HD6 Bill Tracker

## What this is
A static site listing bills sponsored or cosponsored by Ohio State Rep.
Christine Cockley (District 6), with plain-language summaries and current
status. Plus a CLI that generates her office's monthly newsletter section.
Rebuilt daily by GitHub Actions, served from GitHub Pages. No backend.

## Non-negotiable constraints

1. **No unreviewed summary is ever published.** Summaries live in
   `content/summaries/*.yaml` and require `reviewed_by` and `reviewed_on`
   fields. `summaries.load_all()` raises on any summary missing either, which
   fails the build. There is no flag to override this. Bills without a
   reviewed summary show the official title only.

2. **Summaries derive from LSC analyses.** The Ohio Legislative Service
   Commission publishes a neutral analysis for each bill. That is the source.
   Never summarize from advocacy sites, press releases, or news coverage —
   those carry framing this site must not adopt. Drafts live in
   `content/drafts/` and are not published by anything.

3. **Official, not campaign.** This site describes legislative activity. It
   never uses election language, never mentions opponents, never links to
   cockleyforohio.com, and never characterizes a bill as good or bad. If a
   task would blur that line, stop and ask.

4. **Accessibility is a build gate, not a nice-to-have.** CI runs pa11y
   against every page. A WCAG 2.2 AA violation fails the build. The full bill
   list renders in HTML without JavaScript; filtering is progressive
   enhancement only.

5. **A partial bill list is worse than no build.** The roster is scraped from
   her ohiohouse.gov member page. If the parse yields fewer than
   `fetch.MIN_BILLS` rows, `parse_roster` raises rather than publishing a site
   that understates what she has worked on. Never soften that guard into a
   warning.

## Stack
Python 3.11+, Jinja2, requests, PyYAML, pytest, pa11y (npm, CI only).
No JS framework. No CSS framework. No database. No server. **No API key.**

## Data sources
- **Roster (authoritative):** `ohiohouse.gov/members/christine-cockley/legislation`
  — which bills she is on, primary vs. cosponsor, and the current version.
- **Actions and subjects:** SOLAR API v2 at
  `search-prod.lis.state.oh.us/api/v2/general_assembly_136/`.

LegiScan was the original plan and was dropped. Its free tier needs a key, and
more importantly the SOLAR bulk endpoint that would verify it returns only the
*As Introduced* version of each bill, so its cosponsor lists are frozen at
introduction: on 2026-08-29 it showed her on 76 bills as cosponsor against the
member page's 154. Where sources disagree, ohiohouse.gov wins. See
`docs/HANDOFF.md`.

## Key facts
- General Assembly: 136th (2025–2026)
- Her member_id in the SOLAR API is 3018 (not used by the build; the roster
  page is per-member already)
- 183 items as of 2026-08-29: 29 primary sponsored, 154 cosponsored
- The SOLAR API returns 429 under concurrency — fetch sequentially

## Repo layout
src/tracker/fetch.py       ohiohouse.gov + SOLAR client, disk cache
src/tracker/normalize.py   API response -> internal schema
src/tracker/summaries.py   load + validate reviewed summaries
src/tracker/render.py      Jinja -> static HTML
src/tracker/newsletter.py  monthly digest CLI
src/tracker/draft.py       drafting helper for summary writers
content/summaries/*.yaml   human-reviewed, git-tracked, published
content/drafts/*.yaml      awaiting review, never published
data/snapshot.json         committed daily; the diff IS the changelog
templates/                 Jinja templates
static/                    one CSS file, one small JS file
docs/HANDOFF.md            how the next team takes over

## Conventions
- `data/snapshot.json` is committed on every build. Its git history is the
  bill-status changelog, which is what `newsletter.py` diffs against.
- Status values are the current-version label from ohiohouse.gov, verbatim;
  never invent status labels.
- All dates ISO 8601.
