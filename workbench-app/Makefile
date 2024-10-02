.DEFAULT_GOAL := install

repo_root = $(shell git rev-parse --show-toplevel)

.PHONY: clean
clean:
	$(rm) node_modules || $(true_expression)

.PHONY: install
install:
	pnpm install

.PHONY: test
test:
	pnpm run type-check

.PHONY: format
format:
	pnpm run format

.PHONY: lint
lint:
	pnpm run lint

include $(repo_root)/tools/makefiles/shell.mk
