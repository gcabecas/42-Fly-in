MAP ?= maps/easy/01_linear_path.txt
SHOW_ZONE ?=

.PHONY: install run debug clean lint lint-strict

install:
	uv sync

run:
	uv run python -m src.main $(SHOW_ZONE) $(MAP)

debug:
	uv run python -m pdb -m src.main $(SHOW_ZONE) $(MAP)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +

lint:
	uv run flake8 src/
	uv run mypy src/ --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 src/
	uv run mypy src/ --strict
