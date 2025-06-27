import logging
from typing import Iterable

from chat_context_toolkit.virtual_filesystem import (
    DirectoryEntry,
    FileEntry,
    FileSource,
    MountPoint,
)
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant_extensions.attachments._model import Summarizer

from ...attachments import get_attachments
from ...attachments._summarizer import LLMConfig, LLMFileSummarizer, get_attachment_summary

logger = logging.getLogger(__name__)


class AttachmentsVirtualFileSystemFileSource(FileSource):
    """File source for the attachments."""

    def __init__(
        self,
        context: ConversationContext,
        summarizer: Summarizer,
    ) -> None:
        """Initialize the file source with the conversation context."""
        self.context = context
        self.summarizer = summarizer

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """
        List files and directories at the specified path.
        Should support absolute paths only, such as "/dir/file.txt".
        If the directory does not exist, should raise FileNotFoundError.
        """

        query_prefix = path.lstrip("/") or None
        list_files_result = await self.context.list_files(prefix=query_prefix)

        directories: set[str] = set()
        entries: list[DirectoryEntry | FileEntry] = []

        prefix = path.lstrip("/")

        for file in list_files_result.files:
            if prefix and not file.filename.startswith(prefix):
                continue

            relative_filepath = file.filename.replace(prefix, "")

            if "/" in relative_filepath:
                directory = relative_filepath.rsplit("/", 1)[0]
                if directory in directories:
                    continue

                directories.add(directory)
                entries.append(DirectoryEntry(path=f"/{prefix}{directory}", description="", permission="read"))
                continue

            entries.append(
                FileEntry(
                    path=f"/{prefix}{relative_filepath}",
                    size=file.file_size,
                    timestamp=file.updated_datetime,
                    permission="read",
                    description=(await get_attachment_summary(context=self.context, filename=file.filename)).summary,
                )
            )

        return entries

    async def read_file(self, path: str) -> str:
        """
        Read file content from the specified path.
        Should support absolute paths only, such as "/dir/file.txt".
        If the file does not exist, should raise FileNotFoundError.
        FileSource implementations are responsible for representing the file content as a string.
        """

        workbench_path = path.lstrip("/")

        attachments = await get_attachments(
            context=self.context,
            include_filenames=[workbench_path],
            exclude_filenames=[],
            summarizer=self.summarizer,
        )
        if not attachments:
            raise FileNotFoundError(f"File not found: {path}")

        return attachments[0].content


def attachments_file_source_mount(
    context: ConversationContext, service_config: ServiceConfig, request_config: OpenAIRequestConfig
) -> MountPoint:
    return MountPoint(
        entry=DirectoryEntry(
            path="/attachments",
            description="User and assistant created files and attachments",
            permission="read",
        ),
        file_source=AttachmentsVirtualFileSystemFileSource(
            context=context,
            summarizer=LLMFileSummarizer(
                llm_config=LLMConfig(
                    client_factory=lambda: create_client(service_config),
                    model=request_config.model,
                    max_response_tokens=request_config.response_tokens,
                )
            ),
        ),
    )
