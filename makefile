.PHONY: run format test lint

run:
	python -m app.worker

format:
	black app config tests

test:
	pytest -q

lint:
	black --check app config tests
	flake8 app config tests
