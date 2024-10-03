# Semantic Workbench Setup Guide

This document covers the common setup information for the Semantic Workbench.

# Codespaces

We recommend using [GitHub Codespaces for developing with the Semantic Workbench](../.devcontainer/README.md). This will provide a pre-configured environment with all development tools already installed.

# Local Development

## Prerequisites

Recommended installers:

- Linux: apt or your distribution's package manager
- macOS: [brew](https://brew.sh/)
- Windows: [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)

## Development tools

The backend service for the Semantic Workbench is written in Python.

The frontend for the Semantic Workbench is written in Typescript.

The core dependencies you need to install are:

- `make` - for scripting installation steps of the various projects within this repo
- `uv` - for managing installed versions of `python` - for installing python dependencies
- `nvm` - for managing installed versions of `node`
- `pnpm` - for installing node dependencies

Linux:

    # make is installed by default on linux
    sudo apt update && sudo apt install pipx
    pipx ensurepath
    pipx install uv
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

    nvm install 20 lts
    nvm use 20
    npm install -g pnpm

macOS:

    brew install make
    brew install uv
    brew install nvm

    nvm install 20 lts
    nvm use 20
    npm install -g pnpm

Windows:

    winget install ezwinports.make
    winget install --id=astral-sh.uv  -e
    winget install CoreyButler.NVMforWindows

On Windows, exit and restart the VSCode and/or terminal you installed from to re-load your environment
variables and ensure the newly installed apps are available on your PATH.

Windows continued:

    nvm install 20 lts
    nvm use 20
    npm install -g pnpm

If you haven't already, enable long file paths on Windows.

- Run `regedit`.
- Navigate to `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`.
- Find the `LongPathsEnabled` key. If it doesn’t exist, right-click on the `FileSystem` key, select `New > DWORD (32-bit) Value`, and name it `LongPathsEnabled`.
- Double-click on `LongPathsEnabled`, set its value to `1`, and click OK.

### Configure and build the backend

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
npm install -g pnpm
```

### Build the frontend

Within the [`v1/app`](../workbench-app/) directory, install packages.

```
cd workbench-app
make
```
