.PHONY: test lint format typecheck docs docs-serve codebook install install-dev install-docs clean

# Testing
test:
	uv run python -m pytest

test-v:
	uv run python -m pytest -v

test-unit:
	uv run python -m pytest tests/test_models.py tests/test_eu_models.py tests/test_adapters_eu.py -v

test-integration:
	uv run python -m pytest tests/test_integration_eu.py -v -W ignore::UserWarning

# Code quality
lint:
	uv run ruff check src/

format:
	uv run black src/ tests/

typecheck:
	uv run mypy src/

check: lint typecheck test

# Documentation
docs:
	uv run mkdocs build

docs-serve:
	uv run mkdocs serve

codebook:
	uv run python -c "from openstage.models.eu import EUProcedure; from openstage.models import extract_codebook, codebook_to_markdown; print(codebook_to_markdown(extract_codebook(EUProcedure)))"

# Setup
install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

install-docs:
	uv pip install -e ".[docs]"

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf site/ build/ dist/
