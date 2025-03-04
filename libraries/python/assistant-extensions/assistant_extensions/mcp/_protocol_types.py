"""
Custom Protocol-based type definitions for MCP compatibility.

This module defines Protocol classes to replace missing types from MCP 1.2.1.
"""

from typing import Any, Awaitable, Protocol, TypeVar

from mcp.shared.context import RequestContext
from mcp.types import ErrorData, ListRootsResult

T = TypeVar('T')

class SamplingFnT(Protocol):
    """Type for sampling function callbacks used by MCP client session."""
    def __call__(
        self, content: str, **kwargs: Any
    ) -> Awaitable[T]: ...

class ListRootsFnT(Protocol):
    """Type for list_roots callback functions used by MCP client session."""
    def __call__(
        self, context: RequestContext
    ) -> Awaitable[ListRootsResult | ErrorData]: ...

class MCPSamplingMessageHandlerProtocol(Protocol):
    """Type for MCP message handler callbacks used in OpenAISamplingHandler."""
    def __call__(
        self, context: RequestContext, params: Any
    ) -> Awaitable[Any]: ...
