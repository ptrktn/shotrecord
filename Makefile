.PHONY: all
all:
	/bin/true

.PHONY: deps
deps: static/d3.min.js
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

.PHONY: cli-deps
cli-deps: deps
	. venv/bin/activate && pip install matplotlib

static/d3.min.js:
	curl -sL https://d3js.org/d3.v7.min.js > $@

.PHONY: run
run:
	. venv/bin/activate && flask run

