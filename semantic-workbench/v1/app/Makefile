.DEFAULT_GOAL := install

repo_root = $(shell git rev-parse --show-toplevel)

.PHONY: clean
clean:
	$(rm) node_modules || $(true_expression)
	npm cache clean --force

.PHONY: install
install:
	npm install

.PHONY: test
test:
	npm run type-check

.PHONY: format
format:
	npm run format

.PHONY: lint
lint:
	npm run lint

include $(repo_root)/build-tools/makefiles/shell.mk
