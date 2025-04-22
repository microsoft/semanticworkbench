import contextlib
import json
from hashlib import md5
from pathlib import Path
from typing import Callable

import yaml
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import (
    AssistantConversationInspectorStateDataModel,
    ReadOnlyAssistantConversationInspectorStateProvider,
)


def project_to_yaml(state: dict) -> str:
    """
    Project the state to a yaml code block.
    """
    state_as_yaml = yaml.dump(state, sort_keys=False)
    return f"```yaml\n{state_as_yaml}\n```"


class FileStateInspector(ReadOnlyAssistantConversationInspectorStateProvider):
    """
    A conversation inspector state provider that reads the state from a file and displays it as a yaml code block.
    """

    def __init__(
        self,
        display_name: str,
        file_path_source: Callable[[ConversationContext], Path],
        description: str = "",
        projector: Callable[[dict], str | dict] = project_to_yaml,
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"), usedforsecurity=False
        ).hexdigest()
        self._display_name = display_name
        self._file_path_source = file_path_source
        self._description = description
        self._projector = projector

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
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        def read_state(path: Path) -> dict:
            with contextlib.suppress(FileNotFoundError):
                return json.loads(path.read_text(encoding="utf-8"))
            return {}

        state = read_state(self._file_path_source(context))

        projected = self._projector(state)

        return AssistantConversationInspectorStateDataModel(data={"content": projected})
