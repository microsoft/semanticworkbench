mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
include $(mkfile_dir)/shell.mk

.DEFAULT_GOAL ?= install

ifdef UV_PROJECT_DIR
uv_project_args = --directory $(UV_PROJECT_DIR)
venv_dir = $(UV_PROJECT_DIR)/.venv
else
venv_dir = .venv
endif

UV_SYNC_ARGS ?= --all-extras
UV_RUN_ARGS ?= --all-extras --locked

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
	$(rm_dir) $(venv_dir) $(ignore_failure)

.PHONY: lint
lint:
	uvx ruff check --no-cache --fix .

.PHONY: format
format:
	uvx ruff format --no-cache .

ifneq ($(findstring pytest,$(if $(shell $(call command_exists,uv) $(stderr_redirect_null)),$(shell uv tree --depth 1 $(stderr_redirect_null)),)),)
PYTEST_EXISTS=true
endif
ifneq ($(findstring pyright,$(if $(shell $(call command_exists,uv) $(stderr_redirect_null)),$(shell uv tree --depth 1 $(stderr_redirect_null)),)),)
PYRIGHT_EXISTS=true
endif

ifeq ($(PYRIGHT_EXISTS),true)
.PHONY: type-check test
test: type-check
type-check:
	uv run $(uv_project_args) $(UV_RUN_ARGS) pyright $(PYRIGHT_ARGS)
endif

ifeq ($(PYTEST_EXISTS),true)
.PHONY: test
test:
	uv run $(uv_project_args) $(UV_RUN_ARGS) pytest $(PYTEST_ARGS)
endif
