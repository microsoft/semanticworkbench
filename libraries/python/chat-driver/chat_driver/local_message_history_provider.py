import json
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Any

from context.context import ContextProtocol
from openai.types.chat import (
    ChatCompletionMessageParam,
)

from .message_formatter import MessageFormatter, format_message

DEFAULT_DATA_DIR = Path(".data")


@dataclass
class LocalMessageHistoryProviderConfig:
    context: ContextProtocol
    data_dir: PathLike | str | None = None
    messages: list[ChatCompletionMessageParam] = field(default_factory=list)
    formatter: MessageFormatter | None = None


class LocalMessageHistoryProvider:
    def __init__(self, config: LocalMessageHistoryProviderConfig) -> None:
        if not config.data_dir:
            self.data_dir = DEFAULT_DATA_DIR / "chat_driver" / config.context.session_id
        else:
            self.data_dir = Path(config.data_dir)
        self.formatter = config.formatter or format_message

        # Create the messages file if it doesn't exist.
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)
        self.messages_file = self.data_dir / "messages.json"
        if not self.messages_file.exists():
            self.messages_file.write_text("[]")

    async def get(self) -> list[ChatCompletionMessageParam]:
        return json.loads(self.messages_file.read_text())

    async def append(self, message: ChatCompletionMessageParam) -> None:
        messages = await self.get()
        messages.append(message)
        self.messages_file.write_text(json.dumps(messages, indent=2))

    # Additional methods.

    async def extend(self, messages: list[ChatCompletionMessageParam]) -> None:
        existing_messages = await self.get()
        existing_messages.extend(messages)
        self.messages_file.write_text(json.dumps(existing_messages, indent=2))

    async def set(self, messages: list[ChatCompletionMessageParam], vars: dict[str, Any]) -> None:
        self.messages_file.write_text(json.dumps(messages, indent=2))

    def delete_all(self) -> None:
        self.messages_file.write_text("[]")
