# How to write a summary

Two to four sentences, roughly an 8th-grade reading level, drafted only from
the Legislative Service Commission (LSC) analysis of the bill.

## Rules

1. **Describe what the bill does, not what it aims to achieve.** "Would require
   businesses to disclose when an AI system is interacting with someone," not
   "Would protect consumers from deceptive AI."
2. **No adjectives about the bill.** Not important, not common-sense, not
   controversial, not overdue. If a word would look like a position, cut it.
3. **No predictions about passage.** Never "is expected to pass," "faces
   opposition," or "has bipartisan support."
4. **"Would," not "will."** A bill that has not become law does not do
   anything yet.
5. **Spell out acronyms on first use.** "Ohio Bureau of Motor Vehicles (BMV)."
6. **Name who acts.** "The Attorney General could bring civil action," not
   "civil action could be brought."
7. **Only the LSC analysis.** Never a press release, advocacy site, news story,
   or the bill's own findings section — each carries framing this site cannot
   adopt.
8. **When the analysis is unclear, write less.** A shorter accurate summary
   beats a longer one you had to guess at. Leaving a bill title-only is always
   an acceptable outcome.
9. **No election language, ever.** No campaign, opponent, election, race,
   endorsement, or link to a campaign site anywhere in this repo.

## The review step

The person who writes a summary is not the person who reviews it. The reviewer
reads the LSC analysis independently and checks each sentence against it, then
puts their own name in `reviewed_by` and the date in `reviewed_on` and commits.

An unreviewed summary is not a smaller problem than a wrong one. The build
refuses to publish either.

## Example

Format only — write your own from the analysis, and never copy a
`reviewed_by` line from an example.

```yaml
# content/summaries/hb32.yaml
bill: HB32
summary: >
  Would add a section to the Revised Code designating the month of July as
  Celebrating Disabilities Month.
source: "LSC Bill Analysis, H. B. No. 32, 136th GA"
source_url: "https://www.legislature.ohio.gov/legislation/136/hb32"
reviewed_by: "A. Student"
reviewed_on: 2026-09-14
```
