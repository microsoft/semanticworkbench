import io
from typing import Callable, Iterable

from assistant_drive import Drive
from chat_context_toolkit.virtual_filesystem import DirectoryEntry, FileEntry, MountPoint
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.filesystem._filesystem import AttachmentsExtension, _get_attachments, log_and_send_message_on_error
from assistant.filesystem._model import FilesystemFile
from assistant.filesystem._tasks import get_filesystem_metadata

# region Attachments


class AttachmentFileSource:
    def __init__(self, context: ConversationContext, attachments_extension: AttachmentsExtension) -> None:
        self.context = context
        self.attachments_extension = attachments_extension

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """
        List files and directories at the specified path.

        Attachments do not have a directory structure, so it only supports the root path "/".
        """
        attachments = await _get_attachments(
            context=self.context,
            error_handler=log_and_send_message_on_error,
            include_filenames=None,
            exclude_filenames=[],
        )
        filesystem_metadata = await get_filesystem_metadata(self.context)

        file_entries: list[FileEntry] = []
        for attachment in attachments:
            file_summary = filesystem_metadata.get(attachment.filename, FilesystemFile()).summary
            file_entry = FileEntry(
                path=f"/{attachment.filename}",
                size=len(attachment.content.encode("utf-8")),
                timestamp=attachment.updated_datetime,
                permission="read",
                description=file_summary,  # TODO: Need to get summaries here
            )
            file_entries.append(file_entry)
        return file_entries

    async def read_file(self, path: str) -> str:
        """
        Read the content of a file at the specified path.

        Archive does not have a directory structure, so it only supports the root path "/".
        """
        workbench_path = path.lstrip("/")
        file_content = await self.attachments_extension.get_attachment(context=self.context, filename=workbench_path)
        if file_content is None:
            file_content = "This file is empty."
        return file_content


def attachments_file_source_mount(
    context: ConversationContext, attachments_extension: AttachmentsExtension
) -> MountPoint:
    return MountPoint(
        entry=DirectoryEntry(
            path="/attachments",
            description="User and assistant created files and attachments",
            permission="read",
        ),
        file_source=AttachmentFileSource(context=context, attachments_extension=attachments_extension),
    )


# endregion


# region Editable Documents


class EditableDocumentsFileSource:
    def __init__(self, context: ConversationContext, drive_provider: Callable[[ConversationContext], Drive]) -> None:
        self.context = context
        self.drive_provider = drive_provider

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """
        List files and directories at the specified path.

        Editable documents do not have a directory structure, so it only supports the root path "/".
        """
        drive = self.drive_provider(self.context)
        filesystem_metadata = await get_filesystem_metadata(self.context)

        file_entries: list[FileEntry] = []
        for filename in drive.list():
            try:
                metadata = drive.get_metadata(filename)
                file_summary = filesystem_metadata.get(filename, FilesystemFile()).summary
                file_entry = FileEntry(
                    path=f"/{filename}",
                    size=metadata.size,
                    timestamp=metadata.updated_at,
                    permission="read_write",
                    description=file_summary,
                )
                file_entries.append(file_entry)
            except FileNotFoundError:
                # Skip files that have no metadata (shouldn't happen normally)
                continue

        return file_entries

    async def read_file(self, path: str) -> str:
        """
        Read the content of a file at the specified path.

        Archive does not have a directory structure, so it only supports the root path "/".
        """
        workbench_path = path.lstrip("/")
        drive = self.drive_provider(self.context)
        try:
            buffer = io.BytesIO()
            with drive.open_file(workbench_path) as file:
                buffer.write(file.read())
            return buffer.getvalue().decode("utf-8")
        except FileNotFoundError:
            return "This file does not exist"


def editable_documents_file_source_mount(
    context: ConversationContext, drive_provider: Callable[[ConversationContext], Drive]
) -> MountPoint:
    return MountPoint(
        entry=DirectoryEntry(
            path="/editable_documents", description="Document Editor Created Files", permission="read_write"
        ),
        file_source=EditableDocumentsFileSource(context=context, drive_provider=drive_provider),
    )


# endregion
