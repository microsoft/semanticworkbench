import io
import logging
import pathlib
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, AsyncIterator

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


@dataclass
class ConversationContext:
    id: str
    title: str
    assistant: AssistantContext

    @property
    def _workbench_client(self) -> semantic_workbench_api_model.workbench_service_client.ConversationAPIClient:
        return semantic_workbench_api_model.workbench_service_client.WorkbenchServiceClientBuilder(
            base_url=str(settings.workbench_service_url),
            assistant_service_id=self.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
        ).for_conversation(self.assistant.id, self.id)

    async def send_messages(
        self, messages: workbench_model.NewConversationMessage | list[workbench_model.NewConversationMessage]
    ) -> workbench_model.ConversationMessageList:
        if not isinstance(messages, list):
            messages = [messages]
        return await self._workbench_client.send_messages(*messages)

    async def update_participant_me(
        self, participant: workbench_model.UpdateParticipant
    ) -> workbench_model.ConversationParticipant:
        return await self._workbench_client.update_participant_me(participant)

    async def get_participants(self, include_inactive=False) -> workbench_model.ConversationParticipantList:
        return await self._workbench_client.get_participants(include_inactive=include_inactive)

    async def get_messages(
        self,
        before: uuid.UUID | None = None,
        after: uuid.UUID | None = None,
        message_types: list[workbench_model.MessageType] = [workbench_model.MessageType.chat],
        participant_ids: list[str] | None = None,
        participant_role: workbench_model.ParticipantRole | None = None,
        limit: int | None = None,
    ) -> workbench_model.ConversationMessageList:
        return await self._workbench_client.get_messages(
            before=before,
            after=after,
            message_types=message_types,
            participant_ids=participant_ids,
            participant_role=participant_role,
            limit=limit,
        )

    async def send_conversation_state_event(self, state_event: workbench_model.AssistantStateEvent) -> None:
        return await self._workbench_client.send_conversation_state_event(self.assistant.id, state_event)

    async def write_file(
        self, filename: str, file_content: io.BytesIO, content_type: str = "application/octet-stream"
    ) -> workbench_model.File:
        return await self._workbench_client.write_file(filename, file_content, content_type)

    @asynccontextmanager
    async def read_file(
        self, filename: str, chunk_size: int | None = None
    ) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        async with self._workbench_client.read_file(filename, chunk_size=chunk_size) as stream:
            yield stream

    async def get_files(self, prefix: str | None = None) -> workbench_model.FileList:
        return await self._workbench_client.get_files(prefix=prefix)

    async def file_exists(self, filename: str) -> bool:
        return await self._workbench_client.file_exists(filename)

    async def delete_file(self, filename: str) -> None:
        return await self._workbench_client.delete_file(filename)


def storage_directory_for_context(context: AssistantContext | ConversationContext, partition: str = "") -> pathlib.Path:
    match context:
        case AssistantContext():
            directory = context.id

        case ConversationContext():
            directory = f"{context.assistant.id}-{context.id}"

    if partition:
        directory = f"{directory}_{partition}"

    return pathlib.Path(settings.storage.root) / directory
