from typing import Any, List, Protocol, Sequence

from assistant_extensions.ai_clients.model import CompletionMessage
from attr import dataclass
from mcp import Tool
from semantic_workbench_api_model.workbench_model import (
    MessageType,
)

from assistant.extensions.tools.__model import ToolsConfigModel

from ...extensions.tools import ToolCall


@dataclass
class NumberTokensResult:
    count: int
    metadata: dict[str, Any]
    metadata_key: str


@dataclass
class ResponseResult:
    content: str | None
    tool_calls: List[ToolCall] | None
    message_type: MessageType
    metadata: dict[str, Any]
    completion_total_tokens: int


class ResponseProvider(Protocol):
    async def get_response(
        self,
        messages: List[CompletionMessage],
        metadata_key: str,
        tools_extension_config: ToolsConfigModel,
        mcp_tools: List[Tool] | None,
    ) -> ResponseResult: ...

    async def num_tokens_from_messages(
        self,
        messages: Sequence[CompletionMessage],
        model: str,
        metadata_key: str,
    ) -> NumberTokensResult: ...
