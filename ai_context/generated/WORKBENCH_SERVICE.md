# workbench-service

[collect-files]

**Search:** ['workbench-service']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output', 'devdb', 'migrations/versions']
**Include:** ['pyproject.toml', 'alembic.ini', 'migrations/env.py']
**Date:** 5/29/2025, 11:26:49 AM
**Files:** 59

=== File: workbench-service/.env.example ===
# Description: Example of .env file
# Usage: Copy this file to .env and set the values

# NOTE:
# - Environment variables in the host environment will take precedence over values in this file.
# - When running with VS Code, you must 'stop' and 'start' the process for changes to take effect.
#   It is not enough to just use the VS Code 'restart' button

# Description: Optional environment variables for Azure Speech
# These environment variables are optional and only needed if you wish to provide support for
# speech recognition and synthesis using Azure Speech.
#
# More info: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/overview
#
# After creating a resource, get the resource ID from the Azure portal:
# - Go to the Azure portal at https://portal.azure.com
# - Navigate to the resource group that contains your Speech resource
# - Click on the Speech resource
# - Copy the Resource ID from the Resource > Properties blade
# - Get the region from the Overview blade
#
AZURE_SPEECH__RESOURCE_ID=<YOUR_RESOURCE_ID>
AZURE_SPEECH__REGION=<YOUR_REGION>

# Environment variable to override the default Entra App ID
WORKBENCH__AUTH__ALLOWED_APP_ID=<YOUR_APP_ID>


# Configuration for automatic re-titling of new conversations
# Optional: If they are unset, this feature will be disabled.
#WORKBENCH__SERVICE__AZURE_OPENAI_ENDPOINT=<YOUR_AZURE_OPENAI_ENDPOINT>
#WORKBENCH__SERVICE__AZURE_OPENAI_DEPLOYMENT=<YOUR_AZURE_OPENAI_DEPLOYMENT>
#WORKBENCH__SERVICE__AZURE_OPENAI_MODEL=<YOUR_AZURE_OPENAI_MODEL>


=== File: workbench-service/.vscode/extensions.json ===
{
  "recommendations": [
    "aaron-bond.better-comments",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "epivision.vscode-file-header",
    "esbenp.prettier-vscode",
    "github.vscode-github-actions",
    "ms-azuretools.vscode-docker",
    "ms-python.debugpy",
    "ms-python.python",
    "ms-vscode.makefile-tools",
    "ms-vscode.vscode-node-azure-pack",
    "tamasfe.even-better-toml",
    "streetsidesoftware.code-spell-checker"
  ]
}


=== File: workbench-service/.vscode/launch.json ===
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "debugpy",
      "request": "launch",
      "name": "service: semantic-workbench-service",
      "cwd": "${workspaceFolder}",
      "module": "semantic_workbench_service.start",
      "justMyCode": false,
      "consoleTitle": "semantic-workbench-service"
    }
  ]
}


=== File: workbench-service/.vscode/settings.json ===
{
  "editor.bracketPairColorization.enabled": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll": "explicit"
  },
  "editor.guides.bracketPairs": "active",
  "editor.formatOnPaste": true,
  "editor.formatOnType": true,
  "editor.formatOnSave": true,
  "files.eol": "\n",
  "files.exclude": {
    "**/.git": true,
    "**/.svn": true,
    "**/.hg": true,
    "**/CVS": true,
    "**/.DS_Store": true,
    "**/Thumbs.db": true
  },
  "files.trimTrailingWhitespace": true,
  "flake8.ignorePatterns": ["**/*.py"], // disable flake8 in favor of ruff
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "python.analysis.autoFormatStrings": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.fixAll": ["source.unusedImports"],
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.typeCheckingMode": "standard",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "python.testing.pytestEnabled": true,
  "python.testing.cwd": "${workspaceFolder}",
  "python.testing.pytestArgs": [],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.unusedImports": "explicit",
      "source.organizeImports": "explicit",
      "source.formatDocument": "explicit"
    }
  },
  "ruff.nativeServer": "on",
  "search.exclude": {
    "**/.venv": true,
    "**/.data": true,
    "**/__pycache__": true
  },
  "better-comments.highlightPlainText": true,
  "better-comments.multilineComments": true,
  "better-comments.tags": [
    {
      "tag": "!",
      "color": "#FF2D00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "?",
      "color": "#3498DB",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "//",
      "color": "#474747",
      "strikethrough": true,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "todo",
      "color": "#FF8C00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "fixme",
      "color": "#FF2D00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "*",
      "color": "#98C379",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    }
  ],
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "abcjs",
    "activedescendant",
    "addoption",
    "aiosqlite",
    "aiter",
    "appsettings",
    "arcname",
    "aread",
    "asgi",
    "assistantparticipant",
    "assistantserviceregistration",
    "asyncpg",
    "autoflush",
    "azurewebsites",
    "cachetools",
    "Codespace",
    "Codespaces",
    "cognitiveservices",
    "conversationmessage",
    "conversationrole",
    "conversationshare",
    "conversationshareredemption",
    "datetime",
    "datname",
    "dbaeumer",
    "dbapi",
    "dbtype",
    "deadcode",
    "decompile",
    "deepmerge",
    "devcontainer",
    "devcontainers",
    "devtunnel",
    "dotenv",
    "echosql",
    "endregion",
    "epivision",
    "esbenp",
    "fastapi",
    "fileversion",
    "fluentui",
    "getfixturevalue",
    "griffel",
    "hashkey",
    "httpx",
    "innerjoin",
    "inspectable",
    "isouter",
    "joinedload",
    "jsonable",
    "jsonlogger",
    "jungaretti",
    "jwks",
    "keyvault",
    "Langchain",
    "levelname",
    "levelno",
    "listbox",
    "msal",
    "neato",
    "nonchat",
    "norender",
    "Ofsteps",
    "ondelete",
    "openai",
    "pydantic",
    "pylance",
    "pyproject",
    "pythonjsonlogger",
    "quickstart",
    "raiseerr",
    "reactflow",
    "reduxjs",
    "rehype",
    "rjsf",
    "rootpath",
    "selectin",
    "semanticworkbench",
    "sessionmaker",
    "setenv",
    "sqlalchemy",
    "sqlmodel",
    "sqltypes",
    "stackoverflow",
    "starlette",
    "streamsaver",
    "subprocessor",
    "tabster",
    "tamasfe",
    "tiktoken",
    "toplevel",
    "tracebacks",
    "Typeahead",
    "upscaled",
    "usecwd",
    "userparticipant",
    "uvicorn",
    "virtualenvs",
    "webservice",
    "westus",
    "winget",
    "workbenchservice",
    "workflowdefinition",
    "workflowrun",
    "workflowuserparticipant"
  ]
}


=== File: workbench-service/Dockerfile ===
ARG python_image=python:3.11-slim

FROM ${python_image} AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY ./libraries/python /libraries/python
COPY ./workbench-service /workbench-service

RUN uv sync --directory /workbench-service --no-editable --no-dev --locked

FROM ${python_image}

# BEGIN: enable ssh in azure web app - comment out if not needed
########
# install sshd and set password for root
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && echo "root:Docker!" | chpasswd

# azure sshd config
COPY ./tools/docker/azure_website_sshd.conf /etc/ssh/sshd_config
ENV SSHD_PORT=2222
########
# END: enable ssh in azure web app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /workbench-service/.venv /workbench-service/.venv
ENV PATH=/workbench-service/.venv/bin:$PATH

# alembic migrations related files
COPY ./workbench-service/alembic.ini /workbench-service/alembic.ini
COPY ./workbench-service/migrations /workbench-service/migrations

# entrypoint script
COPY ./tools/docker/docker-entrypoint.sh /scripts/docker-entrypoint.sh
RUN chmod +x /scripts/docker-entrypoint.sh

WORKDIR /workbench-service

ENV workbench__service__host=0.0.0.0
ENV workbench__service__port=3000
ENV PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/scripts/docker-entrypoint.sh"]
CMD ["start-service"]


=== File: workbench-service/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)

include $(repo_root)/tools/makefiles/python.mk

-include ./.env

DBTYPE ?= sqlite

ifeq ($(DBTYPE), postgresql)
WORKBENCH__DB__URL ?= postgresql:///workbench
else
WORKBENCH__DB__URL ?= sqlite:///.data/workbench.db
endif

.PHONY: start
start:
	WORKBENCH__DB__URL="$(WORKBENCH__DB__URL)" uv run start-service

.PHONY: alembic-upgrade-head
alembic-upgrade-head:
	WORKBENCH__DB__URL="$(WORKBENCH__DB__URL)" uv run alembic upgrade head

.PHONY: alembic-generate-migration
alembic-generate-migration:
ifndef migration
	$(info You must provide a name for the migration.)
	$(info ex: make alembic-generate-migration migration="neato changes")
	$(error "migration" is not set)
else
	WORKBENCH__DB__URL="$(WORKBENCH__DB__URL)" uv run alembic revision --autogenerate -m "$(migration)"
endif

DOCKER_PATH = $(repo_root)

docker-%: DOCKER_IMAGE_NAME := workbench

include $(repo_root)/tools/makefiles/docker.mk


=== File: workbench-service/README.md ===
# Semantic Workbench Service

## Architecture

The Semantic Workbench service consists of several key components that interact to provide a seamless user experience:

**Workbench Service**: A backend Python service that handles state management, user interactions, conversation history, file storage, and real-time event distribution.

[**Workbench App**](../workbench-app): A single-page web application written in TypeScript and React that provides the user interface for interacting with assistants.

**FastAPI Framework**: Powers the HTTP API and Server-Sent Events (SSE) for real-time updates between clients and assistants.

**Database Layer**: Uses SQLModel (SQLAlchemy) with support for both SQLite (development) and PostgreSQL (production) for persistent storage.

**Authentication**: Integrated Azure AD/Microsoft authentication with JWT token validation.

**Assistants**: Independently developed services that connect to the Workbench through a RESTful API, enabling AI capabilities.

![Architecture Diagram](../docs/images/architecture-animation.gif)

### Core Components

- **Controller Layer**: Implements business logic for conversations, assistants, files, and users
- **Database Models**: SQLModel-based entities for storing application state
- **Authentication**: Azure AD integration with JWT validation
- **File Storage**: Versioned file system for conversation attachments and artifacts
- **Event System**: Real-time event distribution using Server-Sent Events (SSE)
- **API Layer**: RESTful endpoints for all service operations

### Communication

The communication between the Workbench and Assistants is managed through multiple channels:

1. **HTTP API**: RESTful endpoints for CRUD operations and state management
2. **Server-Sent Events (SSE)**: Real-time event streaming for immediate updates
3. **Event System**: Structured event types (e.g., `message.created`, `conversation.updated`) for real-time state synchronization
4. **Webhook Callbacks**: Assistant registration with callback URLs for event delivery

### Database Structure

The service uses SQLModel to manage structured data:

- **Users**: Authentication and profile information
- **Conversations**: Messaging history and metadata
- **Messages**: Different message types with content and metadata
- **Participants**: Users and assistants in conversations
- **Files**: Versioned attachments for conversations
- **Assistants**: Registered assistants and their configurations
- **Shares**: Conversation sharing capabilities

## Features

### Conversation Management
- Create, update, and delete conversations
- Add and remove participants
- Different message types (chat, note, notice, command)
- Message metadata and debug information

### File Management
- File attachment support
- Versioned file storage
- Multiple content types

### Sharing
- Share conversations with other users
- Public/private share links
- Share redemption

### Integration with Assistants
- Assistant registration and discovery
- API key management for secure communication
- Event-based communication

### Speech Services
- Azure Speech integration for text-to-speech

## Configuration

The service is configured through environment variables:

```
# Basic configuration
WORKBENCH_SERVICE_HOST=127.0.0.1
WORKBENCH_SERVICE_PORT=5000

# Database settings
WORKBENCH_SERVICE_DB_CONNECTION=sqlite+aiosqlite:///./workbench-service.db
# Or for PostgreSQL:
# WORKBENCH_SERVICE_DB_CONNECTION=postgresql+asyncpg://user:pass@host:port/dbname

# Authentication
WORKBENCH_SERVICE_TENANT_ID=your-azure-tenant-id
WORKBENCH_SERVICE_CLIENT_ID=your-client-id

# File storage
WORKBENCH_SERVICE_FILES_DIR=./.data/files
```

See the [environment setup guide](../docs/SETUP_DEV_ENVIRONMENT.md) for complete configuration options.

## Setup Guide

### Prerequisites

- Python 3.11+
- Access to database (SQLite for development, PostgreSQL for production)
- Azure AD application registration (for authentication)

### Installing Dependencies

In the [workbench-service](./) directory:

```sh
make
```

This will use [uv](https://github.com/astral-sh/uv) to install all Python dependencies.

If this fails in Windows, try running a vanilla instance of `cmd` or `powershell` and not within `Cmder` or another shell that may have modified the environment.

### Database Migration

The service uses Alembic for database migrations:

```sh
# Initialize the database
uv run alembic upgrade head
```

### Running from VS Code

To run and/or debug in VS Code:
1. Open the workspace file `semantic-workbench.code-workspace`
2. View->Run
3. Select "service: semantic-workbench-service"

### Running from the Command Line

In the [workbench-service](./) directory:

```sh
uv run start-service [--host HOST] [--port PORT]
```

### Running Tests

```sh
uv run pytest
```

## API Documentation

When running the service, access the FastAPI auto-generated documentation at:

- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

## Troubleshooting

### Common Issues

- **Database connection errors**: Verify your connection string and database permissions
- **Authentication failures**: Check your Azure AD configuration and client IDs
- **File storage permissions**: Ensure the service has write access to the files directory

### Debug Mode

Enable debug logging for more detailed information:

```sh
WORKBENCH_SERVICE_LOG_LEVEL=DEBUG uv run start-service
```

=== File: workbench-service/alembic.ini ===
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = %(here)s/migrations

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# see https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file
# for all available tokens
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python>=3.9 or backports.zoneinfo library.
# Any required deps can installed by adding `alembic[tz]` to the pip requirements
# string value is passed to ZoneInfo()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; This defaults
# to migrations/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path.
# The path separator used here should be the separator specified by "version_path_separator" below.
# version_locations = %(here)s/bar:%(here)s/bat:migrations/versions

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses os.pathsep.
# If this key is omitted entirely, it falls back to the legacy behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.

# set to 'true' to search source files recursively
# in each "version_locations" directory
# new in Alembic version 1.10
# recursive_version_locations = false

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url =


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
hooks = ruff_check, ruff_format

ruff_check.type = exec
ruff_check.executable = uvx
ruff_check.options = ruff check --fix REVISION_SCRIPT_FILENAME

ruff_format.type = exec
ruff_format.executable = uvx
ruff_format.options = ruff format REVISION_SCRIPT_FILENAME


=== File: workbench-service/migrations/README ===
alembic migrations for workbench postgresql db


=== File: workbench-service/migrations/env.py ===
import asyncio
import logging

import semantic_workbench_service
from alembic import context
from rich.logging import RichHandler
from semantic_workbench_service.db import (
    ensure_async_driver_scheme,
)
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config
from sqlmodel import SQLModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_db_url() -> str:
    url = semantic_workbench_service.settings.db.url
    return ensure_async_driver_scheme(url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    url = semantic_workbench_service.settings.db.url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def async_run_migrations_online(connectable) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    async with connectable.connect() as connection:
        await connection.run_sync(run_migrations)

    await connectable.dispose()


def connect() -> AsyncEngine:
    url = get_db_url()
    config_section = config.get_section(config.config_ini_section, {})
    config_section["sqlalchemy.url"] = url
    return async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )


def run_migrations_online():
    if len(logging.root.handlers) == 0:
        logging.basicConfig(
            level=logging.INFO,
            format="%(name)s | %(message)s",
            datefmt="[%X]",
            handlers=[RichHandler()],
        )
        logging.getLogger("sqlalchemy").setLevel(logging.INFO)

    logging.getLogger("alembic").setLevel(logging.INFO)

    connectable = config.attributes.get("connection", None)
    if connectable is None:
        connectable = connect()

    if isinstance(connectable, AsyncEngine):
        return asyncio.run(async_run_migrations_online(connectable))

    run_migrations(connectable)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


=== File: workbench-service/migrations/script.py.mako ===
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}


=== File: workbench-service/migrations/versions/2024_09_19_000000_69dcda481c14_init.py ===
"""init

Revision ID: 69dcda481c14
Revises: None
Create Date: 2024-09-24 18:26:06.987227

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "69dcda481c14"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass


=== File: workbench-service/migrations/versions/2024_09_19_190029_dffb1d7e219a_file_version_filename.py ===
"""upgrades file version storage filename

Revision ID: dffb1d7e219a
Revises: 69dcda481c14
Create Date: 2024-09-19 19:00:29.233114

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from semantic_workbench_service import db
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlmodel import select

# revision identifiers, used by Alembic.
revision: str = "dffb1d7e219a"
down_revision: Union[str, None] = "69dcda481c14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


async def upgrade_file_versions(conn: AsyncConnection) -> None:
    file_version_details = []
    for row in await conn.execute(
        select(db.File.file_id, db.File.filename, db.FileVersion.version).join(db.FileVersion)
    ):
        file_version_details.append((row[0], row[1], row[2]))

    for file_id, filename, version in file_version_details:
        await conn.execute(
            sa.update(db.FileVersion)
            .where(db.FileVersion.file_id == file_id)
            .where(db.FileVersion.version == version)
            .values(storage_filename=f"{file_id.hex}:{filename}:{str(version).zfill(7)}")
        )


def upgrade() -> None:
    op.add_column("fileversion", sa.Column("storage_filename", sqlmodel.AutoString(), nullable=True))
    op.execute("UPDATE fileversion SET storage_filename = ''")
    op.run_async(upgrade_file_versions)
    with op.batch_alter_table("fileversion") as batch_op:
        batch_op.alter_column("storage_filename", nullable=False)


def downgrade() -> None:
    op.drop_column("fileversion", "storage_filename")


=== File: workbench-service/migrations/versions/2024_09_20_204130_b29524775484_share.py ===
"""share

Revision ID: b29524775484
Revises: dffb1d7e219a
Create Date: 2024-09-17 20:41:30.747858

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "b29524775484"
down_revision: Union[str, None] = "dffb1d7e219a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversationshare",
        sa.Column("conversation_share_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("created_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("label", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("conversation_permission", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_redeemable", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.conversation_id"],
            name="fk_file_conversation_id_conversation",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["user.user_id"],
        ),
        sa.PrimaryKeyConstraint("conversation_share_id"),
    )
    op.create_table(
        "conversationshareredemption",
        sa.Column("conversation_share_redemption_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_share_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_permission", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("new_participant", sa.Boolean(), nullable=False),
        sa.Column("redeemed_by_user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_share_id"],
            ["conversationshare.conversation_share_id"],
            name="fk_conversationshareredemption_conversation_share_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["redeemed_by_user_id"],
            ["user.user_id"],
            name="fk_conversationshareredemption_user_id_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("conversation_share_redemption_id"),
    )
    op.add_column("assistant", sa.Column("imported_from_assistant_id", sa.Uuid(), nullable=True))
    op.add_column("conversation", sa.Column("imported_from_conversation_id", sa.Uuid(), nullable=True))
    op.add_column(
        "userparticipant", sa.Column("conversation_permission", sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )
    op.execute("UPDATE userparticipant SET conversation_permission = 'read_write'")
    with op.batch_alter_table("userparticipant") as batch_op:
        batch_op.alter_column("conversation_permission", nullable=False)

    inspector = inspect(op.get_bind())
    uq_constraints = inspector.get_unique_constraints("fileversion")
    if any("uq_fileversion_file_id_version" == uq_constraint["name"] for uq_constraint in uq_constraints):
        with op.batch_alter_table("fileversion") as batch_op:
            batch_op.drop_constraint("uq_fileversion_file_id_version", type_="unique")


def downgrade() -> None:
    op.drop_column("userparticipant", "conversation_permission")
    op.drop_column("conversation", "imported_from_conversation_id")
    op.drop_column("assistant", "imported_from_assistant_id")
    op.drop_table("conversationshareredemption")
    op.drop_table("conversationshare")


=== File: workbench-service/migrations/versions/2024_10_30_231536_039bec8edc33_index_message_type.py ===
"""index message_type

Revision ID: 039bec8edc33
Revises: b29524775484
Create Date: 2024-10-30 23:15:36.240812

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "039bec8edc33"
down_revision: Union[str, None] = "b29524775484"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f("ix_conversationmessage_message_type"), "conversationmessage", ["message_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_conversationmessage_message_type"), table_name="conversationmessage")


=== File: workbench-service/migrations/versions/2024_11_04_204029_5149c7fb5a32_conversationmessagedebug.py ===
"""conversationmessagedebug

Revision ID: 5149c7fb5a32
Revises: 039bec8edc33
Create Date: 2024-11-04 20:40:29.252951

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel as sm
from alembic import op
from semantic_workbench_service import db

# revision identifiers, used by Alembic.
revision: str = "5149c7fb5a32"
down_revision: Union[str, None] = "039bec8edc33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversationmessagedebug",
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["conversationmessage.message_id"],
            name="fk_conversationmessagedebug_message_id_conversationmessage",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("message_id"),
    )

    bind = op.get_bind()
    max_sequence = bind.execute(sm.select(sm.func.max(db.ConversationMessage.sequence))).scalar()
    if max_sequence is not None:
        step = 100
        for sequence_start in range(1, max_sequence + 1, step):
            sequence_end_exclusive = sequence_start + step

            results = bind.execute(
                sm.select(db.ConversationMessage.message_id, db.ConversationMessage.meta_data).where(
                    db.ConversationMessage.sequence >= sequence_start,
                    db.ConversationMessage.sequence < sequence_end_exclusive,
                )
            ).fetchall()

            for message_id, meta_data in results:
                debug = meta_data.pop("debug", None)
                if not debug:
                    continue

                bind.execute(
                    sm.insert(db.ConversationMessageDebug).values(
                        message_id=message_id,
                        data=debug,
                    )
                )

                bind.execute(
                    sm.update(db.ConversationMessage)
                    .where(db.ConversationMessage.message_id == message_id)
                    .values(meta_data=meta_data)
                )


def downgrade() -> None:
    bind = op.get_bind()

    max_sequence = bind.execute(sm.select(sm.func.max(db.ConversationMessage.sequence))).scalar()
    if max_sequence is not None:
        step = 100
        for sequence_start in range(1, max_sequence + 1, step):
            sequence_end_exclusive = sequence_start + step
            results = bind.execute(
                sm.select(
                    db.ConversationMessageDebug.message_id,
                    db.ConversationMessageDebug.data,
                    db.ConversationMessage.meta_data,
                )
                .join(db.ConversationMessage)
                .where(
                    db.ConversationMessage.sequence >= sequence_start,
                    db.ConversationMessage.sequence < sequence_end_exclusive,
                )
            ).fetchall()

            for message_id, debug_data, meta_data in results:
                meta_data["debug"] = debug_data
                bind.execute(
                    sm.update(db.ConversationMessage)
                    .where(db.ConversationMessage.message_id == message_id)
                    .values(meta_data=meta_data)
                )

    op.drop_table("conversationmessagedebug")


=== File: workbench-service/migrations/versions/2024_11_05_015124_245baf258e11_double_check_debugs.py ===
"""double-check debugs

Revision ID: 245baf258e11
Revises: 5149c7fb5a32
Create Date: 2024-11-05 01:51:24.835708

"""

from typing import Sequence, Union

import sqlmodel as sm
from alembic import op
from semantic_workbench_service import db

# revision identifiers, used by Alembic.
revision: str = "245baf258e11"
down_revision: Union[str, None] = "5149c7fb5a32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    max_sequence = bind.execute(sm.select(sm.func.max(db.ConversationMessage.sequence))).scalar()
    if max_sequence is not None:
        step = 100
        for sequence_start in range(1, max_sequence + 1, step):
            sequence_end_exclusive = sequence_start + step

            results = bind.execute(
                sm.select(db.ConversationMessage.message_id, db.ConversationMessage.meta_data).where(
                    db.ConversationMessage.sequence >= sequence_start,
                    db.ConversationMessage.sequence < sequence_end_exclusive,
                )
            ).fetchall()

            for message_id, meta_data in results:
                debug = meta_data.pop("debug", None)
                if not debug:
                    continue

                bind.execute(
                    sm.insert(db.ConversationMessageDebug).values(
                        message_id=message_id,
                        data=debug,
                    )
                )

                bind.execute(
                    sm.update(db.ConversationMessage)
                    .where(db.ConversationMessage.message_id == message_id)
                    .values(meta_data=meta_data)
                )


def downgrade() -> None:
    pass


=== File: workbench-service/migrations/versions/2024_11_25_191056_a106de176394_drop_workflow.py ===
"""drop workflow

Revision ID: a106de176394
Revises: 245baf258e11
Create Date: 2024-11-25 19:10:56.835186

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a106de176394"
down_revision: Union[str, None] = "245baf258e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("workflowuserparticipant")
    op.drop_table("workflowrun")
    op.drop_table("workflowdefinition")

    with op.batch_alter_table("assistantparticipant") as batch_op:
        batch_op.add_column(sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False))

    with op.batch_alter_table("userparticipant") as batch_op:
        batch_op.add_column(sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False))


def downgrade() -> None:
    op.drop_column("userparticipant", "metadata")
    op.drop_column("assistantparticipant", "metadata")
    op.create_table(
        "workflowdefinition",
        sa.Column("workflow_definition_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("data", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("workflow_definition_id", name="workflowdefinition_pkey"),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "workflowuserparticipant",
        sa.Column("workflow_definition_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("image", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("service_user", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("active_participant", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_definition_id"],
            ["workflowdefinition.workflow_definition_id"],
            name="fk_workflowuserparticipant_workflowdefinition",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("workflow_definition_id", "user_id", name="workflowuserparticipant_pkey"),
    )
    op.create_table(
        "workflowrun",
        sa.Column("workflow_run_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("workflow_definition_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("data", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["workflow_definition_id"],
            ["workflowdefinition.workflow_definition_id"],
            name="fk_workflowrun_workflowdefinition",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("workflow_run_id", name="workflowrun_pkey"),
    )


=== File: workbench-service/migrations/versions/2025_03_19_140136_aaaf792d4d72_set_user_title_set.py ===
"""set user_title_set

Revision ID: aaaf792d4d72
Revises: a106de176394
Create Date: 2025-03-19 14:01:36.127350

"""

from typing import Sequence, Union

import sqlmodel as sm
from alembic import op
from semantic_workbench_service import db

# revision identifiers, used by Alembic.
revision: str = "aaaf792d4d72"
down_revision: Union[str, None] = "a106de176394"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Add the __user_title_set key to the meta_data of all conversations to prevent
    # auto-retitling for existing conversations
    for conversation_id, meta_data in bind.execute(
        sm.select(db.Conversation.conversation_id, db.Conversation.meta_data)
    ).yield_per(1):
        meta_data = meta_data or {}
        meta_data["__user_title_set"] = True

        bind.execute(
            sm.update(db.Conversation)
            .where(sm.col(db.Conversation.conversation_id) == conversation_id)
            .values(meta_data=meta_data)
        )


def downgrade() -> None:
    bind = op.get_bind()

    # Drop the __user_title_set key
    for conversation_id, meta_data in bind.execute(
        sm.select(db.Conversation.conversation_id, db.Conversation.meta_data)
    ).yield_per(1):
        meta_data = meta_data or {}
        if not meta_data.pop("__user_title_set", None):
            continue

        bind.execute(
            sm.update(db.Conversation)
            .where(sm.col(db.Conversation.conversation_id) == conversation_id)
            .values(meta_data=meta_data)
        )


=== File: workbench-service/migrations/versions/2025_03_21_153250_3763629295ad_add_assistant_template_id.py ===
"""add template_id

Revision ID: 3763629295ad
Revises: aaaf792d4d72
Create Date: 2025-03-21 15:32:50.919136

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3763629295ad"
down_revision: Union[str, None] = "aaaf792d4d72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("assistant") as batch_op:
        batch_op.add_column(sa.Column("template_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.execute("update assistant set template_id = ' default' where template_id is null")
    with op.batch_alter_table("assistant") as batch_op:
        batch_op.alter_column("template_id", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("assistant") as batch_op:
        batch_op.drop_column("template_id")


=== File: workbench-service/migrations/versions/2025_05_19_163613_b2f86e981885_delete_context_transfer_assistants.py ===
"""delete context transfer assistants

Revision ID: b2f86e981885
Revises: 3763629295ad
Create Date: 2025-05-19 16:36:13.739217

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2f86e981885"
down_revision: Union[str, None] = "3763629295ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM assistant
        WHERE assistant_service_id = 'project-assistant.made-exploration'
        AND template_id = 'context_transfer'
        """
    )
    op.execute(
        """
        UPDATE assistantparticipant
        SET active_participant = false
        WHERE assistant_id NOT IN (
            SELECT assistant_id
            FROM assistant
        )
        """
    )


def downgrade() -> None:
    pass


=== File: workbench-service/pyproject.toml ===
[project]
name = "semantic-workbench-service"
version = "0.1.0"
description = "Library for facilitating the implementation of FastAPI-based Semantic Workbench essistants."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11,<3.13"
dependencies = [
    "aiosqlite~=0.20.0",
    "alembic~=1.13.1",
    "asgi-correlation-id>=4.3.1",
    "asyncpg~=0.29.0",
    "azure-cognitiveservices-speech>=1.41.1",
    "azure-core[aio]>=1.30.0",
    "azure-identity>=1.16.0",
    "azure-keyvault-secrets>=4.8.0",
    "cachetools>=5.3.3",
    "deepmerge>=2.0",
    "fastapi[standard]~=0.115.0",
    "greenlet~=3.0.3",
    "jsonschema>=4.20.0",
    "openai-client>=0.1.0",
    "pydantic-settings>=2.2.0",
    "python-dotenv>=1.0.0",
    "python-jose[cryptography]>=3.3.0",
    "python-json-logger>=2.0.7",
    "rich>=13.7.0",
    "semantic-workbench-api-model>=0.1.0",
    "sqlmodel~=0.0.14",
    "sse-starlette>=1.8.2",
]

[dependency-groups]
dev = [
    "asgi-lifespan>=2.1.0",
    "pyright>=1.1.389",
    "pytest>=7.4.3",
    "pytest-asyncio>=0.23.5.post1",
    "pytest-docker>=3.1.1",
    "pytest-httpx>=0.30.0",
    # semantic-workbench-assistant is used for integration tests
    "semantic-workbench-assistant>=0.1.0",
]

[tool.uv.sources]
openai-client = { path = "../libraries/python/openai-client", editable = true }
semantic-workbench-api-model = { path = "../libraries/python/semantic-workbench-api-model", editable = true }
semantic-workbench-assistant = { path = "../libraries/python/semantic-workbench-assistant", editable = true }

[project.scripts]
start-semantic-workbench-service = "semantic_workbench_service.start:main"
start-service = "semantic_workbench_service.start:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
addopts = "-vv"
log_cli = true
log_cli_level = "WARNING"
log_cli_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"


# fail tests on warnings that aren't explicitly ignored
filterwarnings = [
    "error",
    # stream warnings are from bugs in starlette - hopefully they fix this
    "ignore: Unclosed .MemoryObject(Send|Receive)Stream.:ResourceWarning",
    # aiosqlite doesn't handle cancelations correctly
    "ignore: Exception in thread Thread:pytest.PytestUnhandledThreadExceptionWarning",
    # asyncpg sometimes fails to close sockets/transports/connections
    "ignore: unclosed <socket.socket:ResourceWarning",
    "ignore: unclosed transport:ResourceWarning",
    "ignore: unclosed connection <asyncpg.connection:ResourceWarning",
]


=== File: workbench-service/semantic_workbench_service/__init__.py ===
from . import config

settings = config.Settings()


=== File: workbench-service/semantic_workbench_service/api.py ===
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncContextManager, AsyncGenerator, Callable

from fastapi import FastAPI

logger = logging.getLogger(__name__)


class FastAPILifespan:
    def __init__(self) -> None:
        self._lifecycle_handlers: list[Callable[[], AsyncContextManager[None]]] = []

    def register_handler(self, handler: Callable[[], AsyncContextManager[None]]) -> None:
        self._lifecycle_handlers.append(handler)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        async with AsyncExitStack() as stack:
            logger.debug("app lifespan starting up; title: %s, version: %s", app.title, app.version)

            for handler in self._lifecycle_handlers:
                await stack.enter_async_context(handler())

            logger.info("app lifespan started; title: %s, version: %s", app.title, app.version)

            try:
                yield
            finally:
                logger.debug("app lifespan shutting down; title: %s, version: %s", app.title, app.version)

        logger.info("app lifespan shut down; title: %s, version: %s", app.title, app.version)


=== File: workbench-service/semantic_workbench_service/assistant_api_key.py ===
import hashlib
import logging
import re
import secrets as python_secrets
from typing import Protocol

import cachetools
import cachetools.keys
from azure.core.credentials_async import AsyncTokenCredential
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient

from . import settings

logger = logging.getLogger(__name__)


class ApiKeyStore(Protocol):
    def generate_key_name(self, identifier: str) -> str: ...

    async def get(self, key_name: str) -> str | None: ...

    async def reset(self, key_name: str) -> str: ...

    async def delete(self, key_name: str) -> None: ...


class KeyVaultApiKeyStore(ApiKeyStore):
    """
    Stores API keys in Azure Key Vault.
    """

    def __init__(
        self,
        key_vault_url: str,
        identity: AsyncTokenCredential,
    ) -> None:
        self._secret_client = SecretClient(vault_url=key_vault_url, credential=identity)

    def generate_key_name(self, identifier: str) -> str:
        """
        Generates unique secret name, derived from the identifier, that matches requirements for KeyVault.
        https://azure.github.io/PSRule.Rules.Azure/en/rules/Azure.KeyVault.SecretName/
        - Between 1 and 127 characters long.
        - Alphanumerics and hyphens (dash).
        """
        prefix = "api-key-"
        service_id_hash = hashlib.sha256(identifier.encode()).hexdigest()
        suffix = f"-{service_id_hash}"
        identifier_label_max_length = 127 - len(prefix) - len(suffix)
        identifier_label = re.sub(r"[^a-z0-9-]", "-", identifier)[:identifier_label_max_length]
        secret_name = f"{prefix}{identifier_label}{suffix}"
        assert re.match(r"^[a-z0-9-]{1,127}$", secret_name)
        return secret_name

    async def get(self, key_name: str) -> str | None:
        try:
            secret = await self._secret_client.get_secret(name=key_name)
            return secret.value
        except ResourceNotFoundError:
            return None

    async def reset(self, key_name: str) -> str:
        new_api_key = generate_api_key()
        try:
            await self._secret_client.set_secret(name=key_name, value=new_api_key)
        except ResourceExistsError as e:
            if "deleted" not in e.message:
                raise

            # If the secret is in a deleted state, purge it and create a new one.
            await self._secret_client.purge_deleted_secret(name=key_name)
            await self._secret_client.set_secret(name=key_name, value=new_api_key)

        return new_api_key

    async def delete(self, key_name: str) -> None:
        try:
            deleted_secret = await self._secret_client.delete_secret(name=key_name)
            if deleted_secret.scheduled_purge_date is not None:
                await self._secret_client.purge_deleted_secret(name=key_name)
        except ResourceNotFoundError:
            pass


class FixedApiKeyStore(ApiKeyStore):
    """
    API key store for local development and testing that always returns the same key. Not suitable for production.
    """

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    def generate_key_name(self, identifier: str) -> str:
        return identifier

    async def get(self, key_name: str) -> str | None:
        return self._api_key

    async def reset(self, key_name: str) -> str:
        return self._api_key

    async def delete(self, key_name: str) -> None:
        pass


def cached(api_key_store: ApiKeyStore, max_cache_size: int, ttl_seconds: float) -> ApiKeyStore:
    hash_key = cachetools.keys.hashkey
    cache = cachetools.TTLCache(maxsize=max_cache_size, ttl=ttl_seconds)

    original_get = api_key_store.get
    original_reset = api_key_store.reset
    original_delete = api_key_store.delete

    async def get(key_name: str) -> str | None:
        cache_key = hash_key(key_name)
        if secret := cache.get(cache_key):
            return secret

        secret = await original_get(key_name)
        if secret is not None:
            cache[cache_key] = secret
        return secret

    async def reset(key_name: str) -> str:
        secret = await original_reset(key_name)
        cache_key = hash_key(key_name)
        cache[cache_key] = secret
        return secret

    async def delete(key_name: str) -> None:
        cache_key = hash_key(key_name)
        cache.pop(cache_key, None)
        return await original_delete(key_name)

    api_key_store.get = get
    api_key_store.reset = reset
    api_key_store.delete = delete

    return api_key_store


def get_store() -> ApiKeyStore:
    if settings.service.assistant_api_key.is_secured:
        logger.info("creating KeyVaultApiKeyStore; key vault url: %s", settings.service.assistant_api_key.key_vault_url)
        key_vault_store = KeyVaultApiKeyStore(
            key_vault_url=str(settings.service.assistant_api_key.key_vault_url),
            identity=DefaultAzureCredential(),
        )

        return cached(api_key_store=key_vault_store, max_cache_size=200, ttl_seconds=10 * 60)

    logger.info("creating FixedApiKeyStore for local development and testing")
    return FixedApiKeyStore(api_key="")


def generate_api_key(length: int = 32) -> str:
    return python_secrets.token_urlsafe(length)


=== File: workbench-service/semantic_workbench_service/auth.py ===
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status


@dataclass
class AssistantServicePrincipal:
    assistant_service_id: str


@dataclass
class UserPrincipal:
    user_id: str
    name: str


@dataclass
class AssistantPrincipal(AssistantServicePrincipal):
    assistant_id: uuid.UUID


class ServiceUserPrincipal(UserPrincipal):
    pass


Principal = UserPrincipal | AssistantServicePrincipal

authenticated_principal: ContextVar[Principal | None] = ContextVar("request_principal", default=None)


def _request_principal() -> Principal:
    # the principal is stored in the request state by middle-ware
    principal = authenticated_principal.get()
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return principal


DependsPrincipal = Annotated[Principal, Depends(_request_principal)]


ActorPrincipal = UserPrincipal | AssistantPrincipal


def _actor_principal(principal: DependsPrincipal) -> ActorPrincipal:
    if not isinstance(principal, ActorPrincipal):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return principal


DependsActorPrincipal = Annotated[ActorPrincipal, Depends(_actor_principal)]


def _user_principal(principal: DependsPrincipal) -> UserPrincipal:
    if isinstance(principal, UserPrincipal):
        return principal
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def _assistant_service_principal(principal: DependsPrincipal) -> AssistantServicePrincipal:
    if isinstance(principal, AssistantServicePrincipal):
        return principal
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def _assistant_principal(principal: DependsPrincipal) -> AssistantPrincipal:
    if isinstance(principal, AssistantPrincipal):
        return principal
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


DependsAssistantServicePrincipal = Annotated[AssistantServicePrincipal, Depends(_assistant_service_principal)]
DependsAssistantPrincipal = Annotated[AssistantPrincipal, Depends(_assistant_principal)]
DependsUserPrincipal = Annotated[UserPrincipal, Depends(_user_principal)]


=== File: workbench-service/semantic_workbench_service/azure_speech.py ===
import logging

from azure.identity import DefaultAzureCredential

from . import settings

logger = logging.getLogger(__name__)


def get_token() -> dict[str, str]:
    if settings.azure_speech.resource_id == "" or settings.azure_speech.region == "":
        return {}

    credential = DefaultAzureCredential()
    try:
        token = credential.get_token("https://cognitiveservices.azure.com/.default").token
    except Exception as e:
        logger.error(f"Failed to get token: {e}")
        return {}

    return {
        "token": f"aad#{settings.azure_speech.resource_id}#{token}",
        "region": settings.azure_speech.region,
    }


=== File: workbench-service/semantic_workbench_service/config.py ===
from typing import Annotated

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from .files import StorageSettings
from .logging_config import LoggingSettings


class DBSettings(BaseSettings):
    url: str = "sqlite:///.data/workbench.db"
    echosql: bool = False
    postgresql_ssl_mode: str = "require"
    postgresql_pool_size: int = 10
    alembic_config_path: str = "./alembic.ini"


class ApiKeySettings(BaseSettings):
    key_vault_url: HttpUrl | None = None

    @property
    def is_secured(self) -> bool:
        return self.key_vault_url is not None


class AuthSettings(BaseSettings):
    allowed_jwt_algorithms: set[str] = {"RS256"}
    allowed_app_id: str = "22cb77c3-ca98-4a26-b4db-ac4dcecba690"


class AssistantIdentifiers(BaseSettings):
    assistant_service_id: str
    template_id: str
    name: str


class WebServiceSettings(BaseSettings):
    protocol: str = "http"
    host: str = "127.0.0.1"
    port: int = 3000

    assistant_api_key: ApiKeySettings = ApiKeySettings()

    anonymous_paths: list[str] = ["/", "/docs", "/openapi.json"]

    assistant_service_online_check_interval_seconds: float = 10.0

    azure_openai_endpoint: Annotated[str, Field(validation_alias="azure_openai_endpoint")] = ""
    azure_openai_deployment: Annotated[str, Field(validation_alias="azure_openai_deployment")] = "gpt-4o-mini"
    azure_openai_model: Annotated[str, Field(validation_alias="azure_openai_model")] = "gpt-4o-mini"
    azure_openai_api_version: Annotated[str, Field(validation_alias="azure_openai_api_version")] = "2025-02-01-preview"

    default_assistants: list[AssistantIdentifiers] = []


class AzureSpeechSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="azure_speech__", env_nested_delimiter="_", env_file=".env", extra="allow"
    )

    resource_id: str = ""
    region: str = ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="workbench__", env_nested_delimiter="__", env_file=".env", extra="allow"
    )

    db: DBSettings = DBSettings()
    storage: StorageSettings = StorageSettings()
    logging: LoggingSettings = LoggingSettings()
    service: WebServiceSettings = WebServiceSettings()
    azure_speech: AzureSpeechSettings = AzureSpeechSettings()
    auth: AuthSettings = AuthSettings()


if __name__ == "__main__":
    # for verifying environment variables are having the expected effect
    settings = Settings()
    print(settings.model_dump())


=== File: workbench-service/semantic_workbench_service/controller/__init__.py ===
from . import participant, user
from .assistant import AssistantController
from .assistant_service_client_pool import AssistantServiceClientPool
from .assistant_service_registration import AssistantServiceRegistrationController
from .conversation import ConversationController
from .conversation_share import ConversationShareController
from .exceptions import (
    ConflictError,
    Error,
    ForbiddenError,
    InvalidArgumentError,
    NotFoundError,
)
from .file import FileController
from .user import UserController

__all__ = [
    "AssistantController",
    "AssistantServiceRegistrationController",
    "AssistantServiceClientPool",
    "ConversationController",
    "ConversationShareController",
    "ForbiddenError",
    "FileController",
    "InvalidArgumentError",
    "ConflictError",
    "Error",
    "NotFoundError",
    "user",
    "participant",
    "UserController",
]


=== File: workbench-service/semantic_workbench_service/controller/assistant.py ===
import asyncio
import datetime
import io
import logging
import pathlib
import re
import shutil
import tempfile
import uuid
import zipfile
from typing import IO, AsyncContextManager, Awaitable, BinaryIO, Callable, NamedTuple

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError
from semantic_workbench_api_model.assistant_model import (
    AssistantPutRequestModel,
    ConfigPutRequestModel,
    ConfigResponseModel,
    ConversationPutRequestModel,
    StateDescriptionListResponseModel,
    StatePutRequestModel,
    StateResponseModel,
)
from semantic_workbench_api_model.assistant_service_client import (
    AssistantError,
)
from semantic_workbench_api_model.workbench_model import (
    Assistant,
    AssistantList,
    AssistantStateEvent,
    ConversationEvent,
    ConversationEventType,
    ConversationImportResult,
    NewAssistant,
    NewConversation,
    UpdateAssistant,
)
from sqlalchemy.orm import joinedload
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, files, query, settings
from ..event import ConversationEventQueueItem
from . import convert, exceptions, export_import
from . import participant as participant_
from . import user as user_
from .assistant_service_client_pool import AssistantServiceClientPool

logger = logging.getLogger(__name__)


ExportResult = NamedTuple(
    "ExportResult",
    [("file_path", str), ("content_type", str), ("filename", str), ("cleanup", Callable[[], None])],
)


class AssistantController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
        client_pool: AssistantServiceClientPool,
        file_storage: files.Storage,
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event
        self._client_pool = client_pool
        self._file_storage = file_storage

    async def _ensure_assistant(
        self,
        session: AsyncSession,
        assistant_id: uuid.UUID,
        principal: auth.AssistantPrincipal | auth.UserPrincipal,
        include_assistants_from_conversations: bool = False,
    ) -> db.Assistant:
        match principal:
            case auth.UserPrincipal():
                assistant = (
                    await session.exec(
                        query.select_assistants_for(
                            user_principal=principal,
                            include_assistants_from_conversations=include_assistants_from_conversations,
                        ).where(db.Assistant.assistant_id == assistant_id)
                    )
                ).one_or_none()

            case auth.AssistantPrincipal():
                assistant = (
                    await session.exec(
                        query.select(db.Assistant)
                        .where(db.Assistant.assistant_id == assistant_id)
                        .where(db.Assistant.assistant_id == principal.assistant_id)
                        .where(db.Assistant.assistant_service_id == principal.assistant_service_id)
                    )
                ).one_or_none()

        if assistant is None:
            raise exceptions.NotFoundError()

        return assistant

    async def _ensure_assistant_conversation(
        self, session: AsyncSession, assistant: db.Assistant, conversation_id: uuid.UUID
    ) -> db.Conversation:
        conversation = (
            await session.exec(
                query.select_conversations_for(
                    principal=auth.AssistantPrincipal(
                        assistant_service_id=assistant.assistant_service_id, assistant_id=assistant.assistant_id
                    )
                ).where(db.Conversation.conversation_id == conversation_id)
            )
        ).one_or_none()
        if conversation is None:
            raise exceptions.NotFoundError()

        return conversation

    async def _put_assistant(self, assistant: db.Assistant, from_export: IO[bytes] | None) -> None:
        await (
            await self._client_pool.service_client(
                registration=assistant.related_assistant_service_registration,
            )
        ).put_assistant(
            assistant_id=assistant.assistant_id,
            request=AssistantPutRequestModel(assistant_name=assistant.name, template_id=assistant.template_id),
            from_export=from_export,
        )

    async def forward_event_to_assistant(self, assistant_id: uuid.UUID, event: ConversationEvent) -> None:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    select(db.Assistant)
                    .where(db.Assistant.assistant_id == assistant_id)
                    .options(joinedload(db.Assistant.related_assistant_service_registration, innerjoin=True))
                )
            ).one()

        try:
            await (await self._client_pool.assistant_client(assistant)).post_conversation_event(event=event)
        except AssistantError as e:
            if e.status_code != httpx.codes.NOT_FOUND:
                logger.exception(
                    "error forwarding event to assistant; assistant_id: %s, conversation_id: %s, event: %s",
                    assistant.assistant_id,
                    event.conversation_id,
                    event,
                )

    async def _remove_assistant_from_conversation(
        self,
        session: AsyncSession,
        assistant: db.Assistant,
        conversation_id: uuid.UUID,
    ) -> None:
        try:
            await self.disconnect_assistant_from_conversation(conversation_id=conversation_id, assistant=assistant)
        except AssistantError:
            logger.error("error disconnecting assistant", exc_info=True)

        for participant in await session.exec(
            select(db.AssistantParticipant)
            .where(
                db.AssistantParticipant.conversation_id == conversation_id,
                db.AssistantParticipant.assistant_id == assistant.assistant_id,
                col(db.AssistantParticipant.active_participant).is_(True),
            )
            .with_for_update()
        ):
            participant.active_participant = False
            session.add(participant)

            participants = await participant_.get_conversation_participants(
                session=session, conversation_id=conversation_id, include_inactive=True
            )
            await self._notify_event(
                ConversationEventQueueItem(
                    event=participant_.participant_event(
                        event_type=ConversationEventType.participant_updated,
                        conversation_id=conversation_id,
                        participant=convert.conversation_participant_from_db_assistant(
                            participant, assistant=assistant
                        ),
                        participants=participants,
                    )
                )
            )

        await session.flush()

    async def disconnect_assistant_from_conversation(self, conversation_id: uuid.UUID, assistant: db.Assistant) -> None:
        await (await self._client_pool.assistant_client(assistant)).delete_conversation(conversation_id=conversation_id)

    async def connect_assistant_to_conversation(
        self, conversation: db.Conversation, assistant: db.Assistant, from_export: IO[bytes] | None
    ) -> None:
        await (await self._client_pool.assistant_client(assistant)).put_conversation(
            ConversationPutRequestModel(id=str(conversation.conversation_id), title=conversation.title),
            from_export=from_export,
        )

    async def create_assistant(
        self,
        new_assistant: NewAssistant,
        user_principal: auth.UserPrincipal,
    ) -> Assistant:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            assistant_service = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == new_assistant.assistant_service_id
                    )
                )
            ).one_or_none()
            if assistant_service is None:
                raise exceptions.InvalidArgumentError(
                    detail=f"assistant service id {new_assistant.assistant_service_id} is not valid"
                )

            if not assistant_service.assistant_service_online:
                raise exceptions.InvalidArgumentError(
                    detail=(
                        f"assistant service '{assistant_service.name}' ({assistant_service.assistant_service_id}) is"
                        " currently offline"
                    )
                )

            if not new_assistant.image:
                try:
                    # fallback to the participant icon if the assistant service has one in metadata
                    service_info = await (
                        await self._client_pool.service_client(
                            registration=assistant_service,
                        )
                    ).get_service_info()
                except AssistantError:
                    logger.exception("error getting assistant service info")
                else:
                    dashboard_card_config = service_info.metadata.get("_dashboard_card", {})
                    if isinstance(dashboard_card_config, dict):

                        class DashboardCardConfig(BaseModel):
                            model_config = ConfigDict(extra="allow")
                            icon: str

                        template_config = dashboard_card_config.get(new_assistant.template_id)
                        if template_config:
                            try:
                                template_config = DashboardCardConfig.model_validate(template_config)
                                new_assistant.image = template_config.icon
                            except ValidationError:
                                logger.error(
                                    "error validating dashboard card config for assistant service %s",
                                    assistant_service.name,
                                )

            assistant = db.Assistant(
                owner_id=user_principal.user_id,
                name=new_assistant.name,
                image=new_assistant.image,
                meta_data=new_assistant.metadata,
                assistant_service_id=assistant_service.assistant_service_id,
                template_id=new_assistant.template_id,
                imported_from_assistant_id=None,
            )
            session.add(assistant)
            await session.commit()
            await session.refresh(assistant)

            try:
                await self._put_assistant(assistant=assistant, from_export=None)
            except AssistantError:
                logger.error("error creating assistant", exc_info=True)
                await session.delete(assistant)
                await session.commit()
                raise

        return await self.get_assistant(user_principal=user_principal, assistant_id=assistant.assistant_id)

    async def update_assistant(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        update_assistant: UpdateAssistant,
    ) -> Assistant:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    query.select_assistants_for(
                        user_principal=user_principal,
                    )
                    .where(db.Assistant.assistant_id == assistant_id)
                    .with_for_update()
                )
            ).one_or_none()
            if assistant is None:
                raise exceptions.NotFoundError()

            assistant_service = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant.assistant_service_id
                    )
                )
            ).one()
            if not assistant_service.assistant_service_online:
                raise exceptions.InvalidArgumentError(
                    detail=f"assistant service '{assistant_service.name}' is currently offline"
                )

            updates = update_assistant.model_dump(exclude_unset=True)
            for field, value in updates.items():
                match field:
                    case "metadata":
                        assistant.meta_data = value
                    case _:
                        setattr(assistant, field, value)

            session.add(assistant)

            try:
                await self._put_assistant(assistant=assistant, from_export=None)
            except AssistantError:
                logger.error("error updating assistant", exc_info=True)
                raise

            await session.commit()
            await session.refresh(assistant)

        return await self.get_assistant(user_principal=user_principal, assistant_id=assistant.assistant_id)

    async def delete_assistant(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> None:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    query.select_assistants_for(
                        user_principal=user_principal,
                    )
                    .where(db.Assistant.assistant_id == assistant_id)
                    .with_for_update()
                )
            ).one_or_none()
            if assistant is None:
                raise exceptions.NotFoundError()

            conversations = (
                await session.exec(
                    select(db.Conversation)
                    .join(db.AssistantParticipant)
                    .where(
                        db.AssistantParticipant.assistant_id == assistant_id,
                        col(db.AssistantParticipant.active_participant).is_(True),
                    )
                )
            ).all()

            for conversation in conversations:
                await self._remove_assistant_from_conversation(
                    session=session,
                    assistant=assistant,
                    conversation_id=conversation.conversation_id,
                )

            try:
                await (
                    await self._client_pool.service_client(assistant.related_assistant_service_registration)
                ).delete_assistant(assistant_id=assistant.assistant_id)

            except AssistantError:
                logger.exception("error disconnecting assistant")

            await session.delete(assistant)
            await session.commit()

    async def get_assistants(
        self,
        user_principal: auth.UserPrincipal,
        conversation_id: uuid.UUID | None = None,
    ) -> AssistantList:
        async with self._get_session() as session:
            if conversation_id is None:
                await self._create_default_user_assistants(user_principal=user_principal)

                assistants = (
                    await session.exec(
                        query.select_assistants_for(user_principal=user_principal).order_by(
                            col(db.Assistant.created_datetime).desc(),
                            col(db.Assistant.name).asc(),
                        )
                    )
                ).all()

                return convert.assistant_list_from_db(models=assistants)

            conversation = (
                await session.exec(
                    query.select_conversations_for(
                        principal=user_principal, include_all_owned=True, include_observer=True
                    ).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            assistants = await session.exec(
                select(db.Assistant)
                .join(
                    db.AssistantParticipant, col(db.Assistant.assistant_id) == col(db.AssistantParticipant.assistant_id)
                )
                .where(col(db.AssistantParticipant.active_participant).is_(True))
                .where(db.AssistantParticipant.conversation_id == conversation_id)
            )

            return convert.assistant_list_from_db(models=assistants)

    async def _create_default_user_assistants(
        self,
        user_principal: auth.UserPrincipal,
    ) -> None:
        """Create default assistants for the user if they don't already exist."""
        async with self._get_session() as session:
            for identifiers in settings.service.default_assistants:
                existing_assistant = (
                    await session.exec(
                        query.select_assistants_for(user_principal=user_principal).where(
                            db.Assistant.assistant_service_id == identifiers.assistant_service_id,
                            db.Assistant.template_id == identifiers.template_id,
                        )
                    )
                ).first()

                if existing_assistant is not None:
                    continue

                assistant_service = (
                    await session.exec(
                        select(db.AssistantServiceRegistration).where(
                            db.AssistantServiceRegistration.assistant_service_id == identifiers.assistant_service_id
                        )
                    )
                ).one_or_none()
                if assistant_service is None:
                    logger.error(
                        "configured assistant service id for default assistants is not valid; id: %s",
                        identifiers.assistant_service_id,
                    )
                    continue

                if not assistant_service.assistant_service_online:
                    logger.error(
                        "configured assistant service id for default assistants is not online; id: %s",
                        identifiers.assistant_service_id,
                    )
                    continue

                try:
                    await self.create_assistant(
                        user_principal=user_principal,
                        new_assistant=NewAssistant(
                            assistant_service_id=identifiers.assistant_service_id,
                            template_id=identifiers.template_id,
                            name=identifiers.name,
                        ),
                    )
                except AssistantError:
                    logger.exception(
                        "error creating default assistant; assistant_service_id: %s, template_id: %s",
                        identifiers.assistant_service_id,
                        identifiers.template_id,
                    )

    async def get_assistant(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> Assistant:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal,
                assistant_id=assistant_id,
                session=session,
                include_assistants_from_conversations=True,
            )
            return convert.assistant_from_db(model=assistant)

    async def get_assistant_config(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> ConfigResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal, assistant_id=assistant_id, session=session
            )

        return await (await self._client_pool.assistant_client(assistant)).get_config()

    async def update_assistant_config(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        updated_config: ConfigPutRequestModel,
    ) -> ConfigResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal, assistant_id=assistant_id, session=session
            )

        return await (await self._client_pool.assistant_client(assistant)).put_config(updated_config)

    async def get_assistant_conversation_state_descriptions(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> StateDescriptionListResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal,
                assistant_id=assistant_id,
                session=session,
                include_assistants_from_conversations=True,
            )
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return await (await self._client_pool.assistant_client(assistant)).get_state_descriptions(
            conversation_id=conversation_id
        )

    async def get_assistant_conversation_state(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        state_id: str,
    ) -> StateResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal,
                assistant_id=assistant_id,
                session=session,
                include_assistants_from_conversations=True,
            )
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return await (await self._client_pool.assistant_client(assistant)).get_state(
            conversation_id=conversation_id, state_id=state_id
        )

    async def update_assistant_conversation_state(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        state_id: str,
        updated_state: StatePutRequestModel,
    ) -> StateResponseModel:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                principal=user_principal,
                assistant_id=assistant_id,
                session=session,
                include_assistants_from_conversations=True,
            )
            await self._ensure_assistant_conversation(
                assistant=assistant, conversation_id=conversation_id, session=session
            )

        return await (await self._client_pool.assistant_client(assistant)).put_state(
            conversation_id=conversation_id, state_id=state_id, updated_state=updated_state
        )

    async def post_assistant_state_event(
        self,
        assistant_id: uuid.UUID,
        state_event: AssistantStateEvent,
        assistant_principal: auth.AssistantPrincipal,
        conversation_ids: list[uuid.UUID] = [],
    ) -> None:
        async with self._get_session() as session:
            await self._ensure_assistant(principal=assistant_principal, assistant_id=assistant_id, session=session)

            if not conversation_ids:
                for participant in await session.exec(
                    select(db.AssistantParticipant).where(
                        db.AssistantParticipant.assistant_id == assistant_id,
                        col(db.AssistantParticipant.active_participant).is_(True),
                    )
                ):
                    conversation_ids.append(participant.conversation_id)

        match state_event.event:
            case "focus":
                conversation_event_type = ConversationEventType.assistant_state_focus
            case "created":
                conversation_event_type = ConversationEventType.assistant_state_created
            case "deleted":
                conversation_event_type = ConversationEventType.assistant_state_deleted
            case _:
                conversation_event_type = ConversationEventType.assistant_state_updated

        for conversation_id in conversation_ids:
            await self._notify_event(
                ConversationEventQueueItem(
                    event=ConversationEvent(
                        conversation_id=conversation_id,
                        event=conversation_event_type,
                        data={
                            "assistant_id": assistant_id,
                            "state_id": state_event.state_id,
                            "conversation_id": conversation_id,
                        },
                    ),
                )
            )

    EXPORT_WORKBENCH_FILENAME = "workbench.jsonl"
    EXPORT_ASSISTANT_DATA_FILENAME = "assistant_data.bin"
    EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME = "conversation_data.bin"

    async def export_assistant(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
    ) -> ExportResult:
        async with self._get_session() as session:
            assistant = await self._ensure_assistant(
                session=session, assistant_id=assistant_id, principal=user_principal
            )

            conversations = await session.exec(
                query.select_conversations_for(principal=user_principal, include_all_owned=True)
                .join(db.AssistantParticipant)
                .where(
                    db.AssistantParticipant.assistant_id == assistant_id,
                    col(db.AssistantParticipant.active_participant).is_(True),
                )
            )
            conversation_ids = {conversation.conversation_id for conversation in conversations}

            export_file_name = assistant.name.strip().replace(" ", "_")
            export_file_name = re.sub(r"(?u)[^-\w.]", "", export_file_name)
            export_file_name = (
                f"assistant_{export_file_name}_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}"
            )

            return await self._export(
                session=session,
                export_filename_prefix=export_file_name,
                conversation_ids=conversation_ids,
                assistant_ids=set((assistant_id,)),
            )

    async def _export(
        self,
        conversation_ids: set[uuid.UUID],
        assistant_ids: set[uuid.UUID],
        session: AsyncSession,
        export_filename_prefix: str,
    ) -> ExportResult:
        temp_dir_path = pathlib.Path(tempfile.mkdtemp())

        # write all files to a temporary directory
        export_dir_path = temp_dir_path / "export"
        export_dir_path.mkdir()

        # export records from database
        with (export_dir_path / AssistantController.EXPORT_WORKBENCH_FILENAME).open("+wb") as workbench_file:
            async for file_bytes in export_import.export_file(
                conversation_ids=conversation_ids,
                assistant_ids=assistant_ids,
                session=session,
            ):
                workbench_file.write(file_bytes)

        # export files from storage
        for conversation_id in conversation_ids:
            source_dir = self._file_storage.path_for(namespace=str(conversation_id), filename="")
            if not source_dir.is_dir():
                continue

            conversation_dir = export_dir_path / "files" / str(conversation_id)
            conversation_dir.mkdir(parents=True)

            await asyncio.to_thread(shutil.copytree, src=source_dir, dst=conversation_dir, dirs_exist_ok=True)

        # enumerate assistants
        assistants = await session.exec(select(db.Assistant).where(col(db.Assistant.assistant_id).in_(assistant_ids)))

        for assistant in assistants:
            assistant_client = await self._client_pool.assistant_client(assistant)

            # export assistant data
            assistant_dir = export_dir_path / "assistants" / str(assistant.assistant_id)
            assistant_dir.mkdir(parents=True)

            with (assistant_dir / AssistantController.EXPORT_ASSISTANT_DATA_FILENAME).open("wb") as assistant_file:
                async with assistant_client.get_exported_data() as response:
                    async for chunk in response:
                        assistant_file.write(chunk)

            # enumerate assistant conversations
            assistant_participants = await session.exec(
                select(db.AssistantParticipant)
                .where(db.AssistantParticipant.assistant_id == assistant.assistant_id)
                .where(col(db.AssistantParticipant.conversation_id).in_(conversation_ids))
            )

            for assistant_participant in assistant_participants:
                conversation_dir = assistant_dir / "conversations" / str(assistant_participant.conversation_id)
                conversation_dir.mkdir(parents=True)

                # export assistant conversation data
                with (conversation_dir / AssistantController.EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME).open(
                    "wb"
                ) as conversation_file:
                    async with assistant_client.get_exported_conversation_data(
                        conversation_id=assistant_participant.conversation_id
                    ) as response:
                        async for chunk in response:
                            conversation_file.write(chunk)

        # zip the export directory
        zip_file_path = await asyncio.to_thread(
            shutil.make_archive,
            base_name=str(temp_dir_path / "zip"),
            format="zip",
            root_dir=export_dir_path,
            base_dir="",
            logger=logger,
            verbose=True,
        )

        def _cleanup() -> None:
            shutil.rmtree(temp_dir_path, ignore_errors=True)

        return ExportResult(
            file_path=zip_file_path,
            content_type="application/zip",
            filename=export_filename_prefix + ".zip",
            cleanup=_cleanup,
        )

    async def export_conversations(
        self,
        user_principal: auth.UserPrincipal,
        conversation_ids: set[uuid.UUID],
    ) -> ExportResult:
        async with self._get_session() as session:
            conversations = await session.exec(
                query.select_conversations_for(
                    principal=user_principal, include_all_owned=True, include_observer=True
                ).where(col(db.Conversation.conversation_id).in_(conversation_ids))
            )
            conversation_ids = {conversation.conversation_id for conversation in conversations}

            assistant_ids = set(
                (
                    await session.exec(
                        select(db.Assistant.assistant_id)
                        .join(
                            db.AssistantParticipant,
                            col(db.AssistantParticipant.assistant_id) == col(db.Assistant.assistant_id),
                        )
                        .where(
                            col(db.AssistantParticipant.active_participant).is_(True),
                            col(db.AssistantParticipant.conversation_id).in_(conversation_ids),
                        )
                    )
                ).unique()
            )

            return await self._export(
                session=session,
                export_filename_prefix=(
                    f"semantic_workbench_conversation_export_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}"
                ),
                conversation_ids=conversation_ids,
                assistant_ids=assistant_ids,
            )

    async def import_conversations(
        self,
        from_export: BinaryIO,
        user_principal: auth.UserPrincipal,
    ) -> ConversationImportResult:
        async with self._get_session() as session:
            with tempfile.TemporaryDirectory() as extraction_dir:
                extraction_path = pathlib.Path(extraction_dir)

                # extract the zip file to a temporary directory
                with zipfile.ZipFile(file=from_export, mode="r") as zip_file:
                    await asyncio.to_thread(zip_file.extractall, path=extraction_path)

                # import records into database
                with (extraction_path / AssistantController.EXPORT_WORKBENCH_FILENAME).open("rb") as workbench_file:
                    import_result = await export_import.import_files(
                        session=session,
                        owner_id=user_principal.user_id,
                        files=[workbench_file],
                    )

                await session.commit()

                # import files into storage
                for old_conversation_id, new_conversation_id in import_result.conversation_id_old_to_new.items():
                    files_path = extraction_path / "files" / str(old_conversation_id)
                    if not files_path.is_dir():
                        continue

                    storage_path = self._file_storage.path_for(namespace=str(new_conversation_id), filename="")
                    await asyncio.to_thread(shutil.copytree, src=files_path, dst=storage_path)

                try:
                    # enumerate assistants
                    for old_assistant_id, (new_assistant_id, is_new) in import_result.assistant_id_old_to_new.items():
                        assistant = (
                            await session.exec(
                                select(db.Assistant).where(db.Assistant.assistant_id == new_assistant_id)
                            )
                        ).one()

                        assistant_service = (
                            await session.exec(
                                select(db.AssistantServiceRegistration).where(
                                    db.AssistantServiceRegistration.assistant_service_id
                                    == assistant.assistant_service_id
                                )
                            )
                        ).one_or_none()
                        if assistant_service is None:
                            raise exceptions.InvalidArgumentError(
                                detail=f"assistant service id {assistant.assistant_service_id} is not valid"
                            )

                        assistant_dir = extraction_path / "assistants" / str(old_assistant_id)

                        if is_new:
                            # create the assistant from the assistant data file
                            with (assistant_dir / AssistantController.EXPORT_ASSISTANT_DATA_FILENAME).open(
                                "rb"
                            ) as assistant_file:
                                try:
                                    await self._put_assistant(
                                        assistant=assistant,
                                        from_export=assistant_file,
                                    )
                                except AssistantError:
                                    logger.error("error creating assistant on import", exc_info=True)
                                    raise

                        # enumerate assistant conversations
                        for old_conversation_id in import_result.assistant_conversation_old_ids[old_assistant_id]:
                            new_conversation_id = import_result.conversation_id_old_to_new[old_conversation_id]
                            new_conversation = (
                                await session.exec(
                                    select(db.Conversation).where(
                                        db.Conversation.conversation_id == new_conversation_id
                                    )
                                )
                            ).one()

                            conversation_dir = assistant_dir / "conversations" / str(old_conversation_id)

                            # create the conversation from the conversation data file
                            with (
                                conversation_dir / AssistantController.EXPORT_ASSISTANT_CONVERSATION_DATA_FILENAME
                            ).open("rb") as conversation_file:
                                try:
                                    await self.connect_assistant_to_conversation(
                                        conversation=new_conversation,
                                        assistant=assistant,
                                        from_export=conversation_file,
                                    )
                                except AssistantError:
                                    logger.error("error connecting assistant to conversation on import", exc_info=True)
                                    raise

                except Exception:
                    async with self._get_session() as session_delete:
                        for new_assistant_id, is_new in import_result.assistant_id_old_to_new.values():
                            if not is_new:
                                continue
                            assistant = (
                                await session_delete.exec(
                                    select(db.Assistant).where(db.Assistant.assistant_id == new_assistant_id)
                                )
                            ).one_or_none()
                            if assistant is not None:
                                await session_delete.delete(assistant)
                        for new_conversation_id in import_result.conversation_id_old_to_new.values():
                            conversation = (
                                await session_delete.exec(
                                    select(db.Conversation).where(
                                        db.Conversation.conversation_id == new_conversation_id
                                    )
                                )
                            ).one_or_none()
                            if conversation is not None:
                                await session_delete.delete(conversation)
                        await session_delete.commit()

                    raise

            await session.commit()

        return ConversationImportResult(
            assistant_ids=[assistant_id for assistant_id, _ in import_result.assistant_id_old_to_new.values()],
            conversation_ids=list(import_result.conversation_id_old_to_new.values()),
        )

    # TODO: decide if we should move this to the conversation controller?
    #   it's a bit of a mix between the two and reaches into the assistant controller
    #   to access storage and assistant data, so it's not a clean fit in either
    #   also, we should consider DRYing up the import/export code with this
    async def duplicate_conversation(
        self, principal: auth.ActorPrincipal, conversation_id: uuid.UUID, new_conversation: NewConversation
    ) -> ConversationImportResult:
        async with self._get_session() as session:
            # Ensure the actor has access to the conversation
            original_conversation = await self._ensure_conversation_access(
                session=session,
                principal=principal,
                conversation_id=conversation_id,
            )
            if original_conversation is None:
                raise exceptions.NotFoundError()

            title = new_conversation.title or f"{original_conversation.title} (Copy)"

            meta_data = {
                **original_conversation.meta_data,
                **new_conversation.metadata,
                "_original_conversation_id": str(original_conversation.conversation_id),
            }

            # Create a new conversation with the same properties
            conversation = db.Conversation(
                owner_id=original_conversation.owner_id,
                title=title,
                meta_data=meta_data,
                imported_from_conversation_id=original_conversation.conversation_id,
                # Use the current datetime for the new conversation
                created_datetime=datetime.datetime.now(datetime.UTC),
            )
            session.add(conversation)
            await session.flush()  # To generate new_conversation.conversation_id

            # Copy messages from the original conversation
            messages = await session.exec(
                select(db.ConversationMessage)
                .where(db.ConversationMessage.conversation_id == conversation_id)
                .order_by(col(db.ConversationMessage.sequence))
            )
            message_id_old_to_new = {}
            for message in messages:
                new_message_id = uuid.uuid4()
                message_id_old_to_new[message.message_id] = new_message_id
                new_message = db.ConversationMessage(
                    # Do not set 'sequence'; let the database assign it
                    **message.model_dump(exclude={"message_id", "conversation_id", "sequence"}),
                    message_id=new_message_id,
                    conversation_id=conversation.conversation_id,
                )
                session.add(new_message)

            # Copy message debug data from the original conversation
            for old_message_id, new_message_id in message_id_old_to_new.items():
                message_debugs = await session.exec(
                    select(db.ConversationMessageDebug).where(db.ConversationMessageDebug.message_id == old_message_id)
                )
                for debug in message_debugs:
                    new_debug = db.ConversationMessageDebug(
                        **debug.model_dump(exclude={"message_id"}),
                        message_id=new_message_id,
                    )
                    session.add(new_debug)

            # Copy File entries associated with the conversation
            files = await session.exec(
                select(db.File)
                .where(db.File.conversation_id == original_conversation.conversation_id)
                .order_by(col(db.File.created_datetime).asc())
            )

            file_id_old_to_new = {}
            for file in files:
                new_file_id = uuid.uuid4()
                file_id_old_to_new[file.file_id] = new_file_id
                new_file = db.File(
                    **file.model_dump(exclude={"file_id", "conversation_id"}),
                    file_id=new_file_id,
                    conversation_id=conversation.conversation_id,
                )
                session.add(new_file)

            # Copy FileVersion entries associated with the files
            for old_file_id, new_file_id in file_id_old_to_new.items():
                file_versions = await session.exec(
                    select(db.FileVersion)
                    .where(db.FileVersion.file_id == old_file_id)
                    .order_by(col(db.FileVersion.version).asc())
                )
                for version in file_versions:
                    new_version = db.FileVersion(
                        **version.model_dump(exclude={"file_id"}),
                        file_id=new_file_id,
                    )
                    session.add(new_version)

            # Copy files associated with the conversation
            original_files_path = self._file_storage.path_for(
                namespace=str(original_conversation.conversation_id), filename=""
            )
            new_files_path = self._file_storage.path_for(namespace=str(conversation.conversation_id), filename="")
            if original_files_path.exists():
                await asyncio.to_thread(shutil.copytree, original_files_path, new_files_path)

            # Associate existing assistant participants
            # Fetch assistant participants and collect into a list
            assistant_participants = (
                await session.exec(
                    select(db.AssistantParticipant).where(
                        db.AssistantParticipant.conversation_id == conversation_id,
                        db.AssistantParticipant.active_participant,
                    )
                )
            ).all()
            for participant in assistant_participants:
                new_participant = db.AssistantParticipant(
                    conversation_id=conversation.conversation_id,
                    assistant_id=participant.assistant_id,
                    name=participant.name,
                    image=participant.image,
                    joined_datetime=participant.joined_datetime,
                    status=participant.status,
                    status_updated_datetime=participant.status_updated_datetime,
                    active_participant=participant.active_participant,
                )
                session.add(new_participant)

            # Associate existing user participants
            user_participants = await session.exec(
                select(db.UserParticipant).where(
                    db.UserParticipant.conversation_id == conversation_id,
                    db.UserParticipant.active_participant,
                )
            )
            for participant in user_participants:
                new_user_participant = db.UserParticipant(
                    conversation_id=conversation.conversation_id,
                    user_id=participant.user_id,
                    name=participant.name,
                    image=participant.image,
                    service_user=participant.service_user,
                    joined_datetime=participant.joined_datetime,
                    status=participant.status,
                    status_updated_datetime=participant.status_updated_datetime,
                    active_participant=participant.active_participant,
                    conversation_permission=participant.conversation_permission,
                )
                session.add(new_user_participant)

            await session.commit()

            # Initialize assistant state for the new conversation
            assistant_ids = {participant.assistant_id for participant in assistant_participants}
            for assistant_id in assistant_ids:
                assistant = await session.get(db.Assistant, assistant_id)
                if not assistant:
                    continue  # Assistant not found, skip

                try:
                    # **Export the assistant's conversation data from the original conversation**
                    assistant_client = await self._client_pool.assistant_client(assistant)
                    async with assistant_client.get_exported_conversation_data(
                        conversation_id=conversation_id
                    ) as export_response:
                        # Read the exported data into a BytesIO buffer
                        from_export = io.BytesIO()
                        async for chunk in export_response:
                            from_export.write(chunk)
                        from_export.seek(0)  # Reset buffer position to the beginning

                    # **Connect the assistant to the new conversation with the exported data**
                    await self.connect_assistant_to_conversation(
                        conversation=conversation,
                        assistant=assistant,
                        from_export=from_export,
                    )
                except AssistantError as e:
                    logger.error(
                        f"Error connecting assistant {assistant_id} to new conversation {conversation.conversation_id}: {e}",
                        exc_info=True,
                    )
                    # Optionally handle the error (e.g., remove assistant from the conversation)

            return ConversationImportResult(
                assistant_ids=list(assistant_ids),
                conversation_ids=[conversation.conversation_id],
            )

    async def _ensure_conversation_access(
        self,
        session: AsyncSession,
        principal: auth.ActorPrincipal,
        conversation_id: uuid.UUID,
    ) -> db.Conversation:
        match principal:
            case auth.UserPrincipal():
                conversation = (
                    await session.exec(
                        query.select_conversations_for(
                            principal=principal,
                        ).where(db.Conversation.conversation_id == conversation_id)
                    )
                ).one_or_none()
            case auth.AssistantPrincipal():
                conversation = (
                    await session.exec(
                        select(db.Conversation)
                        .join(db.AssistantParticipant)
                        .where(db.Conversation.conversation_id == conversation_id)
                        .where(db.AssistantParticipant.assistant_id == principal.assistant_id)
                        .where(db.AssistantParticipant.active_participant)
                    )
                ).one_or_none()
            case _:
                raise exceptions.UnauthorizedError("Principal type not supported.")

        if conversation is None:
            raise exceptions.NotFoundError()

        return conversation


=== File: workbench-service/semantic_workbench_service/controller/assistant_service_client_pool.py ===
import asyncio
from typing import Self

from semantic_workbench_api_model.assistant_service_client import (
    AssistantClient,
    AssistantServiceClient,
    AssistantServiceClientBuilder,
)

from .. import assistant_api_key, db


class AssistantServiceClientPool:
    def __init__(self, api_key_store: assistant_api_key.ApiKeyStore) -> None:
        self._api_key_store = api_key_store
        self._service_clients: dict[str, AssistantServiceClient] = {}
        self._assistant_clients: dict[str, AssistantClient] = {}
        self._client_lock = asyncio.Lock()

    def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        for client in self._service_clients.values():
            await client.aclose()
        for client in self._assistant_clients.values():
            await client.aclose()

    async def service_client(self, registration: db.AssistantServiceRegistration) -> AssistantServiceClient:
        service_id = registration.assistant_service_id
        url = registration.assistant_service_url
        key = f"{service_id}-{url}"

        if key not in self._service_clients:
            async with self._client_lock:
                if key not in self._service_clients:
                    self._service_clients[key] = (await self._client_builder(registration)).for_service()

        return self._service_clients[key]

    async def assistant_client(self, assistant: db.Assistant) -> AssistantClient:
        assistant_id = assistant.assistant_id
        url = assistant.related_assistant_service_registration.assistant_service_url
        key = f"{assistant_id}-{url}"

        if key not in self._assistant_clients:
            async with self._client_lock:
                if key not in self._assistant_clients:
                    self._assistant_clients[key] = (
                        await self._client_builder(assistant.related_assistant_service_registration)
                    ).for_assistant(assistant_id)

        return self._assistant_clients[key]

    async def _client_builder(
        self,
        registration: db.AssistantServiceRegistration,
    ) -> AssistantServiceClientBuilder:
        api_key = await self._api_key_store.get(registration.api_key_name)
        if api_key is None:
            raise RuntimeError(f"assistant service {registration.assistant_service_id} does not have API key set")

        return AssistantServiceClientBuilder(
            base_url=str(registration.assistant_service_url),
            api_key=api_key,
        )


=== File: workbench-service/semantic_workbench_service/controller/assistant_service_registration.py ===
import asyncio
import datetime
import logging
from typing import AsyncContextManager, Awaitable, Callable, Iterable

from semantic_workbench_api_model.assistant_model import ServiceInfoModel
from semantic_workbench_api_model.assistant_service_client import AssistantError
from semantic_workbench_api_model.workbench_model import (
    AssistantServiceInfoList,
    AssistantServiceRegistration,
    AssistantServiceRegistrationList,
    ConversationEventType,
    NewAssistantServiceRegistration,
    UpdateAssistantServiceRegistration,
    UpdateAssistantServiceRegistrationUrl,
)
from sqlalchemy import update
from sqlmodel import col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import assistant_api_key, auth, db, settings
from ..event import ConversationEventQueueItem
from . import convert, exceptions
from . import participant as participant_
from . import user as user_
from .assistant_service_client_pool import AssistantServiceClientPool

logger = logging.getLogger(__name__)


class AssistantServiceRegistrationController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
        api_key_store: assistant_api_key.ApiKeyStore,
        client_pool: AssistantServiceClientPool,
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event
        self._api_key_store = api_key_store
        self._client_pool = client_pool

    @property
    def _registration_is_secured(self) -> bool:
        return settings.service.assistant_api_key.is_secured

    async def api_key_source(self, assistant_service_id: str) -> str | None:
        generated_key_name = self._api_key_store.generate_key_name(assistant_service_id)
        if assistant_service_id == generated_key_name:
            return await self._api_key_store.get(generated_key_name)

        async with self._get_session() as session:
            api_key_name = (
                await session.exec(
                    select(db.AssistantServiceRegistration.api_key_name).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
                    )
                )
            ).first()
        if api_key_name is None:
            return None
        return await self._api_key_store.get(api_key_name)

    async def create_registration(
        self,
        user_principal: auth.UserPrincipal,
        new_assistant_service: NewAssistantServiceRegistration,
    ) -> AssistantServiceRegistration:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            assistant_service_id = new_assistant_service.assistant_service_id.strip().lower()

            existing_registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
                    )
                )
            ).first()
            if existing_registration is not None:
                raise exceptions.ConflictError("assistant service with this assistant_service_id already exists")

            api_key_name = self._api_key_store.generate_key_name(assistant_service_id)
            registration = db.AssistantServiceRegistration(
                assistant_service_id=assistant_service_id,
                created_by_user_id=user_principal.user_id,
                name=new_assistant_service.name,
                description=new_assistant_service.description,
                include_in_listing=new_assistant_service.include_in_listing,
                api_key_name=api_key_name,
            )
            session.add(registration)
            await session.flush()
            await session.refresh(registration)

            api_key = await self._api_key_store.reset(registration.api_key_name)

            await session.commit()

        return convert.assistant_service_registration_from_db(
            registration, api_key=api_key, include_api_key_name=self._registration_is_secured
        )

    async def get_registrations(
        self, user_ids: set[str], assistant_service_online: bool | None = None
    ) -> AssistantServiceRegistrationList:
        async with self._get_session() as session:
            query_registrations = (
                select(db.AssistantServiceRegistration)
                .where(col(db.AssistantServiceRegistration.include_in_listing).is_(True))
                .order_by(col(db.AssistantServiceRegistration.created_datetime).asc())
            )

            if user_ids:
                query_registrations = select(db.AssistantServiceRegistration).where(
                    col(db.AssistantServiceRegistration.created_by_user_id).in_(user_ids)
                )

            if assistant_service_online is not None:
                query_registrations = query_registrations.where(
                    col(db.AssistantServiceRegistration.assistant_service_online).is_(True)
                )

            assistant_services = await session.exec(query_registrations)

            return convert.assistant_service_registration_list_from_db(
                assistant_services, include_api_key_name=self._registration_is_secured
            )

    async def get_registration(self, assistant_service_id: str) -> AssistantServiceRegistration:
        async with self._get_session() as session:
            registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
                    )
                )
            ).first()
            if registration is None:
                raise exceptions.NotFoundError()

            api_key = await self._api_key_store.get(registration.api_key_name)
            masked_api_key = self.mask_api_key(api_key)

            return convert.assistant_service_registration_from_db(
                registration, api_key=masked_api_key, include_api_key_name=self._registration_is_secured
            )

    @staticmethod
    def mask_api_key(api_key: str | None) -> str | None:
        if api_key is None:
            return None

        unmasked_length = 4
        if len(api_key) <= unmasked_length:
            # return a fixed mask if the api key is too short
            return "*" * 32

        # returns partially masked api key
        return f"{api_key[:unmasked_length]}{'*' * (len(api_key) - unmasked_length)}"

    async def update_registration(
        self,
        user_principal: auth.UserPrincipal,
        assistant_service_id: str,
        update_assistant_service: UpdateAssistantServiceRegistration,
    ) -> AssistantServiceRegistration:
        async with self._get_session() as session:
            registration_query = (
                select(db.AssistantServiceRegistration)
                .where(db.AssistantServiceRegistration.assistant_service_id == assistant_service_id)
                .with_for_update()
            )
            if self._registration_is_secured:
                registration_query = registration_query.where(
                    db.AssistantServiceRegistration.created_by_user_id == user_principal.user_id
                )
            registration = (await session.exec(registration_query)).first()

            if registration is None:
                raise exceptions.NotFoundError()

            if "name" in update_assistant_service.model_fields_set:
                if update_assistant_service.name is None:
                    raise exceptions.InvalidArgumentError("name cannot be null")
                registration.name = update_assistant_service.name
            if "description" in update_assistant_service.model_fields_set:
                if update_assistant_service.description is None:
                    raise exceptions.InvalidArgumentError("description cannot be null")
                registration.description = update_assistant_service.description
            if "include_in_listing" in update_assistant_service.model_fields_set:
                if update_assistant_service.include_in_listing is None:
                    raise exceptions.InvalidArgumentError("include_in_listing cannot be null")
                registration.include_in_listing = update_assistant_service.include_in_listing

            session.add(registration)
            await session.commit()
            await session.refresh(registration)

        return convert.assistant_service_registration_from_db(
            registration, include_api_key_name=self._registration_is_secured
        )

    async def update_assistant_service_url(
        self,
        assistant_service_principal: auth.AssistantServicePrincipal,
        assistant_service_id: str,
        update_assistant_service_url: UpdateAssistantServiceRegistrationUrl,
    ) -> tuple[AssistantServiceRegistration, Iterable]:
        if assistant_service_id != assistant_service_principal.assistant_service_id:
            raise exceptions.ForbiddenError()

        background_task_args: Iterable = ()
        async with self._get_session() as session:
            registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration)
                    .where(db.AssistantServiceRegistration.assistant_service_id == assistant_service_id)
                    .with_for_update()
                )
            ).first()

            if registration is None:
                if self._registration_is_secured:
                    raise exceptions.NotFoundError()

                api_key_name = self._api_key_store.generate_key_name(assistant_service_id.lower())
                registration = db.AssistantServiceRegistration(
                    assistant_service_id=assistant_service_id,
                    created_by_user_id="semantic-workbench",
                    name=update_assistant_service_url.name,
                    description=update_assistant_service_url.description,
                    include_in_listing=True,
                    api_key_name=api_key_name,
                )

            if self._registration_is_secured and update_assistant_service_url.url.scheme != "https":
                raise exceptions.InvalidArgumentError("url must be https")

            if registration.assistant_service_url != str(update_assistant_service_url.url):
                registration.assistant_service_url = str(update_assistant_service_url.url)
                logger.info(
                    "updated assistant service url; assistant_service_id: %s, url: %s",
                    assistant_service_id,
                    registration.assistant_service_url,
                )

            registration.assistant_service_online_expiration_datetime = datetime.datetime.now(
                datetime.UTC
            ) + datetime.timedelta(seconds=update_assistant_service_url.online_expires_in_seconds)

            if not registration.assistant_service_online:
                registration.assistant_service_online = True
                background_task_args = (self._update_participants, assistant_service_id)

            session.add(registration)
            await session.commit()
            await session.refresh(registration)

        return convert.assistant_service_registration_from_db(
            registration, include_api_key_name=self._registration_is_secured
        ), background_task_args

    async def _update_participants(
        self,
        assistant_service_id: str,
    ) -> None:
        async with self._get_session() as session:
            participants_and_assistants = await session.exec(
                select(db.AssistantParticipant, db.Assistant)
                .join(db.Assistant, col(db.Assistant.assistant_id) == col(db.AssistantParticipant.assistant_id))
                .where(db.Assistant.assistant_service_id == assistant_service_id)
            )

            for participant, assistant in participants_and_assistants:
                participants = await participant_.get_conversation_participants(
                    session=session, conversation_id=participant.conversation_id, include_inactive=True
                )
                await self._notify_event(
                    ConversationEventQueueItem(
                        event=participant_.participant_event(
                            event_type=ConversationEventType.participant_updated,
                            conversation_id=participant.conversation_id,
                            participant=convert.conversation_participant_from_db_assistant(
                                participant, assistant=assistant
                            ),
                            participants=participants,
                        ),
                        # assistants do not need to receive assistant-participant online/offline events
                        event_audience={"user"},
                    )
                )

    async def reset_api_key(
        self,
        user_principal: auth.UserPrincipal,
        assistant_service_id: str,
    ) -> AssistantServiceRegistration:
        async with self._get_session() as session:
            registration_query = select(db.AssistantServiceRegistration).where(
                db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
            )
            if self._registration_is_secured:
                registration_query = registration_query.where(
                    db.AssistantServiceRegistration.created_by_user_id == user_principal.user_id
                )

            registration = (await session.exec(registration_query)).first()
            if registration is None:
                raise exceptions.NotFoundError()

            api_key = await self._api_key_store.reset(registration.api_key_name)

        return convert.assistant_service_registration_from_db(
            registration, api_key=api_key, include_api_key_name=self._registration_is_secured
        )

    async def check_assistant_service_online_expired(self) -> None:
        async with self._get_session() as session:
            conn = await session.connection()
            result = await conn.execute(
                update(db.AssistantServiceRegistration)
                .where(col(db.AssistantServiceRegistration.assistant_service_online).is_(True))
                .where(
                    or_(
                        col(db.AssistantServiceRegistration.assistant_service_online_expiration_datetime).is_(None),
                        col(db.AssistantServiceRegistration.assistant_service_online_expiration_datetime)
                        <= datetime.datetime.now(
                            datetime.UTC,
                        ),
                    ),
                )
                .values(assistant_service_online=False)
                .returning(col(db.AssistantServiceRegistration.assistant_service_id))
            )
            if not result.rowcount:
                return

            assistant_service_ids = result.scalars().all()
            await session.commit()

        for assistant_service_id in assistant_service_ids:
            await self._update_participants(assistant_service_id=assistant_service_id)

    async def delete_registration(
        self,
        user_principal: auth.UserPrincipal,
        assistant_service_id: str,
    ) -> None:
        async with self._get_session() as session:
            registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration)
                    .where(db.AssistantServiceRegistration.assistant_service_id == assistant_service_id)
                    .where(db.AssistantServiceRegistration.created_by_user_id == user_principal.user_id)
                )
            ).first()
            if registration is None:
                raise exceptions.NotFoundError()

            await session.delete(registration)
            await session.commit()

            await self._api_key_store.delete(registration.api_key_name)

    async def get_service_info(self, assistant_service_id: str) -> ServiceInfoModel:
        async with self._get_session() as session:
            registration = (
                await session.exec(
                    select(db.AssistantServiceRegistration).where(
                        db.AssistantServiceRegistration.assistant_service_id == assistant_service_id
                    )
                )
            ).first()

            if registration is None:
                raise exceptions.NotFoundError()

        return await (await self._client_pool.service_client(registration=registration)).get_service_info()

    async def get_service_infos(self, user_ids: set[str] = set()) -> AssistantServiceInfoList:
        async with self._get_session() as session:
            query_registrations = (
                select(db.AssistantServiceRegistration)
                .where(col(db.AssistantServiceRegistration.include_in_listing).is_(True))
                .order_by(col(db.AssistantServiceRegistration.created_datetime).asc())
            )

            if user_ids:
                query_registrations = select(db.AssistantServiceRegistration).where(
                    col(db.AssistantServiceRegistration.created_by_user_id).in_(user_ids)
                )

            query_registrations = query_registrations.where(
                col(db.AssistantServiceRegistration.assistant_service_online).is_(True)
            )

            assistant_services = await session.exec(query_registrations)

        infos_or_exceptions = await asyncio.gather(
            *[
                (await self._client_pool.service_client(registration=registration)).get_service_info()
                for registration in assistant_services
            ],
            return_exceptions=True,
        )

        infos: list[ServiceInfoModel] = []
        for info_or_exception in infos_or_exceptions:
            match info_or_exception:
                case AssistantError():
                    logger.error("failed to get assistant service info", exc_info=info_or_exception)

                case BaseException():
                    raise info_or_exception

                case ServiceInfoModel():
                    infos.append(info_or_exception)

        return AssistantServiceInfoList(assistant_service_infos=infos)


=== File: workbench-service/semantic_workbench_service/controller/conversation.py ===
import datetime
import logging
import uuid
from typing import (
    Annotated,
    AsyncContextManager,
    Awaitable,
    Callable,
    Iterable,
    Literal,
    Sequence,
)

import deepmerge
import openai_client
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, HttpUrl
from semantic_workbench_api_model.assistant_service_client import AssistantError
from semantic_workbench_api_model.workbench_model import (
    Conversation,
    ConversationEvent,
    ConversationEventType,
    ConversationList,
    ConversationMessage,
    ConversationMessageDebug,
    ConversationMessageList,
    ConversationParticipant,
    ConversationParticipantList,
    MessageType,
    NewConversation,
    NewConversationMessage,
    ParticipantRole,
    UpdateConversation,
    UpdateParticipant,
)
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import and_, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, query, settings
from ..event import ConversationEventQueueItem
from . import assistant, convert, exceptions
from . import participant as participant_
from . import user as user_

logger = logging.getLogger(__name__)


class ConversationTitleResponse(BaseModel):
    """Model for responses from LLM for automatic conversation re-titling."""

    title: Annotated[
        str,
        Field(
            description="The updated title of the conversation. If the subject matter of the conversation has changed significantly from the current title, suggest a short, but descriptive title for the conversation. Ideally 4 words or less in length. Leave it blank to keep the current title.",
        ),
    ]


META_DATA_KEY_USER_SET_TITLE = "__user_set_title"
META_DATA_KEY_AUTO_TITLE_COUNT = "__auto_title_count"
AUTO_TITLE_COUNT_LIMIT = 3
"""
The maximum number of times a conversation can be automatically retitled.
"""


class ConversationController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
        assistant_controller: assistant.AssistantController,
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event
        self._assistant_controller = assistant_controller

    async def create_conversation(
        self,
        new_conversation: NewConversation,
        user_principal: auth.UserPrincipal,
    ) -> Conversation:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            conversation = db.Conversation(
                owner_id=user_principal.user_id,
                title=new_conversation.title or NewConversation().title,
                meta_data=new_conversation.metadata,
                imported_from_conversation_id=None,
            )

            if new_conversation.title and new_conversation.title != NewConversation().title:
                conversation.meta_data = {
                    **conversation.meta_data,
                    META_DATA_KEY_USER_SET_TITLE: True,
                }

            session.add(conversation)

            session.add(
                db.UserParticipant(
                    conversation_id=conversation.conversation_id,
                    user_id=user_principal.user_id,
                    conversation_permission="read_write",
                )
            )

            await session.commit()
            await session.refresh(conversation)

        return await self.get_conversation(
            conversation_id=conversation.conversation_id,
            principal=user_principal,
            latest_message_types=set(),
        )

    async def create_conversation_with_owner(
        self,
        new_conversation: NewConversation,
        owner_id: str,
        principal: auth.AssistantPrincipal,
    ) -> Conversation:
        async with self._get_session() as session:
            conversation = db.Conversation(
                owner_id=owner_id,
                title=new_conversation.title or NewConversation().title,
                meta_data=new_conversation.metadata,
                imported_from_conversation_id=None,
            )

            if new_conversation.title and new_conversation.title != NewConversation().title:
                conversation.meta_data = {
                    **conversation.meta_data,
                    META_DATA_KEY_USER_SET_TITLE: True,
                }

            session.add(conversation)

            # session.add(
            #     db.UserParticipant(
            #         conversation_id=conversation.conversation_id,
            #         user_id=owner_id,
            #         conversation_permission="read_write",
            #     )
            # )

            session.add(
                db.AssistantParticipant(
                    conversation_id=conversation.conversation_id,
                    assistant_id=principal.assistant_id,
                )
            )

            await session.commit()
            await session.refresh(conversation)

            assistant = (
                await session.exec(select(db.Assistant).where(db.Assistant.assistant_id == principal.assistant_id))
            ).one_or_none()
            if assistant is None:
                raise exceptions.NotFoundError()

        await self._assistant_controller.connect_assistant_to_conversation(
            assistant=assistant,
            conversation=conversation,
            from_export=None,
        )

        return await self.get_conversation(
            conversation_id=conversation.conversation_id,
            principal=principal,
            latest_message_types=set(),
        )

    async def _projections_with_participants(
        self,
        session: AsyncSession,
        conversation_projections: Sequence[tuple[db.Conversation, db.ConversationMessage | None, bool, str]],
    ) -> Iterable[
        tuple[
            db.Conversation,
            Iterable[db.UserParticipant],
            Iterable[db.AssistantParticipant],
            dict[uuid.UUID, db.Assistant],
            db.ConversationMessage | None,
            bool,
            str,
        ]
    ]:
        user_participants = (
            await session.exec(
                select(db.UserParticipant).where(
                    col(db.UserParticipant.conversation_id).in_([
                        c[0].conversation_id for c in conversation_projections
                    ])
                )
            )
        ).all()

        assistant_participants = (
            await session.exec(
                select(db.AssistantParticipant).where(
                    col(db.AssistantParticipant.conversation_id).in_([
                        c[0].conversation_id for c in conversation_projections
                    ])
                )
            )
        ).all()

        assistants = (
            await session.exec(
                select(db.Assistant).where(
                    col(db.Assistant.assistant_id).in_([p.assistant_id for p in assistant_participants])
                )
            )
        ).all()
        assistants_map = {assistant.assistant_id: assistant for assistant in assistants}

        def merge() -> Iterable[
            tuple[
                db.Conversation,
                Iterable[db.UserParticipant],
                Iterable[db.AssistantParticipant],
                dict[uuid.UUID, db.Assistant],
                db.ConversationMessage | None,
                bool,
                str,
            ]
        ]:
            for (
                conversation,
                latest_message,
                latest_message_has_debug,
                permission,
            ) in conversation_projections:
                conversation_id = conversation.conversation_id
                conversation_user_participants = (
                    up for up in user_participants if up.conversation_id == conversation_id
                )
                conversation_assistant_participants = (
                    ap for ap in assistant_participants if ap.conversation_id == conversation_id
                )
                yield (
                    conversation,
                    conversation_user_participants,
                    conversation_assistant_participants,
                    assistants_map,
                    latest_message,
                    latest_message_has_debug,
                    permission,
                )

        return merge()

    async def get_conversations(
        self,
        principal: auth.ActorPrincipal,
        latest_message_types: set[MessageType],
        include_all_owned: bool = False,
    ) -> ConversationList:
        async with self._get_session() as session:
            include_all_owned = include_all_owned and isinstance(principal, auth.UserPrincipal)

            conversation_projections = (
                await session.exec(
                    query.select_conversation_projections_for(
                        principal=principal,
                        include_all_owned=include_all_owned,
                        include_observer=True,
                        latest_message_types=latest_message_types,
                    ).order_by(col(db.Conversation.created_datetime).desc())
                )
            ).all()

            projections_with_participants = await self._projections_with_participants(
                session=session, conversation_projections=conversation_projections
            )

            return convert.conversation_list_from_db(models=projections_with_participants)

    async def get_assistant_conversations(
        self,
        user_principal: auth.UserPrincipal,
        assistant_id: uuid.UUID,
        latest_message_types: set[MessageType],
    ) -> ConversationList:
        async with self._get_session() as session:
            assistant = (
                await session.exec(
                    query.select_assistants_for(user_principal=user_principal).where(
                        db.Assistant.assistant_id == assistant_id
                    )
                )
            ).one_or_none()
            if assistant is None:
                raise exceptions.NotFoundError()

            conversation_projections = (
                await session.exec(
                    query.select_conversation_projections_for(
                        principal=auth.AssistantPrincipal(
                            assistant_service_id=assistant.assistant_service_id,
                            assistant_id=assistant_id,
                        ),
                        latest_message_types=latest_message_types,
                    )
                )
            ).all()

            projections_with_participants = await self._projections_with_participants(
                session=session, conversation_projections=conversation_projections
            )

            return convert.conversation_list_from_db(models=projections_with_participants)

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        principal: auth.ActorPrincipal,
        latest_message_types: set[MessageType],
    ) -> Conversation:
        async with self._get_session() as session:
            include_all_owned = isinstance(principal, auth.UserPrincipal)

            conversation_projection = (
                await session.exec(
                    query.select_conversation_projections_for(
                        principal=principal,
                        include_all_owned=include_all_owned,
                        include_observer=True,
                        latest_message_types=latest_message_types,
                    ).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation_projection is None:
                raise exceptions.NotFoundError()

            projections_with_participants = await self._projections_with_participants(
                session=session,
                conversation_projections=[conversation_projection],
            )

            (
                conversation,
                user_participants,
                assistant_participants,
                assistants,
                latest_message,
                latest_message_has_debug,
                permission,
            ) = next(iter(projections_with_participants))

            return convert.conversation_from_db(
                model=conversation,
                latest_message=latest_message,
                latest_message_has_debug=latest_message_has_debug,
                permission=permission,
                user_participants=user_participants,
                assistant_participants=assistant_participants,
                assistants=assistants,
            )

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        update_conversation: UpdateConversation,
        user_principal: auth.ActorPrincipal,
    ) -> Conversation:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(
                        principal=user_principal,
                        include_all_owned=True,
                    )
                    .where(
                        db.Conversation.conversation_id == conversation_id,
                    )
                    .with_for_update()
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            for key, value in update_conversation.model_dump(exclude_unset=True).items():
                match key:
                    case "metadata":
                        system_entries = {k: v for k, v in conversation.meta_data.items() if k.startswith("__")}
                        conversation.meta_data = {
                            **conversation.meta_data,
                            **value,
                            **system_entries,
                        }
                    case "title":
                        if value == conversation.title:
                            continue
                        conversation.title = value
                        conversation.meta_data = {
                            **conversation.meta_data,
                            META_DATA_KEY_USER_SET_TITLE: True,
                        }
                    case _:
                        setattr(conversation, key, value)

            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

        conversation_model = await self.get_conversation(
            conversation_id=conversation.conversation_id,
            principal=user_principal,
            latest_message_types=set(),
        )

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation.conversation_id,
                    event=ConversationEventType.conversation_updated,
                    data={
                        "conversation": conversation_model.model_dump(),
                    },
                )
            )
        )

        return conversation_model

    async def get_conversation_participants(
        self,
        conversation_id: uuid.UUID,
        principal: auth.ActorPrincipal,
        include_inactive: bool = False,
    ) -> ConversationParticipantList:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(
                        principal=principal,
                        include_all_owned=True,
                        include_observer=True,
                    ).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            return await participant_.get_conversation_participants(
                session=session,
                conversation_id=conversation.conversation_id,
                include_inactive=include_inactive,
            )

    async def get_conversation_participant(
        self,
        conversation_id: uuid.UUID,
        participant_id: str,
        principal: auth.ActorPrincipal,
    ) -> ConversationParticipant:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(
                        principal=principal,
                        include_all_owned=True,
                        include_observer=True,
                    ).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            possible_user_participant = (
                await session.exec(
                    select(db.UserParticipant)
                    .where(db.UserParticipant.conversation_id == conversation.conversation_id)
                    .where(db.UserParticipant.user_id == participant_id)
                )
            ).one_or_none()
            if possible_user_participant is not None:
                return convert.conversation_participant_from_db_user(possible_user_participant)

            possible_assistant_participant = (
                await session.exec(
                    select(db.AssistantParticipant)
                    .where(db.AssistantParticipant.conversation_id == conversation.conversation_id)
                    .where(db.AssistantParticipant.assistant_id == participant_id)
                )
            ).one_or_none()
            if possible_assistant_participant is not None:
                assistant = (
                    await session.exec(
                        select(db.Assistant).where(
                            db.Assistant.assistant_id == possible_assistant_participant.assistant_id
                        )
                    )
                ).one_or_none()
                return convert.conversation_participant_from_db_assistant(
                    possible_assistant_participant, assistant=assistant
                )

        raise exceptions.NotFoundError()

    async def add_or_update_conversation_participant(
        self,
        conversation_id: uuid.UUID,
        participant_id: str,
        update_participant: UpdateParticipant,
        principal: auth.ActorPrincipal,
    ) -> ConversationParticipant:
        if update_participant.active_participant is not None and not update_participant.active_participant:
            update_participant.status = None

        async with self._get_session() as session:

            async def update_user_participant(
                conversation: db.Conversation, user: db.User
            ) -> tuple[
                ConversationParticipant,
                Literal[ConversationEventType.participant_updated,] | None,
            ]:
                event_type: ConversationEventType | None = None
                participant = (
                    await session.exec(
                        select(db.UserParticipant)
                        .join(db.Conversation)
                        .where(db.UserParticipant.conversation_id == conversation.conversation_id)
                        .where(db.UserParticipant.user_id == user.user_id)
                        .where(
                            or_(
                                col(db.UserParticipant.active_participant).is_(True),
                                db.Conversation.owner_id == user.user_id,
                            )
                        )
                        .with_for_update()
                    )
                ).one_or_none()
                if participant is None:
                    raise exceptions.NotFoundError()

                if update_participant.active_participant is not None:
                    event_type = ConversationEventType.participant_updated
                    participant.active_participant = update_participant.active_participant

                if update_participant.status != participant.status:
                    event_type = event_type or ConversationEventType.participant_updated
                    participant.status = update_participant.status
                    participant.status_updated_datetime = datetime.datetime.now(datetime.UTC)

                if update_participant.metadata is not None:
                    event_type = event_type or ConversationEventType.participant_updated
                    participant.meta_data = deepmerge.always_merger.merge(
                        {**participant.meta_data}, update_participant.metadata
                    )

                if event_type is not None:
                    session.add(participant)
                    await session.commit()
                    await session.refresh(participant)

                return convert.conversation_participant_from_db_user(participant), event_type

            async def update_assistant_participant(
                conversation: db.Conversation,
                assistant: db.Assistant,
            ) -> tuple[
                ConversationParticipant,
                Literal[
                    ConversationEventType.participant_created,
                    ConversationEventType.participant_updated,
                ]
                | None,
            ]:
                new_participant = await db.insert_if_not_exists(
                    session,
                    db.AssistantParticipant(
                        conversation_id=conversation.conversation_id,
                        assistant_id=assistant.assistant_id,
                        status=update_participant.status,
                        name=assistant.name,
                        image=assistant.image,
                    ),
                )
                event_type = ConversationEventType.participant_created if new_participant else None
                participant = (
                    await session.exec(
                        select(db.AssistantParticipant)
                        .where(db.AssistantParticipant.conversation_id == conversation.conversation_id)
                        .where(db.AssistantParticipant.assistant_id == assistant.assistant_id)
                        .with_for_update()
                    )
                ).one()

                original_participant = participant.model_copy(deep=True)

                active_participant_changed = new_participant
                if update_participant.active_participant is not None:
                    event_type = event_type or ConversationEventType.participant_updated
                    active_participant_changed = active_participant_changed or (
                        participant.active_participant != update_participant.active_participant
                    )
                    participant.active_participant = update_participant.active_participant

                if participant.status != update_participant.status:
                    event_type = event_type or ConversationEventType.participant_updated
                    participant.status = update_participant.status
                    participant.status_updated_datetime = datetime.datetime.now(datetime.UTC)

                if update_participant.metadata is not None:
                    event_type = event_type or ConversationEventType.participant_updated
                    participant.meta_data = {
                        **deepmerge.always_merger.merge(participant.meta_data.copy(), update_participant.metadata)
                    }
                    flag_modified(participant, "meta_data")

                if event_type is not None:
                    session.add(participant)
                    await session.commit()
                    await session.refresh(participant)

                if active_participant_changed and participant.active_participant:
                    try:
                        await self._assistant_controller.connect_assistant_to_conversation(
                            assistant=assistant,
                            conversation=conversation,
                            from_export=None,
                        )
                    except AssistantError:
                        logger.error(
                            f"failed to connect assistant {assistant.assistant_id} to conversation"
                            f" {conversation.conversation_id}",
                            exc_info=True,
                        )
                        session.add(original_participant)
                        await session.commit()
                        raise

                if active_participant_changed and not participant.active_participant:
                    try:
                        await self._assistant_controller.disconnect_assistant_from_conversation(
                            assistant=assistant,
                            conversation_id=conversation.conversation_id,
                        )
                    except AssistantError:
                        logger.error(
                            f"failed to disconnect assistant {assistant.assistant_id} from conversation"
                            f" {conversation.conversation_id}",
                            exc_info=True,
                        )

                return (
                    convert.conversation_participant_from_db_assistant(
                        participant,
                        assistant=assistant,
                    ),
                    event_type,
                )

            match principal:
                case auth.UserPrincipal():
                    await user_.add_or_update_user_from(user_principal=principal, session=session)

                    # users can update participants in any conversation they own or are participants of
                    conversation = (
                        await session.exec(
                            query.select_conversations_for(
                                principal=principal,
                                include_all_owned=True,
                                include_observer=True,
                            ).where(db.Conversation.conversation_id == conversation_id)
                        )
                    ).one_or_none()
                    if conversation is None:
                        raise exceptions.NotFoundError()

                    assistant_id: uuid.UUID | None = None
                    try:
                        assistant_id = uuid.UUID(participant_id)
                        participant_role = "assistant"
                    except ValueError:
                        participant_role = "user"

                    match participant_role:
                        case "user":
                            # users can only update their own participant
                            if participant_id != principal.user_id:
                                raise exceptions.ForbiddenError()

                            user = (
                                await session.exec(select(db.User).where(db.User.user_id == participant_id))
                            ).one_or_none()
                            if user is None:
                                raise exceptions.NotFoundError()

                            participant, event_type = await update_user_participant(conversation, user)

                        case "assistant":
                            # users can add any of their assistants to conversation
                            assistant = (
                                await session.exec(
                                    query.select_assistants_for(user_principal=principal).where(
                                        db.Assistant.assistant_id == assistant_id
                                    )
                                )
                            ).one_or_none()
                            if assistant is None:
                                raise exceptions.NotFoundError()

                            (
                                participant,
                                event_type,
                            ) = await update_assistant_participant(conversation, assistant)

                case auth.AssistantServicePrincipal():
                    # assistants can update participants in conversations they are already participants of
                    conversation = (
                        await session.exec(
                            query.select_conversations_for(principal=principal).where(
                                db.Conversation.conversation_id == conversation_id
                            )
                        )
                    ).one_or_none()

                    if conversation is None:
                        raise exceptions.NotFoundError()

                    # assistants can only update their own status
                    if participant_id != str(principal.assistant_id):
                        raise exceptions.ForbiddenError()

                    assistant = (
                        await session.exec(
                            select(db.Assistant).where(db.Assistant.assistant_id == principal.assistant_id)
                        )
                    ).one_or_none()
                    if assistant is None:
                        raise exceptions.NotFoundError()

                    if assistant.assistant_service_id != principal.assistant_service_id:
                        raise exceptions.ForbiddenError()

                    participant, event_type = await update_assistant_participant(conversation, assistant)

            if event_type is not None:
                participants = await participant_.get_conversation_participants(
                    session=session,
                    conversation_id=conversation.conversation_id,
                    include_inactive=True,
                )

                await self._notify_event(
                    ConversationEventQueueItem(
                        event=participant_.participant_event(
                            event_type=event_type,
                            conversation_id=conversation.conversation_id,
                            participant=participant,
                            participants=participants,
                        ),
                    )
                )

            return participant

    async def create_conversation_message(
        self,
        principal: auth.ActorPrincipal,
        conversation_id: uuid.UUID,
        new_message: NewConversationMessage,
    ) -> tuple[ConversationMessage, Iterable]:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=principal).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            if (
                new_message.id is not None
                and (
                    await session.exec(
                        query.select(db.ConversationMessage)
                        .where(db.ConversationMessage.conversation_id == conversation_id)
                        .where(db.ConversationMessage.message_id == new_message.id)
                    )
                ).one_or_none()
                is not None
            ):
                raise exceptions.ConflictError(f"message with id {new_message.id} already exists")

            match principal:
                case auth.UserPrincipal():
                    role = "user"
                    participant_id = principal.user_id
                case auth.AssistantServicePrincipal():
                    # allow assistants to send messages as users, if provided
                    if new_message.sender is not None and new_message.sender.participant_role == "user":
                        role = "user"
                        participant_id = new_message.sender.participant_id
                    else:
                        role = "assistant"
                        participant_id = str(principal.assistant_id)

            # pop "debug" from metadata, if it exists, and merge with the debug field
            message_debug = (new_message.metadata or {}).pop("debug", None)
            # ensure that message_debug is a dictionary, in cases like {"debug": "some message"}, or {"debug": [1,2]}
            if message_debug and not isinstance(message_debug, dict):
                message_debug = {"debug": message_debug}
            message_debug = deepmerge.always_merger.merge(message_debug or {}, new_message.debug_data or {})

            message = db.ConversationMessage(
                conversation_id=conversation.conversation_id,
                sender_participant_role=role,
                sender_participant_id=participant_id,
                message_type=new_message.message_type.value,
                content=new_message.content,
                content_type=new_message.content_type,
                filenames=new_message.filenames or [],
                meta_data=new_message.metadata or {},
            )
            if new_message.id is not None:
                message.message_id = new_message.id

            session.add(message)

            if message_debug:
                debug = db.ConversationMessageDebug(
                    message_id=message.message_id,
                    data=message_debug,
                )
                session.add(debug)

            await session.commit()
            await session.refresh(message)

            background_task: Iterable = ()
            if self._conversation_candidate_for_retitling(
                conversation=conversation
            ) and self._message_candidate_for_retitling(message=message):
                background_task = (
                    self._retitle_conversation,
                    principal,
                    conversation_id,
                    message.sequence,
                )

        message_response = convert.conversation_message_from_db(message, has_debug=bool(message_debug))

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation_id,
                    event=ConversationEventType.message_created,
                    data={
                        "message": message_response.model_dump(),
                    },
                ),
            )
        )

        return message_response, background_task

    def _message_candidate_for_retitling(self, message: db.ConversationMessage) -> bool:
        """Check if the message is a candidate for retitling the conversation."""
        if message.sender_participant_role != ParticipantRole.user.value:
            return False

        if message.message_type != MessageType.chat.value:
            return False

        return True

    def _conversation_candidate_for_retitling(self, conversation: db.Conversation) -> bool:
        """Check if the conversation is a candidate for retitling."""
        if conversation.meta_data.get(META_DATA_KEY_USER_SET_TITLE, False):
            return False

        if conversation.meta_data.get(META_DATA_KEY_AUTO_TITLE_COUNT, 0) >= AUTO_TITLE_COUNT_LIMIT:
            return False

        return True

    async def _retitle_conversation(
        self,
        principal: auth.ActorPrincipal,
        conversation_id: uuid.UUID,
        latest_message_sequence: int,
    ) -> None:
        """Retitle the conversation based on the most recent messages."""

        if not settings.service.azure_openai_endpoint:
            logger.warning(
                "Azure OpenAI endpoint is not configured, skipping retitling conversation %s",
                conversation_id,
            )
            return

        if not settings.service.azure_openai_deployment:
            logger.warning(
                "Azure OpenAI deployment is not configured, skipping retitling conversation %s",
                conversation_id,
            )
            return

        async with self._get_session() as session:
            # Retrieve the most recent messages
            messages = list(
                (
                    await session.exec(
                        select(db.ConversationMessage)
                        .where(
                            db.ConversationMessage.conversation_id == conversation_id,
                            db.ConversationMessage.sequence <= latest_message_sequence,
                            db.ConversationMessage.message_type == MessageType.chat.value,
                        )
                        .order_by(col(db.ConversationMessage.sequence).desc())
                        .limit(10)
                    )
                ).all()
            )
            if not messages:
                return

        messages.reverse()

        completion_messages: list[ChatCompletionMessageParam] = []
        for message in messages:
            match message.sender_participant_role:
                case ParticipantRole.user.value:
                    completion_messages.append({
                        "role": "user",
                        "content": message.content,
                    })

                case _:
                    completion_messages.append({
                        "role": "assistant",
                        "content": message.content,
                    })

        # Call the LLM to get a new title
        try:
            async with openai_client.create_client(
                openai_client.AzureOpenAIServiceConfig(
                    auth_config=openai_client.AzureOpenAIAzureIdentityAuthConfig(),
                    azure_openai_deployment=settings.service.azure_openai_deployment,
                    azure_openai_endpoint=HttpUrl(settings.service.azure_openai_endpoint),
                ),
            ) as client:
                response = await client.beta.chat.completions.parse(
                    messages=[
                        *completion_messages,
                        {
                            "role": "developer",
                            "content": ("The current conversation title is: {conversation.title}"),
                        },
                    ],
                    model=settings.service.azure_openai_model,
                    # the model's description also contains instructions
                    response_format=ConversationTitleResponse,
                )

                if not response.choices:
                    raise RuntimeError("No choices in azure openai response")

                result = response.choices[0].message.parsed
                if result is None:
                    raise RuntimeError("No parsed result in azure openai response")

        except Exception:
            logger.exception("Failed to retitle conversation %s", conversation_id)
            return

        # Update the conversation title if it has not already been changed from the default
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    select(db.Conversation).where(db.Conversation.conversation_id == conversation_id).with_for_update()
                )
            ).one_or_none()
            if conversation is None:
                return

            if not self._conversation_candidate_for_retitling(conversation):
                return

            if result.title.strip():
                conversation.title = result.title.strip()

            conversation.meta_data = {
                **conversation.meta_data,
                META_DATA_KEY_AUTO_TITLE_COUNT: conversation.meta_data.get(META_DATA_KEY_AUTO_TITLE_COUNT, 0) + 1,
            }

            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

        conversation_model = await self.get_conversation(
            conversation_id=conversation.conversation_id,
            principal=principal,
            latest_message_types=set(),
        )

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation.conversation_id,
                    event=ConversationEventType.conversation_updated,
                    data={
                        "conversation": conversation_model.model_dump(),
                    },
                )
            )
        )

    async def get_message(
        self,
        principal: auth.ActorPrincipal,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> ConversationMessage:
        async with self._get_session() as session:
            projection = (
                await session.exec(
                    query.select_conversation_message_projections_for(principal=principal)
                    .where(db.ConversationMessage.conversation_id == conversation_id)
                    .where(db.ConversationMessage.message_id == message_id)
                )
            ).one_or_none()
            if projection is None:
                raise exceptions.NotFoundError()

        message, has_debug = projection

        return convert.conversation_message_from_db(message, has_debug=has_debug)

    async def get_message_debug(
        self,
        principal: auth.ActorPrincipal,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> ConversationMessageDebug:
        async with self._get_session() as session:
            message_debug = (
                await session.exec(
                    query.select_conversation_message_debugs_for(principal=principal).where(
                        db.Conversation.conversation_id == conversation_id,
                        db.ConversationMessageDebug.message_id == message_id,
                    )
                )
            ).one_or_none()
            if message_debug is None:
                raise exceptions.NotFoundError()

        return convert.conversation_message_debug_from_db(message_debug)

    async def get_messages(
        self,
        principal: auth.ActorPrincipal,
        conversation_id: uuid.UUID,
        participant_roles: list[ParticipantRole] | None = None,
        participant_ids: list[str] | None = None,
        message_types: list[MessageType] | None = None,
        before: uuid.UUID | None = None,
        after: uuid.UUID | None = None,
        limit: int = 100,
    ) -> ConversationMessageList:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=principal, include_observer=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = query.select_conversation_message_projections_for(principal=principal).where(
                db.ConversationMessage.conversation_id == conversation_id
            )

            if participant_roles is not None:
                select_query = select_query.where(
                    col(db.ConversationMessage.sender_participant_role).in_([r.value for r in participant_roles])
                )

            if participant_ids is not None:
                select_query = select_query.where(
                    col(db.ConversationMessage.sender_participant_id).in_(participant_ids)
                )

            if message_types is not None:
                select_query = select_query.where(
                    col(db.ConversationMessage.message_type).in_([t.value for t in message_types])
                )

            if before is not None:
                boundary = (
                    await session.exec(
                        query.select_conversation_messages_for(principal=principal).where(
                            db.ConversationMessage.message_id == before
                        )
                    )
                ).one_or_none()
                if boundary is not None:
                    select_query = select_query.where(db.ConversationMessage.sequence < boundary.sequence)

            if after is not None:
                boundary = (
                    await session.exec(
                        query.select_conversation_messages_for(principal=principal).where(
                            db.ConversationMessage.message_id == after
                        )
                    )
                ).one_or_none()
                if boundary is not None:
                    select_query = select_query.where(db.ConversationMessage.sequence > boundary.sequence)

            messages = list(
                (
                    await session.exec(select_query.order_by(col(db.ConversationMessage.sequence).desc()).limit(limit))
                ).all()
            )
            messages.reverse()

            return convert.conversation_message_list_from_db(messages)

    async def delete_message(
        self,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user_principal: auth.UserPrincipal,
    ) -> None:
        async with self._get_session() as session:
            message = (
                await session.exec(
                    query.select_conversation_messages_for(principal=user_principal).where(
                        db.ConversationMessage.conversation_id == conversation_id,
                        db.ConversationMessage.message_id == message_id,
                        or_(
                            db.Conversation.owner_id == user_principal.user_id,
                            db.ConversationMessage.sender_participant_id == user_principal.user_id,
                            and_(
                                col(db.UserParticipant.active_participant).is_(True),
                                db.UserParticipant.conversation_permission == "read_write",
                            ),
                        ),
                    )
                )
            ).one_or_none()
            if message is None:
                raise exceptions.NotFoundError()

            message_response = convert.conversation_message_from_db(message, has_debug=False)

            await session.delete(message)
            await session.commit()

            await self._notify_event(
                ConversationEventQueueItem(
                    event=ConversationEvent(
                        conversation_id=conversation_id,
                        event=ConversationEventType.message_deleted,
                        data={
                            "message": message_response.model_dump(),
                        },
                    ),
                )
            )


=== File: workbench-service/semantic_workbench_service/controller/conversation_share.py ===
import logging
import uuid
from typing import AsyncContextManager, Awaitable, Callable

from semantic_workbench_api_model.workbench_model import (
    ConversationShare,
    ConversationShareList,
    ConversationShareRedemption,
    ConversationShareRedemptionList,
    NewConversationShare,
)
from sqlmodel import and_, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, query
from ..event import ConversationEventQueueItem
from . import convert, exceptions
from . import user as user_

logger = logging.getLogger(__name__)


class ConversationShareController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event

    async def create_conversation_share(
        self,
        new_conversation_share: NewConversationShare,
        user_principal: auth.UserPrincipal,
    ) -> ConversationShare:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal=user_principal, include_all_owned=True).where(
                        db.Conversation.conversation_id == new_conversation_share.conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.InvalidArgumentError("Conversation not found")

            conversation_share = db.ConversationShare(
                conversation_id=new_conversation_share.conversation_id,
                owner_id=user_principal.user_id,
                label=new_conversation_share.label,
                conversation_permission=new_conversation_share.conversation_permission,
                meta_data=new_conversation_share.metadata,
            )

            session.add(conversation_share)
            await session.commit()

            await session.refresh(conversation_share)

        return convert.conversation_share_from_db(conversation_share)

    async def create_conversation_share_with_owner(
        self,
        new_conversation_share: NewConversationShare,
        owner_id: str,
    ) -> ConversationShare:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    select(db.Conversation).where(
                        db.Conversation.conversation_id == new_conversation_share.conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.InvalidArgumentError("Conversation not found")

            conversation_share = db.ConversationShare(
                conversation_id=new_conversation_share.conversation_id,
                owner_id=owner_id,
                label=new_conversation_share.label,
                conversation_permission=new_conversation_share.conversation_permission,
                meta_data=new_conversation_share.metadata,
            )

            session.add(conversation_share)
            await session.commit()

            await session.refresh(conversation_share)

        return convert.conversation_share_from_db(conversation_share)

    async def get_conversation_shares(
        self,
        user_principal: auth.UserPrincipal,
        conversation_id: uuid.UUID | None,
        include_unredeemable: bool,
    ) -> ConversationShareList:
        async with self._get_session() as session:
            query = select(db.ConversationShare).where(
                and_(
                    db.ConversationShare.owner_id == user_principal.user_id,
                    or_(include_unredeemable is True, col(db.ConversationShare.is_redeemable).is_(True)),
                )
            )
            if conversation_id is not None:
                query = query.where(db.ConversationShare.conversation_id == conversation_id)

            conversation_shares = await session.exec(query)

            return convert.conversation_share_list_from_db(conversation_shares)

    async def get_conversation_share(
        self,
        user_principal: auth.UserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShare:
        async with self._get_session() as session:
            conversation_share = (
                await session.exec(
                    select(db.ConversationShare)
                    .where(db.ConversationShare.conversation_share_id == conversation_share_id)
                    .where(
                        or_(
                            db.ConversationShare.owner_id == user_principal.user_id,
                            col(db.ConversationShare.is_redeemable).is_(True),
                        )
                    )
                )
            ).one_or_none()

            if conversation_share is None:
                raise exceptions.NotFoundError()

            return convert.conversation_share_from_db(conversation_share)

    async def delete_conversation_share(
        self,
        user_principal: auth.UserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> None:
        async with self._get_session() as session:
            conversation_share = (
                await session.exec(
                    select(db.ConversationShare)
                    .where(
                        db.ConversationShare.owner_id == user_principal.user_id,
                        db.ConversationShare.conversation_share_id == conversation_share_id,
                        col(db.ConversationShare.is_redeemable).is_(True),
                    )
                    .with_for_update()
                )
            ).one_or_none()

            if conversation_share is None:
                raise exceptions.NotFoundError()

            await session.delete(conversation_share)
            await session.commit()

    async def redeem_conversation_share(
        self,
        user_principal: auth.UserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShareRedemption:
        async with self._get_session() as session:
            await user_.add_or_update_user_from(session=session, user_principal=user_principal)

            # any user can redeem a "redeemable" share, if they have the ID
            conversation_share = (
                await session.exec(
                    select(db.ConversationShare).where(
                        db.ConversationShare.conversation_share_id == conversation_share_id,
                        col(db.ConversationShare.is_redeemable).is_(True),
                    )
                )
            ).one_or_none()
            if conversation_share is None:
                raise exceptions.NotFoundError()

            new_participant = False
            participant = (
                await session.exec(
                    select(db.UserParticipant)
                    .where(db.UserParticipant.conversation_id == conversation_share.conversation_id)
                    .where(db.UserParticipant.user_id == user_principal.user_id)
                    .with_for_update()
                )
            ).one_or_none()
            new_participant = participant is None or not participant.active_participant

            if participant is None:
                participant = db.UserParticipant(
                    conversation_id=conversation_share.conversation_id,
                    user_id=user_principal.user_id,
                    conversation_permission=conversation_share.conversation_permission,
                )

            if not participant.active_participant:
                participant.active_participant = True

            if (
                new_participant
                or
                # only re-assign permission for existing participants if it's a promotion
                (participant.conversation_permission == "read" and conversation_share.conversation_permission != "read")
            ):
                participant.conversation_permission = conversation_share.conversation_permission

            session.add(participant)

            redemption = db.ConversationShareRedemption(
                conversation_share_id=conversation_share_id,
                conversation_id=conversation_share.conversation_id,
                redeemed_by_user_id=user_principal.user_id,
                conversation_permission=participant.conversation_permission,
                new_participant=new_participant,
            )
            session.add(redemption)

            await session.commit()

            await session.refresh(redemption)

            return convert.conversation_share_redemption_from_db(redemption)

    async def get_redemptions_for_share(
        self,
        user_principal: auth.UserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShareRedemptionList:
        async with self._get_session() as session:
            redemptions = await session.exec(
                select(db.ConversationShareRedemption)
                .join(db.ConversationShare)
                .where(
                    db.ConversationShareRedemption.conversation_share_id == conversation_share_id,
                    db.ConversationShare.owner_id == user_principal.user_id,
                )
            )

            return convert.conversation_share_redemption_list_from_db(redemptions)

    async def get_redemptions_for_user(
        self,
        user_principal: auth.UserPrincipal,
    ) -> ConversationShareRedemptionList:
        async with self._get_session() as session:
            redemptions = await session.exec(
                select(db.ConversationShareRedemption).where(
                    db.ConversationShareRedemption.redeemed_by_user_id == user_principal.user_id,
                )
            )

            return convert.conversation_share_redemption_list_from_db(redemptions)


=== File: workbench-service/semantic_workbench_service/controller/convert.py ===
import uuid
from typing import Iterable, Mapping

from semantic_workbench_api_model.workbench_model import (
    Assistant,
    AssistantList,
    AssistantServiceRegistration,
    AssistantServiceRegistrationList,
    Conversation,
    ConversationList,
    ConversationMessage,
    ConversationMessageDebug,
    ConversationMessageList,
    ConversationParticipant,
    ConversationParticipantList,
    ConversationPermission,
    ConversationShare,
    ConversationShareList,
    ConversationShareRedemption,
    ConversationShareRedemptionList,
    File,
    FileList,
    FileVersion,
    FileVersions,
    MessageSender,
    MessageType,
    ParticipantRole,
    User,
    UserList,
)

from .. import db


def user_from_db(model: db.User) -> User:
    return User(
        id=model.user_id,
        name=model.name,
        image=model.image,
        service_user=model.service_user,
        created_datetime=model.created_datetime,
    )


def user_list_from_db(models: Iterable[db.User]) -> UserList:
    return UserList(users=[user_from_db(model) for model in models])


def assistant_service_registration_from_db(
    model: db.AssistantServiceRegistration,
    include_api_key_name: bool,
    api_key: str | None = None,
) -> AssistantServiceRegistration:
    return AssistantServiceRegistration(
        assistant_service_id=model.assistant_service_id,
        created_by_user_id=model.created_by_user_id,
        created_by_user_name=model.related_created_by_user.name,
        created_datetime=model.created_datetime,
        name=model.name,
        description=model.description,
        include_in_listing=model.include_in_listing,
        api_key_name=model.api_key_name if include_api_key_name else "",
        api_key=api_key,
        assistant_service_url=model.assistant_service_url,
        assistant_service_online=model.assistant_service_online,
        assistant_service_online_expiration_datetime=model.assistant_service_online_expiration_datetime,
    )


def assistant_service_registration_list_from_db(
    models: Iterable[db.AssistantServiceRegistration], include_api_key_name: bool
) -> AssistantServiceRegistrationList:
    return AssistantServiceRegistrationList(
        assistant_service_registrations=[
            assistant_service_registration_from_db(model=a, include_api_key_name=include_api_key_name) for a in models
        ]
    )


def assistant_from_db(
    model: db.Assistant,
) -> Assistant:
    return Assistant(
        id=model.assistant_id,
        name=model.name,
        image=model.image,
        metadata=model.meta_data,
        assistant_service_id=model.assistant_service_id,
        assistant_service_online=model.related_assistant_service_registration.assistant_service_online,
        template_id=model.template_id,
        created_datetime=model.created_datetime,
    )


def assistant_list_from_db(
    models: Iterable[db.Assistant],
) -> AssistantList:
    return AssistantList(assistants=[assistant_from_db(model=a) for a in models])


def conversation_participant_from_db_user(model: db.UserParticipant) -> ConversationParticipant:
    return ConversationParticipant(
        role=ParticipantRole.service if model.service_user else ParticipantRole.user,
        id=model.user_id,
        conversation_id=model.conversation_id,
        name=model.name,
        image=model.image,
        status=model.status,
        status_updated_timestamp=model.status_updated_datetime,
        active_participant=model.active_participant,
        metadata=model.meta_data,
        conversation_permission=ConversationPermission(model.conversation_permission),
    )


def conversation_participant_from_db_assistant(
    model: db.AssistantParticipant, assistant: db.Assistant | None
) -> ConversationParticipant:
    return ConversationParticipant(
        role=ParticipantRole.assistant,
        id=str(model.assistant_id),
        conversation_id=model.conversation_id,
        name=model.name,
        image=model.image,
        status=model.status,
        status_updated_timestamp=model.status_updated_datetime,
        active_participant=model.active_participant,
        metadata=model.meta_data,
        online=assistant.related_assistant_service_registration.assistant_service_online if assistant else False,
        conversation_permission=ConversationPermission.read_write,
    )


def conversation_participant_list_from_db(
    user_participants: Iterable[db.UserParticipant],
    assistant_participants: Iterable[db.AssistantParticipant],
    assistants: Mapping[uuid.UUID, db.Assistant],
) -> ConversationParticipantList:
    return ConversationParticipantList(
        participants=[conversation_participant_from_db_user(model=p) for p in user_participants]
        + [
            conversation_participant_from_db_assistant(model=p, assistant=assistants.get(p.assistant_id))
            for p in assistant_participants
        ]
    )


def conversation_from_db(
    model: db.Conversation,
    user_participants: Iterable[db.UserParticipant],
    assistant_participants: Iterable[db.AssistantParticipant],
    assistants: Mapping[uuid.UUID, db.Assistant],
    latest_message: db.ConversationMessage | None,
    latest_message_has_debug: bool,
    permission: str,
) -> Conversation:
    return Conversation(
        id=model.conversation_id,
        title=model.title,
        owner_id=model.owner_id,
        imported_from_conversation_id=model.imported_from_conversation_id,
        metadata=model.meta_data,
        created_datetime=model.created_datetime,
        conversation_permission=ConversationPermission(permission),
        latest_message=conversation_message_from_db(model=latest_message, has_debug=latest_message_has_debug)
        if latest_message
        else None,
        participants=conversation_participant_list_from_db(
            user_participants=user_participants,
            assistant_participants=assistant_participants,
            assistants=assistants,
        ).participants,
    )


def conversation_list_from_db(
    models: Iterable[
        tuple[
            db.Conversation,
            Iterable[db.UserParticipant],
            Iterable[db.AssistantParticipant],
            dict[uuid.UUID, db.Assistant],
            db.ConversationMessage | None,
            bool,
            str,
        ]
    ],
) -> ConversationList:
    return ConversationList(
        conversations=[
            conversation_from_db(
                model=conversation,
                user_participants=user_participants,
                assistant_participants=assistant_participants,
                assistants=assistants,
                latest_message=latest_message,
                latest_message_has_debug=latest_message_has_debug,
                permission=permission,
            )
            for conversation, user_participants, assistant_participants, assistants, latest_message, latest_message_has_debug, permission in models
        ]
    )


def conversation_share_from_db(model: db.ConversationShare) -> ConversationShare:
    return ConversationShare(
        id=model.conversation_share_id,
        created_by_user=user_from_db(model.related_owner),
        conversation_id=model.conversation_id,
        conversation_title=model.related_conversation.title,
        owner_id=model.owner_id,
        conversation_permission=ConversationPermission(model.conversation_permission),
        is_redeemable=model.is_redeemable,
        created_datetime=model.created_datetime,
        label=model.label,
        metadata=model.meta_data,
    )


def conversation_share_list_from_db(models: Iterable[db.ConversationShare]) -> ConversationShareList:
    return ConversationShareList(conversation_shares=[conversation_share_from_db(model=m) for m in models])


def conversation_share_redemption_from_db(model: db.ConversationShareRedemption) -> ConversationShareRedemption:
    return ConversationShareRedemption(
        id=model.conversation_share_redemption_id,
        redeemed_by_user=user_from_db(model.related_redeemed_by_user),
        conversation_share_id=model.conversation_share_id,
        conversation_permission=ConversationPermission(model.conversation_permission),
        conversation_id=model.conversation_id,
        created_datetime=model.created_datetime,
        new_participant=model.new_participant,
    )


def conversation_share_redemption_list_from_db(
    models: Iterable[db.ConversationShareRedemption],
) -> ConversationShareRedemptionList:
    return ConversationShareRedemptionList(
        conversation_share_redemptions=[conversation_share_redemption_from_db(model=m) for m in models]
    )


def conversation_message_from_db(model: db.ConversationMessage, has_debug: bool) -> ConversationMessage:
    return ConversationMessage(
        id=model.message_id,
        sender=MessageSender(
            participant_id=model.sender_participant_id,
            participant_role=ParticipantRole(model.sender_participant_role),
        ),
        timestamp=model.created_datetime,
        message_type=MessageType(model.message_type),
        content=model.content,
        content_type=model.content_type,
        metadata=model.meta_data,
        filenames=model.filenames,
        has_debug_data=has_debug,
    )


def conversation_message_list_from_db(
    models: Iterable[tuple[db.ConversationMessage, bool]],
) -> ConversationMessageList:
    return ConversationMessageList(messages=[conversation_message_from_db(m, debug) for m, debug in models])


def conversation_message_debug_from_db(model: db.ConversationMessageDebug) -> ConversationMessageDebug:
    return ConversationMessageDebug(
        message_id=model.message_id,
        debug_data=model.data,
    )


def file_from_db(models: tuple[db.File, db.FileVersion]) -> File:
    file, version = models
    return File(
        conversation_id=file.conversation_id,
        filename=file.filename,
        current_version=file.current_version,
        content_type=version.content_type,
        file_size=version.file_size,
        participant_id=version.participant_id,
        participant_role=ParticipantRole(version.participant_role),
        metadata=version.meta_data,
        created_datetime=file.created_datetime,
        updated_datetime=version.created_datetime,
    )


def file_list_from_db(models: Iterable[tuple[db.File, db.FileVersion]]) -> FileList:
    return FileList(files=[file_from_db(m) for m in models])


def file_version_from_db(model: db.FileVersion) -> FileVersion:
    return FileVersion(
        version=model.version,
        content_type=model.content_type,
        file_size=model.file_size,
        metadata=model.meta_data,
    )


def file_versions_from_db(file: db.File, versions: Iterable[db.FileVersion]) -> FileVersions:
    return FileVersions(
        conversation_id=file.conversation_id,
        filename=file.filename,
        created_datetime=file.created_datetime,
        current_version=file.current_version,
        versions=[file_version_from_db(v) for v in versions],
    )


=== File: workbench-service/semantic_workbench_service/controller/exceptions.py ===
from typing import Annotated, Any

from fastapi import HTTPException
from typing_extensions import Doc


class Error(HTTPException):
    pass


class RuntimeError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=500, detail=detail)


class NotFoundError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=404, detail=detail)


class ConflictError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class InvalidArgumentError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=400, detail=detail)


class ForbiddenError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=403, detail=detail)


=== File: workbench-service/semantic_workbench_service/controller/export_import.py ===
import collections
import datetime
import re
import tempfile
import uuid
from operator import or_
from typing import IO, Any, AsyncGenerator, Generator, Iterable, Iterator

from attr import dataclass
from pydantic import BaseModel
from sqlalchemy import ScalarResult, func
from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import db


class _Record(BaseModel):
    type: str
    data: dict[str, Any]


def _model_record(model: SQLModel) -> _Record:
    data = model.model_dump(mode="json")
    return _Record(type=model.__class__.__name__, data=data)


def _lines_from(records: Iterator[_Record]) -> Generator[bytes, None, None]:
    for record in records:
        yield (record.model_dump_json() + "\n").encode("utf-8")


async def export_file(
    conversation_ids: set[uuid.UUID],
    assistant_ids: set[uuid.UUID],
    session: AsyncSession,
) -> AsyncGenerator[bytes, None]:
    assistants = await session.exec(
        select(db.Assistant)
        .where(col(db.Assistant.assistant_id).in_(assistant_ids))
        .order_by(col(db.Assistant.assistant_id).asc())
    )

    conversations = await session.exec(
        select(db.Conversation)
        .where(col(db.Conversation.conversation_id).in_(conversation_ids))
        .order_by(col(db.Conversation.conversation_id).asc())
    )

    files = await session.exec(
        select(db.File)
        .where(col(db.File.conversation_id).in_(conversation_ids))
        .order_by(col(db.File.conversation_id).asc())
        .order_by(col(db.File.created_datetime).asc())
    )

    file_versions = await session.exec(
        select(db.FileVersion)
        .join(db.File)
        .where(col(db.File.conversation_id).in_(conversation_ids))
        .order_by(col(db.File.conversation_id).asc())
        .order_by(col(db.File.created_datetime).asc())
        .order_by(col(db.FileVersion.version).asc())
    )

    messages = await session.exec(
        select(db.ConversationMessage)
        .where(col(db.ConversationMessage.conversation_id).in_(conversation_ids))
        .order_by(col(db.ConversationMessage.conversation_id).asc())
        .order_by(col(db.ConversationMessage.sequence).asc())
    )

    message_debugs = await session.exec(
        select(db.ConversationMessageDebug)
        .join(db.ConversationMessage)
        .where(col(db.ConversationMessage.conversation_id).in_(conversation_ids))
        .order_by(col(db.ConversationMessage.conversation_id).asc())
        .order_by(col(db.ConversationMessage.sequence).asc())
    )

    user_participants = await session.exec(
        select(db.UserParticipant)
        .where(col(db.UserParticipant.conversation_id).in_(conversation_ids))
        .order_by(col(db.UserParticipant.conversation_id).asc())
        .order_by(col(db.UserParticipant.joined_datetime).asc())
    )

    assistant_participants = await session.exec(
        select(db.AssistantParticipant)
        .where(col(db.AssistantParticipant.conversation_id).in_(conversation_ids))
        .order_by(col(db.AssistantParticipant.conversation_id).asc())
        .order_by(col(db.AssistantParticipant.joined_datetime).asc())
    )

    def _records(*sources: ScalarResult) -> Generator[_Record, None, None]:
        for source in sources:
            for record in source:
                yield _model_record(record)

    with tempfile.TemporaryFile() as f:
        f.writelines(
            _lines_from(
                _records(
                    assistants,
                    conversations,
                    messages,
                    message_debugs,
                    user_participants,
                    assistant_participants,
                    files,
                    file_versions,
                )
            )
        )
        f.seek(0)
        for line in iter(lambda: f.readline(), b""):
            yield line


@dataclass
class ImportResult:
    assistant_id_old_to_new: dict[uuid.UUID, tuple[uuid.UUID, bool]]
    conversation_id_old_to_new: dict[uuid.UUID, uuid.UUID]
    message_id_old_to_new: dict[uuid.UUID, uuid.UUID]
    assistant_conversation_old_ids: dict[uuid.UUID, set[uuid.UUID]]
    file_id_old_to_new: dict[uuid.UUID, uuid.UUID]


async def import_files(session: AsyncSession, owner_id: str, files: Iterable[IO[bytes]]) -> ImportResult:
    result = ImportResult(
        assistant_id_old_to_new={},
        conversation_id_old_to_new={},
        message_id_old_to_new={},
        assistant_conversation_old_ids=collections.defaultdict(set),
        file_id_old_to_new={},
    )

    async def _process_record(record: _Record) -> None:
        match record.type:
            case db.Assistant.__name__:
                assistant = db.Assistant.model_validate(record.data)

                # re-use existing assistants with matching service_id, template_id, and name
                existing_assistant = (
                    await session.exec(
                        select(db.Assistant)
                        .where(db.Assistant.owner_id == owner_id)
                        .where(
                            db.Assistant.assistant_service_id == assistant.assistant_service_id,
                            db.Assistant.template_id == assistant.template_id,
                            db.Assistant.name == assistant.name,
                        )
                        .order_by(col(db.Assistant.created_datetime).desc())
                        .limit(1)
                    )
                ).one_or_none()
                if existing_assistant:
                    result.assistant_id_old_to_new[assistant.assistant_id] = existing_assistant.assistant_id, False
                    return

                assistant.imported_from_assistant_id = assistant.assistant_id
                assistant.created_datetime = datetime.datetime.now(datetime.UTC)
                result.assistant_id_old_to_new[assistant.assistant_id] = uuid.uuid4(), True
                assistant.assistant_id, _ = result.assistant_id_old_to_new[assistant.assistant_id]
                assistant.owner_id = owner_id

                like_expression = re.sub(r"([?%_])", r"\\\1", assistant.name.lower())
                like_expression = f"{like_expression} (%)"
                existing_count = 0
                for possible_match in await session.exec(
                    select(db.Assistant)
                    .where(db.Assistant.owner_id == owner_id)
                    .where(
                        or_(
                            func.lower(col(db.Assistant.name)).like(like_expression),
                            func.lower(col(db.Assistant.name)) == assistant.name.lower(),
                        )
                    )
                ):
                    if possible_match.name.lower() == assistant.name.lower():
                        existing_count += 1
                        continue
                    name = possible_match.name.lower().replace(assistant.name.lower(), "", 1)
                    if re.match(r"^ \(\d+\)$", name):
                        existing_count += 1

                if existing_count > 0:
                    assistant.name = f"{assistant.name} ({existing_count})"

                session.add(assistant)

            case db.AssistantParticipant.__name__:
                participant = db.AssistantParticipant.model_validate(record.data)
                result.assistant_conversation_old_ids[participant.assistant_id].add(participant.conversation_id)
                conversation_id = result.conversation_id_old_to_new.get(participant.conversation_id)
                if conversation_id is None:
                    raise RuntimeError(f"conversation_id {participant.conversation_id} is not found")
                participant.conversation_id = conversation_id
                participant.status = None
                assistant_id, _ = result.assistant_id_old_to_new.get(participant.assistant_id, (None, None))
                if assistant_id is not None:
                    participant.assistant_id = assistant_id
                session.add(participant)

            case db.UserParticipant.__name__:
                participant = db.UserParticipant.model_validate(record.data)
                conversation_id = result.conversation_id_old_to_new.get(participant.conversation_id)
                if conversation_id is None:
                    raise RuntimeError(f"conversation_id {participant.conversation_id} is not found")
                participant.conversation_id = conversation_id
                # user participants should always be inactive on import
                participant.active_participant = False
                participant.status = None

                await db.insert_if_not_exists(
                    session, db.User(user_id=participant.user_id, name="unknown imported user", service_user=False)
                )

                session.add(participant)

            case db.Conversation.__name__:
                conversation = db.Conversation.model_validate(record.data)
                conversation.imported_from_conversation_id = conversation.conversation_id
                result.conversation_id_old_to_new[conversation.conversation_id] = uuid.uuid4()
                conversation.conversation_id = result.conversation_id_old_to_new[conversation.conversation_id]
                conversation.created_datetime = datetime.datetime.now(datetime.UTC)
                conversation.owner_id = owner_id

                like_expression = re.sub(r"([?%_])", r"\\\1", conversation.title.lower())
                like_expression = f"{like_expression} (%)"
                existing_count = 0
                for possible_match in await session.exec(
                    select(db.Conversation)
                    .where(db.Conversation.owner_id == owner_id)
                    .where(
                        or_(
                            func.lower(col(db.Conversation.title)).like(like_expression),
                            func.lower(col(db.Conversation.title)) == conversation.title.lower(),
                        )
                    )
                ):
                    if possible_match.title.lower() == conversation.title.lower():
                        existing_count += 1
                        continue

                    name = possible_match.title.lower().replace(conversation.title.lower(), "", 1)
                    if re.match(r"^ \(\d+\)$", name):
                        existing_count += 1

                if existing_count > 0:
                    conversation.title = f"{conversation.title} ({existing_count})"

                session.add(conversation)

            case db.ConversationMessage.__name__:
                record.data.pop("sequence", None)
                message = db.ConversationMessage.model_validate(record.data)
                conversation_id = result.conversation_id_old_to_new.get(message.conversation_id)
                if conversation_id is None:
                    raise RuntimeError(f"conversation_id {message.conversation_id} is not found")
                message.conversation_id = conversation_id
                result.message_id_old_to_new[message.message_id] = uuid.uuid4()
                message.message_id = result.message_id_old_to_new[message.message_id]

                if message.sender_participant_role == "assistant":
                    assistant_id, _ = result.assistant_id_old_to_new.get(
                        uuid.UUID(message.sender_participant_id), (None, None)
                    )
                    if assistant_id is not None:
                        message.sender_participant_id = str(assistant_id)
                session.add(message)

            case db.ConversationMessageDebug.__name__:
                message_debug = db.ConversationMessageDebug.model_validate(record.data)
                message_id = result.message_id_old_to_new.get(message_debug.message_id)
                if message_id is None:
                    raise RuntimeError(f"message_id {message_debug.message_id} is not found")
                message_debug.message_id = message_id
                session.add(message_debug)

            case db.File.__name__:
                file = db.File.model_validate(record.data)
                result.file_id_old_to_new[file.file_id] = uuid.uuid4()
                file.file_id = result.file_id_old_to_new[file.file_id]

                conversation_id = result.conversation_id_old_to_new.get(file.conversation_id)
                if conversation_id is None:
                    raise RuntimeError(f"conversation_id {file.conversation_id} is not found")
                file.conversation_id = conversation_id
                session.add(file)

            case db.FileVersion.__name__:
                file_version = db.FileVersion.model_validate(record.data)
                file_id = result.file_id_old_to_new.get(file_version.file_id)
                if file_id is None:
                    raise RuntimeError(f"file_id {file_version.file_id} is not found")
                file_version.file_id = file_id

                if file_version.participant_role == "assistant":
                    assistant_id, _ = result.assistant_id_old_to_new.get(
                        uuid.UUID(file_version.participant_id), (None, None)
                    )
                    if assistant_id is not None:
                        file_version.participant_id = str(assistant_id)
                session.add(file_version)

    for file in files:
        for line in iter(lambda: file.readline(), b""):
            record = _Record.model_validate_json(line.decode("utf-8"))
            await _process_record(record)
            await session.flush()

    # ensure the owner is a participant in all conversations
    for _, conversation_id in result.conversation_id_old_to_new.items():
        await db.insert_if_not_exists(
            session,
            db.UserParticipant(
                conversation_id=conversation_id,
                user_id=owner_id,
                active_participant=True,
                conversation_permission="read_write",
            ),
        )

        importing_user_participant = (
            await session.exec(
                select(db.UserParticipant)
                .where(db.UserParticipant.conversation_id == conversation_id)
                .where(db.UserParticipant.user_id == owner_id)
                .with_for_update()
            )
        ).one()
        importing_user_participant.conversation_permission = "read_write"
        importing_user_participant.active_participant = True
        session.add(importing_user_participant)

    await session.flush()

    return result


=== File: workbench-service/semantic_workbench_service/controller/file.py ===
import uuid
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Generator,
    Iterable,
    NamedTuple,
)

from fastapi import UploadFile
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    FileList,
    FileVersions,
)
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db, files, query
from ..event import ConversationEventQueueItem
from . import convert, exceptions

DownloadFileResult = NamedTuple(
    "DownloadFileResult", [("filename", str), ("content_type", str), ("stream", Iterable[bytes])]
)


class FileController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
        notify_event: Callable[[ConversationEventQueueItem], Awaitable],
        file_storage: files.Storage,
    ) -> None:
        self._get_session = get_session
        self._notify_event = notify_event
        self._file_storage = file_storage

    async def upload_files(
        self,
        conversation_id: uuid.UUID,
        upload_files: list[UploadFile],
        principal: auth.ActorPrincipal,
        file_metadata: dict[str, Any],
    ) -> FileList:
        if len(upload_files) > 10:
            raise exceptions.InvalidArgumentError(detail="file uploads limited to 10 at a time")

        unique_filenames = {f.filename for f in upload_files}
        if len([f for f in unique_filenames if not f]) > 0:
            raise exceptions.InvalidArgumentError(detail="filename is required for all file uploads")

        if len(unique_filenames) != len(upload_files):
            raise exceptions.InvalidArgumentError(detail="filenames are required to be unique")

        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            existing_files = (
                await session.exec(
                    select(db.File)
                    .where(db.File.conversation_id == conversation_id)
                    .where(col(db.File.filename).in_(unique_filenames))
                    .with_for_update()
                )
            ).all()

            file_record_and_uploads = [
                (
                    next(
                        (f for f in existing_files if f.filename == upload_file.filename),
                        db.File(
                            conversation_id=conversation_id,
                            filename=upload_file.filename,
                            current_version=0,
                        ),
                    ),
                    upload_file,
                )
                for upload_file in upload_files
                if upload_file.filename
            ]

            match principal:
                case auth.UserPrincipal():
                    role = "user"
                    participant_id = principal.user_id
                case auth.AssistantServicePrincipal():
                    role = "assistant"
                    participant_id = str(principal.assistant_id)

            file_record_and_versions: list[tuple[db.File, db.FileVersion]] = []

            for file_record, upload_file in file_record_and_uploads:
                file_record.current_version += 1
                new_version = db.FileVersion(
                    file_id=file_record.file_id,
                    participant_role=role,
                    participant_id=participant_id,
                    version=file_record.current_version,
                    content_type=upload_file.content_type or "",
                    file_size=upload_file.size or 0,
                    meta_data=file_metadata.get(file_record.filename, {}),
                    storage_filename=f"{file_record.file_id.hex}_{file_record.current_version}",
                )
                file_record_and_versions.append((file_record, new_version))

                self._file_storage.write_file(
                    namespace=str(conversation_id),
                    filename=new_version.storage_filename,
                    content=upload_file.file,
                )
                session.add(file_record)
                session.add(new_version)

                await self._notify_event(
                    ConversationEventQueueItem(
                        event=ConversationEvent(
                            conversation_id=conversation_id,
                            event=(
                                ConversationEventType.file_created
                                if new_version.version == 1
                                else ConversationEventType.file_updated
                            ),
                            data={
                                "file": convert.file_from_db((file_record, new_version)).model_dump(),
                            },
                        ),
                    )
                )

            await session.commit()

            return convert.file_list_from_db(file_record_and_versions)

    async def list_files(
        self,
        conversation_id: uuid.UUID,
        principal: auth.ActorPrincipal,
        prefix: str | None = None,
    ) -> FileList:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal, include_all_owned=True, include_observer=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = (
                select(db.File, db.FileVersion)
                .join(db.FileVersion)
                .where(db.File.current_version == db.FileVersion.version)
                .where(db.File.conversation_id == conversation_id)
            )
            if prefix is not None:
                select_query = select_query.where(db.File.filename.startswith(prefix))
            select_query = select_query.order_by(col(db.File.filename).asc())
            files = await session.exec(select_query)

            return convert.file_list_from_db(files)

    async def file_versions(
        self,
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.ActorPrincipal,
        version: int | None = None,
    ) -> FileVersions:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal, include_all_owned=True, include_observer=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = (
                select(db.File, db.FileVersion)
                .join(db.FileVersion)
                .where(db.File.conversation_id == conversation_id)
                .where(db.File.filename == filename)
            )
            if version is not None:
                select_query = select_query.where(db.FileVersion.version == version)
            select_query = select_query.order_by(col(db.FileVersion.version).asc())

            file_records = (await session.exec(select_query)).all()
            if not file_records:
                raise exceptions.NotFoundError()

            return convert.file_versions_from_db(
                file=file_records[0][0],
                versions=(version for _, version in file_records),
            )

    async def update_file_metadata(
        self,
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.ActorPrincipal,
        metadata: dict[str, Any],
    ) -> FileVersions:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal, include_all_owned=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            record_pair = (
                await session.exec(
                    (
                        select(db.File, db.FileVersion)
                        .join(db.FileVersion)
                        .where(db.File.conversation_id == conversation_id)
                        .where(db.File.filename == filename)
                        .order_by(col(db.FileVersion.version).desc())
                        .limit(1)
                    )
                )
            ).one_or_none()
            if record_pair is None:
                raise exceptions.NotFoundError()

            file_record, version_record = record_pair
            version_record.meta_data = {**version_record.meta_data, **metadata}

            session.add(version_record)
            await session.commit()

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation_id,
                    event=ConversationEventType.file_updated,
                    data={
                        "file": convert.file_from_db((file_record, version_record)).model_dump(),
                    },
                ),
            )
        )

        return await self.file_versions(
            conversation_id=conversation_id,
            filename=filename,
            principal=principal,
            version=version_record.version,
        )

    async def download_file(
        self,
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.ActorPrincipal,
        version: int | None = None,
    ) -> DownloadFileResult:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal, include_all_owned=True, include_observer=True).where(
                        db.Conversation.conversation_id == conversation_id
                    )
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            select_query = (
                select(db.File, db.FileVersion)
                .join(db.FileVersion)
                .where(db.File.conversation_id == conversation_id)
                .where(db.File.filename == filename)
            )
            if version is not None:
                select_query = select_query.where(db.FileVersion.version == version)
            else:
                select_query = select_query.where(db.File.current_version == db.FileVersion.version)

            file_records = (await session.exec(select_query)).one_or_none()
            if file_records is None:
                raise exceptions.NotFoundError()

            file_record, version_record = file_records

        def generator_wrapper() -> Generator[bytes, Any, None]:
            with self._file_storage.read_file(
                namespace=str(conversation_id),
                filename=version_record.storage_filename,
            ) as file:
                for chunk in iter(lambda: file.read(100 * 1_024), b""):
                    yield chunk

        filename = file_record.filename.split("/")[-1]

        return DownloadFileResult(
            filename=filename,
            content_type=version_record.content_type,
            stream=generator_wrapper(),
        )

    async def delete_file(
        self,
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.ActorPrincipal,
    ) -> None:
        async with self._get_session() as session:
            conversation = (
                await session.exec(
                    query.select_conversations_for(principal).where(db.Conversation.conversation_id == conversation_id)
                )
            ).one_or_none()
            if conversation is None:
                raise exceptions.NotFoundError()

            file_record = (
                await session.exec(
                    select(db.File)
                    .where(db.File.conversation_id == conversation_id)
                    .where(db.File.filename == filename)
                )
            ).one_or_none()
            if file_record is None:
                raise exceptions.NotFoundError()

            current_version = (
                await session.exec(
                    select(db.FileVersion)
                    .where(db.FileVersion.file_id == file_record.file_id)
                    .where(db.FileVersion.version == file_record.current_version)
                )
            ).one()

            version_records = (
                await session.exec(select(db.FileVersion).where(db.FileVersion.file_id == file_record.file_id))
            ).all()

            for version_record in version_records:
                self._file_storage.delete_file(
                    namespace=str(conversation_id),
                    filename=version_record.storage_filename,
                )
                await session.delete(version_record)
            await session.commit()

            await session.delete(file_record)
            await session.commit()

        await self._notify_event(
            ConversationEventQueueItem(
                event=ConversationEvent(
                    conversation_id=conversation_id,
                    event=ConversationEventType.file_deleted,
                    data={
                        "file": convert.file_from_db((file_record, current_version)).model_dump(),
                    },
                ),
            )
        )


=== File: workbench-service/semantic_workbench_service/controller/participant.py ===
import uuid
from typing import Literal

from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    ConversationParticipant,
    ConversationParticipantList,
)
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import db
from . import convert


async def get_conversation_participants(
    session: AsyncSession, conversation_id: uuid.UUID, include_inactive: bool
) -> ConversationParticipantList:
    user_query = select(db.UserParticipant).where(db.UserParticipant.conversation_id == conversation_id)
    assistant_query = select(db.AssistantParticipant).where(db.AssistantParticipant.conversation_id == conversation_id)

    if not include_inactive:
        user_query = user_query.where(col(db.UserParticipant.active_participant).is_(True))
        assistant_query = assistant_query.where(col(db.AssistantParticipant.active_participant).is_(True))

    user_results = (await session.exec(user_query)).all()
    assistant_results = (await session.exec(assistant_query)).all()

    assistant_ids = {p.assistant_id for p in assistant_results}
    assistants = (
        await session.exec(select(db.Assistant).where(col(db.Assistant.assistant_id).in_(assistant_ids)))
    ).all()
    assistant_map = {a.assistant_id: a for a in assistants}

    return convert.conversation_participant_list_from_db(
        user_participants=user_results, assistant_participants=assistant_results, assistants=assistant_map
    )


def participant_event(
    event_type: Literal[
        ConversationEventType.participant_created,
        ConversationEventType.participant_updated,
    ],
    conversation_id: uuid.UUID,
    participant: ConversationParticipant,
    participants: ConversationParticipantList,
) -> ConversationEvent:
    return ConversationEvent(
        conversation_id=conversation_id,
        event=event_type,
        data={
            "participant": participant.model_dump(),
            **participants.model_dump(),
        },
    )


=== File: workbench-service/semantic_workbench_service/controller/user.py ===
from typing import AsyncContextManager, Callable

from semantic_workbench_api_model import workbench_model
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import auth, db
from . import convert


async def add_or_update_user_from(
    session: AsyncSession,
    user_principal: auth.UserPrincipal,
) -> None:
    is_service_user = isinstance(user_principal, auth.ServiceUserPrincipal)
    inserted = await db.insert_if_not_exists(
        session, db.User(user_id=user_principal.user_id, name=user_principal.name, service_user=is_service_user)
    )
    if inserted:
        return await session.commit()

    user = (
        await session.exec(select(db.User).where(db.User.user_id == user_principal.user_id).with_for_update())
    ).one()
    user.name = user_principal.name
    user.service_user = isinstance(user_principal, auth.ServiceUserPrincipal)
    session.add(user)
    await session.commit()


class UserController:
    def __init__(
        self,
        get_session: Callable[[], AsyncContextManager[AsyncSession]],
    ) -> None:
        self._get_session = get_session

    async def update_user(
        self,
        user_principal: auth.UserPrincipal,
        user_id: str,
        update_user: workbench_model.UpdateUser,
    ) -> workbench_model.User:
        async with self._get_session() as session:
            inserted = await db.insert_if_not_exists(
                session, db.User(user_id=user_id, name=update_user.name or user_principal.name, image=update_user.image)
            )

            user = (await session.exec(select(db.User).where(db.User.user_id == user_id).with_for_update())).one()
            if not inserted:
                updates = update_user.model_dump(exclude_unset=True)
                for field, value in updates.items():
                    setattr(user, field, value)

                session.add(user)

            await session.commit()

        return convert.user_from_db(model=user)

    async def get_users(self, user_ids: list[str]) -> workbench_model.UserList:
        async with self._get_session() as session:
            users = (await session.exec(select(db.User).where(col(db.User.user_id).in_(user_ids)))).all()

        return convert.user_list_from_db(models=users)

    async def get_user_me(self, user_principal: auth.UserPrincipal) -> workbench_model.User:
        async with self._get_session() as session:
            await add_or_update_user_from(session, user_principal=user_principal)
            user = (await session.exec(select(db.User).where(db.User.user_id == user_principal.user_id))).one()

        return convert.user_from_db(model=user)


=== File: workbench-service/semantic_workbench_service/db.py ===
import datetime
import logging
import pathlib
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator
from urllib.parse import urlparse

import sqlalchemy
import sqlalchemy.event
import sqlalchemy.orm
import sqlalchemy.orm.attributes
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import Field, Relationship, Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from . import service_user_principals
from .config import DBSettings

# Download DB Browser for SQLite to view the database
# https://sqlitebrowser.org/dl/

logger = logging.getLogger(__name__)


def _date_time_nullable() -> Any:  # noqa: ANN401
    return Field(sa_column=sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), nullable=True))


def date_time_default_to_now(index: bool | None = None) -> Any:  # noqa: ANN401
    return Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            index=index,
            default=lambda: datetime.datetime.now(datetime.UTC),
        ),
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )


class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    created_datetime: datetime.datetime = date_time_default_to_now()
    name: str
    image: str | None = None
    service_user: bool = False

    def on_update(self, session: Session) -> None:
        # update UserParticipants for this user
        participants = session.exec(select(UserParticipant).where(UserParticipant.user_id == self.user_id))
        for participant in participants:
            participant.name = self.name
            participant.image = self.image
            participant.service_user = self.service_user
            session.add(participant)


class AssistantServiceRegistration(SQLModel, table=True):
    assistant_service_id: str = Field(primary_key=True)
    created_by_user_id: str = Field(foreign_key="user.user_id")
    created_datetime: datetime.datetime = date_time_default_to_now()
    name: str
    description: str
    include_in_listing: bool = True
    api_key_name: str

    assistant_service_url: str = ""
    assistant_service_online_expiration_datetime: Annotated[datetime.datetime | None, _date_time_nullable()] = None
    assistant_service_online: bool = False

    related_created_by_user: User = Relationship(sa_relationship_kwargs={"lazy": "selectin"})


class Assistant(SQLModel, table=True):
    assistant_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: str = Field(foreign_key="user.user_id", index=True)
    assistant_service_id: str = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "assistantserviceregistration.assistant_service_id",
                name="fk_assistant_assistant_service_id_assistantserviceregistration",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )
    template_id: str
    created_datetime: datetime.datetime = date_time_default_to_now()
    imported_from_assistant_id: uuid.UUID | None
    name: str
    image: str | None = None
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_owner: User = Relationship()
    related_assistant_service_registration: sqlalchemy.orm.Mapped[AssistantServiceRegistration] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def on_update(self, session: Session) -> None:
        # update AssistantParticipants for this assistant
        participants = session.exec(
            select(AssistantParticipant).where(AssistantParticipant.assistant_id == self.assistant_id),
        )
        for participant in participants:
            participant.name = self.name
            participant.image = self.image
            session.add(participant)


class Conversation(SQLModel, table=True):
    conversation_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_datetime: datetime.datetime = date_time_default_to_now()
    owner_id: str = Field(foreign_key="user.user_id")
    title: str
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})
    imported_from_conversation_id: uuid.UUID | None

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_owner: sqlalchemy.orm.Mapped[User] = Relationship()


class ConversationShare(SQLModel, table=True):
    conversation_share_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_file_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )
    created_datetime: datetime.datetime = date_time_default_to_now()
    owner_id: str = Field(foreign_key="user.user_id")
    label: str
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})

    conversation_permission: str

    is_redeemable: bool = True

    # these relationships are needed to enforce correct INSERT order by SQLModel
    related_owner: sqlalchemy.orm.Mapped[User] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    related_conversation: sqlalchemy.orm.Mapped[Conversation] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class ConversationShareRedemption(SQLModel, table=True):
    conversation_share_redemption_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_share_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversationshare.conversation_share_id",
                name="fk_conversationshareredemption_conversation_share_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )
    conversation_id: uuid.UUID
    conversation_permission: str
    new_participant: bool
    redeemed_by_user_id: str = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "user.user_id",
                name="fk_conversationshareredemption_user_id_user",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )
    created_datetime: datetime.datetime = date_time_default_to_now()

    # these relationships are needed to enforce correct INSERT order by SQLModel
    related_conversation_share: sqlalchemy.orm.Mapped[ConversationShare] = Relationship()
    related_redeemed_by_user: sqlalchemy.orm.Mapped[User] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class AssistantParticipant(SQLModel, table=True):
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_assistantparticipant_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
    )
    assistant_id: uuid.UUID = Field(primary_key=True)
    name: str = ""
    image: str | None = None
    joined_datetime: datetime.datetime = date_time_default_to_now()
    status: str | None = None
    status_updated_datetime: datetime.datetime = date_time_default_to_now()
    active_participant: bool = True
    meta_data: dict[str, Any] = Field(
        sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON, server_default="{}", nullable=False), default={}
    )

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_conversation: Conversation = Relationship()

    def on_update(self, session: Session) -> None:
        # update this participant to match the related assistant, if one exists
        assistant = session.exec(select(Assistant).where(Assistant.assistant_id == self.assistant_id)).one_or_none()
        if assistant is None:
            return

        sqlalchemy.orm.attributes.set_attribute(self, "name", assistant.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", assistant.image)

    def on_insert(self, session: Session) -> None:
        # update this participant to match the related assistant, requiring one to exist
        assistant = session.exec(select(Assistant).where(Assistant.assistant_id == self.assistant_id)).one()
        sqlalchemy.orm.attributes.set_attribute(self, "name", assistant.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", assistant.image)


class UserParticipant(SQLModel, table=True):
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_userparticipant_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
    )
    user_id: str = Field(primary_key=True)
    name: str = ""
    image: str | None = None
    service_user: bool = False
    joined_datetime: datetime.datetime = date_time_default_to_now()
    status: str | None = None
    status_updated_datetime: datetime.datetime = date_time_default_to_now()
    active_participant: bool = True
    meta_data: dict[str, Any] = Field(
        sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON, server_default="{}", nullable=False), default={}
    )
    conversation_permission: str

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_conversation: Conversation = Relationship()

    def on_update(self, session: Session) -> None:
        # update this participant to match the related user, if one exists
        user = session.exec(select(User).where(User.user_id == self.user_id)).one_or_none()
        if user is None:
            return

        sqlalchemy.orm.attributes.set_attribute(self, "name", user.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", user.image)
        sqlalchemy.orm.attributes.set_attribute(self, "service_user", user.service_user)

    def on_insert(self, session: Session) -> None:
        # update this participant to match the related user, requiring one to exist
        user = session.exec(select(User).where(User.user_id == self.user_id)).one()

        sqlalchemy.orm.attributes.set_attribute(self, "name", user.name)
        sqlalchemy.orm.attributes.set_attribute(self, "image", user.image)
        sqlalchemy.orm.attributes.set_attribute(self, "service_user", user.service_user)


class ConversationMessage(SQLModel, table=True):
    sequence: int = Field(default=None, nullable=False, primary_key=True)
    message_id: uuid.UUID = Field(default_factory=uuid.uuid4, unique=True)
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_conversationmessage_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )
    created_datetime: datetime.datetime = date_time_default_to_now()
    sender_participant_id: str
    sender_participant_role: str
    message_type: str = Field(index=True)
    content: str
    content_type: str
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})
    filenames: list[str] = Field(sa_column=sqlalchemy.Column(sqlalchemy.JSON), default=[])

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_conversation: Conversation = Relationship()


class ConversationMessageDebug(SQLModel, table=True):
    message_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversationmessage.message_id",
                name="fk_conversationmessagedebug_message_id_conversationmessage",
                ondelete="CASCADE",
            ),
            nullable=False,
            primary_key=True,
        ),
    )
    data: dict[str, Any] = Field(sa_column=sqlalchemy.Column(sqlalchemy.JSON, nullable=False), default={})

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_messag: ConversationMessage = Relationship()


class File(SQLModel, table=True):
    file_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "conversation.conversation_id",
                name="fk_file_conversation_id_conversation",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )

    filename: str
    current_version: int
    created_datetime: datetime.datetime = date_time_default_to_now(index=True)

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_conversation: Conversation = Relationship()

    __table_args__ = (
        sqlalchemy.UniqueConstraint("conversation_id", "filename", name="uq_file_conversation_id_filename"),
    )


class FileVersion(SQLModel, table=True):
    file_id: uuid.UUID = Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                "file.file_id",
                name="fk_fileversion_file_id_file",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
    )
    version: int = Field(primary_key=True)
    participant_id: str
    participant_role: str
    created_datetime: datetime.datetime = date_time_default_to_now(index=True)
    meta_data: dict[str, Any] = Field(sa_column=sqlalchemy.Column("metadata", sqlalchemy.JSON), default={})
    content_type: str
    file_size: int
    storage_filename: str

    # this relationship is needed to enforce correct INSERT order by SQLModel
    related_file: File = Relationship()


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
SQLModel.metadata.naming_convention = NAMING_CONVENTION


def ensure_async_driver_scheme(url: str) -> str:
    return url.replace("sqlite://", "sqlite+aiosqlite://").replace("postgresql://", "postgresql+asyncpg://")


@sqlalchemy.event.listens_for(sqlalchemy.Pool, "connect")
def set_sqlite_pragma(
    dbapi_connection: sqlalchemy.engine.interfaces.DBAPIConnection,
    _: sqlalchemy.pool.ConnectionPoolEntry,
) -> None:
    if hasattr(sqlalchemy.dialects, "sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


@asynccontextmanager
async def create_engine(settings: DBSettings) -> AsyncIterator[AsyncEngine]:
    # ensure that the database url is using the async driver
    db_url = ensure_async_driver_scheme(settings.url)
    parsed_url = urlparse(db_url)
    is_sqlite = parsed_url.scheme.startswith("sqlite")
    is_postgres = parsed_url.scheme.startswith("postgresql")

    url_for_log = db_url
    if parsed_url.password:
        url_for_log = url_for_log.replace(parsed_url.password, "****")
    logger.info("creating database engine for %s", url_for_log)

    if is_sqlite and "/" in parsed_url.path:
        # create parent directory for sqlite db file as a convenience
        file_path = parsed_url.path[1:]
        pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    kw_args: dict = {"echo": settings.echosql, "future": True}
    if is_postgres:
        kw_args.update({
            "connect_args": {
                "ssl": settings.postgresql_ssl_mode,
            },
            "pool_pre_ping": True,
            "pool_size": settings.postgresql_pool_size,
        })

    engine = create_async_engine(db_url, **kw_args)

    try:
        yield engine
    finally:
        await engine.dispose()


@sqlalchemy.event.listens_for(Session, "before_flush")
def _session_before_flush(session: Session, flush_context, instances) -> None:  # noqa: ANN001, ARG001
    for obj in session.dirty:
        if not hasattr(obj, "on_update"):
            continue
        obj.on_update(session)

    for obj in session.new:
        if not hasattr(obj, "on_insert"):
            continue
        obj.on_insert(session)


async def bootstrap_db(engine: AsyncEngine, settings: DBSettings) -> None:
    logger.info("bootstrapping database")
    await _ensure_schema(engine=engine, settings=settings)
    await _create_default_data(engine=engine)


async def _ensure_schema(engine: AsyncEngine, settings: DBSettings) -> None:
    def execute_ensure_version(connection: sqlalchemy.Connection) -> None:
        from alembic import command, config

        cfg = config.Config(settings.alembic_config_path)
        cfg.attributes["connection"] = connection
        command.ensure_version(cfg)

    async with engine.begin() as conn:
        await conn.run_sync(execute_ensure_version)

    alembic_version_exists = False
    async with engine.begin() as conn:
        row = (await conn.exec_driver_sql("SELECT count(version_num) FROM alembic_version")).one()
        alembic_version_exists = row[0] > 0

    if not alembic_version_exists:
        return await _create_schema(engine=engine, alembic_config_path=settings.alembic_config_path)

    return await _migrate_schema(engine=engine, alembic_config_path=settings.alembic_config_path)


async def _migrate_schema(engine: AsyncEngine, alembic_config_path: str) -> None:
    from alembic import command, config

    logger.info("migrating database schema; alembic_config_path=%s", alembic_config_path)

    def execute_upgrade(connection: sqlalchemy.Connection) -> None:
        logger.info("running alembic upgrade to head")
        cfg = config.Config(alembic_config_path)
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    def execute_check(connection: sqlalchemy.Connection) -> None:
        logger.info("running alembic check")
        cfg = config.Config(alembic_config_path)
        cfg.attributes["connection"] = connection
        command.check(cfg)

    async with engine.begin() as conn:
        await conn.run_sync(execute_upgrade)
        await conn.run_sync(execute_check)

    return None


async def _create_schema(engine: AsyncEngine, alembic_config_path: str) -> None:
    logger.info("creating database schema; alembic_config_path=%s", alembic_config_path)

    def execute_stamp_head(connection: sqlalchemy.Connection) -> None:
        from alembic import command, config

        cfg = config.Config(alembic_config_path)
        cfg.attributes["connection"] = connection
        command.stamp(cfg, "head")

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.run_sync(execute_stamp_head)


async def _create_default_data(engine: AsyncEngine) -> None:
    async with create_session(engine) as session:
        workbench_user = User(
            user_id=service_user_principals.semantic_workbench.user_id,
            name=service_user_principals.semantic_workbench.name,
            service_user=True,
        )
        await insert_if_not_exists(session, workbench_user)
        await session.commit()


@asynccontextmanager
async def create_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_maker() as async_session:
        yield async_session


async def insert_if_not_exists(session: AsyncSession, model: SQLModel) -> bool:
    """
    Inserts the provided record if a row with the same primary key(s) does already exist in the table.
    Returns True if the record was inserted, False if it already existed.
    """

    # the postgresql.insert function is used to generate an INSERT statement with an ON CONFLICT DO NOTHING clause.
    # note that sqlite also supports ON CONFLICT DO NOTHING, so this works with both database types.
    statement = (
        postgresql.insert(model.__class__).values(**model.model_dump(exclude_unset=True)).on_conflict_do_nothing()
    )
    conn = await session.connection()
    result = await conn.execute(statement)
    return result.rowcount > 0


=== File: workbench-service/semantic_workbench_service/event.py ===
from typing import Literal

from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import ConversationEvent


class ConversationEventQueueItem(BaseModel):
    event: ConversationEvent
    event_audience: set[Literal["user", "assistant"]] = set(["user", "assistant"])


=== File: workbench-service/semantic_workbench_service/files.py ===
import hashlib
import logging
import pathlib
from contextlib import contextmanager
from typing import BinaryIO, Iterator

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class StorageSettings(BaseSettings):
    root: str = ".data/files"


class Storage:
    def __init__(self, settings: StorageSettings):
        self.root = pathlib.Path(settings.root)
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("initialized file storage; root: %s", self.root.absolute())

    def _file_path(self, namespace: str, filename: str, mkdir=False) -> pathlib.Path:
        self._ensure_initialized()
        namespace_path = self.root / namespace
        if mkdir:
            namespace_path.mkdir(exist_ok=True)
        filename_hash = hashlib.sha256(filename.encode("utf-8")).hexdigest()
        return namespace_path / filename_hash

    def path_for(self, namespace: str, filename: str) -> pathlib.Path:
        namespace_path = self.root / namespace
        if not filename:
            return namespace_path

        filename_hash = hashlib.sha256(filename.encode("utf-8")).hexdigest()
        return namespace_path / filename_hash

    def file_exists(self, namespace: str, filename: str) -> bool:
        file_path = self._file_path(namespace, filename)
        return file_path.exists()

    def write_file(self, namespace: str, filename: str, content: BinaryIO) -> None:
        file_path = self._file_path(namespace, filename, mkdir=True)
        with open(file_path, "wb") as f:
            for chunk in iter(lambda: content.read(100 * 1_024), b""):
                f.write(chunk)

    def delete_file(self, namespace: str, filename: str) -> None:
        file_path = self._file_path(namespace, filename)
        file_path.unlink(missing_ok=True)

    @contextmanager
    def read_file(self, namespace: str, filename: str) -> Iterator[BinaryIO]:
        file_path = self._file_path(namespace, filename)
        with open(file_path, "rb") as f:
            yield f


=== File: workbench-service/semantic_workbench_service/logging_config.py ===
import logging
import re
from time import perf_counter
from typing import Awaitable, Callable

import asgi_correlation_id
from fastapi import Request, Response
from pydantic_settings import BaseSettings
from pythonjsonlogger import json as jsonlogger
from rich.logging import RichHandler


class LoggingSettings(BaseSettings):
    json_format: bool = False
    log_level: str = "INFO"


class JSONHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.setFormatter(
            jsonlogger.JsonFormatter(
                "%(filename)s %(name)s %(lineno)s %(levelname)s %(correlation_id)s %(message)s %(taskName)s"
                " %(process)d",
                timestamp=True,
            )
        )


class DebugLevelForNoisyLogFilter(logging.Filter):
    """Lowers logs for specific routes to DEBUG level."""

    def __init__(self, log_level: int, *names_and_patterns: tuple[str, re.Pattern]):
        self._log_level = log_level
        self._names_and_patterns = names_and_patterns

    def filter(self, record: logging.LogRecord) -> bool:
        if not any(
            record.name == name and pattern.search(record.getMessage()) for name, pattern in self._names_and_patterns
        ):
            return True

        record.levelname = logging.getLevelName(logging.DEBUG)
        record.levelno = logging.DEBUG

        return self._log_level <= record.levelno


def config(settings: LoggingSettings):
    log_level = logging.getLevelNamesMapping()[settings.log_level.upper()]

    handler = RichHandler(rich_tracebacks=True)
    if settings.json_format:
        handler = JSONHandler()

    handler.addFilter(
        DebugLevelForNoisyLogFilter(
            log_level,
            # noisy assistant-service pings
            ("uvicorn.access", re.compile(r"PUT /assistant-service-registrations/[^\s]+ HTTP")),
        )
    )
    handler.addFilter(asgi_correlation_id.CorrelationIdFilter(uuid_length=8, default_value="-"))

    logging.basicConfig(
        level=log_level,
        format="%(name)35s [%(correlation_id)s] %(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )


def log_request_middleware(
    logger: logging.Logger | None = None,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    access_logger = logger or logging.getLogger("access_log")

    async def middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        This middleware will log all requests and their processing time.
        E.g. log:
        0.0.0.0:1234 - "GET /ping HTTP/1.1" 200 OK 1.00ms 0b
        """
        url = f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path
        start_time = perf_counter()
        response = await call_next(request)
        process_time = (perf_counter() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        host = getattr(getattr(request, "client", None), "host", None)
        port = getattr(getattr(request, "client", None), "port", None)
        http_version = f"HTTP/{request.scope.get('http_version', '1.1')}"
        content_length = response.headers.get("content-length", 0)
        access_logger.info(
            f'{host}:{port} - "{request.method} {url} {http_version}" {response.status_code} {formatted_process_time}ms {content_length}b',
        )
        return response

    return middleware


=== File: workbench-service/semantic_workbench_service/middleware.py ===
import logging
import secrets
import time
from functools import lru_cache
from typing import Any, Awaitable, Callable

import httpx
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, jwt
from semantic_workbench_api_model import workbench_service_client
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from . import auth, settings

logger = logging.getLogger(__name__)


_unauthorized_assistant_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
)


async def _assistant_service_principal_from_request(
    request: Request,
    api_key_source: Callable[[str], Awaitable[str | None]],
) -> auth.AssistantServicePrincipal | None:
    assistant_service_params = workbench_service_client.AssistantServiceRequestHeaders.from_headers(request.headers)
    if not assistant_service_params.assistant_service_id:
        return None

    assistant_service_id = assistant_service_params.assistant_service_id
    api_key = assistant_service_params.api_key

    assistant_params = workbench_service_client.AssistantRequestHeaders.from_headers(request.headers)
    assistant_id = assistant_params.assistant_id

    expected_api_key = await api_key_source(assistant_service_id)
    if expected_api_key is None:
        logger.info(
            "assistant service authentication failed; assistant_service_id: %s, error: api key not found in store",
            assistant_service_id,
        )
        raise _unauthorized_assistant_exception

    current_password_bytes = api_key.encode("utf8")
    correct_password_bytes = expected_api_key.encode("utf8")
    is_correct_password = secrets.compare_digest(current_password_bytes, correct_password_bytes)

    if not is_correct_password:
        logger.info(
            "assistant service authentication failed; assistant_service_id: %s, error: api key mismatch",
            assistant_service_id,
        )
        raise _unauthorized_assistant_exception

    if assistant_id:
        return auth.AssistantPrincipal(assistant_service_id=assistant_service_id, assistant_id=assistant_id)

    return auth.AssistantServicePrincipal(assistant_service_id=assistant_service_id)


async def _user_principal_from_request(request: Request) -> auth.UserPrincipal | None:
    token = await OAuth2PasswordBearer(tokenUrl="token", auto_error=False)(request)
    if token is None:
        return None

    allowed_jwt_algorithms = settings.auth.allowed_jwt_algorithms

    try:
        algorithm: str = jwt.get_unverified_header(token).get("alg") or ""

        match algorithm:
            case "RS256":
                keys = _get_rs256_jwks()
            case _:
                keys = ""

        decoded = jwt.decode(
            token,
            algorithms=allowed_jwt_algorithms,
            key=keys,
            options={"verify_signature": False, "verify_aud": False},
        )
        app_id: str = decoded.get("appid", "")
        tid: str = decoded.get("tid", "")
        oid: str = decoded.get("oid", "")
        name: str = decoded.get("name", "")
        user_id = f"{tid}.{oid}"

    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token")

    except Exception:
        logger.exception("error decoding token", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if algorithm not in allowed_jwt_algorithms:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token algorithm")

    if app_id != settings.auth.allowed_app_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid app")

    return auth.UserPrincipal(user_id=user_id, name=name)


async def principal_from_request(
    request: Request,
    api_key_source: Callable[[str], Awaitable[str | None]],
) -> auth.Principal | None:
    assistant_principal = await _assistant_service_principal_from_request(request, api_key_source=api_key_source)
    if assistant_principal is not None:
        return assistant_principal

    user_principal = await _user_principal_from_request(request)
    if user_principal is not None:
        return user_principal

    return None


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        api_key_source: Callable[[str], Awaitable[str | None]],
        exclude_methods: set[str] = set(),
        exclude_paths: set[str] = set(),
    ) -> None:
        super().__init__(app)
        self.exclude_methods = exclude_methods
        self.exclude_routes = exclude_paths
        self.api_key_source = api_key_source

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in self.exclude_methods:
            return await call_next(request)

        if request.url.path in self.exclude_routes:
            return await call_next(request)

        try:
            principal = await principal_from_request(request, api_key_source=self.api_key_source)

            if principal is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        except HTTPException as exc:
            # if the authorization header is invalid, return the error response
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception:
            logger.exception("error validating authorization header")
            # return a generic error response
            return Response(status_code=500)

        auth.authenticated_principal.set(principal)
        return await call_next(request)


def ttl_lru_cache(seconds_to_live: int, maxsize: int = 128):
    """
    Time aware lru caching
    """

    def wrapper(func):
        @lru_cache(maxsize)
        def inner(__ttl, *args, **kwargs):
            # Note that __ttl is not passed down to func,
            # as it's only used to trigger cache miss after some time
            return func(*args, **kwargs)

        return lambda *args, **kwargs: inner(time.time() // seconds_to_live, *args, **kwargs)

    return wrapper


@ttl_lru_cache(seconds_to_live=60 * 10)
def _get_rs256_jwks() -> dict[str, Any]:
    response = httpx.Client().get("https://login.microsoftonline.com/common/discovery/v2.0/keys")
    return response.json()


=== File: workbench-service/semantic_workbench_service/query.py ===
from typing import Any, TypeVar

from semantic_workbench_api_model.workbench_model import MessageType
from sqlalchemy import Function
from sqlmodel import and_, col, func, literal, or_, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from . import auth, db, settings


def json_extract_path(expression, *paths: str) -> Function[Any]:
    if settings.db.url.startswith("sqlite"):
        return func.json_extract(expression, f"$.{'.'.join(paths)}")
    return func.json_extract_path(expression, *paths)


def select_assistants_for(
    user_principal: auth.UserPrincipal, include_assistants_from_conversations: bool = False
) -> SelectOfScalar[db.Assistant]:
    return select(db.Assistant).where(
        or_(
            db.Assistant.owner_id == user_principal.user_id,
            and_(
                include_assistants_from_conversations is True,
                col(db.Assistant.assistant_id).in_(
                    select(db.AssistantParticipant.assistant_id)
                    .join(
                        db.Conversation,
                        and_(
                            col(db.Conversation.conversation_id) == col(db.AssistantParticipant.conversation_id),
                            col(db.AssistantParticipant.active_participant).is_(True),
                        ),
                    )
                    .join(
                        db.UserParticipant,
                        and_(
                            col(db.UserParticipant.conversation_id) == col(db.Conversation.conversation_id),
                            col(db.UserParticipant.user_id) == user_principal.user_id,
                            col(db.UserParticipant.active_participant).is_(True),
                        ),
                    )
                    .distinct()
                ),
            ),
        )
    )


SelectT = TypeVar("SelectT", SelectOfScalar, Select)


def _select_conversations_for(
    principal: auth.ActorPrincipal,
    select_query: SelectT,
    include_all_owned: bool = False,
    include_observer: bool = False,
) -> SelectT:
    match principal:
        case auth.UserPrincipal():
            join_clause = and_(
                db.UserParticipant.conversation_id == db.Conversation.conversation_id,
                db.UserParticipant.user_id == principal.user_id,
            )
            if not include_observer:
                join_clause = and_(join_clause, db.UserParticipant.conversation_permission != "read")

            query = select_query.join_from(db.Conversation, db.UserParticipant, onclause=join_clause)

            where_clause = col(db.UserParticipant.active_participant).is_(True)

            if include_all_owned:
                where_clause = or_(where_clause, db.Conversation.owner_id == principal.user_id)

            query = query.where(where_clause)

            return query

        case auth.AssistantPrincipal():
            query = select_query.join(
                db.AssistantParticipant,
                and_(
                    db.AssistantParticipant.conversation_id == db.Conversation.conversation_id,
                    db.AssistantParticipant.assistant_id == principal.assistant_id,
                    col(db.AssistantParticipant.active_participant).is_(True),
                ),
            )

            return query


def select_conversations_for(
    principal: auth.ActorPrincipal,
    include_all_owned: bool = False,
    include_observer: bool = False,
) -> SelectOfScalar[db.Conversation]:
    return _select_conversations_for(
        principal=principal,
        select_query=select(db.Conversation),
        include_all_owned=include_all_owned,
        include_observer=include_observer,
    )


def select_conversation_projections_for(
    principal: auth.ActorPrincipal,
    latest_message_types: set[MessageType],
    include_all_owned: bool = False,
    include_observer: bool = False,
) -> Select[tuple[db.Conversation, db.ConversationMessage | None, bool, str]]:
    match principal:
        case auth.UserPrincipal():
            select_query = select(
                db.Conversation,
                db.ConversationMessage,
                col(db.ConversationMessageDebug.message_id).is_not(None).label("has_debug"),
                db.UserParticipant.conversation_permission,
            )

        case auth.AssistantPrincipal():
            select_query = select(
                db.Conversation,
                db.ConversationMessage,
                col(db.ConversationMessageDebug.message_id).is_not(None).label("has_debug"),
                literal("read_write").label("conversation_permission"),
            )

    query = _select_conversations_for(
        principal=principal,
        include_all_owned=include_all_owned,
        include_observer=include_observer,
        select_query=select_query,
    )

    latest_message_subquery = (
        select(
            db.ConversationMessage.conversation_id,
            func.max(db.ConversationMessage.sequence).label("latest_message_sequence"),
        )
        .where(col(db.ConversationMessage.message_type).in_(latest_message_types))
        .group_by(col(db.ConversationMessage.conversation_id))
        .subquery()
    )

    return (
        query.join_from(
            db.Conversation,
            latest_message_subquery,
            onclause=col(db.Conversation.conversation_id) == col(latest_message_subquery.c.conversation_id),
            isouter=True,
        )
        .join_from(
            db.Conversation,
            db.ConversationMessage,
            onclause=and_(
                col(db.Conversation.conversation_id) == col(db.ConversationMessage.conversation_id),
                col(db.ConversationMessage.sequence) == col(latest_message_subquery.c.latest_message_sequence),
            ),
            isouter=True,
        )
        .join_from(
            db.ConversationMessage,
            db.ConversationMessageDebug,
            isouter=True,
        )
    )


def _select_conversation_messages_for(
    select_query: SelectT,
    principal: auth.ActorPrincipal,
) -> SelectT:
    match principal:
        case auth.UserPrincipal():
            return (
                select_query.join(db.Conversation)
                .join(db.UserParticipant)
                .where(db.UserParticipant.user_id == principal.user_id)
            )

        case auth.AssistantPrincipal():
            return (
                select_query.join(db.Conversation)
                .join(db.AssistantParticipant)
                .where(db.AssistantParticipant.assistant_id == principal.assistant_id)
            )


def select_conversation_messages_for(principal: auth.ActorPrincipal) -> SelectOfScalar[db.ConversationMessage]:
    return _select_conversation_messages_for(select(db.ConversationMessage), principal)


def select_conversation_message_projections_for(
    principal: auth.ActorPrincipal,
) -> Select[tuple[db.ConversationMessage, bool]]:
    return _select_conversation_messages_for(
        select(db.ConversationMessage, col(db.ConversationMessageDebug.message_id).is_not(None)).join(
            db.ConversationMessageDebug, isouter=True
        ),
        principal,
    )


def select_conversation_message_debugs_for(
    principal: auth.ActorPrincipal,
) -> SelectOfScalar[db.ConversationMessageDebug]:
    match principal:
        case auth.UserPrincipal():
            return (
                select(db.ConversationMessageDebug)
                .join(db.ConversationMessage)
                .join(db.Conversation)
                .join(db.UserParticipant)
                .where(db.UserParticipant.user_id == principal.user_id)
            )

        case auth.AssistantPrincipal():
            return (
                select(db.ConversationMessageDebug)
                .join(db.ConversationMessage)
                .join(db.Conversation)
                .join(db.AssistantParticipant)
                .where(db.AssistantParticipant.assistant_id == principal.assistant_id)
            )


=== File: workbench-service/semantic_workbench_service/service.py ===
import asyncio
import contextlib
import datetime
import json
import logging
import urllib.parse
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import (
    Annotated,
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    NoReturn,
)

import asgi_correlation_id
import starlette.background
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from semantic_workbench_api_model.assistant_model import (
    ConfigPutRequestModel,
    ConfigResponseModel,
    ServiceInfoModel,
    StateDescriptionListResponseModel,
    StatePutRequestModel,
    StateResponseModel,
)
from semantic_workbench_api_model.workbench_model import (
    Assistant,
    AssistantList,
    AssistantServiceInfoList,
    AssistantServiceRegistration,
    AssistantServiceRegistrationList,
    AssistantStateEvent,
    Conversation,
    ConversationEvent,
    ConversationEventType,
    ConversationImportResult,
    ConversationList,
    ConversationMessage,
    ConversationMessageDebug,
    ConversationMessageList,
    ConversationParticipant,
    ConversationParticipantList,
    ConversationShare,
    ConversationShareList,
    ConversationShareRedemption,
    ConversationShareRedemptionList,
    FileList,
    FileVersions,
    MessageType,
    NewAssistant,
    NewAssistantServiceRegistration,
    NewConversation,
    NewConversationMessage,
    NewConversationShare,
    ParticipantRole,
    UpdateAssistant,
    UpdateAssistantServiceRegistration,
    UpdateAssistantServiceRegistrationUrl,
    UpdateConversation,
    UpdateFile,
    UpdateParticipant,
    UpdateUser,
    User,
    UserList,
)
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sse_starlette import EventSourceResponse, ServerSentEvent

from semantic_workbench_service import azure_speech
from semantic_workbench_service.logging_config import log_request_middleware

from . import assistant_api_key, auth, controller, db, files, middleware, settings
from .event import ConversationEventQueueItem

logger = logging.getLogger(__name__)


def init(
    app: FastAPI,
    register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
) -> None:
    api_key_store = assistant_api_key.get_store()
    stop_signal: asyncio.Event = asyncio.Event()

    conversation_sse_queues_lock = asyncio.Lock()
    conversation_sse_queues: dict[uuid.UUID, set[asyncio.Queue[ConversationEvent]]] = defaultdict(set)

    user_sse_queues_lock = asyncio.Lock()
    user_sse_queues: dict[str, set[asyncio.Queue[ConversationEvent]]] = defaultdict(set)

    assistant_event_queues: dict[uuid.UUID, asyncio.Queue[ConversationEvent]] = {}

    background_tasks: set[asyncio.Task] = set()

    def _controller_get_session() -> AsyncContextManager[AsyncSession]:
        return db.create_session(app.state.db_engine)

    async def _forward_events_to_assistant(
        assistant_id: uuid.UUID, event_queue: asyncio.Queue[ConversationEvent]
    ) -> NoReturn:
        while True:
            try:
                event = await event_queue.get()
                event_queue.task_done()

                asgi_correlation_id.correlation_id.set(event.correlation_id)

                start_time = datetime.datetime.now(datetime.UTC)

                await assistant_controller.forward_event_to_assistant(assistant_id=assistant_id, event=event)

                end_time = datetime.datetime.now(datetime.UTC)
                logger.debug(
                    "forwarded event to assistant; assistant_id: %s, conversation_id: %s, event_id: %s,"
                    " duration: %s, time since event: %s",
                    assistant_id,
                    event.conversation_id,
                    event.id,
                    end_time - start_time,
                    end_time - event.timestamp,
                )

            except Exception:
                logger.exception("exception in _forward_events_to_assistant")

    async def _notify_event(queue_item: ConversationEventQueueItem) -> None:
        if stop_signal.is_set():
            logger.warning(
                "ignoring event due to stop signal; conversation_id: %s, event: %s, id: %s",
                queue_item.event.conversation_id,
                queue_item.event.event,
                queue_item.event.id,
            )
            return

        logger.debug(
            "received event to notify; conversation_id: %s, event: %s, event_id: %s, audience: %s",
            queue_item.event.conversation_id,
            queue_item.event.event,
            queue_item.event.id,
            queue_item.event_audience,
        )

        if "user" in queue_item.event_audience:
            enqueued_count = 0
            async with conversation_sse_queues_lock:
                for queue in conversation_sse_queues.get(queue_item.event.conversation_id, {}):
                    enqueued_count += 1
                    await queue.put(queue_item.event)

            logger.debug(
                "enqueued event for SSE; count: %d, conversation_id: %s, event: %s, event_id: %s",
                enqueued_count,
                queue_item.event.conversation_id,
                queue_item.event.event,
                queue_item.event.id,
            )

            if queue_item.event.event in [
                ConversationEventType.message_created,
                ConversationEventType.message_deleted,
                ConversationEventType.conversation_updated,
                ConversationEventType.participant_created,
                ConversationEventType.participant_updated,
            ]:
                task = asyncio.create_task(_notify_user_event(queue_item.event), name="notify_user_event")
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

        if "assistant" in queue_item.event_audience:
            async with _controller_get_session() as session:
                assistant_ids = (
                    await session.exec(
                        select(db.Assistant.assistant_id)
                        .join(
                            db.AssistantParticipant,
                            col(db.Assistant.assistant_id) == col(db.AssistantParticipant.assistant_id),
                        )
                        .join(db.AssistantServiceRegistration)
                        .where(col(db.AssistantServiceRegistration.assistant_service_online).is_(True))
                        .where(col(db.AssistantParticipant.active_participant).is_(True))
                        .where(db.AssistantParticipant.conversation_id == queue_item.event.conversation_id)
                    )
                ).all()

            for assistant_id in assistant_ids:
                if assistant_id not in assistant_event_queues:
                    queue = asyncio.Queue()
                    assistant_event_queues[assistant_id] = queue
                    task = asyncio.create_task(
                        _forward_events_to_assistant(assistant_id, queue),
                        name=f"forward_events_to_{assistant_id}",
                    )
                    background_tasks.add(task)

                await assistant_event_queues[assistant_id].put(queue_item.event)
                logger.debug(
                    "enqueued event for assistant; conversation_id: %s, event: %s, event_id: %s, assistant_id: %s",
                    queue_item.event.conversation_id,
                    queue_item.event.event,
                    queue_item.event.id,
                    assistant_id,
                )

    async def _notify_user_event(event: ConversationEvent) -> None:
        listening_user_ids = set(user_sse_queues.keys())
        async with _controller_get_session() as session:
            active_user_participants = (
                await session.exec(
                    select(db.UserParticipant.user_id).where(
                        col(db.UserParticipant.active_participant).is_(True),
                        db.UserParticipant.conversation_id == event.conversation_id,
                        col(db.UserParticipant.user_id).in_(listening_user_ids),
                    )
                )
            ).all()

        if not active_user_participants:
            return

        async with user_sse_queues_lock:
            for user_id in active_user_participants:
                for queue in user_sse_queues.get(user_id, {}):
                    await queue.put(event)
                    logger.debug(
                        "enqueued event for user SSE; user_id: %s, conversation_id: %s", user_id, event.conversation_id
                    )

    assistant_client_pool = controller.AssistantServiceClientPool(api_key_store=api_key_store)

    assistant_service_registration_controller = controller.AssistantServiceRegistrationController(
        get_session=_controller_get_session,
        notify_event=_notify_event,
        api_key_store=api_key_store,
        client_pool=assistant_client_pool,
    )

    app.add_middleware(
        middleware.AuthMiddleware,
        exclude_methods={"OPTIONS"},
        exclude_paths=set(settings.service.anonymous_paths),
        api_key_source=assistant_service_registration_controller.api_key_source,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)

    app.middleware("http")(log_request_middleware())

    user_controller = controller.UserController(get_session=_controller_get_session)
    assistant_controller = controller.AssistantController(
        get_session=_controller_get_session,
        notify_event=_notify_event,
        client_pool=assistant_client_pool,
        file_storage=files.Storage(settings.storage),
    )
    conversation_controller = controller.ConversationController(
        get_session=_controller_get_session,
        notify_event=_notify_event,
        assistant_controller=assistant_controller,
    )
    conversation_share_controller = controller.ConversationShareController(
        get_session=_controller_get_session,
        notify_event=_notify_event,
    )

    file_controller = controller.FileController(
        get_session=_controller_get_session,
        notify_event=_notify_event,
        file_storage=files.Storage(settings.storage),
    )

    @asynccontextmanager
    async def _lifespan() -> AsyncIterator[None]:
        async with db.create_engine(settings.db) as engine:
            await db.bootstrap_db(engine, settings=settings.db)

            app.state.db_engine = engine

            background_tasks.add(
                asyncio.create_task(
                    _update_assistant_service_online_status(), name="update_assistant_service_online_status"
                ),
            )

            try:
                yield

            finally:
                stop_signal.set()

                for task in background_tasks:
                    task.cancel()

                with contextlib.suppress(asyncio.CancelledError):
                    await asyncio.gather(*background_tasks, return_exceptions=True)

    register_lifespan_handler(_lifespan)

    async def _update_assistant_service_online_status() -> NoReturn:
        while True:
            try:
                await asyncio.sleep(settings.service.assistant_service_online_check_interval_seconds)
                await assistant_service_registration_controller.check_assistant_service_online_expired()

            except Exception:
                logger.exception("exception in _update_assistant_service_online_status")

    @app.get("/")
    async def root() -> Response:
        return Response(status_code=status.HTTP_200_OK, content="")

    @app.get("/users")
    async def list_users(
        user_ids: list[str] = Query(alias="id"),
    ) -> UserList:
        return await user_controller.get_users(user_ids=user_ids)

    @app.get("/users/me")
    async def get_user_me(
        user_principal: auth.DependsUserPrincipal,
    ) -> User:
        return await user_controller.get_user_me(user_principal=user_principal)

    @app.put("/users/me")
    async def update_user_me(
        user_principal: auth.DependsUserPrincipal,
        update_user: UpdateUser,
    ) -> User:
        return await user_controller.update_user(
            user_principal=user_principal, user_id=user_principal.user_id, update_user=update_user
        )

    @app.post("/assistant-service-registrations")
    async def create_assistant_service_registration(
        user_principal: auth.DependsUserPrincipal,
        new_assistant_service: NewAssistantServiceRegistration,
    ) -> AssistantServiceRegistration:
        return await assistant_service_registration_controller.create_registration(
            user_principal=user_principal, new_assistant_service=new_assistant_service
        )

    @app.put("/assistant-service-registrations/{assistant_service_id:path}")
    async def update_assistant_service_registration_url(
        principal: auth.DependsAssistantServicePrincipal,
        assistant_service_id: str,
        update_assistant_service: UpdateAssistantServiceRegistrationUrl,
        background_tasks: BackgroundTasks,
    ) -> AssistantServiceRegistration:
        registration, task_args = await assistant_service_registration_controller.update_assistant_service_url(
            assistant_service_principal=principal,
            assistant_service_id=assistant_service_id,
            update_assistant_service_url=update_assistant_service,
        )
        if task_args:
            background_tasks.add_task(*task_args)
        return registration

    @app.patch("/assistant-service-registrations/{assistant_service_id:path}")
    async def update_assistant_service_registration(
        principal: auth.DependsUserPrincipal,
        assistant_service_id: str,
        update_assistant_service: UpdateAssistantServiceRegistration,
    ) -> AssistantServiceRegistration:
        return await assistant_service_registration_controller.update_registration(
            user_principal=principal,
            assistant_service_id=assistant_service_id,
            update_assistant_service=update_assistant_service,
        )

    @app.post("/assistant-service-registrations/{assistant_service_id:path}/api-key")
    async def reset_assistant_service_registration_api_key(
        user_principal: auth.DependsUserPrincipal,
        assistant_service_id: str,
    ) -> AssistantServiceRegistration:
        return await assistant_service_registration_controller.reset_api_key(
            user_principal=user_principal, assistant_service_id=assistant_service_id
        )

    @app.get("/assistant-service-registrations")
    async def list_assistant_service_registrations(
        user_principal: auth.DependsUserPrincipal,
        user_ids: Annotated[list[str], Query(alias="user_id")] = [],
        assistant_service_online: Annotated[bool | None, Query(alias="assistant_service_online")] = None,
    ) -> AssistantServiceRegistrationList:
        user_id_set = set([user_principal.user_id if user_id == "me" else user_id for user_id in user_ids])
        return await assistant_service_registration_controller.get_registrations(
            user_ids=user_id_set, assistant_service_online=assistant_service_online
        )

    @app.get("/assistant-service-registrations/{assistant_service_id:path}")
    async def get_assistant_service_registration(
        user_principal: auth.DependsUserPrincipal, assistant_service_id: str
    ) -> AssistantServiceRegistration:
        return await assistant_service_registration_controller.get_registration(
            assistant_service_id=assistant_service_id
        )

    @app.delete(
        "/assistant-service-registrations/{assistant_service_id:path}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_assistant_service(
        user_principal: auth.DependsUserPrincipal,
        assistant_service_id: str,
    ) -> None:
        return await assistant_service_registration_controller.delete_registration(
            user_principal=user_principal, assistant_service_id=assistant_service_id
        )

    @app.get("/assistant-services/{assistant_service_id:path}/info")
    @app.get("/assistant-services/{assistant_service_id:path}")
    async def get_assistant_service_info(
        user_principal: auth.DependsUserPrincipal, assistant_service_id: str
    ) -> ServiceInfoModel:
        return await assistant_service_registration_controller.get_service_info(
            assistant_service_id=assistant_service_id
        )

    @app.get("/assistant-services")
    async def list_assistant_service_infos(
        principal: auth.DependsPrincipal,
        user_ids: Annotated[list[str], Query(alias="user_id")] = [],
    ) -> AssistantServiceInfoList:
        match principal:
            case auth.UserPrincipal():
                user_id_set = set([principal.user_id if user_id == "me" else user_id for user_id in user_ids])

            case auth.AssistantServicePrincipal():
                user_id_set = set(user_ids)

        return await assistant_service_registration_controller.get_service_infos(user_ids=user_id_set)

    @app.get("/assistants")
    async def list_assistants(
        user_principal: auth.DependsUserPrincipal, conversation_id: uuid.UUID | None = None
    ) -> AssistantList:
        return await assistant_controller.get_assistants(user_principal=user_principal, conversation_id=conversation_id)

    @app.get("/assistants/{assistant_id}")
    async def get_assistant(user_principal: auth.DependsUserPrincipal, assistant_id: uuid.UUID) -> Assistant:
        return await assistant_controller.get_assistant(user_principal=user_principal, assistant_id=assistant_id)

    @app.post("/assistants", status_code=status.HTTP_201_CREATED)
    async def create_assistant(
        new_assistant: NewAssistant,
        user_principal: auth.DependsUserPrincipal,
    ) -> Assistant:
        return await assistant_controller.create_assistant(user_principal=user_principal, new_assistant=new_assistant)

    @app.patch("/assistants/{assistant_id}")
    async def update_assistant(
        assistant_id: uuid.UUID,
        update_assistant: UpdateAssistant,
        user_principal: auth.DependsUserPrincipal,
    ) -> Assistant:
        return await assistant_controller.update_assistant(
            user_principal=user_principal, assistant_id=assistant_id, update_assistant=update_assistant
        )

    @app.get(
        "/assistants/{assistant_id}/export", description="Export an assistant's configuration and conversation data."
    )
    async def export_assistant(
        user_principal: auth.DependsUserPrincipal,
        assistant_id: uuid.UUID,
    ) -> FileResponse:
        result = await assistant_controller.export_assistant(user_principal=user_principal, assistant_id=assistant_id)

        return FileResponse(
            path=result.file_path,
            media_type=result.content_type,
            filename=result.filename,
            background=starlette.background.BackgroundTask(result.cleanup),
        )

    @app.get(
        "/conversations/export",
        description="Export  one or more conversations and the assistants that participate in them.",
    )
    async def export_conversations(
        user_principal: auth.DependsUserPrincipal,
        conversation_ids: list[uuid.UUID] = Query(alias="id"),
    ) -> FileResponse:
        result = await assistant_controller.export_conversations(
            user_principal=user_principal, conversation_ids=set(conversation_ids)
        )

        return FileResponse(
            path=result.file_path,
            media_type=result.content_type,
            filename=result.filename,
            background=starlette.background.BackgroundTask(result.cleanup),
        )

    @app.post("/conversations/import")
    async def import_conversations(
        from_export: Annotated[UploadFile, File(alias="from_export")],
        user_principal: auth.DependsUserPrincipal,
    ) -> ConversationImportResult:
        return await assistant_controller.import_conversations(
            user_principal=user_principal, from_export=from_export.file
        )

    @app.get("/assistants/{assistant_id}/config")
    async def get_assistant_config(
        user_principal: auth.DependsUserPrincipal,
        assistant_id: uuid.UUID,
    ) -> ConfigResponseModel:
        return await assistant_controller.get_assistant_config(user_principal=user_principal, assistant_id=assistant_id)

    @app.put("/assistants/{assistant_id}/config")
    async def update_assistant_config(
        user_principal: auth.DependsUserPrincipal,
        assistant_id: uuid.UUID,
        updated_config: ConfigPutRequestModel,
    ) -> ConfigResponseModel:
        return await assistant_controller.update_assistant_config(
            user_principal=user_principal,
            assistant_id=assistant_id,
            updated_config=updated_config,
        )

    @app.get("/assistants/{assistant_id}/conversations/{conversation_id}/states")
    async def get_assistant_conversation_state_descriptions(
        user_principal: auth.DependsUserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> StateDescriptionListResponseModel:
        return await assistant_controller.get_assistant_conversation_state_descriptions(
            user_principal=user_principal,
            assistant_id=assistant_id,
            conversation_id=conversation_id,
        )

    @app.get("/assistants/{assistant_id}/conversations/{conversation_id}/states/{state_id}")
    async def get_assistant_conversation_state(
        user_principal: auth.DependsUserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        state_id: str,
    ) -> StateResponseModel:
        return await assistant_controller.get_assistant_conversation_state(
            user_principal=user_principal,
            assistant_id=assistant_id,
            conversation_id=conversation_id,
            state_id=state_id,
        )

    @app.put("/assistants/{assistant_id}/conversations/{conversation_id}/states/{state_id}")
    async def update_assistant_conversation_state(
        user_principal: auth.DependsUserPrincipal,
        assistant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        state_id: str,
        updated_state: StatePutRequestModel,
    ) -> StateResponseModel:
        return await assistant_controller.update_assistant_conversation_state(
            user_principal=user_principal,
            assistant_id=assistant_id,
            conversation_id=conversation_id,
            state_id=state_id,
            updated_state=updated_state,
        )

    @app.post("/assistants/{assistant_id}/states/events", status_code=status.HTTP_204_NO_CONTENT)
    async def post_assistant_state_event(
        assistant_id: uuid.UUID,
        state_event: AssistantStateEvent,
        assistant_principal: auth.DependsAssistantPrincipal,
        conversation_id: Annotated[uuid.UUID | None, Query()] = None,
    ) -> None:
        await assistant_controller.post_assistant_state_event(
            assistant_id=assistant_id,
            state_event=state_event,
            assistant_principal=assistant_principal,
            conversation_ids=[conversation_id] if conversation_id else [],
        )

    @app.delete(
        "/assistants/{assistant_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_assistant(
        user_principal: auth.DependsUserPrincipal,
        assistant_id: uuid.UUID,
    ) -> None:
        await assistant_controller.delete_assistant(
            user_principal=user_principal,
            assistant_id=assistant_id,
        )

    @app.get("/assistants/{assistant_id}/conversations")
    async def get_assistant_conversations(
        assistant_id: uuid.UUID,
        user_principal: auth.DependsUserPrincipal,
        latest_message_types: Annotated[list[MessageType], Query(alias="latest_message_type")] = [MessageType.chat],
    ) -> ConversationList:
        return await conversation_controller.get_assistant_conversations(
            user_principal=user_principal,
            assistant_id=assistant_id,
            latest_message_types=set(latest_message_types),
        )

    @app.get("/conversations/{conversation_id}/events")
    async def conversation_server_sent_events(
        conversation_id: uuid.UUID, request: Request, principal: auth.DependsActorPrincipal
    ) -> EventSourceResponse:
        # ensure the principal has access to the conversation
        await conversation_controller.get_conversation(
            conversation_id=conversation_id,
            principal=principal,
            latest_message_types=set(),
        )

        principal_id_type = "assistant_id" if isinstance(principal, auth.AssistantPrincipal) else "user_id"
        principal_id = principal.assistant_id if isinstance(principal, auth.AssistantPrincipal) else principal.user_id

        logger.debug(
            "client connected to sse; %s: %s, conversation_id: %s",
            principal_id_type,
            principal_id,
            conversation_id,
        )
        event_queue = asyncio.Queue[ConversationEvent]()

        async with conversation_sse_queues_lock:
            queues = conversation_sse_queues[conversation_id]
            queues.add(event_queue)

        async def event_generator() -> AsyncIterator[ServerSentEvent]:
            try:
                while True:
                    if stop_signal.is_set():
                        logger.debug("sse stopping due to signal; conversation_id: %s", conversation_id)
                        break

                    try:
                        if await request.is_disconnected():
                            logger.debug("client disconnected from sse; conversation_id: %s", conversation_id)
                            break
                    except Exception:
                        logger.exception(
                            "error checking if client disconnected from sse; conversation_id: %s", conversation_id
                        )
                        break

                    try:
                        try:
                            async with asyncio.timeout(1):
                                conversation_event = await event_queue.get()
                        except asyncio.TimeoutError:
                            continue

                        server_sent_event = ServerSentEvent(
                            id=conversation_event.id,
                            event=conversation_event.event.value,
                            data=conversation_event.model_dump_json(include={"timestamp", "data"}),
                            retry=1000,
                        )
                        yield server_sent_event
                        logger.debug(
                            "sent event to sse client; %s: %s, conversation_id: %s, event: %s, id: %s, time since"
                            " event: %s",
                            principal_id_type,
                            principal_id,
                            conversation_id,
                            conversation_event.event,
                            conversation_event.id,
                            datetime.datetime.now(datetime.UTC) - conversation_event.timestamp,
                        )

                    except Exception:
                        logger.exception("error sending event to sse client; conversation_id: %s", conversation_id)

            finally:
                queues.discard(event_queue)
                if len(queues) == 0:
                    async with conversation_sse_queues_lock:
                        if len(queues) == 0:
                            conversation_sse_queues.pop(conversation_id, None)

        return EventSourceResponse(event_generator(), sep="\n")

    @app.get("/events")
    async def user_server_sent_events(
        request: Request, user_principal: auth.DependsUserPrincipal
    ) -> EventSourceResponse:
        logger.debug("client connected to user events sse; user_id: %s", user_principal.user_id)

        event_queue = asyncio.Queue[ConversationEvent]()

        async with user_sse_queues_lock:
            queues = user_sse_queues[user_principal.user_id]
            queues.add(event_queue)

        async def event_generator() -> AsyncIterator[ServerSentEvent]:
            try:
                while True:
                    if stop_signal.is_set():
                        logger.debug("sse stopping due to signal; user_id: %s", user_principal.user_id)
                        break

                    try:
                        if await request.is_disconnected():
                            logger.debug("client disconnected from sse; user_id: %s", user_principal.user_id)
                            break
                    except Exception:
                        logger.exception(
                            "error checking if client disconnected from sse; user_id: %s", user_principal.user_id
                        )
                        break

                    try:
                        try:
                            async with asyncio.timeout(1):
                                conversation_event = await event_queue.get()
                        except asyncio.TimeoutError:
                            continue

                        server_sent_event = ServerSentEvent(
                            id=conversation_event.id,
                            event=conversation_event.event.value,
                            data=json.dumps({
                                **conversation_event.model_dump(mode="json", include={"timestamp", "data"}),
                                "conversation_id": str(conversation_event.conversation_id),
                            }),
                            retry=1000,
                        )
                        yield server_sent_event
                        logger.debug(
                            "sent event to user sse client; user_id: %s, event: %s",
                            user_principal.user_id,
                            server_sent_event.event,
                        )

                    except Exception:
                        logger.exception("error sending event to sse client; user_id: %s", user_principal.user_id)

            finally:
                queues.discard(event_queue)
                if len(queues) == 0:
                    async with conversation_sse_queues_lock:
                        if len(queues) == 0:
                            user_sse_queues.pop(user_principal.user_id, None)

        return EventSourceResponse(event_generator(), sep="\n")

    @app.post("/conversations")
    async def create_conversation(
        new_conversation: NewConversation,
        user_principal: auth.DependsUserPrincipal,
    ) -> Conversation:
        return await conversation_controller.create_conversation(
            user_principal=user_principal,
            new_conversation=new_conversation,
        )

    @app.post("/conversations/{owner_id}")
    async def create_conversation_with_owner(
        assistant_principal: auth.DependsAssistantPrincipal,
        new_conversation: NewConversation,
        owner_id: str,
    ) -> Conversation:
        return await conversation_controller.create_conversation_with_owner(
            new_conversation=new_conversation,
            principal=assistant_principal,
            owner_id=owner_id,
        )

    @app.post("/conversations/{conversation_id}")
    async def duplicate_conversation(
        conversation_id: uuid.UUID,
        principal: auth.DependsActorPrincipal,
        new_conversation: NewConversation,
    ) -> ConversationImportResult:
        return await assistant_controller.duplicate_conversation(
            principal=principal, conversation_id=conversation_id, new_conversation=new_conversation
        )

    @app.get("/conversations")
    async def list_conversations(
        principal: auth.DependsActorPrincipal,
        include_inactive: bool = False,
        latest_message_types: Annotated[list[MessageType], Query(alias="latest_message_type")] = [MessageType.chat],
    ) -> ConversationList:
        return await conversation_controller.get_conversations(
            principal=principal,
            include_all_owned=include_inactive,
            latest_message_types=set(latest_message_types),
        )

    @app.get("/conversations/{conversation_id}")
    async def get_conversation(
        conversation_id: uuid.UUID,
        principal: auth.DependsActorPrincipal,
        latest_message_types: Annotated[list[MessageType], Query(alias="latest_message_type")] = [MessageType.chat],
    ) -> Conversation:
        return await conversation_controller.get_conversation(
            principal=principal,
            conversation_id=conversation_id,
            latest_message_types=set(latest_message_types),
        )

    @app.patch("/conversations/{conversation_id}")
    async def update_conversation(
        conversation_id: uuid.UUID,
        update_conversation: UpdateConversation,
        user_principal: auth.DependsActorPrincipal,
    ) -> Conversation:
        return await conversation_controller.update_conversation(
            user_principal=user_principal,
            conversation_id=conversation_id,
            update_conversation=update_conversation,
        )

    @app.get("/conversations/{conversation_id}/participants")
    async def list_conversation_participants(
        conversation_id: uuid.UUID,
        principal: auth.DependsActorPrincipal,
        include_inactive: bool = False,
    ) -> ConversationParticipantList:
        return await conversation_controller.get_conversation_participants(
            principal=principal,
            conversation_id=conversation_id,
            include_inactive=include_inactive,
        )

    def _translate_participant_id_me(principal: auth.ActorPrincipal, participant_id: str) -> str:
        if participant_id != "me":
            return participant_id

        match principal:
            case auth.UserPrincipal():
                return principal.user_id
            case auth.AssistantPrincipal():
                return str(principal.assistant_id)

    @app.get("/conversations/{conversation_id}/participants/{participant_id}")
    async def get_conversation_participant(
        conversation_id: uuid.UUID,
        participant_id: str,
        principal: auth.DependsActorPrincipal,
    ) -> ConversationParticipant:
        participant_id = _translate_participant_id_me(principal, participant_id)

        return await conversation_controller.get_conversation_participant(
            principal=principal,
            conversation_id=conversation_id,
            participant_id=participant_id,
        )

    @app.patch("/conversations/{conversation_id}/participants/{participant_id}")
    @app.put("/conversations/{conversation_id}/participants/{participant_id}")
    async def add_or_update_conversation_participant(
        conversation_id: uuid.UUID,
        participant_id: str,
        update_participant: UpdateParticipant,
        principal: auth.DependsActorPrincipal,
    ) -> ConversationParticipant:
        participant_id = _translate_participant_id_me(principal, participant_id)

        return await conversation_controller.add_or_update_conversation_participant(
            participant_id=participant_id,
            update_participant=update_participant,
            conversation_id=conversation_id,
            principal=principal,
        )

    @app.get("/conversations/{conversation_id}/messages")
    async def list_conversation_messages(
        conversation_id: uuid.UUID,
        principal: auth.DependsActorPrincipal,
        participant_roles: Annotated[list[ParticipantRole] | None, Query(alias="participant_role")] = None,
        participant_ids: Annotated[list[str] | None, Query(alias="participant_id")] = None,
        message_types: Annotated[list[MessageType] | None, Query(alias="message_type")] = None,
        before: Annotated[uuid.UUID | None, Query()] = None,
        after: Annotated[uuid.UUID | None, Query()] = None,
        limit: Annotated[int, Query(lte=500)] = 100,
    ) -> ConversationMessageList:
        return await conversation_controller.get_messages(
            conversation_id=conversation_id,
            principal=principal,
            participant_ids=participant_ids,
            participant_roles=participant_roles,
            message_types=message_types,
            before=before,
            after=after,
            limit=limit,
        )

    @app.post("/conversations/{conversation_id}/messages")
    async def create_conversation_message(
        conversation_id: uuid.UUID,
        new_message: NewConversationMessage,
        principal: auth.DependsActorPrincipal,
        background_tasks: BackgroundTasks,
    ) -> ConversationMessage:
        response, task_args = await conversation_controller.create_conversation_message(
            conversation_id=conversation_id,
            new_message=new_message,
            principal=principal,
        )
        if task_args:
            background_tasks.add_task(*task_args)
        return response

    @app.get(
        "/conversations/{conversation_id}/messages/{message_id}",
    )
    async def get_message(
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        principal: auth.DependsActorPrincipal,
    ) -> ConversationMessage:
        return await conversation_controller.get_message(
            conversation_id=conversation_id,
            message_id=message_id,
            principal=principal,
        )

    @app.get(
        "/conversations/{conversation_id}/messages/{message_id}/debug_data",
    )
    async def get_message_debug_data(
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        principal: auth.DependsActorPrincipal,
    ) -> ConversationMessageDebug:
        return await conversation_controller.get_message_debug(
            conversation_id=conversation_id,
            message_id=message_id,
            principal=principal,
        )

    @app.delete(
        "/conversations/{conversation_id}/messages/{message_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_message(
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user_principal: auth.DependsUserPrincipal,
    ) -> None:
        await conversation_controller.delete_message(
            conversation_id=conversation_id,
            message_id=message_id,
            user_principal=user_principal,
        )

    @app.put("/conversations/{conversation_id}/files")
    async def upload_files(
        conversation_id: uuid.UUID,
        upload_files: Annotated[list[UploadFile], File(alias="files")],
        principal: auth.DependsActorPrincipal,
        file_metadata_raw: str = Form(alias="metadata", default="{}"),
    ) -> FileList:
        try:
            file_metadata: dict[str, dict[str, Any]] = json.loads(file_metadata_raw)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

        if not isinstance(file_metadata, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="metadata must be a JSON object as a string"
            )

        return await file_controller.upload_files(
            conversation_id=conversation_id,
            upload_files=upload_files,
            principal=principal,
            file_metadata=file_metadata,
        )

    @app.get("/conversations/{conversation_id}/files")
    async def list_files(
        conversation_id: uuid.UUID,
        principal: auth.DependsActorPrincipal,
        prefix: str | None = None,
    ) -> FileList:
        return await file_controller.list_files(conversation_id=conversation_id, principal=principal, prefix=prefix)

    @app.get("/conversations/{conversation_id}/files/{filename:path}/versions")
    async def file_versions(
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.DependsActorPrincipal,
        version: int | None = None,
    ) -> FileVersions:
        return await file_controller.file_versions(
            conversation_id=conversation_id, filename=filename, principal=principal, version=version
        )

    @app.get("/conversations/{conversation_id}/files/{filename:path}")
    async def download_file(
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.DependsActorPrincipal,
        version: int | None = None,
    ) -> StreamingResponse:
        result = await file_controller.download_file(
            conversation_id=conversation_id,
            filename=filename,
            principal=principal,
            version=version,
        )

        return StreamingResponse(
            result.stream,
            media_type=result.content_type,
            headers={"Content-Disposition": f'attachment; filename="{urllib.parse.quote(result.filename)}"'},
        )

    @app.patch("/conversations/{conversation_id}/files/{filename:path}")
    async def update_file(
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.DependsActorPrincipal,
        update_file: UpdateFile,
    ) -> FileVersions:
        return await file_controller.update_file_metadata(
            conversation_id=conversation_id,
            filename=filename,
            principal=principal,
            metadata=update_file.metadata,
        )

    @app.delete("/conversations/{conversation_id}/files/{filename:path}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_file(
        conversation_id: uuid.UUID,
        filename: str,
        principal: auth.DependsActorPrincipal,
    ) -> None:
        await file_controller.delete_file(
            conversation_id=conversation_id,
            filename=filename,
            principal=principal,
        )

    @app.post("/conversation-shares")
    async def create_conversation_share(
        user_principal: auth.DependsUserPrincipal,
        new_conversation_share: NewConversationShare,
    ) -> ConversationShare:
        return await conversation_share_controller.create_conversation_share(
            user_principal=user_principal,
            new_conversation_share=new_conversation_share,
        )

    # create_conversation_share_with_owner
    @app.post("/conversation-shares/{owner_id}")
    async def create_conversation_share_with_owner(
        new_conversation_share: NewConversationShare,
        owner_id: str,
    ) -> ConversationShare:
        return await conversation_share_controller.create_conversation_share_with_owner(
            new_conversation_share=new_conversation_share,
            owner_id=owner_id,
        )

    @app.get("/conversation-shares")
    async def list_conversation_shares(
        user_principal: auth.DependsUserPrincipal,
        include_unredeemable: bool = False,
        conversation_id: uuid.UUID | None = None,
    ) -> ConversationShareList:
        return await conversation_share_controller.get_conversation_shares(
            user_principal=user_principal,
            conversation_id=conversation_id,
            include_unredeemable=include_unredeemable,
        )

    @app.get("/conversation-shares/{conversation_share_id}")
    async def get_conversation_share(
        user_principal: auth.DependsUserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShare:
        return await conversation_share_controller.get_conversation_share(
            user_principal=user_principal,
            conversation_share_id=conversation_share_id,
        )

    @app.delete("/conversation-shares/{conversation_share_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_conversation_share(
        user_principal: auth.DependsUserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> None:
        await conversation_share_controller.delete_conversation_share(
            user_principal=user_principal,
            conversation_share_id=conversation_share_id,
        )

    @app.post("/conversation-shares/{conversation_share_id}/redemptions")
    async def redeem_conversation_share(
        user_principal: auth.DependsUserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShareRedemption:
        return await conversation_share_controller.redeem_conversation_share(
            user_principal=user_principal,
            conversation_share_id=conversation_share_id,
        )

    @app.get("/conversation-shares/{conversation_share_id}/redemptions")
    async def list_conversation_share_redemptions(
        user_principal: auth.DependsUserPrincipal,
        conversation_share_id: uuid.UUID,
    ) -> ConversationShareRedemptionList:
        return await conversation_share_controller.get_redemptions_for_share(
            user_principal=user_principal,
            conversation_share_id=conversation_share_id,
        )

    @app.get("/conversation-share-redemptions")
    async def list_conversation_share_redemptions_for_user(
        user_principal: auth.DependsUserPrincipal,
    ) -> ConversationShareRedemptionList:
        return await conversation_share_controller.get_redemptions_for_user(
            user_principal=user_principal,
        )

    @app.get("/azure-speech/token")
    async def get_azure_speech_token() -> dict[str, str]:
        return azure_speech.get_token()


=== File: workbench-service/semantic_workbench_service/service_user_principals.py ===
from . import auth

workflow = auth.ServiceUserPrincipal(user_id="workflow", name="Workflow Service")

semantic_workbench = auth.ServiceUserPrincipal(user_id="semantic-workbench", name="Semantic Workbench Service")


=== File: workbench-service/semantic_workbench_service/start.py ===
import argparse
import logging

import uvicorn
from fastapi import FastAPI

from . import logging_config, service, settings
from .api import FastAPILifespan

logging_config.config(settings=settings.logging)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    lifespan = FastAPILifespan()
    app = FastAPI(lifespan=lifespan.lifespan, title="Semantic Workbench Service", version="0.1.0")
    service.init(
        app,
        register_lifespan_handler=lifespan.register_handler,
    )
    return app


def main():
    parse_args = argparse.ArgumentParser(
        description="start the Semantic workbench service", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parse_args.add_argument(
        "--host",
        dest="host",
        type=str,
        default=settings.service.host,
        help="host IP to run service on",
    )
    parse_args.add_argument(
        "--port", dest="port", type=int, default=settings.service.port, help="port to run service on"
    )
    args = parse_args.parse_args()

    settings.service.host = args.host
    settings.service.port = args.port

    logger.info("Starting workbench service ...")
    app = create_app()
    uvicorn.run(
        app,
        host=settings.service.host,
        port=settings.service.port,
        access_log=False,
        log_config={"version": 1, "disable_existing_loggers": False},
    )


if __name__ == "__main__":
    main()


=== File: workbench-service/tests/__init__.py ===


=== File: workbench-service/tests/conftest.py ===
import asyncio
import os
import pathlib
import tempfile
import uuid
from typing import AsyncGenerator, Iterator

import asyncpg
import dotenv
import httpx
import pytest
import semantic_workbench_assistant.assistant_app
import semantic_workbench_assistant.assistant_service
import semantic_workbench_assistant.canonical
import semantic_workbench_assistant.storage
import semantic_workbench_service
import semantic_workbench_service.assistant_api_key
from fastapi import FastAPI
from semantic_workbench_api_model import (
    assistant_service_client,
    workbench_service_client,
)
from semantic_workbench_service import files, settings
from semantic_workbench_service import service as workbenchservice
from semantic_workbench_service.api import FastAPILifespan
from semantic_workbench_service.config import DBSettings

from tests.types import MockUser


def create_test_user(monkeypatch: pytest.MonkeyPatch) -> MockUser:
    random_id = str(uuid.uuid4())
    name = f"test user {random_id}"
    test_user = MockUser(tenant_id=random_id, object_id=random_id, name=name)

    # monkeypatch the allowed_jwt_algorithms and app_ids for tests
    monkeypatch.setattr(settings.auth, "allowed_jwt_algorithms", {test_user.token_algo})
    monkeypatch.setattr(settings.auth, "allowed_app_id", test_user.app_id)

    return test_user


@pytest.fixture
def test_user(monkeypatch: pytest.MonkeyPatch) -> MockUser:
    return create_test_user(monkeypatch)


@pytest.fixture
def test_user_2(monkeypatch: pytest.MonkeyPatch) -> MockUser:
    return create_test_user(monkeypatch)


def env_var(name: str) -> str | None:
    if name in os.environ:
        return os.environ[name]
    dotenv_path = dotenv.find_dotenv(usecwd=True)
    if not dotenv_path:
        return None
    dotenv_values = dotenv.dotenv_values(dotenv_path)
    return dotenv_values.get(name)


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--echosql",
        action="store_true",
        help="echo db sql statements",
        default=(env_var("WORKBENCH_PYTEST_ECHOSQL") or "").lower() in ["true", "1"],
    )
    parser.addoption(
        "--dbtype",
        action="store",
        help="database type",
        choices=["sqlite", "postgresql"],
        default=env_var("WORKBENCH_PYTEST_DBTYPE") or "sqlite",
    )


@pytest.fixture(scope="session")
def docker_compose_file() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "docker-compose.yaml"


@pytest.fixture
def db_type(request: pytest.FixtureRequest) -> str:
    return request.config.option.dbtype


@pytest.fixture
def echo_sql(request: pytest.FixtureRequest) -> bool:
    return request.config.option.echosql


@pytest.fixture
async def db_settings(db_type: str, echo_sql: bool, request: pytest.FixtureRequest) -> AsyncGenerator[DBSettings, None]:
    db_settings = semantic_workbench_service.settings.db.model_copy()
    db_settings.echosql = echo_sql
    db_settings.alembic_config_path = str(pathlib.Path(__file__).parent.parent / "alembic.ini")

    match db_type:
        case "sqlite":
            # use a sqlite db in an auto-deleted temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                path = pathlib.Path(temp_dir) / f"{uuid.uuid4().hex}.db"
                db_settings.url = f"sqlite:///{path}"

                yield db_settings

        case "postgresql":
            # use a postgresql db in a docker container
            docker_services = request.getfixturevalue("docker_services")
            docker_ip = request.getfixturevalue("docker_ip")
            db_name = f"workbench_test_{uuid.uuid4().hex}"
            postgresql_port = docker_services.port_for("postgres", 5432)
            postgresql_url = f"postgresql://{docker_ip}:{postgresql_port}"

            db_settings.url = f"{postgresql_url}/{db_name}"
            db_settings.postgresql_ssl_mode = "disable"
            db_settings.postgresql_pool_size = 1

            admin_db_url = f"{postgresql_url}/postgres"

            async def db_is_up() -> bool:
                try:
                    conn = await asyncpg.connect(dsn=admin_db_url)
                    await conn.close()
                except (
                    asyncio.TimeoutError,
                    ConnectionResetError,
                    asyncpg.exceptions.CannotConnectNowError,
                    ConnectionError,
                ):
                    return False
                else:
                    return True

            async def wait_until_responsive(timeout: float, pause: float) -> None:
                async with asyncio.timeout(timeout):
                    while True:
                        if await db_is_up():
                            return
                        await asyncio.sleep(pause)

            await wait_until_responsive(timeout=30.0, pause=0.1)

            admin_connection: asyncpg.Connection = await asyncpg.connect(dsn=admin_db_url)
            try:
                await admin_connection.execute(f"CREATE DATABASE {db_name}")

                try:
                    yield db_settings
                finally:
                    await admin_connection.execute(
                        "select pg_terminate_backend(pid) from pg_stat_activity where datname=$1",
                        db_name,
                    )
                    await admin_connection.execute(f"DROP DATABASE {db_name}")

            finally:
                await admin_connection.close()


@pytest.fixture
def storage_settings() -> Iterator[files.StorageSettings]:
    storage_settings = semantic_workbench_service.settings.storage.model_copy()

    with tempfile.TemporaryDirectory() as temp_dir:
        storage_settings.root = temp_dir
        yield storage_settings


@pytest.fixture
def workbench_service(
    db_settings: DBSettings,
    storage_settings: files.StorageSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    monkeypatch.setattr(semantic_workbench_service.settings, "db", db_settings)
    monkeypatch.setattr(semantic_workbench_service.settings, "storage", storage_settings)

    api_key = uuid.uuid4().hex

    # monkeypatch the api key store for the workbench service
    monkeypatch.setattr(
        semantic_workbench_service.assistant_api_key,
        "get_store",
        lambda: semantic_workbench_service.assistant_api_key.FixedApiKeyStore(api_key=api_key),
    )

    # monkeypatch the configured api key for the assistant service
    monkeypatch.setattr(semantic_workbench_assistant.assistant_service.settings, "workbench_service_api_key", api_key)

    lifespan = FastAPILifespan()
    app = FastAPI(title="workbench service", lifespan=lifespan.lifespan)
    workbenchservice.init(
        app,
        register_lifespan_handler=lifespan.register_handler,
    )

    # monkeypatch workbench client to use a transport that directs requests to the workbench app
    monkeypatch.setattr(workbench_service_client, "httpx_transport_factory", lambda: httpx.ASGITransport(app=app))

    return app


@pytest.fixture
def canonical_assistant_service(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[FastAPI]:
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr(semantic_workbench_assistant.settings.storage, "root", temp_dir)

        assistant_app = semantic_workbench_assistant.canonical.canonical_app.fastapi_app()

        # configure assistant client to use a specific transport that directs requests to the assistant app
        monkeypatch.setattr(
            assistant_service_client, "httpx_transport_factory", lambda: httpx.ASGITransport(app=assistant_app)
        )

        yield assistant_app


=== File: workbench-service/tests/docker-compose.yaml ===
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${USER:-${USERNAME:-postgres}}
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - 5444:5432


=== File: workbench-service/tests/test_assistant_api_key.py ===
import asyncio
import uuid

from semantic_workbench_service.assistant_api_key import ApiKeyStore, cached


class MockApiKeyStore(ApiKeyStore):
    def __init__(self) -> None:
        self._api_keys: dict[str, str] = {}

    def override_api_key(self, key_name: str, api_key: str):
        self._api_keys[key_name] = api_key

    def generate_key_name(self, identifier: str) -> str:
        return identifier

    async def get(self, key_name: str) -> str | None:
        return self._api_keys.get(key_name)

    async def reset(self, key_name: str) -> str:
        new_key = uuid.uuid4().hex
        self._api_keys[key_name] = new_key
        return new_key

    async def delete(self, key_name: str) -> None:
        self._api_keys.pop(key_name, None)


async def test_cached_api_key_store():
    ttl_seconds = 0.5
    mock_store = MockApiKeyStore()
    cached_store = cached(api_key_store=mock_store, max_cache_size=200, ttl_seconds=ttl_seconds)

    key_name = "key"

    # set and get initial api key
    api_key = uuid.uuid4().hex
    mock_store.override_api_key(key_name=key_name, api_key=api_key)

    assert (await cached_store.get(key_name=key_name)) == api_key

    # update key on the "backend"
    updated_api_key = uuid.uuid4().hex
    mock_store.override_api_key(key_name=key_name, api_key=updated_api_key)

    # ensure that the old value is still returned
    assert (await cached_store.get(key_name=key_name)) == api_key

    # ensure that reset returns the new value
    reset_api_key = await cached_store.reset(key_name=key_name)
    assert reset_api_key != updated_api_key
    assert (await cached_store.get(key_name=key_name)) == reset_api_key

    # ensure that delete removes the item from the cache
    await cached_store.delete(key_name=key_name)
    assert (await cached_store.get(key_name=key_name)) is None

    # delete again, this time updating the value on the "backend" before getting
    await cached_store.delete(key_name=key_name)
    mock_store.override_api_key(key_name=key_name, api_key=updated_api_key)
    assert (await cached_store.get(key_name=key_name)) == updated_api_key

    # ensure that the cache is cleared after the TTL
    another_updated_api_key = uuid.uuid4().hex
    mock_store.override_api_key(key_name=key_name, api_key=another_updated_api_key)
    assert (await cached_store.get(key_name=key_name)) == updated_api_key
    await asyncio.sleep(ttl_seconds)

    assert (await cached_store.get(key_name=key_name)) == another_updated_api_key

    # ensure that a different key has an isolated cache
    second_key_name = "second_key"
    second_api_key = await cached_store.reset(key_name=second_key_name)
    assert await cached_store.get(key_name=second_key_name) == second_api_key
    mock_store.override_api_key(key_name=second_key_name, api_key=uuid.uuid4().hex)
    assert await cached_store.get(key_name=second_key_name) == second_api_key

    assert await cached_store.get(key_name=key_name) == another_updated_api_key


=== File: workbench-service/tests/test_files.py ===
import io
import uuid

import pytest

from semantic_workbench_service import files


def test_read_file_not_found(storage_settings: files.StorageSettings) -> None:
    file_storage = files.Storage(settings=storage_settings)

    with (
        pytest.raises(FileNotFoundError),
        file_storage.read_file(
            namespace="conversation_id",
            filename="filename",
        ) as f,
    ):
        f.read()


def test_write_file(storage_settings: files.StorageSettings) -> None:
    file_storage = files.Storage(settings=storage_settings)

    file_storage.write_file(namespace="conversation_id", filename="filename", content=io.BytesIO(b"content"))


def test_write_read_delete_file(storage_settings: files.StorageSettings) -> None:
    file_storage = files.Storage(settings=storage_settings)

    conversation_id = uuid.uuid4().hex
    filename = "myfile.txt"
    file_content = b"""
    this is a text file.
    """
    file_storage.write_file(namespace=conversation_id, filename=filename, content=io.BytesIO(file_content))

    with file_storage.read_file(namespace=conversation_id, filename=filename) as f:
        assert f.read() == file_content

    file_storage.delete_file(namespace=conversation_id, filename=filename)

    with pytest.raises(FileNotFoundError), file_storage.read_file(namespace=conversation_id, filename=filename) as f:
        pass


=== File: workbench-service/tests/test_integration.py ===
import asyncio
import io
import json
import logging
import re
import uuid

import httpx
import pytest
import semantic_workbench_assistant.canonical
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from semantic_workbench_api_model import assistant_model, workbench_model

from .types import MockUser


async def wait_for_assistant_service_registration(
    wb_client: httpx.AsyncClient,
) -> workbench_model.AssistantServiceRegistration:
    for _ in range(10):
        http_response = await wb_client.get("/assistant-service-registrations")
        http_response.raise_for_status()
        assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(http_response.json())
        if assistant_services.assistant_service_registrations:
            return assistant_services.assistant_service_registrations[0]

        await asyncio.sleep(0.01)

    raise Exception("Timed out waiting for assistant service registration")


async def test_flow_create_assistant_update_config(
    workbench_service: FastAPI,
    canonical_assistant_service: FastAPI,
    test_user: MockUser,
) -> None:
    async with (
        LifespanManager(workbench_service),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=workbench_service),
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(canonical_assistant_service),
    ):
        assistant_service = await wait_for_assistant_service_registration(wb_client)

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=assistant_service.assistant_service_id,
            ).model_dump(mode="json"),
        )
        logging.info("POST wb/assistants resp: %s", resp.json())
        resp.raise_for_status()

        assistant = workbench_model.Assistant(**resp.json())
        logging.info("POST wb/assistants resp loaded into model: %s", assistant)

        resp = await wb_client.get(f"/assistants/{assistant.id}")
        logging.info("GET wb/assistant/id resp: %s", resp.json())
        resp.raise_for_status()

        assert resp.json() == json.loads(assistant.model_dump_json())

        config = assistant_model.ConfigPutRequestModel(
            config=semantic_workbench_assistant.canonical.ConfigStateModel(
                short_text="test short text",
                long_text="test long text",
                prompt=semantic_workbench_assistant.canonical.PromptConfigModel(
                    custom_prompt="test custom prompt",
                    temperature=0.999999,
                ),
            ).model_dump(),
        )
        resp = await wb_client.put(f"/assistants/{assistant.id}/config", json=config.model_dump(mode="json"))
        resp.raise_for_status()


async def test_flow_create_assistant_update_conversation_state(
    workbench_service: FastAPI,
    canonical_assistant_service: FastAPI,
    test_user: MockUser,
) -> None:
    async with (
        LifespanManager(workbench_service),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=workbench_service),
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(canonical_assistant_service),
    ):
        assistant_service = await wait_for_assistant_service_registration(wb_client)

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=assistant_service.assistant_service_id,
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())

        assistant = workbench_model.Assistant.model_validate(resp.json())
        logging.info("POST wb/assistants resp loaded into model: %s", assistant)

        resp = await wb_client.get(f"/assistants/{assistant.id}")
        resp.raise_for_status()
        logging.info("GET wb/assistant/id resp: %s", resp.json())

        assert resp.json() == json.loads(assistant.model_dump_json())

        resp = await wb_client.post("/conversations", json={"title": "test-conversation"})
        resp.raise_for_status()
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()
        participant = workbench_model.ConversationParticipant.model_validate(resp.json())
        assert participant.online is True

        resp = await wb_client.get(f"/assistants/{assistant.id}/conversations/{conversation.id}/states")
        resp.raise_for_status()
        logging.info("GET asst/conversations/id/states resp: %s", resp.json())

        states = assistant_model.StateDescriptionListResponseModel(**resp.json())
        logging.info("GET asst/conversations/id/states resp loaded into model: %s", states)

        assert len(states.states) == 1
        assert states.states[0].id == "simple_state"

        resp = await wb_client.get(f"/assistants/{assistant.id}/conversations/{conversation.id}/states/simple_state")
        resp.raise_for_status()
        logging.info("GET asst/conversations/id/states/simple_state resp: %s", resp.json())

        state = assistant_model.StateResponseModel(**resp.json())
        logging.info("GET asst/conversations/id/states/simple_state resp loaded into model: %s", state)

        assert "message" in state.data

        updated_message = f"updated message {uuid.uuid4()}"
        state_update = assistant_model.StatePutRequestModel(
            data={"message": updated_message},
        )
        resp = await wb_client.put(
            f"/assistants/{assistant.id}/conversations/{conversation.id}/states/simple_state",
            json=state_update.model_dump(mode="json"),
        )
        resp.raise_for_status()

        resp = await wb_client.get(f"/assistants/{assistant.id}/conversations/{conversation.id}/states/simple_state")
        resp.raise_for_status()
        logging.info("GET asst/conversations/id/states/simple_state resp: %s", resp.json())

        state = assistant_model.StateResponseModel(**resp.json())
        logging.info("GET asst/conversations/id/states/simple_state resp loaded into model: %s", state)

        assert "message" in state.data
        assert state.data["message"] == updated_message


async def test_flow_create_assistant_send_message_receive_resp(
    workbench_service: FastAPI,
    canonical_assistant_service: FastAPI,
    test_user: MockUser,
) -> None:
    async with (
        LifespanManager(workbench_service),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=workbench_service),
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(canonical_assistant_service),
    ):
        assistant_service = await wait_for_assistant_service_registration(wb_client)

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=assistant_service.assistant_service_id,
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())

        assistant = workbench_model.Assistant(**resp.json())

        resp = await wb_client.post("/conversations", json={"title": "test-conversation"})
        resp.raise_for_status()
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()

        resp = await wb_client.post(
            f"/conversations/{conversation.id}/messages",
            json={"content": "hello"},
        )
        resp.raise_for_status()
        logging.info("POST wb/conversations/%s/messages resp: %s", conversation.id, resp.json())

        attempts = 1
        messages = []
        while attempts <= 10 and len(messages) < 2:
            if attempts > 1:
                await asyncio.sleep(0.5)
            attempts += 1

            resp = await wb_client.get(f"/conversations/{conversation.id}/messages")
            resp.raise_for_status()
            logging.info("GET wb/conversations/%s/messages resp: %s", conversation.id, resp.json())

            messages_resp = resp.json()

            assert "messages" in messages_resp
            messages = messages_resp["messages"]

        assert len(messages) > 1


async def test_flow_create_assistant_send_message_receive_resp_export_import_assistant(
    workbench_service: FastAPI,
    canonical_assistant_service: FastAPI,
    test_user: MockUser,
) -> None:
    async with (
        LifespanManager(workbench_service),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=workbench_service),
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(canonical_assistant_service),
    ):
        assistant_service = await wait_for_assistant_service_registration(wb_client)

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=assistant_service.assistant_service_id,
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())

        assistant = workbench_model.Assistant(**resp.json())

        resp = await wb_client.post("/conversations", json={"title": "test-conversation"})
        resp.raise_for_status()
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()

        async def send_message_wait_for_response(conversation: workbench_model.Conversation) -> None:
            resp = await wb_client.get(f"/conversations/{conversation.id}/messages")
            resp.raise_for_status()
            existing_messages = workbench_model.ConversationMessageList.model_validate(resp.json())

            logging.info("POST wb/conversations/%s/messages resp: %s", conversation.id, resp.json())
            resp = await wb_client.post(
                f"/conversations/{conversation.id}/messages",
                json={"content": "hello"},
            )
            resp.raise_for_status()
            logging.info("POST wb/conversations/%s/messages resp: %s", conversation.id, resp.json())

            url = f"/conversations/{conversation.id}/messages"
            params = {}
            if existing_messages.messages:
                params = {"after": str(existing_messages.messages[-1].id)}
            attempts = 1
            messages = []
            while attempts <= 10 and len(messages) < 2:
                if attempts > 1:
                    await asyncio.sleep(0.5)

                attempts += 1

                resp = await wb_client.get(url, params=params)
                resp.raise_for_status()
                logging.info("GET %s resp: %s", url, resp.json())

                messages_response = workbench_model.ConversationMessageList.model_validate(resp.json())
                messages = messages_response.messages

            assert len(messages) == 2
            assert messages[0].sender.participant_role == workbench_model.ParticipantRole.user
            assert messages[1].sender.participant_role == workbench_model.ParticipantRole.assistant

        await send_message_wait_for_response(conversation)

        resp = await wb_client.get(f"/assistants/{assistant.id}/export")
        resp.raise_for_status()

        assert resp.headers["content-type"] == "application/zip"
        assert "content-length" in resp.headers
        assert int(resp.headers["content-length"]) > 0

        logging.info("response: %s", resp.content)

        exported_file = io.BytesIO(resp.content)

        for import_number in range(1, 3):
            resp = await wb_client.post("/conversations/import", files={"from_export": exported_file})
            logging.info("import %s response: %s", import_number, resp.json())
            resp.raise_for_status()

            import_result = workbench_model.ConversationImportResult.model_validate(resp.json())
            new_assistant_id = import_result.assistant_ids[0]

            resp = await wb_client.get(f"/assistants/{new_assistant_id}/conversations")
            conversations = workbench_model.ConversationList.model_validate(resp.json())
            new_conversation = conversations.conversations[0]

            resp = await wb_client.get("/assistants")
            logging.info("response: %s", resp.json())
            resp.raise_for_status()
            assistants_response = workbench_model.AssistantList.model_validate(resp.json())
            assistant_count = len(assistants_response.assistants)
            assert assistant_count == 1
            assert assistants_response.assistants[0].name == "test-assistant"

            # ensure the new assistant can send and receive messages in the new conversation
            await send_message_wait_for_response(new_conversation)


async def test_flow_create_assistant_send_message_receive_resp_export_import_conversations(
    workbench_service: FastAPI,
    canonical_assistant_service: FastAPI,
    test_user: MockUser,
) -> None:
    async with (
        LifespanManager(workbench_service),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=workbench_service),
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(canonical_assistant_service),
    ):
        assistant_service = await wait_for_assistant_service_registration(wb_client)

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=assistant_service.assistant_service_id,
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())

        assistant = workbench_model.Assistant(**resp.json())

        resp = await wb_client.post("/conversations", json={"title": "test-conversation"})
        resp.raise_for_status()
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()

        async def send_message_wait_for_response(conversation: workbench_model.Conversation) -> None:
            resp = await wb_client.get(f"/conversations/{conversation.id}/messages")
            resp.raise_for_status()
            existing_messages = workbench_model.ConversationMessageList.model_validate(resp.json())

            resp = await wb_client.post(
                f"/conversations/{conversation.id}/messages",
                json={"content": "hello"},
            )
            resp.raise_for_status()
            logging.info("POST wb/conversations/%s/messages resp: %s", conversation.id, resp.json())

            url = f"/conversations/{conversation.id}/messages"
            params = {}
            if existing_messages.messages:
                params = {"after": str(existing_messages.messages[-1].id)}
            attempts = 1
            messages = []
            while attempts <= 10 and len(messages) < 2:
                if attempts > 1:
                    await asyncio.sleep(0.5)

                attempts += 1

                resp = await wb_client.get(url, params=params)
                resp.raise_for_status()
                logging.info("GET wb/conversations/%s/messages resp: %s", conversation.id, resp.json())

                messages_response = workbench_model.ConversationMessageList.model_validate(resp.json())
                messages = messages_response.messages

            assert len(messages) == 2
            assert messages[0].sender.participant_role == workbench_model.ParticipantRole.user
            assert messages[1].sender.participant_role == workbench_model.ParticipantRole.assistant

        await send_message_wait_for_response(conversation)

        resp = await wb_client.get("/conversations/export", params={"id": str(conversation.id)})
        resp.raise_for_status()

        assert resp.headers["content-type"] == "application/zip"
        assert "content-length" in resp.headers
        assert int(resp.headers["content-length"]) > 0

        logging.info("response: %s", resp.content)

        file_io = io.BytesIO(resp.content)

        for import_number in range(1, 3):
            resp = await wb_client.post("/conversations/import", files={"from_export": file_io})
            logging.info("import %s response: %s", import_number, resp.json())
            resp.raise_for_status()
            import_result = workbench_model.ConversationImportResult.model_validate(resp.json())
            assert len(import_result.assistant_ids) == 1
            new_assistant_id = import_result.assistant_ids[0]

            resp = await wb_client.get(f"/assistants/{new_assistant_id}/conversations")
            conversations = workbench_model.ConversationList.model_validate(resp.json())
            new_conversation = conversations.conversations[0]

            resp = await wb_client.get("/assistants")
            logging.info("response: %s", resp.json())
            resp.raise_for_status()

            assistants_response = workbench_model.AssistantList.model_validate(resp.json())
            assistant_count = len(assistants_response.assistants)
            assert assistant_count == 1

            assert assistants_response.assistants[0].name == "test-assistant"

            # ensure the new assistant can send and receive messages in the new conversation
            await send_message_wait_for_response(new_conversation)


@pytest.mark.parametrize(
    # spell-checker:ignore dlrow olleh
    ("command", "command_args", "expected_response_content_regex"),
    [
        ("/reverse", "hello world", re.compile("dlrow olleh")),
        ("/reverse", "-h", re.compile("usage: /reverse.+", re.DOTALL)),
        ("/reverse", "", re.compile("/reverse: error: .+", re.DOTALL)),
    ],
)
async def test_flow_create_assistant_send_command_message_receive_resp(
    workbench_service: FastAPI,
    canonical_assistant_service: FastAPI,
    test_user: MockUser,
    command: str,
    command_args: str,
    expected_response_content_regex: re.Pattern,
) -> None:
    async with (
        LifespanManager(workbench_service),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=workbench_service),
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(canonical_assistant_service),
    ):
        assistant_service = await wait_for_assistant_service_registration(wb_client)

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=assistant_service.assistant_service_id,
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())
        assistant = workbench_model.Assistant.model_validate(resp.json())
        logging.info("assistant: %s", assistant)

        resp = await wb_client.post(
            "/conversations",
            json={"title": "test-assistant"},
        )
        resp.raise_for_status()
        logging.info("POST wb/conversations resp: %s", resp.json())
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()

        command_content = f"{command} {command_args}"
        resp = await wb_client.post(
            f"/conversations/{conversation.id}/messages",
            json={
                "message_type": "command",
                "content_type": "application/json",
                "content": command_content,
            },
        )
        resp.raise_for_status()
        logging.info("POST wb/conversations/%s/messages resp: %s", conversation.id, resp.json())

        attempts = 1
        messages = []
        while attempts <= 10 and len(messages) < 2:
            if attempts > 1:
                await asyncio.sleep(0.5)
            attempts += 1

            resp = await wb_client.get(f"/conversations/{conversation.id}/messages")
            resp.raise_for_status()
            logging.info("GET wb/conversations/%s/messages resp: %s", conversation.id, resp.json())

            messages_resp = resp.json()

            assert "messages" in messages_resp
            messages = messages_resp["messages"]

        assert len(messages) > 1
        response_message = messages[1]

        assert expected_response_content_regex.fullmatch(response_message["content"])
        assert response_message["message_type"] == "command-response"


=== File: workbench-service/tests/test_middleware.py ===
import uuid

import fastapi
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from semantic_workbench_service import assistant_api_key, middleware, settings

from .types import MockUser


def mock_api_key_source(initial_api_key: str = ""):
    async def source(assistant_service_id: str) -> str | None:
        return await assistant_api_key.FixedApiKeyStore(initial_api_key).get(assistant_service_id)

    return source


async def test_auth_middleware_rejects_disallowed_algo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.auth, "allowed_jwt_algorithms", {"RS256"})

    tid = str(uuid.uuid4())
    token = jwt.encode(
        claims={
            "tid": tid,
        },
        key="",
        algorithm="HS256",
    )

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=mock_api_key_source())

    with TestClient(app) as client:
        http_response = client.get("/", headers={"Authorization": f"Bearer {token}"})

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "invalid token algorithm"


def test_auth_middleware_rejects_disallowed_app_id(monkeypatch: pytest.MonkeyPatch) -> None:
    algo = "HS256"

    monkeypatch.setattr(settings.auth, "allowed_app_id", "fake-app-id")
    monkeypatch.setattr(settings.auth, "allowed_jwt_algorithms", {algo})

    token = jwt.encode(
        claims={
            "appid": "not allowed",
        },
        key="",
        algorithm=algo,
    )

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=mock_api_key_source())

    with TestClient(app) as client:
        http_response = client.get("/", headers={"Authorization": f"Bearer {token}"})

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "invalid app"


def test_auth_middleware_rejects_missing_authorization_header():
    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=mock_api_key_source())

    with TestClient(app) as client:
        http_response = client.get("/")

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "not authenticated"


def test_auth_middleware_accepts_valid_user(test_user: MockUser):
    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=mock_api_key_source())

    with TestClient(app) as client:
        http_response = client.get("/", headers=test_user.authorization_headers)

        assert http_response.status_code == 404


def test_auth_middleware_accepts_valid_assistant_service():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=mock_api_key_source(test_api_key))

    valid_assistant_service_id = uuid.uuid4().hex
    with TestClient(app) as client:
        http_response = client.get(
            "/",
            headers={
                "X-Assistant-Service-ID": valid_assistant_service_id,
                "X-API-Key": test_api_key,
            },
        )

        assert http_response.status_code == 404


def test_auth_middleware_rejects_invalid_assistant_api_key():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=mock_api_key_source(test_api_key))

    valid_assistant_service_id = uuid.uuid4().hex
    with TestClient(app) as client:
        http_response = client.get(
            "/",
            headers={
                "X-Assistant-Service-ID": valid_assistant_service_id,
                "X-API-Key": "incorrect key",
            },
        )

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "invalid credentials"


def test_auth_middleware_rejects_invalid_assistant_service_id():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=mock_api_key_source(test_api_key))

    invalid_assistant_service_id = ""
    with TestClient(app) as client:
        http_response = client.get(
            "/",
            headers={
                "X-Assistant-Service-ID": invalid_assistant_service_id,
                "X-API-Key": test_api_key,
            },
        )

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "not authenticated"


def test_auth_middleware_accepts_valid_assistant():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=mock_api_key_source(test_api_key))

    valid_assistant_service_id = uuid.uuid4().hex
    valid_assistant_id = uuid.uuid4()
    with TestClient(app) as client:
        http_response = client.get(
            "/",
            headers={
                "X-Assistant-Service-ID": valid_assistant_service_id,
                "X-Assistant-ID": str(valid_assistant_id),
                "X-API-Key": test_api_key,
            },
        )

        assert http_response.status_code == 404


def test_auth_middleware_allows_anonymous_excluded_paths():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_route("/", route=lambda _: fastapi.Response(status_code=200))
    app.add_middleware(
        middleware.AuthMiddleware,
        api_key_source=mock_api_key_source(test_api_key),
        exclude_paths={"/"},
    )

    with TestClient(app) as client:
        http_response = client.get("/")

        assert http_response.status_code == 200


=== File: workbench-service/tests/test_migrations.py ===
import pytest
import semantic_workbench_service
from alembic import command
from alembic.config import Config
from semantic_workbench_service import db
from semantic_workbench_service.config import DBSettings


@pytest.fixture
async def bootstrapped_db_settings(db_settings: DBSettings) -> DBSettings:
    async with db.create_engine(db_settings) as engine:
        await db.bootstrap_db(engine, settings=db_settings)

    return db_settings


@pytest.fixture
def alembic_config(bootstrapped_db_settings: DBSettings, monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setattr(semantic_workbench_service.settings, "db", bootstrapped_db_settings)
    return Config(bootstrapped_db_settings.alembic_config_path)


def test_migration_cycle(alembic_config: Config) -> None:
    """Test that all migrations can downgrade and upgrade without error."""

    # check that there are no schema differences from head
    command.check(alembic_config)

    # downgrade to base
    command.downgrade(alembic_config, "base")

    # and upgrade back to head
    command.upgrade(alembic_config, "head")

    # check that the current revision is head
    command.check(
        alembic_config,
    )


=== File: workbench-service/tests/test_workbench_service.py ===
import asyncio
import datetime
import io
import json
import logging
import re
import time
import uuid
from unittest.mock import AsyncMock, Mock

import httpx
import openai_client
import pytest
import semantic_workbench_api_model.assistant_model as api_model
import semantic_workbench_service
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import HttpUrl
from pytest_httpx import HTTPXMock
from semantic_workbench_api_model import workbench_model, workbench_service_client

from .types import MockUser


def test_service_init(workbench_service: FastAPI):
    with TestClient(app=workbench_service):
        pass


id_segment = "[0-9a-f-]+"


def register_assistant_service(client: TestClient) -> workbench_model.AssistantServiceRegistration:
    new_registration = workbench_model.NewAssistantServiceRegistration(
        assistant_service_id=uuid.uuid4().hex,
        name="test-assistant-service",
        description="",
    )
    http_response = client.post("/assistant-service-registrations", json=new_registration.model_dump(mode="json"))
    assert httpx.codes.is_success(http_response.status_code)

    registration = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

    update_with_url = workbench_model.UpdateAssistantServiceRegistrationUrl(
        name=new_registration.name,
        description=new_registration.description,
        url=HttpUrl("http://testassistantservice"),
        online_expires_in_seconds=60,
    )
    http_response = client.put(
        f"/assistant-service-registrations/{new_registration.assistant_service_id}",
        json=update_with_url.model_dump(mode="json"),
        headers=workbench_service_client.AssistantServiceRequestHeaders(
            assistant_service_id=registration.assistant_service_id,
            api_key=registration.api_key or "",
        ).to_headers(),
    )
    assert httpx.codes.is_success(http_response.status_code)

    return registration


def test_create_assistant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        new_assistant = workbench_model.NewAssistant(
            name="test-assistant",
            assistant_service_id=registration.assistant_service_id,
            metadata={"test": "value"},
        )
        http_response = client.post("/assistants", json=new_assistant.model_dump(mode="json"))
        assert httpx.codes.is_success(http_response.status_code)

        logging.info("response: %s", http_response.json())

        assistant_response = workbench_model.Assistant.model_validate(http_response.json())
        assert assistant_response.name == new_assistant.name
        assert assistant_response.assistant_service_id == new_assistant.assistant_service_id
        assert assistant_response.metadata == new_assistant.metadata


def test_create_assistant_request_failure(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_exception(httpx.NetworkError("test error"))

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        new_assistant = workbench_model.NewAssistant(
            name="test-assistant",
            assistant_service_id=registration.assistant_service_id,
            image="pass an image to circumvent the request to the assistant service to get one",
            metadata={"test": "value"},
        )
        http_response = client.post("/assistants", json=new_assistant.model_dump(mode="json"))

        assert http_response.status_code == httpx.codes.FAILED_DEPENDENCY
        response_body = http_response.json()
        assert "detail" in response_body
        assert re.match(
            r"Failed to connect to assistant at url http://testassistantservice/[0-9a-f-]{36}; NetworkError: test"
            r" error",
            response_body["detail"],
        )


def exclude_system_keys(metadata: dict) -> dict:
    """Omit system metadata from the given metadata dictionary."""
    return {k: v for k, v in metadata.items() if not k.startswith("__")}


def test_create_conversation(workbench_service: FastAPI, test_user: MockUser):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_conversation = workbench_model.NewConversation(title="test", metadata={"test": "value"})
        http_response = client.post("/conversations", json=new_conversation.model_dump(mode="json"))
        assert httpx.codes.is_success(http_response.status_code)

        logging.info("response: %s", http_response.json())

        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert conversation_response.title == new_conversation.title
        assert exclude_system_keys(conversation_response.metadata) == new_conversation.metadata

        http_response = client.get(f"/conversations/{conversation_response.id}")
        assert httpx.codes.is_success(http_response.status_code)

        get_conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert get_conversation_response.title == new_conversation.title
        assert exclude_system_keys(get_conversation_response.metadata) == new_conversation.metadata


class AsyncContextManagerMock:
    def __init__(self, mock: Mock) -> None:
        self.mock = mock

    async def __aenter__(self):
        """Enter async context manager."""
        return self.mock

    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context manager."""
        pass


def test_create_conversation_and_retitle(
    workbench_service: FastAPI, test_user: MockUser, monkeypatch: pytest.MonkeyPatch
):
    from semantic_workbench_service.controller.conversation import ConversationTitleResponse

    mock_parsed_choice = Mock()
    mock_parsed_choice.message.parsed = ConversationTitleResponse(title="A sweet title")

    mock_parsed_completion = Mock()
    mock_parsed_completion.choices = [mock_parsed_choice]

    mock_client = Mock()
    mock_client.beta.chat.completions.parse = AsyncMock()
    mock_client.beta.chat.completions.parse.return_value = mock_parsed_completion

    mock_create_client = Mock(spec=openai_client.create_client)
    mock_create_client.return_value = AsyncContextManagerMock(mock_client)

    monkeypatch.setattr(openai_client, "create_client", mock_create_client)

    monkeypatch.setattr(semantic_workbench_service.settings.service, "azure_openai_endpoint", "https://something/")
    monkeypatch.setattr(semantic_workbench_service.settings.service, "azure_openai_deployment", "something")

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_conversation = workbench_model.NewConversation(metadata={"test": "value"})
        http_response = client.post("/conversations", json=new_conversation.model_dump(mode="json"))
        assert httpx.codes.is_success(http_response.status_code)

        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert conversation_response.title == "New Conversation"

        http_response = client.get(f"/conversations/{conversation_response.id}")
        assert httpx.codes.is_success(http_response.status_code)

        get_conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert get_conversation_response.title == new_conversation.title

        new_message = workbench_model.NewConversationMessage(content="hi")
        http_response = client.post(
            f"/conversations/{conversation_response.id}/messages", json=new_message.model_dump(mode="json")
        )
        assert httpx.codes.is_success(http_response.status_code)

        for _ in range(10):
            http_response = client.get(f"/conversations/{conversation_response.id}")
            assert httpx.codes.is_success(http_response.status_code)

            get_conversation_response = workbench_model.Conversation.model_validate(http_response.json())
            if get_conversation_response.title != "New Conversation":
                break
            time.sleep(0.1)

        get_conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert get_conversation_response.title == "A sweet title"


def test_create_update_conversation(workbench_service: FastAPI, test_user: MockUser):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_conversation = workbench_model.NewConversation(title="test-conversation", metadata={"test": "value"})
        http_response = client.post("/conversations", json=new_conversation.model_dump(mode="json"))
        assert httpx.codes.is_success(http_response.status_code)

        conversation_response = workbench_model.Conversation.model_validate(http_response.json())

        updated_title = f"new-title{uuid.uuid4()}"
        updated_metadata = {"test": uuid.uuid4().hex}

        http_response = client.patch(
            f"/conversations/{conversation_response.id}",
            json=workbench_model.UpdateConversation(title=updated_title, metadata=updated_metadata).model_dump(
                mode="json",
            ),
        )
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/conversations/{conversation_response.id}")
        assert httpx.codes.is_success(http_response.status_code)

        get_conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert get_conversation_response.title == updated_title
        assert exclude_system_keys(get_conversation_response.metadata) == updated_metadata


def test_create_assistant_add_to_conversation(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)

        assistant = workbench_model.Assistant.model_validate(http_response.json())

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)

        conversation = workbench_model.Conversation.model_validate(http_response.json())

        http_response = client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/assistants/{assistant.id}/conversations")
        assert httpx.codes.is_success(http_response.status_code)

        assistant_conversations = workbench_model.ConversationList.model_validate(http_response.json())
        assert len(assistant_conversations.conversations) == 1
        assert assistant_conversations.conversations[0].id == conversation.id


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_create_assistant_add_to_conversation_delete_assistant_retains_participant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="DELETE",
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)

        assistant = workbench_model.Assistant.model_validate(http_response.json())

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)

        conversation = workbench_model.Conversation.model_validate(http_response.json())

        http_response = client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/conversations/{conversation.id}/participants")
        assert httpx.codes.is_success(http_response.status_code)

        participants = workbench_model.ConversationParticipantList.model_validate(http_response.json())

        assert len(participants.participants) == 2
        assert {p.id for p in participants.participants} == {test_user.id, str(assistant.id)}

        assistant_participant = next(p for p in participants.participants if p.id == str(assistant.id))
        assert assistant_participant.name == assistant.name
        assert assistant_participant.image == assistant.image
        assert assistant_participant.active_participant is True
        assert assistant_participant.online is True

        # update assistant and verify that the participant attributes are updated
        http_response = client.patch(
            f"/assistants/{assistant.id}",
            json=workbench_model.UpdateAssistant(name="new-name", image="foo").model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)

        assistant = workbench_model.Assistant.model_validate(http_response.json())
        assert assistant.name == "new-name"
        assert assistant.image == "foo"

        http_response = client.get(f"/conversations/{conversation.id}/participants")
        assert httpx.codes.is_success(http_response.status_code)

        participants = workbench_model.ConversationParticipantList.model_validate(http_response.json())

        assert len(participants.participants) == 2
        assert {p.id for p in participants.participants} == {test_user.id, str(assistant.id)}

        assistant_participant = next(p for p in participants.participants if p.id == str(assistant.id))
        assert assistant_participant.name == assistant.name
        assert assistant_participant.image == assistant.image
        assert assistant_participant.active_participant is True
        assert assistant_participant.online is True

        # delete assistant and verify that the participant is still in the conversation
        http_response = client.delete(f"/assistants/{assistant.id}")
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/conversations/{conversation.id}/participants", params={"include_inactive": True})
        assert httpx.codes.is_success(http_response.status_code)

        participants = workbench_model.ConversationParticipantList.model_validate(http_response.json())

        assert len(participants.participants) == 2
        assert {p.id for p in participants.participants} == {test_user.id, str(assistant.id)}

        assistant_participant = next(p for p in participants.participants if p.id == str(assistant.id))
        assert assistant_participant.name == assistant.name
        assert assistant_participant.image == assistant.image
        assert assistant_participant.active_participant is False
        assert assistant_participant.online is False


def test_create_get_assistant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = http_response.json()
        logging.info("response: %s", assistant_response)
        assert "id" in assistant_response
        assistant_id = assistant_response["id"]

        http_response = client.get(f"/assistants/{assistant_id}")
        assert httpx.codes.is_success(http_response.status_code)
        assert http_response.json() == assistant_response

        http_response = client.get("/assistants")
        assert httpx.codes.is_success(http_response.status_code)
        assistants_response = http_response.json()
        assert "assistants" in assistants_response
        assert assistants_response["assistants"] == [assistant_response]


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_create_update_assistant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
    test_user_2: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
                metadata={"test": "value"},
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = http_response.json()
        logging.info("response: %s", assistant_response)
        assert "id" in assistant_response
        assistant_id = assistant_response["id"]

        updated_name = f"new-name{uuid.uuid4()}"
        updated_metadata = {"test": uuid.uuid4().hex}
        http_response = client.patch(
            f"/assistants/{assistant_id}",
            json=workbench_model.UpdateAssistant(name=updated_name, metadata=updated_metadata).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/assistants/{assistant_id}")
        assert httpx.codes.is_success(http_response.status_code)
        assistants_response = workbench_model.Assistant.model_validate(http_response.json())
        assert assistants_response.name == updated_name
        assert assistants_response.metadata == updated_metadata

        # ensure another user cannot update
        http_response = client.patch(
            f"/assistants/{assistant_id}",
            json=workbench_model.UpdateAssistant(name=updated_name, metadata=updated_metadata).model_dump(mode="json"),
            headers=test_user_2.authorization_headers,
        )
        assert httpx.codes.is_client_error(http_response.status_code)


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_create_delete_assistant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
    test_user_2: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="DELETE",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="DELETE",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = http_response.json()
        logging.info("response: %s", assistant_response)
        assert "id" in assistant_response
        assistant_id = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        payload = {"content": "hello"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        assert httpx.codes.is_success(http_response.status_code)

        # ensure another user cannot delete
        http_response = client.delete(f"/assistants/{assistant_id}", headers=test_user_2.authorization_headers)
        assert httpx.codes.is_client_error(http_response.status_code)

        http_response = client.delete(f"/assistants/{assistant_id}")
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/assistants/{assistant_id}")
        assert http_response.status_code == httpx.codes.NOT_FOUND


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_create_assistant_update_participant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        logging.info("response: %s", http_response.json())
        assistant_id = http_response.json()["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/conversations/{conversation_id}/participants")
        assert httpx.codes.is_success(http_response.status_code)
        logging.info("response: %s", http_response.json())
        participants_response = http_response.json()
        assert "participants" in participants_response
        participants = participants_response["participants"]
        assert len(participants) == 2

        expected_participant_ids = {test_user.id, assistant_id}
        participant_ids = {p["id"] for p in participants}
        assert participant_ids == expected_participant_ids

        http_response = client.get(f"/conversations/{conversation_id}/participants/{test_user.id}")
        assert httpx.codes.is_success(http_response.status_code)
        my_id_participant = http_response.json()

        http_response = client.get(f"/conversations/{conversation_id}/participants/me")
        assert httpx.codes.is_success(http_response.status_code)
        me_participant = http_response.json()

        assert my_id_participant == me_participant

        http_response = client.patch(f"/conversations/{conversation_id}/participants/me", json={"status": "testing"})
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/conversations/{conversation_id}/participants/me")
        assert httpx.codes.is_success(http_response.status_code)
        updated_me_participant = http_response.json()
        assert updated_me_participant["status"] == "testing"

        me_timestamp = datetime.datetime.fromisoformat(me_participant["status_updated_timestamp"])
        updated_timestamp = datetime.datetime.fromisoformat(updated_me_participant["status_updated_timestamp"])
        assert updated_timestamp > me_timestamp


@pytest.mark.parametrize("message_type", ["command", "log", "note", "notice"])
def test_create_conversation_send_nonchat_message(
    workbench_service: FastAPI,
    test_user: MockUser,
    message_type: str,
):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        # create a chat message that should not be returned
        message_content = "message of type chat"
        payload = {"message_type": "chat", "content_type": "text/plain", "content": message_content}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        assert httpx.codes.is_success(http_response.status_code)

        message_content = f"message of type {message_type}"
        payload = {"message_type": message_type, "content_type": "text/plain", "content": message_content}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"message_type": message_type})
        assert httpx.codes.is_success(http_response.status_code)
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 1
        message = messages[0]
        assert message["content"] == message_content
        assert message["sender"]["participant_id"] == test_user.id
        assert message["message_type"] == message_type


def test_create_conversation_send_user_message(workbench_service: FastAPI, test_user: MockUser):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation = workbench_model.Conversation.model_validate(http_response.json())
        conversation_id = conversation.id

        assert conversation.latest_message is None

        payload = {"content": "hello"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)
        message = workbench_model.ConversationMessage.model_validate(http_response.json())
        message_id = message.id
        assert message.has_debug_data is False

        http_response = client.get(f"/conversations/{conversation_id}/messages")
        assert httpx.codes.is_success(http_response.status_code)
        messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
        assert len(messages.messages) == 1
        message = messages.messages[0]
        assert message.content == "hello"
        assert message.sender.participant_id == test_user.id

        http_response = client.get(f"/conversations/{conversation_id}/messages/{message_id}")
        assert httpx.codes.is_success(http_response.status_code)
        message = workbench_model.ConversationMessage.model_validate(http_response.json())
        assert message.content == "hello"
        assert message.sender.participant_id == test_user.id

        # send another chat message, with debug
        payload = {
            "content": "hello again",
            "metadata": {"debug": {"key1": "value1"}},
            "debug_data": {"key2": "value2"},
        }
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)
        message = workbench_model.ConversationMessage.model_validate(http_response.json())
        message_two_id = message.id

        # debug should be stripped out
        assert message.metadata == {}
        assert message.has_debug_data is True

        http_response = client.get(f"/conversations/{conversation_id}/messages/{message_two_id}/debug_data")
        assert httpx.codes.is_success(http_response.status_code)
        message = workbench_model.ConversationMessageDebug.model_validate(http_response.json())

        assert message.debug_data == {"key1": "value1", "key2": "value2"}

        # send a log message
        payload = {"content": "hello again", "message_type": "log"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)
        message = workbench_model.ConversationMessage.model_validate(http_response.json())
        message_log_id = message.id

        # get all messages
        http_response = client.get(f"/conversations/{conversation_id}/messages")
        assert httpx.codes.is_success(http_response.status_code)
        messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
        assert len(messages.messages) == 3
        message = messages.messages[0]
        assert message.content == "hello"
        assert message.sender.participant_id == test_user.id
        assert message.id == message_id
        message = messages.messages[1]
        assert message.content == "hello again"
        assert message.sender.participant_id == test_user.id
        assert message.id == message_two_id
        message = messages.messages[2]
        assert message.content == "hello again"
        assert message.sender.participant_id == test_user.id
        assert message.id == message_log_id

        # limit messages
        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"limit": 1})
        assert httpx.codes.is_success(http_response.status_code)
        messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
        assert len(messages.messages) == 1
        message = messages.messages[0]
        assert message.id == message_log_id

        # get messages before
        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"before": str(message_two_id)})
        assert httpx.codes.is_success(http_response.status_code)
        messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
        assert len(messages.messages) == 1
        message = messages.messages[0]
        assert message.id == message_id

        # get messages after
        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"after": str(message_id)})
        assert httpx.codes.is_success(http_response.status_code)
        messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
        assert len(messages.messages) == 2
        message = messages.messages[0]
        assert message.id == message_two_id
        message = messages.messages[1]
        assert message.id == message_log_id

        # get messages by type
        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"message_type": "chat"})
        assert httpx.codes.is_success(http_response.status_code)
        messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
        assert len(messages.messages) == 2

        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"message_type": "log"})
        assert httpx.codes.is_success(http_response.status_code)
        messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
        assert len(messages.messages) == 1

        http_response = client.get(
            f"/conversations/{conversation_id}/messages",
            params={"message_type": ["chat", "log"]},
        )
        assert httpx.codes.is_success(http_response.status_code)
        messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
        assert len(messages.messages) == 3

        # check latest chat message in conversation (chat is default)
        http_response = client.get(f"/conversations/{conversation_id}")
        assert httpx.codes.is_success(http_response.status_code)
        conversation = workbench_model.Conversation.model_validate(http_response.json())
        assert conversation.latest_message is not None
        assert conversation.latest_message.id == message_two_id

        # check latest log message in conversation
        http_response = client.get(f"/conversations/{conversation_id}", params={"latest_message_type": ["log"]})
        assert httpx.codes.is_success(http_response.status_code)
        conversation = workbench_model.Conversation.model_validate(http_response.json())
        assert conversation.latest_message is not None
        assert conversation.latest_message.id == message_log_id


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_create_assistant_send_assistant_message(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        logging.info("response: %s", http_response.json())
        assistant_response = http_response.json()
        assistant_id = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        payload = {"content": "hello", "metadata": {"assistant_id": assistant_id, "generated_by": "test"}}
        assistant_headers = {
            **workbench_service_client.AssistantServiceRequestHeaders(
                assistant_service_id=registration.assistant_service_id,
                api_key=registration.api_key or "",
            ).to_headers(),
            **workbench_service_client.AssistantRequestHeaders(
                assistant_id=assistant_id,
            ).to_headers(),
        }
        http_response = client.post(
            f"/conversations/{conversation_id}/messages",
            json=payload,
            headers=assistant_headers,
        )
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/conversations/{conversation_id}/messages")
        assert httpx.codes.is_success(http_response.status_code)
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 1
        message = messages[0]
        assert message["content"] == "hello"
        assert message["sender"]["participant_id"] == assistant_id
        assert message["metadata"] == {"assistant_id": assistant_id, "generated_by": "test"}


def test_create_conversation_write_read_delete_file(
    workbench_service: FastAPI,
    test_user: MockUser,
):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.get(f"/conversations/{conversation_id}/files")
        assert httpx.codes.is_success(http_response.status_code)
        logging.info("response: %s", http_response.json())
        files = http_response.json()["files"]
        assert len(files) == 0

        # write 3 files
        payload = [
            ("files", ("test.txt", "hello world\n", "text/plain")),
            ("files", ("path1/path2/test.html", "<html><body></body></html>\n", "text/html")),
            ("files", ("path1/path2/test.bin", bytes(range(ord("a"), ord("f"))), "application/octet-stream")),
        ]
        http_response = client.put(
            f"/conversations/{conversation_id}/files",
            files=payload,
            # one of them has metadata
            data={"metadata": json.dumps({"path1/path2/test.bin": {"generated_by": "test"}})},
        )
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)
        files = http_response.json()["files"]
        assert [f["filename"] for f in files] == ["test.txt", "path1/path2/test.html", "path1/path2/test.bin"]
        assert files[2]["metadata"] == {"generated_by": "test"}

        # get the file listing
        http_response = client.get(f"/conversations/{conversation_id}/files")
        assert httpx.codes.is_success(http_response.status_code)
        logging.info("response: %s", http_response.json())
        files = http_response.json()["files"]
        assert [f["filename"] for f in files] == ["path1/path2/test.bin", "path1/path2/test.html", "test.txt"]

        # get files by prefix
        http_response = client.get(f"/conversations/{conversation_id}/files", params={"prefix": "path1/path2"})
        assert httpx.codes.is_success(http_response.status_code)
        logging.info("response: %s", http_response.json())
        files = http_response.json()["files"]
        assert [f["filename"] for f in files] == ["path1/path2/test.bin", "path1/path2/test.html"]

        # download a file
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt")
        assert httpx.codes.is_success(http_response.status_code)
        assert http_response.text == "hello world\n"

        # download another file
        http_response = client.get(f"/conversations/{conversation_id}/files/path1/path2/test.html")
        assert httpx.codes.is_success(http_response.status_code)
        assert http_response.text == "<html><body></body></html>\n"

        # re-write test.txt
        payload = [
            ("files", ("test.txt", "hello again\n", "text/plain")),
        ]
        http_response = client.put(f"/conversations/{conversation_id}/files", files=payload)
        assert httpx.codes.is_success(http_response.status_code)

        # get all versions
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt/versions")
        assert httpx.codes.is_success(http_response.status_code)
        file_versions = http_response.json()
        assert len(file_versions["versions"]) == 2
        assert file_versions["versions"][0]["version"] == 1
        assert file_versions["versions"][1]["version"] == 2

        # get a single version
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt/versions", params={"version": 1})
        assert httpx.codes.is_success(http_response.status_code)
        file_versions = http_response.json()
        assert len(file_versions["versions"]) == 1
        assert file_versions["versions"][0]["version"] == 1

        # get the file content for the current version
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt")
        assert httpx.codes.is_success(http_response.status_code)
        assert http_response.text == "hello again\n"

        # get the file content for the prior version
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt", params={"version": 1})
        assert httpx.codes.is_success(http_response.status_code)
        assert http_response.text == "hello world\n"

        # delete a file
        http_response = client.delete(f"/conversations/{conversation_id}/files/test.txt")
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt")
        assert http_response.status_code == httpx.codes.NOT_FOUND

        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt/versions")
        assert http_response.status_code == httpx.codes.NOT_FOUND


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_create_assistant_export_import_data(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/export-data"),
        method="GET",
        json={"data": "assistant test export data"},
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/export-data"),
        method="GET",
        json={"data": "conversation test export data"},
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = http_response.json()
        assistant_id = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        payload = {"content": "hello"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get(f"/assistants/{assistant_id}/export")
        assert httpx.codes.is_success(http_response.status_code)

        assert http_response.headers["content-type"] == "application/zip"
        assert "content-length" in http_response.headers
        assert int(http_response.headers["content-length"]) > 0

        logging.info("response: %s", http_response.content)

        file_io = io.BytesIO(http_response.content)

        for import_number in range(1, 3):
            http_response = client.post("/conversations/import", files={"from_export": file_io})
            logging.info("response: %s", http_response.json())
            assert httpx.codes.is_success(http_response.status_code)

            http_response = client.get("/assistants")
            logging.info("response: %s", http_response.json())
            assert httpx.codes.is_success(http_response.status_code)
            assistants_response = http_response.json()
            assert "assistants" in assistants_response
            assistant_count = len(assistants_response["assistants"])
            assert assistant_count == 1

            for index, assistant in enumerate(assistants_response["assistants"]):
                assert assistant["name"] == "test-assistant"


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_create_assistant_conversations_export_import_conversations(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
) -> None:
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/export-data"),
        method="GET",
        json={"data": "assistant test export data"},
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/export-data"),
        method="GET",
        json={"data": "conversation test export data"},
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant-1",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = http_response.json()
        assistant_id_1 = assistant_response["id"]

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant-2",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = http_response.json()
        assistant_id_2 = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation-1"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = http_response.json()
        conversation_id_1 = conversation_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation-2"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = http_response.json()
        conversation_id_2 = conversation_response["id"]

        # both assistants are in conversation-1
        http_response = client.put(f"/conversations/{conversation_id_1}/participants/{assistant_id_1}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.put(f"/conversations/{conversation_id_1}/participants/{assistant_id_2}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        # only assistant-1 is in conversation-2
        http_response = client.put(f"/conversations/{conversation_id_2}/participants/{assistant_id_1}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        payload = {"content": "hello", "debug_data": {"key": "value"}}
        http_response = client.post(f"/conversations/{conversation_id_1}/messages", json=payload)
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.post(f"/conversations/{conversation_id_2}/messages", json=payload)
        assert httpx.codes.is_success(http_response.status_code)

        # export both conversations
        http_response = client.get("/conversations/export", params={"id": [conversation_id_1, conversation_id_2]})
        assert httpx.codes.is_success(http_response.status_code)

        assert http_response.headers["content-type"] == "application/zip"
        assert "content-length" in http_response.headers
        assert int(http_response.headers["content-length"]) > 0

        logging.info("response: %s", http_response.content)

        file_io = io.BytesIO(http_response.content)

        for _ in range(1, 3):
            http_response = client.post("/conversations/import", files={"from_export": file_io})
            logging.info("response: %s", http_response.json())
            assert httpx.codes.is_success(http_response.status_code)

            http_response = client.get("/assistants")
            logging.info("response: %s", http_response.json())
            assert httpx.codes.is_success(http_response.status_code)
            assistants_response = http_response.json()
            assert "assistants" in assistants_response
            assistant_count = len(assistants_response["assistants"])
            assert assistant_count == 2

        http_response = client.get("/assistants")
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)

        assistants = workbench_model.AssistantList.model_validate(http_response.json())

        assistants.assistants = sorted(assistants.assistants, key=lambda a: a.name)
        assert len(assistants.assistants) == 2
        assert assistants.assistants[0].name == "test-assistant-1"
        assert assistants.assistants[1].name == "test-assistant-2"

        http_response = client.get("/conversations")
        logging.info("response: %s", http_response.json())
        assert httpx.codes.is_success(http_response.status_code)

        conversations = workbench_model.ConversationList.model_validate(http_response.json())
        conversations.conversations = sorted(conversations.conversations, key=lambda c: c.title)

        assert conversations.conversations[0].title == "test-conversation-1"
        assert conversations.conversations[1].title == "test-conversation-1 (1)"
        assert conversations.conversations[2].title == "test-conversation-1 (2)"
        assert conversations.conversations[3].title == "test-conversation-2"
        assert conversations.conversations[4].title == "test-conversation-2 (1)"
        assert conversations.conversations[5].title == "test-conversation-2 (2)"

        for conversation in conversations.conversations:
            http_response = client.get(f"/conversations/{conversation.id}/messages")
            assert httpx.codes.is_success(http_response.status_code)

            messages = workbench_model.ConversationMessageList.model_validate(http_response.json())
            assert len(messages.messages) == 1

            message = messages.messages[0]
            assert message.content == "hello"
            assert message.sender.participant_id == test_user.id
            assert message.has_debug_data is True

            http_response = client.get(f"/conversations/{conversation.id}/messages/{message.id}/debug_data")
            assert httpx.codes.is_success(http_response.status_code)
            message_debug = workbench_model.ConversationMessageDebug.model_validate(http_response.json())
            assert message_debug.debug_data == {"key": "value"}


def test_export_import_conversations_with_files(
    workbench_service: FastAPI,
    test_user: MockUser,
) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation-1"})
        assert httpx.codes.is_success(http_response.status_code)

        conversation_1 = workbench_model.Conversation.model_validate(http_response.json())

        http_response = client.post("/conversations", json={"title": "test-conversation-2"})
        assert httpx.codes.is_success(http_response.status_code)

        conversation_2 = workbench_model.Conversation.model_validate(http_response.json())

        for conversation in [conversation_1, conversation_2]:
            payload = [
                ("files", ("test.txt", "hello world\n", "text/plain")),
                ("files", ("path1/path2/test.html", "<html><body></body></html>\n", "text/html")),
                ("files", ("path1/path2/test.bin", bytes(range(ord("a"), ord("f"))), "application/octet-stream")),
            ]
            http_response = client.put(f"/conversations/{conversation.id}/files", files=payload)
            assert httpx.codes.is_success(http_response.status_code)

            file_list = workbench_model.FileList.model_validate(http_response.json())
            assert len(file_list.files) == 3

        http_response = client.get(
            "/conversations/export", params={"id": [str(conversation_1.id), str(conversation_2.id)]}
        )
        assert httpx.codes.is_success(http_response.status_code)

        exported_data = io.BytesIO(http_response.content)

        for _ in range(1, 2):
            http_response = client.post("/conversations/import", files={"from_export": exported_data})
            assert httpx.codes.is_success(http_response.status_code)

            import_result = workbench_model.ConversationImportResult.model_validate(http_response.json())
            assert len(import_result.conversation_ids) == 2

            for conversation_id in import_result.conversation_ids:
                http_response = client.get(f"/conversations/{conversation_id}/files")
                assert httpx.codes.is_success(http_response.status_code)

                file_list = workbench_model.FileList.model_validate(http_response.json())
                assert len(file_list.files) == 3

                for file in file_list.files:
                    http_response = client.get(f"/conversations/{conversation_id}/files/{file.filename}")
                    assert httpx.codes.is_success(http_response.status_code)

                    match file.filename:
                        case "test.txt":
                            assert http_response.text == "hello world\n"
                        case "path1/path2/test.html":
                            assert http_response.text == "<html><body></body></html>\n"
                        case "path1/path2/test.bin":
                            assert http_response.content == bytes(range(ord("a"), ord("f")))
                        case _:
                            pytest.fail(f"unexpected file: {file.filename}")


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_create_conversations_get_participants(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation-1"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        conversation_id_1 = conversation_response.id

        http_response = client.post("/conversations", json={"title": "test-conversation-2"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        conversation_id_2 = conversation_response.id

        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant-1",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = workbench_model.Assistant.model_validate(http_response.json())
        assistant_id_1 = assistant_response.id

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant-2",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = workbench_model.Assistant.model_validate(http_response.json())
        assistant_id_2 = assistant_response.id

        # both assistants are in conversation-1
        http_response = client.put(f"/conversations/{conversation_id_1}/participants/{assistant_id_1}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.put(f"/conversations/{conversation_id_1}/participants/{assistant_id_2}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        # only assistant-1 is in conversation-2
        http_response = client.put(f"/conversations/{conversation_id_2}/participants/{assistant_id_1}", json={})
        assert httpx.codes.is_success(http_response.status_code)

        for conversation_id, participant_ids in {
            conversation_id_1: {str(assistant_id_1), str(assistant_id_2), test_user.id},
            conversation_id_2: {str(assistant_id_1), test_user.id},
        }.items():
            http_response = client.get(f"/conversations/{conversation_id}/participants")
            assert httpx.codes.is_success(http_response.status_code)
            participants_response = workbench_model.ConversationParticipantList.model_validate(http_response.json())

            assert {p.id for p in participants_response.participants} == participant_ids

        for assistant_id, conversation_ids in {
            assistant_id_1: {conversation_id_1, conversation_id_2},
            assistant_id_2: {conversation_id_1},
        }.items():
            http_response = client.get(f"/assistants/{assistant_id}/conversations")
            assert httpx.codes.is_success(http_response.status_code)
            conversations_response = workbench_model.ConversationList.model_validate(http_response.json())

            assert {c.id for c in conversations_response.conversations} == conversation_ids


@pytest.mark.parametrize(
    "url_template",
    [
        "/conversations/{conversation_id}",
        "/conversations/{conversation_id}/messages",
        "/conversations/{conversation_id}/participants",
    ],
)
def test_conversation_not_visible_to_non_participants(
    workbench_service: FastAPI,
    test_user: MockUser,
    test_user_2: MockUser,
    httpx_mock: HTTPXMock,
    url_template: str,
):
    httpx_mock.add_response(
        url="http://testassistantservice/",
        method="GET",
        json=api_model.ServiceInfoModel(assistant_service_id="", name="", templates=[], metadata={}).model_dump(
            mode="json"
        ),
    )
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation"})
        assert httpx.codes.is_success(http_response.status_code)
        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        conversation_id = conversation_response.id

        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        assistant_response = workbench_model.Assistant.model_validate(http_response.json())

        # ensure user 2 cannot make get request
        http_response = client.get(
            url_template.format(conversation_id=conversation_id),
            headers=test_user_2.authorization_headers,
        )
        assert http_response.status_code == httpx.codes.NOT_FOUND

        # ensure assistant request always returns 404
        assistant_headers = {
            **workbench_service_client.AssistantServiceRequestHeaders(
                assistant_service_id=registration.assistant_service_id,
                api_key=registration.api_key or "",
            ).to_headers(),
            **workbench_service_client.AssistantRequestHeaders(
                assistant_id=assistant_response.id,
            ).to_headers(),
        }
        http_response = client.get(url_template.format(conversation_id=conversation_id), headers=assistant_headers)
        assert http_response.status_code == httpx.codes.NOT_FOUND


def test_create_assistant_service_registration(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-name",
            description="test description",
        )

        http_response = client.post(
            "/assistant-service-registrations",
            json=new_assistant_service.model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)

        created_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert created_assistant_service.name == new_assistant_service.name
        assert created_assistant_service.description == new_assistant_service.description
        assert created_assistant_service.created_by_user_id == test_user.id
        assert created_assistant_service.api_key is not None


def test_create_get_assistant_service_registration(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-name",
            description="test description",
        )

        http_response = client.post(
            "/assistant-service-registrations",
            json=new_assistant_service.model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)

        # get single registration
        http_response = client.get(f"/assistant-service-registrations/{new_assistant_service.assistant_service_id}")
        assert httpx.codes.is_success(http_response.status_code)

        assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert assistant_service.name == new_assistant_service.name
        assert assistant_service.description == new_assistant_service.description
        assert assistant_service.created_by_user_id == test_user.id
        # get on single registration returns a mask API key
        assert assistant_service.api_key is not None
        assert assistant_service.api_key.endswith("*" * 10)

        # get all registrations
        http_response = client.get("/assistant-service-registrations")
        assert httpx.codes.is_success(http_response.status_code)

        retrieved_assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(
            http_response.json(),
        )

        assert len(retrieved_assistant_services.assistant_service_registrations) == 1

        assistant_service = retrieved_assistant_services.assistant_service_registrations[0]
        assert assistant_service.name == new_assistant_service.name
        assert assistant_service.description == new_assistant_service.description
        assert assistant_service.created_by_user_id == test_user.id
        assert assistant_service.api_key is None

        # get registrations owned by user
        http_response = client.get("/assistant-service-registrations", params={"owner_id": "me"})
        assert httpx.codes.is_success(http_response.status_code)

        retrieved_assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(
            http_response.json(),
        )

        assert len(retrieved_assistant_services.assistant_service_registrations) == 1

        assistant_service = retrieved_assistant_services.assistant_service_registrations[0]
        assert assistant_service.name == new_assistant_service.name
        assert assistant_service.description == new_assistant_service.description
        assert assistant_service.created_by_user_id == test_user.id
        assert assistant_service.api_key is None


def test_create_update_assistant_service_registration(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-nam",
            description="test description",
        )
        http_response = client.post(
            "/assistant-service-registrations",
            json=new_assistant_service.model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        update_assistant_service = workbench_model.UpdateAssistantServiceRegistration(
            name="updated-assistant-service",
            description="updated description",
        )
        http_response = client.patch(
            f"/assistant-service-registrations/{assistant_service.assistant_service_id}",
            json=update_assistant_service.model_dump(mode="json", exclude_unset=True),
        )
        assert httpx.codes.is_success(http_response.status_code)

        updated_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert updated_assistant_service.name == update_assistant_service.name
        assert updated_assistant_service.description == update_assistant_service.description
        assert updated_assistant_service.api_key is None


def test_create_assistant_service_registration_reset_api_key(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-name",
            description="test description",
        )

        http_response = client.post(
            "/assistant-service-registrations",
            json=new_assistant_service.model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)

        created_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert created_assistant_service.api_key is not None

        http_response = client.post(
            f"/assistant-service-registrations/{created_assistant_service.assistant_service_id}/api-key",
        )
        assert httpx.codes.is_success(http_response.status_code)

        reset_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert reset_assistant_service.api_key is not None
        # NOTE: the api key will not change because the test ApiKeyStore is used


def test_create_delete_assistant_service_registration(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-name",
            description="test description",
        )

        http_response = client.post(
            "/assistant-service-registrations",
            json=new_assistant_service.model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)

        created_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        http_response = client.delete(
            f"/assistant-service-registrations/{created_assistant_service.assistant_service_id}",
        )
        assert httpx.codes.is_success(http_response.status_code)

        http_response = client.get("/assistant-service-registrations")
        assert httpx.codes.is_success(http_response.status_code)

        retrieved_assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(
            http_response.json(),
        )

        assert len(retrieved_assistant_services.assistant_service_registrations) == 0


async def test_create_update_assistant_service_registration_url(
    workbench_service: FastAPI,
    test_user: MockUser,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # force continuous checks for assistants going offline
    monkeypatch.setattr(
        semantic_workbench_service.settings.service,
        "assistant_service_online_check_interval_seconds",
        0.1,
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-nam",
            description="test description",
        )
        http_response = client.post(
            "/assistant-service-registrations",
            json=new_assistant_service.model_dump(mode="json"),
        )
        assert httpx.codes.is_success(http_response.status_code)
        assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        update_assistant_service = workbench_model.UpdateAssistantServiceRegistrationUrl(
            name="updated-assistant-service",
            description="updated description",
            url=HttpUrl("https://example.com"),
            online_expires_in_seconds=0,
        )
        http_response = client.put(
            f"/assistant-service-registrations/{assistant_service.assistant_service_id}",
            json=update_assistant_service.model_dump(mode="json", exclude_unset=True),
            headers=workbench_service_client.AssistantServiceRequestHeaders(
                assistant_service_id=assistant_service.assistant_service_id,
                api_key=assistant_service.api_key or "",
            ).to_headers(),
        )
        assert httpx.codes.is_success(http_response.status_code)

        updated_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert updated_assistant_service.api_key is None
        assert updated_assistant_service.assistant_service_url == str(update_assistant_service.url)
        assert updated_assistant_service.assistant_service_online is True

        # give time for the assistant service online check to run
        await asyncio.sleep(1.0)

        # verify that when the url expires, the assistant service is reported as offline
        http_response = client.get(f"/assistant-service-registrations/{assistant_service.assistant_service_id}")
        assert httpx.codes.is_success(http_response.status_code)
        retrieved_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert retrieved_assistant_service.assistant_service_online is False


@pytest.mark.parametrize(
    ("permission"),
    [
        workbench_model.ConversationPermission.read,
        workbench_model.ConversationPermission.read_write,
    ],
)
async def test_create_redeem_delete_conversation_share(
    workbench_service: FastAPI,
    test_user: MockUser,
    test_user_2: MockUser,
    permission: workbench_model.ConversationPermission,
) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_conversation = workbench_model.NewConversation(title="test-conversation")

        http_response = client.post("/conversations", json=new_conversation.model_dump(mode="json"))
        assert httpx.codes.is_success(http_response.status_code)

        created_conversation = workbench_model.Conversation.model_validate(http_response.json())

        new_conversation_share = workbench_model.NewConversationShare(
            conversation_id=created_conversation.id,
            label="share",
            conversation_permission=permission,
        )

        http_response = client.post("/conversation-shares", json=new_conversation_share.model_dump(mode="json"))
        assert httpx.codes.is_success(http_response.status_code)

        created_conversation_share = workbench_model.ConversationShare.model_validate(http_response.json())

        assert created_conversation_share.conversation_id == created_conversation.id
        assert created_conversation_share.conversation_permission == permission

        http_response = client.get(f"/conversation-shares/{created_conversation_share.id}")
        assert httpx.codes.is_success(http_response.status_code)

        retrieved_conversation_share = workbench_model.ConversationShare.model_validate(http_response.json())

        assert retrieved_conversation_share == created_conversation_share

        http_response = client.get("/conversation-shares")
        assert httpx.codes.is_success(http_response.status_code)

        retrieved_conversation_shares = workbench_model.ConversationShareList.model_validate(http_response.json())
        assert retrieved_conversation_shares.conversation_shares == [created_conversation_share]

        # redeem the conversation share with user-2
        http_response = client.post(
            f"/conversation-shares/{created_conversation_share.id}/redemptions",
            headers=test_user_2.authorization_headers,
        )
        assert httpx.codes.is_success(http_response.status_code)

        redemption = workbench_model.ConversationShareRedemption.model_validate(http_response.json())
        assert redemption.redeemed_by_user.id == test_user_2.id
        assert redemption.conversation_permission == permission

        # ensure user-2 can retrieve the conversation
        http_response = client.get(
            f"/conversations/{created_conversation.id}", headers=test_user_2.authorization_headers
        )
        assert httpx.codes.is_success(http_response.status_code)

        retrieved_conversation = workbench_model.Conversation.model_validate(http_response.json())
        assert retrieved_conversation.id == created_conversation.id

        # ensure user-2 can retrieve their participant
        http_response = client.get(
            f"/conversations/{created_conversation.id}/participants/me", headers=test_user_2.authorization_headers
        )
        participant = workbench_model.ConversationParticipant.model_validate(http_response.json())
        assert participant.role == workbench_model.ParticipantRole.user
        assert participant.conversation_id == created_conversation.id
        assert participant.active_participant is True
        assert participant.conversation_permission == permission

        # delete the conversation share
        http_response = client.delete(f"/conversation-shares/{created_conversation_share.id}")
        assert httpx.codes.is_success(http_response.status_code)

        # ensure user-2 can still retrieve the conversation
        http_response = client.get(
            f"/conversations/{created_conversation.id}", headers=test_user_2.authorization_headers
        )
        assert httpx.codes.is_success(http_response.status_code)

        # ensure user 2 can no longer redeem the conversation share
        http_response = client.post(
            "/conversation-shares/redeem",
            headers=test_user_2.authorization_headers,
        )
        assert httpx.codes.is_client_error(http_response.status_code)


=== File: workbench-service/tests/types.py ===
from jose import jwt


class MockUser:
    tenant_id: str
    object_id: str
    name: str

    app_id: str = "test-app-id"
    token_algo: str = "HS256"

    def __init__(self, tenant_id: str, object_id: str, name: str):
        self.tenant_id = tenant_id
        self.object_id = object_id
        self.name = name

    @property
    def id(self) -> str:
        return f"{self.tenant_id}.{self.object_id}"

    @property
    def jwt_token(self) -> str:
        return jwt.encode(
            claims={
                "tid": self.tenant_id,
                "oid": self.object_id,
                "name": self.name,
                "appid": self.app_id,
            },
            key="",
            algorithm=self.token_algo,
        )

    @property
    def authorization_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.jwt_token}"}


