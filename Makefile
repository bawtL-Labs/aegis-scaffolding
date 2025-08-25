.PHONY: install-dev run-rel run-api test-core test-all fmt lint

install-dev:
	pip install -e .[dev] -r requirements-lock.txt

run-rel:
	python -m sam.cli start

run-api:
	python -m sam.cli start --api

test-core:
	pytest -q tests/test_psp.py tests/test_vsp_engine.py

test-all:
	pytest -q

fmt:
	ruff format || ruff format

lint:
	ruff check sam tests