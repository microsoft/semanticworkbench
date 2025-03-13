# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable

from mcp.server.fastmcp import Context

from mcp_extensions.llm.llm_types import ChatCompletionRequest, ChatCompletionResponse
from mcp_extensions.llm.mcp_chat_completion import mcp_chat_completion
from mcp_extensions.llm.openai_chat_completion import openai_chat_completion


async def chat_completion(
    request: ChatCompletionRequest,
    provider: str,
    client: Callable[..., Any] | Context,
) -> ChatCompletionResponse:
    """Get a chat completion response from the given provider. Currently supported providers:
    - `azure_openai` - Azure OpenAI
    - `mcp` - MCP Sampling

    Args:
        request: Request parameter object
        provider: The supported provider name
        client: Client information, see the provider's implementation for what can be provided

    Returns:
        ChatCompletionResponse: The chat completion response.
    """
    if (provider == "openai" or provider == "azure_openai" or provider == "dev") and isinstance(client, Callable):
        return openai_chat_completion(request, client)
    elif provider == "mcp" and isinstance(client, Context):
        return await mcp_chat_completion(request, client)
    else:
        raise ValueError(f"Provider {provider} not supported or client is of the wrong type")
