.PHONY: build queue web
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
