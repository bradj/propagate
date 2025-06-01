.PHONY: build queue web deploy run
build:
	python propagate/build.py
	cp eo/eo.json web/public
	cd web && npm run build

web: build
	cd web && npm run dev

deploy: build
	cd web && rm -Rf dist && npm run build && netlify deploy --prod

queue:
	redis-cli KEYS "*:queue:*" | xargs -n 1 redis-cli LRANGE 0 -1

run:
	python propagate/main.py

run-batch:
	python propagate/main.py batch
