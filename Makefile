.PHONY: build clean zip

build:
	python build.py

clean:
	rm -rf dist/ build/ __pycache__ *.pyc

zip: build
	zip -r DJPal-macOS.zip dist/DJPal/
	@echo "Created DJPal-macOS.zip"
