import datetime
import pathlib
from typing import Protocol, Sequence

from attr import dataclass
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, SkipValidation


class TokenCounter(Protocol):
    def __call__(self, messages: list[ChatCompletionMessageParam]) -> int:
        """
        Returns the token count for the given list of OpenAI messages.
        """
        ...


HistoryMessageParam = (
    ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam | ChatCompletionToolMessageParam
)


@dataclass
class ArchiveTaskConfig:
    message_poll_interval_seconds: float = 60.0
    """Interval to poll for new messages to archive."""

    chunk_token_count_threshold: int = 30_000
    """Token count threshold for archiving chunks."""


class MessageProtocol(Protocol):
    @property
    def id(self) -> str:
        """The unique identifier for the message."""
        ...

    @property
    def timestamp(self) -> datetime.datetime:
        """
        The timestamp of the message.
        This is typically the time when the message was created or "sent".
        """
        ...

    @property
    def openai_message(self) -> HistoryMessageParam:
        """
        The OpenAI message representation.
        """
        ...


class MessageProvider(Protocol):
    """
    Protocol for a message source that can return an ordered list of messages, oldest to most recent, returning
    messages after the `after_id`, if set.
    """

    async def __call__(self, after_id: str | None) -> Sequence[MessageProtocol]: ...


class StorageProvider(Protocol):
    """
    Protocol for a file system provider that can read and write the message history archive.
    """

    async def read_text_file(self, relative_file_path: pathlib.PurePath) -> str | None:
        """
        Reads a text file from storage identified by `file_path`.

        Args:
            relative_file_path: The path to the file to read.

        Returns:
            The content of the file as a string, or None if the file does not exist.
        """
        ...

    async def write_text_file(self, relative_file_path: pathlib.PurePath, content: str) -> None:
        """
        Writes a text file to storage identified by `relative_file_path`.

        Args:
            relative_file_path: The path to the file to write.
            content: The content to write to the file.
        """
        ...

    async def list_files(self, relative_directory_path: pathlib.PurePath) -> list[pathlib.PurePath]:
        """
        Lists all files in the specified directory.

        Args:
            relative_directory_path: The path to the directory to list files from.

        Returns:
            AsyncIterable[pathlib.PurePath]: A list of paths to the files in the directory.
        """
        ...


class ArchivesState(BaseModel):
    """
    State of the message history archives.
    This class is a pydantic BaseModel to simplify serialization and deserialization.
    """

    most_recent_archived_message_id: str | None = None
    """The ID of the most recent archived message."""


class ArchiveManifest(BaseModel):
    """
    The manifest of a message archive, containing metadata about the messages.
    This class is a pydantic BaseModel to simplify serialization and deserialization.
    """

    summary: str
    """A summary of the messages in this archive."""
    message_ids: list[str]
    """The IDs of the messages in this archive."""
    timestamp_oldest: datetime.datetime
    """The timestamp of the oldest message in this archive."""
    timestamp_most_recent: datetime.datetime
    """The timestamp of the most recent message in this archive."""
    filename: str
    """The filename where the content of this archive is stored."""


class ArchiveContent(BaseModel):
    """
    The content of an archive, containing the actual messages.
    This class is a pydantic BaseModel to simplify serialization and deserialization.
    """

    messages: list[SkipValidation[HistoryMessageParam]]
    """
    The list of messages in this archive.

    Note: SkipValidation is used to work around a bug in pydantic with OpenAI message types.
    https://github.com/pydantic/pydantic/issues/9541
    """


class Summarizer(Protocol):
    """
    Protocol for a summarizer that can summarize a list of messages.
    """

    async def summarize(self, messages: list[HistoryMessageParam]) -> str:
        """
        Summarizes a list of messages.

        Args:
            messages: The list of messages to summarize.

        Returns:
            A summary of the messages.
        """
        ...
