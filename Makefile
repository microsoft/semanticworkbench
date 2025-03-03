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
# Example: "ruff.interpreter": ["${workspaceFolder}/../.venv"],
#

# Define venv directory and python version
VENV_DIR := .venv
PYTHON_VERSION := 3.11

.PHONY: install

# The .venv directory will be created if it doesn't exist
install: $(VENV_DIR)

$(VENV_DIR):
# The required version of python will be installed if it is not already installed
	uv venv --python $(PYTHON_VERSION) $(VENV_DIR)

clean:
	$(rm_dir) $(VENV_DIR) $(ignore_failure)

include $(this_dir)/tools/makefiles/recursive.mk
