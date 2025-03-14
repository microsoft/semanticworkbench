repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/shell.mk

VENV_DIR := .venv
PYTHON_VERSION := 3.11

.PHONY: install

install: $(VENV_DIR)

$(VENV_DIR):
	uv venv --python $(PYTHON_VERSION) $(VENV_DIR)

.PHONY: clean
clean:
	$(rm_dir) $(VENV_DIR) $(ignore_failure)
