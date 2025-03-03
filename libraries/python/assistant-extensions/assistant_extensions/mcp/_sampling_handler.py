from typing import Protocol

from mcp import CreateMessageResult
from mcp.types import CreateMessageRequestParams, ErrorData

from assistant_extensions.mcp._model import MCPSamplingMessageHandler


class SamplingHandler(Protocol):
    async def handle_message(
        self,
        context,
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData: ...

    @property
    def message_handler(self) -> MCPSamplingMessageHandler: ...
