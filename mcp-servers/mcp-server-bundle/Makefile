# Makefile for mcp-server-bundle

# Get the repository root
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk

# Detect OS
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
else
    DETECTED_OS := $(shell uname -s)
endif

.PHONY: package

package: install
ifeq ($(DETECTED_OS),Windows)
	$(MAKE) -C ../mcp-server-filesystem-edit package
endif
	uv run pyinstaller pyinstaller.spec

.PHONY: clean-package

clean: clean-package

clean-package:
	$(rm_dir) dist $(ignore_failure)
	$(rm_dir) build $(ignore_failure)
