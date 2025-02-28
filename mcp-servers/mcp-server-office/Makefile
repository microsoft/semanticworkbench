repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk

# Check OS and architecture
IS_ARM64 := $(filter ARM64, $(PROCESSOR_ARCHITECTURE) $(PROCESSOR_ARCHITEW6432))

ifneq ($(IS_ARM64),)
	# Does not support ARM64
    override .DEFAULT_GOAL := skip-all
endif

.PHONY: skip-all package

skip-all:
	@echo Only for Windows x64 but "$(OS) $(PROCESSOR_ARCHITECTURE) $(PROCESSOR_ARCHITEW6432)" detected, skipping.

package:
	pyinstaller --onefile --name=mcp-server-office --distpath=./dist mcp_server/start.py
