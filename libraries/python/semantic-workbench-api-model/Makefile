repo_root = $(shell git rev-parse --show-toplevel)

.DEFAULT_GOAL := venv

include $(repo_root)/tools/makefiles/poetry.mk

test: venv
	$(VENV_BIN)/pytest
