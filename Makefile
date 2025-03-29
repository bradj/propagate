.PHONY: build
build:
	python propagate/build.py
	cp eo/eo.json web/public
	cd web && npm run build
