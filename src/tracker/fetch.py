"""Ohio Legislature data. No API key required.

Two public sources, in the order they are trusted:

* ``ohiohouse.gov`` member page — the authoritative roster. Which bills she is
  on, whether as primary sponsor or cosponsor, and the current version of each.
* SOLAR API v2 at ``search-prod.lis.state.oh.us`` — action history per bill and
  the Legislature's own subject tags.

Why the roster is scraped rather than taken from the API: the SOLAR bulk
legislation endpoint returns only the *As Introduced* version of every bill, so
its cosponsor lists and version labels are frozen at introduction. On
2026-08-29 that endpoint listed Rep. Cockley on 76 bills as a cosponsor while
her member page listed 154, because cosponsors sign on after introduction. The
member page is the source the Legislature itself publishes; it wins.

Everything is cached to .cache/ for 20 hours, so a second run in the same day
makes no network calls and development works offline.
"""

import json
import re
import time
from html import unescape
from pathlib import Path

import requests

MEMBER = "christine-cockley"
ROSTER_URL = f"https://ohiohouse.gov/members/{MEMBER}/legislation"
API = "https://search-prod.lis.state.oh.us/api/v2/general_assembly_136"
UA = "HD6-Bill-Tracker/1.0 (volunteer civic project; contact rep06@ohiohouse.gov)"

CACHE = Path(".cache")
MAX_AGE = 20 * 3600  # ponytail: "once a day" = anything older than 20 hours
MIN_BILLS = 50  # a roster smaller than this means the page changed shape

_TABLE = re.compile(r"<caption>(.*?)</caption>(.*?)</table>", re.S)
_ROW = re.compile(
    r'<a href="/legislation/136/([^"]+)">.*?</a>.*?'
    r'<td class="title-cell">(.*?)</td>.*?'
    r'<td class="current-version-cell">(.*?)</td>',
    re.S,
)


def _cached(name: str, url: str) -> str:
    path = CACHE / name
    if path.exists() and time.time() - path.stat().st_mtime < MAX_AGE:
        return path.read_text(encoding="utf-8")
    for attempt in range(5):
        r = requests.get(url, timeout=30, headers={"User-Agent": UA})
        if r.status_code != 429:  # the LIS API rate-limits; back off politely
            break
        time.sleep(2**attempt)
    r.raise_for_status()
    CACHE.mkdir(exist_ok=True)
    path.write_text(r.text, encoding="utf-8")
    return r.text


def parse_roster(page: str, minimum: int = MIN_BILLS) -> list[dict]:
    """Pull bill number, role, title and current version out of the member page.

    Kept separate from the download so it can be tested against a saved copy —
    this regex is the most fragile thing in the codebase, because it depends on
    someone else's HTML.
    """
    out = []
    for caption, body in _TABLE.findall(page):
        role = "primary" if "Primary" in caption else "cosponsor"
        for number, title, version in _ROW.findall(body):
            out.append(
                {
                    "number": number,
                    "role": role,
                    "title": unescape(re.sub(r"<[^>]+>", "", title)).strip(),
                    "version": unescape(version).strip(),
                }
            )
    if len(out) < minimum:
        raise SystemExit(
            f"Only {len(out)} bills parsed from the member page, expected at "
            f"least {minimum}. The page layout probably changed — fix the "
            f"parser in fetch.py before publishing, or the site silently drops "
            f"bills."
        )
    return out


def roster() -> list[dict]:
    """Her bills, with the role she holds on each. Authoritative."""
    return parse_roster(_cached("roster.html", ROSTER_URL))


def subjects() -> dict[str, list[str]]:
    """The Legislature's own subject tags, keyed by bill number."""
    data = json.loads(_cached("legislation.json", f"{API}/legislation/?format=json"))
    return {
        r["number"]: sorted(
            {s["primary"] for s in (r.get("subjects") or []) if s.get("primary")}
        )
        for r in data
    }


def actions(number: str) -> list[dict]:
    return json.loads(
        _cached(f"actions_{number}.json", f"{API}/legislation/{number}/actions/")
    )


def all_bills() -> list[dict]:
    entries = roster()
    subject_tags = subjects()
    # Sequential on purpose: the LIS API returns 429 under concurrency, and a
    # warm cache makes this loop free anyway.
    for i, entry in enumerate(entries, 1):
        entry["subjects"] = subject_tags.get(entry["number"], [])
        entry["actions"] = actions(entry["number"])
        if i % 25 == 0:
            print(f"  {i}/{len(entries)} bills", flush=True)
    return entries


if __name__ == "__main__":
    from src.tracker.normalize import SNAPSHOT, write_snapshot

    bills = write_snapshot(all_bills())
    primary = sum(1 for b in bills if b.role == "primary")
    print(f"wrote {SNAPSHOT}: {len(bills)} bills ({primary} primary, "
          f"{len(bills) - primary} cosponsored)")
