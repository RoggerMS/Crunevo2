.PHONY: lint fmt test

lint:
	ruff check .
	black . --check

fmt:
	ruff check --fix .
	black .

test:
	ruff check .
	black . --check
	pytest -q
