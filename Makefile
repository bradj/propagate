.PHONY: build queue web deploy run run-batch run-force batch-list batch-status batch-process
build:
	python propagate/build.py
	cp eo/eo.json web/public
	cd web && npm run build

web: build
	cd web && npm run dev

deploy: build
	cd web && rm -Rf dist && npm run build && netlify deploy --prod

# Standard processing
run:
	python propagate/main.py

# Process specific president (default: donald-trump)
run-president:
	@read -p "Enter president key (donald-trump, joe-biden, barack-obama, george-w-bush, all): " president; \
	python propagate/main.py --president $$president

# Force reprocess all orders
run-force:
	python propagate/main.py --force

# Force reprocess specific president
run-force-president:
	@read -p "Enter president key (donald-trump, joe-biden, barack-obama, george-w-bush, all): " president; \
	python propagate/main.py --president $$president --force

# Batch processing
run-batch:
	python propagate/main.py batch

# Batch process specific president
run-batch-president:
	@read -p "Enter president key (donald-trump, joe-biden, barack-obama, george-w-bush, all): " president; \
	python propagate/main.py batch --president $$president

# Batch process with force
run-batch-force:
	python propagate/main.py batch --force

# Batch management commands
batch-list:
	python propagate/batch_manager.py list

batch-status:
	@read -p "Enter batch ID: " batch_id; \
	python propagate/batch_manager.py status $$batch_id

batch-process:
	@read -p "Enter batch ID: " batch_id; \
	python propagate/batch_manager.py process $$batch_id
