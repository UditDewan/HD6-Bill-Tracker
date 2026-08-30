# Drafts

Summaries that have **not** been reviewed. Nothing publishes from this
directory — `render.py` only ever reads `content/summaries/`.

    python -m src.tracker.draft --todo     # what still needs a summary
    python -m src.tracker.draft HB217      # facts + a skeleton in this folder

Write the summary following `docs/STYLE.md`. Then a **different person** reads
the LSC analysis, checks every sentence against it, fills in `reviewed_by` with
their own name and `reviewed_on` with the date, and moves the file:

    git mv content/drafts/hb217.yaml content/summaries/hb217.yaml

That move is the entire publication step, and it is deliberately manual.
