.PHONY: lint fmt test ci check smoke

lint:
	ruff check .
	black . --check

fmt:
	ruff check --fix .
	black .

test:
	ruff check .
	black . --check
	python scripts/validate_fly_health.py
	pytest -q

ci:
	$(MAKE) lint
	python scripts/validate_fly_health.py
	pytest -q

check:
	python scripts/validate_fly_health.py

smoke:
	python scripts/smoke_check.py
