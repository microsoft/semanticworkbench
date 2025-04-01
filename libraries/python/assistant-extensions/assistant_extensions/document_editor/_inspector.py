import datetime
import io
import logging
import uuid
from contextlib import asynccontextmanager
from hashlib import md5
from typing import Annotated, Any, AsyncGenerator, Callable, Protocol

from assistant_drive import Drive, IfDriveFileExistsBehavior
from pydantic import BaseModel, ValidationError
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


def _get_ui_schema(readonly: bool) -> dict[str, Any]:
    schema = get_ui_schema(DocumentFileStateModel)
    schema["ui:options"] = {
        **schema.get("ui:options", {}),
        "collapsible": False,
        "title": "Document Editor",
        "readonly": readonly,
    }
    return schema


class InspectorController(Protocol):
    async def is_enabled(self, context: ConversationContext) -> bool: ...
    async def is_read_only(self, context: ConversationContext) -> bool: ...
    async def get_current_document(
        self, context: ConversationContext
    ) -> DocumentFileStateModel | None: ...
    async def update_current_document(
        self, context: ConversationContext, content: str
    ) -> None: ...


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

    async def get(
        self, context: ConversationContext
    ) -> AssistantConversationInspectorStateDataModel:
        if not await self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"content": "The Document Editor extension is not enabled."}
            )

        document = await self._controller.get_current_document(context)
        if not document:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No current document."}
            )

        return AssistantConversationInspectorStateDataModel(
            data=document.model_dump(mode="json"),
            json_schema=document.model_json_schema(),
            ui_schema=_get_ui_schema(await self._controller.is_read_only(context)),
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

        await self._controller.update_current_document(context, model.content)


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

    async def get(
        self, context: ConversationContext
    ) -> AssistantConversationInspectorStateDataModel:
        if not await self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"content": "The Document Editor MCP server is not enabled."}
            )

        document = await self._controller.get_current_document(context)
        if not document:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No current document."}
            )

        return AssistantConversationInspectorStateDataModel(
            data={
                "content": f"```markdown\n_Filename: {document.filename}_\n\n{document.content}\n```"
            }
        )


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

        viewer = ReadonlyDocumentFileStateInspector(
            controller=self,
            display_name="Document Viewer",
        )
        app.add_inspector_state_provider(state_id=viewer.state_id, provider=viewer)

        editor = EditableDocumentFileStateInspector(
            controller=self,
            display_name="Document Editor",
        )
        app.add_inspector_state_provider(state_id=editor.state_id, provider=editor)

        async def emit_state_change_event(ctx: ConversationContext) -> None:
            for state_id in (editor.state_id, viewer.state_id):
                await ctx.send_conversation_state_event(
                    workbench_model.AssistantStateEvent(
                        state_id=state_id,
                        event="updated",
                        state=None,
                    )
                )

        @app.events.conversation.file.on_created_including_mine
        @app.events.conversation.file.on_updated_including_mine
        @app.events.conversation.file.on_deleted_including_mine
        async def on_file_change(
            ctx: ConversationContext,
            event: workbench_model.ConversationEvent,
            file: workbench_model.File,
        ) -> None:
            if not file.filename.endswith(".md"):
                return

            self._selected_file[ctx.id] = file.filename
            if event.event == workbench_model.ConversationEventType.file_deleted:
                self._selected_file.pop(ctx.id, None)

            await emit_state_change_event(ctx)

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
                    await emit_state_change_event(ctx)

                case False:
                    if ctx.id not in self._readonly:
                        return
                    self._readonly.remove(ctx.id)
                    await emit_state_change_event(ctx)

    async def is_enabled(self, context: ConversationContext) -> bool:
        config = await self._config_provider(context)
        return config.enabled

    async def is_read_only(self, context: ConversationContext) -> bool:
        return context.id in self._readonly

    async def get_current_document(
        self, context: ConversationContext
    ) -> DocumentFileStateModel | None:
        drive = self._drive_provider(context)
        markdown_files = [
            filename for filename in drive.list() if filename.endswith(".md")
        ]
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

    async def update_current_document(
        self, context: ConversationContext, content: str
    ) -> None:
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


@asynccontextmanager
async def lock_document_edits(
    app: AssistantAppProtocol, context: ConversationContext
) -> AsyncGenerator[None, None]:
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
