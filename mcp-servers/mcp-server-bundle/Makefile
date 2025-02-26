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

.PHONY: package package-windows package-macos

# Package target that calls the appropriate OS-specific target
package: install
ifeq ($(DETECTED_OS),Windows)
	$(MAKE) package-windows
else ifeq ($(DETECTED_OS),Darwin)
	$(MAKE) package-macos
else
	@echo "Unsupported OS for packaging: $(DETECTED_OS)"
	@exit 1
endif

# Windows-specific packaging
package-windows:
	uv run pyinstaller pyinstaller.spec
	@echo "Windows package created: dist/mcp-server-bundle.exe"

# macOS-specific packaging
package-macos:
	uv run pyinstaller pyinstaller.spec
	@echo "macOS package created: dist/mcp-server-bundle"

clean:
	$(rm_dir) dist $(ignore_failure)
	$(rm_dir) build $(ignore_failure)
