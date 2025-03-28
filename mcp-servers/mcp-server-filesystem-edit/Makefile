repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk
include $(repo_root)/tools/makefiles/docker-mcp-server.mk

MCP_SERVER_MAIN_MODULE=mcp_server_filesystem_edit.start

# Check OS and architecture
IS_WINDOWS := $(if $(findstring Windows_NT, $(OS)),1,)
IS_NOT_ARM64 := $(if $(findstring ARM64, $(PROCESSOR_ARCHITECTURE) $(PROCESSOR_ARCHITEW6432)),,1)
IS_SUPPORTED_PLATFORM = $(and $(IS_WINDOWS), $(IS_NOT_ARM64))

.PHONY: package skip-package

skip-package:
	$(error Only for Windows x64 but "$(OS) $(PROCESSOR_ARCHITECTURE) $(PROCESSOR_ARCHITEW6432)" detected, skipping.)

package: install
ifneq ($(IS_SUPPORTED_PLATFORM),1)
	$(MAKE) skip-package
endif
	uv run pyinstaller --onefile --name=mcp-server-filesystem-edit --distpath=./dist mcp_server_filesystem_edit/start.py
	$(rm_file) *.spec

# Ensure early exit before running package target if unsupported

.PHONY: clean-package

clean: clean-package

clean-package:
	$(rm_dir) dist $(ignore_failure)
	$(rm_dir) build $(ignore_failure)
