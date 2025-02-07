.DEFAULT_GOAL := install

repo_root = $(shell git rev-parse --show-toplevel)

.PHONY: clean
clean:
	$(rm_dir) node_modules $(ignore_failure)

.PHONY: install
install:
	pnpm install

.PHONY: package
package:
	pnpm run package-extension

include $(repo_root)/tools/makefiles/shell.mk
