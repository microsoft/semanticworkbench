from contextlib import asynccontextmanager
from typing import AsyncGenerator

from assistant_drive import Drive, DriveConfig
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    ConversationContext,
    storage_directory_for_context,
)

from ..mcp._assistant_file_resource_handler import AssistantFileResourceHandler
from ._inspector import DocumentInspectors, lock_document_edits
from ._model import DocumentEditorConfigProvider


class DocumentEditorExtension:
    """
    Document Editor Extension for an Assistant. This extension provides functionality in support of MCP servers
    that can edit documents. It provides a client-resource handler, backed by a Drive, that the MCP server can
    read and write document files to. Additionally, it provides inspectors for viewing the document file list,
    viewing the documents, as well as editing the documents.
    """

    def __init__(
        self,
        app: AssistantAppProtocol,
        config_provider: DocumentEditorConfigProvider,
        storage_directory: str = "documents",
    ) -> None:
        self._app = app
        self._storage_directory = storage_directory
        self._inspectors = DocumentInspectors(
            app=app,
            config_provider=config_provider,
            drive_provider=self._drive_for,
        )

    def _drive_for(self, ctx: ConversationContext) -> Drive:
        root = storage_directory_for_context(ctx) / self._storage_directory
        drive = Drive(DriveConfig(root=root))
        return drive

    def client_resource_handler_for(
        self, ctx: ConversationContext
    ) -> AssistantFileResourceHandler:
        return AssistantFileResourceHandler(drive=self._drive_for(ctx))

    @asynccontextmanager
    async def lock_document_edits(
        self, ctx: ConversationContext
    ) -> AsyncGenerator[None, None]:
        """
        Lock the document for editing and return a context manager that will unlock the document when exited.
        """
        async with lock_document_edits(app=self._app, context=ctx) as lock:
            yield lock
