from typing import Iterable, cast

from chat_context_toolkit.virtual_filesystem import DirectoryEntry, FileEntry, MountPoint
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..archive._archive import archive_reader_for
from ..archive._summarizer import convert_oai_messages_to_xml


class ArchiveFileSource:
    def __init__(self, context: ConversationContext, archive_storage_sub_directory: str = "archives") -> None:
        self._archive_reader = archive_reader_for(
            context=context, archive_storage_sub_directory=archive_storage_sub_directory
        )

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """
        List files and directories at the specified path.

        Archive does not have a directory structure, so it only supports the root path "/".
        """
        if not path == "/":
            raise FileNotFoundError("Archive does not have a directory structure, only the root path '/' is supported.")

        files: list[FileEntry] = []
        async for manifest in self._archive_reader.list():
            files.append(
                FileEntry(
                    path=f"/{manifest.filename}",
                    size=manifest.content_size_bytes or 0,
                    timestamp=manifest.timestamp_most_recent,
                    permission="read",
                    description=manifest.summary,
                )
            )

        return files

    async def read_file(self, path: str) -> str:
        """
        Read the content of a file at the specified path.

        Archive does not have a directory structure, so it only supports the root path "/".
        """

        archive_path = path.lstrip("/")

        if not archive_path:
            raise FileNotFoundError("Path must be specified, e.g. '/archive_filename.json'")

        content = await self._archive_reader.read(filename=archive_path)

        if content is None:
            raise FileNotFoundError(f"File not found: '{path}'")

        return convert_oai_messages_to_xml(cast(list[ChatCompletionMessageParam], content.messages))


def archive_file_source_mount(context: ConversationContext) -> MountPoint:
    return MountPoint(
        entry=DirectoryEntry(
            path="/archives",
            description="Archives of the conversation history that no longer fit in the context window.",
            permission="read",
        ),
        file_source=ArchiveFileSource(context=context),
    )
