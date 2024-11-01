import contextlib
import json
from pathlib import Path
from typing import AsyncIterator, Callable

import yaml
from semantic_workbench_api_model.workbench_model import AssistantStateEvent
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import (
    AssistantConversationInspectorStateDataModel,
    ReadOnlyAssistantConversationInspectorStateProvider,
)


class FileStateInspector(ReadOnlyAssistantConversationInspectorStateProvider):
    def __init__(
        self,
        display_name: str,
        file_path_source: Callable[[ConversationContext], Path],
        state_id: str,
        description: str = "",
    ) -> None:
        self._state_id = state_id
        self._display_name = display_name
        self._file_path_source = file_path_source
        self._description = description

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
        def read_state(path: Path) -> dict:
            with contextlib.suppress(FileNotFoundError):
                return json.loads(path.read_text(encoding="utf-8"))
            return {}

        state = read_state(self._file_path_source(context))

        # return the state as a yaml code block, as it is easier to read than json
        return AssistantConversationInspectorStateDataModel(
            data={"content": f"```yaml\n{yaml.dump(state, sort_keys=False)}\n```"},
        )


@contextlib.asynccontextmanager
async def state_change_event_after(context: ConversationContext, state_id: str) -> AsyncIterator[None]:
    yield
    await context.send_conversation_state_event(AssistantStateEvent(state_id=state_id, event="updated", state=None))
