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
	# First build the mcp-servers we are packaging
ifeq ($(DETECTED_OS),Windows)
	$(MAKE) -C ../mcp-server-office package
endif
	$(MAKE) -C ../mcp-server-filesystem package
	uv run pyinstaller pyinstaller.spec

clean:
	$(rm_dir) dist $(ignore_failure)
	$(rm_dir) build $(ignore_failure)
