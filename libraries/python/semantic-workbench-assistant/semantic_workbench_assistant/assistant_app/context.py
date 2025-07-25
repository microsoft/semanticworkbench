import asyncio
import io
import logging
import pathlib
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, AsyncIterator

import httpx
import semantic_workbench_api_model
import semantic_workbench_api_model.workbench_service_client
from semantic_workbench_api_model import workbench_model

from .. import settings

logger = logging.getLogger(__name__)


@dataclass
class AssistantContext:
    id: str
    name: str

    _assistant_service_id: str
    _template_id: str = field(default="default")


class ConversationContext:
    def __init__(
        self,
        id: str,
        title: str,
        assistant: AssistantContext,
        httpx_client: httpx.AsyncClient,
    ) -> None:
        self.id = id
        self.title = title
        self.assistant = assistant

        self._httpx_client = httpx_client

        self._status_lock = asyncio.Lock()
        self._status_stack: list[str | None] = []
        self._prior_status: str | None = None

    def for_conversation(
        self,
        conversation_id: str,
    ) -> "ConversationContext":
        return ConversationContext(
            id=conversation_id,
            title="",
            assistant=self.assistant,
            httpx_client=self._httpx_client,
        )

    @property
    def _conversation_client(
        self,
    ) -> semantic_workbench_api_model.workbench_service_client.ConversationAPIClient:
        return semantic_workbench_api_model.workbench_service_client.WorkbenchServiceClientBuilder(
            assistant_service_id=self.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
            httpx_client=self._httpx_client,
        ).for_conversation(self.assistant.id, self.id)

    @property
    def _conversations_client(
        self,
    ) -> semantic_workbench_api_model.workbench_service_client.ConversationsAPIClient:
        return semantic_workbench_api_model.workbench_service_client.WorkbenchServiceClientBuilder(
            assistant_service_id=self.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
            httpx_client=self._httpx_client,
        ).for_conversations(self.assistant.id)

    @property
    def _assistant_service_client(
        self,
    ) -> semantic_workbench_api_model.workbench_service_client.AssistantServiceAPIClient:
        return semantic_workbench_api_model.workbench_service_client.WorkbenchServiceClientBuilder(
            assistant_service_id=self.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
            httpx_client=self._httpx_client,
        ).for_service()

    async def send_messages(
        self,
        messages: workbench_model.NewConversationMessage | list[workbench_model.NewConversationMessage],
    ) -> workbench_model.ConversationMessageList:
        if not isinstance(messages, list):
            messages = [messages]
        return await self._conversation_client.send_messages(*messages)

    async def update_participant_me(
        self, participant: workbench_model.UpdateParticipant
    ) -> workbench_model.ConversationParticipant:
        return await self._conversation_client.update_participant_me(participant)

    @asynccontextmanager
    async def set_status(self, status: str | None) -> AsyncGenerator[None, None]:
        """
        Context manager to update the participant status and reset it when done.

        Example:
        ```python
        async with conversation.set_status("processing ..."):
            await do_some_work()
        ```
        """
        async with self._status_lock:
            self._status_stack.append(self._prior_status)
            self._prior_status = status
        await self._conversation_client.update_participant_me(workbench_model.UpdateParticipant(status=status))
        try:
            yield
        finally:
            async with self._status_lock:
                revert_to_status = self._status_stack.pop()
            await self._conversation_client.update_participant_me(
                workbench_model.UpdateParticipant(status=revert_to_status)
            )

    async def get_conversation(self) -> workbench_model.Conversation:
        return await self._conversation_client.get_conversation()

    async def update_conversation(self, metadata: dict[str, Any]) -> workbench_model.Conversation:
        return await self._conversation_client.update_conversation(metadata)

    async def update_conversation_title(self, title: str) -> workbench_model.Conversation:
        return await self._conversation_client.update_conversation_title(title)

    async def get_participants(self, include_inactive=False) -> workbench_model.ConversationParticipantList:
        return await self._conversation_client.get_participants(include_inactive=include_inactive)

    async def get_messages(
        self,
        before: uuid.UUID | None = None,
        after: uuid.UUID | None = None,
        message_types: list[workbench_model.MessageType] = [workbench_model.MessageType.chat],
        participant_ids: list[str] | None = None,
        participant_role: workbench_model.ParticipantRole | None = None,
        limit: int | None = None,
    ) -> workbench_model.ConversationMessageList:
        return await self._conversation_client.get_messages(
            before=before,
            after=after,
            message_types=message_types,
            participant_ids=participant_ids,
            participant_role=participant_role,
            limit=limit,
        )

    async def send_conversation_state_event(self, state_event: workbench_model.AssistantStateEvent) -> None:
        return await self._conversation_client.send_conversation_state_event(self.assistant.id, state_event)

    async def write_file(
        self,
        filename: str,
        file_content: io.BytesIO,
        content_type: str = "application/octet-stream",
    ) -> workbench_model.File:
        return await self._conversation_client.write_file(filename, file_content, content_type)

    @asynccontextmanager
    async def read_file(
        self, filename: str, chunk_size: int | None = None
    ) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        async with self._conversation_client.read_file(filename, chunk_size=chunk_size) as stream:
            yield stream

    async def get_file(self, filename: str) -> workbench_model.File | None:
        return await self._conversation_client.get_file(filename=filename)

    async def list_files(self, prefix: str | None = None) -> workbench_model.FileList:
        return await self._conversation_client.get_files(prefix=prefix)

    async def file_exists(self, filename: str) -> bool:
        return await self._conversation_client.file_exists(filename)

    async def delete_file(self, filename: str) -> None:
        return await self._conversation_client.delete_file(filename)

    async def update_file(self, filename: str, metadata: dict[str, Any]) -> workbench_model.FileVersions:
        return await self._conversation_client.update_file(filename, metadata)

    async def get_assistant_services(self, user_ids: list[str] = []) -> workbench_model.AssistantServiceInfoList:
        return await self._assistant_service_client.get_assistant_services(user_ids=user_ids)

    @asynccontextmanager
    async def state_updated_event_after(self, state_id: str, focus_event: bool = False) -> AsyncIterator[None]:
        """
        Raise state "updated" event after the context manager block is executed, and optionally, a
        state "focus" event.

        Example:
        ```python
        # notify workbench that state has been updated
        async with conversation.state_updated_event_after("my_state_id"):
            await do_some_work()

        # notify workbench that state has been updated and set focus
        async with conversation.state_updated_event_after("my_state_id", focus_event=True):
            await do_some_work()
        ```
        """
        yield
        if focus_event:
            await self.send_conversation_state_event(
                workbench_model.AssistantStateEvent(state_id=state_id, event="focus", state=None)
            )
        await self.send_conversation_state_event(
            workbench_model.AssistantStateEvent(state_id=state_id, event="updated", state=None)
        )


def storage_directory_for_context(context: AssistantContext | ConversationContext, partition: str = "") -> pathlib.Path:
    match context:
        case AssistantContext():
            directory = context.id

        case ConversationContext():
            directory = f"{context.assistant.id}-{context.id}"

    if partition:
        directory = f"{directory}_{partition}"

    return pathlib.Path(settings.storage.root) / directory
