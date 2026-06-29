.PHONY: run test lint

run:
	python -m app.worker

test:
	pytest -q

lint:
	flake8 app tests
