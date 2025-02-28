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
	uv run pyinstaller --onefile --name=mcp-server-filesystem --distpath=./dist mcp_server_filesystem/start.py
	$(rm_file) *.spec

clean:
	$(rm_dir) dist $(ignore_failure)
	$(rm_dir) build $(ignore_failure)
