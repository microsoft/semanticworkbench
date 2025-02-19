from typing import Any, Protocol, Sequence

from attr import dataclass
from llm_client.model import CompletionMessage
from semantic_workbench_api_model.workbench_model import (
    MessageType,
)


@dataclass
class NumberTokensResult:
    count: int
    metadata: dict[str, Any]
    metadata_key: str


@dataclass
class ResponseResult:
    content: str | None
    message_type: MessageType
    metadata: dict[str, Any]
    completion_total_tokens: int


class ResponseProvider(Protocol):
    async def get_response(
        self,
        messages: list[CompletionMessage],
        metadata_key: str,
    ) -> ResponseResult: ...

    async def num_tokens_from_messages(
        self,
        messages: Sequence[CompletionMessage],
        model: str,
        metadata_key: str,
    ) -> NumberTokensResult: ...
