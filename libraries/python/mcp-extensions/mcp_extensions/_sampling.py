from typing import Any

from mcp import IncludeContext, SamplingMessage, ServerSession
from mcp.server.fastmcp import Context
from mcp.types import CreateMessageResult, ModelPreferences


async def send_sampling_request(
    fastmcp_server_context: Context,
    messages: list[SamplingMessage],
    max_tokens: int,
    system_prompt: str | None = None,
    include_context: IncludeContext | None = None,
    temperature: float | None = None,
    stop_sequences: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    model_preferences: ModelPreferences | None = None,
) -> CreateMessageResult:
    """
    Sends a sampling request to the FastMCP server.
    """
    server_session: ServerSession = fastmcp_server_context.session

    return await server_session.create_message(
        messages=messages,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        include_context=include_context,
        temperature=temperature,
        stop_sequences=stop_sequences,
        metadata=metadata,
        model_preferences=model_preferences,
    )
