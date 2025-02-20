.DEFAULT_GOAL := install

repo_root = $(shell git rev-parse --show-toplevel)

.PHONY: clean
clean:
	$(rm_dir) node_modules $(ignore_failure)

.PHONY: install
install:
	pnpm install

.PHONY: test type-check
test type-check: install
	pnpm run type-check

.PHONY: format
format: install
	pnpm run format

.PHONY: lint
lint: install
	pnpm run lint

.PHONY: start
start:
	pnpm run start

include $(repo_root)/tools/makefiles/shell.mk
