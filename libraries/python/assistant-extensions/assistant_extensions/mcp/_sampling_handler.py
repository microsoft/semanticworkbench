from typing import Any, Protocol

from mcp import ClientSession, CreateMessageResult
from mcp.shared.context import RequestContext
from mcp.types import CreateMessageRequestParams, ErrorData

from assistant_extensions.mcp._model import MCPSamplingMessageHandler


class SamplingHandler(Protocol):
    async def handle_message(
        self,
        context: RequestContext[ClientSession, Any],
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData: ...

    @property
    def message_handler(self) -> MCPSamplingMessageHandler: ...
