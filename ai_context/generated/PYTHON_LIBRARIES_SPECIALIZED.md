# libraries/python/assistant-drive | libraries/python/guided-conversation

[collect-files]

**Search:** ['libraries/python/assistant-drive', 'libraries/python/guided-conversation']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output']
**Include:** ['pyproject.toml', 'README.md']
**Date:** 5/29/2025, 11:45:28 AM
**Files:** 31

=== File: README.md ===
# Semantic Workbench

Semantic Workbench is a versatile tool designed to help prototype intelligent assistants quickly.
It supports the creation of new assistants or the integration of existing ones, all within a
cohesive interface. The workbench provides a user-friendly UI for creating conversations with one
or more assistants, configuring settings, and exposing various behaviors.

The Semantic Workbench is composed of three main components:

- [Workbench Service](workbench-service/README.md) (Python): The backend service that
  handles core functionalities.
- [Workbench App](workbench-app/README.md) (React/Typescript): The frontend web user
  interface for interacting with workbench and assistants.
- [Assistant Services](examples) (Python, C#, etc.): any number of assistant services that implement the service protocols/APIs,
  developed using any framework and programming language of your choice.

Designed to be agnostic of any agent framework, language, or platform, the Semantic Workbench
facilitates experimentation, development, testing, and measurement of agent behaviors and workflows.
Assistants integrate with the workbench via a RESTful API, allowing for flexibility and broad applicability in various development environments.

![Semantic Workbench architecture](https://raw.githubusercontent.com/microsoft/semanticworkbench/main/docs/images/architecture-animation.gif)

# Workbench interface examples

![Configured dashboard example](docs/images/dashboard_configured_view.png)

![Prospector Assistant example](docs/images/prospector_example.png)

![Message debug inspection](docs/images/message_inspection.png)

![Mermaid graph example](examples/dotnet/dotnet-02-message-types-demo/docs/mermaid.png)

![ABC music example](examples/dotnet/dotnet-02-message-types-demo/docs/abc.png)

# Quick start (Recommended) - GitHub Codespaces for turn-key development environment

GitHub Codespaces provides a cloud-based development environment for your repository. It allows you to develop, build, and test your code
in a consistent environment, without needing to install dependencies or configure your local machine. It works with any system with a web
browser and internet connection, including Windows, MacOS, Linux, Chromebooks, tablets, and mobile devices.

See the [GitHub Codespaces / devcontainer README](.devcontainer/README.md) for more information on how to set up and use GitHub Codespaces
with Semantic Workbench.

## Local development environment

See the [setup guide](docs/SETUP_DEV_ENVIRONMENT.md) on how to configure your dev environment. Or if you have Docker installed you can use dev containers with VS Code which will function similarly to Codespaces.

## Using VS Code

Codespaces will is configured to use `semantic-workbench.code-workspace`, if you are working locally that is recommended over opening the repo root. This ensures that all project configurations, such as tools, formatters, and linters, are correctly applied in VS Code. This avoids issues like incorrect error reporting and non-functional tools.

Workspace files allow us to manage multiple projects within a monorepo more effectively. Each project can use its own virtual environment (venv), maintaining isolation and avoiding dependency conflicts. Multi-root workspaces (\*.code-workspace files) can point to multiple projects, each configured with its own Python interpreter, ensuring seamless functionality of Python tools and extensions.

### Start the app and service

- Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `semantic-workbench` to start the project
- Open your browser and navigate to `https://127.0.0.1:4000`
  - You may receive a warning about the app not being secure; click `Advanced` and `Proceed to localhost` to continue
- You can now interact with the app and service in the browser

### Start an assistant service:

- Launch an example an [example](examples/) assistant service:
  - No llm api keys needed
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `examples: python-01-echo-bot` to start the example assistant that echos your messages. This is a good base to understand the basics of building your own assistant.
  - Bring your own llm api keys
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `examples: python-02-simple-chatbot` to start the example chatbot assistant. Either set your keys in your .env file or after creating the assistant as described below, select it and provide the keys in the configuration page.

## Open the Workbench and create an Assistant

Open the app in your browser at [`https://localhost:4000`](https://localhost:4000). When you first log into the Semantic Workbench, follow these steps to get started:

1. **Create an Assistant**: On the dashboard, click the `New Assistant` button. Select a template from the available assistant services, provide a name, and click `Save`.

2. **Start a Conversation**: On the dashboard, click the `New Conversation` button. Provide a title for the conversation and click `Save`.

3. **Add the Assistant**: In the conversation window, click the conversation canvas icon and add your assistant to the conversation from the conversation canvas. Now you can converse with your assistant using the message box at the bottom of the conversation window.

   ![Open Conversation Canvas](docs/images/conversation_canvas_open.png)

   ![Open Canvas](docs/images/open_conversation_canvas.png)

Expected: You get a response from your assistant!

Note that the workbench provides capabilities that not all examples use, for example providing attachments. See the [Semantic Workbench](docs/WORKBENCH_APP.md) for more details.

# Developing your own assistants

To develop new assistants and connect existing ones, see the [Assistant Development Guide](docs/ASSISTANT_DEVELOPMENT_GUIDE.md) or any check out one of the [examples](examples).

- [Python example 1](examples/python/python-01-echo-bot/README.md): a simple assistant echoing text back.
- [Python example 2](examples/python/python-02-simple-chatbot/README.md): a simple chatbot implementing metaprompt guardrails and content moderation.
- [Python example 3](examples/python/python-03-multimodel-chatbot/README.md): an extension of the simple chatbot that supports configuration against additional llms.
- [.NET example 1](examples/dotnet/dotnet-01-echo-bot/README.md): a simple agent with echo and support for a basic `/say` command.
- [.NET example 2](examples/dotnet/dotnet-02-message-types-demo/README.md): a simple assistants showcasing Azure AI Content Safety integration and some workbench features like Mermaid graphs.
- [.NET example 3](examples/dotnet/dotnet-03-simple-chatbot/README.md): a functional chatbot implementing metaprompt guardrails and content moderation.

## Starting the workbench from the command line

- Run the script `tools\run-workbench-chatbot.sh` or `tools\run-workbench-chatbot.ps` which does the following:
  - Starts the backend service, see [here for instructions](workbench-service/README.md).
  - Starts the frontend app, see [here for instructions](workbench-app/README.md).
  - Starts the [Python chatbot example](examples/python/python-02-simple-chatbot/README.md)

## Refreshing Dev Environment

- Use the `tools\reset-service-data.sh` or `tools\reset-service-data.sh` script to reset all service data. You can also delete `~/workbench-service/.data` or specific files if you know which one(s).
- From repo root, run `make clean install`.
  - This will perform a `git clean` and run installs in all sub-directories
- Or a faster option if you just want to install semantic workbench related stuff:
  - From repo root, run `make clean`
  - From `~/workbench-app`, run `make install`
  - From `~/workbench-service`, run `make install`

# Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com>.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

Please see the detailed [contributing guide](CONTRIBUTING.md) for more information on how you can get involved.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

# Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.


=== File: libraries/python/assistant-drive/.gitignore ===
__pycache__
.pytest_cache
*.egg*
.data
.venv
venv
.env

poetry.lock


=== File: libraries/python/assistant-drive/.vscode/extensions.json ===
{
  "recommendations": [
    "aarontamasfe.even-better-toml",
    "charliermarsh.ruff",
    "ms-python.python"
  ]
}


=== File: libraries/python/assistant-drive/.vscode/settings.json ===
{
  "editor.bracketPairColorization.enabled": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": "always",
    "source.organizeImports": "always"
  },
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnPaste": true,
  "editor.formatOnSave": true,
  "editor.formatOnType": true,
  "editor.guides.bracketPairs": "active",
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "flake8.ignorePatterns": ["**/*.py"], // disable flake8 in favor of ruff
  "jupyter.debugJustMyCode": false,
  "python.analysis.autoFormatStrings": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.exclude": [
    "**/.venv/**",
    "**/.data/**",
    "**/__pycache__/**"
  ],
  "python.analysis.fixAll": ["source.unusedImports"],
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.typeCheckingMode": "standard",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "python.testing.cwd": "${workspaceFolder}",
  "python.testing.pytestArgs": ["--color", "yes"],
  "python.testing.pytestEnabled": true,
  "search.exclude": {
    "**/.venv": true,
    "**/data": true
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
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
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "dotenv",
    "httpx",
    "openai",
    "pydantic",
    "pypdf",
    "runtimes",
    "subdrive",
    "tiktoken"
  ]
}


=== File: libraries/python/assistant-drive/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/assistant-drive/README.md ===
# Assistant Drive

These are file storage capabilities.

=== File: libraries/python/assistant-drive/assistant_drive/__init__.py ===
from .drive import Drive, DriveConfig, IfDriveFileExistsBehavior

__all__ = [
    "Drive",
    "DriveConfig",
    "IfDriveFileExistsBehavior",
]


=== File: libraries/python/assistant-drive/assistant_drive/drive.py ===
import io
import json
import pathlib
from contextlib import contextmanager
from datetime import datetime
from enum import StrEnum
from os import PathLike
from typing import Any, BinaryIO, Iterator

from pydantic import BaseModel


class IfDriveFileExistsBehavior(StrEnum):
    FAIL = "fail"
    OVERWRITE = "overwrite"
    AUTO_RENAME = "auto_rename"


class DriveConfig(BaseModel):
    root: str | PathLike
    default_if_exists_behavior: IfDriveFileExistsBehavior = IfDriveFileExistsBehavior.OVERWRITE


class FileMetadata:
    def __init__(self, filename: str, dir: str | None, content_type: str, size: int) -> None:
        self.filename = filename
        self.dir = dir
        self.content_type = content_type
        self.size = size
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "dir": self.dir,
            "content_type": self.content_type,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "FileMetadata":
        metadata = FileMetadata(
            filename=data["filename"],
            dir=data["dir"],
            content_type=data["content_type"],
            size=data["size"],
        )
        metadata.created_at = datetime.fromisoformat(data["created_at"])
        metadata.updated_at = datetime.fromisoformat(data["updated_at"])
        return metadata


class Drive:
    def __init__(self, config: DriveConfig) -> None:
        self.root_path = pathlib.Path(config.root)
        self.default_if_exists_behavior = config.default_if_exists_behavior

    def _path_for(self, filename: str | None = None, dir: str | None = None) -> pathlib.Path:
        """Return the actual path for a dir/file combo, creating the dir as needed."""
        namespace_path = self.root_path / (dir or "")
        namespace_path.mkdir(parents=True, exist_ok=True)
        if filename is None:
            return namespace_path
        return namespace_path / filename

    def _metadata_dir_for(self, filename: str, dir: str | None = None) -> pathlib.Path:
        """Return the metadata directory path for a file."""
        file_path = self._path_for(filename, dir)
        return file_path.parent / (file_path.name + ".metadata")

    def _metadata_file_path(self, filename: str, dir: str | None = None) -> pathlib.Path:
        """Return the path to the metadata.json file for a given file."""
        metadata_dir = self._metadata_dir_for(filename, dir)
        return metadata_dir / "metadata.json"

    def _write_metadata(self, metadata: FileMetadata) -> None:
        """Write metadata to the appropriate metadata directory."""
        metadata_dir = self._metadata_dir_for(metadata.filename, metadata.dir)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = metadata_dir / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

    def _read_metadata(self, filename: str, dir: str | None = None) -> FileMetadata:
        """Read metadata from the metadata directory."""
        metadata_file = self._metadata_file_path(filename, dir)
        if not metadata_file.exists():
            raise FileNotFoundError(f"No metadata found for {filename}")

        with open(metadata_file, "r") as f:
            data = json.load(f)
            return FileMetadata.from_dict(data)

    #########################
    # Drive methods.
    #########################

    def subdrive(self, dir: str | pathlib.Path) -> "Drive":
        """Create a new Drive instance for a subdirectory of this drive.

        Args:
            dir: The subdirectory path relative to this drive's root

        Returns:
            A new Drive instance with its root at the specified subdirectory
        """
        new_root = self.root_path / dir
        config = DriveConfig(root=new_root, default_if_exists_behavior=self.default_if_exists_behavior)
        return Drive(config)

    def delete_drive(self) -> None:
        """Delete the entire drive directory and all its contents.

        This is a destructive operation that will delete all files and metadata
        in the drive. Use with caution.

        Raises:
            ValueError: If the drive's root path is a system directory (e.g., '/' or '/home')
        """
        # Basic safety check to prevent accidental deletion of system directories
        root_path = self.root_path.absolute()
        suspicious_paths = [
            pathlib.Path("/"),
            pathlib.Path("/home"),
            pathlib.Path("/usr"),
            pathlib.Path("/etc"),
            pathlib.Path("/var"),
            pathlib.Path("/tmp"),
            pathlib.Path("C:\\"),
            pathlib.Path("C:"),
            pathlib.Path("/Users"),
        ]
        if root_path in suspicious_paths:
            raise ValueError(f"Refusing to delete system directory: {root_path}")

        if self.root_path.exists():
            import shutil

            shutil.rmtree(self.root_path)

    #########################
    # File methods.
    #########################

    def write(
        self,
        content: BinaryIO,
        filename: str,
        dir: str | None = None,
        if_exists: IfDriveFileExistsBehavior | None = None,
        content_type: str | None = None,
    ) -> FileMetadata:
        """Write a file and its metadata."""
        if if_exists is None:
            if_exists = self.default_if_exists_behavior

        if self.file_exists(filename, dir):
            if if_exists == IfDriveFileExistsBehavior.FAIL:
                raise FileExistsError(f"File {filename} already exists")
            elif if_exists == IfDriveFileExistsBehavior.AUTO_RENAME:
                base, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
                counter = 1
                while self.file_exists(filename, dir):
                    filename = f"{base}({counter}).{ext}" if ext else f"{base}({counter})"
                    counter += 1

        # Get current position in stream
        pos = content.tell()

        # Create metadata
        content.seek(0, 2)  # Seek to end to get size
        size = content.tell()
        content.seek(0)  # Reset to beginning

        if content_type is None:
            content_type = self._guess_content_type(filename)

        metadata = FileMetadata(filename=filename, dir=dir, content_type=content_type, size=size)

        # Write the file
        file_path = self._path_for(filename, dir)
        with open(file_path, "wb") as f:
            f.write(content.read())

        # Write metadata
        self._write_metadata(metadata)

        # Restore stream position
        content.seek(pos)
        return metadata

    def delete(self, filename: str, dir: str | None = None) -> None:
        """Delete a file and its metadata directory."""
        file_path = self._path_for(filename, dir)
        metadata_dir = self._metadata_dir_for(filename, dir)

        if file_path.exists():
            file_path.unlink()
        if metadata_dir.exists():
            import shutil

            shutil.rmtree(metadata_dir)

    @contextmanager
    def open_file(self, filename: str, dir: str | None = None) -> Iterator[BinaryIO]:
        """Open a file for reading."""
        file_path = self._path_for(filename, dir)
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} not found")

        with open(file_path, "rb") as f:
            yield f

    def get_metadata(self, filename: str, dir: str | None = None) -> FileMetadata:
        """Get metadata for a file."""
        return self._read_metadata(filename, dir)

    def file_exists(self, filename: str, dir: str | None = None) -> bool:
        """Check if a file exists."""
        return self._path_for(filename, dir).exists()

    def _guess_content_type(self, filename: str) -> str:
        """Guess the content type of a file based on its extension."""
        import mimetypes

        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    def list(self, dir: str = "") -> Iterator[str]:
        """List all files and directories in a directory (non-recursively).

        Args:
            dir: The directory to list files from. Defaults to root directory.

        Returns:
            Iterator of names (without paths) of files and directories that contain files.
            Excludes empty directories and metadata directories.
        """
        dir_path = self._path_for(dir=dir)
        if not dir_path.is_dir():
            return

        for path in dir_path.iterdir():
            # Skip metadata directories
            if path.name.endswith(".metadata"):
                continue

            if path.is_file():
                yield path.name
            elif path.is_dir():
                # Include directory if it contains any non-metadata files or non-empty directories
                has_content = False
                for subpath in path.rglob("*"):
                    if subpath.is_file() and not any(p.name.endswith(".metadata") for p in subpath.parents):
                        has_content = True
                        break
                if has_content:
                    yield path.name

    #########################
    # Pydantic model methods.
    #########################

    from typing import TypeVar

    ModelT = TypeVar("ModelT", bound=BaseModel)

    def write_model(
        self,
        value: BaseModel,
        filename: str,
        dir: str | None = None,
        serialization_context: dict[str, Any] | None = None,
        if_exists: IfDriveFileExistsBehavior | None = None,
    ) -> None:
        """Write a pydantic model to a file.

        Args:
            value: The Pydantic model to write
            filename: Name of the file to write to
            dir: Optional directory path relative to drive root
            serialization_context: Optional context dict passed to model_dump_json
            if_exists: How to handle existing files. Uses drive default if not specified.
        """
        data_json = value.model_dump_json(context=serialization_context)
        data_bytes = data_json.encode("utf-8")
        self.write(io.BytesIO(data_bytes), filename, dir, if_exists)

    def read_model(
        self, cls: type[ModelT], filename: str, dir: str | None = None, strict: bool | None = None
    ) -> ModelT:
        """Read a pydantic model from a file.

        Args:
            cls: The Pydantic model class to deserialize into
            filename: Name of the file to read from
            dir: Optional directory path relative to drive root
            strict: Whether to use strict validation. Default is None (use model's settings)

        Returns:
            An instance of the specified model class

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValidationError: If the file content can't be parsed into the model
        """
        with self.open_file(filename, dir) as f:
            data_json = f.read().decode("utf-8")
        return cls.model_validate_json(data_json, strict=strict)

    def read_models(
        self,
        cls: type[ModelT],
        dir: str | None = None,
    ) -> Iterator[ModelT]:
        """Read all Pydantic models from files in a directory.

        Args:
            cls: The Pydantic model class to deserialize into
            dir: Optional directory path relative to drive root

        Yields:
            Instances of the specified model class

        Note:
            Files that fail to parse as valid models are skipped with a warning.
        """
        import logging

        logger = logging.getLogger(__name__)

        dir_path = self._path_for(None, dir)
        if not dir_path.is_dir():
            return

        for name in self.list(dir or ""):
            path = dir_path / name
            if path.is_file():
                try:
                    yield self.read_model(cls, name, dir)
                except Exception as e:
                    logger.warning(f"Failed to read model from {path}: {e}")


=== File: libraries/python/assistant-drive/assistant_drive/tests/test_basic.py ===
from io import BytesIO
from tempfile import TemporaryDirectory

import pytest
from assistant_drive import Drive
from assistant_drive.drive import DriveConfig, IfDriveFileExistsBehavior
from pydantic import BaseModel

file_content = BytesIO(b"Hello, World!")  # Convert byte string to BytesIO


@pytest.fixture(scope="function")
def drive():
    with TemporaryDirectory() as temp_dir:
        drive = Drive(DriveConfig(root=temp_dir))
        yield drive


def test_write_to_root(drive):
    # Add a file with a directory.
    metadata = drive.write(file_content, "test.txt")

    assert metadata.filename == "test.txt"
    assert metadata.dir is None
    assert metadata.content_type == "text/plain"
    assert metadata.size == 13
    assert metadata.created_at is not None
    assert metadata.updated_at is not None

    assert list(drive.list()) == ["test.txt"]


def test_write_to_directory(drive):
    metadata = drive.write(file_content, "test.txt", "summaries")

    assert metadata.filename == "test.txt"
    assert metadata.dir == "summaries"
    assert metadata.content_type == "text/plain"
    assert metadata.size == 13
    assert metadata.created_at is not None
    assert metadata.updated_at is not None

    assert list(drive.list()) == ["summaries"]
    assert list(drive.list(dir="summaries")) == ["test.txt"]


def test_write_to_nested_directory(drive):
    metadata = drive.write(file_content, "test.txt", "abc/summaries")

    assert metadata.filename == "test.txt"
    assert metadata.dir == "abc/summaries"
    assert metadata.content_type == "text/plain"
    assert metadata.size == 13
    assert metadata.created_at is not None
    assert metadata.updated_at is not None

    assert list(drive.list()) == ["abc"]
    assert list(drive.list(dir="abc")) == ["summaries"]
    assert list(drive.list(dir="abc/summaries")) == ["test.txt"]


def test_exists(drive):
    assert not drive.file_exists("test.txt", "summaries")
    drive.write(file_content, "test.txt", "summaries")
    assert drive.file_exists("test.txt", "summaries")


def test_open(drive):
    drive.write(file_content, "test.txt", "summaries")
    with drive.open_file("test.txt", "summaries") as f:
        assert f.read() == b"Hello, World!"


def test_list(drive):
    drive.write(file_content, "test.txt", "summaries")
    assert list(drive.list(dir="summaries")) == ["test.txt"]

    drive.write(file_content, "test2.txt", "summaries")
    assert sorted(list(drive.list(dir="summaries"))) == ["test.txt", "test2.txt"]


def test_open_non_existent_file(drive):
    with pytest.raises(FileNotFoundError):
        with drive.open_file("test.txt", "summaries") as f:
            f.read()


def test_auto_rename(drive, if_exists=IfDriveFileExistsBehavior.AUTO_RENAME):
    drive.write(file_content, "test.txt", "summaries")
    metadata = drive.write(file_content, "test.txt", "summaries", if_exists=IfDriveFileExistsBehavior.AUTO_RENAME)
    assert metadata.filename == "test(1).txt"
    assert sorted(list(drive.list(dir="summaries"))) == sorted(["test.txt", "test(1).txt"])


def test_overwrite(drive):
    drive.write(file_content, "test.txt", "summaries")
    metadata = drive.write(BytesIO(b"XXX"), "test.txt", "summaries", if_exists=IfDriveFileExistsBehavior.OVERWRITE)
    assert metadata.filename == "test.txt"
    with drive.open_file("test.txt", "summaries") as f:
        assert f.read() == b"XXX"
    assert list(drive.list(dir="summaries")) == ["test.txt"]


def test_fail(drive):
    drive.write(file_content, "test.txt", "summaries")
    with pytest.raises(FileExistsError):
        drive.write(file_content, "test.txt", "summaries", if_exists=IfDriveFileExistsBehavior.FAIL)


def test_delete(drive):
    drive.write(file_content, "test.txt", "summaries")
    drive.delete(dir="summaries", filename="test.txt")
    assert list(drive.list(dir="summaries")) == []

    # Add a file with the same name but overwrite.
    metadata = drive.write(file_content, "test.txt", "summaries", if_exists=IfDriveFileExistsBehavior.OVERWRITE)
    assert metadata.filename == "test.txt"
    assert sorted(list(drive.list(dir="summaries"))) == sorted(["test.txt"])


@pytest.mark.skip("Not implemented")
def test_open_files_multiple_files(drive) -> None:
    drive.write(file_content, "test.txt", "summaries")
    drive.write(file_content, "test2.txt", "summaries")

    files = list(drive.open_files("summaries"))
    assert len(files) == 2

    for file_context in files:
        with file_context as file:
            assert file.read() == b"Hello, World!"


@pytest.mark.skip("Not implemented")
def test_open_files_empty_dir(drive) -> None:
    files = list(drive.open_files("summaries"))
    assert len(files) == 0


def test_write_model(drive) -> None:
    class TestModel(BaseModel):
        name: str

    model = TestModel(name="test")
    drive.write_model(model, "test.json", "summaries")

    with drive.open_file("test.json", "summaries") as f:
        assert f.read() == b'{"name":"test"}'


def test_read_model(drive) -> None:
    class TestModel(BaseModel):
        name: str

    model = TestModel(name="test")
    drive.write_model(model, "test.json", "summaries")

    model = drive.read_model(TestModel, "test.json", "summaries")
    assert model.name == "test"


def test_read_models(drive) -> None:
    class TestModel(BaseModel):
        name: str

    model_1 = TestModel(name="test1")
    drive.write_model(model_1, "test1.json", "summaries")

    model_2 = TestModel(name="test2")
    drive.write_model(model_2, "test2.json", "summaries")

    models = list(drive.read_models(TestModel, "summaries"))
    assert len(models) == 2

    assert sorted([models[0].name, models[1].name]) == ["test1", "test2"]


def test_read_model_non_existent_file(drive) -> None:
    class TestModel(BaseModel):
        name: str

    with pytest.raises(FileNotFoundError):
        drive.read_model(TestModel, "test.json", "summaries")


def test_subdrive(drive) -> None:
    subdrive = drive.subdrive("summaries")
    assert subdrive.root_path == drive.root_path / "summaries"
    assert list(subdrive.list()) == []

    subdrive.write(file_content, "test.txt")
    assert list(subdrive.list()) == ["test.txt"]
    assert list(drive.list("summaries")) == ["test.txt"]


=== File: libraries/python/assistant-drive/pyproject.toml ===
[project]
name = "assistant-drive"
version = "0.1.0"
description = "MADE:Exploration Assistant Drive"
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.6.1",
    "pydantic-settings>=2.5.2",
    # "python-magic>=0.4.27",
    # "python-magic-bin>=0.4.14",
]

[dependency-groups]
dev = [
    "pytest>=8.3.1",
    "pytest-asyncio>=0.23.8",
    "pytest-repeat>=0.9.3",
    "ipykernel>=6.29.5",
    "pyright>=1.1.389",
]

[tool.uv.sources]
# python-magic = { git = "https://github.com/julian-r/python-magic.git#egg=python-magic" }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"


=== File: libraries/python/assistant-drive/pytest.ini ===
# pytest.ini
[pytest]
minversion = 6.0
addopts = -vv -rP
pythonpath = .
testpaths = **/tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
asyncio_mode = auto
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s | %(levelname)-7s | %(name)s | %(message)s


=== File: libraries/python/assistant-drive/usage.ipynb ===
{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "%reload_ext autoreload\n",
    "%autoreload 2\n",
    "\n",
    "from assistant_drive import Drive, DriveConfig\n",
    "from io import BytesIO  # Import BytesIO\n",
    "\n",
    "session_id=\"demo\"\n",
    "drive = Drive(DriveConfig(root=f\".data/drive/{session_id}\"))\n",
    "\n",
    "print(list(drive.list()))\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Basic Usage"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Create BinaryIO from text.\n",
    "file_content = BytesIO(b\"Hello, World!\")  # Convert byte string to BytesIO\n",
    "metadata = drive.write(file_content, \"test.txt\")\n",
    "print(metadata)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": ".venv",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}


=== File: libraries/python/guided-conversation/.vscode/settings.json ===
{
  "editor.bracketPairColorization.enabled": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": "always",
    "source.organizeImports": "always"
  },
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnPaste": true,
  "editor.formatOnSave": true,
  "editor.formatOnType": true,
  "editor.guides.bracketPairs": "active",
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "flake8.ignorePatterns": ["**/*.py"], // disable flake8 in favor of ruff
  "jupyter.debugJustMyCode": false,
  "python.analysis.autoFormatStrings": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.exclude": [
    "**/.venv/**",
    "**/.data/**",
    "**/__pycache__/**"
  ],
  "python.analysis.fixAll": ["source.unusedImports"],
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.typeCheckingMode": "standard",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "python.testing.cwd": "${workspaceFolder}",
  "search.exclude": {
    "**/.venv": true,
    "**/data": true
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
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
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "Contoso",
    "dotenv",
    "httpx",
    "openai",
    "pydantic",
    "pypdf",
    "pyright",
    "runtimes",
    "tiktoken",
    "venv"
  ]
}


=== File: libraries/python/guided-conversation/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/guided-conversation/README.md ===
# Guided Conversation

This library is a modified copy of the [guided-conversation](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/demos/guided_conversations) library from the [Semantic Kernel](https://github.com/microsoft/semantic-kernel) repository.

The guided conversation library supports scenarios where an agent with a goal and constraints leads a conversation. There are many of these scenarios where we hold conversations that are driven by an objective and constraints. For example:

- a teacher guiding a student through a lesson
- a call center representative collecting information about a customer's issue
- a sales representative helping a customer find the right product for their specific needs
- an interviewer asking candidate a series of questions to assess their fit for a role
- a nurse asking a series of questions to triage the severity of a patient's symptoms
- a meeting where participants go around sharing their updates and discussing next steps

The common thread between all these scenarios is that they are between a creator leading the conversation and a user(s) who are participating. The creator defines the goals, a plan for how the conversation should flow, and often collects key information through a form throughout the conversation. They must exercise judgment to navigate and adapt the conversation towards achieving the set goal all while writing down key information and planning in advance.

The goal of this framework is to show how we can build a common framework to create AI agents that can assist a creator in running conversational scenarios semi-autonomously and generating artifacts like notes, forms, and plans that can be used to track progress and outcomes. A key tenant of this framework is the following principal: think with the model, plan with the code. This means that the model is used to understand user inputs and make complex decisions, but code is used to apply constraints and provide structure to make the system reliable. To better understand this concept, please visit the original project on the [Semantic Kernel](https://github.com/microsoft/semantic-kernel) repository and their [guided-conversation](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/demos/guided_conversations) library, notebooks, demos, and documentation.

## Example usage with a Semantic Workbench assistant

For an example of how to use this library with a Semantic Workbench assistant, we have provided a [Guided Conversation Assistant](../../../assistants/guided-conversation-assistant/) for reference.


=== File: libraries/python/guided-conversation/guided_conversation/__init__.py ===


=== File: libraries/python/guided-conversation/guided_conversation/functions/__init__.py ===


=== File: libraries/python/guided-conversation/guided_conversation/functions/conversation_plan.py ===
import logging

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions import FunctionResult, KernelArguments, KernelPlugin

from guided_conversation.plugins.agenda import Agenda
from guided_conversation.plugins.artifact import Artifact
from guided_conversation.utils.conversation_helpers import Conversation
from guided_conversation.utils.resources import GCResource, ResourceConstraintMode

logger = logging.getLogger(__name__)

conversation_plan_template = """<message role="system">You are a helpful, thoughtful, and meticulous assistant.
You are conducting a conversation with a user. \
Your goal is to complete an artifact as thoroughly as possible by the end of the conversation, and to ensure a
smooth experience for the user.

This is the schema of the artifact you are completing:
{{ artifact_schema }}{% if context %}

Here is some additional context about the conversation:
{{ context }}{% endif %}

Throughout the conversation, you must abide by these rules:
{{ rules }}{% if current_state_description %}

Here's a description of the conversation flow:
{{ current_state_description }}
Follow this description, and exercise good judgment about when it is appropriate to deviate.{% endif %}

You will be provided the history of your conversation with the user up until now and the current state of the artifact.
Note that if the value for a field in the artifact is 'Unanswered', it means that the field has not been completed.
You need to select the best possible action(s), given the state of the conversation and the artifact.
These are the possible actions you can take:
{% if show_agenda %}Update agenda (required parameters: items)
- If the latest agenda is set to "None", you should always pick this action.
- You should pick this action if you need to change your plan for the conversation to make the best use of the
remaining turns available to you. \
Consider how long it usually takes to get the information you need (which is a function of the quality and pace of
the user's responses), \
the number, complexity, and importance of the remaining fields in the artifact, and the number of turns remaining
({{ remaining_resource }}). \
Based on these factors, you might need to accelerate (e.g. combine several topics) or slow down the conversation
(e.g. spread out a topic), in which case you should update the agenda accordingly. \
Note that skipping an artifact field is NOT a valid way to accelerate the conversation.
- You must provide an ordered list of items to be completed sequentially, where the first item contains everything
you will do in the current turn of the conversation (in addition to updating the agenda). \
For example, if you choose to send a message to the user asking for their name and medical history, then you would
write "ask for name and medical history" as the first item. \
If you think medical history will take longer than asking for the name, then you would write
"complete medical history" as the second item, with an estimate of how many turns you think it will take. \
Do NOT include items that have already been completed. \
Items must always represent a conversation topic (corresponding to the "Send message to user" action). Updating the
artifact (e.g. "update field X based on the discussion") or terminating the conversation is NOT a valid item.
- The latest agenda was created in the previous turn of the conversation. \
Even if the total turns in the latest agenda equals the remaining turns, you should still update the agenda if you
think the current plan is suboptimal (e.g. the first item was completed, the order of items is not ideal, an item is
too broad or not a conversation topic, etc.).
- Each item must have a description and and your best guess for the number of turns required to complete it. Do not
provide a range of turns. \
It is EXTREMELY important that the total turns allocated across all items in the updated agenda (including the first
item for the current turn) {{ total_resource_str }} \
Everything in the agenda should be something you expect to complete in the remaining turns - there shouldn't be any
optional "buffer" items. \
It can be helpful to include the cumulative turns allocated for each item in the agenda to ensure you adhere to this
rule, e.g. item 1 = 2 turns (cumulative total = 2), item 2 = 4 turns (cumulative total = 6), etc.
- Avoid high-level items like "ask follow-up questions" - be specific about what you need to do.
- Do NOT include wrap-up items such as "review and confirm all information with the user" (you should be doing this
throughout the conversation) or "thank the user for their time". \
Do NOT repeat topics that have already been sufficiently addressed. {{ ample_time_str }}{% endif %}

Send message to user (required parameters: message)
- If there is no conversation history, you should always pick this action.
- You should pick this action if (a) the user asked a question or made a statement that you need to respond to, \
or (b) you need to follow-up with the user because the information they provided is incomplete, invalid, ambiguous,
or in some way insufficient to complete the artifact. \
For example, if the artifact schema indicates that the "date of birth" field must be in the format "YYYY-MM-DD", but
the user has only provided the month and year, you should send a message to the user asking for the day. \
Likewise, if the user claims that their date of birth is February 30, you should send a message to the user asking
for a valid date. \
If the artifact schema is open-ended (e.g. it asks you to rate how pressing the user's issue is, without specifying
rules for doing so), use your best judgment to determine whether you have enough information or you need to continue
probing the user. \
It's important to be thorough, but also to avoid asking the user for unnecessary information.

Update artifact fields (required parameters: field, value)
- You should pick this action as soon as (a) the user provides new information that is not already reflected in the
current state of the artifact and (b) you are able to submit a valid value for a field in the artifact using this new
information. \
If you have already updated a field in the artifact and there is no new information to update the field with, you
should not pick this action.
- Make sure the value adheres to the constraints of the field as specified in the artifact schema.
- If the user has provided all required information to complete a field (i.e. the criteria for "Send message to user"
are not satisfied) but the information is in the wrong format, you should not ask the user to reformat their response. \
Instead, you should simply update the field with the correctly formatted value. For example, if the artifact asks for
the date of birth in the format "YYYY-MM-DD", and the user provides their date of birth as "June 15, 2000", you should
update the field with the value "2000-06-15".
- Prioritize accuracy over completion. You should never make up information or make assumptions in order to complete
a field. \
For example, if the field asks for a 10-digit phone number, and the user provided a 9-digit phone number, you should
not add a digit to the phone number in order to complete the field. \
Instead, you should follow-up with the user to ask for the correct phone number. If they still aren't able to provide
one, you should leave the field unanswered.
- If the user isn't able to provide all of the information needed to complete a field, \
use your best judgment to determine if a partial answer is appropriate (assuming it adheres to the formatting
requirements of the field). \
For example, if the field asks for a description of symptoms along with details about when the symptoms started, but
the user isn't sure when their symptoms started, \
it's better to record the information they do have rather than to leave the field unanswered (and to indicate that
the user was unsure about the start date).
- If it's possible to update multiple fields at once (assuming you're adhering to the above rules in all cases), you
should do so. \
For example, if the user provides their full name and date of birth in the same message, you should select the
"update artifact fields" action twice, once for each field.

End conversation (required parameters: None)
{{ termination_instructions }}
{{ resource_instructions }}

If you select the "Update artifact field" action or the "Update agenda" action, you should also select one of the
"Send message to user" or "End conversation" actions. \
Note that artifact and updates updates will always be executed before a message is sent to the user or the
conversation is terminated. \
Also note that only one message can be sent to the user at a time.

Your task is to state your step-by-step reasoning for the best possible action(s), followed by a final recommendation
of which action(s) to take, including all required parameters.
Someone else will be responsible for executing the action(s) you select and they will only have access to your output \
(not any of the conversation history, artifact schema, or other context) so it is EXTREMELY important \
that you clearly specify the value of all required parameters for each action you select.</message>

<message role="user">Conversation history:
{{ chat_history }}

Latest agenda:
{{ agenda_state }}

Current state of the artifact:
{{ artifact_state }}</message>"""


async def conversation_plan_function(
    kernel: Kernel,
    chat_history: Conversation,
    context: str,
    rules: list[str],
    conversation_flow: str,
    current_artifact: Artifact,
    req_settings: PromptExecutionSettings,
    resource: GCResource,
    agenda: Agenda,
) -> FunctionResult:
    """Reasons/plans about the next best action(s) to continue the conversation. In this function, a DESCRIPTION of
    the possible actions
    are surfaced to the agent. Note that the agent will not execute the actions, but will provide a step-by-step
    reasoning for the best
    possible action(s). The implication here is that NO tool/plugin calls are made, only a description of what tool
    calls might be called
    is created.

    Currently, the reasoning/plan from this function is passed to another function (which leverages openai tool
    calling) that will execute
    the actions.

    Args:
        kernel (Kernel): The kernel object.
        chat_history (Conversation): The conversation history
        context (str): Creator provided context of the conversation
        rules (list[str]): Creator provided rules
        conversation_flow (str): Creator provided conversation flow
        current_artifact (Artifact): The current artifact
        req_settings (dict): The request settings
        resource (GCResource): The resource object

    Returns:
        FunctionResult: The function result.
    """
    # clear any pre-existing tools from the request settings
    # req_settings.tools = None
    # req_settings.tool_choice = None

    # clear any extension data
    if hasattr(req_settings, "extension_data"):
        req_settings.extension_data = {}

    kernel_function = kernel.add_function(
        prompt=conversation_plan_template,
        function_name="conversation_plan_function",
        plugin_name="conversation_plan",
        template_format="jinja2",
        prompt_execution_settings=req_settings,
    )
    if isinstance(kernel_function, KernelPlugin):
        raise ValueError("Invalid kernel function type.")

    remaining_resource = resource.remaining_units if resource.remaining_units else 0
    resource_instructions = resource.get_resource_instructions()

    total_resource_str = ""
    ample_time_str = ""

    # if there is a resource constraint and there's more than one turn left, include the update agenda action
    if (resource_instructions != "") and (remaining_resource > 1):
        if resource.get_resource_mode() == ResourceConstraintMode.MAXIMUM:
            total_resource_str = f"does not exceed the remaining turns ({remaining_resource})."
            ample_time_str = ""
        elif resource.get_resource_mode() == ResourceConstraintMode.EXACT:
            total_resource_str = (
                f"is equal to the remaining turns ({remaining_resource}). Do not leave any turns unallocated."
            )
            ample_time_str = """If you have many turns remaining, instead of including wrap-up items or repeating
            topics, you should include items that increase the breadth and/or depth of the conversation \
in a way that's directly relevant to the artifact (e.g. "collect additional details about X", "ask for clarification
about Y", "explore related topic Z", etc.)."""
        else:
            logger.error("Invalid resource mode.")
    else:
        total_resource_str = ""
        ample_time_str = ""
    termination_instructions = _get_termination_instructions(resource)

    # only include the agenda if there is a resource constraint and there's more than one turn left
    show_agenda = resource_instructions != "" and remaining_resource > 1

    arguments = KernelArguments(
        context=context,
        artifact_schema=current_artifact.get_schema_for_prompt(),
        rules=" ".join([r.strip() for r in rules]),
        current_state_description=conversation_flow,
        show_agenda=show_agenda,
        remaining_resource=remaining_resource,
        total_resource_str=total_resource_str,
        ample_time_str=ample_time_str,
        termination_instructions=termination_instructions,
        resource_instructions=resource_instructions,
        chat_history=chat_history.get_repr_for_prompt(),
        agenda_state=agenda.get_agenda_for_prompt(),
        artifact_state=current_artifact.get_artifact_for_prompt(),
    )

    result = await kernel.invoke(function=kernel_function, arguments=arguments)
    if result is None:
        raise ValueError("Invalid kernel result.")
    return result


def _get_termination_instructions(resource: GCResource):
    """
    Get the termination instructions for the conversation. This is contingent on the resources mode,
    if any, that is available.

    Assumes we're always using turns as the resource unit.

    Args:
        resource (GCResource): The resource object.

    Returns:
        str: the termination instructions
    """
    # Termination condition under no resource constraints
    if resource.resource_constraint is None:
        return (
            "- You should pick this action as soon as you have completed the artifact to the best of your ability, the"
            " conversation has come to a natural conclusion, or the user is not cooperating so you cannot continue the"
            " conversation."
        )

    # Termination condition under exact resource constraints
    if resource.resource_constraint.mode == ResourceConstraintMode.EXACT:
        return (
            "- You should only pick this action if the user is not cooperating so you cannot continue the conversation."
        )

    # Termination condition under maximum resource constraints
    elif resource.resource_constraint.mode == ResourceConstraintMode.MAXIMUM:
        return (
            "- You should pick this action as soon as you have completed the artifact to the best of your ability, the"
            " conversation has come to a natural conclusion, or the user is not cooperating so you cannot continue the"
            " conversation."
        )

    else:
        logger.error("Invalid resource mode provided.")
        return ""


=== File: libraries/python/guided-conversation/guided_conversation/functions/execution.py ===
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions import FunctionResult, KernelArguments, KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function

execution_template = """<message role="system">You are a helpful, thoughtful, and meticulous assistant.
You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the
end of the conversation.
You will be given some reasoning about the best possible action(s) to take next given the state of the conversation
as well as the artifact schema.
The reasoning is supposed to state the recommended action(s) to take next, along with all required parameters for each action.
Your task is to execute ALL actions recommended in the reasoning in the order they are listed.
If the reasoning's specification of an action is incomplete (e.g. it doesn't include all required parameters for the
action, \
or some parameters are specified implicitly, such as "send a message that contains a greeting" instead of explicitly
providing \
the value of the "message" parameter), do not execute the action. You should never fill in missing or imprecise
parameters yourself.
If the reasoning is not clear about which actions to take, or all actions are specified in an incomplete way, \
return 'None' without selecting any action.</message>

<message role="user">Artifact schema:
{{ artifact_schema }}

If the type in the schema is str, the "field_value" parameter in the action should be also be a string.
These are example parameters for the update_artifact action: {"field_name": "company_name", "field_value": "Contoso"}
DO NOT write JSON in the "field_value" parameter in this case. {"field_name": "company_name", "field_value": "{"value": "Contoso"}"} is INCORRECT.

Reasoning:
{{ reasoning }}</message>"""


@kernel_function(name="send_message_to_user", description="Sends a message to the user.")
def send_message(message: Annotated[str, "The message to send to the user."]) -> None:
    return None


@kernel_function(name="end_conversation", description="Ends the conversation.")
def end_conversation() -> None:
    return None


async def execution(
    kernel: Kernel, reasoning: str, functions: list[str], req_settings: PromptExecutionSettings, artifact_schema: str
) -> FunctionResult:
    """Executes the actions recommended by the reasoning/planning call in the given context.

    Args:
        kernel (Kernel): The kernel object.
        reasoning (str): The reasoning from a previous model call.
        functions (list[str]): The list of plugins to INCLUDE for the tool call.
        req_settings (PromptExecutionSettings): The prompt execution settings.
        artifact (str): The artifact schema for the execution prompt.

    Returns:
        FunctionResult: The result of the execution.
    """
    req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
        auto_invoke=False, filters={"included_plugins": functions}
    )

    kernel_function = kernel.add_function(
        prompt=execution_template,
        function_name="execution",
        plugin_name="execution",
        template_format="jinja2",
        prompt_execution_settings=req_settings,
    )
    if not isinstance(kernel_function, KernelFunction):
        raise ValueError("Invalid kernel function type.")

    arguments = KernelArguments(
        artifact_schema=artifact_schema,
        reasoning=reasoning,
    )

    result = await kernel.invoke(function=kernel_function, arguments=arguments)
    if result is None:
        raise ValueError("Invalid kernel result.")
    return result


=== File: libraries/python/guided-conversation/guided_conversation/functions/final_update_plan.py ===
# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# TODO: Search for and find the `# type: ignore` comments in the copied code and remove them

from semantic_kernel import Kernel
from semantic_kernel.functions import FunctionResult, KernelArguments, KernelPlugin

from guided_conversation.utils.conversation_helpers import Conversation

final_update_template = """<message role="system">You are a helpful, thoughtful, and meticulous assistant.
You just finished a conversation with a user.{% if context %} Here is some additional context about the conversation:
{{ context }}{% endif %}

Your goal is to complete an artifact as thoroughly and accurately as possible based on the conversation.

This is the schema of the artifact:
{{ artifact_schema }}

You will be given the current state of the artifact as well as the conversation history.
Note that if the value for a field in the artifact is 'Unanswered', it means that the field was not completed. \
Some fields may have already been completed during the conversation.

Your need to determine whether there are any fields that need to be updated, and if so, update them.
- You should only update a field if both of the following conditions are met: (a) the current state does NOT adequately reflect the conversation \
and (b) you are able to submit a valid value for a field. \
You are allowed to update completed fields, but you should only do so if the current state is inadequate, \
e.g. the user corrected a mistake in their date of birth, but the artifact does not show the corrected version. \
Remember that it's always an option to reset a field to "Unanswered" - this is often the best choice if the artifact contains incorrect information that cannot be corrected. \
Do not submit a value that is identical to the current state of the field (e.g. if the field is already "Unanswered" and the user didn't provide any new information about it, you should not submit "Unanswered"). \
- Make sure the value adheres to the constraints of the field as specified in the artifact schema. \
If it's not possible to update a field with a valid value (e.g., the user provided an invalid date of birth), you should not update the field.
- If the artifact schema is open-ended (e.g. it asks you to rate how pressing the user's issue is, without specifying rules for doing so), \
use your best judgment to determine whether you have enough information to complete the field based on the conversation.
- Prioritize accuracy over completion. You should never make up information or make assumptions in order to complete a field. \
For example, if the field asks for a 10-digit phone number, and the user provided a 9-digit phone number, you should not add a digit to the phone number in order to complete the field.
- If the user wasn't able to provide all of the information needed to complete a field, \
use your best judgment to determine if a partial answer is appropriate (assuming it adheres to the formatting requirements of the field). \
For example, if the field asks for a description of symptoms along with details about when the symptoms started, but the user wasn't sure when their symptoms started, \
it's better to record the information they do have rather than to leave the field unanswered (and to indicate that the user was unsure about the start date).
- It's possible to update multiple fields at once (assuming you're adhering to the above rules in all cases). It's also possible that no fields need to be updated.

Your task is to state your step-by-step reasoning about what to update, followed by a final recommendation.
Someone else will be responsible for executing the updates and they will only have access to your output \
(not any of the conversation history, artifact schema, or other context) so make sure to specify exactly which \
fields to update and the values to update them with, or to state that no fields need to be updated.
</message>

<message role="user">Conversation history:
{{ conversation_history }}

Current state of the artifact:
{{ artifact_state }}</message>"""


async def final_update_plan_function(
    kernel: Kernel,
    req_settings: dict,
    chat_history: Conversation,
    context: str,
    artifact_schema: str,
    artifact_state: str,
) -> FunctionResult:
    """This function is responsible for updating the artifact based on the conversation history when the conversation ends. This function may not always update the artifact, namely if the current state of the artifact is already accurate based on the conversation history. The function will return a step-by-step reasoning about what to update, followed by a final recommendation. The final recommendation will specify exactly which fields to update and the values to update them with, or to state that no fields need to be updated.


    Args:
        kernel (Kernel): The kernel object.
        req_settings (dict): The prompt execution settings.
        chat_history (Conversation): The conversation history.
        context (str): The context of the conversation.
        artifact_schema (str): The schema of the artifact.
        artifact_state (str): The current state of the artifact.

    Returns:
        FunctionResult: The result of the function (step-by-step reasoning about what to update in the artifact)
    """
    req_settings.tools = None  # type: ignore
    req_settings.tool_choice = None  # type: ignore

    # clear any extension data
    if hasattr(req_settings, "extension_data"):
        req_settings.extension_data = {}  # type: ignore

    kernel_function = kernel.add_function(
        prompt=final_update_template,
        function_name="final_update_plan_function",
        plugin_name="final_update_plan",
        template_format="jinja2",
        prompt_execution_settings=req_settings,
    )
    if isinstance(kernel_function, KernelPlugin):
        raise ValueError("Invalid kernel function type.")

    arguments = KernelArguments(
        conversation_history=chat_history.get_repr_for_prompt(),
        context=context,
        artifact_schema=artifact_schema,
        artifact_state=artifact_state,
    )

    result = await kernel.invoke(function=kernel_function, arguments=arguments)
    if result is None:
        raise ValueError("Invalid kernel result.")
    return result


=== File: libraries/python/guided-conversation/guided_conversation/guided_conversation_agent.py ===
# Copyright (c) Microsoft. All rights reserved.

# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# type: ignore

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from guided_conversation.functions.conversation_plan import conversation_plan_function
from guided_conversation.functions.execution import end_conversation, execution, send_message
from guided_conversation.functions.final_update_plan import final_update_plan_function
from guided_conversation.plugins.agenda import Agenda
from guided_conversation.plugins.artifact import Artifact
from guided_conversation.utils.conversation_helpers import (
    Conversation,
    ConversationMessageType,
    create_formatted_timestamp,
)
from guided_conversation.utils.openai_tool_calling import (
    ToolValidationResult,
    parse_function_result,
    validate_tool_calling,
)
from guided_conversation.utils.plugin_helpers import PluginOutput, format_kernel_functions_as_tools
from guided_conversation.utils.resources import GCResource, ResourceConstraint

MAX_DECISION_RETRIES = 2


class ToolName(Enum):
    UPDATE_ARTIFACT_TOOL = "update_artifact_field"
    UPDATE_AGENDA_TOOL = "update_agenda"
    SEND_MSG_TOOL = "send_message_to_user"
    END_CONV_TOOL = "end_conversation"
    GENERATE_PLAN_TOOL = "generate_plan"
    EXECUTE_PLAN_TOOL = "execute_plan"
    FINAL_UPDATE_TOOL = "final_update"
    GUIDED_CONVERSATION_AGENT_TOOLBOX = "gc_agent"


@dataclass
class GCOutput:
    """The output of the GuidedConversation agent.

    Args:
        ai_message (str): The message to send to the user.
        is_conversation_over (bool): Whether the conversation is over.
    """

    ai_message: str | None = field(default=None)
    is_conversation_over: bool = field(default=False)


class GuidedConversation:
    def __init__(
        self,
        kernel: Kernel,
        artifact: type[BaseModel],
        rules: list[str],
        conversation_flow: str | None,
        context: str | None,
        resource_constraint: ResourceConstraint | None,
        service_id: str = "gc_main",
    ) -> None:
        """Initializes the GuidedConversation agent.

        Args:
            kernel (Kernel): An instance of Kernel. Must come initialized with a AzureOpenAI or OpenAI service.
            artifact (BaseModel): The artifact to be used as the goal/working memory/output of the conversation.
            rules (list[str]): The rules to be used in the guided conversation (dos and dont's).
            conversation_flow (str | None): The conversation flow to be used in the guided conversation.
            context (str | None): The scene-setting for the conversation.
            resource_constraint (ResourceConstraint | None): The limit on the conversation length (for ex: number of turns).
            service_id (str): Provide a service_id associated with the kernel's service that was provided.
        """

        self.logger = logging.getLogger(__name__)
        self.kernel = kernel
        self.service_id = service_id

        self.conversation = Conversation()
        self.resource = GCResource(resource_constraint)
        self.artifact = Artifact(self.kernel, self.service_id, artifact)
        self.rules = rules
        self.conversation_flow = conversation_flow
        self.context = context
        self.agenda = Agenda(self.kernel, self.service_id, self.resource.get_resource_mode(), MAX_DECISION_RETRIES)

        # Plugins will be executed in the order of this list.
        self.plugins_order = [
            ToolName.UPDATE_ARTIFACT_TOOL.value,
            ToolName.UPDATE_AGENDA_TOOL.value,
        ]

        # Terminal plugins are plugins that are handled in a special way:
        # - Only one terminal plugin can be called in a single step of the conversation as it leads to the end of the conversation step.
        # - The order of this list determines the execution priority.
        # - For example, if the model chooses to both call send message and end conversation,
        #   Send message will be executed first and since the orchestration step returns, end conversation will not be executed.
        self.terminal_plugins_order = [
            ToolName.SEND_MSG_TOOL.value,
            ToolName.END_CONV_TOOL.value,
        ]

        self.current_failed_decision_attempts = 0

        # Set common request settings
        self.req_settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)
        self.req_settings.max_tokens = 2000
        self.kernel.add_function(plugin_name=ToolName.SEND_MSG_TOOL.value, function=send_message)
        self.kernel.add_function(plugin_name=ToolName.END_CONV_TOOL.value, function=end_conversation)
        self.kernel.add_function(
            plugin_name=ToolName.UPDATE_ARTIFACT_TOOL.value, function=self.artifact.update_artifact_field
        )
        self.kernel.add_function(
            plugin_name=ToolName.UPDATE_AGENDA_TOOL.value, function=self.agenda.update_agenda_items
        )

        # Set orchestrator functions for the agent
        self.kernel_function_generate_plan = self.kernel.add_function(
            plugin_name="gc_agent", function=self.generate_plan
        )
        self.kernel_function_execute_plan = self.kernel.add_function(plugin_name="gc_agent", function=self.execute_plan)
        self.kernel_function_final_update = self.kernel.add_function(plugin_name="gc_agent", function=self.final_update)

    async def step_conversation(self, user_input: str | None = None) -> GCOutput:
        """Given a message from a user, this will execute the guided conversation agent up until a
        terminal plugin is called or the maximum number of decision retries is reached."""
        self.logger.info(f"Starting conversation step {self.resource.turn_number}.")
        self.resource.start_resource()
        self.current_failed_decision_attempts = 0
        if user_input:
            self.conversation.add_messages(
                ChatMessageContent(
                    role=AuthorRole.USER,
                    content=user_input,
                    metadata={
                        "turn_number": self.resource.turn_number,
                        "type": ConversationMessageType.DEFAULT,
                        "timestamp": create_formatted_timestamp(),
                    },
                )
            )

        # Keep generating and executing plans until a terminal plugin is called
        # or the maximum number of decision retries is reached.
        while self.current_failed_decision_attempts < MAX_DECISION_RETRIES:
            plan = await self.kernel.invoke(self.kernel_function_generate_plan)
            executed_plan = await self.kernel.invoke(
                self.kernel_function_execute_plan, KernelArguments(plan=plan.value)
            )
            success, plugins, terminal_plugins = executed_plan.value

            if success != ToolValidationResult.SUCCESS:
                self.logger.warning(
                    f"Failed to parse tools in plan on retry attempt {self.current_failed_decision_attempts} out of {MAX_DECISION_RETRIES}."
                )
                self.current_failed_decision_attempts += 1
                continue

            # Run a step of the orchestration logic based on the plugins called by the model.
            # First execute all regular plugins (if any) in the order returned by execute_plan
            for plugin_name, plugin_args in plugins:
                if plugin_name == f"{ToolName.UPDATE_ARTIFACT_TOOL.value}-{ToolName.UPDATE_ARTIFACT_TOOL.value}":
                    plugin_args["conversation"] = self.conversation
                    # Modify plugin_args such that field=field_name and value=field_value
                    plugin_args["field_name"] = plugin_args.pop("field")
                    plugin_args["field_value"] = plugin_args.pop("value")
                    await self._call_plugin(self.artifact.update_artifact, plugin_args)
                elif plugin_name == f"{ToolName.UPDATE_AGENDA_TOOL.value}-{ToolName.UPDATE_AGENDA_TOOL.value}":
                    plugin_args["remaining_turns"] = self.resource.get_remaining_turns()
                    plugin_args["conversation"] = self.conversation
                    await self._call_plugin(self.agenda.update_agenda, plugin_args)

            # Then execute the first terminal plugin (if any)
            if terminal_plugins:
                gc_output = GCOutput()
                plugin_name, plugin_args = terminal_plugins[0]
                if plugin_name == f"{ToolName.SEND_MSG_TOOL.value}-{ToolName.SEND_MSG_TOOL.value}":
                    gc_output.ai_message = plugin_args["message"]
                elif plugin_name == f"{ToolName.END_CONV_TOOL.value}-{ToolName.END_CONV_TOOL.value}":
                    await self.kernel.invoke(self.kernel_function_final_update)
                    gc_output.ai_message = "I will terminate this conversation now. Thank you for your time!"
                    gc_output.is_conversation_over = True
                self.resource.increment_resource()
                return gc_output

        # Handle case where the maximum number of decision retries was reached.
        self.logger.warning(f"Failed to execute plan after {MAX_DECISION_RETRIES} attempts.")
        self.resource.increment_resource()
        gc_output = GCOutput()
        gc_output.ai_message = "An error occurred and I must sadly end the conversation."
        gc_output.is_conversation_over = True
        return gc_output

    @kernel_function(
        name=ToolName.GENERATE_PLAN_TOOL.value,
        description="Generate a plan based on a time constraint for the current state of the conversation.",
    )
    async def generate_plan(self) -> str:
        """Generate a plan for the current state of the conversation. The idea here is to explicitly let the model plan before
        generating any plugin calls. This has been shown to increase reliability.

        Returns:
            str: The plan generated by the plan function.
        """
        self.logger.info("Generating plan for the current state of the conversation")
        plan = await conversation_plan_function(
            self.kernel,
            self.conversation,
            self.context,
            self.rules,
            self.conversation_flow,
            self.artifact,
            self.req_settings,
            self.resource,
            self.agenda,
        )
        plan = plan.value[0].content
        self.conversation.add_messages(
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=plan,
                metadata={
                    "turn_number": self.resource.turn_number,
                    "type": ConversationMessageType.REASONING,
                    "timestamp": create_formatted_timestamp(),
                },
            )
        )
        return plan

    @kernel_function(
        name=ToolName.EXECUTE_PLAN_TOOL.value,
        description="Given the generated plan by the model, use that plan to generate which functions to execute.",
    )
    async def execute_plan(
        self, plan: str
    ) -> tuple[ToolValidationResult, list[tuple[str, dict]], list[tuple[str, dict]]]:
        """Given the generated plan by the model, use that plan to generate which functions to execute.
        Once the tool calls are generated by the model, we sort them into two groups: regular plugins and terminal plugins
        according to the definition in __init__

        Args:
            plan (str): The plan generated by the model.

        Returns:
            tuple[ToolValidationResult, list[tuple[str, dict]], list[tuple[str, dict]]]: A tuple containing the validation result
            of the tool calls, the regular plugins to execute, and the terminal plugins to execute alongside their arguments.
        """
        self.logger.info("Executing plan.")

        req_settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)
        functions = self.plugins_order + self.terminal_plugins_order
        result = await execution(
            kernel=self.kernel,
            reasoning=plan,
            functions=functions,
            req_settings=req_settings,
            artifact_schema=self.artifact.get_schema_for_prompt(),
        )

        parsed_result = parse_function_result(result)
        formatted_tools = format_kernel_functions_as_tools(self.kernel, functions)
        validation_result = validate_tool_calling(parsed_result, formatted_tools)

        # Sort plugin calls into two groups in the order of the corresponding lists defined in __init__
        plugins = []
        terminal_plugins = []
        if validation_result == ToolValidationResult.SUCCESS:
            for plugin in self.plugins_order:
                for idx, called_plugin_name in enumerate(parsed_result["tool_names"]):
                    plugin_name = f"{plugin}-{plugin}"
                    if called_plugin_name == plugin_name:
                        plugins.append((parsed_result["tool_names"][idx], parsed_result["tool_args_list"][idx]))

            for terminal_plugin in self.terminal_plugins_order:
                for idx, called_plugin_name in enumerate(parsed_result["tool_names"]):
                    terminal_plugin_name = f"{terminal_plugin}-{terminal_plugin}"
                    if called_plugin_name == terminal_plugin_name:
                        terminal_plugins.append((
                            parsed_result["tool_names"][idx],
                            parsed_result["tool_args_list"][idx],
                        ))

        return validation_result, plugins, terminal_plugins

    @kernel_function(
        name=ToolName.FINAL_UPDATE_TOOL.value,
        description="After the last message of a conversation was added to the conversation history, perform a final update of the artifact",
    )
    async def final_update(self):
        """Explicit final update of the artifact after the conversation ends."""
        self.logger.info("Final update of the artifact prior to terminating the conversation.")

        # Get a plan from the model
        reasoning_response = await final_update_plan_function(
            kernel=self.kernel,
            req_settings=self.req_settings,
            chat_history=self.conversation,
            context=self.context,
            artifact_schema=self.artifact.get_schema_for_prompt(),
            artifact_state=self.artifact.get_artifact_for_prompt(),
        )

        # Then generate the functions to be executed
        req_settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)

        functions = [ToolName.UPDATE_ARTIFACT_TOOL.value]
        execution_response = await execution(
            kernel=self.kernel,
            reasoning=reasoning_response.value[0].content,
            functions=functions,
            req_settings=req_settings,
            artifact_schema=self.artifact.get_schema_for_prompt(),
        )

        parsed_result = parse_function_result(execution_response)
        formatted_tools = format_kernel_functions_as_tools(self.kernel, functions)
        validation_result = validate_tool_calling(parsed_result, formatted_tools)

        # If the tool call was successful, update the artifact.
        if validation_result != ToolValidationResult.SUCCESS:
            self.logger.warning(f"No artifact change during final update due to: {validation_result.value}")
            pass
        else:
            for i in range(len(parsed_result["tool_names"])):
                tool_name = parsed_result["tool_names"][i]
                tool_args = parsed_result["tool_args_list"][i]
                if (
                    tool_name == f"{ToolName.UPDATE_ARTIFACT_TOOL.value}-{ToolName.UPDATE_ARTIFACT_TOOL.value}"
                    and "field" in tool_args
                    and "value" in tool_args
                ):
                    # Check if tool_args contains the field and value to update
                    plugin_output = await self.artifact.update_artifact(
                        field_name=tool_args["field"],
                        field_value=tool_args["value"],
                        conversation=self.conversation,
                    )
                    if plugin_output.update_successful:
                        self.logger.info(f"Artifact field {tool_args['field']} successfully updated.")
                        # Set turn numbers
                        for message in plugin_output.messages:
                            message.metadata["turn_number"] = self.resource.turn_number
                        self.conversation.add_messages(plugin_output.messages)
                    else:
                        self.logger.error(f"Final artifact field update of {tool_args['field']} failed.")

    def to_json(self) -> dict:
        return {
            "artifact": self.artifact.to_json(),
            "agenda": self.agenda.to_json(),
            "chat_history": self.conversation.to_json(),
            "resource": self.resource.to_json(),
        }

    async def _call_plugin(self, plugin_function: Callable, plugin_args: dict):
        """Common logic whenever any plugin is called like handling errors and appending to chat history."""
        self.logger.info(f"Calling plugin {plugin_function.__name__}.")
        output: PluginOutput = await plugin_function(**plugin_args)
        if output.update_successful:
            # Set turn numbers
            for message in output.messages:
                message.metadata["turn_number"] = self.resource.turn_number
            self.conversation.add_messages(output.messages)
        else:
            self.logger.warning(
                f"Plugin {plugin_function.__name__} failed to execute on attempt {self.current_failed_decision_attempts} out of {MAX_DECISION_RETRIES}."
            )
            self.current_failed_decision_attempts += 1

    @classmethod
    def from_json(
        cls,
        json_data: dict,
        kernel: Kernel,
        artifact: type[BaseModel],
        rules: list[str],
        conversation_flow: str | None,
        context: str | None,
        resource_constraint: ResourceConstraint | None,
        service_id: str = "gc_main",
    ) -> "GuidedConversation":
        loaded_artifact = Artifact.from_json(
            json_data["artifact"],
            kernel=kernel,
            service_id=service_id,
            input_artifact=artifact,
            max_artifact_field_retries=MAX_DECISION_RETRIES,
        )
        loaded_agenda = Agenda.from_json(
            json_data["agenda"],
            kernel=kernel,
            service_id=service_id,
            resource_constraint_mode=resource_constraint.mode if resource_constraint else None,
        )
        loaded_conversation = Conversation.from_json(json_data["chat_history"])
        loaded_resource = GCResource.from_json(json_data["resource"])

        gc = cls(
            kernel=kernel,
            artifact=artifact,
            rules=rules,
            conversation_flow=conversation_flow,
            context=context,
            resource_constraint=resource_constraint,
            service_id=service_id,
        )
        gc.agenda = loaded_agenda
        gc.artifact = loaded_artifact
        gc.conversation = loaded_conversation
        gc.resource = loaded_resource

        return gc


=== File: libraries/python/guided-conversation/guided_conversation/plugins/__init__.py ===


=== File: libraries/python/guided-conversation/guided_conversation/plugins/agenda.py ===
# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# TODO: Search for and find the `# type: ignore` comments in the copied code and remove them

import logging
from typing import Annotated, Any

from pydantic import Field, ValidationError
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from guided_conversation.utils.base_model_llm import BaseModelLLM
from guided_conversation.utils.conversation_helpers import Conversation, ConversationMessageType
from guided_conversation.utils.openai_tool_calling import ToolValidationResult
from guided_conversation.utils.plugin_helpers import PluginOutput, fix_error, update_attempts
from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit, format_resource

AGENDA_ERROR_CORRECTION_SYSTEM_TEMPLATE = """<message role="system">You are a helpful, thoughtful, and meticulous assistant.
You are conducting a conversation with a user. You tried to update the agenda, but the update was invalid.
You will be provided the history of your conversation with the user, \
your previous attempt(s) at updating the agenda, and the error message(s) that resulted from your attempt(s).
Your task is to correct the update so that it is valid. \
Your changes should be as minimal as possible - you are focused on fixing the error(s) that caused the update to be invalid.
Note that if the resource allocation is invalid, you must follow these rules:
1. You should not change the description of the first item (since it has already been executed), but you can change its resource allocation
2. For all other items, you can combine or split them, or assign them fewer or more resources, \
but the content they cover collectively should not change (i.e. don't eliminate or add new topics).
For example, the invalid attempt was "item 1 = ask for date of birth (1 turn), item 2 = ask for phone number (1 turn), \
item 3 = ask for phone type (1 turn), item 4 = explore treatment history (6 turns)", \
and the error says you need to correct the total resource allocation to 7 turns. \
A bad solution is "item 1 = ask for date of birth (1 turn), \
item 2 = explore treatment history (6 turns)" because it eliminates the phone number and phone type topics. \
A good solution is "item 1 = ask for date of birth (2 turns), item 2 = ask for phone number, phone type,
and treatment history (2 turns), item 3 = explore treatment history (3 turns)."</message>

<message role="user">Conversation history:
{{ conversation_history }}

Previous attempts to update the agenda:
{{ previous_attempts }}</message>"""

UPDATE_AGENDA_TOOL = "update_agenda"


class _BaseAgendaItem(BaseModelLLM):
    title: str = Field(description="Brief description of the item")
    resource: int = Field(description="Number of turns required for the item")


class _BaseAgenda(BaseModelLLM):
    items: list[_BaseAgendaItem] = Field(
        description="Ordered list of items to be completed in the remainder of the conversation",
        default_factory=list,
    )


class Agenda:
    """An abstraction to manage a conversation agenda. The expected use case is that another agent will generate an agenda.
    This class will validate if it is valid, and help correct it if it is not.

    Args:
        kernel (Kernel): The Semantic Kernel instance to use for calling the LLM. Don't forget to set your
                req_settings since this class uses tool calling functionality from the Semantic Kernel.
        service_id (str): The service ID to use for the Semantic Kernel tool calling. One kernel can have multiple
                services. The service ID is used to identify which service to use for LLM calls. The Agenda object
                assumes that the service has tool calling capabilities and is some flavor of chat completion.
        resource_constraint_mode (ResourceConstraintMode): The mode for resource constraints.
        max_agenda_retries (int): The maximum number of retries for updating the agenda.
    """

    def __init__(
        self,
        kernel: Kernel,
        service_id: str,
        resource_constraint_mode: ResourceConstraintMode | None,
        max_agenda_retries: int = 2,
    ) -> None:
        logger = logging.getLogger(__name__)

        self.id = "agenda_plugin"
        self.kernel = Kernel()
        self.logger = logger
        self.kernel = kernel
        self.service_id = service_id

        self.resource_constraint_mode = resource_constraint_mode
        self.max_agenda_retries = max_agenda_retries

        self.agenda = _BaseAgenda()

    async def update_agenda(
        self,
        items: list[dict[str, str]],
        remaining_turns: int,
        conversation: Conversation,
    ) -> PluginOutput:
        """Updates the agenda model with the given items (generally generated by an LLM) and validates if the update is valid.
        The agenda update reasons in terms of turns for validating the if the proposed agenda is valid.
        If you wish to use a different resource unit, convert the value to turns in some way because
        we found that LLMs do much better at reasoning in terms of turns.

        Args:
            items (list[dict[str, str]]): A list of agenda items.
                Each item should have the following keys:
                - title (str): A brief description of the item.
                - resource (int): The number of turns required for the item.
            remaining_turns (int): The number of remaining turns.
            conversation (Conversation): The conversation object.

        Returns:
            PluginOutput: A PluginOutput object with the success status. Does not generate any messages.
        """
        previous_attempts = []
        while True:
            try:
                # Try to update the agenda, and do extra validation checks
                self.agenda.items = items  # type: ignore
                self._validate_agenda_update(items, remaining_turns)
                self.logger.info(f"Agenda updated successfully: {self.get_agenda_for_prompt()}")
                return PluginOutput(True, [])
            except (ValidationError, ValueError) as e:
                # Update the previous attempts and get instructions for the LLM
                previous_attempts, llm_formatted_attempts = update_attempts(
                    error=e,
                    attempt_id=str(items),
                    previous_attempts=previous_attempts,
                )

                # If we have reached the maximum number of retries return a failure
                if len(previous_attempts) > self.max_agenda_retries:
                    self.logger.warning(f"Failed to update agenda after {self.max_agenda_retries} attempts.")
                    return PluginOutput(False, [])
                else:
                    self.logger.info(f"Attempting to fix the agenda error. Attempt {len(previous_attempts)}.")
                    response = await self._fix_agenda_error(llm_formatted_attempts, conversation)
                    if response is None:
                        raise ValueError("Invalid response from the LLM.")
                    if response["validation_result"] != ToolValidationResult.SUCCESS:
                        self.logger.warning(
                            f"Failed to fix the agenda error due to a failure in the LLM tool call: {response['validation_result']}"
                        )
                        return PluginOutput(False, [])
                    else:
                        # Use the result of the first tool call to try the update again
                        items = response["tool_args_list"][0]["items"]

    def get_agenda_for_prompt(self) -> str:
        """Gets a string representation of the agenda for use in an LLM prompt.

        Returns:
            str: A string representation of the agenda.
        """
        agenda_json = self.agenda.model_dump()
        agenda_items = agenda_json.get("items", [])
        if len(agenda_items) == 0:
            return "None"
        agenda_str = "\n".join([
            f"{i + 1}. [{format_resource(item['resource'], ResourceConstraintUnit.TURNS)}] {item['title']}"
            for i, item in enumerate(agenda_items)
        ])
        total_resource = format_resource(sum([item["resource"] for item in agenda_items]), ResourceConstraintUnit.TURNS)
        agenda_str += f"\nTotal = {total_resource}"
        return agenda_str

    # The following is the kernel function that will be provided to the LLM call
    class Items:
        title: Annotated[str, "Description of the item"]
        resource: Annotated[int, "Number of turns required for the item"]

    @kernel_function(
        name=UPDATE_AGENDA_TOOL,
        description="Updates the agenda.",
    )
    def update_agenda_items(
        self,
        items: Annotated[list[Items], "Ordered list of items to be completed in the remainder of the conversation"],
    ):
        pass

    async def _fix_agenda_error(self, previous_attempts: str, conversation: Conversation) -> dict[Any, Any]:
        """Calls an LLM to try and fix an error in the agenda update."""
        req_settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)
        req_settings.max_tokens = 2000  # type: ignore
        req_settings.tool_choice = "auto"  # type: ignore
        self.kernel.add_function(plugin_name=self.id, function=self.update_agenda_items)
        req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            auto_invoke=False, filters={"included_plugins": [self.id]}
        )

        arguments = KernelArguments(
            conversation_history=conversation.get_repr_for_prompt(exclude_types=[ConversationMessageType.REASONING]),
            previous_attempts=previous_attempts,
        )

        return await fix_error(
            kernel=self.kernel,
            prompt_template=AGENDA_ERROR_CORRECTION_SYSTEM_TEMPLATE,
            req_settings=req_settings,  # type: ignore
            arguments=arguments,
        )

    def _validate_agenda_update(self, items: list[dict[str, str]], remaining_turns: int) -> None:
        """Validates if any constraints were violated while performing the agenda update.

        Args:
            items (list[dict[str, str]]): A list of agenda items.
            remaining_turns (int): The number of remaining turns.

        Raises:
            ValueError: If any validation checks fail.
        """
        # The total, proposed allocation of resources.
        total_resources = sum([item["resource"] for item in items])  # type: ignore

        violations = []
        # In maximum mode, the total resources should not exceed the remaining turns
        if (self.resource_constraint_mode == ResourceConstraintMode.MAXIMUM) and (total_resources > remaining_turns):
            total_resource_instruction = (
                f"The total turns allocated in the agenda must not exceed the remaining amount ({remaining_turns})"
            )
            violations.append(f"{total_resource_instruction}; but the current total is {total_resources}.")

        # In exact mode if the total resources were not exactly equal to the remaining turns
        if (self.resource_constraint_mode == ResourceConstraintMode.EXACT) and (total_resources != remaining_turns):
            total_resource_instruction = (
                f"The total turns allocated in the agenda must equal the remaining amount ({remaining_turns})"
            )
            violations.append(f"{total_resource_instruction}; but the current total is {total_resources}.")

        # Check if any item has a resource value of 0
        if any(item["resource"] <= 0 for item in items):  # type: ignore
            violations.append("All items must have a resource value greater than 0.")

        # Raise an error if any violations were found
        if len(violations) > 0:
            self.logger.debug(f"Agenda update failed due to the following violations: {violations}.")
            raise ValueError(" ".join(violations))

    def to_json(self) -> dict:
        agenda_dict = self.agenda.model_dump()
        return {
            "agenda": agenda_dict,
        }

    @classmethod
    def from_json(
        cls,
        json_data: dict,
        kernel: Kernel,
        service_id: str,
        resource_constraint_mode: ResourceConstraintMode | None,
        max_agenda_retries: int = 2,
    ) -> "Agenda":
        agenda = cls(kernel, service_id, resource_constraint_mode, max_agenda_retries)
        agenda.agenda.items = json_data["agenda"]["items"]
        return agenda


=== File: libraries/python/guided-conversation/guided_conversation/plugins/artifact.py ===
# Copyright (c) Microsoft. All rights reserved.

# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# type: ignore

import inspect
import logging
from typing import Annotated, Any, Literal, get_args, get_origin, get_type_hints

from pydantic import BaseModel, create_model
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from guided_conversation.utils.base_model_llm import BaseModelLLM
from guided_conversation.utils.conversation_helpers import Conversation, ConversationMessageType
from guided_conversation.utils.openai_tool_calling import ToolValidationResult
from guided_conversation.utils.plugin_helpers import PluginOutput, fix_error, update_attempts

ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE = """<message role="system">You are a helpful, thoughtful, and meticulous assistant.
You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation.
You have tried to update a field in the artifact, but the value you provided did not adhere \
to the constraints of the field as specified in the artifact schema.
You will be provided the history of your conversation with the user, the schema for the field, \
your previous attempt(s) at updating the field, and the error message(s) that resulted from your attempt(s).
Your task is to select the best possible action to take next:
1. Update artifact
- You should pick this action if you have a valid value to submit for the field in question.
2. Resume conversation
- You should pick this action if: (a) you do NOT have a valid value to submit for the field in question, and \
(b) you need to ask the user for more information in order to obtain a valid value. \
For example, if the user stated that their date of birth is June 2000, but the artifact field asks for the date of birth in the format \
"YYYY-MM-DD", you should resume the conversation and ask the user for the day.</message>

<message role="user">Conversation history:
{{ conversation_history }}

Schema:
{{ artifact_schema }}

Previous attempts to update the field "{{ field_name }}" in the artifact:
{{ previous_attempts }}</message>"""

UPDATE_ARTIFACT_TOOL = "update_artifact_field"
RESUME_CONV_TOOL = "resume_conversation"


class Artifact:
    """The Artifact plugin takes in a Pydantic base model, and robustly handles updating the fields of the model
    A typical use case is as a form an agent must complete throughout a conversation.
    Another use case is as a working memory for the agent.

    The primary interface is update_artifact, which takes in the field_name to update and its new value.
    Additionally, the chat_history is passed in to help the agent make informed decisions in case an error occurs.

    The Artifact also exposes several functions to access internal state:
    get_artifact_for_prompt, get_schema_for_prompt, and get_failed_fields.
    """

    def __init__(
        self, kernel: Kernel, service_id: str, input_artifact: type[BaseModel], max_artifact_field_retries: int = 2
    ) -> None:
        """
        Initialize the Artifact plugin with the given Pydantic base model.

        Args:
            kernel (Kernel): The Semantic Kernel instance to use for calling the LLM. Don't forget to set your
                req_settings since this class uses tool calling functionality from the Semantic Kernel.
            service_id (str): The service ID to use for the Semantic Kernel tool calling. One kernel can have multiple
                services. The service ID is used to identify which service to use for LLM calls. The Artifact object
                assumes that the service has tool calling capabilities and is some flavor of chat completion.
            input_artifact (BaseModel): The Pydantic base model to use as the artifact
            max_artifact_field_retries (int): The maximum number of times to retry updating a field in the artifact
        """
        logger = logging.getLogger(__name__)
        self.logger = logger

        self.id = "artifact_plugin"
        self.kernel = kernel
        self.service_id = service_id
        self.max_artifact_field_retries = max_artifact_field_retries

        self.original_schema = input_artifact.model_json_schema()
        self.artifact = self._initialize_artifact(input_artifact)

        # failed_artifact_fields maps a field name to a list of the history of the failed attempts to update it
        # dict: key = field, value = list of tuple[attempt, error message]
        self.failed_artifact_fields: dict[str, list[tuple[str, str]]] = {}

    # The following are the kernel functions that will be provided to the LLM call
    @kernel_function(
        name=UPDATE_ARTIFACT_TOOL,
        description="Sets the value of a field in the artifact",
    )
    def update_artifact_field(
        self,
        field: Annotated[str, "The name of the field to update in the artifact"],
        value: Annotated[str, "The value to set the field to"],
    ) -> None:
        pass

    @kernel_function(
        name=RESUME_CONV_TOOL,
        description="Resumes conversation to get more information from the user ",
    )
    def resume_conversation(self):
        pass

    async def update_artifact(self, field_name: str, field_value: Any, conversation: Conversation) -> PluginOutput:
        """The core interface for the Artifact plugin.
        This function will attempt to update the given field_name to the given field_value.
        If the field_value fails Pydantic validation, an LLM will determine one of two actions to take.
        Given the conversation as additional context the two actions are:
            - Retry the update the artifact by fixing the formatting using the previous failed attempts as guidance
            - Take no action or in other words, resume the conversation to ask the user for more information because the user gave incomplete or incorrect information

        Args:
            field_name (str): The name of the field to update in the artifact
            field_value (Any): The value to set the field to
            conversation (Conversation): The conversation object that contains the history of the conversation

        Returns:
            PluginOutput: An object with two fields: a boolean indicating success
            and a list of conversation messages that may have been generated.

            Several outcomes can happen:
            - The update may have failed due to
                - A field_name that is not valid in the artifact.
                - The field_value failing Pydantic validation and all retries failed.
                - The model failed to correctly call a tool.
                In this case, the boolean will be False and the list may contain a message indicating the failure.

            - The agent may have successfully updated the artifact or fixed it.
                In this case, the boolean will be True and the list will contain a message indicating the update and possibly intermediate messages.

            - The agent may have decided to resume the conversation.
                In this case, the boolean will be True and the messages may only contain messages indicated previous errors.
        """

        conversation_messages: list[ChatMessageContent] = []

        # Check if the field name is valid, and return with a failure message if not
        is_valid_field, msg = self._is_valid_field(field_name)
        if not is_valid_field:
            conversation_messages.append(msg)
            return PluginOutput(update_successful=False, messages=conversation_messages)

        # Try to update the field, and handle any errors that occur until the field is
        # successfully updated or skipped according to max_artifact_field_retries
        while True:
            try:
                # Check if there have been too many previous failed attempts to update the field
                if len(self.failed_artifact_fields.get(field_name, [])) >= self.max_artifact_field_retries:
                    self.logger.warning(f"Updating field {field_name} has failed too many times. Skipping.")
                    return PluginOutput(False, conversation_messages)

                # Attempt to update the artifact
                msg = self._execute_update_artifact(field_name, field_value)
                conversation_messages.append(msg)
                return PluginOutput(True, conversation_messages)
            except Exception as e:
                self.logger.warning(f"Error updating field {field_name}: {e}. Retrying...")
                # Handle update error will increment failed_artifact_fields, once it has failed
                # greater than self.max_artifact_field_retries the field will be skipped and the loop will break
                success, new_field_value = await self._handle_update_error(field_name, field_value, conversation, e)

                # The agent has successfully fixed the field.
                if success and new_field_value is not None:
                    self.logger.info(f"Agent successfully fixed field {field_name}. New value: {new_field_value}")
                    field_value = new_field_value
                # This is the case where the agent has decided to resume the conversation.
                elif success:
                    self.logger.info(
                        f"Agent could not fix the field itself & decided to resume conversation to fix field {field_name}"
                    )
                    return PluginOutput(True, conversation_messages)
                self.logger.warning(f"Agent failed to fix field {field_name}. Retrying...")
                # Otherwise, the agent has failed and we will go through the loop again

    def get_artifact_for_prompt(self) -> dict:
        """Returns a formatted JSON-like representation of the current state of the fields artifact.
        Any fields that were failed are completely omitted.

        Returns:
            str: The string representation of the artifact.
        """
        failed_fields = self.get_failed_fields()
        return {k: v for k, v in self.artifact.model_dump().items() if k not in failed_fields}

    def get_schema_for_prompt(self, filter_one_field: str | None = None) -> str:
        """Gets a clean version of the original artifact schema, optimized for use in an LLM prompt.

        Args:
            filter_one_field (str | None): If this is provided, only the schema for this one field will be returned.

        Returns:
            str: The cleaned schema
        """

        def _clean_properties(schema: dict, failed_fields: list[str]) -> str:
            properties = schema.get("properties", {})
            clean_properties = {}
            for name, property_dict in properties.items():
                if name not in failed_fields:
                    cleaned_property = {}
                    for k, v in property_dict.items():
                        if k in ["title", "default"]:
                            continue
                        cleaned_property[k] = v
                    clean_properties[name] = cleaned_property

            clean_properties_str = str(clean_properties)
            clean_properties_str = clean_properties_str.replace("$ref", "type")
            clean_properties_str = clean_properties_str.replace("#/$defs/", "")
            return clean_properties_str

        # If filter_one_field is provided, only get the schema for that one field
        if filter_one_field:
            if not self._is_valid_field(filter_one_field):
                self.logger.error(f'Field "{filter_one_field}" is not a valid field in the artifact.')
                raise ValueError(f'Field "{filter_one_field}" is not a valid field in the artifact.')
            filtered_schema = {"properties": {filter_one_field: self.original_schema["properties"][filter_one_field]}}
            filtered_schema.update((k, v) for k, v in self.original_schema.items() if k != "properties")
            schema = filtered_schema
        else:
            schema = self.original_schema

        failed_fields = self.get_failed_fields()
        properties = _clean_properties(schema, failed_fields)
        if not properties:
            self.logger.error("No properties found in the schema.")
            raise ValueError("No properties found in the schema.")

        types_schema = schema.get("$defs", {})
        custom_types = []
        for type_name, type_info in types_schema.items():
            if f"'type': '{type_name}'" in properties:
                clean_schema = _clean_properties(type_info, [])
                if clean_schema != "{}":
                    custom_types.append(f"{type_name} = {clean_schema}")

        if custom_types:
            explanation = f"If you wanted to create a {type_name} object, for example, you would make a JSON object \
with the following keys: {', '.join(types_schema[type_name]['properties'].keys())}."
            custom_types_str = "\n".join(custom_types)
            return f"""{properties}

Here are the definitions for the custom types referenced in the artifact schema:
{custom_types_str}

{explanation}
Remember that when updating the artifact, the field will be the original field name in the artifact and the JSON object(s) will be the value."""
        else:
            return properties

    def get_failed_fields(self) -> list[str]:
        """Get a list of fields that have failed all attempts to update.

        Returns:
            list[str]: A list of field names that have failed all attempts to update.
        """
        fields = []
        for field, attempts in self.failed_artifact_fields.items():
            if len(attempts) >= self.max_artifact_field_retries:
                fields.append(field)
        return fields

    def _initialize_artifact(self, artifact_model: type[BaseModel]) -> BaseModelLLM:
        """Create a new artifact model based on the one provided by the user
        with "Unanswered" set for all fields.

        Args:
            artifact_model (BaseModel): The Pydantic class provided by the user

        Returns:
            BaseModelLLM: The new artifact model with "Unanswered" set for all fields
        """
        modified_classes = self._modify_classes(artifact_model)
        artifact = self._modify_base_artifact(artifact_model, modified_classes)
        return artifact()

    def _get_type_if_subtype(self, target_type: type[Any], base_type: type[Any]) -> type[Any] | None:
        """Recursively checks the target_type to see if it is a subclass of base_type or a generic including base_type.

        Args:
            target_type: The type to check.
            base_type: The type to check against.

        Returns:
            The class type if target_type is base_type, a subclass of base_type, or a generic including base_type; otherwise, None.
        """
        origin = get_origin(target_type)
        if origin is None:
            if not inspect.isclass(target_type):
                return None

            if issubclass(target_type, base_type):
                return target_type

            return None

        # Recursively check if any of the arguments are the target type
        for arg in get_args(target_type):
            result = self._get_type_if_subtype(arg, base_type)
            if result is not None:
                return result
        return None

    def _modify_classes(self, artifact_class: type[BaseModel]) -> dict[str, type[BaseModelLLM]]:
        """Find all classes used as type hints in the artifact, and modify them to set 'Unanswered' as a default and valid value for all fields."""
        modified_classes = {}
        # Find any instances of BaseModel in the artifact class in the first "level" of type hints
        for field_name, field_type in get_type_hints(artifact_class).items():
            is_base_model = self._get_type_if_subtype(field_type, BaseModel)
            if is_base_model is not None:
                modified_classes[field_name] = self._modify_base_artifact(is_base_model)

        return modified_classes

    def _replace_type_annotations(
        self, field_annotation: type[Any] | None, modified_classes: dict[str, type[BaseModelLLM]]
    ) -> type:
        """Recursively replace type annotations with modified classes where applicable."""
        # Get the origin of the field annotation, which is the base type for generic types (e.g., List[str] -> list, Dict[str, int] -> dict)
        origin = get_origin(field_annotation)
        # Get the type arguments of the generic type (e.g., List[str] -> str, Dict[str, int] -> str, int)
        args = get_args(field_annotation)

        if origin is None:
            # The type is not generic; check if it's a subclass that needs to be replaced
            if isinstance(field_annotation, type) and issubclass(field_annotation, BaseModelLLM):
                return modified_classes.get(field_annotation.__name__, field_annotation)
            return field_annotation
        else:
            # The type is generic; recursively replace the type annotations of the arguments
            new_args = tuple(self._replace_type_annotations(arg, modified_classes) for arg in args)
            return origin[new_args]

    def _modify_base_artifact(
        self, artifact_model: type[BaseModel], modified_classes: dict[str, type[BaseModelLLM]] | None = None
    ) -> type[BaseModelLLM]:
        """Create a new artifact model with 'Unanswered' as a default and valid value for all fields."""
        for _, field_info in artifact_model.model_fields.items():
            # Replace original classes with modified version
            if modified_classes is not None:
                field_info.annotation = self._replace_type_annotations(field_info.annotation, modified_classes)
            # This makes it possible to always set a field to "Unanswered"
            field_info.annotation = field_info.annotation | Literal["Unanswered"]
            # This sets the default value to "Unanswered"
            field_info.default = "Unanswered"
            # This adds "Unanswered" as a possible value to any regex patterns
            metadata = field_info.metadata
            for m in metadata:
                if hasattr(m, "pattern"):
                    m.pattern += "|Unanswered"
        field_definitions = {
            name: (field_info.annotation, field_info) for name, field_info in artifact_model.model_fields.items()
        }
        artifact_model = create_model("Artifact", __base__=BaseModelLLM, **field_definitions)
        return artifact_model

    def _is_valid_field(self, field_name: str) -> tuple[bool, ChatMessageContent]:
        """Check if the field_name is a valid field in the artifact. Returns True if it is, False and an error message otherwise."""
        if field_name not in self.artifact.model_fields:
            error_message = f'Field "{field_name}" is not a valid field in the artifact.'
            msg = ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=error_message,
                metadata={"type": ConversationMessageType.ARTIFACT_UPDATE, "turn_number": None},
            )
            return False, msg
        return True, None

    async def _fix_artifact_error(
        self,
        field_name: str,
        previous_attempts: str,
        conversation_repr: str,
        artifact_schema_repr: str,
    ) -> dict[str, Any]:
        """Calls the LLM to fix an error in the artifact using Semantic Kernel kernel."""

        req_settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)
        req_settings.max_tokens = 2000

        self.kernel.add_function(plugin_name=self.id, function=self.update_artifact_field)
        self.kernel.add_function(plugin_name=self.id, function=self.resume_conversation)
        filter = {"included_plugins": [self.id]}
        req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(auto_invoke=False, filters=filter)

        arguments = KernelArguments(
            field_name=field_name,
            conversation_history=conversation_repr,
            previous_attempts=previous_attempts,
            artifact_schema=artifact_schema_repr,
            settings=req_settings,
        )

        return await fix_error(
            kernel=self.kernel,
            prompt_template=ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE,
            req_settings=req_settings,
            arguments=arguments,
        )

    def _execute_update_artifact(
        self,
        field_name: Annotated[str, "The name of the field to update in the artifact"],
        field_value: Annotated[Any, "The value to set the field to"],
    ) -> ChatMessageContent:
        """Update a field in the artifact with a new value. This will raise an error if the field_value is invalid."""
        setattr(self.artifact, field_name, field_value)
        msg = ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            content=f"Assistant updated {field_name} to {field_value}",
            metadata={"type": ConversationMessageType.ARTIFACT_UPDATE, "turn_number": None},
        )
        return msg

    async def _handle_update_error(
        self, field_name: str, field_value: Any, conversation: Conversation, error: Exception
    ) -> tuple[bool, Any]:
        """
        Handles the logic for when an error occurs while updating a field.
        Creates the appropriate context for the model and calls the LLM to fix the error.

        Args:
            field_name (str): The name of the field to update in the artifact
            field_value (Any): The value to set the field to
            conversation (Conversation): The conversation object that contains the history of the conversation
            error (Exception): The error that occurred while updating the field

        Returns:
            tuple[bool, Any]: A tuple containing a boolean indicating success and the new field value if successful (if not, then None)
        """
        # Update the failed attempts for the field
        previous_attempts = self.failed_artifact_fields.get(field_name, [])
        previous_attempts, llm_formatted_attempts = update_attempts(
            error=error, attempt_id=str(field_value), previous_attempts=previous_attempts
        )
        self.failed_artifact_fields[field_name] = previous_attempts

        # Call the LLM to fix the error
        conversation_history_repr = conversation.get_repr_for_prompt(exclude_types=[ConversationMessageType.REASONING])
        artifact_schema_repr = self.get_schema_for_prompt(filter_one_field=field_name)
        result = await self._fix_artifact_error(
            field_name, llm_formatted_attempts, conversation_history_repr, artifact_schema_repr
        )

        # Handling the result of the LLM call
        if result["validation_result"] != ToolValidationResult.SUCCESS:
            return False, None
        # Only consider the first tool call
        tool_name = result["tool_names"][0]
        tool_args = result["tool_args_list"][0]
        if tool_name == f"{self.id}-{UPDATE_ARTIFACT_TOOL}":
            field_value = tool_args["value"]
            return True, field_value
        elif tool_name == f"{self.id}-{RESUME_CONV_TOOL}":
            return True, None

    def to_json(self) -> dict:
        artifact_fields = self.artifact.model_dump()
        return {
            "artifact": artifact_fields,
            "failed_fields": self.failed_artifact_fields,
        }

    @classmethod
    def from_json(
        cls,
        json_data: dict,
        kernel: Kernel,
        service_id: str,
        input_artifact: type[BaseModel],
        max_artifact_field_retries: int = 2,
    ) -> "Artifact":
        artifact = cls(kernel, service_id, input_artifact, max_artifact_field_retries)

        artifact.failed_artifact_fields = json_data["failed_fields"]

        # Iterate over artifact fields and set them to the values in the json data
        # Skip any fields that are set as "Unanswered"
        for field_name, field_value in json_data["artifact"].items():
            if field_value != "Unanswered":
                setattr(artifact.artifact, field_name, field_value)
        return artifact


=== File: libraries/python/guided-conversation/guided_conversation/utils/__init__.py ===


=== File: libraries/python/guided-conversation/guided_conversation/utils/base_model_llm.py ===
# Copyright (c) Microsoft. All rights reserved.

# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# type: ignore

import ast
from types import NoneType
from typing import get_args

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator


class BaseModelLLM(BaseModel):
    """A Pydantic base class for use when an LLM is completing fields. Provides a custom field validator and Pydantic Config."""

    @field_validator("*", mode="before")
    def parse_literal_eval(cls, value: str, info: ValidationInfo):  # noqa: N805
        """An LLM will always result in a string (e.g. '["x", "y"]'), so we need to parse it to the correct type"""
        # Get the type hints for the field
        annotation = cls.model_fields[info.field_name].annotation
        typehints = get_args(annotation)
        if len(typehints) == 0:
            typehints = [annotation]

        # Usually fields that are NoneType have another type hint as well, e.g. str | None
        # if the LLM returns "None" and the field allows NoneType, we should return None
        # without this code, the next if-block would leave the string "None" as the value
        if (NoneType in typehints) and (value == "None"):
            return None

        # If the field allows strings, we don't parse it - otherwise a validation error might be raised
        # e.g. phone_number = "1234567890" should not be converted to an int if the type hint is str
        if str in typehints:
            return value
        try:
            evaluated_value = ast.literal_eval(value)
            return evaluated_value
        except Exception:
            return value

    model_config = ConfigDict(
        # Ensure that validation happens every time a field is updated, not just when the artifact is created
        validate_assignment=True,
        # Do not allow extra fields to be added to the artifact
        extra="forbid",
    )


=== File: libraries/python/guided-conversation/guided_conversation/utils/conversation_helpers.py ===
# Copyright (c) Microsoft. All rights reserved.

# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# type: ignore

import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Union

from semantic_kernel.contents import ChatMessageContent


class ConversationMessageType(StrEnum):
    DEFAULT = "default"
    ARTIFACT_UPDATE = "artifact-update"
    REASONING = "reasoning"


@dataclass
class Conversation:
    """An abstraction to represent a list of messages and common operations such as adding messages
    and getting a string representation.

    Args:
        conversation_messages (list[ChatMessageContent]): A list of ChatMessageContent objects.
    """

    logger = logging.getLogger(__name__)
    conversation_messages: list[ChatMessageContent] = field(default_factory=list)

    def add_messages(self, messages: Union[ChatMessageContent, list[ChatMessageContent], "Conversation", None]) -> None:
        """Add a message, list of messages to the conversation or merge another conversation into the end of this one.

        Args:
            messages (Union[ChatMessageContent, list[ChatMessageContent], "Conversation"]): The message(s) to add.
                All messages will be added to the end of the conversation.

        Returns:
            None
        """
        if isinstance(messages, list):
            self.conversation_messages.extend(messages)
        elif isinstance(messages, Conversation):
            self.conversation_messages.extend(messages.conversation_messages)
        elif isinstance(messages, ChatMessageContent):
            # if ChatMessageContent.metadata doesn't have type, then add default
            if "type" not in messages.metadata:
                messages.metadata["type"] = ConversationMessageType.DEFAULT
            self.conversation_messages.append(messages)
        else:
            self.logger.warning(f"Invalid message type: {type(messages)}")
            return None

    def get_repr_for_prompt(
        self,
        exclude_types: list[ConversationMessageType] | None = None,
    ) -> str:
        """Create a string representation of the conversation history for use in LLM prompts.

        Args:
            exclude_types (list[ConversationMessageType] | None): A list of message types to exclude from the conversation
                history. If None, all message types will be included.

        Returns:
            str: A string representation of the conversation history.
        """
        if len(self.conversation_messages) == 0:
            return "None"

        # Do not include the excluded messages types in the conversation history repr.
        if exclude_types is not None:
            conversation_messages = [
                message
                for message in self.conversation_messages
                if "type" in message.metadata and message.metadata["type"] not in exclude_types
            ]
        else:
            conversation_messages = self.conversation_messages

        to_join = []
        current_turn = None
        for message in conversation_messages:
            participant_name = message.name
            # Modify the default user to be capitalized for consistency with how assistant is written.
            if participant_name == "user":
                participant_name = "User"

            # If the turn number is None, don't include it in the string
            if "turn_number" in message.metadata and current_turn != message.metadata["turn_number"]:
                current_turn = message.metadata["turn_number"]
                to_join.append(f"[Turn {current_turn}]")

            # Add the message content
            if (message.role == "assistant") and (
                "type" in message.metadata and message.metadata["type"] == ConversationMessageType.ARTIFACT_UPDATE
            ):
                to_join.append(message.content)
            elif message.role == "assistant":
                to_join.append(f"Assistant: {message.content}")
            else:
                user_string = message.content.strip()
                if user_string == "":
                    to_join.append(f"{participant_name}: <sent an empty message>")
                else:
                    to_join.append(f"{participant_name}: {user_string}")
        conversation_string = "\n".join(to_join)
        return conversation_string

    def message_to_json(self, message: ChatMessageContent) -> dict:
        """
        Convert a ChatMessageContent object to a JSON serializable dictionary.

        Args:
            message (ChatMessageContent): The ChatMessageContent object to convert to JSON.

        Returns:
            dict: A JSON serializable dictionary representation of the ChatMessageContent object.
        """
        return {
            "role": message.role,
            "content": message.content,
            "name": message.name,
            "metadata": {
                "turn_number": message.metadata["turn_number"] if "turn_number" in message.metadata else None,
                "type": message.metadata["type"] if "type" in message.metadata else ConversationMessageType.DEFAULT,
                "timestamp": message.metadata["timestamp"] if "timestamp" in message.metadata else None,
            },
        }

    def to_json(self) -> dict:
        json_data = {}
        json_data["conversation"] = {}
        json_data["conversation"]["conversation_messages"] = [
            self.message_to_json(message) for message in self.conversation_messages
        ]
        return json_data

    @classmethod
    def from_json(
        cls,
        json_data: dict,
    ) -> "Conversation":
        conversation = cls()
        for message in json_data["conversation"]["conversation_messages"]:
            conversation.add_messages(
                ChatMessageContent(
                    role=message["role"],
                    content=message["content"],
                    name=message["name"],
                    metadata={
                        "turn_number": message["metadata"]["turn_number"],
                        "type": ConversationMessageType(message["metadata"]["type"]),
                        "timestamp": message["metadata"]["timestamp"],
                    },
                )
            )

        return conversation


def create_formatted_timestamp() -> str:
    """Create a formatted timestamp."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))


=== File: libraries/python/guided-conversation/guided_conversation/utils/openai_tool_calling.py ===
# Copyright (c) Microsoft. All rights reserved.

# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# type: ignore

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.functions import FunctionResult

logger = logging.getLogger(__name__)


@dataclass
class ToolArg:
    argument_name: str
    required: bool


@dataclass
class Tool:
    name: str
    args: list[ToolArg]


class ToolValidationResult(Enum):
    NO_TOOL_CALLED = "No tool was called"
    INVALID_TOOL_CALLED = "A tool was called with an unexpected name"
    MISSING_REQUIRED_ARGUMENT = "The tool called is missing a required argument"
    INVALID_ARGUMENT_TYPE = "The value of an argument is of an unexpected type"
    INVALID_ARGUMENT = "The tool called has an unexpected argument"
    SUCCESS = "success"


def parse_function_result(response: FunctionResult) -> dict[str, Any]:
    """Parse the response from SK's FunctionResult object into only the relevant data for easier downstream processing.
    This should only be used when you expect the response to contain tool calls.

    Args:
        response (FunctionResult): The response from the kernel.

    Returns:
        dict[str, Any]: The parsed response data with the following format if n was set greater than 1:
        {
            "choices": [
                {
                    "tool_names": list[str],
                    "tool_args_list": list[dict[str, Any]],
                    "message": str,
                    "finish_reason": str,
                    "validation_result": ToolValidationResult
                }, ...
            ]
        }
        Otherwise, the response will directly contain the data from the first choice (tool_names, etc keys)
    """
    response_data: dict[str, Any] = {"choices": []}
    for response_choice in response.value:
        response_data_curr = {}
        finish_reason = response_choice.finish_reason

        if finish_reason == "tool_calls":
            tool_names = []
            tool_args_list = []
            # Only look at the items that are of instance `FunctionCallContent`
            tool_calls = [item for item in response_choice.items if isinstance(item, FunctionCallContent)]
            for tool_call in tool_calls:
                if "-" not in tool_call.name:
                    logger.info(f"Tool call name {tool_call.name} does not match naming convention - modifying name.")
                    tool_names.append(tool_call.name + "-" + tool_call.name)
                else:
                    tool_names.append(tool_call.name)
                try:
                    tool_args = json.loads(tool_call.arguments)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse tool arguments for tool call {tool_call.name}. Using empty dict.")
                    tool_args = {}
                tool_args_list.append(tool_args)
            response_data_curr["tool_names"] = tool_names
            response_data_curr["tool_args_list"] = tool_args_list

        response_data_curr["message"] = response_choice.content
        response_data_curr["finish_reason"] = finish_reason
        response_data["choices"].append(response_data_curr)

    if len(response_data["choices"]) == 1:
        response_data.update(response_data["choices"][0])
        del response_data["choices"]

    return response_data


def construct_tool_objects(kernel_function_tools: dict) -> list[Tool]:
    """Construct a list of Tool objects from the kernel function tools definition.

    Args:
        kernel_function_tools (dict): The definition of tools done by the kernel function.

    Returns:
        list[Tool]: The list of Tool objects constructed from the kernel function tools definition.
    """

    tool_objects: list[Tool] = []
    for tool_definition in kernel_function_tools:
        tool_name = tool_definition["function"]["name"]
        tool_args = tool_definition["function"]["parameters"]["properties"]

        tool_arg_objects: list[ToolArg] = []
        for argument_name, _ in tool_args.items():
            tool_arg = ToolArg(argument_name=argument_name, required=False)
            tool_arg_objects.append(tool_arg)

        required_args = tool_definition["function"]["parameters"]["required"]
        for tool_arg_object in tool_arg_objects:
            if tool_arg_object.argument_name in required_args:
                tool_arg_object.required = True

        tool_objects.append(Tool(name=tool_name, args=tool_arg_objects))
    return tool_objects


def validate_tool_calling(response: dict[str, Any], request_tool_param: dict) -> ToolValidationResult:
    """Validate that the response from the LLM called tools corrected.
    1. Check if any tool was called.
    2. Check if the tools called were valid (names match)
    3. Check if all the required arguments were passed.

    Args:
        response (dict[str, Any]): The response from the LLM containing the tools called (output of parse_function_result)
        tools (list[Tool]): The list of tools that can be called by the model.

    Returns:
        ToolValidationResult: The result of the validation. ToolValidationResult.SUCCESS if the validation passed.
    """

    tool_objects = construct_tool_objects(request_tool_param)
    tool_names = response.get("tool_names", [])
    tool_args_list = response.get("tool_args_list", [])

    # Check if any tool was called.
    if not tool_names:
        logger.info("No tool was called.")
        return ToolValidationResult.NO_TOOL_CALLED

    for tool_name, tool_args in zip(tool_names, tool_args_list, strict=True):
        # Check the tool names is valid.
        tool: Tool | None = next((t for t in tool_objects if t.name == tool_name), None)
        if not tool:
            logger.warning(f"Invalid tool called: {tool_name}")
            return ToolValidationResult.INVALID_TOOL_CALLED

        for arg in tool.args:
            # Check if the required arguments were passed.
            if arg.required and arg.argument_name not in tool_args:
                logger.warning(f"Missing required argument '{arg.argument_name}' for tool '{tool_name}'.")
                return ToolValidationResult.MISSING_REQUIRED_ARGUMENT

        for tool_arg_name in tool_args.keys():
            if tool_arg_name not in [arg.argument_name for arg in tool.args]:
                logger.warning(f"Unexpected argument '{tool_arg_name}' for tool '{tool_name}'.")
                return ToolValidationResult.INVALID_ARGUMENT

    return ToolValidationResult.SUCCESS


=== File: libraries/python/guided-conversation/guided_conversation/utils/plugin_helpers.py ===
# # Copyright (c) Microsoft. All rights reserved.

# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# type: ignore

from dataclasses import dataclass

from pydantic import ValidationError
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelArguments

from guided_conversation.utils.openai_tool_calling import parse_function_result, validate_tool_calling


@dataclass
class PluginOutput:
    """A wrapper for all Guided Conversation Plugins. This class is used to return the output of a generic plugin.

    Args:
        update_successful (bool): Whether the update was successful.
        messages (list[ChatMessageContent]): A list of messages to be used at the user's digression, it
        contains information about the process of calling the plugin.
    """

    update_successful: bool
    messages: list[ChatMessageContent]


def format_kernel_functions_as_tools(kernel: Kernel, functions: list[str]):
    """Format kernel functions as JSON schemas for custom validation."""
    formatted_tools = []
    for _, kernel_plugin_def in kernel.plugins.items():
        for function_name, function_def in kernel_plugin_def.functions.items():
            if function_name in functions:
                func_metadata = function_def.metadata
                formatted_tools.append(kernel_function_metadata_to_function_call_format(func_metadata))
    return formatted_tools


async def fix_error(
    kernel: Kernel, prompt_template: str, req_settings: AzureChatCompletion, arguments: KernelArguments
) -> dict:
    """Invokes the error correction plugin. If a plugin is called & fails during execution, this function will retry
    the plugin. At a high level, we recommend the following steps when calling a plugin:
    1. Call the plugin.
    2. Parse the response.
    3. Validate the response.
    4. If the response is invalid (Validation or Value Error), retry the plugin by calling *this function*. For best
    results, check out plugins/agenda.py or plugins/artifact.py for examples of prompt templates & corresponding
    tools (which should be passed in the req_settings object). This function will handle the retry logic for you.

    Args:
        kernel (Kernel): The kernel object.
        prompt_template (str): The prompt template for the plugin.
        req_settings (AzureChatCompletion): The prompt execution settings.
        arguments (KernelArguments): The kernel arguments.

    Returns:
        dict: The result of the plugin call.
    """
    kernel_function_obj = kernel.add_function(
        prompt=prompt_template,
        function_name="error_correction",
        plugin_name="error_correction",
        template_format="jinja2",
        prompt_execution_settings=req_settings,
    )

    result = await kernel.invoke(function=kernel_function_obj, arguments=arguments)
    parsed_result = parse_function_result(result)

    formatted_tools = []
    for _, kernel_plugin_def in kernel.plugins.items():
        for _, function_def in kernel_plugin_def.functions.items():
            func_metadata = function_def.metadata
            formatted_tools.append(kernel_function_metadata_to_function_call_format(func_metadata))

    # Add any tools from req_settings
    if req_settings.tools:
        formatted_tools.extend(req_settings.tools)

    validation_result = validate_tool_calling(parsed_result, formatted_tools)
    parsed_result["validation_result"] = validation_result
    return parsed_result


def update_attempts(
    error: Exception, attempt_id: str, previous_attempts: list[tuple[str, str]]
) -> tuple[list[tuple[str, str]], str]:
    """
    Updates the plugin class attribute list of previous attempts with the current attempt and error message
    (including duplicates).

    Args:
        error (Exception): The error object.
        attempt_id (str): The ID of the current attempt.
        previous_attempts (list): The list of previous attempts.

    Returns:
        str: A formatted (optimized for LLM performance) string of previous attempts, with duplicates removed.
    """
    if isinstance(error, ValidationError):
        error_str = "; ".join([e.get("msg") for e in error.errors()])
        # replace "; Input should be 'Unanswered'" with " or input should be 'Unanswered'" for clarity
        error_str = error_str.replace("; Input should be 'Unanswered'", " or input should be 'Unanswered'")
    else:
        error_str = str(error)
    new_failed_attempt = (attempt_id, error_str)
    previous_attempts.append(new_failed_attempt)

    # Format previous attempts to be more friendly for the LLM
    attempts_list = []
    for attempt, error in previous_attempts:
        attempts_list.append(f"Attempt: {attempt}\nError: {error}")
    llm_formatted_attempts = "\n".join(attempts_list)

    return previous_attempts, llm_formatted_attempts


=== File: libraries/python/guided-conversation/guided_conversation/utils/resources.py ===
# Copyright (c) Microsoft. All rights reserved.

# FIXME: Copied code from Semantic Kernel repo, using as-is despite type errors
# type: ignore

import logging
import math
import time
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ResourceConstraintUnit(StrEnum):
    """Choose the unit of the resource constraint.
    Seconds and Minutes are real-time and will be impacted by the latency of the model."""

    SECONDS = "seconds"
    MINUTES = "minutes"
    TURNS = "turns"


class ResourceConstraintMode(StrEnum):
    """Choose how the agent should use the resource.
    Maximum: is an upper bound, i.e. the agent can end the conversation before the resource is exhausted
    Exact: the agent should aim to use exactly the given amount of the resource"""

    MAXIMUM = "maximum"
    EXACT = "exact"


class ResourceConstraint(BaseModel):
    """A structured representation of the resource constraint for the GuidedConversation agent.

    Args:
        quantity (float | int): The quantity of the resource constraint.
        unit (ResourceConstraintUnit): The unit of the resource constraint.
        mode (ResourceConstraintMode): The mode of the resource constraint.
    """

    quantity: float | int
    unit: ResourceConstraintUnit
    mode: ResourceConstraintMode

    model_config = ConfigDict(arbitrary_types_allowed=True)


def format_resource(quantity: float, unit: ResourceConstraintUnit) -> str:
    """Get formatted string for a given quantity and unit (e.g. 1 second, 20 seconds)"""
    if unit != ResourceConstraintUnit.TURNS:
        quantity = round(quantity, 1)
    unit = unit.value
    return f"{quantity} {unit[:-1] if quantity == 1 else unit}"


class GCResource:
    """Resource constraints for the GuidedConversation agent. This class is used to keep track of the resource
    constraints. If resource_constraint is None, then the agent can continue indefinitely. This also means
    that no agenda will be created for the conversation.

    Args:
        resource_constraint (ResourceConstraint | None): The resource constraint for the conversation.
        initial_seconds_per_turn (int): The initial number of seconds per turn. Defaults to 120 seconds.
    """

    def __init__(
        self,
        resource_constraint: ResourceConstraint | None,
        initial_seconds_per_turn: int = 120,
    ):
        logger = logging.getLogger(__name__)
        self.logger = logger
        self.resource_constraint: ResourceConstraint | None = resource_constraint
        self.initial_seconds_per_turn: int = initial_seconds_per_turn

        self.turn_number: int = 0
        self.remaining_units: float | None = None
        self.elapsed_units: float | None = None

        if resource_constraint is not None:
            self.elapsed_units = 0
            self.remaining_units = resource_constraint.quantity

    def start_resource(self) -> None:
        """To be called at the start of a conversation turn"""
        if self.resource_constraint is not None and (
            self.resource_constraint.unit == ResourceConstraintUnit.SECONDS
            or self.resource_constraint.unit == ResourceConstraintUnit.MINUTES
        ):
            self.start_time = time.time()

    def increment_resource(self) -> None:
        """Increment the resource counter by one turn."""
        if self.resource_constraint is not None:
            if self.resource_constraint.unit == ResourceConstraintUnit.SECONDS:
                self.elapsed_units += time.time() - self.start_time
                self.remaining_units = self.resource_constraint.quantity - self.elapsed_units
            elif self.resource_constraint.unit == ResourceConstraintUnit.MINUTES:
                self.elapsed_units += (time.time() - self.start_time) / 60
                self.remaining_units = self.resource_constraint.quantity - self.elapsed_units
            elif self.resource_constraint.unit == ResourceConstraintUnit.TURNS:
                self.elapsed_units += 1
                self.remaining_units -= 1

        self.turn_number += 1

    def get_resource_mode(self) -> ResourceConstraintMode:
        """Get the mode of the resource constraint.

        Returns:
            ResourceConstraintMode | None: The mode of the resource constraint, or None if there is no
                resource constraint.
        """
        return self.resource_constraint.mode if self.resource_constraint is not None else None

    def get_elapsed_turns(self, formatted_repr: bool = False) -> str | int:
        """Get the number of elapsed turns.

        Args:
            formatted_repr (bool): If true, return a formatted string representation of the elapsed turns.
                If false, return an integer. Defaults to False.

        Returns:
            str | int: The description/number of elapsed turns.
        """
        if formatted_repr:
            return format_resource(self.turn_number, ResourceConstraintUnit.TURNS)
        else:
            return self.turn_number

    def get_remaining_turns(self, formatted_repr: bool = False) -> str | int:
        """Get the number of remaining turns.

        Args:
            formatted_repr (bool): If true, return a formatted string representation of the remaining turns.

        Returns:
            str | int: The description/number of remaining turns.
        """
        if formatted_repr:
            return format_resource(self.estimate_remaining_turns(), ResourceConstraintUnit.TURNS)
        else:
            return self.estimate_remaining_turns()

    def estimate_remaining_turns(self) -> int:
        """Estimate the remaining turns based on the resource constraint, thereby translating certain
        resource units (e.g. seconds, minutes) into turns.

        Returns:
            int: The estimated number of remaining turns.
        """
        if self.resource_constraint is not None:
            if (
                self.resource_constraint.unit == ResourceConstraintUnit.SECONDS
                or self.resource_constraint.unit == ResourceConstraintUnit.MINUTES
            ):
                elapsed_turns = self.turn_number

                # TODO: This can likely be simplified
                if self.resource_constraint.unit == ResourceConstraintUnit.MINUTES:
                    time_per_turn = (
                        self.initial_seconds_per_turn
                        if elapsed_turns == 0
                        else (self.elapsed_units * 60) / elapsed_turns
                    )
                    time_per_turn /= 60
                else:
                    time_per_turn = (
                        self.initial_seconds_per_turn if elapsed_turns == 0 else self.elapsed_units / elapsed_turns
                    )
                remaining_turns = self.remaining_units / time_per_turn

                # Round down, unless it's less than 1, in which case round up
                remaining_turns = math.ceil(remaining_turns) if remaining_turns < 1 else math.floor(remaining_turns)
                return remaining_turns
            elif self.resource_constraint.unit == ResourceConstraintUnit.TURNS:
                return self.resource_constraint.quantity - self.turn_number
        else:
            self.logger.error(
                "Resource constraint is not set, so turns cannot be estimated using function estimate_remaining_turns"
            )
            raise ValueError(
                "Resource constraint is not set. Do not try to call this method without a resource constraint."
            )

    def get_resource_instructions(self) -> tuple[str, str]:
        """Get the resource instructions for the conversation.

        Assumes we're always using turns as the resource unit.

        Returns:
            str: the resource instructions
        """
        if self.resource_constraint is None:
            return ""

        formatted_elapsed_resource = format_resource(self.elapsed_units, ResourceConstraintUnit.TURNS)
        formatted_remaining_resource = format_resource(self.remaining_units, ResourceConstraintUnit.TURNS)

        # if the resource quantity is anything other than 1, the resource unit should be plural (e.g. "minutes" instead of "minute")
        is_plural_elapsed = self.elapsed_units != 1
        is_plural_remaining = self.remaining_units != 1

        if self.elapsed_units > 0:
            resource_instructions = f"So far, {formatted_elapsed_resource} {'have' if is_plural_elapsed else 'has'} elapsed since the conversation began. "
        else:
            resource_instructions = ""

        if self.resource_constraint.mode == ResourceConstraintMode.EXACT:
            exact_mode_instructions = f"""There {"are" if is_plural_remaining else "is"} {formatted_remaining_resource} remaining (including this one) - the conversation will automatically terminate when 0 turns are left. \
You should continue the conversation until it is automatically terminated. This means you should NOT preemptively end the conversation, \
either explicitly (by selecting the "End conversation" action) or implicitly (e.g. by telling the user that you have all required information and they should wait for the next step). \
Your goal is not to maximize efficiency (i.e. complete the artifact as quickly as possible then end the conversation), but rather to make the best use of ALL remaining turns available to you"""

            if is_plural_remaining:
                resource_instructions += f"""{exact_mode_instructions}. This will require you to plan your actions carefully using the agenda: you want to avoid the situation where you have to pack too many topics into the final turns because you didn't account for them earlier, \
or where you've rushed through the conversation and all fields are completed but there are still many turns left."""

            # special instruction for the final turn (i.e. 1 remaining) in exact mode
            else:
                resource_instructions += f"""{exact_mode_instructions}, including this one. Therefore, you should use this turn to ask for any remaining information needed to complete the artifact, \
        or, if the artifact is already completed, continue to broaden/deepen the discussion in a way that's directly relevant to the artifact. Do NOT indicate to the user that the conversation is ending."""

        elif self.resource_constraint.mode == ResourceConstraintMode.MAXIMUM:
            resource_instructions += f"""You have a maximum of {formatted_remaining_resource} (including this one) left to complete the conversation. \
You can decide to terminate the conversation at any point (including now), otherwise the conversation will automatically terminate when 0 turns are left. \
You will need to plan your actions carefully using the agenda: you want to avoid the situation where you have to pack too many topics into the final turns because you didn't account for them earlier."""

        else:
            self.logger.error("Invalid resource mode provided.")

        return resource_instructions

    def to_json(self) -> dict:
        return {
            "turn_number": self.turn_number,
            "remaining_units": self.remaining_units,
            "elapsed_units": self.elapsed_units,
        }

    @classmethod
    def from_json(
        cls,
        json_data: dict,
    ) -> "GCResource":
        gc_resource = cls(
            resource_constraint=None,
            initial_seconds_per_turn=120,
        )
        gc_resource.turn_number = json_data["turn_number"]
        gc_resource.remaining_units = json_data["remaining_units"]
        gc_resource.elapsed_units = json_data["elapsed_units"]
        return gc_resource


=== File: libraries/python/guided-conversation/pyproject.toml ===
[project]
name = "guided-conversation"
version = "0.1.0"
description = "MADE:Exploration Guided Conversation"
authors = [{name="MADE:Explorers"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "semantic-kernel>=1.11.0",
]

[tool.uv]
package = true

[tool.uv.sources]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pyright>=1.1.389",
]

[tool.pyright]
exclude = ["**/.venv", "**/.data", "**/__pycache__"]


