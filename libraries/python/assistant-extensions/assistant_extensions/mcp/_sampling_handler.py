from typing import Any, Protocol

from mcp import CreateMessageResult
from mcp.shared.context import RequestContext
from mcp.types import CreateMessageRequestParams, ErrorData



class SamplingHandler(Protocol):
    async def handle_message(
        self,
        context: RequestContext,
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData: ...

    @property
    def message_handler(self) -> Any: ...
