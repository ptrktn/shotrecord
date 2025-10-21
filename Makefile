all:
	/bin/true

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

.PHONY: deps
deps: static/d3.min.js

static/d3.min.js:
	curl -sL https://d3js.org/d3.v7.min.js > $@

run: deps
	. venv/bin/activate && flask run

