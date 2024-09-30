# If set to true, virtualenvs will be created in the project directory
POETRY_VIRTUALENVS_IN_PROJECT ?= true
ifeq ($(POETRY_VIRTUALENVS_IN_PROJECT),true)
export POETRY_VIRTUALENVS_IN_PROJECT
endif

POETRY_PACKAGE ?= .

install_marker_path = .venv/.install-marker-$(notdir $(abspath $(1)))

## Rules

.PHONY: venv install
venv install: lock $(call install_marker_path,$(POETRY_PACKAGE))

.PHONY: lock
lock:
	poetry --directory=$(POETRY_PACKAGE) lock

$(POETRY_PACKAGE)/poetry.lock: $(POETRY_PACKAGE)/pyproject.toml
	poetry --directory=$(POETRY_PACKAGE) lock

$(call install_marker_path,$(POETRY_PACKAGE)): $(POETRY_PACKAGE)/poetry.lock
	poetry --directory=$(POETRY_PACKAGE) install
	@$(call touch,$@)

.PHONY: clean-venv clean
clean-venv clean:
	poetry --directory=$(POETRY_PACKAGE) env remove --all

DIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(DIR)/shell.mk
