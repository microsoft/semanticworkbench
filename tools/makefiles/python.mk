mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
include $(mkfile_dir)/shell.mk

.DEFAULT_GOAL ?= install

ifdef UV_PROJECT_DIR
uv_project_args = --project $(UV_PROJECT_DIR)
venv_dir = $(UV_PROJECT_DIR)/.venv
else
venv_dir = .venv
endif

UV_SYNC_ARGS ?= --all-extras
UV_RUN_ARGS ?= --all-extras

PYTEST_ARGS ?= --color=yes

## Rules

.PHONY: install
install:
	uv sync $(uv_project_args) $(UV_SYNC_ARGS)

.PHONY: lock
lock:
	uv lock $(uv_project_args) $(UV_LOCK_ARGS)

.PHONY: clean
clean:
	$(rm) $(venv_dir)

.PHONY: lint
lint:
	uvx ruff check --fix .

.PHONY: format
format:
	uvx ruff format .

ifneq ($(findstring pytest,$(if $(shell command -v uv $(stderr_redirect_null)),$(shell uv tree --depth 1),)),)
.PHONY: test
test:
	uv run $(uv_project_args) $(UV_RUN_ARGS) pytest $(PYTEST_ARGS)
endif
