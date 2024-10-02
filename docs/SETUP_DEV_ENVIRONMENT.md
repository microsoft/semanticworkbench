# Semantic Workbench Setup Guide

This document covers the common setup information for the Semantic Workbench.

# Codespaces

We recommend using [GitHub Codespaces for developing with the Semantic Workbench](../.devcontainer/README.md). This will provide a pre-configured environment with VS Code and no additional setup.

# Local Development

## Prerequisites

Recommended installers:

- macOS: [brew](https://brew.sh/)
- Windows: [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
- Linux: apt or your distribution's package manager

## Service Setup

The backend service for the Semantic Workbench is written in Python. Currently we require Python 3.11.

The core dependencies you need to install are: `uv` and `make`.

`uv` will automatically install the correct version of Python for you when you run `uv sync`.

Linux:

     sudo apt update
     sudo apt install pipx
     pipx ensurepath
     pipx install uv

macOS:

      brew install uv
      brew install make

Windows:

      winget install ezwinports.make
      python -m pip install --user pipx
      python -m pipx ensurepath
      pipx install uv

If you haven't already, enable long file paths on Windows.

- Run `regedit`.
- Navigate to `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`.
- Find the `LongPathsEnabled` key. If it doesn’t exist, right-click on the `FileSystem` key, select `New > DWORD (32-bit) Value`, and name it `LongPathsEnabled`.
- Double-click on `LongPathsEnabled`, set its value to `1`, and click OK.

### Configure and build the backend

- Within the [`v1/service`](../workbench-service/) directory, create your virtual environment, and install the service packages:

      make

  If this fails in Windows, try running a vanilla instance of `cmd` or `powershell` and not within `Cmder` or another shell that may have modified the environment.

# Frontend Setup

The frontend for the Semantic Workbench is written in [Node 20](https://nodejs.org/en/download).

Linux ([latest instructions](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating)):

      curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

macOS:

      brew install nvm

Windows:

      winget install CoreyButler.NVMforWindows

Once you have nvm installed:

```
nvm install 20 lts
nvm use 20
```

### Build the frontend

Within the [`v1/app`](../workbench-app/) directory, install packages.

```
cd workbench-app
make
```
