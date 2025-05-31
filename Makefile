this_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
include $(this_dir)/tools/makefiles/recursive.mk

# AI Context Files Generation - runs at repo root only
.PHONY: ai-context-files
ai-context-files:
	@echo "Building AI context files..."
	@python tools/build_ai_context_files.py
	@echo "AI context files generated in ai_context/generated/"
