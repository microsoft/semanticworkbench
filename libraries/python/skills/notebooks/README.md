# MADE: Exploration Skill notebooks

These are Jupyter notebooks for investigating the functionality of the skill
library.

## Environment setup

- Install Python 3.11.
- Install [![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/).
- For simplicity, all of these notebooks share the same python/poetry
  environment, which is managed locally and managed by Poetry. From the notebook
  directory, run `poetry update` to install all python dependencies listed in
  [./pyproject.toml](pyproject.toml) into the [.\.venv](.venv) folder.
- Open this directory as a workspace in VS Code. e.g.,
  `code .\users\papayne\workspaces\notebooks.code-workspace` from the repo root.

## Using a notebook

Just open any `*.ipynb` file (a notebook file) and start exploring via VSCode's
built-in Jupyter Notebook viewers.

### Select the right python (poetry) environment

If you get python dependency errors in the notebook code, make sure you have the
correct python environment activated. A Poetry
[./pyproject.toml](pyproject.toml) is provided that lists all the dependencies.
You can install them however you like to manage your dependencies, but here is
what I do:

- Ctrl-Shift-P > Python:Select Interpreter, select the Notebooks workspace,
  select "Use Python from 'python.defaultInterpreterPath' setting .\.venv".
- Now in your notebook, make sure you select the same python environment from
  the top-right dropdown.
- A cell is at the top of these notebook that will print out the current python
  environment. Make sure it is the local notebooks environment and you should be
  good to go!
