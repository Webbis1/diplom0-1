.PHONY: install lint test run docs clean

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -e ".[dev]"

lint:
	$(VENV)/bin/mypy src/
	$(VENV)/bin/ruff check src/

test:
	$(VENV)/bin/pytest

run:
	$(VENV)/bin/python -m src

docs:
	$(VENV)/bin/pyreverse -Amy -o mmd -p diplom src/
	cp classes_diplom.mmd docs/classes_diplom.mmd

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf $(VENV)