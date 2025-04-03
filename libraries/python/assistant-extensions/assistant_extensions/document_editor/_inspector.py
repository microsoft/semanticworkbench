import datetime
import io
import logging
import uuid
from contextlib import asynccontextmanager
from hashlib import md5
from typing import Annotated, Any, AsyncGenerator, Callable, Literal, Protocol

import deepmerge
from assistant_drive import Drive, IfDriveFileExistsBehavior
from pydantic import BaseModel, Field, ValidationError, create_model
from semantic_workbench_api_model import workbench_model
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)
from semantic_workbench_assistant.config import UISchema, get_ui_schema

from ._model import DocumentEditorConfigProvider

logger = logging.getLogger(__name__)


class DocumentFileStateModel(BaseModel):
    filename: Annotated[str, UISchema(readonly=True)]
    content: Annotated[str, UISchema(widget="textarea", rows=800, hide_label=True)]


def document_list_model(documents: list[DocumentFileStateModel]) -> type[BaseModel]:
    filenames = [document.filename for document in documents]

    return create_model(
        "DocumentListModel",
        active_document=Annotated[
            Literal[tuple(filenames)],
            Field(
                title="Edit a document:",
                description="Select a document and click Edit .",
            ),
        ],
    )


def _get_document_editor_ui_schema(readonly: bool, documents: list[DocumentFileStateModel]) -> dict[str, Any]:
    schema = get_ui_schema(DocumentFileStateModel)
    multiple_files_message = "To edit another document, switch to the Documents tab." if len(documents) > 1 else ""
    schema = deepmerge.always_merger.merge(
        schema.copy(),
        {
            "ui:options": {
                "collapsible": False,
                "title": "Document Editor",
                "description": multiple_files_message,
                "readonly": readonly,
            },
        },
    )
    return schema


def _get_document_list_ui_schema(model: type[BaseModel], filenames: list[str]) -> dict[str, Any]:
    return {
        "ui:options": {
            "collapsible": False,
            "hideTitle": True,
        },
        "ui:submitButtonOptions": {
            "submitText": "Edit",
            "norender": len(filenames) <= 1,
        },
        "active_document": {
            "ui:options": {
                "widget": "radio" if len(filenames) > 1 else "hidden",
            },
        },
    }


class InspectorController(Protocol):
    async def is_enabled(self, context: ConversationContext) -> bool: ...
    async def is_read_only(self, context: ConversationContext) -> bool: ...
    async def read_active_document(self, context: ConversationContext) -> DocumentFileStateModel | None: ...
    async def write_active_document(self, context: ConversationContext, content: str) -> None: ...
    async def set_active_filename(self, context: ConversationContext, filename: str) -> None: ...
    async def list_documents(self, context: ConversationContext) -> list[DocumentFileStateModel]: ...


class EditableDocumentFileStateInspector:
    def __init__(
        self,
        controller: InspectorController,
        display_name: str,
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._controller = controller

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        if not await self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"markdown_content": "## Hello World\nThis is some Markdown content."},
            )

        document = await self._controller.read_active_document(context)
        if not document:
            return AssistantConversationInspectorStateDataModel(
                data={"markdown_content": "## Hello World\nThis is some Markdown content."},
            )

        return AssistantConversationInspectorStateDataModel(
            data={"markdown_content": "## Hello World\nThis is some Markdown content."},
        )

    async def set(
        self,
        context: ConversationContext,
        data: dict[str, Any],
    ) -> None:
        if not await self._controller.is_enabled(context):
            return
        if await self._controller.is_read_only(context):
            return

        try:
            model = DocumentFileStateModel.model_validate(data)
        except ValidationError:
            logger.exception("invalid data for DocumentFileStateModel")
            return

        await self._controller.write_active_document(context, model.content)


class ReadonlyDocumentFileStateInspector:
    def __init__(
        self,
        controller: InspectorController,
        display_name: str,
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._controller = controller

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        if not await self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"markdown_content": "## Hello World\nThis is some Markdown content."}
            )

        document = await self._controller.read_active_document(context)
        if not document:
            return AssistantConversationInspectorStateDataModel(
                data={"markdown_content": "## Hello World\nThis is some Markdown content."}
            )

        return AssistantConversationInspectorStateDataModel(
            data={"markdown_content": "## Hello World\nThis is some Markdown content."}
        )


class DocumentListInspector:
    def __init__(
        self,
        controller: InspectorController,
        display_name: str,
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._controller = controller

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        if not await self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"content": "The Document Editor extension is not enabled."}
            )

        documents = await self._controller.list_documents(context)
        if not documents:
            return AssistantConversationInspectorStateDataModel(data={"content": "No documents available."})

        filenames = [document.filename for document in documents]
        model = document_list_model(documents)

        current_document = await self._controller.read_active_document(context)
        selected_filename = current_document.filename if current_document else filenames[0]

        return AssistantConversationInspectorStateDataModel(
            data={
                "attachments": [
                    DocumentFileStateModel.model_validate(document).model_dump(mode="json") for document in documents
                ],
                "active_document": selected_filename,
            },
            json_schema=model.model_json_schema(),
            ui_schema=_get_document_list_ui_schema(model, filenames),
        )

    async def set(
        self,
        context: ConversationContext,
        data: dict[str, Any],
    ) -> None:
        if not await self._controller.is_enabled(context):
            return

        active_document = data.get("active_document")
        if not active_document:
            return

        await self._controller.set_active_filename(context, active_document)


class DocumentInspectors:
    def __init__(
        self,
        app: AssistantAppProtocol,
        config_provider: DocumentEditorConfigProvider,
        drive_provider: Callable[[ConversationContext], Drive],
    ) -> None:
        self._config_provider = config_provider
        self._drive_provider = drive_provider
        self._selected_file: dict[str, str] = {}
        self._readonly: set[str] = set()

        self._file_list = DocumentListInspector(
            controller=self,
            display_name="Documents",
            description="Download a document:",
        )
        app.add_inspector_state_provider(state_id=self._file_list.state_id, provider=self._file_list)

        self._viewer = ReadonlyDocumentFileStateInspector(
            controller=self,
            display_name="Document Viewer",
        )
        # app.add_inspector_state_provider(
        #     state_id=self._viewer.state_id, provider=self._viewer
        # )

        self._editor = EditableDocumentFileStateInspector(
            controller=self,
            display_name="Document Editor",
        )
        app.add_inspector_state_provider(state_id=self._editor.state_id, provider=self._editor)

        @app.events.conversation.participant.on_updated_including_mine
        async def on_participant_update(
            ctx: ConversationContext,
            event: workbench_model.ConversationEvent,
            participant: workbench_model.ConversationParticipant,
        ) -> None:
            documents_locked = participant.metadata.get("document_lock", None)
            if documents_locked is None:
                return

            match documents_locked:
                case True:
                    if ctx.id in self._readonly:
                        return
                    self._readonly.add(ctx.id)
                    await self._emit_state_change_event(ctx)

                case False:
                    if ctx.id not in self._readonly:
                        return
                    self._readonly.remove(ctx.id)
                    await self._emit_state_change_event(ctx)

    async def _emit_state_change_event(self, ctx: ConversationContext) -> None:
        for state_id in (
            self._editor.state_id,
            # self._viewer.state_id,
            self._file_list.state_id,
        ):
            await ctx.send_conversation_state_event(
                workbench_model.AssistantStateEvent(
                    state_id=state_id,
                    event="updated",
                    state=None,
                )
            )

    async def on_external_write(self, context: ConversationContext, filename: str) -> None:
        self._selected_file[context.id] = filename
        await context.send_conversation_state_event(
            workbench_model.AssistantStateEvent(
                state_id=self._editor.state_id,
                event="focus",
                state=None,
            )
        )

    async def is_enabled(self, context: ConversationContext) -> bool:
        config = await self._config_provider(context)
        return config.enabled

    async def is_read_only(self, context: ConversationContext) -> bool:
        return context.id in self._readonly

    async def read_active_document(self, context: ConversationContext) -> DocumentFileStateModel | None:
        drive = self._drive_provider(context)
        markdown_files = [filename for filename in drive.list() if filename.endswith(".md")]
        if not markdown_files:
            self._selected_file.pop(context.id, None)
            return None

        if context.id not in self._selected_file:
            self._selected_file[context.id] = markdown_files[0]

        selected_file_name = self._selected_file[context.id]

        buffer = io.BytesIO()
        try:
            with drive.open_file(selected_file_name) as file:
                buffer.write(file.read())
        except FileNotFoundError:
            return None

        file_content = buffer.getvalue().decode("utf-8")

        return DocumentFileStateModel(content=file_content, filename=selected_file_name)

    async def write_active_document(self, context: ConversationContext, content: str) -> None:
        drive = self._drive_provider(context)
        filename = self._selected_file.get(context.id)
        if not filename:
            raise ValueError("No file selected")

        drive.write(
            content=io.BytesIO(content.encode("utf-8")),
            filename=filename,
            if_exists=IfDriveFileExistsBehavior.OVERWRITE,
            content_type="text/markdown",
        )

    async def list_documents(self, context: ConversationContext) -> list[DocumentFileStateModel]:
        drive = self._drive_provider(context)
        markdown_files = [filename for filename in drive.list() if filename.endswith(".md")]

        documents = []
        for filename in markdown_files:
            buffer = io.BytesIO()
            try:
                with drive.open_file(filename) as file:
                    buffer.write(file.read())
            except FileNotFoundError:
                continue

            file_content = buffer.getvalue().decode("utf-8")
            documents.append(DocumentFileStateModel(content=file_content, filename=filename))

        return sorted(documents, key=lambda x: x.filename)

    async def set_active_filename(self, context: ConversationContext, filename: str) -> None:
        self._selected_file[context.id] = filename

        await context.send_conversation_state_event(
            workbench_model.AssistantStateEvent(
                state_id=self._editor.state_id,
                event="focus",
                state=None,
            )
        )


@asynccontextmanager
async def lock_document_edits(app: AssistantAppProtocol, context: ConversationContext) -> AsyncGenerator[None, None]:
    """
    A temporary work-around to call the event handlers directly to communicate the document lock
    status to the document inspectors. This circumvents the serialization of event delivery by
    calling the event handlers directly.

    It uses an arbitrary event type that the inspector is listening for. The key data is in the
    Participant.metadata["document_lock"] field. The rest is unused.
    """

    def participant(lock: bool) -> workbench_model.ConversationParticipant:
        return workbench_model.ConversationParticipant(
            conversation_id=uuid.UUID(context.id),
            active_participant=True,
            conversation_permission=workbench_model.ConversationPermission.read,
            id="",
            role=workbench_model.ParticipantRole.assistant,
            name="",
            status=None,
            metadata={
                "document_lock": lock,
            },
            status_updated_timestamp=datetime.datetime.now(),
            image=None,
        )

    # lock document edits
    await app.events.conversation.participant._on_updated_handlers(
        False,
        context,
        None,
        participant(True),
    )

    try:
        yield

    finally:
        # unlock the documents
        await app.events.conversation.participant._on_updated_handlers(
            False,
            context,
            None,
            participant(False),
        )
