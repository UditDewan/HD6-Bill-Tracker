fetch:
	python -m src.tracker.fetch

render:
	python -m src.tracker.render

test:
	pytest -q

# make draft BILL=HB663   (omit BILL for the work queue)
draft:
	python -m src.tracker.draft $(BILL)

# make newsletter SINCE=2026-05-01 [FORMAT=html]
newsletter:
	python -m src.tracker.newsletter --since $(SINCE) --format $(or $(FORMAT),text)

# The same accessibility gate CI runs. Needs node.
a11y: render
	python -c "import json,pathlib; print(json.dumps({'defaults':{'concurrency':2,'timeout':60000},'urls':sorted(p.resolve().as_uri() for p in pathlib.Path('site').rglob('*.html'))}))" > pa11yci.json
	npx pa11y-ci --config pa11yci.json --threshold 0

.PHONY: fetch render test draft newsletter a11y
