PYTHON := .venv/bin/python

.PHONY: setup install build queue web deploy run run-batch run-force batch-list batch-status batch-process run-auto run-history test

setup:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

install:
	pip install -e ".[dev]"

build:
	$(PYTHON) propagate/build.py
	cp eo/eo.json web/public
	cd web && npm run build

web: build
	cd web && npm run dev

deploy: build
	cd web && rm -Rf dist && npm run build && netlify deploy --prod

# Standard processing
run:
	$(PYTHON) propagate/main.py

# Process specific president (default: donald-trump)
run-president:
	@read -p "Enter president key (donald-trump, joe-biden, barack-obama, george-w-bush, all): " president; \
	$(PYTHON) propagate/main.py --president $$president

# Force reprocess all orders
run-force:
	$(PYTHON) propagate/main.py --force

# Force reprocess specific president
run-force-president:
	@read -p "Enter president key (donald-trump, joe-biden, barack-obama, george-w-bush, all): " president; \
	$(PYTHON) propagate/main.py --president $$president --force

# Batch processing
run-batch:
	$(PYTHON) propagate/main.py batch

# Batch process specific president
run-batch-president:
	@read -p "Enter president key (donald-trump, joe-biden, barack-obama, george-w-bush, all): " president; \
	$(PYTHON) propagate/main.py batch --president $$president

# Batch process with force
run-batch-force:
	$(PYTHON) propagate/main.py batch --force

# Batch management commands
batch-list:
	$(PYTHON) propagate/batch_manager.py list

batch-status:
	@read -p "Enter batch ID: " batch_id; \
	$(PYTHON) propagate/batch_manager.py status $$batch_id

batch-process:
	@read -p "Enter batch ID: " batch_id; \
	$(PYTHON) propagate/batch_manager.py process $$batch_id

# Automated pipeline
run-auto:
	$(PYTHON) propagate/run.py

# Pipeline run history
run-history:
	$(PYTHON) propagate/run_history.py

# Run tests
test:
	.venv/bin/python -m pytest tests/ -v

.PHONY: fmt
fmt:
	.venv/bin/ruff format propagate/
	.venv/bin/ruff check --fix propagate/

.PHONY: claude
claude:
	claude --setting-sources project,local --model claude-opus-4-6
