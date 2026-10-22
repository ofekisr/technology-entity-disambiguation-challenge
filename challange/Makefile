PYTHON ?= python3.12
VENV := .venv
BIN := $(VENV)/bin
NAME ?= AWS

.PHONY: setup test resolve eval build validate

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -q -e ".[dev]"

test:
	$(BIN)/python -m pytest -q

resolve:
	@$(BIN)/idx resolve "$(NAME)"

eval:
	@$(BIN)/idx eval

build:
	@$(BIN)/idx build

validate:
	@$(BIN)/idx validate
