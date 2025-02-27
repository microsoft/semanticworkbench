this_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

# Some extensions, such as Ruff, try to use python from the first project that is
# loaded in a multi-root workspace. This can cause issues if that project is not
# a python project. To solve this, we can create a python .venv in the root of the
# workspace and use a path of "${workspaceFolder}/../.venv" in the the workspace
# settings.json to force the extension to use the correct python interpreter.
#
# For Ruff issue, see:
# https://github.com/astral-sh/ruff-vscode/issues/653#issuecomment-2684697931
#
# Example: "ruff.interpreter": ["${workspaceFolder}/../.venv/bin/python"],
#

install:
	@if [ ! -d .venv ]; then \
		echo ".venv not found, creating it using uv venv..."; \
		uv venv; \
	else \
		echo ".venv found."; \
	fi

clean:
	$(rm_dir) .venv $(ignore_failure)
	@echo ".venv removed"

include $(this_dir)/tools/makefiles/recursive.mk
