import json
from hashlib import md5
from typing import Awaitable, Callable
from urllib.parse import quote

from assistant_extensions.mcp import MCPServerConfig
from mcp.types import TextResourceContents
from pydantic import AnyUrl
from semantic_workbench_api_model import workbench_model
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from ._whiteboard import whiteboard_mcp_session


class WhiteboardInspector:
    def __init__(
        self,
        app: AssistantAppProtocol,
        server_config_provider: Callable[[ConversationContext], Awaitable[MCPServerConfig]],
        state_id: str = "",
        display_name: str = "Debug: Whiteboard",
        description: str = "Read-only view of the whiteboard memory.",
    ) -> None:
        self._state_id = (
            state_id
            or md5(
                (type(self).__name__ + "_" + display_name).encode("utf-8"),
                usedforsecurity=False,
            ).hexdigest()
        )
        self._display_name = display_name
        self._description = description
        self._server_config_provider = server_config_provider
        self._viewing_message_timestamp = ""

        app.add_inspector_state_provider(
            state_id=self.state_id,
            provider=self,
        )

        @app.events.conversation.participant.on_updated
        async def participant_updated(
            ctx: ConversationContext,
            event: workbench_model.ConversationEvent,
            participant: workbench_model.ConversationParticipant,
        ) -> None:
            if participant.role != workbench_model.ParticipantRole.user:
                return

            viewing_message_timestamp = participant.metadata.get("viewing_message_timestamp")
            if not viewing_message_timestamp:
                return

            if viewing_message_timestamp == self._viewing_message_timestamp:
                return

            self._viewing_message_timestamp = viewing_message_timestamp
            await ctx.send_conversation_state_event(
                workbench_model.AssistantStateEvent(
                    state_id=self.state_id,
                    event="updated",
                    state=None,
                )
            )

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def is_enabled(self, context: ConversationContext) -> bool:
        server_config = await self._server_config_provider(context)
        return server_config.enabled

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        server_config = await self._server_config_provider(context)
        if not server_config.enabled:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "Whiteboard memory is disabled. Edit the assistant configuration to enable it."},
            )

        async with whiteboard_mcp_session(context, server_config=server_config) as whiteboard_session:
            resource_url = AnyUrl("resource://memory/whiteboard")
            if self._viewing_message_timestamp:
                resource_url = AnyUrl(f"resource://memory/whiteboard/{quote(self._viewing_message_timestamp)}")

            result = await whiteboard_session.client_session.read_resource(resource_url)
            if not result.contents:
                return AssistantConversationInspectorStateDataModel(
                    data={"content": "Error: Whiteboard resource is empty."},
                )

            contents = result.contents[0]

            match contents:
                case TextResourceContents():
                    model = json.loads(contents.text)
                    return AssistantConversationInspectorStateDataModel(
                        data={
                            "content": model.get("content") or "_The whiteboard is currently empty._",
                            "metadata": {
                                "debug": model.get("metadata"),
                            }
                            if model.get("metadata")
                            else {},
                        },
                    )
                case _:
                    return AssistantConversationInspectorStateDataModel(
                        data={"content": "Error: Whiteboard resource is not a text content."},
                    )
