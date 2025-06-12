.PHONY: lint fmt test ci

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

ci:
	$(MAKE) lint
	pytest -q
