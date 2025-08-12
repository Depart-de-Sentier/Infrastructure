.PHONY: build check format ruff-check ruff-format

build:
	python -m build

check: ruff-check
ruff-check:
	ruff check $(TARGET)

format: ruff-format
ruff-format:
	ruff format $(TARGET)
