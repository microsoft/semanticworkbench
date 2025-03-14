This directory exists to enable certain VSCode extensions to work on multi-root VSCode workspaces.

For example, the Ruff VSCode extension requires a single virtual environment to run Ruff in for the
entire workspace. This directory contains that virtual environment.

To set up the virtual environment, run the following command:
```bash
make install
```

Or just run `make` from the root of the repository.

The workspace needs this directory to be added as a root.
```json
{
    "folders": [
        ...
        {
            "path": ".multi-root-tools"
        },
        ...
    ]
}
```

And for ruff, it needs to be specified as the interpreter:
```json
{
    "settings": {
        "ruff.interpreter": "${workspaceFolder:.multi-root-tools}/.venv"
    }
}
```
