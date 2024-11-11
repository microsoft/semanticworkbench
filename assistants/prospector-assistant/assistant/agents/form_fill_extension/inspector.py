import contextlib
import json
from enum import StrEnum
from hashlib import md5
from pathlib import Path
from typing import Callable

import yaml
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import (
    AssistantConversationInspectorStateDataModel,
    ReadOnlyAssistantConversationInspectorStateProvider,
)


class StateProjection(StrEnum):
    """
    The projection to use when displaying the state.
    """

    original_content = "original_content"
    """Return the state as string content."""
    json_to_yaml = "json_to_yaml"
    """Return the state as a yaml code block."""


class FileStateInspector(ReadOnlyAssistantConversationInspectorStateProvider):
    """
    A conversation inspector state provider that reads the state from a file and displays it as a yaml code block.
    """

    def __init__(
        self,
        display_name: str,
        file_path_source: Callable[[ConversationContext], Path],
        description: str = "",
        projection: StateProjection = StateProjection.json_to_yaml,
        select_field: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"), usedforsecurity=False
        ).hexdigest()
        self._display_name = display_name
        self._file_path_source = file_path_source
        self._description = description
        self._projection = projection
        self._select_field = select_field

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

        selected = state.get(self._select_field) if self._select_field else state

        match self._projection:
            case StateProjection.original_content:
                return AssistantConversationInspectorStateDataModel(data={"content": selected})
            case StateProjection.json_to_yaml:
                state_as_yaml = yaml.dump(selected, sort_keys=False)
                # return the state as a yaml code block, as it is easier to read than json
                return AssistantConversationInspectorStateDataModel(
                    data={"content": f"```yaml\n{state_as_yaml}\n```"},
                )
